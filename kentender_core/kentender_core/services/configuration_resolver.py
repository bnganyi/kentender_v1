# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.14 §4.10/§7.2 — ResolveProcurementConfiguration and
ValidateProcurementConfigurationForDecision.

One result shape over every rule a consumer needs, whichever store owns it:
the seven Regulatory Reference kinds (`regulatory_reference.resolve_reference`),
Method eligibility (`Procurement Method Profile`, plan D10) and Procurement
schedules (`Procedure Schedule Profile`). Each call returns an explicit status
from the closed §4.10 set, the exact selected version and its verification,
the typed payload, and a `resolution_hash` over the canonical input and
result. The owning module stores that evidence with its decision and, in its
own decision transaction, calls `validate_procurement_configuration_for_
decision` with the hash it checked: a changed configuration is refused
rather than silently decided on mixed evidence (CFG10-AC-045).

This wraps the existing per-kind resolvers without changing them; their
current callers (Planning, Tenders) move onto it in their own changes
(FOLLOW_UPS FU-21).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import getdate

from kentender_core.services import procurement_settings as settings
from kentender_core.services import regulatory_reference as register
from kentender_core.services.configuration_errors import ConfigurationError, fail_cfg

METHOD_ELIGIBILITY = "Method eligibility"
PROCUREMENT_SCHEDULE = "Procurement schedule"
# The one optional reference: its absence is "Not published", never a
# missing mandatory rule (§5, §8.1).
OPTIONAL_RULES = frozenset({"Market price index"})
RULES = frozenset(register.REFERENCE_KINDS) | {PROCUREMENT_SCHEDULE}

STATUSES = ("Resolved", "Missing", "Ambiguous", "Unverified", "Incomplete", "Unsupported", "Conflict", "MissingBasis", "NotPublished")


def resolve_procurement_configuration(
	*,
	consumer: str,
	action: str,
	rule: str,
	applicability_date: str = "",
	method: str = "",
	category: str = "",
	entity_type: str = "",
	county: bool | None = None,
) -> dict[str, Any]:
	"""The exact configuration `consumer` must use for `action`.

	`applicability_date` is the date the owning module derived from its own
	facts under the rule's declared date basis; this service never
	substitutes today's date or a financial-year start for a missing one
	(§4.10) — no date is `MissingBasis`."""
	consumer = (consumer or "").strip()
	if not consumer or not (action or "").strip():
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Name the consumer and the action this configuration is for.")
	if rule not in RULES:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", f"{rule} is not available in this release.")

	request = {
		"consumer": consumer,
		"action": action,
		"rule": rule,
		"applicability_date": str(getdate(applicability_date)) if applicability_date else "",
		"method": method,
		"category": category,
		"entity_type": entity_type,
		"county": county,
	}
	if not applicability_date:
		return _envelope(request, "MissingBasis", explanation="applicability_date_required")

	if rule == METHOD_ELIGIBILITY:
		result = _method(request)
	elif rule == PROCUREMENT_SCHEDULE:
		result = _schedule(request)
	else:
		result = _reference(request)
	return result


def validate_procurement_configuration_for_decision(*, expected_hash: str, **context: Any) -> dict[str, Any]:
	"""Re-resolve inside the caller's decision transaction and refuse if the
	result is not the one the caller checked, or is not usable."""
	current = resolve_procurement_configuration(**context)
	if not expected_hash or current["resolution_hash"] != expected_hash:
		fail_cfg("CFG_CONFIGURATION_CHANGED")
	return current


# --------------------------------------------------------------------------


def _reference(request: dict[str, Any]) -> dict[str, Any]:
	out = register.resolve_reference(
		reference_kind=request["rule"],
		applicability_date=request["applicability_date"],
		entity_type=request["entity_type"],
		county=request["county"],
		category=request["category"],
	)
	status = out["status"]
	if status == "Missing" and request["rule"] in OPTIONAL_RULES:
		return _envelope(request, "NotPublished", explanation="optional_rule_not_published")
	if status == "Ambiguous":
		return _envelope(request, "Ambiguous", explanation="versions_overlap", candidates=out.get("candidates", []))
	if status in ("Missing", "MissingBasis"):
		return _envelope(request, status, explanation="no_version_covers_date" if status == "Missing" else "applicability_date_required")
	return _envelope(
		request,
		status,
		explanation="" if status == "Resolved" else "sources_not_verified",
		selected={
			"store": register.DOCTYPE,
			"set": out.get("reference_set"),
			"version": out.get("reference"),
			"version_number": out.get("version_number"),
		},
		verification_status=out.get("verification_status"),
		payload=out.get("payload") or {},
	)


def _method(request: dict[str, Any]) -> dict[str, Any]:
	try:
		out = settings.resolve_method_profile(
			procurement_method=request["method"],
			procurement_category=request["category"],
			applicability_date=request["applicability_date"],
		)
	except ConfigurationError:
		_forget_last_message()
		return _envelope(request, "Ambiguous", explanation="versions_overlap")
	return _profile(request, out, settings.METHOD_PROFILE, missing_category="category_not_covered")


def _schedule(request: dict[str, Any]) -> dict[str, Any]:
	try:
		out = settings.resolve_schedule_profile(
			procurement_method=request["method"],
			procurement_category=request["category"],
			applicability_date=request["applicability_date"],
		)
	except ConfigurationError:
		_forget_last_message()
		return _envelope(request, "Ambiguous", explanation="versions_overlap")
	return _profile(request, out, settings.SCHEDULE_PROFILE)


def _profile(request: dict[str, Any], out: dict[str, Any], store: str, missing_category: str = "") -> dict[str, Any]:
	if not out.get("found"):
		return _envelope(request, "Missing", explanation="no_version_covers_date")
	if missing_category and not out.get("category_supported", True):
		return _envelope(request, "Missing", explanation=missing_category)
	verification = out.get("verification_status") or settings.VERIFICATION_PENDING
	status = "Resolved" if verification == settings.VERIFICATION_VERIFIED else "Unverified"
	payload = {k: v for k, v in out.items() if k not in ("found", "applicability_date")}
	return _envelope(
		request,
		status,
		explanation="" if status == "Resolved" else "sources_not_verified",
		selected={
			"store": store,
			"set": out.get("procurement_method"),
			"version": out.get("name") or out.get("profile"),
			"version_number": out.get("version_number"),
		},
		verification_status=verification,
		payload=payload,
	)


def _envelope(
	request: dict[str, Any],
	status: str,
	*,
	explanation: str = "",
	selected: dict[str, Any] | None = None,
	verification_status: str = "",
	payload: dict[str, Any] | None = None,
	candidates: list[str] | None = None,
) -> dict[str, Any]:
	result = {
		"status": status,
		"explanation_code": explanation,
		"rule": request["rule"],
		"applicability": {"date": request["applicability_date"]},
		"selected": selected,
		"verification_status": verification_status,
		"payload": payload or {},
		"candidates": candidates or [],
	}
	canonical = json.dumps({"request": request, "result": result}, sort_keys=True, separators=(",", ":"), default=str)
	result["resolution_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
	return result


def _forget_last_message() -> None:
	"""A resolver's refusal is reported here as a status, so the message
	`frappe.throw` queued for it must not ride back as a pop-up."""
	log = getattr(frappe.local, "message_log", None)
	if log:
		log.pop()
