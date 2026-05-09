# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender-specific STD parameter values — validation, stale output marking.

STDINST-0200.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_OUTPUTS_STALED,
	EVT_STDINST_PARAMETER_CHANGED,
)
# Pack §8 — post-publication parameters frozen unless addendum flow (future STDINST-0800).
INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION: frozenset[str] = frozenset(
	{
		"Published Locked",
		"Addendum Pending",
		"Addendum Regenerated",
		"Superseded",
		"Cancelled",
	}
)

# Known parameter_code → logical outputs that become stale (unknown codes: no automatic staleness).
# WORKS-COMP-0200 TDS groups + identity/minimal churn (Bundle-only for narrative fields).
_STALE_BUNDLE_DSM_DOM: frozenset[str] = frozenset({"Bundle", "DSM", "DOM"})
_STALE_BUNDLE_DSM_DEM: frozenset[str] = frozenset({"Bundle", "DSM", "DEM"})
# Pack §15 site information — Bundle, DSM, DEM, DCM
_STALE_BUNDLE_DSM_DEM_DCM: frozenset[str] = frozenset({"Bundle", "DSM", "DEM", "DCM"})
_STALE_BUNDLE_DEM: frozenset[str] = frozenset({"Bundle", "DEM"})
_STALE_BUNDLE_ONLY: frozenset[str] = frozenset({"Bundle"})
_STALE_BUNDLE_DCM: frozenset[str] = frozenset({"Bundle", "DCM"})

PARAMETER_CODE_TO_STALE_OUTPUTS: dict[str, frozenset[str]] = {
	# Dates / deadlines
	"submission_deadline": _STALE_BUNDLE_DSM_DOM,
	"opening_datetime": _STALE_BUNDLE_DSM_DOM,
	"clarification_deadline": _STALE_BUNDLE_DSM_DOM,
	# Tender security
	"tender_security_required": _STALE_BUNDLE_DSM_DEM,
	"tender_security_type": _STALE_BUNDLE_DSM_DEM,
	"tender_security_amount": _STALE_BUNDLE_DSM_DEM,
	"tender_security_currency": _STALE_BUNDLE_DSM_DEM,
	# Bid validity
	"bid_validity_days": _STALE_BUNDLE_DSM_DEM,
	# Site visit (pack §15: site information → Bundle, DSM, DEM, DCM)
	"site_visit_required": _STALE_BUNDLE_DSM_DEM_DCM,
	"site_visit_datetime": _STALE_BUNDLE_DSM_DEM_DCM,
	"site_visit_location": _STALE_BUNDLE_DSM_DEM_DCM,
	# Preference / evaluation thresholds (pack §15 → Bundle, DSM, DEM)
	"margin_of_preference_applicable": _STALE_BUNDLE_DSM_DEM,
	# Identity / method / meetings / currency / language — Bundle-only
	"tender_title": _STALE_BUNDLE_ONLY,
	"procuring_entity_name": _STALE_BUNDLE_ONLY,
	"project_location": _STALE_BUNDLE_ONLY,
	"procurement_method": _STALE_BUNDLE_ONLY,
	"pre_tender_meeting_required": _STALE_BUNDLE_ONLY,
	"pre_tender_meeting_datetime": _STALE_BUNDLE_ONLY,
	"pre_tender_meeting_location": _STALE_BUNDLE_ONLY,
	# Currency also gates SCC payment wording — stale Bundle + DCM (WORKS-COMP-0400).
	"bid_currency": _STALE_BUNDLE_DCM,
	"language": _STALE_BUNDLE_ONLY,
	# WORKS-COMP-0210 evaluation / qualification options (pack staleness table).
	"minimum_average_annual_turnover_amount": _STALE_BUNDLE_DSM_DEM,
	"minimum_average_annual_turnover_currency": _STALE_BUNDLE_DSM_DEM,
	"minimum_average_annual_turnover_years": _STALE_BUNDLE_DSM_DEM,
	"similar_works_experience_minimum_contracts": _STALE_BUNDLE_DSM_DEM,
	"similar_works_experience_minimum_value_each": _STALE_BUNDLE_DSM_DEM,
	"similar_works_experience_period_years": _STALE_BUNDLE_DSM_DEM,
	"key_personnel_required": _STALE_BUNDLE_DSM_DEM,
	"equipment_schedule_required": _STALE_BUNDLE_DSM_DEM,
	# WORKS-COMP-0400 — SCC completion parameters (pack §13 stale table: Bundle + DCM).
	"scc.completion_period_months": _STALE_BUNDLE_DCM,
	"scc.defects_liability_period_months": _STALE_BUNDLE_DCM,
	"scc.performance_security_required": _STALE_BUNDLE_DCM,
	"scc.performance_security_percentage": _STALE_BUNDLE_DCM,
	"scc.retention_percentage": _STALE_BUNDLE_DCM,
	"scc.liquidated_damages_rate": _STALE_BUNDLE_DCM,
	"scc.advance_payment_allowed": _STALE_BUNDLE_DCM,
	"scc.insurance_requirements": _STALE_BUNDLE_DCM,
	"scc.engineer_or_project_manager": _STALE_BUNDLE_DCM,
	"scc.payment_terms": _STALE_BUNDLE_DCM,
	"scc.dispute_resolution_forum": _STALE_BUNDLE_DCM,
	"scc.maximum_liquidated_damages_percent": _STALE_BUNDLE_DCM,
}

