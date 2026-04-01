# API capture: Partner GLN tab save

Date: 2026-03-31
Fiscal: 104779
Partner: API2 test (PartnerId `3035811552`, account `10140`)

## User action captured
- User edited GLN information on the GLN tab and saved.

## Browser-captured endpoint sequence

### Initial GLN tab load
- `GET /Api/Fiscal/104779/Partner/3035811552/GLNNumber?ForceNoPaging=true&Page=0&PageSize=30&ShowDeactivated=false`

### Save behavior
- `POST /Api/Fiscal/104779/PartnerGLNNumber`
- Follow-up requests observed against created resource id:
  - `GET /Api/Fiscal/104779/PartnerGLNNumber/3035704683`
  - `GET /Api/Fiscal/104779/PartnerGLNNumber/3035704683`
  - `GET /Api/Fiscal/104779/PartnerGLNNumber/3035704683`

Notes:
- The save operation used the collection endpoint (`POST /PartnerGLNNumber`) indicating create semantics.
- Repeated GETs on `/PartnerGLNNumber/{id}` indicate UI refresh/reload after save.

## Verified persisted data (live API readback)
Using generated partner client methods:
- `api_partner_gln_number__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id_gln_number`
- `api_partner_gln_number__get_get__api__fiscal_fiscal_id__partner_gln_number_id`

Readback entity:

```json
{
  "Version": 4,
  "IsDeactivated": false,
  "FiscalSetupId": 104779,
  "CreatedAt": "2026-03-31T18:25:17.163Z",
  "PartnerId": 3035811552,
  "Description": "EHF",
  "Attention": "EHF",
  "GLN": "999222888",
  "PartnerName": null,
  "Id": 3035704683
}
```

## Wrapper implications
- GLN tab appears to be handled by Partner GLNNumber endpoints, not partner root PUT.
- Relevant generated methods to wrap:
  - `api_partner_gln_number__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id_gln_number`
  - `api_partner_gln_number__post_post__api__fiscal_fiscal_id__partner_gln_number`
  - `api_partner_gln_number__put_put__api__fiscal_fiscal_id__partner_gln_number_id`
  - `api_partner_gln_number__delete_delete__api__fiscal_fiscal_id__partner_gln_number_id`
