# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Structured Works Requirements rows for an STD Instance.

STDINST-0220.
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
	EVT_STDINST_OUTPUTS_STALED,
	EVT_STDINST_WORKS_REQUIREMENT_CHANGED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION,
	OUTPUT_KEY_TO_PARENT_FIELD,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

INSTANCE_STATUSES_BLOCKING_WORKS_REQUIREMENT_MUTATION = INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION

DRIVE_FIELD_TO_LOGICAL_OUTPUT: tuple[tuple[str, str], ...] = (
	("drives_bundle", "Bundle"),
	("drives_dsm", "DSM"),
	("drives_dem", "DEM"),
	("drives_dcm", "DCM"),
)


def _normalize_cc(value: str | None) -> str:
	return (value or "").strip()


def _works_requirement_substantive_fingerprint(row: Any) -> tuple[Any, ...]:
	return (
		(row.get("structured_text") or "").strip(),
		(row.get("structured_data") or "").strip(),
		(row.get("requirement_status") or "").strip(),
		int(row.get("attachment_required") or 0),
		(row.get("attachment_status") or "").strip(),
		int(row.get("drives_bundle") or 0),
		int(row.get("drives_dsm") or 0),
		int(row.get("drives_dem") or 0),
		int(row.get("drives_dcm") or 0),
		(row.get("source_addendum_code") or "").strip(),
	)


def logical_outputs_from_row(row: Any) -> frozenset[str]:
	out: set[str] = set()
	for field, key in DRIVE_FIELD_TO_LOGICAL_OUTPUT:
		if int(row.get(field) or 0):
			out.add(key)
	return frozenset(out)


def works_requirements_snapshot(doc: Document) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	for row in doc.get("works_requirements") or []:
		rc = _normalize_cc(row.get("requirement_code"))
		cc = _normalize_cc(row.get("component_code"))
		if not rc or not cc:
			continue
		rows.append(
			{
				"requirement_code": rc,
				"component_code": cc,
				"requirement_status": (row.get("requirement_status") or "").strip(),
				"structured_text": (row.get("structured_text") or "").strip(),
				"structured_data": (row.get("structured_data") or "").strip(),
				"attachment_required": int(row.get("attachment_required") or 0),
				"attachment_status": (row.get("attachment_status") or "").strip(),
				"drives_bundle": int(row.get("drives_bundle") or 0),
				"drives_dsm": int(row.get("drives_dsm") or 0),
				"drives_dem": int(row.get("drives_dem") or 0),
				"drives_dcm": int(row.get("drives_dcm") or 0),
				"source_addendum_code": _normalize_cc(row.get("source_addendum_code")),
			}
		)
	rows.sort(key=lambda r: (r["component_code"], r["requirement_code"]))
	return rows


def assert_no_duplicate_requirement_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.works_requirements or []:
		rc = _normalize_cc(row.requirement_code)
		if not rc:
			continue
		if rc in seen:
			frappe.throw(
				_("Duplicate requirement_code in table: {0}").format(rc),
				title=_("STD Works Requirements"),
			)
		seen.add(rc)


def assert_works_requirement_rows_have_component_code(doc: Document) -> None:
	for row in doc.works_requirements or []:
		if not _normalize_cc(row.component_code):
			frappe.throw(
				_("Works requirement rows must have component_code."),
				title=_("STD Works Requirements"),
			)


def assert_no_duplicate_component_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.works_requirements or []:
		cc = _normalize_cc(row.component_code)
		if not cc:
			continue
		if cc in seen:
			frappe.throw(
				_("Duplicate component_code in table: {0}").format(cc),
				title=_("STD Works Requirements"),
			)
		seen.add(cc)


def mark_outputs_stale_for_works_requirement_change(
	instance_name: str,
	affected: frozenset[str],
) -> Document | None:
	"""Merge stale logical outputs from ``drives_*``; clear ``current_*``; readiness Blocked."""
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
			"source": "works_requirement",
			"stale_outputs": sorted(affected),
		},
	)
	return doc


