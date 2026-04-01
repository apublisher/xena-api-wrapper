# Partner ledger match capture (2026-04-01)

Fiscal: 104779  
Partner: MPS Bilskade Bergen AS (id 2247873100, account 10008)

## Goal
Capture API activity when matching an open payment with an open invoice in Partner ledger.

## Capture baseline
- Session tag: `partner-ledger-match`
- Baseline reset at: `2026-04-01T10:15:55.804Z`
- Resource timing count after reset: `0`

## Captured API calls after baseline
1. `GET /Api/Fiscal/104779/LedgerTag/CurrencyDifferenceTag?ForceNoPaging=true`
2. `GET /Api/Fiscal/104779/Partner/2247873100/UnsettledPost?ForceNoPaging=true`
3. `POST /Api/Fiscal/104779/Order/Pay`

Notes:
- The match action clearly triggered `Order/Pay` after loading unsettled posts.
- `CurrencyDifferenceTag` appears to be support data for settlement/posting behavior.

## Generated client mapping candidates
- Unsettled list: partner namespace
  - `api_payment__get_unsettled_partner_post_get__api__fiscal_fiscal_id__partner_id__unsettled_post`
- Payment/match operation: order namespace
  - `api_order__put_pay_put__api__fiscal_fiscal_id__order__pay(pay_data, fiscal_id, **kwargs)`

## Next step
Capture request payload shape for `/Order/Pay` (fields in `pay_data`) to implement a safe wrapper method for matching open payment and invoice.

## Captured Order/Pay request payload
Captured during repeat match action (method observed: `PUT`):

```json
{
  "ledgerPosts": [
    {
      "LedgerTagId": 2180183781,
      "LedgerTagNumber": null,
      "LedgerTagDescription": "Valutakursdifferanse",
      "Amount": 0
    }
  ],
  "currencyAbbreviation": "NOK",
  "partnerPostIds": [3020754398, 2900254804],
  "payDate": 20420,
  "partialSettleId": 3020754398
}
```

Field notes:
- `partnerPostIds`: ids included in settlement operation (invoice/payment partner posts).
- `partialSettleId`: anchor post id for partial settlement context.
- `payDate`: Xena fiscal day integer.
- `ledgerPosts`: adjustment postings (currency-difference tag shown here).
- `currencyAbbreviation`: operation currency.
