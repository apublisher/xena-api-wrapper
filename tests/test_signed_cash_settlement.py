import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerWorkflow,PartnerLedgerError
class SignedCashTests(unittest.TestCase):
 def setUp(self):
  self.w=PartnerLedgerWorkflow.__new__(PartnerLedgerWorkflow);self.w._fiscal_id='1';self.put=Mock()
  self.row=dict(Id=10,PartnerId=20,RemainingAmount=-100,CurrencyAbbreviation='NOK',Amount=-100,VoucherNumber=123,FiscalDateDays=20697)
  self.w.get_posts=Mock(return_value={'Entities':[self.row]});self.w.get_unsettled_posts=Mock(return_value={'Entities':[self.row]})
  self.w._client=SimpleNamespace(order=SimpleNamespace(api_order__put_pay_put__api__fiscal_fiscal_id__order__pay=self.put),finance=SimpleNamespace(api_ledger_tag__get_settlement_tag_get__api__fiscal_fiscal_id__ledger_tag__settlement_tag=Mock(return_value={'Entities':[dict(Id=30,Number=1903,Description='Kort')]}),api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag=Mock(return_value={'Entities':[]})))
 def test_signed_payload_uses_negative_account_amount_for_credit(self):
  p=self.w.build_customer_cash_settlement_payload(20,[10],amount=-100,payment_ledger_tag_id=30,pay_date='2026-09-01')
  self.assertEqual(p['ledgerPosts'][0]['Amount'],-100);self.assertEqual(p['partnerPostIds'],[10]);self.assertEqual(self.w.get_posts.call_args.kwargs['post_type'],'customer_credit_note');self.put.assert_not_called()
 def test_normal_positive_payment_api_still_rejects_negative(self):
  with self.assertRaises(PartnerLedgerError):self.w.build_customer_payment_payload(20,[10],amount=-100,payment_ledger_tag_id=30,pay_date='2026-09-01')
 def test_wrong_remaining_sign_is_rejected(self):
  self.row['RemainingAmount']=100
  with self.assertRaises(PartnerLedgerError):self.w.build_customer_cash_settlement_payload(20,[10],amount=-100,payment_ledger_tag_id=30,pay_date='2026-09-01')
 def test_refund_resolver_uses_credit_note_type(self):
  self.assertEqual(self.w.resolve_customer_invoice_post_id(20,123,amount=-100,fiscal_date='2026-09-01'),10)
  self.assertEqual(self.w.get_posts.call_args.kwargs['post_type'],'customer_credit_note')
if __name__=='__main__':unittest.main()
