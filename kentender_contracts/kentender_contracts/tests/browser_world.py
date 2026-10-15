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
STAGED = {"delivery": ("CM-UI-0005", "CM-UI-AWD-05"), "service": ("CM-UI-0006", "CM-UI-AWD-06-SVC")}
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


def _stage(kind: str, contract_id: str, award_case: str, people: dict[str, str]) -> dict:
	"""An Active contract with its inspectors appointed and declared, taken to the step the delivery spec starts from."""
	from kentender_contracts.services import delivery

	t = tw.Thread(people, tag=f"UI{contract_id[-4:]}", contract_id=contract_id, services=award_case.endswith("-SVC"), award_case=award_case)
	t.active()
	t.appointed("Accounting Officer decides" if kind == "delivery" else "Committee accepts")
	out = {"contract": t.case}
	if kind == "delivery":
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
	data = {"previous_instant": str(previous or ""), "password": PASSWORD, "contract": received["contract"], "people": people, "supplier": world.SUPPLIER, "item": world.ITEM_FA, "location": world.LOCATION, "bank": world.BANK_ACCOUNT,
		"mode": world.MODE, "unit": tw.unit(), "security_contract": extra["security"], "outside_contract": extra["outside"], "ending_contract": extra["ending"], "delivery_contract": staged["delivery"]["contract"], "delivery_units": staged["delivery"]["units"], "service_contract": staged["service"]["contract"], "existing": {"reference": EXISTING_REFERENCE, "receipt": receipt, "invoice": invoice,
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
