"""Deterministic Departmental Needs seed (NDS-CHG-001 v1.6 §14).

§14.1: "The site PE, ERPNext Fiscal Year, Needs-submission flag and close
instant, OUs, units of measure and assignments come from Configuration &
Governance. Seeds fail if any authoritative prerequisite differs; they do not
invent fallback records." Every one of those is
`kentender_core.seeds.site_setup`'s own canonical KT-STD-001 §8 fixture
world — this module never creates or repairs any of it, and refuses loudly
if it is missing rather than building a parallel one.

This seed's own job is narrow: drive the four §14.3 default Needs to their
exact states through the real §8.2 commands (§14.7), exactly as the v1.1
cycle did — only the authority, scope and Financial Year/unit sources
underneath have changed.

Organisation Units are resolved from each actor's own real, Enabled
`User Responsibility Assignment` rather than by name lookup. The site
currently carries two Organisation Unit records sharing the name "Human
Resources Management and Development" — one from `site_setup.py`'s governed
`add_organisation_unit` command, one from an older, separate legacy fixture
world (`AUTH_IMPLEMENTATION_TRACKER_v2.0.md` conflict C4, resolved in favour
of the governed/name-addressed one but not yet cleaned up — out of scope for
this cutover). Resolving through the actor's actual grant sidesteps that
ambiguity entirely: whichever unit the actor can really act in is the only
one that matters here.
"""

from __future__ import annotations

from contextlib import contextmanager

import frappe

from kentender_procurement.departmental_needs.constants import (
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
)
from kentender_core.seeds import calendar, clock
from kentender_procurement.departmental_needs.services import lifecycle

#: The year whose Needs intake is open on the site (Year 2, FY 2027/28): the
#: year tests create their own Needs in.
FY = calendar.YEAR2.fiscal_year
NS = "KENTENDER_MVP_1_R1_NDS"

DEPARTMENTAL_AUTHOR = "Departmental Author"
HEAD_OF_USER_DEPARTMENT = "Head of User Department"

# §14.2 — the KT-STD-001 §8.3 shared register's exact NDS actors.
AUTHOR = "grace.wanjiku@moh.example.test"
REVIEWER = "peter.kimani@moh.example.test"
ACTING_REVIEWER = "julia.njeri@moh.example.test"
PLANNER = "mercy.kilonzo@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"

# §14.1 governed units — ERPNext UOM, `enabled=1` (Configuration & Governance
# owned; docname is the exact `uom_name`).
UNITS = ("Programme", "Each")

RETURN_REASON = (
	"Confirm the number of trainees to be supported and revise the laptop quantity "
	"if the approved training cohort has changed."
)
YEAR2_RETURN_REASON = (
	"Confirm the number of training rooms to be equipped and revise the quantity "
	"if the approved training plan has changed."
)

# §14.3 / KT-STD-001 §8.4A / PLN-CHG-001 v1.18 §13.1 — the fixture instants
# (EAT) each command runs **at**, under the frozen seed clock
# (kentender_core.seeds.clock, plan D19), by position in a year's list.
# Creation and submission fall on 24 Nov inside the Needs window
# (09:00–15:30); decisions keep the SEED-001 §3.2 harmonized instants (the
# first Digital Health laptops Need accepted on 25 Nov 09:30, the returned
# HRMD Need at 10:00). Year 1 runs the same instants 364 days earlier
# (`calendar.YEAR1`). Nothing is back-stamped after the fact.
_TIMES = (
	{"create": "2026-11-24 09:00:00", "submit": "2026-11-24 09:40:00", "decide": "2026-11-24 14:00:00"},
	{"create": "2026-11-24 11:30:00", "submit": "2026-11-24 12:20:00"},
	{
		"create": "2026-11-24 10:00:00",
		"submit": "2026-11-24 10:30:00",
		"return": "2026-11-24 13:35:00",
		"resubmit": "2026-11-25 09:00:00",
		"decide": "2026-11-25 10:00:00",
	},
	{"create": "2026-11-24 10:15:00", "submit": "2026-11-24 10:45:00", "decide": "2026-11-25 09:30:00"},
)

# The year's Needs intake, opened for the build and closed at its documented
# instant (site_setup.INTAKE for Year 2; the same instant 364 days earlier for
# Year 1).
_INTAKE = {"open": "2026-11-24 08:00:00", "closes": "2026-11-25 23:59:00"}

