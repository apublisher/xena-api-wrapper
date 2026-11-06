import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from xena_api_wrappers.workflows.partner.customer_receipt import CustomerReceiptWorkflow,CustomerReceiptError,allocate_receipt
class ReceiptTests(unittest.TestCase):
 def setUp(self):
  self.row=dict(Id=10,PartnerId=20,CurrencyAbbreviation='NOK',RemainingAmount='100.00')
  self.w=SimpleNamespace(partner=SimpleNamespace(get_by_id=Mock(return_value=dict(Id=20,AccountNumber=12000,IsDeactivated=False))),partner_ledger=SimpleNamespace(get_posts=Mock(return_value={'Entities':[self.row]})),get_ledger_tag_by_number=Mock(side_effect=lambda n:dict(Id=n,Number=n,IsDeactivated=False,LedgerTagType='LedgerTagType_Settlement' if n==1925 else 'LedgerTagType_Default',DefaultVatId=None)),voucher_draft=SimpleNamespace(preview_convenience_rows=Mock(side_effect=lambda rows:rows),create_lines_convenience=Mock()))
  self.f=CustomerReceiptWorkflow(self.w)
  self.args=dict(bank_amount='100.00',bank_account=1925,pay_date='2026-09-07',reference='OCR batch A / payment 1',invoice_post_id=10,expected_remaining='100.00')
 def test_partial_preserves_open_balance_and_uses_partial_post(self):
  p=self.f.build_plan(20,**dict(self.args,bank_amount='40.00'))
  self.assertEqual(p['principal'],'40.00');self.assertEqual(p['invoice_remaining_after'],'60.00');self.assertEqual(p['rows'][0]['partial_settle_id'],10)
  self.w.voucher_draft.create_lines_convenience.assert_not_called()
 def test_overpayment_generates_unallocated_customer_credit(self):
  p=self.f.build_plan(20,**dict(self.args,bank_amount='120.00'))
  self.assertEqual(p['customer_credit'],'20.00');self.assertEqual(len(p['rows']),2);self.assertNotIn('settled_partner_post_ids',p['rows'][1])
 def test_closed_invoice_generates_full_customer_credit(self):
  self.row['RemainingAmount']='0.00'
  p=self.f.build_plan(20,**dict(self.args,expected_remaining='0.00'))
  self.assertEqual(p['customer_credit'],'100.00');self.assertEqual(len(p['rows']),1)
 def test_documented_income_splits_full_bank_amount_without_changing_principal(self):
  p=self.f.build_plan(20,**dict(self.args,bank_amount='120.00',income_allocations=[dict(account=8050,amount='20.00')]))
  self.assertEqual(p['income_total'],'20.00');self.assertEqual(p['customer_credit'],'0.00');self.assertEqual(p['rows'][1]['amount'],'-20.00');self.assertEqual(p['rows'][1]['contra_account'],1925)
 def test_income_cannot_reduce_principal_on_underpayment(self):
  with self.assertRaises(CustomerReceiptError):self.f.build_plan(20,**dict(self.args,bank_amount='50.00',income_allocations=[dict(account=8050,amount='10.00')]))
 def test_changed_balance_or_wrong_partner_blocks(self):
  self.row['RemainingAmount']='99.00'
  with self.assertRaises(CustomerReceiptError):self.f.build_plan(20,**self.args)
  self.row.update(RemainingAmount='100.00',PartnerId=21)
  with self.assertRaises(CustomerReceiptError):self.f.build_plan(20,**self.args)
 def test_strict_money_rejects_invalid_and_extra_decimals(self):
  for value in ('NaN','Infinity','1.001',True,-1,0):
   with self.subTest(value=value),self.assertRaises(CustomerReceiptError):allocate_receipt(value,100)
 def test_previous_preview_principal_can_be_reserved_without_faking_live_balance(self):
  p=self.f.build_plan(20,**dict(self.args,bank_amount='30.00',reserved_principal='100.00'))
  self.assertEqual(p['customer_credit'],'30.00');self.assertEqual(p['snapshot_remaining'],'100.00')
 def test_standalone_credit_requires_customer_context(self):
  self.w.partner.get_contexts=Mock(return_value={'Entities':[]})
  with self.assertRaises(CustomerReceiptError):self.f.build_plan(20,**dict(self.args,invoice_post_id=None,expected_remaining=0))
  self.w.partner.get_contexts.return_value={'Entities':[dict(PartnerId=20,ContextType='ContextType_Customer',IsDeactivated=False)]}
  p=self.f.build_plan(20,**dict(self.args,invoice_post_id=None,expected_remaining=0))
  self.assertEqual(p['customer_credit'],'100.00')
 def test_create_draft_does_not_write_if_reserved_balance_not_yet_applied(self):
  p=self.f.build_plan(20,**dict(self.args,bank_amount='30.00',reserved_principal='100.00'))
  with self.assertRaises(CustomerReceiptError):self.f.create_draft(p,ledger_id=1)
  self.w.voucher_draft.create_lines_convenience.assert_not_called()
if __name__=='__main__':unittest.main()
