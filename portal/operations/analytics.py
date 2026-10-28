from datetime import datetime,time,timedelta
from django import forms
from django.db.models import Count,F
from django.db.models.functions import Coalesce,TruncDate
from django.utils import timezone
from .models import Participation,IdentityRecord,Stay,KitIssue
from .access import can,scoped

class DashboardFilters(forms.Form):
    state=forms.ChoiceField(required=False)
    district=forms.ChoiceField(required=False)
    tribe=forms.ChoiceField(required=False,label='Self-reported tribe')
    tribal_status=forms.ChoiceField(required=False,choices=[('','All'),('Tribal','Tribal'),('Not Tribal','Not Tribal'),('Prefer not to say','Prefer not to say'),('__blank__','Not specified')])
    participant_type=forms.ChoiceField(required=False)
    element=forms.ChoiceField(required=False)
    registration=forms.ChoiceField(required=False,choices=[('','All'),('Registered','Registered'),('Scheduled','Scheduled / approved'),('Draft','Draft'),('Submitted','Submitted'),('Rejected','Rejected')])
    created_from=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    created_to=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
    def __init__(self,*a,queryset,demographics,**kw):
        super().__init__(*a,**kw)
        for field,column in [('state','state_snapshot'),('district','participant__district'),('tribe','participant__tribe_name'),('participant_type','category'),('element','stream_label')]:
            values=queryset.exclude(**{column:''}).values_list(column,flat=True).distinct().order_by(column)
            self.fields[field].choices=[('','All')]+[(x,x) for x in values]
        if not demographics:
            self.fields.pop('tribe');self.fields.pop('tribal_status')
    def clean(self):
        d=super().clean()
        if d.get('created_from') and d.get('created_to') and d['created_from']>d['created_to']:raise forms.ValidationError('Start date must not be after end date.')
        return d

def filtered(queryset,data):
    for field,column in [('state','state_snapshot'),('district','participant__district'),('tribe','participant__tribe_name'),('participant_type','category'),('element','stream_label')]:
        if data.get(field):queryset=queryset.filter(**{column:data[field]})
    if data.get('tribal_status'):queryset=queryset.filter(participant__tribal_status='' if data['tribal_status']=='__blank__' else data['tribal_status'])
    status=data.get('registration')
    if status=='Registered':queryset=queryset.filter(registered_at__isnull=False)
    elif status=='Scheduled':queryset=queryset.filter(review='Approved',registered_at__isnull=True)
    elif status:queryset=queryset.filter(review=status,registered_at__isnull=True)
    queryset=queryset.annotate(report_created=Coalesce('source_created_at','created_at'))
    if data.get('created_from'):queryset=queryset.filter(report_created__gte=timezone.make_aware(datetime.combine(data['created_from'],time.min)))
    if data.get('created_to'):queryset=queryset.filter(report_created__lt=timezone.make_aware(datetime.combine(data['created_to']+timedelta(days=1),time.min)))
    return queryset

def bars(rows,label='label',value='total',limit=15):
    clean=[{'label':str(r.get(label) or 'Not specified'),'value':r[value]} for r in rows]
    clean.sort(key=lambda r:(-r['value'],r['label']))
    if len(clean)>limit:
        rest=clean[limit:];clean=clean[:limit]+[{'label':'Other groups','value':sum(x['value'] for x in rest)}]
    maximum=max([r['value'] for r in clean],default=0)
    for row in clean:row['width']=round(100*row['value']/maximum,2) if maximum else 0
    return clean

def groups(qs,column):return list(qs.values(label=F(column)).annotate(total=Count('pk')).order_by('-total','label'))

def summary(qs,demographics):
    total=qs.count();registered=qs.filter(registered_at__isnull=False).count()
    cards=[('Attendee records',total),('Registered',registered),('States represented',qs.exclude(state_snapshot='').values('state_snapshot').distinct().count())]
    if demographics:cards.append(('Self-reported tribes',qs.exclude(participant__tribe_name='').values('participant__tribe_name').distinct().count()))
    charts=[{'title':'Samvaad element','rows':bars(groups(qs,'stream_label'))},{'title':'Participant type','rows':bars(groups(qs,'category'))},{'title':'State coverage','rows':bars(groups(qs,'state_snapshot'))}]
    if demographics:
        for title,column in [('Tribal status (self-reported)','participant__tribal_status'),('Gender (self-reported)','participant__gender'),('PWD status (self-reported)','participant__disability_status'),('Tribe representation (self-reported)','participant__tribe_name')]:charts.append({'title':title,'rows':bars(groups(qs,column))})
    for chart in charts:
        if chart['title'] in ['Tribal status (self-reported)','Gender (self-reported)','PWD status (self-reported)']:
            chart['kind']='donut';chart['sum']=sum(row['value'] for row in chart['rows']);offset=0
            for index,row in enumerate(chart['rows']):
                length=282.743*row['value']/chart['sum'] if chart['sum'] else 0
                row['dash']=f'{length:.3f} {282.743-length:.3f}';row['offset']=round(-offset,3);row['color']=['#194F40','#A76B34','#D9B676','#778D9B'][index%4];offset+=length
    ids=qs.values('id')
    identity=list(IdentityRecord.objects.filter(participation__in=ids).values('document_type').annotate(total=Count('participation_id',distinct=True)))
    if demographics:
        recorded=sum(r['total'] for r in identity)
        if total>recorded:identity.append({'document_type':'Not recorded','total':total-recorded})
        charts.append({'title':'Identity proof type — status only','rows':bars(identity,label='document_type')})
    stays=Stay.objects.filter(participation__in=ids,cancelled=False,checked_in_at__isnull=False,checked_out_at__isnull=True)
    accommodation=list(stays.values('bed__room__property__name').annotate(total=Count('participation_id',distinct=True)))
    charts.append({'title':'Checked-in participants by property','rows':bars(accommodation,label='bed__room__property__name')})
    issued=KitIssue.objects.filter(participation__in=ids,replacement_of__isnull=True).values('participation_id').distinct().count()
    eligible=qs.filter(kit_eligible=True).count()
    charts.append({'title':'Kit distribution','rows':bars([{'label':'Issued','total':issued},{'label':'Eligible — pending','total':max(0,eligible-issued)},{'label':'Not eligible','total':total-eligible}])})
    trend=list(qs.annotate(day=TruncDate('report_created')).values('day').annotate(total=Count('id')).order_by('day'))
    max_count=max([r['total'] for r in trend],default=0)
    for i,row in enumerate(trend):
        row['x']=round(35+(i/(len(trend)-1) if len(trend)>1 else .5)*630,2)
        row['y']=round(175-(row['total']/max_count if max_count else 0)*145,2)
    matrix=list(qs.values('stream_label','category').annotate(total=Count('id')).order_by('stream_label','category'))
    spocs=list(qs.values('registration_spoc','stream_label').annotate(total=Count('id')).order_by('registration_spoc','stream_label'))
    districts=groups(qs,'participant__district')
    return {'cards':cards,'charts':charts,'trend':trend,'trend_max':max_count,'trend_first':trend[0]['day'] if trend else None,'trend_last':trend[-1]['day'] if trend else None,'trend_points':' '.join(f'{r["x"]},{r["y"]}' for r in trend),'matrix':matrix,'spocs':spocs,'districts':districts,'total':total,'registered':registered}
