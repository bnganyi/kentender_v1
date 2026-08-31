# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §14 — the deterministic Planning seed (Phase 11).

The integrated §14.4–14.6 baseline is driven through the real §8.2 commands
with the named §14.2 role actors (never Administrator for a business
decision), then the §14 design-clock instants are stamped onto the evidence
rows the commands produced — the NDS seed's proven pattern. Isolated
profiles (§14.10) each rebuild the MOH Planning world to their own state and
are therefore mutually exclusive with the integrated baseline; the §14.7
direct-requirement fixture is the one exception (a Draft, direct-only DPP in
the *other* department, which touches no Annual Plan and coexists safely).

Identifier note (the NDS-seed precedent, recorded there first): the live
Configuration & Governance records are ``MOH-DIR-DHP`` / ``MOH-DIR-HRMD``;
the spec writes these as ``OU-MOH-DHI`` / ``OU-MOH-HRMD``. The live
identifiers are authoritative — seeds never invent a fallback record
(§14.1) — so every server-generated reference that embeds the OU code
carries the live code (e.g. ``DPP-MOH-MOH-DIR-DHP-2027-001`` rather than
§14.4's ``DPP-MOH-DHI-2027-001``), and sequence-scanned identifiers start
at the first free number on this site rather than §14.5's illustrative
``PPI-MOH-2027-021``. The *stable* identifiers (Need, Plan root, actor
emails, Budget Line references, window instants, amounts, dates, titles)
match §14 exactly.

§14.9 (KEBS ×2) fails loudly by design on this repository: no authoritative
KEBS Budget Line or KEBS Strategic Objective exists in Budget's or
Strategy's own approved seed contracts, §14.3 names only MOH fixtures, and
§14.1 forbids inventing either. `seed_kebs_profiles` verifies and names the
exact missing prerequisites instead of fabricating them.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import add_days, now_datetime
from frappe.utils.password import update_password

PLAYWRIGHT_NS = "KENTENDER_PLAYWRIGHT"
NS = "KENTENDER_MVP_1_R1_PLN"

PE = "PE-MOH"
FY = "FY-2027-2028"
CTX = "CTX-MOH-2027-2028"
OU_DHI = "MOH-DIR-DHP"  # spec: OU-MOH-DHI — Digital Health (live id authoritative)
OU_HRMD = "MOH-DIR-HRMD"  # spec: OU-MOH-HRMD

NEED = "NDS-MOH-2027-0001"
BL_DHI = "MOH-BL-DHI-2027"
BL_HWD = "MOH-BL-HWD-2027"
OBJECTIVE_TITLE = "Strengthen interoperable national digital health services"

WINDOW_OPENS = "2026-10-01 00:00:00"
WINDOW_CLOSES = "2026-11-30 23:59:59"
DESTINATION_ID = "MOH-APP-SANDBOX-v1"

AUTHOR = "grace.wanjiku@moh.example.test"
HOD = "peter.kimani@moh.example.test"
ACTING_HOD = "julia.njeri@moh.example.test"
PLANNER = "mercy.kilonzo@moh.example.test"
BUDGET_OFFICER = "moh.budget.officer@example.test"
ACCOUNTING_OFFICER = "amina.hassan@moh.example.test"
STATUTORY = "moh.plan.approver@example.test"
AUDITOR = "peter.ouma@audit.example.test"
NO_CONTEXT = "no.context@example.test"

UNITS = (
	("UNIT-PROGRAMME", "Programme"),
	("UNIT-EACH", "Each"),
	("UNIT-SERVICE", "Service"),
)

# §14.5 planned dates and package text.
ITEM_VALUES = {
	"title": "National digital health infrastructure upgrade",
	"description": (
		"Procure and implement the national digital health infrastructure "
		"upgrade as one integrated FY 2027/28 programme."
	),
	"aggregation_reason": "",
	"invitation_date": "2027-05-01",
	"bid_opening_date": "2027-05-23",
	"evaluation_completion_date": "2027-06-23",
	"award_approval_date": "2027-07-10",
	"award_notification_date": "2027-07-14",
	"contract_signing_date": "2027-08-01",
	"delivery_completion_date": "2027-08-31",
}

# §14.7 isolated direct-requirement fixture — a Digital Health direct entry
# (its pinned MOH-BL-DHI-2027 Budget Line is department-scoped to Digital
# Health, so the entry can only live in the DHI departmental plan, where the
# accepted Need also projects: the profile is the mixed-DPP proof).
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
	"unit": "UNIT-SERVICE",
	"required_by_date": "2027-10-31",
	"indicative_amount": 20000000,
}

