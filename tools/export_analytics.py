"""Allowlisted synthetic star-schema export; never use against production records."""
import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def export(db,out):
    db=Path(db)
    if not db.is_file():
        raise ValueError('Database does not exist.')
    s=sqlite3.connect(f'file:{db.resolve()}?mode=ro',uri=True);s.row_factory=sqlite3.Row
    try:
        # Fail closed; only artificial TEST contacts emitted by seed.py are accepted.
        if s.execute("SELECT count(*) FROM participants WHERE id NOT LIKE 'synthetic-person-%' OR phone NOT LIKE 'TEST-%'").fetchone()[0]:
            raise ValueError('Exporter accepts only an unmodified synthetic seed database.')
        out=Path(out);out.mkdir(parents=True,exist_ok=True)
        def write(name,fields,rows):
            with (out/name).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        rows=s.execute('''SELECT e.id,e.participant,e.edition,e.stream,e.category,e.review,e.arrived,e.registered,e.departed,d.year,
            (SELECT min(d2.year) FROM participations p2 JOIN editions d2 ON d2.id=p2.edition WHERE p2.participant=e.participant) first_year
            FROM participations e JOIN editions d ON e.edition=d.id ORDER BY e.id''').fetchall()
        fact=[dict(ParticipationKey=r['id'],ParticipantKey=hashlib.sha256(r['participant'].encode()).hexdigest()[:24],EditionKey=r['edition'],StreamKey=r['stream'],Category=r['category'],ReviewStatus=r['review'],Arrived=r['arrived'],Registered=r['registered'],Departed=r['departed'],IsFirstYear=int(r['year']==r['first_year'])) for r in rows]
        write('FactParticipation.csv',['ParticipationKey','ParticipantKey','EditionKey','StreamKey','Category','ReviewStatus','Arrived','Registered','Departed','IsFirstYear'],fact)
        write('DimEdition.csv',['EditionKey','Year','Starts','Ends'],[dict(EditionKey=r['id'],Year=r['year'],Starts=r['starts'],Ends=r['ends']) for r in s.execute('SELECT * FROM editions')])
        write('DimStream.csv',['StreamKey','Name'],[dict(StreamKey=r['id'],Name=r['name']) for r in s.execute("SELECT * FROM units WHERE kind='Stream'")])
        write('DimParticipant.csv',['ParticipantKey','State','District'],[dict(ParticipantKey=hashlib.sha256(r['id'].encode()).hexdigest()[:24],State=r['state'],District=r['district']) for r in s.execute('SELECT id,state,district FROM participants')])
        summary=dict(synthetic=True,classification='pseudonymous synthetic; not an anonymization guarantee',exported_at=datetime.now(timezone.utc).isoformat(),fact_grain='one participant per edition',participations=len(fact),participants=s.execute('SELECT count(*) FROM participants').fetchone()[0])
        (out/'refresh.json').write_text(json.dumps(summary,indent=2)+'\n')
        return summary
    finally:s.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    print(json.dumps(export(a.db,a.out)))
