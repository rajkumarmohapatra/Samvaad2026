"""Generate >=3,000 synthetic current-year records plus reusable historical masters."""
import argparse
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workbench.core import Store, Principal, now, uid


def seed(path, count=3000):
    if count < 3000:
        raise ValueError('Acceptance dataset requires at least 3,000 current-year records.')
    if Path(path).exists():
        raise ValueError('Refusing to overwrite an existing database. Choose a new path.')
    s=Store(path); admin=Principal('synthetic-admin',('Admin',))
    for year in (2025,2026):
        s.configure(admin,f'edition-{year}',f'Sambad {year} — synthetic',year,f'{year}-11-15',f'{year}-11-19')
    units=json.loads((Path(__file__).resolve().parents[1]/'data-model/initial-units.json').read_text())
    for unit in units:
        ident=s.add_unit(admin,unit['name'])
        # Demonstration classification only, not an assertion about Sambad governance.
        if unit['name'] in ('Tribal Artisans','Tribal Cuisine','Tribal Healers','Tribal Sports'):
            s.configure_unit(admin,ident,kind='Stream')
    streams=[r['id'] for r in s.db.execute("SELECT id FROM units WHERE kind='Stream' ORDER BY name")]
    with s.transaction():
        for edition in ('edition-2025','edition-2026'):
            for stream in streams: s.db.execute('INSERT INTO edition_units VALUES(?,?)',(edition,stream))
        for n in range(count):
            master=f'synthetic-person-{n:05}'
            # Deliberately non-dialable synthetic contact strings, not real test phone numbers.
            # Direct generator bypasses user-entry digit validation; form tests use artificial digits.
            s.db.execute('INSERT INTO participants VALUES(?,?,?,?,?,?,?)',(master,f'Synthetic Participant {n:05}',f'TEST-{n:07}',('Jharkhand','Odisha','Chhattisgarh','West Bengal')[n%4],f'Synthetic District {n%20}','Not supplied',now()))
            years=(2025,2026) if n<600 else (2026,)
            for year in years:
                ident=f'synthetic-{year}-{n:05}'
                review=('Draft','Submitted','Approved','Approved','Approved')[n%5]
                arrived=int(review=='Approved' and n%3==0)
                registered=int(review=='Approved' and n%4==0)
                s.db.execute('INSERT INTO participations(id,participant,edition,stream,category,review,arrived,registered,token,created) VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,master,f'edition-{year}',streams[n%len(streams)],'Delegate',review,arrived,registered,uid(),now()))
                s.db.execute('INSERT INTO assignments VALUES(?,?,1)',(ident,streams[n%len(streams)]))
        for n in range(100): s.db.execute('INSERT INTO beds VALUES(?,?,?,?)',(f'bed-{n:03}','edition-2026',f'Synthetic Property {n//25}',int(n%10==0)))
        s.db.execute('INSERT INTO trips VALUES(?,?,?,?)',('trip-demo','edition-2026','Synthetic station pickup',20))
        s.db.execute('INSERT INTO kit_stock VALUES(?,?,?)',('edition-2026','Standard',3000))
        s.db.execute('INSERT INTO meal_windows VALUES(?,?,?,?)',('lunch-demo','edition-2026','Synthetic day-one lunch',3000))
        s.db.execute("UPDATE editions SET closed=1 WHERE id='edition-2025'")
    s.close()
    return {'participants':count,'participations':count+600,'years':[2025,2026]}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--db',default='test-data/generated/synthetic.db');p.add_argument('--count',type=int,default=3000);a=p.parse_args()
    Path(a.db).parent.mkdir(parents=True,exist_ok=True)
    print(json.dumps(seed(a.db,a.count)))
