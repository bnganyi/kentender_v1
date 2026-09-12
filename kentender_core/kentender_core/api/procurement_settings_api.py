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
def set_reminder_threshold_days(days, idempotency_key: str | None = None) -> dict[str, Any]:
	return settings.set_reminder_threshold_days(days=int(days), idempotency_key=idempotency_key or "")
