# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Immutable STD Instance / output snapshots at lifecycle gates (configuration, publication, addendum, …).

STDINST-0500.

Not to be confused with ``tender_management.services.works_tender_snapshot``, which hashes
officer-stage ``Procurement Tender`` configuration for Works hardening (WH-009 / WH-011).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.attachment import section_attachments_snapshot
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_SNAPSHOT_CREATED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parameter_values_snapshot,
)
from kentender_procurement.tender_management.std_instance.works_requirement import works_requirements_snapshot

def _sha256_hex(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(obj: Any) -> str:
	return _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")))


def _strip(value: str | None) -> str:
	return (value or "").strip()


def final_snapshot_content_fingerprint(doc: Document) -> tuple[Any, ...]:
	"""Substantive evidence fields while snapshot is Final (excludes ``snapshot_status``)."""
	return (
		_strip(doc.tender_std_instance),
		_strip(doc.procurement_tender),
		_strip(doc.snapshot_type),
		_strip(doc.snapshot_reason),
		_strip(doc.source_template_version_code),
		_strip(doc.source_addendum_code),
		_strip(doc.ref_bundle_output),
		_strip(doc.ref_dsm_output),
		_strip(doc.ref_dom_output),
		_strip(doc.ref_dem_output),
		_strip(doc.ref_dcm_output),
		_strip(doc.parameter_values_hash),
		_strip(doc.works_requirements_hash),
		_strip(doc.attachments_hash),
		_strip(doc.boq_hash),
		_strip(doc.complete_instance_hash),
	)


def assert_final_snapshot_honored(prev_doc: Document, new_doc: Document) -> None:
	"""Final snapshots immutable except Final→Superseded / Final→Archived with unchanged evidence."""
	if getattr(new_doc.flags, "ignore_snapshot_immutability", False):
		return

	prev_st = (prev_doc.snapshot_status or "").strip()
	if prev_st != "Final":
		return

	fp_old = final_snapshot_content_fingerprint(prev_doc)
	fp_new = final_snapshot_content_fingerprint(new_doc)
	new_st = (new_doc.snapshot_status or "").strip()

	if fp_old != fp_new:
		frappe.throw(_("Final STD snapshot evidence cannot change."), title=_("STD Instance Snapshot"))

	if prev_st == new_st:
		return

	if new_st in ("Superseded", "Archived"):
		return

	frappe.throw(
		_("Final STD snapshot cannot change to status {0}.").format(new_st),
		title=_("STD Instance Snapshot"),
	)


def _boq_snapshot_payload(boq: Document) -> dict[str, Any]:
	bills: list[dict[str, Any]] = []
	for row in sorted(boq.boq_bills or [], key=lambda r: _strip(r.bill_instance_code)):
		bills.append(
			{
				"bill_instance_code": _strip(row.bill_instance_code),
				"bill_number": _strip(row.bill_number),
				"bill_title": _strip(row.bill_title),
				"bill_type": _strip(row.bill_type),
				"order_index": int(row.order_index or 0),
				"status": _strip(row.status),
			}
		)
	items: list[dict[str, Any]] = []
	for row in sorted(boq.boq_items or [], key=lambda r: _strip(r.item_instance_code)):
		items.append(
			{
				"item_instance_code": _strip(row.item_instance_code),
				"bill_instance_code": _strip(row.bill_instance_code),
				"item_number": _strip(row.item_number),
				"description": _strip(row.description),
				"unit": _strip(row.unit),
				"quantity": float(row.quantity or 0),
				"item_type": _strip(row.item_type),
				"supplier_input_mode": _strip(row.supplier_input_mode),
				"rate_required_from_supplier": int(row.rate_required_from_supplier or 0),
				"fixed_amount": float(row.fixed_amount or 0),
				"provisional_sum_amount": float(row.provisional_sum_amount or 0),
				"status": _strip(row.status),
				"source_addendum_code": _strip(row.source_addendum_code),
			}
		)
	return {
		"name": boq.name,
		"header": {
			"boq_definition_code": _strip(boq.boq_definition_code),
			"currency": _strip(boq.currency),
			"pricing_model": _strip(boq.pricing_model),
			"quantity_owner": _strip(boq.quantity_owner),
			"supplier_input_mode": _strip(boq.supplier_input_mode),
			"amount_computation_rule": _strip(boq.amount_computation_rule),
			"arithmetic_correction_stage": _strip(boq.arithmetic_correction_stage),
			"status": _strip(boq.status),
			"version_number": int(boq.version_number or 0),
			"source_addendum_code": _strip(boq.source_addendum_code),
		},
		"bills": bills,
		"items": items,
	}


def _compute_boq_hash(instance_name: str) -> str:
	boq = get_boq_for_instance(instance_name)
	if not boq:
		return _sha256_json({"boq": None})
	return _sha256_json(_boq_snapshot_payload(boq))


def _compute_hashes_and_refs(
	inst: Document,
	output_ref_overrides: dict[str, str | None] | None,
	readiness_evidence: dict[str, Any] | None = None,
) -> tuple[str, str, str, str, str, dict[str, str | None]]:
	pv = parameter_values_snapshot(inst)
	wr = works_requirements_snapshot(inst)
	sa = section_attachments_snapshot(inst)
	ph = _sha256_json(pv)
	wh = _sha256_json(wr)
	ah = _sha256_json(sa)
	bh = _compute_boq_hash(inst.name)

	refs: dict[str, str | None] = {}
	for key, parent_field in OUTPUT_KEY_TO_PARENT_FIELD.items():
		if output_ref_overrides and key in output_ref_overrides:
			v = output_ref_overrides[key]
			refs[key] = (v or "").strip() or None
		else:
			raw = inst.get(parent_field)
			refs[key] = _strip(raw) or None

	refs_norm = json.dumps(
		{k: refs[k] or "" for k in sorted(refs.keys())},
		sort_keys=True,
		separators=(",", ":"),
	)
	hash_parts: list[str] = [ph, wh, ah, bh, refs_norm]
	if readiness_evidence is not None:
		hash_parts.append(_sha256_json(readiness_evidence))
	ch = _sha256_hex("|".join(hash_parts))

	return ph, wh, ah, bh, ch, refs


def assert_final_publication_snapshot_exists(instance_name: str) -> None:
	if not frappe.db.exists("Tender STD Instance", instance_name):
		frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)
	found = frappe.get_all(
		"Tender STD Instance Snapshot",
		filters={
			"tender_std_instance": instance_name,
			"snapshot_type": "Publication",
			"snapshot_status": "Final",
		},
		limit=1,
		pluck="name",
	)
	if not found:
		frappe.throw(
			_("A Final Publication snapshot is required for this STD Instance."),
			title=_("STD Instance Snapshot"),
		)


