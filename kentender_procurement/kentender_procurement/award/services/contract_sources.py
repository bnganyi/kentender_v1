# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award's provider of the contract's source material (CM-CHG-001 v0.8 section 19.4; plan D20; tracker CM8-513, CM8-517).

Award is the integrator of an award: it hands Contracting references to the twelve sources the agreement is made from, and never copies. Each reference is `S<n>-<award case>`, resolved here by asking the
owner of the thing through that owner's published seam (Tenders for the issued tender, its schedules, conditions, criteria and Form No. 4; Bid Evaluation for the accepted offer and its prices; the site
configuration for the entity; Supplier Accounts for the supplier; Budget for the funding), plus what Award itself holds (the notification and the signing window; the restrictions). The content of a source is
canonical JSON (Form No. 4 is HTML), so its digest is stable, and Award freezes that digest in the package: a source that changes after the award then fails verification instead of being silently used.

A source nobody can build is not hidden: the provider says why (`unavailable`), the head of procurement sees the reason and its owner, and the agreement is not generated from the rest."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import clocks, state

OWNER = {
	"S1": "Tenders", "S2": "Bid Evaluation", "S3": "Bid Evaluation, Tenders", "S4": "Tenders", "S5": "Tenders", "S6": "Tenders", "S7": "Tenders and the template release", "S8": "Award",
	"S9": "Budget", "S10": "Site configuration", "S11": "Supplier Accounts", "S12": "Award",
}
CATEGORY = {
	"S1": "issued_tender_release_addenda", "S2": "accepted_tender_and_clarifications", "S3": "price_schedule", "S4": "requirements_and_technical_schedules", "S5": "gcc_scc_and_commercial_terms",
	"S6": "inspection_and_acceptance_criteria", "S7": "form_no_4_source", "S8": "award_notification_and_signing_window", "S9": "funding_lineage", "S10": "entity_identity",
	"S11": "supplier_identity_and_signatories", "S12": "restrictions_and_award_event",
}
#: sources that are live facts rather than frozen ones: a later restriction is not "a source that changed after the award" (it reaches Contracting as an update)
LIVE = {"S12"}
_REFERENCE = re.compile(r"^(S\d+)-(.+)$")


class Unavailable(Exception):
	"""The owner owns this but cannot give it now, and says why."""


def _json(value: Any) -> bytes:
	return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False).encode("utf-8")


# -- what Award itself holds --------------------------------------------------------------------------------------------------------------
def _s8(doc) -> tuple[bytes, str, str]:
	decision = state.committed_decision(doc)
	batch = state.current_batch(doc)
	notice = state.successful_notice(batch)
	if not decision or decision.outcome != "Award" or not notice or notice.status != "Given":
		raise Unavailable("The notification of award has not been given.")
	earliest = clocks.earliest_permitted(doc, batch)
	if not earliest.get("known"):
		raise Unavailable("The waiting period after the notification is not established.")
	rows = clocks.current(doc, "Minimum wait", notice.name)
	rule = frappe.db.get_value(clocks.CLOCK, rows[0].name, ["rule", "calendar", "timezone", "profile_version"], as_dict=True) if rows else None
	if not rule:
		raise Unavailable("The waiting period has no recorded rule.")
	from kentender_procurement.tenders.services import award_seam

	validity = award_seam.validity(doc.tender) or {}
	end = validity.get("validity_end")
	basis = f"{cstr(rule.rule)} ({cstr(rule.calendar)}; {cstr(rule.timezone)}; profile {cstr(rule.profile_version)})"
	if end:
		basis += f"; the window ends with the tender validity ({cstr((validity.get('rule') or {}).get('counting'))})"
	content = {"notification": {"id": notice.name, "given_at": cstr(notice.given_at), "digest": notice.content_digest}, "signing_window": {"result": "Established by Award",
		"earliest_signing_at": cstr(earliest["at"]), "ends_on": str(get_datetime(end).date()) if end else None, "counting_basis": basis}}
	return _json(content), "application/json", cstr(batch.version)


def _s12(doc) -> tuple[bytes, str, str]:
	decision = state.committed_decision(doc)
	if not decision:
		raise Unavailable("No decision is committed.")
	restrictions = [{"id": i.name, "type": i.issue_type, "state": i.state, "disposition": i.disposition} for i in
		(frappe.get_doc(state.ISSUE, n) for n in frappe.get_all(state.ISSUE, filters={"award_case": doc.name}, pluck="name", order_by="creation asc"))]
	return _json({"restrictions": restrictions, "event": "AwardDecisionRecorded v1", "event_id": f"{decision.name}-EVT"}), "application/json", cstr(decision.version)


# -- what the other owners give -----------------------------------------------------------------------------------------------------------
def _seam(module: str, function: str, **kwargs) -> Any:
	import importlib

	owner = importlib.import_module(module)
	try:
		return getattr(owner, function)(**kwargs)
	except owner.Unavailable as exc:
		raise Unavailable(str(exc)) from exc
	except frappe.DoesNotExistError as exc:
		raise Unavailable(cstr(exc)) from exc


