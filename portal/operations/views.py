import csv,hashlib,io,json,secrets,uuid
from datetime import timedelta
from decimal import Decimal,InvalidOperation
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError,PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q,Count,Sum
from django.forms import modelform_factory
from django.http import Http404,HttpResponse,JsonResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from .models import *
from .access import can,require,require_person,scoped,full_profile
from .context import current_edition,editions_for
from .forms import NominationForm,ImportForm,BootstrapForm,ConfigForm
from . import services,imports
from .notifications import flag_validation


def health(request):return JsonResponse({'status':'ok','service':'samvaad-360'})

def request_key(request):return request.POST.get('request_key','')

def edition_required(request):
    e=current_edition(request)
    if not e:raise PermissionDenied('No event edition has been assigned. Ask the administrator to configure your access.')
    return e

class SecureLogin(LoginView):
    template_name='registration/login.html'
    def key(self):return hashlib.sha256(('login:'+self.request.POST.get('username','').strip().casefold()).encode()).hexdigest()
    def post(self,request,*a,**kw):
        row=LoginAttempt.objects.filter(pk=self.key()).first()
        if row and row.failures>=8 and row.last_at>timezone.now()-timedelta(minutes=20):
            return render(request,self.template_name,{'form':self.get_form(),'locked':True},status=429)
        return super().post(request,*a,**kw)
    def form_invalid(self,form):
        row,_=LoginAttempt.objects.get_or_create(key=self.key())
        if row.last_at<timezone.now()-timedelta(minutes=20):row.failures=0
        row.failures+=1;row.save()
        return super().form_invalid(form)
    def form_valid(self,form):
        LoginAttempt.objects.filter(pk=self.key()).delete()
        return super().form_valid(form)


@sensitive_post_parameters('token','password1','password2')
def bootstrap(request):
    User=get_user_model()
    if not settings.BOOTSTRAP_TOKEN or User.objects.filter(is_superuser=True).exists():raise Http404()
    form=BootstrapForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        lock,_=LoginAttempt.objects.get_or_create(key='bootstrap-setup-lock')
        if lock.failures>=8 and lock.last_at>timezone.now()-timedelta(minutes=20):return HttpResponse('Setup temporarily locked.',status=429)
        if not secrets.compare_digest(form.cleaned_data['token'],settings.BOOTSTRAP_TOKEN):
            lock.failures+=1;lock.save();form.add_error('token','Invalid setup code.')
        else:
            with transaction.atomic():
                LoginAttempt.objects.select_for_update().get(pk=lock.pk)
                if User.objects.filter(is_superuser=True).exists():raise Http404()
                User.objects.create_superuser(username=form.cleaned_data['username'],email=form.cleaned_data['email'],password=form.cleaned_data['password1'])
            messages.success(request,'Administrator created. Sign in, then configure event editions and staff roles.');return redirect('login')
    if request.method=='POST' and form.errors:flag_validation(request,form.errors)
    return render(request,'operations/form.html',{'form':form,'title':'Create the first administrator','intro':'Use the one-time setup code configured in the hosting secret store. Setup closes after the first administrator is created.'})

@login_required
@require_POST
def select_edition(request):
    e=get_object_or_404(editions_for(request.user),pk=request.POST.get('edition'))
    request.session['edition']=str(e.pk);return redirect('dashboard')

