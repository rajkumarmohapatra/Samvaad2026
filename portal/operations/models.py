import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator,RegexValidator
from django.db import models
from django.db.models import Q

class Record(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:abstract=True

class Event(Record):
    name=models.CharField(max_length=150,default='Samvaad')
    active=models.BooleanField(default=True)
    def __str__(self):return self.name

class Edition(Record):
    event=models.ForeignKey(Event,on_delete=models.PROTECT)
    year=models.PositiveSmallIntegerField()
    title=models.CharField(max_length=160)
    starts=models.DateField();ends=models.DateField()
    closed=models.BooleanField(default=False)
    helpdesk_contact=models.CharField(max_length=200,blank=True)
    class Meta:constraints=[models.UniqueConstraint(fields=['event','year'],name='unique_event_year'),models.CheckConstraint(condition=Q(ends__gte=models.F('starts')),name='edition_dates_order')]
    def __str__(self):return self.title

class Unit(Record):
    KINDS=[('Unclassified','Unclassified'),('Stream','Stream'),('Team','Team'),('Program','Program')]
    name=models.CharField(max_length=180,unique=True)
    kind=models.CharField(max_length=20,choices=KINDS,default='Unclassified')
    active=models.BooleanField(default=True)
    merged_into=models.ForeignKey('self',on_delete=models.PROTECT,null=True,blank=True)
    def __str__(self):return self.name

class EditionUnit(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    unit=models.ForeignKey(Unit,on_delete=models.PROTECT)
    display_name=models.CharField(max_length=180)
    active=models.BooleanField(default=True)
    class Meta:constraints=[models.UniqueConstraint(fields=['edition','unit'],name='unique_edition_unit')]
    def __str__(self):return f'{self.edition}: {self.display_name}'

class Membership(Record):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    role=models.CharField(max_length=32)
    stream=models.ForeignKey(Unit,on_delete=models.PROTECT,null=True,blank=True)
    active=models.BooleanField(default=True)
    def __str__(self):return f'{self.user}: {self.role} ({self.edition})'

class RolePermission(Record):
    role=models.CharField(max_length=32)
    resource=models.CharField(max_length=40)
    action=models.CharField(max_length=20,choices=[(a,a) for a in ['view','create','edit','approve','export','delete']])
    class Meta:constraints=[models.UniqueConstraint(fields=['role','resource','action'],name='unique_role_grant')]
    def __str__(self):return f'{self.role}: {self.resource}.{self.action}'

class Participant(Record):
    TRIBAL_STATUS_CHOICES=[('', 'Not specified'), ('Tribal', 'Tribal'), ('Not Tribal', 'Not Tribal'), ('Prefer not to say', 'Prefer not to say')]
    name=models.CharField(max_length=150)
    preferred_name=models.CharField(max_length=100,blank=True)
    phone=models.CharField(max_length=20,validators=[RegexValidator(r'^\d{10,15}$','Use 10 to 15 digits.')],db_index=True)
    alternate_phone=models.CharField(max_length=20,blank=True,validators=[RegexValidator(r'^\d{10,15}$','Use 10 to 15 digits or leave blank.')])
    email=models.EmailField(blank=True)
    state=models.CharField(max_length=80)
    district=models.CharField(max_length=100,blank=True)
    village=models.CharField(max_length=120,blank=True)
    community=models.CharField(max_length=180,blank=True,help_text='Optional, self-reported; never inferred.')
    tribal_status=models.CharField('Tribal or Not Tribal',max_length=20,choices=TRIBAL_STATUS_CHOICES,blank=True,default='',help_text='Optional, self-reported. Do not infer this from community, name or location.')
    tribe_name=models.CharField(max_length=180,blank=True,default='',help_text='Optional tribe name, exactly as supplied by the participant.')
    gender=models.CharField(max_length=30,blank=True,choices=[('', 'Not specified'),('Male','Male'),('Female','Female'),('Other','Other / self-described'),('Prefer not to say','Prefer not to say')])
    country=models.CharField(max_length=100,blank=True)
    state_or_ut=models.CharField(max_length=100,blank=True,help_text='Original state/UT classification or label, if supplied.')
    disability_status=models.CharField(max_length=20,blank=True,choices=[('', 'Not specified'),('Yes','Yes'),('No','No'),('Prefer not to say','Prefer not to say')],help_text='Optional, self-reported PWD status; not a medical diagnosis.')
    sub_tribe=models.CharField(max_length=180,blank=True)
    tribe_reference=models.ForeignKey('TribeReference',on_delete=models.PROTECT,null=True,blank=True,help_text='Optional approved master reference; never inferred from name or location.')
    languages=models.CharField(max_length=180,blank=True)
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='participant_profile')
    def __str__(self):return self.name
    def clean(self):
        super().clean()
        if self.tribal_status=='Not Tribal' and (self.tribe_name.strip() or self.tribe_reference_id):
            raise ValidationError({'tribe_name':'Leave tribe name blank when Not Tribal is selected.'})

class Participation(Record):
    participant=models.ForeignKey(Participant,on_delete=models.PROTECT)
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    primary_stream=models.ForeignKey(Unit,on_delete=models.PROTECT)
    stream_label=models.CharField(max_length=180)
    name_snapshot=models.CharField(max_length=150)
    state_snapshot=models.CharField(max_length=80)
    category=models.CharField(max_length=40,default='Delegate')
    nominating_team=models.ForeignKey(Unit,on_delete=models.PROTECT,null=True,blank=True,related_name='nominations')
    secondary_streams=models.ManyToManyField(Unit,blank=True,related_name='secondary_participations')
    starts=models.DateField();ends=models.DateField()
    review=models.CharField(max_length=20,choices=[(s,s) for s in ['Draft','Submitted','Approved','Rejected']],default='Draft',db_index=True)
    nominated_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name='reviews')
    review_notes=models.TextField(blank=True)
    arrived_at=models.DateTimeField(null=True,blank=True)
    registered_at=models.DateTimeField(null=True,blank=True)
    departed_at=models.DateTimeField(null=True,blank=True)
    closed_at=models.DateTimeField(null=True,blank=True)
    identity_status=models.CharField(max_length=20,choices=[('Pending','Pending'),('Verified','Verified'),('NotRequired','Not required'),('Rejected','Rejected')],default='Pending')
    travel_eligible=models.BooleanField(default=False)
    accommodation_eligible=models.BooleanField(default=False)
    food_eligible=models.BooleanField(default=True)
    kit_eligible=models.BooleanField(default=True)
    finance_eligible=models.BooleanField(default=False)
    dietary_instructions=models.CharField(max_length=200,blank=True)
    accessible_bed_required=models.BooleanField(default=False)
    accommodation_group=models.CharField(max_length=30,blank=True,help_text='Configured operational compatibility group; no inferred identity.')
    source_identifier=models.CharField(max_length=100,blank=True)
    attendee_group=models.CharField(max_length=20,blank=True,choices=[('', 'Not specified'),('Participant','Participant'),('Support','Support / non-participant')])
    element_representative=models.CharField(max_length=150,blank=True)
    registration_spoc=models.CharField(max_length=150,blank=True)
    registration_mode=models.CharField(max_length=40,blank=True,choices=[('', 'Not specified'),('Desk','Desk'),('Online','Online'),('Import','Import'),('Other','Other')])
    remarks=models.CharField(max_length=1000,blank=True,help_text='Operational notes only. Do not enter identity, health or banking information here.')
    photo_reference=models.CharField(max_length=250,blank=True,help_text='Approved private asset reference only; no public sharing links or photo uploads.')
    source_created_at=models.DateTimeField(null=True,blank=True)
    source_item_type=models.CharField(max_length=80,blank=True)
    source_path=models.CharField(max_length=250,blank=True)
    legacy_qr_reference=models.CharField(max_length=100,blank=True,help_text='Legacy reference only. New badges always use a fresh opaque token.')
    version=models.PositiveIntegerField(default=1)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['participant','edition'],name='unique_person_edition'),models.UniqueConstraint(fields=['edition','source_identifier'],condition=~Q(source_identifier=''),name='unique_source_id_per_edition'),models.CheckConstraint(condition=Q(ends__gte=models.F('starts')),name='participation_dates_order')]
        indexes=[models.Index(fields=['edition','primary_stream','review'])]
    def __str__(self):return f'{self.name_snapshot} / {self.edition}'

