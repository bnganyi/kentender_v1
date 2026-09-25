# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.11 §16.4 — the Budget receiving side of a Procurement
Planning budget revision request, proven from Budget's side alone
(FU-V127-02: it was only ever exercised through Planning's tests).

BUD21-AC-001 receipt from the Planning service principal, idempotent;
BUD21-AC-002 not required / stale basis; BUD21-AC-003 the successor it opens
or reuses is linked; BUD21-AC-004 Revised on activation of a successor that
changes the line, Open otherwise; BUD21-AC-005 decline, withdraw and
closure; BUD21-AC-006 one outcome event each, delivered once and in order,
retried when a consumer fails; BUD21-AC-007/008 only the Budget Officer's
work, never cleared by viewing, and no Planning state on a Budget screen.

Budget is upstream of Procurement, so nothing here imports Planning: the
tests act as the registered Planning principal through the same flag
Planning's gateway sets, and replace the outcome consumers with a recorder.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import frappe
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_revision_request_contracts as brr
from kentender_budget.services.budget_my_work_provider import my_work_rows
from kentender_budget.tests.test_bud_chg_001_v19_usability import _V19Base
from kentender_core.services.responsibility_errors import ResponsibilityError

HWD = "Digital health workforce development"
DHI = "Digital health infrastructure programme"

#: Outcome bodies handed to the recording consumer, in delivery order.
DELIVERED: list[dict] = []
FAIL_DELIVERY = {"on": False}


def record_outcome(body: dict) -> None:
	"""The test's stand-in for `kt_budget_revision_outcome_consumers`."""
	if FAIL_DELIVERY["on"]:
		raise RuntimeError("consumer unavailable")
	DELIVERED.append(dict(body))


@contextmanager
def recording_consumer():
	original = frappe.get_hooks

	def hooks(name=None, *args, **kwargs):
		if name == brr.CONSUMERS_HOOK:
			return ["kentender_budget.tests.test_bud_chg_001_v111_revision_request.record_outcome"]
		return original(name, *args, **kwargs)

	DELIVERED.clear()
	FAIL_DELIVERY["on"] = False
	with patch.object(frappe, "get_hooks", side_effect=hooks):
		yield DELIVERED


@contextmanager
def as_planning():
	frappe.flags[brr.PRINCIPAL_FLAG] = brr.PLANNING_PRINCIPAL
	try:
		yield
	finally:
		frappe.flags.pop(brr.PRINCIPAL_FLAG, None)


class _RevisionRequestBase(_V19Base):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.planner = cls._make_user("planner", ("Procurement Planner",))

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for budget in cls._budgets:
			requests = frappe.get_all("Budget Revision Request", filters={"budget": budget}, pluck="name")
			for name in frappe.get_all("Budget Revision Request Event", filters={"budget_revision_request": ("in", requests or ["-"])}, pluck="name"):
				frappe.delete_doc("Budget Revision Request Event", name, force=True, ignore_permissions=True)
			for name in requests:
				frappe.delete_doc("Budget Revision Request", name, force=True, ignore_permissions=True)
		super().tearDownClass()

	def receive(self, fy: str, line: str, planned: float, *, planning_id: str | None = None, key: str | None = None, **extra) -> dict:
		planning_id = planning_id or f"PBR-TEST-{frappe.generate_hash(length=8).upper()}"
		payload = {
			"planning_request_id": planning_id,
			"idempotency_key": key or f"key-{planning_id}",
			"fiscal_year": fy,
			"budget_line": line,
			"planned_amount": planned,
			"plan_version_reference": "PLN-TEST-V2",
			"plan_label": "PLN-TEST, Version 2",
			"requested_by": self.planner,
			**extra,
		}
		frappe.set_user("Administrator")
		with as_planning():
			return brr.receive_budget_revision_request(payload)

	def request(self, result: dict):
		return frappe.get_doc("Budget Revision Request", {"budget_revision_request_id": result["budget_revision_request_id"]})

	def approved(self, version: str, line: str) -> float:
		return frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, "approved_amount")


