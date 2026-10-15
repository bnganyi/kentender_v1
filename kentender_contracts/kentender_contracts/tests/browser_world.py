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

from kentender_contracts.services import formation, records
from kentender_core.services import test_clock
from kentender_contracts.simulation import sources
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw

TEST_SITE = "kentender-test.local"
PASSWORD = "CmWalk-2027-Aa1!"
CONTRACT = "CM-UI-0001"
AWARD_CASE = "CM-UI-AWD-01"
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
	frappe.db.commit()
	data = {"previous_instant": str(previous or ""), "password": PASSWORD, "contract": received["contract"], "people": people, "supplier": world.SUPPLIER, "item": world.ITEM_FA, "location": world.LOCATION, "bank": world.BANK_ACCOUNT,
		"mode": world.MODE, "unit": tw.unit()}
	output().parent.mkdir(parents=True, exist_ok=True)
	output().write_text(json.dumps(data, indent=1))
	print(json.dumps(data))
	return data


def clean() -> dict:
	_guard()
	_use_canonical_people()
	frappe.set_user("Administrator")
	cases = frappe.get_all("Contract Case", filters={"contract_id": CONTRACT}, pluck="name")
	for case in cases:
		for doctype in records.DOCTYPES:
			if doctype in ("Contract Case", "Contract Simulated Signature", "Contract Simulated Funding") or not frappe.get_meta(doctype).has_field("contract_case"):
				continue
			frappe.db.delete(doctype, {"contract_case": case})
		frappe.db.delete("Contract Simulated Funding", {"contract": case})
		frappe.db.delete("Contract Case", {"name": case})
	frappe.db.delete("Contract Simulated Signature", {"signer": ["in", list(_addresses().values())]})
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
