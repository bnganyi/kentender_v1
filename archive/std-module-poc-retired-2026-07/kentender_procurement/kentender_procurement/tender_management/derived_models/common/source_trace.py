# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0110 — Source trace schema and validation (pack §6).

Does not import ``generated_output`` (avoid cycles). Per-type validators are
imported lazily inside ``validate_derived_output_source_traces``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import frappe
from frappe import _

# Stable title for ValidationError and tracker §4
DERIVED_SOURCE_TRACE_MISSING = "DERIVED_SOURCE_TRACE_MISSING"

SOURCE_TRACE_TYPES: frozenset[str] = frozenset(
	{
		"Section",
		"Clause",
		"Parameter",
		"Form",
		"BOQ",
		"WorksRequirement",
		"Drawing",
		"Attachment",
		"EvaluationResult",
		"Addendum",
		"SystemRule",
	}
)

_OPTIONAL_TRACE_STRING_KEYS: frozenset[str] = frozenset(
	{
		"source_section_code",
		"source_clause_code",
		"source_parameter_code",
		"source_form_code",
		"source_boq_item_code",
		"source_component_code",
		"source_addendum_code",
		"mapping_code",
	}
)


def validate_source_trace(obj: Any) -> dict[str, Any]:
	"""Validate ``source_trace`` object shape; return normalized dict."""
	if not isinstance(obj, Mapping):
		frappe.throw(
			_("source_trace must be an object."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	raw: dict[str, Any] = dict(obj)
	st = (raw.get("source_type") or "").strip()
	if not st:
		frappe.throw(
			_("source_trace.source_type is required."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	if st not in SOURCE_TRACE_TYPES:
		frappe.throw(
			_("source_trace.source_type {0} is not allowed.").format(st),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	for key in raw:
		if key == "source_type":
			continue
		if key not in _OPTIONAL_TRACE_STRING_KEYS:
			frappe.throw(
				_("source_trace has unknown key: {0}").format(key),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		val = raw[key]
		if val is not None and not isinstance(val, str):
			frappe.throw(
				_("source_trace.{0} must be a string.").format(key),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
	return raw


def validate_derived_output_source_traces(output_type: str, content: Any) -> None:
	"""Validate per-element ``source_trace`` for Bundle, DSM, DOM, DEM, DCM."""
	ot = (output_type or "").strip()
	if not isinstance(content, dict):
		frappe.throw(
			_("Generated output content_json must be an object for trace validation."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	# Lazy imports avoid circular dependency with per-type validators.
	if ot == "Bundle":
		from kentender_procurement.tender_management.derived_models.bundle.validator import (
			validate_bundle_source_traces,
		)

		validate_bundle_source_traces(content)
	elif ot == "DSM":
		from kentender_procurement.tender_management.derived_models.dsm.validator import (
			validate_dsm_source_traces,
		)

		validate_dsm_source_traces(content)
	elif ot == "DOM":
		from kentender_procurement.tender_management.derived_models.dom.validator import (
			validate_dom_source_traces,
		)

		validate_dom_source_traces(content)
	elif ot == "DEM":
		from kentender_procurement.tender_management.derived_models.dem.validator import (
			validate_dem_source_traces,
		)

		validate_dem_source_traces(content)
	elif ot == "DCM":
		from kentender_procurement.tender_management.derived_models.dcm.validator import (
			validate_dcm_source_traces,
		)

		validate_dcm_source_traces(content)