@login_required
def dashboard(request):
    e=current_edition(request)
    if not e:return render(request,'operations/empty.html',{'title':'Welcome to Samvaad 360','intro':'Create an event and edition in Administration, then enable streams and assign staff roles.'})
    if not can(request.user,e,'participants') and not can(request.user,e,'reports'):return redirect('my_visit')
    resource='participants' if can(request.user,e,'participants') else 'reports'
    qs=scoped(request.user,e,resource)
    stats={'Nominations':qs.count(),'Approved':qs.filter(review='Approved').count(),'Reviews pending':qs.filter(review='Submitted').count(),'Arrivals confirmed':qs.filter(arrived_at__isnull=False).count(),'Registered':qs.filter(registered_at__isnull=False).count(),'Departed':qs.filter(departed_at__isnull=False).count()}
    recent=list(qs.order_by('-updated_at')[:6])
    operations=[]
    if can(request.user,e,'accommodation'):
        beds=Bed.objects.filter(room__property__edition=e,active=True).count();occupied=Stay.objects.filter(participation__in=scoped(request.user,e,'accommodation'),checked_in_at__isnull=False,checked_out_at__isnull=True,cancelled=False).count()
        operations.append(('Beds occupied',f'{occupied} / {beds}'))
    if can(request.user,e,'kits'):operations.append(('Kits issued',KitIssue.objects.filter(participation__in=scoped(request.user,e,'kits')).count()))
    if can(request.user,e,'food'):operations.append(('Meals served',MealIssue.objects.filter(participation__in=scoped(request.user,e,'food')).count()))
    if can(request.user,e,'tickets'):operations.append(('Open helpdesk cases',ticket_queryset(request.user,e).exclude(status='Resolved').count()))
    return render(request,'operations/dashboard.html',{'stats':stats,'recent':recent,'operations':operations,'can_nominate':can(request.user,e,'participants','create')})

@login_required
def participants(request):
    e=edition_required(request);require(request.user,e,'participants')
    qs=scoped(request.user,e);q=request.GET.get('q','').strip()[:150]
    if q:
        pred=Q(name_snapshot__istartswith=q)|Q(participant__phone=q)
        try:
            token=uuid.UUID(q);pred|=Q(pk=token)|Q(badge__token=token,badge__revoked_at__isnull=True)
        except ValueError:pass
        qs=qs.filter(pred).distinct()
    status=request.GET.get('status','')
    if status in ['Draft','Submitted','Approved','Rejected']:qs=qs.filter(review=status)
    page=Paginator(qs.order_by('name_snapshot','id'),30).get_page(request.GET.get('page'))
    return render(request,'operations/participants.html',{'page':page,'q':q,'status':status,'can_nominate':can(request.user,e,'participants','create')})

@login_required
def nomination(request,pk=None):
    e=edition_required(request);require(request.user,e,'participants','edit' if pk else 'create')
    p=get_object_or_404(scoped(request.user,e,'participants','edit'),pk=pk) if pk else None
    form=NominationForm(request.POST or None,user=request.user,edition=e,participation=p)
    if request.method=='POST' and form.is_valid():
        try:
            result=services.nominate(request.user,e,form.cleaned_data['request_key'],form.cleaned_data,p)
            messages.success(request,'Draft saved. Submit it when ready for review.');return redirect('participant_detail',pk=result['id'])
        except (ValidationError,PermissionDenied) as ex:flag_validation(request,ex);form.add_error(None,str(ex))
    if request.method=='POST' and form.errors:flag_validation(request,form.errors)
    return render(request,'operations/form.html',{'form':form,'title':'Edit nomination' if p else 'New nomination','intro':'Use participant-provided information. Community is optional; banking and emergency information are handled in separate restricted screens.'})

@login_required
def participant_detail(request,pk):
    e=edition_required(request);p=get_object_or_404(scoped(request.user,e),pk=pk)
    permissions={r:can(request.user,e,r,a) and scoped(request.user,e,r,a).filter(pk=p.pk).exists() for r,a in [('review','approve'),('identity','approve'),('arrival','create'),('registration','approve'),('accommodation','create'),('transport','create'),('food','create'),('kits','create'),('venue','create'),('finance','create'),('bank','create'),('badge','create')]}
    context={'p':p,'permissions':permissions,'request_key':str(uuid.uuid4()),'editable':can(request.user,e,'participants','edit') and p.review in ['Draft','Rejected'],'profile_visible':full_profile(request.user,e,p),'timeline':Audit.objects.filter(participation=p).select_related('actor'),'stays':Stay.objects.filter(participation=p).select_related('bed__room__property') if can(request.user,e,'accommodation') else [],'claims':Claim.objects.filter(participation=p) if can(request.user,e,'finance') else [],'badges':Badge.objects.filter(participation=p).order_by('-created_at') if can(request.user,e,'badge') else [],'assigned_sessions':Attendance.objects.filter(participation=p).select_related('session__venue'),'journey_titles':['Nomination','Review','Arrival','Accommodation','Registration','Services','Departure']}
    if permissions['identity']:context['identity_record']=IdentityRecord.objects.filter(participation=p).first()
    return render(request,'operations/participant.html',context)

