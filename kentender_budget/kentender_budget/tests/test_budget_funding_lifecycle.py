# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-SUP-005 — Funding Lifecycle shared read model."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.seeds.budget_role_users import upsert_budget_role_users
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.services.budget_audit_contracts import EVENT_RESERVED, get_budget_audit
from kentender_budget.services.budget_check_reserve_contracts import reserve_funding
from kentender_budget.services.budget_funding_activity import list_funding_activity
from kentender_budget.services.budget_funding_lifecycle import list_funding_lifecycle
from kentender_budget.services.budget_permissions import ensure_budget_roles


def _purge_test_reservations_for_budget(budget_code: str = "MOH-BUD-2027-2028") -> None:
	"""Remove non-fixture reservations left by prior reserve_funding tests on shared site."""
	budget = frappe.db.get_value("Budget", {"generated_reference": budget_code}, "name")
	if not budget or not frappe.db.exists("DocType", "Funding Reservation"):
		return
	rows = frappe.get_all(
		"Funding Reservation",
		filters={"budget": budget},
		fields=["name", "generated_reference", "fixture_namespace", "budget_line", "original_amount"],
	)
	for r in rows:
		if (r.fixture_namespace or "").strip():
			continue
		if not (r.generated_reference or "").startswith("RSV-"):
			continue
		# Keep pack fixture codes even if namespace blank.
		if r.generated_reference in ("RSV-MOH-0001",):
			continue
		line = r.budget_line
		amt = flt(r.original_amount)
		frappe.delete_doc("Funding Reservation", r.name, force=1, ignore_permissions=True)
		if line and amt:
			cur = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
			frappe.db.set_value(
				"Budget Line",
				line,
				"amount_reserved",
				max(0.0, cur - amt),
				update_modified=False,
			)
		# Drop paired audit rows for this RSV code (immutable purge flag).
		if frappe.db.exists("DocType", "Budget Audit Event"):
			frappe.flags.allow_budget_audit_purge = True
			try:
				for name in frappe.get_all(
					"Budget Audit Event",
					filters={"record_code": r.generated_reference},
					pluck="name",
				):
					frappe.delete_doc("Budget Audit Event", name, force=1, ignore_permissions=True)
			finally:
				frappe.flags.allow_budget_audit_purge = False


