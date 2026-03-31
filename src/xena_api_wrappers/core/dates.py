from __future__ import annotations

import re
from datetime import date, datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DateInput = date | datetime | int | str
DEFAULT_BUSINESS_TIMEZONE = "Europe/Copenhagen"
_UNIX_EPOCH = date(1970, 1, 1)
_NORWEGIAN_DATE_PATTERN = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def _to_zoneinfo(value: str | tzinfo) -> tzinfo:
    if isinstance(value, str):
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"Unknown timezone '{value}'. Install tzdata or pass a tzinfo object explicitly."
            ) from exc
    return value


def _as_epoch_day(value: date) -> int:
    return (value - _UNIX_EPOCH).days


def _parse_legacy_yyyymmdd(value: str) -> date:
    year = int(value[0:4])
    month = int(value[4:6])
    day = int(value[6:8])
    return date(year, month, day)


def _parse_date_string(value: str) -> date | datetime:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Date string cannot be empty")

    # Backward compatibility: accept legacy YYYYMMDD date strings.
    if cleaned.isdigit() and len(cleaned) == 8:
        return _parse_legacy_yyyymmdd(cleaned)

    norwegian_match = _NORWEGIAN_DATE_PATTERN.match(cleaned)
    if norwegian_match:
        day, month, year = map(int, norwegian_match.groups())
        return date(year, month, day)

    try:
        return date.fromisoformat(cleaned)
    except ValueError:
        pass

    iso_candidate = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError as exc:
        raise ValueError(f"Unsupported date string format: {value}") from exc


def from_fiscal_date_int(value: int) -> date:
    """Convert Xena fiscal epoch-day int to a Python date."""
    return date.fromordinal(_UNIX_EPOCH.toordinal() + value)


def to_fiscal_date_int(
    value: DateInput,
    *,
    business_timezone: str | tzinfo = DEFAULT_BUSINESS_TIMEZONE,
    assume_timezone: str | tzinfo | None = DEFAULT_BUSINESS_TIMEZONE,
) -> int:
    """Convert date-like input to Xena fiscal epoch-day int.

    Supported input:
    - date
    - datetime (aware or naive)
    - epoch-day int
    - ISO string
    - Norwegian date string (DD.MM.YYYY)

    For timezone-aware datetime values, conversion is done in business_timezone.
    For naive datetime values, assume_timezone is applied first.
    """
    if isinstance(value, datetime):
        business_tz = _to_zoneinfo(business_timezone)
        dt_value = value
        if dt_value.tzinfo is None:
            if assume_timezone is None:
                raise ValueError(
                    "Naive datetime requires assume_timezone, or pass assume_timezone=None to fail fast"
                )
            dt_value = dt_value.replace(tzinfo=_to_zoneinfo(assume_timezone))
        business_date = dt_value.astimezone(business_tz).date()
        return _as_epoch_day(business_date)

    if isinstance(value, date):
        return _as_epoch_day(value)

    if isinstance(value, int):
        # Keep epoch-day int as-is.
        return value

    parsed = _parse_date_string(value)
    if isinstance(parsed, datetime):
        return to_fiscal_date_int(
            parsed,
            business_timezone=business_timezone,
            assume_timezone=assume_timezone,
        )

    return _as_epoch_day(parsed)
