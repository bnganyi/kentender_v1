# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-11 shows (BDS-CHG-001 v0.8 §10.12; plan Phase 11, slice
11.11), decided here from the Draft, its readiness and the published
definition's own compositions — never from board rows:

- the one header action this viewer may take: Submit bid for the Authorised
  Signatory on a Ready bid while supplier portal information is complete;
  Continue saved bid while it is being restored; otherwise none;
- the computed result ("All required bid information is complete.") on a
  Ready bid, and the availability notice in its place while a bid still in
  preparation waits on portal information;
- the physical original as this supplier's own bid knows it;
- the summary grid, the five tasks with their exact issue links (a rejected
  file at its row; a response an addendum changed at its task), what is
  offered (the goods response and the warranty obligations), the
  declarations and evidence, and the price summary.

Nothing here saves anything."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import addendum, company_view, guidance, labels, price, projection, readiness, tender_security, tenders_gateway, workspace_view

TITLE = "Review bid"
DESCRIPTION = "Check the complete bid before submitting it to the electronic tender box."
READY_TEXT = "All required bid information is complete."
TONES = {"Complete": "live", "Needs attention": "attention"}
# What is offered, by the definition's own goods field keys and warranty
# obligation keys (the published facts name them; a Tender without one simply
# has no such line).
GOODS_FACTS = (("offered_make_model", "Offered model"), ("offered_delivery_date", "Delivery"))
WARRANTY_FACTS = (("minimum_warranty_months", "Warranty"), ("maximum_support_response_hours", "Support response"))
SIGNATORY_OWN = {"BDS_SIGNATORY_CERTIFICATE_REQUIRED"}
# Guidance fixes that would lead back to this page or repeat its header action.
PAGE_FIXES = ("review_bid", "continue_bid")


def _lower(text: str) -> str:
	return text[:1].lower() + text[1:]


def _value(ctx, field) -> str:
	value = ctx.value(field)
	if value in (None, "", []):
		return ""
	if field.control_id == "CTL-DATE":
		return labels.date_label(value)
	return ", ".join(cstr(v) for v in value) if isinstance(value, list) else cstr(value)


def offering(ctx) -> list[dict[str, str]]:
	rows: list[dict[str, str]] = []
	for group in ctx.model.groups_of("requirements"):
		facts = group.published_facts or {}
		if group.composition_id == "COMP-GOODS-OFFER":
			by_key = {f.field_key: f for f in group.fields}
			for key, label in GOODS_FACTS:
				if key in by_key:
					rows.append({"label": label, "value": _value(ctx, by_key[key])})
			if facts.get("quantity"):
				rows.insert(1, {"label": "Quantity", "value": f"{cstr(facts['quantity'])} {cstr(facts.get('unit'))}".strip()})
		if group.composition_id == "COMP-WARRANTY-SUPPORT":
			label = dict(WARRANTY_FACTS).get(cstr(facts.get("obligation_key")))
			answer = next((f for f in group.fields if f.control_id not in ("CTL-EVIDENCE", "CTL-LONG-TEXT") and "compliance" not in f.label.lower()), None)
			if label and answer:
				value = _value(ctx, answer)
				unit = cstr(facts.get("unit"))
				rows.append({"label": label, "value": f"{value} {unit}".strip() if value else ""})
	order = [label for _k, label in GOODS_FACTS[:1]] + ["Quantity"] + [label for _k, label in GOODS_FACTS[1:]] + [label for _k, label in WARRANTY_FACTS]
	return sorted(rows, key=lambda r: order.index(r["label"]))


def _evidence_fields(tasks):
	return [(key, fs) for key, state in tasks.items() for fs in state.fields if fs.visible and fs.field.kind == "evidence"]


def _counted(parts: list[tuple[int, str]]) -> str:
	return " · ".join(f"{n} {word}" for n, word in parts if n) or "None"


def declarations(ctx, tasks, published: dict[str, Any], security: dict[str, Any]) -> list[dict[str, str]]:
	rows = company_view.declarations(ctx, tasks, projection.task_view(ctx, tasks, "company")["groups"])
	confirmed = sum(1 for r in rows if r["status"] == "Confirmed")
	complete = sum(1 for r in rows if r["status"] == "Complete")
	open_rows = len(rows) - confirmed - complete
	fields = _evidence_fields(tasks)
	accepted = sum(1 for _k, fs in fields for f in (projection.field_view(ctx, fs).get("evidence") or {}).get("files") or [] if f["status"] == "Accepted")
	rejected = sum(1 for _k, fs in fields if fs.issue and fs.issue["text"] == readiness.REJECTED_FILE)
	out = [
		{"label": "Declarations", "value": _counted([(confirmed, "confirmed"), (complete, "complete"), (open_rows, "to complete")])},
		{"label": "Evidence items", "value": _counted([(accepted, "accepted"), (rejected, "rejected")])},
	]
	if security.get("required"):
		recorded = security["physical_receipt_status"] != tender_security.NOT_RECORDED
		out += [
			{"label": "Tender security reference", "value": security.get("reference") or "—"},
			{"label": "Physical receipt", "value": security["physical_receipt_reference"] if recorded else "Not yet recorded"},
		]
	return out


