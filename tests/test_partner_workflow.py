from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.partner.partner import PartnerAddressDTO, PartnerDTO, PartnerError, PartnerWorkflow


class _FakePartner:
    def __init__(self) -> None:
        self.list_calls: list[dict[str, Any]] = []
        self.last_create_dto: dict[str, Any] | None = None
        self.last_update_dto: dict[str, Any] | None = None
        self.last_update_id: str | None = None
        self.last_context_create: dict[str, Any] | None = None
        self.last_gln_create: dict[str, Any] | None = None
        self.last_gln_update: dict[str, Any] | None = None
        self.last_gln_update_id: str | None = None
        self.last_gln_delete_id: int | None = None
        self.last_delivery_create: dict[str, Any] | None = None
        self.last_delivery_update: dict[str, Any] | None = None
        self.last_delivery_update_id: str | None = None
        self.last_delivery_delete_id: int | None = None

    def api_partner__get_get__api__fiscal_fiscal_id__partner(
        self,
        fiscal_id: str,
        query_string: str | None = None,
        excluded_id: int | None = None,
        include_default: bool | None = None,
        partner_context_type: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.list_calls.append(
            {
                "fiscal_id": fiscal_id,
                "query_string": query_string,
                "excluded_id": excluded_id,
                "include_default": include_default,
                "partner_context_type": partner_context_type,
                "show_deactivated": list_options_show_deactivated,
                "page": list_options_page,
                "page_size": list_options_page_size,
                "force_no_paging": list_options_force_no_paging,
            }
        )
        return {
            "Count": 2,
            "Entities": [
                {"Id": 101, "Name": "Acme", "ContextType": partner_context_type},
                {"Id": 102, "Name": "Nordic", "ContextType": partner_context_type},
            ],
        }

    def api_partner__get_get__api__fiscal_fiscal_id__partner_id(self, id: int, fiscal_id: str) -> dict[str, Any]:
        return {"Id": id, "Name": "One Partner", "FiscalId": fiscal_id, "OrgNumber": "999222888"}

    def api_partner__post_post__api__fiscal_fiscal_id__partner(self, dto: dict[str, Any], fiscal_id: str) -> dict[str, Any]:
        _ = fiscal_id
        self.last_create_dto = dto
        return {"Id": 555, **dto}

    def api_partner__put_put__api__fiscal_fiscal_id__partner_id(
        self,
        dto: dict[str, Any],
        fiscal_id: str,
        id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_update_dto = dto
        self.last_update_id = id
        return {"Id": int(id), **dto}

    def api_partner__get_by_account_number_get__api__fiscal_fiscal_id__partner__by_account_number_account_number(
        self,
        account_number: int,
        fiscal_id: str,
    ) -> dict[str, Any]:
        return {"Id": 999, "AccountNumber": account_number, "FiscalId": fiscal_id}

    def api_partner__get_context_types_get__api__fiscal_fiscal_id__partner__context_types(
        self,
        fiscal_id: str,
    ) -> list[str]:
        _ = fiscal_id
        return ["Customer", "Supplier", "Employee"]

    def api_partner_context__get_by_partner_get__api__fiscal_fiscal_id__partner_id__context(
        self,
        id: int,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = fiscal_id
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        return {
            "Count": 1,
            "Entities": [
                {"Id": 777, "PartnerId": id, "ContextType": "ContextType_Customer"},
            ],
        }

    def api_partner_context__post_post__api__fiscal_fiscal_id__partner_context(
        self,
        create_data: dict[str, Any],
        fiscal_id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_context_create = create_data
        return {"Id": 888, **create_data}

    def api_partner_gln_number__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id_gln_number(
        self,
        id: int,
        fiscal_id: str,
        query_string: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = fiscal_id
        _ = query_string
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        return {
            "Count": 1,
            "Entities": [{"Id": 333, "PartnerId": id, "GLN": "999222888", "Description": "EHF", "Attention": "EHF"}],
        }

    def api_partner_gln_number__get_get__api__fiscal_fiscal_id__partner_gln_number_id(self, id: int, fiscal_id: str) -> dict[str, Any]:
        _ = fiscal_id
        return {"Id": id, "PartnerId": 123, "GLN": "999222888", "Description": "EHF", "Attention": "EHF"}

    def api_partner_gln_number__post_post__api__fiscal_fiscal_id__partner_gln_number(self, article: dict[str, Any], fiscal_id: str) -> dict[str, Any]:
        _ = fiscal_id
        self.last_gln_create = article
        return {"Id": 333, **article}

    def api_partner_gln_number__put_put__api__fiscal_fiscal_id__partner_gln_number_id(self, article: dict[str, Any], fiscal_id: str, id: str) -> dict[str, Any]:
        _ = fiscal_id
        self.last_gln_update = article
        self.last_gln_update_id = id
        return {"Id": int(id), **article}

    def api_partner_gln_number__delete_delete__api__fiscal_fiscal_id__partner_gln_number_id(self, id: int, fiscal_id: str) -> dict[str, Any]:
        _ = fiscal_id
        self.last_gln_delete_id = id
        return {"Id": id, "Deleted": True}

    def api_partner_delivery_address__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id__delivery_address(
        self,
        id: int,
        fiscal_id: str,
        query_string: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = fiscal_id
        _ = query_string
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        return {
            "Count": 1,
            "Entities": [
                {
                    "Id": 444,
                    "PartnerId": id,
                    "Address": {"Name": "Delivery", "Street": "Gaten 1", "Zip": "5258", "City": "BLOMSTERDALEN", "CountryName": "NO"},
                    "Email": "jarle@aspectus.net",
                }
            ],
        }

    def api_partner_delivery_address__get_get__api__fiscal_fiscal_id__partner_delivery_address_id(
        self,
        id: int,
        fiscal_id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        return {"Id": id, "PartnerId": 123, "Address": {"Name": "Delivery"}}

    def api_partner_delivery_address__post_post__api__fiscal_fiscal_id__partner_delivery_address(
        self,
        address: dict[str, Any],
        fiscal_id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_delivery_create = address
        return {"Id": 444, **address}

    def api_partner_delivery_address__put_put__api__fiscal_fiscal_id__partner_delivery_address_id(
        self,
        address: dict[str, Any],
        fiscal_id: str,
        id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_delivery_update = address
        self.last_delivery_update_id = id
        return {"Id": int(id), **address}

    def api_partner_delivery_address__delete_delete__api__fiscal_fiscal_id__partner_delivery_address_id(
        self,
        id: int,
        fiscal_id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_delivery_delete_id = id
        return {"Id": id, "Deleted": True}


class PartnerWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_partner = _FakePartner()
        client = SimpleNamespace(partner=self.fake_partner)
        self.workflow = PartnerWorkflow(client, "104779")

    def test_get_all_forwards_filter_arguments(self) -> None:
        payload = self.workflow.get_all(
            query_string="acme",
            partner_context_type="Supplier",
            show_deactivated=True,
            page=2,
            page_size=25,
            force_no_paging=False,
            excluded_id=10,
            include_default=True,
        )

        self.assertEqual(payload["Count"], 2)
        self.assertEqual(self.fake_partner.list_calls[-1]["query_string"], "acme")
        self.assertEqual(self.fake_partner.list_calls[-1]["partner_context_type"], "Supplier")
        self.assertEqual(self.fake_partner.list_calls[-1]["show_deactivated"], True)
        self.assertEqual(self.fake_partner.list_calls[-1]["page"], 2)
        self.assertEqual(self.fake_partner.list_calls[-1]["page_size"], 25)

    def test_get_entities_reads_entities_list(self) -> None:
        entities = self.workflow.get_entities(partner_context_type="Customer")
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["Id"], 101)

    def test_get_entities_raises_on_invalid_shape(self) -> None:
        original = self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner

        def _invalid(*args: Any, **kwargs: Any) -> dict[str, Any]:
            _ = args
            _ = kwargs
            return {"Count": 1}

        self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner = _invalid  # type: ignore[method-assign]

        with self.assertRaises(PartnerError):
            self.workflow.get_entities()

        self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner = original  # type: ignore[method-assign]

    def test_context_helpers_apply_expected_types(self) -> None:
        self.workflow.get_customers()
        self.assertEqual(self.fake_partner.list_calls[-1]["partner_context_type"], "Customer")

        self.workflow.get_suppliers()
        self.assertEqual(self.fake_partner.list_calls[-1]["partner_context_type"], "Supplier")

        self.workflow.get_employees()
        self.assertEqual(self.fake_partner.list_calls[-1]["partner_context_type"], "Employee")

        self.workflow.get_all_contexts()
        self.assertEqual(self.fake_partner.list_calls[-1]["partner_context_type"], "All")

    def test_get_by_id_and_account_number(self) -> None:
        by_id = self.workflow.get_by_id(123)
        by_account = self.workflow.get_by_account_number(1500)

        self.assertEqual(by_id["Id"], 123)
        self.assertEqual(by_account["AccountNumber"], 1500)

    def test_get_context_types(self) -> None:
        values = self.workflow.get_context_types()
        self.assertEqual(values, ["Customer", "Supplier", "Employee"])

    def test_create_and_update(self) -> None:
        created = self.workflow.create({"ShortDescription": "API kundetest"})
        self.assertEqual(created["Id"], 555)
        self.assertEqual(self.fake_partner.last_create_dto, {"ShortDescription": "API kundetest"})

        updated = self.workflow.update(555, {"ShortDescription": "API kundetest 2"})
        self.assertEqual(updated["Id"], 555)
        self.assertEqual(self.fake_partner.last_update_id, "555")
        self.assertEqual(self.fake_partner.last_update_dto, {"ShortDescription": "API kundetest 2"})

    def test_get_contexts(self) -> None:
        payload = self.workflow.get_contexts(123)
        self.assertEqual(payload["Count"], 1)
        self.assertEqual(payload["Entities"][0]["PartnerId"], 123)

    def test_add_context(self) -> None:
        payload = self.workflow.add_context(123, "ContextType_Customer", invoice_email="  apikunde@gj-system.no  ")
        self.assertEqual(payload["ContextType"], "ContextType_Customer")
        self.assertEqual(self.fake_partner.last_context_create, {
            "PartnerId": 123,
            "ContextType": "ContextType_Customer",
            "InvoiceEmail": "apikunde@gj-system.no",
        })

    def test_add_context_rejects_invalid_email(self) -> None:
        with self.assertRaises(PartnerError):
            self.workflow.add_context(123, "ContextType_Customer", invoice_email="not-an-email")

    def test_create_trims_partner_email_fields(self) -> None:
        payload = self.workflow.create(
            {
                "ShortDescription": "API kundetest",
                "PartnerCustomerContextInvoiceMail": "  apikunde@gj-system.no  ",
            }
        )
        self.assertEqual(payload["PartnerCustomerContextInvoiceMail"], "apikunde@gj-system.no")

    def test_create_rejects_invalid_partner_email_fields(self) -> None:
        with self.assertRaises(PartnerError):
            self.workflow.create(
                {
                    "ShortDescription": "API kundetest",
                    "PartnerCustomerContextInvoiceMail": "bad email",
                }
            )

    def test_create_accepts_partner_dto(self) -> None:
        dto = PartnerDTO(
            short_description="API kundetest",
            address=PartnerAddressDTO(name="API kundetest", zip="5258", country_name="NO"),
            partner_type="xena_partnertype_company",
            partner_customer_context_invoice_mail="  apikunde@gj-system.no ",
        )

        payload = self.workflow.create(dto)
        self.assertEqual(payload["ShortDescription"], "API kundetest")
        self.assertEqual(payload["Address"]["Zip"], "5258")
        self.assertEqual(payload["PartnerCustomerContextInvoiceMail"], "apikunde@gj-system.no")

    def test_update_accepts_partner_dto(self) -> None:
        dto = PartnerDTO(
            short_description="API kundetest oppdatert",
            note="oppdatert via dto",
        )

        payload = self.workflow.update(555, dto)
        self.assertEqual(payload["Id"], 555)
        self.assertEqual(payload["ShortDescription"], "API kundetest oppdatert")
        self.assertEqual(payload["Note"], "oppdatert via dto")

    def test_create_customer(self) -> None:
        payload = self.workflow.create_customer(
            name="API kundetest",
            postal_number="5258",
            email="  apikunde@gj-system.no  ",
            street="Espelandsvegen 27",
        )
        self.assertEqual(payload["partner"]["ShortDescription"], "API kundetest")
        self.assertEqual(payload["partner"]["Address"]["Street"], "Espelandsvegen 27")
        self.assertEqual(payload["context"]["ContextType"], "ContextType_Customer")
        self.assertEqual(payload["context"]["InvoiceEmail"], "apikunde@gj-system.no")

    def test_create_supplier(self) -> None:
        payload = self.workflow.create_supplier(
            name="API leverandortest",
            postal_number="5258",
            email="  apilev@gj-system.no ",
        )
        self.assertEqual(payload["partner"]["ShortDescription"], "API leverandortest")
        self.assertEqual(payload["context"]["ContextType"], "ContextType_Supplier")
        self.assertEqual(payload["context"]["InvoiceEmail"], "apilev@gj-system.no")

    def test_get_gln_numbers_and_get_gln_number(self) -> None:
        rows = self.workflow.get_gln_numbers(123)
        self.assertEqual(rows["Count"], 1)
        one = self.workflow.get_gln_number(333)
        self.assertEqual(one["Id"], 333)

    def test_add_gln_defaults_attention_description_and_org_number(self) -> None:
        payload = self.workflow.add_gln_number(123)
        self.assertEqual(payload["GLN"], "999222888")
        self.assertEqual(payload["Description"], "EHF")
        self.assertEqual(payload["Attention"], "EHF")
        self.assertEqual(self.fake_partner.last_gln_create, {
            "PartnerId": 123,
            "GLN": "999222888",
            "Description": "EHF",
            "Attention": "EHF",
        })

    def test_add_gln_prefers_explicit_values(self) -> None:
        payload = self.workflow.add_gln_number(123, gln="777777777", description="B2B", attention="AP")
        self.assertEqual(payload["GLN"], "777777777")
        self.assertEqual(payload["Description"], "B2B")
        self.assertEqual(payload["Attention"], "AP")

    def test_add_gln_raises_when_no_gln_and_no_org_number(self) -> None:
        original = self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner_id

        def _no_org(id: int, fiscal_id: str) -> dict[str, Any]:
            _ = fiscal_id
            return {"Id": id, "Name": "No Org"}

        self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner_id = _no_org  # type: ignore[method-assign]
        with self.assertRaises(PartnerError):
            self.workflow.add_gln_number(123)
        self.fake_partner.api_partner__get_get__api__fiscal_fiscal_id__partner_id = original  # type: ignore[method-assign]

    def test_update_and_delete_gln_number(self) -> None:
        updated = self.workflow.update_gln_number(333, gln="111111111")
        self.assertEqual(updated["Id"], 333)
        self.assertEqual(updated["Description"], "EHF")
        self.assertEqual(self.fake_partner.last_gln_update_id, "333")

        deleted = self.workflow.delete_gln_number(333)
        self.assertEqual(deleted["Deleted"], True)
        self.assertEqual(self.fake_partner.last_gln_delete_id, 333)

    def test_get_delivery_addresses_and_single(self) -> None:
        rows = self.workflow.get_delivery_addresses(123)
        self.assertEqual(rows["Count"], 1)
        one = self.workflow.get_delivery_address(444)
        self.assertEqual(one["Id"], 444)

    def test_add_and_update_delivery_address_normalizes_email(self) -> None:
        created = self.workflow.add_delivery_address(
            {
                "PartnerId": 123,
                "Address": {"Name": "Navn", "Street": "Gaten 1", "Zip": "5258", "City": "BLOMSTERDALEN", "CountryName": "NO"},
                "Email": "  jarle@aspectus.net  ",
            }
        )
        self.assertEqual(created["Email"], "jarle@aspectus.net")

        updated = self.workflow.update_delivery_address(444, {"Email": "  jarle@aspectus.net "})
        self.assertEqual(updated["Id"], 444)
        self.assertEqual(self.fake_partner.last_delivery_update_id, "444")
        self.assertEqual(self.fake_partner.last_delivery_update, {"Email": "jarle@aspectus.net"})

    def test_delete_delivery_address(self) -> None:
        deleted = self.workflow.delete_delivery_address(444)
        self.assertEqual(deleted["Deleted"], True)
        self.assertEqual(self.fake_partner.last_delivery_delete_id, 444)

    def test_add_supplier_address_convenience(self) -> None:
        payload = self.workflow.add_supplier_address(
            123,
            name="Navn på leveringsstedet",
            street="Gaten 1",
            postal_number="5258",
            city="BLOMSTERDALEN",
            note="Notat",
            contact_name="Jarle",
            title="Sir",
            phone="99277029",
            email="  jarle@aspectus.net ",
        )
        self.assertEqual(payload["PartnerId"], 123)
        self.assertEqual(payload["Address"]["Street"], "Gaten 1")
        self.assertEqual(payload["Email"], "jarle@aspectus.net")


if __name__ == "__main__":
    unittest.main()
