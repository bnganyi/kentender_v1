# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical site world — KT-STD-001 v1.3 §8 configuration and the
SEED-001 v1.0 module chain — cleared of everything else and reseeded
progressively, one module stage at a time.

	bench --site <site> execute kentender_core.seeds.canonical.run \\
		--kwargs '{"through": "budget"}'
	bench --site <site> execute kentender_core.seeds.canonical.dry_run
	bench --site <site> execute kentender_core.seeds.canonical.validate \\
		--kwargs '{"through": "budget"}'

Stages (``STAGES``) are cumulative: ``site`` is the KT-STD-001 §8 world
(site Procuring Entity, Organisation Units, ERPNext Fiscal Years, intake
windows, catalogues, the governed funding source, the regulatory reference,
UOMs, actors and their responsibility assignments), ``strategy`` the
STR-CHG-001 §14 plan, ``budget`` the BUD-CHG-001 §15.3 Active baseline.
Departmental Needs and Procurement Planning stages are appended here as
their own seeds are cut over to this orchestrator; until then their
canonical rows (namespaces below) are preserved by the clear, never rebuilt.

Procurement Requisitions (REQ-CHG-001 v1.6) is not a stage either — Needs
and Planning must land first — but it is the first live caller of Budget's
reservation contract: a Funding Reservation / Procurement Commitment
stamped `REQUISITIONS_NS` is canonical evidence of an authorised
Requisition, not disposable test residue, even though no Requisitions
stage exists yet to reseed it.

Every deletion is by explicit identity, namespace or fixture e-mail domain
(KT-STD-001 §8.6: seeds never repair, alias or import legacy records).
ERPNext-owned rows (``_Test Fiscal Year …``, Company, UOM) and the
pre-cutover legacy reference doctypes owned by AUTH-ADR-001's removal phase
(``Procuring Entity``, ``Financial Year``, ``PE Fiscal Year Context`` …) are
never touched (KT-STD-001 §10).
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds import site_setup

STAGES: tuple[str, ...] = ("site", "strategy", "budget")

# Namespaces whose rows are canonical and survive `reset`.
STRATEGY_NS = "str-chg-001-mvp1"
BUDGET_ACTOR_NS = "KENTENDER_MVP_V1"  # Budget's own actor assignments (pre-2026-09-06 sites)
NEEDS_NS = "KENTENDER_MVP_1_R1_NDS"
PLANNING_NS = "KENTENDER_MVP_1_R1_PLN"
REQUISITIONS_NS = "KENTENDER_MVP_1_R1_REQ"  # REQ-CHG-001 v1.6 — not a stage yet (see module docstring)
CANONICAL_NAMESPACES = frozenset({site_setup.FIXTURE_TAG, BUDGET_ACTOR_NS, STRATEGY_NS, NEEDS_NS, PLANNING_NS, REQUISITIONS_NS})

# KT-STD-001 §8.3 — the whole shared register, whatever stage is seeded.
REGISTER_LOCAL_PARTS: tuple[str, ...] = (
	"grace.wanjiku",
	"peter.kimani",
	"julia.njeri",
	"mercy.kilonzo",
	"samuel.otieno",
	"esther.muthoni",
	"alfred.ochieng",
	"naomi.chebet",
	"josphat.mwangi",
	"beatrice.kamau",
	"amina.hassan",
	"daniel.rotich",
	"charles.mutiso",
	"brian.wafula",
)
REGISTER_USERS = frozenset(f"{local}@moh.example.test" for local in REGISTER_LOCAL_PARTS)
# Only accounts on a fixture e-mail domain are ever deleted; a real person's
# account (any other domain) is never a seed's to remove.
FIXTURE_EMAIL_DOMAINS: tuple[str, ...] = ("@moh.example.test", "@example.test", "@test.local", "@moh.test", "@moe.test")

CANONICAL_BUDGET_CODES = ("MOH-BUD-2027-001",)

_LEGACY_DEMO_DOCTYPES = ("Procurement Handoff Card", "Procurement Journey")


# --------------------------------------------------------------------------
# Selection — what is *not* canonical
# --------------------------------------------------------------------------


def _fixture_email(email: str) -> bool:
	return any(email.endswith(domain) for domain in FIXTURE_EMAIL_DOMAINS)


def _site_fiscal_years() -> set[str]:
	from kentender_core.services import site_configuration as configuration

	return {configuration._fy_name(year) for year in site_setup.FISCAL_START_YEARS}


