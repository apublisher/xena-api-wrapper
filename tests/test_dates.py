from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone

from xena_api_wrappers.core.dates import from_fiscal_date_int, to_fiscal_date_int


class DatesTestCase(unittest.TestCase):
    def test_date_to_epoch_day(self) -> None:
        self.assertEqual(to_fiscal_date_int(date(1970, 1, 1)), 0)
        self.assertEqual(to_fiscal_date_int(date(2026, 1, 1)), 20454)

    def test_epoch_day_int_passthrough(self) -> None:
        self.assertEqual(to_fiscal_date_int(20454), 20454)

    def test_iso_string_date(self) -> None:
        self.assertEqual(to_fiscal_date_int("2026-01-01"), 20454)

    def test_norwegian_date_string(self) -> None:
        self.assertEqual(to_fiscal_date_int("31.03.2026"), 20543)

    def test_legacy_yyyymmdd_string(self) -> None:
        self.assertEqual(to_fiscal_date_int("20260101"), 20454)

    def test_timezone_aware_datetime_uses_business_timezone(self) -> None:
        # 23:30 at UTC-5 is next day at UTC+1.
        value = datetime(2026, 3, 31, 23, 30, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(
            to_fiscal_date_int(value, business_timezone=timezone(timedelta(hours=1))),
            to_fiscal_date_int(date(2026, 4, 1)),
        )

    def test_naive_datetime_requires_assume_timezone_when_disabled(self) -> None:
        with self.assertRaises(ValueError):
            to_fiscal_date_int(
                datetime(2026, 1, 1, 0, 30),
                business_timezone="Europe/Copenhagen",
                assume_timezone=None,
            )

    def test_reverse_conversion(self) -> None:
        self.assertEqual(from_fiscal_date_int(20454), date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