@login_required
@require_POST
def journey_action(request,pk,action):
    p=get_object_or_404(Participation,pk=pk,edition=edition_required(request))
    try:services.transition(request.user,p,request_key(request),action,request.POST.get('version','0'),request.POST.get('notes',''));messages.success(request,'Journey updated.')
    except ValidationError as ex:flag_validation(request,ex);messages.error(request,str(ex))
    return redirect('participant_detail',pk=pk)

# Operational configuration forms: no ledger/security/status fields are exposed here.
MODULES={
'accommodation':[(Property,['name','building','address']),(Room,['property','label','capacity','compatible_group','accessible']),(Bed,['room','label','active'])],
 'transport':[(Vehicle,['name','registration','capacity','driver','driver_contact']),(Trip,['vehicle','origin','destination','starts','ends','status']),(Travel,['participation','mode','origin','service_number','booking_reference','arrival_at','departure_at','pickup_point','status'])],
 'food':[(MealLocation,['name','stall']),(MealWindow,['location','name','starts','ends','capacity'])],
 'kits':[(KitType,['name','received','damaged'])],
 'venue':[(Venue,['name','spot','capacity']),(Session,['venue','stream','name','coordinator','starts','ends','capacity'])],
 'tickets':[(Ticket,['participation','category','priority','summary','details','restricted','owner','status','resolution'])],
 'assistance':[(Assistance,['participation','emergency_contact','instructions','review_on'])],
}

def ticket_queryset(user,e):
    qs=Ticket.objects.filter(edition=e)
    allowed=Q(restricted=False)
    if can(user,e,'assistance'):allowed|=~Q(category='Finance')
    if can(user,e,'finance'):allowed|=Q(category='Finance')
    qs=qs.filter(allowed)
    return qs.filter(Q(participation__in=scoped(user,e,'tickets'))|Q(participation__isnull=True))

def config_queryset(model,user,e,resource):
    if model is Ticket:return ticket_queryset(user,e)
    if model is Room:return Room.objects.filter(property__edition=e)
    if model is Bed:return Bed.objects.filter(room__property__edition=e)
    if model in [Travel,Assistance]:return model.objects.filter(participation__in=scoped(user,e,resource))
    return model.objects.filter(edition=e)

@login_required
def module(request,resource):
    if resource=='finance':return finance_list(request)
    if resource=='reports':return reports(request)
    if resource not in MODULES:raise Http404()
    e=edition_required(request);require(request.user,e,resource)
    sections=[]
    for model,fields in MODULES[resource]:
        qs=config_queryset(model,request.user,e,resource).order_by('-created_at')
        headers=fields[:5]
        rows=[]
        for obj in qs[:100]:
            rows.append({'id':obj.pk,'cells':[str(getattr(obj,f))[:150] for f in headers]})
        sections.append({'title':model._meta.verbose_name_plural.title(),'model':model.__name__.lower(),'headers':headers,'rows':rows,'total':qs.count()})
    return render(request,'operations/module.html',{'title':resource.title(),'resource':resource,'sections':sections,'can_create':can(request.user,e,resource,'create'),'can_edit':can(request.user,e,resource,'edit')})

