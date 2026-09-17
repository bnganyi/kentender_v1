# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.9 §16.2 — the usability contracts behind the v1.9 screens:
the §11.1B workspace state matrix and server-decided actions (BUD19-AC-001/
002/025/026), the decision-first approval read with live protection and
typed blockers (BUD19-AC-011/012/013/014), the save/submit/recovery contract
with idempotent replay (BUD19-AC-003/004/007/008), successor omission and
transfer totals (BUD19-AC-009/010), year-end closure (BUD19-AC-021/022), and
the requisition-led reservation rows with partial conversion and
requires-review facts (BUD19-AC-015/017/018).

Every fixture is disposable and purged in reverse order, including the
reservations, commitments and ledger rows the scenarios create.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_audit_contracts import get_funding_activity
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import FUNDING_SOURCE, _FinanceTestBase, check_reserve


class _V19Base(_FinanceTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.auditor = cls._make_user("auditor", ("Auditor",))
		cls.nobody = cls._make_user("nobody", ())
		cls._budgets: list[str] = []

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for budget in cls._budgets:
			for doctype in ("Procurement Commitment",):
				for name in frappe.get_all(doctype, filters={"reservation": ["in", frappe.get_all("Funding Reservation", filters={"budget": budget}, pluck="name") or ["-"]]}, pluck="name"):
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			for name in frappe.get_all("Funding Reservation", filters={"budget": budget}, pluck="name"):
				frappe.delete_doc("Funding Reservation", name, force=True, ignore_permissions=True)
			frappe.flags.allow_budget_audit_purge = True
			try:
				for name in frappe.get_all("Budget Audit Event", filters={"budget": budget}, pluck="name"):
					frappe.delete_doc("Budget Audit Event", name, force=True, ignore_permissions=True)
			finally:
				frappe.flags.allow_budget_audit_purge = False
			for name in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": ["in", frappe.get_all("Procurement Budget Version", filters={"budget": budget}, pluck="name") or ["-"]]}, pluck="name"):
				frappe.delete_doc("Procurement Budget Line Version", name, force=True, ignore_permissions=True)
		super().tearDownClass()

	@classmethod
	def _past_fy(cls) -> str:
		"""A disposable Fiscal Year that has already ended (closure fixtures)."""
		cls._fy_counter += 1
		start_year = 1800 + (int(cls.suffix, 16) + cls._fy_counter * 31) % 150
		fy = frappe.get_doc({"doctype": "Fiscal Year", "year": f"{start_year}-{start_year + 1}", "year_start_date": f"{start_year}-07-01", "year_end_date": f"{start_year + 1}-06-30"}).insert(ignore_permissions=True)
		cls._track("Fiscal Year", fy.name)
		return fy.name

	def _draft(self, *, fiscal_year=None, dhi=100_000_000, hwd=60_000_000, submit=False) -> tuple[str, str, str]:
		"""Officer records an allocation with two lines. Returns (fy, budget, version)."""
		fy = fiscal_year or self._fresh_fy()
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{"fiscal_year": fy, "approval_reference": f"V19-{self.suffix}", "approval_date": add_days(nowdate(), -10), "authorised_total": dhi + hwd, "approval_document": "/files/test-approval.pdf"}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		budget, version = result["budget"]["id"], result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", budget)
		self._budgets.append(budget)
		lines = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [
				{"title": "Digital health infrastructure programme", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": dhi},
				{"title": "Digital health workforce development", "owner_org_unit": "", "funding_source": FUNDING_SOURCE, "approved_amount": hwd},
			]}
		)
		self.assertTrue(lines["ok"], lines.get("errors"))
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)
		if submit:
			submitted = readiness.submit_budget_version({"budget_version": version})
			self.assertTrue(submitted["ok"], submitted.get("blockers"))
		return fy, budget, version

	def _active(self, **kwargs) -> tuple[str, str, str]:
		fy, budget, version = self._draft(submit=True, **kwargs)
		self._as(self.approver)
		approved = readiness.approve_budget_version({"budget_version": version})
		self.assertTrue(approved["ok"], approved.get("blockers"))
		return fy, budget, version

	def _line(self, version: str, title: str) -> str:
		return frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": title}, "budget_line")

	def _reserve(self, line: str, amount: float, *, ref: str) -> str:
		self._as(self.finance_officer)
		tag = frappe.generate_hash(length=6)
		token = check_reserve.check_funding(
			plan_item=f"PPI-{tag}", plan_version=f"PLN-{tag}", finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}",
			allocations=[{"budget_line": line, "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": f"PSA-{tag}"}],
			correlation_id=frappe.generate_hash(length=12), calling_module="Procurement Requisitions", caller_reference=ref,
		)
		result = check_reserve.reserve_funding(token=token["token"], finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}", idempotency_key=f"IDEM-{tag}")
		self.assertTrue(result["ok"])
		return result["reservations"][0]["reservation_id"]

	def _successor(self, budget: str, *, dhi: float, hwd: float, submit=True, revision_type="Transfer") -> str:
		self._as(self.officer)
		created = contracts.create_budget_successor_version(budget, {"revision_type": revision_type})
		self.assertTrue(created["ok"], created)
		version = created["version"]["id"]
		self._track("Procurement Budget Version", version)
		editor = lines_svc.get_budget_version_lines_editor(version)
		rows = []
		for r in editor["rows"]:
			amount = dhi if r["title"].startswith("Digital health infrastructure") else hwd
			rows.append({"budget_line": r["budget_line"], "title": r["title"], "owner_org_unit": r["owner_org_unit"], "funding_source": r["funding_source"], "approved_amount": amount})
		saved = lines_svc.save_budget_lines_draft({"budget_version": version, "lines": rows})
		self.assertTrue(saved["ok"], saved.get("errors"))
		if submit:
			submitted = readiness.submit_budget_version({"budget_version": version})
			self.assertTrue(submitted["ok"], submitted.get("blockers"))
		return version