# Two-year seed world (owner, 4 Oct 2026, D8–D10). A year's Needs, in the
# order the commands create them, so each reference is the year's next one.
#
# Year 1 (FY 2026/27, carried out): the §14.3 laptop and infrastructure Needs
# the executed Annual Plan takes up, due inside FY 2026/27 (Needs refuse a
# Required by outside their year, departmental_needs.services.lifecycle).
# Julia Njeri accepts the Digital Health ones inside her acting window.
#
# Year 2 (FY 2027/28, being prepared): the same journeys with the year's own
# requirements (D10), so the references, states and instants the module has
# always shown are kept — NDS-MOH-2027-0002 is still Submitted for Dr Peter
# Kimani's review, NDS-MOH-2027-0003 still returned once and corrected. Peter
# holds Digital Health from 2 Dec 2025, so he decides them all.
YEAR_NEEDS = {
	"year1": (
		{
			"unit_name": "Digital Health",
			"title": "National digital health infrastructure upgrade",
			"description": "Procure and implement national digital health infrastructure across priority health facilities.",
			"expected_operational_result": "Priority health facilities can use secure and interoperable digital health services.",
			"indicative_quantity": 1,
			"unit": "Programme",
			"required_by_date": "2027-06-30",
			"state": STATE_ACCEPTED,
			"reviewer": ACTING_REVIEWER,
			"times": 0,
		},
		{
			# NDS-CHG-001 v1.14 §14.3 / SEED-001 v1.3 §3.2: Revision 1 asks for
			# 200 and is returned by Peter; Revision 2, the server-created copy,
			# corrects it to 100 and is the accepted source of the combined laptop
			# Plan Item.
			"unit_name": "Human Resources Management and Development",
			"title": "Clinical training laptops for digital health rollout",
			"description": "Laptop computers for clinical training during the national digital health rollout.",
			"expected_operational_result": "Provide the equipment required for staff training on the deployed digital health services.",
			"indicative_quantity": 200,
			"unit": "Each",
			"required_by_date": "2027-06-30",
			"state": STATE_ACCEPTED,
			"corrected_quantity": 100,
			"return_reason": RETURN_REASON,
			"times": 2,
		},
		{
			"unit_name": "Digital Health",
			"title": "Clinical deployment laptops for digital health rollout",
			"description": "Laptop computers for deployment at priority facilities during the national digital health rollout.",
			"expected_operational_result": "Provide endpoint equipment required to use the deployed digital health services.",
			"indicative_quantity": 150,
			"unit": "Each",
			"required_by_date": "2027-06-30",
			"state": STATE_ACCEPTED,
			"reviewer": ACTING_REVIEWER,
			"times": 3,
		},
	),
	"year2": (
		{
			"unit_name": "Digital Health",
			"title": "Health information exchange platform upgrade",
			"description": "Upgrade the national health information exchange platform so facilities can share patient records securely.",
			"expected_operational_result": "Health facilities exchange patient records through one secure, interoperable platform.",
			"indicative_quantity": 1,
			"unit": "Programme",
			"required_by_date": "2027-08-31",
			"state": STATE_ACCEPTED,
			"times": 0,
		},
		{
			"unit_name": "Human Resources Management and Development",
			"title": "Digital health workforce certification programme",
			"description": "Professional certification programme for staff supporting national digital health services.",
			"expected_operational_result": "Build internal capacity to operate and support national digital health platforms.",
			"indicative_quantity": 1,
			"unit": "Programme",
			"required_by_date": "2027-12-31",
			"state": STATE_SUBMITTED,
			"times": 1,
		},
		{
			"unit_name": "Human Resources Management and Development",
			"title": "Training centre audio-visual equipment",
			"description": "Projectors, displays and sound equipment for the Ministry's staff training centres.",
			"expected_operational_result": "Training rooms can run digital health courses with working presentation and sound equipment.",
			"indicative_quantity": 20,
			"unit": "Each",
			"required_by_date": "2027-12-31",
			"state": STATE_ACCEPTED,
			"corrected_quantity": 12,
			"return_reason": YEAR2_RETURN_REASON,
			"times": 2,
		},
		{
			"unit_name": "Digital Health",
			"title": "Clinical decision-support software licences",
			"description": "Licences for clinical decision-support software used with the national digital health services.",
			"expected_operational_result": "Clinicians at priority facilities use decision-support tools within the digital health services.",
			"indicative_quantity": 150,
			"unit": "Each",
			"required_by_date": "2027-12-31",
			"state": STATE_ACCEPTED,
			"times": 3,
		},
	),
}


