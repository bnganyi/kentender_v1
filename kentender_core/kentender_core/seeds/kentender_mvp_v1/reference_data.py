# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.4 — PE Type catalogue, Procuring Entity versioning, Financial
Year, PE/FY Context seed data for KENTENDER_MVP_V1. One Reference Data
Manager Frappe Role is the entire maintenance authority (AUTH-ADR-001 v1.1)
— no Capability Profile, Operational Scope Assignment or Separation of Duties
Rule is created for this domain.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.services import reference_data_transitions as txn
from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.reference_data_permissions import REFERENCE_DATA_MANAGER_ROLE

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


# --- Reference Data Manager (§7, §16) -------------------------------------------


def ensure_reference_data_governance_roles(manager_emails: list[str]) -> dict[str, Any]:
	"""AUTH-ADR-001 v1.1 §5.2/§12.2 — Reference Data Manager is the only Role
	that grants PE, Financial Year and PE/FY Context maintenance authority.
	Superseded five-role model (Central Reference Data Steward, Central
	Configuration Approver, PE Configuration Steward, Professional
	Configuration Reviewer / HoPF, and any reference-data-specific Accounting
	Officer grant) is retired by kentender_core.patches.v1_0.
	retire_reference_data_role_proliferation, not reintroduced here."""
	if not frappe.db.exists("Role", REFERENCE_DATA_MANAGER_ROLE):
		frappe.get_doc(
			{"doctype": "Role", "role_name": REFERENCE_DATA_MANAGER_ROLE, "desk_access": 1}
		).insert(ignore_permissions=True)
	for email in manager_emails:
		if frappe.db.exists("User", email):
			frappe.get_doc("User", email).add_roles(REFERENCE_DATA_MANAGER_ROLE)
	return {"role": REFERENCE_DATA_MANAGER_ROLE, "granted_to": manager_emails}


# --- Governance actor (§16) -----------------------------------------------------

STEWARD_EMAIL = "lydia.mwangi@kentender.example.test"
STEWARD_NAME = "Lydia Mwangi"


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
	current legal_name/status. Not a governed transition (no create/activate
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
	(create then activate) as the seeded Reference Data Manager, not a direct write."""
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
	txn.activate_pe(C.PE_NSSF, user=STEWARD_EMAIL)
	return C.PE_NSSF


def seed_pe_moh_history() -> None:
	"""§16's governance-history table for PE-MOH: draft created (Lydia, 29 Jun
	2026 10:10 EAT) / activated (Lydia, 30 Jun 2026 16:25 EAT). PE-MOH's
	version was created by migrate_legacy_pe_to_versioned() (a one-time,
	pre-CFG-CHG-002 direct migration, not a live governed transition — there is
	no real create/activate call to backdate), so these two history rows are
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
			"action": ["in", ["reference_data.pe.create_draft", "reference_data.pe.activate"]],
		},
	):
		return  # idempotent — only seed once
	log_audit_event(
		event_type="reference_data.pe",
		entity=C.PE_MOH,
		document_type="Procuring Entity",
		document_name=C.PE_MOH,
		action="reference_data.pe.create_draft",
		performed_by=STEWARD_EMAIL,
		timestamp=get_datetime("2026-06-29 10:10:00"),
	)
	log_audit_event(
		event_type="reference_data.pe",
		entity=C.PE_MOH,
		document_type="Procuring Entity",
		document_name=C.PE_MOH,
		action="reference_data.pe.activate",
		performed_by=STEWARD_EMAIL,
		timestamp=get_datetime("2026-06-30 16:25:00"),
	)


# --- §16 seed contract: Financial Year 2027/28 ------------------------------------


def seed_financial_year_2027_2028() -> str:
	fy_name = "FY-2027-2028"
	if frappe.db.exists("Financial Year", fy_name):
		return fy_name
	txn.create_fy_draft(2027, user=STEWARD_EMAIL)
	txn.make_fy_available(fy_name, user=STEWARD_EMAIL)
	return fy_name


# --- §16 seed contract: PE/FY Contexts --------------------------------------------

_CONTEXT_ACTIVE_FROM = "2027-01-01 00:00:00"
_CONTEXT_ACTIVE_TO = "2028-09-30 23:59:00"


def _seed_context(pe: str, fy: str) -> str:
	"""Runs the real governed action (enable) as the seeded Reference Data
	Manager. active_from is 1 Jan 2027 — in the future relative to whenever
	this seed actually runs in 2026 — so enable_context() correctly leaves it
	Scheduled, matching real automated-activation semantics. It is then
	force-activated: this fixture represents a snapshot as of the spec's
	stated 15 Mar 2027 fixture clock (§16), not the real run date, and there
	is no way to make the real scheduler cross a fictional future date.
	Documented direct status write, narrowly scoped, not a substitute for the
	governed action that already ran."""
	context_name = f"CTX-{pe.removeprefix('PE-')}-2027-2028"
	if frappe.db.exists("PE Fiscal Year Context", context_name):
		return context_name

	txn.enable_context(pe, fy, _CONTEXT_ACTIVE_FROM, _CONTEXT_ACTIVE_TO, user=STEWARD_EMAIL)  # -> Scheduled (active_from is future for real)

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
		"PE Fiscal Year Context", moh_ctx, "reference_data.context.enable", STEWARD_EMAIL, "2026-12-15 14:40:00"
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
	"""§16 full seed contract, run after upsert_pe_types/migrate_legacy_pes in
	the orchestrator."""
	_upsert_desk_user(STEWARD_EMAIL, STEWARD_NAME)
	roles = ensure_reference_data_governance_roles([STEWARD_EMAIL])
	seed_pe_moh_history()
	nssf = seed_pe_nssf()
	fy = seed_financial_year_2027_2028()
	contexts = seed_pe_fy_contexts()
	return {"pe_nssf": nssf, "financial_year": fy, "contexts": contexts, "governance_roles": roles}