# §14.8 isolated combined-source fixture (DES-09A text).
COMBINED_A = {  # HRMD
	"title": "Clinical training laptops for digital health rollout",
	"description": "Laptop computers for clinical training during the national digital health rollout.",
	"expected_operational_result": "Provide the equipment required for staff training on the deployed digital health services.",
	"quantity": 200, "unit": "UNIT-EACH", "required_by_date": "2027-12-31",
	"indicative_amount": 48000000,
}
COMBINED_B = {  # Digital Health
	"title": "Clinical deployment laptops for digital health rollout",
	"description": "Laptop computers for deployment at priority facilities during the national digital health rollout.",
	"expected_operational_result": "Provide endpoint equipment required to use the deployed digital health services.",
	"quantity": 300, "unit": "UNIT-EACH", "required_by_date": "2027-12-31",
	"indicative_amount": 72000000,
}
COMBINED_ITEM_VALUES = {
	"title": "Clinical laptops for digital health rollout",
	"description": (
		"Procure clinical training and deployment laptops for the national "
		"digital health rollout as one combined FY 2027/28 goods package."
	),
	"aggregation_reason": (
		"Training and deployment laptops share one specification and one "
		"delivery window, so a single combined tender lot secures better "
		"pricing than two separate department-level procurements."
	),
	"invitation_date": "2027-05-01",
	"bid_opening_date": "2027-05-23",
	"evaluation_completion_date": "2027-06-23",
	"award_approval_date": "2027-07-10",
	"award_notification_date": "2027-07-14",
	"contract_signing_date": "2027-08-01",
	"delivery_completion_date": "2027-12-31",
}

# §14.4–14.6 design-clock instants, stamped after the commands run. The
# module's read models render every stored datetime as UTC converted to EAT
# (§12.13 — `plan_read._eat`), so these are stored as the UTC equivalents of
# §14's stated EAT times and DISPLAY as §14's exact values.
CLOCK = {
	"dpp_submitted": "2026-11-25 07:00:00",  # 25 Nov 2026, 10:00 EAT
	"dpp_accepted": "2026-11-27 11:00:00",  # 27 Nov 2026, 14:00 EAT
	"finance_confirmed": "2026-12-04 07:00:00",  # 4 Dec 2026, 10:00 EAT
	"plan_submitted": "2026-12-05 07:00:00",  # 5 Dec 2026, 10:00 EAT
	"ao_adopted": "2026-12-08 07:00:00",  # 8 Dec 2026, 10:00 EAT
	"statutory_approved": "2026-12-09 08:00:00",  # 9 Dec 2026, 11:00 EAT
	"publication_attempted": "2026-12-10 11:55:00",  # 10 Dec 2026, 14:55 EAT
	"publication_acknowledged": "2026-12-10 12:00:00",  # 10 Dec 2026, 15:00 EAT
}

