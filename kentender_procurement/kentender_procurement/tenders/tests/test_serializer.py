# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.5 — the canonical serializer on the §10.1 fixture:
grouping with lineage (AC-018), eleven technical rows (AC-019), six
warranty values and five acceptance checks (AC-020), absent optional
schedules (AC-021), determinism (AC-024) and the internal-only boundary
(§4.3). The response schema, evaluation mappings and contract projection
(§4.5.1–4.5.3, AC-022) come from the compiled Published Bid Definition
(`bid_definition`, plan D25), never from this module."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.compiler import projection as std_projection
from kentender_procurement.std_templates.services import installer as std_installer
from kentender_procurement.std_templates.services import runtime as std_runtime
from kentender_procurement.tenders.services import bid_definition, controls, digest, serializer
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

	def test_the_goods_schedule_reconciles_exactly_to_the_inherited_items(self):
		"""RG-24 / AUD-XC-117 — the comparison is exact decimal arithmetic: float noise cannot fail a schedule that
		reconciles, and a difference far below the old 1e-6 epsilon cannot hide one that does not."""
		from kentender_procurement.tenders.services import review

		snapshot = {**self.snapshot, "items": [{**self.snapshot["items"][0], "quantity": "1000000.00000001"}, {**self.snapshot["items"][1], "quantity": "0.1"}, {**self.snapshot["items"][1], "requisition_item_id": "SRC-X-3", "quantity": "0.2"}]}
		lines = serializer.goods_lines(snapshot)
		self.assertTrue(review.goods_schedule_reconciles(snapshot, lines))
		drifted = [{**line, "source_items": [{**s, "quantity": "1000000.00000002"} if s["requisition_item_id"] == snapshot["items"][0]["requisition_item_id"] else s for s in line["source_items"]]} for line in lines]
		self.assertFalse(review.goods_schedule_reconciles(snapshot, drifted))
		self.assertFalse(review.goods_schedule_reconciles(snapshot, []))

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
		self.assertEqual(by_id["TECH-010"]["required_value"], "Wi-Fi 6 and Bluetooth 5 or later")
		self.assertEqual(by_id["TECH-011"]["required_value"], "USB-C ×2; USB-A ×2; HDMI ×1")
		warranty = serializer.warranty_support(self.snapshot)
		self.assertEqual(warranty, {"minimum_warranty_months": "36", "onsite_support_required": True, "maximum_support_response_hours": "8", "manufacturer_support_required": True, "service_location_constraint": "Within Kenya", "support_description": "Supplier to provide escalation and warranty-contact details."})
		self.assertEqual([a["acceptance_requirement_id"] for a in serializer.acceptance_rows(self.snapshot)], [f"ACC-{i:03d}" for i in range(1, 6)])

	def test_optional_schedules_are_absent_when_their_sources_are_empty(self):
		self.assertEqual(serializer.related_services(self.snapshot), [])
		self.assertEqual(serializer.supporting_materials(self.snapshot), [])


class TestMappings(SerializerCase):
	def test_every_published_requirement_maps_once_into_response_evaluation_and_contract(self):
		evidence = [{"label": "Electrical compatibility certificate", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": "TECH-001", "mandatory": True}]
		tender, version = sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS, evidence=evidence)
		definition = bid_definition.compile_version(tender, version)
		published = {f"TECH-{i:03d}" for i in range(1, 12)}
		for kind, ids in bid_definition.technical_mapping_sets(definition).items():
			self.assertEqual(ids, published, kind)
		goods = {r["group_key"] for r in definition["response_rows"] if r["identity"]["source_family"] == "goods"}
		self.assertEqual(len(goods), 1)  # two items sharing one specification = one supplier line
		self.assertFalse([r for r in definition["response_rows"] if r["identity"]["source_family"] == "related_service"])  # AC-021
		self.assertIn("EVG-TECHNICAL-COMPLIANCE", {m["evaluation_group_id"] for m in definition["evaluation_mappings"]})


class TestRenderContextAndDigests(SerializerCase):
	def _pair(self, **kwargs):
		return sample.insert_tender_with_version(values=self.values, fixture_namespace=fx.NS, **kwargs)

	def test_the_render_context_carries_every_key_the_installed_release_consumes(self):
		tender, version = self._pair()
		context = serializer.render_context(tender, version, snap.load(version))
		# The context the installed release's masters consume for its MoH fixture.
		release = std_runtime.release_doc(version.template_release_id)
		projection = json.loads((std_installer.DEFAULT_PACKAGE / "04_fixture/moh_input.json").read_text(encoding="utf-8"))
		fixture = std_projection.document_context(projection, std_runtime.document_constants(release))
		# Release 1.1's masters never read `price` or `plan_item` (no template
		# tag names either); the serializer still supplies them, and nothing else.
		self.assertEqual(set(serializer.public_context(context)) - set(fixture), {"price", "plan_item"})
		self.assertEqual(set(fixture) - set(serializer.public_context(context)), set())
		# Every sub-key the release's masters are rendered with is supplied
		# (StrictUndefined would fail the render otherwise); the serializer may
		# carry more, as it does for `requisition`.
		for key, value in fixture.items():
			if isinstance(value, dict):
				self.assertLessEqual(set(value), set(context[key]), key)
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
		generated = bid_definition.component_digests(tender, version)
		self.assertEqual(set(generated), {"response_schema_digest", "evaluation_contract_digest", "contract_projection_digest"})
		self.assertEqual(bid_definition.component_digests(frappe.get_doc("Tender", tender.name), reloaded), generated)
		self.assertEqual(snap.recompute_digest(snap.load(reloaded)), reloaded.requisition_snapshot_digest)
		self.assertEqual(len(digest.sha256_hex({"a": 1})), 64)


	def test_a_package_digested_before_the_reason_field_still_verifies(self):
		"""v0.16: the optional shortened-period reason must not change the digest of a package that does not use it, so a Version
		submitted or approved before the field existed still verifies at approval and authorisation. A package that does use it is
		digested with it, so the reason cannot be altered after approval."""
		tender, version = self._pair()
		material = serializer.content_material(tender, version, snap.load(version))["officer_values"]
		self.assertNotIn("shortened_period_reason", material)
		without = serializer.package_digest(tender, version, snap.load(version))
		version.officer_payload_json = json.dumps({**json.loads(version.officer_payload_json), "shortened_period_reason": "Needed before the October training."})
		with_reason = serializer.package_digest(tender, version, snap.load(version))
		self.assertNotEqual(without, with_reason)
		self.assertIn("shortened_period_reason", serializer.content_material(tender, version, snap.load(version))["officer_values"])
		version.officer_payload_json = json.dumps({k: v for k, v in json.loads(version.officer_payload_json).items() if k != "shortened_period_reason"})
		self.assertEqual(serializer.package_digest(tender, version, snap.load(version)), without)


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