@login_required
def config_edit(request,resource,model_name,pk=None):
    if resource not in MODULES:raise Http404()
    e=edition_required(request);require(request.user,e,resource,'edit' if pk else 'create')
    pair=next(((m,f) for m,f in MODULES[resource] if m.__name__.lower()==model_name),None)
    if not pair:raise Http404()
    model,fields=pair
    obj=get_object_or_404(config_queryset(model,request.user,e,resource),pk=pk) if pk else None
    Form=modelform_factory(model,form=ConfigForm,fields=fields)
    form=Form(request.POST or None,instance=obj,user=request.user,edition=e)
    if request.method=='POST' and form.is_valid():
        def work():
            row=form.save(commit=False)
            if hasattr(row,'edition_id'):row.edition=e
            if model is Ticket and row.status=='Resolved':row.resolved_at=timezone.now()
            # Inventory edits cannot erase consumed capacity.
            if model is KitType and row.received-row.damaged<KitIssue.objects.filter(kind=row).count():raise ValidationError('Stock cannot be reduced below issued quantity.')
            if model is Vehicle and row.pk and any(t.passenger_set.filter(cancelled=False).count()>row.capacity for t in Trip.objects.filter(vehicle=row)):raise ValidationError('Vehicle capacity is below an existing manifest.')
            if model is Session and row.pk and Attendance.objects.filter(session=row).count()>row.capacity:raise ValidationError('Capacity is below existing session assignments.')
            row.save();form.save_m2m();services.audit(request.user,e,resource+'.configuration_saved',detail={'entity':model.__name__,'id':str(row.pk)})
            return {'id':str(row.pk)}
        try:
            services.mutate(request.user,e,form.cleaned_data['request_key'],'config.'+model_name,{k:str(v) for k,v in form.cleaned_data.items()},work)
            messages.success(request,'Saved.');return redirect('module',resource=resource)
        except ValidationError as ex:flag_validation(request,ex);form.add_error(None,str(ex))
    if request.method=='POST' and form.errors:flag_validation(request,form.errors)
    return render(request,'operations/form.html',{'form':form,'title':('Edit ' if obj else 'Create ')+model._meta.verbose_name.title(),'intro':'Only records in your assigned event edition are selectable.'})

@login_required
@sensitive_post_parameters('account_number','document_number')
def service_form(request,pk,kind):
    e=edition_required(request);p=get_object_or_404(Participation,pk=pk,edition=e)
    resource={'bed':'accommodation','trip':'transport','kit':'kits','meal':'food','entitlement':'food','session':'venue','attendance':'venue','badge':'badge','bank':'bank','claim':'finance','identity':'identity'}.get(kind)
    if not resource:raise Http404()
    require_person(request.user,p,resource,'approve' if kind=='identity' else 'create')
    fields={'request_key':forms.CharField(widget=forms.HiddenInput,initial=str(uuid.uuid4()))}
    if kind=='bed':fields.update(bed=forms.ModelChoiceField(Bed.objects.filter(room__property__edition=e,active=True).select_related('room__property')),starts=forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type':'datetime-local'})),ends=forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type':'datetime-local'})))
    if kind=='trip':fields['trip']=forms.ModelChoiceField(Trip.objects.filter(edition=e,status__in=['Planned','Boarding']))
    if kind=='kit':
        fields['kit']=forms.ModelChoiceField(KitType.objects.filter(edition=e));fields['replacement']=forms.ModelChoiceField(KitIssue.objects.filter(participation=p,replacement_of__isnull=True),required=False);fields['reason']=forms.CharField(required=False)
    if kind in ['meal','entitlement']:fields['window']=forms.ModelChoiceField(MealWindow.objects.filter(edition=e))
    if kind in ['session','attendance']:fields['session']=forms.ModelChoiceField(Session.objects.filter(edition=e))
    if kind=='badge':fields['reason']=forms.CharField(initial='Initial issue')
    if kind=='identity':fields.update(document_type=forms.ChoiceField(choices=[(x,x) for x in ['Aadhaar','Voter ID','PAN','Passport','Other']]),document_number=forms.CharField(required=False,widget=forms.PasswordInput,help_text='Optional. Prefer recording verification without retaining the full number.'),private_reference=forms.CharField(required=False,max_length=250,help_text='Approved private document reference only. No public sharing links.'))
    if kind=='bank':
        fields.update(holder=forms.CharField(max_length=150),bank=forms.CharField(max_length=120),account_number=forms.CharField(widget=forms.PasswordInput,help_text='Stored encrypted; never included in the badge or general reports.'),ifsc=forms.RegexField(r'^[A-Z]{4}0[A-Z0-9]{6}$'))
    if kind=='claim':fields.update(category=forms.CharField(max_length=100),amount=forms.DecimalField(max_digits=10,decimal_places=2,min_value=Decimal('0.01'),label='Requested amount (INR)'))
    Form=type('ServiceForm',(forms.Form,),fields);form=Form(request.POST or None)
    if request.method=='POST' and form.is_valid():
        d=form.cleaned_data;k=d['request_key']
        try:
            if kind=='bed':services.allocate_bed(request.user,p,k,d['bed'],d['starts'],d['ends'])
            elif kind=='trip':services.allocate_trip(request.user,p,k,d['trip'])
            elif kind=='kit':services.issue_service(request.user,p,k,'kits',d['kit'],d['replacement'],d['reason'])
            elif kind=='meal':services.issue_service(request.user,p,k,'food',d['window'])
            elif kind=='entitlement':
                def grant():
                    if d['window'].edition_id!=p.edition_id or not p.food_eligible:raise ValidationError('Check food eligibility and edition.')
                    row,_=MealEntitlement.objects.get_or_create(participation=p,window=d['window']);services.audit(request.user,e,'meal.entitlement',p);return {'id':str(row.pk)}
                services.mutate(request.user,e,k,'entitlement',{'p':p.pk,'window':d['window'].pk},grant)
            elif kind in ['session','attendance']:services.assign_session(request.user,p,k,d['session'],attend=kind=='attendance')
            elif kind=='badge':
                result=services.issue_badge(request.user,p,k,d['reason']);return redirect('badge_print',pk=result['id'])
            elif kind=='identity':services.save_identity(request.user,p,k,d)
            elif kind=='bank':services.save_bank(request.user,p,k,d)
            elif kind=='claim':services.finance(request.user,p,k,'request',{'category':d['category'],'amount_paise':int(d['amount']*100)})
            messages.success(request,'Operation recorded.');return redirect('participant_detail',pk=p.pk)
        except (ValidationError,BankRecord.DoesNotExist) as ex:flag_validation(request,ex);form.add_error(None,str(ex))
    if request.method=='POST' and form.errors:flag_validation(request,form.errors)
    return render(request,'operations/form.html',{'form':form,'title':kind.title()+' — '+p.name_snapshot,'intro':'This operation is validated and recorded on the server. Payment-related screens record approvals and external references; they do not transfer money.'})

