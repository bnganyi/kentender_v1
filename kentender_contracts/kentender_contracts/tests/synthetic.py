# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Synthetic sources for development (CM-CHG-001 v0.8 plan D17, D18, D20; owner decision OD-D: synthetic upstreams are development only).

Two things, both clearly synthetic and never accepted as package acceptance (level L1):

* `award_package()` is shaped like Award's frozen `content_json` -- the keys `reconciliation/package_gap.md` lists, no more -- carrying the ten-laptop demonstration
  (10 units at KES 100,000). A test compares the keys with that document so the stand-in cannot drift from what Award hands over.
* `source_handoff()` is the D20 `ContractSourceHandoff`: one reference per source S1 to S12 with owner, version, SHA-256, media type, size, locator and basis, and a
  provider (`fetch`, `verify`) that returns bytes whose digest recomputes. `REAL_TODAY` records, from `package_gap.md`, which of the twelve the real owners do not yet
  supply, so a green L1 run is never mistaken for formation acceptance.

Pure Python, no Frappe: usable from any test and from the seed builders."""

from __future__ import annotations

import hashlib
from typing import Any

CASE = "CM-DEMO-AWD-01"
TERMS = "CM-DEMO-TERMS-01"
SUPPLIER = "Afya Digital Supplies Limited"
LAPTOPS, UNIT_PRICE = 10, 100_000

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


def award_package() -> dict[str, Any]:
	"""The keys Award freezes in `content_json` (package_gap.md), carrying the synthetic demonstration."""
	total = LAPTOPS * UNIT_PRICE
	return {
		"award_case": CASE, "tender": "TND-DEMO-001", "tender_reference": "MOH/ICT/2027/DEMO-01", "lot": "LOT-1", "cycle": 1,
		"report": {"id": "EVL-DEMO-1", "version": 1, "digest": _sha(b"evaluation report"), "source": "synthetic"},
		"opinion": {"id": "OPN-DEMO-1", "version": 1, "digest": _sha(b"opinion"), "proof": "synthetic"},
		"decision": {"id": "DEC-DEMO-1", "version": 1, "outcome": "Award", "supplier": SUPPLIER, "organisation": "ORG-DEMO-1", "bid": "BID-DEMO-1",
			"submitted_amount": total, "evaluated_amount": total, "currency": "KES"},
		"notice_batch": {"id": "NTB-DEMO-1", "version": 1, "notices": [{"id": "NTC-DEMO-1", "digest": _sha(b"notice"), "given_at": "2027-06-30 10:00:00", "evidence": "synthetic"}]},
		"response": {"id": "RSP-DEMO-1", "response": "Accepted", "by": "mary.wanjiku@afyadigital.example", "received_at": "2027-07-01 09:00:00", "authority": "synthetic"},
		"contract_terms": {"quantity": LAPTOPS, "warranty": "36 months", "delivery_and_warranty": "As issued in the tender and the supplier's response",
			"reservation_treatment": "As recorded in the tender's reservation lineage", "performance_security": "As published in the tender (Contracting verifies before signature)",
			"tender_security": "As recorded at submission"},
		"restrictions": [], "legal_profile": "SYNTHETIC-ILLUSTRATIVE", "fixture_namespace": "CM_DEMO",
	}


def _bytes(number: str) -> bytes:
	return f"synthetic source {number} for {CASE}".encode()


def _sha(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def source_handoff() -> list[dict[str, Any]]:
	"""One reference per required source S1 to S12 (plan D20)."""
	rows = []
	for number, (category, owner, real) in SOURCES.items():
		data = _bytes(number)
		rows.append({"source": number, "category": category, "owner": owner, "reference": f"{number}-{CASE}", "version": 1, "sha256": _sha(data), "media_type": "text/plain",
			"size": len(data), "locator": f"synthetic/{number}", "basis": "required by CM v0.8 section 19.4", "provider": "synthetic", "real_handoff_today": real})
	return rows


class Provider:
	"""The `describe` / `fetch` / `verify` seam of D20, answering from the synthetic handoff. `tamper` makes one source's bytes differ, to prove verification."""

	def __init__(self, *, tamper: str = ""):
		self.tamper = tamper

	def describe(self, reference: str) -> dict[str, Any] | None:
		return next((r for r in source_handoff() if r["reference"] == reference), None)

	def fetch(self, reference: str) -> dict[str, Any] | None:
		row = self.describe(reference)
		if row is None:
			return None
		data = _bytes(row["source"]) + (b" tampered" if row["source"] == self.tamper else b"")
		return {"content": data, "digest": _sha(data)}

	def verify(self, reference: str) -> bool:
		row, got = self.describe(reference), self.fetch(reference)
		return bool(row and got and got["digest"] == row["sha256"])


def missing_from_real_handoff() -> list[str]:
	"""The sources the real owners do not yet supply in a form CM can use (everything but Present)."""
	return [k for k, v in REAL_TODAY.items() if v != "Present"]
