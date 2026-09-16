# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.6-§4.10, §7 — the regulator reference register.

Each of the seven governed rule kinds (Method eligibility, Reservation
rules, Exclusive preference, Preference margins, Market price index,
Approval applicability, Publication obligations) is a `Regulatory
Reference Set` (a stable key + kind) with immutable, numbered `Regulatory
Reference` versions. Append-only `Reference Verification Event` records
carry source-check evidence; a version's own `verification_status` field
stays a maintained projection of the latest event's outcome, so existing
consumers keep reading it directly rather than joining the event trail.

Method eligibility remains owned by `Procedure Method Profile`
(`kentender_core.services.procurement_settings`) — proven, already
versioned, already read by Planning's method-admissibility check — and is
not duplicated into this envelope (plan D1/D10); it is therefore the one
kind `create_regulatory_reference`/`save_regulatory_reference_version`
still refuse (`CFG_SCHEMA_UNSUPPORTED`) — a future Add-rule screen routes
that kind to the Method Profile functions directly instead. Every other
kind (Reservation rules, Exclusive preference, Preference margins, Market
price index, Approval applicability, Publication obligations) has a typed
`payload_json` validator.

`get_regulatory_reference(fiscal_year)` keeps its exact v0.9 name and return
shape: dependency research (16 Sep 2026) confirmed it is Planning's
`readiness.py` sole read path — the old per-kind `resolve_regulatory_rule`
function had zero production callers and is replaced outright by
`resolve_reference` (the §5 selection algorithm). `threshold_matrix` is now
derived at read time from `Procurement Method Profile`'s in-force
conditions instead of a second, independently-writable copy (closes FU-08).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import flt, getdate

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.configuration_errors import fail_cfg
from kentender_core.services.procurement_settings import (
	METHOD_PROFILE,
	PROCUREMENT_CATEGORIES,
	VERIFICATION_PENDING,
	VERIFICATION_STATUSES,
	VERIFICATION_VERIFIED,
	_code,
	_in_force,
	_next_version,
	_require_verification,
	_supersede_overlapping,
)
from kentender_core.services.reference_data_idempotency import run_idempotent
from kentender_core.services.site_configuration import PE_TYPES, require_configuration_administrator

DOCTYPE = "Regulatory Reference"
SET_DOCTYPE = "Regulatory Reference Set"
EVENT_DOCTYPE = "Reference Verification Event"

# §10.6 — "Rule kind offers exactly seven options."
REFERENCE_KINDS: tuple[str, ...] = (
	"Method eligibility",
	"Reservation rules",
	"Exclusive preference",
	"Preference margins",
	"Market price index",
	"Approval applicability",
	"Publication obligations",
)

APPLICABILITY_BASES: tuple[str, ...] = (
	"FiscalYearStart",
	"PlanSubmissionDate",
	"PlanApprovalDate",
	"ProceedingAuthorizationDate",
	"InvitationDate",
	"ContractSigningDate",
)

COUNTY_APPLICABILITY: tuple[str, ...] = ("All", "County", "NonCounty")

# §4.7 — "Supported comparators are Equal, NotEqual, In, NotIn, LessThan,
# LessThanOrEqual, GreaterThan and GreaterThanOrEqual."
COMPARATORS: tuple[str, ...] = (
	"Equal",
	"NotEqual",
	"In",
	"NotIn",
	"LessThan",
	"LessThanOrEqual",
	"GreaterThan",
	"GreaterThanOrEqual",
)

# §4.7 Publication obligation row.
DUE_RULES: tuple[str, ...] = ("Immediate", "CalendarDaysAfter", "WorkingDaysAfter", "PeriodEndPlusDays")

# REQ-CHG-001 v1.6 §5A / STD-TPL-001 v0.4 §6.1 — unchanged by this remodel; a
# Requisition or Tender screen imports this tuple directly.
TENDER_RENDERABLE_RESERVATION_CATEGORIES: tuple[str, ...] = (
	"None",
	"Youth",
	"Women",
	"Persons with disabilities",
	"Other disadvantaged group",
)


# --------------------------------------------------------------------------
# Reference sets — §7 CreateRegulatoryReference / RenameRegulatoryReference
# --------------------------------------------------------------------------


