import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from decimal import Decimal
from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerWorkflow,PartnerLedgerError

class SplitCashTests(unittest.TestCase):
 def setUp(self):
  self.w=PartnerLedgerWorkflow.__new__(PartnerLedgerWorkflow);self.w._fiscal_id='1';self.put=Mock()
  self.row=dict(Id=10,PartnerId=20,RemainingAmount=51500,CurrencyAbbreviation='NOK')
  self.w.get_posts=Mock(return_value={'Entities':[self.row]});self.w.get_unsettled_posts=Mock(return_value={'Entities':[self.row]})
  self.w._client=SimpleNamespace(order=SimpleNamespace(api_order__put_pay_put__api__fiscal_fiscal_id__order__pay=self.put),finance=SimpleNamespace(api_ledger_tag__get_settlement_tag_get__api__fiscal_fiscal_id__ledger_tag__settlement_tag=Mock(return_value={'Entities':[dict(Id=30,Number=1903),dict(Id=31,Number=1905),dict(Id=32,Number=1902)]}),api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag=Mock(return_value={'Entities':[dict(Id=99,Number=8050)]})))
  self.allocations=[dict(payment_ledger_tag_id=30,amount='40000'),dict(payment_ledger_tag_id=31,amount='11500')]
 def build(self):return self.w.build_customer_split_cash_payload(20,[10],allocations=self.allocations,pay_date='2026-10-01')
 def test_116644_exact_account_allocation_without_write(self):
  p=self.build();self.assertEqual({r['LedgerTagId']:r['Amount'] for r in p['ledgerPosts']},{30:40000,31:11500,32:0,99:0});self.put.assert_not_called()
 def test_116720_cash_and_card(self):
  self.row['RemainingAmount']=1299;self.allocations=[dict(payment_ledger_tag_id=32,amount=1099),dict(payment_ledger_tag_id=30,amount=200)]
  p=self.build();self.assertEqual(sum(Decimal(str(r['Amount'])) for r in p['ledgerPosts']),Decimal(1299))
 def test_single_request_for_both_accounts(self):
  self.w.pay_customer_split_cash(20,[10],allocations=self.allocations,pay_date='2026-10-01');self.put.assert_called_once()
 def test_mismatch_rejected_before_put(self):
  self.allocations[0]['amount']='39999'
  with self.assertRaises(PartnerLedgerError):self.build()
  self.put.assert_not_called()
 def test_income_account_is_not_settlement_account(self):
  self.allocations[1]['payment_ledger_tag_id']=99
  with self.assertRaises(PartnerLedgerError):self.build()
 def test_duplicate_account_is_rejected(self):
  self.allocations[1]['payment_ledger_tag_id']=30
  with self.assertRaises(PartnerLedgerError):self.build()
 def test_mixed_signs_are_rejected(self):
  self.allocations[1]['amount']='-11500'
  with self.assertRaises(PartnerLedgerError):self.build()
 def test_no_rounding_of_subcent_amounts(self):
  self.allocations[1]['amount']='11500.001'
  with self.assertRaises(PartnerLedgerError):self.build()
 def test_signed_refund_preserves_allocations(self):
  self.row['RemainingAmount']=-51500
  for a in self.allocations:a['amount']=str(-Decimal(a['amount']))
  p=self.build();self.assertEqual(sum(r['Amount'] for r in p['ledgerPosts']),-51500)
if __name__=='__main__':unittest.main()
