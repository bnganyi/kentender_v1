# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1, §5.5 rule 5 — Budget's funding position for Procurement Analytics
(`kentender_budget/services/analytics_provider.py`; plan Phase 2B, FU-ANL-04, ANL-M-11).

Class one builds one synthetic Budget world once (a Fiscal Year with an Active Version and a later Draft Version, three
Budget Lines owned by Digital Health, HRMD and "all departments", and nine reservations/commitments chosen so that a float
would show: 0.10 + 0.20) and reads it as every persona; the provider only reads. Class two builds a Budget through
Budget's own commands, reserves through its own `check_funding`/`reserve_funding`, and checks the provider against
Budget's own position (`_version_totals`).

The Head of User Department view is the owner decision of 5 October 2026 ("HOD has to have budget visibility"): the
department funding view through the Analytics aggregate only. A test below proves no Budget read rule moved for that role.

Run:
  bench --site kentender-test.local run-tests --app kentender_budget \\
    --module kentender_budget.tests.test_analytics_provider
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import frappe

from kentender_budget.services import analytics_provider as provider
from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import _FinanceTestBase
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE, _BudgetLifecycleTestBase
from kentender_core.services import analytics_contract as ac
from kentender_core.services import responsibility_administration as administration

AT = datetime(2027, 6, 18, 10, 0)
NS = "BUD_ANL_TESTS"
D = Decimal
NO_ACTIVE = {"funding": None, "reason": "no_active_budget"}
WHOLE_ROLES = {
	"officer": "Budget Officer", "approver": "Budget Approver", "fco": "Finance Confirmation Officer", "auditor": "Auditor",
	"ao": "Accounting Officer", "hopf": "Head of Procurement Function", "techop": "Technical Operator",
}
TABLES = (
	"Procurement Budget", "Procurement Budget Version", "Procurement Budget Line", "Procurement Budget Line Version", "Funding Reservation",
	"Procurement Commitment", "Budget Audit Event", "User Responsibility Assignment",
)


from kentender_budget.services.budget_service_principal import PRINCIPAL_REQUISITIONS, service_caller
from kentender_core.services.command_write_guard import fixture_insert, purge_doc

ANL_REQ = service_caller(PRINCIPAL_REQUISITIONS, reference="REQ-ANL-1")


