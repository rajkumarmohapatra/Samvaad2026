import hashlib,json,re
from datetime import datetime,time,timedelta
from decimal import Decimal,InvalidOperation
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import *
from .access import require,require_person,scoped


def audit(user,edition,action,p=None,detail=None):
    return Audit.objects.create(actor=user,edition=edition,participation=p,action=action,detail=detail or {})


def mutate(user,edition,key,action,payload,work):
    if not key or len(key)>128:raise ValidationError('A valid request key is required.')
    fingerprint=hashlib.sha256(json.dumps({'action':action,'data':payload},sort_keys=True,default=str).encode()).hexdigest()
    with transaction.atomic():
        current=Edition.objects.select_for_update().get(pk=edition.pk)
        if current.closed:raise ValidationError('This edition is closed. Historical records are read-only.')
        old=Receipt.objects.filter(actor=user,key=key).first()
        if old:
            if old.fingerprint!=fingerprint:raise ValidationError('This request key was already used for different input.')
            return old.result
        result=work()
        Receipt.objects.create(actor=user,key=key,fingerprint=fingerprint,result=result)
        return result


def nominate(user,edition,key,data,existing=None):
    require(user,edition,'participants','create')
    stream=data['primary_stream']
    if stream.kind!='Stream' or not stream.active or not EditionUnit.objects.filter(edition=edition,unit=stream,active=True).exists():raise ValidationError('Choose an active stream enabled for this edition.')
    # Scope is evaluated independently of the browser's filtered dropdown.
    if not user.is_superuser:
        from .access import memberships
        ms=memberships(user,edition,'participants','create')
        if not ms.exclude(role='StreamOwner').filter(stream__isnull=True).exists() and not ms.filter(stream=stream).exists():raise PermissionDenied('You cannot nominate to that stream.')
    def work():
        name=data['name'].strip();phone=data['phone'].strip()
        if not re.fullmatch(r'\d{10,15}',phone):raise ValidationError('Phone must contain 10 to 15 digits.')
        if existing:
            require_person(user,existing,'participants','edit')
            p=Participation.objects.select_for_update().get(pk=existing.pk)
            if p.review not in ['Draft','Rejected']:raise ValidationError('Submitted or approved records cannot be edited. Request a reviewed correction.')
            if p.version!=int(data.get('version',p.version)):raise ValidationError('The record changed. Refresh before saving.')
            master=p.participant
            master.name=name;master.phone=phone
            for f in ['state','district','village','community','languages','email','preferred_name','alternate_phone']:setattr(master,f,data.get(f,''))
            for f in ['tribal_status','tribe_name']:
                if f in data:setattr(master,f,data[f])
            master.full_clean();master.save()
            p.name_snapshot=name;p.state_snapshot=data['state'];p.primary_stream=stream;p.stream_label=stream.name;p.category=data['category'];p.version+=1
        else:
            reuse=data.get('existing_participant')
            if reuse:
                if not user.is_superuser:raise PermissionDenied('Only a privileged administrator may resolve an existing master for reuse.')
                master=reuse
                if Participation.objects.filter(participant=master,edition=edition).exists():raise ValidationError('Participant already exists in this edition.')
            else:
                if Participant.objects.filter(name__iexact=name,phone=phone).exists():raise ValidationError('Likely duplicate. Ask an administrator to confirm whether the existing master should be reused.')
                master=Participant(name=name,phone=phone,**{f:data.get(f,'') for f in ['state','district','village','community','tribal_status','tribe_name','languages','email','preferred_name','alternate_phone']})
                master.full_clean();master.save()
            p=Participation(participant=master,edition=edition,primary_stream=stream,stream_label=stream.name,name_snapshot=name,state_snapshot=data['state'],category=data['category'],nominated_by=user,starts=edition.starts,ends=edition.ends)
        for f in ['travel_eligible','accommodation_eligible','food_eligible','kit_eligible','finance_eligible','accessible_bed_required','accommodation_group','dietary_instructions']:
            if f in data:setattr(p,f,data[f])
        p.full_clean();p.save();p.secondary_streams.set(data.get('secondary_streams',[]))
        audit(user,edition,'nomination.updated' if existing else 'nomination.created',p)
        return {'id':str(p.pk)}
    payload={k:[str(x.pk) for x in v] if hasattr(v,'model') else str(v.pk) if hasattr(v,'pk') else v for k,v in data.items()}
    return mutate(user,edition,key,'nominate',payload,work)


