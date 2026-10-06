# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §14 — the deterministic Planning seed (Phase 7 of the
v1.12 cycle, tracker PLN-701..703).

The integrated §14.4–14.6 baseline is driven through the real §8.2 commands
with the named §14.2 role actors (never Administrator for a business
decision), then the §14 design-clock instants are stamped onto the evidence
rows the commands produced. Isolated profiles (§14.10) each rebuild the
Planning world for FY 2027/28 to their own state and are mutually exclusive
with the integrated baseline.

One site = one Procuring Entity (AUTH-ADR-001 v1.6): there is no PE, PE
context, submission-window doctype or framework permission row anywhere in this seed.
Authority is the shared KT-STD-001 §8.3 register seeded by
`kentender_core.seeds.site_setup` (Grace, Peter, Julia, Mercy, Josphat,
Naomi, Samuel); this seed adds only the two actors §14.2 introduces — Amina
Hassan (Accounting Officer) and Daniel Rotich (statutory approver) — through
`responsibility_administration.grant`. Departmental-plan intake is the
Fiscal Year flag CFG-CHG-002 v0.9 §4.2 defines (site_setup seeds it on
2027-2028, closing 30 Nov 2026, 23:59 EAT).

Identifier note (the NDS-seed precedent): Organisation Units are resolved
from the actors' real granted assignments by unit name — server-generated
references embed the live unit code, so `DPP-MOH-DHI-2027-001` in §14.4
reads `DPP-MOH-<live code>-2027-001` on a site, and sequence-scanned
identifiers start at the first free number. Stable identifiers (Need, Plan
root, actor emails, Budget Line references, amounts, dates, titles) match
§14 exactly.

§14.5's illustrative milestone dates imply a 31-day evaluation period, above
the governed 30-day ceiling (§4.9, PLN-AC-114); the seed derives its baseline
from the governed defaults PLN-DES-09 shows (21 / 30 / 5 / 2 / 14 days from
1 May 2027) and the deviation is recorded in FOLLOW_UPS (FU-08).

§14.9 (KEBS ×2) is retired, not fixed — see the note beside the deleted
`seed_combined_profile`/`seed_kebs_profiles` functions below (SEED-001 §1.1).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime
from frappe.utils.password import update_password

from kentender_core.seeds import calendar, clock
from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_core.services import responsibility_administration as administration
from kentender_core.services import site_configuration

PLAYWRIGHT_NS = "KENTENDER_PLAYWRIGHT"
NS = "KENTENDER_MVP_1_R1_PLN"

# PLN-CHG-001 v1.23 §13 — nothing seeded may claim `Verified`. The canonical
# world registers its method and schedule profiles as
# `Fixture-verified — not production law`, which is what the submission gate
# admits and what every screen showing a rule must display. Leaving them at
# `Production verification pending` (the site default, and the right default
# for a real site) makes the canonical Plan permanently unsubmittable.
VERIFICATION_FIXTURE = "Fixture-verified — not production law"
# §10.2's own schedule arithmetic: tendering 21, evaluation 30 (maximum),
# award buffer 5, notification 2, standstill 14 (minimum).
PROFILE_LIMITS = {"bid_opening": (7, None), "evaluation_completion": (None, 30), "contract_signing": (14, None)}
# The mandatory planning allocation: 30% of what the plan actually plans to
# procure. This world plans KES 130m (KES 80m infrastructure, designated None,
# plus the KES 50m combined laptop package, designated Youth), so KES 39m is
# required and the KES 50m qualifying package clears it. The KES 160m approved
# budget is the ceiling the plan fits inside, not the measure of this
# obligation (corrected 24 Sep 2026 — see
# `docs/mvp-1-r1/99_other/thirty_percent_reservation_rule.pdf`).
RESERVATION_TARGET_PERCENT = 30

#: The executed Annual Plan's year (two-year seed world: Year 1, FY 2026/27):
#: the plan the Requisitions and later stages consume.
FY = calendar.YEAR1.fiscal_year
#: The isolated profiles (§14.10) rebuild a Planning world on the prepared
#: year (Year 2, FY 2027/28), mutually exclusive with the canonical plans.
PROFILE_FY = calendar.YEAR2.fiscal_year
DHI_NAME = "Digital Health"  # spec: OU-MOH-DHI
HRMD_NAME = "Human Resources Management and Development"  # spec: OU-MOH-HRMD

#: The profiles' accepted Digital Health Need (Year 2's first).
NEED = "NDS-MOH-2027-0001"
# SEED-001 §3.2/§3.6, PLN-CHG-001 v1.13 §14.5 (2026-09-05) — the harmonized
# combined item's two real, Need-backed sources, now Year 1's (two-year seed
# world plan D8). Both Needs are Accepted by
# `departmental_needs.seeds.kentender_mvp_r1` before this seed runs.
NEED_HRMD_LAPTOPS = "NDS-MOH-2026-0002"
NEED_DHI_LAPTOPS = "NDS-MOH-2026-0003"
OBJECTIVE_TITLE = "Strengthen interoperable national digital health services"
DESTINATION_ID = "MOH-APP-SANDBOX-v1"

AUTHOR = "grace.wanjiku@moh.example.test"
HOD = "peter.kimani@moh.example.test"
ACTING_HOD = "julia.njeri@moh.example.test"
PLANNER = "mercy.kilonzo@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"  # v1.18 §6.2 / §13.1: signs and submits (assigned by site_setup)
FINANCE = "josphat.mwangi@moh.example.test"
ACCOUNTING_OFFICER = "amina.hassan@moh.example.test"
STATUTORY = "daniel.rotich@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"
NO_AUTHORITY = "samuel.otieno@moh.example.test"

# §14.2 — the two actors this document adds to the shared register.
PLANNING_ACTORS = (
	(ACCOUNTING_OFFICER, "Amina Hassan", "Accounting Officer"),
	(STATUTORY, "Daniel Rotich", "Plan Statutory Approver"),
)

UNITS = ("Programme", "Each", "Service Month")

# §14.5 package text with the governed baseline inputs (see module docstring).
ITEM_VALUES = {
	"title": "National digital health infrastructure upgrade",
	"description": (
		"Procure and implement the national digital health infrastructure "
		"upgrade as one integrated FY 2027/28 programme."
	),
	"plan_horizon": "Single year",
	"aggregation_indicator": "Not aggregated",
	"lotting_indicator": "Single lot",
	"reservation_category": "None",
	"procurement_method": "Open Tender",
	"baseline_invitation_date": "2027-05-01",
	# PLN-CHG-001 v1.18 §4.6 — estimate basis and the estimated delivery
	# period; v1.27 §10.2 gives the basis text and reference word for word
	# (until 26 Sep 2026 the seed carried an invented survey and reference).
	"estimate_basis": "Market survey estimate includes delivery, installation where applicable and other identified incidental costs.",
	"estimate_basis_reference": "Market survey working paper",
	"estimated_delivery_period_days": 30,
	"tendering_period_days": 21,
	"evaluation_period_days": 30,
	"award_approval_buffer_days": 5,
	"notification_buffer_days": 2,
	"standstill_period_days": 14,
}

# §14.7 isolated direct-requirement fixture (the mixed-DPP proof: the
# accepted Need plus one direct entry in the same Digital Health plan).
DIRECT_FIXTURE = {
	"title": "Digital health platform security assessment",
	"description": (
		"Assess the security of the national digital health platform and "
		"provide a prioritised remediation report."
	),
	"expected_operational_result": (
		"The Ministry receives a prioritised and actionable security remediation plan."
	),
	"quantity": 1,
	"unit": "Service Month",
	"required_by_date": "2027-10-31",
	"indicative_amount": 20000000,
}

# PLN-CHG-001 v1.13 §14.5 — the combined item's two real Need-backed
# fundings. KES 50,000,000 combined over 250 Each with no per-line amount
# stated in either SEED-001 or §14.5; split by quantity share at a uniform
# per-unit price (both departments draw "one standard laptop specification"),
# which is the only value consistent with both the stated total and the
# stated 100/150 quantities: KES 200,000 per unit.
COMBINED_TOTAL_AMOUNT = 50_000_000
NEED_HRMD_LAPTOPS_AMOUNT = 20_000_000  # 100 each
NEED_DHI_LAPTOPS_AMOUNT = 30_000_000  # 150 each

COMBINED_ITEM_VALUES = {
	**ITEM_VALUES,
	"title": "Clinical training and deployment laptops for digital health rollout",
	"description": (
		"Procure and deploy one common laptop specification for clinical training "
		"and field digital-health deployment across two departments."
	),
	"aggregation_reason": (
		"Both departments require the same laptop specification for the same "
		"national digital-health rollout; combining secures better unit pricing "
		"and one delivery schedule."
	),
	"aggregation_indicator": "Aggregated into this package",
	# §13 / D9 — the canonical world must reach Active because the
	# Requisitions and Tender Preparation seed stages consume it. Its
	# qualifying designation is what satisfies the mandatory planning
	# allocation; §10.2's BASE None/None shortfall is a UI fixture, not this
	# world. This is a fixture designation, not verified category eligibility.
	"reservation_category": "Youth",
	# §14.5 — "using the same governed periods as PPI-MOH-2027-021," a
	# fortnight-later invitation date; every other *_period_days field is
	# inherited from ITEM_VALUES above unchanged.
	"baseline_invitation_date": "2027-05-15",
	# v1.27 §10.2 / SEED-001 v1.3 §3.6: laptops 60 calendar days, estimated
	# completion 24 Sep 2027 (the seed inherited the infrastructure item's 30
	# until 26 Sep 2026).
	"estimated_delivery_period_days": 60,
}

TREASURY_EVIDENCE_FILE = "Treasury-dispatch-evidence-example.pdf"