OUTPUT_KEY_TO_PARENT_FIELD: dict[str, str] = {
	"Bundle": "current_bundle_output_code",
	"DSM": "current_dsm_output_code",
	"DOM": "current_dom_output_code",
	"DEM": "current_dem_output_code",
	"DCM": "current_dcm_output_code",
}


def _normalize_pc(parameter_code: str | None) -> str:
	return (parameter_code or "").strip()


def _value_nonempty(value: str | None) -> bool:
	return bool((value or "").strip())


def parameter_values_snapshot(doc: Document) -> list[dict[str, Any]]:
	"""Deterministic snapshot of child rows for publication-lock / audit comparisons."""
	rows: list[dict[str, Any]] = []
	for row in doc.get("parameter_values") or []:
		pc = _normalize_pc(row.get("parameter_code"))
		if not pc:
			continue
		rows.append(
			{
				"parameter_code": pc,
				"value_code": (row.get("value_code") or "").strip(),
				"value": (row.get("value") or "").strip(),
				"value_status": row.get("value_status") or "",
				"source": row.get("source") or "",
				"drives_bundle": int(row.get("drives_bundle") or 0),
				"drives_dsm": int(row.get("drives_dsm") or 0),
				"drives_dom": int(row.get("drives_dom") or 0),
				"drives_dem": int(row.get("drives_dem") or 0),
				"drives_dcm": int(row.get("drives_dcm") or 0),
				"parameter_locked": int(row.get("parameter_locked") or 0),
				"source_addendum_code": (row.get("source_addendum_code") or "").strip(),
			}
		)
	rows.sort(key=lambda r: r["parameter_code"])
	return rows


