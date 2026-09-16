# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1, §5.5.3, §10.11 (C03/C04), §11.6 and §17.2 —
the Procurement settings Configuration & Governance maintains and every
module reads only through this service:

- the governed **funding-source catalogue** (CFG v0.9 §4.4);
- versioned, effective-dated **method eligibility profiles**;
- versioned, effective-dated **procedure schedule profiles**;
- the operational **approaching-milestone reminder threshold**.

Rules: Administrator / System Manager maintain them under the existing
configuration authority with no approval workflow (CFG-BR-012); a referenced
Version is immutable — an edit is a new Version and the earlier one is
retained; resolvers select the exact Version in force for the legally
applicable date and fail closed on ambiguity (`CFG_RULE_UNRESOLVED`); nothing
here decides what blocks a Plan — Planning does, from the `complete` and
`verification_status` facts returned.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, getdate, now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_core.services.configuration_errors import fail_cfg
from kentender_core.services.reference_data_idempotency import run_idempotent
from kentender_core.services.site_configuration import PE_TYPES, require_configuration_administrator

FUNDING_SOURCE = "Funding Source"
METHOD_PROFILE = "Procurement Method Profile"
SCHEDULE_PROFILE = "Procedure Schedule Profile"
SETTINGS = "Procurement Settings"
CALENDAR = "Business Day Calendar"

VERIFICATION_PENDING = "Production verification pending"
VERIFICATION_FIXTURE = "Fixture-verified — not production law"
VERIFICATION_VERIFIED = "Verified"
VERIFICATION_STATUSES: tuple[str, ...] = (VERIFICATION_PENDING, VERIFICATION_FIXTURE, VERIFICATION_VERIFIED)

PROCUREMENT_CATEGORIES: tuple[str, ...] = ("Goods", "Works", "Services")
COUNTING_RULES: tuple[str, ...] = ("Calendar days", "Working days")
CONDITION_KINDS: tuple[str, ...] = ("Known fact", "Declaration")
MILESTONE_BASES: tuple[str, ...] = ("Statutory", "Planning assumption", "Source-derived")

# §10.1 — the seven Third Schedule milestones in order; the first is the
# invitation anchor, the last derives from the item's estimated delivery
# period; the five between carry the profile periods.
MILESTONES: tuple[str, ...] = (
	"invitation",
	"bid_opening",
	"evaluation_completion",
	"award_approval",
	"award_notification",
	"contract_signing",
	"delivery_completion",
)
MILESTONE_LABELS: dict[str, str] = {
	"invitation": "Invitation or advertisement",
	"bid_opening": "Bid opening",
	"evaluation_completion": "Evaluation completion",
	"award_approval": "Tender award approval",
	"award_notification": "Notification of award",
	"contract_signing": "Contract signing",
	"delivery_completion": "Delivery or implementation completion",
}
# The period each milestone closes (the input a Planner adjusts).
PERIOD_BY_MILESTONE: dict[str, str] = {
	"bid_opening": "tendering_period_days",
	"evaluation_completion": "evaluation_period_days",
	"award_approval": "award_approval_buffer_days",
	"award_notification": "notification_buffer_days",
	"contract_signing": "standstill_period_days",
}

DEFAULT_REMINDER_THRESHOLD_DAYS = 7


# --------------------------------------------------------------------------
# Funding sources (CFG v0.9 §4.4; C03)
# --------------------------------------------------------------------------


def _funding_source_referenced(name: str) -> bool:
	"""A Budget line version (BUD-CHG-001) is the one governed consumer."""
	for doctype in ("Procurement Budget Line Version", "Procurement Budget Line"):
		if frappe.db.exists("DocType", doctype) and frappe.db.has_column(doctype, "funding_source"):
			if frappe.db.exists(doctype, {"funding_source": name}):
				return True
	return False


def list_funding_sources() -> list[dict[str, Any]]:
	rows = frappe.get_all(FUNDING_SOURCE, fields=["name", "label", "record_status", "modified"], order_by="label asc")
	return [
		{
			"name": r["name"],
			"label": r["label"],
			"enabled": r["record_status"] == "Available",
			"record_status": r["record_status"],
			"referenced": _funding_source_referenced(r["name"]),
			"expected_version": str(r["modified"]),
		}
		for r in rows
	]