def transition(user,p,key,action,version,notes=''):
    policy={'submit':('participants','edit'),'approve':('review','approve'),'reject':('review','approve'),'verify':('identity','approve'),'identity_not_required':('identity','approve'),'arrive':('arrival','create'),'register':('registration','approve'),'depart':('accommodation','edit'),'close':('configuration','edit')}
    if action not in policy:raise ValidationError('Unknown journey action.')
    resource,perm=policy[action];require_person(user,p,resource,perm)
    def work():
        row=Participation.objects.select_for_update().get(pk=p.pk)
        if row.closed_at or row.version!=int(version):raise ValidationError('Record changed or was closed. Refresh first.')
        if action=='submit':
            if row.review not in ['Draft','Rejected']:raise ValidationError('Only draft/rejected records can be submitted.')
            row.review='Submitted'
        elif action in ['approve','reject']:
            if row.review!='Submitted':raise ValidationError('Only submitted records can be reviewed.')
            if row.nominated_by_id==user.pk:raise ValidationError('Another authorised reviewer must review your nomination.')
            if action=='reject' and not notes.strip():raise ValidationError('A rejection reason is required.')
            row.review='Approved' if action=='approve' else 'Rejected';row.reviewer=user;row.review_notes=notes
        elif action in ['verify','identity_not_required']:
            if row.review!='Approved':raise ValidationError('Approve the nomination first.')
            row.identity_status='Verified' if action=='verify' else 'NotRequired'
        elif action in ['arrive','register']:
            if row.review!='Approved' or row.departed_at:raise ValidationError('An approved, active participation is required.')
            if action=='arrive':
                if row.arrived_at:raise ValidationError('Arrival already recorded.')
                row.arrived_at=timezone.now()
            else:
                if row.identity_status not in ['Verified','NotRequired']:raise ValidationError('Complete the authorised identity verification first.')
                if row.registered_at:raise ValidationError('Registration already recorded.')
                row.registered_at=timezone.now()
        elif action=='depart':
            if not row.arrived_at or row.departed_at:raise ValidationError('An active arrival is required.')
            if Stay.objects.filter(participation=row,cancelled=False,checked_out_at__isnull=True).exists():raise ValidationError('Check out or cancel accommodation first.')
            row.departed_at=timezone.now()
        elif action=='close':
            if not row.departed_at:raise ValidationError('Confirm departure before closing.')
            row.closed_at=timezone.now()
        row.version+=1;row.save();audit(user,row.edition,'journey.'+action,row)
        return {'id':str(row.pk),'version':row.version}
    return mutate(user,p.edition,key,action,{'id':p.pk,'version':version,'notes':notes},work)


def allocate_bed(user,p,key,bed,starts,ends):
    require_person(user,p,'accommodation','create')
    def work():
        p.refresh_from_db()
        if not p.accommodation_eligible or p.review!='Approved' or p.departed_at:raise ValidationError('Approved accommodation eligibility is required.')
        if starts>=ends:raise ValidationError('Checkout must be after check-in.')
        if starts.date()<p.edition.starts or ends.date()>p.edition.ends+timedelta(days=1):raise ValidationError('Stay must fit the event edition.')
        if bed.room.property.edition_id!=p.edition_id or not bed.active:raise ValidationError('Choose an active bed in this edition.')
        if p.accessible_bed_required and not bed.room.accessible:raise ValidationError('An accessible room is required.')
        if bed.room.compatible_group and bed.room.compatible_group!=p.accommodation_group:raise ValidationError('Room compatibility requirement is not met.')
        overlaps=Stay.objects.filter(cancelled=False,checked_out_at__isnull=True,starts__lt=ends,ends__gt=starts)
        if overlaps.filter(Q(bed=bed)|Q(participation=p)).exists():raise ValidationError('Bed or participant has an overlapping reservation.')
        if overlaps.filter(bed__room=bed.room).count()>=bed.room.capacity:raise ValidationError('Room occupancy limit reached.')
        stay=Stay.objects.create(participation=p,bed=bed,starts=starts,ends=ends)
        audit(user,p.edition,'accommodation.reserved',p,{'stay':str(stay.pk)})
        return {'id':str(stay.pk)}
    return mutate(user,p.edition,key,'reserve_bed',{'person':p.pk,'bed':bed.pk,'starts':starts,'ends':ends},work)


def stay_action(user,stay,key,action):
    p=stay.participation;require_person(user,p,'accommodation','edit')
    def work():
        row=Stay.objects.select_for_update().get(pk=stay.pk)
        if action=='checkin':
            if not p.arrived_at or p.departed_at or row.cancelled or row.checked_in_at:raise ValidationError('Confirm active arrival and select an unstarted reservation.')
            if timezone.now()<row.starts-timedelta(hours=12) or timezone.now()>row.ends:raise ValidationError('Reservation is outside the check-in window.')
            row.checked_in_at=timezone.now()
        elif action=='checkout':
            if not row.checked_in_at or row.checked_out_at:raise ValidationError('An active check-in is required.')
            row.checked_out_at=timezone.now()
        elif action=='cancel':
            if row.checked_in_at and not row.checked_out_at:raise ValidationError('Check out an occupied bed before cancellation.')
            row.cancelled=True
        else:raise ValidationError('Unknown stay action.')
        row.save();audit(user,p.edition,'accommodation.'+action,p,{'stay':str(row.pk)});return {'id':str(row.pk)}
    return mutate(user,p.edition,key,'stay.'+action,{'id':stay.pk},work)


