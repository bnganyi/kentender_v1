# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Steps 12 + 13 + 14 — Procurement Tender server methods + form actions.

Step 12: thin whitelisted wrappers over the Step 11 template engine. Each method:

1. loads the tender via :func:`_get_tender_doc` (raises clear errors for
   missing names, missing tenders, or missing write permission per §9 / §10);
2. delegates to ``std_template_engine`` (no rule logic in this controller);
3. persists the result with ``tender.save()`` and returns the §13 envelope.

§12 status mapping is centralised in
:func:`_validation_status_to_tender_status`. §6.7 ``prepare_render_context``
keeps the JSON render context in ``generated_tender_pack_html`` prefixed
with the :data:`RENDER_CONTEXT_BANNER` for debug/inspection.

Step 13 adds :func:`generate_tender_pack_preview` which renders the
``templates/std_works_poc/tender_pack.html`` Jinja master into
``generated_tender_pack_html`` (HTML-only preview, no PDF). It refuses to
render when validation reports any blockers.

Step 14 hardens :func:`generate_required_forms` so it also persists
``validation_messages`` / ``validation_status`` / ``configuration_hash``
via the engine's writer helpers and returns the §11 envelope (status,
``blocks_generation``, hash). The engine itself now raises on unknown
form codes (§16) and joins multi-source activation (§8.4).

Step 15 hardens :func:`generate_sample_boq` — validates sample rows,
normalizes child payloads + notes, resets validation state, returns
``categories`` / optional ``lot_verification`` (see **STD-POC-016**).

See **STD-POC-013** / **STD-POC-014** / **STD-POC-015** / **STD-POC-016**
for controller path / template location adaptations and the sidecar JS choice.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.services import std_template_engine as engine

RENDER_CONTEXT_BANNER = (
	"// STD POC RENDER CONTEXT — JSON, not final tender pack HTML"
)

_VALIDATION_TO_TENDER_STATUS = {
	"Passed": "Validated",
	"Passed With Warnings": "Validated",
	"Failed": "Validation Failed",
	"Blocked": "Validation Failed",
}

VARIANT_CODES: tuple[str, ...] = (
	"VARIANT-INTERNATIONAL",
	"VARIANT-TENDER-SECURING-DECLARATION",
	"VARIANT-RESERVED-TENDER",
	"VARIANT-MISSING-SITE-VISIT-DATE",
	"VARIANT-MISSING-ALTERNATIVE-SCOPE",
	"VARIANT-SINGLE-LOT",
	"VARIANT-RETENTION-MONEY-SECURITY",
)


_WORKS_HARDENING_STATUS_FIELDS: tuple[str, ...] = (
	"works_hardening_status",
	"derived_models_status",
	"boq_hardening_status",
	"works_requirements_status",
	"attachments_status",
)
_WORKS_HARDENING_STATUS_DEFAULT = "Not Checked"


