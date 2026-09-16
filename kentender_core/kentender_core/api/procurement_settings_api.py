"""PLN-CHG-001 v1.18 §10.11 (C03/C04) / §11.6 — whitelisted Procurement
settings endpoints. Thin wrappers over
:mod:`kentender_core.services.procurement_settings` and the regulator
reference register, with explicit signatures (no ``**kwargs``); every
authority check, validation and audit write happens inside the service.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_core.services import procurement_settings as settings
from kentender_core.services import regulatory_reference as register


def _rows(payload) -> list[dict[str, Any]]:
	if isinstance(payload, str):
		return json.loads(payload or "[]")
	return list(payload or [])


def _obj(payload) -> dict[str, Any]:
	if isinstance(payload, str):
		return json.loads(payload or "{}")
	return dict(payload or {})


def _list(payload) -> list:
	if payload is None or payload == "":
		return []
	if isinstance(payload, str):
		return json.loads(payload)
	return list(payload)


def _bool(value) -> bool | None:
	if value is None or value == "":
		return None
	if isinstance(value, str):
		return value.strip().lower() not in ("", "0", "false", "no")
	return bool(value)


@frappe.whitelist()
def get_procurement_settings() -> dict[str, Any]:
	return settings.get_procurement_settings()


@frappe.whitelist()
def add_funding_source(label: str, idempotency_key: str | None = None) -> dict[str, Any]:
	return settings.add_funding_source(label=label, idempotency_key=idempotency_key or "")


@frappe.whitelist()
def update_funding_source(name: str, label: str | None = None, enabled=None, expected_version: str | None = None) -> dict[str, Any]:
	return settings.update_funding_source(name=name, label=label or "", enabled=_bool(enabled), expected_version=expected_version or "")


@frappe.whitelist()
def get_method_profile(name: str) -> dict[str, Any]:
	return settings.get_method_profile(name)


@frappe.whitelist()
def register_method_profile_version(
	procurement_method: str,
	effective_from: str,
	conditions,
	effective_until: str | None = None,
	verification_status: str | None = None,
	applicability_basis: str | None = None,
	source_instrument: str | None = None,
	provision: str | None = None,
	source_document: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	return settings.register_method_profile_version(
		procurement_method=procurement_method,
		effective_from=effective_from,
		conditions=_rows(conditions),
		effective_until=effective_until or "",
		verification_status=verification_status or settings.VERIFICATION_PENDING,
		applicability_basis=applicability_basis or "Planned invitation date",
		source_instrument=source_instrument or "",
		provision=provision or "",
		source_document=source_document or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def get_schedule_profile(name: str) -> dict[str, Any]:
	return settings.get_schedule_profile(name)


@frappe.whitelist()
def register_schedule_profile_version(
	procurement_method: str,
	procurement_category: str,
	profile_name: str,
	effective_from: str,
	milestones,
	procedure: str | None = None,
	effective_until: str | None = None,
	counting_rule: str | None = None,
	calendar: str | None = None,
	estimated_delivery_period_default_days=None,
	verification_status: str | None = None,
	applicability_basis: str | None = None,
	source_instrument: str | None = None,
	provision: str | None = None,
	source_document: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	default_days = None if estimated_delivery_period_default_days in (None, "") else int(estimated_delivery_period_default_days)
	return settings.register_schedule_profile_version(
		procurement_method=procurement_method,
		procurement_category=procurement_category,
		profile_name=profile_name,
		effective_from=effective_from,
		milestones=_rows(milestones),
		procedure=procedure or "",
		effective_until=effective_until or "",
		counting_rule=counting_rule or "Calendar days",
		calendar=calendar or "",
		estimated_delivery_period_default_days=default_days,
		verification_status=verification_status or settings.VERIFICATION_PENDING,
		applicability_basis=applicability_basis or "Planned invitation date",
		source_instrument=source_instrument or "",
		provision=provision or "",
		source_document=source_document or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def get_regulatory_reference_version(name: str) -> dict[str, Any]:
	if not frappe.db.exists(register.DOCTYPE, name):
		frappe.throw("That reference version does not exist.")
	return register._projection(name)


@frappe.whitelist()
def list_regulatory_reference_versions(reference_set: str) -> list[dict[str, Any]]:
	"""§7 `ListRegulatoryReferenceVersions` — every version of one set, newest
	first (C03-D's immutable version history)."""
	return register.list_regulatory_reference_versions(reference_set)


@frappe.whitelist()
def create_regulatory_reference(
	reference_key: str,
	reference_kind: str,
	display_name: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `CreateRegulatoryReference` — step 1 of §7.3's two-command creation:
	the stable set, with no version and so no legal eligibility yet."""
	return register.create_regulatory_reference(
		reference_key=reference_key,
		reference_kind=reference_kind,
		display_name=display_name or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def save_regulatory_reference_version(
	reference_set: str,
	payload,
	effective_from: str,
	effective_until: str | None = None,
	applicability_basis: str | None = None,
	applicability_entity_types=None,
	applicability_county: str | None = None,
	applicability_categories=None,
	applicability_currency: str | None = None,
	source_instrument: str | None = None,
	provision: str | None = None,
	source_document: str | None = None,
	interpretation: str | None = None,
	supersedes_version_ids=None,
	change_reason: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `SaveRegulatoryReferenceVersion` — step 2 of §7.3: a new immutable
	numbered version. `verification_status` is deliberately not accepted from
	a client: a version is Pending until a `Check sources` event says
	otherwise (§4.6)."""
	return register.save_regulatory_reference_version(
		reference_set=reference_set,
		payload=_obj(payload),
		effective_from=effective_from,
		effective_until=effective_until or "",
		applicability_basis=applicability_basis or "",
		applicability_entity_types=_list(applicability_entity_types),
		applicability_county=applicability_county or "All",
		applicability_categories=_list(applicability_categories),
		applicability_currency=applicability_currency or "KES",
		source_instrument=source_instrument or "",
		provision=provision or "",
		source_document=source_document or "",
		interpretation=interpretation or "",
		supersedes_version_ids=_list(supersedes_version_ids),
		change_reason=change_reason or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def rename_regulatory_reference(
	reference_set: str, display_name: str, expected_version: str | None = None
) -> dict[str, Any]:
	"""§7 `RenameRegulatoryReference` — the display name only; key, kind and
	frozen consumer names are untouched."""
	return register.rename_regulatory_reference(
		reference_set=reference_set,
		display_name=display_name,
		expected_version=expected_version or "",
	)


@frappe.whitelist()
def record_reference_verification(
	target_doctype: str,
	target_name: str,
	outcome: str,
	source_check_date: str | None = None,
	instrument_edition: str | None = None,
	provisions: str | None = None,
	source_document: str | None = None,
	effective_dates_and_amendments: str | None = None,
	applicability_date_basis_explanation: str | None = None,
	interpretation_evidence: str | None = None,
	unresolved_points: str | None = None,
	change_reason: str | None = None,
	expected_prior_event: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `RecordReferenceVerification` — appends one source-check event; the
	target's own verification status follows it as a projection (§4.6)."""
	return register.record_reference_verification(
		target_doctype=target_doctype,
		target_name=target_name,
		outcome=outcome,
		source_check_date=source_check_date or "",
		instrument_edition=instrument_edition or "",
		provisions=provisions or "",
		source_document=source_document or "",
		effective_dates_and_amendments=effective_dates_and_amendments or "",
		applicability_date_basis_explanation=applicability_date_basis_explanation or "",
		interpretation_evidence=interpretation_evidence or "",
		unresolved_points=unresolved_points or "",
		change_reason=change_reason or "",
		expected_prior_event=expected_prior_event or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def list_verification_history(target_doctype: str, target_name: str) -> list[dict[str, Any]]:
	"""§10.8 — the append-only source-check history for one target."""
	return register.list_verification_history(target_doctype, target_name)


@frappe.whitelist()
def get_business_day_calendar(name: str) -> dict[str, Any]:
	return settings.get_business_day_calendar(name)


@frappe.whitelist()
def register_business_day_calendar_version(
	calendar_name: str,
	effective_from: str,
	weekend_days,
	holidays=None,
	effective_until: str | None = None,
	verification_status: str | None = None,
	source_instrument: str | None = None,
	provision: str | None = None,
	source_document: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	days = weekend_days
	if isinstance(days, str):
		days = json.loads(days or "[]")
	return settings.register_business_day_calendar_version(
		calendar_name=calendar_name,
		effective_from=effective_from,
		weekend_days=list(days or []),
		holidays=_rows(holidays),
		effective_until=effective_until or "",
		verification_status=verification_status or settings.VERIFICATION_PENDING,
		source_instrument=source_instrument or "",
		provision=provision or "",
		source_document=source_document or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def set_reminder_threshold_days(days, idempotency_key: str | None = None) -> dict[str, Any]:
	return settings.set_reminder_threshold_days(days=int(days), idempotency_key=idempotency_key or "")
