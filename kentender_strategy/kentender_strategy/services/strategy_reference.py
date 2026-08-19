# Copyright (c) 2026, KenTender and contributors
"""System-generated immutable Strategy references ({PE}-{TYPE}-####)."""

from __future__ import annotations

import re

import frappe
from frappe import _

from kentender_strategy.services.strategy_permissions import user_roles

# Type token → (DocType, fieldname)
REF_TYPE_META: dict[str, tuple[str, str]] = {
	"SP": ("Strategic Plan", "plan_code"),
	"PROG": ("Strategy Programme", "programme_code"),
	"SUB": ("Strategy Sub Programme", "sub_programme_code"),
	"OUT": ("Strategic Outcome", "outcome_code"),
	"IND": ("Performance Indicator", "indicator_code"),
	"TGT": ("Performance Target", "target_code"),
	"MSR": ("Performance Measurement", "measurement_code"),
	"CA": ("Strategy Corrective Action", "corrective_action_code"),
	"PVC": ("Strategy Value Commitment", "commitment_code"),
}

DOCTYPE_REF: dict[str, tuple[str, str]] = {
	dt: (token, field) for token, (dt, field) in REF_TYPE_META.items()
}

REF_RE = re.compile(r"^[A-Z0-9]+-(SP|PROG|SUB|OUT|IND|TGT|MSR|CA|PVC)-\d{4}$")


def pe_slug(procuring_entity: str | None) -> str:
	"""Business prefix from PE entity_code (PE-MOH → MOH)."""
	if not procuring_entity:
		frappe.throw(_("Procuring entity is required to allocate a reference"))
	code = frappe.db.get_value("Procuring Entity", procuring_entity, "entity_code") or procuring_entity
	code = str(code).strip().upper()
	if code.startswith("PE-"):
		code = code[3:]
	slug = re.sub(r"[^A-Z0-9]", "", code)
	if not slug:
		frappe.throw(_("Procuring entity has no usable code for references"))
	return slug


def _max_seq(doctype: str, field: str, prefix: str) -> int:
	# has_column expects the DocType name (not tab-prefixed table name).
	if not frappe.db.has_column(doctype, field):
		return 0
	rows = frappe.db.sql(
		f"SELECT `{field}` FROM `tab{doctype}` WHERE `{field}` LIKE %s",
		(prefix + "%",),
	)
	max_seq = 0
	for (raw,) in rows:
		if not raw or not str(raw).startswith(prefix):
			continue
		tail = str(raw)[len(prefix) :]
		if tail.isdigit():
			max_seq = max(max_seq, int(tail))
	return max_seq


def _series_current(series_key: str) -> int | None:
	"""Read tabSeries.current without DocType ORM (Series has no creation column)."""
	row = frappe.db.sql(
		"SELECT `current` FROM `tabSeries` WHERE `name`=%s",
		(series_key,),
	)
	return int(row[0][0]) if row else None


def allocate_reference(procuring_entity: str, type_token: str) -> str:
	"""Allocate next never-reuse `{PE}-{TYPE}-####` for the entity.

	Uses Frappe naming series (same family as Package/Demand). Series is advanced
	on each call so allocate paths do not reuse numbers. On first use for a prefix,
	the series is seeded past any existing max so remapped seed codes are not reissued.
	"""
	from frappe.model.naming import make_autoname

	type_token = (type_token or "").strip().upper()
	if type_token not in REF_TYPE_META:
		frappe.throw(_("Unknown reference type: {0}").format(type_token))
	doctype, field = REF_TYPE_META[type_token]
	slug = pe_slug(procuring_entity)
	prefix = f"{slug}-{type_token}-"
	series_key = prefix  # Series.name is the prefix including trailing '-'
	# Seed series past current max once (idempotent when series already ahead).
	current_max = _max_seq(doctype, field, prefix)
	existing_series = _series_current(series_key)
	if existing_series is None and current_max:
		frappe.db.sql(
			"INSERT INTO `tabSeries` (`name`, `current`) VALUES (%s, %s)",
			(series_key, current_max),
		)
	elif existing_series is not None and existing_series < current_max:
		frappe.db.sql(
			"UPDATE `tabSeries` SET `current`=%s WHERE `name`=%s",
			(current_max, series_key),
		)
	for _ in range(200):
		candidate = make_autoname(f"{prefix}.####")
		if not frappe.db.exists(doctype, {field: candidate}):
			return candidate
	frappe.throw(_("Could not allocate a unique {0} reference").format(type_token))


