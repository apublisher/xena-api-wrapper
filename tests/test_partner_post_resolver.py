import unittest
from unittest.mock import Mock
from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerWorkflow,PartnerLedgerError
class ResolverTests(unittest.TestCase):
 def setUp(self):
  self.w=PartnerLedgerWorkflow.__new__(PartnerLedgerWorkflow)
  self.row=dict(Id=999,PartnerId=20,VoucherNumber=126056,FiscalDateDays=20697,CurrencyAbbreviation='NOK',Amount=500,RemainingAmount=500)
  self.w.get_posts=Mock(return_value={'Entities':[self.row]})
 def test_returns_reskontro_id_and_not_invoice_entity_id(self):self.assertEqual(self.w.resolve_customer_invoice_post_id(20,126056,amount='500.00',fiscal_date='2026-09-01'),999)
 def test_duplicate_match_rejected(self):
  self.w.get_posts.return_value={'Entities':[self.row,self.row.copy()]}
  with self.assertRaises(PartnerLedgerError):self.w.resolve_customer_invoice_post_id(20,126056,amount=500,fiscal_date='2026-09-01')
 def test_partly_paid_post_rejected(self):
  self.row['RemainingAmount']=400
  with self.assertRaises(PartnerLedgerError):self.w.resolve_customer_invoice_post_id(20,126056,amount=500,fiscal_date='2026-09-01')
 def test_wrong_date_or_voucher_rejected(self):
  with self.assertRaises(PartnerLedgerError):self.w.resolve_customer_invoice_post_id(20,126057,amount=500,fiscal_date='2026-09-01')
  with self.assertRaises(PartnerLedgerError):self.w.resolve_customer_invoice_post_id(20,126056,amount=500,fiscal_date='2026-09-02')
if __name__=='__main__':unittest.main()
