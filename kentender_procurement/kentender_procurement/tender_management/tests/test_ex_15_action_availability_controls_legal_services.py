# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-15 — doc 9 §25 / §7.1–7.3: backend **action availability** gates legal services.

Doc 9 §7.1: the UI must not decide legality alone; services consult
:func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`
before mutating state. This module proves that pattern on a **representative** set of actions
(``TND2_PUBLISH``, ``ADD2_CREATE``, ``TND2_CREATE_FROM_PACKAGE``); an exhaustive per-action matrix
remains workbench / API coverage (**P9-08**, **P9-25**, …).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_15_action_availability_controls_legal_services
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.service import get_action_availability
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.security.permissions.role_permission import RolePermissionService
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.tests.tm2_publish_fixture_chain import Tm2ApprovedForPublicationFixtureChain


def _map_avail_denial(dc: str) -> str:
	if dc == DenialCode.STD_AUTH_PERMISSION_DENIED.value:
		return DenialCode.AUTH_ROLE_DENIED.value
	return dc


class TestEx15ActionAvailabilityControlsLegalServices(Tm2ApprovedForPublicationFixtureChain, IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		RolePermissionService.ensure_matrix_seeded()

	def _package_code_ready_for_tender(self) -> str:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		return str(pc)

	def test_EX_15_publish_tender_denied_when_action_availability_denies(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		out = publish_tender("Administrator", tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_EX_15_publish_denial_aligns_with_get_action_availability(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		actx = {"granted_permissions": [], "object_exists": True}
		avail = get_action_availability("TND2_PUBLISH", "TM2 Tender", tcode, "Administrator", context=actx)
		self.assertFalse(avail.get("allowed"), avail)
		pub = publish_tender("Administrator", tcode, context=actx)
		self.assertFalse(pub.get("ok"), pub)
		want = _map_avail_denial(str(avail.get("denial_code") or ""))
		self.assertEqual(pub.get("denial_code"), want)

	def test_EX_15_create_addendum_denied_when_action_availability_denies(self) -> None:
		tcode = self._mk_approved_for_publication(seed_outputs=True)
		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		pub = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertTrue(pub.get("ok"), pub)

		payload = {
			"title": "EX-15 addendum gate probe",
			"reason": "Permission harness — no addendum shall be created.",
			"primary_impact_type": "BOQ Change",
		}
		out = create_addendum("Administrator", tcode, payload=payload, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_EX_15_create_tender_from_package_denied_when_action_availability_denies(self) -> None:
		pc = self._package_code_ready_for_tender()
		out = create_tender_from_package("Administrator", pc, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)
