# xena-api-wrappers

Task-oriented Python wrappers built on top of `xena-client`.

## Design goals

- Tenant-agnostic core API.
- Runtime credentials supported as first-class input.
- Optional dotenv loading for local development.
- Business-oriented methods that combine multiple low-level API calls.

## Runtime compatibility

- Python: 3.10+
- Primary runtime targets:
	- Windows development environments
	- Linux servers (for example Ubuntu 22)

## Date/time behavior

- Fiscal dates are handled as epoch-day integers (days since 1970-01-01), matching observed Xena API behavior.
- Supported date inputs in wrappers:
	- `date`
	- `datetime`
	- epoch-day `int`
	- ISO date/datetime string
	- Norwegian date format `DD.MM.YYYY`
- For timezone-aware `datetime`, values are converted to the configured business timezone before taking the local calendar date.
- This prevents date drift around midnight when caller timezone differs from business timezone.

## Quick start

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper(api_key="...", fiscal_id="...")
report = wrapper.ledger_group_data.get_balance_sheet(
	date_from="2026-01-01",
	date_to="2026-01-31",
)
```

## Optional dotenv usage

Install optional support:

```bash
pip install -e .[dotenv]
```

Then:

```python
wrapper = XenaApiWrapper.from_env(load_dotenv=True)
```

## Fiscal period usage

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Get full raw payload from /FiscalPeriod
all_periods = wrapper.fiscal_period.get_all()

# Safe lookup by full date (recommended)
period_id = wrapper.fiscal_period.get_id_by_date("15.01.2026")

# Convenience lookup by year description
period_2026_id = wrapper.fiscal_period.get_id_by_year("2026")
```

## Ledger group usage

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Full raw payload from /LedgerTag/LedgerGroup
all_groups = wrapper.ledger_group.get_all()

# Value by localized text
income_value = wrapper.ledger_group.get_value_by_text("Resultatregnskap")

# Entity by value
asset_group = wrapper.ledger_group.get_by_value("Xena_Domain_Asset_Accounts")
```

## Ledger group data usage

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Explicit mode: pass fiscal_period_id yourself.
period_id = wrapper.fiscal_period.get_id_by_date("2025-01-15")
income_january = wrapper.ledger_group_data.get_by_ledger_group(
	"Xena_Domain_Income_Accounts",
	fiscal_period_id=period_id,
	date_from="2025-01-01",
	date_to="2025-01-31",
)

# Convenience mode: fiscal_period_id is auto-resolved from date_from.
income_january_auto = wrapper.ledger_group_data.get_by_ledger_group(
	"Resultatregnskap",
	date_from="01.01.2025",
	date_to="31.01.2025",
)

# High-level helper for all three balance report groups in one call.
balance_sheet = wrapper.ledger_group_data.get_balance_sheet(
	date_from="2025-01-01",
	date_to="2025-01-31",
)
```

`get_balance_sheet(...)` returns a dict keyed by:
- `Xena_Domain_Income_Accounts`
- `Xena_Domain_Asset_Accounts`
- `Xena_Domain_Liability_Accounts`

## Ledger group detail usage (account level)

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Step 1: Fetch summary rows for a top-level ledger group.
summary = wrapper.ledger_group_data.get_by_ledger_group(
	"Xena_Domain_Income_Accounts",
	date_from="2025-01-01",
	date_to="2025-12-31",
)

# Step 2: Pick one summary row Group value (example: Administration Costs).
ledger_account = "Xena_Domain_Income_Accounts_Administration_Costs"

# Step 3: Fetch account-level detail rows for that summary group.
detail = wrapper.ledger_group_data_detail.get_by_ledger_account(
	ledger_account,
	date_from="2025-01-01",
	date_to="2025-12-31",
)

# Or pass a summary row directly.
first_row = summary["Entities"][0]
detail_from_row = wrapper.ledger_group_data_detail.get_by_summary_group(
	first_row,
	date_from="2025-01-01",
	date_to="2025-12-31",
)
```

`ledger_group_data_detail` follows observed UI behavior:
- endpoint: `/Transaction/LedgerGroupDataDetail`
- `show_deactivated=True` by default
- `fiscal_period_id` optional; when omitted it is auto-resolved from `date_from`

## Practical account list helpers

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Ledger account master ranges from /LedgerAccount.
all_accounts = wrapper.get_all_accounts()          # 1000-9999
balance_accounts = wrapper.get_balance_accounts()  # 1000-2999
result_accounts = wrapper.get_result_accounts()    # 3000-9999

# Account id lookup by account number.
account_1920_id = wrapper.ledger_account.get_id_by_account_number(1920)
```

These helpers read account master data and return rows sorted by `AccountNumber`.

If you want date-ranged report account rows (from LedgerGroupDataDetail), use:

```python
report_accounts = wrapper.get_all_report_accounts("2025-01-01", "2025-12-31")
report_balance_accounts = wrapper.get_balance_report_accounts("2025-01-01", "2025-12-31")
report_result_accounts = wrapper.get_result_report_accounts("2025-01-01", "2025-12-31")
```

