# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.5 — the canonical serializer on the §10.1 fixture:
grouping with lineage (AC-018), eleven technical rows (AC-019), six
warranty values and five acceptance checks (AC-020), absent optional
schedules (AC-021), traceable evaluation mappings (AC-022), the response
schema (§4.5.1), the contract projection (§4.5.3), determinism (AC-024) and
the internal-only boundary (§4.3)."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_templates import loader
from kentender_procurement.tenders.services import controls, digest, serializer
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.tests import fixtures as fx, sample


class SerializerCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.snapshot, self.snapshot_digest = sample.sample_snapshot()
		self.values = sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)


class TestSchedules(SerializerCase):
	def test_two_items_sharing_one_specification_render_as_one_line_with_full_lineage(self):
		lines = serializer.goods_lines(self.snapshot)
		self.assertEqual(len(lines), 1)
		line = lines[0]
		self.assertEqual((line["description"], line["quantity"], line["unit"]), ("Business laptops", "250", "Each"))
		self.assertEqual(line["source_item_ids"], "SRC-MOH-033-001, SRC-MOH-033-002")
		self.assertEqual([s["quantity"] for s in line["source_items"]], [100, 150])
		self.assertEqual([s["reservation_id"] for s in line["source_items"]], ["RES-SAMPLE-001", "RES-SAMPLE-002"])
		self.assertEqual([s["plan_source_allocation_id"] for s in line["source_items"]], ["PSA-MOH-2027-033-001", "PSA-MOH-2027-033-002"])
		self.assertEqual(len(line["technical_requirement_ids"]), 11)

	def test_the_price_schedule_never_carries_the_authorised_value(self):
		schedule = serializer.price_schedule(self.snapshot)
		self.assertEqual(len(schedule["rows"]), 1)
		row = schedule["rows"][0]
		self.assertEqual((row["unit_price"], row["line_total"], row["tax"]), (serializer.SUPPLIER, serializer.CALCULATED, serializer.SUPPLIER))
		self.assertNotIn("50,000,000", json.dumps(schedule))
		self.assertNotIn("20000000", json.dumps(schedule))

	def test_all_eleven_technical_rows_six_warranty_values_and_five_checks(self):
		rows = serializer.technical_rows(self.snapshot)
		self.assertEqual([r["technical_requirement_id"] for r in rows], [f"TECH-{i:03d}" for i in range(1, 12)])
		by_id = {r["technical_requirement_id"]: r for r in rows}
		self.assertEqual((by_id["TECH-003"]["required_value"], by_id["TECH-003"]["unit"]), ("16", "GB"))
		self.assertEqual(by_id["TECH-005"]["required_value"], "NVMe SSD")
		self.assertEqual(by_id["TECH-010"]["required_value"], "Wi-Fi 6, Bluetooth 5 or later")
		self.assertEqual(by_id["TECH-011"]["required_value"], "USB-C ×2, USB-A ×2, HDMI ×1")
		warranty = serializer.warranty_support(self.snapshot)
		self.assertEqual(warranty, {"minimum_warranty_months": "36", "onsite_support_required": True, "maximum_support_response_hours": "8", "manufacturer_support_required": True, "service_location_constraint": "Within Kenya", "support_description": "Supplier to provide escalation and warranty-contact details."})
		self.assertEqual([a["acceptance_requirement_id"] for a in serializer.acceptance_rows(self.snapshot)], [f"ACC-{i:03d}" for i in range(1, 6)])

	def test_optional_schedules_are_absent_when_their_sources_are_empty(self):
		self.assertEqual(serializer.related_services(self.snapshot), [])
		self.assertEqual(serializer.supporting_materials(self.snapshot), [])
		self.assertEqual(serializer.supplier_response_schema(self.snapshot, [])["services"], [])


