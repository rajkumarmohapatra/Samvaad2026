from django.conf import settings
from django.db.models import Q
from .models import Edition
from .access import can,role_names

def editions_for(user):
    if not user.is_authenticated:return Edition.objects.none()
    if user.is_superuser:return Edition.objects.all().order_by('-year')
    return Edition.objects.filter(Q(membership__user=user,membership__active=True)|Q(participation__participant__user=user)).distinct().order_by('-year')

def current_edition(request):
    if hasattr(request,'_edition'):return request._edition
    qs=editions_for(request.user);selected=request.session.get('edition')
    request._edition=qs.filter(pk=selected).first() if selected else None
    if request._edition is None:request._edition=qs.first()
    return request._edition

def common(request):
    e=current_edition(request) if request.user.is_authenticated else None
    nav=[]
    if e:
        for name,label in [('participants','Participants'),('accommodation','Accommodation'),('transport','Transport'),('food','Food'),('kits','Kits'),('venue','Venues & sessions'),('finance','Finance'),('tickets','Helpdesk'),('assistance','Safety & assistance'),('reports','Reports')]:
            if can(request.user,e,name):nav.append((name,label))
    return {'current_edition':e,'editions':editions_for(request.user),'navigation':nav,'roles':role_names(request.user,e) if e else [],'demo_mode':settings.DEMO_MODE}
