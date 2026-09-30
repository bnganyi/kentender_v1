# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published Tenders seam for Bid Evaluation (EVL-CHG-001 v0.4 §5.1, §5.7,
§6 "Tenders → Evaluation preparation" and "Tenders / downstream owner →
Evaluation"; EVL plan D8, D21, D22). Additive: no Tenders rule, record or
screen changes, and no sealed-box fact crosses here.

Bid Evaluation reads a Tender only through these functions:

- `evaluation_candidates()`: published (or later cancelled) Tenders bound to
  a template, for the preparation sweep;
- `publication_fact(tender)`: the authoritative publication and the
  published bid definition's identity;
- `scope_facts(tender)`: each §5.1 scope predicate bound to a published
  value (the installed release's `supported_use` for the definition's
  release, the Tender's product key and the price rows' currency), never a
  title or a default (D21; `reconciliation/scope_binding.md`);
- `dated_rules(tender)`: the tender-validity end from the published
  definition, with its counting rule, source and timezone; the statutory
  evaluation deadline only from an authoritative dated rule, and none exists
  yet (D22, FU-EVL-18);
- `status_events(tender)`: authoritative owner facts, today only the
  cancellation (TPR-CHG-001 v0.13 has no post-close cancellation, suspension
  or validity extension, FU-EVL-02);
- `award_decision_status(tender)`: whether a downstream award decision
  exists. Tenders owns the Tender's status and it has no awarded state, so
  "No award decision recorded" is read from that status; a failed read is
  "Unknown", never a guessed "no award" (§6)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

PUBLISHED = ("Published — open", "Submission period ended")
CANCELLED = "Cancelled"
PRODUCT_KEY = "IT-EQUIPMENT-OPEN-V1"
EXPECTED = {
	"procurement_method": ("Open Tender", "Open Tender"),
	"procurement_category": ("IT Goods", "Goods"),
	"lotting": ("One lot", "Single lot"),
	"currency": ("KES", "KES"),
	"price_treatment": ("Fixed price", "Fixed price"),
	"financial_evaluation": ("Lowest evaluated responsive", "lowest-evaluated-responsive"),
}


def evaluation_candidates() -> list[str]:
	return frappe.get_all("Tender", filters={"overall_status": ("in", (*PUBLISHED, CANCELLED)), "published_at": ("is", "set")}, pluck="name",
		order_by="published_at asc")


def _root(tender: str):
	return frappe.db.get_value("Tender", tender, ["name", "tender_reference", "requirement_title", "overall_status", "publication", "published_at",
		"submission_deadline", "product_key", "template_key", "template_release", "template_release_id", "cancellation", "approved_version", "current_version",
		"fixture_namespace"], as_dict=True)


def publication_fact(tender: str) -> dict[str, Any] | None:
	root = _root(tender)
	if not root or not root.published_at:
		return None
	from kentender_procurement.tenders.services import bid_definition, opening_seam

	stored = bid_definition.current(tender) or {}
	facts = opening_seam.tender_facts(tender) or {}
	return {
		"tender": root.name, "tender_reference": root.tender_reference, "title": cstr(facts.get("title") or root.requirement_title), "publication": cstr(root.publication),
		"published_at": root.published_at, "submission_deadline": root.submission_deadline, "status": cstr(root.overall_status),
		"cancelled": cstr(root.overall_status) == CANCELLED, "product_key": cstr(root.product_key),
		"definition": {k: stored.get(k) for k in ("bid_definition_id", "definition_version", "definition_digest")},
		"template_release_id": cstr(root.template_release_id), "template_release": cstr(root.template_release), "fixture_namespace": cstr(root.fixture_namespace),
	}


def definition(tender: str, definition_version=None) -> dict[str, Any] | None:
	"""The exact published bid definition a bid was made against."""
	from kentender_procurement.tenders.services import bid_definition

	return bid_definition.definition_for(tender, definition_version) if definition_version else bid_definition.current(tender)


def response_labels(tender: str, definition_version=None) -> dict[str, Any]:
	from kentender_procurement.tenders.services import opening_seam

	return opening_seam.definition_labels(tender, definition_version)


def _supported_use(release_id: str) -> dict[str, Any]:
	from kentender_procurement.std_templates.compiler import assets as release_assets
	from kentender_procurement.std_templates.services import runtime

	return runtime.asset_json(runtime.release_doc(release_id), release_assets.ASSET_FILES["product_profile"]).get("supported_use") or {}


