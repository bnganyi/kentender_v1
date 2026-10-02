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
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.tenders.services import clock, compatibility, configuration_gateway, controls, correction, documents, draft_commands, evidence, handoff_gateway, lifecycle, review, serializer, template_binding
from kentender_procurement.tenders.services import guidance as guide
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.services.tender_roles import FORBIDDEN_RESPONSIBILITIES, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR, ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

PAGE = "tenders"
STATUS_FILTERS = (
	("ready", "Ready to start"), ("draft", "Draft"), ("returned", "Returned"), ("in_progress", "In progress"), ("awaiting_approval", "Awaiting procurement approval"),
	("approved", "Awaiting publication authorisation"), ("publishing", "Publication confirmation required"), ("published", "Published — open"),
	("ended", "Submission period ended"), ("cancelled", "Cancelled"), ("correction", "Requisition correction requested"),
)
# Work-summary cards, one rule for every persona: a card for each status where it is that persona's turn (lifecycle order), then
# In progress for the other Tenders in flight, which are waiting on someone else. A requisition not yet started is not a Tender.
COUNT_CARDS = (
	("ready", "Ready to start", "Approved requisitions awaiting a tender"),
	("draft", "Drafts", "Started, not yet submitted"),
	("returned", "Returned to me", "Sent back for correction"),
	("awaiting_approval", "Awaiting procurement approval", "Tenders submitted for procurement approval"),
	("approved", "Awaiting publication authorisation", "Approved tenders awaiting a publication decision"),
	("publishing", "Publication confirmation required", "Authorised tenders awaiting channel confirmation"),
)
IN_FLIGHT_KEYS = ("draft", "returned", "awaiting_approval", "approved", "publishing")
TURN_KEYS = {"officer": ("ready", "draft", "returned"), "hopf": ("awaiting_approval", "publishing"), "ao": ("approved",)}
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
	return frappe.get_all("Tender Channel Confirmation", filters={"publication": root.publication, "subject_type": "Tender package", "status": "Awaiting confirmation"}, pluck="channel_label", order_by="creation asc")


def tender_row(root, actor: str, roles: dict[str, bool]) -> dict[str, Any]:
	version = frappe.get_doc("Tender Version", root.current_version) if root.current_version else None
	status = cstr(root.overall_status)
	key, label, secondary, action_key, action_label, route = "", status, "", "view", "View", [PAGE, root.tender_reference]
	if status == "Draft" and version is not None:
		task_key, task_label = _first_attention_task(version)
		returned = _was_returned(version)
		if returned and task_key == "review":
			# a copied Draft keeps every value, so the row's Correct action goes
			# to the task the reviewer named, not to Review (TPR-DES-01 "returned")
			affected = lifecycle.AFFECTED_TASK_KEYS.get(cstr(frappe.db.get_value("Tender Version", version.predecessor_version, "return_affected_task")))
			if affected:
				task_key, task_label = affected, {"details": "Tender details", "requirements": "Supplier requirements", "review": "Review"}[affected]
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
		# §10.2 READER / TECHNICAL: permitted records with neutral statuses
		action_key, action_label, route, secondary = "view", "View", [PAGE, root.tender_reference], ""
		label = "Draft" if key in ("draft", "returned") else status
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


def turn_keys(roles: dict[str, bool]) -> tuple[str, ...]:
	held = {k for role, keys in TURN_KEYS.items() if roles[role] for k in keys}
	return tuple(k for k, _label, _sub in COUNT_CARDS if k in held)


def in_progress_keys(roles: dict[str, bool]) -> tuple[str, ...]:
	return tuple(k for k in IN_FLIGHT_KEYS if k not in turn_keys(roles))