class TestFundingProvider(_BudgetLifecycleTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.users: dict[str, str] = {}
		for label, role in WHOLE_ROLES.items():
			cls.users[label] = cls._person(label, role)
		cls.users["planner"] = cls._person("planner", "Procurement Planner")
		cls.users["nobody"] = cls._person("nobody", "")
		cls.users["author_a"] = cls._person("authora", "Departmental Author", cls.ou_dhp)
		cls.users["hod_a"] = cls._person("hoda", "Head of User Department", cls.ou_dhp)
		cls.users["hod_b"] = cls._person("hodb", "Head of User Department", cls.ou_hrmd)
		cls.users["hod_officer"] = cls._person("hodofficer", "Head of User Department", cls.ou_dhp)
		cls._grant(cls.users["hod_officer"], "Budget Officer", "")
		cls.users["former"] = cls._person("former", "Head of User Department", cls.ou_hrmd, revoke=True)
		cls.build_world()
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		suffix = cls.suffix
		super().tearDownClass()
		frappe.db.commit()  # the class cleanup rolls back anything not committed: the deletions must be
		left = {
			doctype: count for doctype, count in (
				(doctype, frappe.db.count(doctype, {"generated_reference": ("like", f"ANL-%{suffix}%")}))
				for doctype in ("Procurement Budget", "Procurement Budget Version", "Procurement Budget Line", "Procurement Budget Line Version", "Funding Reservation", "Procurement Commitment")
			) if count
		}
		left |= {name: count for name, count in (("User", frappe.db.count("User", {"name": ("like", f"bud.anl.%{suffix}%")})), ("Assignment", frappe.db.count("User Responsibility Assignment", {"fixture_namespace": NS}))) if count}
		if left:
			raise AssertionError(f"Budget Analytics test rows left behind: {left}")

	# ----- the people -----

	@classmethod
	def _person(cls, label: str, role: str, unit: str = "", *, revoke: bool = False) -> str:
		email = f"bud.anl.{label}.{cls.suffix}@test.local"
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": label, "enabled": 1, "send_welcome_email": 0}).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		cls._track("User", email)
		if role:
			assignment = cls._grant(email, role, unit)
			if revoke:
				administration.revoke(assignment, reason="Revoked inside the Analytics provider test.", actor="Administrator")
		return email

	@classmethod
	def _grant(cls, email: str, role: str, unit: str) -> str:
		outcome = administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS, actor="Administrator")
		cls._track("User Responsibility Assignment", outcome["assignment"])
		return outcome["assignment"]

	# ----- the world -----

	@classmethod
	def _insert(cls, doctype: str, **values) -> str:
		name = fixture_insert(frappe.get_doc({"doctype": doctype, **values})).name
		cls._track(doctype, name)
		return name

	@classmethod
	def _budget(cls, fiscal_year: str, label: str, versions: list[tuple[int, str]]) -> tuple[str, list[str]]:
		budget = cls._insert("Procurement Budget", generated_reference=f"ANL-BUD-{label}-{cls.suffix}", fiscal_year=fiscal_year, currency="KES", title=f"Ministry of Health procurement budget {label}")
		names = [
			cls._insert(
				"Procurement Budget Version", generated_reference=f"ANL-BUD-{label}-{cls.suffix}-V{number}", budget=budget, version_number=number, status=status,
				approval_reference=f"ANL-{label}", approval_date="2020-01-01", authorised_total=150_000_000, approval_document="/files/anl.pdf", currency="KES",
			)
			for number, status in versions
		]
		return budget, names

	@classmethod
	def _line_version(cls, version: str, line: str, title: str, owner: str, amount: str) -> str:
		return cls._insert(
			"Procurement Budget Line Version", generated_reference=f"ANL-LV-{cls.suffix}-{frappe.generate_hash(length=5)}", budget_version=version, budget_line=line,
			title=title, owner_org_unit=owner or None, funding_source=FUNDING_SOURCE, approved_amount=amount, currency="KES",
		)

	@classmethod
	def _reserve(cls, n: int, line: str, source: str, original: str, remaining: str, status: str = "Active") -> str:
		return cls._insert(
			"Funding Reservation", generated_reference=f"ANL-RES-{cls.suffix}-{n}", budget=cls.budget, budget_version_at_creation=cls.active, budget_line=line,
			status=status, plan_item="ANL-PI", plan_source_allocation=f"ANL-PSA-{cls.suffix}-{n}", source_organisation_unit=source,
			original_amount=original, remaining_amount=remaining, currency="KES", correlation_id=f"ANL-{n}",
		)

	@classmethod
	def _commit(cls, n: int, reservation: str, amount: str) -> None:
		cls._insert("Procurement Commitment", generated_reference=f"ANL-COM-{cls.suffix}-{n}", reservation=reservation, contract=f"ANL-CON-{cls.suffix}-{n}", status="Active", current_amount=amount, currency="KES")

	@classmethod
	def build_world(cls):
		frappe.set_user("Administrator")
		a, b = cls.ou_dhp, cls.ou_hrmd
		cls.budget, (cls.active, cls.draft) = cls._budget(cls.fy, "Y1", [(1, "Active"), (2, "Draft")])
		lines = {key: cls._insert("Procurement Budget Line", generated_reference=f"ANL-LINE-{key}-{cls.suffix}", budget=cls.budget) for key in ("ict", "office", "shared")}
		cls.lines = lines
		cls._line_version(cls.active, lines["ict"], "ICT equipment for Digital Health", a, "60000000")
		cls._line_version(cls.active, lines["office"], "Office equipment for Human Resources Management and Development", b, "30000000")
		cls._line_version(cls.active, lines["shared"], "Ministry-wide ICT infrastructure", "", "60000000")
		cls._line_version(cls.draft, lines["ict"], "ICT equipment for Digital Health", a, "99000000")  # a later Draft: never read
		for n, (line, source, original, remaining, status) in enumerate((
			("ict", a, "4000000.00", "4000000.00", "Active"),
			("office", b, "2500000.50", "2500000.50", "Active"),
			("shared", b, "8000000.00", "8000000.00", "Active"),
			("office", b, "3500000.00", "3500000.00", "Active"),
			("ict", a, "5000000.00", "0.00", "Converted"),
			("shared", a, "25000000.00", "20000000.00", "Partially Converted"),
			("office", b, "1000000.00", "0.00", "Released"),
			("ict", a, "0.10", "0.10", "Active"),
			("ict", a, "0.20", "0.20", "Active"),
		), 1):
			reservation = cls._reserve(n, lines[line], source, original, remaining, status)
			if n == 5:
				cls._commit(n, reservation, "5000000.00")
			if n == 6:
				cls._commit(n, reservation, "5000000.00")
		# a Fiscal Year whose Budget has no Active Version (Draft only; Superseded only) and one with no Budget at all
		cls.fy_draft = cls._fresh_fy()
		cls._budget(cls.fy_draft, "Y2", [(1, "Draft")])
		cls.fy_superseded = cls._fresh_fy()
		cls._budget(cls.fy_superseded, "Y3", [(1, "Superseded")])
		cls.fy_none = cls._fresh_fy()

	# ----- reads -----

	def read(self, who: str, *, fy: str = "", org_unit: str = "") -> dict:
		user = self.users.get(who, who)
		return provider.facts(user=user, kind=ac.FUNDING, at=AT, fiscal_year=fy or self.fy, org_unit=org_unit)

	def table(self, result: dict, key: str = "label") -> dict:
		return {line[key]: line for line in result["lines"]}

	def pairs(self, result: dict) -> list[tuple]:
		return sorted((r["source_org_unit"], r["line_owner_org_unit"], r["reserved"], r["committed"]) for r in result["reservations"])

	ICT, OFFICE, SHARED = "ICT equipment for Digital Health", "Office equipment for Human Resources Management and Development", "Ministry-wide ICT infrastructure"

	def expected_lines(self) -> dict:
		a, b = self.ou_dhp, self.ou_hrmd
		return {
			self.ICT: {"label": self.ICT, "owner_org_unit": a, "registered": D("60000000.00"), "reserved": D("4000000.30"), "committed": D("5000000.00"), "available": D("50999999.70")},
			self.OFFICE: {"label": self.OFFICE, "owner_org_unit": b, "registered": D("30000000.00"), "reserved": D("6000000.50"), "committed": D("0.00"), "available": D("23999999.50")},
			self.SHARED: {"label": self.SHARED, "owner_org_unit": "", "registered": D("60000000.00"), "reserved": D("28000000.00"), "committed": D("5000000.00"), "available": D("27000000.00")},
		}

	def expected_reservations(self) -> list[tuple]:
		a, b = self.ou_dhp, self.ou_hrmd
		return sorted([
			(a, a, D("4000000.00"), D("0.00")), (b, b, D("2500000.50"), D("0.00")), (b, "", D("8000000.00"), D("0.00")), (b, b, D("3500000.00"), D("0.00")),
			(a, a, D("0.00"), D("5000000.00")), (a, "", D("20000000.00"), D("5000000.00")), (a, a, D("0.10"), D("0.00")), (a, a, D("0.20"), D("0.00")),
		])  # the Released reservation holds nothing and is left out

	# ----- the whole-Budget view -----

	def test_the_whole_view_gives_each_line_exactly(self):
		result = self.read("officer")
		self.assertEqual((result["fiscal_year"], result["version"], result["as_at"], result["view"]), (self.fy, 1, AT, "whole"))
		self.assertEqual(result["budget_title"], frappe.db.get_value("Procurement Budget", self.budget, "title"))
		self.assertEqual(self.table(result), self.expected_lines())
		self.assertEqual([line["label"] for line in result["lines"]], sorted(self.expected_lines()))  # Budget's own title order

	def test_no_figure_is_a_float_and_cents_do_not_drift(self):
		result = self.read("officer")
		for line in result["lines"]:
			for key in ("registered", "reserved", "committed", "available"):
				self.assertIsInstance(line[key], Decimal, f"{line['label']} {key}")
		for reservation in result["reservations"]:
			self.assertIsInstance(reservation["reserved"], Decimal)
			self.assertIsInstance(reservation["committed"], Decimal)
		self.assertEqual(self.table(result)[self.ICT]["reserved"], D("4000000.30"))  # 4,000,000 + 0.10 + 0.20: a float sums to ...0.30000000000000004

	def test_reserved_committed_and_available_always_add_up_to_the_registered_allocation(self):
		result = self.read("officer")
		for line in result["lines"]:
			self.assertEqual(line["reserved"] + line["committed"] + line["available"], line["registered"], line["label"])
		totals = {key: sum(line[key] for line in result["lines"]) for key in ("registered", "reserved", "committed", "available")}
		self.assertEqual(totals, {"registered": D("150000000"), "reserved": D("38000000.80"), "committed": D("10000000"), "available": D("101999999.20")})
		self.assertEqual(totals["reserved"] + totals["committed"] + totals["available"], totals["registered"])

	def test_the_reservations_carry_their_source_department_and_their_lines_owner(self):
		result = self.read("officer")
		self.assertEqual(self.pairs(result), self.expected_reservations())
		# the reservations reconcile with the lines they sit on
		self.assertEqual(sum(r["reserved"] for r in result["reservations"]), sum(line["reserved"] for line in result["lines"]))
		self.assertEqual(sum(r["committed"] for r in result["reservations"]), sum(line["committed"] for line in result["lines"]))

	def test_only_the_active_version_is_read(self):
		self.assertEqual(self.table(self.read("officer"))[self.ICT]["registered"], D("60000000.00"))  # the Draft says 99,000,000

	def test_every_whole_budget_reader_gets_the_same_position(self):
		reference = self.read("officer")
		for who in ("approver", "fco", "auditor", "ao", "hopf", "techop", "Administrator"):
			self.assertEqual(self.read(who), reference, who)

	def test_the_accounting_officer_and_head_of_procurement_function_read_the_active_version_only(self):
		"""They read approved versions only (`budget_read_scope`); the position they get is the Active one, never the Draft."""
		for who in ("ao", "hopf"):
			frappe.set_user(self.users[who])
			self.assertNotIn(self.draft, frappe.get_list("Procurement Budget Version", pluck="name"), who)
			frappe.set_user("Administrator")
			result = self.read(who)
			self.assertEqual(result["version"], 1, who)
			self.assertEqual(self.table(result)[self.ICT]["registered"], D("60000000.00"), who)

	# ----- the department view -----

	def test_a_head_of_user_department_sees_their_own_line_in_full_and_only_their_own_reservations_on_the_shared_line(self):
		result = self.read("hod_b")
		a, b = self.ou_dhp, self.ou_hrmd
		self.assertEqual(result["view"], "department")
		self.assertEqual(self.table(result), {self.OFFICE: self.expected_lines()[self.OFFICE]})
		self.assertEqual(self.pairs(result), sorted([(b, b, D("2500000.50"), D("0.00")), (b, "", D("8000000.00"), D("0.00")), (b, b, D("3500000.00"), D("0.00"))]))
		self.assertNotIn(a, {r["source_org_unit"] for r in result["reservations"]})

	def test_the_shared_allocation_is_never_given_to_or_divided_for_a_department(self):
		for who in ("hod_a", "hod_b"):
			result = self.read(who)
			self.assertNotIn(self.SHARED, self.table(result), who)
			self.assertNotIn("", {line["owner_org_unit"] for line in result["lines"]}, who)
			for line in result["lines"]:
				self.assertEqual(line["registered"], self.expected_lines()[line["label"]]["registered"], who)  # whole, never a share
		# the shared line's own reservations by the department are all it gets of that line
		shared = [r for r in self.read("hod_a")["reservations"] if r["line_owner_org_unit"] == ""]
		self.assertEqual([(r["reserved"], r["committed"]) for r in shared], [(D("20000000.00"), D("5000000.00"))])

	def test_the_other_departments_head_sees_the_mirror_view(self):
		result = self.read("hod_a")
		self.assertEqual(self.table(result), {self.ICT: self.expected_lines()[self.ICT]})
		self.assertEqual(
			self.pairs(result),
			sorted([(self.ou_dhp, self.ou_dhp, D("4000000.00"), D("0.00")), (self.ou_dhp, self.ou_dhp, D("0.00"), D("5000000.00")), (self.ou_dhp, "", D("20000000.00"), D("5000000.00")),
				(self.ou_dhp, self.ou_dhp, D("0.10"), D("0.00")), (self.ou_dhp, self.ou_dhp, D("0.20"), D("0.00"))]),
		)

	def test_a_whole_budget_reader_who_names_a_department_gets_that_departments_view(self):
		for who in ("officer", "ao", "hopf", "Administrator"):
			chosen = self.read(who, org_unit=self.ou_hrmd)
			self.assertEqual(chosen["view"], "department", who)
			self.assertEqual((self.table(chosen), self.pairs(chosen)), (self.table(self.read("hod_b")), self.pairs(self.read("hod_b"))), who)

	def test_a_head_of_user_department_cannot_name_a_department_outside_their_scope(self):
		with self.assertRaises(frappe.PermissionError):
			self.read("hod_a", org_unit=self.ou_hrmd)
		self.assertEqual(self.read("hod_a", org_unit=self.ou_dhp)["view"], "department")

	def test_a_head_who_also_holds_a_budget_responsibility_gets_the_whole_view_until_they_name_a_department(self):
		self.assertEqual(self.read("hod_officer")["view"], "whole")
		self.assertEqual(self.table(self.read("hod_officer")), self.expected_lines())
		self.assertEqual(self.read("hod_officer", org_unit=self.ou_dhp)["view"], "department")

	def test_the_grant_is_the_analytics_view_only_and_no_budget_read_rule_moved(self):
		"""Owner decision 5 Oct 2026: no DocPerm, no change to Budget reads. The Head of User Department still opens no Budget record."""
		hod = self.users["hod_a"]
		frappe.set_user(hod)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Procurement Budget Version", pluck="name")
		self.assertFalse(frappe.has_permission("Procurement Budget", "read", self.budget, user=hod))
		self.assertIsNotNone(contracts.forbidden_verdict(hod))
		frappe.set_user("Administrator")
		self.assertEqual(self.read("hod_a")["view"], "department")  # and yet the department funding view is theirs

	# ----- who gets nothing -----

	def test_roles_outside_the_audience_get_nothing(self):
		for who in ("planner", "nobody", "author_a", "former"):
			user = self.users[who]
			self.assertEqual(provider.applies(user=user, at=AT), set(), who)
			with self.assertRaises(frappe.PermissionError):
				provider.facts(user=user, kind=ac.FUNDING, at=AT, fiscal_year=self.fy)
		for user in ("Guest", ""):
			self.assertEqual(provider.applies(user=user, at=AT), set(), user)

	def test_a_revoked_head_of_user_department_gets_nothing(self):
		self.assertEqual(frappe.db.get_value("User Responsibility Assignment", {"user": self.users["former"]}, "status"), "Revoked")
		with self.assertRaises(frappe.PermissionError):
			self.read("former")

	def test_applies_names_funding_for_the_audience(self):
		for who in list(WHOLE_ROLES) + ["hod_a", "hod_b", "hod_officer", "Administrator"]:
			self.assertEqual(provider.applies(user=self.users.get(who, who), at=AT), {ac.FUNDING}, who)

	# ----- a year with nothing to show -----

	def test_a_year_with_no_active_version_returns_the_defined_empty_answer(self):
		for fy in (self.fy_draft, self.fy_superseded, self.fy_none):
			for who in ("officer", "ao", "hopf", "auditor", "hod_a", "Administrator"):
				self.assertEqual(self.read(who, fy=fy), NO_ACTIVE, f"{who} {fy}")

	# ----- the call itself -----

	def test_a_missing_year_or_another_kind_is_refused(self):
		with self.assertRaises(ValueError):
			provider.facts(user=self.users["officer"], kind=ac.FUNDING, at=AT, fiscal_year="")
		with self.assertRaises(ValueError):
			provider.facts(user=self.users["officer"], kind=ac.TENDERS, at=AT, fiscal_year=self.fy)

	def test_a_read_creates_and_changes_nothing(self):
		def snapshot():
			return {t: frappe.db.count(t) for t in TABLES} | {"modified": frappe.db.get_value("Procurement Budget Version", self.active, "modified")}

		before = snapshot()
		for who in ("officer", "ao", "hod_a", "Administrator"):
			self.read(who)
			self.read(who, fy=self.fy_none)
		self.assertEqual(snapshot(), before)

	def test_the_provider_does_not_depend_on_the_session_user(self):
		frappe.set_user(self.users["nobody"])  # a session with no responsibility at all
		self.assertEqual(self.read("officer"), self._as_admin_read("officer"))
		self.assertEqual(provider.applies(user=self.users["officer"], at=AT), {ac.FUNDING})

	def _as_admin_read(self, who: str) -> dict:
		frappe.set_user("Administrator")
		return self.read(who)


