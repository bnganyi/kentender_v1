# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Section-bound attachments for an STD Instance — versioning, supplier-facing rules.

STDINST-0210.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_ATTACHMENT_CHANGED,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION,
)

# Same publication posture as parameter values (pack §9 + alignment with §8 locks).
INSTANCE_STATUSES_BLOCKING_ATTACHMENT_MUTATION = INSTANCE_STATUSES_BLOCKING_PARAMETER_MUTATION


def _normalize_ac(value: str | None) -> str:
	return (value or "").strip()


def published_content_fingerprint(row: Document | Any) -> tuple[Any, ...]:
	"""Fingerprint binding + file payload for immutability checks (excludes attachment status)."""
	return (
		_normalize_ac(row.get("section_code")),
		_normalize_ac(row.get("component_code")),
		_normalize_ac(row.get("file_reference")),
		_normalize_ac(row.get("file_name")),
		_normalize_ac(row.get("file_hash")),
		(row.get("classification") or "").strip(),
		int(row.get("version_number") or 0),
	)


def section_attachments_snapshot(doc: Document) -> list[dict[str, Any]]:
	"""Deterministic snapshot for publication-lock comparisons."""
	rows: list[dict[str, Any]] = []
	for row in doc.get("section_attachments") or []:
		ac = _normalize_ac(row.get("attachment_code"))
		if not ac:
			continue
		rows.append(
			{
				"attachment_code": ac,
				"section_code": _normalize_ac(row.get("section_code")),
				"component_code": _normalize_ac(row.get("component_code")),
				"file_reference": _normalize_ac(row.get("file_reference")),
				"file_name": _normalize_ac(row.get("file_name")),
				"file_hash": _normalize_ac(row.get("file_hash")),
				"classification": (row.get("classification") or "").strip(),
				"version_number": int(row.get("version_number") or 0),
				"status": (row.get("status") or "").strip(),
				"source_addendum_code": _normalize_ac(row.get("source_addendum_code")),
				"supersedes_attachment_code": _normalize_ac(row.get("supersedes_attachment_code")),
			}
		)
	rows.sort(key=lambda r: r["attachment_code"])
	return rows


def assert_no_duplicate_attachment_codes(doc: Document) -> None:
	seen: set[str] = set()
	for row in doc.section_attachments or []:
		ac = _normalize_ac(row.attachment_code)
		if not ac:
			continue
		if ac in seen:
			frappe.throw(
				_("Duplicate attachment_code in table: {0}").format(ac),
				title=_("STD Section Attachments"),
			)
		seen.add(ac)


def assert_section_attachment_rows_bound(doc: Document) -> None:
	"""Unbound attachments denied (domain §9.3)."""
	for row in doc.section_attachments or []:
		if (row.status or "") == "Archived":
			continue
		if not _normalize_ac(row.section_code):
			frappe.throw(
				_("Section-bound attachment requires section_code (attachment {0}).").format(
					_normalize_ac(row.attachment_code) or row.name
				),
				title=_("STD Section Attachment Unbound"),
			)
		if not _normalize_ac(row.file_reference):
			frappe.throw(
				_("Section-bound attachment requires file_reference (attachment {0}).").format(
					_normalize_ac(row.attachment_code) or row.name
				),
				title=_("STD Section Attachment Unbound"),
			)
		if not _normalize_ac(row.file_name):
			frappe.throw(
				_("Section-bound attachment requires file_name (attachment {0}).").format(
					_normalize_ac(row.attachment_code) or row.name
				),
				title=_("STD Section Attachment Unbound"),
			)


def assert_published_attachment_rows_honored(prev_doc: Document, new_doc: Document) -> None:
	"""Published rows are immutable except Published → Superseded with unchanged content fingerprint."""
	prev_map = {_normalize_ac(r.attachment_code): r for r in (prev_doc.section_attachments or [])}
	new_map = {_normalize_ac(r.attachment_code): r for r in (new_doc.section_attachments or [])}
	for ac, pr in prev_map.items():
		if (pr.status or "") != "Published":
			continue
		cur = new_map.get(ac)
		if cur is None:
			frappe.throw(
				_("Published attachment {0} cannot be removed.").format(ac),
				title=_("STD Section Attachment Published"),
			)
		fp_old = published_content_fingerprint(pr)
		fp_new = published_content_fingerprint(cur)
		if fp_old != fp_new:
			frappe.throw(
				_("Published attachment {0} cannot change binding or file fields.").format(ac),
				title=_("STD Section Attachment Published"),
			)
		st_new = (cur.status or "").strip()
		if st_new == "Published":
			continue
		if st_new == "Superseded":
			continue
		frappe.throw(
			_("Published attachment {0} cannot change to status {1}.").format(ac, st_new),
			title=_("STD Section Attachment Published"),
		)