_V12_DOCTYPES = (
	# dependents first, roots last
	"Plan Drawdown Reference",
	"Annual Plan Publication",
	"Plan Reservation Reference",
	"Plan Governance Decision",
	"Plan Governance Task",
	"Plan Finance Decision",
	"Plan Finance Task",
	"Plan Source Allocation",
	"Annual Plan Item",
	"Annual Plan Version",
	"Annual Plan",
	"Departmental Plan Validation Decision",
	"Departmental Plan Validation Task",
	"Departmental Plan Submission",
	"Departmental Plan Entry",
	"Departmental Plan Version",
	"Departmental Plan",
	"Departmental Plan Submission Window",
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
	name = frappe.db.get_value("Budget Line", {"generated_reference": reference}, "name")
	if not name:
		return ""
	active = frappe.get_all(
		"Budget Line Version", filters={"budget_line": name}, fields=["budget_version"],
	)
	for row in active:
		if frappe.db.get_value("Budget Version", row.budget_version, "status") == "Active":
			return name
	return ""


def _objective() -> str:
	node = frappe.db.get_value(
		"Strategy Node", {"title": OBJECTIVE_TITLE, "node_type": "Strategic Objective"}, "name"
	)
	return node or ""


def verify_prerequisites() -> dict[str, str]:
	"""§14.1/§14.3 — every authoritative prerequisite present and usable, or
	one loud failure naming exactly what is absent. Nothing is invented."""
	missing: list[str] = []

	def need(label: str, ok) -> None:
		if not ok:
			missing.append(label)

	need(f"Procuring Entity {PE}", frappe.db.exists("Procuring Entity", PE))
	need(f"Financial Year {FY}", frappe.db.exists("Financial Year", FY))
	need(f"PE Fiscal Year Context {CTX}", frappe.db.exists("PE Fiscal Year Context", CTX))
	need(f"Organisation Unit {OU_DHI} (spec: OU-MOH-DHI)", frappe.db.exists("Organisation Unit", OU_DHI))
	need(f"Organisation Unit {OU_HRMD} (spec: OU-MOH-HRMD)", frappe.db.exists("Organisation Unit", OU_HRMD))
	for title in ("Non-consulting services", "Consulting services", "Goods"):
		need(
			f"Requirement Type {title} (Active)",
			frappe.db.get_value("Requirement Type", title, "status") == "Active",
		)
	need(
		"Procurement Method Open Tender (Active)",
		frappe.db.get_value("Procurement Method", "Open Tender", "status") == "Active",
	)
	bl_dhi = _budget_line(BL_DHI)
	bl_hwd = _budget_line(BL_HWD)
	need(f"Budget Line {BL_DHI} with an Active Budget Version", bl_dhi)
	need(f"Budget Line {BL_HWD} with an Active Budget Version", bl_hwd)
	objective = _objective()
	need(f"Active Strategic Objective '{OBJECTIVE_TITLE}'", objective)
	# through the published contract only (D5) — a non-empty current accepted
	# version IS "Accepted for planning".
	from kentender_procurement.procurement_planning.services import needs_intake

	need(
		f"Departmental Need {NEED} Accepted for planning",
		needs_intake.current_accepted_version_of(NEED, PE, FY),
	)
	if missing:
		frappe.throw(
			"PLN §14 seed prerequisites are absent or differ — seeds never invent "
			"a substitute (§14.1). Missing: " + "; ".join(missing)
		)
	return {"bl_dhi": bl_dhi, "bl_hwd": bl_hwd, "objective": objective}


# --- configuration the Planning seed itself owns -----------------------------


def _units() -> None:
	for code, label in UNITS:
		if frappe.db.exists("Unit Of Measure", code):
			frappe.db.set_value(
				"Unit Of Measure", code, {"unit_label": label, "status": "Active"}, update_modified=False
			)
			continue
		frappe.get_doc(
			{
				"doctype": "Unit Of Measure", "unit_code": code, "unit_label": label,
				"status": "Active", "fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)


def _submission_window() -> None:
	"""§14.1 — 1 Oct to 30 Nov 2026 EAT inclusive, stored exactly."""
	values = {"opens_at": WINDOW_OPENS, "closes_at": WINDOW_CLOSES}
	existing = frappe.db.get_value("Departmental Plan Submission Window", {"pe_fy_context": CTX})
	if existing:
		frappe.db.set_value("Departmental Plan Submission Window", existing, values, update_modified=False)
		return
	frappe.get_doc(
		{
			"doctype": "Departmental Plan Submission Window",
			"pe_fy_context": CTX, "fixture_namespace": NS, **values,
		}
	).insert(ignore_permissions=True)


def _destination() -> None:
	from kentender_procurement.procurement_planning.services.plan_publication import (
		DESTINATION_ADAPTER,
	)

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


def _ensure_role(name: str) -> None:
	if not frappe.db.exists("Role", name):
		frappe.get_doc({"doctype": "Role", "role_name": name, "desk_access": 1}).insert(
			ignore_permissions=True
		)


def _user(email: str, full_name: str, roles: tuple[str, ...]) -> str:
	for role in roles:
		_ensure_role(role)
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User", "email": email, "first_name": parts[0],
				"last_name": " ".join(parts[1:]), "full_name": full_name,
				"enabled": 1, "user_type": "System User", "send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("User", email, {"enabled": 1, "full_name": full_name}, update_modified=False)
	if roles:
		frappe.get_doc("User", email).add_roles("Desk User", *roles)
	update_password(email, "Test@123")
	return email


def _user_permission(user: str, doctype: str, value: str) -> None:
	if frappe.db.exists("User Permission", {"user": user, "allow": doctype, "for_value": value}):
		return
	frappe.get_doc(
		{
			"doctype": "User Permission", "user": user, "allow": doctype,
			"for_value": value, "apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)


def _actors() -> None:
	"""§14.2 — native roles and User Permission rows only. The NDS seed
	already provisions Grace/Peter/Julia's departmental identities; this adds
	the Planning-side roles and the actors §14.2 introduces. Julia's acting
	window (26–30 Nov 2026) is expressed exactly the NDS way: her scoped
	User Permission row exists for the approved period and is removed when it
	ends — no validity fields are invented."""
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()
	_user(AUTHOR, "Grace Wanjiku", ("Departmental Author",))
	_user(HOD, "Dr Peter Kimani", ("Departmental Author", "Head of User Department"))
	_user(ACTING_HOD, "Julia Njeri", ("Head of User Department",))
	_user(PLANNER, "Mercy Kilonzo", ("Procurement Planner",))
	_user(BUDGET_OFFICER, "MOH Budget Officer", ("Budget Officer",))
	_user(ACCOUNTING_OFFICER, "Amina Hassan", ("Accounting Officer",))
	_user(STATUTORY, "MOH statutory approver", ("Plan Statutory Approver",))
	_user(AUDITOR, "Peter Ouma", ("Planning Auditor",))
	_user(NO_CONTEXT, "No-context User", ())

	for user in (AUTHOR, HOD, PLANNER, BUDGET_OFFICER, ACCOUNTING_OFFICER, STATUTORY, AUDITOR):
		_user_permission(user, "Procuring Entity", PE)
		_user_permission(user, "Financial Year", FY)
	for user in (AUTHOR, HOD):
		for unit in (OU_DHI, OU_HRMD):
			_user_permission(user, "Organisation Unit", unit)
	_user_permission(ACTING_HOD, "Procuring Entity", PE)
	_user_permission(ACTING_HOD, "Financial Year", FY)
	_user_permission(ACTING_HOD, "Organisation Unit", OU_DHI)


# --- the §14.4–14.6 integrated baseline, driven through real commands --------


@contextmanager
def _open_window():
	"""The §14.1 window is Closed at any realistic seeding time; widen it for
	the build and restore the exact instants afterwards (NDS pattern)."""
	window = frappe.db.get_value("Departmental Plan Submission Window", {"pe_fy_context": CTX})
	if not window:
		frappe.throw("The §14.1 DPP submission window is missing — run _submission_window() first.")
	now = now_datetime()
	frappe.db.set_value(
		"Departmental Plan Submission Window", window,
		{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)}, update_modified=False,
	)
	try:
		yield
	finally:
		frappe.db.set_value(
			"Departmental Plan Submission Window", window,
			{"opens_at": WINDOW_OPENS, "closes_at": WINDOW_CLOSES}, update_modified=False,
		)


def _build_accepted_dpp(prereqs: dict[str, str]) -> dict[str, Any]:
	"""§14.4 — the Need-only DHI departmental plan through the real commands:
	Grace funds the projected Need entry, Peter submits, Mercy classifies and
	accepts, which auto-creates the Draft Annual Plan (§5.2)."""
	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
		plan_read,
	)

	with _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=PE, organisation_unit=OU_DHI, financial_year=FY,
			idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
		)
		entry_id = frappe.db.get_value(
			"Departmental Plan Entry",
			{"dpp_version": opened["current_version"], "need": NEED},
			"entry_id",
		)
		if not entry_id:
			frappe.throw(
				f"The accepted Need {NEED} did not project into the Draft DPP — "
				"check the Departmental Needs seed ran first (§14.10)."
			)
		funded = dpp_lifecycle.save_need_funding(
			dpp_version=opened["current_version"], entry_id=entry_id,
			budget_line=prereqs["bl_dhi"], indicative_amount=80000000,
			expected_record_version=opened["record_version"], idempotency_key=_key("fund-need"),
		)
	with _as(HOD):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=funded["record_version"], idempotency_key=_key("submit-dpp"),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLANNER):
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={entry_id: "Non-consulting services"},
			task_token=task.task_token, idempotency_key=_key("accept-dpp"),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
	return {"accepted": accepted, "plan": plan, "entry_id": entry_id}


def _form_and_confirm(plan: dict[str, Any], prereqs: dict[str, str]) -> str:
	"""§14.5/§14.6 — one Plan Item from the Need source, completed with the
	exact §14.5 package and schedule, Finance-confirmed by the MOH Budget
	Officer against the real Budget contract (RSV per §14.6)."""
	from kentender_procurement.procurement_planning.services import (
		plan_finance,
		plan_read,
		plan_workbench,
	)

	with _as(PLANNER):
		formed = plan_workbench.form_plan_items(
			plan_version=plan["version_reference"],
			dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"],
			idempotency_key=_key("form-item"),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		plan_workbench.save_plan_item(
			plan_item=item_id,
			values={**ITEM_VALUES, "strategic_objective": prereqs["objective"]},
			expected_record_version=item["record_version"], idempotency_key=_key("save-item"),
		)
		item = plan_read.get_plan_item(plan_item_id=item_id)
		requested = plan_finance.request_finance_confirmation(
			plan_item=item_id, expected_record_version=item["record_version"],
			idempotency_key=_key("request-finance"),
		)
	task = frappe.get_doc("Plan Finance Task", requested["task"])
	with _as(BUDGET_OFFICER):
		read = plan_read.get_finance_task(task=task.name)
		plan_finance.confirm_funding(
			task=task.name, task_token=task.task_token,
			check_token=read["budget_check_token"], idempotency_key=_key("confirm-funding"),
		)
	return item_id


def _govern_and_publish(plan_reference: str) -> dict[str, Any]:
	"""§14.6 — Mercy submits, Amina adopts, the statutory approver approves,
	and PublishAnnualPlan runs automatically inside approval (§11.15),
	activating the Version on the sandbox acknowledgement."""
	from kentender_procurement.procurement_planning.services import plan_governance, plan_read

	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"],
			idempotency_key=_key("submit-plan"),
		)
	ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
	with _as(ACCOUNTING_OFFICER):
		adopted = plan_governance.adopt_and_submit_plan(
			task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key("adopt-plan"),
		)
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(STATUTORY):
		approved = plan_governance.approve_annual_plan(
			task=statutory_task.name, task_token=statutory_task.task_token,
			idempotency_key=_key("approve-plan"),
		)
	return approved


def _stamp_design_clock(plan_reference: str) -> None:
	"""§14.4–14.6 exact instants onto the evidence rows the commands wrote."""
	plan_name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	version = frappe.db.get_value("Annual Plan", plan_name, "active_version") or frappe.db.get_value(
		"Annual Plan", plan_name, "open_successor_version"
	)
	dpp_versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": ("in", frappe.get_all(
			"Departmental Plan", filters={"procuring_entity": PE, "fixture_namespace": NS}, pluck="name"
		) or ("",))},
		pluck="name",
	)
	for submission in frappe.get_all(
		"Departmental Plan Submission", filters={"dpp_version": ("in", dpp_versions or ("",))}, pluck="name"
	):
		frappe.db.set_value(
			"Departmental Plan Submission", submission, "submitted_at",
			CLOCK["dpp_submitted"], update_modified=False,
		)
	for decision in frappe.get_all(
		"Departmental Plan Validation Decision",
		filters={"decision": "Accept departmental plan"}, pluck="name",
	):
		if frappe.db.get_value("Departmental Plan Validation Decision", decision, "fixture_namespace") == NS:
			frappe.db.set_value(
				"Departmental Plan Validation Decision", decision, "decided_at",
				CLOCK["dpp_accepted"], update_modified=False,
			)
	for decision in frappe.get_all(
		"Plan Finance Decision", filters={"fixture_namespace": NS, "decision": "Confirm funding"},
		pluck="name",
	):
		frappe.db.set_value(
			"Plan Finance Decision", decision, "decided_at", CLOCK["finance_confirmed"],
			update_modified=False,
		)
	if version:
		frappe.db.set_value(
			"Annual Plan Version", version,
			{"submitted_at": CLOCK["plan_submitted"], "activated_at": CLOCK["publication_acknowledged"]},
			update_modified=False,
		)
		for stage, when in (
			("Accounting Officer adoption", CLOCK["ao_adopted"]),
			("Statutory approval", CLOCK["statutory_approved"]),
		):
			decision = frappe.db.get_value(
				"Plan Governance Decision", {"plan_version": version, "stage": stage}, "name"
			)
			if decision:
				frappe.db.set_value(
					"Plan Governance Decision", decision, "decided_at", when, update_modified=False
				)
		publication = frappe.db.get_value("Annual Plan Publication", {"plan_version": version}, "name")
		if publication:
			frappe.db.set_value(
				"Annual Plan Publication", publication,
				{
					"attempted_at": CLOCK["publication_attempted"],
					"acknowledged_at": CLOCK["publication_acknowledged"],
				},
				update_modified=False,
			)


