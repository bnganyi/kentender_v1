# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Drawing register rows on ``Tender STD Instance`` — Section VII binding, staleness.

WORKS-COMP-0230 / STDINST drawing register.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_DRAWING_REGISTER_CHANGED,
	EVT_STDINST_OUTPUTS_STALED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
)

INSTANCE_STATUSES_BLOCKING_DRAWING_REGISTER_MUTATION = frozenset(
	{
		"Published Locked",
		"Addendum Pending",
		"Addendum Regenerated",
		"Superseded",
		"Cancelled",
	}
)

# POC STD uses ``DRAWINGS``; pack example uses ``SECTION_VII_DRAWINGS`` — accept both.
SECTION_VII_ALLOWED_CODES: frozenset[str] = frozenset({"DRAWINGS", "SECTION_VII_DRAWINGS"})


def _norm(value: str | None) -> str:
	return (value or "").strip()


def logical_outputs_from_drawing_row(row: Any) -> frozenset[str]:
	out: set[str] = {"Bundle", "DEM", "DCM"}
	ar = getattr(row, "acknowledgement_required", None)
	if ar is None and isinstance(row, dict):
		ar = row.get("acknowledgement_required")
	if int(ar or 0):
		out.add("DSM")
	return frozenset(out)


def _drawing_substantive_fingerprint(row: Any) -> tuple[Any, ...]:
	return (
		_norm(getattr(row, "title", None) or row.get("title")),
		_norm(getattr(row, "revision", None) or row.get("revision")),
		_norm(getattr(row, "file_reference", None) or row.get("file_reference")),
		_norm(getattr(row, "file_name", None) or row.get("file_name")),
		_norm(getattr(row, "file_hash", None) or row.get("file_hash")),
		_norm(getattr(row, "section_code", None) or row.get("section_code")),
		(getattr(row, "classification", None) or row.get("classification") or "").strip(),
		(getattr(row, "issue_status", None) or row.get("issue_status") or "").strip(),
		int(getattr(row, "acknowledgement_required", None) or row.get("acknowledgement_required") or 0),
	)


def mark_outputs_stale_for_drawing_change(
	instance_name: str,
	affected: frozenset[str],
) -> Document | None:
	if not affected:
		return None

	doc = frappe.get_doc("Tender STD Instance", instance_name)

	raw = (doc.outputs_stale_flags or "").strip()
	existing: list[str] = []
	if raw:
		try:
			parsed = json.loads(raw)
			if isinstance(parsed, list):
				existing = [str(x) for x in parsed]
		except Exception:
			existing = []

	merged = sorted(set(existing) | set(affected))
	doc.outputs_stale_flags = json.dumps(merged)

	for key in affected:
		field = OUTPUT_KEY_TO_PARENT_FIELD.get(key)
		if field:
			doc.set(field, None)

	doc.readiness_status = "Blocked"

	doc.save(ignore_permissions=True)
	emit_std_instance_event(
		EVT_STDINST_OUTPUTS_STALED,
		instance_code=instance_name,
		document_name=instance_name,
		details={
			"source": "drawing_register",
			"stale_outputs": sorted(affected),
		},
	)
	return doc


