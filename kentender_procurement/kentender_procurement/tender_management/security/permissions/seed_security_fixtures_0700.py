# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0700 — security seed fixtures (users + NEG-SEC cases).

Bench::

	bench --site kentender.midas.com execute \
		kentender_procurement.tender_management.security.permissions.seed_security_fixtures_0700.run
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import frappe

from kentender_procurement.tender_management.security.permissions.role_permission import (
	RolePermissionService,
)
from kentender_procurement.tender_management.security.permissions.service import (
	PermissionService,
)

FIXTURE_USERS: tuple[dict[str, str], ...] = (
	{"actor_user_code": "USER-STD-ADMIN-001", "email": "sec0700_std_admin@example.com", "security_role_code": "ROLE_STD_ADMIN"},
	{"actor_user_code": "USER-LEGAL-REVIEWER-001", "email": "sec0700_legal_reviewer@example.com", "security_role_code": "ROLE_LEGAL_REVIEWER"},
	{"actor_user_code": "USER-PROC-OFFICER-001", "email": "sec0700_proc_officer@example.com", "security_role_code": "ROLE_PROCUREMENT_OFFICER"},
	{"actor_user_code": "USER-PROC-ASSISTANT-001", "email": "sec0700_proc_assistant@example.com", "security_role_code": "ROLE_PROCUREMENT_ASSISTANT"},
	{"actor_user_code": "USER-APPROVER-001", "email": "sec0700_approver@example.com", "security_role_code": "ROLE_APPROVING_AUTHORITY"},
	{"actor_user_code": "USER-OPENING-001", "email": "sec0700_opening@example.com", "security_role_code": "ROLE_OPENING_COMMITTEE"},
	{"actor_user_code": "USER-EVAL-001", "email": "sec0700_eval@example.com", "security_role_code": "ROLE_EVALUATION_COMMITTEE"},
	{"actor_user_code": "USER-AUDITOR-001", "email": "sec0700_auditor@example.com", "security_role_code": "ROLE_AUDITOR"},
	{"actor_user_code": "USER-SYSADMIN-001", "email": "sec0700_sysadmin@example.com", "security_role_code": "ROLE_SYSTEM_ADMIN"},
)

NEGATIVE_ACCESS_CASES: tuple[dict[str, str], ...] = (
	{
		"case_code": "NEG-SEC-001",
		"actor_user_code": "USER-STD-ADMIN-001",
		"action_code": "RELEASE_PACKAGE_TO_TENDER",
		"expected_denial_code": "RELEASE_PERMISSION_DENIED",
	},
	{
		"case_code": "NEG-SEC-002",
		"actor_user_code": "USER-STD-ADMIN-001",
		"action_code": "CREATE_STD_INSTANCE_FROM_TENDER",
		"expected_denial_code": "STD_AUTH_PERMISSION_DENIED",
	},
	{
		"case_code": "NEG-SEC-003",
		"actor_user_code": "USER-PROC-OFFICER-001",
		"action_code": "CONFIGURE_STD_TEMPLATE_MAPPINGS",
		"expected_denial_code": "STD_AUTH_PERMISSION_DENIED",
	},
	{
		"case_code": "NEG-SEC-004",
		"actor_user_code": "USER-PROC-ASSISTANT-001",
		"action_code": "PUBLISH_TENDER",
		"expected_denial_code": "PUBLISH_PERMISSION_DENIED",
	},
	{
		"case_code": "NEG-SEC-005",
		"actor_user_code": "USER-APPROVER-001",
		"action_code": "EDIT_WORKS_BOQ_DURING_APPROVAL",
		"expected_denial_code": "STD_AUTH_PERMISSION_DENIED",
	},
	{
		"case_code": "NEG-SEC-006",
		"actor_user_code": "USER-OPENING-001",
		"action_code": "PERFORM_BOQ_ARITHMETIC_CORRECTION",
		"expected_denial_code": "BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION",
	},
	{
		"case_code": "NEG-SEC-007",
		"actor_user_code": "USER-EVAL-001",
		"action_code": "ADD_MANUAL_EVALUATION_CRITERIA",
		"expected_denial_code": "MANUAL_EVALUATION_CRITERIA_DENIED",
	},
	{
		"case_code": "NEG-SEC-008",
		"actor_user_code": "USER-AUDITOR-001",
		"action_code": "EDIT_STD_INSTANCE_PARAMETERS",
		"expected_denial_code": "STD_AUTH_PERMISSION_DENIED",
	},
)


def _ensure_fixture_user(spec: dict[str, str]) -> str:
	actor_user_code = spec["actor_user_code"]
	email = spec["email"]
	existing_name = frappe.db.get_value("User", {"email": email}, "name")
	if existing_name:
		doc = frappe.get_doc("User", existing_name)
		changed = False
		if int(doc.enabled or 0) != 1:
			doc.enabled = 1
			changed = True
		if (doc.user_type or "") != "System User":
			doc.user_type = "System User"
			changed = True
		if (doc.username or "") != actor_user_code:
			doc.username = actor_user_code
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
			frappe.db.set_value("User", existing_name, "user_type", "System User")
		return "updated" if changed else "unchanged"

	doc = frappe.new_doc("User")
	doc.email = email
	doc.first_name = actor_user_code
	doc.username = actor_user_code
	doc.user_type = "System User"
	doc.enabled = 1
	doc.new_password = "Test@1234"
	doc.send_welcome_email = 0
	doc.insert(ignore_permissions=True)
	frappe.db.set_value("User", doc.name, "user_type", "System User")
	return "created"


def upsert_security_seed_fixtures() -> dict[str, Any]:
	"""Ensure SEC-0700 users and NEG-SEC fixture cases exist in code/DB."""
	frappe.set_user("Administrator")
	PermissionService.ensure_catalog_seeded()
	RolePermissionService.ensure_matrix_seeded()

	users_created = 0
	users_updated = 0
	users_unchanged = 0
	for spec in FIXTURE_USERS:
		action = _ensure_fixture_user(dict(spec))
		if action == "created":
			users_created += 1
		elif action == "updated":
			users_updated += 1
		else:
			users_unchanged += 1

	return {
		"ok": True,
		"users_total": len(FIXTURE_USERS),
		"users_created": users_created,
		"users_updated": users_updated,
		"users_unchanged": users_unchanged,
		"negative_cases_total": len(NEGATIVE_ACCESS_CASES),
		"negative_access_cases": negative_access_cases(),
	}


def negative_access_cases() -> list[dict[str, str]]:
	"""Return a deep-copied list so tests can mutate safely."""
	return deepcopy(list(NEGATIVE_ACCESS_CASES))


def fixture_users() -> list[dict[str, str]]:
	return deepcopy(list(FIXTURE_USERS))


def run() -> dict[str, Any]:
	return upsert_security_seed_fixtures()