def create_regulatory_reference(
	*, reference_key: str, reference_kind: str, display_name: str = "", fixture_namespace: str = "", idempotency_key: str = ""
) -> dict[str, Any]:
	"""§7 `CreateRegulatoryReference` — the empty stable set; no legal
	eligibility until a usable version resolves (§7.3 step 1 of 2)."""
	require_configuration_administrator()
	key = " ".join((reference_key or "").split())
	if not key:
		fail_cfg("CFG_PROFILE_INVALID", "Enter a reference key.")
	if reference_kind not in REFERENCE_KINDS:
		fail_cfg("CFG_PROFILE_INVALID", "Select a rule kind.")

	def _do() -> dict[str, Any]:
		doc = frappe.get_doc(
			{
				"doctype": SET_DOCTYPE,
				"reference_key": key,
				"reference_kind": reference_kind,
				"display_name": (display_name or key).strip(),
				"fixture_namespace": fixture_namespace,
			}
		)
		doc.insert(ignore_permissions=True)
		log_audit_event(
			event_type="site_configuration",
			document_type=SET_DOCTYPE,
			document_name=doc.name,
			action="create_regulatory_reference",
			metadata={"reference_key": key, "reference_kind": reference_kind},
		)
		return {"reference_set": doc.name, "reference_key": key, "reference_kind": reference_kind, "created": True}

	return run_idempotent(idempotency_key, SET_DOCTYPE, _code(key), "create_regulatory_reference", _do)


def rename_regulatory_reference(*, reference_set: str, display_name: str, expected_version: str = "") -> dict[str, Any]:
	"""§7 `RenameRegulatoryReference` — audits the display name only; key,
	kind and frozen consumer names remain unchanged."""
	require_configuration_administrator()
	if not frappe.db.exists(SET_DOCTYPE, reference_set):
		fail_cfg("CFG_PROFILE_INVALID", "That reference does not exist.")
	doc = frappe.get_doc(SET_DOCTYPE, reference_set)
	if expected_version and str(doc.modified) != str(expected_version):
		fail_cfg("CFG_VERSION_CONFLICT")
	before = doc.display_name
	doc.display_name = " ".join((display_name or "").split()) or doc.display_name
	doc.save(ignore_permissions=True)
	log_audit_event(
		event_type="site_configuration",
		document_type=SET_DOCTYPE,
		document_name=doc.name,
		action="rename_regulatory_reference",
		metadata={"before": before, "after": doc.display_name},
	)
	return {"reference_set": doc.name, "display_name": doc.display_name, "expected_version": str(doc.modified)}


def get_reference_set(name: str) -> dict[str, Any]:
	if not frappe.db.exists(SET_DOCTYPE, name):
		fail_cfg("CFG_PROFILE_INVALID", "That reference does not exist.")
	doc = frappe.get_cached_doc(SET_DOCTYPE, name)
	versions = list_regulatory_reference_versions(reference_set=name)
	return {
		"reference_set": doc.name,
		"reference_key": doc.reference_key,
		"reference_kind": doc.reference_kind,
		"display_name": doc.display_name,
		"versions": versions,
		"latest": versions[0] if versions else None,
		"expected_version": str(doc.modified),
	}


def list_reference_sets(reference_kind: str = "") -> list[dict[str, Any]]:
	filters = {"reference_kind": reference_kind} if reference_kind else {}
	names = frappe.get_all(SET_DOCTYPE, filters=filters, pluck="name", order_by="display_name asc")
	out = []
	for name in names:
		doc = frappe.get_cached_doc(SET_DOCTYPE, name)
		active = frappe.get_all(
			DOCTYPE,
			filters={"reference_set": name, "status": "Active"},
			fields=["name", "version_number", "verification_status", "effective_from", "effective_until"],
			order_by="effective_from desc, version_number desc",
			limit_page_length=0,
		)
		# The version a reader means by "the current rule" is the one in force
		# today — not merely the highest-numbered Active row. A set can carry
		# several non-overlapping Active versions for different periods (a
		# future-dated one, or another module's far-future test period), and
		# ordering by version number alone reported that one as current.
		today = getdate()
		current = next(
			(
				row
				for row in active
				if getdate(row["effective_from"]) <= today
				and (not row["effective_until"] or getdate(row["effective_until"]) >= today)
			),
			None,
		)
		# Nothing covers today: show the next period that starts, else the
		# most recent that ended — never nothing while versions exist.
		if current is None and active:
			upcoming = [row for row in active if getdate(row["effective_from"]) > today]
			current = upcoming[-1] if upcoming else active[0]
		out.append(
			{
				"reference_set": doc.name,
				"reference_key": doc.reference_key,
				"reference_kind": doc.reference_kind,
				"display_name": doc.display_name,
				"has_version": bool(active),
				"version": current,
			}
		)
	return out


def list_regulatory_reference_versions(reference_set: str) -> list[dict[str, Any]]:
	names = frappe.get_all(
		DOCTYPE, filters={"reference_set": reference_set}, pluck="name", order_by="version_number desc"
	)
	return [_projection(n) for n in names]