def _canonical_units() -> set[str]:
	"""The site root plus every unit a canonical row still points at, with
	its ancestors — resolved from data, never from the retired mnemonic codes."""
	keep: set[str] = set()
	root = frappe.db.get_value("Organisation Unit", {"parent_organisation_unit": ["in", ["", None]]}, "name")
	if root:
		keep.add(root)
	for doctype, field, filters in (
		("User Responsibility Assignment", "organisation_unit", {"user": ["in", list(REGISTER_USERS)]}),
		("Departmental Need", "organisation_unit", {"fixture_namespace": NEEDS_NS}),
		("Departmental Plan", "organisation_unit", {"fixture_namespace": PLANNING_NS}),
		("Procurement Budget Line Version", "owner_org_unit", {}),
	):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, field):
			continue
		for unit in frappe.get_all(doctype, filters=filters, pluck=field):
			while unit and unit not in keep:
				keep.add(unit)
				unit = frappe.db.get_value("Organisation Unit", unit, "parent_organisation_unit")
	return keep


def _fiscal_year_referenced(fy: str) -> bool:
	for doctype, field in (
		("Procurement Budget", "fiscal_year"),
		("Annual Plan", "fiscal_year"),
		("Departmental Plan", "fiscal_year"),
		("Departmental Need", "financial_year"),
		("Regulatory Reference", "fiscal_year"),
		("Performance Target", "fiscal_year"),
	):
		if frappe.db.exists("DocType", doctype) and frappe.db.has_column(doctype, field):
			if frappe.db.count(doctype, {field: fy}):
				return True
	return False


def collect_non_canonical() -> dict[str, list[str]]:
	"""Everything `reset` would remove, as `{doctype: [names]}` — read-only."""
	plan: dict[str, list[str]] = {}

	def add(doctype: str, names: list[str]) -> None:
		if names:
			plan.setdefault(doctype, []).extend(n for n in names if n not in plan.get(doctype, []))

	# Budget: any budget that is not the §15.3 baseline; on the baseline, any
	# version that is not Active, and any reservation — §15.4A's reservation
	# exists only once a Procurement Requisition module creates it.
	if frappe.db.exists("DocType", "Procurement Budget"):
		add(
			"Procurement Budget",
			frappe.get_all("Procurement Budget", filters={"generated_reference": ["not in", CANONICAL_BUDGET_CODES]}, pluck="name"),
		)
		canonical = frappe.get_all("Procurement Budget", filters={"generated_reference": ["in", CANONICAL_BUDGET_CODES]}, pluck="name")
		if canonical:
			add(
				"Procurement Budget Version",
				frappe.get_all("Procurement Budget Version", filters={"budget": ["in", canonical], "status": ["!=", "Active"]}, pluck="name"),
			)
			# A reservation/commitment stamped REQUISITIONS_NS is canonical
			# evidence of an authorised Requisition (REQ-CHG-001 v1.6), not test
			# residue; anything else on the canonical budget is disposable — the
			# same rule collect_non_canonical() already applies to Needs/Planning.
			stray_reservations = [
				r.name
				for r in frappe.get_all("Funding Reservation", filters={"budget": ["in", canonical]}, fields=["name", "fixture_namespace"])
				if (r.fixture_namespace or "") != REQUISITIONS_NS
			]
			add("Funding Reservation", stray_reservations)
			if stray_reservations and frappe.db.exists("DocType", "Procurement Commitment"):
				add(
					"Procurement Commitment",
					frappe.get_all("Procurement Commitment", filters={"reservation": ["in", stray_reservations]}, pluck="name"),
				)

	# Departmental Needs, Procurement Planning and the regulatory reference:
	# rows outside their canonical namespace. Filtered in Python — a SQL
	# `not in` never matches a NULL namespace, and unstamped test rows are
	# exactly the ones to catch.
	for doctype, ns in (
		("Departmental Need", NEEDS_NS),
		("Annual Plan", PLANNING_NS),
		("Departmental Plan", PLANNING_NS),
		("Regulatory Reference", site_setup.FIXTURE_TAG),
	):
		if frappe.db.exists("DocType", doctype):
			add(doctype, [r.name for r in frappe.get_all(doctype, fields=["name", "fixture_namespace"]) if (r.fixture_namespace or "") != ns])

	for doctype in _LEGACY_DEMO_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			add(doctype, frappe.get_all(doctype, pluck="name"))

	# Assignments outside the canonical namespaces, or on a non-register fixture user.
	uras = frappe.get_all("User Responsibility Assignment", fields=["name", "user", "fixture_namespace"])
	add(
		"User Responsibility Assignment",
		[
			r.name
			for r in uras
			if (r.fixture_namespace or "") not in CANONICAL_NAMESPACES or (r.user not in REGISTER_USERS and _fixture_email(r.user))
		],
	)
	add(
		"User",
		[
			u
			# Any user type: Frappe stores a desk-role-less account as a Website
			# User, and fixture personas are created both ways.
			for u in frappe.get_all("User", filters={"name": ["not in", ["Administrator", "Guest"]]}, pluck="name")
			if _fixture_email(u) and u not in REGISTER_USERS
		],
	)

	keep_units = _canonical_units()
	add("Organisation Unit", [u for u in frappe.get_all("Organisation Unit", pluck="name") if u not in keep_units])

	site_fys = _site_fiscal_years()
	add(
		"Fiscal Year",
		[
			fy
			for fy in frappe.get_all("Fiscal Year", filters={"name": ["not like", "_Test%"]}, pluck="name")
			if fy not in site_fys and not _fiscal_year_referenced(fy)
		],
	)
	return plan


