# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 reads — `GetTendersWorkspace`, `GetTenderStart`,
`GetTender`, `GetTenderReview`. Verdict-first (KT-STD-001 §3A): the
Forbidden verdict is resolved before anything renders; record reads mask
outsiders as not-found (§8); permitted actions are server-computed from
the actor's responsibilities and the exact state (§11.1(1)); reads create
no record, task, decision, render, confirmation or event."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.authorization import is_technical
from kentender_procurement.tenders.services import compatibility, controls, correction, documents, draft_commands, evidence, handoff_gateway, lifecycle, review, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.services.tender_roles import FORBIDDEN_RESPONSIBILITIES, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

PAGE = "tenders"
STATUS_FILTERS = (
	("ready", "Ready to start"), ("draft", "Draft"), ("returned", "Returned"), ("awaiting_approval", "Awaiting procurement approval"),
	("approved", "Awaiting publication authorisation"), ("publishing", "Publication confirmation required"), ("published", "Published — open"),
	("ended", "Submission period ended"), ("cancelled", "Cancelled"), ("correction", "Requisition correction requested"),
)
TENDER_FIELDS = [
	"name", "tender_reference", "requirement_title", "requisition_reference", "requisition_handoff", "plan_item_id", "fiscal_year", "overall_status",
	"current_version", "approved_version", "publication", "published_at", "submission_deadline", "lead_org_unit", "contributing_org_unit_ids", "record_version", "modified",
]


def _can(fn, *args, **kwargs) -> bool:
	try:
		fn(*args, **kwargs)
		return True
	except (TendersError, frappe.DoesNotExistError, frappe.PermissionError):
		return False


def _full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user) if user else ""


def _ou_label(unit: str) -> str:
	if not unit:
		return ""
	for field in ("unit_name", "organisation_unit_name", "name"):
		if frappe.db.has_column("Organisation Unit", field):
			return cstr(frappe.db.get_value("Organisation Unit", unit, field) or unit)
	return cstr(unit)


def actor_roles(actor: str) -> dict[str, bool]:
	return {
		"officer": authz.has_site_role(ROLE_PROCUREMENT_OFFICER, actor),
		"hopf": authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor),
		"ao": authz.has_site_role(ROLE_ACCOUNTING_OFFICER, actor),
		"auditor": authz.can_read_site(ROLE_AUDITOR, actor),
		"technical": is_technical(actor),
	}


# --------------------------------------------------------------------------
# GetTendersWorkspace
# --------------------------------------------------------------------------


def _first_attention_task(version) -> tuple[str, str]:
	statuses = draft_commands.task_statuses(version)
	for key, label in (("details", "Tender details"), ("requirements", "Supplier requirements"), ("review", "Review")):
		if statuses.get(key) != "Complete":
			return key, label
	return "review", "Review"


def _was_returned(version) -> bool:
	if not version.predecessor_version:
		return False
	return cstr(frappe.db.get_value("Tender Version", version.predecessor_version, "status")) == "Returned"


def _outstanding_confirmations(root) -> list[str]:
	if not root.publication:
		return []
	return frappe.get_all("Tender Channel Confirmation", filters={"publication": root.publication, "subject_type": "Publication", "status": "Awaiting confirmation"}, pluck="channel_label", order_by="creation asc")


