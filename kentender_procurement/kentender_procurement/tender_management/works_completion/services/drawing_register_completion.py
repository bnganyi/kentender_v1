# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0230 — Drawing register completion (pack payload + stable blocker codes).

Delegates persistence to ``StdInstanceDrawingRegisterService``.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.tender_management.services.tender_configuration import parse_configuration_json
from kentender_procurement.tender_management.std_instance.drawing_register import (
	SECTION_VII_ALLOWED_CODES,
	StdInstanceDrawingRegisterService,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_DRAWING_REGISTER_CHANGED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

# Phase 1: Works tender-stage completion expects at least one drawing row when saving validation runs.
DRAWING_REGISTER_REQUIRED: bool = True

_CODE_MESSAGES: dict[str, str] = {
	"DRAWING_REGISTER_MISSING": _("Drawing register must contain at least one Section VII drawing."),
	"DRAWING_FILE_MISSING": _("Each drawing must have a file reference."),
	"DRAWING_SECTION_INVALID": _("Each drawing must be bound to Section VII (allowed section codes)."),
	"DRAWING_REVISION_MISSING": _("Drawing revision is required."),
	"DRAWING_DUPLICATE_REVISION": _("Duplicate drawing_code and revision in the payload."),
	"WORKS_INSTANCE_NOT_FOUND": _("Tender STD Instance was not found."),
}


def _norm(value: str | None) -> str:
	return (value or "").strip()


def _truthy(val: Any) -> bool:
	if isinstance(val, bool):
		return val
	s = str(val).strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _drawing_register_rows_required(instance_code: str) -> bool:
	"""Non-empty register required unless tender config ``WORKS.DRAWING_REGISTER_OPTIONAL`` is truthy."""
	if not DRAWING_REGISTER_REQUIRED:
		return False
	tm2 = frappe.db.get_value("Tender STD Instance", instance_code, "tm2_tender")
	if not tm2 or not frappe.db.exists("TM2 Tender", tm2):
		return True
	tender = frappe.get_doc("TM2 Tender", tm2)
	cfg = parse_configuration_json(tender)
	if _truthy(cfg.get("WORKS.DRAWING_REGISTER_OPTIONAL")):
		return False
	return True


class WorksDrawingRegisterService:
	"""Validate and save pack-shaped drawing register payloads."""

	@staticmethod
	def validate_drawing_register(instance_code: str) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``."""
		code = _norm(instance_code)
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": str(_CODE_MESSAGES["WORKS_INSTANCE_NOT_FOUND"]),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		doc = frappe.get_doc("Tender STD Instance", code)
		rows = list(doc.drawing_register or [])

		blockers: list[dict[str, str]] = []

		if _drawing_register_rows_required(code) and len(rows) < 1:
			blockers.append(
				{
					"code": "DRAWING_REGISTER_MISSING",
					"message": str(_CODE_MESSAGES["DRAWING_REGISTER_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

		for row in rows:
			dc = _norm(row.drawing_code)
			rv = _norm(row.revision)
			if not rv:
				blockers.append(
					{
						"code": "DRAWING_REVISION_MISSING",
						"message": str(_CODE_MESSAGES["DRAWING_REVISION_MISSING"]),
						"severity": SEVERITY_HIGH,
					}
				)
			if not _norm(row.file_reference):
				blockers.append(
					{
						"code": "DRAWING_FILE_MISSING",
						"message": str(_CODE_MESSAGES["DRAWING_FILE_MISSING"]),
						"severity": SEVERITY_CRITICAL,
					}
				)
			sc = _norm(row.section_code)
			if not sc or sc not in SECTION_VII_ALLOWED_CODES:
				blockers.append(
					{
						"code": "DRAWING_SECTION_INVALID",
						"message": str(_CODE_MESSAGES["DRAWING_SECTION_INVALID"]),
						"severity": SEVERITY_CRITICAL,
					}
				)

		seen: set[str] = set()
		for row in rows:
			key = f"{_norm(row.drawing_code)}::{_norm(row.revision)}"
			if key in seen:
				blockers.append(
					{
						"code": "DRAWING_DUPLICATE_REVISION",
						"message": str(_CODE_MESSAGES["DRAWING_DUPLICATE_REVISION"]),
						"severity": SEVERITY_HIGH,
					}
				)
				break
			seen.add(key)

		return {"valid": not blockers, "blockers": blockers}

	@staticmethod
	def save_drawing_register(
		instance_code: str,
		payload: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		code = _norm(instance_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save drawing register: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Drawing register"),
			)

		raw = payload if isinstance(payload, dict) else {}
		items = raw.get("drawings")
		if items is None:
			items = []
		if not isinstance(items, list):
			frappe.throw(_("Payload must include a \"drawings\" array."), title=_("Drawing register"))

		stale_before = stale_logical_outputs_snapshot(code)

		user = actor or frappe.session.user
		pairs_seen: set[tuple[str, str]] = set()
		for item in items:
			if not isinstance(item, dict):
				frappe.throw(_("Each drawings item must be an object."), title=_("Drawing register"))
			dc = _norm(item.get("drawing_code"))
			rv = _norm(item.get("revision"))
			pair = (dc, rv)
			if dc and rv:
				if pair in pairs_seen:
					frappe.throw(
						str(_CODE_MESSAGES["DRAWING_DUPLICATE_REVISION"]),
						title=_("Drawing register"),
					)
				pairs_seen.add(pair)

			title = _norm(item.get("title")) or None
			file_reference = _norm(item.get("file_reference")) or None
			section_code = _norm(item.get("section_code")) or None
			classification = _norm(item.get("classification")) or "Supplier Facing"
			issue_status = _norm(item.get("issue_status")) or "Current"
			ack = _truthy(item.get("acknowledgement_required"))
			file_name = _norm(item.get("file_name")) or None
			file_hash = _norm(item.get("file_hash")) or None

			if not dc or not rv:
				frappe.throw(_("Each drawing requires drawing_code and revision."), title=_("Drawing register"))

			StdInstanceDrawingRegisterService.set_drawing_row(
				code,
				dc,
				rv,
				title=title,
				file_reference=file_reference,
				section_code=section_code,
				classification=classification,
				issue_status=issue_status,
				acknowledgement_required=ack,
				file_name=file_name,
				file_hash=file_hash,
				user=user,
				ignore_publication_lock=False,
			)

		val = WorksDrawingRegisterService.validate_drawing_register(code)
		if not val.get("valid"):
			parts = [str(b.get("message") or b.get("code")) for b in (val.get("blockers") or [])]
			frappe.throw(
				_("Drawing register validation failed: {0}").format("; ".join(parts)),
				title=_("Drawing register"),
			)

		emit_works_completion_audit(
			WORKS_DRAWING_REGISTER_CHANGED,
			code,
			details={"drawing_count": len(items)},
			performed_by=user,
		)
		emit_works_output_stale_if_new(code, stale_before, source="drawing_register", performed_by=user)

		return {"ok": True, "instance_code": code}

	@staticmethod
	def attach_drawing_file(
		instance_code: str,
		drawing_code: str,
		*,
		revision: str | None = None,
		file_name: str,
		file_reference: str,
		file_hash: str | None = None,
		actor: str | None = None,
	) -> Any:
		code = _norm(instance_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot attach drawing file: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Drawing register"),
			)

		rv = _norm(revision) if revision is not None else None
		row = StdInstanceDrawingRegisterService.find_row(code, drawing_code, rv)
		if row is None:
			frappe.throw(_("Drawing row was not found."), title=_("Drawing register"))

		user = actor or frappe.session.user
		stale_before = stale_logical_outputs_snapshot(code)
		out = StdInstanceDrawingRegisterService.set_drawing_row(
			code,
			_norm(row.drawing_code),
			_norm(row.revision),
			title=_norm(row.title),
			file_reference=file_reference.strip(),
			section_code=_norm(row.section_code),
			classification=(row.classification or "Supplier Facing").strip(),
			issue_status=(row.issue_status or "Current").strip(),
			acknowledgement_required=bool(cint(getattr(row, "acknowledgement_required", 0))),
			file_name=file_name.strip(),
			file_hash=_norm(file_hash) or None,
			user=user,
			ignore_publication_lock=False,
		)
		emit_works_completion_audit(
			WORKS_DRAWING_REGISTER_CHANGED,
			code,
			details={
				"path": "attach_drawing_file",
				"drawing_code": _norm(row.drawing_code),
				"revision": _norm(row.revision),
			},
			performed_by=user,
		)
		emit_works_output_stale_if_new(
			code, stale_before, source="drawing_register_attach", performed_by=user
		)
		return out