class TestReceipt(_RevisionRequestBase):
	def test_ac_001_one_open_request_replayed_idempotently_with_no_budget_effect(self):
		fy, budget, v1 = self._active()
		hwd = self._line(v1, HWD)
		reservations_before = frappe.db.count("Funding Reservation", {"budget": budget})

		first = self.receive(fy, hwd, 62_000_000, planning_id="PBR-TEST-AC001-" + self.suffix)
		self.assertTrue(first["ok"], first)
		request = self.request(first)
		self.assertEqual(request.status, brr.STATUS_OPEN)
		self.assertEqual(request.approved_amount_at_receipt, 60_000_000)
		self.assertEqual(request.over_amount, 2_000_000)
		self.assertEqual(request.budget_line_version_at_receipt, frappe.db.get_value("Procurement Budget Line Version", {"budget_version": v1, "budget_line": hwd}, "name"))
		self.assertEqual(request.requested_by, self.planner)
		self.assertTrue(request.requested_by_assignment)

		# The same request again is a replay, not a second request.
		again = self.receive(fy, hwd, 62_000_000, planning_id=request.planning_request_id)
		self.assertTrue(again["ok"])
		self.assertTrue(again["replayed"])
		self.assertEqual(again["budget_revision_request_id"], first["budget_revision_request_id"])
		self.assertEqual(frappe.db.count("Budget Revision Request", {"planning_request_id": request.planning_request_id}), 1)
		# The same Planning request with different content is refused.
		conflict = self.receive(fy, hwd, 63_000_000, planning_id=request.planning_request_id)
		self.assertEqual(conflict["code"], "BUDGET_IDEMPOTENCY_CONFLICT")

		# BUD-BR-028 — a request is not a revision: nothing about the money moves.
		self.assertEqual(self.approved(v1, hwd), 60_000_000)
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", v1, "status"), "Active")
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget": budget}), reservations_before)
		self.assertTrue(frappe.db.exists("Budget Audit Event", {"budget": budget, "downstream_reference": request.planning_request_id}))

	def test_ac_001_only_the_planning_principal_for_a_current_planner(self):
		fy, budget, v1 = self._active()
		hwd = self._line(v1, HWD)
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			brr.receive_budget_revision_request({"planning_request_id": "PBR-TEST-NOPRINCIPAL", "fiscal_year": fy, "budget_line": hwd, "planned_amount": 62_000_000, "requested_by": self.planner})
		with self.assertRaises(frappe.PermissionError):
			self.receive(fy, hwd, 62_000_000, requested_by=self.nobody)

	def test_ac_002_not_required_and_stale_basis(self):
		fy, budget, v1 = self._active()
		hwd = self._line(v1, HWD)
		fits = self.receive(fy, hwd, 60_000_000)
		self.assertFalse(fits["ok"])
		self.assertEqual(fits["code"], "BUDGET_REVISION_NOT_REQUIRED")
		stale = self.receive(fy, hwd, 62_000_000, expected_line_revision="not-the-current-line-version")
		self.assertFalse(stale["ok"])
		self.assertEqual(stale["code"], "BUDGET_DECISION_BASIS_STALE")
		self.assertEqual(frappe.db.count("Budget Revision Request", {"budget": budget}), 0)