def upsert_planning_base(*, commit: bool = False) -> dict[str, Any]:
	"""The §14.4–14.6 integrated baseline.

	Idempotent by stable state: a rerun that finds the MOH Annual Plan already
	Active returns it untouched (§14.10 — no duplicate root, Version, entry,
	allocation, task, decision, reservation or publication attempt)."""
	_guard()
	prereqs = verify_prerequisites()
	_units()
	_submission_window()
	_destination()
	_actors()

	existing = frappe.db.get_value(
		"Annual Plan", {"procuring_entity": PE, "financial_year": FY},
		["name", "plan_reference", "active_version"], as_dict=True,
	)
	if existing and existing.active_version:
		if commit:
			frappe.db.commit()
		return {
			"ok": True, "idempotent": True, "plan_reference": existing.plan_reference,
			"active_version": existing.active_version,
		}
	if existing:
		frappe.throw(
			f"An MOH Annual Plan exists mid-lifecycle ({existing.plan_reference}) — an "
			"isolated profile is loaded. Run reset_planning_seed() before reseeding "
			"the integrated baseline (§14.10)."
		)

	with _open_window():
		built = _build_accepted_dpp(prereqs)
		item_id = _form_and_confirm(built["plan"], prereqs)
		approved = _govern_and_publish(built["accepted"]["annual_plan"])
	_stamp_design_clock(built["accepted"]["annual_plan"])
	if commit:
		frappe.db.commit()
	return {
		"ok": True, "idempotent": False,
		"plan_reference": built["accepted"]["annual_plan"],
		"plan_item": item_id,
		"publication_result": approved["publication_result"],
	}


