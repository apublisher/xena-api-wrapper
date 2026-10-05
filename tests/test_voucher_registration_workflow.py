from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
import os
import unittest
from typing import Any, Callable
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import requests
from xena_api_wrappers import OAuthRequiredError, XenaApiWrapper, XenaBearerCredentials, XenaCredentials
from xena_api_wrappers.core.authentication import require_bearer
from xena_api_wrappers.workflows.bookkeeping import (
    RegistrationInboxError,
    RegistrationInboxWorkflow,
    VoucherRegistrationError,
    VoucherRegistrationWorkflow,
)
from xena_api_wrappers.workflows.document import DocumentError


class _RecordingSession(requests.Session):
    """Exercise real generated methods and request preparation without network I/O."""

    def __init__(self) -> None:
        super().__init__()
        self.trust_env = False
        self.calls: list[requests.PreparedRequest] = []
        self.replies: deque[tuple[Any, int]] = deque()

    def reply(self, payload: Any, status: int = 200) -> None:
        self.replies.append((payload, status))

    def send(self, request: requests.PreparedRequest, **kwargs: Any) -> requests.Response:
        _ = kwargs
        self.calls.append(request)
        if not self.replies:
            raise AssertionError("Unexpected network request")
        payload, status = self.replies.popleft()
        response = requests.Response()
        response.status_code = status
        response.headers["Content-Type"] = "application/json"
        response._content = json.dumps(payload).encode("utf-8")
        _ = response.content
        response.request = request
        response.url = request.url or ""
        return response


class _WorkflowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.wrapper = XenaApiWrapper(access_token="test-access-token", fiscal_id="42")
        self.session = _RecordingSession()
        self.session.auth = self.wrapper.client.session.auth
        self.wrapper.client.session = self.session
        self.workflow = self.wrapper.voucher_registration


