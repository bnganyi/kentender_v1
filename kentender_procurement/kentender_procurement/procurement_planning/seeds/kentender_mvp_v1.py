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

from kentender_core.seeds import clock
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
# §10.2's illustrative mandatory planning allocation: 30% of the KES 160m
# annual procurement budget = KES 48m required.
RESERVATION_TARGET_PERCENT = 30

FY = "2027-2028"
DHI_NAME = "Digital Health"  # spec: OU-MOH-DHI
HRMD_NAME = "Human Resources Management and Development"  # spec: OU-MOH-HRMD

NEED = "NDS-MOH-2027-0001"
# SEED-001 §3.2/§3.6, PLN-CHG-001 v1.13 §14.5 (2026-09-05) — the harmonized
# combined item's two real, Need-backed sources. Both Needs are Accepted by
# `departmental_needs.seeds.kentender_mvp_r1` before this seed runs.
NEED_HRMD_LAPTOPS = "NDS-MOH-2027-0003"
NEED_DHI_LAPTOPS = "NDS-MOH-2027-0004"
BL_DHI = "MOH-BL-DHI-2027"
BL_HWD = "MOH-BL-HWD-2027"
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
	# PLN-CHG-001 v1.18 §4.6 — estimate basis and the estimated delivery period
	"estimate_basis": "Market survey of the current supplier panel including delivery, installation and incidental costs.",
	"estimate_basis_reference": "MS-2027-001",
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
	# fortnight-later invitation date; every *_period_days field is
	# inherited from ITEM_VALUES above unchanged.
	"baseline_invitation_date": "2027-05-15",
}

# §14.4–14.6 design-clock instants, stored as the UTC equivalents of the
# stated EAT times (read models render EAT, §12.13).
CLOCK = {
	"dpp_submitted": "2026-11-25 07:00:00",  # 25 Nov 2026, 10:00 EAT
	"dpp_accepted": "2026-11-27 11:00:00",  # 27 Nov 2026, 14:00 EAT
	"finance_confirmed": "2026-12-04 07:00:00",  # 4 Dec 2026, 10:00 EAT
	"plan_submitted": "2026-12-05 07:00:00",  # 5 Dec 2026, 10:00 EAT
	"ao_adopted": "2026-12-08 07:00:00",  # 8 Dec 2026, 10:00 EAT
	"statutory_approved": "2026-12-09 08:00:00",  # 9 Dec 2026, 11:00 EAT
	"publication_attempted": "2026-12-10 11:55:00",  # 10 Dec 2026, 14:55 EAT
	"publication_acknowledged": "2026-12-10 12:00:00",  # 10 Dec 2026, 15:00 EAT
	"treasury_submitted": "2026-12-10 11:00:00",  # 10 Dec 2026, 14:00 EAT (§10.12)
}

