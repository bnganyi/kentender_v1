# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §22.1 / §25 **EX-04** / **EX-20** — block v1 rule-injection configuration and publish without STD binding.

Detects v1-style manual rule-injection flags on tender documents. All denials use ``AUTH_LEGACY_PATH_DENIED`` and record
``DeniedActionAuditService`` (smoke doc 8 — Access Denied).

**TM2 Tender** must not carry DSM/DOM/DEM/DCM-owned rule injection (top-level flags or
``configuration_json``); see :func:`assert_tm2_tender_no_legacy_rule_injection`.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.audit.denied_action import (
	DeniedActionAuditService,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)

# Same canonical keys as ``validate_legacy_lockout_checks`` (doc 5 §18.8 / WORKS-LEGACY-*).
LEGACY_RULE_INJECTION_KEYS: frozenset[str] = frozenset(
	{
		"content_source_is_upload",
		"manual_submission_checklist_enabled",
		"manual_opening_register_enabled",
		"manual_evaluation_criteria_enabled",
		"manual_contract_terms_enabled",
	}
)


def _truthy_legacy(value: Any) -> bool:
	if value in (1, True, "1"):
		return True
	if isinstance(value, str) and value.strip().lower() in ("true", "yes", "on"):
		return True
	return False


def _collect_legacy_keys_from_mapping(obj: Any, found: set[str]) -> None:
	if isinstance(obj, dict):
		for key, val in obj.items():
			ks = str(key)
			if ks in LEGACY_RULE_INJECTION_KEYS and _truthy_legacy(val):
				found.add(ks)
			_collect_legacy_keys_from_mapping(val, found)
	elif isinstance(obj, list):
		for item in obj:
			_collect_legacy_keys_from_mapping(item, found)


def collect_legacy_rule_injection_flags(tender_doc: Document) -> list[str]:
	"""Return sorted unique legacy flag names present on the tender or in ``configuration_json``."""
	found: set[str] = set()
	for key in LEGACY_RULE_INJECTION_KEYS:
		if hasattr(tender_doc, key) and _truthy_legacy(getattr(tender_doc, key, None)):
			found.add(key)
	raw = tender_doc.get("configuration_json")
	parsed: dict | None = None
	if isinstance(raw, dict):
		parsed = raw
	elif isinstance(raw, str) and raw.strip():
		try:
			out = json.loads(raw)
		except json.JSONDecodeError:
			out = None
		parsed = out if isinstance(out, dict) else None
	if isinstance(parsed, dict):
		_collect_legacy_keys_from_mapping(parsed, found)
	return sorted(found)


def record_auth_legacy_path_denial(
	*,
	actor: str,
	action_code: str,
	object_type: str,
	object_code: str,
	user_message: str,
	event_type: str,
	tender_code: str | None = None,
) -> str | None:
	"""Append denied-action audit with ``AUTH_LEGACY_PATH_DENIED`` (Critical)."""
	tc = (tender_code or object_code or "").strip() or None
	full_message = f"Access Denied — {user_message.strip()}"
	return DeniedActionAuditService.record_denied_action(
		(actor or "").strip() or "Administrator",
		action_code,
		object_type,
		object_code,
		{
			"denial_code": DenialCode.AUTH_LEGACY_PATH_DENIED.value,
			"message": full_message,
			"risk_level": "Critical",
		},
		{
			"event_type": event_type,
			"tender_code": tc or object_code,
			"message": full_message,
		},
	)


def assert_tm2_tender_no_legacy_rule_injection(tm2_doc: Document) -> None:
	"""Deny internal DSM/DOM/DEM/DCM v1-style rule injection on **TM2 Tender** (doc 9 §25 EX-04)."""
	flags = collect_legacy_rule_injection_flags(tm2_doc)
	if not flags:
		return
	tc = cstr(getattr(tm2_doc, "tender_code", None) or "").strip() or tm2_doc.name
	actor = (frappe.session.user or "").strip() or "Administrator"
	record_auth_legacy_path_denial(
		actor=actor,
		action_code="SAVE_TM2_TENDER",
		object_type="TM2 Tender",
		object_code=tm2_doc.name,
		user_message=_(
			"TM2 Tender may not define DSM/DOM/DEM/DCM-owned rules internally ({0})."
		).format(", ".join(flags)),
		event_type=AuditEventCode.MANUAL_RULE_INJECTION_DENIED.value,
		tender_code=tc,
	)
	frappe.throw(
		_("Tender Management v2 does not allow internal rule-injection flags on TM2 Tender ({0}).").format(
			", ".join(flags)
		),
		frappe.ValidationError,
		title=DenialCode.AUTH_LEGACY_PATH_DENIED.value,
	)


def assert_procurement_tender_std_binding_for_publish(
	tender_code: str, *, actor: str
) -> None:
	"""Deny publication when **TM2 Tender** has no ``std_template`` (doc 9 §22.1 item 5).

	Legacy name retained for imports; ``tender_code`` is the business **TM2** ``tender_code`` (or doc name).
	"""
	from kentender_procurement.tender_management.services.tm2_tender_resolve import (
		resolve_tm2_tender_document,
	)

	tc = (tender_code or "").strip()
	if not tc:
		return
	tm2 = resolve_tm2_tender_document(tc)
	if not tm2:
		return
	std_tpl = (tm2.get("std_template") or "").strip()
	if std_tpl:
		return
	act = (actor or "").strip() or "Administrator"
	tcode = cstr(getattr(tm2, "tender_code", None) or "").strip() or tm2.name
	record_auth_legacy_path_denial(
		actor=act,
		action_code="PUBLISH_TENDER",
		object_type="TM2 Tender",
		object_code=tm2.name,
		user_message=_("Publication requires an STD template binding on the TM2 tender."),
		event_type=AuditEventCode.PUBLICATION_DENIED.value,
		tender_code=tcode,
	)
	frappe.throw(
		_("Cannot publish: TM2 tender has no STD template binding."),
		frappe.ValidationError,
		title=DenialCode.AUTH_LEGACY_PATH_DENIED.value,
	)