# --------------------------------------------------------------------------
# Clearing
# --------------------------------------------------------------------------


def _delete_docs(doctype: str, names: list[str], deleted: dict[str, int], **flags) -> None:
	for name in names:
		if not frappe.db.exists(doctype, name):
			continue
		doc = frappe.get_doc(doctype, name)
		for key, value in flags.items():
			doc.flags[key] = value
		doc.delete(ignore_permissions=True, force=True)
		deleted[doctype] = deleted.get(doctype, 0) + 1


def _delete_need(need: str, deleted: dict[str, int]) -> None:
	# Same mechanism as departmental_needs.seeds.playwright_ui_fixtures.
	# purge_fixture_needs: review tasks and decisions are retained
	# permanently through the document API, so fixture purges go raw.
	for doctype in (
		"Departmental Need Event",
		"Need Planning Usage Projection",
		"Departmental Need Decision",
		"Departmental Need Review Task",
		"Need Withdrawal Request",
		"Departmental Need Version",
	):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, "departmental_need"):
			continue
		names = frappe.get_all(doctype, filters={"departmental_need": need}, pluck="name")
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
			deleted[doctype] = deleted.get(doctype, 0) + len(names)
	frappe.db.delete("Notification Log", {"document_type": "Departmental Need", "document_name": need})
	frappe.db.delete("Departmental Need", {"name": need})
	deleted["Departmental Need"] = deleted.get("Departmental Need", 0) + 1


def _delete_user(user: str, deleted: dict[str, int]) -> None:
	for doctype, field in (
		("User Responsibility Assignment", "user"),
		("User Scope Assignment", "user"),
		("User Permission", "user"),
		("Notification Log", "for_user"),
		("Contact", "user"),
	):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, field):
			continue
		for name in frappe.get_all(doctype, filters={field: user}, pluck="name"):
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			deleted[doctype] = deleted.get(doctype, 0) + 1
	frappe.delete_doc("User", user, force=1, ignore_permissions=True)
	deleted["User"] = deleted.get("User", 0) + 1