class TestMappings(SerializerCase):
	def test_every_published_requirement_maps_once_into_response_evaluation_and_contract(self):
		state = controls.normalise(self.values)
		evidence = [{"evidence_requirement_id": "EV-001", "label": "Electrical compatibility certificate", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": "TECH-001", "mandatory": True, "row_order": 1}]
		schema = serializer.supplier_response_schema(self.snapshot, evidence)
		evaluation = serializer.evaluation_contract(state, self.snapshot, evidence)
		contract = serializer.contract_obligations(state, self.snapshot)
		published = [f"TECH-{i:03d}" for i in range(1, 12)]
		self.assertEqual([r["technical_requirement_id"] for r in schema["technical"]], published)
		self.assertEqual([r["technical_requirement_id"] for r in evaluation["technical_pass_fail"]], published)
		self.assertEqual([r["technical_requirement_id"] for r in contract["technical"]], published)
		self.assertTrue(schema["technical"][0]["evidence_references"]["required"])
		self.assertFalse(schema["technical"][1]["evidence_references"]["required"])
		self.assertEqual(evaluation["stages"], list(serializer.EVALUATION_STAGES))
		self.assertEqual(evaluation["hidden_criteria"], [])
		self.assertEqual(evaluation["eligibility_checklist"][0]["evidence_requirement_id"], "EV-001")
		self.assertEqual([c["required"] for c in evaluation["qualification_criteria"]], [True, True, True, True, True])
		self.assertEqual(evaluation["qualification_criteria"][3]["minimum_contracts"], 2)
		self.assertEqual([i["requisition_item_id"] for i in contract["items"]], ["SRC-MOH-033-001", "SRC-MOH-033-002"])
		self.assertEqual(contract["items"][1]["reservation_id"], "RES-SAMPLE-002")
		self.assertEqual(len(contract["acceptance"]), 5)
		self.assertEqual(contract["parameters"]["performance_security_percent"], 10)
		self.assertEqual(schema["warranty_support"]["identity"], snap.WARRANTY_ID)
		self.assertEqual(len(schema["goods"]), 1)
		self.assertEqual(schema["goods"][0]["quantity"], "250")


class TestRenderContextAndDigests(SerializerCase):
	def _pair(self, **kwargs):
		return sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS, **kwargs)

	def test_the_render_context_has_exactly_the_installed_fixture_shape(self):
		tender, version = self._pair()
		context = serializer.render_context(tender, version, snap.load(version))
		fixture = json.loads(loader.read_text("fixtures/moh_input.json"))
		self.assertEqual(set(serializer.public_context(context)), set(fixture))
		for key, value in fixture.items():
			if isinstance(value, dict):
				self.assertEqual(set(context[key]), set(value), key)
		self.assertEqual(context["tender"]["submission_deadline"], "5 June 2027, 11:00 EAT")
		self.assertEqual(context["tender"]["opening_datetime"], "5 June 2027, 11:00 EAT")
		self.assertEqual(context["tender"]["validity_date"], "3 October 2027")
		self.assertEqual(context["tender"]["tender_security"]["amount"], "500,000.00")
		self.assertEqual(context["requisition"]["authorised_quantity"], "250 Each")
		self.assertEqual(context["reservation"]["category"], "Youth")
		self.assertEqual(context["goods"][0]["quantity"], "250")
		self.assertEqual(len(context["technical_requirements"]), 11)
		self.assertEqual(context["submission"]["comparable_experience"], {"required": True, "count": "2", "period_years": "5"})

	def test_internal_context_never_reaches_a_public_key(self):
		tender, version = self._pair()
		context = serializer.render_context(tender, version, snap.load(version))
		public = json.dumps(serializer.public_context(context))
		self.assertNotIn("Strengthen interoperable", public)
		self.assertNotIn("Single year", public)
		self.assertNotIn("RES-SAMPLE", public)
		self.assertEqual(context["_internal"]["plan_horizon"], "Single year")
		self.assertEqual(context["_internal"]["authorised_value"], 50000000.0)

	def test_digests_are_deterministic_across_reloads(self):
		tender, version = self._pair()
		first = serializer.package_digest(tender, version, snap.load(version))
		reloaded = frappe.get_doc("Tender Version", version.name)
		second = serializer.package_digest(frappe.get_doc("Tender", tender.name), reloaded, snap.load(reloaded))
		self.assertEqual(first, second)
		generated = serializer.generated_digests(serializer.officer_state(version), snap.load(version), [])
		self.assertEqual(set(generated), {"response_schema_digest", "evaluation_contract_digest", "contract_projection_digest"})
		self.assertEqual(snap.recompute_digest(snap.load(reloaded)), reloaded.requisition_snapshot_digest)
		self.assertEqual(len(digest.sha256_hex({"a": 1})), 64)


class TestControls(IntegrationTestCase):
	def test_defaults_and_task_vocabulary(self):
		snapshot, _ = sample.sample_snapshot()
		defaults = controls.defaults(snapshot)
		self.assertEqual(defaults["tender_validity_days"], 120)
		self.assertEqual(defaults["tender_title"], snapshot["requirement_title"])
		self.assertTrue(defaults["after_sales_evidence_required"])
		state = controls.normalise(defaults)
		self.assertEqual(controls.task_status(state, controls.TASK_DETAILS, baseline=defaults), "Needs attention")
		self.assertEqual(controls.task_status(state, controls.TASK_REQUIREMENTS, baseline=defaults), "Not started")
		state["past_experience_required"] = True
		self.assertEqual(controls.task_status(state, controls.TASK_REQUIREMENTS, baseline=defaults), "Needs attention")
		complete = controls.normalise(sample.officer_values(inspection_location="x", contact_office="y"))
		self.assertEqual(controls.task_status(complete, controls.TASK_REQUIREMENTS, baseline=defaults), "Complete")

	def test_validate_rejects_inherited_unknown_hidden_and_out_of_range(self):
		from kentender_procurement.tenders.services.errors import TendersError

		with self.assertRaises(TendersError) as ctx:
			controls.validate({"quantity": 5}, {})
		self.assertEqual(ctx.exception.code, "TND_INHERITED_EDIT")
		clean, errors = controls.validate({"nonsense": 1, "tender_validity_days": 400, "meeting_mode": "Physical", "minimum_comparable_contracts": 0, "tender_security_amount": "500000.005"}, {"pre_tender_meeting": False})
		self.assertEqual(set(errors), {"nonsense", "tender_validity_days", "meeting_mode", "minimum_comparable_contracts", "tender_security_amount"})
		self.assertEqual(clean, {})
		clean, errors = controls.validate({"past_experience_required": True, "minimum_comparable_contracts": "7", "experience_period_years": 12}, {})
		self.assertEqual(errors, {})
		self.assertEqual((clean["minimum_comparable_contracts"], clean["experience_period_years"]), (7, 12))

	def test_missing_reports_only_applicable_required_fields(self):
		state = controls.normalise({"pre_tender_meeting": False})
		fields = {f for _t, f, _l in controls.missing(state)}
		self.assertIn("tender_title", fields)
		self.assertNotIn("meeting_datetime", fields)
		state = controls.normalise({"pre_tender_meeting": True, "meeting_mode": "Online"})
		fields = {f for _t, f, _l in controls.missing(state)}
		self.assertIn("online_joining_information", fields)
		self.assertNotIn("meeting_venue", fields)
