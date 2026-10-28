import csv
import json
import tempfile
import unittest
from pathlib import Path
from tools.seed import seed
from tools.export_analytics import export
from workbench.core import Store

ROOT=Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_json_and_schema_keys(self):
        for p in ROOT.rglob('*.json'):
            if 'generated' not in p.parts:
                self.assertIsNotNone(json.loads(p.read_text()),str(p))
        entities=json.loads((ROOT/'data-model/entities.json').read_text())
        self.assertEqual(len({e['name'] for e in entities}),len(entities))
        for e in entities:
            keys=[f['name'] for f in e['fields']]
            self.assertEqual(len(set(keys)),len(keys))
            self.assertIn('RecordKey',keys)
    def test_exact_seed_names_and_no_inferred_classification(self):
        units=json.loads((ROOT/'data-model/initial-units.json').read_text());self.assertEqual(len(units),40)
        self.assertEqual(units[4]['name'],'Colors of Jharkhhand')
        self.assertEqual(units[20]['name'],'NOTE TAKING')
        self.assertTrue(all(u['kind']=='Unclassified' for u in units))
    def test_core_does_not_provision_bank_or_identity(self):
        core=json.loads((ROOT/'sharepoint/core-lists.json').read_text())
        self.assertNotIn('RestrictedBankDetails',[e['name'] for e in core])
        self.assertNotIn('IdentityVerification',[e['name'] for e in core])
    def test_synthetic_export_grain_and_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'seed.db';seed(db);out=Path(tmp)/'export';result=export(db,out)
            self.assertEqual(result['participations'],3600)
            with (out/'FactParticipation.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len({r['ParticipationKey'] for r in rows}),3600)
            self.assertEqual(sum(r['EditionKey']=='edition-2026' for r in rows),3000)
            self.assertEqual(sum(r['EditionKey']=='edition-2026' and r['IsFirstYear']=='0' for r in rows),600)
            for path in out.glob('*.csv'):
                with path.open() as f: headers=next(csv.reader(f))
                for col in headers:
                    self.assertNotIn(col.lower(),('phone','email','fullname','community','accountnumber','ifsc','documentreference','emergencycontact','token'))
            s=Store(db);s.db.execute("UPDATE participants SET phone='0000000000' WHERE id='synthetic-person-00000'");s.close()
            with self.assertRaises(ValueError):export(db,out)


if __name__=='__main__':unittest.main()
