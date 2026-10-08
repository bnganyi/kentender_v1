# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EnsureEvaluationPreparation (EVL-CHG-001 v0.4 §5.1 "Scope gate" and
"Preparation trigger", §7.2; tracker EVL4-401, EVL4-402).

On the first authoritative publication of an in-scope tender, Evaluation
records one preparation case; the Accounting Officer's appointment task
follows from its state (v0.8: the Head of Procurement Function is recorded as
secretary when the committee is appointed, so holds no preparation task). Publication
supplies only the published tender reference and scope, never sealed-box
facts. A replay or addendum creates nothing new. A known unsupported scope
creates no case and no task. Missing or conflicting scope metadata creates a
named issue for the Tenders owner, and no case, until the owner repairs it
and the same publication identity is retried. A final no-bids or
cancellation outcome takes precedence and prevents new preparation. The same
operation runs on a valid nonempty opening intake as a recovery path."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import clock, notify, people, prc, records

SOURCES = ("Publication", "Opening intake")
SCOPE_ISSUE_ROLE = people.HEAD_OF_PROCUREMENT


def case_id(tender_reference: str) -> str:
	return f"EVL-{cstr(tender_reference).removeprefix('TND-')}"


def _scope_issue(tender: str, fact: dict[str, Any], issues: list[str]) -> dict[str, Any]:
	from kentender_core.services import support_issues

	return support_issues.open_issue(module="Bid Evaluation", operation="EnsureEvaluationPreparation", operation_correlation=f"scope:{tender}",
		subject=f"Resolve the evaluation scope for {fact['tender_reference']}", reference_doctype="Tender", reference_name=tender,
		safe_detail=" ".join(issues), holder_role=SCOPE_ISSUE_ROLE, fixture_namespace=records.namespace())


def ensure_preparation(*, tender: str, source: str = "Publication") -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import evaluation_seam as opening
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	if source not in SOURCES:
		raise ValueError(f"Unknown preparation source {source!r}")
	existing = records.case_for(tender)
	if existing:
		doc = frappe.get_doc(records.CASE, existing)
		return records.summary(doc, prepared=False, existing=True)
	fact = tenders.publication_fact(tender)
	if not fact:
		return {"ok": False, "prepared": False, "reason": "not_published"}
	if fact["cancelled"]:
		return {"ok": False, "prepared": False, "reason": "cancelled"}
	outcome = (opening.final_outcome(tender) or {}).get("outcome")
	if outcome == "No bids":
		return {"ok": False, "prepared": False, "reason": "no_bids"}
	scope = tenders.scope_facts(tender)
	if scope["status"] == "Out of scope":
		return {"ok": False, "prepared": False, "reason": "out_of_scope", "predicates": scope["predicates"]}
	if scope["status"] == "Unresolved":
		issue = _scope_issue(tender, fact, scope["issues"])
		return {"ok": False, "prepared": False, "reason": "scope_unresolved", "issue": issue["issue_id"], "issues": scope["issues"]}

	key = f"EnsureEvaluationPreparation:{tender}:{fact['publication']}"

	def body() -> dict[str, Any]:
		if records.case_for(tender):
			return records.summary(frappe.get_doc(records.CASE, records.case_for(tender)), prepared=False, existing=True)
		dated = tenders.dated_rules(tender)
		definition = fact["definition"]
		doc = records.insert(frappe.get_doc({
			"doctype": records.CASE, "evaluation_id": case_id(fact["tender_reference"]), "tender": tender, "tender_reference": fact["tender_reference"],
			"tender_title": fact["title"], "state": "Preparing", "publication": fact["publication"], "publication_version": cstr(definition.get("definition_version")),
			"definition_id": cstr(definition.get("bid_definition_id")), "definition_version": definition.get("definition_version") or 0,
			"definition_digest": cstr(definition.get("definition_digest")), "prepared_from": source, "prepared_at": clock.now(),
			"validity_end": dated.get("validity_end"), "evaluation_deadline": dated.get("evaluation_deadline"), "record_version": 1,
		}))
		created = prc.create(doc, key)
		records.bump(doc, proceeding=created["proceeding"])
		event_id = prc.owner_event(doc, "EvaluationPrepared", f"prepared:{doc.name}", {"publication": fact["publication"], "source": source}, idempotency_key=key)
		records.bump(doc, last_committed_event=event_id)
		from kentender_core.services import support_issues

		support_issues.resolve_on_success(module="Bid Evaluation", operation_correlation=f"scope:{tender}", note="The scope was read from published values.")
		ref = doc.tender_reference
		notify.tell(doc, people.holders(people.ACCOUNTING_OFFICER), subject=f"Appoint evaluation committee for {ref}",
			message=f"Appoint the members who will evaluate {ref}.", key="appoint")
		return records.summary(doc, prepared=True, existing=False)

	return records.command("EnsureEvaluationPreparation", tender=tender, idempotency_key=key, actor="system", payload={"source": source}, body=body)
