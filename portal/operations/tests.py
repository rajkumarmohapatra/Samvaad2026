import io,uuid
from datetime import timedelta
from decimal import Decimal
from cryptography.fernet import Fernet
from django.test import TestCase,Client,override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError,PermissionDenied
from django.utils import timezone
from django.urls import reverse
from .models import *
from .services import *
from .access import DEFAULT_GRANTS,scoped,full_profile
from .forms import ConfigForm
from .imports import preview,commit

@override_settings(STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class PortalTests(TestCase):
    def setUp(self):
        self.User=get_user_model()
        self.admin=self.User.objects.create_superuser('admin','synthetic@example.invalid','Synthetic-Test-Password-2026!')
        self.owner=self.User.objects.create_user('owner',password='Synthetic-Test-Password-2026!')
        self.other=self.User.objects.create_user('other',password='Synthetic-Test-Password-2026!')
        self.reviewer=self.User.objects.create_user('reviewer',password='Synthetic-Test-Password-2026!')
        self.registration=self.User.objects.create_user('registration',password='Synthetic-Test-Password-2026!')
        self.accom=self.User.objects.create_user('accommodation',password='Synthetic-Test-Password-2026!')
        self.maker=self.User.objects.create_user('maker',password='Synthetic-Test-Password-2026!')
        self.checker=self.User.objects.create_user('checker',password='Synthetic-Test-Password-2026!')
        self.payer=self.User.objects.create_user('payer',password='Synthetic-Test-Password-2026!')
        self.event=Event.objects.create(name='SYNTHETIC TEST')
        today=timezone.localdate();self.edition=Edition.objects.create(event=self.event,year=today.year,title='SYNTHETIC TEST',starts=today,ends=today+timedelta(days=5))
        self.a=Unit.objects.create(name='A',kind='Stream');self.b=Unit.objects.create(name='B',kind='Stream')
        for unit in [self.a,self.b]:EditionUnit.objects.create(edition=self.edition,unit=unit,display_name=unit.name)
        for role,resources in DEFAULT_GRANTS.items():
            for resource,actions in resources.items():
                for action in actions.split():RolePermission.objects.create(role=role,resource=resource,action=action)
        for user,role,stream in [(self.owner,'StreamOwner',self.a),(self.other,'StreamOwner',self.b),(self.reviewer,'Reviewer',None),(self.registration,'Registration',None),(self.accom,'Accommodation',None),(self.maker,'FinanceMaker',None),(self.checker,'FinanceChecker',None),(self.payer,'FinancePayer',None)]:Membership.objects.create(user=user,edition=self.edition,role=role,stream=stream)
        self.data={'name':'Synthetic Test','phone':'0000000000','state':'Synthetic State','primary_stream':self.a,'category':'Delegate','food_eligible':True,'kit_eligible':True,'accommodation_eligible':True,'finance_eligible':True}
    def key(self):return str(uuid.uuid4())
    def create(self,n=0,approved=False):
        d={**self.data,'name':f'Synthetic Test {n}','phone':f'0{n:09}'}
        result=nominate(self.owner,self.edition,self.key(),d);p=Participation.objects.get(pk=result['id'])
        if approved:
            transition(self.owner,p,self.key(),'submit',p.version);p.refresh_from_db();transition(self.reviewer,p,self.key(),'approve',p.version);p.refresh_from_db()
        return p
    def register(self,n=0):
        p=self.create(n,True);transition(self.registration,p,self.key(),'verify',p.version);p.refresh_from_db();transition(self.registration,p,self.key(),'register',p.version);p.refresh_from_db();return p
    def test_nomination_idempotency(self):
        key=self.key();one=nominate(self.owner,self.edition,key,self.data);two=nominate(self.owner,self.edition,key,self.data);self.assertEqual(one,two);self.assertEqual(Participation.objects.count(),1)
    def test_request_payload_conflict(self):
        key=self.key();nominate(self.owner,self.edition,key,self.data)
        with self.assertRaises(ValidationError):nominate(self.owner,self.edition,key,{**self.data,'name':'Changed'})
    def test_stream_write_denied(self):
        with self.assertRaises(PermissionDenied):nominate(self.other,self.edition,self.key(),self.data)
    def test_cross_stream_queryset_empty(self):
        self.create();self.assertEqual(scoped(self.other,self.edition).count(),0)
    def test_duplicate_detection(self):
        self.create()
        with self.assertRaises(ValidationError):nominate(self.owner,self.edition,self.key(),{**self.data,'name':'Synthetic Test 0'})
    def test_owner_cannot_approve(self):
        p=self.create()
        with self.assertRaises(PermissionDenied):transition(self.owner,p,self.key(),'approve',p.version)
    def test_reviewer_cannot_self_approve(self):
        p=self.create();p.nominated_by=self.reviewer;p.review='Submitted';p.save()
        with self.assertRaises(ValidationError):transition(self.reviewer,p,self.key(),'approve',p.version)
    def test_review_requires_submission(self):
        p=self.create()
        with self.assertRaises(ValidationError):transition(self.reviewer,p,self.key(),'approve',p.version)
    def test_submitted_draft_cannot_change(self):
        p=self.create();transition(self.owner,p,self.key(),'submit',p.version);p.refresh_from_db()
        with self.assertRaises(ValidationError):nominate(self.owner,self.edition,self.key(),{**self.data,'name':p.name_snapshot,'version':p.version},p)
    def test_stale_journey_version(self):
        p=self.create();transition(self.owner,p,self.key(),'submit',p.version)
        with self.assertRaises(ValidationError):transition(self.reviewer,p,self.key(),'approve',1)
    def test_registration_independent_of_bed(self):
        p=self.register();self.assertTrue(p.registered_at);self.assertFalse(Stay.objects.filter(participation=p).exists())
    def test_registration_needs_identity(self):
        p=self.create(approved=True)
        with self.assertRaises(ValidationError):transition(self.registration,p,self.key(),'register',p.version)
    def test_closed_edition(self):
        self.edition.closed=True;self.edition.save()
        with self.assertRaises(ValidationError):self.create()
    def room(self,accessible=False):
        prop=Property.objects.create(edition=self.edition,name='Synthetic property',address='Synthetic')
        room=Room.objects.create(property=prop,label='R1',capacity=1,accessible=accessible)
        return Bed.objects.create(room=room,label='B1')
    def test_bed_overlap(self):
        p=self.create(approved=True);other=self.create(1,True);bed=self.room();start=timezone.now();end=start+timedelta(days=1)
        allocate_bed(self.accom,p,self.key(),bed,start,end)
        with self.assertRaises(ValidationError):allocate_bed(self.accom,other,self.key(),bed,start,end)
    def test_accessible_requirement(self):
        p=self.create(approved=True);p.accessible_bed_required=True;p.save();bed=self.room();start=timezone.now()
        with self.assertRaises(ValidationError):allocate_bed(self.accom,p,self.key(),bed,start,start+timedelta(days=1))
    def test_room_group_requirement(self):
        p=self.create(approved=True);bed=self.room();bed.room.compatible_group='A';bed.room.save();start=timezone.now()
        with self.assertRaises(ValidationError):allocate_bed(self.accom,p,self.key(),bed,start,start+timedelta(days=1))
    def test_trip_capacity(self):
        p=self.create(approved=True);b=self.create(1,True);now=timezone.now();v=Vehicle.objects.create(edition=self.edition,name='Synthetic',registration='TEST',capacity=1,driver='Synthetic',driver_contact='Synthetic')
        trip=Trip.objects.create(edition=self.edition,vehicle=v,origin='A',destination='B',starts=now,ends=now+timedelta(hours=1))
        allocate_trip(self.admin,p,self.key(),trip)
        with self.assertRaises(ValidationError):allocate_trip(self.admin,b,self.key(),trip)
    def test_kit_duplicate_and_stock(self):
        p=self.register();kind=KitType.objects.create(edition=self.edition,name='Test',received=2)
        issue_service(self.admin,p,self.key(),'kits',kind)
        with self.assertRaises(ValidationError):issue_service(self.admin,p,self.key(),'kits',kind)
    def test_kit_replacement_history(self):
        p=self.register();kind=KitType.objects.create(edition=self.edition,name='Test',received=2)
        a=issue_service(self.admin,p,self.key(),'kits',kind);original=KitIssue.objects.get(pk=a['id'])
        issue_service(self.admin,p,self.key(),'kits',kind,original,'Synthetic lost kit')
        self.assertEqual(KitIssue.objects.count(),2)
    def test_meal_entitlement_required(self):
        p=self.register();now=timezone.now();loc=MealLocation.objects.create(edition=self.edition,name='Test');w=MealWindow.objects.create(edition=self.edition,location=loc,name='Lunch',starts=now-timedelta(hours=1),ends=now+timedelta(hours=1),capacity=1)
        with self.assertRaises(ValidationError):issue_service(self.admin,p,self.key(),'food',w)
        MealEntitlement.objects.create(participation=p,window=w);issue_service(self.admin,p,self.key(),'food',w)
        with self.assertRaises(ValidationError):issue_service(self.admin,p,self.key(),'food',w)
    def test_badge_token_only_and_revocation(self):
        p=self.register();a=issue_badge(self.registration,p,self.key(),'Initial');b=issue_badge(self.registration,p,self.key(),'Replacement')
        self.assertTrue(Badge.objects.get(pk=a['id']).revoked_at);self.assertFalse(Badge.objects.get(pk=b['id']).revoked_at)
        self.client.force_login(self.registration);qr=self.client.get(reverse('badge_qr',args=[b['id']]))
        self.assertEqual(qr.status_code,200);self.assertEqual(qr['Content-Type'],'image/svg+xml');self.assertNotIn(p.participant.phone.encode(),qr.content)
    def test_finance_maker_checker_payer(self):
        p=self.create(approved=True);r=finance(self.maker,p,self.key(),'request',{'category':'Synthetic','amount_paise':12000});claim=Claim.objects.get(pk=r['id'])
        Membership.objects.create(user=self.maker,edition=self.edition,role='FinanceChecker')
        with self.assertRaises(ValidationError):finance(self.maker,p,self.key(),'approve',{'claim':str(claim.pk),'amount_paise':10000})
        finance(self.checker,p,self.key(),'approve',{'claim':str(claim.pk),'amount_paise':10000})
        with self.assertRaises(ValidationError):finance(self.payer,p,self.key(),'record',{'claim':str(claim.pk),'reference':'SYNTHETIC-REF'})
    def test_encrypted_bank_storage_and_separation(self):
        p=self.create(approved=True)
        with override_settings(FIELD_ENCRYPTION_KEY=Fernet.generate_key().decode()):
            save_bank(self.maker,p,self.key(),{'holder':'Synthetic','bank':'Synthetic','account_number':'00000000','ifsc':'TEST0000000'})
            record=BankRecord.objects.get(participant=p.participant);self.assertNotIn('00000000',record.account_cipher)
            with self.assertRaises(PermissionDenied):finance(self.maker,p,self.key(),'verify_bank',{})
            finance(self.checker,p,self.key(),'verify_bank',{})
            self.client.force_login(self.checker);response=self.client.get(reverse('bank_view',args=[p.pk]));self.assertEqual(response.status_code,200);self.assertNotIn(b'00000000',response.content)
    def test_bank_disabled_without_key(self):
        p=self.create(approved=True)
        with override_settings(FIELD_ENCRYPTION_KEY=''):
            with self.assertRaises(ValidationError):save_bank(self.maker,p,self.key(),{'holder':'Synthetic','bank':'Synthetic','account_number':'00000000','ifsc':'TEST0000000'})
    def test_unknown_user_no_access(self):
        p=self.create();outsider=self.User.objects.create_user('outsider');self.client.force_login(outsider)
        self.assertEqual(self.client.get(reverse('participants')).status_code,403)
    def test_participant_only_own_visit(self):
        p=self.create(approved=True);other=self.create(1,True);u=self.User.objects.create_user('participant');p.participant.user=u;p.participant.save();self.client.force_login(u)
        response=self.client.get(reverse('my_visit'));self.assertContains(response,p.name_snapshot);self.assertNotContains(response,other.name_snapshot)
        self.assertEqual(self.client.get(reverse('participant_detail',args=[other.pk])).status_code,404)
    def test_cross_stream_http_denial(self):
        p=self.create();self.client.force_login(self.other);self.assertEqual(self.client.get(reverse('participant_detail',args=[p.pk])).status_code,404)
    def test_mixed_roles_do_not_leak_contact(self):
        p=self.create();Membership.objects.create(user=self.other,edition=self.edition,role='Leadership')
        self.assertFalse(full_profile(self.other,self.edition,p))
    def test_csrf_enforced(self):
        self.create();client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.post(reverse('select_edition'),{'edition':self.edition.pk}).status_code,403)
    def test_import_preview_commit_retry(self):
        f=io.BytesIO(('name,phone,state,primary_stream,category\nSynthetic Import,0000000011,Test,'+str(self.a.pk)+',Delegate\nBad,,Test,'+str(self.b.pk)+',Delegate\n').encode());f.name='test.csv'
        report=preview(self.owner,self.edition,f);self.assertFalse(report[0]['errors']);self.assertTrue(report[1]['errors'])
        commit(self.owner,self.edition,'batch',report);commit(self.owner,self.edition,'batch',report);self.assertEqual(Participation.objects.count(),1)
    def test_dashboard_and_operational_templates(self):
        p=self.create();self.client.force_login(self.admin)
        for url in [reverse('dashboard'),reverse('participants'),reverse('participant_detail',args=[p.pk]),reverse('nominate'),reverse('reports'),reverse('finance'),reverse('import_people'),reverse('bank_view',args=[p.pk])]+[reverse('module',args=[r]) for r in ['accommodation','transport','food','kits','venue','tickets','assistance']]:
            response=self.client.get(url);self.assertEqual(response.status_code,200,url)
        for resource,model in [('accommodation','property'),('transport','vehicle'),('food','meallocation'),('kits','kittype'),('venue','venue'),('tickets','ticket'),('assistance','assistance')]:
            self.assertEqual(self.client.get(reverse('config_create',args=[resource,model])).status_code,200)
    def test_analytics_cannot_retrieve_profiles(self):
        u=self.User.objects.create_user('analytics');Membership.objects.create(user=u,edition=self.edition,role='Analytics');self.client.force_login(u)
        self.assertEqual(self.client.get(reverse('participants')).status_code,403);self.assertEqual(self.client.get(reverse('reports')).status_code,200)
    def test_normal_staff_cannot_use_admin(self):
        self.owner.is_staff=True;self.owner.save();self.client.force_login(self.owner)
        self.assertEqual(self.client.get('/admin/').status_code,302)
    def test_login_rate_limit(self):
        for n in range(8):self.client.post(reverse('login'),{'username':'unknown','password':'incorrect'})
        self.assertEqual(self.client.post(reverse('login'),{'username':'unknown','password':'incorrect'}).status_code,429)
    def test_unauthenticated_redirect(self):self.assertEqual(self.client.get(reverse('participants')).status_code,302)
    def test_self_reported_tribal_fields_save_and_edit(self):
        result=nominate(self.owner,self.edition,self.key(),{**self.data,'tribal_status':'Tribal','tribe_name':'Synthetic Tribe'})
        p=Participation.objects.get(pk=result['id'])
        self.assertEqual(p.participant.tribal_status,'Tribal')
        self.assertEqual(p.participant.tribe_name,'Synthetic Tribe')
        from .forms import NominationForm
        form=NominationForm(user=self.owner,edition=self.edition,participation=p)
        self.assertEqual(form.initial['tribal_status'],'Tribal')
        self.assertEqual(form.initial['tribe_name'],'Synthetic Tribe')
        nominate(self.owner,self.edition,self.key(),{**self.data,'version':p.version,'tribal_status':'Not Tribal','tribe_name':''},p)
        p.participant.refresh_from_db()
        self.assertEqual(p.participant.tribal_status,'Not Tribal')
        self.assertEqual(p.participant.tribe_name,'')
    def test_tribal_fields_default_unspecified_without_inference(self):
        result=nominate(self.owner,self.edition,self.key(),{**self.data,'community':'Synthetic Community'})
        p=Participation.objects.get(pk=result['id'])
        self.assertEqual(p.participant.tribal_status,'')
        self.assertEqual(p.participant.tribe_name,'')
    def test_prefer_not_to_say_is_supported(self):
        result=nominate(self.owner,self.edition,self.key(),{**self.data,'tribal_status':'Prefer not to say'})
        self.assertEqual(Participation.objects.get(pk=result['id']).participant.tribal_status,'Prefer not to say')
    def test_invalid_tribal_status_fails_backend_validation(self):
        with self.assertRaises(ValidationError):nominate(self.owner,self.edition,self.key(),{**self.data,'tribal_status':'Inferred'})
        self.assertEqual(Participant.objects.count(),0)
    def test_not_tribal_with_tribe_name_is_rejected(self):
        with self.assertRaises(ValidationError):nominate(self.owner,self.edition,self.key(),{**self.data,'tribal_status':'Not Tribal','tribe_name':'Synthetic Tribe'})
        self.assertEqual(Participant.objects.count(),0)
    def test_import_accepts_optional_tribal_columns(self):
        from .imports import HEADERS
        self.assertIn('tribal_status',HEADERS);self.assertIn('tribe_name',HEADERS)
        f=io.BytesIO(('name,phone,state,primary_stream,category,tribal_status,tribe_name\nSynthetic Import,0000000011,Test,'+str(self.a.pk)+',Delegate,tribal,Synthetic Tribe\nSynthetic Other,0000000012,Test,'+str(self.a.pk)+',Delegate,not tribal,\n').encode());f.name='test.csv'
        report=preview(self.owner,self.edition,f)
        self.assertTrue(all(not row['errors'] for row in report))
        commit(self.owner,self.edition,'tribal-import',report)
        self.assertEqual(Participant.objects.get(name='Synthetic Import').tribe_name,'Synthetic Tribe')
        self.assertEqual(Participant.objects.get(name='Synthetic Other').tribal_status,'Not Tribal')
    def test_import_reports_tribal_validation_errors(self):
        f=io.BytesIO(('name,phone,state,primary_stream,category,tribal_status,tribe_name\nSynthetic Import,0000000011,Test,'+str(self.a.pk)+',Delegate,Not Tribal,Synthetic Tribe\n').encode());f.name='test.csv'
        report=preview(self.owner,self.edition,f)
        self.assertTrue(report[0]['errors'])
        self.assertTrue(any('tribe_name' in error for error in report[0]['errors']))
    def test_tribal_fields_only_visible_to_authorised_profile_roles(self):
        result=nominate(self.owner,self.edition,self.key(),{**self.data,'tribal_status':'Tribal','tribe_name':'Synthetic Secret Tribe'})
        p=Participation.objects.get(pk=result['id'])
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('participant_detail',args=[p.pk])),'Synthetic Secret Tribe')
        self.client.force_login(self.maker)
        response=self.client.get(reverse('participant_detail',args=[p.pk]))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'Synthetic Secret Tribe')
        self.assertNotContains(response,'Tribal or Not Tribal (self-reported)')
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse('reports')),'Synthetic Secret Tribe')
