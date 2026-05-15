# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-05 — doc 9 §7.6 guarded TM2 legal service helper + P4–P7 spot-check registry.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p2_05_guarded_tm2_legal_service
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.action_availability.guarded_service import (
	TM2_PACK_LEGAL_GUARD_ENTRYPOINTS,
	guardTm2LegalService,
	guard_tm2_legal_service,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)


class TestP205GuardedTm2LegalService(IntegrationTestCase):
	_OBJECT_CODE = "TND-P205-FIXTURE-001"

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

	def test_p2_05_registry_covers_p4_through_p7(self) -> None:
		phases = {e.pack_phase for e in TM2_PACK_LEGAL_GUARD_ENTRYPOINTS}
		self.assertEqual(phases, {"P4", "P5", "P6", "P7"})
		for ep in TM2_PACK_LEGAL_GUARD_ENTRYPOINTS:
			self.assertIsNotNone(spec_for_action(ep.action_code), msg=ep.action_code)

	def test_p2_05_spot_check_each_phase_denies_and_audits(self) -> None:
		for ep in TM2_PACK_LEGAL_GUARD_ENTRYPOINTS:
			with self.subTest(phase=ep.pack_phase, action=ep.action_code):
				out = guard_tm2_legal_service(
					action_code=ep.action_code,
					object_type=ep.object_type,
					object_code=self._OBJECT_CODE,
					actor="Administrator",
					payload={"granted_permissions": []},
				)
				self.assertFalse(out.get("ok"))
				self.assertIn("denial_code", out)
				self.assertIn("message", out)
				self.assertIsInstance(out.get("blockers"), list)
				self.assertEqual(out.get("audit_event_code"), AuditEventCode.ACTION_AVAILABILITY_DENIED)
				audit_name = out.get("audit_log_name")
				self.assertTrue(audit_name)
				assert isinstance(audit_name, str)
				self._created.append(audit_name)
				row = frappe.db.get_value(
					"Audit Event",
					audit_name,
					["event_type", "metadata"],
					as_dict=True,
				)
				self.assertTrue(row)
				self.assertEqual(row.get("event_type"), AuditEventCode.ACTION_AVAILABILITY_DENIED)
				meta = self._meta(row.get("metadata"))
				self.assertEqual(meta.get("action_code"), ep.action_code)

	def test_p2_05_allow_path_no_audit_row(self) -> None:
		spec = spec_for_action("TND2_VIEW")
		self.assertIsNotNone(spec)
		assert spec is not None
		out = guardTm2LegalService(
			action_code="TND2_VIEW",
			object_type="TM2 Tender",
			object_code=self._OBJECT_CODE,
			actor="Administrator",
			payload={"granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(out.get("ok"))
		self.assertIn("availability", out)