def clear_non_canonical(*, plan: dict[str, list[str]] | None = None) -> dict[str, int]:
	"""Apply `collect_non_canonical()` in dependency order. No commit."""
	from kentender_core.seeds.kentender_mvp_v1.clear import _delete_budget_graph

	plan = plan if plan is not None else collect_non_canonical()
	deleted: dict[str, int] = {}

	# Downstream first: Planning and Needs rows may reference Budget lines and units.
	if plan.get("Annual Plan") or plan.get("Departmental Plan"):
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import clear_planning_fixture_rows

		for doctype, count in clear_planning_fixture_rows(include_canonical=False, include_playwright=True).items():
			if count:
				deleted[doctype] = deleted.get(doctype, 0) + count
		# Whatever the module's own clear did not recognise goes raw, children first.
		for doctype in ("Departmental Plan", "Annual Plan"):
			for name in plan.get(doctype, []):
				if frappe.db.exists(doctype, name):
					frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
					deleted[doctype] = deleted.get(doctype, 0) + 1
	for need in plan.get("Departmental Need", []):
		if frappe.db.exists("Departmental Need", need):
			_delete_need(need, deleted)

	for budget in plan.get("Procurement Budget", []):
		_delete_budget_graph(budget, deleted)
	if plan.get("Funding Reservation"):
		reservations = plan["Funding Reservation"]
		if frappe.db.exists("DocType", "Procurement Commitment"):
			_delete_docs(
				"Procurement Commitment",
				frappe.get_all("Procurement Commitment", filters={"reservation": ["in", reservations]}, pluck="name"),
				deleted,
			)
		frappe.flags.allow_budget_audit_purge = True
		try:
			_delete_docs(
				"Budget Audit Event",
				frappe.get_all("Budget Audit Event", filters={"reservation": ["in", reservations]}, pluck="name"),
				deleted,
			)
		finally:
			frappe.flags.allow_budget_audit_purge = False
		_delete_docs("Funding Reservation", reservations, deleted)
	for version in plan.get("Procurement Budget Version", []):
		if not frappe.db.exists("Procurement Budget Version", version):
			continue
		_delete_docs(
			"Procurement Budget Line Version",
			frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="name"),
			deleted,
		)
		frappe.flags.allow_budget_audit_purge = True
		try:
			_delete_docs(
				"Budget Audit Event", frappe.get_all("Budget Audit Event", filters={"budget_version": version}, pluck="name"), deleted
			)
		finally:
			frappe.flags.allow_budget_audit_purge = False
		_delete_docs("Procurement Budget Version", [version], deleted)
	# Attachments whose owning document is gone.
	for row in frappe.get_all(
		"File",
		filters={"attached_to_doctype": ["in", ["Procurement Budget Version", "Procurement Budget"]]},
		fields=["name", "attached_to_doctype", "attached_to_name"],
	):
		if not frappe.db.exists(row.attached_to_doctype, row.attached_to_name):
			frappe.delete_doc("File", row.name, force=1, ignore_permissions=True)
			deleted["File"] = deleted.get("File", 0) + 1

	# The document's own fixture-purge switch (regulatory_reference.on_trash).
	_delete_docs("Regulatory Reference", plan.get("Regulatory Reference", []), deleted, kt_fixture_purge=True)

	for doctype in _LEGACY_DEMO_DOCTYPES:
		_delete_docs(doctype, plan.get(doctype, []), deleted)

	_delete_docs("User Responsibility Assignment", plan.get("User Responsibility Assignment", []), deleted)
	for user in plan.get("User", []):
		if frappe.db.exists("User", user):
			_delete_user(user, deleted)

	# Units children-first: a pass deletes the leaves, the next their parents.
	pending = [u for u in plan.get("Organisation Unit", []) if frappe.db.exists("Organisation Unit", u)]
	for _ in range(8):
		if not pending:
			break
		remaining = []
		for unit in pending:
			if frappe.db.count("Organisation Unit", {"parent_organisation_unit": unit}):
				remaining.append(unit)
				continue
			frappe.delete_doc("Organisation Unit", unit, force=1, ignore_permissions=True)
			deleted["Organisation Unit"] = deleted.get("Organisation Unit", 0) + 1
		pending = remaining

	_delete_docs("Fiscal Year", [fy for fy in plan.get("Fiscal Year", []) if not _fiscal_year_referenced(fy)], deleted)
	return deleted


def clear_canonical_modules() -> dict[str, Any]:
	"""`rebuild`: drop the canonical module rows too (downstream first —
	Planning and Needs reference Budget lines), leaving the §8 site world."""
	out: dict[str, Any] = {}
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import clear_planning_fixture_rows

	out["planning"] = clear_planning_fixture_rows(include_canonical=True, include_playwright=True)
	from kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures import purge_fixture_needs

	out["needs"] = purge_fixture_needs(namespace=NEEDS_NS, commit=False)
	from kentender_core.seeds.kentender_mvp_v1.clear import clear_kentender_mvp_v1_budget

	out["budget"] = clear_kentender_mvp_v1_budget(include_canonical=True, include_playwright=True)
	from kentender_strategy.seeds.kentender_mvp_v1_strategy import clear_kentender_mvp_v1_strategy

	out["strategy"] = clear_kentender_mvp_v1_strategy(include_canonical=True, include_playwright=True)
	return out


# --------------------------------------------------------------------------
# Seeding
# --------------------------------------------------------------------------


def _stage_index(through: str) -> int:
	if through not in STAGES:
		frappe.throw(f"Unknown seed stage {through!r}; expected one of {', '.join(STAGES)}")
	return STAGES.index(through)


