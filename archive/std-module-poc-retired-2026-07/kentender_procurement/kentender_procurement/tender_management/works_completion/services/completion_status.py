# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0120 — Completion status summary for Works tender-stage completion.

Aggregates ``validate_works_completion_context``, read-only readiness evaluation, and
output pointer/stale flags into a UI-ready payload.

EVALUATION_OPTIONS uses ``WorksEvaluationOptionsService.validate_evaluation_options``; WORKS_REQUIREMENTS uses
``WorksRequirementsCompletionService.validate_works_requirements``; DRAWINGS uses
``WorksDrawingRegisterService.validate_drawing_register`` when context is valid, and still maps
``REQUIRED_ATTACHMENTS_INCOMPLETE`` from STD readiness; BOQ uses
``WorksBoqCompletionService.validate_boq`` when context is valid, plus readiness ``BOQ_MISSING`` /
``BOQ_INVALID``; SCC uses ``WorksSccCompletionService.validate_scc_values`` when context is valid.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.readiness import (
	VALID_CURRENT_OUTPUT_STATUSES,
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	WorksEvaluationOptionsService,
)
from kentender_procurement.tender_management.works_completion.services.drawing_register_completion import (
	WorksDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.scc_completion import (
	WorksSccCompletionService,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	WorksRequirementsCompletionService,
)

STAGE_CODES_ORDER: tuple[str, ...] = (
	"CONTEXT",
	"TDS",
	"EVALUATION_OPTIONS",
	"WORKS_REQUIREMENTS",
	"DRAWINGS",
	"BOQ",
	"SCC",
	"OUTPUTS",
	"READINESS",
	"SNAPSHOT_LOCK",
)

_STAGE_LABELS: dict[str, str] = {
	"CONTEXT": "Tender and STD context",
	"TDS": "Tender Data Sheet",
	"EVALUATION_OPTIONS": "Evaluation and qualification options",
	"WORKS_REQUIREMENTS": "Works requirements",
	"DRAWINGS": "Drawings register",
	"BOQ": "Bills of quantities",
	"SCC": "Special conditions of contract",
	"OUTPUTS": "Generated outputs",
	"READINESS": "Readiness validation",
	"SNAPSHOT_LOCK": "Configuration snapshot and lock",
}

_SNAPSHOT_LOCK_COMPLETE_STATUSES: frozenset[str] = frozenset(
	{
		"Locked for Approval",
		"Published Locked",
		"Addendum Pending",
		"Addendum Regenerated",
	}
)

_READINESS_BLOCKER_CODES: frozenset[str] = frozenset(
	{
		"TEMPLATE_OR_PROFILE_MISSING",
		"PARAMETERS_INCOMPLETE",
		"WORKS_REQUIREMENTS_INCOMPLETE",
		"REQUIRED_ATTACHMENTS_INCOMPLETE",
		"BOQ_MISSING",
		"BOQ_INVALID",
		"BUNDLE_MISSING",
		"DSM_MISSING",
		"DOM_MISSING",
		"DEM_MISSING",
		"DCM_MISSING",
		"STALE_OUTPUTS_PRESENT",
		"UNRESOLVED_BLOCKERS",
	}
)

_MAX_READINESS_CRITICAL = 50


def _stale_logical_keys(inst: Document) -> set[str]:
	"""Map stale flag strings to canonical output type keys (e.g. ``Bundle``)."""
	stale_raw = parse_outputs_stale_flags(inst)
	out: set[str] = set()
	for x in stale_raw:
		s = str(x).strip()
		if not s:
			continue
		for logical in OUTPUT_KEY_TO_PARENT_FIELD:
			if s.lower() == logical.lower():
				out.add(logical)
				break
	return out


def _output_states(inst: Document) -> tuple[dict[str, str], int, int]:
	"""Return lowercase output map, missing count, stale count.

	JSON stale flags mark an output as ``Stale`` in the map even when the pointer
	is still empty (regeneration required). Missing counts include those rows for
	OUTPUTS stage blocking.
	"""
	flagged_stale = _stale_logical_keys(inst)
	out: dict[str, str] = {}
	missing = 0
	stale_n = 0
	for logical, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
		key = logical.lower()
		name = (inst.get(field) or "").strip()
		has_row = bool(name and frappe.db.exists("Tender STD Generated Output", name))
		status = ""
		if has_row:
			status = (
				frappe.db.get_value("Tender STD Generated Output", name, "output_status") or ""
			).strip()
		valid_row = has_row and status in VALID_CURRENT_OUTPUT_STATUSES

		if logical in flagged_stale:
			out[key] = "Stale"
			if valid_row:
				stale_n += 1
			else:
				missing += 1
			continue

		if not valid_row:
			out[key] = "Missing"
			missing += 1
			continue
		out[key] = "Current"
	return out, missing, stale_n


def _readiness_blocker_codes(readiness: dict[str, Any]) -> set[str]:
	return {str(b.get("code") or "") for b in readiness.get("blockers") or []}


def _stage_row(
	stage_code: str,
	status: str,
	critical_blockers: int,
	warnings: int,
) -> dict[str, Any]:
	return {
		"stage_code": stage_code,
		"stage_label": _STAGE_LABELS[stage_code],
		"status": status,
		"critical_blockers": int(critical_blockers),
		"warnings": int(warnings),
	}


def _missing_instance_payload(requested_code: str) -> dict[str, Any]:
	stages = []
	for sc in STAGE_CODES_ORDER:
		crit = 1 if sc == "CONTEXT" else 0
		stages.append(_stage_row(sc, "Blocked", crit, 0))
	return {
		"instance_code": (requested_code or "").strip(),
		"tender_code": "",
		"overall_status": "Blocked",
		"stages": stages,
		"outputs": {k: "Missing" for k in ("bundle", "dsm", "dom", "dem", "dcm")},
		"readiness_status": "Blocked",
	}


def get_completion_status(instance_code: str) -> dict[str, Any]:
	"""Return completion summary for UI and orchestration (WORKS-COMP-0120)."""
	code = (instance_code or "").strip()
	if not code or not frappe.db.exists("Tender STD Instance", code):
		return _missing_instance_payload(code)

	inst = frappe.get_doc("Tender STD Instance", code)
	ctx = validate_works_completion_context(code)
	eval_opts = WorksEvaluationOptionsService.validate_evaluation_options(code)
	eval_ok = bool(eval_opts.get("valid"))
	wr_opts = WorksRequirementsCompletionService.validate_works_requirements(code)
	wr_ok = bool(wr_opts.get("valid"))
	dr_opts = WorksDrawingRegisterService.validate_drawing_register(code)
	dr_ok = bool(dr_opts.get("valid"))
	boq_opts = WorksBoqCompletionService.validate_boq(code)
	boq_ok = bool(boq_opts.get("valid"))
	scc_opts = WorksSccCompletionService.validate_scc_values(code)
	scc_ok = bool(scc_opts.get("valid"))
	readiness = StdInstanceReadinessService.evaluate(code, persist=False)
	r_codes = _readiness_blocker_codes(readiness)
	outputs_map, missing_n, stale_n = _output_states(inst)

	if missing_n > 0:
		out_stage_status = "Blocked"
		out_crit, out_warn = missing_n, stale_n
	elif stale_n > 0:
		out_stage_status = "Incomplete"
		out_crit, out_warn = 0, stale_n
	else:
		out_stage_status = "Complete"
		out_crit, out_warn = 0, 0

	ctx_ok = bool(ctx.get("valid"))
	ctx_blockers = len(ctx.get("blockers") or [])

	stages: list[dict[str, Any]] = []

	# CONTEXT
	if ctx_ok:
		stages.append(_stage_row("CONTEXT", "Complete", 0, 0))
	else:
		stages.append(_stage_row("CONTEXT", "Blocked", max(ctx_blockers, 1), 0))

	# TDS
	if "PARAMETERS_INCOMPLETE" in r_codes:
		stages.append(_stage_row("TDS", "Blocked", 1, 0))
	elif not ctx_ok:
		stages.append(_stage_row("TDS", "Incomplete", 0, 0))
	else:
		stages.append(_stage_row("TDS", "Complete", 0, 0))

	# EVALUATION_OPTIONS
	if not eval_ok:
		stages.append(
			_stage_row(
				"EVALUATION_OPTIONS",
				"Blocked",
				max(len(eval_opts.get("blockers") or []), 1),
				0,
			)
		)
	elif not ctx_ok:
		stages.append(_stage_row("EVALUATION_OPTIONS", "Incomplete", 0, 0))
	else:
		stages.append(_stage_row("EVALUATION_OPTIONS", "Complete", 0, 0))

	# WORKS_REQUIREMENTS
	if not wr_ok:
		stages.append(
			_stage_row(
				"WORKS_REQUIREMENTS",
				"Blocked",
				max(len(wr_opts.get("blockers") or []), 1),
				0,
			)
		)
	elif "WORKS_REQUIREMENTS_INCOMPLETE" in r_codes:
		stages.append(_stage_row("WORKS_REQUIREMENTS", "Blocked", 1, 0))
	elif not ctx_ok:
		stages.append(_stage_row("WORKS_REQUIREMENTS", "Incomplete", 0, 0))
	else:
		stages.append(_stage_row("WORKS_REQUIREMENTS", "Complete", 0, 0))

	# DRAWINGS
	if not ctx_ok:
		stages.append(_stage_row("DRAWINGS", "Incomplete", 0, 0))
	elif not dr_ok:
		stages.append(
			_stage_row(
				"DRAWINGS",
				"Blocked",
				max(len(dr_opts.get("blockers") or []), 1),
				0,
			)
		)
	elif "REQUIRED_ATTACHMENTS_INCOMPLETE" in r_codes:
		stages.append(_stage_row("DRAWINGS", "Blocked", 1, 0))
	else:
		stages.append(_stage_row("DRAWINGS", "Complete", 0, 0))

	# BOQ
	if not ctx_ok:
		stages.append(_stage_row("BOQ", "Incomplete", 0, 0))
	elif not boq_ok:
		stages.append(
			_stage_row(
				"BOQ",
				"Blocked",
				max(len(boq_opts.get("blockers") or []), 1),
				0,
			)
		)
	elif "BOQ_MISSING" in r_codes or "BOQ_INVALID" in r_codes:
		stages.append(_stage_row("BOQ", "Blocked", 1, 0))
	else:
		stages.append(_stage_row("BOQ", "Complete", 0, 0))

	# SCC
	if not ctx_ok:
		stages.append(_stage_row("SCC", "Incomplete", 0, 0))
	elif not scc_ok:
		stages.append(
			_stage_row(
				"SCC",
				"Blocked",
				max(len(scc_opts.get("blockers") or []), 1),
				0,
			)
		)
	else:
		stages.append(_stage_row("SCC", "Complete", 0, 0))

	# OUTPUTS
	stages.append(_stage_row("OUTPUTS", out_stage_status, out_crit, out_warn))

	# READINESS
	if readiness.get("status") == "Ready":
		stages.append(_stage_row("READINESS", "Complete", 0, 0))
	else:
		relevant = r_codes & _READINESS_BLOCKER_CODES
		crit = min(len(relevant) if relevant else len(r_codes), _MAX_READINESS_CRITICAL)
		if crit < 1 and readiness.get("blockers"):
			crit = 1
		stages.append(_stage_row("READINESS", "Blocked", crit, 0))

	# SNAPSHOT_LOCK
	ist = (inst.instance_status or "").strip()
	if ist in _SNAPSHOT_LOCK_COMPLETE_STATUSES:
		stages.append(_stage_row("SNAPSHOT_LOCK", "Complete", 0, 0))
	else:
		stages.append(_stage_row("SNAPSHOT_LOCK", "Incomplete", 0, 0))

	readiness_status = str(readiness.get("status") or "Blocked")

	tm2 = (inst.tm2_tender or "").strip()
	tender_code = ""
	if tm2 and frappe.db.exists("TM2 Tender", tm2):
		ref = frappe.db.get_value("TM2 Tender", tm2, "tender_reference")
		tender_code = ((ref or "").strip() or tm2).strip()

	overall = "Incomplete"
	if (
		not ctx_ok
		or not eval_ok
		or not wr_ok
		or not dr_ok
		or not boq_ok
		or not scc_ok
		or readiness_status == "Blocked"
		or out_stage_status == "Blocked"
	):
		overall = "Blocked"
	elif (
		ctx_ok
		and eval_ok
		and wr_ok
		and dr_ok
		and boq_ok
		and scc_ok
		and readiness_status == "Ready"
		and out_stage_status == "Complete"
	):
		overall = "Complete"

	return {
		"instance_code": code,
		"tender_code": tender_code,
		"overall_status": overall,
		"stages": stages,
		"outputs": outputs_map,
		"readiness_status": readiness_status,
	}
