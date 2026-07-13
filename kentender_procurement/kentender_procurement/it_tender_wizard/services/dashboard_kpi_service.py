# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dashboard KPI aggregation."""

from __future__ import annotations

from datetime import date

import frappe
from frappe.utils import getdate

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_permission_service import PERM_VIEW, assert_permission

DASHBOARD_STATUS_FILTERS: tuple[tuple[str, str], ...] = (
	(ws.IN_CONFIGURATION, "In Configuration"),
	(ws.VALIDATION_FAILED, "Validation Failed"),
	(ws.READY_FOR_REVIEW, "Ready for Review"),
	(ws.RETURNED_FOR_CORRECTION, "Returned"),
)

_KPI_STATE_MAP: tuple[tuple[str, frozenset[str]], ...] = (
	("in_configuration", ws.KPI_IN_CONFIGURATION),
	("validation_failed", ws.KPI_VALIDATION_FAILED),
	("ready_for_review", ws.KPI_READY_FOR_REVIEW),
	("returned", ws.KPI_RETURNED),
	("publication_ready", ws.KPI_PUBLICATION_READY),
)


def build_dashboard_filter_options(*, procurement_entity_id: str | None = None) -> dict:
	filters: dict = {}
	if procurement_entity_id:
		filters["procuring_entity_id"] = procurement_entity_id

	rows = frappe.get_all(
		"Tender STD Instance",
		filters=filters,
		fields=[
			"procuring_entity_id",
			"procuring_entity_name",
			"procurement_method_code",
			"procurement_method_name",
		],
	)
	entities: dict[str, str] = {}
	methods: dict[str, str] = {}
	for row in rows:
		entity_id = (row.procuring_entity_id or "").strip()
		entity_name = (row.procuring_entity_name or "").strip()
		if entity_id and entity_name:
			entities[entity_id] = entity_name
		method_code = (row.procurement_method_code or "").strip()
		method_name = (row.procurement_method_name or "").strip()
		if method_code and method_name:
			methods[method_code] = method_name

	return {
		"statuses": [{"value": code, "label": label} for code, label in DASHBOARD_STATUS_FILTERS],
		"entities": [
			{"id": entity_id, "code": entity_id, "name": entity_name}
			for entity_id, entity_name in sorted(entities.items(), key=lambda item: item[1].lower())
		],
		"methods": [
			{"id": method_code, "code": method_code, "name": method_name}
			for method_code, method_name in sorted(methods.items(), key=lambda item: item[1].lower())
		],
	}


def build_dashboard_summary(*, procurement_entity_id: str | None = None) -> dict:
	assert_permission(PERM_VIEW)
	filters: dict = {}
	if procurement_entity_id:
		filters["procuring_entity_id"] = procurement_entity_id

	rows = frappe.get_all(
		"Tender STD Instance",
		filters=filters,
		fields=["name", "wizard_state", "due_at", "modified"],
	)
	today = date.today()
	kpis = {
		"in_configuration": 0,
		"validation_failed": 0,
		"ready_for_review": 0,
		"returned": 0,
		"publication_ready": 0,
		"overdue_actions": 0,
	}
	today_deltas = {key: 0 for key in kpis}
	for row in rows:
		state = row.wizard_state
		modified_on = getdate(row.modified) if row.modified else None
		for kpi_key, states in _KPI_STATE_MAP:
			if state in states:
				kpis[kpi_key] += 1
				if modified_on == today:
					today_deltas[kpi_key] += 1
		if row.due_at and row.due_at < today and state in ws.OVERDUE_ELIGIBLE_STATES:
			kpis["overdue_actions"] += 1
			if modified_on == today:
				today_deltas["overdue_actions"] += 1
	return {
		"kpis": kpis,
		"today_deltas": today_deltas,
		"total": len(rows),
		"filter_options": build_dashboard_filter_options(procurement_entity_id=procurement_entity_id),
	}