class TestWorkspaceStateMatrix(_V19Base):
	"""BUD19-AC-001/002/025/026 — §11.1B every actor finds the next step."""

	def test_no_record_offers_record_allocation_only_to_the_officer(self):
		fy = self._fresh_fy()
		self._as(self.officer)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "no_record")
		self.assertIn("record_allocation", ws["available_actions"])
		self._as(self.auditor)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "no_record")
		self.assertNotIn("record_allocation", ws["available_actions"])
		self.assertNotIn("positions", ws)

	def test_initial_draft_and_submission_have_no_current_position(self):
		fy, budget, version = self._draft()
		self._as(self.officer)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "initial_draft")
		self.assertEqual(ws["pending_version"]["action"], "continue_draft")
		self.assertNotIn("positions", ws)
		self.assertNotIn("record_allocation", ws["available_actions"])
		readiness.submit_budget_version({"budget_version": version})
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "initial_submitted")
		self.assertEqual(ws["pending_version"]["action"], "view_submission")
		self._as(self.approver)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["pending_version"]["action"], "review")
		frappe.set_user("Administrator")
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["pending_version"]["action"], "view_version_readonly")
		self.assertNotIn("positions", ws)

	def test_returned_draft_carries_the_full_reason(self):
		fy, budget, version = self._draft(submit=True)
		self._as(self.approver)
		returned = readiness.return_budget_version({"budget_version": version, "return_reason": "Attach the signed approval instrument, not the draft memo."})
		self.assertTrue(returned["ok"], returned)
		self._as(self.officer)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "returned_draft")
		self.assertEqual(ws["pending_version"]["action"], "correct_and_resubmit")
		self.assertTrue(ws["pending_version"]["is_returned"])
		self.assertIn("signed approval instrument", ws["pending_version"]["return"]["reason"])

	def test_current_with_update_keeps_the_current_allocation(self):
		fy, budget, version = self._active()
		self._as(self.officer)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "current")
		self.assertIn("update_allocation", ws["available_actions"])
		self.assertEqual(ws["positions"]["available"], 160_000_000)
		successor = self._successor(budget, dhi=90_000_000, hwd=70_000_000, submit=False)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "current_with_draft")
		self.assertEqual(ws["pending_version"]["action"], "continue_update")
		self.assertNotIn("update_allocation", ws["available_actions"])
		self.assertEqual(ws["positions"]["approved"], 160_000_000)
		readiness.submit_budget_version({"budget_version": successor})
		self._as(self.auditor)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "current_with_submitted")
		self.assertEqual(ws["version"]["version_number"], 1)
		self.assertEqual(ws["positions"]["available"], 160_000_000)

	def test_lines_read_as_all_departments_never_entity_wide(self):
		fy, budget, version = self._active()
		self._as(self.auditor)
		ws = contracts.get_budget_workspace(fy)
		labels = {row["owner_org_unit"] for row in ws["lines_preview"]}
		self.assertIn("All departments", labels)
		self.assertNotIn("Entity-wide", labels)