class TestAnswering(_RevisionRequestBase):
	def test_ac_003_update_registered_allocation_opens_or_reuses_the_successor_and_links_it(self):
		fy, budget, v1 = self._active()
		hwd, dhi = self._line(v1, HWD), self._line(v1, DHI)
		first = self.receive(fy, hwd, 62_000_000)
		second = self.receive(fy, dhi, 101_000_000)

		self._as(self.officer)
		created = contracts.create_budget_successor_version(budget, {"revision_type": "Supplementary allocation", "budget_revision_request_id": first["budget_revision_request_id"]})
		self.assertTrue(created["ok"], created)
		successor = created["version"]["id"]
		self._track("Procurement Budget Version", successor)
		self.assertEqual(self.request(first).linked_budget_version, successor)
		# A second answer reuses the one open successor and links it too.
		reused = contracts.create_budget_successor_version(budget, {"revision_type": "Supplementary allocation", "budget_revision_request_id": second["budget_revision_request_id"]})
		self.assertFalse(reused["ok"])
		self.assertTrue(reused["existing"])
		self.assertEqual(self.request(second).linked_budget_version, successor)
		self.assertEqual(frappe.db.count("Procurement Budget Version", {"budget": budget, "status": "Draft"}), 1)
		# Linking answers nothing: both stay Open until the successor is approved.
		self.assertEqual({self.request(first).status, self.request(second).status}, {brr.STATUS_OPEN})

	def test_ac_004_activation_revises_a_changed_line_and_leaves_an_unchanged_one_open(self):
		fy, budget, v1 = self._active()
		hwd, dhi = self._line(v1, HWD), self._line(v1, DHI)
		on_hwd = self.receive(fy, hwd, 62_000_000)
		on_dhi = self.receive(fy, dhi, 101_000_000)

		with recording_consumer() as delivered:
			successor = self._successor(budget, dhi=100_000_000, hwd=62_000_000, submit=False, revision_type="Supplementary allocation")
			self._as(self.officer)
			details = contracts.save_budget_version_draft({
				"budget_version": successor, "approval_reference": f"SUPP-{self.suffix}", "approval_date": add_days(nowdate(), -1),
				"authorised_total": 162_000_000, "approval_document": "/files/test-approval.pdf",
			})
			self.assertTrue(details["ok"], details.get("errors"))
			from kentender_budget.services import budget_readiness_contracts as readiness

			submitted = readiness.submit_budget_version({"budget_version": successor})
			self.assertTrue(submitted["ok"], submitted.get("blockers"))
			self._as(self.approver)
			approved = readiness.approve_budget_version({"budget_version": successor})
			self.assertTrue(approved["ok"], approved.get("blockers"))

		revised = self.request(on_hwd)
		self.assertEqual(revised.status, brr.STATUS_REVISED)
		self.assertTrue(revised.outcome_at)
		self.assertEqual(self.request(on_dhi).status, brr.STATUS_OPEN)
		# Planning is told once, with the line's new approved amount.
		self.assertEqual([(d["outcome"], d["planning_request_id"]) for d in delivered], [("Revised", revised.planning_request_id)])
		self.assertEqual(delivered[0]["resulting_approved_amount"], 62_000_000)
		self.assertEqual(delivered[0]["resulting_line_version"], frappe.db.get_value("Procurement Budget Line Version", {"budget_version": successor, "budget_line": hwd}, "name"))

	def test_ac_005_decline_needs_the_budget_officer_and_a_reason_and_answers_once(self):
		fy, budget, v1 = self._active()
		result = self.receive(fy, self._line(v1, HWD), 62_000_000)
		request = self.request(result)
		with recording_consumer() as delivered:
			for reader in (self.approver, self.auditor, self.nobody):
				self._as(reader)
				# Budget's refusal for a missing responsibility (as elsewhere in
				# Budget), not a generic permission error.
				with self.assertRaises(ResponsibilityError):
					brr.decline_budget_revision_request({"budget_revision_request": request.name, "reason": "No further allocation this year."})
			self._as(self.officer)
			for reason in ("too short", "x" * 501):
				refused = brr.decline_budget_revision_request({"budget_revision_request": request.name, "reason": reason})
				self.assertEqual(refused["code"], "BUDGET_REASON_REQUIRED")
			declined = brr.decline_budget_revision_request({"budget_revision_request": request.name, "reason": "No further allocation this year."})
			self.assertTrue(declined["ok"], declined)
			again = brr.decline_budget_revision_request({"budget_revision_request": request.name, "reason": "A second answer to the same request."})
			self.assertEqual(again["code"], "BUDGET_REVISION_REQUEST_CLOSED")
		request.reload()
		self.assertEqual((request.status, request.decline_reason, request.outcome_by), (brr.STATUS_DECLINED, "No further allocation this year.", self.officer))
		self.assertEqual([d["outcome"] for d in delivered], ["Declined"])
		self.assertEqual(delivered[0]["reason"], "No further allocation this year.")

	def test_ac_005_withdraw_comes_only_from_planning_and_leaves_the_successor(self):
		fy, budget, v1 = self._active()
		result = self.receive(fy, self._line(v1, HWD), 62_000_000)
		request = self.request(result)
		self._as(self.officer)
		created = contracts.create_budget_successor_version(budget, {"revision_type": "Supplementary allocation", "budget_revision_request_id": result["budget_revision_request_id"]})
		successor = created["version"]["id"]
		self._track("Procurement Budget Version", successor)

		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			brr.withdraw_budget_revision_request({"planning_request_id": request.planning_request_id})
		with recording_consumer() as delivered, as_planning():
			withdrawn = brr.withdraw_budget_revision_request({"planning_request_id": request.planning_request_id})
			self.assertTrue(withdrawn["ok"], withdrawn)
			self.assertEqual(brr.withdraw_budget_revision_request({"planning_request_id": request.planning_request_id})["code"], "BUDGET_REVISION_REQUEST_CLOSED")
		self.assertEqual(self.request(result).status, brr.STATUS_WITHDRAWN)
		self.assertEqual([d["outcome"] for d in delivered], ["Withdrawn"])
		# The successor already started stays ordinary Budget Officer work.
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", successor, "status"), "Draft")

	def test_ac_005_closing_the_budget_declines_what_is_still_open(self):
		fy, budget, v1 = self._active(fiscal_year=self._past_fy())
		result = self.receive(fy, self._line(v1, HWD), 62_000_000)
		from kentender_budget.services import budget_readiness_contracts as readiness

		with recording_consumer() as delivered:
			self._as(self.approver)
			closed = readiness.close_budget({"budget": budget})
			self.assertTrue(closed["ok"], closed)
		request = self.request(result)
		self.assertEqual((request.status, request.decline_reason), (brr.STATUS_DECLINED, brr.CLOSED_BUDGET_REASON))
		self.assertEqual([(d["outcome"], d["reason"]) for d in delivered], [("Declined", brr.CLOSED_BUDGET_REASON)])


