"""Customer receipt plans and explicit draft creation; never auto-bookkeep."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

class CustomerReceiptError(ValueError):
    pass


def amount(value: Any) -> Decimal:
    try:
        if isinstance(value, bool):raise ValueError()
        result=Decimal(str(value))
        if not result.is_finite() or result != result.quantize(Decimal('.01')):raise ValueError()
        if Decimal(str(float(result))) != result:raise ValueError()
        return result
    except (ValueError,InvalidOperation,TypeError,OverflowError):
        raise CustomerReceiptError('Amounts must be finite NOK with at most two decimals; no rounding') from None


def allocate_receipt(bank_amount: Any, remaining: Any, income_amount: Any=0) -> dict:
    bank,remaining,income=amount(bank_amount),amount(remaining),amount(income_amount)
    if bank<=0 or remaining<0 or income<0 or income>bank:raise CustomerReceiptError('Invalid receipt allocation')
    if income>max(bank-remaining,Decimal(0)):raise CustomerReceiptError('Income cannot consume an outstanding invoice principal')
    principal=min(bank-income,remaining);credit=bank-income-principal
    assert principal+income+credit==bank
    return dict(bank_amount=str(bank),principal=str(principal),income_total=str(income),customer_credit=str(credit),invoice_remaining_after=str(remaining-principal))


def entities(raw):
    if hasattr(raw,'to_dict'):raw=raw.to_dict()
    rows=raw.get('Entities') if isinstance(raw,dict) else raw
    if not isinstance(rows,list):raise CustomerReceiptError('Unexpected Xena list response')
    return rows


@dataclass
class CustomerReceiptWorkflow:
    _wrapper: Any

    def build_plan(self,partner_id:int,*,bank_amount:Any,bank_account:int,pay_date:Any,reference:str,invoice_post_id:int|None=None,income_allocations:list|None=None,expected_remaining:Any=None,reserved_principal:Any=0)->dict:
        if type(partner_id) is not int or partner_id<=0 or type(bank_account) is not int or bank_account<=0:raise CustomerReceiptError('Positive partner ID and bank account required')
        if not isinstance(reference,str) or not reference.strip():raise CustomerReceiptError('A source receipt reference is required')
        bank=amount(bank_amount);partner=self._wrapper.partner.get_by_id(partner_id)
        if hasattr(partner,'to_dict'):partner=partner.to_dict()
        if partner.get('Id')!=partner_id or partner.get('IsDeactivated'):raise CustomerReceiptError('Partner is missing or deactivated')
        number=partner.get('AccountNumber')
        if not str(number).isdigit():raise CustomerReceiptError('Partner account number missing')
        tag=self._wrapper.get_ledger_tag_by_number(bank_account)
        if hasattr(tag,'to_dict'):tag=tag.to_dict()
        if tag.get('IsDeactivated') or tag.get('LedgerTagType')!='LedgerTagType_Settlement':raise CustomerReceiptError('Bank must be an active settlement account')
        if invoice_post_id is None:
            contexts=[c for c in entities(self._wrapper.partner.get_contexts(partner_id)) if c.get('PartnerId')==partner_id and c.get('ContextType')=='ContextType_Customer' and not c.get('IsDeactivated')]
            if len(contexts)!=1:raise CustomerReceiptError('Expected exactly one active customer context')
        remaining=Decimal(0)
        if invoice_post_id is not None:
            if type(invoice_post_id) is not int or invoice_post_id<=0:raise CustomerReceiptError('Invalid invoice post ID')
            matches=[r for r in entities(self._wrapper.partner_ledger.get_posts(partner_id,context_type='customer',post_type='customer_invoice',force_no_paging=True)) if r.get('Id')==invoice_post_id and r.get('PartnerId')==partner_id]
            if len(matches)!=1 or matches[0].get('CurrencyAbbreviation')!='NOK':raise CustomerReceiptError('Invoice post does not belong to this NOK customer')
            remaining=amount(matches[0].get('RemainingAmount'))
            if remaining<0:raise CustomerReceiptError('Customer credit note is not a positive invoice')
        if expected_remaining is not None and amount(expected_remaining)!=remaining:raise CustomerReceiptError('Invoice balance changed since preview')
        reserved=amount(reserved_principal)
        if reserved<0 or reserved>remaining:raise CustomerReceiptError('Invalid previous preview allocation')
        available=remaining-reserved;income_allocations=income_allocations or [];income=Decimal(0)
        for item in income_allocations:
            value=amount(item['amount']);account=item['account']
            if value<=0 or type(account) is not int or account<=0 or account==bank_account:raise CustomerReceiptError('Invalid income line')
            income_tag=self._wrapper.get_ledger_tag_by_number(account)
            if hasattr(income_tag,'to_dict'):income_tag=income_tag.to_dict()
            if income_tag.get('IsDeactivated') or income_tag.get('DefaultVatId') not in (None,0):raise CustomerReceiptError('Interest/fee income must use active accounts without default VAT')
            income+=value
        allocation=allocate_receipt(bank,available,income);principal=amount(allocation['principal']);credit=amount(allocation['customer_credit']);rows=[]
        common=dict(date=pay_date,type='partnerpayment',partner_number=int(number),account=bank_account)
        if principal:
            row=dict(common,amount=str(principal),description=reference+' / faktura',settled_partner_post_ids=[invoice_post_id])
            if principal<available:row['partial_settle_id']=invoice_post_id
            rows.append(row)
        if credit:rows.append(dict(common,amount=str(credit),description=reference+' / ufordelt kundekredit'))
        for item in income_allocations:
            rows.append(dict(date=pay_date,type='finance',amount=str(-amount(item['amount'])),account=item['account'],contra_account=bank_account,description=reference+' / '+item.get('kind','renter/gebyr')))
        payloads=self._wrapper.voucher_draft.preview_convenience_rows(rows)
        return dict(**allocation,partner_id=partner_id,partner_number=int(number),bank_account=bank_account,pay_date=pay_date,reference=reference,invoice_post_id=invoice_post_id,snapshot_remaining=str(remaining),available_remaining=str(available),reserved_principal=str(reserved),income_allocations=income_allocations,rows=rows,preview_payloads=payloads,status='preview_only')

    def create_draft(self,plan:dict,*,ledger_id:int,voucher_number:int|None=None)->dict:
        """Explicit mutation. Caller must durably claim reference; never retry uncertain writes.

        Fresh balance must match the simulated available balance before creating
        any rows. No bookkeeping, distribution or automatic settlement retry.
        """
        if type(ledger_id) is not int or ledger_id<=0:raise CustomerReceiptError('Positive ledger ID required')
        if voucher_number is not None and (type(voucher_number) is not int or voucher_number<=0):raise CustomerReceiptError('Invalid shared voucher number')
        fresh=self.build_plan(plan['partner_id'],bank_amount=plan['bank_amount'],bank_account=plan['bank_account'],pay_date=plan['pay_date'],reference=plan['reference'],invoice_post_id=plan['invoice_post_id'],income_allocations=plan['income_allocations'],expected_remaining=plan['available_remaining'])
        if any(amount(fresh[k])!=amount(plan[k]) for k in ('principal','income_total','customer_credit')):raise CustomerReceiptError('Allocation changed since preview')
        result=self._wrapper.voucher_draft.create_lines_convenience(fresh['rows'],ledger_id=ledger_id,voucher_number=voucher_number)
        for line in result.get('Lines',[]):
            updated=line['Updated']
            if updated.get('VatId') is not None:
                dto=dict(updated);dto.update(VatId=None,VatAbbreviation=None,VatDescription=None)
                self._wrapper.voucher_draft.update_line(updated['Id'],dto)
        return result
