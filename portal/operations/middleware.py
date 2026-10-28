class PrivateResponseMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        if not request.path.startswith('/static/'):
            response['Cache-Control']='private, no-store'
            # Admin uses its own bundled JS/widgets; other screens have no inline scripts.
            if not request.path.startswith('/admin/'):
                response['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
            response['Referrer-Policy']='same-origin'
        return response

class RequestActivityMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        from .notifications import activity_request,activity
        before=request.user if request.user.is_authenticated else None
        token=activity_request.set(request)
        try:
            response=self.get_response(request)
            context=getattr(response,'context_data',None) or {}
            form=context.get('form') or getattr(context.get('adminform'),'form',None)
            if request.method=='POST' and form is not None and form.errors:
                from .notifications import flag_validation
                flag_validation(request,form.errors)
            actor=request.user if request.user.is_authenticated else before
            name=getattr(getattr(request,'resolver_match',None),'view_name','')
            skip=request.path.startswith('/static/') or request.path=='/healthz'
            if not skip and (actor or (request.method=='POST' and name in ['login','setup'])):
                from .context import current_edition
                edition=current_edition(request) if request.user.is_authenticated else None
                severity='info';action='page.viewed' if request.method=='GET' else 'page.action'
                if response.status_code>=500:severity='error';action='request.failed'
                elif response.status_code in [400,403,404,429]:severity='warning';action='request.denied'
                elif getattr(request,'_activity_validation_failed',False):severity='warning';action='validation.failed'
                elif name=='login' and request.method=='POST':
                    action='account.signed_in' if request.user.is_authenticated else 'account.sign_in_failed'
                    severity='info' if request.user.is_authenticated else 'warning'
                elif name=='logout':action='account.signed_out'
                activity(actor,edition,action,severity=severity,message=getattr(request,'_activity_alert_message',None) if action=='validation.failed' else None,request=request)
            return response
        finally:activity_request.reset(token)
