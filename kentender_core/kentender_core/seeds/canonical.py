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
STR-CHG-001 §14 plan, ``budget`` the BUD-CHG-001 §15.3 Active baseline,
``needs`` the NDS-CHG-001 §14.3 default Needs, ``planning`` the
PLN-CHG-001 §14 integrated baseline, ``requisitions`` the REQ-CHG-001 v1.11
§16 Authorised Requisition on the one eligible combined Plan Item,
``tenders`` the TPR-CHG-001 v0.12 §13.3 primary Tender lifecycle on that
Requisition's handoff, ``bid_submission`` the same Tender built with Afya
Digital Supplies Limited's bid interleaved (BDS-CHG-001 v0.8), ``bid_opening``
its opening (BOP-CHG-001 v0.10), ``bid_evaluation`` its evaluation, to the
report sent to Charles Mutiso (EVL-CHG-001 v0.4), and ``award`` its award, to
the package Contracting received (AWD-CHG-001 v0.4). The last four use the
simulated trust, custody and delivery services, so they run only on a test
site. Each stage calls the owning
module's own canonical-shaped seed function directly — never the legacy
multi-PE `kentender_core.seeds.kentender_mvp_v1.orchestrator` — so seeding
through any stage never creates `PE-CGKIS` or any second Procuring Entity.

A Funding Reservation / Procurement Commitment stamped `REQUISITIONS_NS` is
canonical evidence of an authorised Requisition, not disposable test
residue, whether or not `through="requisitions"` was actually requested on
a given run.

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

from kentender_core.seeds import calendar, site_setup

#: Two-year seed world (owner, 4 Oct 2026: "Decisions for the owner:
#: recommendations accepted"; plan D1–D7). The world is read as at
#: `calendar.AS_AT` and carries two financial years, each moved by its own
#: control:
#:
#: - `current` — Year 1, FY 2026/27, the year being carried out. Its budget,
#:   Needs, departmental plans and Active, locked Annual Plan are always built
#:   (`annual_plan`); each later stage adds that step of the executed chain.
#: - `next_year` — Year 2, FY 2027/28, the year being prepared: nothing done
#:   (`none`), then its budget, its Needs, its accepted departmental plans,
#:   and at most its approved, Active Annual Plan.
#:
#: The site, its people and the Strategy are shared and always built.
CURRENT_STAGES: tuple[str, ...] = ("annual_plan", "requisitions", "tenders", "bid_submission", "bid_opening", "bid_evaluation", "award")
NEXT_STAGES: tuple[str, ...] = ("none", "budget", "needs", "departmental_plans", "annual_plan")
#: The plain seed's world (plan D6): Home and Analytics need all of it.
DEFAULT_CURRENT, DEFAULT_NEXT = CURRENT_STAGES[-1], NEXT_STAGES[-1]

#: The single-year ladder `THROUGH` named until 4 Oct 2026, kept one release
#: as an alias (`resolve_years`).
STAGES: tuple[str, ...] = ("site", "strategy", "budget", "needs", "planning", "requisitions", "tenders", "bid_submission", "bid_opening", "bid_evaluation", "award")
_THROUGH_TO_NEXT = {"site": "none", "strategy": "none", "budget": "budget", "needs": "needs", "planning": "annual_plan"}


def resolve_years(*, current: str | None = None, next_year: str | None = None, through: str | None = None) -> tuple[str, str]:
	"""The (current, next_year) pair a call asks for. `through` (the retired
	single-year ladder) maps onto the two: a stage up to `planning` moves only
	the prepared year (the executed year always has its Active plan); a later
	stage moves the executed year with the prepared year complete."""
	if through:
		if through not in STAGES:
			frappe.throw(f"Unknown seed stage {through!r}; expected one of {', '.join(STAGES)}")
		print(f"NOTICE: THROUGH={through} is retired; use CURRENT= and NEXT= (two-year seed world). Mapping it for this release.")
		if through in _THROUGH_TO_NEXT:
			current, next_year = current or CURRENT_STAGES[0], next_year or _THROUGH_TO_NEXT[through]
		else:
			current, next_year = current or through, next_year or DEFAULT_NEXT
	current, next_year = current or DEFAULT_CURRENT, next_year or DEFAULT_NEXT
	if current not in CURRENT_STAGES:
		frappe.throw(f"Unknown CURRENT={current!r} for {calendar.YEAR1.label}; expected one of {', '.join(CURRENT_STAGES)}")
	if next_year not in NEXT_STAGES:
		frappe.throw(f"Unknown NEXT={next_year!r} for {calendar.YEAR2.label} (it never goes past an approved Annual Plan); expected one of {', '.join(NEXT_STAGES)}")
	return current, next_year


def _reaches(stage: str, *, current: str) -> bool:
	return CURRENT_STAGES.index(current) >= CURRENT_STAGES.index(stage)


def _next_reaches(stage: str, *, next_year: str) -> bool:
	return NEXT_STAGES.index(next_year) >= NEXT_STAGES.index(stage)

# Namespaces whose rows are canonical and survive `reset`.
STRATEGY_NS = "str-chg-001-mvp1"
BUDGET_ACTOR_NS = "KENTENDER_MVP_V1"  # Budget's own actor assignments (pre-2026-09-06 sites)
NEEDS_NS = "KENTENDER_MVP_1_R1_NDS"
PLANNING_NS = "KENTENDER_MVP_1_R1_PLN"
REQUISITIONS_NS = "KENTENDER_MVP_1_R1_REQ"  # not stamped on Requisitions' own rows (D5 predates the column) — see clear_non_canonical
TENDERS_NS = "KENTENDER_MVP_1_R1_TND"
BID_OPENING_NS = "KENTENDER_MVP_1_R1_BOP"  # BOP-CHG-001 v0.10 plan D14
BID_EVALUATION_NS = "KENTENDER_MVP_1_R1_EVL"  # EVL-CHG-001 v0.4 plan D18
BIDS_NS = "KENTENDER_MVP_1_R1_BDS"  # BDS-CHG-001 v0.8 plan D19: the canonical bids and supplier accounts
CANONICAL_NAMESPACES = frozenset(
	{site_setup.FIXTURE_TAG, BUDGET_ACTOR_NS, STRATEGY_NS, NEEDS_NS, PLANNING_NS, REQUISITIONS_NS, TENDERS_NS, BID_OPENING_NS, BID_EVALUATION_NS}
)

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
	"daniel.otieno",  # KT-STD-001 v1.11 §8.3 — technical operator
	"nadia.kamau",  # KT-STD-001 v1.12 §8.3 — release operator
	"charles.mutiso",
	"brian.wafula",
	"grace.wambui",  # EVL-CHG-001 v0.4 plan D17 — the evaluation committee and its support holder
	"peter.mugo",
	"ruth.achieng",
	"esther.njeri",
	# TPR-CHG-001 v0.8 §13.1 (plan D8, D8′ in v0.12) — the bidder-facing
	# service identity that receives supplier clarifications (the account
	# name predates v0.12's clarifications and is kept: Tenders FU-32); a
	# canonical service account, never a person, but on the same fixture
	# e-mail domain as every other seeded actor and so registered the same
	# way.
	"tender.inquiry.producer",
)
REGISTER_USERS = frozenset(f"{local}@moh.example.test" for local in REGISTER_LOCAL_PARTS)
# Only accounts on a fixture e-mail domain are ever deleted; a real person's
# account (any other domain) is never a seed's to remove. Includes the
# RFC 2606 reserved placeholder domains (example.com/.org/.net) since stray
# manually-created test accounts land there, not just the project's own
# `.test`/`.local` fixture domains.
FIXTURE_EMAIL_DOMAINS: tuple[str, ...] = (
	"@moh.example.test",
	"@example.test",
	"@test.local",
	"@moh.test",
	"@moe.test",
	"@example.com",
	"@example.org",
	"@example.net",
)