class Audit(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT,null=True)
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT,null=True,blank=True)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    action=models.CharField(max_length=80)
    detail=models.JSONField(default=dict)
    class Meta:ordering=['created_at']

class Receipt(Record):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    key=models.CharField(max_length=128)
    fingerprint=models.CharField(max_length=64)
    result=models.JSONField(default=dict)
    class Meta:constraints=[models.UniqueConstraint(fields=['actor','key'],name='unique_actor_request')]

class Travel(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    mode=models.CharField(max_length=20,choices=[(x,x) for x in ['Train','Flight','Bus','Road','Other']])
    origin=models.CharField(max_length=150)
    service_number=models.CharField(max_length=100,blank=True)
    booking_reference=models.CharField(max_length=100,blank=True)
    arrival_at=models.DateTimeField();departure_at=models.DateTimeField(null=True,blank=True)
    pickup_point=models.CharField(max_length=160)
    status=models.CharField(max_length=30,default='Planned')
    def __str__(self):return f'{self.participation.name_snapshot} - {self.mode}'

class Property(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    name=models.CharField(max_length=150)
    building=models.CharField(max_length=100,blank=True)
    address=models.CharField(max_length=250)
    def __str__(self):return self.name

class Room(Record):
    property=models.ForeignKey(Property,on_delete=models.PROTECT)
    label=models.CharField(max_length=50)
    capacity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    compatible_group=models.CharField(max_length=30,blank=True)
    accessible=models.BooleanField(default=False)
    def __str__(self):return f'{self.property} / {self.label}'

class Bed(Record):
    room=models.ForeignKey(Room,on_delete=models.PROTECT)
    label=models.CharField(max_length=50)
    active=models.BooleanField(default=True)
    class Meta:constraints=[models.UniqueConstraint(fields=['room','label'],name='unique_bed_label')]
    def __str__(self):return f'{self.room} / {self.label}'

class Stay(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    bed=models.ForeignKey(Bed,on_delete=models.PROTECT)
    starts=models.DateTimeField();ends=models.DateTimeField()
    checked_in_at=models.DateTimeField(null=True,blank=True)
    checked_out_at=models.DateTimeField(null=True,blank=True)
    cancelled=models.BooleanField(default=False)
    class Meta:constraints=[models.CheckConstraint(condition=Q(ends__gt=models.F('starts')),name='stay_dates_order')]

class Vehicle(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    name=models.CharField(max_length=100)
    registration=models.CharField(max_length=30)
    capacity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    driver=models.CharField(max_length=100)
    driver_contact=models.CharField(max_length=30)
    def __str__(self):return f'{self.name} ({self.capacity} seats)'

class Trip(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    vehicle=models.ForeignKey(Vehicle,on_delete=models.PROTECT)
    origin=models.CharField(max_length=140);destination=models.CharField(max_length=140)
    starts=models.DateTimeField();ends=models.DateTimeField()
    status=models.CharField(max_length=20,choices=[(s,s) for s in ['Planned','Boarding','InProgress','Completed','Cancelled']],default='Planned')
    class Meta:constraints=[models.CheckConstraint(condition=Q(ends__gt=models.F('starts')),name='trip_dates_order')]
    def __str__(self):return f'{self.origin} → {self.destination} ({self.starts:%d %b %H:%M})'

class Passenger(Record):
    trip=models.ForeignKey(Trip,on_delete=models.PROTECT)
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    cancelled=models.BooleanField(default=False)
    class Meta:constraints=[models.UniqueConstraint(fields=['trip','participation'],name='unique_trip_person')]

class MealLocation(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    name=models.CharField(max_length=120)
    stall=models.CharField(max_length=120,blank=True)
    def __str__(self):return self.name

class MealWindow(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    location=models.ForeignKey(MealLocation,on_delete=models.PROTECT)
    name=models.CharField(max_length=120)
    starts=models.DateTimeField();ends=models.DateTimeField()
    capacity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    class Meta:constraints=[models.CheckConstraint(condition=Q(ends__gt=models.F('starts')),name='meal_dates_order')]
    def __str__(self):return f'{self.name} / {self.location}'

class MealEntitlement(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    window=models.ForeignKey(MealWindow,on_delete=models.PROTECT)
    class Meta:constraints=[models.UniqueConstraint(fields=['participation','window'],name='unique_meal_entitlement')]

class MealIssue(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    window=models.ForeignKey(MealWindow,on_delete=models.PROTECT)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    class Meta:constraints=[models.UniqueConstraint(fields=['participation','window'],name='unique_meal_service')]

class KitType(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    name=models.CharField(max_length=100)
    received=models.PositiveIntegerField(default=0)
    damaged=models.PositiveIntegerField(default=0)
    def __str__(self):return self.name

class KitIssue(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    kind=models.ForeignKey(KitType,on_delete=models.PROTECT)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    replacement_of=models.OneToOneField('self',on_delete=models.PROTECT,null=True,blank=True)
    reason=models.CharField(max_length=200,blank=True)
    class Meta:constraints=[models.UniqueConstraint(fields=['participation','kind'],condition=Q(replacement_of__isnull=True),name='one_original_kit')]

class Venue(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    name=models.CharField(max_length=120)
    spot=models.CharField(max_length=120,blank=True)
    capacity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    def __str__(self):return self.name+(f' / {self.spot}' if self.spot else '')

class Session(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    venue=models.ForeignKey(Venue,on_delete=models.PROTECT)
    stream=models.ForeignKey(Unit,on_delete=models.PROTECT)
    name=models.CharField(max_length=150)
    coordinator=models.CharField(max_length=120)
    starts=models.DateTimeField();ends=models.DateTimeField()
    capacity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    class Meta:constraints=[models.CheckConstraint(condition=Q(ends__gt=models.F('starts')),name='session_dates_order')]
    def __str__(self):return self.name

class Attendance(Record):
    session=models.ForeignKey(Session,on_delete=models.PROTECT)
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    attended_at=models.DateTimeField(null=True,blank=True)
    class Meta:constraints=[models.UniqueConstraint(fields=['session','participation'],name='unique_session_person')]

class BankRecord(Record):
    participant=models.OneToOneField(Participant,on_delete=models.PROTECT)
    holder=models.CharField(max_length=150)
    bank=models.CharField(max_length=120)
    account_cipher=models.TextField()
    entered_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='entered_bank_records')
    last_four=models.CharField(max_length=4)
    ifsc=models.CharField(max_length=11)
    verified_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True)
    verified_at=models.DateTimeField(null=True,blank=True)

class Claim(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    category=models.CharField(max_length=100)
    requested_paise=models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    approved_paise=models.PositiveBigIntegerField(null=True,blank=True)
    maker=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    checker=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name='checked_claims')
    payer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name='paid_claims')
    status=models.CharField(max_length=30,choices=[(s,s) for s in ['Requested','Approved','Rejected','PaymentFailed','Recorded','Reconciled']],default='Requested')
    external_reference=models.CharField(max_length=100,blank=True)
    paid_at=models.DateTimeField(null=True,blank=True)

class Ticket(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT)
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT,null=True,blank=True)
    category=models.CharField(max_length=60)
    priority=models.CharField(max_length=20,choices=[(s,s) for s in ['Low','Normal','High','Critical']],default='Normal')
    summary=models.CharField(max_length=240)
    details=models.TextField(blank=True)
    restricted=models.BooleanField(default=False)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    status=models.CharField(max_length=20,choices=[(s,s) for s in ['Open','InProgress','Escalated','Resolved']],default='Open')
    resolution=models.TextField(blank=True)
    resolved_at=models.DateTimeField(null=True,blank=True)

class Assistance(Record):
    participation=models.OneToOneField(Participation,on_delete=models.PROTECT)
    emergency_contact=models.CharField(max_length=200)
    instructions=models.TextField(blank=True)
    review_on=models.DateField()

class Badge(Record):
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT)
    token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    reason=models.CharField(max_length=150,default='Initial issue')
    revoked_at=models.DateTimeField(null=True,blank=True)

class LoginAttempt(models.Model):
    key=models.CharField(primary_key=True,max_length=64)
    failures=models.PositiveIntegerField(default=0)
    last_at=models.DateTimeField(auto_now=True)


class ParticipantCategory(Record):
    name=models.CharField(max_length=60,unique=True)
    active=models.BooleanField(default=True)
    def __str__(self):return self.name

class TribeReference(Record):
    unique_code=models.CharField(max_length=80,blank=True)
    national_code=models.CharField(max_length=80,blank=True)
    sub_code=models.CharField(max_length=80,blank=True)
    name=models.CharField(max_length=180)
    sub_tribe=models.CharField(max_length=180,blank=True)
    state=models.CharField(max_length=100,blank=True)
    active=models.BooleanField(default=True)
    def __str__(self):return f'{self.name} / {self.state}'

class IdentityRecord(Record):
    participation=models.OneToOneField(Participation,on_delete=models.PROTECT)
    document_type=models.CharField(max_length=50)
    number_cipher=models.TextField(blank=True)
    last_four=models.CharField(max_length=4,blank=True)
    private_reference=models.CharField(max_length=250,blank=True)
    entered_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

class Notification(Record):
    edition=models.ForeignKey(Edition,on_delete=models.PROTECT,null=True,blank=True)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True)
    participation=models.ForeignKey(Participation,on_delete=models.PROTECT,null=True,blank=True)
    action=models.CharField(max_length=100)
    severity=models.CharField(max_length=10,choices=[('info','Activity'),('warning','Warning'),('error','Alert')],default='info')
    message=models.CharField(max_length=240)
    page_name=models.CharField(max_length=120,blank=True)
    page_path=models.CharField(max_length=250,blank=True)
    class Meta:
        ordering=['-created_at']
        indexes=[models.Index(fields=['edition','created_at']),models.Index(fields=['actor','created_at']),models.Index(fields=['severity','created_at'])]

class NotificationRead(Record):
    notification=models.ForeignKey(Notification,on_delete=models.CASCADE)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    class Meta:constraints=[models.UniqueConstraint(fields=['notification','user'],name='unique_notification_reader')]