class ProcurementTender(Document):
	"""STD-WORKS-POC: tender instance linked to an STD template.

	Planning-to-tender integration (B1): when ``procurement_package`` is set, ``plan_id``
	on the package is the source of truth for ``procurement_plan`` (auto-filled if empty;
	validated for mismatch if both are set).
	"""

	def validate(self) -> None:
		self._ensure_works_hardening_status_defaults()
		self._validate_planning_lineage()
		self._validate_unique_active_handoff_tender()
		self._validate_section_attachment_rows()
		self._validate_derived_model_readiness_rows()

	def _validate_section_attachment_rows(self) -> None:
		"""WH-003 — child ``validate`` is not auto-run on parent save; invoke explicitly (doc 5 §9)."""
		for row in self.get("section_attachments") or []:
			row.run_method("validate")

	def _validate_derived_model_readiness_rows(self) -> None:
		"""WH-004 — child ``validate`` is not auto-run on parent save; invoke explicitly (doc 5 §10)."""
		for row in self.get("derived_model_readiness") or []:
			row.run_method("validate")

	def _ensure_works_hardening_status_defaults(self) -> None:
		"""Doc 5 §7 / WH-001 — status fields default to ``Not Checked`` when unset."""
		for fn in _WORKS_HARDENING_STATUS_FIELDS:
			if not (self.get(fn) or "").strip():
				self.set(fn, _WORKS_HARDENING_STATUS_DEFAULT)

	def _validate_unique_active_handoff_tender(self) -> None:
		"""Doc 2 sec. 16.3 / B9 — at most one non-cancelled tender per planning package."""
		from kentender_procurement.tender_management.services.planning_tender_handoff_duplicates import (
			validate_at_most_one_active_planning_tender_per_package,
		)

		validate_at_most_one_active_planning_tender_per_package(
			self.get("procurement_package"),
			current_tender_name=self.name,
		)

	def _validate_planning_lineage(self) -> None:
		if not self.get("procurement_package"):
			return
		pkg_plan = frappe.db.get_value(
			"Procurement Package", self.procurement_package, "plan_id"
		)
		if not pkg_plan:
			return
		if not self.get("procurement_plan"):
			self.procurement_plan = pkg_plan
			return
		if self.procurement_plan != pkg_plan:
			frappe.throw(
				frappe._(
					"Procurement Plan {0} does not match Procurement Package {1} (expected plan {2})."
				).format(self.procurement_plan, self.procurement_package, pkg_plan),
				frappe.ValidationError,
			)


# ---------------------------------------------------------------------------
# §11 — controller-private helpers
# ---------------------------------------------------------------------------


def _get_tender_doc(tender_name: str) -> Document:
	"""Load the tender + verify write permission. Raises clear errors per §10."""
	if not tender_name:
		frappe.throw(
			frappe._("tender_name is required."),
			frappe.ValidationError,
		)
	if not frappe.db.exists("Procurement Tender", tender_name):
		frappe.throw(
			frappe._("Procurement Tender {0} was not found.").format(tender_name),
			frappe.DoesNotExistError,
		)
	tender_doc = frappe.get_doc("Procurement Tender", tender_name)
	tender_doc.check_permission("write")
	return tender_doc


def _get_tender_doc_read(tender_name: str) -> Document:
	"""Load the tender + verify read permission (Admin Step 5 demo workspace HTML)."""
	if not tender_name:
		frappe.throw(
			frappe._("tender_name is required."),
			frappe.ValidationError,
		)
	if not frappe.db.exists("Procurement Tender", tender_name):
		frappe.throw(
			frappe._("Procurement Tender {0} was not found.").format(tender_name),
			frappe.DoesNotExistError,
		)
	tender_doc = frappe.get_doc("Procurement Tender", tender_name)
	tender_doc.check_permission("read")
	return tender_doc


def _require_std_template(tender_doc: Document) -> None:
	if not tender_doc.std_template:
		frappe.throw(frappe._("Select an STD Template before running this action."))


def _parse_configuration_json(tender_doc: Document) -> dict[str, Any]:
	raw = tender_doc.configuration_json
	if not raw:
		frappe.throw(
			frappe._(
				"Tender {0} has no configuration_json yet. Run Load Template Defaults or Load Sample Tender first."
			).format(tender_doc.name)
		)
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError as exc:
		frappe.throw(
			frappe._("Tender {0} has invalid configuration_json: {1}").format(
				tender_doc.name, exc
			)
		)
	if not isinstance(parsed, dict):
		frappe.throw(
			frappe._("Tender {0} configuration_json must be a JSON object.").format(
				tender_doc.name
			)
		)
	return parsed


def _parse_configuration_json_optional(tender_doc: Document) -> dict[str, Any]:
	"""Parse ``configuration_json`` when present; otherwise return an empty dict."""
	raw = tender_doc.configuration_json
	if not raw or not str(raw).strip():
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	if not isinstance(parsed, dict):
		return {}
	return parsed


def _child_rows_to_dicts(child_rows: list[Any] | None) -> list[dict[str, Any]]:
	if not child_rows:
		return []
	rows: list[dict[str, Any]] = []
	for row in child_rows:
		as_dict = getattr(row, "as_dict", None)
		if callable(as_dict):
			rows.append(as_dict())
		elif isinstance(row, dict):
			rows.append(row)
		else:
			rows.append(dict(row))
	return rows