# --------------------------------------------------------------------------
# Typed payloads (§4.7) — Reservation rules and Market price index now;
# the remaining five kinds are explicit Phase 2c work, not silently accepted.
# --------------------------------------------------------------------------


def _validate_reservation_rules_payload(payload: dict[str, Any]) -> dict[str, Any]:
	obligation_code = (payload.get("obligation_code") or "").strip()
	if not obligation_code:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Enter the obligation code.")
	target = payload.get("target_percent")
	if target not in (None, ""):
		target = flt(target)
		if not (0 <= target <= 100):
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "The reservation target must be between 0 and 100.")
	else:
		target = None
	county_target = payload.get("county_target_percent")
	if county_target not in (None, ""):
		county_target = flt(county_target)
		if not (0 <= county_target <= 100):
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "The county target must be between 0 and 100.")
	else:
		county_target = None
	denominator_basis = payload.get("denominator_basis") or ""
	if denominator_basis and denominator_basis not in ("AnnualProcurementBudget", "AnnualProcurementValue"):
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported denominator basis.")
	overlap_policy = payload.get("overlap_policy") or "Independent"
	if overlap_policy not in ("Independent", "MutuallyExclusive", "SpecifiedOverlap"):
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported overlap policy.")
	categories = []
	for row in payload.get("categories") or []:
		category = (row.get("category") or "").strip()
		if not category:
			continue
		categories.append(
			{
				"category": category,
				"advantage_rank": int(row.get("advantage_rank") or 0),
				"is_regional": bool(row.get("is_regional")),
				"statutory_reference": (row.get("statutory_reference") or "").strip(),
			}
		)
	return {
		"obligation_code": obligation_code,
		"target_percent": target,
		"county_target_percent": county_target,
		"denominator_basis": denominator_basis,
		"eligible_designations": [str(d).strip() for d in (payload.get("eligible_designations") or []) if str(d).strip()],
		"overlap_policy": overlap_policy,
		"related_obligation_codes": [str(c).strip() for c in (payload.get("related_obligation_codes") or []) if str(c).strip()],
		"categories": categories,
	}


def _validate_market_price_index_payload(payload: dict[str, Any]) -> dict[str, Any]:
	rows = []
	for row in payload.get("rows") or []:
		category = row.get("category") or ""
		if category and category not in PROCUREMENT_CATEGORIES:
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select goods, works or services for each price row.")
		item = (row.get("item") or "").strip()
		if not item:
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Each price row needs an item.")
		rows.append(
			{
				"item": item,
				"category": category,
				"unit": (row.get("unit") or "").strip(),
				"currency": (row.get("currency") or "KES").strip(),
				"price": flt(row.get("price")),
				"observation_date": str(row.get("observation_date") or ""),
				"publication_date": str(row.get("publication_date") or ""),
				"publication_reference": (row.get("publication_reference") or "").strip(),
			}
		)
	return {"published": bool(rows), "rows": rows}


def _validate_exclusive_preference_payload(payload: dict[str, Any]) -> dict[str, Any]:
	restriction_code = (payload.get("restriction_code") or "").strip()
	if not restriction_code:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Enter the restriction code.")
	category = payload.get("category") or ""
	if category and category not in PROCUREMENT_CATEGORIES:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select goods, works or services.")
	comparator = payload.get("comparator") or ""
	if comparator and comparator not in COMPARATORS:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported comparison.")
	amount = payload.get("amount")
	amount = flt(amount) if amount not in (None, "") else None
	return {
		"restriction_code": restriction_code,
		"category": category,
		"method": (payload.get("method") or "").strip(),
		"currency": (payload.get("currency") or "KES").strip(),
		"comparator": comparator,
		"amount": amount,
		"funding_origin_condition": (payload.get("funding_origin_condition") or "").strip(),
		"local_origin_condition": (payload.get("local_origin_condition") or "").strip(),
		"eligible_party_classification": (payload.get("eligible_party_classification") or "").strip(),
		"source_reference": (payload.get("source_reference") or "").strip(),
	}


def _validate_preference_margins_payload(payload: dict[str, Any]) -> dict[str, Any]:
	scheme_code = (payload.get("scheme_code") or "").strip()
	if not scheme_code:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Enter the scheme code.")
	margin = payload.get("margin_percent")
	if margin not in (None, ""):
		margin = flt(margin)
		if not (0 <= margin <= 100):
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "The margin must be between 0 and 100.")
	else:
		margin = None
	shareholding_from = payload.get("shareholding_from")
	shareholding_to = payload.get("shareholding_to")
	shareholding_from = flt(shareholding_from) if shareholding_from not in (None, "") else None
	shareholding_to = flt(shareholding_to) if shareholding_to not in (None, "") else None
	if shareholding_from is not None and shareholding_to is not None and shareholding_from > shareholding_to:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "The shareholding range is inverted.")
	return {
		"scheme_code": scheme_code,
		"procedure": (payload.get("procedure") or "").strip(),
		"margin_percent": margin,
		"origin_condition": (payload.get("origin_condition") or "").strip(),
		"shareholding_from": shareholding_from,
		"shareholding_to": shareholding_to,
		"shareholding_from_included": bool(payload.get("shareholding_from_included", True)),
		"shareholding_to_included": bool(payload.get("shareholding_to_included", True)),
		"evaluation_basis": (payload.get("evaluation_basis") or "").strip(),
		"source_reference": (payload.get("source_reference") or "").strip(),
	}


