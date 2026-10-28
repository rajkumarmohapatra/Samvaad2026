"""Loopback-only synthetic acceptance UI. No production authentication is provided."""
import argparse
import hmac
import json
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from .core import Store, Principal, RuleError, Forbidden, uid

STATIC=Path(__file__).parent/'static'


def run(path, port):
    csrf=secrets.token_urlsafe(32)
    # Switching these personas is intentionally permitted only in this local test harness.
    roles={'owner':('StreamOwner',),'reviewer':('Reviewer',),'registration':('Registration',),
           'accommodation':('Accommodation',),'transport':('Transport',),'kits':('Kits',),
           'food':('Food',),'leadership':('Leadership',),'admin':('Admin',)}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass  # No participant names, search strings or request bodies in HTTP logs.

        def send(self,status,data,mime='application/json'):
            content=json.dumps(data).encode() if mime=='application/json' else data
            self.send_response(status)
            self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(content)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers();self.wfile.write(content)

        def handle_request(self,post=False):
            # Prevent DNS rebinding and cross-origin access to this local-only server.
            if self.headers.get('Host')!=f'127.0.0.1:{port}':
                return self.send(403,{'error':'Use the exact loopback URL printed in the terminal.'})
            route=urlparse(self.path)
            if not post and route.path in ('/','/app.js','/style.css'):
                file={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[route.path]
                return self.send(200,(STATIC/file).read_bytes(),{'/':'text/html; charset=utf-8','/app.js':'text/javascript','/style.css':'text/css'}[route.path])
            if post and (not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),csrf) or self.headers.get('Origin')!=f'http://127.0.0.1:{port}'):
                return self.send(403,{'error':'Refresh the page before submitting.'})
            s=Store(path)
            try:
                if post:
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=2_100_000: raise RuleError('Request is empty or too large.')
                    data=json.loads(self.rfile.read(length)); params=data
                else:
                    params={k:v[0] for k,v in parse_qs(route.query).items()}
                role=params.get('persona','owner')
                if role not in roles: raise Forbidden('Unknown local persona.')
                streams=tuple(r['id'] for r in s.db.execute("SELECT id FROM units WHERE kind='Stream' AND active=1 ORDER BY name LIMIT 1"))
                p=Principal('local-'+role,roles[role],streams)
                if route.path=='/api/config' and not post:
                    result={'csrf':csrf,'editions':[dict(r) for r in s.db.execute('SELECT * FROM editions ORDER BY year DESC')],
                            'streams':[dict(r) for r in s.db.execute("SELECT * FROM units WHERE kind='Stream' AND active=1 ORDER BY name")],
                            'owner_streams':streams,'personas':list(roles)}
                elif route.path=='/api/dashboard' and not post:
                    result=s.dashboard(p,params['edition'])
                elif route.path=='/api/search' and not post:
                    result=s.search(p,params['edition'],params.get('q',''),offset=int(params.get('offset','0')))
                elif route.path=='/api/timeline' and not post:
                    s.allow(p,'Admin','StreamOwner','Reviewer','Registration','Accommodation','Transport','Kits','Food','Leadership')
                    s.scope(p,params['id'])
                    result=[dict(r) for r in s.db.execute('SELECT actor,action,at FROM audit WHERE participation=? ORDER BY id',(params['id'],))]
                elif route.path=='/api/nominate' and post:
                    result=s.nominate(p,data['key'],data['record'])
                elif route.path=='/api/transition' and post:
                    result=s.transition(p,data['key'],data['id'],data['action'],data['version'])
                elif route.path=='/api/import-preview' and post:
                    result=s.import_preview(p,data['csv'])
                elif route.path=='/api/import-commit' and post:
                    result=s.import_commit(p,data['key'],data['csv'])
                elif route.path=='/api/resources' and not post:
                    s.allow(p,'Accommodation','Transport','Kits','Food')
                    result={'beds':[dict(r) for r in s.db.execute('SELECT id,property,accessible FROM beds WHERE edition=? AND id NOT IN(SELECT bed FROM stays WHERE checked_out IS NULL)',(params['edition'],))],
                            'trips':[dict(r) for r in s.db.execute('SELECT * FROM trips WHERE edition=?',(params['edition'],))],
                            'kits':[dict(r) for r in s.db.execute('SELECT * FROM kit_stock WHERE edition=?',(params['edition'],))],
                            'meals':[dict(r) for r in s.db.execute('SELECT * FROM meal_windows WHERE edition=?',(params['edition'],))]}
                elif route.path=='/api/service' and post:
                    action=data['action']
                    if action=='bed': result=s.allocate_bed(p,data['key'],data['id'],data['resource'])
                    elif action=='checkout': result=s.checkout(p,data['key'],data['id'])
                    elif action=='trip': result=s.allocate_trip(p,data['key'],data['id'],data['resource'])
                    elif action in ('kit','meal'): result=s.issue(p,data['key'],data['id'],data['resource'],meal=action=='meal')
                    else: raise RuleError('Unknown service action.')
                elif route.path=='/api/unit' and post:
                    result={'id':s.add_unit(p,data['name'],data['kind'])}
                elif route.path=='/api/edition' and post:
                    s.configure(p,uid(),data['title'],int(data['year']),data['starts'],data['ends']);result={'created':True}
                else:
                    return self.send(404,{'error':'Route not found.'})
                return self.send(200,result)
            except Forbidden as e: self.send(403,{'error':str(e)})
            except (RuleError,ValueError,KeyError,TypeError) as e: self.send(400,{'error':str(e)})
            except Exception: self.send(500,{'error':'Operation failed. No partial changes were committed; refresh and retry.'})
            finally: s.close()

        def do_GET(self): self.handle_request()
        def do_POST(self): self.handle_request(True)

    server=HTTPServer(('127.0.0.1',port),Handler)
    print(f'SYNTHETIC LOCAL WORKBENCH ONLY: http://127.0.0.1:{port}',flush=True)
    server.serve_forever()

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('--db',default='test-data/generated/synthetic.db'); a.add_argument('--port',type=int,default=8765);args=a.parse_args()
    if not Path(args.db).is_file(): sys.exit('Generate synthetic data first: python3 tools/seed.py')
    run(args.db,args.port)