class StdInstanceParameterService:
	"""STD Instance parameter table — set, validate, lock, stale-output propagation."""

	@staticmethod
	def assert_works_completion_context_for_parameter_writes(
		doc: Document,
		*,
		ignore_works_completion_context: bool = False,
	) -> None:
		"""For Works tender-bound instances, require pack WORKS-COMP-0110 context (RULE-001–002).

		Direct parameter writes must not bypass tender binding / Works category checks.
		"""
		if ignore_works_completion_context:
			return
		if (doc.get("procurement_category") or "").strip() != "WORKS":
			return
		from kentender_procurement.tender_management.works_completion.services.context_validator import (
			validate_works_completion_context,
		)

		ctx = validate_works_completion_context(doc.name)
		if ctx.get("valid"):
			return
		blockers = list(ctx.get("blockers") or [])
		first = blockers[0] if blockers else {}
		code = (first.get("code") or "WORKS_CONTEXT_INVALID").strip()
		msg = (first.get("message") or code).strip()
		try:
			from kentender_procurement.tender_management.works_completion.audit import (
				WORKS_EDIT_DENIED_LOCKED,
				emit_works_completion_audit,
			)

			emit_works_completion_audit(
				WORKS_EDIT_DENIED_LOCKED,
				doc.name,
				details={"reason": "works_completion_context", "blocker_code": code, "message": msg},
			)
		except Exception:
			pass
		frappe.throw(_(msg), title=_(code), exc=frappe.ValidationError)

	@staticmethod
	def status_blocks_parameter_edits(instance_status: str | None) -> bool:
		return bool(instance_status) and instance_status in INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION

	@staticmethod
	def assert_parameter_mutation_allowed(
		instance_status: str | None,
		*,
		ignore_publication_lock: bool = False,
		instance_name: str | None = None,
	) -> None:
		if ignore_publication_lock:
			return
		if StdInstanceParameterService.status_blocks_parameter_edits(instance_status):
			if instance_name and frappe.db.exists("Tender STD Instance", instance_name):
				cat = (frappe.db.get_value("Tender STD Instance", instance_name, "procurement_category") or "").strip()
				if cat == "WORKS":
					try:
						from kentender_procurement.tender_management.works_completion.audit import (
							WORKS_EDIT_DENIED_LOCKED,
							emit_works_completion_audit,
						)

						emit_works_completion_audit(
							WORKS_EDIT_DENIED_LOCKED,
							instance_name,
							details={
								"reason": "parameter_mutation_blocked_status",
								"instance_status": instance_status or "",
							},
						)
					except Exception:
						pass
			frappe.throw(
				_(
					"STD parameter values cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(instance_status),
				title=_("STD Parameters Locked"),
			)

	@staticmethod
	def set_parameter_value(
		instance_name: str,
		parameter_code: str,
		value: str | None,
		*,
		source: str = "Officer Entry",
		drives_bundle: bool = False,
		drives_dsm: bool = False,
		drives_dom: bool = False,
		drives_dem: bool = False,
		drives_dcm: bool = False,
		source_addendum_code: str | None = None,
		user: str | None = None,
		ignore_publication_lock: bool = False,
		ignore_row_lock: bool = False,
		ignore_works_completion_context: bool = False,
	) -> Document:
		pc = _normalize_pc(parameter_code)
		if not pc:
			frappe.throw(_("parameter_code is required."), title=_("STD Parameter"))

		if not ignore_publication_lock:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)
			from kentender_procurement.tender_management.std_instance.publication_lock import (
				StdPublicationLockService,
			)

			StdAuthorizationService.assert_can_edit_draft_instance(instance_name)
			StdPublicationLockService.assert_editable(instance_name, operation_label="edit parameters")

		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceParameterService.assert_parameter_mutation_allowed(
			doc.instance_status,
			ignore_publication_lock=ignore_publication_lock,
			instance_name=instance_name,
		)
		doc.flags.ignore_parameter_publication_lock = bool(ignore_publication_lock)
		StdInstanceParameterService.assert_works_completion_context_for_parameter_writes(
			doc,
			ignore_works_completion_context=bool(
				ignore_works_completion_context or ignore_publication_lock
			),
		)

		actor = user or frappe.session.user
		prev_value: str | None = None
		target_row = None
		for row in doc.parameter_values:
			if _normalize_pc(row.parameter_code) == pc:
				target_row = row
				break

		if target_row is not None:
			if target_row.parameter_locked and not ignore_row_lock:
				frappe.throw(
					_("Parameter {0} is locked and cannot be changed.").format(pc),
					title=_("STD Parameter Locked"),
				)
			prev_value = (target_row.value or "").strip()
		else:
			vc = f"STD-PARAM-{frappe.generate_hash(length=12)}"
			target_row = doc.append(
				"parameter_values",
				{
					"value_code": vc,
					"parameter_code": pc,
				},
			)

		val_normalized = (value or "").strip()
		target_row.value = value
		target_row.source = source
		target_row.drives_bundle = 1 if drives_bundle else 0
		target_row.drives_dsm = 1 if drives_dsm else 0
		target_row.drives_dom = 1 if drives_dom else 0
		target_row.drives_dem = 1 if drives_dem else 0
		target_row.drives_dcm = 1 if drives_dcm else 0
		target_row.changed_by = actor
		target_row.changed_at = now_datetime()
		if source_addendum_code:
			target_row.source_addendum_code = source_addendum_code

		target_row.value_status = "Provided" if _value_nonempty(value) else "Missing"

		value_changed = prev_value != val_normalized
		doc.save(ignore_permissions=True)

		if value_changed:
			mark_outputs_stale_for_parameter_change(doc.name, pc)
			doc = frappe.get_doc("Tender STD Instance", doc.name)
			emit_std_instance_event(
				EVT_STDINST_PARAMETER_CHANGED,
				instance_code=doc.name,
				details={
					"parameter_code": pc,
					"source": source,
					"value_status": target_row.value_status,
				},
			)

		return doc

	@staticmethod
	def validate_parameter_values(instance_name: str) -> dict[str, Any]:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		missing: list[str] = []
		invalid: list[str] = []
		for row in doc.parameter_values or []:
			pc = _normalize_pc(row.parameter_code)
			if not pc:
				continue
			if row.parameter_locked:
				continue
			if row.value_status == "Invalid":
				invalid.append(pc)
			elif not _value_nonempty(row.value):
				missing.append(pc)

		ok = not missing and not invalid
		return {
			"ok": ok,
			"missing": missing,
			"invalid": invalid,
			"instance": instance_name,
		}

	@staticmethod
	def lock_parameter_values(
		instance_name: str,
		*,
		user: str | None = None,
		ignore_works_completion_context: bool = False,
	) -> Document:
		from kentender_procurement.tender_management.std_instance.publication_lock import (
			StdPublicationLockService,
		)

		StdPublicationLockService.assert_editable(instance_name, operation_label="lock parameters")
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceParameterService.assert_works_completion_context_for_parameter_writes(
			doc,
			ignore_works_completion_context=ignore_works_completion_context,
		)
		StdInstanceParameterService.assert_parameter_mutation_allowed(
			doc.instance_status,
			instance_name=instance_name,
		)
		doc.flags.ignore_parameter_publication_lock = False
		actor = user or frappe.session.user
		for row in doc.parameter_values or []:
			row.parameter_locked = 1
			row.value_status = "Locked"
			row.changed_by = actor
			row.changed_at = now_datetime()
		doc.save(ignore_permissions=True)
		return doc


