# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 / DERIVED-0500 — DEM source traces + pack §11 schema validation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_source_trace,
)
from kentender_procurement.tender_management.derived_models.dem.schema import (
	DEM_BOQ_ARITHMETIC_ALLOWED_KEYS,
	DEM_CORRECTION_RULE_ALLOWED_KEYS,
	DEM_FAILURE_EFFECTS,
	DEM_KNOWN_TOP_LEVEL_KEYS,
	DEM_PROHIBITED_KEYS,
	DEM_RANKING_ALLOWED_KEYS,
	DEM_RANKING_METHODS,
	DEM_RULE_ALLOWED_KEYS,
	DEM_RULE_TYPES,
	DEM_SCHEMA_INVALID,
	DEM_STAGE_ALLOWED_KEYS,
	DEM_STAGE_TYPES,
	DEM_STD_TRACE_ANCHOR_KEYS,
)


def dem_trace_references_std(trace: dict[str, Any]) -> bool:
	"""True when trace ties content to STD (§9.11) or an explicit SystemRule mapping."""
	st = (trace.get("source_type") or "").strip()
	if st == "SystemRule":
		return bool((trace.get("mapping_code") or "").strip())
	return any(bool((trace.get(k) or "").strip()) for k in DEM_STD_TRACE_ANCHOR_KEYS)


def _throw_schema(msg: str) -> None:
	frappe.throw(msg, title=DEM_SCHEMA_INVALID, exc=frappe.ValidationError)


def _assert_no_prohibited_keys(obj: Any, path: str) -> None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			ks = k if isinstance(k, str) else str(k)
			if ks in DEM_PROHIBITED_KEYS:
				_throw_schema(_("DEM must not include prohibited field {0} (at {1}).").format(ks, path))
			_assert_no_prohibited_keys(v, f"{path}.{ks}")
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			_assert_no_prohibited_keys(v, f"{path}[{i}]")


def _validate_optional_pack_top_level(payload: dict[str, Any]) -> None:
	for key in ("output_code", "tender_code", "instance_code"):
		if key in payload and payload[key] is not None:
			val = payload[key]
			if not isinstance(val, str) or not val.strip():
				_throw_schema(_("DEM {0} must be a non-empty string when set.").format(key))
	if "version_number" in payload and payload["version_number"] is not None:
		vn = payload["version_number"]
		if not isinstance(vn, int):
			_throw_schema(_("DEM version_number must be an integer when set."))


def _validate_threshold_value(raw: Any, path: str) -> None:
	if raw is None:
		return
	if isinstance(raw, (str, int, float, bool)):
		return
	if isinstance(raw, list):
		for i, x in enumerate(raw):
			_validate_threshold_value(x, f"{path}[{i}]")
		return
	if isinstance(raw, dict):
		for k, v in raw.items():
			_assert_no_prohibited_keys(v, f"{path}.{k}")
			_validate_threshold_value(v, f"{path}.{k}")
		return
	_throw_schema(_("DEM {0}.threshold_value has invalid JSON type.").format(path))


