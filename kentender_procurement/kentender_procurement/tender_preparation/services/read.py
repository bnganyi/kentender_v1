# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11.1 — the six reads plus the preview. Reads create no
Tender, Version, task, decision, render file or handoff. The workspace is
verdict-first (KT-STD-001 §3A): the page-level verdict resolves before any
content is assembled, and a denied actor receives the Forbidden state as
data, never an exception."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_preparation.services import compatibility, controls, draft_commands, evidence, handoff_gateway, lifecycle, render_service, serializer
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_preparation.services import tender_authorization as authz
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError, fail
from kentender_procurement.tender_preparation.services.tender_roles import FORBIDDEN_HEADING, FORBIDDEN_TEXT, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER
from kentender_procurement.tender_templates import loader, registry

STATE_LABELS = {
	"Draft": "Draft", "Submitted for approval": "Submitted for approval", "Approved for publication": "Approved for publication",
	"Upstream correction required": "Upstream correction required",
}


def _can(fn, *args, **kwargs) -> bool:
	try:
		fn(*args, **kwargs)
		return True
	except (TenderPreparationError, frappe.DoesNotExistError, frappe.PermissionError):
		return False


def _user_label(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user) if user else ""


def _eat(value) -> str:
	return serializer.fmt_datetime_eat(value)


def _template_summary() -> dict[str, Any]:
	meta = loader.metadata()
	row = frappe.db.get_value("Supported Tender Template", registry.registry_name(), ["availability", "bundle_digest", "official_source_digest", "official_source_title"], as_dict=True) or frappe._dict()
	return {
		"template_key": meta["template_key"], "template_version": meta["template_version"], "display_name": meta["display_name"],
		"label": f"{meta['display_name']} · Version {meta['template_version']}", "official_source": meta["official_std_family"],
		"official_source_title": row.get("official_source_title", ""), "availability": row.get("availability", "not installed"),
		"bundle_digest": row.get("bundle_digest", ""), "official_source_digest": row.get("official_source_digest", ""),
	}


def _tender_summary(root) -> dict[str, Any]:
	version = frappe.db.get_value("Tender Preparation Version", root.current_version, ["version_number", "version_status", "tender_title", "blocking_count", "warning_count", "modified"], as_dict=True) or frappe._dict()
	return {
		"tender": root.name, "tender_reference": root.tender_reference, "title": version.get("tender_title") or root.requirement_title,
		"requirement_title": root.requirement_title, "requisition_reference": root.requisition_reference, "plan_item_id": root.plan_item_id,
		"current_state": root.current_state, "state_label": STATE_LABELS.get(root.current_state, root.current_state),
		"version_number": version.get("version_number"), "version_status": version.get("version_status"), "version_label": f"Version {version.get('version_number') or ''}".strip(),
		"blocking_count": version.get("blocking_count") or 0, "warning_count": version.get("warning_count") or 0,
		"record_version": root.record_version, "updated_at": _eat(version.get("modified")),
	}


# --------------------------------------------------------------------------
# GetTenderPreparationWorkspace
# --------------------------------------------------------------------------