def _s1(doc):
	data = _seam("kentender_procurement.tenders.services.contract_seam", "issued_instance", tender=doc.tender)
	return _json(data), "application/json", cstr(data["template_release"])


def _snapshot(doc) -> dict[str, Any]:
	rep = state.current_report(doc)
	if not rep:
		raise Unavailable("The evaluation report the award rests on is not held.")
	return state.snapshot(rep)


def _accepted(doc) -> tuple[str, str]:
	"""The frozen evaluation report and the accepted bid inside it (the award's decision names the same bid)."""
	snap = _snapshot(doc)
	decision = state.committed_decision(doc)
	bid = (snap.get("recommended") or {}).get("bid")
	if not decision or decision.outcome != "Award" or decision.bid_reference != (snap.get("recommended") or {}).get("bid_reference") or not bid:
		raise Unavailable("The decision does not name the bid the evaluation recommended.")
	return cstr(snap.get("report")), cstr(bid)


def _s2(doc):
	report, bid = _accepted(doc)
	data = _seam("kentender_procurement.bid_evaluation.services.contract_seam", "accepted_offer", report=report, bid=bid)
	return _json(data), "application/json", cstr(data["report"]["version"])


def _s3(doc):
	report, bid = _accepted(doc)
	prices = _seam("kentender_procurement.bid_evaluation.services.contract_seam", "awarded_prices", report=report, bid=bid)
	decision = state.committed_decision(doc)
	lines, total = [], Decimal("0")
	for line in prices["lines"]:
		quantity, line_total, net = Decimal(line["quantity"]), Decimal(line["line_total"]), Decimal(line["unit_price"])
		if quantity <= 0 or line_total % quantity != 0:
			raise Unavailable(f"Line {line['line']} does not divide into a whole unit price including tax.")
		rate = line_total / quantity
		total += line_total
		lines.append({"line_id": f"L{line['line']}", "item": line["description"], "description": line["description"], "uom": line["unit"], "quantity": int(quantity), "rate": float(rate), "amount": float(line_total),
			"net_rate": float(net), "tax_amount": float(Decimal(line["tax_amount"])), "amount_before_tax": float(Decimal(line["amount_before_tax"]))})
	if total != Decimal(cstr(decision.evaluated_amount)):
		raise Unavailable(f"The priced lines come to {total:,.2f} but the decision awarded {Decimal(cstr(decision.evaluated_amount)):,.2f}.")
	return _json({"currency": prices["currency"], "tax_included": True, "total": float(total), "lines": lines, "evaluation": prices["report"]}), "application/json", cstr(prices["report"]["id"])


def _s4(doc):
	data = _seam("kentender_procurement.tenders.services.contract_seam", "schedule_of_requirements", tender=doc.tender)
	return _json(data), "application/json", cstr(data["definition"]["version"])


def _s5(doc):
	data = _seam("kentender_procurement.tenders.services.contract_seam", "conditions", tender=doc.tender)
	warranty = {"months": data["warranty"]["months"], "support": {k: data["warranty"][k] for k in data["warranty"] if k != "months"}}
	content = {"warranty": warranty, "payment": {"days": data["payment"]["days"], "source": data["payment"]["source"]},
		"performance_security": {"required": data["performance_security"]["required"], "percentage": data["performance_security"]["percentage"], "statement": data["performance_security"]["statement"]},
		"delay_damages": data["delay_damages"], "inspection_acceptance_office": data["inspection_acceptance_office"], "template": data["template"]}
	return _json(content), "application/json", cstr(data["template"]["version"])


def _s6(doc):
	data = _seam("kentender_procurement.tenders.services.contract_seam", "acceptance_criteria", tender=doc.tender)
	return _json(data), "application/json", "1"


def _s7(doc):
	data = _seam("kentender_procurement.tenders.services.contract_seam", "form_no_4", tender=doc.tender)
	return data["fragment"].encode("utf-8"), "text/html", cstr(data["release"])


def _s9(doc):
	from kentender_procurement.tenders.services import award_seam

	reservations = award_seam.funding_reservations(doc.tender)
	decision = state.committed_decision(doc)
	if not reservations:
		raise Unavailable("The tender has no recorded budget reservation.")
	if len(reservations) > 1:
		raise Unavailable(f"The award draws on {len(reservations)} reservations ({', '.join(reservations)}) and no funding owner has allocated the awarded price between them.")
	try:
		from kentender_budget.services.budget_downstream_contracts import get_funding_lineage
	except ImportError as exc:
		raise Unavailable("Budget is not installed.") from exc
	rows = get_funding_lineage(reservation=reservations[0]).get("rows") or []
	if not rows:
		raise Unavailable(f"Budget does not hold the reservation {reservations[0]}.")
	row = rows[0]
	return _json({"allocations": [{"reservation": row["reservation"]["id"], "source_allocation": row["reservation"].get("plan_source_allocation"), "budget_line": row["budget_line"],
		"amount": float(Decimal(cstr(decision.evaluated_amount)))}], "lineage": rows}), "application/json", cstr(row.get("budget_version_at_creation"))


