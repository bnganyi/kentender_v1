# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §5/§6/§9.2 — Budget Version lifecycle domain rules.

Covers the core governance commands (save_budget_version_draft,
save_budget_lines_draft, submit_budget_version, return_budget_version,
approve_budget_version, create_budget_successor_version) and the readiness/
identity/floor-breach rules they enforce (BUD-BR-004/007/017/019/020/022,
BUD-AC-005-010, 022-025). Each test class gets its own disposable Financial
Year (Budget is one-per-Procuring-Entity-per-Financial-Year, so tests can't
share PE-MOH/FY-2027-2028 with the canonical seed or each other) and
disposable Officer/Approver users, torn down afterward.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_permissions import ensure_budget_roles

PE_MOH = "PE-MOH"
OU_DHP = "MOH-DIR-DHP"
OU_HRMD = "MOH-DIR-HRMD"
FUNDING_SOURCE = "Government of Kenya"


class _BudgetLifecycleTestBase(FrappeTestCase):
	"""Shared disposable-fixture scaffolding — a fresh Financial Year (and
	matching PE Fiscal Year Context) plus Officer/Approver users per test
	class, all torn down in reverse creation order."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()
		frappe.set_user("Administrator")
		cls.suffix = uuid4().hex[:6]
		cls._cleanup: list[tuple[str, str]] = []
		cls._fy_counter = 0

		cls.fy = cls._fresh_fy()

		cls.officer = cls._make_user("officer", ("Budget Officer",))
		cls.approver = cls._make_user("approver", ("Budget Approver",))
		cls.dual = cls._make_user("dual", ("Budget Officer", "Budget Approver"))
		cls.viewer = cls._make_user("viewer", ("Budget Viewer",))

	@classmethod
	def _fresh_fy(cls) -> str:
		"""Disposable Financial Year: BR-003 generates name/label/dates purely
		from start_year, so use a distinct, unlikely-to-collide future year —
		one per call, since Budget is one-per-(PE, Financial Year) and each
		test method that builds its own Active baseline needs its own slot,
		not just one shared per test class."""
		cls._fy_counter += 1
		start_year = 2100 + (int(cls.suffix, 16) + cls._fy_counter * 97) % 5000
		fy_doc = frappe.get_doc({"doctype": "Financial Year", "start_year": start_year}).insert(ignore_permissions=True)
		fy = fy_doc.name
		cls._track("Financial Year", fy)
		ctx = frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": PE_MOH,
				"financial_year": fy,
				"context_status": "Active",
				"active_from": f"{start_year}-01-01",
				"active_to": f"{start_year + 1}-09-30",
			}
		).insert(ignore_permissions=True)
		cls._track("PE Fiscal Year Context", ctx.name)
		return fy

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for doctype, name in reversed(cls._cleanup):
			if doctype == "Budget Audit Event":
				frappe.flags.allow_budget_audit_purge = True
			try:
				if frappe.db.exists(doctype, name):
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			finally:
				frappe.flags.allow_budget_audit_purge = False
		super().tearDownClass()

	@classmethod
	def _track(cls, doctype: str, name: str) -> str:
		cls._cleanup.append((doctype, name))
		return name

	@classmethod
	def _make_user(cls, label: str, roles: tuple[str, ...]) -> str:
		email = f"bud.{label}.{cls.suffix}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles(*roles)
		cls._track("User", email)
		perm = frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Procuring Entity", "for_value": PE_MOH}
		).insert(ignore_permissions=True)
		cls._track("User Permission", perm.name)
		# Budget Line's owner_org_unit scoping (assert_org_unit_in_scope) still
		# runs through the older User Scope Assignment engine, not just
		# AUTH-ADR-001 Role + User Permission — a blank organisation_unit row
		# grants entity-wide access within the PE (org_scope_access.py's
		# permitted_org_units: "any blank organisation_unit assignment =>
		# entity-wide"), matching how the real seed's own personas are set up.
		for role in roles:
			usa = frappe.get_doc(
				{
					"doctype": "User Scope Assignment",
					"user": email,
					"role": role,
					"procuring_entity": PE_MOH,
					"organisation_unit": "",
					"include_descendants": 0,
				}
			).insert(ignore_permissions=True)
			cls._track("User Scope Assignment", usa.name)
		return email

	def _as(self, user: str) -> None:
		frappe.set_user(user)

	def _create_active_baseline(self, *, dhi_amount=100_000_000, hwd_amount=60_000_000) -> tuple[str, str]:
		"""Officer creates + submits, Approver approves. Returns (budget, version)
		docnames. Uses its own fresh Financial Year (not the class-level
		self.fy) so multiple test methods in the same class — each calling
		this once — never collide on Budget's one-per-(PE, FY) rule."""
		fy = self._fresh_fy()
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": fy,
				"approval_reference": f"TEST-{self.suffix}",
				"approval_date": add_days(nowdate(), -10),
				"authorised_total": dhi_amount + hwd_amount,
				"approval_document": "/files/test-approval.pdf",
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		budget = result["budget"]["id"]
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", budget)

		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version,
				"lines": [
					{"title": "DHI test line", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": dhi_amount},
					{"title": "HWD test line", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": hwd_amount},
				],
			}
		)
		self.assertTrue(lines_result["ok"], lines_result.get("errors"))
		for lv in frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Budget Line", lv)

		submit_result = readiness.submit_budget_version({"budget_version": version})
		self.assertTrue(submit_result["ok"], submit_result.get("blockers"))

		self._as(self.approver)
		approve_result = readiness.approve_budget_version({"budget_version": version})
		self.assertTrue(approve_result["ok"], approve_result.get("blockers"))
		frappe.set_user("Administrator")
		return budget, version


