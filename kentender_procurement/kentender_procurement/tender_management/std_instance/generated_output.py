# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Versioned generated outputs: Bundle, DSM, DOM, DEM, DCM — append-only after publish.

STDINST-0400. Generation is a deterministic stub (no PDF/rendering pipeline).
Production uses Draft → publish sets Published and updates ``Tender STD Instance`` pointers.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.derived_models.events.audit import (
	emit_derived_model_audit_for_output,
	emit_derived_model_generation_failed,
)
from kentender_procurement.tender_management.derived_models.events.codes import (
	DERIVED_MODEL_GENERATED,
	DERIVED_MODEL_GENERATION_FAILED,
	DERIVED_MODEL_MARKED_STALE,
	DERIVED_MODEL_SUPERSEDED,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_OUTPUT_GENERATED,
	EVT_STDINST_OUTPUT_GENERATION_FAILED,
	EVT_STDINST_OUTPUTS_SUPERSEDED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parse_outputs_stale_flags,
)

SYNC_GENERATION_JOB_CODE = "SYNC-STDINST-0400"

OUTPUT_TYPES: frozenset[str] = frozenset({"Bundle", "DSM", "DOM", "DEM", "DCM"})

# Keep in sync with ``Tender STD Generated Output`` Select options (DERIVED-0100).
OUTPUT_STATUSES: frozenset[str] = frozenset(
	{"Draft", "Current", "Published", "Superseded", "Archived", "Stale", "Failed"}
)


def _canonical_json(obj: Any) -> str:
	if obj is None:
		return "{}"
	if isinstance(obj, str):
		try:
			parsed = json.loads(obj)
			return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
		except Exception:
			return json.dumps(obj, sort_keys=True, separators=(",", ":"))
	return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def published_generated_output_content_fingerprint(doc: Document) -> tuple[Any, ...]:
	"""Immutable PE-facing fields while Published."""
	cj = doc.get("content_json")
	return (
		(doc.tender_std_instance or "").strip(),
		(doc.output_type or "").strip(),
		int(doc.version_number or 0),
		_canonical_json(cj),
		(doc.input_hash or "").strip(),
		(doc.output_hash or "").strip(),
		(doc.source_template_version_code or "").strip(),
		(doc.source_profile_code or "").strip(),
		(doc.source_instance_snapshot_code or "").strip(),
		(doc.source_addendum_code or "").strip(),
		(doc.rendered_file_reference or "").strip(),
		(doc.generated_by_job_code or "").strip(),
		(doc.tender_code or "").strip(),
		(doc.supersedes_output_code or "").strip(),
	)


def snapshot_bound_core_fingerprint(doc: Document) -> tuple[Any, ...]:
	"""PE-facing fields for Final snapshot-bound rows, excluding publication-only ``supersedes_output_code``."""
	return published_generated_output_content_fingerprint(doc)[:-1]


def assert_draft_current_generated_output_content_guarded(prev_doc: Document, new_doc: Document) -> None:
	"""Draft/Current rows cannot have bundle content mutated outside generation services (RULE-011)."""
	if getattr(new_doc.flags, "allow_generated_output_service_mutation", False):
		return
	prev_st = (prev_doc.output_status or "").strip()
	if prev_st not in ("Draft", "Current"):
		return
	fp_old = published_generated_output_content_fingerprint(prev_doc)
	fp_new = published_generated_output_content_fingerprint(new_doc)
	if fp_old != fp_new:
		frappe.throw(
			_("Generated output content cannot be edited manually while status is {0}.").format(prev_st),
			title=_("STD Generated Output"),
		)


def assert_published_generated_output_honored(prev_doc: Document, new_doc: Document) -> None:
	"""Published outputs are immutable (core fields). Allowed outcomes: stay Published, or Published→Superseded/Stale."""
	if getattr(new_doc.flags, "ignore_generated_output_immutability", False):
		return

	prev_st = (prev_doc.output_status or "").strip()
	if prev_st != "Published":
		return

	fp_old = published_generated_output_content_fingerprint(prev_doc)
	fp_new = published_generated_output_content_fingerprint(new_doc)
	new_st = (new_doc.output_status or "").strip()

	if fp_old != fp_new:
		frappe.throw(_("Published generated output cannot change."), title=_("STD Generated Output"))

	if prev_st == new_st:
		return

	if new_st in ("Superseded", "Stale"):
		return

	frappe.throw(
		_("Published generated output cannot change to status {0}.").format(new_st),
		title=_("STD Generated Output"),
	)


