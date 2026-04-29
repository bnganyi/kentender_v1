"""STD workbench: resolve selected objects and server-side action availability (STD-CURSOR-1006)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from frappe.model.document import Document

from kentender_procurement.std_engine.services.authorization_service import check_std_permission

# UI object_type strings (search_std_workbench_objects) -> (DocType, business code field)
OBJECT_TYPE_RESOLUTION: dict[str, tuple[str, str]] = {
	"Template Family": ("STD Template Family", "template_code"),
	"Template Version": ("STD Template Version", "version_code"),
	"Applicability Profile": ("STD Applicability Profile", "profile_code"),
	"STD Instance": ("STD Instance", "instance_code"),
	"Generation Job": ("STD Generation Job", "generation_job_code"),
	"Generated Output": ("STD Generated Output", "output_code"),
	"Addendum Impact": ("STD Addendum Impact Analysis", "impact_analysis_code"),
	"Readiness Run": ("STD Readiness Run", "readiness_run_code"),
}

# Map UI object_type to authorization_service OBJECTS keys (uppercase)
UI_TYPE_TO_AUTH_KEY: dict[str, str] = {
	"Template Family": "TEMPLATE_FAMILY",
	"Template Version": "TEMPLATE_VERSION",
	"Applicability Profile": "APPLICABILITY_PROFILE",
	"STD Instance": "STD_INSTANCE",
	"Generation Job": "GENERATION_JOB",
	"Generated Output": "GENERATED_OUTPUT",
	"Addendum Impact": "ADDENDUM_IMPACT",
	"Readiness Run": "READINESS_RUN",
}


def resolve_std_document(object_type: str, object_code: str) -> tuple[str, str, Document] | None:
	"""Return (doctype, name, doc) or None if unknown type or missing code."""
	ot = (object_type or "").strip()
	code = (object_code or "").strip()
	if not ot or not code:
		return None
	spec = OBJECT_TYPE_RESOLUTION.get(ot)
	if not spec:
		return None
	doctype, code_field = spec
	name = frappe.db.get_value(doctype, {code_field: code}, "name")
	if not name:
		return None
	doc = frappe.get_doc(doctype, name)
	return doctype, name, doc


def _perm_read(doctype: str, name: str, user: str) -> bool:
	return bool(frappe.has_permission(doctype, ptype="read", doc=name, user=user))


def _perm_write(doctype: str, name: str, user: str) -> bool:
	return bool(frappe.has_permission(doctype, ptype="write", doc=name, user=user))


def _state_cards_for_doc(doctype: str, doc: Document) -> list[dict[str, str]]:
	cards: list[dict[str, str]] = []
	if doctype == "STD Template Version":
		cards.extend(
			[
				{"id": "version_status", "label": _("Version status"), "value": str(doc.get("version_status") or "—")},
				{"id": "legal_review", "label": _("Legal review"), "value": str(doc.get("legal_review_status") or "—")},
				{"id": "policy_review", "label": _("Policy review"), "value": str(doc.get("policy_review_status") or "—")},
			]
		)
	elif doctype == "STD Instance":
		cards.extend(
			[
				{"id": "instance_status", "label": _("Instance status"), "value": str(doc.get("instance_status") or "—")},
				{"id": "readiness", "label": _("Readiness"), "value": str(doc.get("readiness_status") or "—")},
			]
		)
	elif doctype == "STD Template Family":
		cards.append({"id": "family_status", "label": _("Family status"), "value": str(doc.get("family_status") or "—")})
	elif doctype == "STD Applicability Profile":
		cards.append({"id": "profile_status", "label": _("Profile status"), "value": str(doc.get("profile_status") or "—")})
	elif doctype == "STD Generation Job":
		cards.append({"id": "job_status", "label": _("Job status"), "value": str(doc.get("status") or "—")})
	elif doctype == "STD Generated Output":
		cards.append({"id": "output_status", "label": _("Output status"), "value": str(doc.get("status") or "—")})
	elif doctype == "STD Addendum Impact Analysis":
		cards.append({"id": "impact_status", "label": _("Impact status"), "value": str(doc.get("status") or "—")})
	elif doctype == "STD Readiness Run":
		cards.append({"id": "run_status", "label": _("Run status"), "value": str(doc.get("status") or "—")})
	return cards


def _blockers_and_warnings(doctype: str, doc: Document) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
	blockers: list[dict[str, str]] = []
	warnings: list[dict[str, str]] = []
	if doctype == "STD Template Version" and str(doc.get("version_status") or "") == "Validation Blocked":
		blockers.append(
			{
				"severity": "danger",
				"text": _("This template version is validation blocked; resolve structure or policy issues before activation."),
			}
		)
	if doctype == "STD Instance":
		if str(doc.get("readiness_status") or "") == "Blocked":
			blockers.append(
				{
					"severity": "danger",
					"text": _("Readiness is blocked; review readiness findings and generated outputs."),
				}
			)
		if str(doc.get("instance_status") or "") == "Blocked":
			warnings.append({"severity": "warning", "text": _("Instance is in a blocked workflow state.")})
	if doctype == "STD Generation Job" and str(doc.get("status") or "") == "Failed":
		warnings.append(
			{
				"severity": "warning",
				"text": _("Generation job failed; inspect job detail and logs from the DocType form."),
			}
		)
	return blockers, warnings


def _action_dict(
	*,
	action_id: str,
	label: str,
	allowed: bool,
	visible: bool,
	reason: str,
	requires_confirmation: bool,
	risk_level: str,
	route: list[str] | None = None,
	meta: dict[str, Any] | None = None,
	confirmation_message: str | None = None,
) -> dict[str, Any]:
	disabled = not allowed
	out: dict[str, Any] = {
		"id": action_id,
		"label": label,
		"allowed": allowed,
		"visible": visible,
		"disabled": disabled,
		"reason": reason or "",
		"requires_confirmation": bool(requires_confirmation and allowed),
		"risk_level": risk_level,
		"route": route,
	}
	if meta is not None:
		out["meta"] = meta
	if confirmation_message:
		out["confirmation_message"] = confirmation_message
	return out


def build_std_action_availability(object_type: str, object_code: str, actor: str | None = None) -> dict[str, Any]:
	"""Build actions, state cards, and blockers for a workbench selection. Authorization is server-side only."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": _("Not permitted")}

	resolved = resolve_std_document(object_type, object_code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": _("No document matches this type and code."),
			"object_type": object_type,
			"code": object_code,
		}

	doctype, name, doc = resolved
	auth_key = UI_TYPE_TO_AUTH_KEY.get((object_type or "").strip())

	has_read = _perm_read(doctype, name, user)
	has_write = _perm_write(doctype, name, user)

	actions: list[dict[str, Any]] = []

	open_route = ["Form", doctype, name] if has_read else None
	actions.append(
		_action_dict(
			action_id="open_in_desk",
			label=_("Open in Desk"),
			allowed=has_read,
			visible=True,
			reason="" if has_read else _("You do not have permission to read this document."),
			requires_confirmation=False,
			risk_level="low",
			route=open_route,
		)
	)

	edit_allowed = False
	edit_reason = _("You do not have permission to edit this document.")
	edit_requires_confirmation = False
	edit_risk = "medium"

	if doctype in ("STD Readiness Run", "STD Audit Event"):
		edit_reason = _("This document is read-only in the workbench.")
	elif has_write:
		edit_reason = ""
		if doctype == "STD Template Version" and auth_key:
			chk = check_std_permission(user, "STD_VERSION_EDIT_CONTENT", auth_key, object_code)
			edit_allowed = bool(chk.get("allowed"))
			if not edit_allowed:
				edit_reason = str(chk.get("message") or _("Edit is not allowed for this template version."))
			else:
				edit_requires_confirmation = bool(chk.get("requires_confirmation"))
				edit_risk = str(chk.get("risk_level") or "medium").lower()
		elif doctype == "STD Instance" and auth_key:
			chk = check_std_permission(user, "STD_INSTANCE_EDIT_CONTENT", auth_key, object_code)
			edit_allowed = bool(chk.get("allowed"))
			if not edit_allowed:
				edit_reason = str(chk.get("message") or _("Edit is not allowed for this instance."))
			else:
				edit_requires_confirmation = bool(chk.get("requires_confirmation"))
				edit_risk = str(chk.get("risk_level") or "medium").lower()
		else:
			edit_allowed = True

	edit_visible = doctype not in ("STD Readiness Run", "STD Audit Event")
	edit_confirm_msg = None
	if edit_allowed and edit_requires_confirmation:
		edit_confirm_msg = _("Open this document in Desk for editing? High-impact changes may affect tenders.")
	actions.append(
		_action_dict(
			action_id="edit_in_desk",
			label=_("Edit in Desk"),
			allowed=edit_allowed,
			visible=edit_visible,
			reason=edit_reason,
			requires_confirmation=edit_requires_confirmation,
			risk_level=edit_risk,
			route=(["Form", doctype, name] if edit_allowed else None),
			confirmation_message=edit_confirm_msg,
		)
	)

	create_allowed = False
	create_reason = _("Only active template versions can seed a new STD instance from here.")
	create_confirm = False
	create_risk = "medium"
	if doctype == "STD Template Version" and auth_key == "TEMPLATE_VERSION":
		ctx = {"template_version_code": object_code}
		chk = check_std_permission(user, "STD_INSTANCE_CREATE_FROM_TEMPLATE", auth_key, object_code, ctx)
		create_allowed = bool(chk.get("allowed"))
		create_reason = str(chk.get("message") or "") if not create_allowed else ""
		create_confirm = bool(chk.get("requires_confirmation"))
		create_risk = str(chk.get("risk_level") or "medium").lower()

	create_msg = _("Create a new STD instance from this template version?") if create_allowed and create_confirm else None
	actions.append(
		_action_dict(
			action_id="create_std_instance",
			label=_("New STD instance from version"),
			allowed=create_allowed,
			visible=doctype == "STD Template Version",
			reason=create_reason or ("" if create_allowed else _("Action not available.")),
			requires_confirmation=create_confirm,
			risk_level=create_risk,
			route=None,
			meta={"template_version_code": object_code} if create_allowed else None,
			confirmation_message=create_msg,
		)
	)

	publish_allowed = False
	publish_reason = _("Only applicable to STD instances.")
	publish_confirm = True
	publish_risk = "high"
	if doctype == "STD Instance" and auth_key == "STD_INSTANCE":
		ctx = {
			"requires_addendum": False,
			"addendum_completed": True,
			"requires_generated_models": False,
			"generated_models_ready": True,
		}
		chk = check_std_permission(user, "STD_INSTANCE_PUBLISH_LOCK", auth_key, object_code, ctx)
		publish_allowed = bool(chk.get("allowed"))
		publish_reason = str(chk.get("message") or "") if not publish_allowed else ""
		publish_confirm = bool(chk.get("requires_confirmation", True))
		publish_risk = str(chk.get("risk_level") or "high").lower()

	pub_msg = _("Open the instance in Desk to review publish and lock options. Continue?") if publish_allowed else None
	actions.append(
		_action_dict(
			action_id="publish_lock_instance",
			label=_("Publish / lock instance"),
			allowed=publish_allowed,
			visible=doctype == "STD Instance",
			reason=publish_reason or ("" if publish_allowed else _("Action not available in current state.")),
			requires_confirmation=publish_confirm,
			risk_level=publish_risk,
			route=(["Form", doctype, name] if publish_allowed else None),
			confirmation_message=pub_msg,
		)
	)

	state_cards = _state_cards_for_doc(doctype, doc)
	blockers, warnings = _blockers_and_warnings(doctype, doc)

	title = str(doc.get("version_label") or doc.get("template_title") or doc.get("profile_title") or object_code)
	if doctype == "STD Instance":
		title = str(doc.get("tender_code") or doc.get("instance_code") or object_code)

	return {
		"ok": True,
		"doctype": doctype,
		"name": name,
		"object_type": object_type,
		"code": object_code,
		"title": title,
		"state_cards": state_cards,
		"actions": actions,
		"blockers": blockers,
		"warnings": warnings,
	}


def validate_actor_override(actor: str | None) -> str:
	"""Return effective user for permission checks. Only privileged users may pass actor != session user."""
	target = (actor or "").strip() or frappe.session.user
	if not target or target == "Guest":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if target == frappe.session.user:
		return target
	if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles(frappe.session.user):
		return target
	frappe.throw(_("Not permitted to evaluate actions for another user."), frappe.PermissionError)


__all__ = [
	"OBJECT_TYPE_RESOLUTION",
	"build_std_action_availability",
	"resolve_std_document",
	"validate_actor_override",
]
