# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0120 — ``DerivedOutputVersioningService`` (pack §7 façade over STD generated outputs)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUTS_STALED
from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import OUTPUT_KEY_TO_PARENT_FIELD

DERIVED_OUTPUT_VERSIONING_TITLE = "Derived Output Versioning"


def _parse_content_json(raw: Any) -> Any:
	if raw is None:
		return None
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			return json.loads(s)
		except Exception:
			return raw
	return raw


class DerivedOutputVersioningService:
	"""Pack-aligned output lifecycle API; delegates persistence to ``StdInstanceGeneratedOutputService``."""

	@staticmethod
	def createDraftOutput(
		instance_code: str,
		output_type: str,
		content: Any,
		metadata: dict[str, Any] | None = None,
	) -> Document:
		code = (instance_code or "").strip()
		ot = (output_type or "").strip()
		meta = dict(metadata or {})
		if not isinstance(content, dict):
			frappe.throw(_("content must be a dict."), title=_(DERIVED_OUTPUT_VERSIONING_TITLE))
		ignore_lock = bool(meta.get("ignore_generated_output_lock", False))
		return StdInstanceGeneratedOutputService.insert_draft_output(
			code,
			ot,
			content,
			input_hash=meta.get("input_hash"),
			output_hash=meta.get("output_hash"),
			generated_by_job_code=(meta.get("generated_by_job_code") or "").strip() or None,
			source_instance_snapshot_code=(meta.get("source_instance_snapshot_code") or "").strip() or None,
			source_addendum_code=(meta.get("source_addendum_code") or "").strip() or None,
			ignore_generated_output_lock=ignore_lock,
			output_doc_name=(meta.get("output_doc_name") or "").strip() or None,
		)

	@staticmethod
	def markCurrent(output_code: str) -> Document:
		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		doc = frappe.get_doc("Tender STD Generated Output", name)
		st = (doc.output_status or "").strip()
		if st != "Draft":
			frappe.throw(
				_("Only Draft outputs can be marked Current (got {0}).").format(st or "Unknown"),
				title=_(DERIVED_OUTPUT_VERSIONING_TITLE),
				exc=frappe.ValidationError,
			)
		doc.flags.allow_generated_output_service_mutation = True
		doc.output_status = "Current"
		doc.save(ignore_permissions=True)
		return frappe.get_doc("Tender STD Generated Output", name)

	@staticmethod
	def markPublished(output_code: str, snapshot_code: str | None = None) -> Document:
		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		if (snapshot_code or "").strip():
			doc = frappe.get_doc("Tender STD Generated Output", name)
			doc.flags.allow_generated_output_service_mutation = True
			doc.source_instance_snapshot_code = snapshot_code.strip()
			doc.save(ignore_permissions=True)
		return StdInstanceGeneratedOutputService.publish_output(name)

	@staticmethod
	def markStale(output_code: str, reason: str | None = None) -> None:
		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		doc = frappe.get_doc("Tender STD Generated Output", name)
		instance_name = (doc.tender_std_instance or "").strip()
		if not instance_name:
			frappe.throw(_("Output has no STD Instance."), title=_(DERIVED_OUTPUT_VERSIONING_TITLE))
		StdInstanceGeneratedOutputService.mark_output_stale(instance_name, output_code=name)
		emit_std_instance_event(
			EVT_STDINST_OUTPUTS_STALED,
			instance_code=instance_name,
			document_name=instance_name,
			details={
				"source": "DerivedOutputVersioningService",
				"output_code": name,
				"reason": (reason or "").strip() or None,
			},
		)

	@staticmethod
	def supersedeOutput(old_output_code: str, new_output_code: str) -> Document:
		old_n = (old_output_code or "").strip()
		new_n = (new_output_code or "").strip()
		if not old_n or not frappe.db.exists("Tender STD Generated Output", old_n):
			frappe.throw(_("Old generated output not found."), frappe.DoesNotExistError)
		if not new_n or not frappe.db.exists("Tender STD Generated Output", new_n):
			frappe.throw(_("New generated output not found."), frappe.DoesNotExistError)
		if old_n == new_n:
			frappe.throw(_("Old and new output codes must differ."), title=_(DERIVED_OUTPUT_VERSIONING_TITLE))

		old_doc = frappe.get_doc("Tender STD Generated Output", old_n)
		new_doc = frappe.get_doc("Tender STD Generated Output", new_n)
		if (old_doc.tender_std_instance or "").strip() != (new_doc.tender_std_instance or "").strip():
			frappe.throw(
				_("Outputs must belong to the same STD Instance."),
				title=_(DERIVED_OUTPUT_VERSIONING_TITLE),
				exc=frappe.ValidationError,
			)
		if (old_doc.output_type or "").strip() != (new_doc.output_type or "").strip():
			frappe.throw(
				_("Outputs must have the same output_type."),
				title=_(DERIVED_OUTPUT_VERSIONING_TITLE),
				exc=frappe.ValidationError,
			)

		StdInstanceGeneratedOutputService.supersede_output(old_n)

		ot = (old_doc.output_type or "").strip()
		inst = frappe.get_doc("Tender STD Instance", old_doc.tender_std_instance)
		pf = OUTPUT_KEY_TO_PARENT_FIELD.get(ot)
		if pf and (inst.get(pf) or "").strip() == old_n:
			inst.set(pf, None)
			inst.save(ignore_permissions=True)

		new_doc = frappe.get_doc("Tender STD Generated Output", new_n)
		new_doc.flags.allow_generated_output_service_mutation = True
		new_doc.supersedes_output_code = old_n
		new_doc.save(ignore_permissions=True)
		return frappe.get_doc("Tender STD Generated Output", new_n)

	@staticmethod
	def getCurrentOutput(instance_code: str, output_type: str) -> dict[str, Any]:
		ic = (instance_code or "").strip()
		ot = (output_type or "").strip()
		if ot not in OUTPUT_TYPES:
			frappe.throw(_("Invalid output_type."), title=_(DERIVED_OUTPUT_VERSIONING_TITLE))
		field = OUTPUT_KEY_TO_PARENT_FIELD.get(ot)
		if not field:
			frappe.throw(_("Unknown output type mapping."), title=_(DERIVED_OUTPUT_VERSIONING_TITLE))
		if not frappe.db.exists("Tender STD Instance", ic):
			frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)
		inst = frappe.get_doc("Tender STD Instance", ic)
		out_name = (inst.get(field) or "").strip()
		if not out_name:
			frappe.throw(
				_("No current {0} output is set on this STD Instance.").format(ot),
				title=_(DERIVED_OUTPUT_VERSIONING_TITLE),
				exc=frappe.ValidationError,
			)
		return DerivedOutputVersioningService.getOutputVersion(out_name)

	@staticmethod
	def getOutputVersion(output_code: str) -> dict[str, Any]:
		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		doc = frappe.get_doc("Tender STD Generated Output", name)

		def _dt(val: Any) -> str | None:
			if val is None:
				return None
			if hasattr(val, "isoformat"):
				try:
					return val.isoformat()
				except Exception:
					return str(val)
			return str(val)

		return {
			"name": doc.name,
			"tender_std_instance": doc.tender_std_instance,
			"output_type": doc.output_type,
			"version_number": int(doc.version_number or 0),
			"output_status": doc.output_status,
			"content_json": _parse_content_json(doc.get("content_json")),
			"input_hash": doc.input_hash,
			"output_hash": doc.output_hash,
			"tender_code": doc.tender_code,
			"supersedes_output_code": doc.supersedes_output_code,
			"source_template_version_code": doc.source_template_version_code,
			"source_profile_code": doc.source_profile_code,
			"source_instance_snapshot_code": doc.source_instance_snapshot_code,
			"source_addendum_code": doc.source_addendum_code,
			"generated_by_job_code": doc.generated_by_job_code,
			"generated_at": _dt(doc.generated_at),
			"published_at": _dt(doc.published_at),
		}
