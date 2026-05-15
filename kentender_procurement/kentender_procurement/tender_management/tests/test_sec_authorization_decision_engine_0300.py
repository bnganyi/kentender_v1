# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0300 — ``AuthorizationDecisionEngine.evaluate``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_authorization_decision_engine_0300
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestSecAuthorizationDecisionEngine0300(IntegrationTestCase):
	def setUp(self) -> None:
		RolePermissionService.ensure_matrix_seeded()

	def test_sec_0300_unknown_action_denied(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"NOT_A_REAL_ACTION",
			"Tender",
			"T-1",
			context={"granted_permissions": [DenialCode.PUBLISH_PERMISSION_DENIED]},
		)
		self.assertFalse(res["allowed"])
		assert res.get("allowed") is False
		self.assertEqual(res.get("denial_code"), DenialCode.STD_AUTH_PERMISSION_DENIED)

	def test_sec_0300_missing_actor_denied(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"user_does_not_exist_0300_xx",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={"granted_permissions": ["PERM_TENDER_PUBLISH"]},
		)
		self.assertFalse(res["allowed"])

	def test_sec_0300_publish_allowed_via_grants(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={"granted_permissions": ["PERM_TENDER_PUBLISH"]},
		)
		self.assertTrue(res["allowed"])
		assert res.get("allowed") is True
		self.assertEqual(res["required_permission"], "PERM_TENDER_PUBLISH")
		self.assertEqual(res["risk_level"], "Critical")
		self.assertTrue(res.get("audit_on_attempt"))
		self.assertTrue(res.get("requires_confirmation"))

	def test_sec_0300_permission_denied(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={"granted_permissions": ["PERM_TENDER_VIEW"]},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("denial_code"), DenialCode.STD_AUTH_PERMISSION_DENIED)

	def test_sec_0300_security_role_codes_union(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={"security_role_codes": ["ROLE_PROCUREMENT_OFFICER"]},
		)
		self.assertTrue(res["allowed"])

	def test_sec_0300_object_scope_denied(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"object_scope_ok": False,
			},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)

	def test_sec_0300_negative_rule_denied(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"negative_denial_codes": [DenialCode.PUBLISH_READINESS_NOT_READY],
			},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("denial_code"), DenialCode.PUBLISH_READINESS_NOT_READY)

	def test_sec_0300_website_user_context_grants_for_portal(self) -> None:
		import frappe

		from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
			spec_for_action,
		)

		email = f"wsec-{frappe.generate_hash(length=6)}@example.com"
		u = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "WSec",
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		u.insert(ignore_permissions=True)
		u.append("roles", {"role": "Customer"})
		u.save(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc("User", u.name, force=True, ignore_permissions=True)
			if frappe.db.exists("User", u.name)
			else None
		)
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		res0 = AuthorizationDecisionEngine.evaluate(
			u.name,
			"BID2_SUBMIT",
			"TM2 Tender",
			"TND-ANY",
			context={"object_exists": True},
		)
		self.assertFalse(res0["allowed"])
		self.assertIn("Website User", str(res0.get("message") or ""))

		res1 = AuthorizationDecisionEngine.evaluate(
			u.name,
			"BID2_SUBMIT",
			"TM2 Tender",
			"TND-ANY",
			context={"object_exists": True, "granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(res1["allowed"])

	def test_sec_0300_denied_matches_pack_shape(self) -> None:
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"PUBLISH_TENDER",
			"Tender",
			"T-1",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"state_allows": False,
				"state_denial_code": DenialCode.PUBLISH_READINESS_NOT_READY,
				"state_message": "Tender cannot be published until publication readiness is Ready.",
			},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("action_code"), "PUBLISH_TENDER")
		self.assertEqual(res.get("required_permission"), "PERM_TENDER_PUBLISH")
		self.assertEqual(res.get("denial_code"), DenialCode.PUBLISH_READINESS_NOT_READY)
		self.assertIn("readiness", (res.get("message") or "").lower())