class TestBudgetVersionDraftCreation(_BudgetLifecycleTestBase):
	def test_create_draft_requires_approval_evidence(self):
		"""BUD-BR-004 / BUD-AC-005 — approval reference/date/total are the only
		editable initial fields, and are mandatory."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{"procuring_entity": PE_MOH, "financial_year": self._fresh_fy(), "approval_reference": "", "approval_date": "", "authorised_total": 0}
		)
		self.assertFalse(result["ok"])
		self.assertIn("approval_reference", result["errors"])
		self.assertIn("approval_date", result["errors"])
		self.assertIn("authorised_total", result["errors"])

	def test_only_one_budget_per_pe_and_financial_year(self):
		"""BUD-BR-001."""
		self._as(self.officer)
		payload = {
			"procuring_entity": PE_MOH,
			"financial_year": self._fresh_fy(),
			"approval_reference": f"DUP-{self.suffix}",
			"approval_date": add_days(nowdate(), -5),
			"authorised_total": 1000,
			"approval_document": "/files/x.pdf",
		}
		first = contracts.save_budget_version_draft(dict(payload))
		self.assertTrue(first["ok"], first.get("errors"))
		self._track("Budget Version", first["version"]["id"])
		self._track("Budget", first["budget"]["id"])

		with self.assertRaises(frappe.DuplicateEntryError):
			contracts.save_budget_version_draft(dict(payload))


class TestBudgetLinesDraft(_BudgetLifecycleTestBase):
	def test_submit_blocked_when_line_total_does_not_match_authorised_total(self):
		"""BUD-BR-007 / BUD-AC-007."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": self._fresh_fy(),
				"approval_reference": f"MISMATCH-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 100_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", result["budget"]["id"])

		lines_result = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Under-total line", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 50_000_000}]}
		)
		self.assertTrue(lines_result["ok"], lines_result.get("errors"))
		for lv in frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Budget Line", lv)

		submit_result = readiness.submit_budget_version({"budget_version": version})
		self.assertFalse(submit_result["ok"])
		self.assertEqual(submit_result["code"], "BUDGET_NOT_READY")
		self.assertTrue(any(b["code"] == "lines.total_mismatch" for b in submit_result["blockers"]))

	def test_only_editable_line_fields_are_title_owner_funding_amount(self):
		"""BUD-BR-006 / BUD-AC-006 — no classification/purpose/Strategy fields exist to set."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": self._fresh_fy(),
				"approval_reference": f"FIELDS-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		line_name = frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line")[0]
		self._track("Budget Line", line_name)
		meta = frappe.get_meta("Budget Line")
		for forbidden in ("classification", "funding_source_type", "organisational_owner", "primary_target_code"):
			self.assertFalse(meta.has_field(forbidden), f"Budget Line must not carry {forbidden!r} (BUD-AC-002/029)")


class TestSelfApprovalSegregation(_BudgetLifecycleTestBase):
	def test_submitting_officer_cannot_approve_even_with_approver_role(self):
		"""BUD-AC-008 — the submitting Officer cannot approve their own
		version, even if they also hold Budget Approver, enforced from the
		version's own submission audit event, not a stored field."""
		self._as(self.dual)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": self._fresh_fy(),
				"approval_reference": f"SOD-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		for lv in frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Budget Line", lv)
		readiness.submit_budget_version({"budget_version": version})

		# Still self.dual (the submitter) — approve must be blocked.
		with self.assertRaises(frappe.PermissionError):
			readiness.approve_budget_version({"budget_version": version})

		# A different Approver succeeds.
		self._as(self.approver)
		approve_result = readiness.approve_budget_version({"budget_version": version})
		self.assertTrue(approve_result["ok"], approve_result.get("blockers"))