def seed(*, through: str = STAGES[-1]) -> dict[str, Any]:
	"""Reseed the canonical world up to and including `through`. No commit."""
	last = _stage_index(through)
	report: dict[str, Any] = {"site": site_setup.run(commit=False)}
	if last >= STAGES.index("strategy"):
		from kentender_strategy.seeds.kentender_mvp_v1_strategy import upsert_kentender_mvp_v1_strategy

		report["strategy"] = upsert_kentender_mvp_v1_strategy()
	if last >= STAGES.index("budget"):
		from kentender_budget.seeds.kentender_mvp_v1_portfolio import upsert_kentender_mvp_v1_portfolio

		# The §15.3 Active baseline only — §15.5/§15.6 profiles are created and
		# removed by the tests that need them (§15.7).
		report["budget"] = upsert_kentender_mvp_v1_portfolio(include_test_edges=False, commit=False)
	return report


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def validate(*, through: str = STAGES[-1]) -> dict[str, Any]:
	"""Assert the canonical facts for every stage up to `through`; raise on
	the first stage that fails, listing every failed check."""
	last = _stage_index(through)
	failures: list[str] = []

	def check(ok: bool, message: str) -> None:
		if not ok:
			failures.append(message)

	pe = frappe.db.get_single_value("Site Procuring Entity", "pe_code")
	check(pe == site_setup.SITE["pe_code"], f"site Procuring Entity is {pe!r}, expected {site_setup.SITE['pe_code']!r}")
	units = frappe.get_all("Organisation Unit", fields=["name", "unit_name", "parent_organisation_unit"])
	check(sum(1 for u in units if not u.parent_organisation_unit) == 1, "exactly one root Organisation Unit")
	names = [u.unit_name for u in units]
	for name, _parent in site_setup.UNITS:
		check(names.count(name) == 1, f"exactly one Organisation Unit named {name!r} (found {names.count(name)})")
	check(len(units) == 1 + len(site_setup.UNITS), f"{1 + len(site_setup.UNITS)} Organisation Units, found {len(units)}")
	for fy in _site_fiscal_years():
		check(bool(frappe.db.exists("Fiscal Year", fy)), f"Fiscal Year {fy}")
	extra_fys = [fy for fy in frappe.get_all("Fiscal Year", filters={"name": ["not like", "_Test%"]}, pluck="name") if fy not in _site_fiscal_years()]
	check(not extra_fys, f"no non-canonical Fiscal Years, found {extra_fys}")
	for label in site_setup.FUNDING_SOURCES:
		check(frappe.db.get_value("Funding Source", label, "record_status") == "Available", f"Funding Source {label!r} Available")
	seeded_users = {f"{local}@moh.example.test" for local, _ in site_setup.ACTORS}
	for email in seeded_users:
		check(bool(frappe.db.exists("User", email)), f"user {email}")
	strays = [
		u
		for u in frappe.get_all("User", filters={"name": ["not in", ["Administrator", "Guest"]]}, pluck="name")
		if _fixture_email(u) and u not in REGISTER_USERS
	]
	check(not strays, f"no fixture-domain users outside the register, found {strays}")
	for local, role, _unit, _kwargs in site_setup.ASSIGNMENTS:
		check(
			bool(
				frappe.db.exists(
					"User Responsibility Assignment", {"user": f"{local}@moh.example.test", "business_role": role, "status": ["in", ["Enabled", "Scheduled"]]}
				)
			)
			or bool(frappe.db.exists("User Responsibility Assignment", {"user": f"{local}@moh.example.test", "business_role": role})),
			f"assignment {local}: {role}",
		)

	if last >= STAGES.index("strategy"):
		plans = frappe.get_all("Strategic Plan", filters={"fixture_namespace": STRATEGY_NS}, pluck="name")
		check(len(plans) == 1, f"one canonical Strategic Plan, found {len(plans)}")
		if plans:
			active = frappe.db.count("Strategic Plan Version", {"plan_id": plans[0], "status": "Active"})
			check(active == 1, f"one Active Strategic Plan Version, found {active}")

	if last >= STAGES.index("budget"):
		budgets = frappe.get_all("Procurement Budget", fields=["name", "generated_reference", "fiscal_year"])
		check([b.generated_reference for b in budgets] == list(CANONICAL_BUDGET_CODES), f"only {CANONICAL_BUDGET_CODES}, found {[b.generated_reference for b in budgets]}")
		if budgets:
			budget = budgets[0]
			check(budget.fiscal_year == "2027-2028", f"budget fiscal year {budget.fiscal_year}")
			versions = frappe.get_all("Procurement Budget Version", filters={"budget": budget.name}, fields=["generated_reference", "status"])
			check([(v.generated_reference, v.status) for v in versions] == [("MOH-BUD-2027-001-V1", "Active")], f"one Active V1, found {[(v.generated_reference, v.status) for v in versions]}")
			lines = {
				frappe.db.get_value("Procurement Budget Line", lv.budget_line, "generated_reference"): (lv.title, lv.approved_amount, lv.owner_org_unit)
				for lv in frappe.get_all(
					"Procurement Budget Line Version",
					filters={"budget_version": ["in", [v.name for v in frappe.get_all("Procurement Budget Version", filters={"budget": budget.name}, fields=["name"])]]},
					fields=["budget_line", "title", "approved_amount", "owner_org_unit"],
				)
			}
			check(lines.get("MOH-BL-DHI-2027", ("", 0, ""))[1] == 100_000_000, "MOH-BL-DHI-2027 approved 100,000,000")
			check(lines.get("MOH-BL-HWD-2027", ("", 0, ""))[1] == 60_000_000, "MOH-BL-HWD-2027 approved 60,000,000")
			check(not lines.get("MOH-BL-HWD-2027", ("", 0, "x"))[2], "MOH-BL-HWD-2027 is Entity-wide (SEED-001 §3.5)")
			# §15.4: reservation begins at Requisition. REQ-CHG-001 v1.6 is the
			# first live caller and is not yet a canonical stage, so a reservation
			# stamped REQUISITIONS_NS is expected canonical evidence, not a stray;
			# anything else is a defect (a caller reserving outside that namespace).
			stray_reservations = [
				r.name
				for r in frappe.get_all("Funding Reservation", fields=["name", "fixture_namespace"])
				if (r.fixture_namespace or "") != REQUISITIONS_NS
			]
			check(not stray_reservations, f"no Funding Reservation outside {REQUISITIONS_NS!r}, found {stray_reservations}")
			stray_commitments = [
				r.name
				for r in frappe.get_all("Procurement Commitment", fields=["name", "fixture_namespace"])
				if (r.fixture_namespace or "") != REQUISITIONS_NS
			]
			check(not stray_commitments, f"no Procurement Commitment outside {REQUISITIONS_NS!r}, found {stray_commitments}")

	report = {"ok": not failures, "through": through, "failures": failures}
	if failures:
		frappe.throw("Canonical seed validation failed:\n- " + "\n- ".join(failures))
	return report


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def _assert_allowed(force: bool) -> None:
	if force or frappe.conf.get("developer_mode") or frappe.conf.get("allow_canonical_seed"):
		return
	frappe.throw("Canonical seed refused: enable developer_mode or allow_canonical_seed in site_config, or pass force=True.")


