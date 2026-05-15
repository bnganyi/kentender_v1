# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §13.1 — ``append_tender_audit_event`` / ``appendTenderAuditEvent``.

Central **append-only** writer for **TM2 Tender Audit Event** with doc 9 **§13.2** payload rules for
material STD publication events:

- **Tender Published** — ``event_payload`` must include non-empty ``bundle_output_code``,
  ``dsm_output_code``, ``dom_output_code``, ``dem_output_code``, ``dcm_output_code``,
  ``publication_snapshot_code``;
- **Addendum Issued** — ``event_payload`` must additionally include non-empty ``addendum_code`` plus the
  same five output codes and ``publication_snapshot_code``.

Other ``event_type`` values are inserted without §13.2 key checks (DocType-level rules such as
TM2-AUD-003/004/006 still apply).

Optional ``tm2_audit_row_extras`` merges whitelisted top-level DocType fields (STD linkage columns,
client context, etc.) for callers that previously set them outside ``event_payload`` (P8-03).

Returns the new row's ``audit_event_code`` (same as ``name``).

Tests: ``tender_management.tests.test_p8_01_append_tender_audit_event``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

# Doc 9 §13.2 — publication snapshot bundle on material audits.
_PUBLICATION_STD_REF_KEYS: frozenset[str] = frozenset(
	{
		"bundle_output_code",
		"dsm_output_code",
		"dom_output_code",
		"dem_output_code",
		"dcm_output_code",
		"publication_snapshot_code",
	}
)

_ADDENDUM_ISSUED_EXTRA_KEYS: frozenset[str] = frozenset({"addendum_code"})

_ACTOR_TYPE_OPTIONS: frozenset[str] = frozenset({"User", "System", "Supplier", "API"})

# Optional top-level columns on ``TM2 Tender Audit Event`` (beyond the core ``append_*`` args).
_OPTIONAL_TM2_AUDIT_ROW_KEYS: frozenset[str] = frozenset(
	{
		"std_template_version_code",
		"tender_std_instance_code",
		"output_reference_code",
		"publication_snapshot_code",
		"actor_role",
		"source_ip",
		"user_agent",
		"hash",
	}
)


def _resolve_tm2_name(tender_code: str) -> str | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return str(name)
	if frappe.db.exists("TM2 Tender", tc):
		return str(tc)
	return None


def _validate_section_13_2_payload(*, event_type: str, payload: dict[str, Any], enforce: bool) -> None:
	if not enforce:
		return
	et = cstr(event_type).strip()
	if et == "Tender Published":
		keys = _PUBLICATION_STD_REF_KEYS
		label = _("Tender Published")
	elif et == "Addendum Issued":
		keys = _PUBLICATION_STD_REF_KEYS | _ADDENDUM_ISSUED_EXTRA_KEYS
		label = _("Addendum Issued")
	else:
		return
	for k in sorted(keys):
		if not cstr(payload.get(k)).strip():
			frappe.throw(
				_("{0} audit payload must include non-empty {1} (doc 9 §13.2).").format(label, frappe.bold(k)),
				title=_("Audit Payload Incomplete"),
			)


def append_tender_audit_event(
	tender_code: str,
	event_type: str,
	actor: str,
	payload: dict[str, Any],
	related_object_type: str | None = None,
	related_object_code: str | None = None,
	previous_state: str | None = None,
	new_state: str | None = None,
	reason: str | None = None,
	*,
	denial_code: str | None = None,
	enforce_section_13_2: bool = True,
	actor_type: str = "User",
	tm2_audit_row_extras: dict[str, Any] | None = None,
) -> str:
	"""Append one **TM2 Tender Audit Event**; return ``audit_event_code``."""
	tc = cstr(tender_code).strip()
	if not tc:
		frappe.throw(_("Tender code is required."), title=_("Audit Append"))

	tm2_name = _resolve_tm2_name(tc)
	if not tm2_name:
		frappe.throw(_("TM2 Tender {0} was not found.").format(tc), title=_("Audit Append"))

	pl = dict(payload or {})
	_validate_section_13_2_payload(event_type=event_type, payload=pl, enforce=enforce_section_13_2)

	pub_snap = cstr(pl.get("publication_snapshot_code") or "").strip()

	at = cstr(actor_type or "").strip() or "User"
	if at not in _ACTOR_TYPE_OPTIONS:
		frappe.throw(_("Invalid audit actor_type: {0}").format(at), title=_("Audit Append"))

	row: dict[str, Any] = {
		"doctype": "TM2 Tender Audit Event",
		"tm2_tender": tm2_name,
		"tender_code": tc,
		"event_type": cstr(event_type).strip(),
		"actor_type": at,
		"actor_user": actor if actor and frappe.db.exists("User", actor) else None,
		"occurred_at": now_datetime(),
		"related_object_type": cstr(related_object_type or "").strip() or None,
		"related_object_id": cstr(related_object_code or "").strip() or None,
		"previous_state": cstr(previous_state or "").strip() or None,
		"new_state": cstr(new_state or "").strip() or None,
		"reason": cstr(reason or "").strip() or None,
		"event_payload": pl,
	}
	if denial_code:
		row["denial_code"] = cstr(denial_code).strip()
	if pub_snap:
		row["publication_snapshot_code"] = pub_snap
	if tm2_audit_row_extras:
		for k, raw in tm2_audit_row_extras.items():
			key = cstr(k).strip()
			if key not in _OPTIONAL_TM2_AUDIT_ROW_KEYS:
				continue
			if raw is None:
				continue
			val = cstr(raw).strip() if not isinstance(raw, (int, float)) else raw
			if val == "":
				continue
			row[key] = val

	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return cstr(doc.audit_event_code or doc.name).strip()


def appendTenderAuditEvent(
	tender_code: str,
	event_type: str,
	actor: str,
	payload: dict[str, Any],
	related_object_type: str | None = None,
	related_object_code: str | None = None,
	previous_state: str | None = None,
	new_state: str | None = None,
	reason: str | None = None,
	*,
	denial_code: str | None = None,
	enforce_section_13_2: bool = True,
	actor_type: str = "User",
	tm2_audit_row_extras: dict[str, Any] | None = None,
) -> str:
	"""CamelCase alias for :func:`append_tender_audit_event`."""
	return append_tender_audit_event(
		tender_code,
		event_type,
		actor,
		payload,
		related_object_type=related_object_type,
		related_object_code=related_object_code,
		previous_state=previous_state,
		new_state=new_state,
		reason=reason,
		denial_code=denial_code,
		enforce_section_13_2=enforce_section_13_2,
		actor_type=actor_type,
		tm2_audit_row_extras=tm2_audit_row_extras,
	)