class RegistrationTests(_WorkflowTestCase):
    def test_inbox_is_a_separate_shared_workflow(self) -> None:
        inbox = self.wrapper.registration_inbox
        self.assertIsInstance(inbox, RegistrationInboxWorkflow)
        self.assertIs(inbox, self.wrapper.registration_inbox)
        with patch.object(inbox, "get_all", return_value={"Count": 0, "Entities": []}) as get_all:
            self.assertEqual(self.workflow.get_all(resource_id=9), {"Count": 0, "Entities": []})
            self.assertEqual(get_all.call_args.kwargs["resource_id"], 9)
        with patch.object(inbox, "get_entities", return_value=[]) as get_entities:
            self.assertEqual(self.workflow.get_entities(resource_id=9), [])
            get_entities.assert_called_once_with(resource_id=9)
        with patch.object(inbox, "get_by_id", return_value={"Id": 17}) as get_by_id:
            self.assertEqual(self.workflow.get_inbox_item(17), {"Id": 17})
            get_by_id.assert_called_once_with(17)

    def test_inbox_direct_reads_and_response_errors(self) -> None:
        inbox = self.wrapper.registration_inbox
        self.session.reply({"Count": 1, "Entities": [{"Id": 17}]})
        self.assertEqual(inbox.get_entities(resource_id=9), [{"Id": 17}])
        self.session.reply({"Id": 17, "DocumentId": 20})
        self.assertEqual(inbox.get_by_id(17)["DocumentId"], 20)
        self.session.reply({"Entities": "invalid"})
        with self.assertRaises(RegistrationInboxError):
            inbox.get_entities(resource_id=9)
        self.assertIn(VoucherRegistrationError, RegistrationInboxError.__mro__)

    def test_standalone_registration_keeps_inbox_shortcuts(self) -> None:
        workflow = VoucherRegistrationWorkflow(self.wrapper.client, "42")
        self.session.reply({"Id": 17})
        self.assertEqual(workflow.get_inbox_item(17), {"Id": 17})

    def test_list_uses_captured_endpoint_filters_and_pagination(self) -> None:
        self.session.reply({"Count": 1, "Entities": [{"Id": 17, "DocumentId": 20}]})
        result = self.workflow.get_all(
            resource_id=9, page=1, page_size=10, is_new=True, is_all_approved=False,
        )
        self.assertEqual(result["Count"], 1)
        request = self.session.calls[0]
        self.assertEqual(urlsplit(request.url or "").path, "/Api/Fiscal/42/ResourceInboxDocumentRelation/ByResource")
        self.assertEqual(parse_qs(urlsplit(request.url or "").query), {
            "resourceId": ["9"], "Page": ["1"], "PageSize": ["10"],
            "ForceNoPaging": ["false"], "ShowDeactivated": ["false"],
            "isNew": ["true"], "isParked": ["false"], "isAllApproved": ["false"],
        })
        self.assertEqual(request.headers["Authorization"], "Bearer test-access-token")
        self.assertNotIn("XenaAPIKey", request.headers)

    def test_entities_and_inbox_lookup(self) -> None:
        self.session.reply({"Count": 1, "Entities": [{"Id": 17}]})
        self.assertEqual(self.workflow.get_entities(resource_id=9), [{"Id": 17}])
        self.session.reply({"Id": 17, "DocumentId": 20})
        self.assertEqual(self.workflow.get_inbox_item(17)["DocumentId"], 20)
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/ResourceInboxDocumentRelation/17")

    def test_initial_header_and_summary(self) -> None:
        header: dict[str, Any] = {"Id": 30, "Version": 1, "SupplierInvoiceNumber": "TEST-1", "FiscalDateDays": 20600}
        self.session.reply(header)
        self.assertEqual(self.workflow.get_for_inbox(17), header)
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/ResourceInbox/17/VoucherPreview")
        self.session.reply({"BookkeepingResult": {"IsReadyForBookkeeping": False, "Errors": ["Missing account"]}})
        summary = self.workflow.get_summary(30)
        self.assertFalse(summary["BookkeepingResult"]["IsReadyForBookkeeping"])
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/VoucherPreview/30/Summary")

    def test_header_fields_merge_fresh_dto_and_convert_dates(self) -> None:
        original: dict[str, Any] = {"Id": 30, "Version": 7, "PartnerId": 8, "UnknownField": {"keep": True}, "Description": "old"}
        self.session.reply(original)
        self.session.reply({**original, "Description": None})
        self.workflow.update_fields(30, fiscal_date="01.01.1970", pay_date="02.01.1970", Description=None)
        payload = json.loads(self.session.calls[-1].body or "{}")
        self.assertEqual(payload["Version"], 7)
        self.assertEqual(payload["UnknownField"], {"keep": True})
        self.assertEqual(payload["FiscalDateDays"], 0)
        self.assertEqual(payload["PayDateDays"], 1)
        self.assertIsNone(payload["Description"])
        self.assertEqual(original["Description"], "old")
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/VoucherPreview/30")

    def test_cost_line_crud_and_merge(self) -> None:
        self.session.reply({"Id": 31, "Version": 0, "VoucherPreviewId": 30})
        created = self.workflow.create_line(30)
        self.assertEqual(json.loads(self.session.calls[-1].body or "{}"), {"VoucherPreviewId": 30})
        self.assertEqual(created["Id"], 31)
        original: dict[str, Any] = {**created, "Version": 2, "Amount": 885, "AccountNumber": 6810, "UnknownField": [1]}
        self.session.reply(original)
        self.session.reply({**original, "Amount": 85})
        self.workflow.update_line_fields(31, Amount=85, Description=None)
        payload = json.loads(self.session.calls[-1].body or "{}")
        self.assertEqual(payload["Version"], 2)
        self.assertEqual(payload["Amount"], 85)
        self.assertEqual(payload["UnknownField"], [1])
        self.assertIsNone(payload["Description"])
        self.assertEqual(original["Amount"], 885)
        second = {"VoucherPreviewId": 30, "Amount": 800, "AccountNumber": 6550}
        before = deepcopy(second)
        self.session.reply({"Id": 32, "Version": 0, **second})
        self.workflow.create_line(30, second)
        self.assertEqual(second, before)
        self.session.reply({"Success": True})
        self.workflow.delete_line(32)
        self.assertEqual(self.session.calls[-1].method, "DELETE")
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/LedgerPostPreview/32")

    def test_line_list_uses_generated_method(self) -> None:
        self.session.reply({"Count": 1, "Entities": [{"Id": 31}]})
        self.assertEqual(self.workflow.get_line_entities(30), [{"Id": 31}])
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/VoucherPreview/30/LedgerPostPreview")

    def test_invalid_dto_and_ids_do_not_send_requests(self) -> None:
        invalid: list[Callable[[], Any]] = [
            lambda: self.workflow.update(30, {}),
            lambda: self.workflow.update(30, {"Id": 29, "Version": 1}),
            lambda: self.workflow.update(1, {"Id": True, "Version": 1}),
            lambda: self.workflow.update(30, {"Id": 30}),
            lambda: self.workflow.update_line(31, {"Id": 31, "Version": True}),
            lambda: self.workflow.create_line(30, {"VoucherPreviewId": 29}),
            lambda: self.workflow.create_line(1, {"VoucherPreviewId": True}),
            lambda: self.workflow.create_line(30, {"Id": 31}),
            lambda: self.workflow.update_fields(30),
            lambda: self.workflow.update_fields(30, fiscal_date=0, FiscalDateDays=0),
            lambda: self.workflow.update_line_fields(31),
            lambda: self.workflow.update_fields(30, Version=99),
            lambda: self.workflow.update_line_fields(31, VoucherPreviewId=99),
            lambda: self.workflow.get_all(resource_id=9, page=-1),
            lambda: self.workflow.get_all(resource_id=9, is_new="false"),  # type: ignore[arg-type]
            lambda: self.workflow.get_lines(30, page=-1),
            lambda: self.workflow.delete_line(True),
        ]
        for operation in invalid:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()
        self.assertEqual(self.session.calls, [])

    def test_unexpected_response_shapes_are_explicit(self) -> None:
        self.session.reply({"Entities": "not-a-list"})
        with self.assertRaises(VoucherRegistrationError):
            self.workflow.get_entities(resource_id=9)
        self.session.reply("not-a-dto")
        with self.assertRaises(VoucherRegistrationError):
            self.workflow.get_by_id(30)

    def test_http_errors_and_redirect_are_not_silenced(self) -> None:
        self.session.reply({"error": "expired"}, status=401)
        with self.assertRaises(requests.HTTPError):
            self.workflow.get_by_id(30)
        self.session.reply({}, status=302)
        with self.assertRaises(VoucherRegistrationError):
            self.workflow.get_all(resource_id=9)

    def test_no_bookkeeping_or_excluded_operations(self) -> None:
        for name in ("bookkeep", "get_contra_lines", "get_difference_lines", "update_partner_context"):
            self.assertFalse(hasattr(self.workflow, name))


