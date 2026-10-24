# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The people and the sources of the ordinary thread, for tests (plan D18, Phase 4; development only, never package acceptance).

Eleven people with the responsibilities the boards give them, a supplier-accounts stand-in that knows the supplier's signatory and representative, the synthetic source
provider and the clock the boards are read at (2 July 2027). Built once per test class on top of `native_world` and removed at its end. Nothing here runs on the dev site."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
from uuid import uuid4

import frappe

from kentender_contracts.services import records
from kentender_contracts.simulation import sources
from kentender_contracts.tests import native_world as world
from kentender_core.services import business_role_registry as registry
from kentender_core.services import responsibility_administration as administration
from kentender_core.services.command_write_guard import purge_doc

DOMAIN = "test.example.test"
#: persona -> (full name, [(responsibility, needs unit)])
PEOPLE: dict[str, tuple[str, list[str]]] = {
	"charles": ("Charles Mutiso", ["Head of Procurement Function"]),
	"brian": ("Brian Wafula", ["Contract preparation", "Contract inspection"]),
	"amina": ("Amina Hassan", ["Accounting Officer", "Entity contract signing"]),
	"julia": ("Julia Njeri", ["Contract inspection"]),
	"carol": ("Carol Coordinator", ["Contract coordination"]),
	"peter": ("Peter Mugo", ["Contract inspection", "Technical certification"]),
	"grace": ("Grace Wanjiku", ["Receiving"]),
	"faith": ("Faith Atieno", ["Contract inspection", "Technical certification"]),
	"josphat": ("Josphat Mwangi", ["Finance preparation"]),
	"beatrice": ("Beatrice Kamau", ["Finance approval"]),
	"daniel": ("Daniel Otieno", ["Technical Operator"]),
	"naomi": ("Naomi Auditor", ["Auditor"]),
	"mary": ("Mary Wanjiku", []),
	"david": ("David Otieno", []),
	"stranger": ("Sam Stranger", []),
}
CLOCK = D("2027-07-02 09:00:00")
#: the supplier's identity as an executed contract states it: country and registration number (the supplier-accounts stand-in resolves it)
REGISTRATION = ("Kenya", "CPR/2018/00123")


#: A browser world walks the seed world's own people: it maps a persona to their canonical address here (see `browser_world.py`); a test world uses throwaway `cm.thread.*` accounts.
ADDRESSES: dict[str, str] = {}


def email(persona: str) -> str:
	if persona in ADDRESSES:
		return ADDRESSES[persona]
	return sources.SUPPLIER_SIGNATORY if persona == "mary" else sources.ENTITY_SIGNATORY if persona == "amina" else f"cm.thread.{persona}@{DOMAIN}"


def ours(address: str) -> bool:
	"""An account this world created (and may delete): throwaway thread accounts only, never a seed-world person."""
	return address.startswith("cm.thread.")


class Suppliers:
	"""Supplier Accounts as the audience and parties code asks it: one organisation, its authorised signatory and its representative."""

	def __init__(self, organisation: str = ""):
		self.org = organisation or sources.organisation_id()

	def _row(self, user: str, responsibility: str) -> dict:
		return {"assignment_id": f"A-{user}", "organisation_id": self.org, "user": user, "responsibility": responsibility, "active": True, "signatory_ready": responsibility == "Authorised Signatory"}

	def active_assignments(self, *, user, at=None):
		return [self._row(user, "Authorised Signatory" if user == email("mary") else "Supplier Representative")] if user in (email("mary"), email("david")) else []

	def find_active_account(self, *, country, registration_number):
		return {"organisation_id": self.org, "legal_name": sources.SUPPLIER} if (country, registration_number) == REGISTRATION else None

	def organisation(self, *, organisation_id):
		return {"legal_name": sources.SUPPLIER, "registered_address": "Westlands Business Park, Waiyaki Way, Nairobi", "country": REGISTRATION[0]} if organisation_id == self.org else None

	def organisation_signatories(self, *, organisation_id, at=None):
		return [self._row(email("mary"), "Authorised Signatory")] if organisation_id == self.org else []

	def organisation_people(self, *, organisation_id, at=None):
		return [self._row(email("mary"), "Authorised Signatory"), self._row(email("david"), "Supplier Representative")] if organisation_id == self.org else []


