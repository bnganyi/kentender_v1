# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-009 — governance snapshot service (doc 7 §13.5 snapshot, §18).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_snapshot_gov009
"""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_snapshot import (
	generate_std_template_governance_snapshot,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


def _ensure_auditor_user(email: str) -> None:
	if frappe.db.exists("User", email):
		u = frappe.get_doc("User", email)
	else:
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "Gov009"
		u.enabled = 1
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
	u.add_roles("STD Template Auditor")
	frappe.db.commit()


class TestStdTemplateGovernanceSnapshotGov009(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV009-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		if frappe.db.exists("STD Template", self._code):
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()
		for email in ("gov009aud@example.com", "gov009plain@example.com"):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
				frappe.db.commit()
		frappe.set_user("Administrator")

	def test_std_gov_009_persists_snapshot_hash_json_and_event(self) -> None:
		ret = generate_std_template_governance_snapshot(self._code)
		self.assertTrue(ret["ok"])
		self.assertEqual(ret["std_template"], self._code)
		h = ret["snapshot_hash"]
		self.assertEqual(len(h), 64)
		self.assertTrue(all(c in "0123456789abcdef" for c in h))

		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.latest_governance_snapshot_hash, h)
		self.assertTrue(doc.latest_governance_snapshot_json.startswith('{"activation":'))
		self.assertEqual(
			hashlib.sha256(doc.latest_governance_snapshot_json.encode("utf-8")).hexdigest(),
			h,
		)

		snap = json.loads(doc.latest_governance_snapshot_json)
		self.assertEqual(snap["snapshot_type"], "STD_TEMPLATE_GOVERNANCE_BASELINE")
		self.assertEqual(snap["snapshot_version"], "V1")
		self.assertEqual(snap["std_template"]["template_code"], self._code)
		self.assertIn("package", snap)
		self.assertIn("lifecycle", snap)
		self.assertIn("validation", snap)
		self.assertIn("events", snap)
		self.assertEqual(snap["mappings"], [])

		codes = [r.event_code for r in (doc.lifecycle_events or [])]
		self.assertIn(gov.EVT_SNAPSHOT_GENERATED, codes)
		last = doc.lifecycle_events[-1]
		self.assertEqual(last.event_code, gov.EVT_SNAPSHOT_GENERATED)
		payload = json.loads(last.payload_json)
		self.assertEqual(payload["snapshot_hash"], h)
		self.assertEqual(payload["snapshot_type"], "STD_TEMPLATE_GOVERNANCE_BASELINE")

	def test_std_gov_009_guest_forbidden(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			generate_std_template_governance_snapshot(self._code)

	def test_std_gov_009_auditor_allowed(self) -> None:
		email = "gov009aud@example.com"
		_ensure_auditor_user(email)
		frappe.set_user(email)
		ret = generate_std_template_governance_snapshot(self._code)
		self.assertTrue(ret["ok"])
		self.assertEqual(ret["snapshot"]["generated_by"], email)

	def test_std_gov_009_user_without_role_forbidden(self) -> None:
		email = "gov009plain@example.com"
		if not frappe.db.exists("User", email):
			u = frappe.new_doc("User")
			u.email = email
			u.first_name = "Gov009Plain"
			u.enabled = 1
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
			frappe.db.commit()
		frappe.set_user(email)
		with self.assertRaises(frappe.PermissionError):
			generate_std_template_governance_snapshot(self._code)
