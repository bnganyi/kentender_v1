"""CFG-CHG-002 v0.6 §7 — whitelisted site-configuration endpoints.

Thin wrappers over :mod:`kentender_core.services.site_configuration`, with
explicit signatures (no ``**kwargs``). Every authority check, validation,
version check and audit write happens inside the service on every call;
nothing here trusts a client-supplied value as authority.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_core.services import site_configuration as configuration


def _obj(payload) -> dict[str, Any]:
	if isinstance(payload, str):
		return json.loads(payload or "{}")
	return payload or {}


@frappe.whitelist()
def get_site_configuration() -> dict[str, Any]:
	"""§7 `GetSiteConfiguration` — identity, root presence and open intake."""
	return configuration.get_site_configuration()


@frappe.whitelist()
def get_system_setup_workspace() -> dict[str, Any]:
	"""KT-STD-001 v1.2 §3A — the System setup page's own load call, carrying
	the Administrator/System Manager verdict alongside the configuration."""
	return configuration.get_system_setup_workspace()


@frappe.whitelist()
def configure_procuring_entity(
	pe_name: str,
	pe_code: str,
	pe_type: str,
	ppra_registration: str | None = None,
	timezone: str | None = None,
	statutory_approval_route: str | None = None,
	entity_is_county=None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `ConfigureProcuringEntity` — first-run: PE plus root unit, atomically.
	PLN-CHG-001 v1.18 §10.11 C01: the mandatory route and the county flag are
	first-run inputs (CFG v0.9 §4.1), validated in the service."""
	county = None
	if entity_is_county not in (None, ""):
		county = str(entity_is_county).strip().lower() not in ("0", "false", "no") if isinstance(entity_is_county, str) else bool(entity_is_county)
	return configuration.configure_procuring_entity(
		pe_name=pe_name,
		pe_code=pe_code,
		pe_type=pe_type,
		ppra_registration=ppra_registration or "",
		timezone=timezone or "Africa/Nairobi",
		statutory_approval_route=statutory_approval_route or "",
		entity_is_county=county,
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def update_procuring_entity(payload, expected_version: str | None = None) -> dict[str, Any]:
	"""§7 `UpdateProcuringEntity` — editable descriptive fields; never the code."""
	return configuration.update_procuring_entity(
		payload=_obj(payload), expected_version=expected_version or ""
	)


@frappe.whitelist()
def list_fiscal_years() -> dict[str, Any]:
	"""§7 `ListFiscalYears` — derived phase, intake state and reference counts."""
	return configuration.list_fiscal_years()


@frappe.whitelist()
def preview_fiscal_year(start_year: int | str) -> dict[str, Any]:
	"""The server-computed Add-financial-year dialog summary (§11.3)."""
	return configuration.preview_fiscal_year(start_year)


@frappe.whitelist()
def list_fiscal_year_intake_history(fiscal_year: str) -> dict[str, Any]:
	"""§10.3 C02 — the Change history disclosure for one financial year."""
	return configuration.list_fiscal_year_intake_history(fiscal_year)


@frappe.whitelist()
def add_fiscal_year(start_year: int | str, idempotency_key: str | None = None) -> dict[str, Any]:
	"""§7 `AddFiscalYear` — generated dates; the site Company attached."""
	return configuration.add_fiscal_year(
		start_year=int(start_year), idempotency_key=idempotency_key or ""
	)


@frappe.whitelist()
def open_needs_submission(
	fiscal_year: str,
	closes_at: str | None = None,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `OpenNeedsSubmission` — atomically closes any other open year."""
	return configuration.open_needs_submission(
		fiscal_year=fiscal_year,
		closes_at=closes_at or "",
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def close_needs_submission(
	fiscal_year: str,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `CloseNeedsSubmission` — audited with actor, instant and reason."""
	return configuration.close_needs_submission(
		fiscal_year=fiscal_year,
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def open_dpp_submission(
	fiscal_year: str,
	closes_at: str | None = None,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""CFG v0.9 §4.2 / CFG-BR-013 — open departmental-plan intake for one year,
	atomically closing any other; independent of the needs flag."""
	return configuration.open_dpp_submission(
		fiscal_year=fiscal_year,
		closes_at=closes_at or "",
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def close_dpp_submission(
	fiscal_year: str,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""CFG v0.9 §4.2 — close departmental-plan intake, audited."""
	return configuration.close_dpp_submission(
		fiscal_year=fiscal_year,
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def get_disposal_plan_submission_state(fiscal_year: str | None = None) -> dict[str, Any]:
	"""CFG-CHG-002 v0.11 §4.3 — the disposal-plan intake flag, read-only."""
	return configuration.get_disposal_plan_submission_state(fiscal_year or "")


@frappe.whitelist()
def open_disposal_plan_submission(
	fiscal_year: str,
	closes_at: str | None = None,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""CFG-CHG-002 v0.11 §4.3 — open disposal-plan intake for one year,
	atomically closing any other; independent of needs and dpp."""
	return configuration.open_disposal_plan_submission(
		fiscal_year=fiscal_year,
		closes_at=closes_at or "",
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def close_disposal_plan_submission(
	fiscal_year: str,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""CFG-CHG-002 v0.11 §4.3 — close disposal-plan intake, audited."""
	return configuration.close_disposal_plan_submission(
		fiscal_year=fiscal_year,
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def update_intake_close_instant(
	module_key: str,
	fiscal_year: str,
	closes_at: str | None = None,
	reason: str | None = None,
	expected_version: str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	"""§7 `UpdateIntakeCloseInstant` — changes only the named module's close
	instant on its currently-open year; never opens or swaps a year."""
	return configuration.update_intake_close_instant(
		module_key=module_key,
		fiscal_year=fiscal_year,
		closes_at=closes_at or "",
		reason=reason or "",
		expected_version=expected_version or "",
		idempotency_key=idempotency_key or "",
	)


@frappe.whitelist()
def set_fiscal_year_disabled(
	fiscal_year: str, disabled: int | str | bool, expected_version: str | None = None
) -> dict[str, Any]:
	"""§7 `SetFiscalYearDisabled` — blocked by references or an open flag."""
	if isinstance(disabled, str):
		disabled = disabled.strip().lower() not in ("", "0", "false", "no")
	return configuration.set_fiscal_year_disabled(
		fiscal_year=fiscal_year, disabled=bool(disabled), expected_version=expected_version or ""
	)


@frappe.whitelist()
def repair_organisation_root(idempotency_key: str | None = None) -> dict[str, Any]:
	"""§7 `RepairOrganisationRoot` — no effect while a root exists."""
	return configuration.repair_organisation_root(idempotency_key=idempotency_key or "")
