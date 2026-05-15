# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §7.6 — TM2 guarded legal service helper + pack phase registry.

Implements the guard pattern from the implementation pack (availability check,
``audit_access_denied`` on deny, structured deny envelope). Public lifecycle
handlers (tracker **P4**–**P7**) should delegate through :func:`guard_tm2_legal_service`
once those services land; this module ships the canonical implementation and a
**spot-check registry** (one representative ``TND2_*`` / pack action per phase).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe

from kentender_procurement.tender_management.security.action_availability.access_denied_audit import (
	audit_access_denied,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.audit.event_catalog import (
	AuditEventCode,
)


@dataclass(frozen=True)
class Tm2PackLegalGuardEntrypoint:
	"""One representative legal surface per tracker phase **P4**–**P7** (spot-check row)."""

	pack_phase: str
	"""High-level phase label: ``P4`` … ``P7``."""

	tracker_scope: str
	"""Human-readable tracker row range (e.g. ``P4-01..P4-08``)."""

	action_code: str
	"""Canonical §7.4 action code evaluated via :func:`get_action_availability`."""

	object_type: str
	"""DocType / logical object type passed to availability (e.g. ``TM2 Tender``)."""

	domain_summary: str
	"""Short description for docs/tests."""


# Spot-check registry: one entrypoint per pack phase P4–P7 (IMPLEMENTATION_TRACKER §P3–§P7).
TM2_PACK_LEGAL_GUARD_ENTRYPOINTS: tuple[Tm2PackLegalGuardEntrypoint, ...] = (
	Tm2PackLegalGuardEntrypoint(
		"P4",
		"P4-01..P4-08",
		"TND2_PUBLISH",
		"TM2 Tender",
		"Core lifecycle (create/bind/readiness/publish/return/cancel)",
	),
	Tm2PackLegalGuardEntrypoint(
		"P5",
		"P5-01..P5-06",
		"ADD2_CREATE",
		"TM2 Tender",
		"Clarification & addendum",
	),
	Tm2PackLegalGuardEntrypoint(
		"P6",
		"P6-01..P6-07",
		"BID2_SUBMIT",
		"TM2 Tender",
		"Supplier access & bid submission",
	),
	Tm2PackLegalGuardEntrypoint(
		"P7",
		"P7-01..P7-04",
		"CLS2_CLOSE_TENDER",
		"TM2 Tender",
		"Closing & downstream handoffs",
	),
)


def _resolve_actor(actor: str | None) -> str:
	explicit = str(actor or "").strip()
	if explicit:
		return explicit
	sess = str(getattr(getattr(frappe, "session", None), "user", None) or "").strip()
	if sess:
		return sess
	return "Administrator"


def guard_tm2_legal_service(
	*,
	action_code: str,
	object_type: str,
	object_code: str,
	actor: str | None = None,
	payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Doc 9 §7.6 guard — evaluate action availability then audit + envelope on deny.

	:param payload: Merged into the availability **context** (``granted_permissions``,
		``security_role_codes``, state hints, etc.).

	:returns: ``{"ok": True, "availability": <§7.3 dict>}`` or a deny dict aligned with
		doc 8 §21.2 (``ok``, ``denial_code``, ``message``, ``blockers``, audit hints).
	"""
	ac = str(action_code or "").strip()
	ot = str(object_type or "").strip()
	oc = str(object_code or "").strip()
	act = _resolve_actor(actor)
	ctx = dict(payload or {})

	availability = get_action_availability(ac, ot, oc, act, context=ctx)
	if availability.get("allowed") is True:
		return {"ok": True, "availability": availability}

	audit_name = audit_access_denied(act, oc, availability, payload=ctx)
	return {
		"ok": False,
		"denial_code": availability.get("denial_code"),
		"message": availability.get("user_message") or availability.get("message") or "",
		"blockers": list(availability.get("blockers") or []),
		"audit_event_code": AuditEventCode.ACTION_AVAILABILITY_DENIED.value,
		"audit_log_name": audit_name,
		"availability": availability,
	}


def guardTm2LegalService(
	*,
	action_code: str,
	object_type: str,
	object_code: str,
	actor: str | None = None,
	payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`guard_tm2_legal_service`."""
	return guard_tm2_legal_service(
		action_code=action_code,
		object_type=object_type,
		object_code=object_code,
		actor=actor,
		payload=payload,
	)