def _save_and_return(tender_doc: Document, result: dict[str, Any]) -> dict[str, Any]:
	tender_doc.save()
	envelope: dict[str, Any] = {"ok": True}
	envelope.update(result)
	envelope.setdefault("tender", tender_doc.name)
	return envelope


def _validation_status_to_tender_status(validation_status: str | None) -> str | None:
	"""§12 — map engine validation_status to ``Procurement Tender.tender_status``."""
	if not validation_status:
		return None
	return _VALIDATION_TO_TENDER_STATUS.get(validation_status)


# ---------------------------------------------------------------------------
# §6.1 — load_template_defaults
# ---------------------------------------------------------------------------


@frappe.whitelist()
def load_template_defaults(tender_name: str) -> dict[str, Any]:
	"""Initialize tender configuration from ``fields.json`` defaults."""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	config = engine.initialize_config(template)
	engine.apply_config_to_tender_doc(tender_doc, config)
	tender_doc.tender_status = "Configured"
	tender_doc.validation_status = "Not Validated"
	tender_doc.set("validation_messages", [])
	return _save_and_return(
		tender_doc,
		{
			"message": "Template defaults loaded.",
			"template_code": template.get("template_code"),
		},
	)


# ---------------------------------------------------------------------------
# §6.2 — load_sample_tender
# ---------------------------------------------------------------------------


@frappe.whitelist()
def load_sample_tender(tender_name: str) -> dict[str, Any]:
	"""Populate tender with the primary sample configuration, lots, and BoQ rows."""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	engine.populate_sample_tender(tender_doc)
	tender_doc.tender_status = "Configured"
	tender_doc.validation_status = "Not Validated"
	tender_doc.set("validation_messages", [])
	tender_doc.set("required_forms", [])
	template_code = (
		tender_doc.template_code or tender_doc.std_template or ""
	)
	return _save_and_return(
		tender_doc,
		{
			"message": "Sample tender loaded.",
			"template_code": template_code,
		},
	)


# ---------------------------------------------------------------------------
# §6.3 — load_sample_variant
# ---------------------------------------------------------------------------


@frappe.whitelist()
def load_sample_variant(tender_name: str, variant_code: str) -> dict[str, Any]:
	"""Populate tender with a sample scenario variant from ``sample_tender.json``."""
	if not variant_code:
		frappe.throw(frappe._("variant_code is required."))
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	try:
		engine.populate_sample_tender(tender_doc, variant_code=variant_code)
	except ValueError as exc:
		frappe.throw(str(exc), frappe.ValidationError)
	tender_doc.tender_status = "Configured"
	tender_doc.validation_status = "Not Validated"
	tender_doc.set("validation_messages", [])
	tender_doc.set("required_forms", [])
	template_code = (
		tender_doc.template_code or tender_doc.std_template or ""
	)
	return _save_and_return(
		tender_doc,
		{
			"message": f"Sample variant {variant_code} loaded.",
			"template_code": template_code,
			"variant_code": variant_code,
		},
	)


# ---------------------------------------------------------------------------
# §6.4 — validate_tender_configuration
# ---------------------------------------------------------------------------


@frappe.whitelist()
def validate_tender_configuration(tender_name: str) -> dict[str, Any]:
	"""Evaluate ``rules.json`` against tender configuration; persist messages + status."""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))
	validation_result = engine.validate_config(template, config, lots=lots, boq_items=boq_items)
	engine.write_validation_to_tender(tender_doc, validation_result)
	tender_status = _validation_status_to_tender_status(validation_result["status"])
	if tender_status:
		tender_doc.tender_status = tender_status

	envelope = _save_and_return(
		tender_doc,
		{
			"message": f"Validation {validation_result['status']}.",
			"status": validation_result["status"],
			"validation_status": validation_result["status"],
			"blocks_generation": validation_result["blocks_generation"],
			"message_count": len(validation_result["messages"]),
			"configuration_hash": validation_result["configuration_hash"],
		},
	)
	envelope["ok"] = not validation_result["blocks_generation"]
	return envelope