def allocate_trip(user,p,key,trip):
    require_person(user,p,'transport','create')
    def work():
        p.refresh_from_db()
        trip.refresh_from_db();trip.vehicle.refresh_from_db()
        if trip.edition_id!=p.edition_id or trip.vehicle.edition_id!=p.edition_id or trip.status not in ['Planned','Boarding'] or p.review!='Approved' or p.closed_at:raise ValidationError('Choose an available trip and approved participation in this edition.')
        if Passenger.objects.filter(trip=trip,cancelled=False).count()>=trip.vehicle.capacity:raise ValidationError('Trip is full.')
        if Passenger.objects.filter(participation=p,cancelled=False,trip__status__in=['Planned','Boarding','InProgress'],trip__starts__lt=trip.ends,trip__ends__gt=trip.starts).exists():raise ValidationError('Participant already has an overlapping trip.')
        row,created=Passenger.objects.get_or_create(trip=trip,participation=p)
        if not created and not row.cancelled:raise ValidationError('Passenger is already allocated.')
        row.cancelled=False;row.save();audit(user,p.edition,'transport.allocated',p,{'trip':str(trip.pk)});return {'id':str(row.pk)}
    return mutate(user,p.edition,key,'allocate_trip',{'person':p.pk,'trip':trip.pk},work)


def issue_service(user,p,key,resource,obj,replacement=None,reason=''):
    require_person(user,p,resource,'create')
    def work():
        p.refresh_from_db()
        if not p.registered_at or p.departed_at:raise ValidationError('An active registration is required.')
        obj.refresh_from_db()
        if obj.edition_id!=p.edition_id:raise ValidationError('Service belongs to another edition.')
        if resource=='kits':
            if not p.kit_eligible:raise ValidationError('Participant is not kit-eligible.')
            if KitIssue.objects.filter(kind=obj).count()>=obj.received-obj.damaged:raise ValidationError('Kit stock is exhausted.')
            if replacement:
                if replacement.participation_id!=p.pk or replacement.kind_id!=obj.pk or not reason.strip() or replacement.replacement_of_id:raise ValidationError('Select an original issue for this participant and provide a replacement reason.')
                if KitIssue.objects.filter(replacement_of=replacement).exists():raise ValidationError('A replacement has already been recorded.')
            elif KitIssue.objects.filter(participation=p,kind=obj,replacement_of__isnull=True).exists():raise ValidationError('Original kit already issued.')
            row=KitIssue.objects.create(participation=p,kind=obj,actor=user,replacement_of=replacement,reason=reason)
        else:
            if not p.food_eligible or not MealEntitlement.objects.filter(participation=p,window=obj).exists():raise ValidationError('No matching meal entitlement.')
            if not obj.starts<=timezone.now()<=obj.ends:raise ValidationError('The meal service window is not open.')
            if MealIssue.objects.filter(window=obj).count()>=obj.capacity:raise ValidationError('Meal window capacity reached.')
            if MealIssue.objects.filter(participation=p,window=obj).exists():raise ValidationError('This meal has already been served.')
            row=MealIssue.objects.create(participation=p,window=obj,actor=user)
        audit(user,p.edition,resource+'.issued',p,{'issue':str(row.pk)});return {'id':str(row.pk)}
    return mutate(user,p.edition,key,'issue.'+resource,{'person':p.pk,'resource':obj.pk,'replacement':str(replacement.pk) if replacement else None,'reason':reason},work)


def assign_session(user,p,key,session,attend=False):
    require_person(user,p,'venue','create')
    def work():
        p.refresh_from_db()
        if p.review!='Approved' or session.edition_id!=p.edition_id:raise ValidationError('Session and approved participation must share an edition.')
        row=Attendance.objects.filter(session=session,participation=p).first()
        if not row:
            if Attendance.objects.filter(session=session).count()>=min(session.capacity,session.venue.capacity):raise ValidationError('Session capacity reached.')
            row=Attendance.objects.create(session=session,participation=p)
        if attend:
            if not p.registered_at:raise ValidationError('Register the participant before recording attendance.')
            row.attended_at=row.attended_at or timezone.now();row.save()
        audit(user,p.edition,'session.attended' if attend else 'session.assigned',p,{'session':str(session.pk)});return {'id':str(row.pk)}
    return mutate(user,p.edition,key,'session',{'person':p.pk,'session':session.pk,'attend':attend},work)