@login_required
@require_POST
def accommodation_action(request,pk,action):
    stay=get_object_or_404(Stay,pk=pk,participation__edition=edition_required(request))
    try:services.stay_action(request.user,stay,request_key(request),action);messages.success(request,'Accommodation updated.')
    except ValidationError as ex:flag_validation(request,ex);messages.error(request,str(ex))
    return redirect('participant_detail',pk=stay.participation_id)

@login_required
def finance_list(request):
    e=edition_required(request);require(request.user,e,'finance')
    qs=Claim.objects.filter(participation__in=scoped(request.user,e,'finance')).select_related('participation').order_by('-created_at')
    return render(request,'operations/finance.html',{'claims':qs[:100],'can_approve':can(request.user,e,'finance','approve'),'can_pay':can(request.user,e,'finance','edit'),'request_key':str(uuid.uuid4())})

@login_required
@require_POST
def finance_action(request,pk,action):
    claim=get_object_or_404(Claim,pk=pk,participation__edition=edition_required(request))
    try:
        amount=Decimal(request.POST.get('amount','0'))
        services.finance(request.user,claim.participation,request_key(request),action,{'claim':str(claim.pk),'amount_paise':int(amount*100) if amount else claim.requested_paise,'reference':request.POST.get('reference','')})
        messages.success(request,'Finance record updated; no bank transfer was performed.')
    except (ValidationError,InvalidOperation,ValueError,OverflowError,BankRecord.DoesNotExist) as ex:flag_validation(request,ex);messages.error(request,str(ex))
    return redirect('finance')

@login_required
@require_POST
def verify_bank(request,pk):
    p=get_object_or_404(Participation,pk=pk,edition=edition_required(request))
    try:services.finance(request.user,p,request_key(request),'verify_bank',{});messages.success(request,'Bank verification recorded.')
    except (ValidationError,BankRecord.DoesNotExist) as ex:messages.error(request,str(ex))
    return redirect('bank_view',pk=pk)

@login_required
def bank_view(request,pk):
    p=get_object_or_404(Participation,pk=pk,edition=edition_required(request));require_person(request.user,p,'bank','view')
    row=BankRecord.objects.filter(participant=p.participant).first()
    # Full account plaintext is never returned by this endpoint.
    services.audit(request.user,p.edition,'bank.masked_record_viewed',p)
    return render(request,'operations/bank.html',{'p':p,'bank':row,'can_verify':can(request.user,p.edition,'bank','approve'),'request_key':str(uuid.uuid4())})

