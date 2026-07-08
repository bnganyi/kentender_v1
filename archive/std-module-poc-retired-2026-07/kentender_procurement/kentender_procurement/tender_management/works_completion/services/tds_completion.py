# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0200 — Works Tender Data Sheet parameter completion.

Persists representative TDS fields as ``Tender STD Instance`` parameter rows via
``StdInstanceParameterService``. ITT clause text is never edited here (parameters only).

Output staleness for parameter codes is defined in ``PARAMETER_CODE_TO_STALE_OUTPUTS``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime

from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
	_normalize_pc,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_TDS_VALUES_CHANGED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
	union_stale_outputs_for_parameter_codes,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

TDS_PARAMETER_CODES: tuple[str, ...] = (
	"tender_title",
	"procuring_entity_name",
	"project_location",
	"procurement_method",
	"submission_deadline",
	"opening_datetime",
	"clarification_deadline",
	"bid_validity_days",
	"tender_security_required",
	"tender_security_type",
	"tender_security_amount",
	"tender_security_currency",
	"site_visit_required",
	"site_visit_datetime",
	"site_visit_location",
	"pre_tender_meeting_required",
	"pre_tender_meeting_datetime",
	"pre_tender_meeting_location",
	"bid_currency",
	"language",
	"margin_of_preference_applicable",
)

_CODE_MESSAGES: dict[str, str] = {
	"TDS_SUBMISSION_DEADLINE_MISSING": _("Submission deadline is required."),
	"TDS_OPENING_DATETIME_MISSING": _("Opening date and time is required."),
	"TDS_OPENING_DATETIME_INVALID": _("Opening must be after the submission deadline."),
	"TDS_CLARIFICATION_DEADLINE_INVALID": _("Clarification deadline must be before the submission deadline."),
	"TDS_BID_VALIDITY_INVALID": _("Bid validity period must be a positive whole number of days."),
	"TENDER_SECURITY_AMOUNT_MISSING": _("Tender security amount is required when security is required."),
	"TENDER_SECURITY_CURRENCY_MISSING": _("Tender security currency is required when security is required."),
	"TDS_SITE_VISIT_DETAILS_MISSING": _("Site visit date/time and location are required when a site visit is mandatory."),
}


