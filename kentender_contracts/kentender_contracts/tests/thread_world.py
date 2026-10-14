# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The people and the sources of the ordinary thread, for tests (plan D18, Phase 4; development only, never package acceptance).

Eleven people with the responsibilities the boards give them, a supplier-accounts stand-in that knows the supplier's signatory and representative, the synthetic source
provider and the clock the boards are read at (2 July 2027). Built once per test class on top of `native_world` and removed at its end. Nothing here runs on the dev site."""

from __future__ import annotations

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
	"peter": ("Peter Mugo", ["Contract inspection", "Technical certification"]),
	"grace": ("Grace Wanjiku", ["Receiving"]),
	"josphat": ("Josphat Mwangi", ["Finance preparation"]),
	"beatrice": ("Beatrice Kamau", ["Finance approval"]),
	"daniel": ("Daniel Otieno", ["Technical Operator"]),
	"mary": ("Mary Wanjiku", []),
	"david": ("David Otieno", []),
}
CLOCK = "2027-07-02 09:00:00"


def email(persona: str) -> str:
	return sources.SUPPLIER_SIGNATORY if persona == "mary" else sources.ENTITY_SIGNATORY if persona == "amina" else f"cm.thread.{persona}@{DOMAIN}"


class Suppliers:
	"""Supplier Accounts as the audience and parties code asks it: one organisation, its authorised signatory and its representative."""

	def __init__(self, organisation: str = "ORG-DEMO-1"):
		self.organisation = organisation

	def _row(self, user: str, responsibility: str) -> dict:
		return {"assignment_id": f"A-{user}", "organisation_id": self.organisation, "user": user, "responsibility": responsibility, "active": True, "signatory_ready": responsibility == "Authorised Signatory"}

	def active_assignments(self, *, user, at=None):
		return [self._row(user, "Authorised Signatory" if user == email("mary") else "Supplier Representative")] if user in (email("mary"), email("david")) else []

	def organisation_signatories(self, *, organisation_id, at=None):
		return [self._row(email("mary"), "Authorised Signatory")] if organisation_id == self.organisation else []

	def organisation_people(self, *, organisation_id, at=None):
		return [self._row(email("mary"), "Authorised Signatory"), self._row(email("david"), "Supplier Representative")] if organisation_id == self.organisation else []


def unit() -> str:
	return frappe.get_all("Organisation Unit", pluck="name", limit=1)[0]


def build() -> dict[str, str]:
	"""Create the people and grant their responsibilities (idempotent). Returns persona -> email."""
	registry.ensure_roles()
	out = {}
	for persona, (name, roles) in PEOPLE.items():
		address = email(persona)
		if not frappe.db.exists("User", address):
			frappe.get_doc({"doctype": "User", "email": address, "first_name": name.split()[0], "last_name": name.split()[-1], "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True).add_roles("Desk User")
		out[persona] = address
		for role in roles:
			if role == "Technical Operator" and registry.REGISTRY[role].technical_holder:
				pass
			administration.grant(user=address, business_role=role, organisation_unit=unit() if registry.REGISTRY[role].requires_organisation_unit else "", actor="Administrator")
	# the Finance people also need the native roles the Payment Entry workflow names
	for persona, roles in (("josphat", ["Accounts User", "Purchase User", "Stock User", "Item Manager"]), ("beatrice", ["Accounts Manager", "Purchase Manager", "Stock Manager"])):
		frappe.get_doc("User", out[persona]).add_roles(*roles)
	frappe.db.commit()
	return out


def teardown() -> None:
	for persona in PEOPLE:
		address = email(persona)
		for name in frappe.get_all("User Responsibility Assignment", filters={"user": address}, pluck="name"):
			purge_doc("User Responsibility Assignment", name)
		if frappe.db.exists("User", address) and address not in (sources.SUPPLIER_SIGNATORY, sources.ENTITY_SIGNATORY):
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


def package_particulars(people: dict[str, str]) -> dict:
	return {"agreement_date": "2027-07-02", "entity_signatory": people["amina"], "item_mapping": {"L1": world.ITEM_FA}, "native_supplier": world.SUPPLIER}


def receive(people: dict[str, str], *, contract_id: str = "CM-TEST-0001") -> dict:
	from kentender_contracts.services import formation

	package = sources.award_package()
	return formation.receive_award_package(package, handoff=sources.source_handoff(package["award_case"]), managing_unit=unit(), idempotency_key=f"receive-{contract_id}", actor="Administrator", contract_id=contract_id)


def purge_native_operation_rows(case_ids: list[str]) -> None:
	records.wipe("CM_TEST")