_DOCTYPES = (
	# dependents first, roots last
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


def _budget_line(reference: str) -> str:
	name = frappe.db.get_value("Procurement Budget Line", {"generated_reference": reference}, "name")
	if not name:
		return ""
	for row in frappe.get_all("Procurement Budget Line Version", filters={"budget_line": name}, fields=["budget_version"]):
		if frappe.db.get_value("Procurement Budget Version", row.budget_version, "status") == "Active":
			return name
	return ""


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

	year = int(FY.split("-")[0])
	# §10.2 anchors the canonical schedules at 1 May and 15 May 2027 while
	# FY 2027/28 begins on 1 July 2027, so a profile window starting at the
	# financial year would not cover the plan's own applicable dates and no
	# rule would resolve. This is the recorded applicability-date/fixture
	# conflict (§17.2, CFG-XD-001) — the fixture's dates are what the
	# specification fixes, so the seed widens its own configuration window to
	# cover them rather than relaxing the resolver or back-dating the plan.
	# A profile's effective window is configuration; the rule it carries is
	# not weakened, and nothing is marked Verified.
	window = {"effective_from": f"{year}-01-01", "effective_until": f"{year + 1}-06-30"}
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
	)
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
	"""§14.1/§14.3 — every authoritative prerequisite present and usable, or
	one loud failure naming exactly what is absent. Nothing is invented."""
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
	bl_dhi = _budget_line(BL_DHI)
	bl_hwd = _budget_line(BL_HWD)
	need(f"Procurement Budget Line {BL_DHI} with an Active Budget Version", bl_dhi)
	need(f"Procurement Budget Line {BL_HWD} with an Active Budget Version", bl_hwd)
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

	if frappe.db.exists("Annual Plan Publication Destination", {"destination_id": DESTINATION_ID}):
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
	"""The §14.1 window closes 30 Nov 2026; after that the flag is re-opened
	for the build and closed again afterwards (CFG v0.9 §4.2)."""
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
			organisation_unit=prereqs["dhi"], fiscal_year=FY, idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
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
	# Submitted 25 Nov 2026, 10:00 EAT (CLOCK["dpp_submitted"]'s wall-clock
	# instant) — inside Julia's Digital Health acting window (1 Oct-30 Nov)
	# and before Peter's own Digital Health assignment starts (1 Dec), the
	# same reasoning the Departmental Needs seed already applies to this
	# unit's November decisions. The command's own authority check reads
	# the real clock (AUTH-ADR-001 §4.6), so it must actually run at that
	# instant (plan D19) — Julia alone is never enough while this runs at
	# today's real date, which falls in neither window.
	with _as(ACTING_HOD), clock.at("2026-11-25 10:00:00"):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=record_version, idempotency_key=_key("submit-dpp"),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLANNER):
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications=classifications, task_token=task.task_token, idempotency_key=_key("accept-dpp"),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	return {"accepted": accepted, "plan": plan, "entry_id": entry_id, "opened": opened}


