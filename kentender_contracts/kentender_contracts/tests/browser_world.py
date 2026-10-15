# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The world the Contract Management browser specs walk (plan Phase 4; tracker CM8-416). Development only; the **test site only**.

Run before a browser spec and after it, through `bench execute` (the Makefile's `cm-ui-world` and `cm-ui-world-clean`):

* `build` -- the people of the boards with their responsibilities and a known password, the ERPNext items, supplier, accounts and Payment Entry workflow the thread needs, and one received Award
  package (the synthetic one: ten laptops, `CM-UI-0001`). It writes the people and the contract to `artifacts/cm-ui-world.json` for the spec. The supplier's people are the canonical Afya
  accounts of the seed world (Mary Wanjiku, David Ouma): only their password on this copy is set.
* `clean` -- removes everything `build` and the walk created, newest first.

It refuses any site but `kentender-test.local`: it sets passwords and writes documents."""

from __future__ import annotations

import json
import os
from pathlib import Path

import frappe
from frappe.utils.password import update_password

from kentender_contracts.native import adapter
from kentender_contracts.services import formation, records
from kentender_core.services import test_clock
from kentender_contracts.simulation import sources
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw

TEST_SITE = "kentender-test.local"
PASSWORD = "CmWalk-2027-Aa1!"
CONTRACT = "CM-UI-0001"
AWARD_CASE = "CM-UI-AWD-01"
#: the other received packages the formation spec walks: the issued terms require a performance security / permit signing outside the system (the case name carries the variant: `sources.variant`)
EXTRA = {"security": ("CM-UI-0002", "CM-UI-AWD-SEC"), "outside": ("CM-UI-0003", "CM-UI-AWD-OUT"), "ending": ("CM-UI-0004", "CM-UI-AWD-04")}
#: the contracts the delivery and acceptance spec walks, staged to the step the spec starts from (the staging goes through the services, each tested): `delivery` has its goods inspected, confirmed and the acceptance
#: report prepared, and leaves acceptance to the Accounting Officer; `service` has a training session recorded as performed (the `-SVC` case carries the goods-plus-service package)
STAGED = {"delivery": ("CM-UI-0005", "CM-UI-AWD-05"), "service": ("CM-UI-0006", "CM-UI-AWD-06-SVC"), "advance": ("CM-UI-0007", "CM-UI-AWD-07-ADV"), "payments": ("CM-UI-0008", "CM-UI-AWD-08"),
	"claims": ("CM-UI-0009", "CM-UI-AWD-09"), "changes": ("CM-UI-0010", "CM-UI-AWD-10"), "warranty": ("CM-UI-0011", "CM-UI-AWD-11"), "delay": ("CM-UI-0012", "CM-UI-AWD-12"),
	"security_actions": ("CM-UI-0013", "CM-UI-AWD-13"), "termination": ("CM-UI-0014", "CM-UI-AWD-14"), "closeout": ("CM-UI-0015", "CM-UI-AWD-15-FIN")}
#: the contracts of the invoice and payment specs: `advance` has its goods accepted and no advance yet; `payments` has a certified, posted invoice of eight to pay in instalments; `claims` has two claims with the
#: same invoice number (the second held for Finance as an apparent duplicate) and units still to claim
EXISTING_REFERENCE = "MOH/ICT/2027/EXT-UI"
NAMESPACE = "CM_UI"

DAVID = "david.ouma@afyadigital.example"


def output() -> Path:
	"""Where the spec reads the world from: the repository's artifacts folder, whatever directory the bench was started in."""
	return Path(os.environ.get("CM_UI_WORLD") or Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "artifacts/cm-ui-world.json")


def _guard() -> None:
	if frappe.local.site != TEST_SITE:
		raise RuntimeError(f"the Contract Management browser world is built on {TEST_SITE} only, not {frappe.local.site}")


#: The seed world's own people, by persona (SEED-002). Their responsibilities for contracts are added here and removed by `clean`; their accounts and what they already hold are not touched.
CANONICAL = {
	"charles": "charles.mutiso@moh.example.test", "brian": "brian.wafula@moh.example.test", "amina": "amina.hassan@moh.example.test", "julia": "julia.njeri@moh.example.test",
	"peter": "peter.mugo@moh.example.test", "grace": "grace.wanjiku@moh.example.test", "josphat": "josphat.mwangi@moh.example.test", "beatrice": "beatrice.kamau@moh.example.test",
	"daniel": "daniel.otieno@moh.example.test", "mary": sources.SUPPLIER_SIGNATORY, "david": DAVID,
}


def _use_canonical_people() -> None:
	tw.ADDRESSES.update(CANONICAL)


def _addresses() -> dict[str, str]:
	_use_canonical_people()
	return {persona: tw.email(persona) for persona in tw.PEOPLE if persona in CANONICAL}


def _accepted(t, count: int) -> list[str]:
	"""Goods delivered, inspected, confirmed and accepted by the committee."""
	units = tw.fresh_serials(count)
	arrival = t.arrive(units)["arrival"]
	t.inspect(arrival, units)
	t.accept(arrival)
	return units


def _stage(kind: str, contract_id: str, award_case: str, people: dict[str, str]) -> dict:
	"""An Active contract with its inspectors appointed and declared, taken to the step the spec that walks it starts from."""
	from frappe.utils import add_days, today

	from kentender_contracts.services import delivery, payment

	frappe.flags.kt_contract_source_providers = None  # the registered provider answers by the case's name; one left over from the previous contract would answer for the wrong variant
	t = tw.Thread(people, tag=f"UI{contract_id[-4:]}", contract_id=contract_id, services=award_case.endswith("-SVC"), award_case=award_case, item=world.ITEM_PLAIN if kind in ("warranty", "closeout") else "", security=kind == "security_actions")
	t.active()
	if kind in ("changes", "warranty", "delay", "security_actions", "termination", "closeout"):
		frappe.db.set_value("Contract Case", t.case, "responsible_user", people["carol"])  # the contract's owner: the coordinator who requests changes and records warranty claims
	t.appointed("Accounting Officer decides" if kind == "delivery" else "Committee accepts")
	out = {"contract": t.case}
	if kind == "advance":
		_accepted(t, 8)
	elif kind == "payments":
		_accepted(t, 8)
		inv = t.claim("PAY-1", 8)["invoice"]
		t.certify_invoice(inv)
		t.post_accounting(inv)
		out["invoice"] = inv
	elif kind == "claims":
		_accepted(t, 8)
		line = [{"line_id": "L1", "quantity": 3}]
		first = payment.submit_invoice(t.case, expected_version=t.version(), idempotency_key=t.key("c1"), actor=people["david"], claim_reference="DUP-1", invoice_date=today(), lines=line)["invoice"]
		second = payment.submit_invoice(t.case, expected_version=t.version(), idempotency_key=t.key("c2"), actor=people["david"], claim_reference="DUP-1", invoice_date=add_days(today(), -1), lines=line)["invoice"]
		out["invoices"] = [first, second]
	elif kind == "changes":
		pass  # an Active contract with its inspectors: the walk requests the extension, names the reviewers, decides and signs
	elif kind == "warranty":
		units = _accepted(t, 10)
		out["units"] = units
		receipt = delivery.posted_receipts(t.case)[0]
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_return

		native = make_purchase_return(receipt)  # Finance's native return of one unit, which the walk names when it reconciles the returned unit
		native.items[0].qty = native.items[0].received_qty = -1
		native.insert(ignore_permissions=True)
		native.submit()
		out["native_return"] = native.name
	elif kind == "closeout":
		_accepted(t, 10)  # everything ordered is accepted and the issued terms ask for the Accounting Officer's final acceptance (the `-FIN` case): the walk records it, completes, closes and corrects
	elif kind == "delay":
		units = tw.fresh_serials(10)
		arrival = t.arrive(units, received_at="2027-07-12 10:00:00")["arrival"]
		t.inspect(arrival, units)
		frappe.flags.kt_cm_clock = "2027-07-25 10:00:00"  # accepted after the due date of the 20th: five days late
		t.accept(arrival)
		frappe.flags.kt_cm_clock = None
	elif kind == "security_actions":
		pass  # an Active contract with a verified performance security of KES 100,000 (TEST-SG-01): the walk claims on it
	elif kind == "termination":
		_accepted(t, 8)
		for number, count in ((1, 6), (2, 2)):  # eight accepted and all claimed, certified and paid: the termination leaves nothing unsettled
			inv = t.claim(f"TERM-{number}", count)["invoice"]
			t.certify_invoice(inv)
			t.pay(inv, f"TERM-BANK-{number}")
	elif kind == "delivery":
		units = tw.fresh_serials(4)
		arrival = t.arrive(units)["arrival"]
		t.inspect(arrival, units)
		delivery.sign_technical_certificate(t.case, arrival=arrival, expected_version=t.version(), idempotency_key=t.key("cert"), actor=people["peter"])
		delivery.prepare_acceptance_report(t.case, arrivals=[arrival], expected_version=t.version(), idempotency_key=t.key("prepare"), actor=people["julia"])
		out["units"] = units
	else:
		delivery.record_arrival(t.case, expected_version=t.version(), idempotency_key=t.key("perform"), actor=people["grace"], received_at="2027-07-26 14:00:00", destination="Afya House training room",
			items=[{"line_id": "L2", "quantity": 1, "units": ["TRAIN-01"]}])
	frappe.db.commit()
	frappe.flags.kt_contract_source_providers = None
	return out


def build() -> dict:
	_guard()
	frappe.set_user("Administrator")
	frappe.flags.kt_cm_fixture_namespace = NAMESPACE
	frappe.conf.kt_cm_simulation_environment = 1  # in this process; the web server reads the site's own flag (the test copy already carries the platform's)
	_use_canonical_people()
	previous = test_clock.current_instant()
	test_clock.set_instant(tw.CLOCK)  # the live pages run on the seed world's own timeline (2027): the supplier's people are in force from March 2027, the award's signing window ends in July
	world.build()
	world.ensure_workflow()
	people = tw.build(NAMESPACE)
	people["david"] = DAVID
	for address in set(people.values()):
		if frappe.db.exists("User", address):
			update_password(address, PASSWORD)
	frappe.db.commit()
	package = {**sources.award_package(), "award_case": AWARD_CASE}  # its own Award case, so the service tests (which receive the demonstration package) never meet this world's contract
	received = formation.receive_award_package(package, handoff=sources.source_handoff(AWARD_CASE), managing_unit=tw.unit(), idempotency_key=f"receive-{CONTRACT}", actor="Administrator", contract_id=CONTRACT)
	extra = {}
	for kind, (contract_id, award_case) in EXTRA.items():
		got = formation.receive_award_package({**sources.award_package(), "award_case": award_case}, handoff=sources.source_handoff(award_case), managing_unit=tw.unit(), idempotency_key=f"receive-{contract_id}",
			actor="Administrator", contract_id=contract_id)
		extra[kind] = got["contract"]
	frappe.db.commit()
	staged = {kind: _stage(kind, contract_id, award_case, people) for kind, (contract_id, award_case) in STAGED.items()}
	receipt = world.fixed_asset_receipt("EXTUI", 4)  # the units of an existing contract that were already received and invoiced before management starts
	invoice = adapter.invoice_receipt(receipt, world.identity("invoice extui", "Native invoice"), bill_no="EXT-UI-INV", qty=4)
	frappe.db.commit()
	from kentender_contracts.services import reporting

	frappe.flags.kt_cm_clock = "2027-08-01 09:00:00"  # the July progress report, generated once July has ended (the live pages run on the world's own clock)
	made = reporting.generate("Progress", period_start="2027-07-01", idempotency_key="ui-world-july-report", actor=people["charles"])
	frappe.flags.kt_cm_clock = None
	report_contract = reporting.sources(reporting.get(made["report"]))["cases"][0]["case"] if made["state"] == "Draft" and made["rows"] else ""
	frappe.db.commit()
	data = {"previous_instant": str(previous or ""), "report": made["report"], "report_state": made["state"], "report_contract": report_contract, "password": PASSWORD, "contract": received["contract"], "people": people, "supplier": world.SUPPLIER, "item": world.ITEM_FA, "location": world.LOCATION, "bank": world.BANK_ACCOUNT,
		"mode": world.MODE, "unit": tw.unit(), "security_contract": extra["security"], "outside_contract": extra["outside"], "ending_contract": extra["ending"], "delivery_contract": staged["delivery"]["contract"], "delivery_units": staged["delivery"]["units"], "service_contract": staged["service"]["contract"], "advance_contract": staged["advance"]["contract"], "payments_contract": staged["payments"]["contract"], "claims_contract": staged["claims"]["contract"], "changes_contract": staged["changes"]["contract"], "warranty_contract": staged["warranty"]["contract"], "warranty_units": staged["warranty"]["units"],
		"warranty_return": staged["warranty"]["native_return"], "delay_contract": staged["delay"]["contract"], "security_contract_actions": staged["security_actions"]["contract"], "termination_contract": staged["termination"]["contract"], "closeout_contract": staged["closeout"]["contract"], "existing": {"reference": EXISTING_REFERENCE, "receipt": receipt, "invoice": invoice,
		"country": tw.REGISTRATION[0], "registration": "PVT-9X7K2M"}}
	output().parent.mkdir(parents=True, exist_ok=True)
	output().write_text(json.dumps(data, indent=1))
	print(json.dumps(data))
	return data


def clean() -> dict:
	_guard()
	_use_canonical_people()
	frappe.set_user("Administrator")
	cases = frappe.get_all("Contract Case", filters={"contract_id": ["in", [CONTRACT, *(c for c, _a in EXTRA.values()), *(c for c, _a in STAGED.values())]]}, pluck="name") + frappe.get_all("Contract Case", filters={"source_reference": EXISTING_REFERENCE}, pluck="name")
	for case in cases:
		for doctype in records.DOCTYPES:
			if doctype in ("Contract Case", "Contract Simulated Signature", "Contract Simulated Funding") or not frappe.get_meta(doctype).has_field("contract_case"):
				continue
			frappe.db.delete(doctype, {"contract_case": case})
		frappe.db.delete("Contract Simulated Funding", {"contract": case})
		frappe.db.delete("Contract Case", {"name": case})
	frappe.db.delete("Contract Report", {"fixture_namespace": NAMESPACE})  # the generated reports belong to no one contract
	frappe.db.delete("Contract Command Journal", {"fixture_namespace": NAMESPACE})
	frappe.db.delete("Contract Simulated Signature", {"signer": ["in", list(_addresses().values())]})
	for name in frappe.get_all("File", filters={"file_name": ["like", "cm-ui-%"]}, pluck="name"):  # the evidence files the walk uploaded
		frappe.delete_doc("File", name, force=True, ignore_permissions=True)
	frappe.db.delete("Contract Command Journal", {"contract_case": ["in", cases]}) if cases else None
	frappe.db.commit()
	failed = world.teardown()
	tw.teardown(NAMESPACE)
	previous = json.loads(output().read_text()).get("previous_instant") if output().exists() else ""
	test_clock.set_instant(previous or None)
	if output().exists():
		output().unlink()
	frappe.db.commit()
	print(json.dumps({"cases": cases, "native_not_removed": failed}))
	return {"cases": cases, "native_not_removed": failed}
