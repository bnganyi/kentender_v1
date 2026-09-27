# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What the portal receives about a bid (BDS-CHG-001 v0.8 §4.4.5, §4.4.8 and
plan D11). Fields travel by opaque handle; groups by an opaque group handle;
published facts only from a vetted list of display facts; a declaration by
its resolved published statement. No response, composition, control, rule,
evaluation or definition identity, digest or path is ever included."""

from __future__ import annotations

import hashlib
from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, tenders_gateway
from kentender_procurement.bid_submission.services.bid_context import BidContext
from kentender_procurement.bid_submission.services.definition_model import Field, Group
from kentender_procurement.bid_submission.services.product_profile import COMPOSITION_HEADINGS
from kentender_procurement.bid_submission.services.readiness import FieldState, TaskState

#: Published facts a bidder may see, in display order, with their labels.
DISPLAY_FACTS: tuple[tuple[str, str], ...] = (
	("description", "Description"), ("equipment_category", "Category"), ("quantity", "Quantity"), ("unit", "Unit"), ("destination", "Delivery location"),
	("latest_delivery_date", "Latest delivery"), ("minimum_warranty_months", "Minimum warranty (months)"), ("applies_to", "Applies to"),
	("comparison", "Requirement"), ("required_value_display", "Required"), ("amount", "Amount"), ("currency", "Currency"), ("permitted_forms", "Permitted forms"),
	("validity_date", "Valid until at least"), ("bank_guarantee_expiry_date", "Bank guarantee valid until at least"),
	("insurance_guarantee_expiry_date", "Insurance guarantee valid until at least"), ("category", "Reservation"), ("entry_number", "Contract"),
	("required_count", "Contracts required"), ("period_years", "Within the last (years)"), ("window_start", "From"), ("window_end", "To"),
	("check_type", "Check"), ("pass_condition", "Passes when"), ("evidence_type", "Evidence"), ("purpose", "Purpose"), ("requirement_text", "What to provide"),
)
_DATE_FACTS = {"latest_delivery_date", "validity_date", "bank_guarantee_expiry_date", "insurance_guarantee_expiry_date", "window_start", "window_end"}
SUPPLIED_FROM = {"SV-ORGANISATION": "account", "SV-ARRANGEMENT": "arrangement", "SV-ARRANGEMENT-MEMBER": "member_account", "SV-SIGNATORY": "signatory"}


def group_handle(ctx: BidContext, group: Group) -> str:
	return "g" + hashlib.sha256(f"{ctx.model.digest}\x00{group.key}".encode("utf-8")).hexdigest()[:16]


def _fact_value(key: str, value) -> str:
	if isinstance(value, list):
		return ", ".join(cstr(v) for v in value)
	if key in _DATE_FACTS and value:
		return labels.date_label(value)
	if key == "amount" and value:
		return labels.money_label(value, "")
	return cstr(value)


def facts(group: Group) -> list[dict[str, str]]:
	published = group.published_facts
	return [{"label": label, "value": _fact_value(key, published[key])} for key, label in DISPLAY_FACTS if published.get(key) not in (None, "", [])]


def statement(ctx: BidContext, group: Group) -> str:
	text_id = group.published_facts.get("text_id")
	if not text_id:
		return ""
	row = next((t for t in ctx.model.definition.get("declaration_texts") or [] if t.get("text_id") == text_id), {})
	return cstr(row.get("resolved_text") or row.get("locked_text"))


def heading(ctx: BidContext, group: Group) -> str:
	if group.published_facts.get("label"):
		return cstr(group.published_facts["label"])
	return COMPOSITION_HEADINGS.get(group.composition_id, "")


def member_name(ctx: BidContext, group: Group) -> str:
	if not group.member:
		return ""
	return next((cstr(m.legal_name) for m in ctx.arrangement.members if m.organisation_id == group.member), "")


def label(ctx: BidContext, field: Field) -> str:
	text = field.label
	if "bidder_name" in field.label_parameters:
		text = text.replace("{bidder_name}", ctx.tenderer_name)
	if "addendum_reference" in field.label_parameters:
		reference = tenders_gateway.addendum_reference(ctx.workspace.tender, cstr(field.group.published_facts.get("addendum_id")))
		text = text.replace("{addendum_reference}", reference or "the addendum")
	return text


def _options(field: Field) -> list[str] | None:
	params = field.validation_parameters
	if field.kind == "yes_no":
		return ["Yes", "No"]
	if field.kind in ("single_choice", "multi_select"):
		return list(params.get("options") or [])
	if field.kind == "ports":
		return list(params.get("port_options") or [])
	return None


def _limits(field: Field) -> dict[str, Any]:
	params = field.validation_parameters
	keep = {"min_length", "max_length", "minimum", "maximum", "scale", "currency"}
	out = {k: v for k, v in params.items() if k in keep}
	if params.get("not_before"):
		out["not_before"] = cstr(params["not_before"])
	if params.get("not_after"):
		out["not_after"] = cstr(params["not_after"])
	return out


def _shown_when(ctx: BidContext, field: Field) -> dict[str, Any] | None:
	rule = field.visibility_rule or {}
	if rule.get("rule_id", "VS-ALWAYS") == "VS-ALWAYS":
		return None
	keys = rule.get("field_keys") or [rule.get("field_key")]
	handles = [f.handle for f in field.group.fields if f.field_key in keys]
	return {"handles": handles, "values": [rule.get("value")]}


def field_view(ctx: BidContext, state: FieldState) -> dict[str, Any]:
	field = state.field
	view: dict[str, Any] = {
		"handle": field.handle, "kind": field.kind, "label": label(ctx, field), "help": field.help_text, "editable": field.editable,
		"visible": state.visible, "required": state.required, "value": state.value, "shown_when": _shown_when(ctx, field), "issue": state.issue,
	}
	if field.supplied:
		view["supplied_from"] = SUPPLIED_FROM.get(field.supplied["source_id"], "account")
	options = _options(field)
	if options is not None:
		view["options"] = options
	limits = _limits(field)
	if limits:
		view["limits"] = limits
	if field.kind == "evidence":
		rule = field.evidence_rule or {}
		view["evidence"] = {
			"type": cstr(rule.get("evidence_type")), "minimum": int(rule.get("minimum") or 0), "maximum": int(rule.get("maximum") or 0), "mandatory": bool(rule.get("mandatory")),
			"files": [
				{"id": e["id"], "name": e["name"], "status": e["scan_status"], "size_bytes": e["size_bytes"], **({"reason": e["scan_result"]} if e["scan_status"] == "Rejected" else {})}
				for e in ctx.evidence.get(field.key, [])
			],
		}
	return view


def task_nav(ctx: BidContext, tasks: dict[str, TaskState]) -> list[dict[str, Any]]:
	return [
		{"key": t.key, "label": t.label, "purpose": t.purpose, "status": tasks[t.key].status, "must_fix": tasks[t.key].must_fix, "review_notes": tasks[t.key].review_notes}
		for t in ctx.model.tasks
	]


def task_view(ctx: BidContext, tasks: dict[str, TaskState], key: str) -> dict[str, Any]:
	state = tasks[key]
	states = {s.field.key: s for s in state.fields}
	groups = []
	for group in ctx.model.groups_of(key):
		groups.append({
			"key": group_handle(ctx, group), "heading": heading(ctx, group), "member": member_name(ctx, group), "facts": facts(group),
			"statement": statement(ctx, group), "fields": [field_view(ctx, states[f.key]) for f in group.fields],
		})
	task = ctx.model.task(key)
	return {"task": {"key": key, "label": task.label, "purpose": task.purpose, "status": state.status, "must_fix": state.must_fix, "review_notes": state.review_notes}, "groups": groups}
