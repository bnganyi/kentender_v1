# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-02 — doc 9 §9.2 ``bind_tender_std_instance``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_02_bind_tender_std_instance
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP402BindTenderStdInstance(_P401Tm2Cleanup):
	def _mk_released_tm2(self) -> tuple[str, str]:
		"""Return ``(package_code, tender_code)`` for a Draft TM2 tender."""
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec_c)
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		self.assertTrue(tcode)
		return pc, tcode

	def test_p4_02_bind_creates_instance_binding_audit_and_status(self) -> None:
		_pc, tcode = self._mk_released_tm2()
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)

		spec_b = spec_for_action("TND2_BIND_STD")
		self.assertIsNotNone(spec_b)
		assert spec_b is not None

		out = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2_name = out.get("tm2_tender")
		si = out.get("tender_std_instance")
		self.assertTrue(si)
		self.assertTrue(out.get("tm2_tender_std_binding"))

		st = frappe.db.get_value("TM2 Tender", tm2_name, "status")
		self.assertEqual(st, "STD Instance Incomplete")
		self.assertEqual(int(frappe.db.get_value("TM2 Tender", tm2_name, "std_bound") or 0), 1)

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2_name, "event_type": "Tender STD Bound"},
			fields=["event_payload"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		pl = ev[0].get("event_payload")
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(pl.get("tender_std_instance_code"), si)

	def test_p4_02_auth_denied_without_permission(self) -> None:
		_pc, tcode = self._mk_released_tm2()
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = bind_tender_std_instance("Administrator", tcode, ver, prof, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_02_rejects_non_draft_status(self) -> None:
		_pc, tcode = self._mk_released_tm2()
		tm2_name = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		frappe.db.set_value("TM2 Tender", tm2_name, "status", "Published")
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		spec_b = spec_for_action("TND2_BIND_STD")
		assert spec_b is not None
		out = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value)
		frappe.db.set_value("TM2 Tender", tm2_name, "status", "Draft")

	def test_p4_02_second_bind_rejected(self) -> None:
		_pc, tcode = self._mk_released_tm2()
		from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE

		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		spec_b = spec_for_action("TND2_BIND_STD")
		assert spec_b is not None
		ctx = {"granted_permissions": [spec_b.required_permission]}
		out1 = bind_tender_std_instance("Administrator", tcode, ver, prof, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = bind_tender_std_instance("Administrator", tcode, ver, prof, context=ctx)
		self.assertFalse(out2.get("ok"))
