import uuid
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import *
from .access import memberships,scoped

class NominationForm(forms.Form):
    request_key=forms.CharField(widget=forms.HiddenInput)
    version=forms.IntegerField(required=False,widget=forms.HiddenInput)
    name=forms.CharField(max_length=150,label='Full name')
    preferred_name=forms.CharField(max_length=100,required=False)
    phone=forms.RegexField(r'^\d{10,15}$',max_length=15,label='Phone (10–15 digits)')
    alternate_phone=forms.CharField(max_length=20,required=False)
    email=forms.EmailField(required=False)
    state=forms.CharField(max_length=80)
    district=forms.CharField(max_length=100,required=False)
    village=forms.CharField(max_length=120,required=False)
    community=forms.CharField(max_length=180,required=False,label='Self-reported community (optional)')
    tribal_status=forms.ChoiceField(choices=Participant.TRIBAL_STATUS_CHOICES,required=False,label='Tribal or Not Tribal',help_text='Optional, self-reported. Select Not specified or Prefer not to say if appropriate.')
    tribe_name=forms.CharField(max_length=180,required=False,label='Tribe name (optional)',help_text='Enter only the name supplied by the participant; leave blank when Not Tribal is selected.')
    languages=forms.CharField(max_length=180,required=False)
    primary_stream=forms.ModelChoiceField(queryset=Unit.objects.none())
    secondary_streams=forms.ModelMultipleChoiceField(queryset=Unit.objects.none(),required=False)
    category=forms.ChoiceField(choices=[(x,x) for x in ['Delegate','Artist','Artisan','Healer','Volunteer','Crew','Other']])
    travel_eligible=forms.BooleanField(required=False)
    accommodation_eligible=forms.BooleanField(required=False)
    food_eligible=forms.BooleanField(required=False,initial=True)
    kit_eligible=forms.BooleanField(required=False,initial=True)
    finance_eligible=forms.BooleanField(required=False)
    accessible_bed_required=forms.BooleanField(required=False)
    accommodation_group=forms.CharField(max_length=30,required=False)
    dietary_instructions=forms.CharField(max_length=200,required=False)
    existing_participant=forms.ModelChoiceField(queryset=Participant.objects.none(),required=False,label='Reuse existing master (administrator only)')
    def __init__(self,*args,user,edition,participation=None,**kwargs):
        super().__init__(*args,**kwargs)
        enabled=Unit.objects.filter(editionunit__edition=edition,editionunit__active=True,kind='Stream',active=True)
        if not user.is_superuser:
            ms=memberships(user,edition,'participants','create')
            if not ms.exclude(role='StreamOwner').filter(stream__isnull=True).exists():enabled=enabled.filter(pk__in=ms.values_list('stream_id',flat=True))
        self.fields['primary_stream'].queryset=enabled
        self.fields['secondary_streams'].queryset=Unit.objects.filter(editionunit__edition=edition,editionunit__active=True,kind='Stream',active=True)
        if user.is_superuser:self.fields['existing_participant'].queryset=Participant.objects.all()
        else:self.fields.pop('existing_participant')
        self.initial['request_key']=str(uuid.uuid4())
        if participation:
            self.initial.update({f:getattr(participation.participant,f) for f in ['name','preferred_name','phone','alternate_phone','email','state','district','village','community','tribal_status','tribe_name','languages']})
            for f in ['version','category','primary_stream','travel_eligible','accommodation_eligible','food_eligible','kit_eligible','finance_eligible','accessible_bed_required','accommodation_group','dietary_instructions']:self.initial[f]=getattr(participation,f)
            self.initial['secondary_streams']=participation.secondary_streams.all()
    def clean(self):
        data=super().clean()
        if data.get('tribal_status')=='Not Tribal' and data.get('tribe_name'):
            self.add_error('tribe_name','Leave tribe name blank when Not Tribal is selected.')
        return data

class ImportForm(forms.Form):
    file=forms.FileField(label='UTF-8 CSV or .xlsx file')
    batch=forms.CharField(widget=forms.HiddenInput)
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.initial['batch']=str(uuid.uuid4())
    def clean_file(self):
        f=self.cleaned_data['file']
        if f.size>2_000_000:raise ValidationError('Maximum file size is 2 MB; split larger files.')
        if not f.name.lower().endswith(('.csv','.xlsx')):raise ValidationError('Upload .csv or .xlsx, not macros or older Excel formats.')
        return f

