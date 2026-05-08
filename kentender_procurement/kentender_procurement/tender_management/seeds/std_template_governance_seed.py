# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS POC STD Template — governance seed (doc 7 §21, STD-GOV-012).

Idempotent overlay for ``KE-PPRA-WORKS-BLDG-2022-04-POC`` (or a test ``template_code``):

- **active** mode (``developer_mode`` or ``force_mode=\"active\"``): lifecycle **Active**,
  tender-eligible flags + hash alignment, ``payload_locked``, four lifecycle rows
  (imported → validation completed → approved → activated) with ``STD-GOV-012`` marker.
- **approved** mode (production migrate): lifecycle **Approved**, hashes aligned,
  ``allowed_for_tender_creation`` 0, three lifecycle rows (no activation event).

Re-run after the marker exists for the same mode → ``{"action": "noop"}``.
Upgrades **approved → active** when switching to active mode (adds activation only).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.std_template_governance import (
	EVT_ACTIVATED,
	EVT_APPROVED,
	EVT_IMPORTED,
	EVT_VALIDATION_COMPLETED,
	STATUS_ACTIVE,
	STATUS_APPROVED,
	STATUS_IMPORTED,
	STATUS_VALIDATED,
	VALIDATION_PASS,
)
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)

SEED_MARKER = "STD-GOV-012"
SEED_RUN_ID = "STD-GOV-012-SEED"
SOURCE_AUTHORITY = "PPRA / POC source"


def _seed_payload(mode: str, **extra: Any) -> dict[str, Any]:
	return {"seed": SEED_MARKER, "mode": mode, **extra}


def _marker_mode_from_events(doc: Any) -> str | None:
	for row in reversed(doc.get("lifecycle_events") or []):
		raw = getattr(row, "payload_json", None) or ""
		if not raw:
			continue
		try:
			data = json.loads(raw)
		except json.JSONDecodeError:
			continue
		if data.get("seed") == SEED_MARKER and data.get("mode") in ("active", "approved"):
			return str(data["mode"])
	return None


def _seed_satisfied(doc: Any, mode: str) -> bool:
	if _marker_mode_from_events(doc) != mode:
		return False
	if mode == "active":
		return doc.lifecycle_status == STATUS_ACTIVE
	return doc.lifecycle_status == STATUS_APPROVED


def _append_seed_events(
	doc: Any,
	mode: str,
	*,
	upgrade_from_approved: bool,
) -> None:
	if upgrade_from_approved:
		write_std_template_lifecycle_event(
			doc,
			EVT_ACTIVATED,
			"governance",
			_seed_payload(mode, phase="upgrade_approved_to_active"),
			from_status=STATUS_APPROVED,
			to_status=STATUS_ACTIVE,
			reason="STD-GOV-012 development activation",
			save=False,
		)
		return

	write_std_template_lifecycle_event(
		doc,
		EVT_IMPORTED,
		"import",
		_seed_payload(mode, phase="bootstrap"),
		from_status=None,
		to_status=STATUS_IMPORTED,
		reason="STD-GOV-012 seed",
		save=False,
	)
	write_std_template_lifecycle_event(
		doc,
		EVT_VALIDATION_COMPLETED,
		"validation",
		_seed_payload(mode, validation_run_id=SEED_RUN_ID, run_id=SEED_RUN_ID, ok=True),
		from_status=STATUS_IMPORTED,
		to_status=STATUS_VALIDATED,
		save=False,
	)
	write_std_template_lifecycle_event(
		doc,
		EVT_APPROVED,
		"governance",
		_seed_payload(mode, comments="STD-GOV-012 seed approval"),
		from_status=STATUS_VALIDATED,
		to_status=STATUS_APPROVED,
		reason="STD-GOV-012 seed",
		save=False,
	)
	if mode == "active":
		write_std_template_lifecycle_event(
			doc,
			EVT_ACTIVATED,
			"governance",
			_seed_payload(mode, phase="bootstrap_activate"),
			from_status=STATUS_APPROVED,
			to_status=STATUS_ACTIVE,
			reason="STD-GOV-012 development activation",
			save=False,
		)