def add_funding_source(*, label: str, idempotency_key: str = "") -> dict[str, Any]:
	require_configuration_administrator()
	label = " ".join((label or "").split())

	def _do() -> dict[str, Any]:
		if not (2 <= len(label) <= 100):
			fail_cfg("CFG_PROFILE_INVALID", "Enter a funding source name of 2–100 characters.")
		if frappe.db.exists(FUNDING_SOURCE, label):
			return {"name": label, "created": False}
		doc = frappe.get_doc({"doctype": FUNDING_SOURCE, "label": label, "record_status": "Available", "created_by_actor": frappe.session.user, "created_at": now_datetime()})
		doc.insert(ignore_permissions=True)
		log_audit_event(event_type="site_configuration", document_type=FUNDING_SOURCE, document_name=doc.name, action="add_funding_source", metadata={"label": label})
		return {"name": doc.name, "created": True}

	return run_idempotent(idempotency_key, FUNDING_SOURCE, label, "add_funding_source", _do)


def update_funding_source(*, name: str, label: str = "", enabled: bool | None = None, expected_version: str = "") -> dict[str, Any]:
	"""Enable/disable, and rename only while nothing references the entry."""
	require_configuration_administrator()
	if not frappe.db.exists(FUNDING_SOURCE, name):
		fail_cfg("CFG_PROFILE_INVALID", "That funding source does not exist.")
	doc = frappe.get_doc(FUNDING_SOURCE, name)
	if expected_version and str(doc.modified) != str(expected_version):
		fail_cfg("CFG_VERSION_CONFLICT")
	before = {"label": doc.label, "record_status": doc.record_status}
	new_label = " ".join((label or "").split())
	if new_label and new_label != doc.label:
		if not (2 <= len(new_label) <= 100):
			fail_cfg("CFG_PROFILE_INVALID", "Enter a funding source name of 2–100 characters.")
		if _funding_source_referenced(name):
			fail_cfg("CFG_CATALOGUE_IN_USE")
		if frappe.db.exists(FUNDING_SOURCE, new_label):
			fail_cfg("CFG_PROFILE_INVALID", "A funding source with that name already exists.")
		frappe.rename_doc(FUNDING_SOURCE, name, new_label, force=True)
		doc = frappe.get_doc(FUNDING_SOURCE, new_label)
		doc.label = new_label
	if enabled is not None:
		doc.record_status = "Available" if enabled else "Retired"
	doc.save(ignore_permissions=True)
	log_audit_event(event_type="site_configuration", document_type=FUNDING_SOURCE, document_name=doc.name, action="update_funding_source", metadata={"before": before, "after": {"label": doc.label, "record_status": doc.record_status}})
	return {"name": doc.name, "enabled": doc.record_status == "Available", "expected_version": str(doc.modified)}


# --------------------------------------------------------------------------
# Shared version mechanics
# --------------------------------------------------------------------------


def _code(text: str) -> str:
	return "".join(ch if ch.isalnum() else "-" for ch in (text or "").upper()).strip("-")


def _overlaps(a_from, a_until, b_from, b_until) -> bool:
	a_from, b_from = getdate(a_from), getdate(b_from)
	a_until = getdate(a_until) if a_until else None
	b_until = getdate(b_until) if b_until else None
	if a_until and a_until < b_from:
		return False
	if b_until and b_until < a_from:
		return False
	return True


def _supersede_overlapping(doctype: str, filters: dict[str, Any], effective_from, effective_until, keep: str) -> list[str]:
	superseded: list[str] = []
	for row in frappe.get_all(doctype, filters={**filters, "status": "Active", "name": ("!=", keep)}, fields=["name", "effective_from", "effective_until"]):
		if _overlaps(row["effective_from"], row["effective_until"], effective_from, effective_until):
			older = frappe.get_doc(doctype, row["name"])
			older.flags.kt_supersede = True
			older.status = "Superseded"
			older.save(ignore_permissions=True)
			superseded.append(row["name"])
	return superseded


def _next_version(doctype: str, filters: dict[str, Any]) -> int:
	current = frappe.get_all(doctype, filters=filters, pluck="version_number", order_by="version_number desc", limit_page_length=1)
	return int(current[0] if current and current[0] else 0) + 1


def _in_force(doctype: str, filters: dict[str, Any], applicability_date) -> list[dict[str, Any]]:
	"""Every Active Version whose effective window contains the date."""
	date = getdate(applicability_date)
	rows = frappe.get_all(doctype, filters={**filters, "status": "Active"}, fields=["name", "effective_from", "effective_until", "version_number"])
	return [r for r in rows if getdate(r["effective_from"]) <= date and (not r["effective_until"] or getdate(r["effective_until"]) >= date)]