def unit() -> str:
	return frappe.get_all("Organisation Unit", pluck="name", limit=1)[0]


def build(namespace: str = "CM_TEST") -> dict[str, str]:
	"""Create the people and grant their responsibilities (idempotent). Returns persona -> email. A responsibility the person already holds is left as it was; the ones granted here carry
	`namespace`, which is how `teardown` removes exactly those."""
	registry.ensure_roles()
	out = {}
	for persona, (name, roles) in PEOPLE.items():
		address = email(persona)
		if not frappe.db.exists("User", address):
			frappe.get_doc({"doctype": "User", "email": address, "first_name": name.split()[0], "last_name": name.split()[-1], "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		out[persona] = address
		for role in roles:
			administration.grant(user=address, business_role=role, organisation_unit=unit() if registry.REGISTRY[role].requires_organisation_unit else "", actor="Administrator", fixture_namespace=namespace)
	# the Finance people also need the native roles the Payment Entry workflow names
	for persona, roles in (("josphat", ["Accounts User", "Purchase User", "Stock User", "Item Manager"]), ("beatrice", ["Accounts Manager", "Purchase Manager", "Stock Manager"])):
		frappe.get_doc("User", out[persona]).add_roles(*roles)
	frappe.db.commit()
	return out


def teardown(namespace: str = "CM_TEST") -> None:
	purge_evidence_files()
	for persona in PEOPLE:
		address = email(persona)
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": address, "fixture_namespace": namespace}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		if ours(address) and frappe.db.exists("User", address):
			for name in frappe.get_all("User Responsibility Assignment", filters={"user": address}, pluck="name"):
				purge_doc("User Responsibility Assignment", name)
			frappe.delete_doc("User", address, force=True, ignore_permissions=True)
	frappe.db.commit()


class Environment:
	"""The flags a thread test runs under, set and restored together."""

	def __enter__(self):
		from kentender_contracts.services import simulation

		self.saved_conf = {flag: frappe.conf.get(flag) for flag in simulation.FLAGS}
		self.saved_flags = {k: frappe.flags.get(k) for k in ("kt_supplier_account_provider", "kt_cm_clock", "kt_contract_source_providers", "kt_contract_funding_providers")}
		frappe.conf.kt_cm_simulation_environment = 1
		frappe.flags.kt_supplier_account_provider = Suppliers()
		frappe.flags.kt_cm_clock = CLOCK
		frappe.flags.kt_contract_source_providers = None
		return self

	def __exit__(self, *exc):
		for flag, value in self.saved_conf.items():
			frappe.conf[flag] = value
		for key, value in self.saved_flags.items():
			setattr(frappe.flags, key, value)
		return False


def capture(board: dict, name: str | None = None) -> dict:
	"""With `CM_CAPTURE_BOARDS=1`, write a board as a fixture for the structural fidelity gate (see test_cm_boards). Returns the board."""
	import json
	import os
	from pathlib import Path

	if os.environ.get("CM_CAPTURE_BOARDS"):
		folder = Path(frappe.get_app_path("kentender_contracts")) / "public/js/contracts/fixtures"
		folder.mkdir(parents=True, exist_ok=True)
		(folder / f"{(name or board['id']).replace(' · ', '_')}.json").write_text(json.dumps(board, indent=1, sort_keys=True, default=str) + "\n")
	return board


def package_particulars(people: dict[str, str], services: bool = False, item: str = "") -> dict:
	return {"agreement_date": D("2027-07-02"), "entity_signatory": people["amina"], "item_mapping": {"L1": item or world.ITEM_FA, **({"L2": world.ITEM_SERVICE} if services else {})}, "native_supplier": world.SUPPLIER, "asset_location": world.LOCATION}


def receive(people: dict[str, str], *, contract_id: str = "CM-TEST-0001", security_required: bool = False, outside_signing: bool = False, services: bool = False, award_case: str = "", advance: bool = False, publication_open: bool = False) -> dict:
	"""Receive the demonstration Award package. With `security_required` the issued terms require a performance security, and the synthetic provider answers for that variant; `services` is the
	goods-plus-service package (ten laptops and a training session)."""
	from kentender_contracts.services import formation

	package = {**sources.award_package(services), **({"award_case": award_case} if award_case else {})}
	if security_required or outside_signing or services or advance:
		frappe.flags.kt_contract_source_providers = [sources.Provider(security_required=security_required, outside_signing=outside_signing, services=services, advance=advance)]
	out = formation.receive_award_package(package, handoff=sources.source_handoff(package["award_case"], security_required=security_required, outside_signing=outside_signing, services=services, advance=advance), managing_unit=unit(),
		idempotency_key=f"receive-{contract_id}", actor="Administrator", contract_id=contract_id)
	if not publication_open:
		publish(people, out["contract"])
		out = {**out, "record_version": int(frappe.db.get_value("Contract Case", out["contract"], "record_version"))}  # recording it advanced the revision the caller holds
	return out


def publish(people: dict[str, str], case: str) -> None:
	"""The head records the award's publication (notice board, with a photograph) as a diligent head does early. The head of procurement has a task to record it (FU-CM-108), the oldest on their day, so a flow that
	does not test the publication duty has it done; a test of the duty itself passes `publication_open`. A profile that cannot answer refuses it, and then there is nothing for the head to record."""
	from kentender_contracts.services import errors, obligations

	row = obligations.get(case, "Publication", "publication")
	if row is None or row.state == "Satisfied":
		return
	try:
		obligations.record_publication(case, obligation=row.name, channel="Notice board", published_on=CLOCK[:10], evidence=[{"label": "Notice board photograph", "file": "/private/files/publication.jpg"}],
			expected_version=int(frappe.db.get_value("Contract Case", case, "record_version")), idempotency_key=f"publish-{case}", actor=people["charles"])
	except errors.ContractError:
		return


def evidence_file(owner: str, label: str) -> str:
	"""A private labelled PDF uploaded by `owner` (the person's own upload is the only file a command accepts as evidence). Removed with the world."""
	from kentender_core.seeds.fixture_files import labelled_pdf

	doc = frappe.get_doc({"doctype": "File", "file_name": f"cm-test-{label}.pdf", "is_private": 1, "content": labelled_pdf(label)}).insert(ignore_permissions=True)
	frappe.db.set_value("File", doc.name, "owner", owner)
	frappe.db.commit()
	return doc.name


def purge_evidence_files() -> None:
	for name in frappe.get_all("File", filters={"file_name": ["like", "cm-test-%"]}, pluck="name"):
		frappe.delete_doc("File", name, force=True, ignore_permissions=True)
	frappe.db.commit()


def purge_native_operation_rows(case_ids: list[str]) -> None:
	records.wipe("CM_TEST")


# -- the thread, a step at a time (each returns what the next step needs) --------------------------------------------------------------------
class Thread:
	"""Drives the ordinary thread through the services as the people of the boards. `case` and the latest `version` are kept so each step passes the version it last saw."""

	def __init__(self, people: dict[str, str], tag: str = "T1", contract_id: str = "", services: bool = False, award_case: str = "", item: str = "", advance: bool = False, security: bool = False):
		self.p, self.tag, self.n, self.services, self.award_case, self.item, self.advance, self.security = people, tag, 0, services, award_case, item, advance, security
		self.contract_id = contract_id or f"CM-TEST-{tag}"
		self.case = ""

	def key(self, step: str) -> str:
		self.n += 1
		return f"{self.tag}-{step}-{self.n}"

	def version(self) -> int:
		return int(frappe.db.get_value("Contract Case", self.case, "record_version"))

	def active(self, publication_open: bool = False) -> str:
		"""Receive, prepare, send, both signatures: an Active contract with its native order. `publication_open` keeps the award's publication duty open (see `receive`)."""
		from kentender_contracts.services import formation

		out = receive(self.p, contract_id=self.contract_id, services=self.services, award_case=self.award_case, advance=self.advance, security_required=self.security, publication_open=publication_open)
		self.case = out["contract"]
		formation.save_particulars(self.case, expected_version=self.version(), idempotency_key=self.key("particulars"), actor=self.p["brian"], values=package_particulars(self.p, self.services, self.item))
		if self.security:  # the performance security the issued terms require is recorded and verified before the agreement is sent
			self.record_security()
		formation.request_signatures(self.case, expected_version=self.version(), idempotency_key=self.key("send"), actor=self.p["charles"])
		formation.sign_contract(self.case, party="Supplier", expected_version=self.version(), idempotency_key=self.key("sign-s"), actor=self.p["mary"])
		formation.sign_contract(self.case, party="Entity", expected_version=self.version(), idempotency_key=self.key("sign-e"), actor=self.p["amina"])
		return self.case

	def record_security(self, *, reference: str = "TEST-SG-01", amount: float = 100_000, issued_on: str = D("2027-07-01"), expires_on: str = D("2027-08-31"), verify: bool = True) -> str:
		"""Charles records an instrument for the Ministry and, unless told not to, verifies it from the issuer's confirmation."""
		from kentender_contracts.services import security

		row = security.record_security(self.case, expected_version=self.version(), idempotency_key=self.key("sec"), actor=self.p["charles"], issuer="Test Bank", beneficiary="Ministry of Health", reference=reference, amount=amount,
			issued_on=issued_on, expires_on=expires_on)["security"]
		if verify:
			security.verify_security(self.case, security=row, expected_version=self.version(), idempotency_key=self.key("secv"), actor=self.p["charles"], confirmation_reference=f"{reference}-CONF", received_on=D("2027-07-02"), basis="Issuer confirmation")
		return row

	def appointed(self, acceptance: str = "Committee accepts") -> dict:
		"""HOP recommends Julia (chair), Peter (technical) and Brian; the Accounting Officer appoints; each declares no interest. `acceptance` is who makes the acceptance a decision."""
		from kentender_contracts.services import delivery

		members = [{"user": self.p["julia"], "capacity": "Chair", "role_label": "User department"}, {"user": self.p["peter"], "capacity": "Member", "certifier": True, "role_label": "Technical"},
			{"user": self.p["brian"], "capacity": "Member", "role_label": "Procurement"}]
		rec = delivery.recommend_inspectors(self.case, expected_version=self.version(), idempotency_key=self.key("recommend"), actor=self.p["charles"], members=members, acceptance=acceptance)
		delivery.appoint_inspectors(self.case, appointment=rec["appointment"], expected_version=self.version(), idempotency_key=self.key("appoint"), actor=self.p["amina"])
		for who in ("julia", "peter", "brian"):
			delivery.declare_interest(self.case, expected_version=self.version(), idempotency_key=self.key("declare"), actor=self.p[who])
		return rec

	def arrive(self, units: list[str], *, received_at: str = D("2027-07-12 10:00:00")) -> dict:
		from kentender_contracts.services import delivery

		return delivery.record_arrival(self.case, expected_version=self.version(), idempotency_key=self.key("arrive"), actor=self.p["grace"], received_at=received_at,
			destination="Afya House store", items=[{"line_id": "L1", "quantity": len(units), "units": units}])

	def inspect(self, arrival: str, units: list[str], bad: tuple[str, ...] = (), blank: tuple[str, ...] = ()) -> dict:
		from kentender_contracts.services import delivery

		return delivery.record_inspection(self.case, arrival=arrival, expected_version=self.version(), idempotency_key=self.key("inspect"), actor=self.p["peter"], observations=readings(units, bad, blank))


def readings(units: list[str], bad: tuple[str, ...] = (), blank: tuple[str, ...] = ()) -> list[dict]:
	"""RAM and storage as supplied; "Starts successfully" is No for a unit in `bad` and not recorded for one in `blank`."""
	out = []
	for unit in units:
		out.append({"unit": unit, "criterion_id": "C1", "value": "16"})
		out.append({"unit": unit, "criterion_id": "C2", "value": "512"})
		out.append({"unit": unit, "criterion_id": "C3", "value": "" if unit in blank else "No" if unit in bad else "Yes"})
	return out


_RUN = uuid4().hex[:6].upper()
_NEXT = [0]


def fresh_serials(count: int) -> list[str]:
	"""Unit identities no earlier test (or earlier run that left assets behind) has used: a unit identifies one unit only, and the native world is built once per class."""
	out = [f"CMT{_RUN}-{_NEXT[0] + n:04d}" for n in range(1, count + 1)]
	_NEXT[0] += count
	return out


def _more(cls):
	"""Steps past inspection, attached to `Thread` (kept apart so the first half reads on its own)."""

	def accept(self, arrival: str) -> dict:
		from kentender_contracts.services import delivery

		delivery.sign_technical_certificate(self.case, arrival=arrival, expected_version=self.version(), idempotency_key=self.key("cert"), actor=self.p["peter"])
		out = delivery.prepare_acceptance_report(self.case, arrivals=[arrival], expected_version=self.version(), idempotency_key=self.key("prepare"), actor=self.p["julia"])
		for who in ("julia", "peter", "brian"):
			last = delivery.sign_acceptance_report(self.case, acceptance=out["acceptance"], expected_version=self.version(), idempotency_key=self.key("sign-a"), actor=self.p[who])
		return {**out, **last}

	def claim(self, reference: str, quantity: int, *, rate=None) -> dict:
		from kentender_contracts.services import payment

		return payment.submit_invoice(self.case, expected_version=self.version(), idempotency_key=self.key("claim"), actor=self.p["david"], claim_reference=reference, invoice_date=frappe.utils.today(),
			lines=[{"line_id": "L1", "quantity": quantity, "rate": rate}])

	def certify_invoice(self, invoice: str) -> dict:
		from kentender_contracts.services import payment

		return payment.sign_certification(self.case, invoice=invoice, expected_version=self.version(), idempotency_key=self.key("certify"), actor=self.p["charles"])

	def post_accounting(self, invoice: str) -> dict:
		"""Josphat completes the accounting details of the native invoice and submits; Beatrice posts it."""
		from kentender_contracts.services import payment

		native = frappe.db.get_value("Contract Invoice", invoice, "native_invoice")
		payment.save_accounting_invoice(self.case, invoice=invoice, expected_version=self.version(), idempotency_key=self.key("acct"), actor=self.p["josphat"], posting_date=frappe.utils.today(),
			payable_account=frappe.db.get_value("Company", world.COMPANY, "default_payable_account"), cost_centre=frappe.db.get_value("Company", world.COMPANY, "cost_center"),
			expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
		payment.submit_accounting_invoice(self.case, invoice=invoice, expected_version=self.version(), idempotency_key=self.key("acct-s"), actor=self.p["josphat"])
		return payment.approve_accounting_invoice(self.case, invoice=invoice, expected_version=self.version(), idempotency_key=self.key("acct-a"), actor=self.p["beatrice"])

	def pay(self, invoice: str, reference: str) -> dict:
		"""The accounting invoice is posted, then Josphat drafts and submits the payment, Beatrice approves and confirms the settlement."""
		from kentender_contracts.services import payment

		if frappe.db.get_value("Contract Invoice", invoice, "accounting_state") != "Posted":  # Finance may already have posted the liability
			self.post_accounting(invoice)
		draft = payment.save_finance_draft(self.case, invoice=invoice, expected_version=self.version(), idempotency_key=self.key("draft"), actor=self.p["josphat"], mode_of_payment=world.MODE,
			paid_from=world.BANK_ACCOUNT, reference_no=reference)
		payment.submit_finance_for_approval(self.case, payment=draft["payment"], expected_version=self.version(), idempotency_key=self.key("submit"), actor=self.p["josphat"])
		payment.approve_finance_record(self.case, payment=draft["payment"], expected_version=self.version(), idempotency_key=self.key("approve"), actor=self.p["beatrice"])
		settled = payment.record_finance_settlement(self.case, payment=draft["payment"], expected_version=self.version(), idempotency_key=self.key("settle"), actor=self.p["beatrice"],
			effective_date=D("2027-07-20"), evidence=f"Bank statement line for {reference}")
		return {**draft, **settled}

	def change_through(self, kind: str = "Extension", request: dict | None = None, *, number: int = 1, requester: str = "david", reason: str = "Supplier reports a shipment delay.") -> dict:
		"""A change requested, reviewed by three named people, decided by the Accounting Officer and signed by both parties: the amendment is effective."""
		from kentender_contracts.services import change

		request = request or ({"proposed_date": D("2027-07-27")} if kind == "Extension" else {"quantities": {"L1": 11}})
		evidence = [{"label": "Supplier request 1", "file": "/private/files/request-1.pdf"}]
		change.request_change(self.case, kind=kind, request=request, reason=reason, evidence=evidence, expected_version=self.version(), idempotency_key=self.key("ask"), actor=self.p[requester])
		roster = dict(zip(change.REVIEW_KINDS[kind], (self.p["peter"], self.p["faith"], self.p["brian"]), strict=True))
		change.appoint_reviewers(self.case, change=number, reference="AO/VAR/2027/001", reviewers=roster, expected_version=self.version(), idempotency_key=self.key("appoint"), actor=self.p["charles"])
		for review_kind, reviewer in roster.items():
			change.record_review(self.case, change=number, kind=review_kind, recommendation="Approve the change without a price change.", declaration=change.NO_CONFLICT, reference="QTY-01" if review_kind == "Funding confirmation" else "",
				expected_version=self.version(), idempotency_key=self.key("rec"), actor=reviewer)
			change.sign_review(self.case, change=number, kind=review_kind, expected_version=self.version(), idempotency_key=self.key("sig"), actor=reviewer)
		change.submit_for_decision(self.case, change=number, expected_version=self.version(), idempotency_key=self.key("submit"), actor=self.p["charles"])
		change.decide(self.case, change=number, decision="Approve", reason="The documented grounds support the change.", expected_version=self.version(), idempotency_key=self.key("decide"), actor=self.p["amina"])
		change.sign_amendment(self.case, change=number, party="Supplier", expected_version=self.version(), idempotency_key=self.key("sign-s"), actor=self.p["mary"])
		return change.sign_amendment(self.case, change=number, party="Entity", expected_version=self.version(), idempotency_key=self.key("sign-e"), actor=self.p["amina"])

	def confirm_delivery(self, *, method: str = "Hand delivery to the supplier", reference: str = "DISP-001") -> dict:
		"""The head of procurement confirms that the signed completion certificate reached the contractor, with the day, the way and the proof: the close-out review is generated from it."""
		from kentender_contracts.services import clock, closeout

		certificate = closeout.completion_certificate(self.case)
		return closeout.confirm_certificate_delivery(self.case, certificate=certificate.name, delivered_on=str(clock.now().date()), method=method, reference=reference, evidence=[{"label": "Signed delivery note", "file": "/private/files/delivery-note.pdf"}],
			expected_version=self.version(), idempotency_key=self.key("delivered"), actor=self.p["charles"])

	cls.accept, cls.claim, cls.certify_invoice, cls.post_accounting, cls.pay, cls.change_through, cls.confirm_delivery = accept, claim, certify_invoice, post_accounting, pay, change_through, confirm_delivery
	return cls


_more(Thread)