def _build_hrmd_laptops_dpp(prereqs: dict[str, str]) -> str:
	"""PLN-CHG-001 v1.13 §14.4/SEED-001 §3.3 — a new HRMD departmental plan
	carrying only Need-3 (`NEED_HRMD_LAPTOPS`), submitted and accepted the
	same way as the DHI plan. Accepting a second department's DPP for the
	same Fiscal Year attaches to the one existing Annual Plan (§5.2 is keyed
	by Fiscal Year, not by department), the same behaviour the two-department
	combined item always relied on."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation

	with _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=prereqs["hrmd"], fiscal_year=FY, idempotency_key=_key("open-hrmd-dpp"), fixture_namespace=NS,
		)
		entry_id = frappe.db.get_value(
			"Departmental Plan Entry", {"dpp_version": opened["current_version"], "need": NEED_HRMD_LAPTOPS}, "entry_id"
		)
		if not entry_id:
			frappe.throw(
				f"The accepted Need {NEED_HRMD_LAPTOPS} did not project into the Draft DPP — "
				"run the Departmental Needs seed first (§14.10)."
			)
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id, budget_line=prereqs["bl_hwd"],
			indicative_amount=NEED_HRMD_LAPTOPS_AMOUNT, expected_record_version=opened["record_version"],
			idempotency_key=_key("fund-hrmd-laptops"),
		)
	with _as(HOD):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=funded["record_version"], idempotency_key=_key("submit-hrmd-dpp"),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLANNER):
		dpp_validation.accept_departmental_plan(
			task=task.name, classifications={entry_id: "Goods"}, task_token=task.task_token,
			idempotency_key=_key("accept-hrmd-dpp"),
		)
	return entry_id


def _form_each_and_combined_items(plan_reference: str, prereqs: dict[str, str]) -> tuple[str, str]:
	"""PLN-CHG-001 v1.13 §14.5 — two Plan Items formed into the same Draft
	Annual Plan Version before its one finance/governance/publication cycle
	runs: Need-1's item (unchanged) and the harmonized combined item from
	Need-3 (HRMD) + Need-4 (Digital Health). Both DHI and HRMD DPPs must
	already be accepted (their entries are "laptops"-titled; Need-1's is
	not) so this always selects the right entries regardless of row order."""
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench

	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		sources = plan["unallocated_sources"]
		single_source = next(s for s in sources if "laptops" not in s["title"])
		laptop_sources = [s["dpp_entry"] for s in sources if "laptops" in s["title"]]
		if len(laptop_sources) != 2:
			frappe.throw(
				f"Expected exactly 2 unallocated laptop sources for the combined item, found {len(laptop_sources)}."
			)

		formed_each = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"], dpp_entries=[single_source["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=_key("form-item"),
		)
		item_id = formed_each["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id, values={**ITEM_VALUES, "strategic_objective": prereqs["objective"]},
			expected_record_version=item["record_version"], idempotency_key=_key("save-item"),
		)

		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		formed_combined = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"], dpp_entries=laptop_sources,
			mode="combined",
			# §10.7 — the combination is named and justified where it is made,
			# exactly as U08 asks the Planner for it.
			combination_reason=COMBINED_ITEM_VALUES["aggregation_reason"],
			combined_title=COMBINED_ITEM_VALUES["title"],
			expected_record_version=plan["record_version"], idempotency_key=_key("form-combined"),
		)
		combined_item_id = formed_combined["created_items"][0]
		combined_item = plan_read.get_plan_item(plan_item_id=combined_item_id)
		plan_workbench.save_plan_item(
			plan_item=combined_item_id, values={**COMBINED_ITEM_VALUES, "strategic_objective": prereqs["objective"]},
			expected_record_version=combined_item["record_version"], idempotency_key=_key("save-combined"),
		)
	return item_id, combined_item_id


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


def _submit_plan(plan_reference: str) -> Any:
	from kentender_procurement.procurement_planning.services import plan_governance, plan_read

	with _as(HOPF):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key("submit-plan"),
		)
	return frappe.get_doc("Plan Governance Task", submitted["task"])


def _govern_and_publish(plan_reference: str) -> dict[str, Any]:
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

	ao_task = _submit_plan(plan_reference)
	with _as(ACCOUNTING_OFFICER):
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key("adopt-plan"))
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(STATUTORY):
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=_key("approve-plan"),
		)

	plan_version = approved["plan_version"]
	# §5.5.2.2 — the AO records that the exact approved document was sent.
	# This is external dispatch evidence, not another approval.
	with _as(ACCOUNTING_OFFICER):
		treasury.record_treasury_submission(
			plan_version=plan_version,
			submitted_at=CLOCK["treasury_submitted"],
			channel="Official correspondence",
			destination="National Treasury",
			dispatch_reference="MOH/APP/2027/001",
			exact_document_confirmed=True,
			idempotency_key=_key("treasury-submission"),
		)
	frappe.set_user("Administrator")
	published = publication_pipeline.publish_annual_plan(plan_version=plan_version, idempotency_key=_key("publish-plan"))
	return {**approved, "publication_result": published.get("result"), "publication": published.get("publication")}


def _stamp_design_clock(plan_reference: str) -> None:
	"""§14.4–14.6 exact instants onto the evidence rows the commands wrote."""
	plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	version = frappe.db.get_value("Annual Plan", plan_name, "active_version") or frappe.db.get_value("Annual Plan", plan_name, "open_successor_version")
	roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": FY}, pluck="name")
	dpp_versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": ("in", roots or ("",))}, pluck="name")
	for submission in frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ("in", dpp_versions or ("",))}, pluck="name"):
		frappe.db.set_value("Departmental Plan Submission", submission, "submitted_at", CLOCK["dpp_submitted"], update_modified=False)
	tasks = frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": FY}, pluck="name")
	for decision in frappe.get_all("Departmental Plan Validation Decision", filters={"task": ("in", tasks or ("",)), "decision": "Accept departmental plan"}, pluck="name"):
		frappe.db.set_value("Departmental Plan Validation Decision", decision, "decided_at", CLOCK["dpp_accepted"], update_modified=False)
	if not version:
		return
	for decision in frappe.get_all(
		"Plan Finance Decision",
		filters={"task": ("in", frappe.get_all("Plan Finance Task", filters={"plan_version": version}, pluck="name") or ("",)), "decision": "Confirm plan funding"},
		pluck="name",
	):
		frappe.db.set_value("Plan Finance Decision", decision, "decided_at", CLOCK["finance_confirmed"], update_modified=False)
	frappe.db.set_value(
		"Annual Plan Version", version,
		{"submitted_at": CLOCK["plan_submitted"], "activated_at": CLOCK["publication_acknowledged"]}, update_modified=False,
	)
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


def upsert_planning_base(*, commit: bool = False) -> dict[str, Any]:
	"""The §14.4–14.6 integrated baseline. Idempotent by stable state: a rerun
	that finds the FY 2027/28 Annual Plan already Active returns it untouched
	(§14.10 — no duplicate root, Version, entry, allocation, task, decision
	or publication attempt)."""
	_guard()
	_actors()
	# §13: the canonical world's own fixture-verified rules, before anything
	# that has to resolve one.
	ensure_profiles()
	prereqs = verify_prerequisites()
	_destination()

	existing = frappe.db.get_value("Annual Plan", {"fiscal_year": FY}, ["name", "plan_reference", "active_version"], as_dict=True)
	if existing and existing.active_version:
		if commit:
			frappe.db.commit()
		return {"ok": True, "idempotent": True, "plan_reference": existing.plan_reference, "active_version": existing.active_version}
	if existing:
		frappe.throw(
			f"An Annual Plan exists mid-lifecycle ({existing.plan_reference}) — an isolated profile is loaded. "
			"Run reset_planning_seed() before reseeding the integrated baseline (§14.10)."
		)
	if frappe.db.exists("Departmental Plan", {"fiscal_year": FY}):
		# a leftover pre-Plan profile world: reset, then build (stale journal rows replay otherwise)
		reset_planning_seed()
		_destination()

	with _intake_open():
		# PLN-CHG-001 v1.13 §14.4/§14.5 (SEED-001) — the DHI departmental plan
		# carries both Need-1 (the existing single-department item) and
		# Need-4 (Digital Health's half of the harmonized combined item) as
		# two entries in the same DPP, submitted and accepted together.
		built = _build_accepted_dpp(
			prereqs,
			extra_need_fundings=[
				{
					"need": NEED_DHI_LAPTOPS,
					"budget_line": prereqs["bl_hwd"],
					"amount": NEED_DHI_LAPTOPS_AMOUNT,
					"classification": "Goods",
				}
			],
		)
		hrmd_entry_id = _build_hrmd_laptops_dpp(prereqs)
		item_id, combined_item_id = _form_each_and_combined_items(built["accepted"]["annual_plan"], prereqs)
		task = frappe.get_doc("Plan Finance Task", _request_funding(built["accepted"]["annual_plan"]))
		with _as(FINANCE):
			from kentender_procurement.procurement_planning.services import plan_finance

			plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_key("confirm-funding"))
		approved = _govern_and_publish(built["accepted"]["annual_plan"])
	_stamp_design_clock(built["accepted"]["annual_plan"])
	if commit:
		frappe.db.commit()
	return {
		"ok": True, "idempotent": False,
		"plan_reference": built["accepted"]["annual_plan"],
		"plan_item": item_id,
		"combined_plan_item": combined_item_id,
		"hrmd_entry": hrmd_entry_id,
		"publication_result": approved["publication_result"],
	}


# --- isolated profiles (§14.10 — mutually exclusive with the baseline) -------


def reset_planning_seed(*, commit: bool = False) -> dict[str, int]:
	"""Remove every Planning row on FY 2027/28 and every NS-stamped row, the
	Need usage projection activation published (reversed through the same
	published channel), and the seed's own command-journal rows."""
	from uuid import uuid4

	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake

	_guard()
	frappe.set_user("Administrator")
	accepted_revision = needs_intake.current_accepted_revision_of(NEED, FY)
	if accepted_revision and needs_usage.is_actively_included(accepted_revision):
		needs_usage.project_planning_usage(
			departmental_need=NEED, accepted_revision=accepted_revision, usage="Not included",
			source_event_id=f"pln-seed-reset:{uuid4().hex}", source_event_time=now_datetime(), user="Administrator",
		)
	deleted = _wipe_fiscal_year(FY)
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
			organisation_unit=prereqs["dhi"], fiscal_year=FY, idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
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