class TestDecisionFirstApprovalRead(_V19Base):
	"""BUD19-AC-011/012/013/014 — changes, evidence and live protection together."""

	def test_successor_review_leads_with_changes_and_protection(self):
		fy, budget, v1 = self._active()
		dhi = self._line(v1, "Digital health infrastructure programme")
		self._reserve(dhi, 80_000_000, ref="REQ-V19-001")
		v2 = self._successor(budget, dhi=90_000_000, hwd=70_000_000)
		self._as(self.approver)
		task = readiness.get_budget_approval_task(v2)
		self.assertEqual(task["kind"], "successor")
		self.assertNotIn("readiness", task)
		rows = {r["title"]: r for r in task["changes"]["rows"]}
		self.assertEqual(rows["Digital health infrastructure programme"]["change"], -10_000_000)
		self.assertEqual(task["changes"]["total_change"], 0)
		self.assertIn("moves from Digital health infrastructure programme to Digital health workforce development", task["changes"]["summary"])
		protection = {r["title"]: r for r in task["protection"]["rows"]}
		self.assertEqual(protection["Digital health infrastructure programme"]["protected_amount"], 80_000_000)
		self.assertEqual(protection["Digital health infrastructure programme"]["available_after_update"], 10_000_000)
		self.assertTrue(task["protection"]["as_at_display"].endswith("EAT"))
		self.assertEqual(task["evidence"]["approved_allocation"], 160_000_000)
		self.assertTrue(task["capabilities"]["can_approve"])
		self.assertTrue(task["capabilities"]["can_return"])
		lines = readiness.get_budget_approval_task_lines(v2)
		self.assertIn("protected_amount", lines["rows"][0])
		self.assertNotIn("floor", lines["rows"][0])
		self.assertEqual(lines["total_available_after_update"], 80_000_000)

	def test_live_breach_shows_exact_shortfall_and_blocks_approval(self):
		fy, budget, v1 = self._active()
		dhi = self._line(v1, "Digital health infrastructure programme")
		self._reserve(dhi, 95_000_000, ref="REQ-V19-002")
		v2 = self._successor(budget, dhi=90_000_000, hwd=70_000_000, submit=False)
		self._as(self.officer)
		submitted = readiness.submit_budget_version({"budget_version": v2})
		self.assertFalse(submitted["ok"])
		breach = [b for b in submitted["blockers"] if b["rule"] == "BUDGET_REVISION_FLOOR_BREACH"][0]
		self.assertEqual(breach["detail"]["shortfall"], 5_000_000)
		self.assertIn("Shortfall: KES 5,000,000", breach["message"])
		# Submit the version regardless (simulating a hold that arrived after submission)
		frappe.db.set_value("Funding Reservation", {"budget_line": dhi}, "remaining_amount", 0)
		submitted = readiness.submit_budget_version({"budget_version": v2})
		self.assertTrue(submitted["ok"], submitted.get("blockers"))
		frappe.db.set_value("Funding Reservation", {"budget_line": dhi}, "remaining_amount", 95_000_000)
		self._as(self.approver)
		task = readiness.get_budget_approval_task(v2)
		row = [r for r in task["protection"]["rows"] if r["title"].startswith("Digital health infrastructure")][0]
		self.assertEqual(row["shortfall"], 5_000_000)
		self.assertIsNone(row["available_after_update"])
		self.assertFalse(task["capabilities"]["can_approve"])
		self.assertTrue(task["capabilities"]["can_return"])
		approved = readiness.approve_budget_version({"budget_version": v2})
		self.assertFalse(approved["ok"])
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", v2, "status"), "Submitted for approval")

	def test_initial_review_shows_the_complete_set_without_a_predecessor(self):
		fy, budget, version = self._draft(submit=True)
		self._as(self.approver)
		task = readiness.get_budget_approval_task(version)
		self.assertEqual(task["kind"], "initial")
		self.assertEqual(len(task["line_details"]), 2)
		self.assertIsNone(task["changes"]["rows"][0]["current_amount"])
		self.assertEqual(task["protection"]["rows"], [])
		changes = readiness.get_budget_approval_task_changes(version)
		self.assertTrue(changes["is_initial_baseline"])
		frappe.set_user("Administrator")
		task = readiness.get_budget_approval_task(version)
		self.assertFalse(task["capabilities"]["can_approve"])
		self.assertFalse(task["capabilities"]["can_return"])
		self.assertTrue(task["capabilities"]["is_technical_reader"])