# ---------------------------------------------------------------------------
# §6.5 — generate_required_forms
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate_required_forms(tender_name: str) -> dict[str, Any]:
	"""Resolve and persist the required-forms checklist on the tender.

	Step 14 §11: this also re-runs validation, persists ``validation_messages``
	+ ``validation_status`` + ``configuration_hash`` via
	:func:`engine.write_validation_to_tender`, maps the engine status to
	``tender_status`` per §12, and returns the full §11 envelope so clients can
	react to ``blocks_generation`` without a second round-trip.
	"""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))

	validation_result = engine.validate_config(
		template, config, lots=lots, boq_items=boq_items
	)
	engine.write_validation_to_tender(tender_doc, validation_result)
	mapped_status = _validation_status_to_tender_status(validation_result["status"])
	if mapped_status:
		tender_doc.tender_status = mapped_status

	required_forms = engine.resolve_required_forms(
		template, config, validation_result=validation_result
	)
	engine.write_required_forms_to_tender(tender_doc, required_forms)

	if tender_doc.tender_status in (None, "", "Draft"):
		tender_doc.tender_status = "Configured"

	return _save_and_return(
		tender_doc,
		{
			"message": f"{len(required_forms)} required forms generated.",
			"required_form_count": len(required_forms),
			"validation_status": validation_result["status"],
			"blocks_generation": validation_result["blocks_generation"],
			"configuration_hash": validation_result["configuration_hash"],
		},
	)


# ---------------------------------------------------------------------------
# §6.6 — generate_sample_boq
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate_sample_boq(tender_name: str) -> dict[str, Any]:
	"""Populate tender with validated sample BoQ rows from ``sample_tender.json`` (POC only).

	Step 15: clears ``boq_items``, validates rows, writes normalized child rows
	with audit notes, sets ``validation_status`` to ``Not Validated``, clears
	``validation_messages``, returns counts + sorted distinct categories.
	"""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	template = engine.load_template(tender_doc.std_template)

	try:
		rows = engine.load_sample_boq_rows(template)

		lots_dicts = _child_rows_to_dicts(tender_doc.get("lots"))
		lot_codes = {
			str(lot.get("lot_code"))
			for lot in lots_dicts
			if lot.get("lot_code") not in (None, "")
		}
		engine.validate_sample_boq_rows(
			rows,
			engine.get_allowed_boq_categories(),
			existing_lot_codes=lot_codes if lot_codes else frozenset(),
			strict_lot_references=bool(lot_codes),
		)
	except ValueError as exc:
		frappe.throw(str(exc), frappe.ValidationError)

	child_rows = engine.build_boq_child_rows(rows)
	tender_doc.set("boq_items", [])
	for row in child_rows:
		tender_doc.append("boq_items", row)

	tender_doc.validation_status = "Not Validated"
	tender_doc.set("validation_messages", [])

	if tender_doc.tender_status in (None, "", "Draft"):
		tender_doc.tender_status = "Configured"

	summary = engine.summarize_boq_rows(rows)
	result: dict[str, Any] = {
		"message": "Sample BoQ generated.",
		"boq_row_count": summary["boq_row_count"],
		"categories": summary["categories"],
	}
	if not lot_codes:
		result["lot_verification"] = "skipped_no_lots"
	else:
		result["lot_verification"] = "verified"

	return _save_and_return(tender_doc, result)


# ---------------------------------------------------------------------------
# §6.7 — prepare_render_context
# ---------------------------------------------------------------------------