class TestBudgetFundingLifecycle(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_role_users()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		_purge_test_reservations_for_budget()
		upsert_moh_mvp_v1_portfolio()

	def tearDown(self):
		_purge_test_reservations_for_budget()
		frappe.set_user("Administrator")

	def test_moh_0001_includes_reservation_commitment_expenditure_sorted(self):
		dto = list_funding_lifecycle("MOH-BUD-2027-2028")
		self.assertEqual(dto["budget"]["code"], "MOH-BUD-2027-2028")
		domain = [e for e in dto["events"] if e.get("kind") == "domain"]
		by_code = {e["source_code"]: e for e in domain}
		self.assertIn("RSV-MOH-0001", by_code)
		self.assertIn("COM-MOH-2027-005", by_code)
		self.assertIn("EXP-MOH-2027-005-01", by_code)
		self.assertEqual(by_code["RSV-MOH-0001"]["source_doctype"], "Funding Reservation")
		self.assertEqual(by_code["COM-MOH-2027-005"]["source_doctype"], "Procurement Commitment")
		self.assertEqual(by_code["EXP-MOH-2027-005-01"]["source_doctype"], "Expenditure Snapshot")
		# Deterministic descending order by event_at_sort / type / code.
		sort_keys = [
			(e.get("event_at_sort") or "", e.get("event_type") or "", e.get("source_code") or "")
			for e in dto["events"]
		]
		self.assertEqual(sort_keys, sorted(sort_keys, reverse=True))

	def test_reserve_dedup_activity_stable_audit_has_evidence(self):
		line = frappe.db.get_value("Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name")
		key = "TEST:LIFECYCLE-DEDUP:MOH-BL-HWD-2027:15000000.00"
		result = reserve_funding(
			budget_line=line,
			demand_name="DMD-TEST-LIFECYCLE-DEDUP",
			requested_amount=15_000_000,
			idempotency_key=key,
		)
		self.assertTrue(result["ok"])
		code = result["reservation_code"]

		life = list_funding_lifecycle("MOH-BUD-2027-2028")
		domain_rsv = [
			e
			for e in life["events"]
			if e.get("kind") == "domain"
			and e.get("source_doctype") == "Funding Reservation"
			and e.get("source_code") == code
		]
		self.assertEqual(len(domain_rsv), 1)
		self.assertTrue(domain_rsv[0].get("audit_ref"))

		paired_audits = [
			e
			for e in life["events"]
			if e.get("kind") == "audit"
			and e.get("event_type") == EVENT_RESERVED
			and (e.get("audit_payload") or {}).get("record_code") == code
		]
		self.assertEqual(len(paired_audits), 1)
		self.assertTrue(paired_audits[0].get("paired_with_domain"))

		activity = list_funding_activity("MOH-BUD-2027-2028")
		rsv_rows = [r for r in activity["rows"] if r["code"] == code]
		self.assertEqual(len(rsv_rows), 1)
		codes = [r["code"] for r in activity["rows"]]
		self.assertEqual(len(codes), len(set(codes)))

		audit = get_budget_audit("MOH-BUD-2027-2028", event_type=EVENT_RESERVED)
		self.assertTrue(any(r["record_code"] == code for r in audit["rows"]))

	def test_projections_use_shared_lifecycle(self):
		from kentender_budget.services import budget_audit_contracts as audit_mod
		from kentender_budget.services import budget_downstream_contracts as down_mod
		from kentender_budget.services import budget_funding_activity as act_mod

		self.assertIs(act_mod.list_funding_lifecycle, list_funding_lifecycle)
		self.assertIs(down_mod.list_funding_lifecycle, list_funding_lifecycle)
		self.assertIn("list_funding_lifecycle", act_mod.list_funding_activity.__code__.co_names)
		self.assertIn("list_funding_lifecycle", down_mod.list_downstream_usage.__code__.co_names)
		self.assertIn("list_funding_lifecycle", audit_mod.get_budget_audit.__code__.co_names)

	def test_pe_moe_officer_denied_moh_budget(self):
		frappe.set_user("other.entity.officer@example.test")
		try:
			with self.assertRaises(frappe.PermissionError):
				list_funding_lifecycle("MOH-BUD-2027-2028")
		finally:
			frappe.set_user("Administrator")

	def test_unprivileged_user_denied(self):
		email = "budget.lifecycle.nopriv@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Lifecycle",
					"last_name": "Nopriv",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				list_funding_lifecycle("MOH-BUD-2027-2028")
		finally:
			frappe.set_user("Administrator")

	def test_reserve_updates_activity_via_shared_path(self):
		line = frappe.db.get_value("Budget Line", {"generated_reference": "MOH-BL-HWD-2027"}, "name")
		before = list_funding_activity("MOH-BUD-2027-2028")
		before_codes = {r["code"] for r in before["rows"]}
		key = "TEST:LIFECYCLE-ACT:MOH-BL-HWD-2027:12000000.00"
		result = reserve_funding(
			budget_line=line,
			demand_name="DMD-TEST-LIFECYCLE-ACT",
			requested_amount=12_000_000,
			idempotency_key=key,
		)
		after = list_funding_activity("MOH-BUD-2027-2028")
		self.assertIn(result["reservation_code"], {r["code"] for r in after["rows"]})
		self.assertGreaterEqual(after["row_count"], before["row_count"])
		self.assertTrue(before_codes.issubset({r["code"] for r in after["rows"]}))
		row = next(r for r in after["rows"] if r["code"] == result["reservation_code"])
		self.assertEqual(row["activity_type"], "reservation")
		self.assertEqual(flt(row["amount"]), 12_000_000)
