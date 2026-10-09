# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §10.1 reads — verdict first, side-effect free, shaped
for their boards (REQ19-AC-002/022/032/054/077/078/094/097/101/102,
REQ110-AC-003, REQ111-AC-001/003)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.procurement_requisitions.services import read
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase


class TestWorkspace(RequisitionCase):
	def test_ready_to_start_then_your_work_leads_with_the_draft(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		base = read.get_requisition_workspace()
		self.assertEqual(base["your_work"], [])
		ready = next(r for r in base["ready_to_start"] if r["plan_item_id"] == item_id)
		self.assertTrue(ready["route"].endswith(f"/new/{item_id}"))
		self.assertIsNone(ready["existing"])
		self.assertEqual(ready["plan_item_reference"], frappe.db.get_value("Plan Item", item_id, "plan_item_reference"))
		requisition = fx.prepare(item_id)["requisition"]
		frappe.set_user(fx.AUTHOR)
		draft = read.get_requisition_workspace()
		work = next(w for w in draft["your_work"] if w["requisition"] == requisition)
		self.assertEqual((work["task"], work["action"]), ("Complete request details", "Continue"))
		self.assertFalse(any(r["plan_item_id"] == item_id for r in draft["ready_to_start"]))

	def test_an_open_requisition_says_its_state_once_and_a_draft_adds_its_next_task(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		frappe.set_user(fx.AUTHOR)
		work = [w for w in read.get_requisition_workspace()["your_work"] if w["requisition"] == requisition]
		self.assertTrue(work, "a Draft leads Your work for its author")
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition)
		fx.enter_estimates(requisition)
		fx.apply_standard_package(requisition)
		fx.send(requisition)
		frappe.set_user(fx.AUTHOR)
		row = next(r for r in read.get_requisition_workspace()["ready_to_start"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["existing"]["summary"], f"{reference} \u00b7 Awaiting department approval")
		self.assertEqual(row["existing"]["summary"].count("Awaiting department approval"), 1)

	def test_an_assigned_decision_leads_for_the_hod(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		frappe.set_user(fx.HOD)
		work = read.get_requisition_workspace()["your_work"]
		self.assertEqual([(w["task"], w["action"]) for w in work if w["requisition"] == requisition], [("Review departmental requisition", "Review")])

	def test_a_user_with_no_responsibility_gets_the_inline_forbidden_state(self):
		from kentender_procurement.procurement_planning.tests import fixtures as pln_fx

		pln_fx._user("reqt.nobody@example.test", "REQ Test Nobody")
		frappe.set_user("reqt.nobody@example.test")
		result = read.get_requisition_workspace()
		self.assertEqual(result["outcome"], "FORBIDDEN")
		self.assertTrue(result["message"].startswith("You do not have access to Procurement Requisitions."))
		self.assertNotIn("register", result)

	def test_the_technical_reader_sees_every_row_and_no_work(self):
		_, item_id = fx.active_item()
		fx.prepare(item_id)
		frappe.set_user("Administrator")
		# The register is paged (ten by default); the row just built sorts by its own modified time.
		result = read.get_requisition_workspace(filters={"page_size": 100})
		self.assertEqual((result["mode"], result["your_work"]), ("technical", []))
		self.assertTrue(any(r["title"] for r in result["register"]))
		# REQ-DES-01-TECHNICAL: the purchase reference under its title and a
		# working Financial year filter.
		row = next(r for r in result["register"] if r["plan_item_id"] == item_id)
		self.assertEqual(row["plan_item_reference"], frappe.db.get_value("Plan Item", item_id, "plan_item_reference"))
		fy = row["fiscal_year"]
		self.assertIn(fy, [o["value"] for o in result["filters"]["fiscal_years"]])
		self.assertTrue(all(o["label"].startswith("FY ") for o in result["filters"]["fiscal_years"]))
		self.assertTrue(read.get_requisition_workspace(filters={"fiscal_year": fy})["register"])
		self.assertEqual(read.get_requisition_workspace(filters={"fiscal_year": "no-such-year"})["register"], [])


	def test_the_register_is_paged_and_says_how_many_rows_match(self):
		"""The table-pagination standard: ten rows by default, a page size from the
		fixed offer, the matching total, and a page past the end clamps to the last
		one. Reads the technical register as it stands rather than building rows."""
		frappe.set_user("Administrator")
		everything = read.get_requisition_workspace(filters={"page_size": 100})
		total = everything["paging"]["total"]
		if total <= 10:
			self.skipTest("needs more than ten requisitions in the register to page")
		self.assertEqual(len(everything["register"]), min(total, 100))
		first = read.get_requisition_workspace()
		self.assertEqual(first["paging"], {"page": 1, "page_size": 10, "total": total, "pages": -(-total // 10)})
		self.assertEqual(len(first["register"]), 10)
		second = read.get_requisition_workspace(filters={"page": 2})
		self.assertEqual(second["paging"]["page"], 2)
		self.assertFalse({r["requisition"] for r in first["register"]} & {r["requisition"] for r in second["register"]})
		self.assertEqual(
			[r["requisition"] for r in first["register"] + second["register"]],
			[r["requisition"] for r in everything["register"]][: len(first["register"]) + len(second["register"])],
		)
		past = read.get_requisition_workspace(filters={"page": 999})
		self.assertEqual(past["paging"]["page"], past["paging"]["pages"])
		self.assertTrue(past["register"])
		# A page size outside the offer falls back to ten rather than being honoured.
		self.assertEqual(read.get_requisition_workspace(filters={"page_size": 7})["paging"]["page_size"], 10)
		# The total follows the filters, not the whole register.
		none = read.get_requisition_workspace(filters={"fiscal_year": "no-such-year"})
		self.assertEqual((none["register"], none["paging"]["total"], none["paging"]["page"]), ([], 0, 1))
		# `register_total` keeps meaning "every row before filtering".
		self.assertEqual(none["register_total"], everything["register_total"])


class TestRecordAndTasks(RequisitionCase):
	def test_an_unrelated_department_is_masked_as_not_found(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		frappe.set_user(fx.CONTRIBUTOR)
		self.assertEqual(read.get_requisition_record(requisition=requisition)["outcome"], "NOT_FOUND")

	def test_after_submission_the_hod_task_is_read_only_but_keeps_withdraw_and_planning_correction(self):
		# REQ-DES-07-SUBMITTED: no edit, return or submit; Request Planning
		# correction and Withdraw requisition remain available to the lead HoD.
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		frappe.set_user(fx.HOD)
		task = fx.open_task(requisition, "Head of User Department")
		fx.submit_as_hod(requisition)
		frappe.set_user(fx.HOD)
		view = read.get_department_approval_task(task=task)
		self.assertEqual(view["mode"], "reader")
		self.assertEqual(view["header"]["badge"]["label"], "Submitted to Procurement")
		self.assertFalse(view["actions"]["submit_to_procurement"] or view["actions"]["return_for_correction"])
		self.assertTrue(view["actions"]["withdraw"])
		self.assertTrue(view["actions"]["request_planning_correction"])
		frappe.set_user(fx.AUDITOR)
		auditor = read.get_department_approval_task(task=task)
		self.assertFalse(any(auditor["actions"].values()))

	def test_the_procurement_task_leads_with_the_decision_and_its_financial_consequence(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOPF)
		task = fx.open_task(requisition, "Head of Procurement Function")
		view = read.get_procurement_authorisation_task(task=task)
		self.assertEqual(view["result"]["title"], "Ready to authorise")
		self.assertEqual(view["result"]["detail"], "Authorising will reserve KES 50,000,000.00 and allow Tender Preparation to begin.")
		self.assertEqual(len(view["checks"]["rows"]), 9)
		self.assertEqual(view["checks"]["summary"], "9 checks passed")
		self.assertTrue(view["actions"]["authorise"])
		self.assertTrue(view["actions"]["change_submitting_department"])
		self.assertEqual(len(view["funding"]["sources"]), 2)
		self.assertEqual(view["planning"]["hold"], "None unresolved")
		self.assertEqual(frappe.db.count("Funding Reservation", {"calling_module": "Procurement Requisitions"}), 0)
		self.assertNotIn("target_percent", json.dumps(view, default=str))
		self.assertEqual([s["key"] for s in view["sections"]], ["purpose", "amounts", "equipment", "requirements", "services", "acceptance", "supporting_materials"])

	def test_the_auditor_reads_the_task_with_no_decision(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.AUDITOR)
		view = read.get_procurement_authorisation_task(task=fx.open_task(requisition, "Head of Procurement Function"))
		self.assertEqual(view["mode"], "reader")
		self.assertFalse(any(view["actions"][k] for k in ("authorise", "return_to_department", "request_planning_correction")))


class TestAuthorisedView(RequisitionCase):
	def test_actor_variants(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		frappe.set_user(fx.HOPF)
		hopf = read.get_requisition_record(requisition=requisition)
		self.assertEqual((hopf["kind"], hopf["header"]["badge"]["label"]), ("authorised", "Authorised"))
		self.assertTrue(hopf["actions"]["revoke"])
		self.assertEqual(len(hopf["reservations"]), 2)
		self.assertEqual(hopf["facts"][2], {"label": "Requisition value", "value": "KES 50,000,000.00"})
		frappe.set_user(fx.AUDITOR)
		auditor = read.get_requisition_record(requisition=requisition)
		self.assertFalse(auditor["actions"]["revoke"] or auditor["actions"]["continue_to_tender_preparation"])
		self.assertTrue(auditor["actions"]["export"])


class TestExport(RequisitionCase):
	def test_export_is_the_exact_displayed_version_read_only_and_masked_like_the_read(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		frappe.set_user(fx.AUDITOR)
		before = frappe.db.get_value("Procurement Requisition", requisition, "record_version")
		exported = read.export_requisition(requisition=requisition)
		self.assertEqual(exported["outcome"], "OK")
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		self.assertTrue(exported["filename"].startswith(reference))
		self.assertTrue(exported["filename"].endswith(".json"))
		document = json.loads(exported["content"])
		self.assertEqual(document["kind"], "authorised")
		self.assertEqual([s["key"] for s in document["sections"]], ["purpose", "amounts", "equipment", "requirements", "services", "acceptance", "supporting_materials"])
		self.assertNotIn("actions", document)
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "record_version"), before)
		frappe.set_user(fx.CONTRIBUTOR)
		self.assertEqual(read.export_requisition(requisition=requisition)["outcome"], "NOT_FOUND")
