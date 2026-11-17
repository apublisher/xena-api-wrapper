from __future__ import annotations

from datetime import date
import json
import unittest
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import requests

from xena_api_wrappers import XenaApiWrapper
from xena_api_wrappers.workflows import ReconciliationError


class ReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wrapper = XenaApiWrapper(api_key="test-key", fiscal_id="42")
        self.wrapper.client.session.trust_env = False
        self.workflow = self.wrapper.reconciliation
        self.payload: Any = {"Count": 0, "Entities": []}
        self.status = 200
        self.raw_body: bytes | None = None
        send_patch = patch("requests.sessions.Session.send", side_effect=self._respond)
        self.send = send_patch.start()
        self.addCleanup(send_patch.stop)

    def _respond(self, request: requests.PreparedRequest, **kwargs: Any) -> requests.Response:
        _ = kwargs
        response = requests.Response()
        response.status_code = self.status
        response.headers["Content-Type"] = "application/json"
        response._content = self.raw_body if self.raw_body is not None else json.dumps(self.payload).encode()
        _ = response.content
        response.request = request
        response.url = request.url or ""
        return response

    def test_context_discovery_uses_generated_bank_client_and_paging(self) -> None:
        self.payload = {"Count": 1, "Entities": [{"Id": 7, "LedgerTagId": 19}]}
        self.assertIs(self.workflow, self.wrapper.reconciliation)
        self.assertEqual(
            self.workflow.get_bank_contexts(force_no_paging=False, page=2, page_size=5),
            self.payload,
        )
        request: requests.PreparedRequest = self.send.call_args.args[0]
        self.assertEqual(urlsplit(request.url or "").path, "/Api/Fiscal/42/LedgerTagBankContext")
        self.assertEqual(parse_qs(urlsplit(request.url or "").query), {
            "includeDefaults": ["False"],
            "listOptions.showDeactivated": ["False"],
            "listOptions.forceNoPaging": ["False"],
            "listOptions.page": ["2"],
            "listOptions.pageSize": ["5"],
        })
        self.assertEqual(request.headers["XenaAPIKey"], "test-key")
        self.assertEqual(self.send.call_args.kwargs["timeout"], 30)

    def test_transaction_read_preserves_history_and_never_triggers_import(self) -> None:
        self.payload = {"Count": 2, "Entities": [
            {"Id": 11, "FiscalDateDays": 19000, "BankSettlementId": 6, "Amount": -15},
            {"Id": 12, "FiscalDateDays": 20774, "BankSettlementId": None, "Amount": 20},
        ]}
        self.assertEqual(self.workflow.get_bank_transactions(7), self.payload)
        self.send.assert_called_once()
        request: requests.PreparedRequest = self.send.call_args.args[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(
            urlsplit(request.url or "").path,
            "/Api/Fiscal/42/LedgerTagBankContext/7/Posting",
        )
        query = parse_qs(urlsplit(request.url or "").query)
        self.assertEqual(query["showReconciled"], ["True"])
        self.assertEqual(query["listOptions.forceNoPaging"], ["True"])
        self.assertNotIn("fiscalDateFrom", query)
        self.assertNotIn("fiscalDateTo", query)

    def test_transaction_filters_convert_dates_and_pass_paging(self) -> None:
        self.workflow.get_bank_transactions(
            7, date_from="2026-01-01", date_to=date(2026, 12, 31),
            show_reconciled=False, reverse_date_sort=True,
            force_no_paging=False, page=1, page_size=25,
        )
        request: requests.PreparedRequest = self.send.call_args.args[0]
        query = parse_qs(urlsplit(request.url or "").query)
        self.assertEqual(query, {
            "fiscalDateFrom": ["20454"], "fiscalDateTo": ["20818"],
            "showReconciled": ["False"], "reverseDateSort": ["True"],
            "listOptions.showDeactivated": ["False"],
            "listOptions.forceNoPaging": ["False"],
            "listOptions.page": ["1"], "listOptions.pageSize": ["25"],
        })

    def test_invalid_filters_fail_before_network_io(self) -> None:
        cases: list[dict[str, Any]] = [
            {"bank_context_id": 0},
            {"bank_context_id": True},
            {"bank_context_id": 7, "page": -1},
            {"bank_context_id": 7, "page_size": 0},
            {"bank_context_id": 7, "date_from": "2026-12-31", "date_to": "2026-01-01"},
            {"bank_context_id": 7, "date_from": True},
            {"bank_context_id": 7, "show_reconciled": "false"},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.workflow.get_bank_transactions(**kwargs)
        self.send.assert_not_called()

    def test_malformed_pages_are_not_reported_as_empty_results(self) -> None:
        payloads: list[Any] = [{"Count": 0}, {"Count": 1, "Entities": [None]}, {"Entities": []}, []]
        for payload in payloads:
            self.payload = payload
            with self.subTest(payload=payload), self.assertRaises(ReconciliationError):
                self.workflow.get_bank_transactions(7)
        self.status = 403
        with self.assertRaises(requests.HTTPError):
            self.workflow.get_bank_contexts()

    def test_sync_api_key_uses_isolated_session_empty_body_and_no_redirects(self) -> None:
        self.wrapper.client.session.headers["Cookie"] = "must-not-be-forwarded"
        self.wrapper.client.session.headers["X-Unrelated"] = "private"
        self.raw_body = b""
        self.assertIsNone(self.workflow.sync_bank_transactions(timeout=45))
        self.send.assert_called_once()
        request = self.send.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            request.url,
            "https://xena-services-bankimport-api-v1-production.codezoo.io/mappings/actions/update",
        )
        self.assertIsNone(request.body)
        self.assertEqual(request.headers["XenaAPIKey"], "test-key")
        self.assertEqual(request.headers["x-fiscal-id"], "42")
        for header in ("Authorization", "Cookie", "X-Unrelated"):
            self.assertNotIn(header, request.headers)
        self.assertFalse(self.send.call_args.kwargs["allow_redirects"])
        self.assertEqual(self.send.call_args.kwargs["timeout"], 45)

    def test_sync_uses_current_bearer_after_external_token_replacement(self) -> None:
        self.wrapper.set_access_token("new-token")
        self.payload = {"updated": 0}
        self.assertEqual(self.workflow.sync_bank_transactions(), self.payload)
        request = self.send.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer new-token")
        self.assertNotIn("XenaAPIKey", request.headers)
        self.wrapper.set_access_token("replacement-token")
        self.workflow.sync_bank_transactions()
        self.assertEqual(
            self.send.call_args.args[0].headers["Authorization"], "Bearer replacement-token",
        )

    def test_sync_http_failures_and_timeouts_are_never_retried(self) -> None:
        for status in (401, 403, 429, 500):
            self.status = status
            self.send.reset_mock()
            with self.subTest(status=status), self.assertRaises(requests.HTTPError) as raised:
                self.workflow.sync_bank_transactions()
            self.assertEqual(raised.exception.response.status_code, status)
            self.send.assert_called_once()
        self.send.reset_mock()
        self.send.side_effect = requests.Timeout("test timeout")
        with self.assertRaises(requests.Timeout):
            self.workflow.sync_bank_transactions()
        self.send.assert_called_once()

    def test_sync_rejects_redirects_and_invalid_response_bodies(self) -> None:
        self.status = 302
        with self.assertRaises(ReconciliationError):
            self.workflow.sync_bank_transactions()
        self.send.assert_called_once()
        self.status = 200
        self.raw_body = b"<html>not an API response</html>"
        with self.assertRaises(requests.exceptions.JSONDecodeError):
            self.workflow.sync_bank_transactions()

    def test_sync_rejects_invalid_timeout_and_ambiguous_credentials(self) -> None:
        for timeout in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(timeout=timeout), self.assertRaises(ReconciliationError):
                self.workflow.sync_bank_transactions(timeout=timeout)
        self.wrapper.client.session.headers["Authorization"] = "Bearer another-token"
        with self.assertRaises(ReconciliationError):
            self.workflow.sync_bank_transactions()
        self.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