def _validate_approval_applicability_payload(payload: dict[str, Any]) -> dict[str, Any]:
	from kentender_core.services.site_configuration import STATUTORY_APPROVAL_ROUTES

	entity_types = [e for e in (payload.get("entity_types") or []) if e]
	for entity_type in entity_types:
		if entity_type not in PE_TYPES:
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", f"Unknown entity type: {entity_type}.")
	county_applicability = payload.get("county_applicability") or "All"
	if county_applicability not in COUNTY_APPLICABILITY:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select the county applicability.")
	approval_route = payload.get("approval_route") or ""
	if approval_route and approval_route not in STATUTORY_APPROVAL_ROUTES:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported approval route.")
	return {
		"entity_types": entity_types,
		"county_applicability": county_applicability,
		"required_entity_evidence": (payload.get("required_entity_evidence") or "").strip(),
		"approval_route": approval_route,
		"required_capacity_code": (payload.get("required_capacity_code") or "").strip(),
		"source_reference": (payload.get("source_reference") or "").strip(),
	}


def _validate_publication_obligations_payload(payload: dict[str, Any]) -> dict[str, Any]:
	obligation_id = (payload.get("obligation_id") or "").strip()
	if not obligation_id:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Enter the obligation ID.")
	due_rule = payload.get("due_rule") or ""
	if due_rule and due_rule not in DUE_RULES:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported due rule.")
	days = payload.get("days")
	if days not in (None, ""):
		days = int(days)
		if days < 0:
			fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Days must not be negative.")
	else:
		days = None
	if due_rule in ("CalendarDaysAfter", "WorkingDaysAfter") and days is None:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Enter the number of days for this due rule.")
	return {
		"obligation_id": obligation_id,
		"accountable_actor_role": (payload.get("accountable_actor_role") or "").strip(),
		"recipient": (payload.get("recipient") or "").strip(),
		"channel": (payload.get("channel") or "").strip(),
		"trigger_event": (payload.get("trigger_event") or "").strip(),
		"due_rule": due_rule,
		"days": days,
		"reporting_period": (payload.get("reporting_period") or "").strip(),
		"integration_evidence_contract_code": (payload.get("integration_evidence_contract_code") or "").strip(),
		"source_reference": (payload.get("source_reference") or "").strip(),
	}


_PAYLOAD_VALIDATORS: dict[str, Any] = {
	"Reservation rules": _validate_reservation_rules_payload,
	"Market price index": _validate_market_price_index_payload,
	"Exclusive preference": _validate_exclusive_preference_payload,
	"Preference margins": _validate_preference_margins_payload,
	"Approval applicability": _validate_approval_applicability_payload,
	"Publication obligations": _validate_publication_obligations_payload,
}


def _validate_payload(reference_kind: str, payload: dict[str, Any] | None) -> dict[str, Any]:
	validator = _PAYLOAD_VALIDATORS.get(reference_kind)
	if validator is None:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", f"{reference_kind} is not available in this release.")
	return validator(payload or {})


# --------------------------------------------------------------------------
# Versions — §7 SaveRegulatoryReferenceVersion
# --------------------------------------------------------------------------


