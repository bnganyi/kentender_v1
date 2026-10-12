# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Approval integrity and eligibility (WP3.3): AUD-XC-105 (no-self-approval reads
the CURRENT submission attempt and fails closed; the submit audit write is not
swallowed), AUD-BUD-001 (owner scope / source unit where money moves),
AUD-BUD-002 (immutable per-attempt submission snapshot), AUD-BUD-003 (a Closed
Budget is not re-activated by an open successor), AUD-BUD-004 (one contract on
several reservations) and AUD-BUD-010 (inactive unit / funding source on a new
line)."""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.utils import add_days, nowdate

from kentender_core.services import organisation_structure as structure
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_budget.services import budget_audit_contracts as audit
from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, PRINCIPAL_REQUISITIONS, service_caller
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE, owner_ou
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase
from kentender_budget.utils.version_stamp import stamped
from kentender_core.services.command_write_guard import purge_doc


class _Base(_PrincipalBase):
	def _draft(self, *, amount=10_000_000, user=None, ou=None, funding=FUNDING_SOURCE):
		"""A Draft baseline with one line, created by the Officer."""
		self._as(user or self.officer)
		result = contracts.save_budget_version_draft(stamped(
			{"fiscal_year": self._fresh_fy(), "approval_reference": f"AI-{self.suffix}", "approval_date": add_days(nowdate(), -5), "authorised_total": amount}
		))
		self.assertTrue(result["ok"], result)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		saved = lines_svc.save_budget_lines_draft(stamped(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp if ou is None else ou, "funding_source": funding, "approved_amount": amount}]}
		))
		self.assertTrue(saved["ok"], saved)
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)
		return result["budget"]["id"], version

	def _submit(self, version, user):
		self._as(user)
		out = readiness.submit_budget_version(stamped({"budget_version": version}))
		self.assertTrue(out["ok"], out)

	def _return(self, version, user=None):
		self._as(user or self.approver)
		out = readiness.return_budget_version(stamped({"budget_version": version, "return_reason": "Please correct the figures."}))
		self.assertTrue(out["ok"], out)

	def _set_amount(self, version, amount, user):
		self._as(user)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		out = contracts.save_budget_version_draft(stamped({"budget_version": version, "approval_reference": f"AI2-{self.suffix}", "approval_date": add_days(nowdate(), -4), "authorised_total": amount}))
		self.assertTrue(out["ok"], out)
		saved = lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": amount}]}))
		self.assertTrue(saved["ok"], saved)


class TestNoSelfApprovalOfTheCurrentAttempt(_Base):
	def test_a_resubmitting_dual_role_user_cannot_approve_their_own_new_attempt(self):
		"""AUD-XC-105 — A submits, E returns, B (Officer + Approver) edits and
		resubmits; B must be blocked even though the FIRST submitter was A."""
		_budget, version = self._draft()
		self._submit(version, self.officer)
		self._return(version)
		self._set_amount(version, 9_000_000, self.dual)
		self._submit(version, self.dual)
		self._as(self.dual)
		with self.assertRaises(ResponsibilityError) as ctx:
			readiness.approve_budget_version(stamped({"budget_version": version}))
		self.assertEqual(ctx.exception.code, "AUTH_SEGREGATION_BLOCKED")
		self._as(self.approver)
		self.assertTrue(readiness.approve_budget_version(stamped({"budget_version": version}))["ok"])

	def test_the_first_submitter_is_not_blocked_on_someone_elses_later_attempt(self):
		"""AUD-XC-105 — the earlier submitter (dual) can decide an attempt that
		another Officer submitted."""
		_budget, version = self._draft(user=self.dual)
		self._submit(version, self.dual)
		self._return(version)
		self._set_amount(version, 9_000_000, self.officer)
		self._submit(version, self.officer)
		self._as(self.dual)
		self.assertTrue(readiness.approve_budget_version(stamped({"budget_version": version}))["ok"])

	def test_a_missing_submission_event_blocks_the_decision(self):
		"""AUD-XC-105 — fail closed: with no submission event nobody can be shown
		independent of the submission, so Approve is refused for everyone."""
		_budget, version = self._draft()
		self._submit(version, self.officer)
		frappe.flags.allow_budget_audit_purge = True
		try:
			frappe.db.delete("Budget Audit Event", {"budget_version": version, "event_type": audit.EVENT_SUBMITTED})
		finally:
			frappe.flags.allow_budget_audit_purge = False
		self._as(self.approver)
		with self.assertRaises(ResponsibilityError) as ctx:
			readiness.approve_budget_version(stamped({"budget_version": version}))
		self.assertEqual(ctx.exception.code, "AUTH_SEGREGATION_BLOCKED")

	def test_a_failed_submit_audit_write_fails_the_submit(self):
		"""AUD-XC-105 — the submission event is not best-effort: if it cannot be
		written the version stays a Draft and no attempt is kept."""
		_budget, version = self._draft()
		self._as(self.officer)
		with patch.object(audit, "record_event", side_effect=frappe.ValidationError("ledger down")):
			with self.assertRaises(frappe.ValidationError):
				readiness.submit_budget_version(stamped({"budget_version": version}))
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Draft")
		self.assertEqual(frappe.db.count("Budget Submission Attempt", {"budget_version": version}), 0)
		self.assertEqual(frappe.db.count("Budget Audit Event", {"budget_version": version, "event_type": audit.EVENT_SUBMITTED}), 0)


class TestSubmissionAttemptSnapshot(_Base):
	def test_return_edit_resubmit_keeps_each_attempt_with_its_content_and_decision(self):
		"""AUD-BUD-002 — attempt 1 (10m, document D1) is returned; the Officer
		changes the figure and the document and resubmits; attempt 1 is still
		exactly what was submitted, with its decision, and history exposes both."""
		_budget, version = self._draft(amount=10_000_000)
		frappe.db.set_value("Procurement Budget Version", version, "approval_document", "/files/d1.pdf")
		self._submit(version, self.officer)
		self._return(version)
		self._as(self.officer)
		out = contracts.save_budget_version_draft(stamped(
			{"budget_version": version, "approval_reference": f"AI3-{self.suffix}", "approval_date": add_days(nowdate(), -4), "authorised_total": 9_000_000, "approval_document": "/files/d2.pdf"}
		))
		self.assertTrue(out["ok"], out)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 9_000_000}]}))
		self._submit(version, self.officer)

		history = audit.get_budget_version_history(version)
		attempts = {a["attempt_number"]: a for a in history["attempts"]}
		self.assertEqual(sorted(attempts), [1, 2])
		first, second = attempts[1], attempts[2]
		self.assertEqual(first["approval_document"], "/files/d1.pdf")
		self.assertEqual(first["authorised_total"], 10_000_000)
		self.assertEqual([l["approved_amount"] for l in first["lines"]], [10_000_000])
		self.assertEqual(first["outcome"], "Returned")
		self.assertEqual(first["decided_by"], self.approver)
		self.assertEqual(first["return_reason"], "Please correct the figures.")
		self.assertEqual(second["approval_document"], "/files/d2.pdf")
		self.assertEqual([l["approved_amount"] for l in second["lines"]], [9_000_000])
		self.assertEqual(second["outcome"], "Submitted")
		self.assertEqual(second["submitted_by"], self.officer)

		self._as(self.approver)
		self.assertTrue(readiness.approve_budget_version(stamped({"budget_version": version}))["ok"])
		frappe.db.commit()
		after = {a["attempt_number"]: a for a in audit.get_budget_version_history(version)["attempts"]}
		self.assertEqual(after[2]["outcome"], "Approved")
		self.assertEqual(after[1]["outcome"], "Returned", "an earlier attempt's decision is never overwritten")

	def test_an_attempt_cannot_be_edited_or_deleted(self):
		_budget, version = self._draft()
		self._submit(version, self.officer)
		name = frappe.db.get_value("Budget Submission Attempt", {"budget_version": version}, "name")
		self._as("Administrator")
		# no user, not even Administrator, edits or deletes an attempt (AUD-XC-006)
		attempt = frappe.get_doc("Budget Submission Attempt", name)
		attempt.approval_reference = "CHANGED"
		with self.assertRaises(frappe.PermissionError):
			attempt.save(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("Budget Submission Attempt", name, force=True, ignore_permissions=True)
		# and even the owning service's write window cannot rewrite what was submitted
		from kentender_budget.services.budget_write_family import budget_write

		with budget_write():
			with self.assertRaises(frappe.ValidationError):
				attempt.save(ignore_permissions=True)


class TestClosedBudgetStaysClosed(_Base):
	def test_an_open_successor_cannot_reactivate_a_closed_budget(self):
		"""AUD-BUD-003 — V2 is submitted, V1 is then closed after year end; approving
		V2 is refused (BUDGET_CLOSED) and no reservation is admitted."""
		budget, version = self._draft(amount=10_000_000)
		self._submit(version, self.officer)
		self._as(self.approver)
		self.assertTrue(readiness.approve_budget_version(stamped({"budget_version": version}))["ok"])
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(succ["ok"], succ)
		v2 = succ["version"]["id"]
		self._track("Procurement Budget Version", v2)
		self.assertTrue(readiness.submit_budget_version(stamped({"budget_version": v2}))["ok"])
		fy = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		frappe.db.set_value("Fiscal Year", fy, "year_end_date", add_days(nowdate(), -3))
		self._as(self.approver)
		closed = readiness.close_budget(stamped({"budget": budget}))
		self.assertTrue(closed["ok"], closed)

		self._as(self.dual)
		out = readiness.approve_budget_version(stamped({"budget_version": v2}))
		self.assertFalse(out["ok"])
		self.assertEqual(out["code"], "BUDGET_CLOSED")
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", v2, "status"), "Submitted for approval")
		self.assertFalse(frappe.db.exists("Procurement Budget Version", {"budget": budget, "status": "Active"}))
		self._as(self.hopf)
		with self.assertRaises(frappe.ValidationError):
			self._reserve_one(line, 1_000_000)

	def _reserve_one(self, line, amount):
		correlation = self._key("closed")
		checked = check_reserve.check_funding(
			plan_item="PPI-CL", plan_version="PLN-CL", source_set_hash=f"H-{correlation}",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "plan_source_allocation": f"PSA-{correlation}", "drawdown_line_id": f"DDL-{correlation}"}],
			correlation_id=correlation, caller=service_caller(PRINCIPAL_REQUISITIONS, reference="REQ-CL"), caller_reference="REQ-CL",
		)
		return checked

	def test_only_one_open_successor_is_created(self):
		"""AUD-BUD-003 — the at-most-one-open-successor rule holds on the locked path."""
		budget, version = self._draft(amount=10_000_000)
		self._submit(version, self.officer)
		self._as(self.approver)
		readiness.approve_budget_version(stamped({"budget_version": version}))
		self._as(self.officer)
		first = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(first["ok"], first)
		self._track("Procurement Budget Version", first["version"]["id"])
		second = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertFalse(second["ok"])
		self.assertEqual(second["version"]["id"], first["version"]["id"])


class TestOneContractOnSeveralReservations(_Base):
	def test_two_reservations_convert_under_one_contract(self):
		"""AUD-BUD-004 — BUD §4.6's own fixture: a 20m and a 30m reservation funding
		one contract. Two commitments, one per reservation; a repeat is a replay."""
		budget, version = self._draft(amount=100_000_000)
		self._submit(version, self.officer)
		self._as(self.approver)
		readiness.approve_budget_version(stamped({"budget_version": version}))
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		ids = []
		for amount in (20_000_000, 30_000_000):
			self._as(self.hopf)
			correlation = self._key("two")
			req = service_caller(PRINCIPAL_REQUISITIONS, reference=f"REQ-{correlation}")
			checked = check_reserve.check_funding(
				plan_item="PPI-TWO", plan_version="PLN-TWO", source_set_hash=f"H-{correlation}",
				allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "plan_source_allocation": f"PSA-{correlation}", "drawdown_line_id": f"DDL-{correlation}"}],
				correlation_id=correlation, caller=req, caller_reference=f"REQ-{correlation}",
			)
			ids.append(check_reserve.reserve_funding(token=checked["token"], source_set_hash=f"H-{correlation}", idempotency_key=correlation, caller=req)["reservations"][0]["reservation_id"])
		contract = self._key("CTR-TWO")
		caller = service_caller(PRINCIPAL_CONTRACT, reference=contract)
		first = commitment_svc.convert_reservation(ids[0], contract, 20_000_000, self._key("cv"), contract_event_id=f"{contract}:s", contract_event_type="ContractSigned", caller=caller)
		second = commitment_svc.convert_reservation(ids[1], contract, 30_000_000, self._key("cv"), contract_event_id=f"{contract}:s", contract_event_type="ContractSigned", caller=caller)
		self.assertNotEqual(first["commitment"]["commitment_id"], second["commitment"]["commitment_id"])
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": contract}), 2)
		self.assertEqual(contracts._line_position(line, contracts._line_version_for(version, line))["committed"], 50_000_000)
		again = commitment_svc.convert_reservation(ids[1], contract, 30_000_000, self._key("cv"), contract_event_id=f"{contract}:s", contract_event_type="ContractSigned", caller=caller)
		self.assertTrue(again["reused"])
		self.assertEqual(frappe.db.count("Procurement Commitment", {"contract": contract}), 2)

	def test_the_database_keeps_one_commitment_per_contract_and_reservation(self):
		unique: dict[str, list[str]] = {}
		for row in frappe.db.sql("show index from `tabProcurement Commitment`"):
			if row[1] == 0:
				unique.setdefault(row[2], []).append(row[4])
		self.assertEqual(unique.get("uq_commitment_contract_reservation"), ["contract", "reservation"])
		self.assertNotIn(["contract"], unique.values(), "the table-wide unique index on contract must be gone")

	def test_the_patch_is_idempotent(self):
		from kentender_budget.patches import bud_chg_001_v1_12_commitment_contract_unique_per_reservation as patch

		patch.execute()
		patch.execute()
		names = [r[2] for r in frappe.db.sql("show index from `tabProcurement Commitment`") if r[2] == "uq_commitment_contract_reservation"]
		self.assertEqual(len(names), 2, "one two-column unique key, not duplicated")


class TestOwnerScopeAndSourceUnit(_Base):
	def _active_line(self, *, owner):
		budget, version = self._draft(amount=100_000_000, ou=owner)
		self._submit(version, self.officer)
		self._as(self.approver)
		self.assertTrue(readiness.approve_budget_version(stamped({"budget_version": version}))["ok"])
		return frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")

	def _check(self, line, source, *, reserve=False):
		self._as(self.hopf)
		correlation = self._key("ou")
		req = service_caller(PRINCIPAL_REQUISITIONS, reference=f"REQ-{correlation}")
		row = {"budget_line": line, "amount": 1_000_000, "plan_source_allocation": f"PSA-{correlation}", "drawdown_line_id": f"DDL-{correlation}"}
		if source is not None:
			row["source_organisation_unit"] = source
		checked = check_reserve.check_funding(
			plan_item="PPI-OU", plan_version="PLN-OU", source_set_hash=f"H-{correlation}", allocations=[row], correlation_id=correlation, caller=req, caller_reference=f"REQ-{correlation}"
		)
		if reserve:
			return check_reserve.reserve_funding(token=checked["token"], source_set_hash=f"H-{correlation}", idempotency_key=correlation, caller=req)
		return checked

	def _title(self):
		return [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]

	def test_a_line_owned_by_another_department_refuses_the_allocation(self):
		"""AUD-BUD-001 — BUD18-AC-055: an isolated DHI-owned line rejects an HRMD source."""
		line = self._active_line(owner=self.ou_dhp)
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._check(line, self.ou_hrmd)
		self.assertIn("BUDGET_LINE_NOT_ELIGIBLE", self._title())
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._check(line, self.ou_hrmd, reserve=True)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)
		self.assertTrue(self._check(line, self.ou_dhp)["all_sufficient"])

	def test_a_missing_source_unit_is_refused_even_for_an_entity_wide_line(self):
		"""AUD-BUD-001 — BUDGET_SOURCE_OU_REQUIRED; Entity-wide accepts any real unit."""
		line = self._active_line(owner="")
		for source in (None, ""):
			frappe.local.message_log = []
			with self.assertRaises(frappe.ValidationError):
				self._check(line, source)
			self.assertIn("BUDGET_SOURCE_OU_REQUIRED", self._title())
		self.assertTrue(self._check(line, self.ou_dhp)["all_sufficient"])
		self.assertTrue(self._check(line, self.ou_hrmd)["all_sufficient"])

	def test_an_unknown_source_unit_is_not_eligible(self):
		line = self._active_line(owner="")
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			self._check(line, "NO-SUCH-UNIT")
		self.assertIn("BUDGET_LINE_NOT_ELIGIBLE", self._title())


class TestCatalogueStateOfNewLines(_Base):
	def test_a_new_line_cannot_name_an_inactive_unit_on_save_or_approval(self):
		"""AUD-BUD-010 — BUD18-AC-056."""
		self._as("Administrator")
		retired = structure.add_organisation_unit(name=f"KT Budget Retired {self.suffix}")["unit"]
		self._track("Organisation Unit", retired)
		frappe.db.set_value("Organisation Unit", retired, "status", "Inactive")
		self._as(self.officer)
		result = contracts.save_budget_version_draft(stamped(
			{"fiscal_year": self._fresh_fy(), "approval_reference": f"CAT-{self.suffix}", "approval_date": add_days(nowdate(), -5), "authorised_total": 5_000_000}
		))
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		saved = lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [{"title": "Retired line", "owner_org_unit": retired, "funding_source": FUNDING_SOURCE, "approved_amount": 5_000_000}]}))
		self.assertFalse(saved["ok"])
		self.assertIn("lines.0.owner_org_unit", saved["errors"])

		# A line that slipped in (or whose unit was retired afterwards, as a new line) is caught at submit and at approval.
		frappe.db.set_value("Organisation Unit", retired, "status", "Active")
		saved = lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [{"title": "Line", "owner_org_unit": retired, "funding_source": FUNDING_SOURCE, "approved_amount": 5_000_000}]}))
		self.assertTrue(saved["ok"], saved)
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)
		self._submit(version, self.officer)
		frappe.db.set_value("Organisation Unit", retired, "status", "Inactive")
		self._as(self.approver)
		out = readiness.approve_budget_version(stamped({"budget_version": version}))
		self.assertFalse(out["ok"])
		self.assertEqual(out["code"], "BUDGET_NOT_READY")
		self.assertTrue(any(b["rule"] == "BUDGET_LINE_NOT_ELIGIBLE" for b in out["blockers"]), out["blockers"])
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Submitted for approval")

	def test_a_new_line_cannot_name_a_retired_funding_source(self):
		source = frappe.get_doc({"doctype": "Funding Source", "label": f"KT Retired Source {self.suffix}", "record_status": "Retired"}).insert(ignore_permissions=True)
		self._track("Funding Source", source.name)
		self._as(self.officer)
		result = contracts.save_budget_version_draft(stamped(
			{"fiscal_year": self._fresh_fy(), "approval_reference": f"CATF-{self.suffix}", "approval_date": add_days(nowdate(), -5), "authorised_total": 5_000_000}
		))
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		saved = lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [{"title": "Retired source", "owner_org_unit": self.ou_dhp, "funding_source": source.name, "approved_amount": 5_000_000}]}))
		self.assertFalse(saved["ok"])
		self.assertIn("lines.0.funding_source", saved["errors"])
