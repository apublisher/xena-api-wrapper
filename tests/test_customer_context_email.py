import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from xena_api_wrappers.workflows.partner.partner import PartnerWorkflow,PartnerError
class ContextEmailTests(unittest.TestCase):
 def setUp(self):
  self.w=PartnerWorkflow.__new__(PartnerWorkflow);self.w._fiscal_id='1'
  self.put=Mock();self.w._client=SimpleNamespace(partner=SimpleNamespace(api_partner_context__put_put__api__fiscal_fiscal_id__partner_context_id=self.put))
  self.context=dict(Id=10,PartnerId=20,ContextType='ContextType_Customer',Version=5,InvoiceEmail='bad',CurrencyAbbreviation='NOK')
  self.w.get_contexts=Mock(return_value={'Entities':[self.context]})
 def test_writes_real_context_preserving_version(self):
  self.w.update_customer_invoice_email(20,' a@example.com ')
  dto=self.put.call_args.kwargs['dto'];self.assertEqual(dto['InvoiceEmail'],'a@example.com');self.assertEqual(dto['Version'],5);self.assertEqual(self.put.call_args.kwargs['id'],'10')
 def test_blank_is_explicit_null(self):
  self.w.update_customer_invoice_email(20,' ')
  self.assertIsNone(self.put.call_args.kwargs['dto']['InvoiceEmail'])
 def test_ambiguous_or_invalid_never_writes(self):
  with self.assertRaises(PartnerError):self.w.update_customer_invoice_email(20,'bad')
  self.w.get_contexts.return_value={'Entities':[self.context,self.context]}
  with self.assertRaises(PartnerError):self.w.update_customer_invoice_email(20,None)
  self.put.assert_not_called()
if __name__=='__main__':unittest.main()
