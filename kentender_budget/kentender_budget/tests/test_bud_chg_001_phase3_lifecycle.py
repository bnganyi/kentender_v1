# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.3 §5/§6/§9.2 — Budget Version lifecycle domain rules.

Covers the core governance commands (save_budget_version_draft,
save_budget_lines_draft, submit_budget_version, return_budget_version,
approve_budget_version, create_budget_successor_version) and the readiness/
identity/floor-breach rules they enforce (BUD-BR-004/007/017/019/020/022,
BUD-AC-005-010, 022-025). Each test class gets its own disposable ERPNext
Fiscal Year (Budget is one-per-Fiscal-Year — one site is one Procuring
Entity, so there is no PE dimension to disambiguate on any more) and
disposable Officer/Approver users, torn down afterward.

Denials surface as the closed AUTH-ADR-001 v1.6 §10 vocabulary
(`ResponsibilityError`), not `frappe.PermissionError` — mirrors
`kentender_strategy`'s own v1.6 test suite. `frappe.PermissionError` is
reserved for read-scope denials (the registered `has_permission` hook).
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.responsibility_errors import ResponsibilityError
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

FUNDING_SOURCE = "Government of Kenya"


class _BudgetLifecycleTestBase(FrappeTestCase):
	"""Shared disposable-fixture scaffolding — a fresh Fiscal Year plus
	Officer/Approver users per test class, granted through the real
	administration command (v1.6 — never a raw Role + User Permission
	pair), all torn down in reverse creation order."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_governance_roles()
		frappe.set_user("Administrator")
		cls.suffix = uuid4().hex[:6]
		cls._cleanup: list[tuple[str, str]] = []
		cls._fy_counter = 0

		cls.fy = cls._fresh_fy()
		cls.ou_dhp = cls._fresh_ou("DHP")
		cls.ou_hrmd = cls._fresh_ou("HRMD")

		cls.officer = cls._make_user("officer", ("Budget Officer",))
		cls.approver = cls._make_user("approver", ("Budget Approver",))
		cls.dual = cls._make_user("dual", ("Budget Officer", "Budget Approver"))

	@classmethod
	def _fresh_ou(cls, label: str) -> str:
		"""Disposable Organisation Unit, resolved by name through the real
		governed command. KT-STD-001 §8.2's mnemonic codes (`OU-MOH-DHP`) can
		never be produced through `add_organisation_unit` — unit codes are
		always server-generated (CFG v0.6 §4.3, see `site_setup.py`'s own
		"conflict C4" note) — so these tests resolve identity by name, exactly
		like `kentender_core.tests.v16_fixtures.unit()`, never a hardcoded
		code string a real site can never produce."""
		result = structure.add_organisation_unit(name=f"KT Budget Test {label} {cls.suffix}")
		cls._track("Organisation Unit", result["unit"])
		return result["unit"]

	@classmethod
	def _fresh_fy(cls) -> str:
		"""Disposable ERPNext Fiscal Year: Budget is one-per-Fiscal-Year, so
		each test method that builds its own Active baseline needs its own
		slot, not just one shared per test class."""
		cls._fy_counter += 1
		start_year = 2100 + (int(cls.suffix, 16) + cls._fy_counter * 97) % 5000
		fy_doc = frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": f"{start_year}-{start_year + 1}",
				"year_start_date": f"{start_year}-07-01",
				"year_end_date": f"{start_year + 1}-06-30",
			}
		).insert(ignore_permissions=True)
		fy = fy_doc.name
		cls._track("Fiscal Year", fy)
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
		"""v1.6 — authority is an Enabled Site-wide assignment granted through
		the real administration command, never a raw Role + User Permission
		pair (mirrors `kentender_strategy`'s test `_actor()` helper)."""
		email = f"bud.{label}.{cls.suffix}@test.local"
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		cls._track("User", email)
		for role in roles:
			outcome = administration.grant(
				user=email,
				business_role=role,
				organisation_unit="",
				fixture_namespace="BUD_CHG_001_TESTS",
				actor="Administrator",
			)
			cls._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
		return email

	def _as(self, user: str) -> None:
		frappe.set_user(user)

	def _create_active_baseline(self, *, dhi_amount=100_000_000, hwd_amount=60_000_000) -> tuple[str, str]:
		"""Officer creates + submits, Approver approves. Returns (budget, version)
		docnames. Uses its own fresh Fiscal Year (not the class-level self.fy)
		so multiple test methods in the same class — each calling this once —
		never collide on Budget's one-per-Fiscal-Year rule."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"TEST-{self.suffix}",
				"approval_date": add_days(nowdate(), -10),
				"authorised_total": dhi_amount + hwd_amount,
				"approval_document": "/files/test-approval.pdf",
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		budget = result["budget"]["id"]
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", budget)

		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version,
				"lines": [
					{"title": "DHI test line", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": dhi_amount},
					{"title": "HWD test line", "owner_org_unit": self.ou_hrmd, "funding_source": FUNDING_SOURCE, "approved_amount": hwd_amount},
				],
			}
		)
		self.assertTrue(lines_result["ok"], lines_result.get("errors"))
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)

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
			{"fiscal_year": self._fresh_fy(), "approval_reference": "", "approval_date": "", "authorised_total": 0}
		)
		self.assertFalse(result["ok"])
		self.assertIn("approval_reference", result["errors"])
		self.assertIn("approval_date", result["errors"])
		self.assertIn("authorised_total", result["errors"])

	def test_only_one_budget_per_fiscal_year(self):
		"""BUD-BR-002/BUD-BR-001."""
		self._as(self.officer)
		payload = {
			"fiscal_year": self._fresh_fy(),
			"approval_reference": f"DUP-{self.suffix}",
			"approval_date": add_days(nowdate(), -5),
			"authorised_total": 1000,
			"approval_document": "/files/x.pdf",
		}
		first = contracts.save_budget_version_draft(dict(payload))
		self.assertTrue(first["ok"], first.get("errors"))
		self._track("Procurement Budget Version", first["version"]["id"])
		self._track("Procurement Budget", first["budget"]["id"])

		with self.assertRaises(frappe.DuplicateEntryError):
			contracts.save_budget_version_draft(dict(payload))

	def test_registering_a_budget_does_not_require_an_approval_document(self):
		"""Approval document is not required to register/save-draft a Budget
		Version — only before it can be submitted for review (see
		test_submit_blocked_without_approval_document below). Regression test:
		Procurement Budget Version.approval_document was DB `reqd: 1`, so even
		though `_validate_draft_payload` never checked it, the very first
		`.insert()` still raised Frappe's own generic MandatoryError before the
		user ever reached the file upload step."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"NODOC-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 1000,
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		self._track("Procurement Budget Version", result["version"]["id"])
		self._track("Procurement Budget", result["budget"]["id"])

	def test_submit_blocked_without_approval_document(self):
		"""Optional at draft save, still mandatory before submission
		(BUD-BR-018-family evidence guard in `_evaluate_readiness`)."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"NODOC-SUBMIT-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])

		lines_result = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		self.assertTrue(lines_result["ok"], lines_result.get("errors"))
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)

		submit_result = readiness.submit_budget_version({"budget_version": version})
		self.assertFalse(submit_result["ok"])
		self.assertTrue(any(b["code"] == "evidence.approval_document" for b in submit_result["blockers"]))


class TestBudgetLinesDraft(_BudgetLifecycleTestBase):
	def test_submit_blocked_when_line_total_does_not_match_authorised_total(self):
		"""BUD-BR-007 / BUD-AC-007."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"MISMATCH-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 100_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])

		lines_result = lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Under-total line", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 50_000_000}]}
		)
		self.assertTrue(lines_result["ok"], lines_result.get("errors"))
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)

		submit_result = readiness.submit_budget_version({"budget_version": version})
		self.assertFalse(submit_result["ok"])
		self.assertEqual(submit_result["code"], "BUDGET_NOT_READY")
		self.assertTrue(any(b["code"] == "lines.total_mismatch" for b in submit_result["blockers"]))

	def test_only_editable_line_fields_are_title_owner_funding_amount(self):
		"""BUD-BR-006 / BUD-AC-006 — no classification/purpose/Strategy fields exist to set."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"FIELDS-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		line_name = frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line")[0]
		self._track("Procurement Budget Line", line_name)
		meta = frappe.get_meta("Procurement Budget Line")
		for forbidden in ("classification", "funding_source_type", "organisational_owner", "primary_target_code"):
			self.assertFalse(meta.has_field(forbidden), f"Budget Line must not carry {forbidden!r} (BUD-AC-002/029)")


class TestSelfApprovalSegregation(_BudgetLifecycleTestBase):
	def test_submitting_officer_cannot_approve_even_with_approver_role(self):
		"""BUD-AC-025 — the submitting Officer cannot approve their own
		version, even if they also hold Budget Approver, enforced from the
		version's own submission audit event, not a stored field."""
		self._as(self.dual)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"SOD-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)
		readiness.submit_budget_version({"budget_version": version})

		# Still self.dual (the submitter) — approve must be blocked.
		with self.assertRaises(ResponsibilityError):
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
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"RET-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])
		lines_svc.save_budget_lines_draft(
			{"budget_version": version, "lines": [{"title": "Line A", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 10_000_000}]}
		)
		for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", lv)
		readiness.submit_budget_version({"budget_version": version})

		self._as(self.approver)
		too_short = readiness.return_budget_version({"budget_version": version, "return_reason": "short"})
		self.assertFalse(too_short["ok"])
		self.assertIn("return_reason", too_short["errors"])

		result2 = readiness.return_budget_version({"budget_version": version, "return_reason": "Missing supporting evidence for this line item."})
		self.assertTrue(result2["ok"], result2.get("errors"))
		doc = frappe.get_doc("Procurement Budget Version", version)
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
		line_name = frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line")[0]
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
		self._track("Procurement Budget Version", new_version)

		dhi_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")
		result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": new_version,
				"lines": [
					{"budget_line": dhi_line, "title": "Renamed", "owner_org_unit": self.ou_hrmd, "funding_source": FUNDING_SOURCE, "approved_amount": 100_000_000},
				],
			}
		)
		self.assertTrue(result["ok"], result.get("errors"))
		saved_title = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": new_version, "budget_line": dhi_line}, "title")
		self.assertEqual(saved_title, "DHI test line", "identity-locked title must not change even though the payload requested it")

	def test_previously_active_line_cannot_be_removed(self):
		"""BUD-BR-020 / BUD-AC-025 — a line with a remaining reservation
		cannot be omitted (here: any previously-Active line at all, since
		removal itself is rejected outright for a locked line)."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new_version = succ["version"]["id"]
		self._track("Procurement Budget Version", new_version)
		dhi_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")

		result = lines_svc.save_budget_lines_draft({"budget_version": new_version, "lines": [{"budget_line": dhi_line, "remove": True}]})
		self.assertFalse(result["ok"])
		self.assertTrue(any("removed" in msg for msg in result["errors"].values()))

	def test_transfer_must_balance_increases_and_decreases(self):
		"""BUD-BR-022 — an unbalanced Transfer is blocked at submit."""
		budget, active_version = self._create_active_baseline()
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new_version = succ["version"]["id"]
		self._track("Procurement Budget Version", new_version)
		dhi_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")

		# Increase DHI by 10m without a matching decrease anywhere — unbalanced.
		lines_svc.save_budget_lines_draft(
			{"budget_version": new_version, "lines": [{"budget_line": dhi_line, "title": "DHI test line", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 110_000_000}]}
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
		self._track("Procurement Budget Version", new_version)
		dhi_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active_version, "title": "DHI test line"}, "budget_line")
		hwd_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active_version, "title": "HWD test line"}, "budget_line")

		lines_svc.save_budget_lines_draft(
			{
				"budget_version": new_version,
				"lines": [
					{"budget_line": dhi_line, "title": "DHI test line", "owner_org_unit": self.ou_dhp, "funding_source": FUNDING_SOURCE, "approved_amount": 90_000_000},
					{"budget_line": hwd_line, "title": "HWD test line", "owner_org_unit": self.ou_hrmd, "funding_source": FUNDING_SOURCE, "approved_amount": 70_000_000},
				],
			}
		)
		submit_result = readiness.submit_budget_version({"budget_version": new_version})
		self.assertTrue(submit_result["ok"], submit_result.get("blockers"))

		self._as(self.approver)
		approve_result = readiness.approve_budget_version({"budget_version": new_version})
		self.assertTrue(approve_result["ok"], approve_result.get("blockers"))

		self.assertEqual(frappe.db.get_value("Procurement Budget Version", new_version, "status"), "Active")
		self.assertEqual(frappe.db.get_value("Procurement Budget Version", active_version, "status"), "Superseded")


class TestScopeAndPermissions(_BudgetLifecycleTestBase):
	def test_bare_user_without_budget_role_cannot_act(self):
		"""BUD-AC-004 — a user without a Budget assignment cannot create/
		submit/return/approve. Uses a fresh no-role user, not Administrator
		itself (which is always allowed to read, but never to mutate,
		without an assignment — §8)."""
		bare_user = f"bud.bare.{self.suffix}@test.local"
		if not frappe.db.exists("User", bare_user):
			frappe.get_doc(
				{"doctype": "User", "email": bare_user, "first_name": "Bare", "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
			self._track("User", bare_user)
		self._as(bare_user)
		with self.assertRaises(ResponsibilityError):
			contracts.save_budget_version_draft(
				{
					"fiscal_year": self._fresh_fy(),
					"approval_reference": "X",
					"approval_date": add_days(nowdate(), -1),
					"authorised_total": 100,
					"approval_document": "/files/x.pdf",
				}
			)

	def test_administrator_without_assignment_cannot_mutate(self):
		"""§8 — Administrator has full technical read but no Budget business
		mutation without an assignment, same as any other user (AUTH-AC-018)."""
		self._as("Administrator")
		with self.assertRaises(ResponsibilityError):
			contracts.save_budget_version_draft(
				{
					"fiscal_year": self._fresh_fy(),
					"approval_reference": "X",
					"approval_date": add_days(nowdate(), -1),
					"authorised_total": 100,
					"approval_document": "/files/x.pdf",
				}
			)

	def test_unassigned_user_cannot_read_a_draft_version_by_direct_id(self):
		"""§17.2 coverage item 4 — direct-route access to a Budget Version
		excluded from the actor's register is denied, not just hidden from a
		listing (`kentender_scope_map`'s registered `has_permission` hook,
		not a Budget-local read-scope function)."""
		self._as(self.officer)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": self._fresh_fy(),
				"approval_reference": f"VIEW-{self.suffix}",
				"approval_date": add_days(nowdate(), -5),
				"authorised_total": 10_000_000,
				"approval_document": "/files/x.pdf",
			}
		)
		version = result["version"]["id"]
		self._track("Procurement Budget Version", version)
		self._track("Procurement Budget", result["budget"]["id"])

		outsider = f"bud.outsider.{self.suffix}@test.local"
		if not frappe.db.exists("User", outsider):
			frappe.get_doc(
				{"doctype": "User", "email": outsider, "first_name": "Outsider", "enabled": 1, "send_welcome_email": 0}
			).insert(ignore_permissions=True)
			self._track("User", outsider)
		self._as(outsider)
		# KT-STD-001 v1.2 §3A.2 (2026-09-06): the direct-route read resolves the
		# denial as data — the screen paints its Forbidden panel and Frappe
		# raises no "Not permitted" modal — and discloses nothing of the Draft.
		# The registered has_permission hook still denies a raw scoped read
		# (test_bud_chg_001_phase4_scope_map covers that layer).
		verdict = contracts.get_budget_version_draft(version)
		self.assertEqual(verdict.get("outcome"), "FORBIDDEN")
		self.assertNotIn("version", verdict)
		self.assertNotIn("budget", verdict)
		with self.assertRaises(frappe.PermissionError):
			frappe.has_permission("Procurement Budget Version", doc=version, user=outsider, throw=True)