class TestOutcomeOutbox(_RevisionRequestBase):
	def test_ac_006_one_event_per_outcome_in_utc_and_retried_in_order_after_a_failure(self):
		fy, budget, v1 = self._active()
		result = self.receive(fy, self._line(v1, HWD), 62_000_000)
		request = self.request(result)
		with recording_consumer() as delivered:
			FAIL_DELIVERY["on"] = True
			self._as(self.officer)
			declined = brr.decline_budget_revision_request({"budget_revision_request": request.name, "reason": "No further allocation this year."})
			# The Budget answer stands even though Planning could not be told.
			self.assertTrue(declined["ok"], declined)
			self.assertEqual(self.request(result).status, brr.STATUS_DECLINED)
			event = frappe.get_doc("Budget Revision Request Event", {"budget_revision_request": request.name})
			self.assertEqual((event.status, event.attempts, event.sequence), ("Pending", 1, 1))
			self.assertEqual(delivered, [])

			FAIL_DELIVERY["on"] = False
			frappe.set_user("Administrator")
			# The scheduler entry commits its deliveries; held back here so the
			# class's fixtures still roll back with it (it left them behind).
			with patch.object(frappe.db, "commit"):
				self.assertGreaterEqual(brr.retry_pending_outcomes(), 1)
				self.assertEqual(brr.retry_pending_outcomes(), 0)
		event.reload()
		self.assertEqual(event.status, "Delivered")
		mine = [d for d in delivered if d["planning_request_id"] == request.planning_request_id]
		self.assertEqual(len(mine), 1)
		self.assertEqual(mine[0]["event"], brr.OUTCOME_EVENT)
		self.assertEqual(mine[0]["sequence"], 1)
		# BUD v1.11 §6 — an instant crossing the contract is ISO-8601 UTC.
		self.assertRegex(mine[0]["decided_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
		self.assertEqual(frappe.db.count("Budget Revision Request Event", {"budget_revision_request": request.name}), 1)


class TestWhoSeesTheRequest(_RevisionRequestBase):
	def test_ac_007_only_the_budget_officer_sees_it_and_viewing_never_clears_it(self):
		fy, budget, v1 = self._active()
		result = self.receive(fy, self._line(v1, HWD), 62_000_000)
		request_id = result["budget_revision_request_id"]

		for _ in range(2):  # reading twice changes nothing
			rows = brr.open_requests_for_workspace(budget, self.officer)
			self.assertEqual([r["budget_revision_request_id"] for r in rows], [request_id])
			self._as(self.officer)
			self.assertEqual([r["budget_revision_request_id"] for r in contracts.get_budget_workspace(fy)["revision_requests"]], [request_id])
			self.assertEqual([r["task_id"] for r in my_work_rows(user=self.officer)["assigned"] if r["task_type"] == "budget.revision_request"], [request_id])
		for reader in (self.approver, self.auditor, "Administrator"):
			self.assertEqual(brr.open_requests_for_workspace(budget, reader), [], reader)
			self.assertEqual([r for r in my_work_rows(user=reader)["assigned"] if r["task_type"] == "budget.revision_request"], [], reader)

		self._as(self.officer)
		brr.decline_budget_revision_request({"budget_revision_request": self.request(result).name, "reason": "No further allocation this year."})
		self.assertEqual(brr.open_requests_for_workspace(budget, self.officer), [])
		self.assertEqual([r for r in my_work_rows(user=self.officer)["assigned"] if r["task_type"] == "budget.revision_request"], [])

	def test_ac_008_the_request_row_carries_no_planning_state(self):
		fy, budget, v1 = self._active()
		self.receive(fy, self._line(v1, HWD), 62_000_000)
		row = brr.open_requests_for_workspace(budget, self.officer)[0]
		text = " ".join(str(v) for v in row.values()).lower()
		for planning_state in ("waiting", "finance", "funding confirmation", "sign"):
			self.assertNotIn(planning_state, text)
		self.assertIn("over by kes 2,000,000", text)