def _year(year: str) -> calendar.Year:
	return calendar.year(year)


def references(year: str) -> list[str]:
	"""The references `year`'s Needs are generated with, in creation order:
	`NDS-{site PE code}-{FY start year}-{4 digits}` (§4.2)."""
	return [f"NDS-MOH-{_year(year).start_year}-{index:04d}" for index in range(1, len(YEAR_NEEDS[year]) + 1)]


def need_specs(year: str) -> list[dict]:
	"""`year`'s Needs with their references and fixture instants filled in."""
	specs = []
	for reference, spec in zip(references(year), YEAR_NEEDS[year]):
		times = {step: _year(year).at(at) for step, at in _TIMES[spec["times"]].items()}
		specs.append({**spec, "reference": reference, "timeline": times})
	return specs


#: Year 2's Needs (the year whose intake is open) under the names the module's
#: tests read. Year 1's come from `need_specs("year1")`.
NEEDS = tuple(need_specs("year2"))
TIMELINE = {spec["reference"]: spec["timeline"] for spec in NEEDS}
# Kept for readers of the earlier design-clock contract: Year 2's decision
# instants, keyed the way the v1.6 seed keyed them.
DECISION_TIMES = {
	(spec["reference"], "Accept for planning" if spec["state"] == STATE_ACCEPTED else "Submit"): spec["timeline"]["decide" if spec["state"] == STATE_ACCEPTED else "submit"]
	for spec in NEEDS
}