@frappe.whitelist()
def prepare_render_context(tender_name: str) -> dict[str, Any]:
	"""Build render context (no HTML rendering); refuse when blockers exist."""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))

	validation_result = engine.validate_config(
		template, config, lots=lots, boq_items=boq_items
	)
	engine.write_validation_to_tender(tender_doc, validation_result)
	tender_status = _validation_status_to_tender_status(validation_result["status"])
	if tender_status:
		tender_doc.tender_status = tender_status

	if validation_result["blocks_generation"]:
		tender_doc.save()
		return {
			"ok": False,
			"message": (
				"Cannot prepare render context: tender configuration has blockers."
			),
			"tender": tender_doc.name,
			"status": validation_result["status"],
			"validation_status": validation_result["status"],
			"blocks_generation": True,
			"configuration_hash": validation_result["configuration_hash"],
			"required_form_count": 0,
		}

	required_forms = engine.resolve_required_forms(
		template, config, validation_result=validation_result
	)
	engine.write_required_forms_to_tender(tender_doc, required_forms)

	render_context = engine.build_render_context(
		template,
		config,
		lots=lots,
		boq_items=boq_items,
		validation_result=validation_result,
		required_forms=required_forms,
	)

	tender_doc.generated_tender_pack_html = (
		f"{RENDER_CONTEXT_BANNER}\n"
		f"{json.dumps(render_context, indent=2, sort_keys=True, default=str)}"
	)
	tender_doc.last_generated_at = frappe.utils.now_datetime()
	tender_doc.tender_status = "Tender Pack Generated"

	return _save_and_return(
		tender_doc,
		{
			"message": "Render context prepared.",
			"status": validation_result["status"],
			"validation_status": validation_result["status"],
			"blocks_generation": False,
			"configuration_hash": validation_result["configuration_hash"],
			"required_form_count": len(required_forms),
		},
	)


# ---------------------------------------------------------------------------
# Step 13 §12 — generate_tender_pack_preview
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate_tender_pack_preview(tender_name: str) -> dict[str, Any]:
	"""Render ``templates/std_works_poc/tender_pack.html`` into ``generated_tender_pack_html``.

	HTML-only preview per Step 13 §6 boundary (no PDF, no Print Format). Refuses
	to render when validation flags any blocker; persists validation messages and
	required-forms checklist either way.
	"""
	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))

	validation_result = engine.validate_config(
		template, config, lots=lots, boq_items=boq_items
	)
	engine.write_validation_to_tender(tender_doc, validation_result)
	mapped_status = _validation_status_to_tender_status(validation_result["status"])
	if mapped_status:
		tender_doc.tender_status = mapped_status

	if validation_result["blocks_generation"]:
		tender_doc.save()
		return {
			"ok": False,
			"message": (
				"Tender-pack preview was not generated because validation blocks generation."
			),
			"tender": tender_doc.name,
			"status": validation_result["status"],
			"validation_status": validation_result["status"],
			"blocks_generation": True,
			"message_count": len(validation_result["messages"]),
			"configuration_hash": validation_result["configuration_hash"],
		}

	required_forms = engine.resolve_required_forms(
		template, config, validation_result=validation_result
	)
	engine.write_required_forms_to_tender(tender_doc, required_forms)

	render_context = engine.build_render_context(
		template,
		config,
		lots=lots,
		boq_items=boq_items,
		validation_result=validation_result,
		required_forms=required_forms,
	)

	now_dt = frappe.utils.now_datetime()
	render_context["last_generated_at"] = frappe.utils.format_datetime(now_dt)

	tender_doc.generated_tender_pack_html = frappe.render_template(
		"templates/std_works_poc/tender_pack.html", render_context
	)
	tender_doc.last_generated_at = now_dt
	tender_doc.tender_status = "Tender Pack Generated"

	return _save_and_return(
		tender_doc,
		{
			"message": "Tender-pack preview generated.",
			"status": validation_result["status"],
			"validation_status": validation_result["status"],
			"blocks_generation": False,
			"configuration_hash": validation_result["configuration_hash"],
			"required_form_count": len(required_forms),
		},
	)