def _validate_rule(rule: dict[str, Any], *, si: int, ri: int) -> None:
	path = f"stages[{si}].rules[{ri}]"
	for rk in rule.keys():
		if rk not in DEM_RULE_ALLOWED_KEYS:
			_throw_schema(_("DEM {0} has unknown key: {1}").format(path, rk))
	rc = rule.get("rule_code")
	if not isinstance(rc, str) or not rc.strip():
		_throw_schema(_("DEM {0}.rule_code is required.").format(path))
	rt = rule.get("rule_type")
	if not isinstance(rt, str) or rt.strip() not in DEM_RULE_TYPES:
		_throw_schema(_("DEM {0}.rule_type is invalid.").format(path))
	lbl = rule.get("label")
	if not isinstance(lbl, str) or not lbl.strip():
		_throw_schema(_("DEM {0}.label is required.").format(path))
	if "description" in rule and rule["description"] is not None:
		d = rule["description"]
		if not isinstance(d, str):
			_throw_schema(_("DEM {0}.description must be a string when set.").format(path))
	ds = rule.get("data_source")
	if not isinstance(ds, str) or not ds.strip():
		_throw_schema(_("DEM {0}.data_source is required.").format(path))
	if "operator" in rule and rule["operator"] is not None:
		op = rule["operator"]
		if not isinstance(op, str) or not op.strip():
			_throw_schema(_("DEM {0}.operator must be a non-empty string when set.").format(path))
	if "threshold_value" in rule:
		_validate_threshold_value(rule.get("threshold_value"), path)
	fe = rule.get("failure_effect")
	if not isinstance(fe, str) or fe.strip() not in DEM_FAILURE_EFFECTS:
		_throw_schema(_("DEM {0}.failure_effect is invalid.").format(path))
	trace = rule.get("source_trace")
	if trace is None:
		frappe.throw(
			_("DEM {0} is missing source_trace.").format(path),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	vt = validate_source_trace(trace)
	if not dem_trace_references_std(vt):
		_throw_schema(
			_("DEM {0}.source_trace must reference STD content or a named SystemRule mapping.").format(path),
		)


def _validate_stage(stage: dict[str, Any], *, si: int) -> None:
	path = f"stages[{si}]"
	for sk in stage.keys():
		if sk not in DEM_STAGE_ALLOWED_KEYS:
			_throw_schema(_("DEM {0} has unknown key: {1}").format(path, sk))
	sc = stage.get("stage_code")
	if not isinstance(sc, str) or not sc.strip():
		_throw_schema(_("DEM {0}.stage_code is required.").format(path))
	sn = stage.get("stage_name")
	if not isinstance(sn, str) or not sn.strip():
		_throw_schema(_("DEM {0}.stage_name is required.").format(path))
	seq = stage.get("sequence")
	if not isinstance(seq, int):
		_throw_schema(_("DEM {0}.sequence must be an integer.").format(path))
	stt = stage.get("stage_type")
	if not isinstance(stt, str) or stt.strip() not in DEM_STAGE_TYPES:
		_throw_schema(_("DEM {0}.stage_type is invalid.").format(path))
	if "mandatory" not in stage or not isinstance(stage.get("mandatory"), bool):
		_throw_schema(_("DEM {0}.mandatory must be a boolean.").format(path))
	rules = stage.get("rules")
	if not isinstance(rules, list):
		_throw_schema(_("DEM {0}.rules must be a list.").format(path))
	if len(rules) == 0:
		_throw_schema(_("DEM {0}.rules must not be empty.").format(path))
	for ri, rule in enumerate(rules):
		if not isinstance(rule, dict):
			_throw_schema(_("DEM {0}.rules[{1}] must be an object.").format(path, ri))
		_validate_rule(rule, si=si, ri=ri)


def _validate_boq_arithmetic(block: Any) -> None:
	path = "boq_arithmetic_correction"
	if not isinstance(block, dict):
		_throw_schema(_("DEM boq_arithmetic_correction must be an object."))
	for bk in block.keys():
		if bk not in DEM_BOQ_ARITHMETIC_ALLOWED_KEYS:
			_throw_schema(_("DEM boq_arithmetic_correction has unknown key: {0}").format(bk))
	if "enabled" not in block or not isinstance(block.get("enabled"), bool):
		_throw_schema(_("DEM boq_arithmetic_correction.enabled must be a boolean."))
	sc = block.get("stage_code")
	if not isinstance(sc, str) or not sc.strip():
		_throw_schema(_("DEM boq_arithmetic_correction.stage_code is required."))
	crs = block.get("correction_rules")
	if not isinstance(crs, list):
		_throw_schema(_("DEM boq_arithmetic_correction.correction_rules must be a list."))
	enabled = bool(block.get("enabled"))
	if enabled and len(crs) == 0:
		_throw_schema(_("DEM boq_arithmetic_correction.correction_rules must not be empty when enabled."))
	for ci, row in enumerate(crs):
		cp = f"{path}.correction_rules[{ci}]"
		if not isinstance(row, dict):
			_throw_schema(_("DEM {0} must be an object.").format(cp))
		for ck in row.keys():
			if ck not in DEM_CORRECTION_RULE_ALLOWED_KEYS:
				_throw_schema(_("DEM {0} has unknown key: {1}").format(cp, ck))
		rc = row.get("rule_code")
		if not isinstance(rc, str) or not rc.strip():
			_throw_schema(_("DEM {0}.rule_code is required.").format(cp))
		lbl = row.get("label")
		if not isinstance(lbl, str) or not lbl.strip():
			_throw_schema(_("DEM {0}.label is required.").format(cp))
		if "description" in row and row["description"] is not None:
			d = row["description"]
			if not isinstance(d, str):
				_throw_schema(_("DEM {0}.description must be a string when set.").format(cp))
		tr = row.get("source_trace")
		if tr is None:
			frappe.throw(
				_("DEM {0} is missing source_trace.").format(cp),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		vt = validate_source_trace(tr)
		if not dem_trace_references_std(vt):
			_throw_schema(
				_("DEM {0}.source_trace must reference STD content or a named SystemRule mapping.").format(cp),
			)


def _validate_ranking(block: Any) -> None:
	if not isinstance(block, dict):
		_throw_schema(_("DEM ranking must be an object."))
	for rk in block.keys():
		if rk not in DEM_RANKING_ALLOWED_KEYS:
			_throw_schema(_("DEM ranking has unknown key: {0}").format(rk))
	m = block.get("method")
	if not isinstance(m, str) or m.strip() not in DEM_RANKING_METHODS:
		_throw_schema(_("DEM ranking.method is invalid."))
	rt = block.get("source_trace")
	if rt is None:
		frappe.throw(
			_("DEM ranking is missing source_trace."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	vt = validate_source_trace(rt)
	if not dem_trace_references_std(vt):
		_throw_schema(_("DEM ranking.source_trace must reference STD content or a named SystemRule mapping."))


def validate_dem_source_traces(payload: dict[str, Any]) -> None:
	"""Validate DEM ``content_json``: pack §11 shape, traces, STD traceability, prohibited keys."""
	for uk in payload.keys():
		if uk not in DEM_KNOWN_TOP_LEVEL_KEYS:
			_throw_schema(_("DEM content_json has unknown top-level key: {0}").format(uk))

	for req in (
		"evaluation_method",
		"stages",
		"boq_arithmetic_correction",
		"ranking",
	):
		if req not in payload:
			_throw_schema(_("DEM content_json must include {0}.").format(req))

	_validate_optional_pack_top_level(payload)

	em = payload["evaluation_method"]
	if not isinstance(em, str) or not em.strip():
		_throw_schema(_("DEM evaluation_method is required."))

	stages = payload["stages"]
	if not isinstance(stages, list):
		_throw_schema(_("DEM stages must be a list."))
	if len(stages) == 0:
		_throw_schema(_("DEM stages must not be empty."))

	seen_stage_codes: set[str] = set()
	for si, stage in enumerate(stages):
		if not isinstance(stage, dict):
			_throw_schema(_("DEM stages[{0}] must be an object.").format(si))
		_validate_stage(stage, si=si)
		scc = (stage.get("stage_code") or "").strip()
		if scc in seen_stage_codes:
			_throw_schema(_("DEM duplicate stage_code: {0}").format(scc))
		seen_stage_codes.add(scc)

	_validate_boq_arithmetic(payload["boq_arithmetic_correction"])
	_validate_ranking(payload["ranking"])

	_assert_no_prohibited_keys(payload, "$")
