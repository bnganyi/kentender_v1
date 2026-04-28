# Copyright (c) 2026, KenTender and contributors

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


def _d(doctype: str, field: str, value: str):
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if name:
		if doctype in ("STD Audit Event", "STD Readiness Run", "STD Readiness Finding"):
			frappe.db.delete(doctype, {"name": name})
		else:
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


class TestSTDRuntimeModels(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

		for doctype, field, value in (
			("STD Audit Event", "audit_event_code", "STD-AUDIT-1"),
			("STD Addendum Impact Analysis", "impact_analysis_code", "STD-IMPACT-1"),
			("STD Readiness Finding", "finding_code", "STD-FINDING-1"),
			("STD Readiness Run", "readiness_run_code", "STD-RUN-1"),
			("STD Generation Job", "generation_job_code", "STD-JOB-1"),
			("STD Generated Output", "output_code", "STD-OUTPUT-1"),
			("STD Instance", "instance_code", "STDINST-TND-1"),
			("STD Extraction Mapping", "mapping_code", "STD-MAP-1"),
			("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL"),
			("STD Section Definition", "section_code", "STD-SEC-MAP"),
			("STD Part Definition", "part_code", "STD-PART-MAP"),
			("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
			("STD Template Family", "template_code", "STD-WORKS"),
			("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
		):
			_d(doctype, field, value)

		frappe.get_doc(
			{
				"doctype": "Source Document Registry",
				"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
				"source_document_title": "STD Works Source",
				"issuing_authority": "PPRA",
				"source_revision_label": "Rev April 2022",
				"procurement_category": "Works",
				"legal_use_status": "Approved for Use",
				"status": "Active",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Template Family",
				"template_code": "STD-WORKS",
				"template_title": "STD Works Family",
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
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"template_code": "STD-WORKS",
				"version_label": "Works Building Rev Apr 2022",
				"revision_label": "Rev April 2022",
				"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
				"issuing_authority": "PPRA",
				"procurement_category": "Works",
				"version_status": "Active",
				"legal_review_status": "Approved",
				"policy_review_status": "Approved",
				"structure_validation_status": "Pass",
				"is_current_active_version": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Part Definition",
				"part_code": "STD-PART-MAP",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"part_number": "I",
				"part_title": "Part",
				"order_index": 1,
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Section Definition",
				"section_code": "STD-SEC-MAP",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"part_code": "STD-PART-MAP",
				"section_number": "I",
				"section_title": "Section",
				"section_classification": "Core",
				"editability": "Structured Editable",
				"order_index": 1,
				"source_document_code": "DOC1_WORKS_BUILDING_REV_APR_2022",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Applicability Profile",
				"profile_code": "WORKS-PROFILE-BUILDING-CIVIL",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"profile_title": "Works Profile",
				"procurement_category": "Works",
				"allowed_methods": "[\"Open Tender\"]",
				"profile_status": "Active",
				"requires_boq": 0,
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

	def tearDown(self):
		frappe.set_user("Administrator")
		try:
			for doctype, field, value in (
				("STD Audit Event", "audit_event_code", "STD-AUDIT-1"),
				("STD Addendum Impact Analysis", "impact_analysis_code", "STD-IMPACT-1"),
				("STD Readiness Finding", "finding_code", "STD-FINDING-1"),
				("STD Readiness Run", "readiness_run_code", "STD-RUN-1"),
				("STD Generation Job", "generation_job_code", "STD-JOB-1"),
				("STD Generated Output", "output_code", "STD-OUTPUT-1"),
				("STD Instance", "instance_code", "STDINST-TND-1"),
				("STD Extraction Mapping", "mapping_code", "STD-MAP-1"),
				("STD Applicability Profile", "profile_code", "WORKS-PROFILE-BUILDING-CIVIL"),
				("STD Section Definition", "section_code", "STD-SEC-MAP"),
				("STD Part Definition", "part_code", "STD-PART-MAP"),
				("STD Template Version", "version_code", "STDTV-WORKS-BUILDING-REV-APR-2022"),
				("STD Template Family", "template_code", "STD-WORKS"),
				("Source Document Registry", "source_document_code", "DOC1_WORKS_BUILDING_REV_APR_2022"),
			):
				_d(doctype, field, value)
			frappe.db.commit()
		finally:
			super().tearDown()

	def test_core_runtime_model_graph_creation(self):
		map_doc = frappe.get_doc(
			{
				"doctype": "STD Extraction Mapping",
				"mapping_code": "STD-MAP-1",
				"version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"source_object_type": "Section",
				"source_object_code": "STD-SEC-MAP",
				"target_model": "Bundle",
				"target_component_type": "Section",
			}
		).insert()
		instance = frappe.get_doc(
			{
				"doctype": "STD Instance",
				"instance_code": "STDINST-TND-1",
				"tender_code": "TND-1",
				"template_version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"profile_code": "WORKS-PROFILE-BUILDING-CIVIL",
				"instance_status": "Draft",
				"readiness_status": "Not Run",
			}
		).insert()
		out = frappe.get_doc(
			{
				"doctype": "STD Generated Output",
				"output_code": "STD-OUTPUT-1",
				"instance_code": instance.instance_code,
				"output_type": "Bundle",
				"version_number": 1,
				"status": "Current",
				"source_template_version_code": "STDTV-WORKS-BUILDING-REV-APR-2022",
				"source_profile_code": "WORKS-PROFILE-BUILDING-CIVIL",
				"generated_by_job_code": "STD-JOB-1",
			}
		).insert()
		job = frappe.get_doc(
			{
				"doctype": "STD Generation Job",
				"generation_job_code": "STD-JOB-1",
				"instance_code": instance.instance_code,
				"job_type": "Bundle",
				"trigger_type": "Manual",
				"status": "Completed",
			}
		).insert()
		run = frappe.get_doc(
			{
				"doctype": "STD Readiness Run",
				"readiness_run_code": "STD-RUN-1",
				"object_type": "STD Instance",
				"object_code": instance.instance_code,
				"status": "Ready",
				"run_at": frappe.utils.now_datetime(),
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Readiness Finding",
				"finding_code": "STD-FINDING-1",
				"readiness_run_code": run.readiness_run_code,
				"severity": "Info",
				"rule_code": "RULE-OK",
				"message": "No blockers",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "STD Addendum Impact Analysis",
				"impact_analysis_code": "STD-IMPACT-1",
				"instance_code": instance.instance_code,
				"addendum_code": "ADD-1",
				"status": "Draft",
			}
		).insert()
		audit = frappe.get_doc(
			{
				"doctype": "STD Audit Event",
				"audit_event_code": "STD-AUDIT-1",
				"event_type": "OUTPUT_GENERATED",
				"object_type": "STD Generated Output",
				"object_code": out.output_code,
				"timestamp": frappe.utils.now_datetime(),
			}
		).insert()
		self.assertEqual(map_doc.mapping_code, "STD-MAP-1")
		self.assertEqual(job.generation_job_code, "STD-JOB-1")
		self.assertEqual(audit.audit_event_code, "STD-AUDIT-1")