def mark_outputs_stale_for_parameter_change(
	instance_name: str,
	parameter_code: str,
) -> Document | None:
	"""Merge stale logical outputs for ``parameter_code``; clear matching ``current_*`` codes; readiness Blocked."""
	pc = _normalize_pc(parameter_code)
	affected = PARAMETER_CODE_TO_STALE_OUTPUTS.get(pc)
	if not affected:
		return None

	doc = frappe.get_doc("Tender STD Instance", instance_name)

	raw = (doc.outputs_stale_flags or "").strip()
	existing: list[str] = []
	if raw:
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, list):
				existing = [str(x) for x in parsed]
		except Exception:
			existing = []

	merged = sorted(set(existing) | set(affected))
	doc.outputs_stale_flags = json.dumps(merged)

	for key in affected:
		field = OUTPUT_KEY_TO_PARENT_FIELD.get(key)
		if field:
			doc.set(field, None)

	doc.readiness_status = "Blocked"

	doc.save(ignore_permissions=True)
	emit_std_instance_event(
		EVT_STDINST_OUTPUTS_STALED,
		instance_code=instance_name,
		document_name=instance_name,
		details={
			"source": "parameter",
			"parameter_code": pc,
			"stale_outputs": sorted(affected),
		},
	)
	return doc


def parse_outputs_stale_flags(doc: Document) -> list[str]:
	raw = (doc.outputs_stale_flags or "").strip()
	if not raw:
		return []
	try:
		parsed = json.loads(raw)
		if isinstance(parsed, list):
			return [str(x) for x in parsed]
	except Exception:
		return []
	return []


def assert_locked_parameter_rows_not_mutated(prev_doc: Document, new_doc: Document) -> None:
	"""If a row was locked in ``prev_doc``, forbid value/metadata mutations in ``new_doc``."""
	prev_map = {_normalize_pc(r.parameter_code): r for r in (prev_doc.parameter_values or [])}
	for pc, pr in prev_map.items():
		if not pr.parameter_locked:
			continue
		cur_row = next(
			(r for r in (new_doc.parameter_values or []) if _normalize_pc(r.parameter_code) == pc),
			None,
		)
		if cur_row is None:
			frappe.throw(
				_("Locked parameter {0} cannot be removed.").format(pc),
				title=_("STD Parameter Locked"),
			)
		if not int(cur_row.parameter_locked or 0):
			frappe.throw(
				_("Locked parameter {0} cannot be unlocked via Desk.").format(pc),
				title=_("STD Parameter Locked"),
			)
	for row in new_doc.parameter_values or []:
		pc = _normalize_pc(row.parameter_code)
		if not pc or pc not in prev_map:
			continue
		pr = prev_map[pc]
		if not pr.parameter_locked:
			continue
		if (
			(row.value or "").strip() != (pr.value or "").strip()
			or (row.source or "") != (pr.source or "")
			or int(row.drives_bundle or 0) != int(pr.drives_bundle or 0)
			or int(row.drives_dsm or 0) != int(pr.drives_dsm or 0)
			or int(row.drives_dom or 0) != int(pr.drives_dom or 0)
			or int(row.drives_dem or 0) != int(pr.drives_dem or 0)
			or int(row.drives_dcm or 0) != int(pr.drives_dcm or 0)
			or (row.source_addendum_code or "").strip() != (pr.source_addendum_code or "").strip()
		):
			frappe.throw(
				_("Locked parameter {0} cannot be modified.").format(pc),
				title=_("STD Parameter Locked"),
			)


def assert_no_duplicate_parameter_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.parameter_values or []:
		pc = _normalize_pc(row.parameter_code)
		if not pc:
			continue
		if pc in seen:
			frappe.throw(
				_("Duplicate parameter_code in table: {0}").format(pc),
				title=_("STD Parameter Values"),
			)
		seen.add(pc)
