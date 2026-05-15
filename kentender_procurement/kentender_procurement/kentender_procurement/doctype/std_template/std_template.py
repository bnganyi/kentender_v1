# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

from kentender_procurement.tender_management.services.std_template_engine import (
	_child_rows_to_dicts,
)
from kentender_procurement.tender_management.services import std_template_engine as engine
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_events import (
	write_std_template_lifecycle_event,
)
from kentender_procurement.tender_management.services.std_package_validation import (
	build_rule_trace_report_html,
	build_validation_report_html,
	run_package_validation,
)
from kentender_procurement.tender_management.services.std_package_viewer import build_api_payload
from kentender_procurement.tender_management.services.std_template_loader import import_std_works_poc_template
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template as _lifecycle_activate_std_template,
	approve_std_template as _lifecycle_approve_std_template,
	archive_std_template as _lifecycle_archive_std_template,
	reinstate_std_template as _lifecycle_reinstate_std_template,
	reject_std_template as _lifecycle_reject_std_template,
	retire_std_template as _lifecycle_retire_std_template,
	return_std_template_for_correction as _lifecycle_return_std_template_for_correction,
	submit_std_template_for_approval as _lifecycle_submit_std_template_for_approval,
	supersede_std_template as _lifecycle_supersede_std_template,
	suspend_std_template as _lifecycle_suspend_std_template,
)
from kentender_procurement.tender_management.services.std_template_governance_snapshot import (
	generate_std_template_governance_snapshot as _generate_std_template_governance_snapshot,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	get_std_template_usage_impact as _get_std_template_usage_impact,
)
from kentender_procurement.tender_management.services.std_template_governance_validation import (
	clear_std_template_validation_findings,
	run_std_template_validation as _run_std_template_validation,
)