class StdInstanceAttachmentService:
	"""STD Instance section attachments — attach, addendum replacement, validation."""

	@staticmethod
	def status_blocks_attachment_edits(instance_status: str | None) -> bool:
		return bool(instance_status) and instance_status in INSTANCE_STATUSES_BLOCKING_ATTACHMENT_MUTATION

	@staticmethod
	def assert_attachment_mutation_allowed(
		instance_status: str | None,
		*,
		ignore_publication_lock: bool = False,
	) -> None:
		if ignore_publication_lock:
			return
		if StdInstanceAttachmentService.status_blocks_attachment_edits(instance_status):
			frappe.throw(
				_(
					"STD section attachments cannot be changed while Instance Status is {0}. "
					"Use an addendum workflow when implemented."
				).format(instance_status),
				title=_("STD Attachments Locked"),
			)

	@staticmethod
	def attach_file_to_section(
		instance_name: str,
		section_code: str,
		file_name: str,
		file_reference: str,
		classification: str = "Internal Only",
		*,
		component_code: str | None = None,
		file_hash: str | None = None,
		status: str = "Draft",
		user: str | None = None,
		ignore_publication_lock: bool = False,
	) -> Document:
		sc = _normalize_ac(section_code)
		if not sc:
			frappe.throw(_("section_code is required."), title=_("STD Section Attachment"))
		if not _normalize_ac(file_name) or not _normalize_ac(file_reference):
			frappe.throw(_("file_name and file_reference are required."), title=_("STD Section Attachment"))

		if not ignore_publication_lock:
			from kentender_procurement.tender_management.std_instance.authorization import (
				StdAuthorizationService,
			)
			from kentender_procurement.tender_management.std_instance.publication_lock import (
				StdPublicationLockService,
			)

			StdAuthorizationService.assert_can_edit_draft_instance(
				instance_name,
				attempted_change="edit section attachments",
			)
			StdPublicationLockService.assert_editable(instance_name, operation_label="edit section attachments")

		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceAttachmentService.assert_attachment_mutation_allowed(
			doc.instance_status,
			ignore_publication_lock=ignore_publication_lock,
		)
		doc.flags.ignore_attachment_publication_lock = bool(ignore_publication_lock)

		actor = user or frappe.session.user
		ac = f"STD-ATT-{frappe.generate_hash(length=12)}"
		doc.append(
			"section_attachments",
			{
				"attachment_code": ac,
				"section_code": sc,
				"component_code": _normalize_ac(component_code),
				"file_reference": file_reference.strip(),
				"file_name": file_name.strip(),
				"file_hash": _normalize_ac(file_hash) or None,
				"classification": classification,
				"version_number": 1,
				"status": status,
				"uploaded_by": actor,
				"uploaded_at": now_datetime(),
			},
		)
		doc.save(ignore_permissions=True)
		emit_std_instance_event(
			EVT_STDINST_ATTACHMENT_CHANGED,
			instance_code=instance_name,
			details={
				"section_code": sc,
				"attachment_code": ac,
				"file_name": file_name.strip(),
				"classification": classification,
			},
		)
		return doc

	@staticmethod
	def replace_attachment_through_addendum(
		instance_name: str,
		attachment_code: str,
		file_name: str,
		file_reference: str,
		source_addendum_code: str,
		*,
		file_hash: str | None = None,
		classification: str | None = None,
		component_code: str | None = None,
		section_code: str | None = None,
		user: str | None = None,
	) -> Document:
		ac = _normalize_ac(attachment_code)
		ad_code = _normalize_ac(source_addendum_code)
		if not ac:
			frappe.throw(_("attachment_code is required."), title=_("STD Section Attachment"))
		if not ad_code:
			frappe.throw(_("source_addendum_code is required for replacement."), title=_("STD Section Attachment"))
		if not _normalize_ac(file_name) or not _normalize_ac(file_reference):
			frappe.throw(_("file_name and file_reference are required."), title=_("STD Section Attachment"))

		doc = frappe.get_doc("Tender STD Instance", instance_name)
		doc.flags.ignore_attachment_publication_lock = True

		target = None
		for row in doc.section_attachments or []:
			if _normalize_ac(row.attachment_code) == ac:
				target = row
				break
		if target is None:
			frappe.throw(_("Attachment {0} not found.").format(ac), frappe.DoesNotExistError)

		if (target.status or "") == "Superseded":
			frappe.throw(
				_("Attachment {0} is already superseded.").format(ac),
				title=_("STD Section Attachment"),
			)

		target.status = "Superseded"

		new_ac = f"STD-ATT-{frappe.generate_hash(length=12)}"
		sc = _normalize_ac(section_code) if section_code is not None else _normalize_ac(target.section_code)
		cc = _normalize_ac(component_code) if component_code is not None else _normalize_ac(target.component_code)
		cls = classification if classification is not None else (target.classification or "Internal Only")
		actor = user or frappe.session.user
		doc.append(
			"section_attachments",
			{
				"attachment_code": new_ac,
				"section_code": sc,
				"component_code": cc or None,
				"file_reference": file_reference.strip(),
				"file_name": file_name.strip(),
				"file_hash": _normalize_ac(file_hash) or None,
				"classification": cls,
				"version_number": int(target.version_number or 1) + 1,
				"status": "Draft",
				"source_addendum_code": ad_code,
				"supersedes_attachment_code": ac,
				"uploaded_by": actor,
				"uploaded_at": now_datetime(),
			},
		)
		doc.save(ignore_permissions=True)
		return doc

	@staticmethod
	def validate_attachment_requirements(instance_name: str) -> dict[str, Any]:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		missing: list[str] = []
		violations: list[str] = []
		for row in doc.section_attachments or []:
			ac = _normalize_ac(row.attachment_code)
			if not ac:
				violations.append("row_without_attachment_code")
				continue
			if (row.status or "") == "Archived":
				continue
			if not _normalize_ac(row.section_code):
				missing.append(ac)
			elif not _normalize_ac(row.file_reference):
				missing.append(ac)
			elif not _normalize_ac(row.file_name):
				missing.append(ac)

		ok = not missing and not violations
		return {
			"ok": ok,
			"missing": missing,
			"violations": violations,
			"instance": instance_name,
		}