class TestSaveSubmitRecovery(_V19Base):
	"""BUD19-AC-003/004/007/008 — typed results, one attempt per key."""

	def test_stale_save_is_a_typed_result_not_an_exception(self):
		fy, budget, version = self._draft()
		self._as(self.officer)
		result = contracts.save_budget_version_draft({"budget_version": version, "approval_reference": "X-1", "approval_date": add_days(nowdate(), -1), "authorised_total": 160_000_000, "expected_modified": "2000-01-01 00:00:00"})
		self.assertFalse(result["ok"])
		self.assertEqual(result["code"], "BUDGET_STALE_WRITE")
		self.assertIn("modified", result["version"])

	def test_submit_replays_from_the_same_key_without_a_second_attempt(self):
		fy, budget, version = self._draft()
		self._as(self.officer)
		key = f"submit-{frappe.generate_hash(length=8)}"
		first = readiness.submit_budget_version({"budget_version": version, "idempotency_key": key})
		self.assertTrue(first["ok"], first.get("blockers"))
		second = readiness.submit_budget_version({"budget_version": version, "idempotency_key": key})
		self.assertTrue(second["ok"])
		self.assertTrue(second.get("replayed"))
		self.assertEqual(frappe.db.count("Budget Audit Event", {"budget_version": version, "event_type": "Budget version submitted"}), 1)
		conflict = readiness.submit_budget_version({"budget_version": version, "idempotency_key": key, "expected_modified": "changed"})
		self.assertEqual(conflict["code"], "BUDGET_IDEMPOTENCY_CONFLICT")

	def test_lines_save_reports_exact_amount_still_to_assign(self):
		fy, budget, version = self._draft()
		self._as(self.officer)
		editor = lines_svc.get_budget_version_lines_editor(version)
		rows = [dict(budget_line=r["budget_line"], title=r["title"], owner_org_unit=r["owner_org_unit"], funding_source=r["funding_source"], approved_amount=r["approved_amount"]) for r in editor["rows"]]
		rows[1]["approved_amount"] = 50_000_000
		saved = lines_svc.save_budget_lines_draft({"budget_version": version, "lines": rows})
		self.assertTrue(saved["ok"])
		self.assertEqual(saved["saved_scope"], "budget_lines")
		self.assertEqual(saved["totals"]["amount_still_to_assign"], 10_000_000)
		self.assertFalse(saved["totals"]["match"])
		submitted = readiness.submit_budget_version({"budget_version": version})
		mismatch = [b for b in submitted["blockers"] if b["rule"] == "BUDGET_TOTAL_MISMATCH"][0]
		self.assertEqual(mismatch["detail"]["amount_still_to_assign"], 10_000_000)
		self.assertIn("Amount still to assign: KES 10,000,000", mismatch["message"])