def get_tender_preparation_workspace(*, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_tender_responsibility(actor):
		return {"outcome": "FORBIDDEN", "forbidden": {"heading": FORBIDDEN_HEADING, "text": FORBIDDEN_TEXT}}
	can_prepare = authz.has_site_role(ROLE_PROCUREMENT_OFFICER, actor)
	ready = []
	for row in handoff_gateway.list_eligible(user=actor):
		ready.append({**row, "action_label": "Prepare Tender", "can_prepare": can_prepare, "package_label": f"{row['item_count']} item" + ("" if row["item_count"] == 1 else "s"), "required_by_label": row["latest_delivery_date_label"]})
	tenders = [_tender_summary(frappe.get_doc("Prepared Tender", name)) for name in frappe.get_all("Prepared Tender", order_by="modified desc", pluck="name")]
	for row in tenders:
		row["action_label"] = "Open" if row["current_state"] in ("Draft",) else ("Open approved Tender" if row["current_state"] == "Approved for publication" else "View")
		row["route"] = ["tender-preparation", row["tender"], "approved"] if row["current_state"] == "Approved for publication" else ["tender-preparation", row["tender"]]
	approval_tasks = []
	if authz.can_read_site(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor):
		for task in frappe.get_all("Tender Preparation Task", filters={"status": "Open", "business_role": ROLE_HEAD_OF_PROCUREMENT_FUNCTION}, fields=["name", "tender", "tender_version", "creation"], order_by="creation asc"):
			root = frappe.get_doc("Prepared Tender", task.tender)
			summary = _tender_summary(root)
			approval_tasks.append({**summary, "task": task.name, "received_at": _eat(task.creation), "route": ["tender-preparation", "task", task.name], "action_label": "Open approval task"})
	return {
		"outcome": "OK", "ready_to_prepare": ready, "tenders": tenders, "approval_tasks": approval_tasks,
		"show_approval_tasks": authz.can_read_site(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor), "can_prepare": can_prepare,
		"template": _template_summary(), "count_label": f"{len(tenders)} Tender" + ("" if len(tenders) == 1 else "s"),
	}


# --------------------------------------------------------------------------
# GetTenderCompatibility (Start Tender dialog)
# --------------------------------------------------------------------------


def get_tender_compatibility(*, handoff: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.require_tender_reader(user)
	handoff_doc = handoff_gateway.load(handoff)
	if handoff_doc is None:
		return {"outcome": "HANDOFF_INVALID", "message": "The source Requisition is no longer available for Tender Preparation."}
	if handoff_gateway.requisition_state(handoff_doc) != "Authorised":
		return {"outcome": "HANDOFF_INVALID", "message": "The source Requisition is no longer available for Tender Preparation."}
	existing = draft_commands.existing_tender_for_handoff(handoff_doc.name)
	if existing:
		return {"outcome": "HANDOFF_CONSUMED", "message": "This Requisition is already linked to a Tender.", "tender": existing.name, "tender_reference": existing.tender_reference, "can_view": True}
	if handoff_doc.consumed_at:
		return {"outcome": "HANDOFF_CONSUMED", "message": "This Requisition is already linked to a Tender.", "tender": handoff_doc.tender, "can_view": False}
	snapshot, _ = snap.build(handoff_doc)
	rows = compatibility.evaluate(snapshot, handoff_version=handoff_doc.handoff_version)
	template = _template_summary()
	template_available = template["availability"] == registry.AVAILABLE
	compatible = all(r.ok for r in rows) and template_available
	return {
		"outcome": "OK" if compatible else ("TEMPLATE_UNAVAILABLE" if not template_available else "PRODUCT_UNSUPPORTED"),
		"message": "" if compatible else ("This Tender template is not available for new Tenders." if not template_available else "This Requisition is not supported by the IT-equipment Tender pattern."),
		"handoff": handoff_doc.name, "handoff_version": handoff_doc.handoff_version, "handoff_digest": handoff_doc.handoff_digest,
		"requisition_reference": snapshot.get("requisition_reference"), "requirement_title": snapshot.get("requirement_title"),
		"plan_item_id": snapshot.get("plan_item_id"), "planned_method": snapshot.get("planned_method"), "product_pattern": snapshot.get("product_pattern"),
		"counts": snap.counts(snapshot), "compatibility": [r.as_dict() for r in rows], "template": template,
		"notice": "This template release is fixed for this Tender. A later release will not change it.",
		"can_prepare": compatible and authz.has_site_role(ROLE_PROCUREMENT_OFFICER, actor),
	}


# --------------------------------------------------------------------------
# GetTenderEditor
# --------------------------------------------------------------------------


def _inherited_projection(snapshot: dict[str, Any], version) -> dict[str, Any]:
	evidence_ids = evidence.technical_ids_with_evidence(version)
	return {
		"goods": serializer.goods_lines(snapshot), "technical_requirements": serializer.technical_rows(snapshot, evidence_ids),
		"warranty_support": serializer.warranty_support(snapshot), "related_services": serializer.related_services(snapshot),
		"acceptance_requirements": serializer.acceptance_rows(snapshot), "supporting_materials": serializer.supporting_materials(snapshot),
		"counts": snap.counts(snapshot), "delivery_location": snapshot.get("delivery_location"), "latest_delivery_date": serializer.fmt_date(snapshot.get("latest_delivery_date")),
		"authorised_value": f"KES {serializer.fmt_money(snap.total_value(snapshot))}", "authorised_quantity": f"{serializer.fmt_quantity(snap.total_quantity(snapshot))} {cstr((snapshot.get('items') or [{}])[0].get('unit') or 'Each')}",
		"planned_method": snapshot.get("planned_method"), "reservation_category": snapshot.get("reservation_category_value") or "None", "lotting_indicator": snapshot.get("lotting_indicator"),
		"requisition_reference": snapshot.get("requisition_reference"), "plan_item_id": snapshot.get("plan_item_id"), "fiscal_year": snapshot.get("fiscal_year"),
		"requirement_title": snapshot.get("requirement_title"), "business_need": snapshot.get("business_need"), "expected_operational_result": snapshot.get("expected_operational_result"),
		# §8.1 internal policy context — officer/approver only, never rendered (TPR-AC-044).
		"internal_context": {"strategic_objective_path": snapshot.get("strategic_objective_path"), "plan_horizon": snapshot.get("plan_horizon"), "multi_year_justification": snapshot.get("multi_year_justification"), "internal_only": True},
	}


def _task_status(version, state: dict[str, Any]) -> dict[str, Any]:
	missing = controls.missing(state)
	by_task = {1: [], 4: [], 5: []}
	for task, field, label in missing:
		by_task[task].append({"field": field, "label": label})
	return {
		"1": {"complete": not by_task[1], "missing": by_task[1]},
		"2": {"complete": True, "missing": []},
		"3": {"complete": True, "missing": []},
		"4": {"complete": not by_task[4], "missing": by_task[4]},
		"5": {"complete": not by_task[5], "missing": by_task[5]},
	}


def _readiness_view(version) -> dict[str, Any]:
	findings = [
		{"finding_code": f.finding_code, "severity": f.severity, "task_number": f.task_number, "field_reference": f.field_reference, "message": f.message}
		for f in sorted(version.get("readiness_findings") or [], key=lambda x: x.row_order or 0)
	]
	return {"run_at": _eat(version.readiness_run_at), "blocking_count": version.blocking_count or 0, "warning_count": version.warning_count or 0, "findings": findings, "readiness_digest": version.readiness_digest, "ready": (version.blocking_count or 0) == 0 and bool(version.readiness_run_at)}


def _binding(root, version) -> dict[str, Any]:
	return {
		"template_key": root.template_key, "template_version": root.template_version, "template_label": f"{serializer.TEMPLATE_DISPLAY_NAME} · Version {root.template_version}",
		"official_source_digest": root.official_source_digest, "bundle_digest": root.bundle_digest, "requisition_handoff": root.requisition_handoff,
		"handoff_digest": root.handoff_digest, "requisition_version": root.requisition_version, "requisition_content_digest": root.requisition_content_digest,
		"snapshot_digest": version.snapshot_digest, "content_digest": version.content_digest,
	}


def get_tender_editor(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.require_tender_reader(user)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = frappe.get_doc("Prepared Tender", tender)
	version = frappe.get_doc("Tender Preparation Version", root.current_version)
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	derived = serializer.derived_dates(state)
	is_officer = authz.has_site_role(ROLE_PROCUREMENT_OFFICER, actor)
	editable = is_officer and root.current_state == "Draft" and version.version_status == "Draft"
	return {
		"outcome": "OK", "tender": _tender_summary(root), "binding": _binding(root, version), "inherited": _inherited_projection(snapshot, version),
		"officer_values": {k: (str(v) if hasattr(v, "isoformat") else v) for k, v in state.items()},
		"generated": {
			"tender_reference": root.tender_reference, "opening_datetime": _eat(derived["opening_datetime"]), "validity_date": serializer.fmt_date(derived["validity_date"]),
			"tender_security_treatment": "Tender Security", "tender_security_currency": "KES", "warranty_confirmation_required": "Yes — always required",
			"price_schedule": serializer.price_schedule(snapshot), "evaluation_stages": list(serializer.EVALUATION_STAGES),
		},
		"evidence_requirements": evidence.rows_as_dicts(version), "controls": controls.catalogue_for_client(), "options": _link_options(),
		"tasks": _task_status(version, state), "readiness": _readiness_view(version),
		"permitted_actions": {
			"can_save": editable, "can_run_readiness": editable, "can_submit": editable, "can_add_evidence": editable,
			"can_request_upstream_correction": root.current_state in ("Draft", "Submitted for approval") and _can(authz.require_officer_or_hopf, actor),
			"can_preview": True,
		},
		"prepared_by": _user_label(version.prepared_by), "based_on_version": version.based_on_version,
		"return_reason": _latest_reason(root, "Return for correction") if version.based_on_version else "",
	}


def _link_options() -> dict[str, list[dict[str, str]]]:
	"""§8.0 "Governed reference — Frappe Link restricted to Active records":
	the two option lists the Task 1/5 Link controls render from."""
	return {
		"delivery_locations": [{"value": r.name, "label": r.location_name} for r in frappe.get_all("Delivery Location", filters={"status": "Active"}, fields=["name", "location_name"], order_by="location_name asc")],
		"contact_offices": [{"value": r.name, "label": r.office_name} for r in frappe.get_all("Contact Office", filters={"status": "Active"}, fields=["name", "office_name"], order_by="office_name asc")],
	}


def _latest_reason(root, decision: str) -> str:
	row = frappe.get_all("Tender Preparation Decision", filters={"tender": root.name, "decision": decision}, fields=["reason"], order_by="decided_at desc", limit=1)
	return row[0].reason if row else ""


# --------------------------------------------------------------------------
# GetTenderApprovalTask
# --------------------------------------------------------------------------


def get_tender_approval_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.require_tender_reader(user)
	if not task or not frappe.db.exists("Tender Preparation Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Tender Preparation Task", task)
	root = frappe.get_doc("Prepared Tender", task_doc.tender)
	version = frappe.get_doc("Tender Preparation Version", task_doc.tender_version)
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	renders = render_service.render(root, version, snapshot)
	evidence_rows = evidence.rows_as_dicts(version)
	is_hopf = authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor)
	sod_blocked = actor in {cstr(version.prepared_by), cstr(version.submitted_by)}
	open_task = task_doc.status == "Open" and root.current_state == "Submitted for approval"
	return {
		"outcome": "OK", "task": task_doc.name, "task_status": task_doc.status, "task_record_version": task_doc.record_version,
		"tender": _tender_summary(root), "binding": _binding(root, version), "inherited": _inherited_projection(snapshot, version),
		"officer_values": {k: (str(v) if hasattr(v, "isoformat") else v) for k, v in state.items()}, "controls": controls.catalogue_for_client(),
		"evidence_requirements": evidence_rows, "generated": {"price_schedule": serializer.price_schedule(snapshot), "evaluation_stages": list(serializer.EVALUATION_STAGES)},
		"mappings": {
			"supplier_response_schema": serializer.supplier_response_schema(snapshot, {r["linked_requirement_id"] for r in evidence_rows if r["linked_requirement_type"] == "Technical requirement"}),
			"evaluation_contract": serializer.evaluation_contract(state, snapshot, evidence_rows), "contract_obligations": serializer.contract_obligations(state, snapshot),
		},
		"readiness": _readiness_view(version), "renders": {"invitation_html": renders["invitation_html"], "issued_tender_html": renders["issued_tender_html"], "invitation_digest": renders["invitation_digest"], "issued_tender_digest": renders["issued_tender_digest"], "problems": renders["problems"]},
		"submitted_by": {"name": _user_label(version.submitted_by), "at": _eat(version.submitted_at)}, "prepared_by": {"name": _user_label(version.prepared_by), "at": _eat(version.prepared_at)},
		"permitted_actions": {"can_return": open_task and is_hopf, "can_approve": open_task and is_hopf and not sod_blocked, "sod_blocked": sod_blocked and is_hopf},
		"release": {"template_label": f"{serializer.TEMPLATE_DISPLAY_NAME} · Version {root.template_version}", "bundle_digest": root.bundle_digest, "requisition_content_digest": root.requisition_content_digest},
	}


# --------------------------------------------------------------------------
# GetApprovedTender
# --------------------------------------------------------------------------


def get_approved_tender(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.require_tender_reader(user)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = frappe.get_doc("Prepared Tender", tender)
	if not root.approved_version or not root.publication_handoff:
		fail("TPR_STALE_VERSION", "This Tender has no approved Version.")
	version = frappe.get_doc("Tender Preparation Version", root.approved_version)
	handoff = frappe.get_doc("Tender Publication Handoff", root.publication_handoff)
	package = json.loads(handoff.package_json or "{}")
	decision = frappe.get_all("Tender Preparation Decision", filters={"tender_version": version.name, "decision": "Approve for publication"}, fields=["actor", "decided_at", "name"], order_by="decided_at desc", limit=1)
	approved_by = {"name": _user_label(decision[0].actor), "at": _eat(decision[0].decided_at), "decision": decision[0].name} if decision else {}
	files = {field: handoff.get(field) for field in ("invitation_html_file", "issued_tender_html_file", "invitation_pdf_file", "issued_tender_pdf_file")}
	file_urls = {k: (frappe.db.get_value("File", v, "file_url") if v else "") for k, v in files.items()}
	consumed = bool(handoff.consumed_at)
	return {
		"outcome": "OK", "tender": _tender_summary(root), "binding": _binding(root, version), "approved_by": approved_by,
		"publication_handoff": {"name": handoff.name, "handoff_version": handoff.handoff_version, "status": handoff.status, "generated_at": _eat(handoff.generated_at), "consumed_at": _eat(handoff.consumed_at), "published_on": serializer.fmt_date(handoff.published_on), "package_digest": handoff.package_digest, "status_label": "Consumed by publication" if consumed else "Ready · awaiting downstream acknowledgment"},
		"renders": {"invitation_digest": handoff.invitation_digest, "issued_tender_digest": handoff.issued_tender_digest, "invitation_pdf_digest": (package.get("renders") or {}).get("invitation_pdf_digest"), "issued_tender_pdf_digest": (package.get("renders") or {}).get("issued_tender_pdf_digest"), "files": file_urls},
		"mappings": package.get("generated", {}), "readiness": package.get("readiness", {}), "inherited": _inherited_projection(snap.load(version), version),
		"officer_values": {k: (str(v) if hasattr(v, "isoformat") else v) for k, v in serializer.officer_state(version).items()},
		"notice": "This Tender is approved. The publication package is ready.",
		"permitted_actions": {"can_reopen": (not consumed) and handoff.status == "Ready" and authz.has_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor)},
	}


# --------------------------------------------------------------------------
# GetTenderHistory
# --------------------------------------------------------------------------


def get_tender_history(*, tender: str, user: str | None = None) -> dict[str, Any]:
	authz.require_tender_reader(user)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = frappe.get_doc("Prepared Tender", tender)
	versions = frappe.get_all("Tender Preparation Version", filters={"tender": root.name}, fields=["name", "version_number", "version_status", "based_on_version", "prepared_by", "prepared_at", "submitted_by", "submitted_at", "decided_by", "decided_at", "content_digest", "readiness_digest", "blocking_count", "warning_count"], order_by="version_number asc")
	decisions = frappe.get_all("Tender Preparation Decision", filters={"tender": root.name}, fields=["name", "tender_version", "actor", "legal_capacity", "decision", "reason", "resulting_state", "decided_at"], order_by="decided_at asc")
	handoffs = frappe.get_all("Tender Publication Handoff", filters={"tender": root.name}, fields=["name", "tender_version", "status", "package_digest", "generated_at", "consumed_at", "consumption_correlation_id", "published_on"], order_by="generated_at asc")
	event_rows = frappe.get_all("Tender Preparation Event", filters={"tender": root.name}, fields=["event_id", "event_type", "correlation_id", "occurred_at", "status", "consumer"], order_by="sequence asc")
	for row in versions:
		row["prepared_by_label"], row["submitted_by_label"], row["decided_by_label"] = _user_label(row.prepared_by), _user_label(row.submitted_by), _user_label(row.decided_by)
		row["prepared_at"], row["submitted_at"], row["decided_at"] = _eat(row.prepared_at), _eat(row.submitted_at), _eat(row.decided_at)
	for row in decisions:
		row["actor_label"], row["decided_at"] = _user_label(row.actor), _eat(row.decided_at)
	return {
		"outcome": "OK", "tender": _tender_summary(root), "predecessor_tender": root.predecessor_tender, "versions": versions, "decisions": decisions,
		"publication_handoffs": handoffs, "events": event_rows,
		"requisition_handoff": {"name": root.requisition_handoff, "handoff_digest": root.handoff_digest, "requisition_version": root.requisition_version, "requisition_reference": root.requisition_reference},
	}


# --------------------------------------------------------------------------
# Preview (§14 — always from the server's canonical projection)
# --------------------------------------------------------------------------


def get_tender_preview(*, tender: str, output: str, user: str | None = None) -> dict[str, Any]:
	authz.require_tender_reader(user)
	if output not in ("invitation", "issued_tender"):
		fail("TPR_CONTROL_INVALID", "Preview output must be 'invitation' or 'issued_tender'.")
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = frappe.get_doc("Prepared Tender", tender)
	version = frappe.get_doc("Tender Preparation Version", root.approved_version or root.current_version)
	renders = render_service.render(root, version, snap.load(version))
	html = renders["invitation_html"] if output == "invitation" else renders["issued_tender_html"]
	return {"outcome": "OK", "tender": root.name, "tender_version": version.name, "output": output, "html": html, "digest": renders["invitation_digest"] if output == "invitation" else renders["issued_tender_digest"], "problems": renders["problems"]}