# --- isolated profiles (§14.10 — mutually exclusive with the baseline) -------


def reset_planning_seed(*, commit: bool = False) -> dict[str, int]:
	"""Remove every KENTENDER_MVP_1_R1_PLN Planning row, the real Budget
	reservations the Finance confirmations created, the Need usage
	projections activation published, and the seed's own command-journal
	rows (a journal row surviving its documents would replay a stale result
	on the next build)."""
	_guard()
	reservations = frappe.get_all(
		"Plan Reservation Reference", filters={"fixture_namespace": NS}, pluck="reservation",
	)
	# The Active baseline projected "Fully included" onto the Need — reverse
	# it through the SAME published channel (D5: Planning never writes a
	# Needs record directly; the event is the only path).
	from uuid import uuid4

	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake

	accepted_version = needs_intake.current_accepted_version_of(NEED, PE, FY)
	if accepted_version and needs_usage.is_actively_included(accepted_version):
		needs_usage.project_planning_usage(
			departmental_need=NEED, accepted_version=accepted_version, usage="Not included",
			source_event_id=f"pln-seed-reset:{uuid4().hex}",
			source_event_time=now_datetime(), user="Administrator",
		)
	deleted = clear_planning_fixture_rows(include_playwright=False, namespaces=(NS,))
	if reservations:
		frappe.db.delete("Funding Reservation", {"name": ("in", reservations)})
		deleted["Funding Reservation"] = len(reservations)
	journal = frappe.get_all(
		"Planning Command Journal", filters={"idempotency_key": ("like", "pln-seed:%")}, pluck="name"
	)
	frappe.db.delete("Planning Command Journal", {"name": ("in", journal or ("",))})
	deleted["Planning Command Journal"] = len(journal)
	if commit:
		frappe.db.commit()
	return deleted


def _fresh_profile_world() -> dict[str, str]:
	"""Reset FIRST, then rebuild the §14.1 configuration — the reset clears
	every NS row, the submission window and destination included, so
	recreating them must come after (found live: the original order deleted
	the window it had just upserted, and every submitting profile then
	failed with PLN_WINDOW_CLOSED)."""
	_guard()
	prereqs = verify_prerequisites()
	reset_planning_seed()
	_units()
	_submission_window()
	_destination()
	_actors()
	return prereqs


def seed_direct_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§14.7 — the Digital Health Draft DPP carrying both the projected
	accepted Need and the exact direct security-assessment entry (the mixed-
	DPP proof; the direct entry's pinned MOH-BL-DHI-2027 Budget Line is only
	eligible for this department). Never submitted, never in any Plan."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	prereqs = _fresh_profile_world()
	with _open_window(), _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(
			procuring_entity=PE, organisation_unit=OU_DHI, financial_year=FY,
			idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values={**DIRECT_FIXTURE, "budget_line": prereqs["bl_dhi"]},
			expected_record_version=opened["record_version"], idempotency_key=_key("add-direct"),
		)
	if commit:
		frappe.db.commit()
	return {
		"ok": True, "profile": "direct",
		"departmental_plan": opened["departmental_plan"], "entry_id": added["entry_id"],
	}


