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

from uuid import uuid4

import frappe
from frappe.utils import now_datetime
from frappe.utils.password import update_password

from kentender_procurement.departmental_needs.constants import (
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
	VERSION_ACCEPTED,
	VERSION_DRAFT,
	VERSION_RETURNED,
	VERSION_SUBMITTED,
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

_ROOT_TO_VERSION = {
	STATE_DRAFT: VERSION_DRAFT,
	STATE_SUBMITTED: VERSION_SUBMITTED,
	STATE_RETURNED: VERSION_RETURNED,
	STATE_ACCEPTED: VERSION_ACCEPTED,
}


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


def _need(spec: dict) -> str:
	reference = spec["reference"]
	root_values = {
		"procuring_entity": PE,
		"organisation_unit": spec["organisation_unit"],
		"financial_year": FY,
		"current_state": spec["state"],
		"fixture_namespace": NS,
	}
	if frappe.db.exists("Departmental Need", reference):
		frappe.db.set_value("Departmental Need", reference, root_values, update_modified=False)
	else:
		frappe.get_doc(
			{
				"doctype": "Departmental Need",
				"need_reference": reference,
				"record_version": 1,
				**root_values,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_value("Departmental Need", reference, "owner", AUTHOR, update_modified=False)

	version_id = f"{reference}-V001"
	version_values = {
		"departmental_need": reference,
		"version_number": 1,
		"version_status": _ROOT_TO_VERSION[spec["state"]],
		"title": spec["title"],
		"description": spec["description"],
		"expected_operational_result": spec["expected_operational_result"],
		"indicative_quantity": spec["indicative_quantity"],
		"unit": spec["unit"],
		"required_by_date": spec["required_by_date"],
		"fixture_namespace": NS,
	}
	if frappe.db.exists("Departmental Need Version", version_id):
		frappe.db.set_value(
			"Departmental Need Version", version_id, version_values, update_modified=False
		)
	else:
		frappe.get_doc(
			{"doctype": "Departmental Need Version", "need_version_id": version_id, **version_values}
		).insert(ignore_permissions=True)
	frappe.db.set_value("Departmental Need Version", version_id, "owner", AUTHOR, update_modified=False)

	current_version = version_id
	if spec["state"] == STATE_RETURNED:
		# §14.3 — Version 2 is the server-created editable copy of the returned V1.
		current_version = f"{reference}-V002"
		copy_values = {
			**version_values,
			"version_number": 2,
			"version_status": VERSION_DRAFT,
			"based_on_version": version_id,
		}
		if frappe.db.exists("Departmental Need Version", current_version):
			frappe.db.set_value(
				"Departmental Need Version", current_version, copy_values, update_modified=False
			)
		else:
			frappe.get_doc(
				{
					"doctype": "Departmental Need Version",
					"need_version_id": current_version,
					**copy_values,
				}
			).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Departmental Need Version", current_version, "owner", AUTHOR, update_modified=False
		)

	frappe.db.set_value(
		"Departmental Need",
		reference,
		{
			"current_version": current_version,
			"current_accepted_version": version_id if spec["state"] == STATE_ACCEPTED else None,
		},
		update_modified=False,
	)
	return reference


def _decision(need: str, *, action: str, prior: str, result: str, actor: str, reason: str = "", version: str = "") -> None:
	key = f"nds-seed:{need}:{action}"
	if frappe.db.exists("Departmental Need Decision", {"idempotency_key": key}):
		return
	frappe.get_doc(
		{
			"doctype": "Departmental Need Decision",
			"decision_id": f"NDD-SEED-{uuid4().hex.upper()}",
			"departmental_need": need,
			"need_version": version or None,
			"action": action,
			"actor": actor,
			"scope": f"{PE}/{frappe.db.get_value('Departmental Need', need, 'organisation_unit')}/{FY}",
			"occurred_at": now_datetime(),
			"reason": reason,
			"prior_state": prior,
			"result_state": result,
			"idempotency_key": key,
			"fixture_namespace": NS,
		}
	).insert(ignore_permissions=True)


def upsert_departmental_needs(*, commit: bool = False) -> dict[str, list[str]]:
	"""Idempotent §14.3 default profile."""
	_units()
	_intake_window()
	_actors()
	created = [_need(spec) for spec in NEEDS]

	_decision(
		"NDS-MOH-2027-0001",
		action="Accept for planning",
		prior=STATE_SUBMITTED,
		result=STATE_ACCEPTED,
		actor=REVIEWER,
		version="NDS-MOH-2027-0001-V001",
	)
	_decision(
		"NDS-MOH-2027-0002",
		action="Submit",
		prior=STATE_DRAFT,
		result=STATE_SUBMITTED,
		actor=AUTHOR,
		version="NDS-MOH-2027-0002-V001",
	)
	_decision(
		"NDS-MOH-2027-0003",
		action="Return for correction",
		prior=STATE_SUBMITTED,
		result=STATE_RETURNED,
		actor=REVIEWER,
		reason=RETURN_REASON,
		version="NDS-MOH-2027-0003-V001",
	)
	if commit:
		frappe.db.commit()
	return {"needs": created}
