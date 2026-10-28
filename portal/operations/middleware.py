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