def _truthy_string(val: str | None) -> bool:
	s = (val or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _stringify_tds_value(val: Any) -> str:
	if val is None:
		return ""
	if isinstance(val, bool):
		return "1" if val else "0"
	if isinstance(val, (int, float)):
		return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
	return str(val).strip()


def _merged_tds_state(instance_name: str, patch: dict[str, Any] | None) -> dict[str, str]:
	"""Current persisted TDS parameter strings, overridden by ``patch`` keys."""
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	state: dict[str, str] = {code: "" for code in TDS_PARAMETER_CODES}
	for row in doc.parameter_values or []:
		pc = _normalize_pc(row.parameter_code)
		if pc in state:
			state[pc] = (row.value or "").strip()
	if patch:
		for k, v in patch.items():
			if k in state:
				state[k] = _stringify_tds_value(v)
	return state


def _parse_dt(raw: str) -> datetime | None:
	s = (raw or "").strip()
	if not s:
		return None
	try:
		dt = get_datetime(s)
		return dt if isinstance(dt, datetime) else None
	except Exception:
		return None


def _validate_body(state: dict[str, str]) -> list[dict[str, str]]:
	blockers: list[dict[str, str]] = []

	if not (state.get("submission_deadline") or "").strip():
		blockers.append(
			{
				"code": "TDS_SUBMISSION_DEADLINE_MISSING",
				"message": str(_CODE_MESSAGES["TDS_SUBMISSION_DEADLINE_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	if not (state.get("opening_datetime") or "").strip():
		blockers.append(
			{
				"code": "TDS_OPENING_DATETIME_MISSING",
				"message": str(_CODE_MESSAGES["TDS_OPENING_DATETIME_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	sub_dt = _parse_dt(state.get("submission_deadline", ""))
	open_dt = _parse_dt(state.get("opening_datetime", ""))
	if sub_dt and open_dt and open_dt <= sub_dt:
		blockers.append(
			{
				"code": "TDS_OPENING_DATETIME_INVALID",
				"message": str(_CODE_MESSAGES["TDS_OPENING_DATETIME_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	cl_dt = _parse_dt(state.get("clarification_deadline", ""))
	if cl_dt and sub_dt and cl_dt >= sub_dt:
		blockers.append(
			{
				"code": "TDS_CLARIFICATION_DEADLINE_INVALID",
				"message": str(_CODE_MESSAGES["TDS_CLARIFICATION_DEADLINE_INVALID"]),
				"severity": SEVERITY_HIGH,
			}
		)

	bvd_raw = (state.get("bid_validity_days") or "").strip()
	if not bvd_raw:
		blockers.append(
			{
				"code": "TDS_BID_VALIDITY_INVALID",
				"message": str(_CODE_MESSAGES["TDS_BID_VALIDITY_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)
	else:
		try:
			bvd = int(bvd_raw)
			if bvd <= 0:
				raise ValueError
		except Exception:
			blockers.append(
				{
					"code": "TDS_BID_VALIDITY_INVALID",
					"message": str(_CODE_MESSAGES["TDS_BID_VALIDITY_INVALID"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

	sec_req = _truthy_string(state.get("tender_security_required"))
	if sec_req:
		if not (state.get("tender_security_amount") or "").strip():
			blockers.append(
				{
					"code": "TENDER_SECURITY_AMOUNT_MISSING",
					"message": str(_CODE_MESSAGES["TENDER_SECURITY_AMOUNT_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)
		if not (state.get("tender_security_currency") or "").strip():
			blockers.append(
				{
					"code": "TENDER_SECURITY_CURRENCY_MISSING",
					"message": str(_CODE_MESSAGES["TENDER_SECURITY_CURRENCY_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

	sv_req = _truthy_string(state.get("site_visit_required"))
	if sv_req:
		if not (state.get("site_visit_datetime") or "").strip() or not (
			state.get("site_visit_location") or ""
		).strip():
			blockers.append(
				{
					"code": "TDS_SITE_VISIT_DETAILS_MISSING",
					"message": str(_CODE_MESSAGES["TDS_SITE_VISIT_DETAILS_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

	return blockers


class WorksTdsCompletionService:
	"""Save and validate Works TDS parameter values on a Tender STD Instance."""

	@staticmethod
	def validate_tds_values(
		instance_code: str,
		prospective_values: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``."""
		code = (instance_code or "").strip()
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": _("Tender STD Instance was not found."),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		if prospective_values is not None:
			state = _merged_tds_state(code, prospective_values)
		else:
			state = _merged_tds_state(code, None)

		blockers = _validate_body(state)
		return {"valid": not blockers, "blockers": blockers}

	@staticmethod
	def save_tds_values(
		instance_code: str,
		tds_values: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Persist TDS patch; raises ``ValidationError`` if context or TDS validation fails."""
		code = (instance_code or "").strip()
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save TDS values: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works TDS"),
			)

		patch = {k: v for k, v in (tds_values or {}).items() if k in TDS_PARAMETER_CODES}
		merged = _merged_tds_state(code, patch)
		val = WorksTdsCompletionService.validate_tds_values(code, prospective_values=merged)
		if not val.get("valid"):
			blocks = val.get("blockers") or []
			parts = [str(b.get("message") or b.get("code")) for b in blocks]
			frappe.throw(
				_("TDS validation failed: {0}").format("; ".join(parts)),
				title=_("Works TDS"),
			)

		user = actor or frappe.session.user
		stale_before = stale_logical_outputs_snapshot(code)
		for key in sorted(patch.keys()):
			StdInstanceParameterService.set_parameter_value(
				code,
				key,
				_stringify_tds_value(patch[key]) or None,
				source="Works TDS",
				user=user,
				ignore_publication_lock=False,
			)

		affected = union_stale_outputs_for_parameter_codes(patch.keys())
		emit_works_completion_audit(
			WORKS_TDS_VALUES_CHANGED,
			code,
			affected_outputs=affected,
			details={"parameter_codes": sorted(patch.keys())},
			performed_by=user,
		)
		emit_works_output_stale_if_new(code, stale_before, source="tds", performed_by=user)

		return {"ok": True, "instance_code": code}