def save_regulatory_reference_version(
	*,
	reference_set: str,
	payload: dict[str, Any],
	effective_from: str,
	effective_until: str = "",
	applicability_basis: str = "",
	applicability_entity_types: list[str] | None = None,
	applicability_county: str = "All",
	applicability_categories: list[str] | None = None,
	applicability_currency: str = "KES",
	source_instrument: str = "",
	provision: str = "",
	source_document: str = "",
	interpretation: str = "",
	supersedes_version_ids: list[str] | None = None,
	change_reason: str = "",
	verification_status: str = VERIFICATION_PENDING,
	fixture_namespace: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""§7 `SaveRegulatoryReferenceVersion` — a new immutable numbered version
	after schema/overlap/supersession checks. Defaults to Pending like every
	sibling version record (Method/Schedule Profile, Calendar); real
	production source checks additionally go through
	`record_reference_verification`'s append-only event trail (§5), which
	also updates this same field — both paths are legitimate, matching the
	existing direct-field convention every other governed record already
	uses for fixtures and tests."""
	require_configuration_administrator()
	if not frappe.db.exists(SET_DOCTYPE, reference_set):
		fail_cfg("CFG_PROFILE_INVALID", "That reference does not exist.")
	set_doc = frappe.get_cached_doc(SET_DOCTYPE, reference_set)
	verification = _require_verification(verification_status)
	if applicability_basis and applicability_basis not in APPLICABILITY_BASES:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", "Select a supported date basis.")
	if applicability_county not in COUNTY_APPLICABILITY:
		fail_cfg("CFG_PROFILE_INVALID", "Select the county applicability.")
	entity_types = [e for e in (applicability_entity_types or []) if e]
	for entity_type in entity_types:
		if entity_type not in PE_TYPES:
			fail_cfg("CFG_PROFILE_INVALID", f"Unknown entity type: {entity_type}.")
	categories = [c for c in (applicability_categories or []) if c]
	for category in categories:
		if category not in PROCUREMENT_CATEGORIES:
			fail_cfg("CFG_PROFILE_INVALID", "Select goods, works or services.")
	validated_payload = _validate_payload(set_doc.reference_kind, payload)
	supersedes = [s for s in (supersedes_version_ids or []) if s]
	for s in supersedes:
		if not frappe.db.exists(DOCTYPE, {"name": s, "reference_set": reference_set}):
			fail_cfg("CFG_SUPERSESSION_INVALID")

	def _do() -> dict[str, Any]:
		version = _next_version(DOCTYPE, {"reference_set": reference_set})
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE,
				"reference_set": reference_set,
				"reference_key": set_doc.reference_key,
				"reference_kind": set_doc.reference_kind,
				"version_number": version,
				"status": "Active",
				"effective_from": getdate(effective_from),
				"effective_until": getdate(effective_until) if effective_until else None,
				"applicability_basis": applicability_basis,
				"applicability_entity_types": ",".join(entity_types),
				"applicability_county": applicability_county,
				"applicability_categories": ",".join(categories),
				"applicability_currency": applicability_currency or "KES",
				"verification_status": verification,
				"source_instrument": source_instrument,
				"provision": provision,
				"source_document": source_document,
				"interpretation": interpretation,
				"supersedes_version_ids": ",".join(supersedes),
				"change_reason": change_reason,
				"payload_schema_version": "1",
				"payload_json": json.dumps(validated_payload),
				"fixture_namespace": fixture_namespace,
			}
		)
		doc.insert(ignore_permissions=True)
		superseded = _supersede_overlapping(
			DOCTYPE, {"reference_set": reference_set}, doc.effective_from, doc.effective_until, doc.name
		)
		log_audit_event(
			event_type="site_configuration",
			document_type=DOCTYPE,
			document_name=doc.name,
			action="save_regulatory_reference_version",
			metadata={"version": version, "superseded": superseded, "reference_kind": set_doc.reference_kind},
		)
		return {
			"reference": doc.name,
			"reference_set": reference_set,
			"version_number": version,
			"superseded": superseded,
			"created": True,
		}

	return run_idempotent(idempotency_key, DOCTYPE, reference_set, "save_regulatory_reference_version", _do)


def _projection(name: str) -> dict[str, Any]:
	"""The full read for one named (possibly superseded) version — the only
	caller of the complete typed payload, behind `get_regulatory_reference_version`."""
	doc = frappe.get_cached_doc(DOCTYPE, name)
	return {
		"reference": doc.name,
		"reference_set": doc.reference_set,
		"reference_key": doc.reference_key,
		"reference_kind": doc.reference_kind,
		"version_number": int(doc.version_number),
		"status": doc.status,
		"effective_from": str(doc.effective_from or ""),
		"effective_until": str(doc.effective_until or ""),
		"applicability_basis": doc.applicability_basis or "",
		"applicability_entity_types": [t for t in (doc.applicability_entity_types or "").split(",") if t],
		"applicability_county": doc.applicability_county or "All",
		"applicability_categories": [c for c in (doc.applicability_categories or "").split(",") if c],
		"applicability_currency": doc.applicability_currency or "KES",
		"verification_status": doc.verification_status or VERIFICATION_PENDING,
		"source_instrument": doc.source_instrument or "",
		"provision": doc.provision or "",
		"source_document": doc.source_document or "",
		"interpretation": doc.interpretation or "",
		"supersedes_version_ids": [s for s in (doc.supersedes_version_ids or "").split(",") if s],
		"change_reason": doc.change_reason or "",
		"payload": json.loads(doc.payload_json or "{}"),
		"expected_version": str(doc.modified),
	}


def get_regulatory_reference_version(name: str) -> dict[str, Any]:
	if not frappe.db.exists(DOCTYPE, name):
		fail_cfg("CFG_PROFILE_INVALID", "That reference version does not exist.")
	return _projection(name)


# --------------------------------------------------------------------------
# Verification — §7 RecordReferenceVerification
# --------------------------------------------------------------------------

_VERIFICATION_TARGETS: tuple[str, ...] = (DOCTYPE, "Business Day Calendar")


def _hash_document(source_document: str) -> str:
	if not source_document:
		return ""
	return hashlib.sha256(source_document.encode("utf-8")).hexdigest()


def record_reference_verification(
	*,
	target_doctype: str,
	target_name: str,
	outcome: str,
	source_check_date: str = "",
	instrument_edition: str = "",
	provisions: str = "",
	source_document: str = "",
	effective_dates_and_amendments: str = "",
	applicability_date_basis_explanation: str = "",
	interpretation_evidence: str = "",
	unresolved_points: str = "",
	change_reason: str = "",
	expected_prior_event: str = "",
	fixture_namespace: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""§7 `RecordReferenceVerification` — append verified/pending/rejected
	evidence for the exact immutable version; never mutates the legal
	payload. Verified requires complete evidence (§5); Pending/Rejected
	record the missing or contradictory point."""
	require_configuration_administrator()
	if target_doctype not in _VERIFICATION_TARGETS:
		fail_cfg("CFG_PROFILE_INVALID", "Unknown verification target type.")
	if not frappe.db.exists(target_doctype, target_name):
		fail_cfg("CFG_PROFILE_INVALID", "That version does not exist.")
	if outcome not in ("Pending", "Verified", "Rejected"):
		fail_cfg("CFG_PROFILE_INVALID", "Select a verification outcome.")
	latest = frappe.get_all(
		EVENT_DOCTYPE,
		filters={"target_doctype": target_doctype, "target_name": target_name},
		fields=["name"],
		order_by="creation desc",
		limit_page_length=1,
	)
	current_prior = latest[0]["name"] if latest else ""
	if expected_prior_event and expected_prior_event != current_prior:
		fail_cfg("CFG_VERSION_CONFLICT")
	if outcome == "Verified":
		missing = [
			label
			for label, value in (
				("instrument and edition", instrument_edition),
				("effective dates and amendments", effective_dates_and_amendments),
				("applicability and date basis", applicability_date_basis_explanation),
				("interpretation evidence", interpretation_evidence),
			)
			if not (value or "").strip()
		]
		if missing:
			fail_cfg("CFG_VERIFICATION_EVIDENCE_REQUIRED")
	elif not (unresolved_points or "").strip():
		fail_cfg("CFG_VERIFICATION_EVIDENCE_REQUIRED", "Record the missing or contradictory point for this outcome.")

	def _do() -> dict[str, Any]:
		event = frappe.get_doc(
			{
				"doctype": EVENT_DOCTYPE,
				"target_doctype": target_doctype,
				"target_name": target_name,
				"outcome": outcome,
				"reviewer": frappe.session.user,
				"source_check_date": getdate(source_check_date) if source_check_date else None,
				"instrument_edition": instrument_edition,
				"provisions": provisions,
				"source_document": source_document,
				"source_document_hash": _hash_document(source_document),
				"effective_dates_and_amendments": effective_dates_and_amendments,
				"applicability_date_basis_explanation": applicability_date_basis_explanation,
				"interpretation_evidence": interpretation_evidence,
				"unresolved_points": unresolved_points,
				"change_reason": change_reason,
				"previous_event": current_prior,
				"fixture_namespace": fixture_namespace,
			}
		)
		event.insert(ignore_permissions=True)
		# Pending and Rejected both leave the target's fast-read gate at
		# "not verified" — the distinction between them is a detail/history
		# fact surfaced from the event trail, not a fourth gate value (the
		# 3-value vocabulary is a must-preserve contract for Planning's
		# `reservation_allocations()`).
		target = frappe.get_doc(target_doctype, target_name)
		target.flags.kt_verify = True
		target.verification_status = VERIFICATION_VERIFIED if outcome == "Verified" else VERIFICATION_PENDING
		target.save(ignore_permissions=True)
		log_audit_event(
			event_type="site_configuration",
			document_type=target_doctype,
			document_name=target_name,
			action="record_reference_verification",
			metadata={"outcome": outcome, "event": event.name},
		)
		return {"event": event.name, "target": target_name, "outcome": outcome, "verification_status": target.verification_status}

	return run_idempotent(
		idempotency_key, EVENT_DOCTYPE, f"{target_doctype}:{target_name}", "record_reference_verification", _do
	)


def list_verification_history(target_doctype: str, target_name: str) -> list[dict[str, Any]]:
	names = frappe.get_all(
		EVENT_DOCTYPE,
		filters={"target_doctype": target_doctype, "target_name": target_name},
		pluck="name",
		order_by="creation desc",
	)
	out = []
	for name in names:
		doc = frappe.get_cached_doc(EVENT_DOCTYPE, name)
		out.append(
			{
				"event": doc.name,
				"outcome": doc.outcome,
				"reviewer": doc.reviewer,
				"recorded_at": str(doc.creation),
				"source_check_date": str(doc.source_check_date or ""),
				"unresolved_points": doc.unresolved_points or "",
				"change_reason": doc.change_reason or "",
			}
		)
	return out


# --------------------------------------------------------------------------
# Selection — §5, replacing the unused `resolve_regulatory_rule`
# --------------------------------------------------------------------------


def resolve_reference(
	*,
	reference_kind: str,
	applicability_date: str,
	entity_type: str = "",
	county: bool | None = None,
	category: str = "",
) -> dict[str, Any]:
	"""§5 selection algorithm for one rule kind: exactly one matching,
	Verified candidate is required for production use; a gap, an ambiguity
	and an unverified match are each explicit, never silently resolved by
	recency or version number."""
	if reference_kind not in REFERENCE_KINDS:
		fail_cfg("CFG_SCHEMA_UNSUPPORTED", f"{reference_kind} is not available in this release.")
	if not applicability_date:
		return {"status": "MissingBasis", "reference_kind": reference_kind}
	date = getdate(applicability_date)
	sets = frappe.get_all(SET_DOCTYPE, filters={"reference_kind": reference_kind}, pluck="name")
	candidates = []
	for set_name in sets:
		for row in _in_force(DOCTYPE, {"reference_set": set_name}, date):
			doc = frappe.get_cached_doc(DOCTYPE, row["name"])
			types = [t for t in (doc.applicability_entity_types or "").split(",") if t]
			if entity_type and types and entity_type not in types:
				continue
			if county is not None and doc.applicability_county != "All":
				if bool(county) != (doc.applicability_county == "County"):
					continue
			cats = [c for c in (doc.applicability_categories or "").split(",") if c]
			if category and cats and category not in cats:
				continue
			candidates.append(doc)
	if not candidates:
		return {"status": "Missing", "reference_kind": reference_kind, "applicability_date": str(date)}
	if len(candidates) > 1:
		return {
			"status": "Ambiguous",
			"reference_kind": reference_kind,
			"applicability_date": str(date),
			"candidates": [c.name for c in candidates],
		}
	doc = candidates[0]
	payload = json.loads(doc.payload_json or "{}")
	result = {
		"reference_kind": reference_kind,
		"reference": doc.name,
		"reference_set": doc.reference_set,
		"version_number": int(doc.version_number),
		"verification_status": doc.verification_status,
		"applicability_date": str(date),
		"payload": payload,
	}
	if doc.verification_status != VERIFICATION_VERIFIED:
		return {**result, "status": "Unverified"}
	return {**result, "status": "Resolved"}


# --------------------------------------------------------------------------
# Planning's compatibility read (unchanged name/shape) — §4.10/CFG10-AC-033
# --------------------------------------------------------------------------


def _empty(fiscal_year: str) -> dict[str, Any]:
	return {
		"fiscal_year": fiscal_year,
		"available": False,
		"reference": "",
		"effective_from": "",
		"gazette_reference": "",
		"verification_status": "",
		"applicability_basis": "",
		"source_instrument": "",
		"provision": "",
		"source_document": "",
		"threshold_matrix": [],
		"reservation": {"published": False, "target_percent": None, "county_target_percent": None, "categories": []},
		"exclusive_preference": {"published": False, "works_amount": None, "goods_services_amount": None},
		"market_price_index": {"published": False, "rows": []},
		"schedule_buffers": [],
	}


def _threshold_matrix_from_method_profiles(applicability_date) -> list[dict[str, Any]]:
	"""D10 — derived from `Procurement Method Profile`'s own in-force
	conditions instead of a second, independently-writable copy (FU-08)."""
	rows: list[dict[str, Any]] = []
	for name in frappe.get_all(METHOD_PROFILE, filters={"status": "Active"}, pluck="name"):
		doc = frappe.get_cached_doc(METHOD_PROFILE, name)
		start = getdate(doc.effective_from) if doc.effective_from else None
		end = getdate(doc.effective_until) if doc.effective_until else None
		if not start or start > applicability_date or (end and end < applicability_date):
			continue
		for condition in doc.conditions or []:
			if not condition.maximum_amount:
				continue
			rows.append(
				{
					"procurement_category": condition.procurement_category,
					"procurement_method": doc.procurement_method,
					"max_amount": flt(condition.maximum_amount),
					"basis": condition.cumulative_basis or "",
					"statutory_reference": condition.statutory_reference or "",
				}
			)
	return rows


def get_regulatory_reference(fiscal_year: str) -> dict[str, Any]:
	"""The register in force for `fiscal_year`, as one read-only projection —
	unchanged name and shape (Planning's `readiness.py` sole read path).

	Resolves the Reservation-rules and Market-price-index kinds at the
	Fiscal Year's start date (`FiscalYearStart` basis); `threshold_matrix`
	comes from Method Profile (D10). A year with no version in any kind
	returns `available = False` with every section unpublished, never a
	silent fallback.
	"""
	fiscal_year = (fiscal_year or "").strip()
	if not fiscal_year:
		return _empty(fiscal_year)
	row = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	if not row:
		return _empty(fiscal_year)
	date = getdate(row)
	reservation_doc = _single_in_force("Reservation rules", date)
	out = _empty(fiscal_year)
	out["threshold_matrix"] = _threshold_matrix_from_method_profiles(date)
	if reservation_doc:
		payload = json.loads(reservation_doc.payload_json or "{}")
		categories = sorted(payload.get("categories") or [], key=lambda r: (r.get("advantage_rank") or 0, r.get("category") or ""))
		out.update(
			{
				"available": True,
				"reference": reservation_doc.name,
				"effective_from": str(reservation_doc.effective_from or ""),
				"gazette_reference": reservation_doc.source_instrument or "",
				"verification_status": reservation_doc.verification_status or VERIFICATION_PENDING,
				"applicability_basis": reservation_doc.applicability_basis or "",
				"source_instrument": reservation_doc.source_instrument or "",
				"provision": reservation_doc.provision or "",
				"source_document": reservation_doc.source_document or "",
				"reservation": {
					"published": bool(categories) and payload.get("target_percent") is not None,
					"target_percent": payload.get("target_percent"),
					"county_target_percent": payload.get("county_target_percent"),
					"categories": categories,
				},
			}
		)
	market_doc = _single_in_force("Market price index", date)
	if market_doc:
		payload = json.loads(market_doc.payload_json or "{}")
		out["market_price_index"] = {
			"published": bool(payload.get("published")),
			"rows": [
				{
					"procurement_category": r.get("category", ""),
					"item": r.get("item", ""),
					"unit": r.get("unit", ""),
					"indicative_price": flt(r.get("price")),
				}
				for r in payload.get("rows") or []
			],
		}
	return out


def _single_in_force(reference_kind: str, date):
	"""The one in-force version of `reference_kind` across every set of that
	kind, if unambiguous — the simple compatibility case Planning's read
	needs; `resolve_reference` is the strict, filtered §5 algorithm."""
	sets = frappe.get_all(SET_DOCTYPE, filters={"reference_kind": reference_kind}, pluck="name")
	candidates = []
	for set_name in sets:
		for row in _in_force(DOCTYPE, {"reference_set": set_name}, date):
			candidates.append(row["name"])
	if len(candidates) != 1:
		return None
	return frappe.get_cached_doc(DOCTYPE, candidates[0])


# --------------------------------------------------------------------------
# Fixture cleanup
# --------------------------------------------------------------------------


def purge_fixture_references(fixture_namespace: str) -> int:
	"""Test/fixture cleanup only — production versions are never deleted.

	Order matters: a `Reference Verification Event` Dynamic-Links to its
	target, so events must go first or the target's delete is refused
	(`LinkExistsError`); sets go last for the same reason relative to
	versions.
	"""
	count = 0
	for name in frappe.get_all(EVENT_DOCTYPE, filters={"fixture_namespace": fixture_namespace}, pluck="name"):
		doc = frappe.get_doc(EVENT_DOCTYPE, name)
		doc.flags.kt_fixture_purge = True
		doc.delete(ignore_permissions=True)
		count += 1
	for name in frappe.get_all(DOCTYPE, filters={"fixture_namespace": fixture_namespace}, pluck="name"):
		doc = frappe.get_doc(DOCTYPE, name)
		doc.flags.kt_fixture_purge = True
		doc.delete(ignore_permissions=True)
		count += 1
	for name in frappe.get_all(SET_DOCTYPE, filters={"fixture_namespace": fixture_namespace}, pluck="name"):
		doc = frappe.get_doc(SET_DOCTYPE, name)
		doc.flags.kt_fixture_purge = True
		doc.delete(ignore_permissions=True)
		count += 1
	return count
