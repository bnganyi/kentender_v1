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
from kentender_procurement.departmental_needs.services import lifecycle

FY = "2027-2028"
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

# §14.3 default Needs. Version status follows the root state. `unit_name` is
# resolved against the author's real granted Organisation Units at build time.
NEEDS = (
	{
		"reference": "NDS-MOH-2027-0001",
		"unit_name": "Digital Health",
		"title": "National digital health infrastructure upgrade",
		"description": "Procure and implement national digital health infrastructure across priority health facilities.",
		"expected_operational_result": "Priority health facilities can use secure and interoperable digital health services.",
		"indicative_quantity": 1,
		"unit": "Programme",
		"required_by_date": "2027-08-31",
		"state": STATE_ACCEPTED,
	},
	{
		"reference": "NDS-MOH-2027-0002",
		"unit_name": "Human Resources Management and Development",
		"title": "Digital health workforce certification programme",
		"description": "Professional certification programme for staff supporting national digital health services.",
		"expected_operational_result": "Build internal capacity to operate and support national digital health platforms.",
		"indicative_quantity": 1,
		"unit": "Programme",
		"required_by_date": "2027-12-31",
		"state": STATE_SUBMITTED,
	},
	{
		# SEED-001 §3.2 (2026-09-05): corrected from 200/Returned — this and
		# NDS-MOH-2027-0004 below are the two source Needs the harmonized
		# combined Plan Item PPI-MOH-2027-033 draws from (PLN-CHG-001 v1.13
		# §14.5), so both must reach Accepted, not sit in Returned/Draft.
		"reference": "NDS-MOH-2027-0003",
		"unit_name": "Human Resources Management and Development",
		"title": "Clinical training laptops for digital health rollout",
		"description": "Laptop computers for clinical training during the national digital health rollout.",
		"expected_operational_result": "Provide the equipment required for staff training on the deployed digital health services.",
		"indicative_quantity": 100,
		"unit": "Each",
		"required_by_date": "2027-12-31",
		"state": STATE_ACCEPTED,
	},
	{
		# SEED-001 §3.2 (2026-09-05): corrected from 300/Draft. Accepted by
		# Julia Njeri (Acting Head of User Department, Digital Health), not
		# Peter — the same segregation the shared register already models.
		"reference": "NDS-MOH-2027-0004",
		"unit_name": "Digital Health",
		"title": "Clinical deployment laptops for digital health rollout",
		"description": "Laptop computers for deployment at priority facilities during the national digital health rollout.",
		"expected_operational_result": "Provide endpoint equipment required to use the deployed digital health services.",
		"indicative_quantity": 150,
		"unit": "Each",
		"required_by_date": "2027-12-31",
		"state": STATE_ACCEPTED,
		"reviewer": ACTING_REVIEWER,
	},
)

RETURN_REASON = (
	"Confirm the number of trainees to be supported and revise the laptop quantity "
	"if the approved training cohort has changed."
)

# §14.3 design-clock decision times (EAT), applied after the commands run.
# SEED-001 §3.2 (2026-09-05): 0003/0004 accept at the harmonized chain's own
# instants, replacing 0003's former "Return for correction" entry.
DECISION_TIMES = {
	("NDS-MOH-2027-0001", "Accept for planning"): "2026-11-24 14:00:00",
	("NDS-MOH-2027-0002", "Submit"): "2026-11-24 12:20:00",
	("NDS-MOH-2027-0003", "Accept for planning"): "2026-11-25 10:00:00",
	("NDS-MOH-2027-0004", "Accept for planning"): "2026-11-25 09:30:00",
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
	if not frappe.db.get_value("Fiscal Year", FY, "kentender_needs_submission_open"):
		frappe.throw(
			f"Fiscal Year {FY}'s Needs-submission flag is not Open. Run "
			"kentender_core.seeds.site_setup.run, or "
			"kentender_core.services.site_configuration.open_needs_submission "
			f"directly, first (§14.1)."
		)
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


def _build_need(spec: dict, author_units: dict[str, str]) -> str:
	"""Drive a Need to its §14.3 state through the real §8.2 commands (§14.7).

	Idempotent by reference: a rerun finds the Need already built and returns it
	rather than driving `create_need` again, which would allocate the next free
	reference and duplicate the fixture.
	"""
	reference = spec["reference"]
	if frappe.db.exists("Departmental Need", reference):
		return reference

	with _as(AUTHOR):
		created = lifecycle.create_need(
			organisation_unit=author_units[spec["unit_name"]],
			financial_year=FY,
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
	_namespace(need, created["current_version"])

	if spec["state"] == STATE_DRAFT:
		return need

	with _as(AUTHOR):
		submitted = lifecycle.submit_need(
			need=need,
			expected_version=created["record_version"],
			idempotency_key=f"nds-seed:{reference}:submit",
		)
	if spec["state"] == STATE_SUBMITTED:
		return need

	decision = "accept" if spec["state"] == STATE_ACCEPTED else "return"
	task = frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "status": "Open"},
		["name", "decision_token"],
		as_dict=True,
	)
	with _as(spec.get("reviewer", REVIEWER)):
		result = lifecycle.review_need(
			need=need,
			decision=decision,
			task=task.name,
			expected_version=submitted["record_version"],
			decision_token=task.decision_token,
			idempotency_key=f"nds-seed:{reference}:{decision}",
			reason=RETURN_REASON if decision == "return" else "",
		)
	if result.get("successor_version"):
		# §14.3 — Version 2 is the server-created editable copy of the returned V1.
		_namespace(need, result["successor_version"])
	return need


def _namespace(need: str, version: str = "") -> None:
	frappe.db.set_value("Departmental Need", need, "fixture_namespace", NS, update_modified=False)
	if version:
		frappe.db.set_value(
			"Departmental Need Version", version, "fixture_namespace", NS, update_modified=False
		)


def _stamp_design_clock() -> None:
	"""§14.3 fixes exact decision times; the commands stamp the wall clock."""
	for (need, action), when in DECISION_TIMES.items():
		name = frappe.db.get_value(
			"Departmental Need Decision",
			{"departmental_need": need, "action": action},
			"name",
			order_by="creation desc",
		)
		if name:
			frappe.db.set_value(
				"Departmental Need Decision", name, "occurred_at", when, update_modified=False
			)


def upsert_departmental_needs(*, commit: bool = False) -> dict[str, list[str]]:
	"""Idempotent §14.3 default profile, built through the real commands (§14.7).

	The Needs-submission flag is a durable, Configuration-&-Governance-owned
	toggle now (§4.1) — unlike the old per-PE/FY `Needs Intake Window`, there is
	no transient open/close dance around the build: the seed simply requires
	the flag already Open (§14.1) and fails loudly if it is not.
	"""
	author_units = _require_prerequisites()
	created = [_build_need(spec, author_units) for spec in NEEDS]
	_stamp_design_clock()
	if commit:
		frappe.db.commit()
	return {"needs": created}
