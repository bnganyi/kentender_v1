# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical `contracts` stage (SEED-002 v0.10 section A8.1; owner decisions of 17 October 2026).

The canonical world's three closed-year awards (SEED-002 section A7: staff workstations, multifunction printers, staff laptops, each accepted by Afya Digital Supplies Limited) are carried on from the supplier's
acceptance into Contract Management through the **same services as production**, as the people the register names, each step at its own fixture instant under the frozen seed clock (R6) and none later than
the anchor (R1). Nothing is written into another app's records: Award delivers its frozen package to Contract Management's receiver; Contract Management forms, signs, receives, inspects, accepts, takes
the claim, certifies and settles; Budget converts the funding; ERPNext documents are made by Contract Management's own native adapter.

Where each award stands at the anchor:

| Award | At the anchor | Story |
|---|---|---|
| Y0-1 staff workstations | **Paid** | delivered to Contracting, agreement formed and signed, every unit received, inspected and accepted, the claim certified, posted and paid in full |
| Y0-2 multifunction printers | **In delivery** | agreement in force; two thirds of the printers received, inspected and accepted; the rest not yet delivered |
| Y0-3 staff laptops | **Waiting for its agreement** | delivered to Contracting; the head of procurement has recorded the award's publication and has not yet prepared the contract |

