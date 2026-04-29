from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import parse_json


def _output_payload_dict(doc) -> dict:
	p = doc.get("output_payload")
	if p is None:
		return {}
	if isinstance(p, str):
		return parse_json(p) if p.strip() else {}
	return p

from kentender_procurement.std_engine.services.boq_instance_service import add_boq_bill, add_boq_item, create_or_initialize_boq_instance
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.instance_creation_service import create_std_instance
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object


def _delete_if_exists(doctype: str, field: str, value: str):
	if not frappe.db.table_exists(doctype):
		return
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype == "STD Audit Event":
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class _Phase6Fixture(IntegrationTestCase):
	tender_code = "TND-PH6-1"
	template_code = "STD-WORKS-PH6"
	version_code = "STDTV-PH6-ACTIVE"
	profile_code = "WORKS-PROFILE-PH6-ACTIVE"
	source_doc = "DOC1_WORKS_PH6"
	part_code = "STD-PART-PH6-1"
	section_code = "STD-SEC-PH6-V"
	boq_def_code = "STD-BOQ-PH6-1"
	boq_schema_code = "STD-BOQ-SCH-PH6-QTY"

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		for dt, field, value in (
			("STD Generation Job", "generation_job_code", "GJOB-PH6-KEEP"),
			("STD Generated Output", "output_code", "STDOUT-PH6-KEEP"),
			("STD Instance", "tender_code", self.tender_code),
			("STD BOQ Item Schema Definition", "schema_field_code", self.boq_schema_code),
			("STD BOQ Definition", "boq_definition_code", self.boq_def_code),
			("STD Applicability Profile", "profile_code", self.profile_code),
			("STD Section Definition", "section_code", self.section_code),
			("STD Part Definition", "part_code", self.part_code),
			("STD Template Version", "version_code", self.version_code),
			("STD Template Family", "template_code", self.template_code),
			("Source Document Registry", "source_document_code", self.source_doc),
		):
			_delete_if_exists(dt, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": self.source_doc,
				"source_document_title": "STD",
				"issuing_authority": "PPRA",
				"source_revision_label": "Rev",
				"procurement_category": "Works",
				"legal_use_status": "Approved for Use",
				"status": "Active",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Template Family",
				"template_code": self.template_code,
				"template_title": "PH6 Family",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"allowed_procurement_methods": "[\"Open Tender\"]",
				"family_status": "Active",
				"is_active_family": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Template Version",
				"version_code": self.version_code,
				"template_code": self.template_code,
				"version_label": "PH6 Active",
				"revision_label": "Rev",
				"source_document_code": self.source_doc,
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"version_status": "Active",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 1,
				"immutable_after_activation": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Part Definition",
				"part_code": self.part_code,
				"version_code": self.version_code,
				"part_number": "V",
				"part_title": "BOQ",
				"order_index": 5,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"is_mandatory": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Section Definition",
				"section_code": self.section_code,
				"version_code": self.version_code,
				"part_code": self.part_code,
				"section_number": "V",
				"section_title": "Bills of Quantities",
				"section_classification": "Core",
				"editability": "Structured Editable",
				"is_mandatory": 1,
				"is_supplier_facing": 1,
				"is_contract_facing": 1,
				"order_index": 5,
				"source_document_code": self.source_doc,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD BOQ Definition",
				"boq_definition_code": self.boq_def_code,
				"version_code": self.version_code,
				"section_code": self.section_code,
				"pricing_model": "Admeasurement",
				"quantity_owner": "Procuring Entity",
				"supplier_input_mode": "Rate Only",
				"amount_computation_rule": "qty*rate",
				"total_computation_rule": "sum(amount)",
				"arithmetic_correction_stage": "Evaluation",
				"allows_provisional_sums": 0,
				"allows_dayworks": 0,
				"is_required_for_readiness": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD BOQ Item Schema Definition",
				"schema_field_code": self.boq_schema_code,
				"boq_definition_code": self.boq_def_code,
				"field_key": "quantity",
				"label": "Quantity",
				"item_owner": "Procuring Entity",
				"supplier_editable": 0,
				"required": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": self.profile_code,
				"version_code": self.version_code,
				"profile_title": "Works PH6",
				"procurement_category": "Works",
				"works_profile_type": "Building Civil",
				"allowed_methods": "[\"Open Tender\"]",
				"profile_status": "Active",
				"requires_boq": 1,
				"requires_drawings": 0,
				"requires_specifications": 0,
				"requires_site_information": 0,
				"requires_hse_requirements": 0,
				"requires_environmental_social_requirements": 0,
				"supports_lots": 0,
				"supports_alternative_tenders": 0,
				"supports_margin_of_preference": 0,
				"supports_reservations": 0,
			}
		).insert()
		created = create_std_instance(
			self.tender_code,
			self.version_code,
			self.profile_code,
			{"procurement_category": "Works", "procurement_method": "Open Tender"},
			"Administrator",
		)
		self.instance_code = created["instance_code"]
		create_or_initialize_boq_instance(self.instance_code, "Administrator")
		bill = add_boq_bill(
			self.instance_code,
			{"bill_number": "1", "bill_title": "General", "bill_type": "Work Items", "order_index": 1},
			"Administrator",
		)
		add_boq_item(
			bill["bill_instance_code"],
			{"item_number": "1.1", "description": "Excavation", "unit": "m3", "quantity": 10, "rate": 100},
			"Administrator",
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("STD Audit Event", {"object_code": ("like", "GJOB-%")})
		frappe.db.delete("STD Audit Event", {"object_code": ("like", "STDOUT-%")})
		for job in frappe.get_all("STD Generation Job", filters={"instance_code": self.instance_code}, pluck="name"):
			frappe.delete_doc("STD Generation Job", job, force=True, ignore_permissions=True)
		for out in frappe.get_all("STD Generated Output", filters={"instance_code": self.instance_code}, pluck="name"):
			frappe.delete_doc("STD Generated Output", out, force=True, ignore_permissions=True)
		for bc in frappe.get_all("STD BOQ Instance", filters={"instance_code": self.instance_code}, pluck="boq_instance_code"):
			for bic in frappe.get_all("STD BOQ Bill Instance", filters={"boq_instance_code": bc}, pluck="bill_instance_code"):
				for it in frappe.get_all("STD BOQ Item Instance", filters={"bill_instance_code": bic}, pluck="name"):
					frappe.delete_doc("STD BOQ Item Instance", it, force=True, ignore_permissions=True)
			for bill in frappe.get_all("STD BOQ Bill Instance", filters={"boq_instance_code": bc}, pluck="name"):
				frappe.delete_doc("STD BOQ Bill Instance", bill, force=True, ignore_permissions=True)
			for boq_name in frappe.get_all("STD BOQ Instance", filters={"boq_instance_code": bc}, pluck="name"):
				frappe.delete_doc("STD BOQ Instance", boq_name, force=True, ignore_permissions=True)
		for dt, field, value in (
			("STD Instance", "tender_code", self.tender_code),
			("STD BOQ Item Schema Definition", "schema_field_code", self.boq_schema_code),
			("STD BOQ Definition", "boq_definition_code", self.boq_def_code),
			("STD Applicability Profile", "profile_code", self.profile_code),
			("STD Section Definition", "section_code", self.section_code),
			("STD Part Definition", "part_code", self.part_code),
			("STD Template Version", "version_code", self.version_code),
			("STD Template Family", "template_code", self.template_code),
			("Source Document Registry", "source_document_code", self.source_doc),
		):
			_delete_if_exists(dt, field, value)
		frappe.db.commit()
		super().tearDown()


class TestSTDCURSOR0601GenerationJobFramework(_Phase6Fixture):
	"""STD-CURSOR-0601 — auditable job lifecycle, supersede Current only, failure path, scope."""

	def test_job_creates_all_outputs_and_completes(self):
		res = generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		self.assertEqual(5, len(res["outputs"]))
		job = frappe.db.get_value(
			"STD Generation Job",
			{"generation_job_code": res["generation_job_code"]},
			["status", "input_hash"],
			as_dict=True,
		)
		self.assertEqual("Completed", job.status)
		self.assertTrue(job.input_hash)
		types = {frappe.db.get_value("STD Generated Output", o["output_code"], "output_type") for o in res["outputs"]}
		self.assertEqual({"Bundle", "DSM", "DOM", "DEM", "DCM"}, types)

	def test_regeneration_supersedes_prior_current(self):
		r1 = generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		r2 = generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		for o in r1["outputs"]:
			self.assertEqual("Superseded", frappe.db.get_value("STD Generated Output", o["output_code"], "status"))
		for o in r2["outputs"]:
			self.assertEqual("Current", frappe.db.get_value("STD Generated Output", o["output_code"], "status"))

	def test_published_output_not_superseded_on_regeneration(self):
		r1 = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		bundle_code = r1["outputs"][0]["output_code"]
		transition_std_object("GENERATED_OUTPUT", bundle_code, "STD_OUTPUT_PUBLISH", "Administrator", context={"requires_confirmation": True})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		self.assertEqual("Published", frappe.db.get_value("STD Generated Output", bundle_code, "status"))

	def test_scope_single_output_type(self):
		res = generate_std_outputs(self.instance_code, scope="DOM", actor="Administrator")
		self.assertEqual(1, len(res["outputs"]))
		self.assertEqual("DOM", frappe.db.get_value("STD Generated Output", res["outputs"][0]["output_code"], "output_type"))

	def test_failed_generation_marks_job_failed(self):
		from kentender_procurement.std_engine.services import generation_job_service as gjs

		gjs.GENERATION_TEST_FAIL_AFTER_TYPE = "Bundle"
		try:
			with self.assertRaises(frappe.ValidationError):
				generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
			jobs = frappe.get_all(
				"STD Generation Job",
				filters={"instance_code": self.instance_code},
				fields=["generation_job_code", "status", "error_message"],
				order_by="creation desc",
				limit=1,
			)
			self.assertTrue(jobs)
			job = jobs[0]
			self.assertEqual("Failed", job.status)
			self.assertIn("Simulated", job.error_message or "")
		finally:
			gjs.GENERATION_TEST_FAIL_AFTER_TYPE = None


class TestSTDCURSOR0602BundleGenerator(_Phase6Fixture):
	def test_bundle_manifest_required_sections(self):
		res = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		code = res["outputs"][0]["output_code"]
		doc = frappe.get_doc("STD Generated Output", {"output_code": code})
		manifest = _output_payload_dict(doc)
		ids = {s["id"] for s in manifest["sections"]}
		for required in (
			"issued_page",
			"invitation_to_tender",
			"section_i_itt",
			"section_ii_tds",
			"section_iii_evaluation",
			"section_iv_forms",
			"section_v_boq",
			"section_vi_specifications",
			"section_vii_drawings",
			"section_viii_gcc",
			"section_ix_scc",
			"section_x_contract_forms",
			"supplier_facing_attachments",
		):
			self.assertIn(required, ids, msg=f"missing section {required}")
		self.assertTrue(doc.output_hash)
		self.assertIn("preface", {x["id"] for x in manifest["excluded_from_supplier_bundle"]})

	def test_addendum_adds_section(self):
		res = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator", addendum_code="ADD-1")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		ids = {s["id"] for s in _output_payload_dict(doc)["sections"]}
		self.assertIn("addendum_references", ids)


class TestSTDCURSOR0603DSMGenerator(_Phase6Fixture):
	def test_boq_quantity_read_only(self):
		res = generate_std_outputs(self.instance_code, scope="DSM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		self.assertTrue(pl.get("read_only_model"))
		group = next(g for g in pl["groups"] if g["group_id"] == "priced_boq")
		row = group["fields"][0]
		self.assertFalse(row["quantity"]["editable"])
		self.assertTrue(row["rate"]["editable"])


class TestSTDCURSOR0604DOMGenerator(_Phase6Fixture):
	def test_opening_fields_and_prohibited_list(self):
		res = generate_std_outputs(self.instance_code, scope="DOM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		keys = {f["field_key"] for f in pl["opening_fields"]}
		self.assertIn("opening_date_time_place", keys)
		for bad in pl["prohibited_dom_fields"]:
			self.assertNotIn(bad, keys)


class TestSTDCURSOR0605DEMGenerator(_Phase6Fixture):
	def test_rules_have_source_trace(self):
		res = generate_std_outputs(self.instance_code, scope="DEM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		for rule in pl["rules"]:
			self.assertTrue(rule.get("source_object_type"))
			self.assertTrue(rule.get("source_object_code"))
		stages = pl["stages"]
		self.assertIn("Arithmetic Correction", stages)
		self.assertIn("Qualification", stages)


class TestSTDCURSOR0606DCMGenerator(_Phase6Fixture):
	def test_contract_price_source_rule(self):
		res = generate_std_outputs(self.instance_code, scope="DCM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		cf = pl["carry_forward"]["corrected_evaluated_contract_price"]
		self.assertIn("Evaluation/Award", cf["source_rule"])
		self.assertIn("raw_submitted_boq_total", cf["disallowed_sources"])