class TestFundingMatchesBudgetsOwnPosition(_FinanceTestBase):
	"""A Budget built and reserved through Budget's own commands: the provider's Decimals equal Budget's own line positions."""

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for budget in getattr(cls, "_budgets", []):
			reservations = frappe.get_all("Funding Reservation", filters={"budget": budget}, pluck="name")
			for name in frappe.get_all("Procurement Commitment", filters={"reservation": ("in", reservations or ["-"])}, pluck="name"):
				purge_doc("Procurement Commitment", name)
			for name in reservations:
				purge_doc("Funding Reservation", name)
			frappe.flags.allow_budget_audit_purge = True
			try:
				for name in frappe.get_all("Budget Audit Event", filters={"budget": budget}, pluck="name"):
					purge_doc("Budget Audit Event", name)
			finally:
				frappe.flags.allow_budget_audit_purge = False
			versions = frappe.get_all("Procurement Budget Version", filters={"budget": budget}, pluck="name")
			for name in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": ("in", versions or ["-"])}, pluck="name"):
				purge_doc("Procurement Budget Line Version", name)
		suffix = cls.suffix
		super().tearDownClass()
		frappe.db.commit()
		left = {
			"reservations": frappe.db.count("Funding Reservation", {"plan_item": ("like", "ANL-%")}),
			"users": frappe.db.count("User", {"name": ("like", f"bud.%{suffix}@test.local")}),
			"budgets": frappe.db.count("Procurement Budget", {"generated_reference": ("like", f"%{suffix}%")}),
		}
		left = {name: count for name, count in left.items() if count}
		if left:
			raise AssertionError(f"Budget Analytics parity test rows left behind: {left}")

	def test_the_provider_equals_budgets_own_position_after_real_reservations(self):
		budget, version = self._create_active_baseline(dhi_amount=100_000_000, hwd_amount=60_000_000)
		type(self)._budgets = [budget]  # the class teardown removes it
		fy = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
		for line in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="budget_line"):
			self._track("Procurement Budget Line", line)
		dhi = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")
		hwd = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "HWD test line"}, "budget_line")
		self._as(self.finance_officer)
		token = check_reserve.check_funding(
			plan_item="ANL-PPI-1", plan_version="ANL-PLN-1", finance_task="ANL-FNT-1", source_set_hash="ANL-HASH-1",
			allocations=[
				{"budget_line": dhi, "amount": "72000000.25", "funding_source": FUNDING_SOURCE, "plan_source_allocation": "ANL-PSA-1A", "source_organisation_unit": self.ou_dhp},
				{"budget_line": hwd, "amount": "48000000", "funding_source": FUNDING_SOURCE, "plan_source_allocation": "ANL-PSA-1B", "source_organisation_unit": self.ou_hrmd},
			],
			correlation_id=frappe.generate_hash(length=12), caller=ANL_REQ
		)
		self.assertTrue(check_reserve.reserve_funding(token=token["token"], finance_task="ANL-FNT-1", source_set_hash="ANL-HASH-1", idempotency_key="ANL-IDEM-1", caller=ANL_REQ)["ok"])
		frappe.set_user("Administrator")

		result = provider.facts(user=self.officer, kind=ac.FUNDING, at=AT, fiscal_year=fy)
		own = {row["title"]: row["positions"] for row in contracts._version_totals(version)["lines"]}
		self.assertEqual(sorted(line["label"] for line in result["lines"]), ["DHI test line", "HWD test line"])
		for line in result["lines"]:
			position = own[line["label"]]
			for key, ours in (("approved", "registered"), ("reserved", "reserved"), ("committed", "committed"), ("available", "available")):
				self.assertAlmostEqual(float(line[ours]), position[key], places=2, msg=f"{line['label']} {ours}")
			self.assertEqual(line["reserved"] + line["committed"] + line["available"], line["registered"])
		self.assertEqual(self.pairs_by_source(result), {self.ou_dhp: (D("72000000.25"), D("0.00")), self.ou_hrmd: (D("48000000.00"), D("0.00"))})
		self.assertEqual({line["label"]: line["owner_org_unit"] for line in result["lines"]}, {"DHI test line": self.ou_dhp, "HWD test line": self.ou_hrmd})
		# the Budget Officer's own workspace and the Head of User Department's Analytics view of the same year
		hod = self._hod()
		department = provider.facts(user=hod, kind=ac.FUNDING, at=AT, fiscal_year=fy)
		self.assertEqual([line["label"] for line in department["lines"]], ["HWD test line"])
		self.assertEqual(self.pairs_by_source(department), {self.ou_hrmd: (D("48000000.00"), D("0.00"))})

	def pairs_by_source(self, result: dict) -> dict:
		return {r["source_org_unit"]: (r["reserved"], r["committed"]) for r in result["reservations"]}

	def _hod(self) -> str:
		email = f"bud.anl.realhod.{self.suffix}@test.local"
		user = frappe.get_doc({"doctype": "User", "email": email, "first_name": "realhod", "enabled": 1, "send_welcome_email": 0}).insert(ignore_permissions=True)
		user.add_roles("Desk User")
		self._track("User", email)
		outcome = administration.grant(user=email, business_role="Head of User Department", organisation_unit=self.ou_hrmd, fixture_namespace=NS, actor="Administrator")
		self._track("User Responsibility Assignment", outcome["assignment"])
		return email