class STDTemplate(Document):
	"""STD-WORKS-POC: imported STD template package (metadata + JSON payload). Step 9 — schema only."""

	def before_validate(self) -> None:
		if self.is_new():
			self._gov_prev = None
		else:
			self._gov_prev = frappe.get_doc("STD Template", self.name)

	def validate(self) -> None:
		# STD-GOV-002 — safety net when rows bypass loader (pack §7.2 / §7.4).
		if not self.get("source_authority") and self.get("authority"):
			self.source_authority = self.authority
		if not self.get("lifecycle_status"):
			self.lifecycle_status = gov.STATUS_IMPORTED
		if not (self.get("template_version") or "").strip():
			v = (self.get("version_label") or "").strip() or (self.get("package_version") or "").strip()
			if v:
				self.template_version = v

		if self.is_new():
			if self.get("imported_at") in (None, ""):
				self.imported_at = now_datetime()
			if not self.get("imported_by"):
				self.imported_by = frappe.session.user

		if int(self.get("is_governed_version") or 0) and (str(self.get("package_json") or "").strip()):
			if not (str(self.get("package_hash") or "").strip()):
				frappe.throw(
					_("Governed STD Template with package content requires package_hash."),
					frappe.ValidationError,
				)

		if not getattr(self.flags, "skip_std_template_guards", False):
			self._std_template_enforce_package_mutation_guards()

		self._std_template_refresh_derived_flags()

	def _std_template_field_changed(self, prev: Document, fieldname: str) -> bool:
		a = self.get(fieldname)
		b = prev.get(fieldname)
		if fieldname in ("package_json", "manifest_json"):
			return (str(a or "").strip()) != (str(b or "").strip())
		return a != b

	def _std_template_emit_guard_event(self, event_code: str, payload: dict[str, Any]) -> None:
		try:
			d = frappe.get_doc("STD Template", self.name)
			write_std_template_lifecycle_event(d, event_code, "guard", payload, save=True)
		except Exception:
			frappe.log_error("STD Template governance guard audit failed")

	def _std_template_enforce_package_mutation_guards(self) -> None:
		prev = getattr(self, "_gov_prev", None)
		if not prev:
			return

		prev_status = prev.lifecycle_status or gov.STATUS_IMPORTED
		next_status = self.lifecycle_status or gov.STATUS_IMPORTED
		state_locked = (prev_status in gov.PROTECTED_STATES) or (next_status in gov.PROTECTED_STATES)
		usage_locked = (
			int(prev.tender_usage_count or 0) > 0
			or len(prev.get("template_usage") or []) > 0
			or int(self.tender_usage_count or 0) > 0
			or len(self.get("template_usage") or []) > 0
		)
		payload_locked = int(prev.get("payload_locked") or 0)
		locked_usage_flag = int(prev.get("locked_due_to_usage") or 0)
		mutation_flag = int(prev.get("mutation_blocked") or 0)

		changed = [
			fn
			for fn in gov.PROTECTED_PACKAGE_FIELD_NAMES
			if self.meta.has_field(fn) and self._std_template_field_changed(prev, fn)
		]
		if not changed:
			return

		block = (
			state_locked
			or usage_locked
			or bool(payload_locked)
			or bool(locked_usage_flag)
			or bool(mutation_flag)
		)
		if not block:
			return

		detail = {
			"changed_fields": sorted(changed),
			"from_lifecycle_status": prev_status,
			"package_hash": self.get("package_hash"),
		}
		self._std_template_emit_guard_event(gov.EVT_MUTATION_BLOCKED, detail)
		frappe.throw(
			_("Package fields are immutable in the current lifecycle or usage state ({0}).").format(
				", ".join(sorted(changed))
			),
			frappe.ValidationError,
		)

	def _std_template_refresh_derived_flags(self) -> None:
		usage_len = len(self.get("template_usage") or [])
		if int(self.tender_usage_count or 0) != usage_len:
			self.tender_usage_count = usage_len

		lc = self.lifecycle_status or gov.STATUS_IMPORTED
		ph = (str(self.package_hash or "")).strip()
		lvph = (str(self.latest_validation_package_hash or "")).strip()
		# ``return_std_template_for_correction`` clears ``validation_is_current``; do not
		# re-derive 1 from hash equality while in Returned (GOV-007). Other states use hash match.
		if lc == gov.STATUS_RETURNED:
			self.validation_is_current = 0
		else:
			self.validation_is_current = 1 if ph and lvph and ph == lvph else 0

		self.payload_locked = 1 if lc in gov.PROTECTED_STATES else 0
		self.is_suspended = 1 if lc == gov.STATUS_SUSPENDED else 0
		self.is_historical = 1 if lc in gov.HISTORICAL_LIFECYCLE_STATUSES else 0

		usage_locked = usage_len > 0
		self.locked_due_to_usage = 1 if usage_locked else 0
		self.mutation_blocked = 1 if (lc in gov.PROTECTED_STATES or usage_locked) else 0

		governed = int(self.get("is_governed_version") or 0)
		self.delete_blocked = 1 if (governed or usage_locked) else 0

		if lc != gov.STATUS_ACTIVE:
			self.allowed_for_tender_creation = 0

	def on_trash(self) -> None:
		usage_len = len(self.get("template_usage") or [])
		has_usage = int(self.tender_usage_count or 0) > 0 or usage_len > 0
		if has_usage:
			try:
				d = frappe.get_doc("STD Template", self.name)
				write_std_template_lifecycle_event(
					d,
					gov.EVT_DELETE_BLOCKED,
					"guard",
					{"reason": "tender_usage_exists"},
					save=True,
				)
			except Exception:
				frappe.log_error("STD Template delete-blocked audit failed")
			frappe.throw(
				_("Cannot delete an STD Template that has tender usage."),
				frappe.ValidationError,
			)

		privileged = (
			frappe.session.user == "Administrator"
			or "System Manager" in frappe.get_roles()
			or bool(getattr(self.flags, "ignore_permissions", False))
		)
		if int(self.delete_blocked or 0) and not privileged:
			try:
				d = frappe.get_doc("STD Template", self.name)
				write_std_template_lifecycle_event(
					d,
					gov.EVT_DELETE_BLOCKED,
					"guard",
					{"reason": "delete_blocked"},
					save=True,
				)
			except Exception:
				frappe.log_error("STD Template delete-blocked audit failed")
			frappe.throw(
				_("Deleting this governed STD Template is blocked."),
				frappe.ValidationError,
			)