def _final_snapshot_for_output_row(snapshot_name: str) -> Document | None:
	if not (snapshot_name or "").strip():
		return None
	if not frappe.db.exists("Tender STD Instance Snapshot", snapshot_name):
		return None
	return frappe.get_doc("Tender STD Instance Snapshot", snapshot_name)


def assert_final_snapshot_bound_output_honored(prev_doc: Document, new_doc: Document) -> None:
	"""Rows linked to a Final STD snapshot cannot mutate core evidence fields (DERIVED-0100)."""
	if getattr(new_doc.flags, "ignore_generated_output_immutability", False):
		return
	code = (prev_doc.source_instance_snapshot_code or "").strip()
	if not code:
		return
	snap = _final_snapshot_for_output_row(code)
	if not snap:
		return
	if (snap.tender_std_instance or "").strip() != (prev_doc.tender_std_instance or "").strip():
		return
	if (snap.snapshot_status or "").strip() != "Final":
		return

	prev_st = (prev_doc.output_status or "").strip()
	new_st = (new_doc.output_status or "").strip()

	# Publishing may set ``supersedes_output_code``; that must not trip immutability for Final-bound rows.
	if new_st == "Published" and prev_st in ("Draft", "Current"):
		if snapshot_bound_core_fingerprint(prev_doc) != snapshot_bound_core_fingerprint(new_doc):
			frappe.throw(
				_("Snapshot-bound generated output cannot change."),
				title=_("STD Generated Output"),
			)
		return

	fp_old = published_generated_output_content_fingerprint(prev_doc)
	fp_new = published_generated_output_content_fingerprint(new_doc)
	if fp_old != fp_new:
		frappe.throw(
			_("Snapshot-bound generated output cannot change."),
			title=_("STD Generated Output"),
		)

	if prev_st == new_st:
		return
	if new_st in ("Superseded", "Stale", "Archived"):
		return
	if new_st == "Current" and prev_st == "Draft":
		return
	frappe.throw(
		_("Snapshot-bound generated output cannot change to status {0}.").format(new_st),
		title=_("STD Generated Output"),
	)


