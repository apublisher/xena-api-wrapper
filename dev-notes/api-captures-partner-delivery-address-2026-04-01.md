# API capture: Leverandoradresse / Delivery Address

Date: 2026-04-01
Fiscal: 104779
Partner: API2 test (`PartnerId=3035811552`, account `10140`)

## Capture setup
- Network baseline reset in browser using `performance.clearResourceTimings()`.
- User performed Leverandoradresse operation and saved.

## Browser-captured endpoint sequence

Observed relevant API calls after baseline:
- `POST /Api/Fiscal/104779/PartnerDeliveryAddress`
- `GET /Api/Fiscal/104779/Partner/3035811552/DeliveryAddress?ForceNoPaging=true&Page=0&PageSize=30&ShowDeactivated=false`
- `GET /Api/Fiscal/104779/Partner/3035811552/DeliveryAddress?ForceNoPaging=true&Page=0&PageSize=30&ShowDeactivated=false`

Notes:
- First GET attempt was aborted (`net::ERR_ABORTED`) during UI refresh.
- Subsequent GET completed and refreshed grid.

## Verified persisted row (live API readback)
Method used:
- `api_partner_delivery_address__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id__delivery_address`

Returned row:

```json
{
  "Version": 1,
  "IsDeactivated": false,
  "FiscalSetupId": 104779,
  "CreatedAt": "2026-04-01T09:45:42.69Z",
  "PartnerDefaultDeliveryAddressId": null,
  "PartnerId": 3035811552,
  "IsDefault": false,
  "Address": {
    "City": "BLOMSTERDALEN",
    "CountryName": "NO",
    "PlaceName": "",
    "Street": "Gaten 1",
    "Zip": "5258",
    "Name": "Navn på leveringsstedet",
    "Description": "Navn på leveringsstedet - Gaten 1, 5258 BLOMSTERDALEN",
    "CountryDisplayName": "Norge"
  },
  "Note": "Notat",
  "ContactName": "Jarle",
  "Title": "Sir",
  "Phone": "99277029",
  "Email": "jarle@aspectus.net",
  "Id": 3037057578
}
```

## Wrapper implications
Leverandoradresse is handled by PartnerDeliveryAddress endpoints (not PartnerLocation):
- `api_partner_delivery_address__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id__delivery_address`
- `api_partner_delivery_address__post_post__api__fiscal_fiscal_id__partner_delivery_address`
- `api_partner_delivery_address__put_put__api__fiscal_fiscal_id__partner_delivery_address_id`
- `api_partner_delivery_address__delete_delete__api__fiscal_fiscal_id__partner_delivery_address_id`