# §14.4–14.6 design-clock instants, stored in the site timezone like every
# other instant (owner decision 26 Sep 2026, FU-V127-01; they were UTC
# equivalents while Planning's reads converted from UTC).
#: v1.27 §10.2 / SEED-001 v1.3 §3.3 give each department its own instants;
#: until 26 Sep 2026 both departmental plans shared one submission (10:00)
#: and one acceptance (14:00), and the Head of Procurement Function's
#: signature carried 5 Dec instead of 7 Dec.
CLOCK = {
	"dpp_submitted_dhi": "2026-11-25 10:30:00",
	"dpp_submitted_hrmd": "2026-11-25 11:00:00",
	"dpp_accepted_dhi": "2026-11-27 14:00:00",
	"dpp_accepted_hrmd": "2026-11-27 14:05:00",
	"finance_confirmed": "2026-12-04 10:00:00",
	"plan_submitted": "2026-12-07 10:00:00",
	"ao_adopted": "2026-12-08 10:00:00",
	"statutory_approved": "2026-12-09 11:00:00",
	"publication_attempted": "2026-12-10 14:55:00",
	"publication_acknowledged": "2026-12-10 15:00:00",
	"treasury_submitted": "2026-12-10 14:00:00",  # §10.12
}
#: The UTC values CLOCK held before 26 Sep 2026 — the one-off patch that
#: moves already-seeded rows to site time matches these exactly.
CLOCK_BEFORE_SITE_TIME = {
	"dpp_submitted": "2026-11-25 07:00:00",
	"dpp_accepted": "2026-11-27 11:00:00",
	"finance_confirmed": "2026-12-04 07:00:00",
	"plan_submitted": "2026-12-05 07:00:00",
	"ao_adopted": "2026-12-08 07:00:00",
	"statutory_approved": "2026-12-09 08:00:00",
	"publication_attempted": "2026-12-10 11:55:00",
	"publication_acknowledged": "2026-12-10 12:00:00",
	"treasury_submitted": "2026-12-10 11:00:00",
}

# --- the two-year seed world (owner, 4 Oct 2026; plan D1, D8, D10) ---------
#
# Each seeded year's departmental plans and Annual Plan, built through the
# same commands from data. Year 2 (FY 2027/28, being prepared) runs at the
# §14.4–14.6 instants above; Year 1 (FY 2026/27, carried out) runs the same
# journey 364 days earlier (`calendar.YEAR1`), so its Plan is Active from
# 11 Dec 2025, before the year it plans for begins.
#
# A year's planned dates fit inside that year (two-year seed world
# corrections §1): Needs and direct requirements are required by 30 Jun 2027
# at the latest in Year 1, and each item's baseline invitation leaves its
# signing plus delivery inside that boundary (PLN_DELIVERY_BOUNDARY_INSUFFICIENT
# otherwise). Year 1's Tenders then publish later than their approved dates,
# which Planning reads as Baseline lateness.

#: Steps the §14 clock leaves unstated, at instants between their neighbours.
_YEAR2_STEPS = {
	**CLOCK,
	"dpp_opened_dhi": "2026-11-25 09:50:00",
	"dpp_opened_hrmd": "2026-11-25 10:40:00",
	"items_formed": "2026-12-01 10:00:00",
	"funding_requested": "2026-12-03 10:00:00",
}


def year_clock(year: str) -> dict[str, str]:
	y = calendar.year(year)
	return {step: y.at(at) for step, at in _YEAR2_STEPS.items()}


def _item(title: str, description: str, invitation: str, delivery_days: int, *, designation: str = "None", **extra: Any) -> dict[str, Any]:
	return {
		**ITEM_VALUES, "title": title, "description": description, "reservation_category": designation,
		"baseline_invitation_date": invitation, "estimated_delivery_period_days": delivery_days, **extra,
	}


def _direct(source: str, title: str, purpose: str, quantity: int, amount: int, line: str, *, required_by: str = "2027-06-30") -> dict[str, Any]:
	"""A direct departmental requirement (no Need behind it): IT equipment the
	executed portfolio's Requisitions draw on (two-year seed world proposal §5;
	the only installed Tender format is IT equipment, so each one is)."""
	return {
		"source": source, "line": line, "amount": amount, "classification": "Goods",
		"values": {
			"title": title, "description": f"{title} for {purpose}.",
			"expected_operational_result": f"Staff have working {title.lower()} for {purpose}.",
			"quantity": quantity, "unit": "Each", "required_by_date": required_by, "indicative_amount": amount,
		},
	}


_YEAR1_DESCRIPTION = "Procure and implement the national digital health infrastructure upgrade as one integrated FY 2026/27 programme."

#: Year 1's portfolio of IT equipment, beside the two SEED-001 items: one
#: departmental requirement and Plan Item per Tender or Requisition of the
#: executed portfolio (two-year seed world proposal §5.1–§5.2; titles from the
#: HOME-CHG-001 v0.6 / ANL-CHG-001 v0.8 fixtures where they are IT equipment,
#: IT substitutes where they are not). (source key, item title, department
#: key, purpose, quantity, KES, budget line, invitation, delivery days,
#: designation)
PORTFOLIO = (
	("printers", "Printers", "dhi", "Digital Health offices", 40, 5_000_000, "dhi", "2027-02-15", 30, "None"),
	("lab_desktops", "Laboratory desktop computers", "dhi", "hospital laboratory systems", 60, 9_000_000, "ict", "2027-02-22", 30, "None"),
	("tablets", "Medical-grade tablets", "dhi", "clinical teams at priority facilities", 100, 6_000_000, "dhi", "2027-03-15", 21, "None"),
	("field_laptops", "Field laptops", "dhi", "county digital health officers", 50, 7_000_000, "dhi", "2027-03-01", 30, "None"),
	("routers", "Core network routers", "dhi", "the national digital health data centre", 10, 25_000_000, "ict", "2027-02-01", 60, "Women"),
	("clinic_desktops", "Clinic desktop computers", "dhi", "outpatient clinics", 80, 12_000_000, "dhi", "2027-03-15", 21, "None"),
	("scanners", "Document scanners", "hrmd", "staff records digitisation", 25, 3_500_000, "hrmd", "2027-03-01", 21, "None"),
	("switches", "Network switches", "hrmd", "the training centres' networks", 30, 9_000_000, "ict", "2027-02-08", 45, "None"),
	("ups", "UPS units", "hrmd", "power protection in training centres", 40, 4_000_000, "ict", "2027-03-08", 21, "None"),
	("desktops", "Desktop computers", "hrmd", "human resources offices", 80, 12_000_000, "hrmd", "2027-02-22", 30, "None"),
	("monitors", "Monitors", "hrmd", "human resources offices", 150, 7_500_000, "hrmd", "2027-03-01", 21, "None"),
)
#: The one portfolio item both departments contribute to (ANL-CHG-001 v0.8
#: A1's "IT peripherals" shape, as equipment the Tender format supports): one
#: combined item from two direct requirements.
PERIPHERALS = {
	"title": "Wireless access points",
	"dhi": ("peripherals_dhi", 80, 4_000_000),
	"hrmd": ("peripherals_hrmd", 50, 2_500_000),
	"line": "ict", "invitation": "2027-02-15", "delivery_days": 30,
	"reason": "Both departments need the same wireless access points for the digital health rollout; one package secures one price and one delivery.",
}


def _portfolio_direct(department: str) -> list[dict[str, Any]]:
	rows = [_direct(key, title, purpose, quantity, amount, line) for key, title, dept, purpose, quantity, amount, line, *_ in PORTFOLIO if dept == department]
	key, quantity, amount = PERIPHERALS[department]
	rows.append(_direct(key, PERIPHERALS["title"], "the digital health rollout", quantity, amount, PERIPHERALS["line"]))
	return rows


def _portfolio_items() -> list[dict[str, Any]]:
	items = [
		{"sources": (key,), "values": _item(title, f"{title} for {purpose}.", invitation, days, designation=designation)}
		for key, title, _dept, purpose, _quantity, _amount, _line, invitation, days, designation in PORTFOLIO
	]
	items.append({
		"sources": (PERIPHERALS["dhi"][0], PERIPHERALS["hrmd"][0]), "mode": "combined",
		"values": _item(
			PERIPHERALS["title"], "Common wireless access points for Digital Health and Human Resources Management and Development offices.",
			PERIPHERALS["invitation"], PERIPHERALS["delivery_days"],
			aggregation_indicator="Aggregated into this package", aggregation_reason=PERIPHERALS["reason"],
		),
	})
	return items


def plan_spec(year: str) -> dict[str, Any]:
	"""`year`'s departmental plans, Plan Items and Treasury reference. Need
	sources name the Need by its position in the Needs seed's list for that
	year (`departmental_needs.seeds.kentender_mvp_r1.references`)."""
	from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import references

	needs = references(year)
	if year == "year1":
		return {
			"dpps": (
				{
					"key": "dhi", "unit": DHI_NAME, "submitter": ACTING_HOD,
					"needs": (
						{"source": "infra", "need": needs[0], "line": "dhi", "amount": 80_000_000, "classification": "Non-consulting services"},
						{"source": "laptops_dhi", "need": needs[2], "line": "hwd", "amount": NEED_DHI_LAPTOPS_AMOUNT, "classification": "Goods"},
					),
					"direct": _portfolio_direct("dhi"),
				},
				{
					"key": "hrmd", "unit": HRMD_NAME, "submitter": HOD,
					"needs": ({"source": "laptops_hrmd", "need": needs[1], "line": "hwd", "amount": NEED_HRMD_LAPTOPS_AMOUNT, "classification": "Goods"},),
					"direct": _portfolio_direct("hrmd"),
				},
			),
			"items": (
				# SEED-001 §3.6 / §5.2 with the two-year corrections: baselines
				# moved so signing plus delivery ends by 30 Jun 2027.
				{"sources": ("infra",), "values": {**ITEM_VALUES, "description": _YEAR1_DESCRIPTION, "baseline_invitation_date": "2027-03-01"}},
				{
					"sources": ("laptops_hrmd", "laptops_dhi"), "mode": "combined",
					"values": {**COMBINED_ITEM_VALUES, "baseline_invitation_date": "2027-02-01"},
				},
				*_portfolio_items(),
			),
			"treasury_reference": "MOH/APP/2026/001",
		}
	return {
		"dpps": (
			{
				"key": "dhi", "unit": DHI_NAME, "submitter": HOD,
				"needs": (
					{"source": "hie", "need": needs[0], "line": "dhi", "amount": 70_000_000, "classification": "Non-consulting services"},
					{"source": "cds", "need": needs[3], "line": "hwd", "amount": 20_000_000, "classification": "Goods"},
				),
				"direct": (),
			},
			{
				"key": "hrmd", "unit": HRMD_NAME, "submitter": HOD,
				"needs": ({"source": "av", "need": needs[2], "line": "hwd", "amount": 12_000_000, "classification": "Goods"},),
				"direct": (),
			},
		),
		"items": (
			{"sources": ("hie",), "values": _item(
				"Health information exchange platform upgrade",
				"Upgrade the national health information exchange platform as one FY 2027/28 programme.", "2027-05-03", 30,
			)},
			{"sources": ("av",), "values": _item(
				"Training centre audio-visual equipment", "Projectors, displays and sound equipment for the staff training centres.",
				"2027-08-02", 45, designation="Women",
			)},
			{"sources": ("cds",), "values": _item(
				"Clinical decision-support software licences", "Decision-support software licences for clinicians at priority facilities.",
				"2027-07-15", 60, designation="Youth",
			)},
		),
		"treasury_reference": "MOH/APP/2027/001",
	}