def scope_facts(tender: str) -> dict[str, Any]:
	"""{status: In scope | Out of scope | Unresolved, predicates: [...], issues: [...]}."""
	root = _root(tender)
	if not root:
		return {"status": "Unresolved", "predicates": [], "issues": ["The Tender could not be read."]}
	stored = definition(tender) or {}
	body = stored.get("definition") or {}
	release_id = cstr(body.get("template_release_id") or root.template_release_id)
	issues: list[str] = []
	try:
		use = _supported_use(release_id) if release_id else {}
	except Exception:
		use = {}
		issues.append("The published template release could not be read.")
	if not release_id:
		issues.append("The published definition names no template release.")
	currencies = sorted({cstr(r.get("currency")) for r in body.get("price_rows") or [] if r.get("currency")})
	values = {
		"procurement_method": (cstr(use.get("procurement_method")), "release supported_use.procurement_method"),
		"procurement_category": (cstr(use.get("procurement_category")), "release supported_use.procurement_category"),
		"lotting": (f"{cstr(use.get('lotting_indicator'))} / {cstr(use.get('award_packages'))}" if use else "", "release supported_use.lotting_indicator, award_packages"),
		"currency": (cstr(use.get("currency")) if currencies in ([], [cstr(use.get("currency"))]) else "Conflicting", "release supported_use.currency and price_rows[].currency"),
		"price_treatment": (cstr(use.get("price_treatment")), "release supported_use.price_treatment"),
		"financial_evaluation": (cstr(use.get("financial_evaluation")), "release supported_use.financial_evaluation"),
	}
	predicates = [{"key": "product_key", "label": "IT Goods product key", "value": cstr(root.product_key), "expected": PRODUCT_KEY, "source": "Tender.product_key",
		"ok": cstr(root.product_key) == PRODUCT_KEY and cstr(root.template_key) == PRODUCT_KEY}]
	for key, (label, expected) in EXPECTED.items():
		value, source = values[key]
		if key == "lotting":
			ok = cstr(use.get("lotting_indicator")) == "Single lot" and cstr(use.get("award_packages")) == "1"
		elif key == "financial_evaluation":
			ok = expected in value.lower().replace(" ", "-")
		else:
			ok = value == expected
		predicates.append({"key": key, "label": label, "value": value, "expected": expected, "source": source, "ok": ok})
		if not value:
			issues.append(f"{label} is not published for this Tender.")
		elif value == "Conflicting":
			issues.append(f"{label} conflicts between the release and the price schedule.")
	if not root.product_key:
		issues.append("The product key is not published for this Tender.")
	if issues:
		status = "Unresolved"
	elif all(p["ok"] for p in predicates):
		status = "In scope"
	else:
		status = "Out of scope"
	return {"status": status, "predicates": predicates, "issues": issues, "release_id": release_id}


def dated_rules(tender: str) -> dict[str, Any]:
	root = _root(tender)
	stored = definition(tender) or {}
	body = stored.get("definition") or {}
	validity = None
	for section in body.get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") == "RR-TENDER-SECURITY" and group.get("published_facts", {}).get("validity_date"):
				validity = group["published_facts"]["validity_date"]
	deadline = get_datetime(root.submission_deadline) if root and root.submission_deadline else None
	validity_end = get_datetime(f"{validity} {deadline.time().isoformat()}") if validity and deadline else None
	return {
		"validity_end": validity_end,
		"validity_rule": {"counting": "Submission deadline date plus the published validity days, at the submission deadline's time of day",
			"source": "Published bid definition, tender security validity date", "timezone": "Site time (EAT)", "value": cstr(validity)} if validity_end else None,
		"evaluation_deadline": None,
		"evaluation_rule": None,
		"evaluation_rule_missing": "No authoritative dated rule for the statutory evaluation period is recorded (FU-EVL-18).",
	}


def status_events(tender: str) -> list[dict[str, Any]]:
	root = _root(tender)
	if not root or not root.cancellation:
		return []
	row = frappe.db.get_value("Tender Cancellation", root.cancellation, ["name", "reason", "ground_label", "decided_by", "decided_at"], as_dict=True)
	if not row:
		return []
	return [{"event_key": f"TND-CANCEL:{row.name}", "kind": "Cancellation", "source": "Tenders", "source_reference": row.name,
		"authority": cstr(row.decided_by), "reason": cstr(row.reason or row.ground_label), "effective_at": row.decided_at}]


def award_decision_status(tender: str) -> dict[str, Any]:
	from frappe.utils import now_datetime

	try:
		root = _root(tender)
		if not root:
			return {"status": "Unknown", "checked_at": now_datetime()}
		return {"status": "No award decision recorded", "checked_at": now_datetime(), "source": "Tender status"}
	except Exception:
		return {"status": "Unknown", "checked_at": now_datetime()}


def funding_reservations(tender: str) -> dict[str, Any]:
	"""The budget reservations this Tender draws on (read-only; EVL plan D9).
	The amounts come from Budget's own published contract, never from here."""
	from kentender_procurement.tenders.services import snapshot as snap

	root = _root(tender)
	name = (root.approved_version or root.current_version) if root else None
	if not name:
		return {"reservation_ids": [], "authorised_value": None}
	context = snap.internal_context(snap.load(frappe.get_doc("Tender Version", name)))
	return {"reservation_ids": context["reservation_ids"], "authorised_value": context["authorised_value"]}
