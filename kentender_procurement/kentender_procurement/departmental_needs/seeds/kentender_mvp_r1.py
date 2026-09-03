"""Deterministic Departmental Needs seed (NDS-CHG-001 v1.1 §14).

Actors receive native Frappe roles and User Permission scope only — no
Capability Profile or Operational Scope Assignment (§6, NDS-AC-044).

Phase 1 seeds the §14.3 default profile on the v1.1 version model. Phase 6
completes §14: the §14.4 Planning-usage profile, the §14.5 successor and
withdrawal profiles, and the §14.6 KEBS first-slice profile, each
independently selectable and resettable (§14.7).

Identifier note: the live Configuration & Governance records are
``MOH-DIR-DHP`` / ``MOH-DIR-HRMD``; the spec writes these as ``OU-MOH-DHI`` /
``OU-MOH-HRMD``. The live identifiers are authoritative here, following the
CFG-CHG-002 precedent for ``PE-CGKIS`` — seeds never invent a fallback record
(§14.1).
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, now_datetime
from frappe.utils.password import update_password

from contextlib import contextmanager

from kentender_procurement.departmental_needs.services import lifecycle
from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
)

PE = "PE-MOH"
OU_DIGITAL_HEALTH = "MOH-DIR-DHP"
OU_HRMD = "MOH-DIR-HRMD"
FY = "FY-2027-2028"
NS = "KENTENDER_MVP_1_R1_NDS"

# §14.1 Needs intake window: 1 Sep 2026 00:00:00 to 25 Nov 2026 23:59:59 EAT.
INTAKE_WINDOW = f"NDS-IW-{PE}-{FY}"
INTAKE_OPENS_AT = "2026-09-01 00:00:00"
INTAKE_CLOSES_AT = "2026-11-25 23:59:59"

AUTHOR = "grace.wanjiku@moh.example.test"
REVIEWER = "peter.kimani@moh.example.test"
ACTING_REVIEWER = "julia.njeri@moh.example.test"
PLANNER = "amina.hassan@moh.example.test"
PLANNER_READONLY = "mercy.kilonzo@moh.example.test"
AUDITOR = "auditor.moh@example.test"
# §14.2 — a separate PE scope used only to prove cross-PE isolation.
ISOLATION_REQUESTER = "requester.cgk@example.test"
ISOLATION_PE = "PE-CGKIS"

# §14.2 acting Head of User Department: Julia Njeri, OU-MOH-DHI only, approved
# 1 Oct to 30 Nov 2026. The time bound is expressed by the *existence* of the
# native User Permission row: it is granted for the approved period and removed
# when the period ends. Nothing beyond native Frappe permissions is consulted at
# authorization time, so the framework's own permission engine and this module's
# services always agree — and an ended assignment fails closed simply because
# the row is gone (§6, NDS-AC-042, NDS-AC-010). Frappe's User Permission has no
# validity fields, and adding them would let an expired row still satisfy List
# View and REST access while the services refused it.
ACTING_REVIEWER_FROM = "2026-10-01"
ACTING_REVIEWER_UNTIL = "2026-11-30"

# §14.1 governed units.
UNITS = (
	("UNIT-PROGRAMME", "Programme"),
	("UNIT-EACH", "Each"),
)

# §14.3 default Needs. Version status follows the root state.
NEEDS = (
	{
		"reference": "NDS-MOH-2027-0001",
		"organisation_unit": OU_DIGITAL_HEALTH,
		"title": "National digital health infrastructure upgrade",
		"description": "Procure and implement national digital health infrastructure across priority health facilities.",
		"expected_operational_result": "Priority health facilities can use secure and interoperable digital health services.",
		"indicative_quantity": 1,
		"unit": "UNIT-PROGRAMME",
		"required_by_date": "2027-08-31",
		"state": STATE_ACCEPTED,
	},
	{
		"reference": "NDS-MOH-2027-0002",
		"organisation_unit": OU_HRMD,
		"title": "Digital health workforce certification programme",
		"description": "Professional certification programme for staff supporting national digital health services.",
		"expected_operational_result": "Build internal capacity to operate and support national digital health platforms.",
		"indicative_quantity": 1,
		"unit": "UNIT-PROGRAMME",
		"required_by_date": "2027-12-31",
		"state": STATE_SUBMITTED,
	},
	{
		"reference": "NDS-MOH-2027-0003",
		"organisation_unit": OU_HRMD,
		"title": "Clinical training laptops for digital health rollout",
		"description": "Laptop computers for clinical training during the national digital health rollout.",
		"expected_operational_result": "Provide the equipment required for staff training on the deployed digital health services.",
		"indicative_quantity": 200,
		"unit": "UNIT-EACH",
		"required_by_date": "2027-12-31",
		"state": STATE_RETURNED,
	},
	{
		"reference": "NDS-MOH-2027-0004",
		"organisation_unit": OU_DIGITAL_HEALTH,
		"title": "Clinical deployment laptops for digital health rollout",
		"description": "Laptop computers for deployment at priority facilities during the national digital health rollout.",
		"expected_operational_result": "Provide endpoint equipment required to use the deployed digital health services.",
		"indicative_quantity": 300,
		"unit": "UNIT-EACH",
		"required_by_date": "2027-12-31",
		"state": STATE_DRAFT,
	},
)

RETURN_REASON = (
	"Confirm the number of trainees to be supported and revise the laptop quantity "
	"if the approved training cohort has changed."
)



@contextmanager
def _as(user: str):
	"""Run a command as a real seeded actor, so `owner` and maker-checker hold."""
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


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
				"doctype": "User",
				"email": email,
				"first_name": parts[0],
				"last_name": " ".join(parts[1:]),
				"full_name": full_name,
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("User", email, {"enabled": 1, "full_name": full_name}, update_modified=False)
	frappe.get_doc("User", email).add_roles("Desk User", *roles)
	update_password(email, "Test@123")
	return email


def _user_permission(user: str, doctype: str, value: str) -> None:
	"""Native User Permission — the only scope mechanism this module uses (§6)."""
	if frappe.db.exists("User Permission", {"user": user, "allow": doctype, "for_value": value}):
		return
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": doctype,
			"for_value": value,
			"apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)


def _units() -> None:
	for code, label in UNITS:
		if frappe.db.exists("Unit Of Measure", code):
			frappe.db.set_value(
				"Unit Of Measure", code, {"unit_label": label, "status": "Active"}, update_modified=False
			)
			continue
		frappe.get_doc(
			{
				"doctype": "Unit Of Measure",
				"unit_code": code,
				"unit_label": label,
				"status": "Active",
				"fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)


def _intake_window() -> None:
	"""§14.1 — 1 Sep 2026 00:00:00 to 25 Nov 2026 23:59:59 EAT, inclusive.

	Stored exactly as specified. The window is therefore `Scheduled` before
	1 Sep 2026 and `Closed` after 25 Nov 2026; the design clock (24 Nov 2026)
	sits inside it. Tests that need an Open window set their own instants inside
	their own transaction rather than moving this fixture.
	"""
	values = {"opens_at": INTAKE_OPENS_AT, "closes_at": INTAKE_CLOSES_AT}
	if frappe.db.exists("Needs Intake Window", INTAKE_WINDOW):
		frappe.db.set_value("Needs Intake Window", INTAKE_WINDOW, values, update_modified=False)
		return
	frappe.get_doc(
		{
			"doctype": "Needs Intake Window",
			"needs_intake_window_id": INTAKE_WINDOW,
			"procuring_entity": PE,
			"financial_year": FY,
			"record_version": 1,
			"fixture_namespace": NS,
			**values,
		}
	).insert(ignore_permissions=True)


def _actors() -> None:
	"""§14.2 — an acting HoD holds the same role plus a scoped User Permission."""
	_user(AUTHOR, "Grace Wanjiku", (ROLE_DEPARTMENTAL_AUTHOR,))
	_user(REVIEWER, "Dr Peter Kimani", (ROLE_HEAD_OF_USER_DEPARTMENT,))
	_user(ACTING_REVIEWER, "Julia Njeri", (ROLE_HEAD_OF_USER_DEPARTMENT,))
	_user(PLANNER, "Amina Hassan", (ROLE_PROCUREMENT_PLANNER,))
	_user(PLANNER_READONLY, "Mercy Kilonzo", (ROLE_PROCUREMENT_PLANNER,))
	_user(AUDITOR, "MOH Auditor", (ROLE_AUDITOR,))
	_user(ISOLATION_REQUESTER, "CGK Requester", (ROLE_DEPARTMENTAL_AUTHOR,))

	# §14.2 — PE-CGKIS only. Holds the Departmental Author role but no PE-MOH
	# scope, proving that a role never grants authority on its own.
	_user_permission(ISOLATION_REQUESTER, "Procuring Entity", ISOLATION_PE)

	for user in (AUTHOR, REVIEWER, PLANNER, PLANNER_READONLY, AUDITOR):
		_user_permission(user, "Procuring Entity", PE)
		_user_permission(user, "Financial Year", FY)
	for user in (AUTHOR, REVIEWER):
		for unit in (OU_DIGITAL_HEALTH, OU_HRMD):
			_user_permission(user, "Organisation Unit", unit)

	# Acting HoD: Digital Health only, proving scope is narrower than the role.
	_user_permission(ACTING_REVIEWER, "Procuring Entity", PE)
	_user_permission(ACTING_REVIEWER, "Financial Year", FY)
	_user_permission(ACTING_REVIEWER, "Organisation Unit", OU_DIGITAL_HEALTH)


# §14.3 design-clock decision times (EAT), applied after the commands run.
DECISION_TIMES = {
	("NDS-MOH-2027-0001", "Accept for planning"): "2026-11-24 14:00:00",
	("NDS-MOH-2027-0002", "Submit"): "2026-11-24 12:20:00",
	("NDS-MOH-2027-0003", "Return for correction"): "2026-11-24 13:35:00",
}


def _build_need(spec: dict) -> str:
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
			procuring_entity=PE,
			organisation_unit=spec["organisation_unit"],
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
	with _as(REVIEWER):
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

	The §14.1 window is only open between 1 Sep and 25 Nov 2026, so seeding
	opens it for the duration of the build and restores the exact §14.1 instants
	afterwards. Nothing else about the fixture is adjusted: the states, versions,
	content hashes, review tasks and published events are exactly what the
	commands produced.
	"""
	_units()
	_intake_window()
	_actors()
	restore = frappe.db.get_value(
		"Needs Intake Window", INTAKE_WINDOW, ["opens_at", "closes_at"], as_dict=True
	)
	now = now_datetime()
	frappe.db.set_value(
		"Needs Intake Window",
		INTAKE_WINDOW,
		{"opens_at": add_days(now, -1), "closes_at": add_days(now, 1)},
		update_modified=False,
	)
	try:
		created = [_build_need(spec) for spec in NEEDS]
	finally:
		frappe.db.set_value(
			"Needs Intake Window",
			INTAKE_WINDOW,
			{"opens_at": restore.opens_at, "closes_at": restore.closes_at},
			update_modified=False,
		)
	_stamp_design_clock()
	if commit:
		frappe.db.commit()
	return {"needs": created}