def _s10(doc):
	entity = frappe.db.get_value("Site Procuring Entity", None, ["pe_name", "pe_address", "pe_type"], as_dict=True) if frappe.db.exists("DocType", "Site Procuring Entity") else None
	if not entity or not cstr(entity.pe_name).strip():
		raise Unavailable("The procuring entity's site configuration is not held.")
	if not cstr(entity.pe_address).strip():
		raise Unavailable("The principal address is not held in the entity's site configuration.")
	return _json({"legal_name": entity.pe_name, "address": entity.pe_address, "entity_type": cstr(entity.pe_type)}), "application/json", "1"


def _s11(doc):
	from kentender_core.services import supplier_account_contract

	decision = state.committed_decision(doc)
	provider = supplier_account_contract.provider()
	if provider is None:
		raise Unavailable("Supplier Accounts is not installed.")
	organisation = decision.supplier_organisation
	facts = provider.organisation(organisation_id=organisation)
	if not facts:
		raise Unavailable("The supplier's account is not held.")
	profile = provider.business_profile(organisation_id=organisation) or {}
	# who could sign for the supplier when it accepted the award: an instant Award retains, so the source does not change as time passes (the authority at the signing itself is checked then)
	notice = state.successful_notice(state.current_batch(doc))
	accepted = state.operative_response(notice)
	at = get_datetime(accepted.received_at) if accepted else (get_datetime(notice.given_at) if notice and notice.given_at else get_datetime(decision.decided_at))
	signatories = [{"name": frappe.db.get_value("User", s["user"], "full_name") or s["user"], "user": s["user"], "capacity": "Authorised signatory", "authority_evidence": s.get("authority_evidence_id"),
		"effective_from": cstr(s.get("effective_from")), "effective_to": cstr(s.get("effective_to"))} for s in provider.organisation_signatories(organisation_id=organisation, at=at)]
	return _json({"legal_name": facts.get("legal_name"), "form": profile.get("business_structure") or profile.get("company_type"), "organisation": organisation, "country": facts.get("country"),
		"registration_number": facts.get("registration_number"), "registered_address": facts.get("registered_address"), "signatories": signatories}), "application/json", "1"


BUILDERS = {"S1": _s1, "S2": _s2, "S3": _s3, "S4": _s4, "S5": _s5, "S6": _s6, "S7": _s7, "S8": _s8, "S9": _s9, "S10": _s10, "S11": _s11, "S12": _s12}


def build(number: str, doc) -> dict[str, Any]:
	"""One source: its content, media type, version and digest, or the reason it cannot be given."""
	try:
		content, media, version = BUILDERS[number](doc)
	except Unavailable as exc:
		return {"unavailable": cstr(exc)}
	return {"content": content, "media_type": media, "version": version, "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}


def _case(reference: str):
	found = _REFERENCE.match(cstr(reference))
	if not found or found.group(1) not in BUILDERS or not frappe.db.exists("Award Case", found.group(2)):
		return None, None
	return found.group(1), frappe.get_doc("Award Case", found.group(2))


class Provider:
	"""Registered on `kt_contract_source_provider`; answers only the references of Award cases."""

	def references(self, *, award_case: str) -> list[dict[str, Any]]:
		if not frappe.db.exists("Award Case", award_case):
			return []
		doc = frappe.get_doc("Award Case", award_case)
		rows = []
		for number in BUILDERS:
			built = build(number, doc)
			row = {"source": number, "reference": f"{number}-{award_case}", "owner": OWNER[number], "category": CATEGORY[number]}
			if "unavailable" in built:
				row["unavailable"] = built["unavailable"]
			else:
				row.update(version=built["version"], media_type=built["media_type"], size=built["size"])
				if number not in LIVE:
					row["sha256"] = built["sha256"]
			rows.append(row)
		return rows

	def describe(self, *, reference: str) -> dict[str, Any] | None:
		number, doc = _case(reference)
		if not number:
			return None
		built = build(number, doc)
		if "unavailable" in built:
			return {"reference": reference, "owner": OWNER[number], "unavailable": built["unavailable"]}
		return {"reference": reference, "version": built["version"], "sha256": built["sha256"], "media_type": built["media_type"], "size": built["size"], "owner": OWNER[number]}

	def fetch(self, *, reference: str) -> dict[str, Any] | None:
		number, doc = _case(reference)
		if not number:
			return None
		built = build(number, doc)
		return None if "unavailable" in built else {"content": built["content"], "digest": built["sha256"]}


def service() -> Provider:
	return Provider()
