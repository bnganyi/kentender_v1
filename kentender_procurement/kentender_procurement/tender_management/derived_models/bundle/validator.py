# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0200 — Bundle ``content_json`` source trace validation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.bundle.schema import BUNDLE_SECTION_CODES
from kentender_procurement.tender_management.derived_models.common.source_trace import (
	DERIVED_SOURCE_TRACE_MISSING,
	validate_source_trace,
)


def validate_bundle_source_traces(payload: dict[str, Any]) -> None:
	"""Require pack §8 top-level keys, outline parity, and per-section ``source_trace``."""
	for key in ("document_outline", "sections", "attachments", "placeholder_status"):
		if key not in payload:
			frappe.throw(
				_("Bundle content_json must include {0}.").format(key),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)

	outline = payload.get("document_outline")
	sections = payload.get("sections")
	attachments = payload.get("attachments")
	ph = payload.get("placeholder_status")

	if not isinstance(outline, list):
		frappe.throw(
			_("Bundle document_outline must be a list."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	if not isinstance(sections, list):
		frappe.throw(
			_("Bundle sections must be a list."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	if not isinstance(attachments, list):
		frappe.throw(
			_("Bundle attachments must be a list."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	if not isinstance(ph, dict):
		frappe.throw(
			_("Bundle placeholder_status must be an object."),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)

	if len(outline) != len(BUNDLE_SECTION_CODES):
		frappe.throw(
			_("Bundle document_outline must have length {0}.").format(len(BUNDLE_SECTION_CODES)),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)
	for oi, code in enumerate(BUNDLE_SECTION_CODES):
		orow = outline[oi]
		if not isinstance(orow, dict):
			frappe.throw(
				_("Bundle document_outline[{0}] must be an object.").format(oi),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		if (orow.get("section_code") or "").strip() != code:
			frappe.throw(
				_("Bundle document_outline[{0}] must have section_code {1}.").format(oi, code),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)

	if len(sections) != len(BUNDLE_SECTION_CODES):
		frappe.throw(
			_("Bundle must include exactly {0} sections.").format(len(BUNDLE_SECTION_CODES)),
			title=DERIVED_SOURCE_TRACE_MISSING,
			exc=frappe.ValidationError,
		)

	for i, code in enumerate(BUNDLE_SECTION_CODES):
		row = sections[i]
		if not isinstance(row, dict):
			frappe.throw(
				_("Bundle sections[{0}] must be an object.").format(i),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		if (row.get("section_code") or "").strip() != code:
			frappe.throw(
				_("Bundle sections[{0}] must have section_code {1}.").format(i, code),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		trace = row.get("source_trace")
		if trace is None:
			frappe.throw(
				_("Bundle sections[{0}] is missing source_trace.").format(i),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		validate_source_trace(trace)

		components = row.get("components")
		if components is not None:
			if not isinstance(components, list):
				frappe.throw(
					_("Bundle sections[{0}].components must be a list.").format(i),
					title=DERIVED_SOURCE_TRACE_MISSING,
					exc=frappe.ValidationError,
				)
			for ci, comp in enumerate(components):
				if not isinstance(comp, dict):
					frappe.throw(
						_("Bundle sections[{0}].components[{1}] must be an object.").format(i, ci),
						title=DERIVED_SOURCE_TRACE_MISSING,
						exc=frappe.ValidationError,
					)
				ct = comp.get("source_trace")
				if ct is None:
					frappe.throw(
						_("Bundle sections[{0}].components[{1}] is missing source_trace.").format(i, ci),
						title=DERIVED_SOURCE_TRACE_MISSING,
						exc=frappe.ValidationError,
					)
				validate_source_trace(ct)

	for ai, att in enumerate(attachments):
		if not isinstance(att, dict):
			frappe.throw(
				_("Bundle attachments[{0}] must be an object.").format(ai),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		at = att.get("source_trace")
		if at is None:
			frappe.throw(
				_("Bundle attachments[{0}] is missing source_trace.").format(ai),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
		validate_source_trace(at)

	for code in BUNDLE_SECTION_CODES:
		if code not in ph:
			frappe.throw(
				_("Bundle placeholder_status is missing key {0}.").format(code),
				title=DERIVED_SOURCE_TRACE_MISSING,
				exc=frappe.ValidationError,
			)
