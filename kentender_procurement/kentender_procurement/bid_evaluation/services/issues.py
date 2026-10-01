# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReportEvaluationIssue, RetryEvaluationOperation and rule reconciliation
(EVL-CHG-001 v0.4 §4.1, §4.3, §6 "Technical issues…", §7.2, §8
EVL_RULE_UNAVAILABLE; tracker EVL4-607; board D08-RULE).

The chair or secretary reports a rule or service problem against the
affected requirement. The issue goes to the platform support record with the
operation and a safe reference, never bids or findings; the requirement's
discussion item passes to that issue, and the issued requirement and every
other result stay available. Support repairs the service and can decide no
result. When a corrected rules implementation is installed, the sweep reruns
the checks for every bid with the reason "Rule correction", keeps the
earlier run, and resolves each rule issue whose requirement no longer lacks
its rule. Nothing clears on reading or on a "mark as read"."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import checks, conclusion, findings, guards, people, prc, records, rules
from kentender_procurement.bid_evaluation.services.errors import invalid

MODULE = "Bid Evaluation"


def correlation(doc, bid: str, requirement_key: str) -> str:
	return f"rule:{doc.name}:{bid}:{requirement_key}"


def report_issue(*, tender: str, bid: str, requirement_key: str, description: str, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_core.services import support_issues

	payload = {"bid": bid, "requirement_key": requirement_key, "description": description}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		conclusion.require_recorder(doc, user)
		guards.closed(doc, guards.Guards()).raise_if_any()
		invalid({"description": "Describe the problem."} if not cstr(description).strip() else {})
		requirement = findings._requirement(doc, bid, requirement_key)
		issue = support_issues.open_issue(module=MODULE, operation="ReportEvaluationIssue", operation_correlation=correlation(doc, bid, requirement_key),
			subject=f"Resolve evaluation issue for {doc.tender_reference}", reference_doctype=records.CASE, reference_name=doc.name,
			safe_detail=f"{requirement['label']}: {cstr(description).strip()}", reported_by=user, holder_role=people.EVALUATION_SUPPORT,
			fixture_namespace=records.namespace())
		item = conclusion.open_item_for(doc, bid, requirement_key) or findings.open_item(doc, bid, requirement_key,
			subject=f"{requirement['label']} — evaluation rule issue", user=user, finding="")
		findings.clear_item(doc, item, kind="Support issue", reference=issue["issue_id"])
		event = prc.owner_event(doc, "EvaluationIssueReported", f"issue:{issue['issue_id']}:{idempotency_key}", {"issue": issue["issue_id"],
			"requirement": requirement_key}, idempotency_key=idempotency_key)
		records.bump(doc, last_committed_event=event)
		return records.summary(doc, issue=issue["issue_id"], created=issue["created"])

	return records.command("ReportEvaluationIssue", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def reconcile_rules(tender: str) -> dict[str, Any] | None:
	"""Rerun the checks when the installed rules differ from the current run's."""
	from kentender_core.services import support_issues
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	name = records.case_for(tender)
	if not name:
		return None
	doc = frappe.get_doc(records.CASE, name)
	run = checks.current_run(name)
	if doc.state != "Reviewing" or not run:
		return None
	fact = tenders.publication_fact(tender) or {}
	try:
		digest = rules.load(cstr(fact.get("product_key")), template_release=cstr(fact.get("template_release")),
			release_id=cstr(fact.get("template_release_id")))["_digest"]
	except rules.RulesUnavailable:
		digest = ""
	if digest == cstr(frappe.db.get_value(checks.RUN, run, "rules_digest")):
		return None
	key = f"rule-correction:{name}:{digest or 'none'}"

	def body() -> dict[str, Any]:
		locked = records.lock(tender)
		ran = checks.run(locked, reason="Rule correction", idempotency_key=key, affected={"rules_digest": digest})
		still = {(r.evaluation_bid, r.requirement_key) for r in frappe.get_all(checks.RESULT, filters={"check_run": ran["run"], "basis": "Rule unavailable"},
			fields=["evaluation_bid", "requirement_key"])}
		for issue in frappe.get_all("Support Issue", filters={"module": MODULE, "operation": "ReportEvaluationIssue", "reference_name": name, "status": "Open"},
				fields=["operation_correlation"]):
			_rule, _case, bid, requirement = issue.operation_correlation.split(":", 3)
			if (bid, requirement) not in still:
				support_issues.resolve_on_success(module=MODULE, operation_correlation=issue.operation_correlation, note="The corrected rule was applied.")
		return records.summary(locked, run=ran["run"])

	return records.command("RunEvaluationChecks", tender=tender, idempotency_key=key, actor="system", payload={"digest": digest}, body=body)
