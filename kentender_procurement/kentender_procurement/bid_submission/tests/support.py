# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Test support for Bid Submission (BDS-CHG-001 v0.8 plan Phase 5).

`FakeAccounts` stands in for the Supplier Accounts provider through the
published contract (`kentender_core.services.supplier_account_contract`
lets a test set `frappe.flags.kt_supplier_account_provider`), so these tests
never reach into kentender_suppliers. Its fixture is BDS-CHG-001 §10.1:
Afya Digital Supplies Limited with David Ouma (Supplier Representative) and
Mary Wanjiku (Authorised Signatory); Kisiwa Digital Limited with Peter
Mwangi and Grace Njeri; Jua Technology Limited as the joint-venture member.

`BidCase` starts every test from a Tender published and open through the
Tenders commands (`OpenPeriodCase`), and removes its own Bid Submission rows,
since this bench has no test rollback."""

from __future__ import annotations

import uuid
from typing import Any

import frappe

from kentender_procurement.bid_submission.seeds import clear
from kentender_procurement.bid_submission.services import candidate_registry
from kentender_procurement.tenders.tests import fixtures as tender_fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase

NS = "BDS_TEST"
DAVID = "bdst.david@example.test"
MARY = "bdst.mary@example.test"
PETER = "bdst.peter@example.test"
GRACE = "bdst.grace@example.test"
NOBODY = "bdst.nobody@example.test"
PEOPLE = {DAVID: "David Ouma", MARY: "Mary Wanjiku", PETER: "Peter Mwangi", GRACE: "Grace Njeri", NOBODY: "No Account Person"}
AFYA, KISIWA, JUA = "ORG-BDST-AFYA", "ORG-BDST-KISIWA", "ORG-BDST-JUA"
START_AT = "2027-05-19 09:20:00"


def key() -> str:
	return f"bdst-{uuid.uuid4().hex}"


class FakeAccounts:
	"""The seven `kt_supplier_account_provider` functions over plain dicts."""

	def __init__(self) -> None:
		self.orgs: dict[str, dict[str, Any]] = {}
		self.assignments: dict[str, dict[str, Any]] = {}
		self.contacts: dict[str, list[dict[str, Any]]] = {}
		self.evidence: dict[str, list[dict[str, Any]]] = {}

	def add_org(self, org: str, legal_name: str, registration_number: str, *, status: str = "Active", email: str = "", country: str = "Kenya") -> None:
		self.orgs[org] = {
			"organisation_id": org, "legal_name": legal_name, "country": country, "registration_number": registration_number, "tax_identifier": f"P0{registration_number[-6:]}X",
			"registered_address": f"{legal_name}, Nairobi", "official_email": email, "official_phone": "+254 700 000 111", "account_status": status, "record_version": 1,
		}
		self.contacts[org] = [{"contact_id": f"{org}-C1", "channel": "Email", "value": email, "contact_version": 1, "is_official": True}] if email else []
		self.evidence[org] = []

	def assign(self, user: str, org: str, responsibility: str, *, job_title: str = "", ready: bool = True) -> str:
		assignment_id = f"ASG-{org}-{user.split('@')[0]}"
		self.assignments[assignment_id] = {
			"assignment_id": assignment_id, "organisation_id": org, "user": user, "responsibility": responsibility, "job_title": job_title, "effective_from": "2027-05-18",
			"effective_to": "", "authority_evidence_id": "", "active": True, "signatory_ready": ready and responsibility == "Authorised Signatory",
		}
		return assignment_id

	def add_evidence(self, org: str, evidence_id: str, evidence_type: str, file_name: str, *, status: str = "Available") -> None:
		self.evidence[org].append({"evidence_id": evidence_id, "evidence_type": evidence_type, "title": file_name, "reference": "", "valid_until": "", "status": status, "file_name": file_name, "file_digest": "d" * 64})

	# -- the contract -------------------------------------------------------
	def active_assignments(self, *, user: str, at=None) -> list[dict[str, Any]]:
		return [dict(a) for a in self.assignments.values() if a["user"] == user and a["active"]]

	def assignment(self, *, assignment_id: str, at=None) -> dict[str, Any] | None:
		row = self.assignments.get(assignment_id)
		return dict(row) if row else None

	def organisation(self, *, organisation_id: str) -> dict[str, Any] | None:
		row = self.orgs.get(organisation_id)
		return dict(row) if row else None

	def verified_contacts(self, *, organisation_id: str) -> list[dict[str, Any]]:
		return [dict(c) for c in self.contacts.get(organisation_id, [])]

	def account_evidence(self, *, organisation_id: str) -> list[dict[str, Any]]:
		return [dict(e) for e in self.evidence.get(organisation_id, [])]

	def evidence_file(self, *, organisation_id: str, evidence_id: str) -> dict[str, Any] | None:
		return None

	def find_active_account(self, *, country: str, registration_number: str) -> dict[str, Any] | None:
		for org in self.orgs.values():
			if org["country"] == country and org["registration_number"] == registration_number and org["account_status"] == "Active":
				return {"organisation_id": org["organisation_id"], "legal_name": org["legal_name"]}
		return None


def fixture_accounts() -> FakeAccounts:
	accounts = FakeAccounts()
	accounts.add_org(AFYA, "Afya Digital Supplies Limited", "PVT-9X7K2M", email="tenders@afyadigital.example")
	accounts.add_org(KISIWA, "Kisiwa Digital Limited", "PVT-KSW001", email="tenders@kisiwadigital.example")
	accounts.add_org(JUA, "Jua Technology Limited", "PVT-JUA002", email="tenders@juatech.example")
	accounts.assign(DAVID, AFYA, "Supplier Representative", job_title="Tender Coordinator")
	accounts.assign(MARY, AFYA, "Authorised Signatory", job_title="Managing Director")
	accounts.assign(PETER, KISIWA, "Supplier Representative", job_title="Bids Manager")
	accounts.assign(GRACE, KISIWA, "Authorised Signatory", job_title="Director")
	accounts.add_evidence(KISIWA, "EVD-BDST-JV", "Joint-venture agreement", "kisiwa-jua-jv-agreement.pdf")
	return accounts


def ensure_people() -> None:
	for email, full_name in PEOPLE.items():
		if not frappe.db.exists("User", email):
			first, _, last = full_name.partition(" ")
			frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)


def remove_people() -> None:
	for email in PEOPLE:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()


def wipe_bids() -> None:
	clear.wipe(tenders=tender_fx.test_tenders(), namespace=NS)
	frappe.db.commit()


class BidCase(OpenPeriodCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_people()
		cls.addClassCleanup(remove_people)
		cls.addClassCleanup(wipe_bids)

	def setUp(self):
		wipe_bids()
		super().setUp()
		self.reference = self._root().tender_reference
		self.accounts = fixture_accounts()
		self._flag("kt_supplier_account_provider", self.accounts)
		self._flag("kt_tender_candidate_registry", candidate_registry)
		self._flag("kt_bds_fixture_namespace", NS)
		self.at(START_AT)

	def _flag(self, name: str, value) -> None:
		previous = frappe.flags.get(name)
		frappe.flags[name] = value
		self.addCleanup(frappe.flags.__setitem__, name, previous)

	def at(self, instant: str) -> None:
		frappe.flags.kt_bds_clock = instant
		frappe.flags.kt_tenders_clock = instant
		self.addCleanup(setattr, frappe.flags, "kt_bds_clock", None)

	def single(self, **overrides) -> dict[str, Any]:
		return {"arrangement_type": "Single organisation", **overrides}

	def joint_venture(self, **overrides) -> dict[str, Any]:
		return {
			"arrangement_type": "Joint venture", "joint_venture_name": "Kisiwa–Jua Technology JV", "members": [{"country": "Kenya", "registration_number": "PVT-JUA002"}],
			"agreement_evidence_id": "EVD-BDST-JV", "signatory_assignment_id": f"ASG-{KISIWA}-bdst.grace", **overrides,
		}
