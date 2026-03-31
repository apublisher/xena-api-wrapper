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
