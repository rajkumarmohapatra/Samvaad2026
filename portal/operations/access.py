from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Membership,RolePermission,Participation

DEFAULT_GRANTS={
'Admin':{'configuration':'view create edit approve export','participants':'view create edit export','review':'view approve','identity':'view approve','arrival':'view create','registration':'view approve','accommodation':'view create edit','transport':'view create edit export','food':'view create edit','kits':'view create edit','venue':'view create edit','finance':'view create','bank':'view create','assistance':'view create edit','tickets':'view create edit','reports':'view export','badge':'view create'},
'Leadership':{'participants':'view','reports':'view'},
'StreamOwner':{'participants':'view create edit','review':'view'},
'Reviewer':{'participants':'view','review':'view approve'},
'Registration':{'participants':'view','identity':'view approve','registration':'view approve','badge':'view create','kits':'view'},
'Accommodation':{'participants':'view','arrival':'view create','accommodation':'view create edit'},
'Transport':{'participants':'view','transport':'view create edit export','arrival':'view'},
'Food':{'participants':'view','food':'view create edit'},
'Kits':{'participants':'view','kits':'view create edit'},
'FinanceMaker':{'participants':'view','finance':'view create','bank':'view create'},
'FinanceChecker':{'participants':'view','finance':'view approve','bank':'view approve'},
'FinancePayer':{'participants':'view','finance':'view edit'},
'Venue':{'participants':'view','venue':'view create edit'},
'Safety':{'participants':'view','assistance':'view create edit','tickets':'view create edit'},
'Helpdesk':{'participants':'view','tickets':'view create edit'},
'Analytics':{'reports':'view export'},
'Participant':{},
}

def memberships(user,edition,resource,action):
    roles=RolePermission.objects.filter(resource=resource,action=action).values_list('role',flat=True)
    return Membership.objects.filter(user=user,edition=edition,active=True,role__in=roles)

def can(user,edition,resource,action='view'):
    return bool(user.is_authenticated and (user.is_superuser or memberships(user,edition,resource,action).exists()))

def require(user,edition,resource,action='view'):
    if not can(user,edition,resource,action):raise PermissionDenied('Your assigned role does not permit this operation.')

def scoped(user,edition,resource='participants',action='view'):
    qs=Participation.objects.filter(edition=edition).select_related('participant','primary_stream','edition')
    if user.is_superuser:return qs
    ms=memberships(user,edition,resource,action)
    if ms.exclude(role='StreamOwner').filter(stream__isnull=True).exists():return qs
    units=list(ms.exclude(stream__isnull=True).values_list('stream_id',flat=True))
    return qs.filter(primary_stream_id__in=units) if units else qs.none()

def require_person(user,p,resource='participants',action='view'):
    if not scoped(user,p.edition,resource,action).filter(pk=p.pk).exists():raise PermissionDenied('This participant is outside your authorised scope.')

def full_profile(user,edition,p=None):
    if user.is_superuser:return True
    qs=Membership.objects.filter(user=user,edition=edition,active=True,role__in=['Admin','StreamOwner','Reviewer','Registration'])
    if p is not None:qs=qs.filter(Q(stream=p.primary_stream)|Q(stream__isnull=True)&~Q(role='StreamOwner'))
    return qs.exists()

def role_names(user,edition):
    if user.is_superuser:return ['Super administrator']
    return list(Membership.objects.filter(user=user,edition=edition,active=True).values_list('role',flat=True))