def _sha256_hex(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _next_version_number(instance_name: str, output_type: str) -> int:
	row = frappe.db.sql(
		"""
		select max(version_number) from `tabTender STD Generated Output`
		where tender_std_instance = %s and output_type = %s
		""",
		(instance_name, output_type),
	)
	max_v = row[0][0] if row and row[0][0] is not None else 0
	return int(max_v) + 1


def _stub_payload(inst: Document, output_type: str) -> dict[str, Any]:
	if output_type == "Bundle":
		from kentender_procurement.tender_management.derived_models.bundle.generator import (
			BundleGenerator,
		)

		return BundleGenerator.generateBundle(inst.name)

	boq = get_boq_for_instance(inst.name)
	base: dict[str, Any] = {
		"std_inst": inst.name,
		"output_type": output_type,
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": len(inst.parameter_values or []),
		"attachment_rows": len(inst.section_attachments or []),
		"works_requirement_rows": len(inst.works_requirements or []),
		"has_boq": bool(boq),
	}
	if output_type == "DSM":
		from kentender_procurement.tender_management.derived_models.dsm.generator import DsmGenerator

		return DsmGenerator.generateDSM(inst.name)
	elif output_type == "DOM":
		from kentender_procurement.tender_management.derived_models.dom.generator import DomGenerator

		return DomGenerator.generateDOM(inst.name)
	elif output_type == "DEM":
		from kentender_procurement.tender_management.derived_models.dem.generator import DemGenerator

		return DemGenerator.generateDEM(inst.name)
	elif output_type == "DCM":
		from kentender_procurement.tender_management.derived_models.dcm.generator import DcmGenerator

		return DcmGenerator.generateDCM(inst.name)
	return base


def remove_stale_flag_keys(instance_name: str, keys: set[str]) -> Document | None:
	"""Remove logical output keys from ``outputs_stale_flags`` JSON array."""
	if not keys:
		return None
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	existing = set(parse_outputs_stale_flags(doc))
	merged = sorted(existing - keys)
	doc.outputs_stale_flags = json.dumps(merged) if merged else ""
	doc.save(ignore_permissions=True)
	return doc


def merge_stale_flag_keys(instance_name: str, keys: set[str]) -> Document:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	existing = set(parse_outputs_stale_flags(doc))
	merged = sorted(existing | keys)
	doc.outputs_stale_flags = json.dumps(merged)
	doc.readiness_status = "Blocked"
	doc.save(ignore_permissions=True)
	return doc


class StdInstanceGeneratedOutputService:
	"""Generated outputs — stub generation, publish, supersede, stale marking."""

	@staticmethod
	def insert_draft_output(
		instance_name: str,
		output_type: str,
		payload: dict[str, Any],
		*,
		input_hash: str | None = None,
		output_hash: str | None = None,
		generated_by_job_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		source_addendum_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		output_doc_name: str | None = None,
	) -> Document:
		"""Insert a new Draft ``Tender STD Generated Output`` row (DERIVED-0120 / STDINST-0400)."""
		try:
			if output_type not in OUTPUT_TYPES:
				frappe.throw(_("Invalid output_type."), title=_("STD Generated Output"))

			if not isinstance(payload, dict):
				frappe.throw(_("content_json payload must be a dict."), title=_("STD Generated Output"))

			if not frappe.db.exists("Tender STD Instance", instance_name):
				frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)

			if not ignore_generated_output_lock:
				from kentender_procurement.tender_management.std_instance.authorization import (
					StdAuthorizationService,
				)

				StdAuthorizationService.assert_can_generate_outputs(instance_name)

			inst = frappe.get_doc("Tender STD Instance", instance_name)

			from kentender_procurement.tender_management.derived_models.common.metadata import (
				tender_code_for_instance,
			)
			from kentender_procurement.tender_management.derived_models.common.source_trace import (
				validate_derived_output_source_traces,
			)

			validate_derived_output_source_traces(output_type, payload)
			content_json_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
			out_h = output_hash if output_hash is not None else _sha256_hex(content_json_str)
			in_h = (
				input_hash
				if input_hash is not None
				else _sha256_hex(
					"|".join(
						[
							instance_name,
							output_type,
							str(inst.template_version_code or ""),
							str(inst.applicability_profile_code or ""),
						]
					)
				)
			)

			vn = _next_version_number(instance_name, output_type)
			job_code = (generated_by_job_code or "").strip() or SYNC_GENERATION_JOB_CODE

			doc = frappe.new_doc("Tender STD Generated Output")
			doc.flags.allow_generated_output_service_mutation = True
			doc.flags.ignore_generated_output_immutability = bool(ignore_generated_output_lock)
			doc.tender_std_instance = instance_name
			doc.output_type = output_type
			doc.version_number = vn
			doc.output_status = "Draft"
			doc.source_template_version_code = inst.template_version_code
			doc.source_profile_code = inst.applicability_profile_code
			if source_instance_snapshot_code:
				doc.source_instance_snapshot_code = source_instance_snapshot_code.strip()
			if source_addendum_code:
				doc.source_addendum_code = source_addendum_code.strip()
			doc.content_json = payload
			doc.input_hash = in_h
			doc.output_hash = out_h
			doc.tender_code = tender_code_for_instance(instance_name)
			doc.generated_by_job_code = job_code
			doc.generated_at = now_datetime()
			oname = (output_doc_name or "").strip() or None
			if oname:
				doc.insert(ignore_permissions=True, set_name=oname)
			else:
				doc.insert(ignore_permissions=True)
			emit_std_instance_event(
				EVT_STDINST_OUTPUT_GENERATED,
				instance_code=instance_name,
				document_type="Tender STD Generated Output",
				document_name=doc.name,
				details={
					"output_type": output_type,
					"version_number": int(doc.version_number or 0),
					"source_addendum_code": source_addendum_code,
				},
			)
			emit_derived_model_audit_for_output(
				DERIVED_MODEL_GENERATED,
				doc,
				extra={"source": "insert_draft_output", "source_addendum_code": source_addendum_code},
			)
			return frappe.get_doc("Tender STD Generated Output", doc.name)
		except Exception as exc:
			emit_std_instance_event(
				EVT_STDINST_OUTPUT_GENERATION_FAILED,
				instance_code=instance_name,
				details={
					"output_type": output_type,
					"error": str(exc),
				},
			)
			emit_derived_model_generation_failed(
				instance_name,
				output_type,
				str(exc),
				source="insert_draft_output",
			)
			raise

	@staticmethod
	def _generate(
		instance_name: str,
		output_type: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		inst = frappe.get_doc("Tender STD Instance", instance_name)
		payload = _stub_payload(inst, output_type)
		return StdInstanceGeneratedOutputService.insert_draft_output(
			instance_name,
			output_type,
			payload,
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def generate_bundle(
		instance_name: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		return StdInstanceGeneratedOutputService._generate(
			instance_name,
			"Bundle",
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def generate_dsm(
		instance_name: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		return StdInstanceGeneratedOutputService._generate(
			instance_name,
			"DSM",
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def generate_dom(
		instance_name: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		return StdInstanceGeneratedOutputService._generate(
			instance_name,
			"DOM",
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def generate_dem(
		instance_name: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		return StdInstanceGeneratedOutputService._generate(
			instance_name,
			"DEM",
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def generate_dcm(
		instance_name: str,
		*,
		source_addendum_code: str | None = None,
		source_instance_snapshot_code: str | None = None,
		ignore_generated_output_lock: bool = False,
		generated_by_job_code: str | None = None,
		output_doc_name: str | None = None,
	) -> Document:
		return StdInstanceGeneratedOutputService._generate(
			instance_name,
			"DCM",
			source_addendum_code=source_addendum_code,
			source_instance_snapshot_code=source_instance_snapshot_code,
			ignore_generated_output_lock=ignore_generated_output_lock,
			generated_by_job_code=generated_by_job_code,
			output_doc_name=output_doc_name,
		)

	@staticmethod
	def insert_failed_output_row(
		instance_name: str,
		output_type: str,
		*,
		error_message: str | None = None,
		generated_by_job_code: str | None = None,
		ignore_generated_output_lock: bool = False,
	) -> Document:
		"""Append a ``Failed`` row (empty ``content_json``) when generation cannot produce a valid Draft."""
		if output_type not in OUTPUT_TYPES:
			frappe.throw(_("Invalid output_type."), title=_("STD Generated Output"))

		if not frappe.db.exists("Tender STD Instance", instance_name):
			frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)

		if not ignore_generated_output_lock:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)

			StdAuthorizationService.assert_can_generate_outputs(instance_name)

		inst = frappe.get_doc("Tender STD Instance", instance_name)
		from kentender_procurement.tender_management.derived_models.common.metadata import (
			tender_code_for_instance,
		)

		vn = _next_version_number(instance_name, output_type)
		job_code = (generated_by_job_code or "").strip() or "DERIVED-0700-FAILED"
		err = (error_message or "").strip() or "generation_failed"
		in_h = _sha256_hex(f"{instance_name}|{output_type}|failed|{vn}|{err}")

		doc = frappe.new_doc("Tender STD Generated Output")
		doc.flags.allow_generated_output_service_mutation = True
		doc.tender_std_instance = instance_name
		doc.output_type = output_type
		doc.version_number = vn
		doc.output_status = "Failed"
		doc.source_template_version_code = inst.template_version_code
		doc.source_profile_code = inst.applicability_profile_code
		doc.content_json = None
		doc.input_hash = in_h
		doc.output_hash = _sha256_hex(err)
		doc.tender_code = tender_code_for_instance(instance_name)
		doc.generated_by_job_code = job_code
		doc.generated_at = now_datetime()
		doc.insert(ignore_permissions=True)
		emit_std_instance_event(
			EVT_STDINST_OUTPUT_GENERATION_FAILED,
			instance_code=instance_name,
			document_type="Tender STD Generated Output",
			document_name=doc.name,
			details={
				"output_type": output_type,
				"version_number": int(doc.version_number or 0),
				"error": err,
				"source": "insert_failed_output_row",
			},
		)
		emit_derived_model_audit_for_output(
			DERIVED_MODEL_GENERATION_FAILED,
			doc,
			extra={"error": err, "source": "insert_failed_output_row"},
		)
		return frappe.get_doc("Tender STD Generated Output", doc.name)

	@staticmethod
	def mark_output_generation_failed(
		output_name: str,
		*,
		error_message: str | None = None,
	) -> Document:
		"""Transition a Draft or Current row to ``Failed`` (DERIVED-0700 partial-failure recording)."""
		if not (output_name or "").strip() or not frappe.db.exists("Tender STD Generated Output", output_name):
			frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
		doc = frappe.get_doc("Tender STD Generated Output", output_name)
		st = (doc.output_status or "").strip()
		if st not in ("Draft", "Current"):
			frappe.throw(
				_("Only Draft or Current outputs can be marked Failed (got {0}).").format(st or "Unknown"),
				title=_("STD Generated Output"),
				exc=frappe.ValidationError,
			)
		doc.flags.allow_generated_output_service_mutation = True
		doc.output_status = "Failed"
		doc.save(ignore_permissions=True)
		emit_std_instance_event(
			EVT_STDINST_OUTPUT_GENERATION_FAILED,
			instance_code=doc.tender_std_instance,
			document_type="Tender STD Generated Output",
			document_name=doc.name,
			details={
				"output_type": doc.output_type,
				"error": (error_message or "").strip() or None,
				"source": "mark_output_generation_failed",
			},
		)
		emit_derived_model_audit_for_output(
			DERIVED_MODEL_GENERATION_FAILED,
			doc,
			extra={
				"error": (error_message or "").strip() or "generation_failed",
				"source": "mark_output_generation_failed",
			},
		)
		return frappe.get_doc("Tender STD Generated Output", doc.name)

	@staticmethod
	def supersede_output(
		output_name: str,
		*,
		ignore_generated_output_immutability: bool = False,
	) -> Document:
		doc = frappe.get_doc("Tender STD Generated Output", output_name)
		doc.flags.allow_generated_output_service_mutation = True
		doc.flags.ignore_generated_output_immutability = bool(ignore_generated_output_immutability)
		doc.output_status = "Superseded"
		doc.save(ignore_permissions=True)
		emit_std_instance_event(
			EVT_STDINST_OUTPUTS_SUPERSEDED,
			instance_code=doc.tender_std_instance,
			document_type="Tender STD Generated Output",
			document_name=doc.name,
			details={"output_type": doc.output_type, "source": "manual_supersede"},
		)
		emit_derived_model_audit_for_output(
			DERIVED_MODEL_SUPERSEDED,
			doc,
			extra={"source": "manual_supersede"},
		)
		return doc

	@staticmethod
	def publish_output(
		output_name: str,
		*,
		ignore_generated_output_immutability: bool = False,
	) -> Document:
		doc = frappe.get_doc("Tender STD Generated Output", output_name)
		st = (doc.output_status or "").strip()
		if st not in ("Draft", "Current"):
			frappe.throw(_("Only Draft or Current outputs can be published."), title=_("STD Generated Output"))

		instance_name = doc.tender_std_instance
		out_type = (doc.output_type or "").strip()
		key = out_type
		if key not in OUTPUT_KEY_TO_PARENT_FIELD:
			frappe.throw(_("Unknown output type mapping."), title=_("STD Generated Output"))

		prev_published_rows = frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": instance_name,
				"output_type": out_type,
				"output_status": "Published",
				"name": ["!=", output_name],
			},
			pluck="name",
			order_by="version_number desc",
			limit=1,
		)
		prev_published_name = prev_published_rows[0] if prev_published_rows else None

		StdInstanceGeneratedOutputService._supersede_other_active(instance_name, out_type, output_name)

		doc = frappe.get_doc("Tender STD Generated Output", output_name)
		doc.flags.allow_generated_output_service_mutation = True
		doc.flags.ignore_generated_output_immutability = bool(ignore_generated_output_immutability)
		if prev_published_name:
			doc.supersedes_output_code = prev_published_name
		doc.output_status = "Published"
		doc.published_at = now_datetime()
		doc.save(ignore_permissions=True)

		parent_field = OUTPUT_KEY_TO_PARENT_FIELD[key]
		inst = frappe.get_doc("Tender STD Instance", instance_name)
		inst.set(parent_field, doc.name)
		inst.save(ignore_permissions=True)

		remove_stale_flag_keys(instance_name, {key})

		return frappe.get_doc("Tender STD Generated Output", doc.name)

	@staticmethod
	def _supersede_other_active(instance_name: str, output_type: str, keep_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": instance_name,
				"output_type": output_type,
				"output_status": ["in", ["Published", "Current"]],
				"name": ["!=", keep_name],
			},
			pluck="name",
		):
			d = frappe.get_doc("Tender STD Generated Output", name)
			d.flags.allow_generated_output_service_mutation = True
			d.flags.ignore_generated_output_immutability = True
			d.output_status = "Superseded"
			d.save(ignore_permissions=True)
			emit_std_instance_event(
				EVT_STDINST_OUTPUTS_SUPERSEDED,
				instance_code=d.tender_std_instance,
				document_type="Tender STD Generated Output",
				document_name=d.name,
				details={"output_type": d.output_type, "source": "publish_conflict_resolution"},
			)
			emit_derived_model_audit_for_output(
				DERIVED_MODEL_SUPERSEDED,
				d,
				extra={"source": "publish_conflict_resolution"},
			)

	@staticmethod
	def mark_output_stale(
		instance_name: str,
		*,
		output_type: str | None = None,
		output_code: str | None = None,
		ignore_generated_output_immutability: bool = False,
	) -> None:
		"""Mark an output Stale; clear parent pointer if it points at that row; merge stale flags."""
		target_name: str | None = None
		resolved_type: str | None = output_type

		if output_code:
			target_name = output_code.strip()
			if not frappe.db.exists("Tender STD Generated Output", target_name):
				frappe.throw(_("Generated output not found."), frappe.DoesNotExistError)
			tsi = frappe.db.get_value("Tender STD Generated Output", target_name, "tender_std_instance")
			if tsi != instance_name:
				frappe.throw(_("Output does not belong to this STD Instance."), title=_("STD Generated Output"))
			if not resolved_type:
				resolved_type = (frappe.db.get_value("Tender STD Generated Output", target_name, "output_type") or "").strip()
		elif output_type:
			ot = output_type.strip()
			if ot not in OUTPUT_TYPES:
				frappe.throw(_("Invalid output_type."), title=_("STD Generated Output"))
			field = OUTPUT_KEY_TO_PARENT_FIELD.get(ot)
			if not field:
				frappe.throw(_("Unknown output type."), title=_("STD Generated Output"))
			target_name = frappe.db.get_value("Tender STD Instance", instance_name, field)
			resolved_type = ot
		else:
			frappe.throw(_("output_type or output_code is required."), title=_("STD Generated Output"))

		assert resolved_type is not None
		key = resolved_type
		if key not in OUTPUT_KEY_TO_PARENT_FIELD:
			frappe.throw(_("Unknown output type."), title=_("STD Generated Output"))

		if target_name:
			doc = frappe.get_doc("Tender STD Generated Output", target_name)
			doc.flags.allow_generated_output_service_mutation = True
			doc.flags.ignore_generated_output_immutability = bool(ignore_generated_output_immutability)
			prev_st = (doc.output_status or "").strip()
			if prev_st == "Published":
				doc.output_status = "Stale"
			elif prev_st not in ("Superseded", "Archived", "Stale", "Failed"):
				doc.output_status = "Stale"
			doc.save(ignore_permissions=True)
			doc = frappe.get_doc("Tender STD Generated Output", target_name)
			new_st = (doc.output_status or "").strip()
			if prev_st != "Stale" and new_st == "Stale":
				emit_derived_model_audit_for_output(
					DERIVED_MODEL_MARKED_STALE,
					doc,
					extra={"source": "mark_output_stale"},
				)

		inst = frappe.get_doc("Tender STD Instance", instance_name)
		field = OUTPUT_KEY_TO_PARENT_FIELD[key]
		if target_name and (inst.get(field) or "").strip() == target_name.strip():
			inst.set(field, None)
			inst.save(ignore_permissions=True)
		merge_stale_flag_keys(instance_name, {key})