_DOCTYPES = (
	# dependents first, roots last
	# PLN v1.27 / owner decision 26 Sep 2026 — the over-budget hand-offs
	# (a budget revision request's Budget side goes with its Budget).
	"Plan Budget Revision Request",
	"Departmental Plan Update Request",
	"Plan Drawdown Reference",
	# PLN-CHG-001 v1.18 §5.5.2 publication chain. These were absent from the
	# purge, so a reset left the previous run's Approved Plan Snapshot behind
	# and the next approval reused it — including its older content shape,
	# which then failed the public-payload build with a bare KeyError.
	"Publication Acknowledgement",
	"Publication Attempt",
	"Publication Intent",
	"Plan Publication Hold",
	"Plan Publication",
	"Treasury Submission Evidence",
	"Late Activation Explanation",
	"Approved Plan Snapshot",
	"Plan Preparation Signature",
	"Plan Financial Basis",
	"Plan Finance Basis Reuse",
	"Milestone Actual Event",
	"Proceeding Coverage",
	"Annual Plan Publication",
	"Plan Governance Decision",
	"Plan Governance Task",
	"Plan Finance Decision",
	"Plan Finance Task",
	"Plan Source Allocation",
	"Annual Plan Item",
	"Plan Item Correction Disposition",
	"Plan Item Correction Request",
	"Plan Item",
	"Annual Plan Version",
	"Annual Plan",
	"DPP Classification Correction",
	"Departmental Plan Validation Decision",
	"Departmental Plan Validation Task",
	"Departmental Plan Submission",
	"Departmental Plan Entry",
	"Departmental Plan Version",
	"Departmental Plan",
	"Annual Plan Publication Destination",
)


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _key(step: str) -> str:
	return f"pln-seed:{step}"


# --- §14.1/§14.3 prerequisite verification (fail loudly, invent nothing) ----


def _objective() -> str:
	return cstr(frappe.db.get_value("Strategy Node", {"title": OBJECTIVE_TITLE, "node_type": "Strategic Objective"}, "name"))


def _unit_for(user: str, role: str, unit_name: str) -> str:
	"""The Organisation Unit named `unit_name` the actor really holds `role`
	in — the register is authoritative, never a name lookup alone."""
	for unit in frappe.get_all(
		"User Responsibility Assignment", filters={"user": user, "business_role": role, "status": "Enabled"}, pluck="organisation_unit",
	):
		if unit and frappe.db.get_value("Organisation Unit", unit, "unit_name") == unit_name:
			return unit
	return ""


def ensure_profiles() -> dict[str, Any]:
	"""Register the fixture-verified method and schedule profiles for the
	canonical Fiscal Year, through the same seeder a real site uses.

	Idempotent: `_seed_*_profiles` skip a profile that already exists for the
	same effective window, so a rerun registers nothing new.
	"""
	from kentender_core.seeds import site_setup
	from kentender_core.services import procurement_settings as settings

	# §10.2 anchors the canonical schedules at 1 May and 15 May 2027 while
	# FY 2027/28 begins on 1 July 2027, so a profile window starting at the
	# financial year would not cover the plan's own applicable dates and no
	# rule would resolve. This is the recorded applicability-date/fixture
	# conflict (§17.2, CFG-XD-001) — the fixture's dates are what the
	# specification fixes, so the configuration window is widened to cover
	# them rather than relaxing the resolver or back-dating the plan. A
	# profile's effective window is configuration; the rule it carries is
	# not weakened, and nothing is marked Verified.
	#
	# That window is now `site_setup.PROFILE_EFFECTIVE` itself rather than a
	# second one computed here. The two disagreed (1 Jan 2027 here, 1 May
	# 2027 there), so whichever stage ran last superseded the other's rows —
	# and seeding through this stage narrowed what the site stage had just
	# widened. One window, owned by the seed that defines the rules.
	window = dict(site_setup.PROFILE_EFFECTIVE)
	methods = site_setup._seed_method_profiles(
		effective=window, verification_status=VERIFICATION_FIXTURE, fixture_namespace=NS,
	)
	schedules = site_setup._seed_schedule_profiles(
		effective=window, verification_status=VERIFICATION_FIXTURE, fixture_namespace=NS,
		limits=PROFILE_LIMITS, estimated_delivery_default_days=30,
	)
	# The seeders skip a profile that already covers this window, so a site
	# that was set up before this seed existed keeps whatever status it was
	# given — on this canonical world, `Production verification pending`,
	# which blocks Sign and submit forever. Stamp those rows to the fixture
	# status. This is the seed correcting its own fixture rules; it never
	# writes `Verified`, and a profile outside this window is untouched.
	site_setup._seed_regulatory_reference(
		fiscal_year=FY,
		fixture_namespace=NS,
		verification_status=VERIFICATION_FIXTURE,
		reservation_target_percent=RESERVATION_TARGET_PERCENT,
		effective=window,
	)
	# CFG-CHG-002 Phase 2c — the remaining four rule kinds get the same
	# fixture-verified treatment as Method eligibility/Reservation rules
	# above, so a canonical world seeded through this stage has all seven
	# "Procurement rules" kinds usable, not just the first three.
	site_setup._seed_exclusive_preference(effective=window, fixture_namespace=NS, verification_status=VERIFICATION_FIXTURE)
	site_setup._seed_preference_margins(effective=window, fixture_namespace=NS, verification_status=VERIFICATION_FIXTURE)
	site_setup._seed_market_price_index(effective=window, fixture_namespace=NS, verification_status=VERIFICATION_FIXTURE)
	site_setup._seed_approval_applicability(effective=window, fixture_namespace=NS, verification_status=VERIFICATION_FIXTURE)
	stamped = 0
	for doctype in (settings.METHOD_PROFILE, settings.SCHEDULE_PROFILE, "Regulatory Reference"):
		for name in frappe.get_all(
			doctype,
			filters={"status": "Active", "verification_status": ("!=", VERIFICATION_FIXTURE)},
			pluck="name",
		):
			frappe.db.set_value(doctype, name, "verification_status", VERIFICATION_FIXTURE, update_modified=False)
			stamped += 1
	return {"method_profiles": methods, "schedule_profiles": schedules, "stamped_fixture_verified": stamped}


def verify_prerequisites() -> dict[str, str]:
	"""§14.1/§14.3 for the isolated profiles' year (`PROFILE_FY`, Year 2) —
	every authoritative prerequisite present and usable, or one loud failure
	naming exactly what is absent. Nothing is invented. The canonical years
	use `_verify_year`."""
	FY = PROFILE_FY
	missing: list[str] = []

	def need(label: str, ok) -> None:
		if not ok:
			missing.append(label)

	need("configured site (System setup)", site_configuration.is_configured())
	need(f"Fiscal Year {FY}", frappe.db.exists("Fiscal Year", FY))
	need("Site Procuring Entity statutory_approval_route", cstr(frappe.db.get_single_value("Site Procuring Entity", "statutory_approval_route")))
	dhi = _unit_for(AUTHOR, "Departmental Author", DHI_NAME)
	hrmd = _unit_for(AUTHOR, "Departmental Author", HRMD_NAME)
	need(f"Grace's Departmental Author assignment in '{DHI_NAME}' (spec OU-MOH-DHI)", dhi)
	need(f"Grace's Departmental Author assignment in '{HRMD_NAME}' (spec OU-MOH-HRMD)", hrmd)
	need(f"Peter's Head of User Department assignment in '{DHI_NAME}'", _unit_for(HOD, "Head of User Department", DHI_NAME))
	need(f"Peter's Head of User Department assignment in '{HRMD_NAME}'", _unit_for(HOD, "Head of User Department", HRMD_NAME))
	for actor, role in ((PLANNER, "Procurement Planner"), (FINANCE, "Finance Confirmation Officer"), (AUDITOR, "Auditor")):
		need(f"{actor} holds {role}", frappe.db.exists("User Responsibility Assignment", {"user": actor, "business_role": role, "status": "Enabled"}))
	for uom in UNITS:
		need(f"UOM {uom} enabled", frappe.db.get_value("UOM", uom, "enabled"))
	for title in ("Non-consulting services", "Consulting services", "Goods", "Works"):
		need(f"Requirement Type {title} (Active)", frappe.db.get_value("Requirement Type", title, "status") == "Active")
	for method in ("Open Tender", "Request for Quotations", "Low Value Procurement"):
		need(f"Procurement Method {method} (Active)", frappe.db.get_value("Procurement Method", method, "status") == "Active")
	from kentender_core.services.regulatory_reference import get_regulatory_reference

	need(f"Regulatory Reference for {FY} (threshold matrix)", get_regulatory_reference(FY).get("available"))
	# The canonical Budget's lines by role — their references are generated
	# (Project Owner decision, 26 Sep 2026), so they are found by title.
	from kentender_budget.seeds.kentender_mvp_v1_portfolio import BUDGETS, canonical_budget_line

	LINES = BUDGETS["year2"]["lines"]
	bl_dhi = canonical_budget_line("dhi", "year2")
	bl_hwd = canonical_budget_line("hwd", "year2")
	need(f"Budget line '{LINES['dhi']['title']}' with an Active Budget Version", bl_dhi)
	need(f"Budget line '{LINES['hwd']['title']}' with an Active Budget Version", bl_hwd)
	objective = _objective()
	need(f"Active Strategic Objective '{OBJECTIVE_TITLE}'", objective)
	from kentender_procurement.procurement_planning.services import needs_intake

	need(f"Departmental Need {NEED} Accepted for planning", needs_intake.current_accepted_revision_of(NEED, FY))
	if missing:
		frappe.throw(
			"PLN §14 seed prerequisites are absent or differ — seeds never invent "
			"a substitute (§14.1). Missing: " + "; ".join(missing)
		)
	return {"bl_dhi": bl_dhi, "bl_hwd": bl_hwd, "objective": objective, "dhi": dhi, "hrmd": hrmd}


# --- configuration the Planning seed itself owns -----------------------------


