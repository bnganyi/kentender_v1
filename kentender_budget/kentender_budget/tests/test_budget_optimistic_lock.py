# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-119 (Budget side), AUD-BUD-006, AUD-BUD-007 (server side) — the
Version's `modified` stamp is mandatory on every state-changing command and a
line save advances it; a line save is one validated change set that either
applies completely or leaves the Draft exactly as it was."""

from __future__ import annotations

from decimal import Decimal

import frappe
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE, _BudgetLifecycleTestBase
from kentender_budget.utils.version_stamp import current_stamp

STALE = "BUDGET_STALE_WRITE"


class _Base(_BudgetLifecycleTestBase):
	def _draft(self, amount=10_000_000):
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{"fiscal_year": self._fresh_fy(), "approval_reference": f"OL-{self.suffix}", "approval_date": add_days(nowdate(), -5), "authorised_total": amount}
		)
		self.assertTrue(result["ok"], result)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		saved = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "expected_modified": result["version"]["modified"], "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": amount}]}
		)
		self.assertTrue(saved["ok"], saved)
		for line in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", line)
		return result["budget"]["id"], version, saved["version"]["modified"]

	def _amounts(self, version):
		return {r.budget_line: r.approved_amount for r in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, fields=["budget_line", "approved_amount"])}


class TestTheStampIsMandatory(_Base):
	def test_the_draft_commands_refuse_a_missing_stamp_and_change_nothing(self):
		"""AUD-XC-119 — omitting `expected_modified` is refused (BUDGET_STALE_WRITE) on
		the draft save, the line save and submit, with no effect."""
		_budget, version, _stamp = self._draft()
		self._as(self.officer)
		before = current_stamp(version)
		refusals = {
			"draft": contracts.save_budget_version_draft({"budget_version": version, "approval_reference": "X", "approval_date": add_days(nowdate(), -1), "authorised_total": 10_000_000}),
			"lines": lines_svc.save_budget_lines_draft({"budget_version": version, "lines": []}),
			"submit": readiness.submit_budget_version({"budget_version": version}),
		}
		for name, result in refusals.items():
			with self.subTest(command=name):
				self.assertFalse(result["ok"], result)
				self.assertEqual(result["code"], STALE)
				self.assertIn("expected_modified", result["errors"])
		self.assertEqual(current_stamp(version), before, "a refused command changed nothing")
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Draft")
		self._as("Administrator")

	def test_return_approve_and_close_need_the_stamp_too(self):
		budget, version, stamp = self._draft()
		self._as(self.officer)
		submitted = readiness.submit_budget_version({"budget_version": version, "expected_modified": stamp})
		self.assertTrue(submitted["ok"], submitted)
		self._as(self.approver)
		no_stamp = readiness.approve_budget_version({"budget_version": version})
		self.assertEqual((no_stamp["ok"], no_stamp["code"]), (False, STALE))
		no_stamp = readiness.return_budget_version({"budget_version": version, "return_reason": "A sufficiently long reason."})
		self.assertEqual((no_stamp["ok"], no_stamp["code"]), (False, STALE))
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Submitted for approval")
		approved = readiness.approve_budget_version({"budget_version": version, "expected_modified": submitted["version"]["modified"]})
		self.assertTrue(approved["ok"], approved)
		fy = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		frappe.db.set_value("Fiscal Year", fy, "year_end_date", add_days(nowdate(), -3))
		no_stamp = readiness.close_budget({"budget": budget})
		self.assertEqual((no_stamp["ok"], no_stamp["code"]), (False, STALE))
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", version, "status"), "Active")
		closed = readiness.close_budget({"budget": budget, "expected_modified": approved["version"]["modified"]})
		self.assertTrue(closed["ok"], closed)
		self._as("Administrator")

	def test_a_stale_stamp_is_refused_and_a_current_one_accepted(self):
		_budget, version, stamp = self._draft()
		self._as(self.officer)
		stale = contracts.save_budget_version_draft({"budget_version": version, "approval_reference": "Y", "approval_date": add_days(nowdate(), -1), "authorised_total": 10_000_000, "expected_modified": "2000-01-01 00:00:00.000000"})
		self.assertEqual(stale["code"], STALE)
		ok = contracts.save_budget_version_draft({"budget_version": version, "approval_reference": "Y", "approval_date": add_days(nowdate(), -1), "authorised_total": 10_000_000, "expected_modified": stamp})
		self.assertTrue(ok["ok"], ok)
		self.assertNotEqual(ok["version"]["modified"], stamp, "the draft save moves the stamp")
		self._as("Administrator")


class TestALineSaveMovesTheStamp(_Base):
	def test_a_second_line_save_with_the_pre_first_stamp_is_refused(self):
		"""AUD-BUD-007 / AUD-XC-119 — two Officers load the Draft at stamp M0; A saves
		50,000,000; B saves 60,000,000 with M0: refused, A's amount stands."""
		_budget, version, m0 = self._draft(amount=100_000_000)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		self._as(self.officer)
		first = lines_svc.save_budget_lines_draft({"budget_version": version, "expected_modified": m0, "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("50000000")}]})
		self.assertTrue(first["ok"], first)
		self.assertNotEqual(first["version"]["modified"], m0, "a line save advances the Version's stamp")
		second = lines_svc.save_budget_lines_draft({"budget_version": version, "expected_modified": m0, "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("60000000")}]})
		self.assertEqual(second["code"], STALE, second)
		self.assertEqual(self._amounts(version)[line], 50_000_000)
		third = lines_svc.save_budget_lines_draft({"budget_version": version, "expected_modified": first["version"]["modified"], "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("60000000")}]})
		self.assertTrue(third["ok"], third)
		self.assertEqual(self._amounts(version)[line], 60_000_000)
		self._as("Administrator")

	def test_the_draft_details_save_is_refused_after_a_line_save_it_did_not_see(self):
		_budget, version, m0 = self._draft(amount=100_000_000)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		self._as(self.officer)
		lines_svc.save_budget_lines_draft({"budget_version": version, "expected_modified": m0, "lines": [{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("70000000")}]})
		stale = contracts.save_budget_version_draft({"budget_version": version, "approval_reference": "Z", "approval_date": add_days(nowdate(), -1), "authorised_total": 100_000_000, "expected_modified": m0})
		self.assertEqual(stale["code"], STALE)
		self._as("Administrator")


class TestALineSaveIsOneChangeSet(_Base):
	def test_a_valid_row_before_a_refused_row_is_not_kept(self):
		"""AUD-BUD-006 — payload [valid change to Line A, a new line with no title]:
		the response is not ok and Line A, the line count and the stamp are as before."""
		_budget, version, stamp = self._draft(amount=100_000_000)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		lines_before = frappe.db.count("Procurement Budget Line", {"budget": frappe.db.get_value("Procurement Budget Version", version, "budget")})
		versions_before = frappe.db.count("Procurement Budget Line Version", {"budget_version": version})
		self._as(self.officer)
		result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version,
				"expected_modified": stamp,
				"lines": [
					{"budget_line": line, "title": "Line A renamed", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("40000000")},
					{"title": "New line ok", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("10")},
					{"title": "", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("20")},
				],
			}
		)
		self.assertFalse(result["ok"], result)
		self.assertIn("lines.2.title", result["errors"])
		self.assertEqual(self._amounts(version)[line], 100_000_000)
		self.assertEqual(frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, "title"), "Line A")
		self.assertEqual(frappe.db.count("Procurement Budget Line Version", {"budget_version": version}), versions_before)
		self.assertEqual(frappe.db.count("Procurement Budget Line", {"budget": frappe.db.get_value("Procurement Budget Version", version, "budget")}), lines_before)
		self.assertEqual(current_stamp(version), stamp, "a refused change set does not move the stamp")
		self._as("Administrator")

	def test_a_removal_before_a_refused_row_is_not_applied(self):
		_budget, version, stamp = self._draft(amount=100_000_000)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		self._as(self.officer)
		result = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "expected_modified": stamp, "lines": [{"budget_line": line, "remove": True}, {"title": "", "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("5")}]}
		)
		self.assertFalse(result["ok"], result)
		self.assertEqual(self._amounts(version), {line: 100_000_000})
		self._as("Administrator")

	def test_a_fully_valid_change_set_applies_completely_and_returns_the_new_stamp(self):
		_budget, version, stamp = self._draft(amount=100_000_000)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version}, "budget_line")
		self._as(self.officer)
		result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version,
				"expected_modified": stamp,
				"lines": [
					{"budget_line": line, "title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("60000000")},
					{"title": "Line B", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": Decimal("40000000")},
				],
			}
		)
		self.assertTrue(result["ok"], result)
		self.assertEqual(sorted(self._amounts(version).values()), [40_000_000, 60_000_000])
		self.assertTrue(result["totals"]["match"], result["totals"])
		self.assertEqual(result["version"]["modified"], current_stamp(version))
		for name in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", name)
		self._as("Administrator")