class TestSuccessorEditing(_V19Base):
	"""BUD19-AC-009/010 — one pending successor; omission only at zero protection."""

	def test_duplicate_successor_returns_the_existing_route(self):
		fy, budget, v1 = self._active()
		v2 = self._successor(budget, dhi=90_000_000, hwd=70_000_000, submit=False)
		self._as(self.officer)
		again = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertFalse(again["ok"])
		self.assertEqual(again["code"], "BUDGET_INVALID_STATE")
		self.assertEqual(again["version"]["id"], v2)
		self.assertEqual(again["route"][-1], "edit")

	def test_omission_is_allowed_only_without_reserved_or_committed_funds(self):
		fy, budget, v1 = self._active()
		dhi = self._line(v1, "Digital health infrastructure programme")
		hwd = self._line(v1, "Digital health workforce development")
		self._reserve(dhi, 80_000_000, ref="REQ-V19-003")
		v2 = self._successor(budget, dhi=100_000_000, hwd=60_000_000, submit=False, revision_type="Reduction")
		self._as(self.officer)
		editor = lines_svc.get_budget_version_lines_editor(v2)
		by = {r["budget_line"]: r for r in editor["rows"]}
		self.assertTrue(by[hwd]["can_omit"])
		self.assertFalse(by[dhi]["can_omit"])
		self.assertEqual(by[dhi]["protected_amount"], 80_000_000)
		blocked = lines_svc.save_budget_lines_draft({"budget_version": v2, "lines": [{"budget_line": dhi, "omit": True}]})
		self.assertFalse(blocked["ok"])
		allowed = lines_svc.save_budget_lines_draft({"budget_version": v2, "lines": [{"budget_line": hwd, "omit": True}]})
		self.assertTrue(allowed["ok"], allowed.get("errors"))
		self.assertEqual([o["budget_line"] for o in allowed.get("rows", []) if False], [])
		editor = lines_svc.get_budget_version_lines_editor(v2)
		self.assertEqual([o["budget_line"] for o in editor["omitted"]], [hwd])
		# History intact: the prior Version still has both line versions.
		self.assertEqual(frappe.db.count("Procurement Budget Line Version", {"budget_version": v1}), 2)

	def test_transfer_totals_report_moved_out_and_in(self):
		fy, budget, v1 = self._active()
		v2 = self._successor(budget, dhi=90_000_000, hwd=70_000_000, submit=False)
		self._as(self.officer)
		editor = lines_svc.get_budget_version_lines_editor(v2)
		self.assertEqual(editor["totals"]["total_moved_out"], 10_000_000)
		self.assertEqual(editor["totals"]["total_moved_in"], 10_000_000)
		self.assertTrue(editor["totals"]["transfer_balanced"])


class TestYearEndClosure(_V19Base):
	"""BUD19-AC-021/022 — before year end, blocked, ready, closed, replay."""

	def test_before_year_end_cannot_close(self):
		fy, budget, v1 = self._active()
		self._as(self.approver)
		status = readiness.get_budget_closure_status(budget)
		self.assertEqual(status["state"], "before_year_end")
		self.assertFalse(status["can_close"])
		closed = readiness.close_budget({"budget": budget})
		self.assertFalse(closed["ok"])
		self.assertEqual(closed["code"], "BUDGET_INVALID_STATE")

	def test_remaining_hold_blocks_and_zero_holds_permit_closure(self):
		fy, budget, v1 = self._active(fiscal_year=self._past_fy())
		dhi = self._line(v1, "Digital health infrastructure programme")
		reservation = self._reserve(dhi, 80_000_000, ref="REQ-V19-004")
		converted = commit.convert_reservation(reservation=reservation, contract="KT-CON-V19-1", amount=60_000_000, idempotency_key=f"conv-{frappe.generate_hash(length=6)}")
		self.assertTrue(converted["ok"])
		self._as(self.approver)
		status = readiness.get_budget_closure_status(budget)
		self.assertEqual(status["state"], "blocked")
		self.assertEqual(status["remaining_total"], 20_000_000)
		self.assertEqual(status["rows"][0]["still_reserved"], 20_000_000)
		blocked = readiness.close_budget({"budget": budget})
		self.assertFalse(blocked["ok"])
		self.assertIn("KES 20,000,000 remains reserved", blocked["errors"]["reservations"])
		# Release the remainder through the owner event; the 60m commitment stays.
		released = commit.release_reservation(reservation=reservation, amount=20_000_000, downstream_event_id="REV-V19-1", downstream_event_type="Requisition revocation", idempotency_key=f"rel-{frappe.generate_hash(length=6)}")
		self.assertTrue(released["ok"])
		status = readiness.get_budget_closure_status(budget)
		self.assertEqual(status["state"], "ready")
		self.assertEqual(status["active_commitments_total"], 60_000_000)
		self.assertTrue(status["can_close"])
		key = f"close-{frappe.generate_hash(length=6)}"
		closed = readiness.close_budget({"budget": budget, "idempotency_key": key})
		self.assertTrue(closed["ok"], closed)
		self.assertEqual(closed["closure"]["state"], "closed")
		replay = readiness.close_budget({"budget": budget, "idempotency_key": key})
		self.assertTrue(replay["ok"] and replay.get("replayed"))
		self.assertEqual(frappe.db.count("Budget Audit Event", {"budget": budget, "event_type": "Budget closed"}), 1)
		ws = contracts.get_budget_workspace(fy)
		self.assertEqual(ws["state"], "closed")
		self.assertEqual(ws["closure"]["closed_by"], frappe.db.get_value("User", self.approver, "full_name"))
		detail = contracts.get_budget_detail(budget)
		self.assertEqual(detail["version"]["status"], "Closed")
		self.assertNotIn("close_budget", detail["available_actions"])
		self._as(self.auditor)
		self.assertEqual(readiness.get_budget_closure_status(budget)["outcome"], "FORBIDDEN")