def validate_planning_seed() -> list[dict[str, Any]]:
	"""§14.10 — validate the integrated baseline through the same domain
	services commands use, returning check rows for the core validator."""
	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake, plan_read, plan_requisition

	checks: list[dict[str, Any]] = []

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"planning.v112.{name}", "ok": bool(ok), "detail": detail})

	plan_row = frappe.db.get_value("Annual Plan", {"fiscal_year": FY}, ["name", "plan_reference", "active_version"], as_dict=True)
	check("plan.exists", bool(plan_row), str(plan_row))
	if not plan_row:
		return checks
	check("plan.active", bool(plan_row.active_version), str(plan_row.active_version))
	if not plan_row.active_version:
		return checks

	plan = plan_read.get_annual_plan(plan_reference=plan_row.plan_reference, user=PLANNER)
	view = plan["active_view"]
	check("active_view", view is not None)
	# PLN-CHG-001 v1.13 §14.5/SEED-001 §3.6 — the integrated baseline now
	# carries the pre-existing single-department item plus the harmonized
	# two-department combined item: 2 items, KES 130,000,000 combined.
	check("active.two_items", bool(view and view["summary"]["plan_items"] == 2), str(view and view["summary"]))
	check("active.value_130m", bool(view and "130,000,000" in view["summary"]["value_display"]))
	check("active.activated_display_15_00_eat", bool(view and view["summary"]["activated_display"] == "10 Dec 2026, 15:00 EAT"), str(view and view["summary"]["activated_display"]))
	check("active.two_items", bool(view and view["summary"]["plan_items"] == 2))
	if view and view["items"]:
		item = view["items"][0]
		# PLN-CHG-001 v1.23 — the approved baseline is the only schedule the
		# MVP keeps, and it lives on the item detail, not on the Active row
		# (which carries planned scope and remaining allowance).
		detail = plan_read.get_plan_item(plan_item_id=item["plan_item_id"], user=PLANNER)
		check("item.baseline_1_may_2027", any(
			r["milestone"] == "invitation" and r["date"] == "2027-05-01" for r in detail["baseline"]["rows"]
		))
		eligibility = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item["plan_item_id"], user=PLANNER)
		check("eligibility.eligible", eligibility["eligible"])
		check("eligibility.remaining_80m", eligibility["remaining_value"] == 80000000)
		check("eligibility.qty_1", eligibility["remaining_quantity"] == 1)
	if view and len(view["items"]) > 1:
		combined = view["items"][1]
		combined_detail = plan_read.get_plan_item(plan_item_id=combined["plan_item_id"], user=PLANNER)
		check("combined.baseline_15_may_2027", any(
			r["milestone"] == "invitation" and r["date"] == "2027-05-15" for r in combined_detail["baseline"]["rows"]
		))
		combined_eligibility = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=combined["plan_item_id"], user=PLANNER)
		# REQ-CHG-001 v1.6 D7 chains its own seed straight after this one in
		# `make seed-kentender-mvp-v1` and authorises a Requisition against this
		# exact combined item — once that has run, "eligible with the full
		# 250/50m remaining" is no longer the true position (it is legitimately
		# fully drawn down), so these three checks only apply to a
		# Planning-only world with no Requisition against this item yet.
		drawn_down = bool(frappe.db.exists("Plan Drawdown Reference", {"plan_item_id": combined["plan_item_id"], "drawdown_state": "Active"}))
		if not drawn_down:
			check("combined.eligibility.eligible", combined_eligibility["eligible"])
			check("combined.eligibility.remaining_50m", combined_eligibility["remaining_value"] == 50000000)
			check("combined.eligibility.qty_250", combined_eligibility["remaining_quantity"] == 250)
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
	accepted_revision = needs_intake.current_accepted_revision_of(NEED, FY)
	check("need_usage.fully_included", bool(accepted_revision) and needs_usage.is_actively_included(accepted_revision), str(accepted_revision))
	return checks
