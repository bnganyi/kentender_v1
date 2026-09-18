# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 `GetTenderHistory` — Versions, decisions,
correction lineage, channel confirmations, addenda, inquiries, cancellation
and downstream events, read-only, for the actor's permitted audience.
Protected inquiry-source identity is exposed to Auditor/technical readers
only (§12.3(7))."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import documents, draft_commands, events, publication_read, read, serializer
from kentender_procurement.tenders.services import tender_authorization as authz


def get_tender_history(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	name = draft_commands.resolve_tender_name(tender)
	root = frappe.get_doc("Tender", name)
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	roles = read.actor_roles(actor)
	internal = mode in ("site", "technical")
	oversight = roles["auditor"] or roles["technical"]
	versions = [read.version_summary(frappe.get_doc("Tender Version", n)) for n in frappe.get_all("Tender Version", filters={"tender": root.name}, pluck="name", order_by="version_number asc")]
	tasks = frappe.get_all("Tender Task", filters={"tender": root.name}, fields=["name", "tender_version", "task_type", "business_role", "status", "decision", "creation"], order_by="creation asc", limit_page_length=0) if internal else []
	out = {
		"outcome": "OK", "mode": mode,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "overall_status": cstr(root.overall_status), "requirement_title": cstr(root.requirement_title)},
		"versions": versions if internal else [{k: v["" if False else k] for k in ("name", "version_number", "status")} for v in versions],
		"decisions": read.decisions_for(root) if internal else [],
		"tasks": tasks,
		"documents": [{"document": d.name, "kind": d.kind, "digest": d.digest, "generated_at": cstr(d.generated_at), "generated_at_label": serializer.fmt_datetime_short(d.generated_at) if d.generated_at else "", "tender_version": cstr(d.tender_version), "addendum": cstr(d.addendum), "cancellation": cstr(d.cancellation)} for d in documents.list_for_tender(root.name)] if internal else [],
		"publication": publication_read.publication_summary(root, actor=actor, roles=roles) if internal else None,
		"open_period": publication_read.open_period_summary(root, actor=actor, roles=roles) if internal else None,
		"events": [
			{k: v for k, v in e.items() if k != "payload"} | {"occurred_at_label": serializer.fmt_datetime_short(e["occurred_at"]) if e.get("occurred_at") else "", "payload": e["payload"] if oversight else {}}
			for e in events.list_for_tender(root.name)
		] if internal else [],
	}
	if oversight:
		out["protected"] = {"inquiry_sources": frappe.get_all("Tender Addendum Inquiry", filters={"tender": root.name}, fields=["name", "candidate_identity", "producer", "inbound_event_id"], limit_page_length=0)}
	return out
