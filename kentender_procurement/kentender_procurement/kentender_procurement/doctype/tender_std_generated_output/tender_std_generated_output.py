# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD Generated Output — STDINST-0400."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.generated_output import (
	assert_draft_current_generated_output_content_guarded,
	assert_final_snapshot_bound_output_honored,
	assert_published_generated_output_honored,
)


class TenderSTDGeneratedOutput(Document):
	def validate(self) -> None:
		self._validate_derived_source_traces_on_content()
		self._validate_single_published_per_instance_type()
		self._validate_single_current_per_instance_type()
		if not self.is_new():
			prev = frappe.get_doc("Tender STD Generated Output", self.name)
			assert_published_generated_output_honored(prev, self)
			assert_final_snapshot_bound_output_honored(prev, self)
			assert_draft_current_generated_output_content_guarded(prev, self)

	def _validate_derived_source_traces_on_content(self) -> None:
		ot = (self.output_type or "").strip()
		if ot not in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
			return
		raw: Any = self.get("content_json")
		if raw is None:
			return
		if isinstance(raw, str) and not (raw.strip()):
			return
		payload: Any = raw
		if isinstance(raw, str):
			try:
				payload = json.loads(raw)
			except Exception:
				frappe.throw(
					_("content_json is not valid JSON."),
					title=_("STD Generated Output"),
					exc=frappe.ValidationError,
				)
		if not isinstance(payload, dict):
			return
		from kentender_procurement.tender_management.derived_models.common.source_trace import (
			validate_derived_output_source_traces,
		)

		validate_derived_output_source_traces(ot, payload)

	def _validate_single_published_per_instance_type(self) -> None:
		if (self.output_status or "").strip() != "Published":
			return
		if not self.tender_std_instance or not self.output_type:
			return
		existing = frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": self.tender_std_instance,
				"output_type": self.output_type,
				"output_status": "Published",
				"name": ["!=", self.name],
			},
			pluck="name",
			limit=1,
		)
		if existing:
			frappe.throw(
				_("Another Published output exists for this STD Instance and output type: {0}").format(
					existing[0],
				),
				title=_("STD Generated Output"),
			)

	def _validate_single_current_per_instance_type(self) -> None:
		if (self.output_status or "").strip() != "Current":
			return
		if not self.tender_std_instance or not self.output_type:
			return
		existing = frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": self.tender_std_instance,
				"output_type": self.output_type,
				"output_status": "Current",
				"name": ["!=", self.name],
			},
			pluck="name",
			limit=1,
		)
		if existing:
			frappe.throw(
				_("Another Current output exists for this STD Instance and output type: {0}").format(
					existing[0],
				),
				title=_("STD Generated Output"),
			)