def bank_cipher():
    if not settings.FIELD_ENCRYPTION_KEY:raise ValidationError('Bank storage is disabled until a field-encryption key is configured in the host secret store.')
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


def save_bank(user,p,key,data):
    require_person(user,p,'bank','create')
    account=data['account_number'].strip()
    if not re.fullmatch(r'\d{6,20}',account) or not re.fullmatch(r'[A-Z]{4}0[A-Z0-9]{6}',data['ifsc']):raise ValidationError('Check account number and IFSC format.')
    cipher=bank_cipher().encrypt(account.encode()).decode()
    def work():
        row,_=BankRecord.objects.update_or_create(participant=p.participant,defaults={'holder':data['holder'],'bank':data['bank'],'entered_by':user,'account_cipher':cipher,'last_four':account[-4:],'ifsc':data['ifsc'],'verified_by':None,'verified_at':None})
        audit(user,p.edition,'bank.updated',p)
        return {'id':str(row.pk)}
    # Only a non-reversible fingerprint is stored for replay checking; no plaintext audit/receipt.
    return mutate(user,p.edition,key,'bank',{'person':p.pk,'digest':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()},work)


def finance(user,p,key,action,data):
    perm={'request':'create','verify_bank':'approve','approve':'approve','reject':'approve','record':'edit','failed':'edit','reconcile':'edit'}.get(action)
    if not perm:raise ValidationError('Unknown finance action.')
    require_person(user,p,'bank' if action=='verify_bank' else 'finance',perm)
    def work():
        p.refresh_from_db()
        if not p.finance_eligible or p.review!='Approved':raise ValidationError('Approved financial eligibility is required.')
        if action=='verify_bank':
            row=BankRecord.objects.get(participant=p.participant)
            if row.entered_by_id==user.pk:raise ValidationError('Another authorised person must verify these bank details.')
            row.verified_by=user;row.verified_at=timezone.now();row.save();audit(user,p.edition,'bank.verified',p);return {'id':str(row.pk)}
        if action=='request':
            amount=int(data['amount_paise'])
            if not 0<amount<=100_000_000:raise ValidationError('Amount must be positive and within the configured application limit.')
            row=Claim.objects.create(participation=p,category=data['category'],requested_paise=amount,maker=user)
        else:
            row=Claim.objects.select_for_update().get(pk=data['claim'],participation=p)
            if action in ['approve','reject']:
                if row.status!='Requested' or row.maker_id==user.pk:raise ValidationError('An outstanding claim requires a different checker.')
                amount=int(data.get('amount_paise',row.requested_paise))
                if not 0<amount<=row.requested_paise:raise ValidationError('Approved amount must be positive and no more than requested.')
                row.checker=user;row.approved_paise=amount if action=='approve' else None;row.status='Approved' if action=='approve' else 'Rejected'
            elif action in ['record','failed']:
                if row.status not in ['Approved','PaymentFailed'] or user.pk in [row.maker_id,row.checker_id]:raise ValidationError('An approved claim needs a distinct payment recorder.')
                if not BankRecord.objects.filter(participant=p.participant,verified_at__isnull=False).exists():raise ValidationError('Verify restricted bank details first.')
                ref=data.get('reference','').strip()
                if action=='record' and not re.fullmatch(r'[A-Za-z0-9/-]{4,100}',ref):raise ValidationError('Enter the approved external payment reference.')
                row.payer=user;row.external_reference=ref;row.status='Recorded' if action=='record' else 'PaymentFailed';row.paid_at=timezone.now() if action=='record' else None
            elif action=='reconcile':
                if row.status!='Recorded':raise ValidationError('Only a recorded external payment can be reconciled.')
                row.status='Reconciled'
            row.save()
        audit(user,p.edition,'finance.'+action,p,{'claim':str(row.pk)});return {'id':str(row.pk),'transfers_money':False}
    return mutate(user,p.edition,key,'finance.'+action,{'person':p.pk,**data},work)


def issue_badge(user,p,key,reason):
    require_person(user,p,'badge','create')
    def work():
        p.refresh_from_db()
        if not p.registered_at or p.departed_at:raise ValidationError('An active completed registration is required.')
        if not reason.strip():raise ValidationError('Provide an issue/reprint/replacement reason.')
        Badge.objects.filter(participation=p,revoked_at__isnull=True).update(revoked_at=timezone.now())
        row=Badge.objects.create(participation=p,actor=user,reason=reason)
        audit(user,p.edition,'badge.issued',p,{'badge':str(row.pk)})
        return {'id':str(row.pk)}
    return mutate(user,p.edition,key,'badge',{'person':p.pk,'reason':reason},work)