# ---------------------------------------------------------------------------
# Admin Console Step 5 — demo workspace HTML (read-only)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_std_demo_workspace_html(tender_name: str) -> dict[str, Any]:
	"""Return Jinja-rendered read-only summary HTML for STD demo workspace tenders."""
	from kentender_procurement.tender_management.services.std_demo_workspace import (
		is_std_demo_tender,
		render_demo_workspace_html,
	)

	tender_doc = _get_tender_doc_read(tender_name)
	if not is_std_demo_tender(tender_doc):
		return {
			"ok": False,
			"error": frappe._(
				"This tender is not part of the STD demo workspace (missing marker or POC template link)."
			),
			"html": "",
		}
	return {"ok": True, "html": render_demo_workspace_html(tender_doc)}


# ---------------------------------------------------------------------------
# Admin Console Step 6 — Required forms + BoQ inspectors (read-only)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_required_forms_inspection(tender_name: str) -> dict[str, Any]:
	"""Return structured required-forms inspection (+ HTML fragment)."""
	from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
		get_required_forms_inspection as build_inspection,
	)

	_get_tender_doc_read(tender_name)
	return build_inspection(tender_name)


@frappe.whitelist()
def get_boq_inspection(tender_name: str) -> dict[str, Any]:
	"""Return structured BoQ inspection (+ HTML fragment)."""
	from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
		get_boq_inspection as build_inspection,
	)

	_get_tender_doc_read(tender_name)
	return build_inspection(tender_name)


@frappe.whitelist()
def get_demo_inspector_summary(tender_name: str) -> dict[str, Any]:
	"""Combined inspectors for one client round-trip."""
	from kentender_procurement.tender_management.services.std_forms_boq_inspectors import (
		get_demo_inspector_summary as build_summary,
	)

	_get_tender_doc_read(tender_name)
	return build_summary(tender_name)


# ---------------------------------------------------------------------------
# Admin Console Step 7 — preview and audit viewer (read-only)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_preview_audit_summary(tender_name: str) -> dict[str, Any]:
	"""Structured preview status, completeness, validation, audit metadata + HTML."""
	from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
		get_preview_audit_summary as build_summary,
	)

	_get_tender_doc_read(tender_name)
	return build_summary(tender_name)


# ---------------------------------------------------------------------------
# Procurement Officer Tender Configuration POC — officer workflow (doc 8)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_available_std_templates_for_officer() -> list[dict[str, Any]]:
	"""STD templates the officer may use for this POC (controlled allowlist)."""
	from kentender_procurement.tender_management.services.officer_tender_config import (
		OFFICER_POC_TEMPLATE_CODE,
	)

	frappe.only_for(("System Manager", "Administrator", "Procurement Officer"))
	return frappe.get_all(
		"STD Template",
		filters={"template_code": OFFICER_POC_TEMPLATE_CODE},
		fields=["name", "template_code", "template_name", "template_short_name"],
	)


@frappe.whitelist()
def initialize_officer_tender_from_template(std_template: str) -> dict[str, Any]:
	"""Create a draft ``Procurement Tender`` linked to ``std_template`` and load template defaults."""
	frappe.only_for(("System Manager", "Administrator", "Procurement Officer"))
	if not std_template:
		frappe.throw(frappe._("std_template is required."), frappe.ValidationError)
	if not frappe.db.exists("STD Template", std_template):
		frappe.throw(frappe._("STD Template not found."), frappe.DoesNotExistError)
	std = frappe.get_doc("STD Template", std_template)
	frappe.has_permission("Procurement Tender", "create", throw=True)
	tender_doc = frappe.new_doc("Procurement Tender")
	tender_doc.std_template = std.name
	tender_doc.tender_title = std.template_short_name or std.template_name or "New tender"
	tender_doc.tender_reference = f"NEW-{frappe.generate_hash(length=8)}"
	tender_doc.procurement_method = "OPEN_COMPETITIVE_TENDERING"
	tender_doc.tender_scope = "NATIONAL"
	tender_doc.insert()
	load_template_defaults(tender_doc.name)
	return {"ok": True, "tender": tender_doc.name, "message": "Tender initialized from STD template."}


