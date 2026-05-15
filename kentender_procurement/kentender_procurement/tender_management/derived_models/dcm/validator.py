# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 / DERIVED-0600 — DCM source traces + pack §12 schema validation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_source_trace,
)
from kentender_procurement.tender_management.derived_models.dcm.schema import (
	DCM_CONTRACT_DOCUMENT_ALLOWED_KEYS,
	DCM_CONTRACT_TERM_ALLOWED_KEYS,
	DCM_KNOWN_TOP_LEVEL_KEYS,
	DCM_MANUAL_PRICE_OVERRIDE_DENIED,
	DCM_PRICE_SOURCE_ALLOWED_KEYS,
	DCM_PRICE_SOURCE_TYPES,
	DCM_PROHIBITED_KEYS,
	DCM_SCHEMA_INVALID,
	DCM_SECURITIES_ALLOWED_KEYS,
	DCM_WORKS_SCOPE_ALLOWED_KEYS,
)


def _throw_schema(msg: str) -> None:
	frappe.throw(msg, title=DCM_SCHEMA_INVALID, exc=frappe.ValidationError)


def _throw_price_denial(msg: str) -> None:
	frappe.throw(msg, title=DCM_MANUAL_PRICE_OVERRIDE_DENIED, exc=frappe.ValidationError)


def _assert_no_prohibited_keys(obj: Any, path: str) -> None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			ks = k if isinstance(k, str) else str(k)
			if ks in DCM_PROHIBITED_KEYS:
				_throw_schema(_("DCM must not include prohibited field {0} (at {1}).").format(ks, path))
			_assert_no_prohibited_keys(v, f"{path}.{ks}")
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			_assert_no_prohibited_keys(v, f"{path}[{i}]")


def _validate_optional_pack_top_level(payload: dict[str, Any]) -> None:
	for key in ("output_code", "tender_code", "instance_code"):
		if key in payload and payload[key] is not None:
			val = payload[key]
			if not isinstance(val, str) or not val.strip():
				_throw_schema(_("DCM {0} must be a non-empty string when set.").format(key))
	if "version_number" in payload and payload["version_number"] is not None:
		vn = payload["version_number"]
		if not isinstance(vn, int):
			_throw_schema(_("DCM version_number must be an integer when set."))

	# Pack §19 — optional commercial scalars (typically emitted together for Works + BOQ).
	for day_key in ("completion_period_days", "defects_liability_period_days"):
		if day_key not in payload or payload[day_key] is None:
			continue
		dv = payload[day_key]
		if isinstance(dv, bool) or not isinstance(dv, int):
			_throw_schema(_("DCM {0} must be a positive integer when set.").format(day_key))
		if dv < 1 or dv > 50000:
			_throw_schema(_("DCM {0} is out of allowed range.").format(day_key))
	for pct_key in ("performance_security_percent", "retention_percent"):
		if pct_key not in payload or payload[pct_key] is None:
			continue
		pv = payload[pct_key]
		if isinstance(pv, bool) or not isinstance(pv, (int, float)):
			_throw_schema(_("DCM {0} must be a number when set.").format(pct_key))
		pf = float(pv)
		if pf < 0.0 or pf > 100.0:
			_throw_schema(_("DCM {0} must be between 0 and 100.").format(pct_key))


def _validate_value_json(val: Any, path: str) -> None:
	if val is None:
		return
	if isinstance(val, (str, int, float, bool)):
		return
	if isinstance(val, list):
		for i, x in enumerate(val):
			_validate_value_json(x, f"{path}[{i}]")
		return
	if isinstance(val, dict):
		_assert_no_prohibited_keys(val, path)
		for k, v in val.items():
			_validate_value_json(v, f"{path}.{k}")
		return
	_throw_schema(_("DCM {0} has invalid JSON value type.").format(path))


