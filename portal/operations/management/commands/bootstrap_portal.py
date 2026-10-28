import json
from pathlib import Path
from datetime import date,timedelta,datetime,time
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from operations.models import *
from operations.access import DEFAULT_GRANTS

class Command(BaseCommand):
    help='Install default role policy and exact organisational names. --demo creates synthetic records only in an empty portal.'
    def add_arguments(self,p):p.add_argument('--demo',action='store_true');p.add_argument('--demo-if-empty',action='store_true');p.add_argument('--count',type=int,default=3000)
    def handle(self,*args,**options):
        with transaction.atomic():
            if not RolePermission.objects.exists():
                for role,resources in DEFAULT_GRANTS.items():
                    for resource,actions in resources.items():
                        for action in actions.split():RolePermission.objects.get_or_create(role=role,resource=resource,action=action)
            if not ParticipantCategory.objects.exists():
                ParticipantCategory.objects.bulk_create([ParticipantCategory(name=name) for name in ['Participants','Atithya','Delegate','Delegate Community','Food Stall','Team Samvaad','Crew','Artist','Artisan','Healer','Volunteer','Other']])
            path=Path(__file__).resolve().parents[4]/'data-model/initial-units.json'
            if not Unit.objects.exists():
                for row in json.loads(path.read_text()):Unit.objects.get_or_create(name=row['name'],defaults={'kind':'Unclassified'})
            if options['demo'] or (options['demo_if_empty'] and not Edition.objects.exists() and not Participant.objects.exists()):
                if Edition.objects.exists() or Participant.objects.exists():raise CommandError('Refusing to seed demo data into a non-empty portal.')
                self.demo(options['count'])
        self.stdout.write(self.style.SUCCESS('Role policy and organisational names installed.'+(' Synthetic demo created.' if options['demo'] else '')))
    def demo(self,count):
        if count<3000:raise CommandError('Use at least 3,000 synthetic current-year records.')
        user,_=get_user_model().objects.get_or_create(username='synthetic-seed',defaults={'is_active':False})
        user.set_unusable_password();user.save()
        event=Event.objects.create(name='Samvaad — SYNTHETIC PILOT')
        today=timezone.localdate()
        current=Edition.objects.create(event=event,year=today.year,title=f'Samvaad {today.year} — SYNTHETIC PILOT',starts=today,ends=today+timedelta(days=5),helpdesk_contact='Synthetic pilot; contact the project administrator')
        old=Edition.objects.create(event=event,year=today.year-1,title=f'Samvaad {today.year-1} — SYNTHETIC HISTORY',starts=date(today.year-1,11,15),ends=date(today.year-1,11,19),closed=True)
        streams=[]
        for name in ['Tribal Artisans','Tribal Cuisine','Tribal Healers','Tribal Sports']:
            unit=Unit.objects.get(name=name);unit.kind='Stream';unit.save();streams.append(unit)
            for e in [current,old]:EditionUnit.objects.create(edition=e,unit=unit,display_name=name)
        masters=[Participant(name=f'Synthetic Participant {n:05}',phone=f'0{n:09}',state=['Jharkhand','Odisha','Chhattisgarh','West Bengal'][n%4],district=f'Synthetic District {n%20}') for n in range(count)]
        Participant.objects.bulk_create(masters,batch_size=500)
        participations=[]
        for n,master in enumerate(masters):
            for e in ([old,current] if n<600 else [current]):
                approved=n%5>=2
                participations.append(Participation(participant=master,edition=e,primary_stream=streams[n%4],stream_label=streams[n%4].name,name_snapshot=master.name,state_snapshot=master.state,category='Delegate',nominated_by=user,starts=e.starts,ends=e.ends,review='Approved' if approved else 'Submitted' if n%5==1 else 'Draft',identity_status='Verified' if approved else 'Pending',registered_at=timezone.now() if approved and n%4==0 else None,arrived_at=timezone.now() if approved and n%3==0 else None,accommodation_eligible=True,travel_eligible=True))
        Participation.objects.bulk_create(participations,batch_size=500)
        prop=Property.objects.create(edition=current,name='Synthetic Accommodation',address='Synthetic location only')
        for n in range(25):
            room=Room.objects.create(property=prop,label=f'R{n+1:02}',capacity=4,accessible=n<3)
            Bed.objects.bulk_create([Bed(room=room,label=str(i+1)) for i in range(4)])
        vehicle=Vehicle.objects.create(edition=current,name='Synthetic shuttle',registration='SYNTHETIC',capacity=20,driver='Synthetic coordinator',driver_contact='Not a real contact')
        now=timezone.now()
        Trip.objects.create(edition=current,vehicle=vehicle,origin='Synthetic station',destination='Synthetic venue',starts=now+timedelta(hours=2),ends=now+timedelta(hours=3))
        location=MealLocation.objects.create(edition=current,name='Synthetic dining location')
        window=MealWindow.objects.create(edition=current,location=location,name='Synthetic meal service',starts=now-timedelta(hours=1),ends=now+timedelta(hours=8),capacity=count)
        MealEntitlement.objects.bulk_create([MealEntitlement(participation=p,window=window) for p in participations if p.edition_id==current.pk],batch_size=500)
        KitType.objects.create(edition=current,name='Standard welcome kit',received=count)
        for n,name in enumerate(['Gopal Maidan','TCC']):
            venue=Venue.objects.create(edition=current,name=name,spot='Synthetic program spot',capacity=500)
            Session.objects.create(edition=current,venue=venue,stream=streams[n],name='Synthetic welcome session '+str(n+1),coordinator='Synthetic coordinator',starts=now+timedelta(hours=4),ends=now+timedelta(hours=5),capacity=200)
        self.stdout.write(f'{count} current-year and 600 historical participations created. No login passwords were seeded.')