def _apply_governance_field_overlay(doc: Any, mode: str) -> None:
	ph = (doc.get("package_hash") or "").strip()
	if not ph:
		return

	doc.is_governed_version = 1
	doc.template_family = doc.template_family or "Works"
	if not (doc.get("procurement_category") or "").strip():
		doc.procurement_category = "WORKS"
	if not (doc.get("template_version") or "").strip():
		doc.template_version = "POC-V1"
	doc.source_authority = SOURCE_AUTHORITY
	doc.source_document_code = doc.name
	doc.import_source_type = "Seed"

	doc.latest_validation_status = VALIDATION_PASS
	doc.latest_validation_run_id = SEED_RUN_ID
	doc.latest_validation_at = now_datetime()
	doc.latest_validation_by = "Administrator"
	doc.latest_validation_package_hash = ph
	doc.latest_validation_result_json = json.dumps(
		{"ok": True, "seed": SEED_MARKER, "run_id": SEED_RUN_ID},
		sort_keys=True,
	)
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 1

	doc.approved_by = doc.approved_by or "Administrator"
	doc.approved_at = doc.approved_at or now_datetime()
	doc.approval_decision = "Approved"
	doc.approval_comments = doc.approval_comments or "STD-GOV-012 seed"
	doc.approval_validation_run_id = SEED_RUN_ID
	doc.approval_package_hash = ph
	doc.approval_override_used = 0
	doc.approval_override_reason = None

	if mode == "active":
		doc.lifecycle_status = STATUS_ACTIVE
		doc.activated_by = doc.activated_by or "Administrator"
		doc.activated_at = doc.activated_at or now_datetime()
		doc.activation_reason = doc.activation_reason or "STD-GOV-012 development seed"
		doc.activation_package_hash = ph
		doc.activation_approval_reference = SEED_RUN_ID
		doc.allowed_for_tender_creation = 1
		doc.is_suspended = 0
		doc.is_default_active_version = 1
	else:
		doc.lifecycle_status = STATUS_APPROVED
		doc.allowed_for_tender_creation = 0
		doc.is_default_active_version = 0


def seed_std_template_governance_for_existing_works_poc(
	template_code: str | None = None,
	*,
	force_mode: str | None = None,
) -> dict[str, Any]:
	"""Idempotent governance overlay (STD-GOV-012). See module docstring."""
	frappe.set_user("Administrator")

	template_code = (template_code or TEMPLATE_CODE).strip()
	mode: str
	if force_mode in ("active", "approved"):
		mode = force_mode
	else:
		mode = "active" if getattr(frappe.conf, "developer_mode", False) else "approved"

	if not frappe.db.exists("STD Template", template_code):
		upsert_std_template(commit=True)

	if not frappe.db.exists("STD Template", template_code):
		return {"ok": False, "error": "missing_std_template", "template_code": template_code}

	doc = frappe.get_doc("STD Template", template_code)

	if _seed_satisfied(doc, mode):
		return {"ok": True, "action": "noop", "template_code": template_code, "mode": mode}

	upgrade = (
		mode == "active"
		and doc.lifecycle_status == STATUS_APPROVED
		and _marker_mode_from_events(doc) == "approved"
	)

	ph = (doc.get("package_hash") or "").strip()
	if not ph:
		upsert_std_template(commit=True)
		doc = frappe.get_doc("STD Template", template_code)
		ph = (doc.get("package_hash") or "").strip()
	if not ph:
		return {"ok": False, "error": "missing_package_hash", "template_code": template_code}

	doc.flags.skip_std_template_guards = True

	if upgrade:
		_apply_governance_field_overlay(doc, "active")
		_append_seed_events(doc, mode, upgrade_from_approved=True)
	else:
		_apply_governance_field_overlay(doc, mode)
		_append_seed_events(doc, mode, upgrade_from_approved=False)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"ok": True,
		"action": "upgrade" if upgrade else "seeded",
		"template_code": template_code,
		"mode": mode,
		"lifecycle_status": doc.lifecycle_status,
	}


def run_after_migrate() -> None:
	"""``after_migrate`` — safe overlay; failures are logged, migrate continues."""
	try:
		seed_std_template_governance_for_existing_works_poc()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "STD-GOV-012 seed_std_template_governance_for_existing_works_poc")
