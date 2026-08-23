# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 — PE Type catalogue, Procuring Entity versioning, Financial Year,
PE/FY Context seed data for KENTENDER_MVP_V1. Grown phase by phase per
docs/mvp-1-r1/05_pe_and_fy_maintenance/IMPLEMENTATION_TRACKER.md.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.services import reference_data_permissions as perm
from kentender_core.services import reference_data_transitions as txn
from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.authorization_administration import (
	change_assignment_state,
	create_draft_assignment,
)

# type_code -> display label. Values marked (spec) are CFG-PEFY-required (§16);
# the rest are carried over from the pre-existing Procuring Entity.entity_type
# Select so no live/seeded row's classification is orphaned by the catalogue switch.
PE_TYPES: dict[str, str] = {
	"NATIONAL_MINISTRY": "National Government Ministry",  # spec
	"STATE_CORPORATION": "State Corporation",  # spec
	"COUNTY_GOVERNMENT": "County Government",  # spec
	"JUDICIARY": "Judiciary",
	"COMMISSION": "Commission",
	"PUBLIC_UNIVERSITY": "Public University",
	"OTHER": "Other",
}


def _upsert_pe_type(type_code: str, label: str) -> str:
	if frappe.db.exists("PE Type", type_code):
		frappe.db.set_value(
			"PE Type", type_code, {"label": label, "status": "Active"}, update_modified=False
		)
		return type_code
	doc = frappe.get_doc(
		{"doctype": "PE Type", "type_code": type_code, "label": label, "status": "Active"}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_pe_types() -> dict[str, Any]:
	created = {code: _upsert_pe_type(code, label) for code, label in PE_TYPES.items()}
	return {"pe_types": created}


# --- Governance Roles (Phase 8 — Page/Workspace visibility gate) ----------------
#
# Frappe Roles gate Page/Workspace *visibility* only, coarser-grained than the
# fine-grained Capability Profile/Operational Scope Assignment engine that gates
# every actual server-side action. A user needs one of these Roles to see the
# "reference-data" Page and the Configuration & Governance sidebar entry at all —
# separate from, and in addition to, whatever reference-data capabilities they hold.

REFERENCE_DATA_STEWARD_ROLE = "Central Reference Data Steward"
REFERENCE_DATA_APPROVER_ROLE = "Central Configuration Approver"


def _ensure_role(role_name: str) -> str:
	if not frappe.db.exists("Role", role_name):
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(
			ignore_permissions=True
		)
	return role_name


def ensure_reference_data_governance_roles(user_emails: list[str]) -> dict[str, Any]:
	"""Grants both governance roles to every known reference-data actor — the Role
	gate is a broad "is this person in the configuration/oversight population"
	check, not a fine split matching each capability profile 1:1."""
	_ensure_role(REFERENCE_DATA_STEWARD_ROLE)
	_ensure_role(REFERENCE_DATA_APPROVER_ROLE)
	for email in user_emails:
		if not frappe.db.exists("User", email):
			continue
		user = frappe.get_doc("User", email)
		user.add_roles(REFERENCE_DATA_STEWARD_ROLE, REFERENCE_DATA_APPROVER_ROLE)
	return {
		"steward_role": REFERENCE_DATA_STEWARD_ROLE,
		"approver_role": REFERENCE_DATA_APPROVER_ROLE,
		"granted_to": user_emails,
	}


# --- Governance actors + capability profiles (§7, §16) -------------------------

STEWARD_EMAIL = "lydia.mwangi@kentender.example.test"
STEWARD_NAME = "Lydia Mwangi"
APPROVER_EMAIL = "daniel.kariuki@kentender.example.test"
APPROVER_NAME = "Daniel Kariuki"

STEWARD_PROFILE = "REFDATA-STEWARD"
APPROVER_PROFILE = "REFDATA-APPROVER"
SOD_RULE_ID = "REFDATA-SOD-CREATE-VS-APPROVE"


def _upsert_desk_user(email: str, full_name: str) -> str:
	if not frappe.db.exists("User", email):
		parts = full_name.split()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": parts[0] if parts else email,
				"last_name": " ".join(parts[1:]) if len(parts) > 1 else "",
				"full_name": full_name,
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.add_roles("Desk User")
	from frappe.utils.password import update_password

	update_password(email, "Test@123")
	return email


def _upsert_capability_profile(profile_id: str, profile_name: str, capabilities: list[str]) -> str:
	import json

	if frappe.db.exists("Capability Profile", profile_id):
		frappe.db.set_value(
			"Capability Profile",
			profile_id,
			{
				"profile_name": profile_name,
				"capabilities": json.dumps(capabilities),
				"allows_entity_wide": 1,
				"status": "Active",
			},
			update_modified=False,
		)
		return profile_id
	doc = frappe.get_doc(
		{
			"doctype": "Capability Profile",
			"profile_id": profile_id,
			"profile_name": profile_name,
			"capabilities": json.dumps(capabilities),
			"allows_entity_wide": 1,  # Steward/Approver act across a whole PE, not one Organisation Unit
			"status": "Active",
			"concurrency_token": frappe.generate_hash(length=8),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


FY_SOD_RULE_ID = "REFDATA-SOD-FY-CREATE-VS-APPROVE"


def _upsert_sod_rule(rule_id: str, rule_name: str, first_capability: str, second_capability: str) -> str:
	if frappe.db.exists("Separation of Duties Rule", rule_id):
		return rule_id
	doc = frappe.get_doc(
		{
			"doctype": "Separation of Duties Rule",
			"rule_id": rule_id,
			"rule_name": rule_name,
			"first_capability": first_capability,
			"second_capability": second_capability,
			"enforcement_level": "Workflow instance",
			"module_name": "Kentender Core",
			"status": "Active",
			"effective_from": now_datetime(),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_active_assignment(user_id: str, profile_id: str, procuring_entity_id: str) -> None:
	existing = frappe.db.get_value(
		"Operational Scope Assignment",
		{"user_id": user_id, "capability_profile_id": profile_id, "procuring_entity_id": procuring_entity_id},
		["name", "status"],
		as_dict=True,
	)
	if existing and existing.status == "Active":
		return
	if existing:
		doc = frappe.get_doc("Operational Scope Assignment", existing.name)
		change_assignment_state(existing.name, doc.concurrency_token, "Active", user="Administrator")
		return
	created = create_draft_assignment(
		{
			"user_id": user_id,
			"capability_profile_id": profile_id,
			"procuring_entity_id": procuring_entity_id,
			"effective_from": now_datetime(),
		},
		user="Administrator",
	)
	change_assignment_state(created["name"], created["concurrency_token"], "Active", user="Administrator")


def upsert_pe_governance_actors(procuring_entities: list[str]) -> dict[str, Any]:
	"""Create the Steward/Approver capability profiles, SoD rule, fixture actors
	(Lydia Mwangi, Daniel Kariuki — §16), and their active assignments across the
	given PEs. Idempotent."""
	_upsert_capability_profile(
		STEWARD_PROFILE,
		"Central Reference Data Steward",
		[perm.PE_CREATE_DRAFT, perm.PE_PROPOSE_AMENDMENT, perm.FY_CREATE_DRAFT],
	)
	_upsert_capability_profile(
		APPROVER_PROFILE,
		"Central Configuration Approver",
		[
			perm.PE_APPROVE_ACTIVATE,
			perm.PE_SUSPEND,
			perm.PE_REINSTATE,
			perm.PE_RETIRE,
			perm.FY_APPROVE_AVAILABLE,
			perm.FY_RETIRE,
		],
	)
	_upsert_sod_rule(
		SOD_RULE_ID,
		"PE create/submit vs. approve-activate (creator cannot approve own proposal)",
		perm.PE_CREATE_DRAFT,
		perm.PE_APPROVE_ACTIVATE,
	)
	_upsert_sod_rule(
		FY_SOD_RULE_ID,
		"FY create/submit vs. approve (creator cannot approve own proposal)",
		perm.FY_CREATE_DRAFT,
		perm.FY_APPROVE_AVAILABLE,
	)
	_upsert_desk_user(STEWARD_EMAIL, STEWARD_NAME)
	_upsert_desk_user(APPROVER_EMAIL, APPROVER_NAME)
	for pe in procuring_entities:
		_ensure_active_assignment(STEWARD_EMAIL, STEWARD_PROFILE, pe)
		_ensure_active_assignment(APPROVER_EMAIL, APPROVER_PROFILE, pe)
	return {"steward": STEWARD_EMAIL, "approver": APPROVER_EMAIL, "procuring_entities": procuring_entities}


# --- PE/FY Context governance actors (§7, §16) ----------------------------------
# Distinct, PE-scoped roles from the central Steward/Approver above — §16's own
# fixture actors for the context maker-checker chain.

CTX_STEWARD_EMAIL = "mercy.kilonzo@moh.example.test"
CTX_STEWARD_NAME = "Mercy Kilonzo"
CTX_REVIEWER_EMAIL = "samuel.otieno@moh.example.test"
CTX_REVIEWER_NAME = "Samuel Otieno"
CTX_AO_EMAIL = "amina.hassan@moh.example.test"
CTX_AO_NAME = "Amina Hassan"

CTX_STEWARD_PROFILE = "REFDATA-CTX-STEWARD"
CTX_REVIEWER_PROFILE = "REFDATA-CTX-REVIEWER"
CTX_AO_PROFILE = "REFDATA-CTX-APPROVER"

CTX_SOD_SUBMIT_VS_RECOMMEND = "REFDATA-SOD-CTX-SUBMIT-VS-RECOMMEND"
CTX_SOD_SUBMIT_VS_APPROVE = "REFDATA-SOD-CTX-SUBMIT-VS-APPROVE"
CTX_SOD_RECOMMEND_VS_APPROVE = "REFDATA-SOD-CTX-RECOMMEND-VS-APPROVE"


def upsert_context_governance_actors(procuring_entities: list[str]) -> dict[str, Any]:
	"""Steward/Reviewer/Accounting-Officer capability profiles, all 3 pairwise SoD
	rules (§7: 'one actor may not satisfy two required decision stages'), fixture
	actors (Mercy Kilonzo, Samuel Otieno, Amina Hassan — §16), and their active
	assignments across the given PEs. Idempotent."""
	_upsert_capability_profile(CTX_STEWARD_PROFILE, "PE Configuration Steward", [perm.CTX_CREATE_DRAFT])
	_upsert_capability_profile(
		CTX_REVIEWER_PROFILE, "Professional Configuration Reviewer", [perm.CTX_RECOMMEND]
	)
	_upsert_capability_profile(CTX_AO_PROFILE, "Accounting Officer", [perm.CTX_APPROVE])

	_upsert_sod_rule(
		CTX_SOD_SUBMIT_VS_RECOMMEND,
		"Context submit vs. recommend",
		perm.CTX_CREATE_DRAFT,
		perm.CTX_RECOMMEND,
	)
	_upsert_sod_rule(
		CTX_SOD_SUBMIT_VS_APPROVE,
		"Context submit vs. approve",
		perm.CTX_CREATE_DRAFT,
		perm.CTX_APPROVE,
	)
	_upsert_sod_rule(
		CTX_SOD_RECOMMEND_VS_APPROVE,
		"Context recommend vs. approve",
		perm.CTX_RECOMMEND,
		perm.CTX_APPROVE,
	)

	_upsert_desk_user(CTX_STEWARD_EMAIL, CTX_STEWARD_NAME)
	_upsert_desk_user(CTX_REVIEWER_EMAIL, CTX_REVIEWER_NAME)
	_upsert_desk_user(CTX_AO_EMAIL, CTX_AO_NAME)
	for pe in procuring_entities:
		_ensure_active_assignment(CTX_STEWARD_EMAIL, CTX_STEWARD_PROFILE, pe)
		_ensure_active_assignment(CTX_REVIEWER_EMAIL, CTX_REVIEWER_PROFILE, pe)
		_ensure_active_assignment(CTX_AO_EMAIL, CTX_AO_PROFILE, pe)
	return {
		"steward": CTX_STEWARD_EMAIL,
		"reviewer": CTX_REVIEWER_EMAIL,
		"accounting_officer": CTX_AO_EMAIL,
		"procuring_entities": procuring_entities,
	}


# --- Legacy PE -> versioned-model migration (CFG-108) --------------------------

# Pre-existing entity_type Select values -> new PE Type catalogue codes.
_LEGACY_TYPE_MAP = {
	"Ministry": "NATIONAL_MINISTRY",
	"County Government": "COUNTY_GOVERNMENT",
	"State Corporation": "STATE_CORPORATION",
	"Judiciary": "JUDICIARY",
	"Commission": "COMMISSION",
	"Public University": "PUBLIC_UNIVERSITY",
}


def migrate_legacy_pe_to_versioned(entity_code: str) -> str | None:
	"""One-time additive migration for a PE seeded before CFG-CHG-002: attach a
	PE Type link and an initial ACTIVE Procuring Entity Version, matching its
	current legal_name/status. Not a governed transition (no submit/approve
	history exists for these legacy rows to replay) — a direct, explicit,
	one-time write, same treatment as any other pre-governance legacy migration
	in this codebase. Idempotent: no-op if current_version_id is already set."""
	pe = frappe.get_doc("Procuring Entity", entity_code)
	if pe.current_version_id:
		return pe.current_version_id

	type_code = _LEGACY_TYPE_MAP.get(pe.entity_type, "OTHER")
	version = frappe.get_doc(
		{
			"doctype": "Procuring Entity Version",
			"procuring_entity": pe.name,
			"version_no": 1,
			"legal_name": pe.legal_name,
			"display_name": pe.entity_name or pe.legal_name,
			"pe_type_code": type_code,
			"timezone": "Africa/Nairobi",
			"version_state": "Active" if pe.status == "Active" else "Draft",
			"valid_from": pe.effective_from or frappe.utils.today(),
		}
	)
	version.insert(ignore_permissions=True)
	pe.db_set("current_version_id", version.name, update_modified=False)
	return version.name


def migrate_legacy_pes(entity_codes: list[str]) -> dict[str, Any]:
	return {code: migrate_legacy_pe_to_versioned(code) for code in entity_codes}


def _backdate_audit_event(document_type: str, document_name: str, action: str, actor: str, when: str) -> None:
	"""Direct write, narrowly scoped to the timestamp of an event the real
	service already recorded — matches AGENTS.md's fixture convention: 'a
	direct write is acceptable only for a test property the service cannot
	produce, such as controlled backdating; isolate it and explain why.' Here:
	§16's governance-history table requires exact historical timestamps
	(2026/2027) that don't exist in reality relative to whenever this seed is
	actually run."""
	name = frappe.db.get_value(
		"Audit Event",
		{"document_type": document_type, "document_name": document_name, "action": action, "performed_by": actor},
		"name",
		order_by="creation desc",
	)
	if name:
		frappe.db.set_value("Audit Event", name, "timestamp", get_datetime(when), update_modified=False)


# --- §16 seed contract: PE-NSSF ---------------------------------------------------


def seed_pe_nssf() -> str:
	"""PE-NSSF — net new, per §16. Runs through the real governed lifecycle
	(create/submit/approve) as the seeded Steward/Approver, not a direct write.
	PE-NSSF doesn't exist until create_pe_draft() returns, so the PE-scoped
	assignments for it (needed by submit/approve's resource-scoped capability
	checks — unlike creation, which uses the any-PE check) are granted
	mid-flow, same bootstrap order as this module's own tests."""
	if frappe.db.exists("Procuring Entity", C.PE_NSSF):
		return C.PE_NSSF
	txn.create_pe_draft(
		{
			"entity_code": C.PE_NSSF,
			"legal_name": C.PE_NSSF_NAME,
			"display_name": C.PE_NSSF_NAME,
			"pe_type_code": "STATE_CORPORATION",
			"effective_from": "2026-07-01",
		},
		user=STEWARD_EMAIL,
	)
	_ensure_active_assignment(STEWARD_EMAIL, STEWARD_PROFILE, C.PE_NSSF)
	_ensure_active_assignment(APPROVER_EMAIL, APPROVER_PROFILE, C.PE_NSSF)
	_ensure_active_assignment(CTX_STEWARD_EMAIL, CTX_STEWARD_PROFILE, C.PE_NSSF)
	_ensure_active_assignment(CTX_REVIEWER_EMAIL, CTX_REVIEWER_PROFILE, C.PE_NSSF)
	_ensure_active_assignment(CTX_AO_EMAIL, CTX_AO_PROFILE, C.PE_NSSF)

	txn.submit_pe(C.PE_NSSF, user=STEWARD_EMAIL)
	txn.approve_activate_pe(C.PE_NSSF, user=APPROVER_EMAIL)
	return C.PE_NSSF


def seed_pe_moh_history() -> None:
	"""§16's governance-history table for PE-MOH: submit (Lydia, 29 Jun 2026
	10:10 EAT) / approve-and-activate (Daniel, 30 Jun 2026 16:25 EAT). PE-MOH's
	version was created by migrate_legacy_pe_to_versioned() (a one-time,
	pre-CFG-CHG-002 direct migration, not a live governed transition — there is
	no real submit/approve call to backdate), so these two history rows are
	inserted directly, narrowly, and are explained here rather than silently
	fabricated. Guard is scoped to this seed's own action names, not "any Audit
	Event for PE-MOH" — PE-MOH already carries unrelated pre-existing events
	(a "support.record.view" trail from an unrelated feature) that a broader
	guard would have collided with, silently skipping this seed forever."""
	if frappe.get_all(
		"Audit Event",
		filters={
			"document_type": "Procuring Entity",
			"document_name": C.PE_MOH,
			"action": ["in", ["reference_data.pe.submit", perm.PE_APPROVE_ACTIVATE]],
		},
	):
		return  # idempotent — only seed once
	log_audit_event(
		event_type="reference_data.pe",
		entity=C.PE_MOH,
		document_type="Procuring Entity",
		document_name=C.PE_MOH,
		action="reference_data.pe.submit",
		performed_by=STEWARD_EMAIL,
		timestamp=get_datetime("2026-06-29 10:10:00"),
	)
	log_audit_event(
		event_type="reference_data.pe",
		entity=C.PE_MOH,
		document_type="Procuring Entity",
		document_name=C.PE_MOH,
		action=perm.PE_APPROVE_ACTIVATE,
		performed_by=APPROVER_EMAIL,
		timestamp=get_datetime("2026-06-30 16:25:00"),
	)


# --- §16 seed contract: Financial Year 2027/28 ------------------------------------


def seed_financial_year_2027_2028() -> str:
	fy_name = "FY-2027-2028"
	if frappe.db.exists("Financial Year", fy_name):
		return fy_name
	txn.create_fy_draft(2027, user=STEWARD_EMAIL)
	txn.submit_fy(fy_name, user=STEWARD_EMAIL)
	txn.approve_fy(fy_name, user=APPROVER_EMAIL)
	return fy_name


# --- §16 seed contract: PE/FY Contexts --------------------------------------------

_CONTEXT_ACTIVE_FROM = "2027-01-01 00:00:00"
_CONTEXT_ACTIVE_TO = "2028-09-30 23:59:00"


def _seed_context(pe: str, fy: str) -> str:
	"""Runs the real governed chain (draft/submit/recommend/approve) as the
	seeded Steward/Reviewer/AO. active_from is 1 Jan 2027 — in the future
	relative to whenever this seed actually runs in 2026 — so approve_context()
	correctly leaves it Scheduled, matching real automated-activation semantics.
	It is then force-activated: this fixture represents a snapshot as of the
	spec's stated 15 Mar 2027 fixture clock (§16), not the real run date, and
	there is no way to make the real scheduler cross a fictional future date.
	Documented direct status write, narrowly scoped, not a substitute for the
	governed chain that already ran."""
	context_name = f"CTX-{pe.removeprefix('PE-')}-2027-2028"
	if frappe.db.exists("PE Fiscal Year Context", context_name):
		return context_name

	txn.create_context_draft(pe, fy, _CONTEXT_ACTIVE_FROM, _CONTEXT_ACTIVE_TO, user=CTX_STEWARD_EMAIL)
	txn.submit_context(context_name, user=CTX_STEWARD_EMAIL)
	txn.recommend_context(context_name, user=CTX_REVIEWER_EMAIL)
	txn.approve_context(context_name, user=CTX_AO_EMAIL)  # -> Scheduled (active_from is future for real)

	frappe.db.set_value("PE Fiscal Year Context", context_name, "context_status", "Active", update_modified=False)
	log_audit_event(
		event_type="reference_data.context",
		entity=context_name,
		document_type="PE Fiscal Year Context",
		document_name=context_name,
		action="reference_data.context.activate",
		performed_by="Administrator",
		metadata={"seed_forced": True},
	)
	return context_name


def seed_pe_fy_contexts() -> dict[str, str]:
	contexts = {
		C.PE_MOH: _seed_context(C.PE_MOH, "FY-2027-2028"),
		C.PE_NSSF: _seed_context(C.PE_NSSF, "FY-2027-2028"),
		C.PE_CGKIS: _seed_context(C.PE_CGKIS, "FY-2027-2028"),
	}

	# §16's exact governance-history timestamps are given for CTX-MOH-2027-2028
	# only — NSSF/CGKIS contexts exist and are Active but keep their real seed-run
	# timestamps (spec gives no exact values for them, so there is nothing to
	# backdate against).
	moh_ctx = contexts[C.PE_MOH]
	_backdate_audit_event(
		"PE Fiscal Year Context", moh_ctx, perm.CTX_CREATE_DRAFT, CTX_STEWARD_EMAIL, "2026-12-13 09:05:00"
	)
	_backdate_audit_event(
		"PE Fiscal Year Context", moh_ctx, "reference_data.context.submit", CTX_STEWARD_EMAIL, "2026-12-13 09:05:00"
	)
	_backdate_audit_event(
		"PE Fiscal Year Context", moh_ctx, perm.CTX_RECOMMEND, CTX_REVIEWER_EMAIL, "2026-12-14 11:15:00"
	)
	_backdate_audit_event(
		"PE Fiscal Year Context", moh_ctx, perm.CTX_APPROVE, CTX_AO_EMAIL, "2026-12-15 14:40:00"
	)
	_backdate_audit_event(
		"PE Fiscal Year Context",
		moh_ctx,
		"reference_data.context.activate",
		"Administrator",
		"2027-01-01 00:00:00",
	)
	return contexts


def upsert_reference_data_mvp1() -> dict[str, Any]:
	"""§16 full seed contract, run after upsert_pe_types/upsert_pe_governance_actors/
	upsert_context_governance_actors/migrate_legacy_pes in the orchestrator."""
	seed_pe_moh_history()
	nssf = seed_pe_nssf()
	fy = seed_financial_year_2027_2028()
	contexts = seed_pe_fy_contexts()
	roles = ensure_reference_data_governance_roles(
		[STEWARD_EMAIL, APPROVER_EMAIL, CTX_STEWARD_EMAIL, CTX_REVIEWER_EMAIL, CTX_AO_EMAIL]
	)
	return {"pe_nssf": nssf, "financial_year": fy, "contexts": contexts, "governance_roles": roles}
