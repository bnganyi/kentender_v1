# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Synthetic sources for development (CM-CHG-001 v0.8 plan D17, D18, D20; owner decision OD-D: synthetic upstreams are development only).

Two things, both clearly synthetic and never accepted as package acceptance (proof level L1):

* `award_package()` is shaped like Award's frozen `content_json` (the keys `reconciliation/package_gap.md` lists, no more), carrying the ten-laptop demonstration of the
  boards: ten laptops at KES 100,000, KES 1,000,000 tax included, delivery due 20 July 2027, warranty 12 months from each unit's acceptance, no performance security.
* `Provider` answers the D20 `describe`/`fetch` seam (`kentender_core.services.contract_source_contract`) for the twelve required sources S1 to S12 with real content, so
  preparation can generate an agreement and freeze a package from them. `REAL_TODAY` records, from `package_gap.md`, which of the twelve the real owners do not yet supply, so a green
  L1 run is never mistaken for formation acceptance.

The provider is registered on `kt_contract_source_provider` and answers only on a simulation site (`services/simulation.py`). Pure Python except the registration."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

CASE = "CM-DEMO-AWD-01"
TERMS = "CM-DEMO-TERMS-01"
SUPPLIER = "Afya Digital Supplies Limited"
LAPTOPS, UNIT_PRICE = 10, 100_000
TOTAL = LAPTOPS * UNIT_PRICE
DELIVERY_DUE = "2027-07-20"
ENTITY = "Ministry of Health"
SUPPLIER_SIGNATORY = "mary.wanjiku@afyadigital.example"
ENTITY_SIGNATORY = "amina.hassan@moh.example.test"

#: S-number -> (category, owning module, status of the real handoff today, verbatim from package_gap.md)
SOURCES: dict[str, tuple[str, str, str]] = {
	"S1": ("issued_tender_release_addenda", "Tenders and the template release", "Absent"),
	"S2": ("accepted_tender_and_clarifications", "Bid Submission, Evaluation, Award", "Partial"),
	"S3": ("price_schedule", "Tenders, Award", "Partial"),
	"S4": ("requirements_and_technical_schedules", "Tenders and the template release", "Partial"),
	"S5": ("gcc_scc_and_commercial_terms", "Template release, Tenders", "Absent"),
	"S6": ("inspection_and_acceptance_criteria", "Tenders and the template release", "Absent"),
	"S7": ("form_no_4_source", "Template release", "Partial"),
	"S8": ("award_notification_and_signing_window", "Award", "Partial"),
	"S9": ("funding_lineage", "Award, Budget", "Absent"),
	"S10": ("entity_identity", "Site configuration", "Absent"),
	"S11": ("supplier_identity_and_signatories", "Supplier accounts, Award", "Present"),
	"S12": ("restrictions_and_award_event", "Award", "Present"),
}
REAL_TODAY = {k: v[2] for k, v in SOURCES.items()}

FORM_4 = (
	"<h1>CONTRACT AGREEMENT (Form No. 4)</h1>"
	"<p>THIS AGREEMENT is made on <span data-insertion=\"agreement_date\">{{agreement_date}}</span> between <span data-insertion=\"entity_name\">{{entity_name}}</span> of "
	"<span data-insertion=\"entity_address\">{{entity_address}}</span> (the Procuring Entity) and <span data-insertion=\"supplier_name\">{{supplier_name}}</span> (the Supplier).</p>"
	"<p>The Procuring Entity engages the Supplier to supply <span data-insertion=\"goods\">{{goods}}</span> for <span data-insertion=\"amount\">{{amount}}</span>.</p>"
	"<p>[Synthetic stand-in: the covenant and precedence text of the issued Form No. 4 is copied verbatim here by the real template-release provider.]</p>"
	"<p>Incorporated documents: <span data-insertion=\"documents\">{{documents}}</span>.</p>"
	"<p>Signed for the Procuring Entity by <span data-insertion=\"entity_signatory\">{{entity_signatory}}</span> and for the Supplier by <span data-insertion=\"supplier_signatory\">{{supplier_signatory}}</span>.</p>"
)

CRITERIA = [
	{"id": "C1", "name": "RAM", "comparator": ">=", "value": 16, "unit": "GB", "line_id": "L1", "coverage": "every unit"},
	{"id": "C2", "name": "Storage", "comparator": ">=", "value": 512, "unit": "GB", "line_id": "L1", "coverage": "every unit"},
	{"id": "C3", "name": "Starts successfully", "comparator": "=", "value": "Yes", "unit": "", "line_id": "L1", "coverage": "every unit"},
]