class TestReturnBudgetVersion(_BudgetLifecycleTestBase):
	def test_return_requires_reason_and_preserves_history(self):
		"""BUD-AC-009."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": self._fresh_fy(),
				"approval_reference": f"RET-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		for lv in frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Budget Line", lv)
		readiness.submit_budget_version({"budget_version": version})

		self._as(self.approver)
		too_short = readiness.return_budget_version({"budget_version": version, "return_reason": "short"})
		self.assertFalse(too_short["ok"])
		self.assertIn("return_reason", too_short["errors"])

		result2 = readiness.return_budget_version({"budget_version": version, "return_reason": "Missing supporting evidence for this line item."})
		self.assertTrue(result2["ok"], result2.get("errors"))
		doc = frappe.get_doc("Budget Version", version)
		self.assertEqual(doc.status, "Draft")
		self.assertTrue(doc.return_reason)
		# History preserved: the original submission event is still there.
		self.assertTrue(
			frappe.db.exists("Budget Audit Event", {"budget_version": version, "event_type": "Budget version submitted"})
		)
		self.assertTrue(
			frappe.db.exists("Budget Audit Event", {"budget_version": version, "event_type": "Budget version returned"})
		)


class TestActiveAndSupersededImmutability(_BudgetLifecycleTestBase):
	def test_active_version_rejects_direct_line_mutation(self):
		"""BUD-AC-010 — Active versions reject direct mutation."""
		budget, version = self._create_active_baseline()
		self._as(self.officer)
		line_name = frappe.get_all("Budget Line Version", filters={"budget_version": version}, pluck="budget_line")[0]
		with self.assertRaises(frappe.ValidationError):
			lines_svc.save_budget_lines_draft({"budget_version": version, "lines": [{"budget_line": line_name, "approved_amount": 999}]})


class TestSuccessorVersionRules(_BudgetLifecycleTestBase):
	def test_identity_locked_line_cannot_change_title_owner_or_funding_source(self):
		"""BUD-BR-019 / BUD-AC-024 — server silently holds the prior identity."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(succ["ok"], succ)
		new_version = succ["version"]["id"]
		self._track("Budget Version", new_version)

		dhi_line = frappe.db.get_value("Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")
		result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": new_version,
				"lines": [
					{"budget_line": dhi_line, "title": "Renamed", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
				],
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		saved_title = frappe.db.get_value("Budget Line Version", {"budget_version": new_version, "budget_line": dhi_line}, "title")
		self.assertEqual(saved_title, "DHI test line", "identity-locked title must not change even though the payload requested it")

	def test_previously_active_line_cannot_be_removed(self):
		"""BUD-BR-020 / BUD-AC-025 — a line with a remaining reservation
		cannot be omitted (here: any previously-Active line at all, since
		removal itself is rejected outright for a locked line)."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new_version = succ["version"]["id"]
		self._track("Budget Version", new_version)
		dhi_line = frappe.db.get_value("Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")

		result = lines_svc.save_budget_lines_draft({"budget_version": new_version, "lines": [{"budget_line": dhi_line, "remove": True}]})
		self.assertFalse(result["ok"])
		self.assertTrue(any("removed" in msg for msg in result["errors"].values()))

	def test_transfer_must_balance_increases_and_decreases(self):
		"""BUD-BR-022 — an unbalanced Transfer is blocked at submit."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new_version = succ["version"]["id"]
		self._track("Budget Version", new_version)
		dhi_line = frappe.db.get_value("Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")

		# Increase DHI by 10m without a matching decrease anywhere — unbalanced.
		lines_svc.save_budget_lines_draft(
			{"budget_version": new_version, "lines": [{"budget_line": dhi_line, "title": "DHI test line", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 110_000_000}]}
		)
		submit_result = readiness.submit_budget_version({"budget_version": new_version})
		self.assertFalse(submit_result["ok"])
		self.assertTrue(any(b["code"] == "transfer.unbalanced" or b["code"] == "transfer.total_changed" for b in submit_result["blockers"]))

	def test_approving_successor_supersedes_prior_active_version(self):
		"""BUD-AC-023 — approving a valid successor atomically supersedes the
		prior Active version."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new_version = succ["version"]["id"]
		self._track("Budget Version", new_version)
		dhi_line = frappe.db.get_value("Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")
		hwd_line = frappe.db.get_value("Budget Line Version", {"budget_version": active_version, "title": "HWD test line"}, "budget_line")

		lines_svc.save_budget_lines_draft(
			{
				"budget_version": new_version,
				"lines": [
					{"budget_line": dhi_line, "title": "DHI test line", "owner_org_unit": OU_DHP, "funding_source": FUNDING_SOURCE, "approved_amount": 90_000_000},
					{"budget_line": hwd_line, "title": "HWD test line", "owner_org_unit": OU_HRMD, "funding_source": FUNDING_SOURCE, "approved_amount": 70_000_000},
				],
			}
		)
		submit_result = readiness.submit_budget_version({"budget_version": new_version})
		self.assertTrue(submit_result["ok"], submit_result.get("blockers"))

		self._as(self.approver)
		approve_result = readiness.approve_budget_version({"budget_version": new_version})
		self.assertTrue(approve_result["ok"], approve_result.get("blockers"))

		self.assertEqual(frappe.db.get_value("Budget Version", new_version, "status"), "Active")
		self.assertEqual(frappe.db.get_value("Budget Version", active_version, "status"), "Superseded")


class TestScopeAndPermissions(_BudgetLifecycleTestBase):
	def test_administrator_without_budget_role_cannot_act(self):
		"""BUD-AC-004 — a System Administrator without a Budget assignment
		cannot create/submit/return/approve. Uses a fresh no-role user, not
		Administrator itself (which is always allowed everywhere by design)."""
		bare_user = f"bud.bare.{self.suffix}@test.local"
		if not frappe.db.exists("User", bare_user):
			frappe.get_doc(
				{"doctype": "User", "email": bare_user, "first_name": "Bare", "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
			self._track("User", bare_user)
		self._as(bare_user)
		with self.assertRaises(frappe.PermissionError):
			contracts.save_budget_version_draft(
				{
					"procuring_entity": PE_MOH,
					"financial_year": self._fresh_fy(),
					"approval_reference": "X",
					"approval_date": add_days(nowdate(), -1),
					"authorised_total": 100,
					"approval_document": "/files/x.pdf",
				}
			)

	def test_viewer_cannot_see_draft_or_submitted_version_by_direct_id(self):
		"""§7 — Viewer may see Active/Superseded/Closed only; a Draft or
		Submitted version is denied even via a direct id, not just hidden
		from a listing (Phase 4's own 'gates direct URLs too' rule)."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": PE_MOH,
				"financial_year": self._fresh_fy(),
				"approval_reference": f"VIEW-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Budget Version", version)
		self._track("Budget", result["budget"]["id"])

		self._as(self.viewer)
		with self.assertRaises(frappe.PermissionError):
			contracts.get_budget_version_draft(version)