ALLOWED_PACKAGE_COMPONENTS: frozenset[str] = frozenset(
	{"manifest", "sections", "fields", "rules", "forms", "render_map", "sample_tender", "full_package"}
)


@frappe.whitelist()
def get_template_package_summary(template_name: str) -> dict:
	"""Admin Console Step 3 — structured summaries + HTML for read-only package viewer."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {"ok": False, "error": _("Invalid package_json: {0}").format(str(e))}
	return build_api_payload(doc, pkg)


@frappe.whitelist()
def get_template_package_component(template_name: str, component_name: str) -> dict:
	"""Return one package component as pretty-printed JSON (read-only)."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	if not component_name:
		frappe.throw(_("component_name is required"))
	if component_name not in ALLOWED_PACKAGE_COMPONENTS:
		frappe.throw(_("Unknown component_name"), frappe.ValidationError)

	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {"ok": False, "error": _("Invalid package_json: {0}").format(str(e))}

	if component_name == "full_package":
		body = pkg
	else:
		body = pkg.get(component_name)

	text = json.dumps(body, indent=2, sort_keys=True, default=str)
	return {"ok": True, "component_name": component_name, "json": text}


@frappe.whitelist()
def validate_std_package(template_name: str) -> dict[str, Any]:
	"""Admin Console Step 4 — structured package validation (read-only)."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		pkg = json.loads(doc.package_json or "{}")
	except json.JSONDecodeError as e:
		return {
			"ok": False,
			"error": _("Invalid package_json: {0}").format(str(e)),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	result = run_package_validation(doc, pkg)
	result["html"] = build_validation_report_html(result)
	return result


@frappe.whitelist()
def trace_std_rules_for_sample(template_name: str, variant_code: str | None = None) -> dict[str, Any]:
	"""Admin Step 4 — rule trace for primary sample or a scenario variant."""
	if not template_name:
		frappe.throw(_("template_name is required"))
	doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	try:
		loaded = engine.load_template(template_name)
	except frappe.DoesNotExistError:
		raise
	except Exception as e:
		return {"ok": False, "error": str(e), "html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>"}
	try:
		cfg = engine.load_sample_config(loaded, variant_code or None)
		lots = engine.load_sample_lots(loaded, variant_code or None)
		boq = engine.load_sample_boq_rows(loaded, variant_code or None)
	except ValueError as e:
		return {
			"ok": False,
			"error": str(e),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	trace = engine.trace_rules(loaded, cfg, lots=lots, boq_items=boq)
	trace_source = "PRIMARY_SAMPLE" if not variant_code else "SAMPLE_VARIANT"
	out: dict[str, Any] = {
		"ok": bool(trace.get("ok")),
		"trace_source": trace_source,
		"variant_code": variant_code,
		"tender": None,
		"template_code": trace.get("template_code"),
		"configuration_hash": trace.get("configuration_hash"),
		"summary": trace.get("summary"),
		"rules": trace.get("rules"),
		"validation_result": trace.get("validation_result"),
	}
	out["html"] = build_rule_trace_report_html(out)
	return out


@frappe.whitelist()
def trace_std_rules_for_tender(tender_name: str) -> dict[str, Any]:
	"""Admin Step 4 — rule trace for an existing Procurement Tender."""
	if not tender_name:
		frappe.throw(_("tender_name is required"))
	tender = frappe.get_doc("Procurement Tender", tender_name)
	if not frappe.has_permission("Procurement Tender", "read", doc=tender):
		frappe.throw(_("Not permitted to read Procurement Tender"), frappe.PermissionError)
	if not tender.std_template:
		err = _("Procurement Tender has no STD Template linked.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	raw = tender.configuration_json
	if not raw:
		err = _("configuration_json is empty on this tender.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	try:
		cfg = json.loads(raw)
	except json.JSONDecodeError as e:
		return {
			"ok": False,
			"error": str(e),
			"html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>",
		}
	if not isinstance(cfg, dict):
		err = _("configuration_json must be a JSON object.")
		return {"ok": False, "error": str(err), "html": f"<div class=\"alert alert-warning\">{frappe.utils.escape_html(str(err))}</div>"}
	lots = _child_rows_to_dicts(getattr(tender, "lots", None))
	boq = _child_rows_to_dicts(getattr(tender, "boq_items", None))
	try:
		loaded = engine.load_template(tender.std_template)
	except frappe.DoesNotExistError:
		raise
	except Exception as e:
		return {"ok": False, "error": str(e), "html": f"<div class=\"alert alert-danger\">{frappe.utils.escape_html(str(e))}</div>"}
	trace = engine.trace_rules(loaded, cfg, lots=lots, boq_items=boq)
	out: dict[str, Any] = {
		"ok": bool(trace.get("ok")),
		"trace_source": "DEMO_TENDER",
		"variant_code": None,
		"tender": tender.name,
		"template_code": trace.get("template_code"),
		"configuration_hash": trace.get("configuration_hash"),
		"summary": trace.get("summary"),
		"rules": trace.get("rules"),
		"validation_result": trace.get("validation_result"),
	}
	out["html"] = build_rule_trace_report_html(out)
	return out


@frappe.whitelist()
def create_or_open_std_demo_tender(
	template_name: str,
	variant_code: str | None = None,
) -> dict[str, Any]:
	"""Admin Step 5 — create a new demo Procurement Tender linked to this STD Template (primary or variant sample)."""
	if variant_code in (None, "", "null"):
		variant_code = None
	if not template_name:
		frappe.throw(_("template_name is required"))
	std_doc = frappe.get_doc("STD Template", template_name)
	if not frappe.has_permission("STD Template", "read", doc=std_doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	if not frappe.has_permission("Procurement Tender", "create"):
		frappe.throw(_("Not permitted to create Procurement Tender"), frappe.PermissionError)

	import time

	t_ref = f"STD-DEMO-{int(time.time())}"
	marker = (
		"STD DEMO WORKSPACE — POC demonstration record for STD-WORKS-POC. "
		"Not for production procurement."
	)
	tender = frappe.new_doc("Procurement Tender")
	tender.naming_series = "PT-.YYYY.-.#####"
	tender.tender_title = _("STD-WORKS-POC Demo Tender")
	tender.tender_reference = t_ref
	tender.std_template = std_doc.name
	tender.procurement_method = "OPEN_COMPETITIVE_TENDERING"
	tender.tender_scope = "NATIONAL"
	tender.poc_notes = f"{marker} template={std_doc.name}"
	try:
		engine.populate_sample_tender(tender, variant_code=variant_code or None)
	except ValueError as e:
		return {"ok": False, "error": str(e), "message": str(e)}
	# Sample config overwrites title/reference; restore demo workspace identity.
	tender.tender_reference = t_ref
	tender.tender_title = _("STD-WORKS-POC Demo Tender")
	tender.tender_status = "Configured"
	tender.validation_status = "Not Validated"
	tender.set("validation_messages", [])
	tender.set("required_forms", [])
	tender.insert()
	frappe.db.commit()
	return {
		"ok": True,
		"message": _("Demo tender ready."),
		"tender": tender.name,
		"template_code": tender.template_code or std_doc.template_code,
		"variant_code": variant_code,
		"route": f"/app/procurement-tender/{tender.name}",
	}


@frappe.whitelist()
def reimport_std_template_package(template_name: str | None = None) -> dict:
	"""Re-run controlled STD-WORKS-POC seed import (Admin Console Step 3)."""
	# Spec: System Manager / technical admin — restrict to elevated roles only.
	roles = set(frappe.get_roles())
	if not roles.intersection({"System Manager", "Administrator"}):
		frappe.throw(
			_("Re-import is restricted to System Manager or Administrator."),
			frappe.PermissionError,
		)
	# template_name accepted for API symmetry; loader is fixed to POC package.
	return import_std_works_poc_template()


# --- STD-GOV-011 — Desk whitelisted governance API (doc 7 §20) -----------------


def _desk_guest_blocked() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _desk_read_std_template(std_template: str) -> Any:
	_desk_guest_blocked()
	doc = frappe.get_doc("STD Template", std_template)
	if not frappe.has_permission("STD Template", "read", doc=doc):
		frappe.throw(_("Not permitted to read STD Template"), frappe.PermissionError)
	return doc


def _desk_replace_roles_ok(doc: Any) -> bool:
	roles = set(frappe.get_roles())
	if "System Manager" in roles or frappe.session.user == "Administrator":
		return True
	if "STD Template Administrator" in roles:
		return True
	if "STD Template Importer" in roles and (doc.get("imported_by") or "") == frappe.session.user:
		return True
	return False


@frappe.whitelist()
def replace_std_template_package(
	std_template: str,
	package_json: str,
	manifest_json: str | None = None,
	reason: str | None = None,
) -> dict[str, Any]:
	"""Controlled package replacement (doc 3 §§8.1, 8.3, 8.5; pack §20)."""
	_desk_guest_blocked()
	text = (reason or "").strip()
	if not text:
		frappe.throw(_("Replacement reason is required."), frappe.ValidationError)

	doc = frappe.get_doc("STD Template", std_template)
	if doc.lifecycle_status not in gov.CONTROLLED_REPLACEMENT_STATES:
		frappe.throw(
			_("Package replacement is not allowed in lifecycle status {0}.").format(doc.lifecycle_status),
			frappe.ValidationError,
		)
	if not _desk_replace_roles_ok(doc):
		frappe.throw(_("Not permitted to replace this package."), frappe.PermissionError)
	if not frappe.has_permission("STD Template", "write", doc=doc):
		frappe.throw(_("Not permitted to update STD Template"), frappe.PermissionError)

	try:
		parsed_pkg: Any = json.loads(package_json)
	except json.JSONDecodeError as exc:
		frappe.throw(_("package_json is not valid JSON: {0}").format(str(exc)), frappe.ValidationError)
	if not isinstance(parsed_pkg, dict):
		frappe.throw(_("package_json must be a JSON object."), frappe.ValidationError)

	manifest_src = (manifest_json if manifest_json is not None else (doc.get("manifest_json") or "{}")).strip()
	try:
		parsed_man: Any = json.loads(manifest_src or "{}")
	except json.JSONDecodeError as exc:
		frappe.throw(_("manifest_json is not valid JSON: {0}").format(str(exc)), frappe.ValidationError)
	if not isinstance(parsed_man, dict):
		frappe.throw(_("manifest_json must be a JSON object."), frappe.ValidationError)

	prev_status = doc.lifecycle_status
	prev_hash = (doc.get("package_hash") or "").strip()
	new_hash = gov.compute_std_package_hash(parsed_pkg)

	doc.flags.skip_std_template_guards = True
	clear_std_template_validation_findings(doc)
	doc.package_json = json.dumps(parsed_pkg, indent=2, ensure_ascii=False)
	doc.manifest_json = json.dumps(parsed_man, indent=2, ensure_ascii=False)
	doc.package_hash = new_hash
	doc.lifecycle_status = gov.STATUS_IMPORTED
	doc.latest_validation_status = gov.VALIDATION_NOT_RUN
	doc.latest_validation_run_id = None
	doc.latest_validation_at = None
	doc.latest_validation_by = None
	doc.latest_validation_package_hash = None
	doc.latest_validation_result_json = None
	doc.critical_finding_count = 0
	doc.warning_finding_count = 0
	doc.info_finding_count = 0
	doc.validation_is_current = 0

	write_std_template_lifecycle_event(
		doc,
		gov.EVT_PACKAGE_REPLACED,
		"import",
		{
			"reason": text[:140],
			"previous_package_hash": prev_hash,
			"new_package_hash": new_hash,
			"previous_lifecycle_status": prev_status,
		},
		from_status=prev_status,
		to_status=doc.lifecycle_status,
		reason=text,
		save=False,
	)
	doc.save(ignore_permissions=True)
	return {
		"ok": True,
		"std_template": doc.name,
		"package_hash": new_hash,
		"lifecycle_status": doc.lifecycle_status,
	}


@frappe.whitelist()
def run_std_template_validation(std_template: str) -> dict[str, Any]:
	"""Desk entrypoint for STD-GOV-006 validation (doc 7 §20)."""
	return _run_std_template_validation(std_template)


@frappe.whitelist()
def submit_std_template_for_approval(std_template: str, comment: str | None = None) -> dict[str, Any]:
	return _lifecycle_submit_std_template_for_approval(std_template, comment)


@frappe.whitelist()
def return_std_template_for_correction(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_return_std_template_for_correction(std_template, reason)


@frappe.whitelist()
def reject_std_template(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_reject_std_template(std_template, reason)


@frappe.whitelist()
def approve_std_template(
	std_template: str, comments: str, override_reason: str | None = None
) -> dict[str, Any]:
	return _lifecycle_approve_std_template(std_template, comments, override_reason)


@frappe.whitelist()
def activate_std_template(
	std_template: str,
	reason: str,
	active_from: str | None = None,
	active_until: str | None = None,
	is_default_active_version: int | str | None = None,
) -> dict[str, Any]:
	use_default = True
	if is_default_active_version is not None and str(is_default_active_version).strip() != "":
		use_default = bool(cint(is_default_active_version))
	return _lifecycle_activate_std_template(
		std_template, reason, active_from, active_until, use_default
	)


@frappe.whitelist()
def suspend_std_template(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_suspend_std_template(std_template, reason)


@frappe.whitelist()
def reinstate_std_template(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_reinstate_std_template(std_template, reason)


@frappe.whitelist()
def supersede_std_template(
	std_template: str,
	replacement_template: str,
	reason: str,
	effective_date: str | None = None,
) -> dict[str, Any]:
	return _lifecycle_supersede_std_template(std_template, replacement_template, reason, effective_date)


@frappe.whitelist()
def retire_std_template(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_retire_std_template(std_template, reason)


@frappe.whitelist()
def archive_std_template(std_template: str, reason: str) -> dict[str, Any]:
	return _lifecycle_archive_std_template(std_template, reason)


@frappe.whitelist()
def generate_std_template_governance_snapshot(
	std_template: str, snapshot_type: str | None = None
) -> dict[str, Any]:
	if snapshot_type:
		return _generate_std_template_governance_snapshot(std_template, snapshot_type=snapshot_type)
	return _generate_std_template_governance_snapshot(std_template)


@frappe.whitelist()
def get_std_template_usage_impact(std_template: str) -> dict[str, Any]:
	return _get_std_template_usage_impact(std_template)


@frappe.whitelist()
def get_std_template_governance_summary(std_template: str) -> dict[str, Any]:
	doc = _desk_read_std_template(std_template)
	ph = (doc.get("package_hash") or "").strip()
	return {
		"ok": True,
		"std_template": doc.name,
		"lifecycle_status": doc.lifecycle_status,
		"latest_validation_status": doc.latest_validation_status,
		"validation_is_current": int(doc.get("validation_is_current") or 0),
		"tender_usage_count": int(doc.get("tender_usage_count") or 0),
		"allowed_for_tender_creation": int(doc.get("allowed_for_tender_creation") or 0),
		"payload_locked": int(doc.get("payload_locked") or 0),
		"package_hash_prefix": ph[:16],
		"has_governance_snapshot": bool((doc.get("latest_governance_snapshot_hash") or "").strip()),
	}


@frappe.whitelist()
def get_std_template_audit_timeline(std_template: str) -> dict[str, Any]:
	doc = _desk_read_std_template(std_template)
	events: list[dict[str, Any]] = []
	for row in doc.get("lifecycle_events") or []:
		events.append(
			{
				"event_code": row.event_code,
				"event_type": row.event_type,
				"event_at": str(row.event_at) if getattr(row, "event_at", None) else None,
				"actor": row.actor,
				"from_status": row.from_status,
				"to_status": row.to_status,
				"reason": row.reason,
			}
		)
	return {"ok": True, "std_template": doc.name, "events": events}