class StdInstanceDrawingRegisterService:
	"""Drawing register child table — upsert, Section VII validation, stale outputs."""

	@staticmethod
	def status_blocks_drawing_register_edits(instance_status: str | None) -> bool:
		return bool(instance_status) and instance_status in INSTANCE_STATUSES_BLOCKING_DRAWING_REGISTER_MUTATION

	@staticmethod
	def assert_drawing_register_mutation_allowed(
		instance_status: str | None,
		*,
		ignore_publication_lock: bool = False,
	) -> None:
		if ignore_publication_lock:
			return
		if StdInstanceDrawingRegisterService.status_blocks_drawing_register_edits(instance_status):
			frappe.throw(
				_(
					"Drawing register cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(instance_status),
				title=_("STD Drawing Register Locked"),
			)

	@staticmethod
	def assert_section_vii(section_code: str | None) -> None:
		sc = _norm(section_code)
		if not sc:
			frappe.throw(_("section_code is required for drawings."), title=_("STD Drawing Register"))
		if sc not in SECTION_VII_ALLOWED_CODES:
			frappe.throw(
				_("Drawing section_code must be Section VII–bound (got {0}).").format(sc),
				title=_("STD Drawing Register"),
			)

	@staticmethod
	def set_drawing_row(
		instance_name: str,
		drawing_code: str,
		revision: str,
		*,
		title: str | None = None,
		file_reference: str | None = None,
		section_code: str | None = None,
		classification: str = "Supplier Facing",
		issue_status: str = "Current",
		acknowledgement_required: bool = False,
		file_name: str | None = None,
		file_hash: str | None = None,
		user: str | None = None,
		ignore_publication_lock: bool = False,
	) -> Document:
		dc = _norm(drawing_code)
		rv = _norm(revision)
		if not dc or not rv:
			frappe.throw(_("drawing_code and revision are required."), title=_("STD Drawing Register"))

		if not ignore_publication_lock:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)
			from kentender_procurement.tender_management.std_instance.publication_lock import (
				StdPublicationLockService,
			)

			StdAuthorizationService.assert_can_edit_draft_instance(instance_name)
			StdPublicationLockService.assert_editable(instance_name, operation_label="edit drawing register")

		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceDrawingRegisterService.assert_drawing_register_mutation_allowed(
			doc.instance_status,
			ignore_publication_lock=ignore_publication_lock,
		)
		doc.flags.ignore_drawing_register_publication_lock = bool(ignore_publication_lock)

		StdInstanceDrawingRegisterService.assert_section_vii(section_code)

		actor = user or frappe.session.user
		prev_fp: tuple[Any, ...] | None = None
		target = None
		for row in doc.drawing_register or []:
			if _norm(row.drawing_code) == dc and _norm(row.revision) == rv:
				target = row
				prev_fp = _drawing_substantive_fingerprint(row)
				break

		if target is None:
			rc = f"STD-DR-{frappe.generate_hash(length=12)}"
			target = doc.append(
				"drawing_register",
				{
					"register_row_code": rc,
					"drawing_code": dc,
					"revision": rv,
				},
			)

		target.title = title or ""
		target.file_reference = file_reference or ""
		target.file_name = file_name or ""
		target.file_hash = file_hash or ""
		target.section_code = _norm(section_code)
		target.classification = classification or "Supplier Facing"
		target.issue_status = issue_status or "Current"
		target.acknowledgement_required = 1 if acknowledgement_required else 0
		target.updated_by = actor
		target.updated_at = now_datetime()

		new_fp = _drawing_substantive_fingerprint(target)
		content_changed = prev_fp != new_fp

		doc.save(ignore_permissions=True)

		if content_changed:
			doc_ref = frappe.get_doc("Tender STD Instance", doc.name)
			row_after = None
			for r in doc_ref.drawing_register or []:
				if _norm(r.drawing_code) == dc and _norm(r.revision) == rv:
					row_after = r
					break
			if row_after is not None:
				affected = logical_outputs_from_drawing_row(row_after)
				if affected:
					mark_outputs_stale_for_drawing_change(doc.name, affected)
			emit_std_instance_event(
				EVT_STDINST_DRAWING_REGISTER_CHANGED,
				instance_code=doc.name,
				details={
					"drawing_code": dc,
					"revision": rv,
					"issue_status": target.issue_status,
				},
			)

		return frappe.get_doc("Tender STD Instance", doc.name)

	@staticmethod
	def find_row(instance_name: str, drawing_code: str, revision: str | None) -> Any | None:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		dc = _norm(drawing_code)
		rv = _norm(revision) if revision is not None else ""
		candidates = [r for r in doc.drawing_register or [] if _norm(r.drawing_code) == dc]
		if not candidates:
			return None
		if rv:
			for r in candidates:
				if _norm(r.revision) == rv:
					return r
			return None
		if len(candidates) == 1:
			return candidates[0]
		return None
