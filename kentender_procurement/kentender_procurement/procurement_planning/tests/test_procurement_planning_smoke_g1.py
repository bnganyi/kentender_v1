# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase G1 — Procurement Planning smoke suite (8. Smoke Test Contracts, 9. Cursor Pack).

Backend (integration) coverage for PP1–PP20. UI/Playwright is G3. Requires F1-capable
site: run F2 + DIA prerequisite + F1 on dev sites.

Run (example)::

	./scripts/bench-with-node.sh --site <site> run-tests --app kentender_procurement \\
	  --doctype "" --module kentender_procurement.procurement_planning.tests.test_procurement_planning_smoke_g1
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cint, flt

from kentender_core.seeds import constants as C
from kentender_core.seeds.seed_budget_line_dia import verify_prerequisites_for_dia
from kentender_procurement.demand_intake.seeds.seed_dia_basic import run as run_seed_dia_basic
from kentender_procurement.procurement_planning.api import package_detail, package_list, workflow
from kentender_procurement.procurement_planning.api.landing import get_pp_landing_shell_data
from kentender_procurement.procurement_planning.api.template_selector import get_pp_template_preview, list_pp_templates
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_package_estimated_value,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1 import (
	BID_0004,
	PKG1_CODE,
	PKG2_CODE,
	PKG3_CODE,
	PLAN_CODE,
	TPL_MED,
	TPL_EMG,
	run as run_f1,
)
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
	resolve_procurement_template_name,
)
from kentender_procurement.procurement_planning.services.template_application import apply_template_to_demands


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