## Ledger post usage (entries by account)

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Account number or account-id string is accepted.
entries = wrapper.get_entries_by_account(
	"1920",
	"2025-01-01",
	"2025-12-31",
	include_running_totals=True,
	force_no_paging=False,
	page=0,
	page_size=100,
	show_deactivated=False,
)
```

This calls `/LedgerTag/{id}/LedgerPost` after resolving account `1920` to its ledger-tag id.

For voucher/transaction level details:

```python
# Note: get_transactions_by_voucher(...) expects voucher id, not voucher number.

# 1) Voucher -> transaction rows
transactions = wrapper.transaction.get_transactions_by_voucher(3020754351)

# If you have voucher number (for example 15316), resolve it first:
voucher = wrapper.transaction.get_voucher_by_number(15316)
voucher_id = wrapper.transaction.get_voucher_id_by_number(15316)
transactions_by_number = wrapper.transaction.get_transactions_by_voucher_number(15316)

# 2) Transaction -> all post types (always returned)
details = wrapper.transaction.get_posting_details(3020754631)
# details contains: ledger_post, partner_post, article_post

# 3) Convenience: voucher -> transaction ids -> full details
details_from_voucher = wrapper.transaction.get_posting_details_by_voucher(3020754351)
details_from_voucher_number = wrapper.transaction.get_posting_details_by_voucher_number(15316)
```

Wrapper-level facade methods are still available for compatibility:
- `wrapper.get_transactions_by_voucher(...)`
- `wrapper.get_posting_details(...)`
- `wrapper.get_posting_details_by_voucher(...)`

## Bookkeeping draft voucher usage (Kassekladd)

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# 1) Resolve draft ledger dynamically (avoid hardcoded names in calling code).
ledger_id = wrapper.get_voucher_draft_ledger_id_by_description("Bank2Xena")

# 2) List lines in selected draft ledger.
lines = wrapper.get_voucher_draft_lines(ledger_id, force_no_paging=True)

# 3) Create and update draft lines.
created = wrapper.create_voucher_draft_line(
	{
		"LedgerId": ledger_id,
		"FiscalDateDays": 20544,
		"VoucherNumber": None,
	}
)

updated = wrapper.update_voucher_draft_line(
	created["Id"],
	{
		"Id": created["Id"],
		"LedgerId": ledger_id,
		"Description": "Imported from bank statement",
	},
)

# 4) Preview summary/validation for selected lines.
summary = wrapper.preview_voucher_draft_summary(
	ledger_id,
	bookkeep_all=False,
	ledger_line_ids=[updated["Id"]],
)
```

The draft voucher workflow intentionally targets draft-safe operations and does not call the bookkeeping/approve endpoint.

## Partner usage

```python
from xena_api_wrappers import XenaApiWrapper

wrapper = XenaApiWrapper.from_env(load_dotenv=True)

# Raw partner list payload with filters.
partners = wrapper.partner.get_all(
	query_string="acme",
	partner_context_type="Customer",
	show_deactivated=False,
	page=0,
	page_size=100,
)

# Convenience context filters.
customers = wrapper.partner.get_customers(query_string="acme")
suppliers = wrapper.partner.get_suppliers()
employees = wrapper.partner.get_employees()

# Entities helper (returns parsed list from response payload).
customer_entities = wrapper.partner.get_entities(partner_context_type="Customer")

# Lookups.
partner = wrapper.partner.get_by_id(123)
partner_by_account = wrapper.partner.get_by_account_number(1500)
context_types = wrapper.partner.get_context_types()
```

Wrapper-level facade methods are also available:
- `wrapper.get_partners(...)`
- `wrapper.get_partner_entities(...)`
- `wrapper.get_customers(...)`
- `wrapper.get_suppliers(...)`
- `wrapper.get_employees(...)`
- `wrapper.get_partner_context_types()`
- `wrapper.get_partner_by_id(...)`
- `wrapper.get_partner_by_account_number(...)`

Create/update and context helpers:

```python
# Raw partner create / update
created = wrapper.create_partner(
	{
		"ShortDescription": "API kundetest",
		"Address": {"Name": "API kundetest", "Zip": "5258", "CountryName": "NO"},
		"PartnerType": "xena_partnertype_company",
	}
)

updated = wrapper.update_partner(created["Id"], {"ShortDescription": "API kundetest (oppdatert)"})

# Add context to classify as customer/supplier
customer_context = wrapper.add_partner_context(
	created["Id"],
	"ContextType_Customer",
	invoice_email="apikunde@gj-system.no",
)

# One-call convenience creators
customer = wrapper.create_customer(
	name="API kundetest",
	postal_number="5258",
	street="Espelandsvegen 27",
	email="apikunde@gj-system.no",
)

supplier = wrapper.create_supplier(
	name="API leverandortest",
	postal_number="5258",
	email="apilev@gj-system.no",
)
```