@login_required
def badge_print(request,pk):
    badge=get_object_or_404(Badge,pk=pk,revoked_at__isnull=True);require_person(request.user,badge.participation,'badge','view')
    services.audit(request.user,badge.participation.edition,'badge.print_viewed',badge.participation,{'badge':str(badge.pk)})
    return render(request,'operations/badge.html',{'badge':badge})

@login_required
def badge_qr(request,pk):
    import qrcode
    import qrcode.image.svg
    badge=get_object_or_404(Badge,pk=pk,revoked_at__isnull=True);require_person(request.user,badge.participation,'badge','view')
    qr=qrcode.make(str(badge.token),image_factory=qrcode.image.svg.SvgPathImage)
    data=io.BytesIO();qr.save(data)
    response=HttpResponse(data.getvalue(),content_type='image/svg+xml');response['Cache-Control']='private, no-store';return response

@login_required
def import_people(request):
    e=edition_required(request);require(request.user,e,'participants','create');form=ImportForm(request.POST or None,request.FILES or None);report=None
    if request.method=='POST':
        if request.POST.get('action')=='commit':
            staged=request.session.get('staged_import')
            if not staged or staged['edition']!=str(e.pk) or staged['batch']!=request.POST.get('batch'):
                flag_validation(request);messages.error(request,'Preview the file again before importing.');return redirect('import_people')
            report=imports.commit(request.user,e,staged['batch'],staged['rows']);staged['rows']=report;request.session['staged_import']=staged;messages.success(request,'Import processed. Review row-level results.')
        elif form.is_valid():
            try:
                report=imports.preview(request.user,e,form.cleaned_data['file'])
                request.session['staged_import']={'edition':str(e.pk),'batch':form.cleaned_data['batch'],'rows':report}
            except (ValidationError,ValueError,KeyError) as ex:form.add_error(None,str(ex))
    if request.method=='POST' and (form.errors or (report and any(row['errors'] for row in report))):flag_validation(request)
    return render(request,'operations/import.html',{'form':form,'report':report,'batch':request.session.get('staged_import',{}).get('batch')})

@login_required
def import_template(request):
    e=edition_required(request);require(request.user,e,'participants','create')
    response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="samvaad-participants-template.csv"'
    w=csv.writer(response);w.writerow(imports.HEADERS)
    return response

@login_required
def import_errors(request):
    e=edition_required(request);require(request.user,e,'participants','create');staged=request.session.get('staged_import')
    if not staged or staged['edition']!=str(e.pk):raise Http404()
    response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="samvaad-import-results.csv"'
    w=csv.writer(response);w.writerow(['row','status','errors'])
    for row in staged['rows']:w.writerow([row['row'],'Saved' if row['saved'] else 'Error' if row['errors'] else 'Valid','; '.join(row['errors'])])
    return response

@login_required
def reports(request):
    e=edition_required(request);require(request.user,e,'reports');qs=scoped(request.user,e,'reports')
    by_stream=list(qs.values('stream_label').annotate(total=Count('id')).order_by('-total'))
    by_state=list(qs.values('state_snapshot').annotate(total=Count('id')).order_by('-total'))
    years=[]
    for year in editions_for(request.user):
        if can(request.user,year,'reports'):years.append({'year':year.year,'title':year.title,'total':scoped(request.user,year,'reports').count()})
    export=request.GET.get('export')=='csv'
    if export:
        require(request.user,e,'reports','export');services.audit(request.user,e,'analytics.exported',detail={'grain':'stream aggregate'})
        response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="samvaad-stream-summary.csv"'
        w=csv.writer(response);w.writerow(['edition','stream','participations'])
        def safe(x):return "'"+x if str(x).startswith(('=','+','-','@','\t','\r')) else x
        for row in by_stream:w.writerow([safe(e.title),safe(row['stream_label']),row['total']])
        return response
    return render(request,'operations/reports.html',{'streams':by_stream,'states':by_state,'years':years,'can_export':can(request.user,e,'reports','export'),'total':qs.count(),'registered':qs.filter(registered_at__isnull=False).count()})

