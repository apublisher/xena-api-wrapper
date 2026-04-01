# Partner ledger read capture (2026-04-01)

Fiscal: 104779  
Partner: MPS Bilskade Bergen AS (id 2247873100, account 10008)

## Goal
Map read endpoints used by the Partner -> Ledger tab filters before implementing wrapper methods.

## Captured endpoint family
Primary data endpoint:

- GET /Api/Fiscal/104779/Transaction/Partner/2247873100/PartnerPost

Observed query parameters:

- ForceNoPaging=false
- Page=0
- PageSize=30
- ShowDeactivated=false
- fiscalPeriodId=2586516686
- fiscalDateFrom=20089
- fiscalDateTo=20453
- isSettled=
- isParked=
- postType=PartnerPostType_CustomerInvoice (and other post types)

Related supporting call:

- GET /Api/Fiscal/104779/FiscalPeriod?ForceNoPaging=true

## Filter interactions seen
- Baseline load: PartnerPost called with and without empty settled/parked values.
- Settled toggle to open only: isSettled=false.
- Parked toggle: isParked=true.
- Reset toggles: empty isSettled/isParked.
- Post type filter changed between at least:
  - PartnerPostType_CustomerInvoice
  - PartnerPostType_CustomerCreditNote
  - PartnerPostType_CustomerPayment
- Fiscal period change updated all three fields:
  - fiscalPeriodId
  - fiscalDateFrom
  - fiscalDateTo

## Wrapper mapping decision
Implemented read workflow in `workflows/partner/partner_ledger.py` using:

- api_transaction__get_partner_posts_by_partner_get__api__fiscal_fiscal_id__transaction__partner_id__partner_post

Method surface includes:

- get_posts(...)
- get_posts_for_year(...)
- get_customer_posts(...)
- get_supplier_posts(...)