# The canonical budget is found by content (`kentender_mvp_v1_portfolio.
# canonical_budget`): its references are the generated ones (Project Owner
# decision, 26 Sep 2026), which a rebuilt world numbers MOH-BUD-2027-001 again.
CANONICAL_BUDGET_CODES = ("MOH-BUD-2027-001",)

_LEGACY_DEMO_DOCTYPES = ("Procurement Handoff Card", "Procurement Journey")


def _playwright_cleanup_allowed() -> bool:
	"""Requisitions' and Tenders' own playwright fixture
	modules refuse to touch their rows unless developer_mode/allow_tests is
	set (or a test is already running) — a guard this orchestrator's own
	`force` cannot bypass, since it belongs to a sibling module. Unlike
	Planning/Needs, their calls here are unconditional (no fixture_namespace
	column to gate on), so on a site without that flag this must be skipped
	rather than fail the whole run — exactly how Planning/Needs behave when
	there is nothing of theirs to clean either."""
	return bool(frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"))


# --------------------------------------------------------------------------
# Selection — what is *not* canonical
# --------------------------------------------------------------------------


def _fixture_email(email: str) -> bool:
	return any(email.endswith(domain) for domain in FIXTURE_EMAIL_DOMAINS)


def _site_fiscal_years() -> set[str]:
	from kentender_core.services import site_configuration as configuration

	return {configuration._fy_name(year) for year in site_setup.FISCAL_START_YEARS}


def _in_force_now(row) -> bool:
	"""Same window test `authorization._within_period` applies at resolution
	time: a blank bound is open, and both ends are inclusive."""
	from frappe.utils import get_datetime, now_datetime

	now = now_datetime()
	starts = row.get("effective_from")
	ends = row.get("effective_to")
	if starts and get_datetime(starts) > now:
		return False
	if ends and get_datetime(ends) < now:
		return False
	return True


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


def _kentender_doctypes(**filters) -> list[str]:
	modules = [module for app in frappe.get_installed_apps() if app.startswith("kentender") for module in frappe.get_module_list(app)]
	return frappe.get_all("DocType", filters={"module": ("in", modules), "is_virtual": 0, **filters}, pluck="name")


def _orphaned_child_rows() -> dict[str, list[str]]:
	"""Child-table rows of KenTender doctypes whose parent record no longer
	exists. A module clean-up that deletes a record raw leaves its child
	rows behind, and no screen can ever reach them again (found 26 Sep
	2026: about 50,000 on the dev site, from Requisitions, Tenders and the
	Regulatory Reference)."""
	out: dict[str, list[str]] = {}
	for child in _kentender_doctypes(istable=1):
		if not frappe.db.table_exists(child):
			continue
		for parenttype in frappe.db.sql_list(f"select distinct parenttype from `tab{child}`"):
			if not parenttype or not frappe.db.exists("DocType", {"name": parenttype, "issingle": 0, "is_virtual": 0}):
				continue
			names = frappe.db.sql_list(
				f"select c.name from `tab{child}` c left join `tab{parenttype}` p on p.name = c.parent "
				"where c.parenttype = %s and p.name is null",
				parenttype,
			)
			if names:
				out.setdefault(child, []).extend(names)
	return out


#: Planning's projections onto Needs, written unstamped (see below). The usage
#: projection is ordered on its event time, so one a rebuild's reset left at
#: the real clock outranks the rebuilt plan's activation under the frozen
#: fixture clock (found 5 Oct 2026: the rebuilt FY 2026/27 Needs read Not
#: included); it goes with its Need like the others.
_NEED_PROJECTIONS = ("Need Planning Disposition Projection", "Need Planning Intake Projection", "Need Planning Usage Projection")


def _projections_without_a_need(doctype: str = "Need Planning Disposition Projection") -> list[str]:
	"""Planning's projection rows for Needs that no longer exist (found
	26 Sep 2026: 11 disposition rows on the dev site; Planning writes them
	unstamped, so no namespace purge reaches them). The intake position
	(owner decision 26 Sep 2026) is written the same way."""
	if not frappe.db.table_exists(doctype):
		return []
	return frappe.db.sql_list(
		f"select p.name from `tab{doctype}` p "
		"left join `tabDepartmental Need` n on n.name = p.departmental_need where n.name is null"
	)


def _orphaned_attachments() -> list[str]:
	"""Files attached to a named KenTender record that no longer exists
	(found 26 Sep 2026: 1,734 from deleted Tender documents)."""
	doctypes = set(_kentender_doctypes(istable=0, issingle=0))
	names: list[str] = []
	for doctype in frappe.db.sql_list("select distinct attached_to_doctype from `tabFile` where ifnull(attached_to_doctype, '') != ''"):
		if doctype in doctypes:
			names += frappe.db.sql_list(
				f"select f.name from `tabFile` f left join `tab{doctype}` d on d.name = f.attached_to_name "
				"where f.attached_to_doctype = %s and ifnull(f.attached_to_name, '') != '' and d.name is null",
				doctype,
			)
	return names


def _undeclared_site_assignments() -> list[str]:
	"""Grants stamped with the site stage's namespace that `site_setup.ASSIGNMENTS`
	no longer declares (found 1 Oct 2026: KT-STD-001 v1.13 dropped the
	Evaluation committee's Departmental Author grants). The namespace marks
	them canonical, so nothing else would ever remove them."""
	declared: set[tuple[str, str, str | None]] = set()
	for local, role, unit_name, _kwargs in site_setup.ASSIGNMENTS:
		unit = frappe.db.get_value("Organisation Unit", {"unit_name": unit_name}, "name") if unit_name else None
		declared.add((f"{local}@moh.example.test", role, unit))
	return [
		r.name
		for r in frappe.get_all(
			"User Responsibility Assignment",
			filters={"fixture_namespace": site_setup.FIXTURE_TAG},
			fields=["name", "user", "business_role", "organisation_unit"],
		)
		if (r.user, r.business_role, r.organisation_unit or None) not in declared
	]


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
		from kentender_budget.seeds.kentender_mvp_v1_portfolio import canonical_budgets

		canonical = canonical_budgets()
		add("Procurement Budget", [name for name in frappe.get_all("Procurement Budget", pluck="name") if name not in canonical])
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

	# Strategy: every plan outside the canonical namespace and every version
	# of the canonical plan other than Version 1 (the module's own rule).
	from kentender_strategy.seeds.kentender_mvp_v1_strategy import strategy_rows_to_clear

	for doctype, names in strategy_rows_to_clear().items():
		add(doctype, names)

	# Tenders: everything not on the canonical Requisition (the module's own
	# rule, `tenders.seeds.clear`).
	from kentender_procurement.tenders.seeds.clear import tender_rows_to_clear

	for doctype, names in tender_rows_to_clear().items():
		add(doctype, names)

	# Requisitions: every root not on a canonical Plan Item (the module's own rule).
	from kentender_procurement.procurement_requisitions.seeds.clear import requisition_rows_to_clear

	for doctype, names in requisition_rows_to_clear().items():
		add(doctype, names)

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
	add("User Responsibility Assignment", _undeclared_site_assignments())
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
	# Direct sweep, independent of any User row: a Contact whose User was
	# already deleted by some other, incomplete test teardown has no User
	# left to find it through, and is otherwise invisible to this clear
	# forever. Found on this site accumulating in the thousands from
	# unrelated CFG/AUTH test suites that create a Contact with no matching
	# User at all.
	add(
		"Contact",
		[
			c.name
			for c in frappe.get_all("Contact", fields=["name", "email_id"])
			if c.email_id and _fixture_email(c.email_id) and c.email_id not in REGISTER_USERS
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
	for child, names in _orphaned_child_rows().items():
		add(child, names)
	add("File", _orphaned_attachments())
	for projection in _NEED_PROJECTIONS:
		add(projection, _projections_without_a_need(projection))
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
		"Need Planning Disposition Projection",
		"Need Planning Intake Projection",
		"Departmental Need Decision",
		"Departmental Need Review Task",
		"Need Withdrawal Request",
		"Departmental Need Revision",
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

	def _fold(result: dict[str, Any]) -> None:
		for doctype, count in result.get("deleted", {}).items():
			if isinstance(count, int) and count:
				deleted[doctype] = deleted.get(doctype, 0) + count

	# Downstream first: Tenders consumes Requisitions' handoff,
	# Requisitions consumes Planning's Plan Item, Planning and Needs
	# reference Budget lines and units. Neither module stamps every
	# doctype with a fixture_namespace column, so their own clear functions
	# (not the `plan` dict) decide what "canonical" means for their rows;
	# `include_canonical=False` here only ever removes Playwright-owned
	# residue, matching how Planning/Needs rows survive `reset`.
	playwright_ok = _playwright_cleanup_allowed()

	from kentender_procurement.tenders.seeds.clear import clear_tender_fixture_rows

	_fold(clear_tender_fixture_rows())

	from kentender_procurement.procurement_requisitions.seeds.clear import clear_requisition_fixture_rows

	_fold(clear_requisition_fixture_rows(include_canonical=False, include_playwright=playwright_ok))
	from kentender_procurement.procurement_requisitions.seeds.clear import clear_stray_requisitions

	_fold(clear_stray_requisitions())

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

	# Strategy last among the modules: Budget lines and Needs point at its
	# objectives, and their strays are gone by now.
	from kentender_strategy.seeds.kentender_mvp_v1_strategy import clear_non_canonical_strategy

	_fold(clear_non_canonical_strategy())

	# The document's own fixture-purge switch (regulatory_reference.on_trash).
	_delete_docs("Regulatory Reference", plan.get("Regulatory Reference", []), deleted, kt_fixture_purge=True)

	for doctype in _LEGACY_DEMO_DOCTYPES:
		_delete_docs(doctype, plan.get(doctype, []), deleted)

	ura_users = set(frappe.get_all("User Responsibility Assignment", filters={"name": ("in", plan.get("User Responsibility Assignment") or [""])}, pluck="user"))
	_delete_docs("User Responsibility Assignment", plan.get("User Responsibility Assignment", []), deleted)
	# A direct delete keeps the Frappe roles the grants projected; re-sync the
	# people who stay (the same projection the revoke command applies).
	from kentender_core.services.responsibility_administration import _sync_projection

	for user in sorted(ura_users):
		if frappe.db.exists("User", user):
			_sync_projection(user)
	for user in plan.get("User", []):
		if frappe.db.exists("User", user):
			_delete_user(user, deleted)
	# Orphaned Contacts direct from the plan (no User left to delete them
	# through) — see collect_non_canonical()'s own note on this.
	_delete_docs("Contact", plan.get("Contact", []), deleted)

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

	# Recomputed fresh, not read from `plan`: a year can go from referenced to
	# unreferenced as a side effect of the deletions just above (its own
	# Annual Plan, Regulatory Reference or Procurement Budget going with it),
	# and the pre-clear `plan` snapshot would miss exactly that year.
	site_fys = _site_fiscal_years()
	candidate_fys = [fy for fy in frappe.get_all("Fiscal Year", filters={"name": ["not like", "_Test%"]}, pluck="name") if fy not in site_fys]
	_delete_docs("Fiscal Year", [fy for fy in candidate_fys if not _fiscal_year_referenced(fy)], deleted)

	# Last, and recomputed like the years: the deletions above leave child
	# rows and attachments of their own behind.
	for child, names in _orphaned_child_rows().items():
		for start in range(0, len(names), 500):
			frappe.db.delete(child, {"name": ("in", names[start : start + 500])})
		deleted[child] = deleted.get(child, 0) + len(names)
	_delete_docs("File", _orphaned_attachments(), deleted)
	for projection in _NEED_PROJECTIONS:
		orphans = _projections_without_a_need(projection)
		if orphans:
			frappe.db.delete(projection, {"name": ("in", orphans)})
			deleted[projection] = deleted.get(projection, 0) + len(orphans)
	return deleted


def clear_canonical_modules() -> dict[str, Any]:
	"""`rebuild`: drop the canonical module rows too (downstream first —
	Tenders before Requisitions before Planning/Needs, since each
	consumes the one before it), leaving the §8 site world."""
	out: dict[str, Any] = {}
	playwright_ok = _playwright_cleanup_allowed()
	# Not clear_requisition_fixture_rows(include_canonical=True, ...): that
	# path is a direct delete which refuses outright on an Authorised
	# Requisition with an Active Budget reservation (the "wipe after
	# authorise" hazard). reset_requisitions_seed() revokes it first through
	# the real command, then does the same delete — the safe rebuild path.
	from kentender_procurement.procurement_requisitions.seeds.clear import clear_requisition_fixture_rows
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import reset_requisitions_seed
	from kentender_procurement.tenders.seeds.clear import canonical_tenders
	from kentender_procurement.tenders.seeds.kentender_mvp_v1 import reset_tenders_seed

	# The canonical Tenders' downstream records first (the laptops' and the
	# executed portfolio's bids, openings, evaluations and awards): deleting a
	# Tender leaves them to their own modules' clears.
	tenders = canonical_tenders()
	if tenders:
		from kentender_procurement.award.seeds import clear as award_clear
		from kentender_procurement.bid_evaluation.seeds import clear as evaluation_clear
		from kentender_procurement.bid_opening.seeds import clear as opening_clear
		from kentender_procurement.bid_submission.seeds import clear as bids_clear

		out["award"] = award_clear.wipe(tenders=tenders)
		out["bid_evaluation"] = evaluation_clear.wipe(tenders=tenders, namespace=BID_EVALUATION_NS)
		out["bid_opening"] = opening_clear.wipe(tenders=tenders, namespace=BID_OPENING_NS)
		out["bid_submission"] = bids_clear.wipe(tenders=tenders, namespace=BIDS_NS)
	out["tenders"] = reset_tenders_seed(commit=False)
	# The canonical supplier accounts go too, so a rebuild recreates them at
	# their seed's own instants (found 5 Oct 2026: accounts seeded with the
	# earlier May–June dates refused the executed portfolio's April bids).
	removal = frappe.get_hooks("kt_seed_supplier_account_removal") or []
	if removal:
		out["supplier_accounts"] = frappe.get_attr(removal[-1])(namespace=BIDS_NS)
	# Tenders is already cleared, so a handoff it consumed has no Tender left;
	# Planning and Budget are cleared below in this same transaction.
	out["requisitions"] = reset_requisitions_seed(commit=False, cross_module_rebuild=True)
	for doctype, count in clear_requisition_fixture_rows(include_canonical=False, include_playwright=playwright_ok).get("deleted", {}).items():
		if isinstance(count, int):
			out["requisitions"][doctype] = out["requisitions"].get(doctype, 0) + count
		else:
			out["requisitions"][doctype] = count
	# Not clear_planning_fixture_rows(include_canonical=True, ...) alone:
	# "Planning Command Journal" isn't one of its _DOCTYPES, so a stale
	# "pln-seed:open-dhi-dpp"-keyed row survives, and the next seed run's
	# open_departmental_plan() replays it — returning a cached result that
	# names a Departmental Plan Version this same clear just deleted, so
	# the seed's very next step ("did the accepted Need project into the
	# Draft DPP") finds nothing and throws. reset_planning_seed() is the
	# complete teardown: it also reverses the Need's usage projection
	# through the real published channel and purges that journal.
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		clear_planning_fixture_rows,
		reset_planning_seed,
	)

	out["planning"] = reset_planning_seed(commit=False)
	for doctype, count in clear_planning_fixture_rows(include_canonical=False, include_playwright=playwright_ok).items():
		out["planning"][doctype] = out["planning"].get(doctype, 0) + count
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


def prepare_site(*, current: str = DEFAULT_CURRENT, open_tender: bool = False, through: str | None = None) -> dict[str, Any]:
	"""What the stages need from the site itself, so one allowed run is enough
	on a new demo or test site (found 4 Oct 2026: a new server failed one
	missing piece at a time). From `requisitions`: this repository's
	IT-equipment tender template, installed and switched on if the site has
	none. From `bid_submission`: the simulated signing, tender-box and
	delivery services (site_config `kt_bds_simulation_environment`), switched
	on with a notice — the canonical bids exist only on a demo or test site.
	The same for a Tender left open (`open_tender`), which is there to be bid on."""
	if through:
		current, _next = resolve_years(through=through)
	out: dict[str, Any] = {"template_release": None, "simulation_switched_on": False}
	if _reaches("requisitions", current=current):
		from kentender_procurement.procurement_requisitions.services.compatibility import template_problem
		from kentender_procurement.std_templates.compiler.errors import STDTemplateError
		from kentender_procurement.std_templates.services import binding, installer

		out["template_release"] = installer.ensure_site_release()
		# usable, not merely installed: a wrong PDF renderer build otherwise
		# surfaces three stages later as a misleading requisition refusal
		try:
			binding.require(out["template_release"], "new_binding")
		except STDTemplateError as exc:
			frappe.throw(f"The IT-equipment tender template cannot be used on this site: {template_problem(exc)} "
				"The seed needs it from the requisitions stage on; fix this and run the seed again.")
	from frappe.utils import cint

	if (_reaches("bid_submission", current=current) or open_tender) and not cint(frappe.conf.get("kt_bds_simulation_environment")):
		from frappe.installer import update_site_config

		update_site_config("kt_bds_simulation_environment", 1)
		frappe.conf.kt_bds_simulation_environment = 1
		out["simulation_switched_on"] = True
		print("NOTICE: switched on the simulated bid services for this site (site_config kt_bds_simulation_environment = 1); "
			"the canonical bids, and bids on a Tender left open, need them. Never set this on a site that takes real bids.")
	return out


#: The stages that can stop before the canonical Tender's deadline (`open_tender`).
OPEN_TENDER_STAGES = ("tenders", "bid_submission")


def _check_open_tender(current: str, open_tender: bool) -> None:
	if open_tender and current not in OPEN_TENDER_STAGES:
		frappe.throw(
			f"OPEN=True leaves the canonical Tender open for bids, before its deadline, so it goes only with CURRENT=tenders "
			f"or CURRENT=bid_submission (asked for CURRENT={current}): the later stages need the Tender closed."
		)


def seed(*, current: str | None = None, next_year: str | None = None, open_tender: bool = False, through: str | None = None) -> dict[str, Any]:
	"""Reseed the canonical world: the executed year through `current`, the
	prepared year through `next_year`. No commit. `open_tender` (owner,
	4 Oct 2026: a Tender anyone can see on /tenders and bid on) stops the
	canonical Tender's story before its 12 Jun 2027 deadline. The site test
	clock is left at the as-at instant (a test site only)."""
	current, next_year = resolve_years(current=current, next_year=next_year, through=through)
	_check_open_tender(current, open_tender)
	ahead = world_ahead(current=current, next_year=next_year)
	if ahead:
		frappe.throw(f"The site holds more than CURRENT={current} NEXT={next_year} asks for: {'; '.join(ahead)}.", exc=CanonicalWorldNeedsRebuild)
	report: dict[str, Any] = {"current": current, "next_year": next_year, "site": site_setup.run(commit=False)}
	report["site"]["prepared"] = prepare_site(current=current, open_tender=open_tender)
	# Independent of the stages: the fixture world's Procurement Rules must be
	# usable whatever is seeded, not only once the Planning stage's own seed
	# happens to run (see `stamp_procurement_rules_fixture_verified`'s docstring).
	report["site"]["rules_stamped_fixture_verified"] = site_setup.stamp_procurement_rules_fixture_verified()
	from kentender_strategy.seeds.kentender_mvp_v1_strategy import upsert_kentender_mvp_v1_strategy

	report["strategy"] = upsert_kentender_mvp_v1_strategy()
	from kentender_budget.seeds.kentender_mvp_v1_portfolio import upsert_kentender_mvp_v1_portfolio

	# The §15.3 Active baselines only — §15.5/§15.6 profiles are created and
	# removed by the tests that need them (§15.7).
	budget_years = ("year1", "year2") if _next_reaches("budget", next_year=next_year) else ("year1",)
	report["budget"] = upsert_kentender_mvp_v1_portfolio(include_test_edges=False, commit=False, years=budget_years)
	from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import upsert_departmental_needs

	needs_years = ("year1", "year2") if _next_reaches("needs", next_year=next_year) else ("year1",)
	report["needs"] = upsert_departmental_needs(commit=False, years=needs_years)
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import upsert_planning_base

	planning_years = {"year1": "annual_plan"}
	if _next_reaches("departmental_plans", next_year=next_year):
		planning_years["year2"] = next_year
	report["planning"] = upsert_planning_base(commit=False, years=planning_years)
	if _reaches("requisitions", current=current):
		from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import upsert_requisitions_base

		report["requisitions"] = upsert_requisitions_base(commit=False)
		# `authorise_requisition()` — the real command — has no fixture
		# concept, so the Budget reservation it opens carries no
		# fixture_namespace by default; this orchestrator owns
		# REQUISITIONS_NS and stamps it here (never the sibling Requisitions
		# module, which must not write another app's doctype directly —
		# KT-STD-001 cross-app rule). Runs on every seed, not just a fresh
		# build, so a reservation opened before this stamping existed is
		# healed on the next canonical seed too.
		stamp_requisition_reservations()
	if _reaches("tenders", current=current) and not _reaches("bid_submission", current=current):
		from kentender_procurement.tenders.seeds.kentender_mvp_v1 import upsert_tenders_base

		report["tenders"] = upsert_tenders_base(commit=False, stop_before_close=open_tender)
	if _reaches("bid_submission", current=current):
		# BDS-CHG-001 v0.8 plan D19: the canonical Tender's chronology with the
		# bid's own lifecycle interleaved (Start bid 19 May … Mary's accepted
		# submission 10 Jun … the close and Bid Opening hand-off 12 Jun). It
		# builds the Tenders stage itself, so the Tender is never first closed
		# with the bid still a Draft.
		from kentender_procurement.bid_submission.seeds.kentender_mvp_v1 import upsert_bid_submission_base

		report["bid_submission"] = upsert_bid_submission_base(commit=False, open_tender=open_tender)
		report["tenders"] = {"ok": True, "via": "bid_submission", "tender": report["bid_submission"].get("tender")}
	if _reaches("bid_opening", current=current):
		# BOP-CHG-001 v0.10 plan D14: the canonical Tender's opening, after the
		# bid_submission stage closed its box at 11:00.
		from kentender_procurement.bid_opening.seeds.kentender_mvp_v1 import upsert_bid_opening_base

		report["bid_opening"] = upsert_bid_opening_base(commit=False)
	if _reaches("bid_evaluation", current=current):
		# EVL-CHG-001 v0.4 plan D18: the canonical Tender's evaluation (§11.1),
		# from appointment on 11 Jun to the report sent on 16 Jun.
		from kentender_procurement.bid_evaluation.seeds.kentender_mvp_v1 import upsert_bid_evaluation_base

		report["bid_evaluation"] = upsert_bid_evaluation_base(commit=False)
	if _reaches("award", current=current):
		# AWD-CHG-001 v0.4 §13: the canonical award, from the report received on
		# 16 Jun to Mary Wanjiku's acceptance on 18 Jun (the waiting period runs
		# at the as-at instant).
		from kentender_procurement.award.seeds.kentender_mvp_v1 import upsert_award_base

		report["award"] = upsert_award_base(commit=False)
	# The executed year's portfolio beside the laptops (two-year seed world
	# proposal §5), each record as far as CURRENT lets it go.
	from kentender_core.seeds import portfolio

	report["portfolio"] = portfolio.seed_portfolio(current=current)
	if _reaches("requisitions", current=current):
		stamp_requisition_reservations()
	report["test_clock"] = set_as_at()
	return report


class CanonicalWorldNeedsRebuild(frappe.ValidationError):
	"""The site holds more of a year than this run asks for (a lower CURRENT
	or NEXT than the last run's). Canonical rows are kept by `reset`, so
	`run` rebuilds the canonical module rows once."""


def world_ahead(*, current: str, next_year: str) -> list[str]:
	"""What the site already holds beyond the requested stages."""
	y2 = calendar.YEAR2.fiscal_year
	ahead: list[str] = []

	def has(doctype: str, filters: dict | None = None) -> bool:
		return bool(frappe.db.exists("DocType", doctype)) and bool(frappe.db.exists(doctype, filters or {}))

	if not _next_reaches("budget", next_year=next_year) and has("Procurement Budget", {"fiscal_year": y2}):
		ahead.append(f"a {calendar.YEAR2.label} budget")
	if not _next_reaches("needs", next_year=next_year) and has("Departmental Need", {"financial_year": y2}):
		ahead.append(f"{calendar.YEAR2.label} Needs")
	if not _next_reaches("departmental_plans", next_year=next_year) and has("Departmental Plan", {"fiscal_year": y2, "current_state": ("!=", "Draft")}):
		ahead.append(f"{calendar.YEAR2.label} departmental plans past Draft")
	if not _next_reaches("annual_plan", next_year=next_year) and has("Annual Plan", {"fiscal_year": y2, "active_version": ("is", "set")}):
		ahead.append(f"an Active {calendar.YEAR2.label} Annual Plan")
	if not _reaches("requisitions", current=current) and has("Procurement Requisition"):
		ahead.append(f"Requisitions (CURRENT={current} stops before requisitions)")
	tenders = frappe.get_all("Tender", pluck="name") if frappe.db.exists("DocType", "Tender") else []
	if not _reaches("tenders", current=current) and tenders:
		ahead.append(f"Tenders (CURRENT={current} stops before tenders)")
	# Only rows of a Tender that still exists: a rebuild deletes the Tenders and
	# leaves its downstream modules' rows to their own clears.
	# A Draft bid is the Tenders stage's own (its candidate registers through
	# Start bid); a submitted one is the bid_submission stage's.
	# Likewise Award takes a delivered evaluation report up by itself: a case
	# still at Opinion is the evaluation stage's consequence.
	for stage, doctype, extra in (
		("bid_submission", "Bid Workspace", {"status": "Submitted"}), ("bid_opening", "Bid Opening Case", {}), ("bid_evaluation", "Evaluation Case", {}),
		("award", "Award Case", {"stage": ("!=", "Opinion")}),
	):
		if not _reaches(stage, current=current) and tenders and has(doctype, {"tender": ("in", tenders), **extra}):
			ahead.append(f"{doctype} rows (CURRENT={current} stops before {stage})")
	return ahead


def stamp_requisition_reservations() -> int:
	"""Stamp every Active reservation a seeded Requisition opened with
	REQUISITIONS_NS (see `seed`)."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import seeded_requisition_references

	stamped = 0
	for reference in seeded_requisition_references():
		for reservation in frappe.get_all(
			"Funding Reservation",
			filters={"calling_module": "Procurement Requisitions", "caller_reference": reference, "status": "Active"},
			pluck="name",
		):
			frappe.db.set_value("Funding Reservation", reservation, "fixture_namespace", REQUISITIONS_NS, update_modified=False)
			stamped += 1
	return stamped


def set_as_at() -> bool:
	"""Put a test site's live pages on the as-at instant (two-year seed world
	plan D1). False on a site that is not a test environment: it reads the
	real clock."""
	from kentender_core.services import test_clock

	return test_clock.set_instant(calendar.AS_AT)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def validate(*, current: str | None = None, next_year: str | None = None, open_tender: bool = False, through: str | None = None) -> dict[str, Any]:
	"""Assert the canonical facts of both years as far as `current` and
	`next_year` reach; raise listing every failed check. `open_tender`: the
	world was seeded with the canonical Tender left open (see `seed`)."""
	current, next_year = resolve_years(current=current, next_year=next_year, through=through)
	_check_open_tender(current, open_tender)
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
	for local in site_setup.TECHNICAL_ACTORS:
		check("System Manager" in frappe.get_roles(f"{local}@moh.example.test"), f"{local} is a technical reader (System Manager)")
	for email, _name in site_setup.PUBLIC_ACTORS:
		check(frappe.db.get_value("User", email, "user_type") == "Website User", f"{email} is a Website User (public observer)")
	strays = [
		u
		for u in frappe.get_all("User", filters={"name": ["not in", ["Administrator", "Guest"]]}, pluck="name")
		if _fixture_email(u) and u not in REGISTER_USERS
	]
	check(not strays, f"no fixture-domain users outside the register, found {strays}")
	check(site_setup.unit_tree_intact(), "every Organisation Unit sits inside its parent's tree range")
	for local, role, unit_name, kwargs in site_setup.ASSIGNMENTS:
		rows = frappe.get_all(
			"User Responsibility Assignment",
			filters={"user": f"{local}@moh.example.test", "business_role": role, "fixture_namespace": site_setup.FIXTURE_TAG},
			fields=["organisation_unit", "effective_from", "effective_to"],
		)
		unit = frappe.db.get_value("Organisation Unit", {"unit_name": unit_name}, "name") if unit_name else None
		terms = [
			(str(row.effective_from or "")[:19], str(row.effective_to or "")[:19])
			for row in rows
			if (row.organisation_unit or None) == unit
		]
		# The dates the seed asks for, not merely a row (since v1.11): an
		# existing assignment is returned as it is, so a changed term only
		# lands on a wiped site.
		expected = (str(kwargs.get("effective_from") or "")[:19], str(kwargs.get("effective_to") or "")[:19])
		check(expected in terms, f"assignment {local}: {role}{' in ' + unit_name if unit_name else ''} from {expected[0] or 'no start'} to {expected[1] or 'no end'} (found {terms}); a changed term needs WIPE=True")
	# Every unit-scoped role a seeded assignment names must have someone
	# holding it *now*, not merely a row somewhere. The check above only
	# asks whether the seed wrote what it said it would; it passed happily
	# while Digital Health had no Head of User Department at all, because
	# the only two grants for that branch were one expired and one not yet
	# started. A canonical world nobody can act in is not canonical.
	scoped: set[tuple[str, str]] = {(role, unit) for _local, role, unit, _kwargs in site_setup.ASSIGNMENTS if unit}
	for role, unit_name in sorted(scoped):
		unit = frappe.db.get_value("Organisation Unit", {"unit_name": unit_name}, "name")
		# A grant reaches the unit it names and that unit's descendants
		# (`authorization.descendants_of`), so a unit is covered by its own
		# grant or by any ancestor's — the same walk the resolver does.
		chain: list[str] = []
		cursor = unit
		while cursor:
			chain.append(cursor)
			cursor = frappe.db.get_value("Organisation Unit", cursor, "parent_organisation_unit")
		holders = [
			row
			for row in frappe.get_all(
				"User Responsibility Assignment",
				filters={"business_role": role, "organisation_unit": ["in", chain], "status": "Enabled"},
				fields=["name", "effective_from", "effective_to"],
			)
			if _in_force_now(row)
		]
		check(bool(holders), f"{role} in force today for {unit_name}")

	from kentender_strategy.seeds.kentender_mvp_v1_strategy import validate_strategy_seed

	for row in validate_strategy_seed():
		check(row["ok"], f"strategy: {row['check']}")

	from kentender_budget.seeds.kentender_mvp_v1_portfolio import canonical_budget, validate_budget_seed

	budget_years = ("year1", "year2") if _next_reaches("budget", next_year=next_year) else ("year1",)
	budgets = frappe.get_all("Procurement Budget", fields=["name", "generated_reference"])
	expected_budgets = sorted(b for b in (canonical_budget(year) for year in budget_years) if b)
	check(sorted(b.name for b in budgets) == expected_budgets and len(expected_budgets) == len(budget_years),
		f"the canonical budgets ({', '.join(calendar.year(y).label for y in budget_years)}) are the only ones, found {[b.generated_reference for b in budgets]}")
	# §15.4: reservation begins at Requisition. A reservation stamped
	# REQUISITIONS_NS is canonical evidence of an authorised Requisition, not
	# a stray; anything else is a defect (a caller reserving outside that namespace).
	stray_reservations = [r.name for r in frappe.get_all("Funding Reservation", fields=["name", "fixture_namespace"]) if (r.fixture_namespace or "") != REQUISITIONS_NS]
	check(not stray_reservations, f"no Funding Reservation outside {REQUISITIONS_NS!r}, found {stray_reservations}")
	stray_commitments = [r.name for r in frappe.get_all("Procurement Commitment", fields=["name", "fixture_namespace"]) if (r.fixture_namespace or "") != REQUISITIONS_NS]
	check(not stray_commitments, f"no Procurement Commitment outside {REQUISITIONS_NS!r}, found {stray_commitments}")
	for year in budget_years:
		for row in validate_budget_seed(year):
			check(row["ok"], f"budget {calendar.year(year).label}: {row['check']}")

	from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import validate_needs_seed

	for year in ("year1", "year2") if _next_reaches("needs", next_year=next_year) else ("year1",):
		for row in validate_needs_seed(year):
			check(row["ok"], f"needs {calendar.year(year).label}: {row['check']}")
	if not _next_reaches("needs", next_year=next_year):
		stray = frappe.get_all("Departmental Need", filters={"financial_year": calendar.YEAR2.fiscal_year}, pluck="name")
		check(not stray, f"no {calendar.YEAR2.label} Needs at NEXT={next_year}, found {stray}")

	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import validate_planning_history, validate_planning_seed, year_plan

	for row in validate_planning_history("year1"):
		check(row["ok"], f"{row['check']}: {row['detail']}")
	if _next_reaches("departmental_plans", next_year=next_year):
		for row in validate_planning_history("year2", through=next_year):
			check(row["ok"], f"{row['check']}: {row['detail']}")
	else:
		# Accepting a Need starts its department's Draft plan by itself, so
		# Draft plans are expected at NEXT=needs; nothing further.
		further = frappe.get_all("Departmental Plan", filters={"fiscal_year": calendar.YEAR2.fiscal_year, "current_state": ("!=", "Draft")}, pluck="name")
		check(not year_plan("year2") and not further, f"no {calendar.YEAR2.label} departmental plan past Draft and no Annual Plan at NEXT={next_year}")
	if current == "annual_plan":
		# Only while nothing downstream has drawn on the executed plan: a
		# Requisition legitimately draws its items down and a Tender records
		# an actual invitation date on them (FU-16).
		for row in validate_planning_seed():
			check(row["ok"], f"{row['check']}: {row['detail']}")

	if _reaches("requisitions", current=current):
		from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import validate_requisitions_seed

		for row in validate_requisitions_seed():
			check(row["ok"], f"{row['check']}: {row['detail']}")

	if _reaches("tenders", current=current):
		from kentender_procurement.tenders.seeds.kentender_mvp_v1 import validate_tenders_seed

		for row in validate_tenders_seed(open_tender=open_tender):
			check(row["ok"], f"{row['check']}: {row['detail']}")
	if _reaches("bid_submission", current=current):
		from kentender_procurement.bid_submission.seeds.kentender_mvp_v1 import validate_bid_submission_seed

		for row in validate_bid_submission_seed(open_tender=open_tender):
			check(row["ok"], row["check"])
	if _reaches("bid_opening", current=current):
		from kentender_procurement.bid_opening.seeds.kentender_mvp_v1 import validate_bid_opening_seed

		for row in validate_bid_opening_seed():
			check(row["ok"], row["check"])
	if _reaches("bid_evaluation", current=current):
		from kentender_procurement.bid_evaluation.seeds.kentender_mvp_v1 import validate_bid_evaluation_seed

		for row in validate_bid_evaluation_seed():
			check(row["ok"], row["check"])
	if _reaches("award", current=current):
		from kentender_procurement.award.seeds.kentender_mvp_v1 import validate_award_seed

		for row in validate_award_seed():
			check(row["ok"], row["check"])
	from kentender_core.seeds import portfolio

	for row in portfolio.validate_portfolio(current=current):
		check(row["ok"], row["check"])

	from frappe.utils import cint

	from kentender_core.services import test_clock

	if cint(frappe.conf.get("kt_bds_simulation_environment")):
		# a test environment runs its live pages on the as-at instant (plan D1)
		check(str(test_clock.current_instant() or "")[:19] == calendar.AS_AT, f"the site test clock is at {calendar.AS_AT} (found {test_clock.current_instant()!r})")

	report = {"ok": not failures, "current": current, "next_year": next_year, "failures": failures}
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
	current: str | None = None,
	next_year: str | None = None,
	through: str | None = None,
	reset: bool = True,
	rebuild: bool = False,
	wipe: bool = False,
	reseed: bool | None = None,
	validate: bool = True,
	force: bool = False,
	commit: bool = True,
	open_tender: bool = False,
) -> dict[str, Any]:
	"""Clear everything non-canonical (``reset``), optionally the canonical
	module rows too (``rebuild``), optionally the site stage itself
	(``wipe`` — the Procuring Entity, Organisation Units, Fiscal Years and
	the §8.3 actors ``rebuild`` alone never touches, since every other
	stage's canonical rows reference them), reseed the executed year through
	``current`` and the prepared year through ``next_year`` (``through``, the
	retired single-year ladder, maps onto them for one release) and
	validate. One transaction: any failure rolls the whole run back.

	``wipe`` implies ``rebuild``: the site stage is the foundation every
	module stage's canonical rows sit on, so it is only ever safe to drop
	after they are already gone, never on its own.

	``reseed`` defaults to the opposite of ``wipe``: plain ``reset``/
	``rebuild`` still reseed immediately, matching every call site before
	this parameter existed, but ``wipe`` alone now means what the word
	says — clear everything and stop, no stage rebuilt, ``through``/
	``validate`` ignored, nothing left on the site to validate against.
	Pass ``reseed=True`` explicitly with ``wipe=True`` for the old
	"wipe then immediately rebuild the whole chain" behaviour.

	``open_tender`` leaves the canonical Tender open for bids (``seed``);
	switching a world between open and closed rebuilds it by itself."""
	if reseed is None:
		reseed = not wipe
	frappe.only_for(("System Manager", "Administrator"))
	_assert_allowed(force)
	current, next_year = resolve_years(current=current, next_year=next_year, through=through)
	if reseed is not False:
		_check_open_tender(current, open_tender)
	frappe.set_user("Administrator")
	result: dict[str, Any] = {"ok": True, "current": current if reseed else None, "next_year": next_year if reseed else None, "reseed": reseed}
	# One permission for the whole run. The needs/planning/requisitions/
	# tenders module seeds each carry their own developer_mode/allow_tests
	# guard; all of them accept `frappe.flags.in_test`, so an allowed run
	# (`_assert_allowed`: developer_mode, allow_canonical_seed or force) sets
	# it for its own duration. (Until 4 Oct 2026 only `force` did, so a site
	# allowed by allow_canonical_seed still stopped at the Planning stage.)
	in_test_before = frappe.flags.in_test
	frappe.flags.in_test = True
	# Frappe refuses any new background job once 500+ are queued, and a
	# full wipe deletes enough documents to pass that inside this one run
	# (found 26 Sep 2026: 650 queued before the site stage recreated its
	# users). The ceiling protects interactive traffic, not this batch run:
	# lift it in this process only — site_config is untouched — and let
	# `make seed-canonical` drain the queue afterwards.
	max_jobs_before = frappe.conf.get("max_queued_jobs")
	frappe.conf.max_queued_jobs = 1_000_000
	# The run is allowed (`_assert_allowed` above), so the register's actors
	# get the fixture password even without developer_mode (site_setup).
	frappe.flags.kt_fixture_passwords = True
	try:
		result["released_profiles"] = release_demo_profiles()
		if rebuild or wipe:
			from kentender_strategy.services.strategy_reference import reset_reference_series

			result["rebuild"] = clear_canonical_modules()
			# The canonical plan is gone, and allocation starts above any
			# number still in use, so a rebuilt world numbers from 0001 again.
			result["reference_series_reset"] = reset_reference_series()
		if wipe:
			from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import wipe_all_planning
			from kentender_procurement.procurement_requisitions.seeds.clear import wipe_all_requisitions
			from kentender_procurement.tenders.seeds.kentender_mvp_v1 import wipe_all_tenders

			# clear_canonical_modules()'s tenders/requisitions/planning steps
			# all select by a live parent (a title, a Requisition, a fiscal
			# year) rather than a fixture_namespace column every row
			# carries, so a row whose parent was already deleted by some
			# other, unrelated test run is invisible to any of them and
			# survives every rebuild forever. Only safe to go unconditional
			# here: `wipe` clears every other module in the same pass, so
			# nothing is left for an orphan to reference.
			result["tenders_wiped"] = wipe_all_tenders()
			result["planning_wiped"] = wipe_all_planning()
			result["requisitions_wiped"] = wipe_all_requisitions()
			result["wiped"] = site_setup.reset_site_setup(commit=False)
			# Not KenTender seed data, but wipe's own job is "empty database"
			# and this recurs constantly: `bench run-tests` on kentender_core
			# (or any app) fires Frappe's before_tests global test-record
			# preload the first time an old-style test class runs, which
			# creates ~39 ERPNext `_Test Fiscal Year %` rows as a side
			# effect of routine test runs during ordinary module work - not
			# a rare event, so a separate command to remember doesn't hold up.
			from kentender_core.tests.erpnext_test_fixture_cleanup import purge as purge_erpnext_test_fixtures

			result["erpnext_test_fixtures_purged"] = purge_erpnext_test_fixtures(commit=False)
		if reset:
			result["removed"] = clear_non_canonical()
		if reseed:
			result["seeded"] = seed(current=current, next_year=next_year, open_tender=open_tender)
			if validate:
				result["validate"] = globals()["validate"](current=current, next_year=next_year, open_tender=open_tender)
		if commit:
			frappe.db.commit()
		print(
			"CANONICAL_SEED_OK current=%s next=%s removed=%s" % (result["current"], result["next_year"], result.get("removed") or {}),
		)
		return result
	except Exception as exc:
		frappe.db.rollback()
		if not _tender_needs_rebuild(exc) or rebuild or wipe:
			raise
	finally:
		frappe.flags.in_test = in_test_before
		frappe.conf.max_queued_jobs = max_jobs_before
		frappe.flags.kt_fixture_passwords = False
	# A bid submission commits at once (the attempt must survive a crash), so a
	# run that failed after the bids left the canonical Tender without its
	# lifecycle (found 4 Oct 2026 on a new server); and a Tender left open for
	# bids (`open_tender`) cannot be closed into the canonical story, nor a
	# closed one reopened. Rebuild, once.
	print(
		"NOTICE: the canonical world is not in the shape this run builds on (more of a year than CURRENT/NEXT ask for, "
		"a Tender left open for bids or closed, or half-built by an earlier failed run); rebuilding the canonical module records."
	)
	out = run(current=current, next_year=next_year, reset=reset, rebuild=True, wipe=False, reseed=reseed, validate=validate, force=force, commit=commit, open_tender=open_tender)
	out["rebuilt_after_partial_world"] = True
	return out


def _tender_needs_rebuild(exc: Exception) -> bool:
	if isinstance(exc, CanonicalWorldNeedsRebuild):
		return True
	try:
		from kentender_procurement.tenders.seeds.kentender_mvp_v1 import CanonicalTenderNeedsRebuild
	except ImportError:
		return False
	return isinstance(exc, CanonicalTenderNeedsRebuild)


def release_demo_profiles() -> dict[str, Any]:
	"""Undo every loaded demo profile before the reset, through each module's
	own release, and clear the site-wide test clock: the canonical world has
	none. Each release is a no-op when its profile is not loaded."""
	from kentender_core.services import test_clock

	out: dict[str, Any] = {}
	# A loaded Requisitions demo profile (REQ-CHG-001 v1.11 §16.4A) holds
	# Budget reservations and Planning requests on the canonical item; undo
	# it through the real commands first, so the reset below never leaves a
	# Requisition row pointing at a reservation it deleted.
	from kentender_procurement.procurement_requisitions.seeds.profiles import release_loaded_profile

	out["requisitions"] = release_loaded_profile()
	# The Departmental Needs demo profiles change the canonical Need
	# NDS-MOH-2027-0001 in place (a successor revision, a withdrawal, a
	# usage projection); each reset is a no-op when its profile is not
	# applied. Found 26 Sep 2026: a test left the successor applied.
	from kentender_procurement.departmental_needs.seeds import profiles as needs_profiles

	out["needs"] = {name: reset() for name, (_apply, reset) in needs_profiles.PROFILES.items() if name != "default"}
	# A Bid Opening profile leaves its loaded marker, test controls and the
	# clock; an Award profile only the clock (found 1 Oct 2026: a plain
	# reseed retold both stories but left every live page on the profile's
	# 2027 moment). Their stages retell the partial opening and award.
	from kentender_procurement.bid_opening.seeds.profiles import release_loaded_profile as release_opening_profile

	out["bid_opening"] = release_opening_profile()
	out["test_clock_cleared"] = test_clock.set_instant(None)
	return out