def _counts(rows: list[dict[str, Any]], roles: dict[str, bool]) -> list[dict[str, Any]]:
	by_key: dict[str, int] = {}
	for row in rows:
		by_key[row["status_key"]] = by_key.get(row["status_key"], 0) + 1
	turn = turn_keys(roles)
	out = [{"key": k, "label": label, "value": by_key.get(k, 0), "sub": sub} for k, label, sub in COUNT_CARDS if k in turn]
	waiting = in_progress_keys(roles)
	out.append({"key": "in_progress", "label": "In progress", "value": sum(by_key.get(k, 0) for k in waiting), "sub": "With someone else, not yet published"})
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
	# the cards summarise the actor's whole queue; a card selects a filter, so filtering must not change them
	counts = [] if roles["technical"] or not (roles["officer"] or roles["hopf"] or roles["ao"]) else _counts(rows, roles)
	needle = cstr(search).strip().lower()
	if needle:
		rows = [r for r in rows if needle in f"{r['tender_reference']} {r['requisition_reference']} {r['purchase']}".lower()]
	if cstr(status).strip():
		wanted = cstr(status).strip()
		rows = [r for r in rows if r["status_key"] in in_progress_keys(roles)] if wanted == "in_progress" else [r for r in rows if r["status_key"] == wanted]
	if cstr(fiscal_year).strip():
		rows = [r for r in rows if r["fiscal_year"] == cstr(fiscal_year).strip()]
	return {
		"outcome": "OK",
		"mode": "technical" if roles["technical"] else ("actor" if (roles["officer"] or roles["hopf"] or roles["ao"]) else "reader"),
		"roles": roles,
		"can_start": roles["officer"],
		"counts": counts,
		"rows": rows,
		"filters": {"statuses": [{"key": k, "label": v} for k, v in STATUS_FILTERS], "fiscal_years": fiscal_years, "search": search, "status": status, "fiscal_year": fiscal_year},
		"count_label": f"{len(rows)} Tender" + ("" if len(rows) == 1 else "s"),
		"empty_text": "No Tenders match these filters." if not rows else "",
	}


# --------------------------------------------------------------------------
# GetTenderStart
# --------------------------------------------------------------------------


WHY_LABELS = {"Procurement category": "Category"}


def _reservation_rule_label(payload: dict[str, Any]) -> str:
	category = cstr(payload.get("reservation_category_value") or payload.get("reservation_category"))
	if not category or category == "None":
		return "No reservation"
	return f"Applicable verified {category} reservation rule · Version {len(payload.get('reservation_rule_snapshot_ids') or []) or 1}"


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
		# §10.15: a viewer who cannot read the linked Tender learns nothing
		# about it — no reference, title or owner (TND_HANDOFF_CONFLICT)
		can_open = _can(lambda: frappe.get_doc("Tender", consumer).check_permission("read")) if not (roles["officer"] or roles["hopf"] or roles["auditor"] or roles["technical"]) else True
		if not can_open:
			return {"outcome": "ALREADY_STARTED", "heading": "Requisition unavailable", "text": "This requisition cannot be used to start a Tender.", "can_open": False}
		root = frappe.db.get_value("Tender", consumer, ["name", "tender_reference"], as_dict=True)
		return {"outcome": "ALREADY_STARTED", "heading": "Tender already started", "text": f"This requisition is linked to {root.tender_reference}.", "tender": root.name, "tender_reference": root.tender_reference, "route": [PAGE, root.tender_reference], "can_open": True}
	payload = handoff_gateway.payload_of(handoff_doc)
	binding = None
	try:
		binding = template_binding.bind()
		template = {"available": True, "display_name": binding["display_name"], "template_version": binding["template_version"], "official_source_title": binding["official_source_title"], "official_source_digest": binding["official_source_digest"], "bundle_digest": binding["bundle_digest"]}
	except STDTemplateError as exc:
		template = {"available": False, "reason": exc.message, "std_template_route": template_binding.inspection_route(actor)}
	checks = compatibility.evaluate(payload, binding if binding else ())
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
		# §10.3 "Why this requisition is supported", in the board's words
		"why": [{"label": WHY_LABELS.get(c.check, c.check), "value": c.required if (c.ok and c.check == "Product") else c.actual} for c in checks],
		"reservation_rule": _reservation_rule_label(payload),
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