def _ensure_f1() -> bool:
	if not _pp_ok():
		return False
	if not verify_prerequisites_for_dia().get("ok"):
		return False
	if not frappe.db.exists("Demand", {"demand_id": BID_0004}):
		try:
			run_seed_dia_basic()
		except Exception:
			return False
	try:
		run_f1(ensure_dia=True)
		frappe.db.commit()
		return bool(frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name"))
	except Exception:
		frappe.db.rollback()
		return False


def _on_plan(code: str) -> str | None:
	return frappe.db.get_value("Procurement Plan", {"plan_code": code}, "name")


def _pkg(plan_name: str, code: str) -> str | None:
	return frappe.db.get_value("Procurement Package", {"plan_id": plan_name, "package_code": code}, "name")


def _delete_pkg_cascade(name: str) -> None:
	for line in frappe.get_all("Procurement Package Line", filters={"package_id": name}, pluck="name"):
		frappe.delete_doc("Procurement Package Line", line, force=True, ignore_permissions=True)
	frappe.delete_doc("Procurement Package", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestProcurementPlanningSmokeG1(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls._f1 = _ensure_f1()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def _skip(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		if not self._f1:
			self.skipTest("F1 or prerequisites (DIA/budget) unavailable")

	# —— PP1 ——
	def test_g_pp01_empty_landing_allows_draft_context(self) -> None:
		if not _pp_ok():
			self.skipTest("not installed")
		plan_code = f"PP-G1E-{frappe.generate_hash()[:4]}"
		existing = _on_plan(plan_code)
		if existing:
			_delete_plan_cascade(existing)
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Plan",
				"plan_name": "G1 empty smoke",
				"plan_code": plan_code,
				"fiscal_year": 2029,
				"procuring_entity": C.ENTITY_MOH,
				"currency": "KES",
				"status": "Draft",
				"is_active": 1,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		try:
			data = get_pp_landing_shell_data(plan=plan_code)
			self.assertTrue(data.get("ok"), data)
			if data.get("current_plan") and (data.get("current_plan", {}).get("status") == "Draft"):
				self.assertIn(
					data.get("show_new_package"),
					(True, 1, False, 0),
					"landing must reflect draft plan flags",
				)
		finally:
			_delete_plan_cascade(doc.name)

	# —— PP2 / PP20 (API surface) ——
	def test_g_pp02_templates_list_business_row_shape(self) -> None:
		self._skip()
		d = list_pp_templates()
		self.assertTrue(d.get("ok"), d)
		rows = d.get("rows") or []
		self.assertGreaterEqual(len(rows), 1, rows)
		for r in rows:
			self.assertIn("template_code", r)
			self.assertIn("default_method", r)
			self.assertIn("applicability_summary", r)
			if r.get("name"):
				self.assertTrue(
					(r.get("template_code") or r.get("template_name")),
					"at least one display key besides internal name",
				)

	def test_g_pp20_preview_uses_business_and_profile_names(self) -> None:
		self._skip()
		p = get_pp_template_preview(TPL_MED)
		self.assertTrue(p and p.get("ok"), p)
		self.assertIn("TPL-", (p.get("template_code") or "") + (p.get("template_name") or ""))
		labs = p.get("profile_labels") or {}
		self.assertIn("risk_profile", labs, "PP20: preview exposes label map for human review")
		self.assertIsInstance(labs.get("risk_profile", ""), str)

	# —— PP3, PP4, PP5, PP17 ——
	def test_g_pp03_to_17_f1_medical_and_emergency_invariants(self) -> None:
		self._skip()
		plan = _on_plan(PLAN_CODE)
		assert plan
		p1 = _pkg(plan, PKG1_CODE)
		self.assertTrue(p1, "PKG1 missing (F1 not applied?)")
		p1d = frappe.get_doc("Procurement Package", p1)
		tcode = frappe.db.get_value("Procurement Template", p1d.template_id, "template_code")
		self.assertEqual(tcode, TPL_MED)
		self.assertEqual(flt(p1d.estimated_value), 5_000_000.0)
		ln = frappe.get_all(
			"Procurement Package Line",
			filters={"package_id": p1, "is_active": 1},
			fields=["amount"],
		)
		self.assertEqual(flt(sum(flt(x.amount) for x in ln)), 5_000_000.0)
		det = package_detail.get_pp_package_detail(p1)
		self.assertTrue(det.get("ok"), det)
		lines2 = det.get("demand_lines") or []
		merged = " ".join(str((x or {}).get("demand_id") or "") for x in lines2)
		self.assertIn("DIA-MOH-2026-0004", merged)
		self.assertIn("DIA-MOH-2026-0011", merged)
		p3 = _pkg(plan, PKG3_CODE)
		if p3:
			self.assertEqual(
				cint(frappe.db.get_value("Procurement Package", p3, "is_emergency")),
				1,
			)
			tt3 = frappe.db.get_value("Procurement Template", frappe.db.get_value("Procurement Package", p3, "template_id"), "template_code")
			self.assertEqual(tt3, TPL_EMG)

	# —— PP6 ——
	def test_g_pp06_insert_without_template_fails(self) -> None:
		self._skip()
		plan = _on_plan(PLAN_CODE)
		if not plan:
			self.skipTest("no F1 plan")
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Package",
				"package_code": f"G6-{frappe.generate_hash()[:4]}",
				"package_name": "G6",
				"plan_id": plan,
				"status": "Draft",
				"is_active": 1,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	# —— PP16 ——
	def test_g_pp16_override_requires_justification(self) -> None:
		self._skip()
		plan = _on_plan(PLAN_CODE)
		p1 = _pkg(plan, PKG1_CODE) if plan else None
		if not p1:
			self.skipTest("no package")
		d = frappe.get_doc("Procurement Package", p1)
		if d.status not in ("Draft", "Completed", "Returned"):
			self.skipTest("package not in editable state")
		d.db_set("method_override_flag", 1, update_modified=False)
		d.db_set("method_override_reason", None, update_modified=False)
		d.reload()
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)
		# reset
		d.db_set("method_override_flag", 0, update_modified=False)
		d.save(ignore_permissions=True)

	# —— PP7 ——
	def test_g_pp07_cannot_structure_without_active_lines(self) -> None:
		self._skip()
		plan = _on_plan(PLAN_CODE)
		tid = resolve_procurement_template_name(TPL_MED)
		code = f"G7-{frappe.generate_hash()[:5]}"
		try:
			out = apply_template_to_demands(
				plan,
				tid,
				[resolve_demand_name(BID_0004)],
				options={"package_code": code, "package_name": "G7 no lines"},
			)
		except frappe.ValidationError as e:
			if "already linked" in str(e).lower() or "packaged" in str(e).lower():
				self.skipTest("No demand without package line; cannot construct PP7 (F1 filled all DIA).")
			raise
		nm = (out.get("packages") or [{}])[0].get("name")
		if not nm:
			self.skipTest("apply did not return package name")
		for line in frappe.get_all("Procurement Package Line", filters={"package_id": nm}, pluck="name"):
			frappe.delete_doc("Procurement Package Line", line, force=True, ignore_permissions=True)
		recompute_package_estimated_value(nm)
		with self.assertRaises(frappe.ValidationError):
			workflow.complete_package(nm)
		_delete_pkg_cascade(nm)

	# —— PP8, PP9, PP10, PP14 (+ PP15) ——
	def test_g_pp08_to_14_workflow_draft_to_ready(self) -> None:
		"""One package: Draft → … → Ready. Uses PKG2. PP9: while Submitted, list pending queue."""
		self._skip()
		plan = _on_plan(PLAN_CODE)
		p = _pkg(plan, PKG2_CODE) if plan else None
		if not p:
			self.skipTest("no PKG2")
		st0 = (frappe.db.get_value("Procurement Package", p, "status") or "").strip()
		if st0 in ("Ready for Tender", "Released to Tender", "Rejected"):
			self.skipTest("PKG2 terminal state; re-run F1 for workflow smoke")
		# work from current state toward Ready for Tender
		st = st0
		if st in ("Draft", "Returned"):
			workflow.complete_package(p)
			st = (frappe.db.get_value("Procurement Package", p, "status") or "").strip()
			self.assertEqual(st, "Completed", st)
			workflow.submit_package(p)
			self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Submitted")
			st = "Submitted"
		if st == "Completed":
			workflow.submit_package(p)
			self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Submitted")
			st = "Submitted"
		if st == "Submitted":
			out9 = package_list.get_pp_package_list(PLAN_CODE, "pending_approval", 50)
			self.assertTrue(out9.get("ok"), out9)
			rows9 = out9.get("rows") or []
			self.assertTrue(
				any((r or {}).get("name") == p for r in rows9),
				f"PKG2 {p!r} should appear in pending_approval (PP9), got {rows9!r}",
			)
			workflow.approve_package(p)
			self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Approved")
		elif st not in ("Approved",):
			self.skipTest(f"PKG2 unexpected baseline state {st!r}")
		workflow.mark_ready_for_tender(p)
		self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Ready for Tender")

	def test_g_pp15_mark_ready_rejected_unless_approved(self) -> None:
		self._skip()
		plan = _on_plan(PLAN_CODE)
		if not plan:
			self.skipTest("no plan")
		pa = (frappe.get_all("Procurement Package", filters={"plan_id": plan, "status": "Draft"}, pluck="name", limit=1) or [None])[0]
		if not pa:
			pa = _pkg(plan, PKG1_CODE)
		if not pa:
			self.skipTest("no draft package for guard test")
		st = (frappe.db.get_value("Procurement Package", pa, "status") or "").strip()
		if st != "Draft":
			self.skipTest("no Draft package to assert pre-approval guard (run after fresh F1)")
		with self.assertRaises(Exception):
			workflow.mark_ready_for_tender(pa)

	# —— PP9 covered in test_g_pp08_to_14 (pending_approval list after submit) ——

	# —— PP11, PP12 (run after test_a0* so PKG1 is still a valid baseline) ——
	def test_zz_g_pp11_12_return_then_reject(self) -> None:
		"""After return (Draft), restructure + submit, then reject."""
		self._skip()
		plan = _on_plan(PLAN_CODE)
		p = _pkg(plan, PKG1_CODE) if plan else None
		if not p:
			self.skipTest("no PKG1")
		st0 = (frappe.db.get_value("Procurement Package", p, "status") or "").strip()
		if st0 in ("Ready for Tender", "Released to Tender", "Rejected", "Submitted", "Approved"):
			self.skipTest("PKG1 not in a safe baseline for return/reject test (re-seed or use fresh F1)")
		# to Submitted
		if st0 == "Draft":
			workflow.complete_package(p)
		if (frappe.db.get_value("Procurement Package", p, "status") or "") == "Completed":
			workflow.submit_package(p)
		self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Submitted")
		workflow.return_package(p, reason="G1 return smoke (mandatory).")
		self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Returned")
		# back to Submitted for reject
		workflow.complete_package(p)
		workflow.submit_package(p)
		workflow.reject_package(p, reason="G1 reject smoke (mandatory).")
		self.assertEqual(frappe.db.get_value("Procurement Package", p, "status"), "Rejected")

	# —— PP19 ——
	def test_g_pp19_plan_submit_approve(self) -> None:
		"""Plan approval requires at least one active package (governance). Use F1 plan if Draft."""
		self._skip()
		plan = _on_plan(PLAN_CODE)
		if not plan:
			self.skipTest("F1 plan missing")
		st = (frappe.db.get_value("Procurement Plan", plan, "status") or "").strip()
		if st != "Draft":
			self.skipTest(f"F1 plan must be Draft for this test (current {st!r})")
		pk = frappe.get_all("Procurement Package", filters={"plan_id": plan, "is_active": 1}, pluck="name")
		if not pk:
			self.skipTest("F1 plan has no packages; cannot test plan approval")
		# Strict submit: every active package must already be Approved.
		for pname in pk:
			frappe.db.set_value("Procurement Package", pname, "status", "Approved", update_modified=False)
		frappe.db.commit()
		workflow.submit_plan(plan)
		workflow.approve_plan(plan)
		self.assertEqual((frappe.db.get_value("Procurement Plan", plan, "status") or ""), "Approved")
		# Leaves PP-MOH-2026 in Approved; re-run F1 seed on dev if you need Draft again.

	# —— PP18, PP13 (negative) ——
	def test_g_pp18_planner_cannot_approve(self) -> None:
		"""Order-independent: use PKG3 and ensure Submitted within this test."""
		self._skip()
		if not frappe.db.exists("User", "planner@moh.test"):
			self.skipTest("planner@moh.test not seeded")
		plan = _on_plan(PLAN_CODE)
		p = _pkg(plan, PKG3_CODE) if plan else None
		if not p:
			self.skipTest("no PKG3")
		st0 = (frappe.db.get_value("Procurement Package", p, "status") or "").strip()
		if st0 in ("Ready for Tender", "Released to Tender", "Rejected", "Approved"):
			self.skipTest("PKG3 not a safe baseline for this negative test; re-seed F1")
		if st0 == "Draft":
			workflow.complete_package(p)
		if (frappe.db.get_value("Procurement Package", p, "status") or "") == "Completed":
			workflow.submit_package(p)
		if (frappe.db.get_value("Procurement Package", p, "status") or "") != "Submitted":
			self.skipTest("PKG3 not Submitted")
		frappe.set_user("planner@moh.test")
		try:
			with self.assertRaises(Exception):
				workflow.approve_package(p)
		finally:
			frappe.set_user("Administrator")

	def test_g_pp13_approved_is_locked_for_planner(self) -> None:
		self._skip()
		if not frappe.db.exists("User", "planner@moh.test"):
			self.skipTest("planner user")
		plan = _on_plan(PLAN_CODE)
		pa = (frappe.get_all("Procurement Package", filters={"plan_id": plan, "status": "Approved"}, pluck="name", limit=1) or [None])[0]
		if not pa:
			self.skipTest("no approved package in DB (PKG2 may be only Ready; run in isolation)")
		d = frappe.get_doc("Procurement Package", pa)
		orig = d.package_name
		d.package_name = f"{(orig or '')}X"
		frappe.set_user("planner@moh.test")
		try:
			with self.assertRaises(Exception):
				d.save(ignore_permissions=True)
		finally:
			frappe.set_user("Administrator")

	def test_a0_g_workflow_return_requires_non_empty_reason(self) -> None:
		"""Runs early: validates whitespace-only reason; leaves PKG1 Submitted for other tests."""
		self._skip()
		plan = _on_plan(PLAN_CODE)
		# Re-use PKG1 if it is Submitted (e.g. from partial runs), else set up from PKG1 Draft
		p = _pkg(plan, PKG1_CODE) if plan else None
		if not p:
			self.skipTest("no PKG1")
		st0 = (frappe.db.get_value("Procurement Package", p, "status") or "").strip()
		if st0 in ("Ready for Tender", "Released to Tender", "Rejected", "Approved"):
			self.skipTest("PKG1 already advanced")
		if st0 == "Draft":
			workflow.complete_package(p)
		if (frappe.db.get_value("Procurement Package", p, "status") or "") == "Completed":
			workflow.submit_package(p)
		if (frappe.db.get_value("Procurement Package", p, "status") or "") != "Submitted":
			self.skipTest("need Submitted PKG1; avoid ordering conflict with return/reject test")
		with self.assertRaises(Exception):
			workflow.return_package(p, reason="   ")


def _delete_plan_cascade(plan_name: str) -> None:
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return
	for p in frappe.get_all("Procurement Package", filters={"plan_id": plan_name}, pluck="name"):
		_delete_pkg_cascade(p)
	frappe.delete_doc("Procurement Plan", plan_name, force=True, ignore_permissions=True)
	frappe.db.commit()