class StdInstanceSnapshotService:
	"""Lifecycle snapshot rows — hashes + output refs; Final snapshots immutable."""

	@staticmethod
	def _create_snapshot(
		instance_name: str,
		snapshot_type: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		source_addendum_code: str | None = None,
		output_ref_overrides: dict[str, str | None] | None = None,
		readiness_evidence: dict[str, Any] | None = None,
	) -> Document:
		reason = _strip(snapshot_reason)
		if not reason:
			frappe.throw(_("snapshot_reason is required."), title=_("STD Instance Snapshot"))

		if not frappe.db.exists("Tender STD Instance", instance_name):
			frappe.throw(_("Tender STD Instance not found."), frappe.DoesNotExistError)

		inst = frappe.get_doc("Tender STD Instance", instance_name)
		pt = _strip(inst.procurement_tender)
		if not pt:
			frappe.throw(_("STD Instance has no Procurement Tender."), title=_("STD Instance Snapshot"))

		ph, wh, ah, bh, ch, refs = _compute_hashes_and_refs(
			inst, output_ref_overrides, readiness_evidence
		)

		doc = frappe.new_doc("Tender STD Instance Snapshot")
		doc.tender_std_instance = instance_name
		doc.procurement_tender = pt
		doc.snapshot_type = snapshot_type
		doc.snapshot_reason = reason
		doc.snapshot_status = snapshot_status
		doc.source_template_version_code = inst.template_version_code
		if source_addendum_code:
			doc.source_addendum_code = source_addendum_code.strip()

		doc.ref_bundle_output = refs.get("Bundle")
		doc.ref_dsm_output = refs.get("DSM")
		doc.ref_dom_output = refs.get("DOM")
		doc.ref_dem_output = refs.get("DEM")
		doc.ref_dcm_output = refs.get("DCM")

		doc.parameter_values_hash = ph
		doc.works_requirements_hash = wh
		doc.attachments_hash = ah
		doc.boq_hash = bh
		doc.complete_instance_hash = ch

		user = frappe.session.user
		if user == "Guest":
			user = "Administrator"
		doc.created_by = user
		doc.created_at = now_datetime()

		doc.insert(ignore_permissions=True)
		emit_std_instance_event(
			EVT_STDINST_SNAPSHOT_CREATED,
			instance_code=instance_name,
			document_type="Tender STD Instance",
			document_name=instance_name,
			details={
				"snapshot_code": doc.name,
				"snapshot_type": snapshot_type,
				"snapshot_status": snapshot_status,
				"snapshot_reason": reason,
				"source_addendum_code": (source_addendum_code or "").strip() or None,
			},
		)
		return frappe.get_doc("Tender STD Instance Snapshot", doc.name)

	@staticmethod
	def create_configuration_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
		source_addendum_code: str | None = None,
		readiness_evidence: dict[str, Any] | None = None,
	) -> Document:
		"""Create a Configuration snapshot.

		:param readiness_evidence: optional dict (e.g. Works readiness status + codes) folded into
			``complete_instance_hash`` when not ``None`` (WORKS-COMP-0700).
		"""
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Configuration",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
			readiness_evidence=readiness_evidence,
		)

	@staticmethod
	def create_publication_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
		source_addendum_code: str | None = None,
	) -> Document:
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Publication",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
		)

	@staticmethod
	def create_addendum_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		source_addendum_code: str | None = None,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
	) -> Document:
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Addendum",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
		)

	@staticmethod
	def create_opening_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
		source_addendum_code: str | None = None,
	) -> Document:
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Opening",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
		)

	@staticmethod
	def create_evaluation_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
		source_addendum_code: str | None = None,
	) -> Document:
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Evaluation",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
		)

	@staticmethod
	def create_contract_snapshot(
		instance_name: str,
		snapshot_reason: str,
		*,
		snapshot_status: str = "Final",
		output_ref_overrides: dict[str, str | None] | None = None,
		source_addendum_code: str | None = None,
	) -> Document:
		return StdInstanceSnapshotService._create_snapshot(
			instance_name,
			"Contract",
			snapshot_reason,
			snapshot_status=snapshot_status,
			output_ref_overrides=output_ref_overrides,
			source_addendum_code=source_addendum_code,
		)
