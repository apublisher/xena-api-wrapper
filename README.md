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
report = wrapper.get_balance_data("2026-01-01", "2026-01-31")
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
