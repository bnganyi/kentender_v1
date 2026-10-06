# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The synthetic upstream sources (AWD-CHG-001 v0.4 §10.1, §13; plan D4, OD-B).

Award's own tests and browser worlds start from a signed Evaluation report in
seconds: this provider serves the §10.1 fixture facts (tender 033, one bid;
tender 036, the unresolved tie; tender 037, two bids) through the same
interface as the real seams, so no tender, bid, opening or evaluation is
built. It answers only on a test environment; a case built on it carries
`source_kind = "Synthetic"`. The real Evaluation → Award seam is proven by
`test_awd_seams`, `test_awd_integration` and the canonical `award` stage.

Live facts a branch needs to change (validity, a cancellation or suspension,
a contact correction, a withdrawn signatory, a corrected report) are kept in
the simulation controls' synthetic state, never in Award's own records."""

from __future__ import annotations

import copy
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import records, simulation, sources

AFYA = "Afya Digital Supplies Limited"
JIRANI = "Jirani Office Supplies Limited"
JIRANI_ORG = "SYN-JIRANI"
TITLE = {"033": "Supply and delivery of business laptops", "036": "Supply and delivery of office laptops", "037": "Supply and delivery of business laptops"}
MEMBERS = [("Grace Wambui", "grace.wambui@moh.example.test"), ("Peter Mugo", "peter.mugo@moh.example.test"), ("Ruth Achieng", "ruth.achieng@moh.example.test")]
SECTIONS = ["Tender and committee", "Bid findings", "Financial comparison", "Clarifications and committee record", "Recommendation and reasons"]


def afya_org() -> str:
	name = frappe.db.get_value("Supplier Organisation", {"legal_name": AFYA}, "name") if frappe.db.exists("DocType", "Supplier Organisation") else None
	return cstr(name) or "SYN-AFYA"


def _state() -> dict[str, Any]:
	doc = frappe.get_single(simulation.CONTROLS)
	return records.loads(doc.get("synthetic_json"), {}) or {}


def _save(state: dict[str, Any]) -> None:
	doc = frappe.get_single(simulation.CONTROLS)
	doc.synthetic_json = records.dumps(state)
	doc.save(ignore_permissions=True)


def _bid(reference: str, n: int, org: str, name: str, amount: str, position, responsiveness: str = "Responsive") -> dict[str, Any]:
	number = reference.replace("TND-", "")
	return {"bid": f"SYN-BID-{number}-{n:02d}", "bid_reference": f"BID-{number}-{n:03d}", "organisation": org, "bidder": name, "submitted_total": amount,
		"evaluated_total": amount, "position": position, "responsiveness": responsiveness, "currency": "KES", "submission_version": f"SUBV-{number}-{n:03d}-01",
		"bidder_arrangement": f"SYN-ARR-{number}-{n:03d}"}


def report(world: str, reference: str, *, version: int = 1, delivered_at=None, outcome: str = "", reason: str = "", overrides: dict | None = None) -> dict[str, Any]:
	"""The §10.1 report for one synthetic world."""
	o = dict(overrides or {})
	afya = afya_org()
	if world == "036":
		bids = [_bid(reference, 1, afya, AFYA, "46400000.00", 1), _bid(reference, 2, JIRANI_ORG, JIRANI, "46400000.00", 1)]
		default_outcome, default_reason, recommended = "No single recommendation — equal evaluated totals", "The published tender has no tie-break rule.", None
	elif world == "037":
		bids = [_bid(reference, 1, afya, AFYA, "46400000.00", 2), _bid(reference, 2, JIRANI_ORG, JIRANI, "45900000.00", 1)]
		default_outcome, default_reason, recommended = "Recommendation", "Jirani Office Supplies Limited is the lowest evaluated responsive tenderer.", bids[1]
	else:
		bids = [_bid(reference, 1, afya, AFYA, "46400000.00", 1)]
		default_outcome, default_reason, recommended = "Recommendation", "The only bid received meets the published requirements.", bids[0]
	outcome = outcome or o.pop("outcome", "") or default_outcome
	if outcome != "Recommendation":
		recommended = None
	if recommended:
		recommended = {**recommended, "quantity": "250 Each", "warranty": "36 months"}
	signed = o.pop("signed", 3)
	at = get_datetime(delivered_at or "2027-06-16 14:07:01")
	sigs = [{"user": u, "name": n, "signed_at": str(at) if i < signed else None} for i, (n, u) in enumerate(MEMBERS)]
	annexes = [{"name": s, "available": True} for s in SECTIONS]
	if o.pop("missing_annex", False):
		annexes[-1] = {**annexes[-1], "available": False}
	number = reference.replace("TND-", "")
	content = {"reference": reference, "version": version, "outcome": outcome, "bids": bids}
	snap = {
		"source_kind": sources.SYNTHETIC, "delivery": f"SYN-DLV:{reference}:{version}", "source_case": f"SYN-EVL-{number}", "report": f"SYN-EVL-{number}-RPT-{version:02d}",
		"version": version, "content_digest": records.digest(content), "digest_verified": not o.pop("digest_mismatch", False), "delivered_at": str(at),
		"recipient": "", "fixture_namespace": records.namespace(), "tender": f"SYN-{reference}", "tender_reference": reference,
		"tender_title": TITLE.get(world, TITLE["033"]), "lot": "1", "procuring_entity": "Ministry of Health", "award_method": "Lowest evaluated responsive tender",
		"signatures": {"required": 3, "signed": signed, "members": sigs}, "sections": SECTIONS, "annexes": annexes, "outcome": outcome,
		"reason": reason or o.pop("reason", "") or default_reason, "qualifications": o.pop("qualifications", []), "funding": o.pop("funding", {"available": "50000000.00",
		"shortfall": "0.00", "qualification": "", "source": "Budget confirmation"}), "recommended": recommended, "comparison": bids,
		"committee": [n for n, _u in MEMBERS], "dissent": o.pop("dissent", []), "narrative": "", "world": world,
		"validity": {"validity_end": o.pop("validity_end", "2027-10-10 11:00:00"), "rule": {"counting": "Submission deadline date plus the published validity days",
			"source": "Published bid definition (synthetic)", "timezone": "Site time (EAT)"}},
	}
	snap.update(o)
	return snap


def deliver(world: str = "033", *, reference: str = "", version: int = 1, delivered_at=None, outcome: str = "", reason: str = "", overrides: dict | None = None,
		receive: bool = True) -> dict[str, Any]:
	"""A synthetic Evaluation delivery, received by Award as a real one is."""
	if not simulation.enabled():
		raise frappe.PermissionError("Synthetic Award sources are available on a test environment only.")
	reference = reference or f"TND-MOH-2027-{world}"
	snap = report(world, reference, version=version, delivered_at=delivered_at, outcome=outcome, reason=reason, overrides=overrides)
	state = _state()
	state.setdefault("deliveries", {})[snap["delivery"]] = snap
	tender = state.setdefault("tenders", {}).setdefault(snap["tender"], {})
	tender.setdefault("validity_end", snap["validity"]["validity_end"])
	tender.setdefault("world", world)
	for b in snap["comparison"]:
		state.setdefault("contacts", {}).setdefault(b["bidder_arrangement"], {"email": "tenders@afyadigital.example" if b["bidder"] == AFYA else
			"tenders@jirani.example", "version": 1})
	_save(state)
	if not receive:
		return snap
	from kentender_procurement.award.services import intake

	return intake.receive(delivery=snap["delivery"], source_kind=sources.SYNTHETIC)


def set_fact(tender: str, **values) -> None:
	"""Change a live synthetic fact (validity_end, cancelled, suspended, status_down…)."""
	state = _state()
	state.setdefault("tenders", {}).setdefault(tender, {}).update(values)
	_save(state)


def add_event(tender: str, event: dict[str, Any]) -> None:
	state = _state()
	state.setdefault("tenders", {}).setdefault(tender, {}).setdefault("events", []).append(event)
	_save(state)


def correct_contact(bidder_arrangement: str, email: str) -> dict[str, Any]:
	"""The contact owner's correction (the supplier's own contact form)."""
	state = _state()
	row = state.setdefault("contacts", {}).setdefault(bidder_arrangement, {"email": "", "version": 0})
	row.update(email=email, version=int(row.get("version") or 0) + 1)
	_save(state)
	return row


def revoke_signatory(user: str, organisation: str) -> None:
	state = _state()
	state.setdefault("revoked", []).append(f"{user}|{organisation}")
	_save(state)


def add_correction(tender: str, correction: dict[str, Any]) -> None:
	state = _state()
	state.setdefault("corrections", {}).setdefault(tender, []).append({"taken": False, **correction})
	_save(state)


def clear() -> None:
	if simulation.enabled():
		_save({})


class SyntheticSource:
	kind = sources.SYNTHETIC

	def _tender(self, tender: str) -> dict[str, Any]:
		return _state().get("tenders", {}).get(tender) or {}

	def _check(self, tender: str = "") -> None:
		if simulation.flag("status_service_down") or (tender and self._tender(tender).get("status_down")):
			raise sources.SourceUnavailable("The synthetic status service is down.")

	def delivered_report(self, delivery: str) -> dict[str, Any] | None:
		snap = _state().get("deliveries", {}).get(delivery)
		if not snap:
			return None
		snap = copy.deepcopy(snap)
		try:
			snap["validity"] = self.validity(snap["tender"])
		except sources.SourceUnavailable:
			snap["validity"] = {"validity_end": None, "rule": None, "unavailable": True}
		return snap

	def pending_deliveries(self) -> list[str]:
		return [k for k, v in _state().get("deliveries", {}).items() if not v.get("taken") and not v.get("returned")]

	def take_up(self, delivery: str) -> None:
		state = _state()
		if delivery in state.get("deliveries", {}):
			state["deliveries"][delivery]["taken"] = True
			_save(state)

	def return_report(self, *, delivery: str, comment: str, idempotency_key: str, user: str) -> dict[str, Any]:
		state = _state()
		snap = state.get("deliveries", {}).get(delivery)
		if not snap:
			return {"ok": False, "message": "Not found"}
		if snap.get("recipient") and user != snap["recipient"]:  # Evaluation answers only its recorded recipient
			raise frappe.DoesNotExistError("Not found")
		snap.update(returned=True, return_comment=comment)
		_save(state)
		return {"ok": True, "report": snap["report"], "returned": True}

	def return_for_correction(self, *, delivery: str, comment: str, instruction: str, authorised_by: str, idempotency_key: str) -> dict[str, Any]:
		return self.return_report(delivery=delivery, comment=comment, idempotency_key=idempotency_key, user=authorised_by)

	def corrections_after(self, tender: str) -> list[dict[str, Any]]:
		return [c for c in _state().get("corrections", {}).get(tender, []) if not c.get("taken")]

	def take_up_correction(self, reference: str) -> None:
		state = _state()
		for rows in state.get("corrections", {}).values():
			for c in rows:
				if c.get("reference") == reference:
					c["taken"] = True
		_save(state)

	def tender_facts(self, tender: str) -> dict[str, Any] | None:
		self._check(tender)
		t = self._tender(tender)
		reference = tender.replace("SYN-", "", 1)
		world = t.get("world") or "033"
		return {"tender": tender, "tender_reference": reference, "title": TITLE.get(world, TITLE["033"]), "lot": "1", "procuring_entity": "Ministry of Health",
			"status": "Cancelled" if t.get("cancelled") else "Submission period ended", "cancelled": bool(t.get("cancelled")), "award_method": "Lowest evaluated responsive tender",
			"currency": "KES"}

	def validity(self, tender: str) -> dict[str, Any]:
		self._check(tender)
		t = self._tender(tender)
		return {"validity_end": get_datetime(t.get("validity_end") or "2027-10-10 11:00:00"), "rule": {"counting": "Submission deadline date plus the published validity days",
			"source": "Published bid definition (synthetic)", "timezone": "Site time (EAT)", "extension_count": int(t.get("extensions") or 0)}}

	def status_events(self, tender: str) -> list[dict[str, Any]]:
		self._check(tender)
		return list(self._tender(tender).get("events") or [])

	def funding(self, tender: str) -> dict[str, Any]:
		"""Budget's current funding position: `funding_down` makes it unreadable,
		`funding_available` changes the amount (default: enough for every world)."""
		t = self._tender(tender)
		if t.get("funding_down"):
			return {"known": False, "reason": "The synthetic Budget service is down."}
		return {"known": True, "available": cstr(t.get("funding_available") or "50000000.00"), "reservations": ["SYN-RSV"], "source": "Budget (synthetic)"}

	def audience(self, tender: str) -> list[dict[str, Any]]:
		state = _state()
		snap = next((v for v in state.get("deliveries", {}).values() if v["tender"] == tender), None)
		if not snap:
			return []
		out = []
		for b in snap["comparison"]:
			contact = state.get("contacts", {}).get(b["bidder_arrangement"]) or {}
			out.append({"bidder_arrangement": b["bidder_arrangement"], "organisation": b["organisation"], "organisation_name": b["bidder"], "bid_reference": b["bid_reference"],
				"submission_version": b["submission_version"], "status": "Submitted", "replaced": [], "contact_email": contact.get("email", ""),
				"contact_version": int(contact.get("version") or 0)})
		for extra in self._tender(tender).get("extra_audience") or []:
			out.append(extra)
		return out

	def notice_contact(self, bidder_arrangement: str) -> dict[str, Any]:
		row = _state().get("contacts", {}).get(bidder_arrangement) or {}
		return {"email": row.get("email", ""), "version": int(row.get("version") or 0)}

	def _real(self, organisation: str) -> bool:
		return bool(organisation) and not organisation.startswith("SYN-")

	def signatory(self, user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
		if f"{user}|{organisation}" in (_state().get("revoked") or []) or not self._real(organisation):
			return None
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.signatory(user, organisation, at=at)

	def acting_for(self, user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
		if f"{user}|{organisation}" in (_state().get("revoked") or []) or not self._real(organisation):
			return None
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.acting_for(user, organisation, at=at)

	def organisations_of(self, user: str, *, at=None) -> list[str]:
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.organisations_of(user, at=at)

	def organisation_users(self, organisation: str, *, at=None) -> list[dict[str, Any]]:
		if not self._real(organisation):
			return []
		from kentender_procurement.bid_submission.services import award_gateway

		return award_gateway.organisation_users(organisation, at=at)

	def status_available(self) -> bool:
		return not simulation.flag("status_service_down")


def synthetic_provider() -> SyntheticSource | None:
	return SyntheticSource() if simulation.enabled() else None