def _json(value: Any) -> bytes:
	return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _content(number: str, case: str) -> bytes:
	if number == "S1":
		return _json({"tender": "TND-DEMO-001", "tender_reference": "MOH/ICT/2027/DEMO-01", "title": "IT equipment delivery", "release": "IT-EQUIPMENT-OPEN-V1", "release_id": "1.5", "addenda": []})
	if number == "S2":
		return _json({"bid": "BID-DEMO-1", "supplier": SUPPLIER, "lines": [{"line_id": "L1", "item": "Laptop", "quantity": LAPTOPS, "rate": UNIT_PRICE}], "clarifications": []})
	if number == "S3":
		return _json({"currency": "KES", "tax_included": True, "total": TOTAL,
			"lines": [{"line_id": "L1", "item": "Laptop", "description": "Laptop computer", "uom": "Nos", "quantity": LAPTOPS, "rate": UNIT_PRICE, "amount": TOTAL}]})
	if number == "S4":
		return _json({"delivery_schedule": {"due": DELIVERY_DUE, "destination": "Ministry of Health, Afya House store"}, "technical": [{"line_id": "L1", "requirement": "Laptop with at least 16 GB RAM and 512 GB storage that starts successfully"}],
			"related_services": []})
	if number == "S5":
		return _json({"warranty": {"months": 12, "from": "each unit's acceptance"}, "payment": {"basis": "certified invoice for accepted units", "terms": "as issued"},
			"performance_security": {"required": False, "statement": "Not required under these test terms"}, "advance": {"allowed": False}, "delivery_due": DELIVERY_DUE})
	if number == "S6":
		return _json({"criteria": CRITERIA})
	if number == "S7":
		return FORM_4.encode()
	if number == "S8":
		return _json({"notification": {"id": "NTC-DEMO-1", "given_at": "2027-06-30 10:00:00"}, "signing_window": {"result": "Within window", "ends_on": "2027-07-14", "counting_basis": "synthetic"}})
	if number == "S9":
		return _json({"allocations": [{"reservation": "RSV-DEMO-1", "source_allocation": "PSA-DEMO-1", "budget_line": "BL-DEMO-1", "amount": TOTAL}]})
	if number == "S10":
		return _json({"legal_name": ENTITY, "address": "Afya House, Nairobi", "entity_type": "Ministry"})
	if number == "S11":
		return _json({"legal_name": SUPPLIER, "form": "Company", "organisation": "ORG-DEMO-1", "signatories": [{"name": "Mary Wanjiku", "user": SUPPLIER_SIGNATORY, "capacity": "Authorised signatory"}]})
	if number == "S12":
		return _json({"restrictions": [], "event": "AwardDecisionRecorded v1"})
	raise KeyError(number)


def _sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def award_package() -> dict[str, Any]:
	"""The keys Award freezes in `content_json` (package_gap.md), carrying the synthetic demonstration."""
	return {
		"award_case": CASE, "tender": "TND-DEMO-001", "tender_reference": "MOH/ICT/2027/DEMO-01", "lot": "LOT-1", "cycle": 1,
		"report": {"id": "EVL-DEMO-1", "version": 1, "digest": _sha(b"evaluation report"), "source": "synthetic"},
		"opinion": {"id": "OPN-DEMO-1", "version": 1, "digest": _sha(b"opinion"), "proof": "synthetic"},
		"decision": {"id": "DEC-DEMO-1", "version": 1, "outcome": "Award", "supplier": SUPPLIER, "organisation": "ORG-DEMO-1", "bid": "BID-DEMO-1",
			"submitted_amount": TOTAL, "evaluated_amount": TOTAL, "currency": "KES"},
		"notice_batch": {"id": "NTB-DEMO-1", "version": 1, "notices": [{"id": "NTC-DEMO-1", "digest": _sha(b"notice"), "given_at": "2027-06-30 10:00:00", "evidence": "synthetic"}]},
		"response": {"id": "RSP-DEMO-1", "response": "Accepted", "by": SUPPLIER_SIGNATORY, "received_at": "2027-07-01 09:00:00", "authority": "synthetic"},
		"contract_terms": {"quantity": LAPTOPS, "warranty": "12 months", "delivery_and_warranty": "As issued in the tender and the supplier's response",
			"reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)",
			"tender_security": "As recorded at submission"},
		"restrictions": [], "legal_profile": "SYNTHETIC-ILLUSTRATIVE", "fixture_namespace": "CM_DEMO",
	}


def reference(number: str, case: str = CASE) -> str:
	return f"{number}-{case}"


def source_handoff(case: str = CASE) -> list[dict[str, Any]]:
	"""One reference per required source S1 to S12 (plan D20)."""
	rows = []
	for number, (category, owner, real) in SOURCES.items():
		data = _content(number, case)
		rows.append({"source": number, "category": category, "owner": owner, "reference": reference(number, case), "version": 1, "sha256": _sha(data),
			"media_type": "text/html" if number == "S7" else "application/json", "size": len(data), "locator": f"synthetic/{number}", "basis": "required by CM v0.8 section 19.4",
			"provider": "synthetic", "real_handoff_today": real})
	return rows


_REFERENCE = re.compile(r"^(S\d+)-(.+)$")


class Provider:
	"""The `describe` / `fetch` seam of D20, answering from the synthetic handoff. `tamper` makes one source's bytes differ, to prove verification."""

	def __init__(self, *, tamper: str = ""):
		self.tamper = tamper

	def _parse(self, reference: str):
		m = _REFERENCE.match(reference or "")
		return (m.group(1), m.group(2)) if m and m.group(1) in SOURCES else (None, None)

	def describe(self, *, reference: str) -> dict[str, Any] | None:
		number, case = self._parse(reference)
		return next((r for r in source_handoff(case) if r["source"] == number), None) if number else None

	def fetch(self, *, reference: str) -> dict[str, Any] | None:
		number, case = self._parse(reference)
		if not number:
			return None
		data = _content(number, case) + (b" tampered" if number == self.tamper else b"")
		return {"content": data, "digest": _sha(data)}


def missing_from_real_handoff() -> list[str]:
	"""The sources the real owners do not yet supply in a form CM can use (everything but Present)."""
	return [k for k, v in REAL_TODAY.items() if v != "Present"]


def service():
	"""The provider registered on `kt_contract_source_provider`: it answers only on a simulation site."""
	from kentender_contracts.services import simulation

	return Provider() if simulation.enabled() else None