def seed_return_profile(*, commit: bool = False) -> dict[str, Any]:
	"""Submitted Plan returned by the Accounting Officer; the numbered
	correction Draft is open (§5.2/§12.10)."""
	from kentender_procurement.procurement_planning.services import plan_governance, plan_read

	prereqs = _fresh_profile_world()
	with _open_window():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		with _as(PLANNER):
			plan = plan_read.get_annual_plan(plan_reference=built["accepted"]["annual_plan"])
			submitted = plan_governance.submit_consolidated_plan(
				plan_version=plan["version_reference"], expected_record_version=plan["record_version"],
				idempotency_key=_key("submit-plan"),
			)
		ao_task = frappe.get_doc("Plan Governance Task", submitted["task"])
		with _as(ACCOUNTING_OFFICER):
			returned = plan_governance.return_plan_version(
				task=ao_task.name,
				reason="Confirm the planned contract-signing date against the delivery completion date.",
				task_token=ao_task.task_token, idempotency_key=_key("return-plan"),
			)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "return", "correction_version": returned["correction_version"]}


def seed_shortfall_profile(*, commit: bool = False) -> dict[str, Any]:
	"""An open Finance task whose required amount exceeds the Budget Line's
	available balance — DES-10's shortfall composition, live."""
	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
		plan_finance,
		plan_read,
		plan_workbench,
	)

	prereqs = _fresh_profile_world()
	with _open_window():
		with _as(AUTHOR):
			opened = dpp_lifecycle.open_departmental_plan(
				procuring_entity=PE, organisation_unit=OU_DHI, financial_year=FY,
				idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
			)
			entry_id = frappe.db.get_value(
				"Departmental Plan Entry",
				{"dpp_version": opened["current_version"], "need": NEED}, "entry_id",
			)
			# deliberately above MOH-BL-DHI-2027's KES 100,000,000 ceiling
			funded = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry_id,
				budget_line=prereqs["bl_dhi"], indicative_amount=150000000,
				expected_record_version=opened["record_version"], idempotency_key=_key("fund-need"),
			)
		with _as(HOD):
			submitted = dpp_lifecycle.submit_departmental_plan(
				dpp_version=opened["current_version"], certification_confirmed=True,
				expected_record_version=funded["record_version"], idempotency_key=_key("submit-dpp"),
			)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		with _as(PLANNER):
			accepted = dpp_validation.accept_departmental_plan(
				task=task.name, classifications={entry_id: "Non-consulting services"},
				task_token=task.task_token, idempotency_key=_key("accept-dpp"),
			)
			plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
			formed = plan_workbench.form_plan_items(
				plan_version=plan["version_reference"],
				dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
				mode="each", expected_record_version=plan["record_version"],
				idempotency_key=_key("form-item"),
			)
			item_id = formed["created_items"][0]
			item = plan_read.get_plan_item(plan_item_id=item_id)
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={**ITEM_VALUES, "strategic_objective": prereqs["objective"]},
				expected_record_version=item["record_version"], idempotency_key=_key("save-item"),
			)
			item = plan_read.get_plan_item(plan_item_id=item_id)
			requested = plan_finance.request_finance_confirmation(
				plan_item=item_id, expected_record_version=item["record_version"],
				idempotency_key=_key("request-finance"),
			)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "shortfall", "finance_task": requested["task"], "plan_item": item_id}