For stricter payload control, prefer `PartnerDTO` / `PartnerAddressDTO` with `wrapper.partner.create(...)` and `wrapper.partner.update(...)`.
Raw dict payloads are still supported for full API coverage, but should only include fields accepted by Xena.

Partner ledger read helpers:

```python
# Direct partner-post query (maps to Transaction/Partner/{partnerId}/PartnerPost)
posts = wrapper.partner_ledger.get_posts(
	2247873100,
	context_type="customer",  # alias -> ContextType_Customer
	fiscal_date_from="2025-01-01",
	fiscal_date_to="2025-12-31",
	is_settled=False,
	post_type="invoice",  # alias -> PartnerPostType_CustomerInvoice
	is_parked=None,
	page=0,
	page_size=30,
	force_no_paging=False,
)

# Resolve fiscal period from year automatically.
posts_2025 = wrapper.partner_ledger.get_posts_for_year(
	2247873100,
	2025,
	context_type="ContextType_Customer",
	post_type="PartnerPostType_CustomerPayment",
)

# Convenience facades are also available on wrapper.
same_posts = wrapper.get_partner_posts(2247873100, context_type="ContextType_Customer")
customer_posts = wrapper.get_customer_partner_posts(2247873100)
supplier_posts = wrapper.get_supplier_partner_posts(2247873100)
```

Alias examples for `post_type`: `invoice`, `credit_note`, `payment`, `supplier_invoice`,
`supplier_credit_note`, `supplier_payment`.

Note: the current generated client does not expose a direct `fiscal_period_id` argument for this endpoint;
use `fiscal_date_from`/`fiscal_date_to` or `get_posts_for_year(...)`.

Strict safe settlement helper:

```python
# Build payload with strict validation before executing settlement.
payload = wrapper.build_partner_settlement_payload_safe(
	2247873100,
	[3020754398, 2900254804],
	pay_date="2025-12-19",
)

# Executes PUT /Order/Pay with validated payload.
result = wrapper.settle_partner_posts_safe(
	2247873100,
	[3020754398, 2900254804],
	pay_date="2025-12-19",
)
```

Safety behavior:
- Uses unsettled-partner-post lookup before settlement.
- Requires all selected post ids to be present in unsettled list.
- Requires selected post `RemainingAmount` sum to be exactly `0`.
- Auto-fetches currency-difference tag from `LedgerTag/CurrencyDifferenceTag`.
- Enforces strict rule: every `ledgerPosts[].Amount` is `0`.

Full settlement logic (implemented):
1. Resolve target partner id (for example by account number via `wrapper.get_partner_by_account_number(...)`).
2. Read open posts with `wrapper.get_partner_unsettled_posts(...)`.
3. Pick candidate post ids to settle (typically one invoice and one payment with opposite `RemainingAmount`).
4. Build safe payload with `wrapper.build_partner_settlement_payload_safe(...)`.
5. Inside payload builder, wrapper validates:
6. `partner_post_ids` is non-empty and has no duplicates.
7. Every id exists in current unsettled posts for the partner.
8. All selected posts share one `CurrencyAbbreviation`.
9. Sum of selected `RemainingAmount` (fallback `Amount`) equals `0` exactly (Decimal math).
10. Currency-difference ledger tag is fetched automatically from `LedgerTag/CurrencyDifferenceTag`.
11. `ledgerPosts` is constructed with strict zero-amount adjustment (`Amount = 0`).
12. `payDate` is converted to Xena fiscal-day int.
13. `partialSettleId` defaults to the first selected post id unless explicitly provided.
14. Execute settlement with `wrapper.settle_partner_posts_safe(...)`, which sends validated payload to `PUT /Order/Pay`.

Failure behavior:
1. Unknown post ids, mixed currency, non-zero sum, missing currency tag, or non-zero ledger adjustment raise `PartnerLedgerError` before write.
2. API-level validation errors are still returned by Xena if backend state changes between validation and submit.

Recommended usage pattern:
1. Use newest selected post date as `pay_date` (often payment date).
2. Preview payload first with `build_partner_settlement_payload_safe(...)`.
3. Submit with `settle_partner_posts_safe(...)` only after review in high-risk automation flows.

Live verified scenario:
1. Partner account: `*AccountNumber*` (`PartnerName`, partner id `2247873100`).
2. Selected unsettled posts: `3020754398` (`-6693.75`) and `2900254804` (`6693.75`).
3. Sum check: `0.00` (passes strict validation).
4. Settlement date: newest selected post date (`payDate=20420`, `2025-11-28`).
5. Built payload included:
6. `ledgerPosts[0].LedgerTagId=2180183781` (`Valutakursdifferanse`)
7. `ledgerPosts[0].Amount=0`
8. `currencyAbbreviation="NOK"`
9. `partnerPostIds=[3020754398, 2900254804]`
10. `partialSettleId=3020754398`
11. Execution result from `settle_partner_posts_safe(...)`: `Success=True`, `StatusCode=200`, `Errors=[]`.
