# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.16 §4.9A / §7.1–7.2 / §12 — Supplier portal settings.

Built ahead of CFG v0.16 approval under BDS-CHG-001 v0.8 owner decision OD-A
(26 Sep 2026). One Single record holds the public support contact and the
three public-notice destinations that the Tenders and Bid Submission portal
pages render. This module is its only writer and the only public reader:

- `update_public_portal_settings` (UpdatePublicPortalSettings): Administrator
  or System Manager; one complete replacement, checked against
  `record_version`, idempotent by key; user-correctable input comes back as
  `{"ok": False, "errors": {field: message}}` (AGENTS.md section 6.10) and
  leaves the record unchanged; every save audits the before/after public
  projection and versions (§12).
- `get_public_portal_settings` (GetPublicPortalSettings): setup authority only.
- `get_public_portal_information` (GetPublicPortalInformation): the
  allowlisted, bidder-safe projection with `Complete`/`Incomplete` and the
  missing categories. It never carries setup audit, prior values or record
  identities. Callers decide what an Incomplete projection blocks (BDS/TPR:
  new Start bid and production Submit); reading public Tenders never depends
  on it.

Saving a destination does not approve the text published there, and nothing
here publishes a Tender, sends a notice or enables bid submission.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

import frappe
from frappe.utils import cstr, now_datetime, validate_email_address

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.configuration_errors import DEFAULT_MESSAGES, fail_cfg
from kentender_core.services.reference_data_idempotency import request_payload, run_idempotent
from kentender_core.services.site_configuration import require_configuration_administrator

SETTINGS = "Public Portal Settings"
EDITABLE_FIELDS: tuple[str, ...] = (
	"supplier_support_email",
	"supplier_support_phone",
	"supplier_support_hours",
	"privacy_notice_url",
	"portal_terms_url",
	"accessibility_statement_url",
)
SUPPORT_LABEL = "Supplier support"
# (projection key, visible label, field) in footer order (BDS-CHG-001 v0.8 §10.1).
NOTICE_LINKS: tuple[tuple[str, str, str], ...] = (
	("privacy", "Privacy and data use", "privacy_notice_url"),
	("terms", "Terms of portal use", "portal_terms_url"),
	("accessibility", "Accessibility", "accessibility_statement_url"),
)
MAX_HOURS_LENGTH = 160
_PHONE = re.compile(r"^\+?[0-9 ()\-]{7,25}$")


def _current_values() -> dict[str, str]:
	return {field: cstr(frappe.db.get_single_value(SETTINGS, field) or "").strip() for field in EDITABLE_FIELDS}


def _current_version() -> int:
	return int(frappe.db.get_single_value(SETTINGS, "record_version") or 0)


def is_public_https_url(value: str) -> bool:
	"""An absolute HTTPS address with a host and no embedded credentials or
	whitespace (CFG16-AC-004)."""
	text = cstr(value or "").strip()
	if not text or any(ch.isspace() for ch in text):
		return False
	try:
		parts = urlsplit(text)
	except ValueError:
		return False
	return parts.scheme == "https" and bool(parts.hostname) and not parts.username and not parts.password


def _email_ok(value: str) -> bool:
	return bool(value) and bool(validate_email_address(value, throw=False))


def _phone_ok(value: str) -> bool:
	return bool(_PHONE.match(value)) and sum(ch.isdigit() for ch in value) >= 7


def _field_errors(values: dict[str, str]) -> dict[str, str]:
	errors: dict[str, str] = {}
	if not _email_ok(values["supplier_support_email"]):
		errors["supplier_support_email"] = DEFAULT_MESSAGES["CFG_PORTAL_SUPPORT_EMAIL_REQUIRED"]
	if values["supplier_support_phone"] and not _phone_ok(values["supplier_support_phone"]):
		errors["supplier_support_phone"] = "Enter a phone number using digits, spaces and an optional leading +."
	if len(values["supplier_support_hours"]) > MAX_HOURS_LENGTH:
		errors["supplier_support_hours"] = f"Enter at most {MAX_HOURS_LENGTH} characters."
	for _key, label, field in NOTICE_LINKS:
		if not is_public_https_url(values[field]):
			errors[field] = f"Enter a complete HTTPS address for {label}."
	return errors


def _projection(values: dict[str, str], version: int) -> dict[str, Any]:
	missing: list[str] = []
	support: dict[str, str] = {"label": SUPPORT_LABEL}
	if _email_ok(values["supplier_support_email"]):
		support["email"] = values["supplier_support_email"]
	else:
		missing.append("support")
	if values["supplier_support_phone"] and _phone_ok(values["supplier_support_phone"]):
		support["phone"] = values["supplier_support_phone"]
	if values["supplier_support_hours"] and len(values["supplier_support_hours"]) <= MAX_HOURS_LENGTH:
		support["hours"] = values["supplier_support_hours"]
	links: list[dict[str, str]] = []
	for key, label, field in NOTICE_LINKS:
		if is_public_https_url(values[field]):
			links.append({"key": key, "label": label, "url": values[field]})
		else:
			missing.append(key)
	return {
		"status": "Incomplete" if missing else "Complete",
		"missing": missing,
		"record_version": version,
		"support": support,
		"links": links,
	}


def get_public_portal_information() -> dict[str, Any]:
	"""GetPublicPortalInformation — the bidder-safe projection (CFG16-AC-006).
	Public: no authority is needed to read it, and it exposes nothing else."""
	return _projection(_current_values(), _current_version())


def get_public_portal_settings() -> dict[str, Any]:
	"""GetPublicPortalSettings — editable values, completeness, token and the
	last-change facts, for setup authority only."""
	require_configuration_administrator()
	values = _current_values()
	version = _current_version()
	projection = _projection(values, version)
	return {
		"values": values,
		"status": projection["status"],
		"missing": projection["missing"],
		"record_version": version,
		"updated_by": cstr(frappe.db.get_single_value(SETTINGS, "updated_by") or ""),
		"updated_at": cstr(frappe.db.get_single_value(SETTINGS, "updated_at") or ""),
	}


def update_public_portal_settings(
	*,
	supplier_support_email: str = "",
	supplier_support_phone: str = "",
	supplier_support_hours: str = "",
	privacy_notice_url: str = "",
	portal_terms_url: str = "",
	accessibility_statement_url: str = "",
	expected_version: int | str | None = None,
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""UpdatePublicPortalSettings — one complete, atomic replacement."""
	request = request_payload(locals())
	actor = require_configuration_administrator()

	def _do() -> dict[str, Any]:
		current = _current_version()
		if expected_version is None or int(expected_version) != current:
			fail_cfg("CFG_VERSION_CONFLICT")
		values = {field: cstr(request[field] or "").strip() for field in EDITABLE_FIELDS}
		errors = _field_errors(values)
		if errors:
			return {"ok": False, "errors": errors}
		before = _projection(_current_values(), current)
		doc = frappe.get_single(SETTINGS)
		for field, value in values.items():
			doc.set(field, value)
		doc.record_version = current + 1
		doc.updated_by = actor
		doc.updated_at = now_datetime()
		frappe.flags.kt_public_portal_command = True
		try:
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.kt_public_portal_command = False
		after = _projection(values, current + 1)
		log_audit_event(
			event_type="site_configuration",
			document_type=SETTINGS,
			document_name=SETTINGS,
			action="update_public_portal_settings",
			metadata={"before": before, "after": after, "before_version": current, "after_version": current + 1},
		)
		return {"ok": True, "record_version": current + 1, "information": after}

	return run_idempotent(idempotency_key, SETTINGS, SETTINGS, "update_public_portal_settings", _do, payload=request)
