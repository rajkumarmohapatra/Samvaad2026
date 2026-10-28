import concurrent.futures
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from workbench.core import Store, Principal, RuleError, Forbidden
from tools.seed import seed


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.db';self.s=Store(self.path)
        self.admin=Principal('admin',('Admin',));self.owner=Principal('owner',('StreamOwner',),('a',));self.other=Principal('other',('StreamOwner',),('b',))
        self.review=Principal('review',('Reviewer',));self.reg=Principal('reg',('Registration',));self.accom=Principal('beds',('Accommodation',));self.transport=Principal('transport',('Transport',))
        self.s.configure(self.admin,'y','Sambad test',2026,'2026-11-15','2026-11-19')
        self.s.db.execute("INSERT INTO units(id,name,kind) VALUES('a','A','Stream'),('b','B','Stream')")
        self.s.db.execute("INSERT INTO edition_units VALUES('y','a'),('y','b')")
        self.data=dict(name='Synthetic Test',phone='0000000000',state='Test',edition='y',stream='a',category='Delegate')

    def tearDown(self):self.s.close();self.tmp.cleanup()
    def person(self,n=0):
        return self.s.nominate(self.owner,f'n{n}',{**self.data,'name':f'Synthetic {n}','phone':f'{n:010}'})['id']
    def action(self,id,action,p):
        v=self.s.db.execute('SELECT version FROM participations WHERE id=?',(id,)).fetchone()[0]
        return self.s.transition(p,f'{action}-{id}-{v}',id,action,v)
    def approved(self,n=0):
        id=self.person(n);self.action(id,'submit',self.owner);self.action(id,'approve',self.review);return id
    def arrived(self,n=0):
        id=self.approved(n);self.action(id,'arrive',self.accom);return id
    def registered(self,n=0):
        id=self.approved(n);self.action(id,'register',self.reg);return id

    def test_nomination_retry_is_idempotent(self):
        a=self.s.nominate(self.owner,'retry',self.data);b=self.s.nominate(self.owner,'retry',self.data)
        self.assertEqual(a,b);self.assertEqual(self.s.dashboard(self.owner,'y')['total'],1)
    def test_retry_key_cannot_change_payload(self):
        self.s.nominate(self.owner,'retry',self.data)
        with self.assertRaises(RuleError):self.s.nominate(self.owner,'retry',{**self.data,'name':'Different'})
    def test_unknown_role_cannot_read(self):
        with self.assertRaises(Forbidden):self.s.search(Principal('unknown',()),'y')
    def test_cross_stream_write_denied(self):
        with self.assertRaises(Forbidden):self.s.nominate(self.other,'n',self.data)
    def test_cross_stream_read_denied(self):
        id=self.person();self.assertEqual(self.s.search(self.other,'y')['total'],0)
        with self.assertRaises(Forbidden):self.s.scope(self.other,id)
    def test_owner_cannot_approve(self):
        id=self.person();self.action(id,'submit',self.owner)
        with self.assertRaises(Forbidden):self.action(id,'approve',self.owner)
    def test_approval_requires_submission(self):
        with self.assertRaises(RuleError):self.action(self.person(),'approve',self.review)
    def test_registration_does_not_require_accommodation(self):
        id=self.registered();self.assertEqual(self.s.scope(self.reg,id)['registered'],1);self.assertEqual(self.s.scope(self.reg,id)['arrived'],0)
    def test_stale_version_rejected(self):
        id=self.person();self.action(id,'submit',self.owner)
        with self.assertRaises(RuleError):self.s.transition(self.review,'stale',id,'approve',1)
    def test_transition_retry(self):
        id=self.person();a=self.s.transition(self.owner,'t',id,'submit',1);b=self.s.transition(self.owner,'t',id,'submit',1);self.assertEqual(a,b)
    def test_likely_duplicate_requires_review(self):
        self.s.nominate(self.owner,'a',self.data)
        with self.assertRaises(RuleError):self.s.nominate(self.owner,'b',self.data)
    def test_shared_phone_not_forced_merge(self):
        self.s.nominate(self.owner,'a',self.data);self.s.nominate(self.owner,'b',{**self.data,'name':'Different Person'})
        self.assertEqual(self.s.dashboard(self.owner,'y')['total'],2)
    def test_historical_reuse(self):
        a=self.s.nominate(self.owner,'a',self.data);self.s.configure(self.admin,'z','Next edition',2027,'2027-11-15','2027-11-19');self.s.db.execute("INSERT INTO edition_units VALUES('z','a')")
        b=self.s.nominate(self.owner,'b',{**self.data,'edition':'z','participant_id':a['participant_id']})
        self.assertEqual(a['participant_id'],b['participant_id']);self.assertNotEqual(a['id'],b['id'])
    def test_closed_edition_cannot_change(self):
        id=self.person();self.s.db.execute("UPDATE editions SET closed=1 WHERE id='y'")
        with self.assertRaises(RuleError):self.action(id,'submit',self.owner)
    def test_unit_merge_preserves_history(self):
        id=self.person();self.s.configure_unit(self.admin,'a',merge_into='b')
        self.assertEqual(self.s.scope(self.owner,id)['stream'],'a')
        with self.assertRaises(RuleError):self.person(1)
    def test_duplicate_bed(self):
        a=self.arrived();b=self.arrived(1);self.s.db.execute("INSERT INTO beds VALUES('bed','y','Hotel',0)")
        self.s.allocate_bed(self.accom,'bed-a',a,'bed')
        with self.assertRaises(RuleError):self.s.allocate_bed(self.accom,'bed-b',b,'bed')
    def test_accessibility(self):
        id=self.arrived();self.s.db.execute("INSERT INTO beds VALUES('bed','y','Hotel',0)")
        with self.assertRaises(RuleError):self.s.allocate_bed(self.accom,'bed',id,'bed',True)
    def test_checkout_required_before_departure(self):
        id=self.arrived();self.s.db.execute("INSERT INTO beds VALUES('bed','y','Hotel',0)");self.s.allocate_bed(self.accom,'b',id,'bed')
        with self.assertRaises(RuleError):self.action(id,'depart',self.accom)
        self.s.checkout(self.accom,'out',id);self.action(id,'depart',self.accom)
    def test_concurrent_last_bed(self):
        a=self.arrived();b=self.arrived(1);self.s.db.execute("INSERT INTO beds VALUES('bed','y','Hotel',0)")
        def worker(id):
            s=Store(self.path)
            try:s.allocate_bed(self.accom,id,id,'bed');return True
            except RuleError:return False
            finally:s.close()
        with concurrent.futures.ThreadPoolExecutor(2) as pool: results=list(pool.map(worker,[a,b]))
        self.assertEqual(sum(results),1)
    def test_trip_capacity(self):
        a=self.approved();b=self.approved(1);self.s.db.execute("INSERT INTO trips VALUES('trip','y','Test',1)");self.s.allocate_trip(self.transport,'a',a,'trip')
        with self.assertRaises(RuleError):self.s.allocate_trip(self.transport,'b',b,'trip')
    def test_kit_uniqueness_and_stock(self):
        a=self.registered();b=self.registered(1);p=Principal('kits',('Kits',));self.s.db.execute("INSERT INTO kit_stock VALUES('y','Standard',1)")
        self.s.issue(p,'a',a,'Standard');self.assertEqual(self.s.issue(p,'a',a,'Standard'),{'issued':True})
        with self.assertRaises(RuleError):self.s.issue(p,'b',b,'Standard')
    def test_meal_uniqueness(self):
        a=self.registered();p=Principal('food',('Food',));self.s.db.execute("INSERT INTO meal_windows VALUES('lunch','y','Lunch',10)");self.s.issue(p,'a',a,'lunch',True)
        with self.assertRaises(RuleError):self.s.issue(p,'b',a,'lunch',True)
    def test_finance_separation(self):
        id=self.approved();p=Principal('maker',('Finance','FinanceChecker','FinancePayer'));c=self.s.claim(p,'claim',id,12500)['id']
        with self.assertRaises(RuleError):self.s.approve_claim(p,'own',c)
        checker=Principal('checker',('FinanceChecker',));self.s.approve_claim(checker,'approve',c)
        with self.assertRaises(RuleError):self.s.record_payment(p,'pay',c,'TEST-1234')
        result=self.s.record_payment(Principal('payer',('FinancePayer',)),'external',c,'TEST-1234');self.assertFalse(result['money_transferred_by_application'])
    def test_money_is_integer_paise(self):
        with self.assertRaises(RuleError):self.s.claim(Principal('maker',('Finance',)),'claim',self.approved(),1.25)
    def test_redacted_read(self):
        self.person();r=self.s.search(Principal('leader',('Leadership',)),'y')['rows'][0];self.assertNotIn('phone',r);self.assertNotIn('community',r)
    def test_search_sql_injection_is_literal(self):
        self.person();self.assertEqual(self.s.search(self.owner,'y',"' OR 1=1 --")['total'],0)
    def test_import_preview_and_row_errors(self):
        text='name,phone,state,edition,stream,category\nSynthetic,0000000000,Test,y,a,Delegate\nBad,,Test,y,b,Delegate\nSynthetic,0000000000,Test,y,a,Delegate\n'
        report=self.s.import_preview(self.owner,text);self.assertFalse(report[0]['errors']);self.assertTrue(report[1]['errors']);self.assertIn('duplicate within file',report[2]['errors']);self.assertEqual(self.s.dashboard(self.owner,'y')['total'],0)
        saved=self.s.import_commit(self.owner,'batch',text);self.assertEqual(sum(bool(r.get('result')) for r in saved),1)
        retry=self.s.import_commit(self.owner,'batch',text);self.assertEqual(saved[0]['result'],retry[0]['result'])
        self.assertEqual(self.s.dashboard(self.owner,'y')['total'],1)
    def test_departed_participant_cannot_register(self):
        id=self.arrived();self.action(id,'depart',self.accom)
        with self.assertRaises(RuleError):self.action(id,'register',self.reg)
    def test_failed_operation_rolls_back_audit_and_master(self):
        self.s.db.execute("DELETE FROM edition_units WHERE unit='a'")
        with self.assertRaises(RuleError):self.person()
        self.assertEqual(self.s.db.execute('SELECT count(*) FROM participants').fetchone()[0],0)
    def test_community_not_required(self):
        self.assertTrue(self.s.nominate(self.owner,'x',self.data)['id'])
    def test_unknown_actions_fail_closed(self):
        with self.assertRaises(RuleError):self.s.transition(self.owner,'x',self.person(),'invented',1)


class ScaleTests(unittest.TestCase):
    def test_full_dataset_and_pagination(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'scale.db';stats=seed(path,6000);s=Store(path);p=Principal('admin',('Admin',))
            self.assertEqual(stats['participations'],6600)
            self.assertEqual(s.dashboard(p,'edition-2026')['total'],6000)
            self.assertEqual(s.dashboard(p,'edition-2025')['total'],600)
            self.assertEqual(s.search(p,'edition-2026','Synthetic Participant 05999')['total'],1)
            ids=set()
            for offset in range(0,6000,100):
                ids.update(r['id'] for r in s.search(p,'edition-2026',limit=100,offset=offset)['rows'])
            self.assertEqual(len(ids),6000);self.assertEqual(s.db.execute('SELECT count(DISTINCT token) FROM participations').fetchone()[0],6600)
            s.close()


if __name__=='__main__':unittest.main()