def period_rule(version) -> dict[str, Any] | None:
	"""v0.16 §5.2: the two preparation-period numbers the Tender details form shows and pre-fills from. The server decides at review."""
	state = serializer.officer_state(version)
	period = configuration_gateway.preparation_period(state.get("issue_date") or clock.today(), cstr(snap.load(version).get("procurement_category")) or "Goods")
	return {**period, "closing_time": controls.DEFAULT_CLOSING_TIME} if period else None


def shortened_period(version) -> dict[str, Any] | None:
	"""The figures when the saved deadline leaves less than the usual (default) tendering period, whether or not a reason is given."""
	state = serializer.officer_state(version)
	period = period_rule(version)
	if not period or not period["default_days"] or not state.get("issue_date") or not state.get("submission_deadline"):
		return None
	return configuration_gateway.period_shortfall(issue_date=state["issue_date"], submission_deadline=state["submission_deadline"], today=clock.today(), minimum_days=period["default_days"])


def period_problem(root, version=None) -> dict[str, Any] | None:
	"""§5.5.6 / §5.10: for an Approved Tender awaiting publication authorisation, the figures when its submission deadline no longer
	leaves the minimum preparation period after the earliest publication (the same check `AuthoriseTenderPublication` makes)."""
	if cstr(root.overall_status) != "Approved" or root.publication:
		return None
	version = frappe.get_doc("Tender Version", root.approved_version) if root.approved_version else version
	if version is None:
		return None
	state = serializer.officer_state(version)
	if not state.get("submission_deadline"):
		return None
	minimum = configuration_gateway.minimum_preparation_days(state.get("issue_date") or clock.today(), cstr(snap.load(version).get("procurement_category")) or "Goods")
	if not minimum:
		return None
	return configuration_gateway.period_shortfall(issue_date=state.get("issue_date"), submission_deadline=state.get("submission_deadline"), today=clock.today(), minimum_days=minimum)


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
		# §5.10: a refused guard is stated up front, not discovered by pressing the button
		if roles["ao"] and _can(lifecycle.require_segregation, version, actor, blocked_columns=("prepared_by", "submitted_by", "approved_by")) and not period_problem(root, version):
			actions.append("authorise_publication")
	if status == "Requisition correction requested" and roles["officer"]:
		if handoff_gateway.successors(plan_item_id=cstr(root.plan_item_id), user=actor):
			actions.append("start_corrected_tender_version")
	if status in ("Publication authorised", "Published — open", "Approved") and roles["hopf"]:
		actions.append("view_publication")
	if status == "Publication authorised":
		if roles["hopf"]:
			actions.append("confirm_publication_channel")
		if roles["ao"] and not frappe.db.exists("Tender Channel Confirmation", {"publication": root.publication, "subject_type": "Tender package", "status": "Confirmed"}):
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
			{"requisition_item_id": i.get("requisition_item_id"), "item_name": i.get("item_name"), "equipment_category": i.get("equipment_category"), "quantity": serializer.fmt_quantity(i.get("quantity")), "unit": i.get("unit") or "Each", "intended_use": i.get("intended_use"), "delivery_location": cstr(snapshot.get("delivery_location")), "latest_delivery_date": serializer.fmt_date_short(snapshot.get("latest_delivery_date")), "source_line_id": next((d.get("source_line_id") for d in snapshot.get("drawdown_lines") or [] if d.get("plan_item_line_id") == i.get("plan_item_line_id")), "")}
			for i in items
		],
		"goods_lines": lines,
		"technical_requirements": serializer.technical_rows(snapshot),
		"warranty_support": serializer.warranty_support(snapshot),
		"acceptance_requirements": serializer.acceptance_rows(snapshot),
		"related_services": serializer.related_services(snapshot),
		"supporting_materials": serializer.supporting_materials(snapshot),
		"counts": snap.counts(snapshot),
		"requirement_tables": requirement_tables(snapshot),
		"carried_summary": carried_summary(snapshot),
		"reservation_evidence": reservation_evidence(snapshot),
	}
	if internal:
		out["internal"] = {
			"authorised_value": f"KES {serializer.fmt_money(snap.total_value(snapshot))}", "strategic_objective": cstr(snapshot.get("strategic_objective_path") or snapshot.get("strategic_objective")),
			"plan_horizon": cstr(snapshot.get("plan_horizon")), "reservation_ids": snap.internal_context(snapshot)["reservation_ids"],
			"drawdown_lines": [{"drawdown_line_id": d.get("drawdown_line_id"), "source_line_id": d.get("source_line_id"), "plan_source_allocation_id": d.get("plan_item_line_id"), "contributing_org_unit": d.get("contributing_org_unit"), "requested_quantity": serializer.fmt_quantity(d.get("requested_quantity")), "requested_value": f"KES {serializer.fmt_money(d.get('requested_value'))}", "reservation_id": d.get("reservation_id")} for d in snapshot.get("drawdown_lines") or []],
			"note": "For internal review only — not included in supplier documents.",
		}
	return out


