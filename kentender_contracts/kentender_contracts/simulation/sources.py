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

#: The goods-plus-service package (board D31): the same ten laptops plus one training session at KES 50,000, named by a `-SVC` case.
SERVICE_RATE = 50_000
SERVICE = {"line_id": "L2", "requirement": "Train ten named users to start and operate the supplied laptops", "deadline": "2027-07-27", "evidence_required": "Attendance and completed practical checklist"}
SERVICE_CRITERIA = [
	{"id": "C4", "name": "Attendance", "label": "Observed attendance", "comparator": ">=", "value": 10, "unit": "users", "line_id": "L2", "coverage": "every unit"},
	{"id": "C5", "name": "Practical checklist", "label": "Practical checklist", "comparator": ">=", "value": 10, "unit": "users", "line_id": "L2", "coverage": "every unit"},
]

CRITERIA = [
	{"id": "C1", "name": "RAM", "comparator": ">=", "value": 16, "unit": "GB", "line_id": "L1", "coverage": "every unit"},
	{"id": "C2", "name": "Storage", "comparator": ">=", "value": 512, "unit": "GB", "line_id": "L1", "coverage": "every unit"},
	{"id": "C3", "name": "Starts successfully", "comparator": "=", "value": "Yes", "unit": "", "line_id": "L1", "coverage": "every unit"},
]


def _json(value: Any) -> bytes:
	return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def organisation_id() -> str:
	"""The supplier's organisation in Supplier Accounts where the site has one (the canonical Afya account), else the stand-in id. The synthetic S11 names it so the supplier's people are the real ones."""
	import frappe

	try:
		return frappe.db.get_value("Supplier Organisation", {"legal_name": SUPPLIER}, "name") or "ORG-DEMO-1"
	except Exception:  # a site without Supplier Accounts (the independence site) has no such table
		return "ORG-DEMO-1"


def variant(case: str, security_required: bool = False, outside_signing: bool = False) -> tuple[bool, bool]:
	"""A demonstration award's variant is named by its case: `-SEC` requires a performance security and `-OUT` permits signing outside the system (so a browser world can hold several, answered by the one
	registered provider)."""
	return security_required or case.endswith("-SEC"), outside_signing or case.endswith("-OUT")


#: The advance branch (board D29): the issued terms provide 10% of the contract sum, paid after signature, recovered at KES 10,000 for each laptop accepted and invoiced.
ADVANCE = {"allowed": True, "percent": 10, "recovery_per_unit": 10_000, "recovery_line": "L1", "after_signature": True,
	"statement": "10% of the contract sum, paid after the agreement is effective and recovered at KES 10,000 for each laptop accepted and invoiced"}


def with_advance(case: str, advance: bool = False) -> bool:
	"""The advance variant is named by its case (`-ADV`), like the others."""
	return advance or case.endswith("-ADV")


def with_services(case: str, services: bool = False) -> bool:
	"""The goods-plus-service variant is named by its case (`-SVC`), like the security and outside-signing variants."""
	return services or case.endswith("-SVC")


def _content(number: str, case: str, security_required: bool = False, outside_signing: bool = False, services: bool = False, advance: bool = False) -> bytes:
	security_required, outside_signing = variant(case, security_required, outside_signing)
	services = with_services(case, services)
	total = TOTAL + (SERVICE_RATE if services else 0)
	if number == "S1":
		return _json({"tender": "TND-DEMO-001", "tender_reference": "MOH/ICT/2027/DEMO-01", "title": "IT equipment delivery", "release": "IT-EQUIPMENT-OPEN-V1", "release_id": "1.5", "addenda": []})
	if number == "S2":
		return _json({"bid": "BID-DEMO-1", "supplier": SUPPLIER, "lines": [{"line_id": "L1", "item": "Laptop", "quantity": LAPTOPS, "rate": UNIT_PRICE}]
			+ ([{"line_id": "L2", "item": "Training", "quantity": 1, "rate": SERVICE_RATE}] if services else []), "clarifications": []})
	if number == "S3":
		return _json({"currency": "KES", "tax_included": True, "total": total,
			"lines": [{"line_id": "L1", "item": "Laptop", "description": "Laptop computer", "uom": "Nos", "quantity": LAPTOPS, "rate": UNIT_PRICE, "amount": TOTAL}]
			+ ([{"line_id": "L2", "item": "Training", "description": "Training session", "uom": "Session", "kind": "service", "quantity": 1, "rate": SERVICE_RATE, "amount": SERVICE_RATE}] if services else [])})
	if number == "S4":
		return _json({"delivery_schedule": {"due": DELIVERY_DUE, "destination": "Ministry of Health, Afya House store"}, "technical": [{"line_id": "L1", "requirement": "Laptop with at least 16 GB RAM and 512 GB storage that starts successfully"}],
			"related_services": [SERVICE] if services else []})
	if number == "S5":
		security = {"required": True, "percentage": 10, "statement": "10% of the contract sum, in the form of a bank guarantee"} if security_required else {"required": False, "statement": "Not required by the issued terms"}
		return _json({"warranty": {"months": 12, "from": "each unit's acceptance"}, "payment": {"basis": "certified invoice for accepted units", "terms": "as issued"},
			"performance_security": security, "advance": ADVANCE if with_advance(case, advance) else {"allowed": False}, "delivery_due": DELIVERY_DUE,
			"signing": {"outside_permitted": True, "basis": "Outside signing permitted by the issued terms"} if outside_signing else {"outside_permitted": False}})
	if number == "S6":
		return _json({"criteria": CRITERIA + (SERVICE_CRITERIA if services else [])})
	if number == "S7":
		return FORM_4.encode()
	if number == "S8":
		return _json({"notification": {"id": "NTC-DEMO-1", "given_at": "2027-06-17 10:00:00"}, "signing_window": {"result": "Within window", "earliest_signing_at": "2027-07-02 09:00:00", "ends_on": "2027-07-14", "counting_basis": "synthetic"}})
	if number == "S9":
		return _json({"allocations": [{"reservation": "RSV-DEMO-1", "source_allocation": "PSA-DEMO-1", "budget_line": "BL-DEMO-1", "amount": total}]})
	if number == "S10":
		return _json({"legal_name": ENTITY, "address": "Afya House, Nairobi", "entity_type": "Ministry"})
	if number == "S11":
		return _json({"legal_name": SUPPLIER, "form": "Company", "organisation": organisation_id(), "signatories": [{"name": "Mary Wanjiku", "user": SUPPLIER_SIGNATORY, "capacity": "Authorised signatory"}]})
	if number == "S12":
		return _json({"restrictions": [], "event": "AwardDecisionRecorded v1"})
	raise KeyError(number)