def _destination() -> None:
	from kentender_procurement.procurement_planning.services.publication_pipeline import DESTINATION_ADAPTER

	existing = frappe.db.get_value("Annual Plan Publication Destination", {"destination_id": DESTINATION_ID}, ["name", "fixture_namespace"], as_dict=True)
	if existing:
		# Found 26 Sep 2026: the canonical plan published to a destination a
		# Planning test world had created; the canonical seed owns it.
		if existing.fixture_namespace != NS:
			frappe.db.set_value("Annual Plan Publication Destination", existing.name, "fixture_namespace", NS, update_modified=False)
		return
	frappe.get_doc(
		{
			"doctype": "Annual Plan Publication Destination",
			"destination_id": DESTINATION_ID,
			"title": "KenTender Annual Plan Publication Sandbox",
			"adapter": DESTINATION_ADAPTER,
			"active": 1,
			"fixture_namespace": NS,
		}
	).insert(ignore_permissions=True)


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		first, _, last = full_name.partition(" ")
		doc = frappe.get_doc(
			{
				"doctype": "User", "email": email, "first_name": first, "last_name": last,
				"enabled": 1, "send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	elif frappe.db.get_value("User", email, "user_type") != "System User":
		frappe.get_doc("User", email).add_roles("Desk User")
	update_password(email, TEST_PASSWORD)


def _actors() -> None:
	"""§14.2 — only the actors this document adds; the rest come from the
	site seed's shared register (§8.3) and are verified, never re-granted."""
	frappe.set_user("Administrator")
	for email, full_name, role in PLANNING_ACTORS:
		_user(email, full_name)
		administration.grant(user=email, business_role=role, organisation_unit="", fixture_namespace=NS, actor="Administrator")


@contextmanager
def _intake_open():
	"""The isolated profiles' year (`PROFILE_FY`): the §14.1 window closes
	30 Nov 2026; after that the flag is re-opened for the build and closed
	again afterwards (CFG v0.9 §4.2)."""
	FY = PROFILE_FY
	was_open = bool(frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_OPEN))
	if not was_open:
		site_configuration.open_dpp_submission(fiscal_year=FY, reason="Planning §14 seed build")
	try:
		yield
	finally:
		if not was_open and frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_OPEN):
			site_configuration.close_dpp_submission(fiscal_year=FY, reason="Planning §14 seed build complete")


# --- the §14.4–14.6 integrated baseline, driven through real commands --------


