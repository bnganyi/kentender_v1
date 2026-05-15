# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 / DERIVED-0400 — DOM source traces + pack §10 schema validation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_source_trace,
)
from kentender_procurement.tender_management.derived_models.dom.schema import (
	DOM_DISCLOSURE_STATUSES,
	DOM_FIELD_TYPES,
	DOM_KNOWN_TOP_LEVEL_KEYS,
	DOM_PACK_PROHIBITED_ACTIONS,
	DOM_PROHIBITED_KEYS,
	DOM_REGISTER_FIELD_ALLOWED_KEYS,
	DOM_SCHEMA_INVALID,
)


def _validate_optional_pack_top_level(payload: dict[str, Any]) -> None:
	if "opening_datetime" in payload and payload["opening_datetime"] is not None:
		od = payload["opening_datetime"]
		if not isinstance(od, str) or not od.strip():
			frappe.throw(
				_("DOM opening_datetime must be a non-empty string when set."),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	if "opening_location" in payload and payload["opening_location"] is not None:
		ol = payload["opening_location"]
		if not isinstance(ol, str) or not ol.strip():
			frappe.throw(
				_("DOM opening_location must be a non-empty string when set."),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	if "version_number" in payload and payload["version_number"] is not None:
		vn = payload["version_number"]
		if not isinstance(vn, int):
			frappe.throw(
				_("DOM version_number must be an integer when set."),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
	for key in ("output_code", "tender_code", "instance_code"):
		if key in payload and payload[key] is not None:
			val = payload[key]
			if not isinstance(val, str) or not val.strip():
				frappe.throw(
					_("DOM {0} must be a non-empty string when set.").format(key),
					title=DOM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)


def _assert_no_prohibited_keys(obj: Any, path: str) -> None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			ks = k if isinstance(k, str) else str(k)
			if ks in DOM_PROHIBITED_KEYS:
				frappe.throw(
					_("DOM must not include prohibited field {0} (at {1}).").format(ks, path),
					title=DOM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)
			_assert_no_prohibited_keys(v, f"{path}.{ks}")
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			_assert_no_prohibited_keys(v, f"{path}[{i}]")


def validate_dom_source_traces(payload: dict[str, Any]) -> None:
	"""Validate DOM ``content_json``: pack §10 shape, traces, prohibited evaluation/arithmetic keys."""
	for uk in payload.keys():
		if uk not in DOM_KNOWN_TOP_LEVEL_KEYS:
			frappe.throw(
				_("DOM content_json has unknown top-level key: {0}").format(uk),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

	for req_key in ("register_fields", "prohibited_actions"):
		if req_key not in payload:
			frappe.throw(
				_("DOM content_json must include {0}.").format(req_key),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

	_validate_optional_pack_top_level(payload)

	pa = payload["prohibited_actions"]
	if not isinstance(pa, list):
		frappe.throw(
			_("DOM prohibited_actions must be a list."),
			title=DOM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	pa_set: set[str] = set()
	for i, x in enumerate(pa):
		if not isinstance(x, str) or not x.strip():
			frappe.throw(
				_("DOM prohibited_actions[{0}] must be a non-empty string.").format(i),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		pa_set.add(x.strip())
	if pa_set != set(DOM_PACK_PROHIBITED_ACTIONS):
		frappe.throw(
			_("DOM prohibited_actions must match the pack §10 manifest exactly."),
			title=DOM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)

	fields = payload["register_fields"]
	if not isinstance(fields, list):
		frappe.throw(
			_("DOM register_fields must be a list."),
			title=DOM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)
	if len(fields) == 0:
		frappe.throw(
			_("DOM register_fields must not be empty."),
			title=DOM_SCHEMA_INVALID,
			exc=frappe.ValidationError,
		)

	seen_codes: set[str] = set()
	for i, row in enumerate(fields):
		path = f"register_fields[{i}]"
		if not isinstance(row, dict):
			frappe.throw(
				_("DOM {0} must be an object.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		for rk in row.keys():
			if rk not in DOM_REGISTER_FIELD_ALLOWED_KEYS:
				frappe.throw(
					_("DOM {0} has unknown key: {1}").format(path, rk),
					title=DOM_SCHEMA_INVALID,
					exc=frappe.ValidationError,
				)
		fc = row.get("field_code")
		if not isinstance(fc, str) or not fc.strip():
			frappe.throw(
				_("DOM {0}.field_code is required.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		fc_s = fc.strip()
		if fc_s in seen_codes:
			frappe.throw(
				_("DOM duplicate register field_code: {0}").format(fc_s),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)
		seen_codes.add(fc_s)

		lbl = row.get("label")
		if not isinstance(lbl, str) or not lbl.strip():
			frappe.throw(
				_("DOM {0}.label is required.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

		ft = row.get("field_type")
		if not isinstance(ft, str) or ft.strip() not in DOM_FIELD_TYPES:
			frappe.throw(
				_("DOM {0}.field_type is invalid.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

		if "mandatory" not in row or not isinstance(row.get("mandatory"), bool):
			frappe.throw(
				_("DOM {0}.mandatory must be a boolean.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

		ds = row.get("disclosure_status")
		if not isinstance(ds, str) or ds.strip() not in DOM_DISCLOSURE_STATUSES:
			frappe.throw(
				_("DOM {0}.disclosure_status is invalid.").format(path),
				title=DOM_SCHEMA_INVALID,
				exc=frappe.ValidationError,
			)

		trace = row.get("source_trace")
		if trace is None:
			frappe.throw(
				_("DOM {0} is missing source_trace.").format(path),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		validate_source_trace(trace)

	_assert_no_prohibited_keys(payload, "$")