def _drawdown_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	"""One row per authorised item line with the contributing unit it was
	approved for (the boards' "Approved requirement" column)."""
	lines = {d.get("plan_item_line_id"): d for d in snapshot.get("drawdown_lines") or []}
	out = []
	for item in snapshot.get("items") or []:
		line = lines.get(item.get("plan_item_line_id")) or {}
		out.append({"item": cstr(item.get("item_name")), "unit_label": _ou_label(cstr(line.get("contributing_org_unit"))), "quantity": serializer.fmt_quantity(item.get("quantity")), "unit": cstr(item.get("unit") or "Each")})
	return out


def requirement_tables(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	"""§10.4 drawer / §10.5 item 6 — every authorised requirement, as the
	boards' four tables (equipment, technical, warranty and support,
	acceptance). Read-only; nothing here is editable (§4.3)."""
	delivery = " · ".join(v for v in (cstr(snapshot.get("delivery_location")), serializer.fmt_date_short(snapshot.get("latest_delivery_date"))) if v)
	warranty = serializer.warranty_support(snapshot)
	yes_no = lambda value: "Yes" if value else "No"
	return [
		{"key": "items", "columns": [{"label": "Item"}, {"label": "Approved requirement"}, {"label": "Quantity", "num": True}, {"label": "Delivery"}], "rows": [[r["item"], r["unit_label"], f"{r['quantity']} {r['unit']}", delivery] for r in _drawdown_rows(snapshot)]},
		{"key": "technical", "columns": [{"label": "Technical requirement"}, {"label": "Value"}], "rows": [[t["label"], _requirement_value(t)] for t in serializer.technical_rows(snapshot)]},
		{"key": "warranty", "columns": [{"label": "Warranty and support"}, {"label": "Value"}], "rows": [
			["Minimum warranty", f"{warranty['minimum_warranty_months']} months"], ["On-site support required", yes_no(warranty["onsite_support_required"])],
			["Maximum support response", f"{warranty['maximum_support_response_hours']} hours"], ["Manufacturer support required", yes_no(warranty["manufacturer_support_required"])],
			["Service location constraint", warranty["service_location_constraint"]], ["Support description", warranty["support_description"]],
		]},
		{"key": "acceptance", "columns": [{"label": "Acceptance check"}, {"label": "Pass condition"}, {"label": "Evidence"}], "rows": [[a["check_type"], a["pass_condition"], cstr(a["evidence_type"])] for a in serializer.acceptance_rows(snapshot)]},
	]


def _requirement_value(row: dict[str, Any]) -> str:
	""""Minimum 16 GB" — the comparison the requisition authorised, then the value."""
	value = f"{row['required_value']} {row['unit']}".strip()
	comparison = cstr(row.get("comparison"))
	return f"{comparison} {value}" if comparison in ("Minimum", "Maximum") else value


def carried_summary(snapshot: dict[str, Any]) -> list[dict[str, str]]:
	"""§10.5 item 6 — the four summary lines of "Requirements carried into the
	contract" (the full tables are revealed in place)."""
	rows = _drawdown_rows(snapshot)
	items = snapshot.get("items") or []
	unit = cstr((items[0].get("unit") if items else "") or "Each")
	names = ", ".join(dict.fromkeys(r["item"] for r in rows))
	split = f" ({' + '.join(r['quantity'] for r in rows)})" if len(rows) > 1 else ""
	place = ", ".join(v for v in (cstr(snapshot.get("delivery_location")),) if v)
	latest = serializer.fmt_date_short(snapshot.get("latest_delivery_date"))
	warranty = serializer.warranty_support(snapshot)
	support = [f"{warranty['minimum_warranty_months']} months"]
	if warranty["onsite_support_required"]:
		support.append("on-site")
	if warranty["maximum_support_response_hours"]:
		support.append(f"{warranty['maximum_support_response_hours']}-hour response")
	if warranty["service_location_constraint"]:
		constraint = warranty["service_location_constraint"]
		support.append(constraint[:1].lower() + constraint[1:])
	checks = [cstr(a["check_type"]).lower() for a in serializer.acceptance_rows(snapshot)]
	technical = len(snapshot.get("technical_requirements") or [])
	return [
		{"label": "Equipment", "text": f"{names} · {serializer.fmt_quantity(snap.total_quantity(snapshot))} {unit}{split}" + (f", {place}" if place else "") + (f", by {latest}" if latest else "")},
		{"label": "Technical", "text": f"{technical} mandatory requirement{'s' if technical != 1 else ''}"},
		{"label": "Warranty and support", "text": ", ".join(support)},
		{"label": "Acceptance", "text": f"{len(checks)} check{'s' if len(checks) != 1 else ''} — {', '.join(checks)}" if checks else "No acceptance checks"},
	]


def reservation_evidence(snapshot: dict[str, Any]) -> list[dict[str, str]]:
	"""§10.5 item 2 — the read-only evidence rows the verified reservation
	rules generate; the officer cannot edit the inherited treatment, and no
	rule identifier is shown in this routine view."""
	rows = []
	category = cstr(snapshot.get("reservation_category_value"))
	if category and category != "None":
		rows.append({"label": f"{category} reservation declaration and evidence", "summary": f"Suppliers must declare {category} eligibility and provide the published certificate reference, validity and evidence", "source": "Required by reservation rule"})
	if snapshot.get("county_resident_reservation"):
		rows.append({"label": "County-resident declaration and evidence", "summary": "Suppliers must declare county residence and provide the published evidence of it", "source": "Required by reservation rule"})
	return rows


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
	# §10.6 item 3 / TPR-DES-05 and DES-06 boards: the purchase is the header's
	# title, not a key fact (DES-07 composes its own row, publication.py)
	facts = [
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


def record_links(root, actor: str) -> list[dict[str, Any]]:
	"""Records other modules keep under this Tender (`kt_tender_record_links`),
	for example its bid opening (BOP-CHG-001 v0.10 §9). Each owner decides
	whether this reader may see its link; Tenders reads nothing of theirs."""
	out: list[dict[str, Any]] = []
	for path in frappe.get_hooks("kt_tender_record_links") or []:
		out += frappe.get_attr(path)(tender=root.name, user=actor) or []
	return out


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
			"template_release": cstr(root.template_release), "std_template_route": template_binding.inspection_route(actor, cstr(root.template_release_id)) if root.template_key else [],
			"template_notice": template_binding.release_notice(root, actor),
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
		# §5.9 / §10.17: the server-derived next step and Tender journey; the
		# editor's two tasks carry their own answers (DES-03 / DES-04)
		"guidance": guide.guidance(root, actor=actor, roles=roles, mode=mode),
		"period_problem": period_problem(root, version) if mode != "department" else None,
		"period_rule": period_rule(version) if mode != "department" else None,
		"task_steps": guide.task_steps(root, actor=actor, roles=roles, mode=mode) if root.overall_status == "Draft" and roles["officer"] and mode != "department" else {},
		"key_facts": key_facts(root, version, snapshot, internal=internal),
		"record_links": record_links(root, actor),
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


def _facts_block(facts: list[tuple[str, str] | tuple[str, str, bool]]) -> dict[str, Any]:
	return {"kind": "facts", "facts": [{"label": f[0], "value": cstr(f[1]), "wide": bool(f[2]) if len(f) > 2 else False} for f in facts]}


def _table_block(columns: list[str], rows: list[list[str]], *, title: str = "", num: tuple[int, ...] = (), muted: tuple[int, ...] = ()) -> dict[str, Any]:
	return {"kind": "table", "title": title, "columns": [{"label": c, "num": i in num} for i, c in enumerate(columns)], "rows": [[cstr(v) for v in r] for r in rows], "muted": list(muted)}


def _yes_no(value) -> str:
	return "Yes" if value else "No"


def _template_label(version) -> str:
	from kentender_procurement.std_templates.services import runtime as std_runtime

	try:
		release = std_runtime.release_doc(cstr(version.template_release_id))
		return f"{cstr(release.display_name)} · Version {cstr(release.template_release)}"
	except Exception:
		return cstr(version.template_release_id)


def _section_bodies(root, version, snapshot: dict[str, Any], state: dict[str, Any], evidence_rows: list[dict[str, Any]], *, internal: bool) -> dict[str, list[dict[str, Any]]]:
	"""§10.6 items 5–7 — each review section's content as the boards draw it
	(fact grids, titled tables, the evaluation list). Shared by DES-05/06/07/09."""
	meeting = serializer._meeting_details(state)
	delivery = " · ".join(v for v in (cstr(snapshot.get("delivery_location")), serializer.fmt_date_short(snapshot.get("latest_delivery_date"))) if v)
	intended = {cstr(i.get("plan_item_line_id")): cstr(i.get("intended_use")) for i in snapshot.get("items") or []}
	items = snapshot.get("items") or []
	equipment = [[r["item"], r["unit_label"], f"{r['quantity']} {r['unit']}", intended.get(cstr(items[i].get("plan_item_line_id")), "") if i < len(items) else "", delivery] for i, r in enumerate(_drawdown_rows(snapshot))]
	technical = [[t["label"], cstr(t.get("comparison") or "Required"), t["required_value"], t["unit"] or "—"] for t in serializer.technical_rows(snapshot)]
	warranty = next(t for t in requirement_tables(snapshot) if t["key"] == "warranty")["rows"]
	acceptance = [[a["check_type"], a["applies_to"], a["pass_condition"], cstr(a["evidence_type"])] for a in serializer.acceptance_rows(snapshot)]
	pricing = [[r["description"], f"{r['quantity']} {r['unit']}", r["unit_price"], r["tax"], r["line_total"]] for r in serializer.price_schedule(snapshot)["rows"]]
	supplier = [[r["label"], r["summary"]] for r in reservation_evidence(snapshot)] + [
		["Manufacturer authorisation", _yes_no(state.get("manufacturer_authorisation_required"))],
		["Product datasheets or brochures", _yes_no(state.get("datasheets_required"))],
		["Warranty confirmation", "Yes — required by authorised requisition"],
		["Past supply experience", f"Yes; {serializer.fmt_number(state.get('minimum_comparable_contracts'))} comparable contracts in {serializer.fmt_number(state.get('experience_period_years'))} years" if state.get("past_experience_required") else "No"],
		["After-sales support evidence", serializer._after_sales_text(state) if state.get("after_sales_evidence_required") else "No"],
	] + [[e["label"], f"{'Required' if e.get('mandatory') else 'Optional'} · proves {e['proves']}"] for e in evidence_rows]
	lineage = "; ".join(f"{cstr(d.get('source_line_id'))} · {serializer.fmt_quantity(d.get('requested_quantity'))} {cstr(d.get('unit') or 'Each')}" for d in snapshot.get("drawdown_lines") or [])
	requisition_version = frappe.db.get_value("Requisition Version", root.requisition_version, "version_number") if root.get("requisition_version") else None
	category = cstr(snapshot.get("reservation_category_value"))
	rule_ids = snapshot.get("reservation_rule_snapshot_ids") or []
	technical_facts = [
		("Template", _template_label(version)),
		("Reservation rule", f"Applicable verified {category} reservation rule · Version {len(rule_ids) or 1}" if category and category != "None" else "No reservation"),
		("Requisition", f"{cstr(snapshot.get('requisition_reference'))} · Authorised" + (f" · Version {requisition_version}" if requisition_version else "")),
		("Plan Item", cstr(snapshot.get("plan_item_id"))),
		("Item/source lineage", lineage, True),
	]
	mappings = _mapping_counts(root, version, snapshot)
	# W1: the board regeneration dropped §10.6 item 7's mappings and digests;
	# restored here (registered in the fidelity departures).
	technical_facts.append(("Requirement mappings", f"{mappings['technical_requirements']} technical requirements → {mappings['responses']} supplier responses, {mappings['evaluation']} evaluation checks, {mappings['contract']} contract obligations", True))
	if internal:
		for label, field in (("Package digest", "package_digest"), ("Response schema digest", "response_schema_digest"), ("Evaluation contract digest", "evaluation_contract_digest"), ("Contract projection digest", "contract_projection_digest"), ("Requisition snapshot digest", "requisition_snapshot_digest")):
			if version.get(field):
				technical_facts.append((label, cstr(version.get(field)), True))
	return {
		"details": [_facts_block([
			("Tender title", cstr(state.get("tender_title") or snapshot.get("requirement_title")), True), ("Issue date", serializer.fmt_date_short(state.get("issue_date"))),
			("Clarification deadline", serializer.fmt_datetime_short(state.get("clarification_deadline"))), ("Submission deadline", serializer.fmt_datetime_short(state.get("submission_deadline"))),
			*((("Reason for a shorter tendering period", cstr(state.get("shortened_period_reason")), True),) if cstr(state.get("shortened_period_reason")).strip() and shortened_period(version) else ()),
			("Tender validity", f"{serializer.fmt_number(state.get('tender_validity_days'))} days" if state.get("tender_validity_days") else ""),
			("Tender security", f"KES {serializer.fmt_money(state.get('tender_security_amount'))}" if state.get("tender_security_amount") is not None else ""),
			("Pre-tender meeting", f"Yes — {meeting}" if meeting else "No"),
		])],
		"requirements": [
			_table_block(["Item", "Approved requirement", "Quantity", "Intended use", "Delivery"], equipment, title="Equipment", num=(2,)),
			_table_block(["Requirement", "Comparison", "Value", "Unit"], technical, title="Technical requirements"),
			_table_block(["Label", "Value"], warranty, title="Warranty and support"),
			_table_block(["Check", "Applies to", "Pass condition", "Evidence"], acceptance, title="Acceptance checks"),
		],
		"pricing": [_table_block(["Line", "Quantity", "Unit price", "Tax", "Total"], pricing, num=(1,), muted=(2, 3, 4))],
		"supplier": [_table_block(["Requirement", "Detail"], supplier), {"kind": "list", "title": "How suppliers will be evaluated", "items": list(serializer.EVALUATION_STAGES)}],
		"contract": [_facts_block([
			("Inspection and acceptance location", cstr(state.get("inspection_location")), True), ("Payment timing", f"{serializer.fmt_number(state.get('payment_timing_days'))} days" if state.get("payment_timing_days") else ""),
			("Performance security", f"Yes; {serializer.fmt_number(state.get('performance_security_percent'))}%" if state.get("performance_security_required") else "No"),
			("Delay damages", f"{serializer.fmt_number(state.get('delay_damages_per_week_percent'))}% per week; maximum {serializer.fmt_number(state.get('maximum_delay_damages_percent'))}%" if state.get("delay_damages_per_week_percent") is not None else ""),
			("Contract contact office", cstr(state.get("contract_contact_office"))),
		])],
		"technical": [_facts_block(technical_facts)],
	}


def review_sections(root, version, snapshot: dict[str, Any], summary: dict[str, Any], *, internal: bool) -> list[dict[str, Any]]:
	"""§10.6 items 5–7 — six sections, each a plain summary plus its content
	blocks; only a section holding a Must fix or a Review note starts open,
	and it carries the count tag (§10.6 item 5)."""
	state = serializer.officer_state(version)
	evidence_rows = [{**r, "proves": evidence.proves_label(r, snapshot)} for r in evidence.rows_as_dicts(version)]
	lines = serializer.goods_lines(snapshot)
	findings = summary.get("findings") or []

	def owner(f) -> str:
		if controls.CATALOGUE.get(f.get("field") or "", {}).get("group") == "contract":
			return "contract"
		return {"details": "details", "requirements": "supplier"}.get(f.get("task"), "")

	def tag(key: str) -> str:
		mine = [f for f in findings if owner(f) == key]
		must = sum(1 for f in mine if f["severity"] == review.MUST_FIX)
		notes = len(mine) - must
		parts = ([f"{must} must fix"] if must else []) + ([f"{notes} review note{'s' if notes != 1 else ''}"] if notes else [])
		return " · ".join(parts)

	bodies = _section_bodies(root, version, snapshot, state, evidence_rows, internal=internal)
	heads = [
		("details", "Tender details", f"Issue {serializer.fmt_date_short(state.get('issue_date'))} · clarification {serializer.fmt_datetime_short(state.get('clarification_deadline'))} · submission {serializer.fmt_datetime_short(state.get('submission_deadline'))} · validity {serializer.fmt_number(state.get('tender_validity_days'))} days · security KES {serializer.fmt_money(state.get('tender_security_amount'))}"),
		("requirements", "Requirements from the authorised requisition", f"{len(snapshot.get('items') or [])} items · {len(snapshot.get('technical_requirements') or [])} technical requirements · {len(snapshot.get('acceptance_requirements') or [])} acceptance checks"),
		("pricing", "Supplier pricing schedule", f"{len(lines)} line{'s' if len(lines) != 1 else ''} · unit price and tax completed by supplier · totals calculated from supplier response"),
		("supplier", "Supplier and evaluation requirements", _supplier_summary(state, evidence_rows)),
		("contract", "Contract terms", f"Payment {serializer.fmt_number(state.get('payment_timing_days'))} days · performance security {serializer.fmt_number(state.get('performance_security_percent')) + '%' if state.get('performance_security_required') else 'not required'} · delay damages {serializer.fmt_number(state.get('delay_damages_per_week_percent'))}% per week, maximum {serializer.fmt_number(state.get('maximum_delay_damages_percent'))}%"),
		("technical", "Technical evidence", f"Template {cstr(version.template_release_id)} · {len(lines)} rendered line{'s' if len(lines) != 1 else ''} from {len(snapshot.get('items') or [])} items"),
	]
	return [{"key": key, "title": title, "summary": text, "tag": tag(key), "open": bool(tag(key)), "blocks": bodies[key]} for key, title, text in heads]


def _mapping_counts(root, version, snapshot: dict[str, Any]) -> dict[str, Any]:
	"""§10.6 item 7 — how many published technical requirements the compiled
	Published Bid Definition maps to a response, an evaluation group and a
	contract obligation (none while the Version cannot compile yet)."""
	from kentender_procurement.tenders.services import bid_definition

	out: dict[str, Any] = {"technical_requirements": len(snapshot.get("technical_requirements") or []), "responses": 0, "evaluation": 0, "contract": 0}
	try:
		sets = bid_definition.technical_mapping_sets(bid_definition.compile_version(root, version))
	except (TendersError, frappe.ValidationError):
		return out
	out.update({"responses": len(sets["supplier response"]), "evaluation": len(sets["evaluation"]), "contract": len(sets["contract"])})
	return out


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
		# the fresh review decides: a must-fix item withdraws Submit (§10.6 Needs attention)
		"allowed_actions": [a for a in allowed_actions(root, version, actor, roles) if not (a == "submit_for_approval" and summary["must_fix_count"])] if mode != "department" else ["view_history"],
		"segregation_message": segregation_message(root, version, actor, roles),
		"submit_blocked_text": "Fix the item above before submitting." if summary["must_fix_count"] else "",
		# §10.6 confirmation: the eligible HOPF is named when one person holds it
		"submit_note": f"The submitted Version will be locked. {guide._display(guide._holders(ROLE_HEAD_OF_PROCUREMENT_FUNCTION), 'The Head of Procurement Function')} can return it or approve the package for publication review.",
		"guidance": guide.guidance(root, actor=actor, roles=roles, mode=mode, context="review", review_summary=summary),
	}
