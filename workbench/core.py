"""Executable domain rules. SQLite transactions test rules, not SharePoint behavior.

Principals are supplied by trusted local code. There is deliberately no production
authentication adapter: do not expose the acceptance workbench to a network.
"""
import csv
import hashlib
import io
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class RuleError(ValueError):
    pass


class Forbidden(PermissionError):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: tuple
    streams: tuple = ()


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS editions(id TEXT PRIMARY KEY, title TEXT NOT NULL, year INTEGER UNIQUE NOT NULL, starts TEXT NOT NULL, ends TEXT NOT NULL, closed INTEGER DEFAULT 0, CHECK(starts<=ends));
CREATE TABLE IF NOT EXISTS units(id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, kind TEXT NOT NULL DEFAULT 'Unclassified', active INTEGER DEFAULT 1, merged_into TEXT REFERENCES units(id));
CREATE TABLE IF NOT EXISTS edition_units(edition TEXT REFERENCES editions(id), unit TEXT REFERENCES units(id), PRIMARY KEY(edition,unit));
CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL, state TEXT NOT NULL, district TEXT NOT NULL DEFAULT '', community TEXT NOT NULL DEFAULT '', created TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_participant_phone ON participants(phone);
CREATE TABLE IF NOT EXISTS participations(id TEXT PRIMARY KEY, participant TEXT REFERENCES participants(id), edition TEXT REFERENCES editions(id), stream TEXT REFERENCES units(id), category TEXT NOT NULL, submitted INTEGER DEFAULT 0, review TEXT DEFAULT 'Draft', arrived INTEGER DEFAULT 0, registered INTEGER DEFAULT 0, departed INTEGER DEFAULT 0, closed INTEGER DEFAULT 0, token TEXT UNIQUE NOT NULL, version INTEGER DEFAULT 1, created TEXT NOT NULL, UNIQUE(participant,edition));
CREATE INDEX IF NOT EXISTS ix_participation_edition_stream ON participations(edition,stream);
CREATE TABLE IF NOT EXISTS assignments(participation TEXT REFERENCES participations(id), stream TEXT REFERENCES units(id), is_primary INTEGER DEFAULT 0, PRIMARY KEY(participation,stream));
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, participation TEXT, actor TEXT NOT NULL, action TEXT NOT NULL, at TEXT NOT NULL, detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS receipts(actor TEXT, request_key TEXT, payload TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(actor,request_key));
CREATE TABLE IF NOT EXISTS beds(id TEXT PRIMARY KEY, edition TEXT REFERENCES editions(id), property TEXT NOT NULL, accessible INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS stays(id TEXT PRIMARY KEY, participation TEXT REFERENCES participations(id), bed TEXT REFERENCES beds(id), checked_in TEXT NOT NULL, checked_out TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS ux_bed_active ON stays(bed) WHERE checked_out IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_participant_active ON stays(participation) WHERE checked_out IS NULL;
CREATE TABLE IF NOT EXISTS trips(id TEXT PRIMARY KEY, edition TEXT REFERENCES editions(id), title TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity>0));
CREATE TABLE IF NOT EXISTS passengers(trip TEXT REFERENCES trips(id), participation TEXT REFERENCES participations(id), PRIMARY KEY(trip,participation));
CREATE TABLE IF NOT EXISTS kit_stock(edition TEXT REFERENCES editions(id), kind TEXT, received INTEGER CHECK(received>=0), PRIMARY KEY(edition,kind));
CREATE TABLE IF NOT EXISTS kits(participation TEXT REFERENCES participations(id), kind TEXT, at TEXT NOT NULL, actor TEXT NOT NULL, PRIMARY KEY(participation,kind));
CREATE TABLE IF NOT EXISTS meal_windows(id TEXT PRIMARY KEY, edition TEXT REFERENCES editions(id), title TEXT, capacity INTEGER CHECK(capacity>0));
CREATE TABLE IF NOT EXISTS meals(window TEXT REFERENCES meal_windows(id), participation TEXT REFERENCES participations(id), at TEXT NOT NULL, PRIMARY KEY(window,participation));
CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY, participation TEXT REFERENCES participations(id), amount_paise INTEGER NOT NULL CHECK(amount_paise>0), maker TEXT NOT NULL, checker TEXT, status TEXT DEFAULT 'Requested', payment_reference TEXT, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY, participation TEXT REFERENCES participations(id), category TEXT NOT NULL, priority TEXT NOT NULL, summary TEXT NOT NULL, sensitive INTEGER NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, created TEXT NOT NULL);
"""


class Store:
    def __init__(self, path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, timeout=20, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.execute('PRAGMA journal_mode=WAL')

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except Exception:
            self.db.execute('ROLLBACK')
            raise

    def allow(self, p, *roles):
        if not set(p.roles).intersection(roles):
            raise Forbidden('Your role cannot perform this action.')

    def scope(self, p, participation):
        row = self.db.execute('SELECT * FROM participations WHERE id=?', (participation,)).fetchone()
        if not row:
            raise RuleError('Participation not found.')
        if set(p.roles) == {'StreamOwner'} and row['stream'] not in p.streams:
            raise Forbidden('This stream is outside your responsibility.')
        return row

    def editable_edition(self, edition):
        row = self.db.execute('SELECT * FROM editions WHERE id=?', (edition,)).fetchone()
        if not row or row['closed']:
            raise RuleError('Select an open event edition.')

    def audit(self, p, action, participation=None, detail=None):
        # Never pass identity, bank, health, or contact values to audit detail.
        self.db.execute('INSERT INTO audit(participation,actor,action,at,detail) VALUES(?,?,?,?,?)',
                        (participation, p.subject, action, now(), json.dumps(detail or {})))

    def once(self, p, key, payload, operation):
        if not key or len(key) > 128:
            raise RuleError('A request key of 1–128 characters is required.')
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with self.transaction():
            old = self.db.execute('SELECT * FROM receipts WHERE actor=? AND request_key=?', (p.subject, key)).fetchone()
            if old:
                if old['payload'] != digest:
                    raise RuleError('Request key was already used for different input.')
                return json.loads(old['result'])
            result = operation()
            self.db.execute('INSERT INTO receipts VALUES(?,?,?,?)', (p.subject, key, digest, json.dumps(result)))
            return result

    def configure(self, p, edition, title, year, starts, ends):
        self.allow(p, 'Admin')
        try:
            if datetime.fromisoformat(starts) > datetime.fromisoformat(ends):
                raise ValueError()
        except ValueError:
            raise RuleError('Provide valid dates in chronological order.')
        with self.transaction():
            if self.db.execute('SELECT 1 FROM editions WHERE id=?', (edition,)).fetchone():
                raise RuleError('Edition already exists; historical dates are immutable here.')
            self.db.execute('INSERT INTO editions(id,title,year,starts,ends) VALUES(?,?,?,?,?)', (edition,title,year,starts,ends))
            self.audit(p, 'edition.created', detail={'edition': edition})

    def add_unit(self, p, name, kind='Unclassified'):
        self.allow(p, 'Admin')
        if kind not in ('Unclassified','Stream','Team','Program') or not name.strip():
            raise RuleError('Choose a valid unit name and type.')
        with self.transaction():
            ident = uid()
            self.db.execute('INSERT INTO units(id,name,kind) VALUES(?,?,?)', (ident,name.strip(),kind))
            self.audit(p, 'unit.created', detail={'unit': ident})
            return ident

    def configure_unit(self, p, ident, name=None, kind=None, active=None, merge_into=None):
        self.allow(p, 'Admin')
        with self.transaction():
            row = self.db.execute('SELECT * FROM units WHERE id=?', (ident,)).fetchone()
            if not row:
                raise RuleError('Unit not found.')
            if merge_into:
                target = self.db.execute('SELECT * FROM units WHERE id=?', (merge_into,)).fetchone()
                if not target or not target['active'] or merge_into == ident:
                    raise RuleError('Choose another active unit as merge target.')
                # Keep existing edition assignments intact; merge affects future selection only.
                active = 0
            new_kind = kind or row['kind']
            if new_kind not in ('Unclassified','Stream','Team','Program'):
                raise RuleError('Invalid unit type.')
            self.db.execute('UPDATE units SET name=?,kind=?,active=?,merged_into=? WHERE id=?',
                            (name or row['name'],new_kind,row['active'] if active is None else int(active),merge_into,ident))
            self.audit(p, 'unit.configured', detail={'unit': ident, 'merge_target': merge_into})

    @staticmethod
    def validate(data):
        errors = []
        for field in ('name','phone','state','edition','stream','category'):
            if not str(data.get(field,'')).strip():
                errors.append(f'{field} is required')
        phone = re.sub(r'[\s()+-]', '', str(data.get('phone','')))
        if not re.fullmatch(r'\d{10,15}', phone):
            errors.append('phone must contain 10–15 digits')
        if len(str(data.get('name',''))) > 150:
            errors.append('name exceeds 150 characters')
        return errors, phone

    def nominate(self, p, key, data):
        self.allow(p, 'Admin','StreamOwner')
        errors, phone = self.validate(data)
        if errors:
            raise RuleError('; '.join(errors))
        if 'Admin' not in p.roles and data['stream'] not in p.streams:
            raise Forbidden('You can nominate only to your assigned streams.')
        def op():
            self.editable_edition(data['edition'])
            unit = self.db.execute('SELECT kind,active FROM units WHERE id=?', (data['stream'],)).fetchone()
            if not unit or not unit['active'] or unit['kind'] != 'Stream':
                raise RuleError('Select an active, classified stream.')
            if not self.db.execute('SELECT 1 FROM edition_units WHERE edition=? AND unit=?', (data['edition'],data['stream'])).fetchone():
                raise RuleError('Stream is not enabled for this edition.')
            # Shared family phones are valid. Exact name+phone is a likely duplicate,
            # not a definitive identity match. Explicit existing master ID is required for reuse.
            existing = data.get('participant_id')
            if existing:
                master = self.db.execute('SELECT * FROM participants WHERE id=?', (existing,)).fetchone()
                if not master or master['name'].casefold() != data['name'].strip().casefold() or master['phone'] != phone:
                    raise RuleError('Existing participant identity does not match; ask the reviewer.')
                if 'Admin' not in p.roles and not self.db.execute('SELECT 1 FROM participations WHERE participant=? AND stream IN (%s)' % ','.join('?' for _ in p.streams), (existing,*p.streams)).fetchone():
                    raise Forbidden('Existing master must already belong to an authorized stream.')
                master_id = existing
            else:
                if self.db.execute('SELECT 1 FROM participants WHERE lower(name)=lower(?) AND phone=?', (data['name'].strip(),phone)).fetchone():
                    raise RuleError('Likely duplicate. Ask a reviewer to confirm reuse of the existing master.')
                master_id = uid()
                self.db.execute('INSERT INTO participants VALUES(?,?,?,?,?,?,?)', (master_id,data['name'].strip(),phone,data['state'].strip(),data.get('district',''),data.get('community',''),now()))
            ident = uid()
            try:
                self.db.execute('INSERT INTO participations(id,participant,edition,stream,category,token,created) VALUES(?,?,?,?,?,?,?)', (ident,master_id,data['edition'],data['stream'],data['category'],uid(),now()))
            except sqlite3.IntegrityError:
                raise RuleError('This participant already has a record for this edition.')
            self.db.execute('INSERT INTO assignments VALUES(?,?,1)', (ident,data['stream']))
            self.audit(p, 'nomination.created', ident)
            return {'id': ident, 'participant_id':master_id}
        return self.once(p, key, data, op)

    def transition(self, p, key, ident, action, version):
        rules = {'submit':(('Admin','StreamOwner'),'review','Submitted'),
                 'approve':(('Reviewer',),'review','Approved'), 'reject':(('Reviewer',),'review','Rejected'),
                 'arrive':(('Accommodation',),'arrived',1), 'register':(('Registration',),'registered',1),
                 'depart':(('Accommodation','Transport'),'departed',1), 'close':(('Admin',),'closed',1)}
        if action not in rules:
            raise RuleError('Unknown transition.')
        roles, field, value = rules[action]
        self.allow(p,*roles)
        def op():
            row = self.scope(p,ident)
            self.editable_edition(row['edition'])
            if row['closed'] or row['version'] != version:
                raise RuleError('Record changed or is closed. Refresh before continuing.')
            if action == 'submit' and row['review'] not in ('Draft','Rejected'):
                raise RuleError('Only draft or rejected nominations can be submitted.')
            if action in ('approve','reject') and row['review'] != 'Submitted':
                raise RuleError('Submit the nomination before review.')
            if action in ('arrive','register') and row['review'] != 'Approved':
                raise RuleError('The nomination must be approved first.')
            if action in ('arrive','register') and row['departed']:
                raise RuleError('This participant has departed. Ask a reviewer to resolve the record.')
            if action == 'register' and row['registered']:
                raise RuleError('Registration already completed.')
            if action == 'arrive' and row['arrived']:
                raise RuleError('Arrival already confirmed.')
            if action == 'depart' and (not row['arrived'] or row['departed']):
                raise RuleError('Confirm arrival before departure, and depart only once.')
            if action in ('depart','close') and self.db.execute('SELECT 1 FROM stays WHERE participation=? AND checked_out IS NULL',(ident,)).fetchone():
                raise RuleError('Check out of accommodation first.')
            if action == 'close' and not row['departed']:
                raise RuleError('Confirm departure before closing participation.')
            self.db.execute(f'UPDATE participations SET {field}=?,version=version+1 WHERE id=?', (value,ident))
            self.audit(p, action, ident)
            return {'id':ident,'version':version+1}
        return self.once(p,key,{'id':ident,'action':action,'version':version},op)

    def search(self, p, edition, query='', limit=50, offset=0):
        self.allow(p,'Admin','StreamOwner','Reviewer','Registration','Accommodation','Transport','Kits','Food','Finance','Leadership','Helpdesk','Venue','Safety','Analytics')
        if not 1 <= limit <= 100 or offset < 0 or len(query)>150:
            raise RuleError('Invalid search pagination.')
        where = ['e.edition=?']
        args = [edition]
        if not set(p.roles).difference({'StreamOwner'}):
            if not p.streams:
                return {'rows':[], 'total':0}
            where.append('e.stream IN (%s)' % ','.join('?' for _ in p.streams))
            args.extend(p.streams)
        if query:
            where.append('(p.name LIKE ? ESCAPE \'\\\' OR p.phone=? OR e.id=? OR e.token=?)')
            escaped = query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            args.extend([escaped+'%',query,query,query])
        predicate=' AND '.join(where)
        total=self.db.execute('SELECT count(*) FROM participations e JOIN participants p ON p.id=e.participant WHERE '+predicate,args).fetchone()[0]
        # Finance/leadership/analytics/volunteers receive no phone or community fields.
        contact = bool(set(p.roles).intersection({'Admin','StreamOwner','Reviewer','Registration'}))
        columns='e.*,p.name'+(',p.phone,p.state,p.district,p.community' if contact else '')
        rows=self.db.execute('SELECT '+columns+' FROM participations e JOIN participants p ON p.id=e.participant WHERE '+predicate+' ORDER BY e.id LIMIT ? OFFSET ?',(*args,limit,offset)).fetchall()
        return {'rows':[dict(r) for r in rows],'total':total}

    def dashboard(self,p,edition):
        self.allow(p,'Admin','Leadership','Analytics','Reviewer','Registration','Accommodation','StreamOwner','Transport','Food','Kits','Finance','Helpdesk','Venue','Safety')
        where='edition=?'; args=[edition]
        if set(p.roles)=={'StreamOwner'}:
            if not p.streams:
                return dict(total=0,approved=0,arrived=0,registered=0,departed=0,pending=0)
            where+=' AND stream IN (%s)' % ','.join('?' for _ in p.streams); args.extend(p.streams)
        return dict(self.db.execute("SELECT count(*) total,coalesce(sum(review='Approved'),0) approved,coalesce(sum(arrived),0) arrived,coalesce(sum(registered),0) registered,coalesce(sum(departed),0) departed,coalesce(sum(review='Submitted'),0) pending FROM participations WHERE "+where,args).fetchone())

    def allocate_bed(self,p,key,ident,bed,needs_accessible=False):
        self.allow(p,'Accommodation')
        def op():
            row=self.scope(p,ident); self.editable_edition(row['edition'])
            target=self.db.execute('SELECT * FROM beds WHERE id=?',(bed,)).fetchone()
            if not target or target['edition']!=row['edition'] or (needs_accessible and not target['accessible']):
                raise RuleError('Bed is incompatible with edition or accessibility requirements.')
            if not row['arrived'] or row['departed'] or row['closed']:
                raise RuleError('An active arrival is required for check-in.')
            try:
                self.db.execute('INSERT INTO stays VALUES(?,?,?,?,NULL)',(uid(),ident,bed,now()))
            except sqlite3.IntegrityError:
                raise RuleError('Bed or participant already has an active allocation.')
            self.audit(p,'accommodation.checkin',ident,{'bed':bed})
            return {'allocated':True}
        return self.once(p,key,{'id':ident,'bed':bed,'accessible':needs_accessible},op)

    def checkout(self,p,key,ident):
        self.allow(p,'Accommodation')
        def op():
            row=self.scope(p,ident); self.editable_edition(row['edition'])
            if self.db.execute('UPDATE stays SET checked_out=? WHERE participation=? AND checked_out IS NULL',(now(),ident)).rowcount!=1:
                raise RuleError('No active stay found.')
            self.audit(p,'accommodation.checkout',ident)
            return {'checked_out':True}
        return self.once(p,key,{'id':ident},op)

    def allocate_trip(self,p,key,ident,trip):
        self.allow(p,'Transport')
        def op():
            row=self.scope(p,ident); self.editable_edition(row['edition'])
            t=self.db.execute('SELECT * FROM trips WHERE id=?',(trip,)).fetchone()
            if not t or t['edition']!=row['edition'] or row['review']!='Approved' or row['closed']:
                raise RuleError('Trip and approved participation must belong to the same open edition.')
            if self.db.execute('SELECT count(*) FROM passengers WHERE trip=?',(trip,)).fetchone()[0]>=t['capacity']:
                raise RuleError('Vehicle capacity is full.')
            try:
                self.db.execute('INSERT INTO passengers VALUES(?,?)',(trip,ident))
            except sqlite3.IntegrityError:
                raise RuleError('Passenger is already allocated.')
            self.audit(p,'transport.allocated',ident,{'trip':trip})
            return {'allocated':True}
        return self.once(p,key,{'id':ident,'trip':trip},op)

    def issue(self,p,key,ident,kind,meal=False):
        self.allow(p,'Food' if meal else 'Kits')
        def op():
            row=self.scope(p,ident); self.editable_edition(row['edition'])
            if not row['registered'] or row['departed'] or row['closed']:
                raise RuleError('An active registration is required.')
            if meal:
                stock=self.db.execute('SELECT capacity FROM meal_windows WHERE id=? AND edition=?',(kind,row['edition'])).fetchone()
                used=self.db.execute('SELECT count(*) FROM meals WHERE window=?',(kind,)).fetchone()[0]
            else:
                stock=self.db.execute('SELECT received FROM kit_stock WHERE edition=? AND kind=?',(row['edition'],kind)).fetchone()
                used=self.db.execute('SELECT count(*) FROM kits k JOIN participations p ON p.id=k.participation WHERE p.edition=? AND kind=?',(row['edition'],kind)).fetchone()[0]
            if not stock or used>=stock[0]:
                raise RuleError('No available meal capacity.' if meal else 'Kit stock is exhausted.')
            try:
                if meal:
                    self.db.execute('INSERT INTO meals VALUES(?,?,?)',(kind,ident,now()))
                else:
                    self.db.execute('INSERT INTO kits VALUES(?,?,?,?)',(ident,kind,now(),p.subject))
            except sqlite3.IntegrityError:
                raise RuleError('This service has already been issued.')
            self.audit(p,'meal.served' if meal else 'kit.issued',ident,{'kind':kind})
            return {'issued':True}
        return self.once(p,key,{'id':ident,'kind':kind,'meal':meal},op)

    def claim(self,p,key,ident,amount_paise):
        self.allow(p,'Finance')
        if type(amount_paise) is not int or not 0<amount_paise<=100000000:
            raise RuleError('Amount must be positive integer paise within the configured limit.')
        def op():
            row=self.scope(p,ident); self.editable_edition(row['edition'])
            if row['review']!='Approved':
                raise RuleError('Approved participation is required.')
            claim_id=uid()
            self.db.execute('INSERT INTO claims(id,participation,amount_paise,maker,created) VALUES(?,?,?,?,?)',(claim_id,ident,amount_paise,p.subject,now()))
            self.audit(p,'finance.requested',ident,{'claim':claim_id})
            return {'id':claim_id}
        return self.once(p,key,{'id':ident,'amount_paise':amount_paise},op)

    def approve_claim(self,p,key,claim):
        self.allow(p,'FinanceChecker')
        def op():
            row=self.db.execute('SELECT * FROM claims WHERE id=?',(claim,)).fetchone()
            if not row or row['status']!='Requested' or row['maker']==p.subject:
                raise RuleError('Another authorized person must approve an outstanding request.')
            participation=self.scope(p,row['participation']); self.editable_edition(participation['edition'])
            self.db.execute("UPDATE claims SET checker=?,status='Approved' WHERE id=?",(p.subject,claim))
            self.audit(p,'finance.approved',row['participation'],{'claim':claim})
            return {'approved':True}
        return self.once(p,key,{'claim':claim},op)

    def record_payment(self,p,key,claim,reference):
        self.allow(p,'FinancePayer')
        if not re.fullmatch(r'[A-Za-z0-9/-]{4,80}',reference):
            raise RuleError('Provide the external finance payment reference.')
        def op():
            row=self.db.execute('SELECT * FROM claims WHERE id=?',(claim,)).fetchone()
            if not row or row['status']!='Approved' or p.subject in (row['maker'],row['checker']):
                raise RuleError('Payment recording requires a distinct payer and approved claim.')
            participation=self.scope(p,row['participation']); self.editable_edition(participation['edition'])
            self.db.execute("UPDATE claims SET payment_reference=?,status='Recorded' WHERE id=?",(reference,claim))
            self.audit(p,'finance.external_payment_recorded',row['participation'],{'claim':claim})
            return {'recorded':True,'money_transferred_by_application':False}
        return self.once(p,key,{'claim':claim,'reference':reference},op)

    def import_preview(self,p,text):
        self.allow(p,'Admin','StreamOwner')
        if len(text.encode())>2_000_000:
            raise RuleError('Import is limited to 2 MB; split the file.')
        reader=csv.DictReader(io.StringIO(text))
        required={'name','phone','state','edition','stream','category'}
        if not required.issubset(reader.fieldnames or []):
            raise RuleError('Import headers must include '+', '.join(sorted(required)))
        result=[]; seen=set()
        for n,row in enumerate(reader,2):
            if n>5001:
                raise RuleError('Maximum 5,000 rows per preview.')
            errors,phone=self.validate(row)
            fingerprint=(str(row.get('name','')).strip().casefold(),phone,row.get('edition'))
            if fingerprint in seen:
                errors.append('duplicate within file')
            seen.add(fingerprint)
            if 'Admin' not in p.roles and row.get('stream') not in p.streams:
                errors.append('stream is not authorized')
            if self.db.execute('SELECT 1 FROM participants WHERE lower(name)=lower(?) AND phone=?',(row.get('name','').strip(),phone)).fetchone() and not row.get('participant_id'):
                errors.append('likely duplicate in existing records; reviewer must confirm identity')
            edition=self.db.execute('SELECT closed FROM editions WHERE id=?',(row.get('edition'),)).fetchone()
            if not edition or edition['closed']:
                errors.append('edition is unavailable or closed')
            if not self.db.execute("SELECT 1 FROM edition_units e JOIN units u ON e.unit=u.id WHERE e.edition=? AND e.unit=? AND u.kind='Stream' AND u.active=1",(row.get('edition'),row.get('stream'))).fetchone():
                errors.append('stream is not active for the edition')
            result.append({'row':n,'data':row,'errors':errors})
        return result

    def import_commit(self,p,batch,text):
        if not isinstance(batch,str) or not 1 <= len(batch) <= 110:
            raise RuleError('Import batch key must contain 1–110 characters.')
        rows=self.import_preview(p,text)
        results=[]
        for r in rows:
            cached=self.db.execute('SELECT 1 FROM receipts WHERE actor=? AND request_key=?',(p.subject,f'{batch}:{r["row"]}')).fetchone()
            if not r['errors'] or cached:
                try:
                    r['result']=self.nominate(p,f'{batch}:{r["row"]}',r['data'])
                    r['errors']=[]
                except (RuleError,Forbidden) as e:
                    r['errors'].append(str(e))
            results.append(r)
        return results