def can_correct_reference(user: str | None = None) -> bool:
	"""Strategy Administrator stand-in: System Manager / Administrator only."""
	have = user_roles(user)
	return "System Manager" in have or frappe.session.user == "Administrator"


def assert_reference_immutable(doc, field: str) -> None:
	"""Block reference edits after first save unless admin correction flag is set."""
	if doc.is_new():
		return
	if not doc.has_value_changed(field):
		return
	if getattr(frappe.flags, "strategy_reference_correction", False) and can_correct_reference():
		return
	frappe.throw(
		_("{0} is system-generated and cannot be edited").format(frappe.unscrub(field)),
		frappe.ValidationError,
	)


def ensure_doc_reference(doc, type_token: str, procuring_entity: str | None, field: str) -> str:
	"""Assign reference on insert when empty. Returns the reference value."""
	current = (doc.get(field) or "").strip()
	if current:
		return current
	if not doc.is_new() and current:
		return current
	ref = allocate_reference(procuring_entity, type_token)
	doc.set(field, ref)
	return ref


def resolve_pe_for_doc(doc) -> str | None:
	"""Best-effort procuring entity for allocation."""
	if doc.get("procuring_entity"):
		return doc.procuring_entity
	plan_version = doc.get("plan_version")
	if plan_version:
		return frappe.db.get_value("Strategic Plan", plan_version, "procuring_entity")
	if doc.doctype == "Performance Measurement" and doc.get("performance_target"):
		pv = frappe.db.get_value("Performance Target", doc.performance_target, "plan_version")
		if pv:
			doc.plan_version = pv
			return frappe.db.get_value("Strategic Plan", pv, "procuring_entity")
	if doc.doctype == "Strategy Corrective Action" and doc.get("plan_version"):
		return frappe.db.get_value("Strategic Plan", doc.plan_version, "procuring_entity")
	return None


def before_insert_assign_reference(doc) -> None:
	meta = DOCTYPE_REF.get(doc.doctype)
	if not meta:
		return
	type_token, field = meta
	pe = resolve_pe_for_doc(doc)
	ensure_doc_reference(doc, type_token, pe, field)


def validate_reference_field(doc) -> None:
	meta = DOCTYPE_REF.get(doc.doctype)
	if not meta:
		return
	_type_token, field = meta
	assert_reference_immutable(doc, field)
	code = (doc.get(field) or "").strip()
	if not code:
		frappe.throw(_("{0} is required").format(frappe.unscrub(field)))


def correct_reference(
	doctype: str,
	name: str,
	new_code: str,
	reason: str,
	plan_version: str | None = None,
) -> dict:
	"""Pre-activation admin correction with audit trail."""
	if not can_correct_reference():
		frappe.throw(_("Only a Strategy Administrator may correct references"), frappe.PermissionError)
	meta = DOCTYPE_REF.get(doctype)
	if not meta:
		frappe.throw(_("Unsupported DocType for reference correction"))
	_token, field = meta
	new_code = (new_code or "").strip().upper()
	if not REF_RE.match(new_code):
		frappe.throw(_("Reference format is invalid"))
	reason = (reason or "").strip()
	if not reason:
		frappe.throw(_("Reason is required to correct a reference"))

	doc = frappe.get_doc(doctype, name)
	# Pre-activation only for plan-scoped docs
	pv = plan_version or doc.get("plan_version")
	if doctype == "Strategic Plan":
		pv = doc.name
		if doc.status not in ("Draft", "Returned"):
			frappe.throw(_("References can only be corrected before activation"))
	elif pv:
		status = frappe.db.get_value("Strategic Plan", pv, "status")
		if status not in ("Draft", "Returned"):
			frappe.throw(_("References can only be corrected before the plan is activated"))

	prior = doc.get(field)
	if prior == new_code:
		return {"id": doc.name, "code": prior, "unchanged": True}
	if frappe.db.exists(doctype, {field: new_code, "name": ["!=", name]}):
		frappe.throw(_("Reference {0} is already in use").format(new_code))

	frappe.flags.strategy_reference_correction = True
	try:
		doc.set(field, new_code)
		doc.save(ignore_permissions=True)
	finally:
		frappe.flags.strategy_reference_correction = False

	from kentender_strategy.services.strategy_audit import record_event

	audit_id = record_event(
		entity_type=doctype,
		entity_name=doc.name,
		event_type="Reference Corrected",
		prior_state=prior or "",
		new_state=new_code,
		plan_version=pv if pv and frappe.db.exists("Strategic Plan", pv) else None,
		reason=reason,
		summary=f"Reference corrected {prior} → {new_code}",
	)
	return {"id": doc.name, "code": new_code, "prior": prior, "audit_event": audit_id}
