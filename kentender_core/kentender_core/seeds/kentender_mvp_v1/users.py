# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract v2 §4.6 access profiles + User Scope Assignments."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_budget.services.budget_authorization import ensure_budget_governance_roles
from kentender_core.seeds import constants as CoreC
from kentender_core.seeds._common import ensure_user_permission
from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.procurement_planning.services.planning_roles import (
	ensure_planning_roles as ensure_v12_planning_roles,
)
from kentender_strategy.services.strategy_authorization import ensure_strategy_governance_roles

# PLN-CHG-001 v1.2 Phase 11 (DEBT-01 closed): the Demand-era persona role
# literals (Requester, Business Approver, Planning Reviewer, Designated
# Approver, Tender Initiator, Planning Viewer, Planning Contributor) are
# retired — no longer created on fresh sites, no longer assigned to any
# fixture persona. The live v1.2 Planning roles come from the module's own
# `ensure_planning_roles`; the §14.2 Planning personas themselves are
# provisioned by the NDS and Planning module seeds with native roles and
# User Permission rows only. "Planning Authority" is NOT retired here — it
# remains a live role owned by procurement_lifecycle / tender-management.
ROLE_PLANNER = "Procurement Planner"
ROLE_ACCOUNTING_OFFICER = "Accounting Officer"

# Retired names, kept ONLY so cleanup paths can strip stale assignments a
# prior seed may have left on a long-lived site; never created or granted.
_RETIRED_PERSONA_ROLES = (
	"Requester",
	"Business Approver",
	"Planning Reviewer",
	"Designated Approver",
	"Tender Initiator",
	"Planning Viewer",
	"Planning Contributor",
)


def ensure_planning_roles() -> None:
	ensure_v12_planning_roles()

