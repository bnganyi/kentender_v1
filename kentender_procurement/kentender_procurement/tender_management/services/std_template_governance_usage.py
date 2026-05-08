# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD template governance — tender eligibility, usage rows, impact (doc 7 §13.4, §16, STD-GOV-008).

``resolve_active_std_template_for_context`` is intentionally conservative: it returns
``ok: false`` with ``error: "ambiguous"`` when multiple active templates match filters and
``template_code`` is not pinned in ``context``.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_procurement.tender_management.services.std_template_governance import (
	EVT_USAGE_BLOCKED,
	EVT_USED_FOR_TENDER,
	STATUS_ACTIVE,
	canonicalize_std_package_payload,
)
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)

USAGE_TYPE_TENDER = "Tender"
USAGE_TYPE_INSTANCE = "Tender STD Instance"
USAGE_TYPE_PLANNING = "Planning Mapping Test"
ALLOWED_USAGE_TYPES = frozenset({USAGE_TYPE_TENDER, USAGE_TYPE_INSTANCE, USAGE_TYPE_PLANNING})


def _guest_blocked() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _norm(s: str | None) -> str:
	return (s or "").strip().upper()


def check_std_template_tender_creation_eligibility(
	std_template: str,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 7 §16 — return eligibility envelope.

	If ``context`` contains truthy ``emit_usage_blocked_event`` and the template is ineligible,
	appends ``EVT_USAGE_BLOCKED`` (single ``save``).
	"""
	ctx = dict(context) if context else {}
	emit_blocked = bool(ctx.pop("emit_usage_blocked_event", False))

	doc = frappe.get_doc("STD Template", std_template)
	reasons: list[str] = []
	warnings: list[str] = []

	ph = (doc.get("package_hash") or "").strip()
	if not ph:
		reasons.append("missing_package_hash")

	if doc.lifecycle_status != STATUS_ACTIVE:
		reasons.append("lifecycle_not_active")

	if not int(doc.get("allowed_for_tender_creation") or 0):
		reasons.append("not_allowed_for_tender_creation")

	for label, fld in (
		("activation_package_hash", "activation_package_hash"),
		("approval_package_hash", "approval_package_hash"),
		("latest_validation_package_hash", "latest_validation_package_hash"),
	):
		val = (doc.get(fld) or "").strip()
		if val != ph:
			reasons.append(f"hash_mismatch:{label}")

	if int(doc.get("is_suspended") or 0):
		reasons.append("is_suspended")

	# --- mapping context (doc 7 §16.8) --------------------------------------
	tf_ctx = ctx.get("template_family")
	if tf_ctx and (doc.get("template_family") or "").strip() and _norm(tf_ctx) != _norm(
		str(doc.get("template_family"))
	):
		reasons.append("template_family_mismatch")

	pc_ctx = ctx.get("procurement_category")
	if pc_ctx and (doc.get("procurement_category") or "").strip() and _norm(pc_ctx) != _norm(
		str(doc.get("procurement_category"))
	):
		reasons.append("procurement_category_mismatch")

	if ctx.get("template_code") and str(ctx["template_code"]).strip() != doc.name:
		reasons.append("template_code_mismatch")

	eligible = len(reasons) == 0

	out: dict[str, Any] = {
		"eligible": eligible,
		"std_template": doc.name,
		"lifecycle_status": doc.lifecycle_status,
		"allowed_for_tender_creation": bool(int(doc.get("allowed_for_tender_creation") or 0)),
		"package_hash": ph,
		"reasons": reasons,
		"warnings": warnings,
	}

	if emit_blocked and not eligible:
		write_std_template_lifecycle_event(
			doc,
			EVT_USAGE_BLOCKED,
			"eligibility",
			{"reasons": reasons, "context": ctx},
			from_status=doc.lifecycle_status,
			save=True,
		)

	return out


def get_std_template_usage_impact(std_template: str) -> dict[str, Any]:
	"""Return a structured usage / lock snapshot for ``std_template`` (doc 7 §13.4)."""
	doc = frappe.get_doc("STD Template", std_template)
	rows = list(doc.get("template_usage") or [])
	last_row = None
	if rows:
		last_row = rows[-1].as_dict()
		last_row.pop("name", None)
		last_row.pop("parent", None)
		last_row.pop("parenttype", None)
		last_row.pop("parentfield", None)
		last_row.pop("idx", None)

	return {
		"std_template": doc.name,
		"tender_usage_count": int(doc.get("tender_usage_count") or 0),
		"locked_due_to_usage": int(doc.get("locked_due_to_usage") or 0),
		"mutation_blocked": int(doc.get("mutation_blocked") or 0),
		"delete_blocked": int(doc.get("delete_blocked") or 0),
		"usage_row_count": len(rows),
		"last_usage_row": last_row,
	}


def record_std_template_usage(
	std_template: str,
	usage_type: str,
	tender: str | None = None,
	tender_std_instance: str | None = None,
	procurement_package: str | None = None,
	configuration_hash: str | None = None,
	payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Append ``template_usage``, bump counters, lock mutations, emit ``EVT_USED_FOR_TENDER``.

	Requires the template to pass :func:`check_std_template_tender_creation_eligibility` first.
	"""
	_guest_blocked()
	if usage_type not in ALLOWED_USAGE_TYPES:
		frappe.throw(_("Invalid usage_type."), frappe.ValidationError)

	elig = check_std_template_tender_creation_eligibility(std_template, None)
	if not elig.get("eligible"):
		frappe.throw(
			_("STD Template is not eligible for usage recording: {0}").format(
				", ".join(elig.get("reasons") or [])
			),
			frappe.ValidationError,
		)

	doc = frappe.get_doc("STD Template", std_template)
	ph = (doc.get("package_hash") or "").strip()
	if not ph:
		frappe.throw(_("package_hash is required to record usage."), frappe.ValidationError)

	usage_code = f"STD-USG-{frappe.generate_hash(length=12)}"
	payload_json: str | None
	if payload:
		payload_json = canonicalize_std_package_payload(payload)
	else:
		payload_json = None

	doc.append(
		"template_usage",
		{
			"usage_code": usage_code,
			"used_at": now_datetime(),
			"used_by": frappe.session.user,
			"usage_type": usage_type,
			"tender": tender,
			"tender_std_instance": tender_std_instance,
			"procurement_package": procurement_package,
			"package_hash_at_use": ph,
			"configuration_hash_at_use": (configuration_hash or "")[:140] or None,
			"usage_status": "Active",
			"payload_json": payload_json,
		},
	)

	doc.tender_usage_count = int(doc.get("tender_usage_count") or 0) + 1
	if not doc.get("first_used_at"):
		doc.first_used_at = now_datetime()
	doc.last_used_at = now_datetime()
	doc.locked_due_to_usage = 1
	doc.mutation_blocked = 1

	summary = {
		"tender_usage_count": doc.tender_usage_count,
		"last_usage_code": usage_code,
		"updated_at": str(now_datetime()),
	}
	doc.usage_summary_json = json.dumps(summary, sort_keys=True, separators=(",", ":"))

	write_std_template_lifecycle_event(
		doc,
		EVT_USED_FOR_TENDER,
		"usage",
		{
			"usage_code": usage_code,
			"usage_type": usage_type,
			"tender": tender,
			"procurement_package": procurement_package,
		},
		from_status=doc.lifecycle_status,
		save=False,
	)
	doc.save(ignore_permissions=True)

	return {
		"ok": True,
		"std_template": doc.name,
		"usage_code": usage_code,
		"tender_usage_count": doc.tender_usage_count,
		"impact": get_std_template_usage_impact(doc.name),
	}


def resolve_active_std_template_for_context(context: dict[str, Any]) -> dict[str, Any]:
	"""Resolve a single **Active** tender-eligible ``STD Template`` for ``context`` filters."""
	ctx = dict(context or {})
	filters: dict[str, Any] = {
		"lifecycle_status": STATUS_ACTIVE,
		"allowed_for_tender_creation": 1,
	}
	if code := (ctx.get("template_code") or "").strip():
		filters["name"] = code
	if tf := (ctx.get("template_family") or "").strip():
		filters["template_family"] = tf
	if pc := (ctx.get("procurement_category") or "").strip():
		filters["procurement_category"] = pc
	if pmp := (ctx.get("procurement_method_profile") or "").strip():
		filters["procurement_method_profile"] = pmp
	if apk := (ctx.get("active_profile_key") or "").strip():
		filters["active_profile_key"] = apk

	rows = frappe.get_all(
		"STD Template",
		filters=filters,
		pluck="name",
		order_by="modified desc",
		limit=20,
	)
	if not rows:
		return {"ok": False, "error": "not_found", "std_template": None}
	if len(rows) > 1 and not (ctx.get("template_code") or "").strip():
		return {
			"ok": False,
			"error": "ambiguous",
			"std_template": None,
			"candidates": rows,
		}
	return {"ok": True, "std_template": rows[0], "candidates": rows}