def tender_row(root, actor: str, roles: dict[str, bool]) -> dict[str, Any]:
	version = frappe.get_doc("Tender Version", root.current_version) if root.current_version else None
	status = cstr(root.overall_status)
	key, label, secondary, action_key, action_label, route = "", status, "", "view", "View", [PAGE, root.tender_reference]
	if status == "Draft" and version is not None:
		task_key, task_label = _first_attention_task(version)
		returned = _was_returned(version)
		key = "returned" if returned else "draft"
		if roles["officer"]:
			label = f"{'Returned to you' if returned else 'Draft'} — {task_label} need{'s' if task_label == 'Review' else ''} attention"
			action_key, action_label, route = ("correct" if returned else "continue"), ("Correct" if returned else "Continue"), [PAGE, root.tender_reference, task_key]
		else:
			label = "Returned for correction" if returned else "Draft"
	elif status == "Awaiting procurement approval":
		key = "awaiting_approval"
		if roles["hopf"]:
			label, action_key, action_label = "Awaiting your approval", "review", "Review"
	elif status == "Approved":
		key = "approved"
		label = "Awaiting publication authorisation"
		if roles["ao"]:
			label, action_key, action_label = "Awaiting your publication decision", "review_publication", "Review publication"
		elif roles["hopf"]:
			label = "Approved — awaiting publication authorisation"
	elif status == "Publication authorised":
		key = "publishing"
		outstanding = _outstanding_confirmations(root)
		label = "Publication confirmation required"
		secondary = " and ".join(o.lower() if i else o for i, o in enumerate(outstanding)) + (" confirmations" if outstanding else "")
		if roles["hopf"]:
			action_key, action_label, route = "complete_confirmations", "Complete confirmations", [PAGE, root.tender_reference, "publication"]
	elif status == "Published — open":
		key = "published"
		label = f"Published — open until {serializer.fmt_datetime_short(root.submission_deadline)}" if root.submission_deadline else "Published — open"
	elif status == "Submission period ended":
		key = "ended"
	elif status == "Cancelled":
		key = "cancelled"
	elif status == "Requisition correction requested":
		key = "correction"
	if not (roles["officer"] or roles["hopf"] or roles["ao"]):
		action_key, action_label, route = "view", "View", [PAGE, root.tender_reference]
		if key in ("draft", "returned"):
			label = "Draft"
	return {
		"kind": "tender", "tender": root.name, "tender_reference": root.tender_reference, "purchase": cstr(root.requirement_title), "plan_item_id": cstr(root.plan_item_id),
		"requisition_reference": cstr(root.requisition_reference), "fiscal_year": cstr(root.fiscal_year), "status_key": key, "status_label": label, "secondary": secondary,
		"required_by": _required_by(root, version), "action_key": action_key, "action_label": action_label, "route": route, "record_version": int(root.record_version or 0), "modified": cstr(root.modified),
	}


def _required_by(root, version) -> str:
	if version is None:
		return ""
	latest = snap.load(version).get("latest_delivery_date")
	return serializer.fmt_date_short(latest) if latest else ""


def start_row(handoff: dict[str, Any], *, can_start: bool) -> dict[str, Any]:
	return {
		"kind": "start", "tender": "", "tender_reference": "Not started", "handoff": handoff["handoff"], "purchase": cstr(handoff.get("requirement_title")), "plan_item_id": cstr(handoff.get("plan_item_id")),
		"requisition_reference": cstr(handoff.get("requisition_reference")), "fiscal_year": "", "status_key": "ready", "status_label": "Ready to start", "secondary": "",
		"required_by": cstr(handoff.get("latest_delivery_date_label") or serializer.fmt_date_short(handoff.get("latest_delivery_date"))),
		"action_key": "start" if can_start else "view", "action_label": "Start Tender" if can_start else "View", "route": [PAGE, "new", handoff["handoff"]] if can_start else [PAGE], "record_version": 0, "modified": "",
	}


def _counts(rows: list[dict[str, Any]], roles: dict[str, bool]) -> list[dict[str, Any]]:
	by_key: dict[str, int] = {}
	for row in rows:
		by_key[row["status_key"]] = by_key.get(row["status_key"], 0) + 1
	out = []
	if roles["officer"]:
		out += [
			{"key": "ready", "label": "Ready to start", "value": by_key.get("ready", 0), "sub": "Approved requisitions awaiting a tender"},
			{"key": "draft", "label": "Drafts", "value": by_key.get("draft", 0), "sub": "Started, not yet submitted"},
			{"key": "returned", "label": "Returned to me", "value": by_key.get("returned", 0), "sub": "Sent back for correction"},
		]
	if roles["hopf"]:
		out.append({"key": "awaiting_approval", "label": "Awaiting procurement approval", "value": by_key.get("awaiting_approval", 0), "sub": "Tenders submitted for procurement approval"})
		if by_key.get("publishing"):
			out.append({"key": "publishing", "label": "Evidence outstanding", "value": by_key.get("publishing", 0), "sub": "Published channels awaiting confirmation"})
	if roles["ao"]:
		out.append({"key": "approved", "label": "Awaiting publication authorisation", "value": by_key.get("approved", 0), "sub": "Approved tenders awaiting a publication decision"})
	return out