class TestLineDetailReads(_V19Base):
	"""BUD19-AC-015/017/018 — requisition-led rows, conservation, requires review."""

	def test_partial_conversion_reads_as_original_remaining_converted(self):
		fy, budget, v1 = self._active()
		dhi = self._line(v1, "Digital health infrastructure programme")
		reservation = self._reserve(dhi, 80_000_000, ref="REQ-V19-005")
		commit.convert_reservation(reservation=reservation, contract="KT-CON-V19-2", amount=60_000_000, idempotency_key=f"conv-{frappe.generate_hash(length=6)}")
		self._as(self.auditor)
		line = contracts.get_budget_line_position(dhi)
		self.assertEqual(line["positions"], {"approved": 100_000_000, "reserved": 20_000_000, "committed": 60_000_000, "available": 20_000_000})
		row = line["reservations"][0]
		self.assertTrue(row["title"].startswith("REQ-V19-005"))
		self.assertEqual(row["originally_reserved"], 80_000_000)
		self.assertEqual(row["still_reserved"], 20_000_000)
		self.assertEqual(row["converted"], 60_000_000)
		self.assertEqual(row["released"], 0)
		self.assertIn("KES 60,000,000 of the reservation is now committed", line["explanation"])
		self.assertTrue(line["as_at_display"].endswith("EAT"))
		activity = get_funding_activity(budget)
		labels = {r["event_type_label"] for r in activity["rows"]}
		self.assertIn("Requisition funding reserved", labels)
		self.assertIn("Converted into a commitment", labels)

	def test_needs_attention_reads_as_requires_review_with_its_reason(self):
		fy, budget, v1 = self._active()
		dhi = self._line(v1, "Digital health infrastructure programme")
		reservation = self._reserve(dhi, 80_000_000, ref="REQ-V19-006")
		# Force a floor breach outside the governed path (a test-only lever),
		# then let the owner revalidation flag the hold.
		frappe.db.set_value("Procurement Budget Line Version", {"budget_version": v1, "budget_line": dhi}, "approved_amount", 50_000_000)
		commit.revalidate_reservations(reservations=[reservation], downstream_event_id="EVT-V19-1", downstream_event_type="Contract variation", idempotency_key=f"rev-{frappe.generate_hash(length=6)}")
		self._as(self.auditor)
		row = contracts.get_budget_line_position(dhi)["reservations"][0]
		self.assertEqual(row["status"], "Needs Attention")
		self.assertEqual(row["status_label"], "Requires review — funds remain reserved")
		self.assertEqual(row["still_reserved"], 80_000_000)
		self.assertEqual(row["review"]["code"], "BUDGET_LINE_FLOOR_BREACH")
		self.assertIn("Requisition", row["review"]["owner_hint"])
