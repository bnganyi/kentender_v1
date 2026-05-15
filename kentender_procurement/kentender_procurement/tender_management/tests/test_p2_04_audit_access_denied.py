# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-04 — doc 9 §7.6 ``audit_access_denied`` writes ``Audit Event`` rows.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p2_04_audit_access_denied
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.access_denied_audit import (
	auditAccessDenied,
	audit_access_denied,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestP204AuditAccessDenied(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		RolePermissionService.ensure_matrix_seeded()
		self._created: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in self._created:
			if name and frappe.db.exists("Audit Event", name):
				frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				out = json.loads(value)
			except Exception:
				return {}
			return out if isinstance(out, dict) else {}
		return {}

	def test_p2_04_denied_availability_writes_audit_event(self) -> None:
		availability = get_action_availability(
			"TND2_PUBLISH",
			"TM2 Tender",
			"TND-P204-001",
			"Administrator",
			context={"granted_permissions": []},
		)
		self.assertFalse(availability["allowed"])
		name = audit_access_denied("Administrator", "TND-P204-001", availability, payload={})
		self.assertTrue(name)
		assert name is not None
		self._created.append(name)

		row = frappe.db.get_value(
			"Audit Event",
			name,
			["event_type", "document_type", "document_name", "performed_by", "metadata"],
			as_dict=True,
		)
		self.assertTrue(row)
		self.assertEqual(row.get("event_type"), AuditEventCode.ACTION_AVAILABILITY_DENIED)
		self.assertEqual(row.get("document_type"), "TM2 Tender")
		self.assertEqual(row.get("document_name"), "TND-P204-001")
		meta = self._meta(row.get("metadata"))
		self.assertEqual(meta.get("denial_code"), DenialCode.STD_AUTH_PERMISSION_DENIED)
		self.assertEqual(meta.get("action_code"), "TND2_PUBLISH")
		self.assertEqual(meta.get("result"), "Denied")

	def test_p2_04_allowed_availability_is_no_op(self) -> None:
		availability = get_action_availability(
			"TND2_VIEW",
			"TM2 Tender",
			"TND-P204-002",
			"Administrator",
			context={"granted_permissions": ["PERM_TENDER_VIEW"]},
		)
		self.assertTrue(availability["allowed"])
		self.assertIsNone(audit_access_denied("Administrator", "TND-P204-002", availability, payload={}))

	def test_p2_04_low_risk_still_records_via_guard(self) -> None:
		"""§7.6 path forces ``audit_on_attempt`` so Medium/Low denials still persist."""
		availability = {
			"action_code": "TND2_VIEW",
			"object_type": "TM2 Tender",
			"object_code": "TND-P204-LOW",
			"allowed": False,
			"denial_code": DenialCode.AUTH_LOGIN_REQUIRED.value,
			"risk_level": "Low",
			"required_permission": "PERM_TENDER_VIEW",
			"user_message": "Login required.",
			"blockers": [],
			"confirmation_required": False,
			"reason_required": False,
		}
		name = auditAccessDenied("user-p204@example.com", "TND-P204-LOW", availability, payload={})
		self.assertTrue(name)
		assert name is not None
		self._created.append(name)