def dry_run() -> dict[str, Any]:
	"""What `run(reset=True)` would remove — deletes nothing."""
	frappe.only_for(("System Manager", "Administrator"))
	plan = collect_non_canonical()
	summary = {doctype: len(names) for doctype, names in plan.items()}
	print("Would remove:", summary or "nothing")
	for doctype, names in plan.items():
		print(f"  {doctype}: {', '.join(names[:12])}{' …' if len(names) > 12 else ''}")
	return {"ok": True, "would_remove": plan, "summary": summary}


def run(
	*,
	through: str = STAGES[-1],
	reset: bool = True,
	rebuild: bool = False,
	validate: bool = True,
	force: bool = False,
	commit: bool = True,
) -> dict[str, Any]:
	"""Clear everything non-canonical (``reset``), optionally the canonical
	module rows too (``rebuild``), reseed up to ``through`` and validate.
	One transaction: any failure rolls the whole run back."""
	frappe.only_for(("System Manager", "Administrator"))
	_assert_allowed(force)
	_stage_index(through)
	frappe.set_user("Administrator")
	result: dict[str, Any] = {"ok": True, "through": through}
	try:
		if rebuild:
			result["rebuild"] = clear_canonical_modules()
		if reset:
			result["removed"] = clear_non_canonical()
		result["seeded"] = seed(through=through)
		if validate:
			result["validate"] = globals()["validate"](through=through)
		if commit:
			frappe.db.commit()
		print(
			"CANONICAL_SEED_OK through=%s removed=%s" % (through, result.get("removed") or {}),
		)
		return result
	except Exception:
		frappe.db.rollback()
		raise
