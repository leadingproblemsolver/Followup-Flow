import os
import tempfile
import unittest
from pathlib import Path
import app

class FollowUpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app.DB_PATH = Path(self.tmp.name) / 'test.sqlite3'
        app.initialize()
    def tearDown(self): self.tmp.cleanup()
    def test_create_and_list(self):
        row = app.add_inquiry({'customer':'Aisha','contact':'123','request':'Gift boxes','value':125})
        self.assertEqual(row['status'],'new')
        self.assertEqual(app.list_inquiries()[0]['value'],125)
    def test_missing_fields_rejected(self):
        with self.assertRaises(ValueError): app.add_inquiry({'customer':'Aisha'})
    def test_negative_value_rejected(self):
        with self.assertRaises(ValueError): app.add_inquiry({'customer':'A','contact':'1','request':'x','value':-1})
    def test_status_update(self):
        id_ = app.add_inquiry({'customer':'A','contact':'1','request':'x'})['id']
        self.assertEqual(app.update_status(id_,'won')['status'],'won')
    def test_invalid_status_rejected(self):
        id_ = app.add_inquiry({'customer':'A','contact':'1','request':'x'})['id']
        with self.assertRaises(ValueError): app.update_status(id_,'unexpected')
        self.assertEqual(app.list_inquiries()[0]['status'],'new')
    def test_unknown_id(self):
        with self.assertRaises(LookupError): app.update_status(999,'won')
    def test_long_input_rejected(self):
        with self.assertRaises(ValueError): app.add_inquiry({'customer':'A'*501,'contact':'1','request':'x'})

if __name__=='__main__': unittest.main()