def _build_accepted_dpp(
	prereqs: dict[str, str],
	*,
	extra_entries: list[dict[str, Any]] | None = None,
	extra_need_fundings: list[dict[str, Any]] | None = None,
	amount: float = 80000000,
) -> dict[str, Any]:
	"""§14.4 — the Digital Health departmental plan through the real commands:
	Grace funds the projected Need entry (plus any further accepted Needs
	already projected for the same unit — `extra_need_fundings`), Julia
	(acting Head of User Department for Digital Health in November)
	submits, Mercy classifies and accepts, which auto-creates the Draft
	Annual Plan (§5.2)."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation, plan_read

	with _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=prereqs["dhi"], fiscal_year=PROFILE_FY, idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
		)
		entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": NEED}, "entry_id")
		if not entry_id:
			frappe.throw(f"The accepted Need {NEED} did not project into the Draft DPP — run the Departmental Needs seed first (§14.10).")
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id, budget_line=prereqs["bl_dhi"], indicative_amount=amount,
			expected_record_version=opened["record_version"], idempotency_key=_key("fund-need"),
		)
		record_version = funded["record_version"]
		classifications = {entry_id: "Non-consulting services"}
		for index, spec in enumerate(extra_entries or []):
			added = dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], values={**spec["values"], "budget_line": prereqs["bl_dhi"]},
				expected_record_version=record_version, idempotency_key=_key(f"add-direct-{index}"),
			)
			record_version = added["record_version"]
			classifications[added["entry_id"]] = spec["classification"]
		for index, spec in enumerate(extra_need_fundings or []):
			need_entry_id = frappe.db.get_value(
				"Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": spec["need"]}, "entry_id"
			)
			if not need_entry_id:
				frappe.throw(
					f"The accepted Need {spec['need']} did not project into the Draft DPP — "
					"run the Departmental Needs seed first (§14.10)."
				)
			need_funded = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=need_entry_id, budget_line=spec["budget_line"],
				indicative_amount=spec["amount"], expected_record_version=record_version,
				idempotency_key=_key(f"fund-need-extra-{index}"),
			)
			record_version = need_funded["record_version"]
			classifications[need_entry_id] = spec["classification"]
	# Submitted 25 Nov 2026, 10:30 EAT (CLOCK["dpp_submitted_dhi"]) — inside Julia's Digital Health acting window (1 Oct-30 Nov)
	# and before Peter's own Digital Health assignment starts (1 Dec), the
	# same reasoning the Departmental Needs seed already applies to this
	# unit's November decisions. The command's own authority check reads
	# the real clock (AUTH-ADR-001 §4.6), so it must actually run at that
	# instant (plan D19) — Julia alone is never enough while this runs at
	# today's real date, which falls in neither window.
	with _as(ACTING_HOD), clock.at(CLOCK["dpp_submitted_dhi"]):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=record_version, idempotency_key=_key("submit-dpp"),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLANNER), clock.at(CLOCK["dpp_accepted_dhi"]):
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications=classifications, task_token=task.task_token, idempotency_key=_key("accept-dpp"),
		)
	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	return {"accepted": accepted, "plan": plan, "entry_id": entry_id, "opened": opened}


def _form_item(plan: dict[str, Any], prereqs: dict[str, str], *, values: dict[str, Any] | None = None) -> str:
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench

	with _as(PLANNER):
		formed = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=_key("form-item"),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values={**(values or ITEM_VALUES), "strategic_objective": prereqs["objective"]},
			expected_record_version=item["record_version"], idempotency_key=_key("save-item"),
		)
	return item_id


def _request_funding(plan_reference: str) -> str:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_read

	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key("request-funding"),
		)
	return requested["task"]


def _form_and_confirm(plan: dict[str, Any], prereqs: dict[str, str]) -> str:
	"""§14.5/§14.6 — one Plan Item from the Need source with the §14.5
	package, then the one plan-level Finance confirmation by Josphat over the
	real affordability contract. No reservation is created."""
	from kentender_procurement.procurement_planning.services import plan_finance

	item_id = _form_item(plan, prereqs)
	task = frappe.get_doc("Plan Finance Task", _request_funding(plan["plan_reference"]))
	with _as(FINANCE):
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_key("confirm-funding"))
	return item_id


def _submit_plan(plan_reference: str, *, steps: dict[str, str] | None = None, key=None) -> Any:
	from kentender_procurement.procurement_planning.services import plan_governance, plan_read

	steps, key = steps or CLOCK, key or _key
	with _as(HOPF), clock.at(steps["plan_submitted"]):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=key("submit-plan"),
		)
	return frappe.get_doc("Plan Governance Task", submitted["task"])


def _govern_and_publish(plan_reference: str, *, steps: dict[str, str] | None = None, treasury_reference: str = "MOH/APP/2027/001", key=None) -> dict[str, Any]:
	"""§14.6 / §5.5.2 — Charles signs and submits, Amina adopts, Daniel
	approves in the entity's configured route.

	Approval commits the exact content and a durable publication intent; it
	does **not** transmit. The rest is the real asynchronous sequence: Amina
	records the external Treasury submission, the worker sends the frozen
	package, and the acknowledgement activates the Version. There is no RQ
	worker on this bench, so the worker step runs inline here — which is
	exactly what it does under test.
	"""
	from kentender_procurement.procurement_planning.services import plan_governance, publication_pipeline, treasury

	frozen = steps is not None
	steps, key = steps or CLOCK, key or _key

	def at(step: str):
		# The canonical years run every governance step at its instant under
		# the frozen clock (plan D19); the isolated profiles keep the real
		# clock and the design-clock stamp afterwards, as they always have.
		from contextlib import nullcontext

		return clock.at(steps[step]) if frozen else nullcontext()

	ao_task = _submit_plan(plan_reference, steps=steps, key=key)
	with _as(ACCOUNTING_OFFICER), at("ao_adopted"):
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=key("adopt-plan"))
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(STATUTORY), at("statutory_approved"):
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=key("approve-plan"),
		)

	plan_version = approved["plan_version"]
	# §5.5.2.2 — the AO records that the exact approved document was sent.
	# This is external dispatch evidence, not another approval. SEED-001 v1.3
	# §3.7 / SEED-AC-020: the reference alone is not evidence, so a labelled
	# synthetic attachment goes with it (the file name is the artboard's
	# placeholder; until 26 Sep 2026 the seed attached nothing).
	from kentender_core.seeds.fixture_files import attached_pdf

	evidence = attached_pdf(
		TREASURY_EVIDENCE_FILE, label=f"Treasury dispatch evidence {treasury_reference}", doctype="Annual Plan Version", name=plan_version,
	)
	with _as(ACCOUNTING_OFFICER), at("treasury_submitted"):
		treasury.record_treasury_submission(
			plan_version=plan_version,
			submitted_at=steps["treasury_submitted"],
			channel="Official correspondence",
			destination="National Treasury",
			dispatch_reference=treasury_reference,
			exact_document_confirmed=True,
			supporting_attachment=evidence,
			idempotency_key=key("treasury-submission"),
		)
	frappe.set_user("Administrator")
	with at("publication_acknowledged"):
		published = publication_pipeline.publish_annual_plan(plan_version=plan_version, idempotency_key=key("publish-plan"))
	return {**approved, "publication_result": published.get("result"), "publication": published.get("publication")}


def _stamp_design_clock(plan_reference: str, *, steps: dict[str, str] | None = None) -> None:
	"""§14.4–14.6 exact instants onto the evidence rows the commands wrote
	(the publication attempt's own two instants, which one inline worker run
	cannot both hold)."""
	CLOCK = steps or globals()["CLOCK"]
	plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	version = frappe.db.get_value("Annual Plan", plan_name, "active_version") or frappe.db.get_value("Annual Plan", plan_name, "open_successor_version")
	# The departmental submissions and acceptances, and the Head of
	# Procurement Function's signature and submission, run at their own
	# instants under the frozen clock and are not stamped here.
	if not version:
		return
	for decision in frappe.get_all(
		"Plan Finance Decision",
		filters={"task": ("in", frappe.get_all("Plan Finance Task", filters={"plan_version": version}, pluck="name") or ("",)), "decision": "Confirm plan funding"},
		pluck="name",
	):
		frappe.db.set_value("Plan Finance Decision", decision, "decided_at", CLOCK["finance_confirmed"], update_modified=False)
	frappe.db.set_value("Annual Plan Version", version, "activated_at", CLOCK["publication_acknowledged"], update_modified=False)
	for stage, when in (("Accounting Officer adoption", CLOCK["ao_adopted"]), ("Statutory approval", CLOCK["statutory_approved"])):
		task = frappe.db.get_value("Plan Governance Task", {"plan_version": version, "stage": stage}, "decision")
		if task:
			frappe.db.set_value("Plan Governance Decision", task, "decided_at", when, update_modified=False)
	# PLN-CHG-001 v1.18 §5.5.2 — the publication chain, not the retired v1.12
	# `Annual Plan Publication` row.
	publication = frappe.db.get_value("Plan Publication", {"plan_version": version}, "name")
	if publication:
		frappe.db.set_value(
			"Plan Publication", publication, "acknowledged_at", CLOCK["publication_acknowledged"], update_modified=False,
		)
		for attempt in frappe.get_all("Publication Attempt", filters={"publication": publication}, pluck="name"):
			frappe.db.set_value(
				"Publication Attempt", attempt,
				{"attempted_at": CLOCK["publication_attempted"], "completed_at": CLOCK["publication_acknowledged"]},
				update_modified=False,
			)
		for ack in frappe.get_all("Publication Acknowledgement", filters={"publication": publication}, pluck="name"):
			frappe.db.set_value(
				"Publication Acknowledgement", ack,
				{"acknowledged_at": CLOCK["publication_acknowledged"], "received_at": CLOCK["publication_acknowledged"]},
				update_modified=False,
			)
		for evidence in frappe.get_all("Treasury Submission Evidence", filters={"plan_version": version}, pluck="name"):
			frappe.db.set_value(
				"Treasury Submission Evidence", evidence, "recorded_at", CLOCK["treasury_submitted"], update_modified=False,
			)


def _verify_year(year: str) -> dict[str, Any]:
	"""§14.1/§14.3 for one seeded year: its Fiscal Year, its budget's lines,
	the Objective and the accepted Needs its departmental plans fund — or one
	loud failure naming exactly what is absent. Nothing is invented."""
	from kentender_budget.seeds.kentender_mvp_v1_portfolio import BUDGETS, canonical_budget_line
	from kentender_procurement.procurement_planning.services import needs_intake

	y = calendar.year(year)
	spec = plan_spec(year)
	missing: list[str] = []

	def need(label: str, ok) -> None:
		if not ok:
			missing.append(label)

	need("configured site (System setup)", site_configuration.is_configured())
	need(f"Fiscal Year {y.fiscal_year}", frappe.db.exists("Fiscal Year", y.fiscal_year))
	lines = {key: canonical_budget_line(key, year) for key in BUDGETS[year]["lines"]}
	for key, line in lines.items():
		need(f"{y.label} budget line '{BUDGETS[year]['lines'][key]['title']}' with an Active Budget Version", line)
	objective = _objective()
	need(f"Active Strategic Objective '{OBJECTIVE_TITLE}'", objective)
	units = {DHI_NAME: _unit_for(AUTHOR, "Departmental Author", DHI_NAME), HRMD_NAME: _unit_for(AUTHOR, "Departmental Author", HRMD_NAME)}
	for name, unit in units.items():
		need(f"Grace's Departmental Author assignment in '{name}'", unit)
	for dpp in spec["dpps"]:
		for row in dpp["needs"]:
			need(f"Departmental Need {row['need']} Accepted for planning", needs_intake.current_accepted_revision_of(row["need"], y.fiscal_year))
	for actor, role in ((PLANNER, "Procurement Planner"), (FINANCE, "Finance Confirmation Officer"), (AUDITOR, "Auditor")):
		need(f"{actor} holds {role}", frappe.db.exists("User Responsibility Assignment", {"user": actor, "business_role": role, "status": "Enabled"}))
	if missing:
		frappe.throw(f"PLN §14 seed prerequisites for {y.label} are absent or differ — seeds never invent a substitute (§14.1). Missing: " + "; ".join(missing))
	return {"lines": lines, "objective": objective, "units": units}


@contextmanager
def _year_intake(year: str):
	"""The year's departmental-plan intake, opened at its documented instant
	with its close instant (CFG-BR-013: opening it closes any other year's).
	The site stage's Year 2 intake is restored afterwards."""
	from kentender_core.seeds import site_setup

	y = calendar.year(year)
	with clock.at(y.at("2026-11-25 09:00:00")):
		site_configuration.open_dpp_submission(
			fiscal_year=y.fiscal_year, closes_at=y.at(site_setup.DPP_INTAKE["closes_at"]),
			reason=f"Departmental procurement plans called for {y.label} under regulation 40(3).",
		)
	try:
		yield
	finally:
		site_setup._seed_dpp_intake()


def _ykey(year: str, step: str) -> str:
	# Year 2 keeps the keys the seed has always used, so a world seeded before
	# the two-year change replays its own journal rather than duplicating it.
	return _key(step if year == "year2" else f"{year}:{step}")


def _build_dpp(year: str, dpp: dict[str, Any], prereqs: dict[str, Any], steps: dict[str, str]) -> dict[str, str]:
	"""One departmental plan through the real commands: Grace funds each
	projected accepted Need and adds each direct requirement, the department's
	head certifies it, Mercy classifies and accepts it (the first acceptance
	of the year creates its Draft Annual Plan, §5.2). Returns
	`{source key: entry_id}`."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation

	y = calendar.year(year)
	key = dpp["key"]
	entries: dict[str, str] = {}
	classifications: dict[str, str] = {}
	with _as(AUTHOR), clock.at(steps[f"dpp_opened_{key}"]):
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=prereqs["units"][dpp["unit"]], fiscal_year=y.fiscal_year,
			idempotency_key=_ykey(year, "open-dhi-dpp" if key == "dhi" else "open-hrmd-dpp"), fixture_namespace=NS,
		)
		record_version = opened["record_version"]
		# Accepting the year's Needs already started this Draft (`dpp_autostart`)
		# without the seed's stamp: stamp it now, so the submission, its task
		# and the Annual Plan the acceptance creates inherit it, and `reset`
		# keeps them as canonical.
		_stamp_namespace("Departmental Plan", opened["departmental_plan"])
		for version_name in frappe.get_all("Departmental Plan Version", filters={"departmental_plan": opened["departmental_plan"]}, pluck="name"):
			_stamp_namespace("Departmental Plan Version", version_name)
		for row in dpp["needs"]:
			entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": row["need"]}, "entry_id")
			if not entry_id:
				frappe.throw(f"The accepted Need {row['need']} did not project into the Draft {dpp['unit']} plan — run the Departmental Needs seed first (§14.10).")
			funded = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry_id, budget_line=prereqs["lines"][row["line"]], indicative_amount=row["amount"],
				expected_record_version=record_version, idempotency_key=_ykey(year, f"fund-{row['source']}"),
			)
			record_version = funded["record_version"]
			entries[row["source"]] = entry_id
			classifications[entry_id] = row["classification"]
		for row in dpp["direct"]:
			added = dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], values={**row["values"], "budget_line": prereqs["lines"][row["line"]]},
				expected_record_version=record_version, idempotency_key=_ykey(year, f"add-{row['source']}"),
			)
			record_version = added["record_version"]
			entries[row["source"]] = added["entry_id"]
			classifications[added["entry_id"]] = row["classification"]
	with _as(dpp["submitter"]), clock.at(steps[f"dpp_submitted_{key}"]):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=record_version, idempotency_key=_ykey(year, "submit-dpp" if key == "dhi" else "submit-hrmd-dpp"),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLANNER), clock.at(steps[f"dpp_accepted_{key}"]):
		dpp_validation.accept_departmental_plan(
			task=task.name, classifications=classifications, task_token=task.task_token,
			idempotency_key=_ykey(year, "accept-dpp" if key == "dhi" else "accept-hrmd-dpp"),
		)
	return entries


def _form_year_items(year: str, plan_reference: str, entries: dict[str, str], prereqs: dict[str, Any], steps: dict[str, str]) -> list[str]:
	"""Every Plan Item of the year's spec, formed from its exact sources and
	given its package, in the one Draft Annual Plan Version."""
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench

	formed_ids: list[str] = []
	with _as(PLANNER), clock.at(steps["items_formed"]):
		for index, item in enumerate(plan_spec(year)["items"]):
			plan = plan_read.get_annual_plan(plan_reference=plan_reference)
			by_entry = {row["entry_id"]: row["dpp_entry"] for row in plan["unallocated_sources"]}
			sources = [by_entry.get(entries.get(source, "")) for source in item["sources"]]
			if not all(sources):
				frappe.throw(f"Planning seed: {item['values']['title']} has no unallocated source for {item['sources']} in {plan_reference}.")
			combined = item.get("mode") == "combined"
			formed = plan_workbench.form_plan_items(
				plan_version=plan["version_reference"], dpp_entries=sources, mode="combined" if combined else "each",
				**({"combination_reason": item["values"]["aggregation_reason"], "combined_title": item["values"]["title"]} if combined else {}),
				expected_record_version=plan["record_version"], idempotency_key=_ykey(year, f"form-item-{index}"),
			)
			item_id = formed["created_items"][0]
			detail = plan_read.get_plan_item(plan_item_id=item_id)
			plan_workbench.save_plan_item(
				plan_item=item_id, values={**item["values"], "strategic_objective": prereqs["objective"]},
				expected_record_version=detail["record_version"], idempotency_key=_ykey(year, f"save-item-{index}"),
			)
			formed_ids.append(item_id)
	return formed_ids


def _confirm_year_funding(year: str, plan_reference: str, steps: dict[str, str]) -> None:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_read

	with _as(PLANNER), clock.at(steps["funding_requested"]):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_ykey(year, "request-funding"),
		)
	task = frappe.get_doc("Plan Finance Task", requested["task"])
	with _as(FINANCE), clock.at(steps["finance_confirmed"]):
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_ykey(year, "confirm-funding"))


def _stamp_namespace(doctype: str, name: str) -> None:
	if frappe.db.get_value(doctype, name, "fixture_namespace") != NS:
		frappe.db.set_value(doctype, name, "fixture_namespace", NS, update_modified=False)


def _accepted_entries(year: str) -> dict[str, str]:
	"""`{source key: entry_id}` of a year's accepted departmental plans, found
	by each spec row's Need or direct-requirement title."""
	y = calendar.year(year)
	out: dict[str, str] = {}
	for dpp in plan_spec(year)["dpps"]:
		unit = _unit_for(AUTHOR, "Departmental Author", dpp["unit"])
		version = frappe.db.get_value("Departmental Plan", {"organisation_unit": unit, "fiscal_year": y.fiscal_year}, "current_accepted_version")
		for row in dpp["needs"]:
			out[row["source"]] = cstr(frappe.db.get_value("Departmental Plan Entry", {"dpp_version": version, "need": row["need"]}, "entry_id"))
		for row in dpp["direct"]:
			out[row["source"]] = cstr(frappe.db.get_value("Departmental Plan Entry", {"dpp_version": version, "title": row["values"]["title"], "need": ("in", ("", None))}, "entry_id"))
	return out


def year_plan(year: str) -> dict[str, Any] | None:
	return frappe.db.get_value("Annual Plan", {"fiscal_year": calendar.year(year).fiscal_year}, ["name", "plan_reference", "active_version"], as_dict=True)


def upsert_year_plan(year: str, *, through: str = "annual_plan") -> dict[str, Any]:
	"""One seeded year's Planning journey, through `through`:
	"departmental_plans" (both departmental plans accepted; the Draft Annual
	Plan exists) or "annual_plan" (its items formed, funding confirmed,
	signed, adopted, approved, sent to the Treasury and published: Active).
	Idempotent by stable state."""
	if through not in ("departmental_plans", "annual_plan"):
		frappe.throw(f"Unknown Planning stop {through!r}; expected departmental_plans or annual_plan.")
	y = calendar.year(year)
	existing = year_plan(year)
	spec = plan_spec(year)
	if existing and existing.active_version:
		return {"ok": True, "idempotent": True, "year": year, "plan_reference": existing.plan_reference, "active_version": existing.active_version}
	roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": y.fiscal_year}, fields=["name", "current_state", "current_accepted_version"])
	accepted = [r for r in roots if r.current_accepted_version]
	dpps_done = bool(existing) and len(accepted) == len(spec["dpps"]) == len(roots)
	if through == "departmental_plans" and dpps_done:
		return {"ok": True, "idempotent": True, "year": year, "plan_reference": existing.plan_reference, "active_version": ""}
	# Accepting a Need starts its department's Draft plan by itself
	# (`dpp_autostart`), so Draft roots are expected; anything further along
	# than the spec's own journey is a profile's or a failed run's world.
	versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": existing.name}, pluck="name") if existing else []
	items = frappe.db.count("Annual Plan Item", {"plan_version": ("in", versions or ("",))}) if existing else 0
	if (existing and not dpps_done) or items or (accepted and not dpps_done) or any(r.current_state not in ("Draft", "Accepted") for r in roots):
		frappe.throw(
			f"The {y.label} Planning world exists mid-lifecycle ({existing.plan_reference if existing else 'departmental plans only'}) — "
			"an isolated profile or a failed run left it. Rebuild the canonical world: make seed-canonical REBUILD=True."
		)
	prereqs = _verify_year(year)
	steps = year_clock(year)
	entries: dict[str, str] = {}
	if dpps_done:
		# A world seeded to its departmental plans, now taken on to its Annual
		# Plan: the accepted entries are the sources, keyed as the spec keys them.
		entries = _accepted_entries(year)
	else:
		with _year_intake(year):
			for dpp in spec["dpps"]:
				entries.update(_build_dpp(year, dpp, prereqs, steps))
	plan = year_plan(year)
	if not plan:
		frappe.throw(f"Accepting the {y.label} departmental plans created no Draft Annual Plan (§5.2).")
	out: dict[str, Any] = {"ok": True, "idempotent": False, "year": year, "plan_reference": plan.plan_reference, "entries": entries}
	if through == "departmental_plans":
		return out
	out["plan_items"] = _form_year_items(year, plan.plan_reference, entries, prereqs, steps)
	_confirm_year_funding(year, plan.plan_reference, steps)
	approved = _govern_and_publish(plan.plan_reference, steps=steps, treasury_reference=spec["treasury_reference"], key=lambda step: _ykey(year, step))
	_stamp_design_clock(plan.plan_reference, steps=steps)
	out["publication_result"] = approved["publication_result"]
	return out


def upsert_planning_base(*, commit: bool = False, years: dict[str, str] | None = None) -> dict[str, Any]:
	"""Each seeded year's Planning journey (`years` maps a year to how far it
	goes; Year 1, the executed year, always to its Active Annual Plan).
	Idempotent by stable state: a rerun that finds a year's Annual Plan
	already Active returns it untouched (§14.10 — no duplicate root, Version,
	entry, allocation, task, decision or publication attempt)."""
	_guard()
	_actors()
	# §13: the canonical world's own fixture-verified rules, before anything
	# that has to resolve one.
	ensure_profiles()
	_destination()
	years = years if years is not None else {"year1": "annual_plan"}
	out: dict[str, Any] = {"ok": True, "years": {}}
	for year in ("year1", "year2"):
		if year in years:
			out["years"][year] = upsert_year_plan(year, through=years[year])
	executed = out["years"].get("year1") or {}
	out.update({"plan_reference": executed.get("plan_reference"), "idempotent": all(r.get("idempotent") for r in out["years"].values())})
	if commit:
		frappe.db.commit()
	return out


def wipe_all_planning() -> dict[str, int]:
	"""Unconditional: every row in every Planning doctype, regardless of
	fiscal year or fixture stamp — except `Annual Plan Publication
	Destination`, which is shared site configuration, not test data.
	`reset_planning_seed`/`clear_planning_fixture_rows` both select by a
	live fiscal year or a currently-known parent; an isolation-year fixture
	whose own parent (e.g. an Annual Plan) was already deleted by some
	other, unrelated test run is invisible to either and survives every
	wipe forever (found: a `PPI-MOH-2099-001` Plan Item under a long-gone
	`PLN-MOH-2099-001`, from some other test's isolation year). Only safe
	unconditionally under a full site `wipe`, which has nothing left on
	Requisitions/Budget/Needs for an orphaned Planning row to reference."""
	deleted: dict[str, int] = {}
	for doctype in _DOCTYPES:
		if doctype == "Annual Plan Publication Destination":
			continue
		deleted[doctype] = frappe.db.count(doctype)
		frappe.db.delete(doctype)
	return deleted


# --- isolated profiles (§14.10 — mutually exclusive with the baseline) -------


def reset_planning_seed(*, commit: bool = False) -> dict[str, int]:
	"""Remove every Planning row on both seeded years (FY 2026/27 and
	FY 2027/28) and every NS-stamped row, each Need usage projection an
	activation published (reversed through the same published channel), and
	the seed's own command-journal rows."""
	from uuid import uuid4

	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake

	_guard()
	frappe.set_user("Administrator")
	for year in calendar.YEARS:
		for need in frappe.get_all("Departmental Need", filters={"financial_year": year.fiscal_year}, pluck="name"):
			accepted_revision = needs_intake.current_accepted_revision_of(need, year.fiscal_year)
			if accepted_revision and needs_usage.is_actively_included(accepted_revision):
				needs_usage.project_planning_usage(
					departmental_need=need, accepted_revision=accepted_revision, usage="Not included",
					source_event_id=f"pln-seed-reset:{uuid4().hex}", source_event_time=now_datetime(), user="Administrator",
				)
	deleted: dict[str, int] = {}
	for year in calendar.YEARS:
		for doctype, count in _wipe_fiscal_year(year.fiscal_year).items():
			deleted[doctype] = deleted.get(doctype, 0) + count
	deleted.update(clear_planning_fixture_rows(include_playwright=False, namespaces=(NS,)))
	journal = frappe.get_all("Planning Command Journal", filters={"idempotency_key": ("like", "pln-seed:%")}, pluck="name")
	frappe.db.delete("Planning Command Journal", {"name": ("in", journal or ("",))})
	deleted["Planning Command Journal"] = len(journal)
	if commit:
		frappe.db.commit()
	return deleted


def _wipe_fiscal_year(fiscal_year: str) -> dict[str, int]:
	"""Rows created through the commands carry no namespace; the Fiscal Year
	is the seed world's boundary (D13)."""
	deleted: dict[str, int] = {}

	def delete(doctype: str, names: list[str]) -> None:
		if names:
			frappe.db.delete(doctype, {"name": ("in", names)})
		deleted[doctype] = deleted.get(doctype, 0) + len(names)

	roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": fiscal_year}, pluck="name")
	versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": ("in", roots or ("",))}, pluck="name")
	tasks = frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": fiscal_year}, pluck="name")
	submissions = frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ("in", versions or ("",))}, pluck="name")
	delete("DPP Classification Correction", frappe.get_all("DPP Classification Correction", filters={"dpp_submission": ("in", submissions or ("",))}, pluck="name"))
	delete("Departmental Plan Validation Decision", frappe.get_all("Departmental Plan Validation Decision", filters={"task": ("in", tasks or ("",))}, pluck="name"))
	delete("Departmental Plan Validation Task", tasks)
	delete("Departmental Plan Submission", submissions)
	delete("Departmental Plan Entry", frappe.get_all("Departmental Plan Entry", filters={"dpp_version": ("in", versions or ("",))}, pluck="name"))
	delete("Departmental Plan Version", versions)
	delete("Departmental Plan", roots)
	plans = frappe.get_all("Annual Plan", filters={"fiscal_year": fiscal_year}, pluck="name")
	plan_versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name")
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
	delete("Plan Drawdown Reference", frappe.get_all("Plan Drawdown Reference", filters={"plan_item": ("in", items or ("",))}, pluck="name"))
	delete("Plan Source Allocation", frappe.get_all("Plan Source Allocation", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Annual Plan Item", items)
	# "Plan Item" (PPI-…) is Annual Plan Item's own parent (its `plan_item`
	# link), created with no fixture_namespace stamp of its own until
	# recently — the same "rows created through the commands carry no
	# namespace" gap this function exists to close for everything else on
	# this Fiscal Year. Its children key off it directly, not the plan
	# version, since a Plan Item outlives a single version.
	plan_items = frappe.get_all("Plan Item", filters={"annual_plan": ("in", plans or ("",))}, pluck="name")
	delete("Plan Item Correction Disposition", frappe.get_all(
		"Plan Item Correction Disposition",
		filters={"correction_request": ("in", frappe.get_all("Plan Item Correction Request", filters={"plan_item": ("in", plan_items or ("",))}, pluck="name") or ("",))},
		pluck="name",
	))
	delete("Plan Item Correction Request", frappe.get_all("Plan Item Correction Request", filters={"plan_item": ("in", plan_items or ("",))}, pluck="name"))
	delete("Plan Item", plan_items)
	for task_doctype, decision_doctype in (("Plan Finance Task", "Plan Finance Decision"), ("Plan Governance Task", "Plan Governance Decision")):
		task_rows = frappe.get_all(task_doctype, filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
		delete(decision_doctype, frappe.get_all(decision_doctype, filters={"task": ("in", task_rows or ("",))}, pluck="name"))
		delete(task_doctype, task_rows)
	delete("Annual Plan Publication", frappe.get_all("Annual Plan Publication", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	# PLN-CHG-001 v1.18 §5.5.2 publication chain, dependents first. This was
	# missing, so a reset left the previous run's Approved Plan Snapshot in
	# place and the next approval reused it — content shape and all.
	publications = frappe.get_all("Plan Publication", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
	delete("Publication Acknowledgement", frappe.get_all("Publication Acknowledgement", filters={"publication": ("in", publications or ("",))}, pluck="name"))
	delete("Publication Attempt", frappe.get_all("Publication Attempt", filters={"publication": ("in", publications or ("",))}, pluck="name"))
	delete("Publication Intent", frappe.get_all("Publication Intent", filters={"publication": ("in", publications or ("",))}, pluck="name"))
	delete("Plan Publication Hold", frappe.get_all("Plan Publication Hold", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Plan Publication", publications)
	delete("Treasury Submission Evidence", frappe.get_all("Treasury Submission Evidence", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Late Activation Explanation", frappe.get_all("Late Activation Explanation", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Approved Plan Snapshot", frappe.get_all("Approved Plan Snapshot", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Plan Preparation Signature", frappe.get_all("Plan Preparation Signature", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Plan Finance Basis Reuse", frappe.get_all("Plan Finance Basis Reuse", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Plan Financial Basis", frappe.get_all("Plan Financial Basis", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Milestone Actual Event", frappe.get_all("Milestone Actual Event", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Proceeding Coverage", frappe.get_all("Proceeding Coverage", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name"))
	delete("Annual Plan Version", plan_versions)
	delete("Annual Plan", plans)

	# Orphans. A previous run that failed part-way could delete the Annual
	# Plan while leaving its publication chain behind; the filters above key
	# off the plan, so those rows become unreachable and the next approval
	# happily reuses a stale snapshot. Sweep anything whose Plan Version no
	# longer exists. (This is how the v1.12 OCDS-shaped snapshots survived
	# every reset until now.)
	live_versions = set(frappe.get_all("Annual Plan Version", pluck="name"))
	for doctype in (
		"Publication Acknowledgement",
		"Publication Attempt",
		"Publication Intent",
	):
		live_publications = set(frappe.get_all("Plan Publication", pluck="name"))
		delete(doctype, [
			row.name for row in frappe.get_all(doctype, fields=["name", "publication"], limit_page_length=0)
			if cstr(row.publication) not in live_publications
		])
	for doctype in (
		"Plan Publication",
		"Plan Publication Hold",
		"Treasury Submission Evidence",
		"Late Activation Explanation",
		"Approved Plan Snapshot",
		"Plan Preparation Signature",
		"Plan Finance Basis Reuse",
		"Plan Financial Basis",
	):
		delete(doctype, [
			row.name for row in frappe.get_all(doctype, fields=["name", "plan_version"], limit_page_length=0)
			if cstr(row.plan_version) not in live_versions
		])
	return deleted


def _fresh_profile_world() -> dict[str, str]:
	"""Reset first, then the §14.1 configuration this seed owns."""
	_guard()
	_actors()
	prereqs = verify_prerequisites()
	reset_planning_seed()
	_destination()
	return prereqs


def seed_direct_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§14.7 — the Digital Health Draft DPP carrying both the projected
	accepted Need and the exact direct security-assessment entry (the mixed-
	DPP proof). Never submitted, never in any Plan."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	prereqs = _fresh_profile_world()
	with _intake_open(), _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=prereqs["dhi"], fiscal_year=PROFILE_FY, idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
		)
		need_entry_id = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": NEED}, "entry_id")
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=need_entry_id, budget_line=prereqs["bl_dhi"], indicative_amount=80000000,
			expected_record_version=opened["record_version"], idempotency_key=_key("fund-need"),
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values={**DIRECT_FIXTURE, "budget_line": prereqs["bl_dhi"]},
			expected_record_version=funded["record_version"], idempotency_key=_key("add-direct"),
		)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "direct", "dpp_reference": opened["dpp_reference"], "entry_id": added["entry_id"], "need_entry_id": need_entry_id}


def seed_return_profile(*, commit: bool = False) -> dict[str, Any]:
	"""Submitted Plan returned by the Accounting Officer; the numbered
	correction Draft is open (§5.2/§12.10)."""
	from kentender_procurement.procurement_planning.services import plan_governance

	prereqs = _fresh_profile_world()
	with _intake_open():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		ao_task = _submit_plan(built["accepted"]["annual_plan"])
		with _as(ACCOUNTING_OFFICER):
			returned = plan_governance.return_plan_version(
				task=ao_task.name, reason="Confirm the planned contract-signing date against the delivery completion date.",
				task_token=ao_task.task_token, idempotency_key=_key("return-plan"),
			)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "return", "correction_version": returned["correction_version"]}


def seed_not_affordable_profile(*, commit: bool = False) -> dict[str, Any]:
	"""A Draft Plan whose planned total exceeds the Procurement Budget Line's
	approved amount — PLN-DES-07's readiness row reads "Exceeds approved" and
	the funding request is refused with PLN_PLAN_NOT_AFFORDABLE (§5.2, §12.9:
	the blocking check runs before a Finance task can exist). Replaces the
	v1.2 "shortfall" profile."""
	prereqs = _fresh_profile_world()
	with _intake_open():
		# deliberately above MOH-BL-DHI-2027's KES 100,000,000 approved amount
		built = _build_accepted_dpp(prereqs, amount=150000000)
		item_id = _form_item(built["plan"], prereqs)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "not_affordable", "plan_reference": built["accepted"]["annual_plan"], "plan_item": item_id}


seed_shortfall_profile = seed_not_affordable_profile  # one-cycle alias for the Make gate


# seed_combined_profile (§14.8) is retired — PLN-CHG-001 v1.13 §14.8/SEED-001
# §1.1 (2026-09-05): the combined laptops item is no longer an isolated,
# mutually-exclusive test profile. It is corrected (one shared Budget Line,
# reduced quantities) and folded into the live integrated baseline as
# PPI-MOH-2027-033 — see `_build_hrmd_laptops_dpp`/`_form_each_and_combined_items`
# above, called from `upsert_planning_base`.


def seed_stale_profile(*, commit: bool = False) -> dict[str, Any]:
	"""Source correction required (§12.7): the allocated DPP entry's
	department resubmits and Mercy re-accepts, leaving the Draft item pinned
	to the predecessor entry document."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation, plan_read, plan_workbench

	prereqs = _fresh_profile_world()
	with _intake_open():
		built = _build_accepted_dpp(prereqs)
		with _as(PLANNER):
			plan = built["plan"]
			formed = plan_workbench.form_plan_items(
				plan_version=plan["version_reference"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
				mode="each", expected_record_version=plan["record_version"], idempotency_key=_key("form-item"),
			)
			item_id = formed["created_items"][0]
		dpp_root = built["opened"]["departmental_plan"]
		with _as(HOD):
			update = dpp_lifecycle.create_departmental_plan_update(
				departmental_plan=dpp_root, expected_record_version=frappe.db.get_value("Departmental Plan", dpp_root, "record_version"),
				idempotency_key=_key("dpp-update"),
			)
			resubmitted = dpp_lifecycle.submit_departmental_plan(
				dpp_version=update["current_version"], certification_confirmed=True,
				expected_record_version=update["record_version"], idempotency_key=_key("resubmit-dpp"),
			)
		task2 = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": resubmitted["task"]})
		with _as(PLANNER):
			dpp_validation.accept_departmental_plan(
				task=task2.name, classifications={built["entry_id"]: "Non-consulting services"}, task_token=task2.task_token, idempotency_key=_key("re-accept-dpp"),
			)
		flagged = plan_read.get_plan_item(plan_item_id=item_id, user=PLANNER)
		if not flagged["source_correction_required"]:
			frappe.throw("Stale profile did not produce the source-correction flag.")
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "stale", "plan_item": item_id}


def seed_successor_profile(*, commit: bool = False) -> dict[str, Any]:
	"""The Active baseline plus an open Draft successor (§5.2 / PLN-DES-14's
	Prepare plan update outcome)."""
	from kentender_procurement.procurement_planning.services import plan_publication

	prereqs = _fresh_profile_world()
	with _intake_open():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		_govern_and_publish(built["accepted"]["annual_plan"])
		with _as(PLANNER):
			begun = plan_publication.begin_plan_update(plan_reference=built["accepted"]["annual_plan"], idempotency_key=_key("begin-update"))
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "successor", "successor_version": begun["successor_version"]}


def seed_publication_failure_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§12.11 — an approved Version whose only publication attempt Failed;
	the System Manager retry path is live. The sandbox adapter cannot fail on
	its own, so the seed patches `_transmit` for this one approval."""
	from unittest.mock import patch

	from kentender_procurement.procurement_planning.services import plan_publication

	prereqs = _fresh_profile_world()
	with _intake_open():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		with patch.object(plan_publication, "_transmit", return_value=("Failed", "")):
			approved = _govern_and_publish(built["accepted"]["annual_plan"])
	if approved["publication_result"] != "Failed":
		frappe.throw("Publication-failure profile did not produce a Failed attempt.")
	plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": built["accepted"]["annual_plan"]})
	version = frappe.get_all("Annual Plan Version", filters={"annual_plan": plan_name}, pluck="name")
	publication = frappe.db.get_value("Annual Plan Publication", {"plan_version": ("in", version), "result": "Failed"}, "name")
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "publication_failure", "publication": publication}


# seed_kebs_profiles (§14.9) is retired — PLN-CHG-001 v1.13 §14.9/SEED-001
# §1.1 (2026-09-05): the bare PPI-KEBS-2026-ICT-001 fixture, keyed to Kenya
# Bureau of Standards, is removed outright (one-site-one-PE has no second
# entity for it to belong to), not fixed by building an authoritative KEBS
# Budget Line/Strategic Objective as FU-01 previously proposed.


# --- shared plumbing ---------------------------------------------------------


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Planning seed fixtures are test/demo data. Enable "
		"developer_mode or allow_tests on this site before building them."
	)


def clear_planning_fixture_rows(
	*,
	include_canonical: bool = False,
	include_playwright: bool = True,
	namespaces: tuple[str, ...] = (),
) -> dict[str, int]:
	"""Namespace-stamped Planning rows; with `include_playwright` the whole
	Playwright world (its Fiscal Year rows too) and the intake flags restored."""
	deleted: dict[str, int] = {}
	selected: list[str] = list(namespaces)
	if include_playwright:
		from kentender_procurement.procurement_planning.seeds import playwright_ui_fixtures as pw

		pw.reset_all(commit=False)
		pw.restore_site(commit=False)
		selected.append(PLAYWRIGHT_NS)
	for doctype in _DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		filters: dict[str, Any] = {}
		if not include_canonical:
			if not selected:
				continue
			filters["fixture_namespace"] = ("in", selected)
		rows = frappe.get_all(doctype, filters=filters, pluck="name")
		for name in rows:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, delete_permanently=True)
		deleted[doctype] = len(rows)
	return deleted


def validate_planning_history(year: str = "year1", *, through: str = "annual_plan") -> list[dict[str, Any]]:
	"""PLN-CHG-001 v1.27 §10.2 / SEED-001 v1.3 §3.3 and §3.6–§3.7 facts of
	one seeded year that no later stage changes, so the core validator
	asserts them whatever stage it seeds through (unlike
	`validate_planning_seed`). `through` "departmental_plans": only the
	departmental plans. Never mutates."""
	from kentender_procurement.departmental_needs.services.usage import planning_usage

	checks: list[dict[str, Any]] = []
	y = calendar.year(year)
	steps = year_clock(year)
	spec = plan_spec(year)

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"planning.{year}.{name}", "ok": bool(ok), "detail": detail})

	for dpp in spec["dpps"]:
		department = dpp["unit"]
		unit = frappe.db.get_value("Organisation Unit", {"unit_name": department}, "name")
		root = frappe.db.get_value("Departmental Plan", {"organisation_unit": unit, "fiscal_year": y.fiscal_year}, "name")
		submission = frappe.db.get_value(
			"Departmental Plan Submission",
			{"dpp_version": ("in", frappe.get_all("Departmental Plan Version", filters={"departmental_plan": root}, pluck="name") or ("",))},
			["name", "submitted_by_user", "submitted_at"], as_dict=True,
		)
		check(f"{department}.certified", bool(submission) and submission.submitted_by_user == dpp["submitter"] and str(submission.submitted_at)[:19] == steps[f"dpp_submitted_{dpp['key']}"], str(submission))
		decision = frappe.db.get_value(
			"Departmental Plan Validation Decision", {"submission": submission.name if submission else "", "decision": "Accept departmental plan"}, ["actor", "decided_at"], as_dict=True,
		)
		check(f"{department}.accepted", bool(decision) and decision.actor == PLANNER and str(decision.decided_at)[:19] == steps[f"dpp_accepted_{dpp['key']}"], str(decision))
	plan_row = year_plan(year)
	if through == "departmental_plans":
		check("plan.draft", bool(plan_row) and not plan_row.active_version, str(plan_row))
		return checks
	check("plan.active", bool(plan_row and plan_row.active_version))
	if not (plan_row and plan_row.active_version):
		return checks
	version = plan_row.active_version
	signature = frappe.db.get_value("Plan Preparation Signature", {"plan_version": version}, ["actor", "signed_at"], as_dict=True)
	check("signature", bool(signature) and signature.actor == HOPF and str(signature.signed_at)[:19] == steps["plan_submitted"], str(signature))
	items = {row.title: row for row in frappe.get_all(
		"Annual Plan Item", filters={"plan_version": version},
		fields=["title", "estimate_basis", "estimate_basis_reference", "estimated_delivery_period_days", "estimated_completion_date", "baseline_invitation_date"],
	)}
	check("items.count", len(items) == len(spec["items"]), f"{len(items)} of {len(spec['items'])}")
	for item in spec["items"]:
		values = item["values"]
		row = items.get(values["title"])
		check(
			f"{values['title']}.baseline",
			bool(row) and (str(row.baseline_invitation_date), row.estimated_delivery_period_days) == (values["baseline_invitation_date"], values["estimated_delivery_period_days"]),
			str(row and (row.baseline_invitation_date, row.estimated_delivery_period_days)),
		)
		check(f"{values['title']}.estimate_basis", bool(row) and (row.estimate_basis, row.estimate_basis_reference) == (ITEM_VALUES["estimate_basis"], ITEM_VALUES["estimate_basis_reference"]))
		check(
			f"{values['title']}.completes_inside_the_year",
			bool(row) and bool(row.estimated_completion_date) and str(row.estimated_completion_date) <= str(frappe.db.get_value("Fiscal Year", y.fiscal_year, "year_end_date")),
			str(row and row.estimated_completion_date),
		)
	activated = frappe.db.get_value("Annual Plan Version", version, "activated_at")
	check("activated", str(activated)[:19] == steps["publication_acknowledged"], str(activated))
	evidence = frappe.db.get_value("Treasury Submission Evidence", {"plan_version": version, "evidence_state": "Current"}, ["supporting_attachment", "dispatch_reference"], as_dict=True)
	check("treasury.attachment", bool(evidence) and bool(frappe.db.exists("File", {"file_url": evidence.supporting_attachment})), str(evidence))
	check("treasury.reference", bool(evidence) and evidence.dispatch_reference == spec["treasury_reference"], str(evidence and evidence.dispatch_reference))
	# Each funded Need reports its accepted revision as Fully included (found
	# 26 Sep 2026: a Departmental Needs profile reset had deleted Need 1's).
	for dpp in spec["dpps"]:
		for row in dpp["needs"]:
			check(f"{row['need']}.fully_included", planning_usage(row["need"]) == "Fully included", planning_usage(row["need"]))
	return checks


def validate_planning_seed() -> list[dict[str, Any]]:
	"""§14.10 — validate the executed year's integrated baseline (Year 1)
	through the same domain services commands use, while no Requisition has
	drawn on it yet. Returns check rows for the core validator."""
	from decimal import Decimal

	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake, plan_read, plan_requisition

	checks: list[dict[str, Any]] = []
	spec = plan_spec("year1")
	steps = year_clock("year1")

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"planning.v112.{name}", "ok": bool(ok), "detail": detail})

	plan_row = year_plan("year1")
	check("plan.exists", bool(plan_row), str(plan_row))
	if not plan_row:
		return checks
	check("plan.active", bool(plan_row.active_version), str(plan_row.active_version))
	if not plan_row.active_version:
		return checks

	plan = plan_read.get_annual_plan(plan_reference=plan_row.plan_reference, user=PLANNER)
	view = plan["active_view"]
	check("active_view", view is not None)
	expected_value = sum(
		Decimal(str(row["amount"])) for dpp in spec["dpps"] for row in (*dpp["needs"], *dpp["direct"])
	)
	check("active.items", bool(view and view["summary"]["plan_items"] == len(spec["items"])), str(view and view["summary"]))
	check("active.value", bool(view and f"{int(expected_value):,}" in view["summary"]["value_display"]), str(view and view["summary"]["value_display"]))
	activated = frappe.utils.get_datetime(steps["publication_acknowledged"])
	check("active.activated_display", bool(view and view["summary"]["activated_display"] == f"{activated.day} {activated:%b %Y, %H:%M} EAT"), str(view and view["summary"]["activated_display"]))
	by_title = {item["title"]: item for item in (view or {}).get("items") or []}
	for item in spec["items"]:
		values = item["values"]
		row = by_title.get(values["title"])
		check(f"{values['title']}.listed", bool(row))
		if not row:
			continue
		detail = plan_read.get_plan_item(plan_item_id=row["plan_item_id"], user=PLANNER)
		check(f"{values['title']}.baseline", any(r["milestone"] == "invitation" and r["date"] == values["baseline_invitation_date"] for r in detail["baseline"]["rows"]))
		if not frappe.db.exists("Plan Drawdown Reference", {"plan_item_id": row["plan_item_id"], "drawdown_state": "Active"}):
			eligibility = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=row["plan_item_id"], user=PLANNER)
			check(f"{values['title']}.eligible", eligibility["eligible"], str(eligibility.get("reason") or ""))
	version = plan_row.active_version
	finance = frappe.db.get_value(
		"Plan Finance Decision",
		{"task": ("in", frappe.get_all("Plan Finance Task", filters={"plan_version": version}, pluck="name") or ("",)), "decision": "Confirm plan funding"},
		["actor", "affordability_statement"], as_dict=True,
	)
	check("finance.confirmed_by_josphat", bool(finance and finance.actor == FINANCE), str(finance and finance.actor))
	check("finance.statement_within_approved", bool(finance and '"within_approved": true' in cstr(finance.affordability_statement)))
	check("reservations.none", frappe.db.count("Funding Reservation", {"fixture_namespace": NS}) == 0)
	for stage, actor in (("Accounting Officer adoption", ACCOUNTING_OFFICER), ("Statutory approval", STATUTORY)):
		decision = frappe.db.get_value("Plan Governance Task", {"plan_version": version, "stage": stage}, "decision")
		who = frappe.db.get_value("Plan Governance Decision", decision, "actor") if decision else ""
		check(f"governance.{stage.split()[0].lower()}_by_named_actor", who == actor, str(who))
	publication = frappe.db.get_value("Plan Publication", {"plan_version": version, "publication_state": "Acknowledged"}, "name")
	check("publication.acknowledged", bool(publication))
	check(
		"publication.treasury_evidence_current",
		bool(frappe.db.get_value("Treasury Submission Evidence", {"plan_version": version, "evidence_state": "Current"}, "name")),
	)
	for dpp in spec["dpps"]:
		for row in dpp["needs"]:
			accepted_revision = needs_intake.current_accepted_revision_of(row["need"], FY)
			check(f"{row['need']}.usage_fully_included", bool(accepted_revision) and needs_usage.is_actively_included(accepted_revision), str(accepted_revision))
	return checks