class BootstrapForm(forms.Form):
    token=forms.CharField(widget=forms.PasswordInput,help_text='One-time code configured in the hosting secret store.')
    username=forms.CharField(max_length=100)
    email=forms.EmailField()
    password1=forms.CharField(widget=forms.PasswordInput,label='Password (12+ characters)')
    password2=forms.CharField(widget=forms.PasswordInput,label='Confirm password')
    def clean(self):
        from django.contrib.auth.password_validation import validate_password
        data=super().clean()
        if data.get('password1')!=data.get('password2'):raise ValidationError('Passwords do not match.')
        if data.get('password1'):validate_password(data['password1'])
        return data

class ConfigForm(forms.ModelForm):
    request_key=forms.CharField(widget=forms.HiddenInput)
    def __init__(self,*args,user,edition,**kwargs):
        self.user=user;self.edition=edition;super().__init__(*args,**kwargs)
        self.initial['request_key']=str(uuid.uuid4())
        for field in self.fields.values():
            if isinstance(field,forms.DateTimeField):field.widget=forms.DateTimeInput(attrs={'type':'datetime-local'},format='%Y-%m-%dT%H:%M');field.input_formats=['%Y-%m-%dT%H:%M']
            elif isinstance(field,forms.DateField):field.widget=forms.DateInput(attrs={'type':'date'})
        for name,field in self.fields.items():
            if not isinstance(field,forms.ModelChoiceField):continue
            model=field.queryset.model
            if model is Participation:field.queryset=scoped(user,edition)
            elif model is Participant:field.queryset=Participant.objects.filter(participation__in=scoped(user,edition)).distinct()
            elif model is Unit:field.queryset=Unit.objects.filter(editionunit__edition=edition,editionunit__active=True,active=True)
            elif model is Property:field.queryset=Property.objects.filter(edition=edition)
            elif model is Room:field.queryset=Room.objects.filter(property__edition=edition)
            elif model is Bed:field.queryset=Bed.objects.filter(room__property__edition=edition)
            elif model is get_user_model():field.queryset=model.objects.filter(Q(membership__edition=edition,membership__active=True)|Q(is_superuser=True)).distinct()
            elif any(f.name=='edition' for f in model._meta.fields):field.queryset=model.objects.filter(edition=edition)
    def clean(self):
        d=super().clean()
        if d.get('starts') and d.get('ends') and d['starts']>=d['ends']:raise ValidationError('End must follow start.')
        if self._meta.model is Trip and d.get('vehicle') and d.get('starts') and d.get('ends'):
            other=Trip.objects.filter(edition=self.edition,vehicle=d['vehicle'],starts__lt=d['ends'],ends__gt=d['starts']).exclude(status='Cancelled')
            if self.instance.pk:other=other.exclude(pk=self.instance.pk)
            if other.exists():raise ValidationError('Vehicle already has an overlapping trip.')
        if self._meta.model is Session and d.get('venue') and d.get('starts') and d.get('ends'):
            if d.get('capacity',0)>d['venue'].capacity:raise ValidationError('Session exceeds venue capacity.')
            other=Session.objects.filter(venue=d['venue'],starts__lt=d['ends'],ends__gt=d['starts'])
            if self.instance.pk:other=other.exclude(pk=self.instance.pk)
            if other.exists():raise ValidationError('This venue spot already has an overlapping session.')
        if self._meta.model is KitType and d.get('received',0)<d.get('damaged',0):raise ValidationError('Damage cannot exceed received stock.')
        if self._meta.model is Ticket:
            if d.get('category') in ['Safety','Health','Finance']:d['restricted']=True
            if d.get('restricted'):
                from .access import can
                if not can(self.user,self.edition,'finance' if d.get('category')=='Finance' else 'assistance','view'):raise ValidationError('Only the authorised restricted-case team may manage this case.')
            if d.get('status')=='Resolved' and not d.get('resolution','').strip():raise ValidationError('Provide a resolution before closing the case.')
        return d
