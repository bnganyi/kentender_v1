# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.1/§7.3/§7.4 — snapshot immutability and lineage,
evidence-row generation, and the Tender reference (TPR-AC-004/007/018)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_preparation.services import evidence, references
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestSnapshot(TenderCase):
	def test_every_inherited_row_keeps_its_requisition_id_and_value(self):
		handoff = fx.authorised_handoff()
		payload = json.loads(frappe.get_doc("Authorised Requisition Handoff", handoff).payload_json)
		prep = fx.prepared(handoff)
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		snapshot = snap.load(version)
		for key in ("items", "technical_requirements", "related_services", "acceptance_requirements", "supporting_materials", "drawdown_lines"):
			self.assertEqual(snapshot[key], payload[key], key)
		self.assertEqual(snapshot["handoff_digest"], payload["handoff_digest"])
		self.assertEqual(snap.recompute_digest(snapshot), version.snapshot_digest)
		visible = snap.visible_ids(snapshot)
		self.assertEqual(visible["Equipment item"], {r["requisition_item_id"] for r in payload["items"]})
		self.assertEqual(visible["Technical requirement"], {r["technical_requirement_id"] for r in payload["technical_requirements"]})

	def test_internal_context_is_separated_from_the_public_snapshot_keys(self):
		prep = fx.prepared()
		snapshot = snap.load(frappe.get_doc("Tender Preparation Version", prep["tender_version"]))
		internal = snap.internal_context(snapshot)
		self.assertEqual(set(internal), set(snap.INTERNAL_ONLY_KEYS))


class TestEvidenceGeneration(TenderCase):
	def test_generated_rows_follow_the_switches_and_link_to_visible_ids(self):
		prep = fx.prepared()
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		snapshot = snap.load(version)
		state = {"manufacturer_authorisation_required": True, "datasheets_required": True, "after_sales_evidence_required": False}
		rows = evidence.generated_rows(state, snapshot)
		tech_count = len(snapshot["technical_requirements"])
		item_count = len(snapshot["items"])
		self.assertEqual(len([r for r in rows if r["source"] == evidence.SOURCE_FIXED]), item_count)  # warranty confirmation
		self.assertEqual(len([r for r in rows if "Datasheet" in r["evidence_label"]]), tech_count)
		visible = snap.visible_ids(snapshot)
		for row in rows:
			self.assertIn(row["linked_requirement_id"], visible[row["linked_requirement_type"]])
		self.assertEqual(len(evidence.generated_rows({**state, "manufacturer_authorisation_required": False, "datasheets_required": False}, snapshot)), item_count)

	def test_no_row_creates_a_hidden_criterion(self):
		"""TPR-AC-018 — every row has a published label and a published link."""
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		for row in evidence.rows_as_dicts(version):
			self.assertTrue(row["evidence_label"] and row["linked_requirement_id"] and row["linked_requirement_type"])


class TestReferences(TenderCase):
	def test_reference_is_derived_from_the_plan_item_and_site(self):
		base = references.base_reference(plan_item_id="PPI-MOH-2027-033")
		self.assertTrue(base.endswith("-2027-033"))
		self.assertTrue(base.startswith("TND-"))

	def test_a_second_tender_on_the_same_plan_item_gets_a_suffix(self):
		prep = fx.prepared()
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		self.assertEqual(references.tender_reference(plan_item_id=root.plan_item_id), f"{root.tender_reference}-2")