class DocumentTests(_WorkflowTestCase):
    def test_document_and_last_version_use_distinct_ids(self) -> None:
        self.session.reply({"Id": 20, "LastVersionId": 21})
        self.assertEqual(self.wrapper.document.get_by_id(20)["LastVersionId"], 21)
        self.session.reply({"Id": 21, "PageCount": 2})
        url = self.wrapper.document.get_preview_url_for_document(20, width=800, page=2)
        self.assertEqual(urlsplit(self.session.calls[-1].url or "").path, "/Api/Fiscal/42/Document/Document/20/LastVersion")
        self.assertEqual(urlsplit(url).path, "/Api/Blob/Fiscal/42/ScaledImage/21")
        self.assertEqual(parse_qs(urlsplit(url).query), {
            "width": ["800"], "page": ["2"], "access_token": ["test-access-token"],
        })

    def test_preview_uses_rotated_token_on_existing_workflow(self) -> None:
        document = self.wrapper.document
        self.wrapper.set_access_token("rotated-test-token")
        self.assertEqual(parse_qs(urlsplit(document.get_preview_url(21)).query)["access_token"], ["rotated-test-token"])
        self.assertIs(document, self.wrapper.document)
        self.assertIs(self.workflow, self.wrapper.voucher_registration)
        self.session.reply({"Count": 0, "Entities": []})
        self.wrapper.registration_inbox.get_all(resource_id=9)
        self.assertEqual(self.session.calls[-1].headers["Authorization"], "Bearer rotated-test-token")
        self.assertNotIn("rotated-test-token", repr(self.wrapper))

    def test_invalid_version_response_and_preview_parameters(self) -> None:
        self.session.reply({"Id": None})
        with self.assertRaises(DocumentError):
            self.wrapper.document.get_preview_url_for_document(20)
        for kwargs in ({"width": 0}, {"page": 0}, {"page": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.wrapper.document.get_preview_url(21, **kwargs)

    def test_preview_token_is_url_encoded(self) -> None:
        self.wrapper.set_access_token("test+token/value==")
        url = self.wrapper.document.get_preview_url(21)
        self.assertEqual(parse_qs(urlsplit(url).query)["access_token"], ["test+token/value=="])
        self.assertIn("test%2Btoken%2Fvalue%3D%3D", url)


class AuthenticationTests(unittest.TestCase):
    def test_api_key_behavior_and_guard(self) -> None:
        wrapper = XenaApiWrapper(api_key="test-api-key", fiscal_id="42")
        session = _RecordingSession()
        session.headers.update(wrapper.client.session.headers)
        wrapper.client.session = session
        workflow = wrapper.voucher_registration
        operations: list[Callable[[], Any]] = [
            lambda: wrapper.registration_inbox.get_all(resource_id=9),
            lambda: wrapper.registration_inbox.get_entities(resource_id=9),
            lambda: wrapper.registration_inbox.get_by_id(17),
            lambda: workflow.get_all(resource_id=9),
            lambda: workflow.get_entities(resource_id=9),
            lambda: workflow.get_inbox_item(17),
            lambda: workflow.get_for_inbox(17),
            lambda: workflow.get_by_id(30),
            lambda: workflow.update(30, {"Id": 30, "Version": 1}),
            lambda: workflow.update_fields(30, Description="test"),
            lambda: workflow.get_lines(30),
            lambda: workflow.get_line_entities(30),
            lambda: workflow.get_line(31),
            lambda: workflow.create_line(30),
            lambda: workflow.update_line(31, {"Id": 31, "Version": 1}),
            lambda: workflow.update_line_fields(31, Amount=1),
            lambda: workflow.delete_line(31),
            lambda: workflow.get_summary(30),
            lambda: wrapper.document.get_by_id(20),
            lambda: wrapper.document.get_last_version(20),
            lambda: wrapper.document.get_preview_url(21),
            lambda: wrapper.document.get_preview_url_for_document(20),
        ]
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(OAuthRequiredError) as caught:
                operation()
            self.assertEqual(caught.exception.code, "oauth_required")
            self.assertTrue(caught.exception.requires_oauth)
        self.assertEqual(session.calls, [])
        session.reply({"Id": 8})
        self.assertEqual(wrapper.partner.get_by_id(8), {"Id": 8})
        self.assertEqual(session.calls[-1].headers["XenaAPIKey"], "test-api-key")
        wrapper.set_access_token("new-test-token")
        session.reply({"Id": 30})
        self.assertEqual(workflow.get_by_id(30), {"Id": 30})
        self.assertNotIn("XenaAPIKey", session.calls[-1].headers)

    def test_guard_checks_current_session_not_constructor_only(self) -> None:
        wrapper = XenaApiWrapper(access_token="test-token", fiscal_id="42")
        wrapper.client.session.auth = None
        wrapper.client.session.trust_env = False
        with self.assertRaises(OAuthRequiredError):
            wrapper.document.get_preview_url(21)
        wrapper.client.session.headers["Authorization"] = "Bearer current-test-token"
        self.assertEqual(require_bearer(wrapper.client), "current-test-token")
        wrapper.client.session.headers["XenaAPIKey"] = "other-test-key"
        with self.assertRaises(OAuthRequiredError):
            require_bearer(wrapper.client)

    def test_bearer_credentials_validation_and_repr(self) -> None:
        credentials = XenaBearerCredentials("test-token", "42")
        self.assertNotIn("test-token", repr(credentials))
        self.assertEqual(require_bearer(XenaApiWrapper(credentials=credentials).client), "test-token")
        for token in ("", "Bearer test-token", "bad\ntoken"):
            with self.subTest(token=token), self.assertRaises(ValueError):
                XenaApiWrapper(access_token=token, fiscal_id="42")
        with self.assertRaises(ValueError):
            XenaApiWrapper(access_token="test-token")
        with self.assertRaises(ValueError):
            XenaApiWrapper(api_key="key", access_token="test-token", fiscal_id="42")
        with self.assertRaises(ValueError):
            XenaApiWrapper(credentials=XenaCredentials("key", "42"), access_token="test-token")

    def test_legacy_credentials_and_factory_contract(self) -> None:
        calls: list[tuple[str, str]] = []

        def factory(secret: str, fiscal_id: str) -> object:
            calls.append((secret, fiscal_id))
            return object()

        XenaApiWrapper(credentials=XenaCredentials("key", "42"), client_factory=factory)
        XenaApiWrapper(access_token="test-token", fiscal_id="42", client_factory=factory)
        self.assertEqual(calls, [("key", "42"), ("test-token", "42")])

    def test_environment_auth_is_explicit(self) -> None:
        with patch.dict(os.environ, {"XENA_ACCESS_TOKEN": "test-token", "XENA_FISCAL_ID": "42"}, clear=True):
            wrapper = XenaApiWrapper.from_env(prefix="XENA_")
            self.assertEqual(require_bearer(wrapper.client), "test-token")
        with patch.dict(os.environ, {"API_KEY": "key", "FISCAL_ID": "42"}, clear=True):
            self.assertEqual(XenaApiWrapper.from_env().client.api_key, "key")
        with patch.dict(os.environ, {"API_KEY": "key", "ACCESS_TOKEN": "test-token", "FISCAL_ID": "42"}, clear=True):
            with self.assertRaises(ValueError):
                XenaApiWrapper.from_env()

    def test_missing_session_is_an_actionable_oauth_error(self) -> None:
        with self.assertRaises(OAuthRequiredError):
            require_bearer(object())


if __name__ == "__main__":
    unittest.main()