def seed_combined_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§14.8 — two Goods sources from two departments combined into one Plan
	Item (500 each · KES 120,000,000, DES-09A's package text). Isolated
	because its funding requirement exceeds the live baseline."""
	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
		plan_read,
		plan_workbench,
	)

	prereqs = _fresh_profile_world()
	with _open_window():
		# DHI: the accepted Need must still be covered, plus the deployment laptops
		with _as(AUTHOR):
			dhi = dpp_lifecycle.open_departmental_plan(
				procuring_entity=PE, organisation_unit=OU_DHI, financial_year=FY,
				idempotency_key=_key("open-dhi-dpp"), fixture_namespace=NS,
			)
			need_entry = frappe.db.get_value(
				"Departmental Plan Entry", {"dpp_version": dhi["current_version"], "need": NEED}, "entry_id",
			)
			funded = dpp_lifecycle.save_need_funding(
				dpp_version=dhi["current_version"], entry_id=need_entry,
				budget_line=prereqs["bl_dhi"], indicative_amount=80000000,
				expected_record_version=dhi["record_version"], idempotency_key=_key("fund-need"),
			)
			added_b = dpp_lifecycle.save_direct_requirement(
				dpp_version=dhi["current_version"],
				values={**COMBINED_B, "budget_line": prereqs["bl_dhi"]},
				expected_record_version=funded["record_version"], idempotency_key=_key("add-deploy"),
			)
		with _as(HOD):
			dhi_submitted = dpp_lifecycle.submit_departmental_plan(
				dpp_version=dhi["current_version"], certification_confirmed=True,
				expected_record_version=added_b["record_version"], idempotency_key=_key("submit-dhi"),
			)
		dhi_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": dhi_submitted["task"]}
		)
		with _as(PLANNER):
			accepted = dpp_validation.accept_departmental_plan(
				task=dhi_task.name,
				classifications={need_entry: "Non-consulting services", added_b["entry_id"]: "Goods"},
				task_token=dhi_task.task_token, idempotency_key=_key("accept-dhi"),
			)

		# HRMD: the training laptops
		with _as(AUTHOR):
			hrmd = dpp_lifecycle.open_departmental_plan(
				procuring_entity=PE, organisation_unit=OU_HRMD, financial_year=FY,
				idempotency_key=_key("open-hrmd-dpp"), fixture_namespace=NS,
			)
			added_a = dpp_lifecycle.save_direct_requirement(
				dpp_version=hrmd["current_version"],
				values={**COMBINED_A, "budget_line": prereqs["bl_hwd"]},
				expected_record_version=hrmd["record_version"], idempotency_key=_key("add-train"),
			)
		with _as(HOD):
			hrmd_submitted = dpp_lifecycle.submit_departmental_plan(
				dpp_version=hrmd["current_version"], certification_confirmed=True,
				expected_record_version=added_a["record_version"], idempotency_key=_key("submit-hrmd"),
			)
		hrmd_task = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": hrmd_submitted["task"]}
		)
		with _as(PLANNER):
			dpp_validation.accept_departmental_plan(
				task=hrmd_task.name, classifications={added_a["entry_id"]: "Goods"},
				task_token=hrmd_task.task_token, idempotency_key=_key("accept-hrmd"),
			)
			plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
			laptop_entries = [
				row["dpp_entry"] for row in plan["unallocated_sources"]
				if "laptops" in row["title"]
			]
			formed = plan_workbench.form_plan_items(
				plan_version=plan["version_reference"], dpp_entries=laptop_entries,
				mode="combined", expected_record_version=plan["record_version"],
				idempotency_key=_key("form-combined"),
			)
			item_id = formed["created_items"][0]
			item = plan_read.get_plan_item(plan_item_id=item_id)
			plan_workbench.save_plan_item(
				plan_item=item_id,
				values={**COMBINED_ITEM_VALUES, "strategic_objective": prereqs["objective"]},
				expected_record_version=item["record_version"], idempotency_key=_key("save-combined"),
			)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "combined", "plan_item": item_id}


def seed_stale_profile(*, commit: bool = False) -> dict[str, Any]:
	"""Source correction required (§4.9/§12.7): the allocated DPP entry's
	department resubmits and Mercy re-accepts, leaving the Draft item pinned
	to the predecessor entry document."""
	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle,
		dpp_validation,
		plan_read,
		plan_workbench,
	)

	prereqs = _fresh_profile_world()
	with _open_window():
		built = _build_accepted_dpp(prereqs)
		with _as(PLANNER):
			plan = built["plan"]
			formed = plan_workbench.form_plan_items(
				plan_version=plan["version_reference"],
				dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
				mode="each", expected_record_version=plan["record_version"],
				idempotency_key=_key("form-item"),
			)
			item_id = formed["created_items"][0]
		dpp_root = frappe.db.get_value(
			"Departmental Plan", {"dpp_reference": built["accepted"]["dpp_reference"]}
		)
		with _as(HOD):
			update = dpp_lifecycle.create_departmental_plan_update(
				departmental_plan=dpp_root,
				expected_record_version=frappe.db.get_value("Departmental Plan", dpp_root, "record_version"),
				idempotency_key=_key("dpp-update"),
			)
			resubmitted = dpp_lifecycle.submit_departmental_plan(
				dpp_version=update["current_version"], certification_confirmed=True,
				expected_record_version=update["record_version"], idempotency_key=_key("resubmit-dpp"),
			)
		task2 = frappe.get_doc(
			"Departmental Plan Validation Task", {"task_reference": resubmitted["task"]}
		)
		with _as(PLANNER):
			dpp_validation.accept_departmental_plan(
				task=task2.name, classifications={built["entry_id"]: "Non-consulting services"},
				task_token=task2.task_token, idempotency_key=_key("re-accept-dpp"),
			)
		flagged = plan_read.get_plan_item(plan_item_id=item_id, user=PLANNER)
		if not flagged["source_correction_required"]:
			frappe.throw("Stale profile did not produce the source-correction flag.")
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "stale", "plan_item": item_id}


def seed_successor_profile(*, commit: bool = False) -> dict[str, Any]:
	"""The Active baseline plus an open Draft successor (§5.2/PLN-DES-14's
	Prepare plan update outcome)."""
	from kentender_procurement.procurement_planning.services import plan_publication

	prereqs = _fresh_profile_world()
	with _open_window():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		_govern_and_publish(built["accepted"]["annual_plan"])
		with _as(PLANNER):
			begun = plan_publication.begin_plan_update(
				plan_reference=built["accepted"]["annual_plan"], idempotency_key=_key("begin-update"),
			)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "successor", "successor_version": begun["successor_version"]}


def seed_publication_failure_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§12.11 — an approved Version whose only publication attempt Failed;
	the System-Manager retry path is live. The sandbox adapter cannot fail on
	its own, so the seed patches `_transmit` for this one approval — the same
	technique the Phase 9 tests use, and the reason this profile exists at
	all (§14.10 names it; the happy path never reaches it)."""
	from unittest.mock import patch

	from kentender_procurement.procurement_planning.services import plan_publication

	prereqs = _fresh_profile_world()
	with _open_window():
		built = _build_accepted_dpp(prereqs)
		_form_and_confirm(built["plan"], prereqs)
		with patch.object(plan_publication, "_transmit", return_value=("Failed", "")):
			approved = _govern_and_publish(built["accepted"]["annual_plan"])
	if approved["publication_result"] != "Failed":
		frappe.throw("Publication-failure profile did not produce a Failed attempt.")
	publication = frappe.db.get_value(
		"Annual Plan Publication", {"result": "Failed", "fixture_namespace": NS}, "name"
	)
	if commit:
		frappe.db.commit()
	return {"ok": True, "profile": "publication_failure", "publication": publication}


def seed_kebs_profiles(*, commit: bool = False) -> dict[str, Any]:
	"""§14.9 — fails loudly by design on this repository (see the module
	docstring): the KEBS PE exists, but no authoritative KEBS Budget Line or
	Strategic Objective does, §14.3 names only MOH fixtures, and §14.1
	forbids inventing either. This function names the exact gap so the
	failure is a decision surface, not a mystery."""
	missing = []
	if not frappe.db.exists("Procuring Entity", "PE-KEBS"):
		missing.append("Procuring Entity PE-KEBS")
	if not frappe.get_all("Budget Line", filters={"generated_reference": ("like", "%KEBS%")}, limit=1):
		missing.append("an authoritative KEBS Budget Line (Budget module seed)")
	if not frappe.get_all(
		"Strategic Plan", filters={"procuring_entity_id": "PE-KEBS"}, limit=1
	):
		missing.append("an authoritative KEBS Strategic Plan/Objective (Strategy module seed)")
	frappe.throw(
		"§14.9 KEBS profiles cannot be seeded: seeds never invent a Budget Line or "
		"Strategic Objective (§14.1), and the owning modules' approved seed "
		"contracts provide none for PE-KEBS. Missing: " + "; ".join(missing)
	)


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
	deleted: dict[str, int] = {}
	selected: list[str] = list(namespaces)
	if include_playwright:
		selected.append(PLAYWRIGHT_NS)
	for doctype in _V12_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		filters: dict[str, Any] = {}
		if not include_canonical:
			if not selected:
				continue
			filters["fixture_namespace"] = ("in", selected)
		rows = frappe.get_all(doctype, filters=filters, pluck="name")
		for name in rows:
			frappe.delete_doc(
				doctype, name, force=True, ignore_permissions=True, delete_permanently=True
			)
		deleted[doctype] = len(rows)
	return deleted


def validate_planning_seed() -> list[dict[str, Any]]:
	"""§14.10 — validate the integrated baseline through the same domain
	services commands use, returning check rows for the core validator."""
	from kentender_procurement.procurement_planning.services import plan_read, plan_requisition

	checks: list[dict[str, Any]] = []

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"planning.v12.{name}", "ok": bool(ok), "detail": detail})

	plan_row = frappe.db.get_value(
		"Annual Plan", {"procuring_entity": PE, "financial_year": FY},
		["name", "plan_reference", "active_version"], as_dict=True,
	)
	check("plan.exists", bool(plan_row), str(plan_row))
	if not plan_row:
		return checks
	check("plan.active", bool(plan_row.active_version), str(plan_row.active_version))
	if not plan_row.active_version:
		return checks

	plan = plan_read.get_annual_plan(plan_reference=plan_row.plan_reference, user=PLANNER)
	check("active_view", plan["active_view"] is not None)
	check(
		"active.one_item",
		bool(plan["active_view"] and plan["active_view"]["summary"]["plan_items"] == 1),
		str(plan["active_view"] and plan["active_view"]["summary"]),
	)
	check(
		"active.value_80m",
		bool(plan["active_view"] and "80,000,000" in plan["active_view"]["summary"]["value_display"]),
	)
	check(
		"active.activated_display_15_00_eat",
		bool(
			plan["active_view"]
			and plan["active_view"]["summary"]["activated_display"] == "10 Dec 2026, 15:00 EAT"
		),
		str(plan["active_view"] and plan["active_view"]["summary"]["activated_display"]),
	)
	if plan["active_view"] and plan["active_view"]["items"]:
		item_id = plan["active_view"]["items"][0]["plan_item_id"]
		eligibility = plan_requisition.get_requisition_eligible_plan_item(
			plan_item_id=item_id, user=PLANNER
		)
		check("eligibility.eligible", eligibility["eligible"])
		check("eligibility.remaining_80m", eligibility["remaining_value"] == 80000000)
		check("eligibility.qty_1", eligibility["remaining_quantity"] == 1)
	reservation = frappe.get_all(
		"Plan Reservation Reference", filters={"fixture_namespace": NS}, fields=["amount"],
	)
	check("reservation.one_80m", len(reservation) == 1 and reservation[0].amount == 80000000)
	from kentender_procurement.departmental_needs.services import usage as needs_usage
	from kentender_procurement.procurement_planning.services import needs_intake

	accepted_version = needs_intake.current_accepted_version_of(NEED, PE, FY)
	check(
		"need_usage.fully_included",
		bool(accepted_version) and needs_usage.is_actively_included(accepted_version),
		str(accepted_version),
	)
	return checks