@frappe.whitelist()
def sync_officer_configuration(tender_name: str) -> dict[str, Any]:
	"""Merge guided top-level fields into ``configuration_json``; invalidate stale outputs."""
	from kentender_procurement.tender_management.services.officer_tender_config import (
		apply_officer_configuration_stale_marks,
		merge_officer_overlay_into_configuration,
	)

	tender_doc = _get_tender_doc(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	merged = merge_officer_overlay_into_configuration(config, tender_doc)
	engine.apply_config_to_tender_doc(tender_doc, merged)
	apply_officer_configuration_stale_marks(tender_doc)
	return _save_and_return(
		tender_doc,
		{"message": "Guided fields synced into configuration JSON."},
	)


@frappe.whitelist()
def mark_officer_configuration_changed(tender_name: str) -> dict[str, Any]:
	"""Mark validation and preview stale after configuration-affecting edits (without full sync)."""
	from kentender_procurement.tender_management.services.officer_tender_config import (
		apply_officer_configuration_stale_marks,
	)

	tender_doc = _get_tender_doc(tender_name)
	apply_officer_configuration_stale_marks(tender_doc)
	return _save_and_return(
		tender_doc,
		{"message": "Validation and preview marked stale; re-validate when ready."},
	)


@frappe.whitelist()
def validate_officer_configuration(tender_name: str) -> dict[str, Any]:
	"""Sync guided fields then run engine validation (doc 8 §9.3)."""
	sync_officer_configuration(tender_name)
	return validate_tender_configuration(tender_name)


@frappe.whitelist()
def get_officer_validation_feedback(tender_name: str) -> dict[str, Any]:
	"""Officer-facing validation summary from persisted rows."""
	from kentender_procurement.tender_management.services.officer_tender_config import (
		tender_status_to_officer_ux_label,
	)

	tender_doc = _get_tender_doc_read(tender_name)
	rows = _child_rows_to_dicts(tender_doc.get("validation_messages"))
	blockers = sum(
		1
		for m in rows
		if (m.get("severity") or "").upper() in ("BLOCKER", "ERROR")
		or m.get("blocks_generation") in (1, True, "1")
	)
	warnings = sum(1 for m in rows if (m.get("severity") or "").upper() == "WARNING")
	return {
		"ok": True,
		"tender": tender_doc.name,
		"validation_status": tender_doc.validation_status or "",
		"tender_status_ux": tender_status_to_officer_ux_label(tender_doc.tender_status),
		"blocker_count": blockers,
		"warning_count": warnings,
		"message_count": len(rows),
		"grouped": {"all": rows},
	}


@frappe.whitelist()
def can_generate_officer_preview(tender_name: str) -> dict[str, Any]:
	"""Whether preview generation is allowed (no blocking validation errors)."""
	tender_doc = _get_tender_doc_read(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	template = engine.load_template(tender_doc.std_template)
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))
	vr = engine.validate_config(template, config, lots=lots, boq_items=boq_items)
	bg = bool(vr.get("blocks_generation"))
	return {
		"ok": True,
		"can_generate": not bg,
		"validation_status": vr.get("status"),
		"blocks_generation": bg,
	}


@frappe.whitelist()
def generate_officer_required_forms(tender_name: str) -> dict[str, Any]:
	sync_officer_configuration(tender_name)
	return generate_required_forms(tender_name)


