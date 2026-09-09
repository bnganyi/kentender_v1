# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11.2 Draft-stage commands: PrepareTender (TPR-AC-001/
002/003/004/036, SMOKE-01/15), SaveTenderDraft (TPR-AC-006/008/019/020/021,
SMOKE-03/06), the evidence rows (TPR-AC-017/018, SMOKE-07) and
RunTenderReadiness (TPR-AC-022)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_preparation.services import draft_commands as cmd
from kentender_procurement.tender_preparation.services import evidence, readiness
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestPrepare(TenderCase):
	def test_prepare_creates_one_bound_draft_and_consumes_the_handoff(self):
		handoff = fx.authorised_handoff()
		result = fx.prepared(handoff)
		self.assertEqual(result["action"], "created")
		root = frappe.get_doc("Prepared Tender", result["tender"])
		version = frappe.get_doc("Tender Preparation Version", root.current_version)
		self.assertEqual(root.template_key, "IT-EQUIPMENT-OPEN-V1")
		self.assertEqual(root.template_version, "1.1")
		self.assertTrue(root.bundle_digest and root.official_source_digest and root.handoff_digest)
		self.assertTrue(root.tender_reference.startswith("TND-"))
		self.assertEqual(root.prepared_by, fx.OFFICER)
		self.assertEqual(version.version_number, 1)
		self.assertTrue(version.snapshot_digest)
		snapshot = json.loads(version.snapshot_json)
		self.assertEqual(snapshot["handoff"], handoff)
		self.assertNotIn("decisions", snapshot)
		self.assertEqual(version.tender_title, snapshot["requirement_title"][:160])
		consumed = frappe.db.get_value("Authorised Requisition Handoff", handoff, ["tender", "tender_version", "template_version"], as_dict=True)
		self.assertEqual((consumed.tender, consumed.tender_version, consumed.template_version), (root.name, version.name, "1.1"))
		# fixed evidence rows exist from the start (warranty confirmation, manufacturer, datasheets)
		sources = {r.source for r in version.evidence_requirements}
		self.assertIn(evidence.SOURCE_FIXED, sources)
		self.assertIn(evidence.SOURCE_GENERATED, sources)

	def test_preparing_twice_returns_the_same_tender(self):
		handoff = fx.authorised_handoff()
		first = fx.prepared(handoff)
		second = fx.prepared(handoff)
		self.assertEqual(first["tender"], second["tender"])
		self.assertEqual(second["action"], "reused")
		self.assertEqual(frappe.db.count("Prepared Tender"), 1)
		self.assertEqual(frappe.db.count("Tender Preparation Version"), 1)

	def test_the_same_key_replays(self):
		handoff = fx.authorised_handoff()
		frappe.set_user(fx.OFFICER)
		k = fx.key()
		first = cmd.prepare_tender(handoff=handoff, idempotency_key=k)
		second = cmd.prepare_tender(handoff=handoff, idempotency_key=k)
		self.assertTrue(second["idempotent"])
		self.assertEqual(first["tender"], second["tender"])

	def test_only_a_procurement_officer_may_prepare(self):
		handoff = fx.authorised_handoff()
		for user in (fx.HOPF, fx.AUDITOR, fx.OUTSIDER):
			frappe.set_user(user)
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				cmd.prepare_tender(handoff=handoff, idempotency_key=fx.key())
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)

	def test_a_missing_or_revoked_handoff_creates_nothing(self):
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.prepare_tender(handoff="RQH-DOES-NOT-EXIST", idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_HANDOFF_INVALID")
		handoff = fx.authorised_handoff()
		requisition = frappe.db.get_value("Authorised Requisition Handoff", handoff, "requisition")
		from kentender_procurement.procurement_requisitions.services import authorise

		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", requisition)
		authorise.revoke_unconsumed_authorisation(requisition=requisition, reason="Revoked before Tender Preparation for the test.", expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.prepare_tender(handoff=handoff, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_HANDOFF_INVALID")
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)

	def test_an_unsupported_requisition_is_rejected_without_records(self):
		"""SMOKE-15 / TPR-AC-036 — four incompatible payloads, none creates a record."""
		handoff = fx.authorised_handoff()
		doc = frappe.get_doc("Authorised Requisition Handoff", handoff)
		payload = json.loads(doc.payload_json)
		variants = {
			"complex ERP": {"related_services": [{"service_requirement_id": "SVC-001", "service_type": "Systems integration", "required_result": "ERP integration and data migration", "applies_to_scope": "All items", "applies_to_id": "", "completion_date": "2102-04-30", "acceptance_evidence": "Report"}]},
			"Works": {"procurement_category": "Works"},
			"unsupported reservation": {"reservation_category_value": "Micro, small and medium enterprise"},
			"multi-lot": {"lotting_indicator": "Packaged into lots"},
		}
		for label, patch in variants.items():
			variant = {**payload, **patch}
			frappe.db.set_value("Authorised Requisition Handoff", handoff, "payload_json", json.dumps(variant), update_modified=False)
			frappe.set_user(fx.OFFICER)
			with self.assertRaises(TenderPreparationError, msg=label) as ctx:
				cmd.prepare_tender(handoff=handoff, idempotency_key=fx.key())
			self.assertEqual(ctx.exception.code, "TPR_PRODUCT_UNSUPPORTED", label)
			frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)
		self.assertFalse(frappe.db.get_value("Authorised Requisition Handoff", handoff, "consumed_at"))

	def test_an_unavailable_template_creates_nothing(self):
		handoff = fx.authorised_handoff()
		from kentender_procurement.tender_templates import registry

		frappe.db.set_value("Supported Tender Template", registry.registry_name(), "availability", registry.UNAVAILABLE, update_modified=False)
		self.addCleanup(registry.install)
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.prepare_tender(handoff=handoff, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_TEMPLATE_UNAVAILABLE")
		self.assertEqual(frappe.db.count("Prepared Tender"), 0)


class TestSaveDraft(TenderCase):
	def test_saving_the_three_tasks_records_values_and_regenerates_evidence(self):
		prep = fx.prepared()
		result = fx.complete_draft(prep["tender"])
		self.assertTrue(result["ok"], result)
		self.assertEqual(result["missing"], [])
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		self.assertEqual(version.tender_title, fx.TASK1["tender_title"])
		self.assertEqual(str(version.issue_date), "2102-01-15")
		self.assertEqual(version.payment_timing_days, "30")
		self.assertEqual(version.minimum_comparable_contracts, "2")
		labels = [r.evidence_label for r in version.evidence_requirements]
		self.assertTrue(any("After-sales support evidence" in l for l in labels))
		self.assertTrue(any("Manufacturer's authorisation" in l for l in labels))

	def test_an_inherited_or_generated_field_is_rejected(self):
		"""SMOKE-03 / TPR-AC-008."""
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		for field in ("items", "requirement_title", "minimum_warranty_months", "tender_reference", "unit_price", "quantity"):
			with self.assertRaises(TenderPreparationError, msg=field) as ctx:
				cmd.save_tender_draft(tender=prep["tender"], values={field: "changed"}, expected_record_version=root.record_version, idempotency_key=fx.key())
			self.assertEqual(ctx.exception.code, "TPR_INHERITED_EDIT")

	def test_free_text_for_booleans_and_finite_choices_is_rejected(self):
		"""SMOKE-06 / TPR-AC-019."""
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.save_tender_draft(tender=prep["tender"], values={"pre_tender_meeting": "maybe", "payment_timing_days": "35", "meeting_mode": "Hybrid", "tender_validity_days": "many"}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertFalse(result["ok"])
		self.assertEqual(set(result["errors"]), {"pre_tender_meeting", "payment_timing_days", "meeting_mode", "tender_validity_days"})

	def test_conditional_fields_are_rejected_while_inapplicable(self):
		"""TPR-AC-020."""
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.save_tender_draft(tender=prep["tender"], values={"pre_tender_meeting": False, "meeting_datetime": "2102-01-20 10:00:00"}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertFalse(result["ok"])
		self.assertIn("meeting_datetime", result["errors"])
		ok = cmd.save_tender_draft(tender=prep["tender"], values={"pre_tender_meeting": True, "meeting_datetime": "2102-01-20 10:00:00", "meeting_mode": "Online", "online_joining_information": "https://meet.example.test/tender"}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertTrue(ok["ok"], ok)

	def test_links_accept_only_active_governed_records(self):
		"""TPR-AC-021."""
		prep = fx.prepared()
		frappe.set_user("Administrator")
		frappe.get_doc({"doctype": "Contact Office", "office_name": "Retired Office — TPR test", "contact_email": "retired@example.test", "status": "Retired", "fixture_namespace": fx.NS}).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("Contact Office", "Retired Office — TPR test", force=1, ignore_permissions=True))
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.save_tender_draft(tender=prep["tender"], values={"contract_contact_office": "Retired Office — TPR test", "inspection_location": "No such location", "meeting_venue": fx.OFFICER}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertFalse(result["ok"])
		self.assertEqual(set(result["errors"]), {"contract_contact_office", "inspection_location", "meeting_venue"})

	def test_a_stale_record_version_is_refused(self):
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.save_tender_draft(tender=prep["tender"], values={"tender_title": "Stale write"}, expected_record_version=99, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_STALE_VERSION")

	def test_a_non_officer_cannot_save(self):
		prep = fx.prepared()
		for user in (fx.HOPF, fx.AUDITOR):
			frappe.set_user(user)
			with self.assertRaises(frappe.DoesNotExistError):
				cmd.save_tender_draft(tender=prep["tender"], values={"tender_title": "x"}, expected_record_version=0, idempotency_key=fx.key())


class TestEvidenceRows(TenderCase):
	def _draft(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		frappe.set_user(fx.OFFICER)
		return prep, frappe.get_doc("Prepared Tender", prep["tender"])

	def test_an_additional_row_must_link_to_a_visible_inherited_id(self):
		"""SMOKE-07 / TPR-AC-017."""
		prep, root = self._draft()
		bad = cmd.add_tender_evidence_requirement(tender=prep["tender"], values={"evidence_label": "Battery test report", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": "TECH-999"}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertFalse(bad["ok"])
		self.assertIn("linked_requirement_id", bad["errors"])
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		tech_id = json.loads(version.snapshot_json)["technical_requirements"][0]["technical_requirement_id"]
		good = cmd.add_tender_evidence_requirement(tender=prep["tender"], values={"evidence_label": "Battery test report", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": tech_id}, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertTrue(good["ok"], good)
		self.assertTrue(good["evidence_requirement_id"].startswith("EV-A"))
		version.reload()
		row = next(r for r in version.evidence_requirements if r.evidence_requirement_id == good["evidence_requirement_id"])
		self.assertEqual(row.source, evidence.SOURCE_ADDITIONAL)
		self.assertEqual(row.linked_requirement_id, tech_id)

	def test_generated_rows_cannot_be_edited_or_removed_directly(self):
		prep, root = self._draft()
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		generated = next(r for r in version.evidence_requirements if r.source != evidence.SOURCE_ADDITIONAL)
		with self.assertRaises(TenderPreparationError) as ctx:
			cmd.remove_tender_evidence_requirement(tender=prep["tender"], evidence_requirement_id=generated.evidence_requirement_id, expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_INHERITED_EDIT")

	def test_a_switch_change_regenerates_rows_but_keeps_additional_ones(self):
		prep, root = self._draft()
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		tech_id = json.loads(version.snapshot_json)["technical_requirements"][0]["technical_requirement_id"]
		added = cmd.add_tender_evidence_requirement(tender=prep["tender"], values={"evidence_label": "Battery test report", "evidence_type": "Certificate", "linked_requirement_type": "Technical requirement", "linked_requirement_id": tech_id}, expected_record_version=root.record_version, idempotency_key=fx.key())
		root.reload()
		cmd.save_tender_draft(tender=prep["tender"], values={"datasheets_required": False}, expected_record_version=root.record_version, idempotency_key=fx.key())
		version.reload()
		labels = [r.evidence_label for r in version.evidence_requirements]
		self.assertFalse(any("Datasheet or brochure evidencing" in l for l in labels))
		self.assertIn(added["evidence_requirement_id"], [r.evidence_requirement_id for r in version.evidence_requirements])


class TestReadiness(TenderCase):
	def test_an_incomplete_draft_reports_missing_controls_as_blocking(self):
		prep = fx.prepared()
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.run_tender_readiness(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertFalse(result["ready"])
		codes = {f["finding_code"] for f in result["findings"]}
		self.assertIn("CONTROL_MISSING", codes)
		fields = {f["field_reference"] for f in result["findings"] if f["finding_code"] == "CONTROL_MISSING"}
		self.assertIn("issue_date", fields)
		self.assertIn("inspection_location", fields)

	def test_a_complete_draft_is_ready_with_the_one_fixture_warning(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.run_tender_readiness(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual([f["message"] for f in result["findings"] if f["severity"] == "Blocking"], [])
		self.assertEqual(result["blocking_count"], 0)
		self.assertEqual(result["warning_count"], 1)
		self.assertEqual(result["findings"][0]["message"], readiness.MANUFACTURER_WARNING)
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		self.assertTrue(version.readiness_digest and version.invitation_html_digest and version.issued_tender_html_digest)
		self.assertNotEqual(version.invitation_html_digest, version.issued_tender_html_digest)

	def test_a_date_order_defect_blocks(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"], overrides={"clarification_deadline": "2102-02-10 17:00:00"})
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		result = cmd.run_tender_readiness(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertIn("DATE_ORDER", {f["finding_code"] for f in result["findings"]})

	def test_a_removed_mapping_blocks_readiness(self):
		"""SMOKE-08 / TPR-AC-014/015/022 — one technical requirement loses its
		evaluation mapping; readiness blocks and names the id."""
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		frappe.set_user(fx.OFFICER)
		root = frappe.get_doc("Prepared Tender", prep["tender"])

		def drop_one(projection):
			projection["evaluation"] = set(sorted(projection["evaluation"])[1:])
			return projection

		readiness._mapping_projection = drop_one
		self.addCleanup(setattr, readiness, "_mapping_projection", None)
		result = cmd.run_tender_readiness(tender=prep["tender"], expected_record_version=root.record_version, idempotency_key=fx.key())
		blocking = [f for f in result["findings"] if f["finding_code"] == "MAPPING_INCOMPLETE"]
		self.assertEqual(len(blocking), 1)
		self.assertIn("evaluation mapping", blocking[0]["message"])
		self.assertFalse(result["ready"])
