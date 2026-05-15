# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B10 — release path integration coverage (doc 2 sec. 21).

Consolidates end-to-end and failure-mode checks for ``release_procurement_package_to_tender``
(happy path, permissions, STD resolution failures, XMV blocks, configuration/audit fail-closed).

Run:
	bench --site <site> run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_planning_tender_handoff_release_integration_b10
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	release_procurement_package_to_tender,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	HandoffStdResolution,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestPlanningTenderHandoffReleaseIntegrationB10(_ReleaseProcurementPackageHandoffFixtures):
	def _ready_package_fixture(self):
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		return plan, tpl, pkg

	def test_b10_s21_happy_path_structured_result_and_lineage(self) -> None:
		"""§21 success path: structured handoff result + PT-HANDOFF-AC-002 linkage.

		Also cited as **§E E1** cross-cut evidence (IMPLEMENTATION_TRACKER §E).
		"""
		_, _, pkg = self._ready_package_fixture()
		out = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(out.get("existing"))
		self.assertEqual(out.get("std_template"), TEMPLATE_CODE)
		self.assertEqual(out.get("tender_status"), "Draft")
		for key in ("tender", "tender_reference", "std_template", "tender_status"):
			self.assertIn(key, out, f"missing structured key {key}")

		tn = out["tender"]
		self._created.append(("TM2 Tender", tn))
		row = frappe.db.get_value(
			"TM2 Tender",
			tn,
			[
				"procurement_package",
				"procurement_plan",
				"configuration_json",
				"planning_handoff_snapshot_sha256",
			],
			as_dict=True,
		)
		self.assertEqual(row.procurement_package, pkg.name)
		self.assertEqual(row.procurement_plan, pkg.plan_id)
		self.assertTrue((row.configuration_json or "").strip())
		self.assertTrue((row.planning_handoff_snapshot_sha256 or "").strip())

	def test_b10_s21_package_not_found(self) -> None:
		out = release_procurement_package_to_tender("PKG-NONEXISTENT-B10-99999")
		self.assertFalse(out.get("ok"))
		self.assertIn("not found", (out.get("message") or "").lower())

	def test_b10_s21_blank_package_name(self) -> None:
		out = release_procurement_package_to_tender("   ")
		self.assertFalse(out.get("ok"))
		self.assertIn("required", (out.get("message") or "").lower())

	def test_b10_s21_no_read_permission_on_package(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		_orig = frappe.has_permission

		def _fake(*args, **kwargs):
			if (
				len(args) >= 2
				and args[0] == "Procurement Package"
				and args[1] == "read"
				and kwargs.get("doc") == pkg.name
			):
				return False
			return _orig(*args, **kwargs)

		with patch.object(frappe, "has_permission", side_effect=_fake):
			out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("not permitted", (out.get("message") or "").lower())

	def test_b10_s21_no_create_permission_on_tender(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		_orig = frappe.has_permission

		def _fake(*args, **kwargs):
			if len(args) >= 2 and args[0] == "TM2 Tender" and args[1] == "create":
				return False
			return _orig(*args, **kwargs)

		with patch.object(frappe, "has_permission", side_effect=_fake):
			out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("not permitted", (out.get("message") or "").lower())

	def test_b10_s21_active_tender_returns_existing(self) -> None:
		"""§21: active tender already exists — return existing (idempotent)."""
		_, _, pkg = self._ready_package_fixture()
		out1 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out1.get("ok"), out1)
		tn = out1["tender"]
		self._created.append(("TM2 Tender", tn))

		out2 = release_procurement_package_to_tender(pkg.name)
		self.assertTrue(out2.get("ok"), out2)
		self.assertTrue(out2.get("existing"))
		self.assertEqual(out2.get("tender"), tn)

	def test_b10_s21_package_not_releasable_status(self) -> None:
		upsert_std_template()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Draft")

		out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("ready for tender", (out.get("message") or "").lower())

	def test_b10_s21_std_template_unresolved(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		fake = HandoffStdResolution(std_name=None, path="unresolved", ambiguous_candidates=())
		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.resolve_std_template_for_handoff",
			return_value=fake,
		):
			out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertIn("no std template", (out.get("message") or "").lower())
		self.assertEqual(out.get("std_resolution_path"), "unresolved")
		self.assertFalse(
			bool(frappe.get_all("TM2 Tender", filters={"procurement_package": pkg.name}, limit=1)),
			"must not persist tender when STD unresolved",
		)

	def test_b10_s21_std_template_ambiguous_blocked(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		fake = HandoffStdResolution(
			std_name=None,
			path="ambiguous",
			ambiguous_candidates=("STD-A", "STD-B"),
		)
		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.resolve_std_template_for_handoff",
			return_value=fake,
		):
			out = release_procurement_package_to_tender(pkg.name)
		self.assertFalse(out.get("ok"))
		self.assertFalse(
			bool(frappe.get_all("TM2 Tender", filters={"procurement_package": pkg.name}, limit=1)),
		)

	def test_b10_s21_audit_write_fail_closed(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.append_handoff_audit_comment",
			side_effect=RuntimeError("audit unavailable"),
		):
			with self.assertRaises(frappe.ValidationError):
				release_procurement_package_to_tender(pkg.name)
		self.assertFalse(
			frappe.get_all(
				"TM2 Tender",
				filters={"procurement_package": pkg.name},
			)
		)

	def test_b10_s21_configuration_prepopulation_failure_no_tender(self) -> None:
		_, _, pkg = self._ready_package_fixture()
		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.build_handoff_configuration_json",
			side_effect=ValueError("configuration unavailable"),
		):
			with self.assertRaises(ValueError):
				release_procurement_package_to_tender(pkg.name)
		self.assertFalse(
			frappe.get_all(
				"TM2 Tender",
				filters={"procurement_package": pkg.name},
			)
		)

	def test_b10_s21_validation_raises_propagates_fail_closed(self) -> None:
		"""§21: validation unavailable / hard failure — no silent success."""
		_, _, pkg = self._ready_package_fixture()
		with patch(
			"kentender_procurement.tender_management.services.release_procurement_package_to_tender.validate_package_for_release_xmv",
			side_effect=RuntimeError("validation service down"),
		):
			with self.assertRaises(RuntimeError):
				release_procurement_package_to_tender(pkg.name)
		self.assertFalse(
			frappe.get_all(
				"TM2 Tender",
				filters={"procurement_package": pkg.name},
			)
		)
