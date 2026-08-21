# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-UI-06 Finance Confirmation ("Check and Reserve" screen/route name) —
check_funding + reserve_funding."""

from __future__ import annotations

import threading

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender_budget.api import dia_budget_control as dia
from kentender_budget.seeds.moh_mvp_v1_portfolio import upsert_moh_mvp_v1_portfolio
from kentender_budget.seeds.budget_authorization_seed import upsert_budget_test_authorization
from kentender_budget.services.budget_check_reserve_contracts import (
	DECISION_AVAILABLE,
	DECISION_INSUFFICIENT,
	LINEAGE_NOTE,
	check_funding,
	reserve_funding,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles


def _line(code: str) -> str:
	return frappe.db.get_value("Budget Line", {"generated_reference": code}, "name")


class TestBudgetCheckReserve(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		upsert_budget_test_authorization()
		cls.seed = upsert_moh_mvp_v1_portfolio()

	def setUp(self):
		upsert_moh_mvp_v1_portfolio()
		# Drop non-seed reservations created by prior tests so MOH-BL-HWD-2027 stays clean.
		for name in frappe.get_all(
			"Funding Reservation",
			filters={"fixture_namespace": ["in", ["", None]], "demand_code": ["like", "DMD-TEST-%"]},
			pluck="name",
		):
			frappe.delete_doc("Funding Reservation", name, force=True, ignore_permissions=True)
		# Also clear by demand_code prefix even if namespace set.
		for name in frappe.get_all(
			"Funding Reservation",
			filters={"demand_code": ["like", "DMD-TEST-%"]},
			pluck="name",
		):
			frappe.delete_doc("Funding Reservation", name, force=True, ignore_permissions=True)
		upsert_moh_mvp_v1_portfolio()

	def test_check_available_on_moh_bl_0002_full_money(self):
		# MOH-BL-HWD-2027: 80M approved, 0 reserved/committed → available 80M.
		dto = check_funding(
			budget_line="MOH-BL-HWD-2027",
			requested_amount=50_000_000,
			demand="DMD-TEST-AVAILABLE",
		)
		self.assertEqual(dto["decision"], DECISION_AVAILABLE)
		self.assertTrue(dto["sufficient"])
		self.assertEqual(flt(dto["available_before"]), 80_000_000)
		self.assertEqual(flt(dto["available_after"]), 30_000_000)
		self.assertEqual(dto["available_before_display"], "KES 80,000,000")
		self.assertEqual(dto["requested_display"], "KES 50,000,000")
		self.assertEqual(dto["available_after_display"], "KES 30,000,000")
		self.assertNotIn("80M", dto["available_before_display"])
		self.assertEqual(dto["budget_line"]["code"], "MOH-BL-HWD-2027")
		self.assertTrue(dto["capabilities"]["can_reserve"])
		self.assertEqual(dto["lineage_note"], LINEAGE_NOTE)

	def test_check_insufficient_on_moh_bl_0001(self):
		# MOH-BL-DHI-2027 remaining available = 480 - 145 - 310 = 25M; 455M request fails.
		dto = check_funding(
			budget_line="MOH-BL-DHI-2027",
			requested_amount=455_000_000,
			demand="DMD-MOH-2027-014",
		)
		self.assertEqual(dto["decision"], DECISION_INSUFFICIENT)
		self.assertFalse(dto["sufficient"])
		self.assertEqual(flt(dto["available_before"]), 25_000_000)
		self.assertEqual(flt(dto["shortfall"]), 430_000_000)
		self.assertEqual(dto["shortfall_display"], "KES 430,000,000")
		self.assertFalse(dto["capabilities"]["can_reserve"])
		self.assertIn("KES", dto["requested_display"])
		self.assertNotIn("455M", dto["requested_display"])

	def test_check_does_not_mutate_balances(self):
		line = _line("MOH-BL-HWD-2027")
		before_r = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		before_c = flt(frappe.db.get_value("Budget Line", line, "amount_committed"))
		check_funding(budget_line=line, requested_amount=10_000_000, demand="DMD-TEST-NOMUT")
		after_r = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		after_c = flt(frappe.db.get_value("Budget Line", line, "amount_committed"))
		self.assertEqual(before_r, after_r)
		self.assertEqual(before_c, after_c)

	def test_reserve_creates_reservation_and_bumps_reserved(self):
		line = _line("MOH-BL-HWD-2027")
		before = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		result = reserve_funding(
			budget_line=line,
			plan_item_code="PPI-TEST-RSV-001",
			demand_name="DMD-TEST-RSV-001",
			requested_amount=40_000_000,
			idempotency_key="TEST:DMD-TEST-RSV-001:MOH-BL-HWD-2027:40000000.00",
		)
		self.assertTrue(result["ok"])
		self.assertFalse(result["reused"])
		self.assertTrue(result["reservation_code"].startswith("RSV-"))
		self.assertEqual(result["original_amount_display"], "KES 40,000,000")
		after = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		self.assertEqual(after, before + 40_000_000)
		self.assertTrue(
			frappe.db.exists("Funding Reservation", {"generated_reference": result["reservation_code"]})
		)

	def test_new_reservation_emits_funding_reserved_audit(self):
		"""BUD-SUP-005 — new reserve_funding inserts Budget Audit Event (not idempotent reuse)."""
		from kentender_budget.services.budget_audit_contracts import EVENT_RESERVED

		line = _line("MOH-BL-HWD-2027")
		key = "TEST:DMD-TEST-RSV-AUDIT:MOH-BL-HWD-2027:9000000.00"
		result = reserve_funding(
			budget_line=line,
			plan_item_code="PPI-TEST-RSV-AUDIT",
			demand_name="DMD-TEST-RSV-AUDIT",
			requested_amount=9_000_000,
			idempotency_key=key,
		)
		self.assertFalse(result["reused"])
		self.assertTrue(
			frappe.db.exists(
				"Budget Audit Event",
				{
					"record_code": result["reservation_code"],
					"event_type": EVENT_RESERVED,
					"record_doctype": "Funding Reservation",
				},
			)
		)
		# Idempotent reuse must not create a second audit row.
		before = frappe.db.count(
			"Budget Audit Event",
			{"record_code": result["reservation_code"], "event_type": EVENT_RESERVED},
		)
		reuse = reserve_funding(
			budget_line=line,
			plan_item_code="PPI-TEST-RSV-AUDIT",
			demand_name="DMD-TEST-RSV-AUDIT",
			requested_amount=9_000_000,
			idempotency_key=key,
		)
		self.assertTrue(reuse["reused"])
		after = frappe.db.count(
			"Budget Audit Event",
			{"record_code": result["reservation_code"], "event_type": EVENT_RESERVED},
		)
		self.assertEqual(before, after)

	def test_reserve_idempotent_same_key(self):
		line = _line("MOH-BL-HWD-2027")
		key = "TEST:DMD-TEST-IDEM:MOH-BL-HWD-2027:20000000.00"
		first = reserve_funding(
			budget_line=line,
			plan_item_code="PPI-TEST-IDEM",
			demand_name="DMD-TEST-IDEM",
			requested_amount=20_000_000,
			idempotency_key=key,
		)
		reserved_after_first = flt(frappe.db.get_value("Budget Line", line, "amount_reserved"))
		second = reserve_funding(
			budget_line=line,
			plan_item_code="PPI-TEST-IDEM",
			demand_name="DMD-TEST-IDEM",
			requested_amount=20_000_000,
			idempotency_key=key,
		)
		self.assertTrue(second["reused"])
		self.assertEqual(first["reservation_code"], second["reservation_code"])
		self.assertEqual(
			flt(frappe.db.get_value("Budget Line", line, "amount_reserved")),
			reserved_after_first,
		)

	def test_reserve_blocks_insufficient(self):
		with self.assertRaises(frappe.ValidationError):
			reserve_funding(
				budget_line="MOH-BL-DHI-2027",
				plan_item_code="PPI-TEST-INSUFF",
				demand_name="DMD-TEST-INSUFF",
				requested_amount=455_000_000,
				idempotency_key="TEST:DMD-TEST-INSUFF:fail",
			)

	def test_reserve_insufficient_emits_notification_idempotent(self):
		"""BUD-SUP-001B — notify before throw; retry does not duplicate."""
		from kentender_budget.services.budget_permissions import ROLE_AUTHORITY, ROLE_OFFICER

		officer = "budget.notify.insuff.officer@example.com"
		if not frappe.db.exists("User", officer):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": officer,
					"first_name": "Insuff",
					"last_name": "Officer",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles(ROLE_OFFICER, ROLE_AUTHORITY)
		else:
			frappe.get_doc("User", officer).add_roles(ROLE_OFFICER, ROLE_AUTHORITY)
		pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		if pe and not frappe.db.exists(
			"User Permission",
			{"user": officer, "allow": "Procuring Entity", "for_value": pe},
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": officer,
					"allow": "Procuring Entity",
					"for_value": pe,
					"is_default": 1,
				}
			).insert(ignore_permissions=True)

		for name in frappe.get_all(
			"Notification Log",
			filters={"email_header": ["like", "kt-budget:funding_insufficient:%"]},
			pluck="name",
		):
			frappe.delete_doc(
				"Notification Log", name, force=True, ignore_permissions=True
			)

		kwargs = dict(
			budget_line="MOH-BL-DHI-2027",
			plan_item_code="PPI-TEST-INSUFF-NTF",
			demand_name="DMD-TEST-INSUFF-NTF",
			requested_amount=455_000_000,
			idempotency_key="TEST:DMD-TEST-INSUFF-NTF:fail",
		)
		with self.assertRaises(frappe.ValidationError):
			reserve_funding(**kwargs)
		count_after_first = frappe.db.count(
			"Notification Log",
			{"email_header": ["like", "kt-budget:funding_insufficient:%"]},
		)
		self.assertGreaterEqual(count_after_first, 1)
		with self.assertRaises(frappe.ValidationError):
			reserve_funding(**kwargs)
		count_after_second = frappe.db.count(
			"Notification Log",
			{"email_header": ["like", "kt-budget:funding_insufficient:%"]},
		)
		self.assertEqual(count_after_first, count_after_second)

	def test_dia_shim_check_and_create(self):
		chk = dia.check_available_budget("MOH-BL-HWD-2027", 50_000_000)
		self.assertTrue(chk["ok"])
		self.assertTrue((chk.get("data") or {}).get("sufficient"))
		self.assertEqual(flt((chk.get("data") or {}).get("amount_available")), 80_000_000)

		bad = dia.check_available_budget("MOH-BL-DHI-2027", 455_000_000)
		self.assertFalse(bad["ok"])
		self.assertFalse((bad.get("data") or {}).get("sufficient"))

		res = dia.create_reservation(
			"MOH-BL-HWD-2027",
			"Procurement Plan Item",
			"PPI-TEST-DIA-001",
			30_000_000,
			actor="Administrator",
		)
		self.assertTrue(res["ok"])
		self.assertTrue((res.get("data") or {}).get("reservation_id"))

	def test_reserve_requires_plan_item_not_demand_alone(self):
		"""BUD-FR-009/010 — no reservation from a Demand reference alone."""
		with self.assertRaises(frappe.ValidationError):
			reserve_funding(
				budget_line="MOH-BL-HWD-2027",
				demand_name="DMD-TEST-NO-PLAN-ITEM",
				requested_amount=1_000_000,
				idempotency_key="TEST:DMD-TEST-NO-PLAN-ITEM:fail",
			)

	def test_dia_shim_rejects_demand_only_source(self):
		"""BUD-FR-009/010 — the DIA shim's legacy Demand-shaped call no longer suffices."""
		res = dia.create_reservation(
			"MOH-BL-HWD-2027",
			"Demand",
			"DMD-TEST-DIA-NO-PLAN-ITEM",
			1_000_000,
			actor="Administrator",
		)
		self.assertFalse(res["ok"])

	def test_concurrent_reserve_cannot_oversubscribe_line(self):
		"""BUD-FR-011/012, BUD-AC-011 — two simultaneous reserve_funding calls
		against the same line for more than its available balance must not
		both succeed; the `FOR UPDATE` row lock in reserve_funding serialises
		them so exactly one wins and the line never goes negative-available."""
		line_name = _line("MOH-BL-HWD-2027")

		def _drop_conc_artifacts():
			for name in frappe.get_all(
				"Funding Reservation",
				filters={"plan_item_code": ["like", "PPI-TEST-CONC-%"]},
				pluck="name",
			):
				frappe.delete_doc("Funding Reservation", name, force=True, ignore_permissions=True)
			frappe.db.commit()

		_drop_conc_artifacts()
		self.addCleanup(_drop_conc_artifacts)
		frappe.db.set_value(
			"Budget Line", line_name, {"amount_reserved": 0, "amount_committed": 0}
		)
		frappe.db.commit()
		site = frappe.local.site
		errors: list[BaseException] = []
		results: list[dict] = []

		def worker(suffix: str):
			try:
				frappe.init(site=site)
				frappe.connect()
				frappe.set_user("Administrator")
				res = reserve_funding(
					budget_line="MOH-BL-HWD-2027",
					plan_item_code=f"PPI-TEST-CONC-{suffix}",
					requested_amount=50_000_000,
					idempotency_key=f"TEST:CONC:{suffix}",
				)
				frappe.db.commit()
				results.append(res)
			except BaseException as exc:  # noqa: BLE001 — collect for assertion
				errors.append(exc)
				try:
					frappe.db.rollback()
				except Exception:
					pass
			finally:
				frappe.destroy()

		t1 = threading.Thread(target=worker, args=("A",))
		t2 = threading.Thread(target=worker, args=("B",))
		t1.start()
		t2.start()
		t1.join(timeout=30)
		t2.join(timeout=30)

		frappe.connect()
		frappe.set_user("Administrator")
		self.assertEqual(len(results), 1, f"expected exactly one winner, got {results}")
		self.assertEqual(len(errors), 1, f"expected exactly one insufficient-funds failure, got {errors}")
		self.assertIsInstance(errors[0], frappe.ValidationError)

		line = frappe.get_doc("Budget Line", line_name)
		self.assertEqual(flt(line.amount_reserved), 50_000_000)
		reservations = frappe.get_all(
			"Funding Reservation",
			filters={"budget_line": line_name, "plan_item_code": ["like", "PPI-TEST-CONC-%"]},
			pluck="name",
		)
		self.assertEqual(len(reservations), 1)

	def test_pe_scope_denial(self):
		email = "budget.check.pe.deny@example.com"
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "Check",
					"last_name": "Deny",
					"send_welcome_email": 0,
					"new_password": "Test@12345",
				}
			)
			user.insert(ignore_permissions=True)
			user.add_roles("Budget Viewer")
		frappe.set_user(email)
		try:
			with self.assertRaises(frappe.PermissionError):
				check_funding(
					budget_line="MOH-BL-HWD-2027",
					requested_amount=1_000_000,
					procuring_entity="PE-MOH",
				)
		finally:
			frappe.set_user("Administrator")