def _issues(ctx, tasks, base: str) -> dict[str, list[dict[str, str]]]:
	"""Each task's exact issue links: a rejected file at its row; a response an
	addendum changed at its task (§10.12 variants)."""
	out: dict[str, list[dict[str, str]]] = {}
	for key, fs in _evidence_fields(tasks):
		if fs.issue and fs.issue["text"] == readiness.REJECTED_FILE:
			item = projection.group_handle(ctx, fs.field.group)
			out.setdefault(key, []).append({"label": f"Replace the rejected {_lower(fs.field.label)}", "href": f"{base}/{key}?item={item}"})
	changed = guidance.change_label(ctx.workspace.tender)
	for key in addendum.attention(ctx):
		if key in tasks and key not in ("documents", readiness.REVIEW_TASK) and tasks[key].status == "Needs attention" and key not in out:
			out[key] = [{"label": f"Confirm the current {changed}", "href": f"{base}/{key}"}]
	return out


def summary(ctx, published: dict[str, Any], root, total: str, *, at) -> list[dict[str, str]]:
	ws, arrangement = ctx.workspace, ctx.arrangement
	joint = arrangement.arrangement_type == "Joint venture"
	signatory = company_view.signatory(ctx, at=at)
	return [
		{"label": "Tender", "value": f"{cstr(published.get('title'))} · {ws.tender_reference}"},
		{"label": "Bidder", "value": f"{ctx.tenderer_name} · {'Joint venture' if joint else 'Single organisation'}"},
		{"label": "Bid", "value": f"{ws.name} · Draft Version {int(ws.current_draft_version or 0)}"},
		{"label": "Current deadline", "value": labels.datetime_label(root.submission_deadline) if root else ""},
		{"label": "Signatory", "value": " · ".join(x for x in (signatory["name"], signatory["job_title"]) if x) if signatory else "—"},
		{"label": "Bid total", "value": total or "—", "strong": True},
	]


def view(ctx, tasks, guided: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	published = tenders_gateway.published_tender(ws.tender_reference, at=at) or {}
	root = tenders_gateway.tender_root(ws.tender_reference)
	closed = ws.status in workspace_view.CLOSED_STATES or workspace_view._closed(root, at)
	ready = readiness.bid_status(tasks) == "Ready to submit"
	codes = {b["reason_code"] for b in (guided.get("submit_guard") or {}).get("blockers") or []}
	incomplete = workspace_view.portal_incomplete()

	nav = projection.task_nav(ctx, tasks)
	first_open = next((row["key"] for row in nav if row["key"] != readiness.REVIEW_TASK and row["status"] != "Complete"), "")
	# Submit bid only when nothing but the signatory's own certificate stands in
	# the way (the Submit page checks it); the production switch, signing or
	# custody outages, missing portal information, an uncertain attempt or the
	# representative's role each keep it absent (§5.10, BDS01-IMP-051).
	submit = {"label": "Submit bid", "href": f"{base}/submit"} if ready and not closed and not (codes - SIGNATORY_OWN) else None
	if submit:
		action = {**submit, "tone": "primary"}
	elif incomplete and not closed:
		action = {"label": "Continue saved bid", "href": f"{base}/{first_open}" if first_open else base, "tone": "secondary" if ready else "primary"}
	else:
		action = None

	notice = None if ready else workspace_view.availability_notice(ws, root, at)
	security = tender_security.response(ctx)
	physical = company_view.physical(security, published)
	if physical and physical["tone"] == "live":
		physical = {"tone": "live", "title": "", "text": f"Physical tender-security original recorded as received on {security['physical_received_at']}."}
	calc = price.summary(ctx)
	issues = _issues(ctx, tasks, base)
	rows = [
		{"key": row["key"], "label": row["label"], "status": row["status"], "tone": TONES.get(row["status"], "draft"), "issues": issues.get(row["key"], []),
		 "href": "" if row["key"] == readiness.REVIEW_TASK else f"{base}/{row['key']}"}
		for row in nav
	]
	next_step = dict(guided["next_step"])
	next_step["fixes"] = [f for f in next_step.get("fixes") or [] if f.get("fix_id") not in PAGE_FIXES]
	from kentender_procurement.bid_submission.services import guidance

	hand_over = guidance.hand_over(ctx, at)
	description = f"This is the complete bid as it will be submitted. {', '.join(hand_over)} (Authorised Signatory) signs and submits it; only an Authorised Signatory can." if hand_over else DESCRIPTION
	from kentender_procurement.bid_submission.services import signatory_notice

	handover = signatory_notice.status(ctx, at=at)
	return {
		**({"handover": handover} if handover else {}),
		"page": {"title": TITLE, "description": description, "back_href": base, "action": action},
		"next_step": next_step,
		"result": {"tone": "live", "text": READY_TEXT} if ready else None,
		"availability_notice": notice,
		"security_notice": physical,
		"summary": summary(ctx, published, root, calc["total"], at=at),
		"task_rows": rows,
		"offering": offering(ctx),
		"declarations": declarations(ctx, tasks, published, security),
		"price_summary": [
			{"label": "Subtotal excluding tax", "value": calc["subtotal"] or "—"}, {"label": "Tax", "value": calc["tax"] or "—"},
			{"label": "Bid total", "value": calc["total"] or "—", "strong": True},
		],
		"footer": {"back_href": base, "submit": submit},
	}