# (email, full_name, roles, pe, org_unit|None, include_descendants)
# Miriam also carries Demand Requester for Contract v2.2 §7.5 single-scope create.
_USER_SPECS: tuple[tuple[Any, ...], ...] = (
	(
		C.USER_MEDICAL,
		"Dr Miriam Njeri",
		("Strategy Author", "Budget Officer"),
		C.PE_MOH,
		C.OU_DIR_DHP,
		1,
	),
	(
		C.USER_PUBLIC,
		"Anne Achieng",
		("Strategy Author", "Budget Officer"),
		C.PE_MOH,
		C.OU_DIR_HRMD,
		1,
	),
	(
		# STR-CHG-001 v1.5 §18.1 "not promoted automatically" policy: an
		# existing bare Strategy Reviewer holder is not auto-granted any
		# current Strategy role (that role was deleted outright, not
		# merged into Strategy Approver). This fixture persona keeps its
		# identity/scope but no Strategy governance role.
		C.USER_STR_REVIEWER,
		"MOH Strategy Reviewer",
		(),
		C.PE_MOH,
		None,
		0,
	),
	(
		# BUD-CHG-001 v1.3 §15.1 — required named Budget Approver actor. The
		# real Site-wide `User Responsibility Assignment` this role needs to
		# actually authorise anything is granted separately, by Budget's own
		# `ensure_budget_actor_assignments()` — this tuple only creates the
		# User and its Frappe Role projection (old-engine `User Scope
		# Assignment` rows this loop also creates are inert for Budget's own
		# authorization, which reads `authorise_record()` only).
		C.USER_BUD_APPROVER,
		"Beatrice Kamau",
		("Budget Approver",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_VIEWER,
		"MOH Management Viewer",
		("Strategy Viewer",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_KISUMU_OFFICER,
		"Kisumu Health Officer",
		("Strategy Author", "Budget Officer"),
		C.PE_CGKIS,
		C.OU_CGK_HEALTH,
		1,
	),
	(
		C.USER_KISUMU_VIEWER,
		"Kisumu Management Viewer",
		("Strategy Viewer",),
		C.PE_CGKIS,
		None,
		0,
	),
	(
		# BUD-AC-008 self-approval-segregation persona — holds both roles so the
		# "submitting Officer cannot approve their own version, even if they also
		# hold Budget Approver" rule has a durable, permanently-dual-role fixture
		# to exercise without a per-test dynamic role toggle.
		C.USER_BUD_DUAL,
		"MOH Budget Officer+Approver",
		("Budget Officer", "Budget Approver"),
		C.PE_MOH,
		None,
		0,
	),
	(
		# BUD-CHG-001 v1.3: there is no Budget Viewer role — this whole persona
		# is Phase 6's to replace (BUD-604's Naomi Chebet/Josphat Mwangi/
		# Beatrice Kamau), not just role-strip; left as-is for now (Phase 5
		# only touched the combined Strategy+Budget Viewer tuples above).
		C.USER_BUD_VIEWER_MOH,
		"MOH Budget Viewer",
		("Budget Viewer",),
		C.PE_MOH,
		None,
		0,
	),
	(
		# BUD-CHG-001 v1.3 §15.1 — required named Auditor actor (reused from
		# STR-CHG-001 v1.6 §14.1). Real assignment: see the comment on
		# USER_BUD_APPROVER above.
		C.USER_BUD_AUDITOR,
		"Naomi Chebet",
		("Auditor",),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_CGK_BUD_OFFICER,
		"Kisumu Budget Officer",
		("Budget Officer",),
		C.PE_CGKIS,
		None,
		0,
	),
	(
		C.USER_CGK_BUD_APPROVER,
		"Kisumu Budget Approver",
		("Budget Approver",),
		C.PE_CGKIS,
		None,
		0,
	),
	(
		C.USER_BUD_VIEWER_KISUMU,
		"Kisumu Budget Viewer",
		("Budget Viewer",),
		C.PE_CGKIS,
		None,
		0,
	),
	(
		C.USER_PLANNING_OFFICER,
		"Mercy Kilonzo",
		(ROLE_PLANNER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_PLANNING_REVIEWER,
		"David Kiptoo",
		# Planning Reviewer was retired with the capability-era Planning
		# module (DEBT-01); the persona keeps its identity/scope, no role.
		(),
		C.PE_MOH,
		None,
		0,
	),
	(
		# Extra SoD persona — not Demo v2.7 §4.6 (Anne / James / Grace / Peter).
		C.USER_ACCOUNTING_OFFICER,
		"Josephine Mburu",
		(ROLE_ACCOUNTING_OFFICER,),
		C.PE_MOH,
		None,
		0,
	),
	(
		C.USER_TENDER_INITIATOR,
		"MOH Tender Initiator",
		# Tender Initiator retired (DEBT-01); identity/scope kept, no role.
		(),
		C.PE_MOH,
		C.OU_DIR_DHP,
		1,
	),
	(
		C.USER_COUNTY_PLANNER,
		"Kisumu Planning Officer",
		(ROLE_PLANNER,),
		C.PE_CGKIS,
		C.OU_CGK_HEALTH,
		1,
	),
	(
		C.USER_BUSINESS_APPROVER,
		"James Mwangi",
		# Business Approver retired with the Demands module (DEBT-01).
		(),
		C.PE_MOH,
		C.OU_DIR_HRMD,
		1,
	),
	(
		C.USER_HOP,
		"Grace Wanjiku",
		# Designated Approver retired (DEBT-01). Grace's live Planning-era
		# roles come from the NDS/Planning module seeds, not this file.
		(),
		C.PE_MOH,
		None,
		0,
	),
	(
		# BUD-CHG-001 v1.3 §15.1 — required named Budget Officer, and
		# separately Finance Confirmation Officer. Real assignment: see the
		# comment on USER_BUD_APPROVER above.
		C.USER_BUD_OFFICER,
		"Josphat Mwangi",
		("Budget Officer", "Finance Confirmation Officer"),
		C.PE_MOH,
		None,
		0,
	),
)


def _clear_fixture_assignments(user: str) -> None:
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": user, "fixture_namespace": C.FIXTURE_NS},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)


def _upsert_scope(
	*,
	user: str,
	role: str,
	pe: str,
	org_unit: str | None,
	include_descendants: int,
) -> None:
	frappe.get_doc(
		{
			"doctype": "User Scope Assignment",
			"user": user,
			"role": role,
			"procuring_entity": pe,
			"organisation_unit": org_unit or "",
			"include_descendants": include_descendants,
			"fixture_namespace": C.FIXTURE_NS,
		}
	).insert(ignore_permissions=True)


def _save_user_identity_if_changed(user, *, first_name: str, last_name: str) -> None:
	changes = {
		"enabled": 1,
		"first_name": first_name,
		"last_name": last_name,
	}
	if all(user.get(field) == value for field, value in changes.items()):
		return
	user.update(changes)
	user.save(ignore_permissions=True)


def _add_missing_roles(user, *roles: str) -> None:
	current = {row.role for row in user.get("roles")}
	missing = [role for role in roles if role not in current]
	if missing:
		user.add_roles(*missing)


def _upsert_user(
	email: str,
	full_name: str,
	roles: tuple[str, ...],
	pe_code: str,
	org_unit: str | None,
	include_descendants: int,
) -> str:
	parts = (full_name or "").split()
	first = parts[0] if parts else email.split("@")[0]
	last = " ".join(parts[1:]) if len(parts) > 1 else "User"
	if not frappe.db.exists("User", email):
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"last_name": last,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		doc.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	_save_user_identity_if_changed(user, first_name=first, last_name=last)
	_add_missing_roles(user, "Desk User", *roles)
	update_password(email, CoreC.TEST_PASSWORD)
	ensure_user_permission(email, pe_code)
	frappe.defaults.set_user_default("Procuring Entity", pe_code, user=email)
	_clear_fixture_assignments(email)
	for role in roles:
		_upsert_scope(
			user=email,
			role=role,
			pe=pe_code,
			org_unit=org_unit,
			include_descendants=include_descendants,
		)
	return email


def _strip_retired_persona_artifacts(email: str) -> None:
	"""DEBT-01 cleanup: remove any retired-role grant or scope assignment a
	prior seed left on a long-lived site. Never grants anything."""
	if not frappe.db.exists("User", email):
		return
	user = frappe.get_doc("User", email)
	have = {r.role for r in (user.roles or [])}
	stale = [r for r in _RETIRED_PERSONA_ROLES if r in have]
	if stale:
		user.roles = [r for r in user.roles if r.role not in _RETIRED_PERSONA_ROLES]
		user.save(ignore_permissions=True)
	for name in frappe.get_all(
		"User Scope Assignment",
		filters={"user": email, "role": ("in", _RETIRED_PERSONA_ROLES)},
		pluck="name",
	):
		frappe.delete_doc("User Scope Assignment", name, force=1, ignore_permissions=True)


def _upsert_multiscope_admin() -> str:
	"""System Manager with explicit multi-PE User Permissions. The Demand-era
	Requester role/scope pairs are retired (DEBT-01); the persona survives as
	a plain multi-entity administrator fixture."""
	email = C.USER_MULTISCOPE
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Multi",
				"last_name": "Scope Admin",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	_save_user_identity_if_changed(user, first_name="Multi", last_name="Scope Admin")
	_add_missing_roles(user, "Desk User", "System Manager")
	update_password(email, CoreC.TEST_PASSWORD)
	ensure_user_permission(email, C.PE_MOH)
	ensure_user_permission(email, C.PE_CGKIS)
	_clear_fixture_assignments(email)
	_strip_retired_persona_artifacts(email)
	return email


def ensure_administrator_planning_support_viewer() -> str:
	"""DEBT-01: the capability-era "Administrator as cross-entity Planning
	Viewer" grant is retired with its role. In the v1.2 native model §6 gives
	administrative users technical oversight without any Planning role, so
	this now only STRIPS the retired grants a prior seed left behind."""
	ensure_planning_roles()
	email = "Administrator"
	_strip_retired_persona_artifacts(email)
	return email


def _upsert_system_admin_no_requester() -> str:
	"""System Manager only; historically proved admin alone cannot create
	Demands — the retired-role strip keeps that guarantee durable."""
	email = C.USER_SYSTEM_ADMIN
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "System",
				"last_name": "Admin",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	_save_user_identity_if_changed(user, first_name="System", last_name="Admin")
	_add_missing_roles(user, "Desk User", "System Manager")
	update_password(email, CoreC.TEST_PASSWORD)
	_clear_fixture_assignments(email)
	_strip_retired_persona_artifacts(email)
	return email


def upsert_canonical_users(*, commit: bool = True) -> dict[str, Any]:
	ensure_strategy_governance_roles()
	ensure_budget_governance_roles()
	ensure_planning_roles()
	# Skip User→Contact sync (avoids RetryBackgroundJobError under tests / reseed).
	prev_import = frappe.flags.in_import
	frappe.flags.in_import = True
	created: list[str] = []
	try:
		for spec in _USER_SPECS:
			created.append(_upsert_user(*spec))
		created.append(_upsert_multiscope_admin())
		created.append(_upsert_system_admin_no_requester())
		created.append(ensure_administrator_planning_support_viewer())
		disabled: list[str] = []
		for email in C.RETIRED_DEMO_USERS:
			if frappe.db.exists("User", email):
				frappe.db.set_value("User", email, "enabled", 0, update_modified=False)
				disabled.append(email)
		if commit:
			frappe.db.commit()
	finally:
		frappe.flags.in_import = prev_import
	return {
		"ok": True,
		"users": created,
		"disabled_retired": disabled,
		"password": CoreC.TEST_PASSWORD,
	}