@frappe.whitelist()
def get_officer_required_forms_checklist(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services.officer_tender_config import (
		shape_officer_required_forms_checklist,
	)

	tender_doc = _get_tender_doc_read(tender_name)
	rows = _child_rows_to_dicts(tender_doc.get("required_forms"))
	shaped = shape_officer_required_forms_checklist(rows)
	return {
		"ok": True,
		"tender": tender_doc.name,
		**shaped,
		"stale_hint": (tender_doc.validation_status or "") == "Not Validated",
	}


@frappe.whitelist()
def generate_officer_representative_boq(tender_name: str) -> dict[str, Any]:
	sync_officer_configuration(tender_name)
	return generate_sample_boq(tender_name)


@frappe.whitelist()
def get_officer_boq_status(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services.officer_tender_config import (
		get_officer_boq_readiness_summary,
	)

	tender_doc = _get_tender_doc_read(tender_name)
	_require_std_template(tender_doc)
	config = _parse_configuration_json(tender_doc)
	boq_items = _child_rows_to_dicts(tender_doc.get("boq_items"))
	lots = _child_rows_to_dicts(tender_doc.get("lots"))
	lot_codes = frozenset(
		str(l.get("lot_code")) for l in lots if l.get("lot_code") not in (None, "")
	)
	summary = get_officer_boq_readiness_summary(
		config, boq_items, existing_lot_codes=lot_codes or None
	)
	return {"ok": True, "tender": tender_doc.name, **summary}


@frappe.whitelist()
def generate_officer_preview(tender_name: str) -> dict[str, Any]:
	sync_officer_configuration(tender_name)
	return generate_tender_pack_preview(tender_name)


@frappe.whitelist()
def get_officer_preview_audit_summary(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services.officer_tender_config import (
		get_officer_preview_audit_summary_enriched,
	)
	from kentender_procurement.tender_management.services.std_preview_audit_viewer import (
		render_preview_audit_viewer_html,
	)

	_get_tender_doc_read(tender_name)
	out = get_officer_preview_audit_summary_enriched(tender_name)
	out["html"] = render_preview_audit_viewer_html(out)
	return out


@frappe.whitelist()
def mark_officer_tender_ready_for_review(tender_name: str) -> dict[str, Any]:
	tender_doc = _get_tender_doc(tender_name)
	tender_doc.tender_status = "POC Demonstrated"
	return _save_and_return(
		tender_doc,
		{"message": "Tender marked ready for review (POC Demonstrated)."},
	)


@frappe.whitelist()
def reset_officer_tender_to_configuring(tender_name: str) -> dict[str, Any]:
	tender_doc = _get_tender_doc(tender_name)
	tender_doc.tender_status = "Configured"
	return _save_and_return(tender_doc, {"message": "Tender status reset to Configuring."})


# ---------------------------------------------------------------------------
# Doc 5 §16 / §24 — Works tender-stage hardening (WH-009)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def run_works_tender_stage_hardening(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services import works_tender_hardening

	return works_tender_hardening.run_works_tender_stage_hardening(tender_name)


@frappe.whitelist()
def validate_works_tender_stage(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services import works_tender_hardening_validation

	return works_tender_hardening_validation.validate_works_tender_stage(tender_name)


@frappe.whitelist()
def get_works_hardening_summary(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services import works_tender_hardening

	return works_tender_hardening.get_works_hardening_summary(tender_name)


@frappe.whitelist()
def get_works_hardening_findings(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services import works_tender_hardening

	return works_tender_hardening.get_works_hardening_findings(tender_name)


@frappe.whitelist()
def get_works_tender_stage_snapshot(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services import works_tender_hardening

	return works_tender_hardening.get_works_tender_stage_snapshot(tender_name)


@frappe.whitelist()
def get_officer_conditional_state_for_tender(tender_name: str) -> dict[str, Any]:
	from kentender_procurement.tender_management.services.officer_guided_field_registry import (
		doctype_fieldname_for_field_code,
		get_officer_guided_field_specs,
	)
	from kentender_procurement.tender_management.services.officer_tender_config import (
		get_officer_conditional_state,
		merge_officer_overlay_into_configuration,
	)

	tender_doc = _get_tender_doc_read(tender_name)
	cfg = _parse_configuration_json_optional(tender_doc)
	merged = merge_officer_overlay_into_configuration(cfg, tender_doc)
	state = get_officer_conditional_state(merged)
	hidden_codes = state.get("hidden_fields") or []
	hidden_fieldnames = [
		doctype_fieldname_for_field_code(str(fc)) for fc in hidden_codes if fc
	]
	guided_fieldnames = [s.doctype_fieldname for s in get_officer_guided_field_specs()]
	return {
		"ok": True,
		"tender": tender_doc.name,
		**state,
		"hidden_fieldnames": hidden_fieldnames,
		"guided_fieldnames": guided_fieldnames,
	}