class StdInstanceWorksRequirementService:
	"""Works requirement rows — set, validate, stale-output propagation."""

	@staticmethod
	def status_blocks_works_requirement_edits(instance_status: str | None) -> bool:
		return bool(instance_status) and instance_status in INSTANCE_STATUSES_BLOCKING_WORKS_REQUIREMENT_MUTATION

	@staticmethod
	def assert_works_requirement_mutation_allowed(
		instance_status: str | None,
		*,
		ignore_publication_lock: bool = False,
	) -> None:
		if ignore_publication_lock:
			return
		if StdInstanceWorksRequirementService.status_blocks_works_requirement_edits(instance_status):
			frappe.throw(
				_(
					"Works requirements cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(instance_status),
				title=_("STD Works Requirements Locked"),
			)

	@staticmethod
	def set_works_requirement(
		instance_name: str,
		component_code: str,
		*,
		structured_text: str | None = None,
		structured_data: str | None = None,
		requirement_status: str = "In Progress",
		attachment_required: bool = False,
		attachment_status: str = "Not Required",
		drives_bundle: bool = False,
		drives_dsm: bool = False,
		drives_dem: bool = False,
		drives_dcm: bool = False,
		source_addendum_code: str | None = None,
		user: str | None = None,
		ignore_publication_lock: bool = False,
	) -> Document:
		enforce_sec_authorization(
			action_code="EDIT_STD_INSTANCE_PARAMETERS",
			actor=user or frappe.session.user,
			object_type="Tender STD Instance",
			object_code=instance_name,
			context={"object_exists": bool(frappe.db.exists("Tender STD Instance", instance_name))},
			fallback_message="Not authorized to edit works requirements.",
		)
		cc = _normalize_cc(component_code)
		if not cc:
			frappe.throw(_("component_code is required."), title=_("STD Works Requirement"))

		if not ignore_publication_lock:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)
			from kentender_procurement.tender_management.std_instance.publication_lock import (
				StdPublicationLockService,
			)

			StdAuthorizationService.assert_can_edit_draft_instance(
				instance_name,
				attempted_change="edit works requirements",
			)
			StdPublicationLockService.assert_editable(instance_name, operation_label="edit works requirements")

		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceWorksRequirementService.assert_works_requirement_mutation_allowed(
			doc.instance_status,
			ignore_publication_lock=ignore_publication_lock,
		)
		doc.flags.ignore_works_requirement_publication_lock = bool(ignore_publication_lock)

		actor = user or frappe.session.user
		prev_fp: tuple[Any, ...] | None = None
		target = None
		for row in doc.works_requirements or []:
			if _normalize_cc(row.component_code) == cc:
				target = row
				prev_fp = _works_requirement_substantive_fingerprint(row)
				break

		if target is None:
			rc = f"STD-WR-{frappe.generate_hash(length=12)}"
			target = doc.append(
				"works_requirements",
				{
					"requirement_code": rc,
					"component_code": cc,
				},
			)

		target.structured_text = structured_text
		target.structured_data = structured_data
		target.requirement_status = requirement_status
		target.attachment_required = 1 if attachment_required else 0
		target.attachment_status = attachment_status
		target.drives_bundle = 1 if drives_bundle else 0
		target.drives_dsm = 1 if drives_dsm else 0
		target.drives_dem = 1 if drives_dem else 0
		target.drives_dcm = 1 if drives_dcm else 0
		if source_addendum_code:
			target.source_addendum_code = source_addendum_code.strip()
		target.updated_by = actor
		target.updated_at = now_datetime()

		new_fp = _works_requirement_substantive_fingerprint(target)
		content_changed = prev_fp != new_fp

		doc.save(ignore_permissions=True)

		if content_changed:
			doc_ref = frappe.get_doc("Tender STD Instance", doc.name)
			row_after = None
			for r in doc_ref.works_requirements or []:
				if _normalize_cc(r.component_code) == cc:
					row_after = r
					break
			if row_after is not None:
				affected = logical_outputs_from_row(row_after)
				if affected:
					mark_outputs_stale_for_works_requirement_change(doc.name, affected)
			emit_std_instance_event(
				EVT_STDINST_WORKS_REQUIREMENT_CHANGED,
				instance_code=doc.name,
				details={
					"component_code": cc,
					"requirement_status": target.requirement_status,
					"attachment_status": target.attachment_status,
				},
			)

		return frappe.get_doc("Tender STD Instance", doc.name)

	@staticmethod
	def validate_works_requirements(instance_name: str) -> dict[str, Any]:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		blocking: list[str] = []
		missing_text: list[str] = []
		for row in doc.works_requirements or []:
			cc = _normalize_cc(row.component_code)
			if not cc:
				continue
			if int(row.attachment_required or 0) and (row.attachment_status or "") != "Complete":
				blocking.append(cc)
			if (row.requirement_status or "") == "Missing" and not (row.structured_text or "").strip():
				missing_text.append(cc)

		ok = not blocking and not missing_text
		return {
			"ok": ok,
			"blocking": blocking,
			"missing_structured_text": missing_text,
			"instance": instance_name,
		}
