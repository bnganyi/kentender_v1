"""AUTH-ADR-001 v1.6 §4.4 — the code-owned business-role registry.

Administrators assign registered responsibilities; they do not define new
roles, scope types or capability strings in production. These tests hold the
registry to the shape §4.4 requires: exactly two scope types, no technical
role registered, no retired role resurrected.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_business_role_registry
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import business_role_registry as registry
from kentender_core.services.responsibility_errors import ResponsibilityError


class TestBusinessRoleRegistry(IntegrationTestCase):
	def test_exactly_three_scope_types_exist(self):
		"""§4.4 — `Site-wide` or `Organisation Unit`; and `Tender`, added on 10 October
		2026 for the tender-security intake duty alone. No other value exists."""
		self.assertEqual(registry.SCOPE_TYPES, ("Site-wide", "Organisation Unit", "Tender"))
		self.assertEqual(registry.roles_with_scope_type(registry.SCOPE_TENDER), ("Tender Security Intake Officer",))
		for name, entry in registry.REGISTRY.items():
			self.assertIn(entry.scope_type, registry.SCOPE_TYPES, f"{name} has no valid scope type")

	def test_scope_type_decides_whether_the_record_names_a_unit(self):
		"""§4.5 — OU required for OU roles, prohibited for Site-wide roles."""
		for entry in registry.REGISTRY.values():
			self.assertEqual(
				entry.requires_organisation_unit, entry.scope_type == registry.SCOPE_OU
			)

	def test_no_procuring_entity_or_global_dimension_survives(self):
		"""§1.1 — the Global and Procuring Entity scope types are removed."""
		self.assertFalse(hasattr(registry, "SCOPE_GLOBAL"))
		self.assertFalse(hasattr(registry, "SCOPE_PE"))
		for entry in registry.REGISTRY.values():
			self.assertFalse(hasattr(entry, "requires_procuring_entity"))

	def test_the_departmental_responsibilities_are_the_organisation_unit_ones(self):
		"""§4.4 — Requisition Preparer stays unregistered until REQ-CHG-001's
		cutover slice names it (KT-STD-001 §7 default-to-omit)."""
		self.assertEqual(
			registry.roles_with_scope_type(registry.SCOPE_OU),
			(
				"Contract coordination",  # CM-CHG-001 v0.8 §6.2
				"Contract preparation",  # CM-CHG-001 v0.8 §6.2
				"Departmental Author",
				"Head of User Department",
				"Receiving",  # CM-CHG-001 v0.8 §6.2
			),
		)

	def test_the_contract_management_responsibilities_use_existing_scope_types_only(self):
		"""CM-CHG-001 v0.8 §6, §6.2, plan D11: three Organisation Unit, five Site-wide, no Contract scope type, each its own Frappe role."""
		ou = ("Contract preparation", "Contract coordination", "Receiving")
		site = ("Contract inspection", "Technical certification", "Entity contract signing", "Finance preparation", "Finance approval")
		for name in ou:
			self.assertEqual(registry.scope_type(name), registry.SCOPE_OU, name)
		for name in site:
			self.assertEqual(registry.scope_type(name), registry.SCOPE_SITE, name)
		for name in ou + site:
			self.assertEqual(registry.projected_frappe_roles(name), (name,), name)
			self.assertEqual(registry.REGISTRY[name].owning_document, "CM-CHG-001 v0.10 §6")
		self.assertEqual(registry.SCOPE_TYPES, ("Site-wide", "Organisation Unit", "Tender"))
		self.assertEqual(registry.roles_with_sod_tag("payment_approval"), ("Finance approval",))
		self.assertEqual(registry.roles_with_sod_tag("payment_preparation"), ("Finance preparation",))

	def test_the_eight_contract_management_bindings_are_exactly_those_of_auth_4_4a(self):
		"""AUTH-ADR-001 v1.16 §4.4A / AUTH-AC-059: the eight responsibilities, with their scopes, reuse the existing registry. Nothing is aliased, no Contract scope or user-year grant exists, and the Tender scope is
		left to the Tender roles."""
		bound = {"Contract preparation": registry.SCOPE_OU, "Contract coordination": registry.SCOPE_OU, "Receiving": registry.SCOPE_OU, "Contract inspection": registry.SCOPE_SITE,
			"Technical certification": registry.SCOPE_SITE, "Entity contract signing": registry.SCOPE_SITE, "Finance preparation": registry.SCOPE_SITE, "Finance approval": registry.SCOPE_SITE}
		for name, scope in bound.items():
			self.assertEqual(registry.scope_type(name), scope, name)
		tender_scoped = set(registry.roles_with_scope_type(registry.SCOPE_TENDER))
		self.assertFalse(tender_scoped & set(bound), "none of the eight uses the Tender scope")
		self.assertNotIn("Contract", registry.SCOPE_TYPES)

	def test_budget_and_contract_management_capacities_stay_distinct(self):
		"""AUTH-AC-060/061: Finance approval (Contract Management) confirms a funding basis; the Planning-only Finance Confirmation Officer does not hold it, and neither Budget Officer nor Budget Approver is a Contract
		Management capacity. The independence of the Budget Approver from the preparer and the confirmers is a check on actual participation, tested where the entry is decided."""
		self.assertNotEqual(registry.projected_frappe_roles("Finance Confirmation Officer"), registry.projected_frappe_roles("Finance approval"))
		self.assertEqual(registry.roles_with_sod_tag("finance_confirmation"), ("Finance Confirmation Officer",))
		for budget_role in ("Budget Officer", "Budget Approver"):
			self.assertNotIn(budget_role, ("Finance preparation", "Finance approval"))
			self.assertNotIn("Finance approval", registry.projected_frappe_roles(budget_role))
			self.assertNotIn("Finance preparation", registry.projected_frappe_roles(budget_role))

	def test_reference_data_manager_is_removed(self):
		"""CFG-CHG-002 v0.6 §1.1 — no Reference Data Manager role exists."""
		self.assertNotIn("Reference Data Manager", registry.REGISTRY)

	def test_no_registered_role_declares_an_exclusive_office_yet(self):
		"""§4.7's mechanism exists in the administration service, but the
		KT-STD-001 §8.3 seed places two simultaneous HoUD holders in the same
		unit (Peter + Grace's Cartesian fixture) and ADR §16 marks the
		AUTH-DES-05 conflict as artboard-only — so no entry may declare the
		flag until an owning module document does (tracker D4)."""
		for name, entry in registry.REGISTRY.items():
			self.assertFalse(entry.exclusive_office, f"{name} declares an undocumented exclusive office")

	def test_head_of_procurement_function_is_registered_site_wide(self):
		"""REQ-CHG-001 v1.6 §8 (2026-09-06) — Requisitions' cutover slice
		registers the office that authorises Requisitions and, later, approves
		Tenders. Not Procurement Planner (KT-STD-001 §8.3)."""
		entry = registry.REGISTRY["Head of Procurement Function"]
		self.assertEqual(entry.scope_type, registry.SCOPE_SITE)
		self.assertEqual(entry.owning_document, "REQ-CHG-001 v1.6 §8")
		self.assertIn("Head of Procurement Function", registry.roles_with_scope_type(registry.SCOPE_SITE))

	def test_evaluation_technical_support_is_registered_site_wide(self):
		"""KT-STD-001 v1.13 §8.3 and EVL-CHG-001 v0.4 §9.1 — the holder of Bid
		Evaluation's technical issues, separate from the Technical Operator
		(Project Owner, 1 Oct 2026: "Own responsibility")."""
		entry = registry.REGISTRY["Evaluation Technical Support"]
		self.assertEqual(entry.scope_type, registry.SCOPE_SITE)
		self.assertIn("KT-STD-001 v1.13", entry.owning_document)
		self.assertEqual(entry.frappe_roles, ("Evaluation Technical Support",))

	def test_procurement_officer_is_registered_site_wide(self):
		"""TPR-CHG-001 v0.8 §6 — Procurement Officer is Site-wide, owned by TPR,
		and carries the tender_preparation segregation tag; the approving
		office carries tender_approval (plus channel_confirmation and
		addendum_issue) on the same single HoPF entry, and the Accounting
		Officer carries publication_authorisation and tender_cancellation."""
		entry = registry.REGISTRY["Procurement Officer"]
		self.assertEqual(entry.scope_type, registry.SCOPE_SITE)
		self.assertIn("TPR-CHG-001", entry.owning_document)
		self.assertIn("tender_preparation", entry.sod_tags)
		self.assertIn("Procurement Officer", registry.roles_with_sod_tag("tender_preparation"))
		self.assertIn("Head of Procurement Function", registry.roles_with_sod_tag("tender_approval"))
		self.assertEqual(registry.roles_with_sod_tag("tender_approval"), ("Head of Procurement Function",))
		self.assertEqual(registry.roles_with_sod_tag("channel_confirmation"), ("Head of Procurement Function",))
		self.assertEqual(registry.roles_with_sod_tag("addendum_issue"), ("Head of Procurement Function",))
		self.assertEqual(registry.roles_with_sod_tag("publication_authorisation"), ("Accounting Officer",))
		self.assertEqual(registry.roles_with_sod_tag("tender_cancellation"), ("Accounting Officer",))

	def test_requisition_preparer_remains_unregistered(self):
		"""KT-STD-001 §7 default-to-omit — illustrative in ADR §4.4, but
		REQ-CHG-001 v1.6 uses Departmental Author instead and never registers
		it; no other approved module names it either."""
		self.assertNotIn("Requisition Preparer", registry.REGISTRY)

	def test_every_entry_names_the_document_that_owns_its_role_name(self):
		"""§4.4 — the module document is the source of the exact role name."""
		for name, entry in registry.REGISTRY.items():
			self.assertTrue(entry.owning_document, f"{name} does not name its owning document")

	def test_administrator_and_system_manager_are_not_business_responsibilities(self):
		"""§4.4/§8 — technical inspection is not a business assignment."""
		self.assertNotIn("Administrator", registry.REGISTRY)
		self.assertNotIn("System Manager", registry.REGISTRY)
		self.assertEqual(registry.TECHNICAL_ROLES, frozenset({"Administrator", "System Manager"}))

	def test_one_auditor_label_serves_every_module(self):
		"""NDS, Budget and PLN v1.12 all name `Auditor`; the earlier
		`Planning Auditor` label is retired (PLN tracker D6)."""
		self.assertIn("Auditor", registry.REGISTRY)
		self.assertNotIn("Planning Auditor", registry.REGISTRY)
		self.assertEqual(registry.scope_type("Finance Confirmation Officer"), registry.SCOPE_SITE)
		self.assertNotIn("finance_confirmation", registry.REGISTRY["Budget Officer"].sod_tags)

	def test_strategy_roles_are_site_wide(self):
		"""§20 — Strategy Author and Approver bind to Site-wide scope."""
		self.assertEqual(registry.scope_type("Strategy Author"), registry.SCOPE_SITE)
		self.assertEqual(registry.scope_type("Strategy Approver"), registry.SCOPE_SITE)

	def test_an_unregistered_role_is_refused_with_the_configuration_code(self):
		with self.assertRaises(ResponsibilityError) as caught:
			registry.require_registered("Applicable Final Authority")
		self.assertEqual(caught.exception.code, "AUTH_CONFIGURATION_INVALID")

	def test_every_projection_role_exists_after_ensure_roles(self):
		registry.ensure_roles()
		for role in registry.all_projected_frappe_roles():
			self.assertTrue(frappe.db.exists("Role", role), f"Role {role} was not provisioned")

	def test_system_manager_may_administer_every_registered_role_except_the_tender_duty(self):
		for name, entry in registry.REGISTRY.items():
			self.assertEqual(registry.may_administer(name, {"System Manager"}), entry.system_setup_assignable, name)
			self.assertFalse(registry.may_administer(name, {"Desk User"}))

	def test_only_the_head_of_procurement_function_assigns_the_tender_security_intake_duty(self):
		"""Project Owner, 10 October 2026: the HOPF assigns the duty, and neither its default
		bundle nor System Manager status carries it."""
		duty = registry.REGISTRY["Tender Security Intake Officer"]
		self.assertTrue(registry.may_administer(duty.business_role, {"Head of Procurement Function"}))
		self.assertFalse(registry.may_administer(duty.business_role, {"System Manager"}))
		self.assertNotIn("tender_security_receipt", registry.REGISTRY["Head of Procurement Function"].sod_tags)
		self.assertEqual(duty.sod_tags, ("tender_security_receipt",))
		self.assertFalse(duty.technical_holder)

	def test_the_head_of_procurement_function_signs_the_annual_plan_preparation(self):
		"""PLN-CHG-001 v1.18 §6.2 / plan D6 — Sign and submit Annual Plan is
		the Head of Procurement Function's preparation accountability; the
		Planner keeps consolidation and never inherits the signature tag."""
		self.assertIn("plan_preparation_signature", registry.REGISTRY["Head of Procurement Function"].sod_tags)
		self.assertNotIn("plan_preparation_signature", registry.REGISTRY["Procurement Planner"].sod_tags)
		self.assertEqual(registry.REGISTRY["Head of Procurement Function"].scope_type, registry.SCOPE_SITE)