def _validate_contract_document(row: dict[str, Any], i: int) -> None:
	path = f"contract_documents[{i}]"
	for rk in row.keys():
		if rk not in DCM_CONTRACT_DOCUMENT_ALLOWED_KEYS:
			_throw_schema(_("DCM {0} has unknown key: {1}").format(path, rk))
	dc = row.get("document_code")
	if not isinstance(dc, str) or not dc.strip():
		_throw_schema(_("DCM {0}.document_code is required.").format(path))
	lbl = row.get("label")
	if not isinstance(lbl, str) or not lbl.strip():
		_throw_schema(_("DCM {0}.label is required.").format(path))
	if "description" in row and row["description"] is not None:
		d = row["description"]
		if not isinstance(d, str):
			_throw_schema(_("DCM {0}.description must be a string when set.").format(path))
	trace = row.get("source_trace")
	if trace is None:
		frappe.throw(
			_("DCM {0} is missing source_trace.").format(path),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	validate_source_trace(trace)


def _validate_contract_term(row: dict[str, Any], i: int) -> None:
	path = f"contract_terms[{i}]"
	for rk in row.keys():
		if rk not in DCM_CONTRACT_TERM_ALLOWED_KEYS:
			_throw_schema(_("DCM {0} has unknown key: {1}").format(path, rk))
	tc = row.get("term_code")
	if not isinstance(tc, str) or not tc.strip():
		_throw_schema(_("DCM {0}.term_code is required.").format(path))
	lbl = row.get("label")
	if not isinstance(lbl, str) or not lbl.strip():
		_throw_schema(_("DCM {0}.label is required.").format(path))
	if "value" not in row:
		_throw_schema(_("DCM {0}.value is required.").format(path))
	_validate_value_json(row.get("value"), f"{path}.value")
	if "editable_in_contract" not in row or not isinstance(row.get("editable_in_contract"), bool):
		_throw_schema(_("DCM {0}.editable_in_contract must be a boolean.").format(path))
	if "description" in row and row["description"] is not None:
		d = row["description"]
		if not isinstance(d, str):
			_throw_schema(_("DCM {0}.description must be a string when set.").format(path))
	trace = row.get("source_trace")
	if trace is None:
		frappe.throw(
			_("DCM {0} is missing source_trace.").format(path),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	validate_source_trace(trace)


def _validate_price_source(payload: dict[str, Any], ps: Any) -> None:
	path = "price_source"
	if not isinstance(ps, dict):
		_throw_schema(_("DCM price_source must be an object."))
	for pk in ps.keys():
		if pk not in DCM_PRICE_SOURCE_ALLOWED_KEYS:
			_throw_schema(_("DCM price_source has unknown key: {0}").format(pk))
	st = ps.get("source_type")
	if not isinstance(st, str) or st.strip() not in DCM_PRICE_SOURCE_TYPES:
		_throw_schema(_("DCM price_source.source_type is invalid."))
	if "manual_override_allowed" not in ps or not isinstance(ps.get("manual_override_allowed"), bool):
		_throw_schema(_("DCM price_source.manual_override_allowed must be a boolean."))
	for ok in ("source_output_code", "source_evaluation_result_code"):
		if ok in ps and ps[ok] is not None:
			v = ps[ok]
			if not isinstance(v, str) or not v.strip():
				_throw_schema(_("DCM price_source.{0} must be a non-empty string when set.").format(ok))

	if payload.get("has_boq") is True:
		if ps.get("source_type") != "CorrectedEvaluatedBOQTotal":
			_throw_price_denial(
				_("Works BOQ tenders must use CorrectedEvaluatedBOQTotal as the contract price source."),
			)
		if ps.get("manual_override_allowed") is not False:
			_throw_price_denial(
				_("Manual contract price override is not allowed for Works BOQ tenders."),
			)


def _validate_securities(block: Any) -> None:
	if block is None:
		return
	if not isinstance(block, dict):
		_throw_schema(_("DCM securities must be an object."))
	for k in block.keys():
		if k not in DCM_SECURITIES_ALLOWED_KEYS:
			_throw_schema(_("DCM securities has unknown key: {0}").format(k))
	for sk in DCM_SECURITIES_ALLOWED_KEYS:
		if sk not in block:
			continue
		val = block.get(sk)
		if val is None:
			continue
		if not isinstance(val, dict):
			_throw_schema(_("DCM securities.{0} must be an object when set.").format(sk))
		_assert_no_prohibited_keys(val, f"securities.{sk}")


def _validate_works_scope(ws: Any) -> None:
	path = "works_scope_references"
	if not isinstance(ws, dict):
		_throw_schema(_("DCM works_scope_references must be an object."))
	for k in ws.keys():
		if k not in DCM_WORKS_SCOPE_ALLOWED_KEYS:
			_throw_schema(_("DCM {0} has unknown key: {1}").format(path, k))
	specs = ws.get("specifications")
	if not isinstance(specs, list):
		_throw_schema(_("DCM works_scope_references.specifications must be a list."))
	for i, x in enumerate(specs):
		if isinstance(x, str):
			if not x.strip():
				_throw_schema(_("DCM works_scope_references.specifications[{0}] must be non-empty.").format(i))
		elif isinstance(x, dict):
			_assert_no_prohibited_keys(x, f"{path}.specifications[{i}]")
		else:
			_throw_schema(_("DCM works_scope_references.specifications[{0}] must be a string or object.").format(i))

	drawings = ws.get("drawings")
	if not isinstance(drawings, list):
		_throw_schema(_("DCM works_scope_references.drawings must be a list."))
	for i, x in enumerate(drawings):
		if isinstance(x, str):
			if not x.strip():
				_throw_schema(_("DCM works_scope_references.drawings[{0}] must be non-empty.").format(i))
		elif isinstance(x, dict):
			_assert_no_prohibited_keys(x, f"{path}.drawings[{i}]")
		else:
			_throw_schema(_("DCM works_scope_references.drawings[{0}] must be a string or object.").format(i))

	boq = ws.get("boq")
	if not isinstance(boq, dict):
		_throw_schema(_("DCM works_scope_references.boq must be an object."))
	_assert_no_prohibited_keys(boq, f"{path}.boq")


def validate_dcm_source_traces(payload: dict[str, Any]) -> None:
	"""Validate DCM ``content_json``: pack §12 shape, traces, Works BOQ price rules, prohibited keys."""
	for uk in payload.keys():
		if uk not in DCM_KNOWN_TOP_LEVEL_KEYS:
			_throw_schema(_("DCM content_json has unknown top-level key: {0}").format(uk))

	for req in ("contract_documents", "contract_terms", "price_source", "works_scope_references"):
		if req not in payload:
			_throw_schema(_("DCM content_json must include {0}.").format(req))

	_validate_optional_pack_top_level(payload)

	docs = payload["contract_documents"]
	if not isinstance(docs, list):
		_throw_schema(_("DCM contract_documents must be a list."))
	if len(docs) == 0:
		_throw_schema(_("DCM contract_documents must not be empty."))
	seen_doc: set[str] = set()
	for i, row in enumerate(docs):
		if not isinstance(row, dict):
			_throw_schema(_("DCM contract_documents[{0}] must be an object.").format(i))
		_validate_contract_document(row, i)
		dc = (row.get("document_code") or "").strip()
		if dc in seen_doc:
			_throw_schema(_("DCM duplicate document_code: {0}").format(dc))
		seen_doc.add(dc)

	terms = payload["contract_terms"]
	if not isinstance(terms, list):
		_throw_schema(_("DCM contract_terms must be a list."))
	if len(terms) == 0:
		_throw_schema(_("DCM contract_terms must not be empty."))
	seen_term: set[str] = set()
	for i, row in enumerate(terms):
		if not isinstance(row, dict):
			_throw_schema(_("DCM contract_terms[{0}] must be an object.").format(i))
		_validate_contract_term(row, i)
		tc = (row.get("term_code") or "").strip()
		if tc in seen_term:
			_throw_schema(_("DCM duplicate term_code: {0}").format(tc))
		seen_term.add(tc)

	_validate_price_source(payload, payload["price_source"])

	if "securities" in payload:
		_validate_securities(payload["securities"])

	_validate_works_scope(payload["works_scope_references"])

	_assert_no_prohibited_keys(payload, "$")
