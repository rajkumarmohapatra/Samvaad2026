from contextvars import ContextVar
from django.db.models import Q
from .models import Notification
from .access import can

activity_request=ContextVar('samvaad_activity_request',default=None)

def activity(user,edition,action,p=None,severity='info',message=None,request=None,record_id=None):
    request=request or activity_request.get()
    page=getattr(getattr(request,'resolver_match',None),'view_name','') if request else ''
    match=getattr(request,'resolver_match',None) if request else None
    path=('/'+match.route) if match else '(system)'
    if not page and request:path='(unmatched route)'
    # Never include query strings, form values, free-text notes, document or bank numbers.
    summary=message or action.replace('.',' ').replace('_',' ').capitalize()
    extra={'id':record_id} if record_id else {}
    return Notification.objects.create(**extra,actor=user if user and user.is_authenticated else None,edition=edition,participation=p,action=action,severity=severity,message=summary[:240],page_name=page[:120],page_path=path[:250])

def flag_validation(request,error=None):
    request._activity_validation_failed=True
    text=str(error).casefold() if error else ''
    request._activity_alert_message='Validation failed. Correct the highlighted fields and retry.'
    for terms,message in [(('capacity','full'),'Capacity limit reached. Review available resources.'),(('stock',),'Stock validation failed. Review inventory availability.'),(('overlap',),'Conflicting allocation detected. Review existing reservations.'),(('duplicate','already used','already exists'),'Duplicate record or request detected. Review before retrying.'),(('phone','email'),'Contact-format validation failed.'),(('date','start','end'),'Date or time validation failed.'),(('identity','aadhaar','pan format'),'Restricted identity validation failed.'),(('amount','payment','bank'),'Restricted finance validation failed.')]:
        if any(term in text for term in terms):
            request._activity_alert_message=message;break

def visible_notifications(user,edition=None):
    qs=Notification.objects.all()
    if user.is_superuser:
        return qs.filter(Q(edition=edition)|Q(edition__isnull=True)) if edition else qs
    if edition is None:return qs.filter(actor=user)
    if can(user,edition,'notifications','view'):return qs.filter(edition=edition)
    return qs.filter(actor=user).filter(Q(edition=edition)|Q(edition__isnull=True))
