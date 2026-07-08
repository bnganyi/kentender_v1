# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-013 §22.3 — audit / snapshot matrix (doc 7 §22.3).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_audit
"""

from __future__ import annotations

import json
import unittest.mock
from datetime import datetime

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	approve_std_template,
	submit_std_template_for_approval,
)
from kentender_procurement.tender_management.services.std_template_governance_snapshot import (
	_build_snapshot_dict,
	_snapshot_hash,
	generate_std_template_governance_snapshot,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	record_std_template_usage,
)
from kentender_procurement.tender_management.services.std_template_governance_validation import (
	run_std_template_validation,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_lifecycle_gov007 import (
	_set_validated_guards,
)


def _package_hash(doc_name: str) -> str:
	ph = frappe.db.get_value("STD Template", doc_name, "package_hash")
	assert ph
	return str(ph)


class TestStdTemplateGovernanceSection223(IntegrationTestCase):
	"""Doc 7 §22.3 — matrix test names."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV013U-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		if frappe.db.exists("STD Template", self._code):
			frappe.db.delete("STD Template Usage", {"parent": self._code})
			frappe.db.set_value(
				"STD Template",
				self._code,
				{
					"tender_usage_count": 0,
					"locked_due_to_usage": 0,
					"mutation_blocked": 0,
				},
			)
			frappe.db.delete("STD Template Validation Finding", {"parent": self._code})
			frappe.db.delete("STD Template Lifecycle Event", {"parent": self._code})
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_import_event_written(self) -> None:
		seed_std_template_governance_for_existing_works_poc(self._code, force_mode="approved")
		d = frappe.get_doc("STD Template", self._code)
		rows = d.get("lifecycle_events") or []
		self.assertTrue(any(r.event_code == gov.EVT_IMPORTED for r in rows))
		row = next(r for r in rows if r.event_code == gov.EVT_IMPORTED)
		self.assertEqual((row.package_hash or "").strip(), (d.package_hash or "").strip())

	def test_validation_events_written(self) -> None:
		frappe.db.set_value("STD Template", self._code, "package_json", "{}")
		frappe.db.commit()
		run_std_template_validation(self._code)
		d = frappe.get_doc("STD Template", self._code)
		codes = [r.event_code for r in (d.lifecycle_events or [])]
		self.assertIn(gov.EVT_VALIDATION_STARTED, codes)
		self.assertIn(gov.EVT_VALIDATION_COMPLETED, codes)

	def test_approval_event_written(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="c")
		approve_std_template(self._code, "approved ok", override_reason="break-glass")
		d = frappe.get_doc("STD Template", self._code)
		row = next(r for r in (d.lifecycle_events or []) if r.event_code == gov.EVT_APPROVED)
		self.assertEqual((row.package_hash or "").strip(), ph)
		self.assertEqual(row.actor, "Administrator")
		self.assertEqual((row.reason or "").strip(), "approved ok")
		payload = json.loads(row.payload_json or "{}")
		self.assertIn("comments", payload)

	def test_activation_event_written(self) -> None:
		ph = _package_hash(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="c")
		approve_std_template(self._code, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		activate_std_template(self._code, reason="production")
		d = frappe.get_doc("STD Template", self._code)
		row = next(r for r in (d.lifecycle_events or []) if r.event_code == gov.EVT_ACTIVATED)
		self.assertEqual((row.package_hash or "").strip(), ph)
		self.assertTrue(row.reason)

	def test_mutation_blocked_event_written(self) -> None:
		frappe.db.set_value("STD Template", self._code, {"lifecycle_status": gov.STATUS_SUBMITTED})
		frappe.db.commit()
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"blocked": true}'
		with self.assertRaises(frappe.ValidationError):
			d.save()
		final = frappe.get_doc("STD Template", self._code)
		codes = [r.event_code for r in (final.lifecycle_events or [])]
		self.assertIn(gov.EVT_MUTATION_BLOCKED, codes)

	def test_usage_event_and_usage_row_written(self) -> None:
		ph = _package_hash(self._code)
		frappe.db.set_value(
			"STD Template",
			self._code,
			{
				"lifecycle_status": gov.STATUS_ACTIVE,
				"allowed_for_tender_creation": 1,
				"package_hash": ph,
				"activation_package_hash": ph,
				"approval_package_hash": ph,
				"latest_validation_package_hash": ph,
				"validation_is_current": 1,
			},
		)
		frappe.db.commit()
		record_std_template_usage(self._code, "Tender", tender="TND-AUD-1", payload={"k": 1})
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(len(d.template_usage or []), 1)
		codes = [r.event_code for r in (d.lifecycle_events or [])]
		self.assertIn(gov.EVT_USED_FOR_TENDER, codes)

	def test_snapshot_hash_generated(self) -> None:
		ret = generate_std_template_governance_snapshot(self._code)
		self.assertTrue(ret["ok"])
		self.assertEqual(len(ret["snapshot_hash"]), 64)
		d = frappe.get_doc("STD Template", self._code)
		self.assertEqual(d.latest_governance_snapshot_hash, ret["snapshot_hash"])

	def test_snapshot_hash_is_stable_for_same_data(self) -> None:
		fixed = datetime(2030, 6, 15, 12, 0, 0)
		path = (
			"kentender_procurement.tender_management.services.std_template_governance_snapshot.now_datetime"
		)
		doc = frappe.get_doc("STD Template", self._code)
		with unittest.mock.patch(path, return_value=fixed):
			snap = _build_snapshot_dict(doc, "STD_TEMPLATE_GOVERNANCE_BASELINE")
		h1 = _snapshot_hash(snap)
		h2 = _snapshot_hash(dict(snap))
		self.assertEqual(h1, h2)