def _sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def award_package(services: bool = False) -> dict[str, Any]:
	"""The keys Award freezes in `content_json` (package_gap.md), carrying the synthetic demonstration. `services` adds the training session to the award."""
	case = f"{CASE}-SVC" if services else CASE
	total = TOTAL + (SERVICE_RATE if services else 0)
	return {
		"award_case": case, "tender": "TND-DEMO-001", "tender_reference": "MOH/ICT/2027/DEMO-01", "lot": "LOT-1", "cycle": 1,
		"report": {"id": "EVL-DEMO-1", "version": 1, "digest": _sha(b"evaluation report"), "source": "synthetic"},
		"opinion": {"id": "OPN-DEMO-1", "version": 1, "digest": _sha(b"opinion"), "proof": "synthetic"},
		"decision": {"id": "DEC-DEMO-1", "version": 1, "outcome": "Award", "supplier": SUPPLIER, "organisation": organisation_id(), "bid": "BID-DEMO-1",
			"submitted_amount": total, "evaluated_amount": total, "currency": "KES"},
		"notice_batch": {"id": "NTB-DEMO-1", "version": 1, "notices": [{"id": "NTC-DEMO-1", "digest": _sha(b"notice"), "given_at": "2027-06-17 10:00:00", "evidence": "synthetic"}]},
		"response": {"id": "RSP-DEMO-1", "response": "Accepted", "by": SUPPLIER_SIGNATORY, "received_at": "2027-07-01 09:00:00", "authority": "synthetic"},
		"contract_terms": {"quantity": LAPTOPS, "warranty": "12 months", "delivery_and_warranty": "As issued in the tender and the supplier's response",
			"reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)",
			"tender_security": "As recorded at submission"},
		"restrictions": [], "legal_profile": "SYNTHETIC-ILLUSTRATIVE", "fixture_namespace": "CM_DEMO",
	}


def reference(number: str, case: str = CASE) -> str:
	return f"{number}-{case}"


def source_handoff(case: str = CASE, *, security_required: bool = False, outside_signing: bool = False, services: bool = False, advance: bool = False) -> list[dict[str, Any]]:
	"""One reference per required source S1 to S12 (plan D20). `security_required` is the variant whose issued terms require a performance security; `services` the goods-plus-service package."""
	rows = []
	for number, (category, owner, real) in SOURCES.items():
		data = _content(number, case, security_required, outside_signing, services, advance)
		rows.append({"source": number, "category": category, "owner": owner, "reference": reference(number, case), "version": 1, "sha256": _sha(data),
			"media_type": "text/html" if number == "S7" else "application/json", "size": len(data), "locator": f"synthetic/{number}", "basis": "required by CM v0.8 section 19.4",
			"provider": "synthetic", "real_handoff_today": real})
	return rows


_REFERENCE = re.compile(r"^(S\d+)-(.+)$")


class Provider:
	"""The `describe` / `fetch` seam of D20, answering from the synthetic handoff. `tamper` makes one source's bytes differ, to prove verification."""

	def __init__(self, *, tamper: str = "", security_required: bool = False, outside_signing: bool = False, services: bool = False, advance: bool = False):
		self.tamper = tamper
		self.security_required = security_required
		self.outside_signing = outside_signing
		self.services = services
		self.advance = advance

	def _parse(self, reference: str):
		m = _REFERENCE.match(reference or "")
		return (m.group(1), m.group(2)) if m and m.group(1) in SOURCES else (None, None)

	def describe(self, *, reference: str) -> dict[str, Any] | None:
		number, case = self._parse(reference)
		return next((r for r in source_handoff(case, security_required=self.security_required, outside_signing=self.outside_signing, services=self.services, advance=self.advance) if r["source"] == number), None) if number else None

	def fetch(self, *, reference: str) -> dict[str, Any] | None:
		number, case = self._parse(reference)
		if not number:
			return None
		data = _content(number, case, self.security_required, self.outside_signing, self.services, self.advance) + (b" tampered" if number == self.tamper else b"")
		return {"content": data, "digest": _sha(data)}


def missing_from_real_handoff() -> list[str]:
	"""The sources the real owners do not yet supply in a form CM can use (everything but Present)."""
	return [k for k, v in REAL_TODAY.items() if v != "Present"]


def service():
	"""The provider registered on `kt_contract_source_provider`: it answers only on a simulation site."""
	from kentender_contracts.services import simulation

	return Provider() if simulation.enabled() else None