@login_required
def my_visit(request):
    rows=Participation.objects.filter(participant__user=request.user,review='Approved').select_related('edition','primary_stream')
    visits=[]
    for p in rows:
        visits.append({'p':p,'stays':Stay.objects.filter(participation=p,cancelled=False).select_related('bed__room__property'),'trips':Passenger.objects.filter(participation=p,cancelled=False).select_related('trip__vehicle'),'sessions':Attendance.objects.filter(participation=p).select_related('session__venue'),'meals':MealEntitlement.objects.filter(participation=p).select_related('window__location')})
    return render(request,'operations/my_visit.html',{'visits':visits})

@login_required
def notifications(request):
    from .notifications import visible_notifications,flag_validation
    e=current_edition(request);qs=visible_notifications(request.user,e).select_related('actor','edition')
    from django.db.models import Exists,OuterRef
    qs=qs.annotate(is_read=Exists(NotificationRead.objects.filter(notification_id=OuterRef('pk'),user=request.user)))
    class FilterForm(forms.Form):
        q=forms.CharField(required=False,max_length=120,label='Search user, page, action or message')
        read_state=forms.ChoiceField(required=False,choices=[('','Read and unread'),('unread','Unread'),('read','Read')])
        severity=forms.ChoiceField(required=False,choices=[('','All activity and alerts'),('info','Activity'),('warning','Warnings'),('error','Errors')])
        from_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
        to_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}))
        def clean(self):
            d=super().clean()
            if d.get('from_date') and d.get('to_date') and d['from_date']>d['to_date']:raise forms.ValidationError('Start date must not be after end date.')
            return d
    form=FilterForm(request.GET)
    if form.is_valid():
        d=form.cleaned_data
        if d.get('read_state'):qs=qs.filter(is_read=d['read_state']=='read')
        if d.get('q'):qs=qs.filter(Q(actor__username__icontains=d['q'])|Q(action__icontains=d['q'])|Q(message__icontains=d['q'])|Q(page_name__icontains=d['q'])|Q(page_path__icontains=d['q']))
        if d.get('severity'):qs=qs.filter(severity=d['severity'])
        if d.get('from_date'):qs=qs.filter(created_at__date__gte=d['from_date'])
        if d.get('to_date'):qs=qs.filter(created_at__date__lte=d['to_date'])
    else:flag_validation(request);qs=qs.none()
    page=Paginator(qs.order_by('-created_at','-id'),40).get_page(request.GET.get('page'))
    query=request.GET.copy();query.pop('page',None)
    return render(request,'operations/notifications.html',{'form':form,'page':page,'query':query.urlencode()})

@login_required
@require_POST
def mark_notifications_read(request):
    from .notifications import visible_notifications
    keys=request.POST.getlist('notification')[:100]
    valid=[]
    for key in keys:
        try:valid.append(uuid.UUID(key))
        except ValueError:continue
    allowed=visible_notifications(request.user,current_edition(request)).filter(pk__in=valid)
    NotificationRead.objects.bulk_create([NotificationRead(notification=n,user=request.user) for n in allowed],ignore_conflicts=True)
    messages.success(request,'Selected notifications marked as read.')
    return redirect('notifications')

@login_required
def dashboard_analytics(request):
    from .analytics import DashboardFilters,filtered,summary
    from .notifications import flag_validation
    e=edition_required(request)
    resource='reports' if can(request.user,e,'reports') else 'participants'
    require(request.user,e,resource)
    qs=scoped(request.user,e,resource);demographics=can(request.user,e,'demographics')
    session_key='dashboard_filters:'+str(e.pk)
    saved=request.session.get(session_key,{})
    if request.method=='POST':
        if 'reset_filters' in request.POST:
            request.session.pop(session_key,None);return redirect('dashboard_analytics')
        form=DashboardFilters(request.POST,queryset=qs,demographics=demographics)
        if form.is_valid():
            saved={k:v.isoformat() if hasattr(v,'isoformat') else v for k,v in form.cleaned_data.items()}
            request.session[session_key]=saved;return redirect('dashboard_analytics')
        flag_validation(request);data={}
    else:
        form=DashboardFilters(saved or None,queryset=qs,demographics=demographics)
        if saved and form.is_valid():data=form.cleaned_data
        else:data={}
    filtered_qs=filtered(qs,data)
    context=summary(filtered_qs,demographics);context.update(form=form,refreshed=timezone.now(),demographics=demographics)
    return render(request,'operations/dashboard_analytics.html',context)