def _require_verification(value: str) -> str:
	value = (value or VERIFICATION_PENDING).strip()
	if value not in VERIFICATION_STATUSES:
		fail_cfg("CFG_PROFILE_INVALID", "Select a valid verification status.")
	return value


def _require_method(method: str) -> str:
	if not frappe.db.exists("Procurement Method", method):
		fail_cfg("CFG_PROFILE_INVALID", f"Unknown procurement method: {method}.")
	return method


# --------------------------------------------------------------------------
# Method eligibility profiles (§5.5.3.3; C03-detail / C04-eligibility)
# --------------------------------------------------------------------------


def register_method_profile_version(
	*,
	procurement_method: str,
	effective_from: str,
	conditions: list[dict[str, Any]],
	effective_until: str = "",
	verification_status: str = VERIFICATION_PENDING,
	applicability_basis: str = "Planned invitation date",
	source_instrument: str = "",
	provision: str = "",
	source_document: str = "",
	fixture_namespace: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""Register one new Version; an overlapping Active Version for the same
	method is superseded (retained). Idempotent on the key."""
	require_configuration_administrator()
	method = _require_method(procurement_method)
	verification = _require_verification(verification_status)

	def _do() -> dict[str, Any]:
		if not conditions:
			fail_cfg("CFG_PROFILE_INVALID", "A method profile needs at least one eligibility condition.")
		rows = []
		seen: set[str] = set()
		for c in conditions:
			cid = (c.get("condition_id") or "").strip()
			if not cid or cid in seen:
				fail_cfg("CFG_PROFILE_INVALID", "Every condition needs a unique condition id.")
			seen.add(cid)
			if c.get("kind") not in CONDITION_KINDS:
				fail_cfg("CFG_PROFILE_INVALID", f"Condition {cid}: kind must be Known fact or Declaration.")
			category = (c.get("procurement_category") or "").strip()
			if category and category not in PROCUREMENT_CATEGORIES:
				fail_cfg("CFG_PROFILE_INVALID", f"Condition {cid}: unknown category.")
			rows.append(
				{
					"condition_id": cid,
					"kind": c["kind"],
					"description": (c.get("description") or "").strip(),
					"procurement_category": category,
					"minimum_amount": flt(c.get("minimum_amount")),
					"maximum_amount": flt(c.get("maximum_amount")),
					"cumulative_basis": c.get("cumulative_basis") or "None",
					"mandatory": 1 if c.get("mandatory", True) else 0,
					"required_evidence": (c.get("required_evidence") or "").strip(),
					"authorisation_actor": (c.get("authorisation_actor") or "").strip(),
					"authorisation_stage": (c.get("authorisation_stage") or "").strip(),
					"statutory_reference": (c.get("statutory_reference") or "").strip(),
				}
			)
		version = _next_version(METHOD_PROFILE, {"procurement_method": method})
		doc = frappe.get_doc(
			{
				"doctype": METHOD_PROFILE,
				"profile_reference": f"MPR-{_code(method)}-V{version}",
				"procurement_method": method,
				"version_number": version,
				"status": "Active",
				"effective_from": getdate(effective_from),
				"effective_until": getdate(effective_until) if effective_until else None,
				"applicability_basis": applicability_basis,
				"verification_status": verification,
				"source_instrument": source_instrument,
				"provision": provision,
				"source_document": source_document,
				"conditions": rows,
				"fixture_namespace": fixture_namespace,
			}
		)
		doc.insert(ignore_permissions=True)
		superseded = _supersede_overlapping(METHOD_PROFILE, {"procurement_method": method}, doc.effective_from, doc.effective_until, doc.name)
		log_audit_event(event_type="site_configuration", document_type=METHOD_PROFILE, document_name=doc.name, action="register_method_profile_version", metadata={"version": version, "superseded": superseded, "verification_status": verification})
		return {"profile": doc.name, "version_number": version, "superseded": superseded, "created": True}

	return run_idempotent(idempotency_key, METHOD_PROFILE, method, "register_method_profile_version", _do)


def _method_profile_projection(doc) -> dict[str, Any]:
	return {
		"profile": doc.name,
		"reference_set": "Method eligibility",
		"procurement_method": doc.procurement_method,
		"version_number": int(doc.version_number),
		"status": doc.status,
		"effective_from": str(doc.effective_from or ""),
		"effective_until": str(doc.effective_until or ""),
		"applicability_basis": doc.applicability_basis or "",
		"verification_status": doc.verification_status or VERIFICATION_PENDING,
		"source_instrument": doc.source_instrument or "",
		"provision": doc.provision or "",
		"source_document": doc.source_document or "",
		"conditions": [
			{
				"condition_id": r.condition_id,
				"kind": r.kind,
				"description": r.description,
				"procurement_category": r.procurement_category or "",
				"minimum_amount": flt(r.minimum_amount),
				"maximum_amount": flt(r.maximum_amount),
				"cumulative_basis": r.cumulative_basis or "None",
				"mandatory": bool(r.mandatory),
				"required_evidence": r.required_evidence or "",
				"authorisation_actor": r.authorisation_actor or "",
				"authorisation_stage": r.authorisation_stage or "",
				"statutory_reference": r.statutory_reference or "",
			}
			for r in (doc.conditions or [])
		],
		"expected_version": str(doc.modified),
	}


def list_method_profiles() -> list[dict[str, Any]]:
	names = frappe.get_all(METHOD_PROFILE, pluck="name", order_by="procurement_method asc, version_number desc")
	return [_method_profile_projection(frappe.get_cached_doc(METHOD_PROFILE, n)) for n in names]


def get_method_profile(name: str) -> dict[str, Any]:
	if not frappe.db.exists(METHOD_PROFILE, name):
		fail_cfg("CFG_PROFILE_INVALID", "That method profile version does not exist.")
	return _method_profile_projection(frappe.get_cached_doc(METHOD_PROFILE, name))


def resolve_method_profile(*, procurement_method: str, procurement_category: str, applicability_date) -> dict[str, Any]:
	"""The exact Version in force for the method on the legally applicable
	date, with the conditions that apply to the category. `found = False`
	when no Version covers the date (a gap Planning reports as
	`PLN_REFERENCE_UNAVAILABLE`); two Active Versions covering the same date
	is a configuration defect and raises `CFG_RULE_UNRESOLVED`."""
	if not applicability_date:
		return {"found": False, "reason": "no_applicability_date"}
	rows = _in_force(METHOD_PROFILE, {"procurement_method": procurement_method}, applicability_date)
	if len(rows) > 1:
		fail_cfg("CFG_RULE_UNRESOLVED", f"More than one method profile for {procurement_method} is in force on {applicability_date}.")
	if not rows:
		return {"found": False, "reason": "no_profile", "procurement_method": procurement_method}
	projection = _method_profile_projection(frappe.get_cached_doc(METHOD_PROFILE, rows[0]["name"]))
	conditions = [c for c in projection["conditions"] if not c["procurement_category"] or c["procurement_category"] == procurement_category]
	category_supported = bool(conditions)
	return {
		**projection,
		"found": True,
		"applicability_date": str(getdate(applicability_date)),
		"procurement_category": procurement_category,
		"conditions": conditions,
		"category_supported": category_supported,
		"complete": category_supported,
	}


# --------------------------------------------------------------------------
# Procedure schedule profiles (§5.5.1; C04)
# --------------------------------------------------------------------------


def register_schedule_profile_version(
	*,
	procurement_method: str,
	procurement_category: str,
	profile_name: str,
	effective_from: str,
	milestones: list[dict[str, Any]],
	procedure: str = "",
	effective_until: str = "",
	counting_rule: str = "Calendar days",
	calendar: str = "",
	estimated_delivery_period_default_days: int | None = None,
	verification_status: str = VERIFICATION_PENDING,
	applicability_basis: str = "Planned invitation date",
	source_instrument: str = "",
	provision: str = "",
	source_document: str = "",
	fixture_namespace: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	require_configuration_administrator()
	method = _require_method(procurement_method)
	if procurement_category not in PROCUREMENT_CATEGORIES:
		fail_cfg("CFG_PROFILE_INVALID", "Select goods, works or services.")
	if counting_rule not in COUNTING_RULES:
		fail_cfg("CFG_PROFILE_INVALID", "Select a counting rule.")
	verification = _require_verification(verification_status)
	if counting_rule == "Working days":
		# §10.9 / CFG-UX-AC-20 — a working-day interval needs a *verified*
		# calendar version that actually covers this profile's period. An
		# existing-but-unverified calendar, or one whose period does not reach
		# the profile's, cannot pass on the strength of its name alone.
		if not calendar or not frappe.db.exists(CALENDAR, calendar):
			fail_cfg("CFG_CALENDAR_REQUIRED")
		row = frappe.db.get_value(
			CALENDAR,
			calendar,
			["status", "verification_status", "effective_from", "effective_until"],
			as_dict=True,
		)
		if row.status != "Active" or row.verification_status != VERIFICATION_VERIFIED:
			fail_cfg("CFG_CALENDAR_REQUIRED", "Select a verified working-day calendar for this interval.")
		if getdate(row.effective_from) > getdate(effective_from) or (
			row.effective_until and effective_until and getdate(row.effective_until) < getdate(effective_until)
		):
			fail_cfg(
				"CFG_CALENDAR_REQUIRED",
				"The selected working-day calendar does not cover this schedule's period.",
			)
	else:
		calendar = ""

	def _do() -> dict[str, Any]:
		if not milestones:
			fail_cfg("CFG_PROFILE_INVALID", "A schedule profile needs its milestone rows.")
		rows = []
		seen: set[str] = set()
		for m in milestones:
			key = m.get("milestone")
			if key not in MILESTONES or key in seen:
				fail_cfg("CFG_PROFILE_INVALID", f"Milestone {key!r} is unknown or repeated.")
			seen.add(key)
			basis = m.get("basis") or "Statutory"
			if basis not in MILESTONE_BASES:
				fail_cfg("CFG_PROFILE_INVALID", f"Milestone {key}: basis must be Statutory, Planning assumption or Source-derived.")
			# Frappe stores a blank Int as 0, so 0 is the one representation of
			# "not set": a blank statutory bound reads as verification required
			# and a blank default as a gap (C04). A genuine zero-day period is
			# therefore not a profile value — none exists in the Third Schedule.
			minimum = int(m.get("minimum_days") or 0)
			maximum = int(m.get("maximum_days") or 0)
			default = int(m.get("default_days") or 0)
			if minimum and default and default < minimum:
				fail_cfg("CFG_PROFILE_INVALID", f"Milestone {key}: the default is below the minimum.")
			if maximum and default and default > maximum:
				fail_cfg("CFG_PROFILE_INVALID", f"Milestone {key}: the default exceeds the maximum.")
			rows.append(
				{
					"milestone": key,
					"label": (m.get("label") or MILESTONE_LABELS[key]).strip(),
					"sequence": int(m.get("sequence") or (MILESTONES.index(key) + 1)),
					"applies": 1 if m.get("applies", True) else 0,
					"counting_rule": m.get("counting_rule") or counting_rule,
					"minimum_days": minimum,
					"maximum_days": maximum,
					"default_days": default,
					"basis": basis,
					"statutory_reference": (m.get("statutory_reference") or "").strip(),
				}
			)
		missing = [k for k in MILESTONES if k not in seen]
		if missing:
			fail_cfg("CFG_PROFILE_INVALID", f"The profile must list every milestone (missing: {', '.join(missing)}).")
		version = _next_version(SCHEDULE_PROFILE, {"procurement_method": method, "procurement_category": procurement_category})
		doc = frappe.get_doc(
			{
				"doctype": SCHEDULE_PROFILE,
				"profile_reference": f"SPR-{_code(method)}-{procurement_category.upper()}-V{version}",
				"profile_name": " ".join((profile_name or "").split()),
				"procurement_method": method,
				"procedure": procedure,
				"procurement_category": procurement_category,
				"version_number": version,
				"status": "Active",
				"effective_from": getdate(effective_from),
				"effective_until": getdate(effective_until) if effective_until else None,
				"applicability_basis": applicability_basis,
				"counting_rule": counting_rule,
				"calendar": calendar,
				"estimated_delivery_period_default_days": estimated_delivery_period_default_days,
				"verification_status": verification,
				"source_instrument": source_instrument,
				"provision": provision,
				"source_document": source_document,
				"milestones": sorted(rows, key=lambda r: r["sequence"]),
				"fixture_namespace": fixture_namespace,
			}
		)
		doc.insert(ignore_permissions=True)
		superseded = _supersede_overlapping(
			SCHEDULE_PROFILE, {"procurement_method": method, "procurement_category": procurement_category}, doc.effective_from, doc.effective_until, doc.name
		)
		log_audit_event(event_type="site_configuration", document_type=SCHEDULE_PROFILE, document_name=doc.name, action="register_schedule_profile_version", metadata={"version": version, "superseded": superseded, "verification_status": verification})
		return {"profile": doc.name, "version_number": version, "superseded": superseded, "created": True}

	return run_idempotent(idempotency_key, SCHEDULE_PROFILE, f"{method}:{procurement_category}", "register_schedule_profile_version", _do)


def _schedule_profile_projection(doc) -> dict[str, Any]:
	milestones = sorted(doc.milestones or [], key=lambda r: int(r.sequence or 0))
	rows = [
		{
			"milestone": r.milestone,
			"label": r.label or MILESTONE_LABELS.get(r.milestone, r.milestone),
			"sequence": int(r.sequence or 0),
			"applies": bool(r.applies),
			"counting_rule": r.counting_rule or doc.counting_rule or "Calendar days",
			"minimum_days": int(r.minimum_days) if r.minimum_days else None,
			"maximum_days": int(r.maximum_days) if r.maximum_days else None,
			"default_days": int(r.default_days) if r.default_days else None,
			"basis": r.basis,
			"statutory_reference": r.statutory_reference or "",
			"period_key": PERIOD_BY_MILESTONE.get(r.milestone, ""),
		}
		for r in milestones
	]
	periods = {r["period_key"]: r for r in rows if r["period_key"] and r["applies"]}
	# Complete = every applicable period milestone has a default and a
	# counting rule; the anchor and the delivery row carry none by design.
	gaps = [r["milestone"] for r in rows if r["applies"] and r["period_key"] and r["default_days"] is None]
	calendar_row = None
	if doc.counting_rule == "Working days":
		if doc.calendar and frappe.db.exists(CALENDAR, doc.calendar):
			calendar_row = _business_day_calendar_projection(frappe.get_cached_doc(CALENDAR, doc.calendar))
		else:
			gaps = [*gaps, "working_day_calendar"]
	return {
		"profile": doc.name,
		"reference_set": "Schedule profile",
		"profile_name": doc.profile_name,
		"procurement_method": doc.procurement_method,
		"procedure": doc.procedure or "",
		"procurement_category": doc.procurement_category,
		"version_number": int(doc.version_number),
		"status": doc.status,
		"effective_from": str(doc.effective_from or ""),
		"effective_until": str(doc.effective_until or ""),
		"applicability_basis": doc.applicability_basis or "",
		"counting_rule": doc.counting_rule or "Calendar days",
		"calendar": calendar_row,
		"estimated_delivery_period_default_days": (
			int(doc.estimated_delivery_period_default_days) if doc.estimated_delivery_period_default_days else None
		),
		"verification_status": doc.verification_status or VERIFICATION_PENDING,
		"source_instrument": doc.source_instrument or "",
		"provision": doc.provision or "",
		"source_document": doc.source_document or "",
		"milestones": rows,
		"periods": periods,
		"complete": not gaps,
		"gaps": gaps,
		"expected_version": str(doc.modified),
	}


def list_schedule_profiles() -> list[dict[str, Any]]:
	names = frappe.get_all(SCHEDULE_PROFILE, pluck="name", order_by="procurement_method asc, procurement_category asc, version_number desc")
	return [_schedule_profile_projection(frappe.get_cached_doc(SCHEDULE_PROFILE, n)) for n in names]


def get_schedule_profile(name: str) -> dict[str, Any]:
	if not frappe.db.exists(SCHEDULE_PROFILE, name):
		fail_cfg("CFG_PROFILE_INVALID", "That schedule profile version does not exist.")
	return _schedule_profile_projection(frappe.get_cached_doc(SCHEDULE_PROFILE, name))


def resolve_schedule_profile(*, procurement_method: str, procurement_category: str, applicability_date) -> dict[str, Any]:
	"""The exact schedule profile Version in force on the applicable date.
	No Version → `found = False` (Planning permits Draft work and blocks
	submission; no Open Tender fallback); two → `CFG_RULE_UNRESOLVED`."""
	if not applicability_date:
		return {"found": False, "reason": "no_applicability_date"}
	filters = {"procurement_method": procurement_method, "procurement_category": procurement_category}
	rows = _in_force(SCHEDULE_PROFILE, filters, applicability_date)
	if len(rows) > 1:
		fail_cfg("CFG_RULE_UNRESOLVED", f"More than one schedule profile for {procurement_method} / {procurement_category} is in force on {applicability_date}.")
	if not rows:
		return {"found": False, "reason": "no_profile", **filters}
	projection = _schedule_profile_projection(frappe.get_cached_doc(SCHEDULE_PROFILE, rows[0]["name"]))
	return {**projection, "found": True, "applicability_date": str(getdate(applicability_date))}


# --------------------------------------------------------------------------
# Business-day calendars (CFG-CHG-002 v0.11 §4.8; C04 working-days)
# --------------------------------------------------------------------------


def register_business_day_calendar_version(
	*,
	calendar_name: str,
	effective_from: str,
	weekend_days: list[str],
	holidays: list[dict[str, Any]] | None = None,
	effective_until: str = "",
	verification_status: str = VERIFICATION_PENDING,
	source_instrument: str = "",
	provision: str = "",
	source_document: str = "",
	fixture_namespace: str = "",
	idempotency_key: str = "",
) -> dict[str, Any]:
	"""§7 `SaveBusinessDayCalendarVersion` — immutable calendar version; a
	newer overlapping version supersedes the earlier one (same pattern as
	schedule profiles)."""
	require_configuration_administrator()
	name = " ".join((calendar_name or "").split())
	if not name:
		fail_cfg("CFG_CALENDAR_REQUIRED", "Enter the calendar name.")
	days = [d for d in (weekend_days or []) if d]
	verification = _require_verification(verification_status)

	def _do() -> dict[str, Any]:
		reference = _code(name) or "CALENDAR"
		version = _next_version(CALENDAR, {"calendar_name": name})
		rows = []
		seen: set[str] = set()
		for h in holidays or []:
			date = h.get("holiday_date")
			if not date or date in seen:
				fail_cfg("CFG_CALENDAR_REQUIRED", "Each holiday needs a distinct date.")
			seen.add(date)
			rows.append(
				{
					"holiday_date": date,
					"holiday_name": (h.get("holiday_name") or "").strip(),
					"source_reference": (h.get("source_reference") or "").strip(),
				}
			)
		doc = frappe.get_doc(
			{
				"doctype": CALENDAR,
				"calendar_reference": f"{reference}-V{version}",
				"calendar_name": name,
				"version_number": version,
				"status": "Active",
				"effective_from": getdate(effective_from),
				"effective_until": getdate(effective_until) if effective_until else None,
				"weekend_days": ",".join(days),
				"verification_status": verification,
				"source_instrument": source_instrument,
				"provision": provision,
				"source_document": source_document,
				"holidays": rows,
				"fixture_namespace": fixture_namespace,
			}
		)
		doc.insert(ignore_permissions=True)
		superseded = _supersede_overlapping(CALENDAR, {"calendar_name": name}, doc.effective_from, doc.effective_until, doc.name)
		log_audit_event(event_type="site_configuration", document_type=CALENDAR, document_name=doc.name, action="register_business_day_calendar_version", metadata={"version": version, "superseded": superseded, "verification_status": verification})
		return {"calendar": doc.name, "version_number": version, "superseded": superseded, "created": True}

	return run_idempotent(idempotency_key, CALENDAR, _code(name) or "CALENDAR", "register_business_day_calendar_version", _do)


def _business_day_calendar_projection(doc) -> dict[str, Any]:
	return {
		"calendar": doc.name,
		"calendar_name": doc.calendar_name,
		"version_number": int(doc.version_number),
		"status": doc.status,
		"effective_from": str(doc.effective_from or ""),
		"effective_until": str(doc.effective_until or ""),
		"weekend_days": [d for d in (doc.weekend_days or "").split(",") if d],
		"verification_status": doc.verification_status or VERIFICATION_PENDING,
		"source_instrument": doc.source_instrument or "",
		"provision": doc.provision or "",
		"source_document": doc.source_document or "",
		"holidays": [
			{"holiday_date": str(r.holiday_date), "holiday_name": r.holiday_name, "source_reference": r.source_reference or ""}
			for r in sorted(doc.holidays or [], key=lambda r: str(r.holiday_date))
		],
		"expected_version": str(doc.modified),
	}


def list_business_day_calendars() -> list[dict[str, Any]]:
	names = frappe.get_all(CALENDAR, pluck="name", order_by="calendar_name asc, version_number desc")
	return [_business_day_calendar_projection(frappe.get_cached_doc(CALENDAR, n)) for n in names]


def get_business_day_calendar(name: str) -> dict[str, Any]:
	if not frappe.db.exists(CALENDAR, name):
		fail_cfg("CFG_CALENDAR_REQUIRED", "That calendar version does not exist.")
	return _business_day_calendar_projection(frappe.get_cached_doc(CALENDAR, name))


# --------------------------------------------------------------------------
# Reminder threshold (§5.5.1B; C04-eligibility-reminder)
# --------------------------------------------------------------------------


def get_reminder_threshold_days() -> int:
	value = frappe.db.get_single_value(SETTINGS, "approaching_milestone_threshold_days")
	# 0 is a real setting (§10.10: reminders begin on the milestone date), so
	# only an absent value falls back to the default — never a falsy one.
	return DEFAULT_REMINDER_THRESHOLD_DAYS if value in (None, "") else int(value)


def set_reminder_threshold_days(*, days: int, idempotency_key: str = "") -> dict[str, Any]:
	require_configuration_administrator()

	def _do() -> dict[str, Any]:
		# §10.10 — a whole number of calendar days, 0–365. 0 is legitimate
		# (reminders begin on the milestone date); anything else is refused
		# here, not only in the browser.
		try:
			value = int(days)
		except (TypeError, ValueError):
			fail_cfg("CFG_PROFILE_INVALID", "Enter a whole number from 0 to 365.")
		if not 0 <= value <= 365:
			fail_cfg("CFG_PROFILE_INVALID", "Enter a whole number from 0 to 365.")
		before = get_reminder_threshold_days()
		doc = frappe.get_doc(SETTINGS)
		doc.approaching_milestone_threshold_days = int(days)
		doc.save(ignore_permissions=True)
		log_audit_event(event_type="site_configuration", document_type=SETTINGS, document_name=SETTINGS, action="set_reminder_threshold_days", metadata={"before": before, "after": int(days)})
		return {"approaching_milestone_threshold_days": int(days)}

	return run_idempotent(idempotency_key, SETTINGS, SETTINGS, "set_reminder_threshold_days", _do)


# --------------------------------------------------------------------------
# The Procurement settings tab read (C03/C04)
# --------------------------------------------------------------------------


def get_procurement_settings() -> dict[str, Any]:
	"""One read for the fifth System setup tab: funding sources, every rule
	Version (method profiles, regulator references), every schedule profile,
	every calendar and the reminder threshold. Administrator / System
	Manager only."""
	from kentender_core.services import regulatory_reference as register

	user = frappe.session.user
	if user != "Administrator" and "System Manager" not in frappe.get_roles(user):
		return {"outcome": "FORBIDDEN"}
	return {
		"outcome": "OK",
		"funding_sources": list_funding_sources(),
		"method_profiles": list_method_profiles(),
		"reference_sets": register.list_reference_sets(),
		"reference_kinds": list(register.REFERENCE_KINDS),
		"schedule_profiles": list_schedule_profiles(),
		"calendars": list_business_day_calendars(),
		"reminder_threshold_days": get_reminder_threshold_days(),
		"verification_statuses": list(VERIFICATION_STATUSES),
		"milestones": [{"milestone": m, "label": MILESTONE_LABELS[m]} for m in MILESTONES],
		"procurement_methods": frappe.get_all("Procurement Method", filters={"status": "Active"}, pluck="name", order_by="name asc"),
		"procurement_categories": list(PROCUREMENT_CATEGORIES),
		# §10.6's "Entity types" applicability control offers the same closed
		# set the Procuring entity screen uses — never a free-text entity name.
		"entity_types": list(PE_TYPES),
	}


# --------------------------------------------------------------------------
# Fixture cleanup
# --------------------------------------------------------------------------


def purge_fixture_profiles(fixture_namespace: str) -> int:
	count = 0
	for doctype in (METHOD_PROFILE, SCHEDULE_PROFILE, CALENDAR):
		for name in frappe.get_all(doctype, filters={"fixture_namespace": fixture_namespace}, pluck="name"):
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_fixture_purge = True
			doc.delete(ignore_permissions=True)
			count += 1
	return count


def purge_playwright_funding_sources(prefix: str = "Playwright test") -> int:
	"""Gate teardown only: remove funding sources the Procurement settings
	browser spec created (name prefix), never a referenced or canonical one."""
	if not (frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests")):
		return 0
	count = 0
	for name in frappe.get_all(FUNDING_SOURCE, filters={"label": ("like", f"{prefix}%")}, pluck="name"):
		if _funding_source_referenced(name):
			continue
		frappe.delete_doc(FUNDING_SOURCE, name, force=True, ignore_permissions=True)
		count += 1
	frappe.db.commit()
	return count
