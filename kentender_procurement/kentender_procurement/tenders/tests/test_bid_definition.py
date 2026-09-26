# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.5.4 / §7.2 `BuildPublishedBidDefinition` (plan D25):
the Tender Version's `TenderVersionProjection v1` compiles through the
shared STD compiler (never a Tender-local builder), carries every §4.5.4
field with the four EVG groups, maps every technical requirement to one
response, evaluation and contract destination, is deterministic, and its
component digests reconcile between submission and publication.
TPR09-AC-083..096, TPR11-AC-007, TPR12-AC-002/003."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler.definition import DEFINITION_FIELDS
from unittest.mock import patch

from kentender_procurement.tenders.services import bid_definition, draft_commands as cmd, lifecycle, publication
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample


class TestBidDefinition(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_all()
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.flags.kt_tenders_clock = "2027-04-20 10:00:00"
		self.addCleanup(setattr, frappe.flags, "kt_tenders_clock", None)

	def _submitted(self):
		authorised = fx.authorised_handoff()
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		root = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=root.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		return root

	def _compile(self, root):
		version = frappe.get_doc("Tender Version", root.current_version)
		try:
			return version, bid_definition.compile_version(root, version)
		except TendersError as exc:
			self.fail(f"{exc.code}: {exc.detail}")

	def test_the_version_compiles_through_the_shared_compiler_with_every_field(self):
		root = self._submitted()
		version, definition = self._compile(root)
		self.assertEqual(tuple(definition), DEFINITION_FIELDS)
		self.assertEqual((definition["tender_version_id"], definition["template_release_id"], definition["publication_id"]), (version.name, version.template_release_id, bid_definition.PLACEHOLDER_PUBLICATION))
		# TPR09-AC-085/094: only the four fixed groups, or an explicit
		# not-evaluated disposition (no group) — never a fifth group
		groups = {m["evaluation_group_id"] for m in definition["evaluation_mappings"]} - {None}
		self.assertLessEqual(groups, {"EVG-ELIGIBILITY", "EVG-TECHNICAL-COMPLIANCE", "EVG-FINANCIAL", "EVG-AWARD"})
		self.assertTrue(all(m["evaluation_treatment"] for m in definition["evaluation_mappings"]))
		self.assertIn("EVG-TECHNICAL-COMPLIANCE", groups)
		published = {r["technical_requirement_id"] for r in frappe.parse_json(version.requisition_snapshot_json)["technical_requirements"]}
		sets = bid_definition.technical_mapping_sets(definition)
		for kind, ids in sets.items():
			self.assertEqual(published - ids, set(), f"{kind} mapping missing")
		# deterministic: the same recorded inputs give the same digest
		self.assertEqual(self._compile(root)[1]["definition_digest"], definition["definition_digest"])

	def test_component_digests_reconcile_from_submission_to_publication(self):
		root = self._submitted()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		version = frappe.get_doc("Tender Version", root.current_version)
		self.assertTrue(version.response_schema_digest and version.evaluation_contract_digest and version.contract_projection_digest)
		root.reload()
		lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		version.reload()
		built = bid_definition.build(frappe.get_doc("Tender", root.name), version, publication_id="TDP-TEST-001")
		self.assertEqual(built["components"], {k: version.get(k) for k in ("response_schema_digest", "evaluation_contract_digest", "contract_projection_digest")})
		self.assertEqual((built["definition"]["publication_id"], built["definition"]["package_digest"]), ("TDP-TEST-001", version.package_digest))

	def test_a_compiler_fault_part_way_through_authorisation_rolls_everything_back(self):
		"""TPR-CHG-001 v0.12 plan Phase 4 (§7.2): the Published Bid Definition
		is built and frozen inside the authorisation transaction — a fault
		after the Publication row was inserted leaves no Publication, no
		definition, no channel rows and the approved Version untouched."""
		root = self._submitted()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		root.reload()
		version = frappe.get_doc("Tender Version", root.approved_version)
		before = (version.modified, version.package_digest, version.record_version)
		counts = lambda: (frappe.db.count("Tender Publication", {"tender": root.name}), frappe.db.count("Tender Bid Definition", {"tender": root.name}), frappe.db.count("Tender Channel Confirmation", {"tender": root.name}))
		self.assertEqual(counts(), (0, 0, 0))
		with patch.object(bid_definition, "build", side_effect=frappe.ValidationError("injected compiler fault")):
			with self.assertRaises(frappe.ValidationError):
				publication.authorise_tender_publication(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		root.reload()
		version.reload()
		self.assertEqual(counts(), (0, 0, 0))
		self.assertEqual((root.overall_status, root.publication or ""), ("Approved", ""))
		self.assertEqual((version.modified, version.package_digest, version.record_version), before)
		# the same decision succeeds once the compiler is healthy, freezing one definition
		authorised = publication.authorise_tender_publication(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.assertTrue(authorised["ok"])
		self.assertEqual(counts()[:2], (1, 1))
		self.assertEqual(frappe.db.get_value("Tender Bid Definition", {"tender": root.name}, "status"), "Frozen")
