# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 / DERIVED-0300 — DSM source traces + pack §9 schema validation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_source_trace,
)
from kentender_procurement.tender_management.derived_models.dsm.schema import (
	DSM_ADDENDUM_ACK_ALLOWED_KEYS,
	DSM_BOQ_RATE_COMPUTED_FIELDS,
	DSM_BOQ_RATE_EDITABLE_FIELDS,
	DSM_BOQ_RATE_ENTRY_ALLOWED_KEYS,
	DSM_BOQ_RATE_LOCKED_FIELDS,
	DSM_KNOWN_TOP_LEVEL_KEYS,
	DSM_PROHIBITED_KEYS,
	DSM_REQUIREMENT_ALLOWED_KEYS,
	DSM_REQUIREMENT_TYPES,
	DSM_SCHEMA_INVALID,
	DSM_SUPPLIER_ACTIONS,
)


def _norm_str_list(label: str, raw: Any, *, path: str) -> list[str]:
	if not isinstance(raw, list):
		frappe.throw(
			_("DSM {0} must be a list ({1}).").format(label, path),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	out: list[str] = []
	for i, x in enumerate(raw):
		if not isinstance(x, str) or not x.strip():
			frappe.throw(
				_("DSM {0}[{1}] must be a non-empty string ({2}).").format(label, i, path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		out.append(x.strip())
	return out


def _assert_field_sets(
	*,
	editable: list[str],
	locked: list[str],
	computed: list[str],
	path: str,
) -> None:
	e_set = set(editable)
	l_set = set(locked)
	c_set = set(computed)
	if e_set != DSM_BOQ_RATE_EDITABLE_FIELDS:
		frappe.throw(
			_("DSM boq_rate_entry editable_fields must match pack §9 ({0}).").format(path),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	if l_set != DSM_BOQ_RATE_LOCKED_FIELDS:
		frappe.throw(
			_("DSM boq_rate_entry locked_fields must match pack §9 ({0}).").format(path),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	if c_set != DSM_BOQ_RATE_COMPUTED_FIELDS:
		frappe.throw(
			_("DSM boq_rate_entry computed_fields must match pack §9 ({0}).").format(path),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)


def _assert_no_prohibited_keys(obj: Any, path: str) -> None:
	"""Reject pack §9 prohibited concepts (keys) anywhere in the DSM JSON tree."""
	if isinstance(obj, dict):
		for k, v in obj.items():
			ks = k if isinstance(k, str) else str(k)
			if ks in DSM_PROHIBITED_KEYS:
				frappe.throw(
					_("DSM must not include prohibited field {0} (at {1}).").format(ks, path),
					title=DSM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)
			_assert_no_prohibited_keys(v, f"{path}.{ks}")
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			_assert_no_prohibited_keys(v, f"{path}[{i}]")


def _validate_optional_pack_top_level(payload: dict[str, Any]) -> None:
	if "submission_deadline" in payload and payload["submission_deadline"] is not None:
		sd = payload["submission_deadline"]
		if not isinstance(sd, str) or not sd.strip():
			frappe.throw(
				_("DSM submission_deadline must be a non-empty string when set."),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	if "submission_mode" in payload and payload["submission_mode"] is not None:
		sm = payload["submission_mode"]
		if not isinstance(sm, str) or not sm.strip():
			frappe.throw(
				_("DSM submission_mode must be a non-empty string when set."),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	if "version_number" in payload and payload["version_number"] is not None:
		vn = payload["version_number"]
		if not isinstance(vn, int):
			frappe.throw(
				_("DSM version_number must be an integer when set."),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	for key in ("output_code", "tender_code", "instance_code"):
		if key in payload and payload[key] is not None:
			val = payload[key]
			if not isinstance(val, str) or not val.strip():
				frappe.throw(
					_("DSM {0} must be a non-empty string when set.").format(key),
					title=DSM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)


def validate_dsm_source_traces(payload: dict[str, Any]) -> None:
	"""Validate DSM ``content_json``: pack §9 shape, traces, and prohibited evaluation content."""
	for uk in payload.keys():
		if uk not in DSM_KNOWN_TOP_LEVEL_KEYS:
			frappe.throw(
				_("DSM content_json has unknown top-level key: {0}").format(uk),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

	for req_key in ("requirements", "boq_rate_entry", "addendum_acknowledgements"):
		if req_key not in payload:
			frappe.throw(
				_("DSM content_json must include {0}.").format(req_key),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

	_validate_optional_pack_top_level(payload)

	req = payload["requirements"]
	if not isinstance(req, list):
		frappe.throw(
			_("DSM requirements must be a list."),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	if len(req) == 0:
		frappe.throw(
			_("DSM requirements must not be empty."),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)

	for i, row in enumerate(req):
		path = f"requirements[{i}]"
		if not isinstance(row, dict):
			frappe.throw(
				_("DSM {0} must be an object.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		for rk in row.keys():
			if rk not in DSM_REQUIREMENT_ALLOWED_KEYS:
				frappe.throw(
					_("DSM {0} has unknown key: {1}").format(path, rk),
					title=DSM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)
		rc = row.get("requirement_code")
		if not isinstance(rc, str) or not rc.strip():
			frappe.throw(
				_("DSM {0}.requirement_code is required.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		rt = row.get("requirement_type")
		if not isinstance(rt, str) or rt.strip() not in DSM_REQUIREMENT_TYPES:
			frappe.throw(
				_("DSM {0}.requirement_type is invalid.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		lbl = row.get("label")
		if not isinstance(lbl, str) or not lbl.strip():
			frappe.throw(
				_("DSM {0}.label is required.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		if "mandatory" not in row or not isinstance(row.get("mandatory"), bool):
			frappe.throw(
				_("DSM {0}.mandatory must be a boolean.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		sa = row.get("supplier_action")
		if not isinstance(sa, str) or sa.strip() not in DSM_SUPPLIER_ACTIONS:
			frappe.throw(
				_("DSM {0}.supplier_action is invalid.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		desc = row.get("description")
		if desc is not None and not isinstance(desc, str):
			frappe.throw(
				_("DSM {0}.description must be a string when set.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		vrc = row.get("validation_rule_code")
		if vrc is not None and (not isinstance(vrc, str) or not vrc.strip()):
			frappe.throw(
				_("DSM {0}.validation_rule_code must be a non-empty string when set.").format(path),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		trace = row.get("source_trace")
		if trace is None:
			frappe.throw(
				_("DSM {0} is missing source_trace.").format(path),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		validate_source_trace(trace)

	bqe = payload["boq_rate_entry"]
	path_bqe = "boq_rate_entry"
	if not isinstance(bqe, dict):
		frappe.throw(
			_("DSM boq_rate_entry must be an object."),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	for bk in bqe.keys():
		if bk not in DSM_BOQ_RATE_ENTRY_ALLOWED_KEYS:
			frappe.throw(
				_("DSM boq_rate_entry has unknown key: {0}").format(bk),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	if "enabled" not in bqe or not isinstance(bqe.get("enabled"), bool):
		frappe.throw(
			_("DSM boq_rate_entry.enabled must be a boolean."),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	editable = _norm_str_list("editable_fields", bqe.get("editable_fields"), path=path_bqe)
	locked = _norm_str_list("locked_fields", bqe.get("locked_fields"), path=path_bqe)
	computed = _norm_str_list("computed_fields", bqe.get("computed_fields"), path=path_bqe)
	_assert_field_sets(editable=editable, locked=locked, computed=computed, path=path_bqe)

	acks = payload["addendum_acknowledgements"]
	if not isinstance(acks, list):
		frappe.throw(
			_("DSM addendum_acknowledgements must be a list."),
			title=DSM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	for i, row in enumerate(acks):
		ap = f"addendum_acknowledgements[{i}]"
		if not isinstance(row, dict):
			frappe.throw(
				_("DSM {0} must be an object.").format(ap),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		for ak in row.keys():
			if ak not in DSM_ADDENDUM_ACK_ALLOWED_KEYS:
				frappe.throw(
					_("DSM {0} has unknown key: {1}").format(ap, ak),
					title=DSM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)
		ac = row.get("addendum_code")
		if not isinstance(ac, str) or not ac.strip():
			frappe.throw(
				_("DSM {0}.addendum_code is required.").format(ap),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		if "mandatory" not in row or not isinstance(row.get("mandatory"), bool):
			frappe.throw(
				_("DSM {0}.mandatory must be a boolean.").format(ap),
				title=DSM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

	_assert_no_prohibited_keys(payload, "$")