@contextmanager
def _as(user: str):
	"""Run a command as a real seeded actor, so `owner` and maker-checker hold."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _granted_units(user: str, business_role: str) -> dict[str, str]:
	"""`unit_name -> organisation_unit id`, over every Enabled grant of `business_role`."""
	ous = frappe.get_all(
		"User Responsibility Assignment",
		filters={"user": user, "business_role": business_role, "status": "Enabled"},
		pluck="organisation_unit",
	)
	return {
		frappe.db.get_value("Organisation Unit", ou, "unit_name"): ou for ou in ous if ou
	}


def _require_prerequisites() -> dict[str, str]:
	"""§14.1 — fail loudly rather than invent a Configuration & Governance record.

	Returns the author's granted `unit_name -> organisation_unit` map, since
	`_build_need` needs it and re-deriving it twice would be wasted queries.
	"""
	if not frappe.db.exists("User", AUTHOR):
		frappe.throw(
			"kentender_core.seeds.site_setup has not been run on this site. Run "
			"`bench --site <site> execute kentender_core.seeds.site_setup.run` "
			"first (NDS-CHG-001 v1.6 §14.1)."
		)
	for year in calendar.YEARS:
		if not frappe.db.exists("Fiscal Year", year.fiscal_year):
			frappe.throw(f"Fiscal Year {year.fiscal_year} is not configured. Run kentender_core.seeds.site_setup.run first (§14.1).")
	for unit in UNITS:
		if not frappe.db.get_value("UOM", unit, "enabled"):
			frappe.throw(f"UOM {unit!r} is not enabled. Run site_setup.run first (§14.1).")
	author_units = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)
	missing = [name for name in ("Digital Health", "Human Resources Management and Development") if name not in author_units]
	if missing:
		frappe.throw(
			f"{AUTHOR} holds no Enabled Departmental Author assignment for: {', '.join(missing)}. "
			"Run site_setup.run first (NDS-CHG-001 v1.6 §14.2)."
		)
	return author_units


def _build_need(spec: dict, author_units: dict[str, str], fiscal_year: str = FY) -> str:
	"""Drive a Need to its §14.3 state through the real §8.2 commands (§14.7).

	Idempotent by reference: a rerun finds the Need already built and returns it
	rather than driving `create_need` again, which would allocate the next free
	reference and duplicate the fixture.
	"""
	reference = spec["reference"]
	if frappe.db.exists("Departmental Need", reference):
		return reference

	when = spec["timeline"]
	with _as(AUTHOR), clock.at(when["create"]):
		created = lifecycle.create_need(
			organisation_unit=author_units[spec["unit_name"]],
			financial_year=fiscal_year,
			title=spec["title"],
			description=spec["description"],
			expected_operational_result=spec["expected_operational_result"],
			indicative_quantity=spec["indicative_quantity"],
			unit=spec["unit"],
			required_by_date=spec["required_by_date"],
			idempotency_key=f"nds-seed:{reference}:create",
		)
	need = created["need"]
	if need != reference:
		frappe.throw(
			f"Seed expected to generate {reference} but the command generated {need}. "
			"Clear the Departmental Needs fixtures before reseeding (§14.7)."
		)
	_namespace(need, created["current_revision"])

	if spec["state"] == STATE_DRAFT:
		_stamp_children(need)
		return need

	with _as(AUTHOR), clock.at(when["submit"]):
		submitted = lifecycle.submit_need(
			need=need,
			expected_version=created["record_version"],
			idempotency_key=f"nds-seed:{reference}:submit",
		)
	if spec["state"] == STATE_SUBMITTED:
		_stamp_children(need)
		return need

	if spec.get("corrected_quantity"):
		submitted = _return_and_correct(spec, submitted, when)

	decision = "accept" if spec["state"] == STATE_ACCEPTED else "return"
	task = _open_task(need)
	with _as(spec.get("reviewer", REVIEWER)), clock.at(when["decide"]):
		result = lifecycle.review_need(
			need=need,
			decision=decision,
			task=task.name,
			expected_version=submitted["record_version"],
			decision_token=task.decision_token,
			idempotency_key=f"nds-seed:{reference}:{decision}",
			reason=spec.get("return_reason", RETURN_REASON) if decision == "return" else "",
		)
	if result.get("successor_revision"):
		# §14.3 — Revision 2 is the server-created editable copy of the returned V1.
		_namespace(need, result["successor_revision"])
	_stamp_children(need)
	return need


def _open_task(need: str):
	return frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "status": "Open"},
		["name", "decision_token"],
		as_dict=True,
	)


def _return_and_correct(spec: dict, submitted: dict, when: dict) -> dict:
	"""§14.3 — the reviewer returns Revision 1 with the NDS-DES-04 reason; the
	author corrects the quantity on the server-created Revision 2 and
	resubmits it. Returns the resubmission, ready for the final decision."""
	need = spec["reference"]
	task = _open_task(need)
	with _as(spec.get("reviewer", REVIEWER)), clock.at(when["return"]):
		returned = lifecycle.review_need(
			need=need,
			decision="return",
			task=task.name,
			expected_version=submitted["record_version"],
			decision_token=task.decision_token,
			idempotency_key=f"nds-seed:{need}:return",
			reason=spec["return_reason"],
		)
	if returned.get("successor_revision"):
		_namespace(need, returned["successor_revision"])
	with _as(AUTHOR), clock.at(when["resubmit"]):
		lifecycle.update_need(
			need=need,
			title=spec["title"],
			description=spec["description"],
			expected_operational_result=spec["expected_operational_result"],
			indicative_quantity=spec["corrected_quantity"],
			unit=spec["unit"],
			required_by_date=spec["required_by_date"],
			expected_version=frappe.db.get_value("Departmental Need", need, "record_version"),
			idempotency_key=f"nds-seed:{need}:correct",
		)
		return lifecycle.submit_need(
			need=need,
			expected_version=frappe.db.get_value("Departmental Need", need, "record_version"),
			idempotency_key=f"nds-seed:{need}:resubmit",
		)


def _namespace(need: str, version: str = "") -> None:
	frappe.db.set_value("Departmental Need", need, "fixture_namespace", NS, update_modified=False)
	if version:
		frappe.db.set_value(
			"Departmental Need Revision", version, "fixture_namespace", NS, update_modified=False
		)


def _stamp_children(need: str) -> None:
	"""Namespace-stamp every Decision/Event/Review Task row the lifecycle
	commands above created for `need`, not just the Need and its Revisions —
	`purge_fixture_needs` filters every _NAMESPACED doctype by this field, so
	an unstamped Decision row survives a rebuild's purge as an orphan and
	then breaks the next create's idempotency replay (it finds the orphan
	but the Need it points at is already gone)."""
	from kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures import (
		_stamp_children as _stamp_children_impl,
	)

	_stamp_children_impl(need, namespace=NS)


def validate_needs_seed(year: str = "year2") -> list[dict]:
	"""One row per NDS-CHG-001 v1.14 §14.3 fact `year`'s Needs carry. Never
	mutates."""
	rows: list[dict] = []
	specs = need_specs(year)
	fiscal_year = _year(year).fiscal_year

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label, "detail": "" if ok else "failed"})

	needs = {n.name: n for n in frappe.get_all("Departmental Need", filters={"fixture_namespace": NS, "financial_year": fiscal_year}, fields=["name", "current_state", "organisation_unit", "current_accepted_revision", "owner"])}
	check(set(needs) == {spec["reference"] for spec in specs}, f"exactly the {len(specs)} canonical {_year(year).label} Needs exist (got {sorted(needs)})")
	for spec in specs:
		reference = spec["reference"]
		need = needs.get(reference)
		if not need:
			continue
		check(need.current_state == spec["state"], f"{reference} is {spec['state']} (got {need.current_state!r})")
		check(frappe.db.get_value("Organisation Unit", need.organisation_unit, "unit_name") == spec["unit_name"], f"{reference} belongs to {spec['unit_name']}")
		check(need.owner == AUTHOR, f"{reference} was created by {AUTHOR}")
		revisions = frappe.get_all(
			"Departmental Need Revision",
			filters={"departmental_need": reference},
			fields=["name", "revision_number", "indicative_quantity", "unit", "required_by_date"],
			order_by="revision_number asc",
		)
		final = revisions[-1] if revisions else None
		expected_revisions = 2 if spec.get("corrected_quantity") else 1
		check(len(revisions) == expected_revisions, f"{reference} has {expected_revisions} revision(s) (got {len(revisions)})")
		quantity = spec.get("corrected_quantity") or spec["indicative_quantity"]
		check(
			bool(final) and (float(final.indicative_quantity or 0), final.unit, str(final.required_by_date)) == (float(quantity), spec["unit"], spec["required_by_date"]),
			f"{reference}'s current revision asks for {quantity} {spec['unit']} by {spec['required_by_date']}",
		)
		if spec["state"] == STATE_ACCEPTED:
			check(bool(final) and need.current_accepted_revision == final.name, f"{reference} accepts revision {expected_revisions}")
		decisions = {
			d.action: d
			for d in frappe.get_all("Departmental Need Decision", filters={"departmental_need": reference}, fields=["action", "actor", "occurred_at", "reason"])
		}
		when = spec["timeline"]
		expected = [("Submit", AUTHOR, when["submit"])]
		if spec.get("corrected_quantity"):
			expected += [("Return for correction", REVIEWER, when["return"]), ("Resubmit", AUTHOR, when["resubmit"])]
		if spec["state"] == STATE_ACCEPTED:
			expected.append(("Accept for planning", spec.get("reviewer", REVIEWER), when["decide"]))
		for action, actor, at in expected:
			decision = decisions.get(action)
			check(bool(decision) and decision.actor == actor and str(decision.occurred_at)[:19] == at, f"{reference}: {action} by {actor} at {at}")
		if spec.get("corrected_quantity"):
			check(decisions.get("Return for correction") and decisions["Return for correction"].reason == spec["return_reason"], f"{reference} is returned with its reason")
	return rows


def _open_intake(year: str):
	"""The year's Needs intake, opened at its documented instant with its close
	instant (CFG-BR-006: opening it closes any other open year). The site
	stage reopens Year 2's afterwards (`site_setup._seed_intake`)."""
	from kentender_core.services import site_configuration as configuration

	y = _year(year)
	with clock.at(y.at(_INTAKE["open"])):
		configuration.open_needs_submission(
			fiscal_year=y.fiscal_year, closes_at=y.at(_INTAKE["closes"]),
			reason=f"Annual needs call for {y.label} issued under circular MOH/PROC/{y.start_year - 1}/07.",
		)


def upsert_departmental_needs(*, commit: bool = False, years: tuple[str, ...] = ("year1", "year2")) -> dict[str, list[str]]:
	"""Idempotent §14.3 Needs of each seeded year, built through the real
	commands (§14.7). A year with Needs still to build has its intake opened
	at its documented instant first, so each command meets the open intake
	it requires (NDS-BR-002); a year already built is left untouched."""
	from kentender_core.seeds import site_setup

	author_units = _require_prerequisites()
	created: dict[str, list[str]] = {}
	for year in years:
		specs = need_specs(year)
		if not all(frappe.db.exists("Departmental Need", spec["reference"]) for spec in specs):
			_open_intake(year)
		created[year] = [_build_need(spec, author_units, _year(year).fiscal_year) for spec in specs]
	# Year 2's intake is the one the site keeps open (until its close instant).
	site_setup._seed_intake()
	if commit:
		frappe.db.commit()
	return {"needs": created}