def get_tenders_workspace(*, search: str = "", status: str = "", fiscal_year: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_tender_responsibility(actor):
		return {
			"outcome": "FORBIDDEN",
			"forbidden": {"heading": "You do not have access to Tenders", "text": f"This area needs one of these responsibilities: {FORBIDDEN_RESPONSIBILITIES}. Ask your KenTender administrator to assign one in System setup."},
		}
	roles = actor_roles(actor)
	rows: list[dict[str, Any]] = []
	if roles["officer"] or roles["hopf"]:
		for handoff in handoff_gateway.list_eligible(actor):
			rows.append(start_row(handoff, can_start=roles["officer"]))
	tenders = frappe.get_list("Tender", fields=TENDER_FIELDS, order_by="modified desc", limit_page_length=0, user=actor)
	for row in tenders:
		rows.append(tender_row(frappe._dict(row), actor, roles))
	fiscal_years = sorted({r["fiscal_year"] for r in rows if r["fiscal_year"]})
	needle = cstr(search).strip().lower()
	if needle:
		rows = [r for r in rows if needle in f"{r['tender_reference']} {r['requisition_reference']} {r['purchase']}".lower()]
	if cstr(status).strip():
		rows = [r for r in rows if r["status_key"] == cstr(status).strip()]
	if cstr(fiscal_year).strip():
		rows = [r for r in rows if r["fiscal_year"] == cstr(fiscal_year).strip()]
	return {
		"outcome": "OK",
		"mode": "technical" if roles["technical"] else ("actor" if (roles["officer"] or roles["hopf"] or roles["ao"]) else "reader"),
		"roles": roles,
		"can_start": roles["officer"],
		"counts": [] if roles["technical"] or not (roles["officer"] or roles["hopf"] or roles["ao"]) else _counts(rows, roles),
		"rows": rows,
		"filters": {"statuses": [{"key": k, "label": v} for k, v in STATUS_FILTERS], "fiscal_years": fiscal_years, "search": search, "status": status, "fiscal_year": fiscal_year},
		"count_label": f"{len(rows)} Tender" + ("" if len(rows) == 1 else "s"),
		"empty_text": "No Tenders match these filters." if not rows else "",
	}


# --------------------------------------------------------------------------
# GetTenderStart
# --------------------------------------------------------------------------


def get_tender_start(*, handoff: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	roles = actor_roles(actor)
	if not (roles["officer"] or roles["hopf"] or roles["auditor"] or roles["technical"]):
		authz.not_found()
	handoff_doc = handoff_gateway.load(handoff)
	if handoff_doc is None or handoff_gateway.requisition_state(handoff_doc) != "Authorised":
		return {"outcome": "SOURCE_UNAVAILABLE", "heading": "Authorised requisition unavailable", "text": "The requisition is no longer available to start this Tender."}
	consumer = handoff_gateway.consumer_tender(handoff_doc)
	if consumer:
		root = frappe.db.get_value("Tender", consumer, ["name", "tender_reference"], as_dict=True)
		return {"outcome": "ALREADY_STARTED", "heading": "Tender already started", "text": f"This requisition is linked to {root.tender_reference}.", "tender": root.name, "tender_reference": root.tender_reference, "route": [PAGE, root.tender_reference], "can_open": roles["officer"] or roles["hopf"] or roles["auditor"] or roles["technical"]}
	payload = handoff_gateway.payload_of(handoff_doc)
	checks = compatibility.evaluate(payload)
	try:
		binding = template_binding.bind()
		template = {"available": True, "display_name": binding["display_name"], "template_version": binding["template_version"], "official_source_title": binding["official_source_title"], "official_source_digest": binding["official_source_digest"], "bundle_digest": binding["bundle_digest"]}
	except Exception as exc:
		template = {"available": False, "reason": str(exc)}
	items = payload.get("items") or []
	unit = cstr((items[0].get("unit") if items else "") or "Each")
	supported = compatibility.is_supported(checks) and template["available"]
	return {
		"outcome": "OK",
		"handoff": handoff_doc.name,
		"summary": {
			"purchase": cstr(payload.get("requirement_title")), "requisition_reference": cstr(payload.get("requisition_reference")), "plan_item_id": cstr(payload.get("plan_item_id")),
			"quantity": f"{serializer.fmt_quantity(snap.total_quantity(payload))} {unit}", "approved_value": f"KES {serializer.fmt_money(snap.total_value(payload))}",
			"method": cstr(payload.get("planned_method")), "latest_delivery": serializer.fmt_date_short(payload.get("latest_delivery_date")), "product": compatibility.PRODUCT_LABEL if supported else cstr(payload.get("product_pattern")),
		},
		"compatibility": [c.as_dict() for c in checks],
		"supported": supported,
		"result_text": "Supported — IT equipment using the standard Open Tender format." if supported else "This requisition is not supported by the current IT-equipment Tender format.",
		"template": template,
		"can_start": roles["officer"] and supported,
	}


# --------------------------------------------------------------------------
# GetTender
# --------------------------------------------------------------------------


def _screen_for(root, version, roles: dict[str, bool]) -> str:
	status = cstr(root.overall_status)
	if status == "Draft":
		return "editor" if roles["officer"] else "record"
	if status == "Awaiting procurement approval":
		return "approval" if roles["hopf"] else "record"
	if status == "Approved":
		return "authorisation" if roles["ao"] else "record"
	if status == "Publication authorised":
		return "publication"
	if status in ("Published — open", "Submission period ended"):
		return "published"
	if status == "Cancelled":
		return "cancelled"
	if status == "Requisition correction requested":
		return "correction"
	return "record"


def badge_for(root, version, roles: dict[str, bool]) -> str:
	status = cstr(root.overall_status)
	if status == "Draft":
		return "Draft"
	if status == "Awaiting procurement approval":
		return "Awaiting your approval" if roles["hopf"] else "Awaiting procurement approval"
	if status == "Approved":
		return "Awaiting publication authorisation"
	if status == "Publication authorised":
		return "Publication confirmation required"
	return status


def allowed_actions(root, version, actor: str, roles: dict[str, bool]) -> list[str]:
	"""§11.1(1) — every control is offered only when the command layer would
	accept it for this actor in this exact state."""
	status = cstr(root.overall_status)
	actions: list[str] = []
	if status == "Draft" and roles["officer"]:
		actions += ["save_draft", "continue", "review_tender", "add_evidence", "preview_documents"]
		if not [r for r in version.get("review_findings") or [] if r.severity == review.MUST_FIX]:
			actions.append("submit_for_approval")
	if status in ("Draft", "Awaiting procurement approval", "Approved") and not root.publication and (roles["officer"] or roles["hopf"]):
		actions.append("request_requisition_correction")
	if status == "Awaiting procurement approval" and roles["hopf"]:
		if _can(lifecycle.require_segregation, version, actor, blocked_columns=("prepared_by", "submitted_by")):
			actions += ["return_for_correction", "approve_tender_package"]
	if status == "Approved":
		if roles["hopf"] and not root.publication:
			actions.append("reopen_tender")
		if roles["ao"] and _can(lifecycle.require_segregation, version, actor, blocked_columns=("prepared_by", "submitted_by", "approved_by")):
			actions.append("authorise_publication")
	if status == "Requisition correction requested" and roles["officer"]:
		if handoff_gateway.successors(plan_item_id=cstr(root.plan_item_id), user=actor):
			actions.append("start_corrected_tender_version")
	if status in ("Publication authorised", "Published — open", "Approved") and roles["hopf"]:
		actions.append("view_publication")
	if status == "Publication authorised":
		if roles["hopf"]:
			actions.append("confirm_publication_channel")
		if roles["ao"] and not frappe.db.exists("Tender Channel Confirmation", {"publication": root.publication, "subject_type": "Publication", "status": "Confirmed"}):
			actions.append("withdraw_publication_authorisation")
	if status == "Published — open":
		if roles["officer"] or roles["hopf"]:
			actions.append("prepare_addendum")
		if roles["hopf"]:
			actions.append("recommend_cancellation")
		if roles["ao"]:
			actions.append("cancel_tender")
	if status == "Cancelled" and (roles["officer"] or roles["hopf"]):
		actions.append("record_cancellation_evidence")
	actions.append("view_history")
	return actions


def segregation_message(root, version, actor: str, roles: dict[str, bool]) -> str:
	status = cstr(root.overall_status)
	if status == "Awaiting procurement approval" and roles["hopf"] and not _can(lifecycle.require_segregation, version, actor, blocked_columns=("prepared_by", "submitted_by")):
		return "You cannot approve a Tender Version you prepared or submitted. Another Head of Procurement Function must decide it."
	if status == "Approved" and roles["ao"] and not _can(lifecycle.require_segregation, version, actor, blocked_columns=("prepared_by", "submitted_by", "approved_by")):
		return "You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function. Another Accounting Officer must decide it."
	return ""


def inherited_projection(snapshot: dict[str, Any], *, internal: bool) -> dict[str, Any]:
	"""§10.4 context strip + drawer, §10.5/§10.6 requirement tables. Internal
	policy context only for authorised internal readers (§4.3)."""
	items = snapshot.get("items") or []
	unit = cstr((items[0].get("unit") if items else "") or "Each")
	lines = serializer.goods_lines(snapshot)
	out = {
		"context": {
			"purchase": cstr(snapshot.get("requirement_title")), "method": cstr(snapshot.get("planned_method")), "quantity": f"{serializer.fmt_quantity(snap.total_quantity(snapshot))} {unit}",
			"latest_delivery": serializer.fmt_date_short(snapshot.get("latest_delivery_date")), "requisition_reference": cstr(snapshot.get("requisition_reference")), "plan_item_id": cstr(snapshot.get("plan_item_id")),
			"reservation_category": cstr(snapshot.get("reservation_category_value") or "None"), "lotting": cstr(snapshot.get("lotting_indicator")), "fiscal_year": cstr(snapshot.get("fiscal_year")),
		},
		"items": [
			{"requisition_item_id": i.get("requisition_item_id"), "item_name": i.get("item_name"), "equipment_category": i.get("equipment_category"), "quantity": serializer.fmt_quantity(i.get("quantity")), "unit": i.get("unit") or "Each", "intended_use": i.get("intended_use"), "delivery_location": cstr(snapshot.get("delivery_location")), "latest_delivery_date": serializer.fmt_date_short(snapshot.get("latest_delivery_date")), "source_line_id": next((d.get("source_line_id") for d in snapshot.get("drawdown_lines") or [] if d.get("drawdown_line_id") == i.get("plan_item_line_id")), "")}
			for i in items
		],
		"goods_lines": lines,
		"technical_requirements": serializer.technical_rows(snapshot),
		"warranty_support": serializer.warranty_support(snapshot),
		"acceptance_requirements": serializer.acceptance_rows(snapshot),
		"related_services": serializer.related_services(snapshot),
		"supporting_materials": serializer.supporting_materials(snapshot),
		"counts": snap.counts(snapshot),
	}
	if internal:
		out["internal"] = {
			"authorised_value": f"KES {serializer.fmt_money(snap.total_value(snapshot))}", "strategic_objective": cstr(snapshot.get("strategic_objective_path") or snapshot.get("strategic_objective")),
			"plan_horizon": cstr(snapshot.get("plan_horizon")), "reservation_ids": snap.internal_context(snapshot)["reservation_ids"],
			"drawdown_lines": [{"drawdown_line_id": d.get("drawdown_line_id"), "source_line_id": d.get("source_line_id"), "plan_source_allocation_id": d.get("plan_item_line_id"), "contributing_org_unit": d.get("contributing_org_unit"), "requested_quantity": serializer.fmt_quantity(d.get("requested_quantity")), "requested_value": f"KES {serializer.fmt_money(d.get('requested_value'))}", "reservation_id": d.get("reservation_id")} for d in snapshot.get("drawdown_lines") or []],
			"note": "For internal review only — not included in supplier documents.",
		}
	return out


def version_summary(version) -> dict[str, Any]:
	return {
		"name": version.name, "version_number": int(version.version_number), "status": version.status, "predecessor_version": cstr(version.predecessor_version),
		"prepared_by": cstr(version.prepared_by), "prepared_by_name": _full_name(version.prepared_by), "prepared_at": cstr(version.prepared_at), "prepared_at_label": serializer.fmt_datetime_short(version.prepared_at) if version.prepared_at else "",
		"submitted_by": cstr(version.submitted_by), "submitted_by_name": _full_name(version.submitted_by), "submitted_at": cstr(version.submitted_at), "submitted_at_label": serializer.fmt_datetime_short(version.submitted_at) if version.submitted_at else "",
		"approved_by": cstr(version.approved_by), "approved_by_name": _full_name(version.approved_by), "approved_at": cstr(version.approved_at), "approved_at_label": serializer.fmt_datetime_short(version.approved_at) if version.approved_at else "",
		"returned_by": cstr(version.returned_by), "returned_by_name": _full_name(version.returned_by), "returned_at_label": serializer.fmt_datetime_short(version.returned_at) if version.returned_at else "", "return_reason": cstr(version.return_reason), "return_affected_task": cstr(version.return_affected_task),
		"reopen_reason": cstr(version.reopen_reason), "stop_reason": cstr(version.stop_reason),
		"package_digest": cstr(version.package_digest), "invitation_digest": cstr(version.invitation_digest), "issued_tender_digest": cstr(version.issued_tender_digest),
		"response_schema_digest": cstr(version.response_schema_digest), "evaluation_contract_digest": cstr(version.evaluation_contract_digest), "contract_projection_digest": cstr(version.contract_projection_digest),
		"requisition_snapshot_digest": cstr(version.requisition_snapshot_digest), "template_release_id": cstr(version.template_release_id), "bundle_digest": cstr(version.bundle_digest), "official_source_digest": cstr(version.official_source_digest),
		"record_version": int(version.record_version or 0),
	}


def documents_for(root, version) -> list[dict[str, Any]]:
	out = []
	for row in documents.list_for_tender(root.name):
		if row.tender_version and version is not None and row.tender_version != version.name and row.kind in (documents.KIND_INVITATION, documents.KIND_COMPLETE):
			continue
		file_row = frappe.db.get_value("File", row.file, ["file_name", "file_size"], as_dict=True) if row.file else None
		out.append({"document": row.name, "kind": row.kind, "digest": row.digest, "generated_at": cstr(row.generated_at), "file_name": file_row.file_name if file_row else "", "size": int(file_row.file_size or 0) if file_row else 0, "format": "PDF" if file_row else "HTML", "addendum": cstr(row.addendum), "cancellation": cstr(row.cancellation)})
	return out


def _returned_panel(version) -> dict[str, Any] | None:
	if not version.predecessor_version:
		return None
	previous = frappe.get_doc("Tender Version", version.predecessor_version)
	if previous.status != "Returned":
		return None
	return {"returned_by": _full_name(previous.returned_by), "returned_at": serializer.fmt_datetime_short(previous.returned_at), "comment": cstr(previous.return_reason), "affected_task": lifecycle.AFFECTED_TASK_KEYS.get(cstr(previous.return_affected_task), "requirements"), "affected_task_label": cstr(previous.return_affected_task)}


def key_facts(root, version, snapshot: dict[str, Any], *, internal: bool) -> list[dict[str, str]]:
	state = serializer.officer_state(version)
	items = snapshot.get("items") or []
	unit = cstr((items[0].get("unit") if items else "") or "Each")
	facts = [
		{"label": "Purchase", "value": cstr(snapshot.get("requirement_title"))},
		{"label": "Requisition", "value": cstr(snapshot.get("requisition_reference"))},
		{"label": "Quantity", "value": f"{serializer.fmt_quantity(snap.total_quantity(snapshot))} {unit}"},
	]
	if internal:
		facts.append({"label": "Approved value", "value": f"KES {serializer.fmt_money(snap.total_value(snapshot))}"})
	facts += [
		{"label": "Method", "value": "Open Tender"},
		{"label": "Submission deadline", "value": serializer.fmt_datetime_short(state.get("submission_deadline"))},
		{"label": "Tender security", "value": f"KES {serializer.fmt_money(state.get('tender_security_amount'))}" if state.get("tender_security_amount") is not None else ""},
		{"label": "Reservation", "value": cstr(snapshot.get("reservation_category_value") or "None")},
		{"label": "Latest delivery", "value": serializer.fmt_date_short(snapshot.get("latest_delivery_date"))},
	]
	return facts


def get_tender(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	name = draft_commands.resolve_tender_name(tender)
	root = frappe.get_doc("Tender", name)
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	roles = actor_roles(actor)
	internal = mode in ("site", "technical")
	version = frappe.get_doc("Tender Version", root.current_version)
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	from kentender_procurement.tenders.services import publication_read

	projection = {
		"outcome": "OK",
		"mode": mode,
		"roles": roles,
		"screen": _screen_for(root, version, roles) if mode != "department" else "record",
		"tender": {
			"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "requirement_title": cstr(root.requirement_title),
			"requisition": cstr(root.requisition), "requisition_reference": cstr(root.requisition_reference), "plan_item_id": cstr(root.plan_item_id), "fiscal_year": cstr(root.fiscal_year),
			"overall_status": cstr(root.overall_status), "badge": badge_for(root, version, roles), "published_at": cstr(root.published_at), "published_at_label": serializer.fmt_datetime_short(root.published_at) if root.published_at else "",
			"submission_deadline": cstr(root.submission_deadline), "submission_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else "",
			"publication": cstr(root.publication), "cancellation": cstr(root.cancellation), "record_version": int(root.record_version or 0), "template_release_id": cstr(root.template_release_id),
		},
		"version": version_summary(version),
		"tasks": draft_commands.task_statuses(version),
		"task_labels": controls.TASK_LABELS,
		"officer_values": state if internal else {k: v for k, v in state.items() if k in ("tender_title", "issue_date", "clarification_deadline", "submission_deadline")},
		"catalogue": controls.catalogue_for_client() if roles["officer"] else {},
		"evidence_requirements": [{**r, "proves": evidence.proves_label(r, snapshot)} for r in evidence.rows_as_dicts(version)],
		"inherited": inherited_projection(snapshot, internal=internal),
		"review": review.summary(version),
		"returned": _returned_panel(version) if root.overall_status == "Draft" else None,
		"evaluation_stages": list(serializer.EVALUATION_STAGES),
		"documents": documents_for(root, version) if internal else [],
		"decisions": decisions_for(root) if internal else [],
		"allowed_actions": allowed_actions(root, version, actor, roles) if mode != "department" else ["view_history"],
		"segregation_message": segregation_message(root, version, actor, roles),
		"correction": correction.correction_state(root, user=actor) if root.overall_status == "Requisition correction requested" else None,
		"key_facts": key_facts(root, version, snapshot, internal=internal),
		"publication": publication_read.publication_summary(root, actor=actor, roles=roles) if internal else None,
		"open_period": publication_read.open_period_summary(root, actor=actor, roles=roles) if internal else None,
		"options": {
			"delivery_locations": frappe.get_all("Delivery Location", filters={"status": "Active"}, pluck="name", order_by="location_name asc") if roles["officer"] else [],
			"contact_offices": frappe.get_all("Contact Office", filters={"status": "Active"}, pluck="name", order_by="office_name asc") if roles["officer"] else [],
			"affected_tasks": list(lifecycle.AFFECTED_TASKS),
		},
	}
	return projection


def decisions_for(root) -> list[dict[str, Any]]:
	rows = frappe.get_all("Tender Decision", filters={"tender": root.name}, fields=["name", "tender_version", "decision", "actor", "business_role", "reason", "affected_task", "decided_at", "subject_type", "subject_id"], order_by="decided_at asc, creation asc", limit_page_length=0)
	for row in rows:
		row["actor_name"] = _full_name(row["actor"])
		row["decided_at_label"] = serializer.fmt_datetime_short(row["decided_at"]) if row["decided_at"] else ""
		row["version_number"] = int(frappe.db.get_value("Tender Version", row["tender_version"], "version_number") or 0) if row["tender_version"] else None
	return rows


# --------------------------------------------------------------------------
# GetTenderReview
# --------------------------------------------------------------------------


def review_sections(root, version, snapshot: dict[str, Any], summary: dict[str, Any], *, internal: bool) -> list[dict[str, Any]]:
	"""§10.6 items 5–7 — six sections, each a plain summary plus details;
	only a section holding a Must fix or a Review note starts open."""
	state = serializer.officer_state(version)
	evidence_rows = [{**r, "proves": evidence.proves_label(r, snapshot)} for r in evidence.rows_as_dicts(version)]
	lines = serializer.goods_lines(snapshot)
	flagged = {f["task"] for f in summary["findings"]} | {"contract" for f in summary["findings"] if controls.CATALOGUE.get(f.get("field") or "", {}).get("group") == "contract"}
	sections = [
		{"key": "details", "title": "Tender details", "summary": f"Issue {serializer.fmt_date_short(state.get('issue_date'))} · clarification {serializer.fmt_datetime_short(state.get('clarification_deadline'))} · submission {serializer.fmt_datetime_short(state.get('submission_deadline'))} · validity {serializer.fmt_number(state.get('tender_validity_days'))} days · security KES {serializer.fmt_money(state.get('tender_security_amount'))}", "open": "details" in flagged, "details": {"fields": [{"label": controls.CATALOGUE[f]["label"], "value": _display_value(f, state)} for f in controls.FIELDS_BY_TASK[controls.TASK_DETAILS] if controls.applies(f, state)]}},
		{"key": "requirements", "title": "Requirements from the authorised requisition", "summary": f"{len(snapshot.get('items') or [])} items · {len(snapshot.get('technical_requirements') or [])} technical requirements · {len(snapshot.get('acceptance_requirements') or [])} acceptance checks", "open": False, "details": {k: v for k, v in inherited_projection(snapshot, internal=internal).items() if k in ("items", "technical_requirements", "warranty_support", "acceptance_requirements", "related_services", "supporting_materials")}},
		{"key": "pricing", "title": "Supplier pricing schedule", "summary": f"{len(lines)} line{'s' if len(lines) != 1 else ''} · unit price and tax completed by supplier · totals calculated from supplier response", "open": False, "details": serializer.price_schedule(snapshot)},
		{"key": "supplier", "title": "Supplier and evaluation requirements", "summary": _supplier_summary(state, evidence_rows), "open": "requirements" in flagged, "details": {"qualification": serializer.qualification_criteria(state), "evidence_requirements": evidence_rows, "stages": list(serializer.EVALUATION_STAGES)}},
		{"key": "contract", "title": "Contract terms", "summary": f"Payment {serializer.fmt_number(state.get('payment_timing_days'))} days · performance security {serializer.fmt_number(state.get('performance_security_percent')) + '%' if state.get('performance_security_required') else 'not required'} · delay damages {serializer.fmt_number(state.get('delay_damages_per_week_percent'))}% per week, maximum {serializer.fmt_number(state.get('maximum_delay_damages_percent'))}%", "open": "contract" in flagged, "details": {"fields": [{"label": controls.CATALOGUE[f]["label"], "value": _display_value(f, state)} for f in controls.FIELDS_BY_TASK[controls.TASK_REQUIREMENTS] if controls.CATALOGUE[f]["group"] == "contract" and controls.applies(f, state)]}},
		{"key": "technical", "title": "Technical evidence", "summary": f"Template {cstr(version.template_release_id)} · {len(lines)} rendered line{'s' if len(lines) != 1 else ''} from {len(snapshot.get('items') or [])} items", "open": False, "details": {"template_release_id": cstr(version.template_release_id), "official_source_digest": cstr(version.official_source_digest), "bundle_digest": cstr(version.bundle_digest), "requisition_snapshot_digest": cstr(version.requisition_snapshot_digest), "package_digest": cstr(version.package_digest), "invitation_digest": cstr(version.invitation_digest), "issued_tender_digest": cstr(version.issued_tender_digest), "response_schema_digest": cstr(version.response_schema_digest), "evaluation_contract_digest": cstr(version.evaluation_contract_digest), "contract_projection_digest": cstr(version.contract_projection_digest), "lineage": [{"line": l["line_number"], "description": l["description"], "quantity": l["quantity"], "source_items": l["source_items"] if internal else [{"requisition_item_id": s["requisition_item_id"], "quantity": s["quantity"]} for s in l["source_items"]]} for l in lines], "mappings": {"technical_requirements": len(snapshot.get("technical_requirements") or []), "responses": len(serializer.supplier_response_schema(snapshot, evidence.rows_as_dicts(version))["technical"]), "evaluation": len(serializer.evaluation_contract(state, snapshot, evidence.rows_as_dicts(version))["technical_pass_fail"]), "contract": len(serializer.contract_obligations(state, snapshot)["technical"])}}},
	]
	return sections


def _display_value(field: str, state: dict[str, Any]) -> str:
	spec = controls.CATALOGUE[field]
	value = state.get(field)
	if value is None:
		return ""
	if spec["type"] == controls.BOOL:
		return "Yes" if value else "No"
	if spec["type"] == controls.DATE:
		return serializer.fmt_date_short(value)
	if spec["type"] == controls.DATETIME:
		return serializer.fmt_datetime_short(value)
	if spec["type"] == controls.MONEY:
		return f"KES {serializer.fmt_money(value)}"
	return cstr(value)


def _supplier_summary(state: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> str:
	parts = []
	if state.get("manufacturer_authorisation_required"):
		parts.append("manufacturer authorisation")
	if state.get("datasheets_required"):
		parts.append("datasheets")
	parts.append("warranty confirmation")
	if state.get("past_experience_required"):
		parts.append(f"{serializer.fmt_number(state.get('minimum_comparable_contracts'))} comparable contracts in {serializer.fmt_number(state.get('experience_period_years'))} years")
	if state.get("after_sales_evidence_required"):
		parts.append("after-sales support evidence")
	return ", ".join(parts).capitalize() + f" · {len(evidence_rows)} additional evidence"


def get_tender_review(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	name = draft_commands.resolve_tender_name(tender)
	root = frappe.get_doc("Tender", name)
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	roles = actor_roles(actor)
	internal = mode in ("site", "technical")
	version = frappe.get_doc("Tender Version", root.current_version)
	snapshot = snap.load(version)
	if version.status == "Draft":
		fresh = review.run(root, version, with_renders=False)
		summary = {"result": fresh["result"], "findings": fresh["findings"], "must_fix": [f for f in fresh["findings"] if f["severity"] == review.MUST_FIX], "review_notes": [f for f in fresh["findings"] if f["severity"] == review.REVIEW_NOTE], "must_fix_count": fresh["must_fix_count"], "review_note_count": fresh["review_note_count"], "review_result_digest": fresh["review_result_digest"]}
	else:
		summary = review.summary(version)
	return {
		"outcome": "OK", "mode": mode, "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "overall_status": cstr(root.overall_status), "record_version": int(root.record_version or 0)},
		"version": version_summary(version),
		"review": summary,
		"key_facts": key_facts(root, version, snapshot, internal=internal),
		"sections": review_sections(root, version, snapshot, summary, internal=internal),
		"documents": documents_for(root, version) if internal else [],
		"allowed_actions": allowed_actions(root, version, actor, roles) if mode != "department" else ["view_history"],
		"segregation_message": segregation_message(root, version, actor, roles),
		"submit_blocked_text": "Fix the item above before submitting." if summary["must_fix_count"] else "",
	}