The instants are offsets from the instant the award reaches Contracting (the end of its waiting period, which Award's own clock rules give), so the story moves with the anchor. The performance security is an
instrument of KCB Bank Kenya (the bank of Afya's bid security) for the amount the issued terms require; its reference and the bank's confirmation are new content for the Project Owner's review.

`kentender_contracts.seeds.demo` (the nine demonstration profiles) is separate and stays so: it tells one synthetic contract at a time on a moved clock. This stage is the world.

    bench --site <site> execute kentender_core.seeds.contracts_stage.upsert_contracts_base
    bench --site <site> execute kentender_core.seeds.contracts_stage.validate_contracts_seed"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterator

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_core.seeds import calendar, clock as seed_clock

NAMESPACE = "KENTENDER_MVP_1_R1_CM"
#: the namespace the canonical Budget keeps its seeded reservations and commitments under (kentender_core.seeds.canonical.REQUISITIONS_NS)
BUDGET_NAMESPACE = "KENTENDER_MVP_1_R1_REQ"
SUPPLIER = "Afya Digital Supplies Limited"
BANK_ACCOUNT_NAME = "KenTender Treasury Account"
MODE_OF_PAYMENT = "Wire Transfer"
WORKFLOW = "KenTender Payment Approval"
ISSUER = "KCB Bank Kenya"
#: the native roles the Payment Entry workflow and the stock and purchase documents ask of Finance (the register people hold their responsibilities; ERPNext's own permissions are separate)
FINANCE_ROLES = {"josphat": ("Accounts User", "Purchase User", "Stock User", "Item Manager"), "beatrice": ("Accounts Manager", "Purchase Manager", "Stock Manager")}

PEOPLE = {
	"charles": "charles.mutiso@moh.example.test", "brian": "brian.wafula@moh.example.test", "amina": "amina.hassan@moh.example.test", "julia": "julia.njeri@moh.example.test",
	"peter": "peter.kimani@moh.example.test", "grace": "grace.wanjiku@moh.example.test", "josphat": "josphat.mwangi@moh.example.test", "beatrice": "beatrice.kamau@moh.example.test",
	"mary": "mary.wanjiku@afyadigital.example", "david": "david.ouma@afyadigital.example",
}


@dataclass(frozen=True)
class Story:
	key: str  # the portfolio item (kentender_core.seeds.portfolio)
	ref: str
	state: str  # paid | delivering | received
	item_code: str
	unit_prefix: str
	delivered_share: tuple[int, int] = (1, 1)  # the part of the quantity that has arrived (numerator, denominator)


STORIES = (
	Story("y0_workstations", "Y0-1", "paid", "KT-WORKSTATION", "WS"),
	Story("y0_printers", "Y0-2", "delivering", "KT-PRINTER", "PRN", (2, 3)),
	Story("y0_laptops", "Y0-3", "received", "KT-LAPTOP", "LPT"),
)
#: what each state means for the case at the anchor: lifecycle, accepted share of the arrived units, settled
EXPECTED = {"paid": {"lifecycle": "Active", "paid": True}, "delivering": {"lifecycle": "Active", "paid": False}, "received": {"lifecycle": "Preparing", "paid": False}}


# -- environment -------------------------------------------------------------------------------------------------------------------------
@contextmanager
def environment() -> Iterator[None]:
	"""The flags the story runs under, set and restored together: Contract Management is Award's receiver, the records carry the stage's namespace, and Budget (not Contract Management's development
	stand-in, which a simulation site would otherwise choose) converts the funding."""
	from kentender_budget.services.contract_funding_provider import service as budget_funding

	saved_conf = {k: frappe.conf.get(k) for k in ("kt_award_contracting_receiver", "kt_cm_simulation_environment")}
	saved_flags = {k: frappe.flags.get(k) for k in ("kt_cm_fixture_namespace", "kt_contract_funding_providers", "kt_awd_clock", "kt_cm_clock", "kt_contract_source_providers")}
	frappe.conf["kt_award_contracting_receiver"] = "contracts"
	frappe.conf["kt_cm_simulation_environment"] = 1
	frappe.flags.kt_cm_fixture_namespace = NAMESPACE
	frappe.flags.kt_contract_funding_providers = [budget_funding()]
	frappe.flags.kt_contract_source_providers = None
	frappe.set_user("Administrator")
	try:
		yield
	finally:
		for key, value in saved_conf.items():
			if value is None:
				frappe.conf.pop(key, None)
			else:
				frappe.conf[key] = value
		for key, value in saved_flags.items():
			setattr(frappe.flags, key, value)


@contextmanager
def at(instant: Any) -> Iterator[None]:
	"""One command at its fixture instant: the shared seed clock and the clocks Award and Contract Management read."""
	moment = str(get_datetime(instant))
	frappe.flags.kt_awd_clock = moment
	frappe.flags.kt_cm_clock = moment
	try:
		with seed_clock.at(moment):
			yield
	finally:
		frappe.flags.kt_awd_clock = None
		frappe.flags.kt_cm_clock = None


def plus(base: Any, **offset: float) -> str:
	return str(get_datetime(base) + timedelta(**offset))


def _guard() -> None:
	from kentender_contracts.services import simulation

	if not simulation.enabled():
		frappe.throw("The canonical contracts stage uses the simulated signing and Finance evidence and is seeded on a simulation environment only.")
	if "kentender_contracts" not in frappe.get_installed_apps():
		frappe.throw("Contract Management is not installed on this site.")


# -- what the world holds ------------------------------------------------------------------------------------------------------------------
def _spec(story: Story) -> dict[str, Any]:
	from kentender_core.seeds import portfolio

	return next(spec for spec in portfolio.PORTFOLIO0 if spec["key"] == story.key)


def award_of(story: Story) -> str:
	"""The Award case of the story's closed-year Tender, or empty."""
	from kentender_core.seeds import portfolio

	requisition = portfolio._requisition(_spec(story))
	tender = frappe.db.get_value("Tender", {"requisition": requisition}, "name") if requisition else ""
	return frappe.db.get_value("Award Case", {"tender": tender}, "name") if tender else ""


def case_of(award: str) -> str:
	return cstr(frappe.db.get_value("Contract Case", {"source_kind": "KenTender award", "source_reference": award}, "name")) if award else ""


def _terms(case: str) -> dict[str, Any]:
	from kentender_contracts.services import records

	name = frappe.db.get_value("Contract Agreement Version", {"contract_case": case}, "terms_json", order_by="version_no desc")
	return records.loads(name) if name else {}


def _version(case: str) -> int:
	return cint(frappe.db.get_value("Contract Case", case, "record_version"))


# -- the native masters Contract Management's documents need ----------------------------------------------------------------------------------
def company() -> str:
	return cstr(frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name"))


def bank_account() -> str:
	return f"{BANK_ACCOUNT_NAME} - {frappe.db.get_value('Company', company(), 'abbr')}"


def ensure_masters() -> dict[str, Any]:
	"""The ERPNext records the story's documents refer to, made once and only where missing: the supplier, one plain stock item per line, the bank account and its mode of payment, the Payment Entry approval
	workflow (Finance configuration: Frappe keeps one active workflow per document type, so none is made over an existing one) and Finance's native roles."""
	from kentender_contracts.native import fields

	made: dict[str, Any] = {}
	fields.ensure()
	if not frappe.db.exists("Supplier", SUPPLIER):
		frappe.get_doc({"doctype": "Supplier", "supplier_name": SUPPLIER, "supplier_group": "Hardware", "supplier_type": "Company", "default_currency": "KES"}).insert(ignore_permissions=True)
		made["supplier"] = SUPPLIER
	for story in STORIES:
		case_award = award_of(story)
		if not case_award or frappe.db.exists("Item", story.item_code):
			continue
		spec, line = _spec(story), _first_line(case_award)
		frappe.get_doc({"doctype": "Item", "item_code": story.item_code, "item_name": spec["item_name"], "item_group": "Products", "stock_uom": "Nos", "is_purchase_item": 1, "is_sales_item": 0, "is_stock_item": 1,
			"valuation_rate": line["rate"], "standard_rate": line["rate"]}).insert(ignore_permissions=True)
		made.setdefault("items", []).append(story.item_code)
	account = bank_account()
	if not frappe.db.exists("Account", account):
		parent = frappe.db.get_value("Account", {"company": company(), "is_group": 1, "account_name": "Bank Accounts"}, "name")
		frappe.get_doc({"doctype": "Account", "account_name": BANK_ACCOUNT_NAME, "parent_account": parent, "company": company(), "account_type": "Bank", "root_type": "Asset", "is_group": 0}).insert(ignore_permissions=True)
		made["bank_account"] = account
	if not frappe.db.exists("Mode of Payment Account", {"parent": MODE_OF_PAYMENT, "company": company()}):
		mop = frappe.get_doc("Mode of Payment", MODE_OF_PAYMENT)
		mop.append("accounts", {"company": company(), "default_account": account})
		mop.save(ignore_permissions=True)
	if not frappe.db.exists("Workflow", {"document_type": "Payment Entry", "is_active": 1}):
		if frappe.db.exists("Workflow", WORKFLOW):  # the stage's own workflow, suspended by a test that did not put it back
			frappe.db.set_value("Workflow", WORKFLOW, "is_active", 1)
		else:
			_payment_workflow()
		made["workflow"] = WORKFLOW
	for persona, roles in FINANCE_ROLES.items():
		frappe.get_doc("User", PEOPLE[persona]).add_roles(*roles)
	frappe.db.commit()
	frappe.clear_cache()
	return made


def _payment_workflow() -> None:
	for state in ("Draft", "Pending Approval", "Approved"):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)
	for action in ("Submit for approval", "Approve", "Return"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Workflow", "workflow_name": WORKFLOW, "document_type": "Payment Entry", "is_active": 1, "workflow_state_field": "workflow_state", "send_email_alert": 0,
		"states": [{"state": "Draft", "doc_status": "0", "allow_edit": "Accounts User"}, {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Accounts Manager"},
			{"state": "Approved", "doc_status": "1", "allow_edit": "Accounts Manager"}],
		"transitions": [
			{"state": "Draft", "action": "Submit for approval", "next_state": "Pending Approval", "allowed": "Accounts User", "allow_self_approval": 1},
			{"state": "Pending Approval", "action": "Approve", "next_state": "Approved", "allowed": "Accounts Manager", "allow_self_approval": 0},
			{"state": "Pending Approval", "action": "Return", "next_state": "Draft", "allowed": "Accounts Manager", "allow_self_approval": 0},
		],
	}).insert(ignore_permissions=True)


def _first_line(award: str) -> dict[str, Any]:
	"""The awarded price line (Award's own source S3, read through the core seam)."""
	from kentender_contracts.services import source_package
	from kentender_core.services import contract_source_contract as seam

	found = source_package.gather([row for row in seam.handoff(award) if row["source"] == "S3"])
	return found["sources"]["S3"]["data"]["lines"][0]


# -- the story ---------------------------------------------------------------------------------------------------------------------------
class Teller:
	"""One award's story, told a step at a time. Every call carries a fresh idempotency key and the version the case was last seen at."""

	def __init__(self, story: Story, award: str):
		self.story, self.award, self.case, self.n = story, award, "", 0

	def key(self, step: str) -> str:
		self.n += 1
		return f"canonical-cm:{self.award}:{step}:{self.n}"

	def v(self) -> int:
		return _version(self.case)

	def deliver(self) -> str:
		"""Award's own refresh, at the instant its waiting period ends: Contract Management's receiver answers and the contract case exists."""
		from kentender_procurement.award.services import clocks, eligibility, records as award_records, state

		doc = frappe.get_doc(award_records.CASE, self.award)
		batch = state.current_batch(doc)
		earliest = clocks.earliest_permitted(doc, batch) if batch else {}
		if not earliest.get("known"):
			frappe.throw(f"{self.award}: the waiting period is not established, so the award cannot be delivered to Contracting.")
		self.delivered_at = str(get_datetime(earliest["at"]))
		with at(self.delivered_at):
			result = eligibility.refresh_case(self.award)
		if result.get("stage") != "Sent to Contracting":
			frappe.throw(f"{self.award}: Award did not deliver the package to Contracting ({result}).")
		self.case = case_of(self.award)
		if not self.case:
			frappe.throw(f"{self.award}: Contract Management made no case from the delivered package.")
		return self.case

	def publication(self, instant: str) -> None:
		from kentender_contracts.services import obligations

		with at(instant):
			row = obligations.get(self.case, "Publication", "publication")
			if row is not None and row.state != "Satisfied":
				obligations.record_publication(self.case, obligation=row.name, channel="Notice board", published_on=instant[:10], evidence=[{"label": "Notice board photograph", "file": "/private/files/publication.jpg"}],
					expected_version=self.v(), idempotency_key=self.key("publication"), actor=PEOPLE["charles"])

	def form(self, d: str) -> None:
		"""Prepare, secure, send and sign: an Active contract with its native order and its funding converted."""
		from kentender_contracts.services import formation, security

		agreement_at = plus(d, days=1, hours=1)
		with at(agreement_at):
			formation.save_particulars(self.case, expected_version=self.v(), idempotency_key=self.key("particulars"), actor=PEOPLE["brian"], values={
				"agreement_date": agreement_at[:10], "entity_signatory": PEOPLE["amina"], "item_mapping": {"L1": self.story.item_code}, "native_supplier": SUPPLIER})
		need = security.requirement(security._terms(self.case))
		if need:
			recorded_at = plus(d, days=1, hours=2)
			with at(recorded_at):
				row = security.record_security(self.case, expected_version=self.v(), idempotency_key=self.key("security"), actor=PEOPLE["charles"], issuer=ISSUER, beneficiary=_terms(self.case)["parties"]["entity"]["name"],
					reference=f"KCB/PG/{recorded_at[:4]}/{self.story.ref[-1]}", amount=need["amount"], issued_on=recorded_at[:10], expires_on=plus(recorded_at, days=3 * 365 + 200)[:10])["security"]
			with at(plus(d, days=1, hours=2.5)):
				security.verify_security(self.case, security=row, expected_version=self.v(), idempotency_key=self.key("verify"), actor=PEOPLE["charles"], confirmation_reference=f"KCB/PG/{recorded_at[:4]}/{self.story.ref[-1]}-CONF",
					received_on=recorded_at[:10], basis="Issuer confirmation")
		with at(plus(d, days=1, hours=3)):
			formation.request_signatures(self.case, expected_version=self.v(), idempotency_key=self.key("send"), actor=PEOPLE["charles"])
		with at(plus(d, days=2)):
			formation.sign_contract(self.case, party="Supplier", expected_version=self.v(), idempotency_key=self.key("sign-supplier"), actor=PEOPLE["mary"])
		with at(plus(d, days=3, hours=1)):
			formation.sign_contract(self.case, party="Entity", expected_version=self.v(), idempotency_key=self.key("sign-entity"), actor=PEOPLE["amina"])

	def inspectors(self, d: str) -> None:
		from kentender_contracts.services import delivery

		members = [{"user": PEOPLE["julia"], "capacity": "Chair", "role_label": "User department"}, {"user": PEOPLE["peter"], "capacity": "Member", "certifier": True, "role_label": "Technical"},
			{"user": PEOPLE["brian"], "capacity": "Member", "role_label": "Procurement"}]
		with at(plus(d, days=5, hours=1)):
			recommended = delivery.recommend_inspectors(self.case, expected_version=self.v(), idempotency_key=self.key("recommend"), actor=PEOPLE["charles"], members=members, acceptance="Committee accepts")
		with at(plus(d, days=5, hours=1.5)):
			delivery.appoint_inspectors(self.case, appointment=recommended["appointment"], expected_version=self.v(), idempotency_key=self.key("appoint"), actor=PEOPLE["amina"])
		for offset, who in ((2, "julia"), (2.25, "peter"), (2.5, "brian")):
			with at(plus(d, days=5, hours=offset)):
				delivery.declare_interest(self.case, expected_version=self.v(), idempotency_key=self.key("declare"), actor=PEOPLE[who])

	def delivered(self, d: str) -> str:
		"""Part (or all) of the goods arrive, are inspected unit by unit against the issued criteria, certified and accepted; returns the arrival."""
		from kentender_contracts.services import delivery

		terms = _terms(self.case)
		line = terms["lines"][0]
		count = max(1, cint(line["quantity"]) * self.story.delivered_share[0] // self.story.delivered_share[1])
		units = [f"{self.story.unit_prefix}-{get_datetime(d).year}-{n:04d}" for n in range(1, count + 1)]
		with at(plus(d, days=12, hours=1)):
			arrival = delivery.record_arrival(self.case, expected_version=self.v(), idempotency_key=self.key("arrival"), actor=PEOPLE["grace"], received_at=plus(d, days=12, hours=1), destination=terms["delivery"]["destination"],
				items=[{"line_id": line["line_id"], "quantity": count, "units": units}])["arrival"]
		readings = [{"unit": unit, "criterion_id": c["id"], "value": cstr(c["value"])} for unit in units for c in terms["criteria"]]
		with at(plus(d, days=13, hours=1)):
			delivery.record_inspection(self.case, arrival=arrival, expected_version=self.v(), idempotency_key=self.key("inspect"), actor=PEOPLE["peter"], observations=readings)
		with at(plus(d, days=14, hours=1)):
			delivery.sign_technical_certificate(self.case, arrival=arrival, expected_version=self.v(), idempotency_key=self.key("certificate"), actor=PEOPLE["peter"])
		with at(plus(d, days=15, hours=1)):
			report = delivery.prepare_acceptance_report(self.case, arrivals=[arrival], expected_version=self.v(), idempotency_key=self.key("prepare"), actor=PEOPLE["julia"])
		for offset, who in ((2, "julia"), (2.25, "peter"), (2.5, "brian")):
			with at(plus(d, days=15, hours=offset)):
				delivery.sign_acceptance_report(self.case, acceptance=report["acceptance"], expected_version=self.v(), idempotency_key=self.key("sign-acceptance"), actor=PEOPLE[who])
		self.units = count
		return arrival

	def paid(self, d: str) -> None:
		"""The supplier claims for what was accepted; procurement certifies, Finance posts the liability and pays it in full."""
		from kentender_contracts.services import payment

		terms = _terms(self.case)
		line = terms["lines"][0]
		with at(plus(d, days=19)):
			invoice = payment.submit_invoice(self.case, expected_version=self.v(), idempotency_key=self.key("claim"), actor=PEOPLE["david"], claim_reference=f"AFYA/INV/{plus(d, days=19)[:4]}/{self.story.ref[-1]}",
				invoice_date=plus(d, days=19)[:10], lines=[{"line_id": line["line_id"], "quantity": self.units, "rate": None}])["invoice"]
		with at(plus(d, days=20)):
			payment.sign_certification(self.case, invoice=invoice, expected_version=self.v(), idempotency_key=self.key("certify"), actor=PEOPLE["charles"])
		native = frappe.db.get_value("Contract Invoice", invoice, "native_invoice")
		with at(plus(d, days=21)):
			payment.save_accounting_invoice(self.case, invoice=invoice, expected_version=self.v(), idempotency_key=self.key("accounting"), actor=PEOPLE["josphat"], posting_date=plus(d, days=21)[:10],
				payable_account=frappe.db.get_value("Company", company(), "default_payable_account"), cost_centre=frappe.db.get_value("Company", company(), "cost_center"),
				expense_account=frappe.db.get_value("Purchase Invoice Item", {"parent": native}, "expense_account"))
			payment.submit_accounting_invoice(self.case, invoice=invoice, expected_version=self.v(), idempotency_key=self.key("accounting-submit"), actor=PEOPLE["josphat"])
		with at(plus(d, days=22)):
			payment.approve_accounting_invoice(self.case, invoice=invoice, expected_version=self.v(), idempotency_key=self.key("accounting-approve"), actor=PEOPLE["beatrice"])
		reference = f"EFT/{plus(d, days=25)[:4]}/{self.story.ref[-1]}"
		with at(plus(d, days=25)):
			draft = payment.save_finance_draft(self.case, invoice=invoice, expected_version=self.v(), idempotency_key=self.key("draft"), actor=PEOPLE["josphat"], mode_of_payment=MODE_OF_PAYMENT,
				paid_from=bank_account(), reference_no=reference)
			payment.submit_finance_for_approval(self.case, payment=draft["payment"], expected_version=self.v(), idempotency_key=self.key("submit"), actor=PEOPLE["josphat"])
		with at(plus(d, days=28)):
			payment.approve_finance_record(self.case, payment=draft["payment"], expected_version=self.v(), idempotency_key=self.key("approve"), actor=PEOPLE["beatrice"])
		with at(plus(d, days=30)):
			payment.record_finance_settlement(self.case, payment=draft["payment"], expected_version=self.v(), idempotency_key=self.key("settle"), actor=PEOPLE["beatrice"], effective_date=plus(d, days=30)[:10],
				evidence=f"Bank statement line for {reference}")

	def tell(self) -> str:
		d = None
		self.deliver()
		d = self.delivered_at
		self.publication(plus(d, minutes=30))
		if self.story.state in ("paid", "delivering"):
			self.form(d)
			self.inspectors(d)
			self.delivered(d)
		if self.story.state == "paid":
			self.paid(d)
		return self.case


def _stamp_commitments(case: str) -> int:
	"""The commitments Budget converted for the contract belong to the canonical Budget's seeded namespace, so its validator reads them as canonical (not as strays)."""
	count = 0
	for name in frappe.get_all("Procurement Commitment", filters={"contract": case}, pluck="name"):
		frappe.db.set_value("Procurement Commitment", name, "fixture_namespace", BUDGET_NAMESPACE, update_modified=False)
		count += 1
	return count


# -- the stage -------------------------------------------------------------------------------------------------------------------------
def problems(story: Story) -> list[str]:
	"""Everything that keeps the story's contract from being the state it claims to be (empty means it is)."""
	award = award_of(story)
	if not award:
		return [f"{story.ref}: the closed-year award is not there"]
	case = case_of(award)
	if not case:
		return [f"{story.ref}: Contract Management holds no case for {award}"]
	found: list[str] = []
	want = EXPECTED[story.state]
	row = frappe.db.get_value("Contract Case", case, ["lifecycle", "legal_profile", "fixture_namespace"], as_dict=True)
	if row.fixture_namespace != NAMESPACE:
		found.append(f"{case} is not in the stage's namespace ({row.fixture_namespace!r})")
	if row.lifecycle != want["lifecycle"]:
		found.append(f"{case} is {row.lifecycle}, not {want['lifecycle']}")
	if frappe.db.get_value("Award Case", award, "stage") != "Sent to Contracting":
		found.append(f"{award} is not Sent to Contracting")
	settled = frappe.db.count("Contract Settlement", {"contract_case": case, "state": "Confirmed"})
	if want["paid"] != bool(settled):
		found.append(f"{case} has {settled} settled payment(s); the story says {'paid' if want['paid'] else 'not paid'}")
	if story.state in ("paid", "delivering"):
		if not frappe.db.exists("Contract Operation Intent", {"contract_case": case, "operation_kind": "Purchase order", "state": "Succeeded"}):
			found.append(f"{case} has no native purchase order")
		if not frappe.db.exists("Procurement Commitment", {"contract": case}):
			found.append(f"{case} has no Budget commitment")
		if not frappe.db.exists("Contract Acceptance", {"contract_case": case, "state": "Effective"}):
			found.append(f"{case} has no accepted delivery")
	return found


def upsert_contracts_base(*, commit: bool = False) -> dict[str, Any]:
	"""The `contracts` stage. A world whose three contracts already stand where the story puts them is returned untouched; any other (a partly told stage, a failed run) is cleared and told again."""
	_guard()
	if all(not problems(story) for story in STORIES):
		return {"ok": True, "idempotent": True, "cases": {s.ref: case_of(award_of(s)) for s in STORIES}}
	from kentender_procurement.award.seeds.kentender_mvp_v1 import award_portfolio_tender
	from kentender_core.seeds import portfolio

	clear_contracts(recreate_awards=False)
	told: dict[str, str] = {}
	with environment():
		for story in STORIES:
			award = award_of(story)
			if not award:
				frappe.throw(f"{story.ref}: the closed-year award is not there; seed through the award stage first.")
			if frappe.db.get_value("Award Case", award, "stage") == "Sent to Contracting":  # a delivery from an earlier, cleared telling
				tender = frappe.db.get_value("Award Case", award, "tender")
				award_portfolio_tender(tender, through="accepted", clock_map=_spec(story)["award"]["clock"])
		ensure_masters()
		_series_floor()
		for story in STORIES:
			award = award_of(story)
			teller = Teller(story, award)
			told[story.ref] = teller.tell()
			_stamp_commitments(told[story.ref])
			frappe.db.commit()
	if commit:
		frappe.db.commit()
	return {"ok": True, "idempotent": False, "cases": told}


def validate_contracts_seed() -> list[dict[str, Any]]:
	"""One row per fact of the stage. Never mutates."""
	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": f"contracts: {label}"})

	for story in STORIES:
		found = problems(story)
		check(not found, f"{story.ref} stands where the story puts it ({story.state})" + (f": {'; '.join(found)}" if found else ""))
	check(bool(frappe.db.exists("Workflow", {"document_type": "Payment Entry", "is_active": 1})), "an active Payment Entry workflow exists (Finance's approval of a payment; a Contract Management test that suspends it must put it back)")
	stray = frappe.get_all("Contract Case", filters={"fixture_namespace": ["!=", NAMESPACE]}, pluck="name")
	check(not stray, f"no Contract Management case outside the canonical namespace (found {stray})")
	profile_cases = frappe.get_all("Contract Case", filters={"fixture_namespace": "CM_DEMO"}, pluck="name")
	check(not profile_cases, f"no Contract Management demonstration profile is loaded (found {profile_cases})")
	return rows


# -- clearing ---------------------------------------------------------------------------------------------------------------------------
NATIVE_ORDER = ("Payment Entry", "Journal Entry", "Purchase Invoice", "Purchase Receipt", "Purchase Order")


def native_documents(cases: list[str]) -> list[tuple[str, str]]:
	"""The ERPNext documents Contract Management linked to these cases, in the order they must be cancelled and removed."""
	rows = frappe.get_all("Contract Transaction Link", filters={"contract_case": ["in", cases or ["-"]]}, fields=["native_doctype", "native_name"])
	# only ERPNext's own documents: a link to a Budget commitment or to the signing simulation's proof is not a native document and goes with its owner's clear
	found = {(r.native_doctype, r.native_name) for r in rows if r.native_name and r.native_doctype in NATIVE_ORDER}
	return sorted(found, key=lambda pair: (NATIVE_ORDER.index(pair[0]), pair[1]))


def _series_snapshot() -> dict[str, int]:
	return {cstr(name): cint(current) for name, current in frappe.db.sql("select name, current from `tabSeries`")}


def _keep_series_counting_up(before: dict[str, int]) -> None:
	"""Frappe lowers a naming series when a document is deleted, and it reads the series of *today's* year for a document named in another: removing a closed-year document (`PUR-ORD-2025-00034`) in 2026
	read it as number 0 and lowered the 2026 series from 0 to -1, so the next order of 2026 was numbered 00000 again and the one after it collided. A series that has been counted up is never counted down by
	the stage's clear (and a number is never used twice)."""
	for name, value in before.items():
		frappe.db.sql("update `tabSeries` set current = %s where name = %s and current < %s", (value, name, value))


def _series_floor() -> int:
	"""Raise a series that has fallen below the highest number a native document of the stage's kinds holds (or below zero) to that number."""
	import re

	highest: dict[str, int] = {}
	for doctype in NATIVE_ORDER:
		for name in frappe.get_all(doctype, pluck="name"):
			found = re.match(r"^(.*?)(\d+)$", cstr(name))
			if found:
				highest[found.group(1)] = max(highest.get(found.group(1), 0), int(found.group(2)))
	fixed = 0
	for prefix, number in highest.items():
		fixed += frappe.db.sql("update `tabSeries` set current = %s where name = %s and current < %s", (number, prefix, number)) or 0
	frappe.db.sql("update `tabSeries` set current = 0 where current < 0 and name regexp '^(PUR-ORD|MAT-PRE|ACC-PINV|ACC-PAY|ACC-JV)-'")
	return len(highest)


def clear_contracts(*, recreate_awards: bool = True) -> dict[str, int]:
	"""Remove the stage: Contract Management's rows (by namespace, and the Award inbox rows its receiver kept under Award's), the native documents they linked, and the stage's masters. Budget's commitments go with
	Budget's own clear (a rebuild drops the canonical budgets); the closed-year awards are told again to the supplier's acceptance when `recreate_awards` (the next `upsert` does it as well)."""
	from kentender_contracts.services import records

	removed: dict[str, int] = {}
	cases = frappe.get_all("Contract Case", filters={"fixture_namespace": NAMESPACE}, pluck="name")
	awards = [a for a in (award_of(s) for s in STORIES) if a]
	cases += [c for c in (case_of(a) for a in awards) if c and c not in cases]
	failed: dict[str, str] = {}
	series = _series_snapshot()
	for doctype, name in native_documents(cases):
		try:
			doc = frappe.get_doc(doctype, name)
			if cint(doc.docstatus) == 1:
				doc.cancel()
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			removed[doctype] = removed.get(doctype, 0) + 1
		except Exception as exc:  # noqa: BLE001 - report and keep clearing
			failed[f"{doctype} {name}"] = cstr(exc)[:160]
	_keep_series_counting_up(series)
	items = [s.item_code for s in STORIES]
	frappe.db.delete("Stock Ledger Entry", {"item_code": ["in", items]})
	frappe.db.delete("Bin", {"item_code": ["in", items]})
	for doctype in records.DOCTYPES:
		if doctype != "Contract Case" and frappe.get_meta(doctype).has_field("contract_case") and cases:
			frappe.db.delete(doctype, {"contract_case": ["in", cases]})
	frappe.db.delete("Contract Award Inbox", {"award_case": ["in", awards or ["-"]]})
	if cases:
		frappe.db.delete("Contract Simulated Funding", {"contract": ["in", cases]})
		frappe.db.delete("Notification Log", {"document_type": "Contract Case", "document_name": ["in", cases]})
		frappe.db.delete("Contract Case", {"name": ["in", cases]})
	removed["Contract Case"] = len(cases)
	removed["rows"] = records.wipe(NAMESPACE)
	for code in items:
		if frappe.db.exists("Item", code):
			try:
				frappe.delete_doc("Item", code, force=True, ignore_permissions=True)
			except Exception as exc:  # noqa: BLE001
				failed[f"Item {code}"] = cstr(exc)[:160]
	if frappe.db.exists("Supplier", SUPPLIER) and not frappe.db.exists("Purchase Order", {"supplier": SUPPLIER}):
		try:
			frappe.delete_doc("Supplier", SUPPLIER, force=True, ignore_permissions=True)
		except Exception as exc:  # noqa: BLE001
			failed[f"Supplier {SUPPLIER}"] = cstr(exc)[:160]
	frappe.db.commit()
	if failed:
		removed["not_removed"] = len(failed)
		frappe.log_error(title="Canonical contracts clear: not removed", message=frappe.as_json(failed))
	return removed
