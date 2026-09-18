# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 reads, the My Work provider, the technical-read
surface and the request-shaped API path: verdict-first workspace (AC-001..
004), start read (AC-005/006), record read with role-computed actions and
segregation copy (AC-037..039, 070), review read (AC-026..028), history,
masked not-found, the `**kwargs` AST guard, and the exact §10.2 status/
action vocabulary."""

from __future__ import annotations

import ast
import os

import frappe
from frappe.handler import execute_cmd
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders import api
from kentender_procurement.tenders.services import draft_commands as cmd, history, lifecycle, my_work_provider, read, technical_read
from kentender_procurement.tenders.tests import fixtures as fx, sample

API = "kentender_procurement.tenders.api"


class TenderReadCase(IntegrationTestCase):
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
		self.addCleanup(setattr, frappe.local, "form_dict", frappe._dict())

	def _started(self) -> tuple[dict, dict]:
		authorised = fx.authorised_handoff(items=(("Business laptops", 1, "Clinical training"),))
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		return authorised, started

	def _complete(self, started: dict) -> None:
		root = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=root.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)

	def call(self, method: str, **args):
		frappe.local.form_dict = frappe._dict(cmd=f"{API}.{method}", csrf_token="irrelevant-but-present-on-every-post", **args)
		had_request = hasattr(frappe.local, "request")
		if not had_request:
			frappe.local.request = frappe._dict(method="POST", path=f"/api/method/{API}.{method}", headers={})
			self.addCleanup(delattr, frappe.local, "request")
		return execute_cmd(f"{API}.{method}")


class TestWorkspaceAndStart(TenderReadCase):
	def test_forbidden_verdict_and_role_queues(self):
		forbidden = read.get_tenders_workspace(user=fx.NOBODY)
		self.assertEqual(forbidden["outcome"], "FORBIDDEN")
		self.assertIn("Procurement Officer, Head of Procurement Function, Accounting Officer", forbidden["forbidden"]["text"])
		authorised = fx.authorised_handoff()
		ws = read.get_tenders_workspace(user=fx.OFFICER)
		self.assertEqual(ws["outcome"], "OK")
		start = next(r for r in ws["rows"] if r["kind"] == "start" and r["handoff"] == authorised["handoff"])
		self.assertEqual((start["tender_reference"], start["status_label"], start["action_label"], start["route"][:2]), ("Not started", "Ready to start", "Start Tender", ["tenders", "new"]))
		self.assertEqual([c["label"] for c in ws["counts"]], ["Ready to start", "Drafts", "Returned to me"])
		self.assertEqual(ws["counts"][0]["value"], 1)
		reader = read.get_tenders_workspace(user=fx.AUDITOR)
		self.assertEqual((reader["mode"], reader["counts"]), ("reader", []))
		self.assertFalse(any(r["kind"] == "start" for r in reader["rows"]))
		technical = read.get_tenders_workspace(user="Administrator")
		self.assertEqual((technical["mode"], technical["counts"]), ("technical", []))
		self.assertEqual(read.get_tenders_workspace(user=fx.OFFICER, status="published")["rows"], [])
		self.assertEqual(read.get_tenders_workspace(user=fx.OFFICER, status="published")["empty_text"], "No Tenders match these filters.")

	def test_the_start_read_creates_nothing_and_reports_the_three_outcomes(self):
		authorised = fx.authorised_handoff()
		before = frappe.db.count("Tender")
		start = read.get_tender_start(handoff=authorised["handoff"], user=fx.OFFICER)
		self.assertEqual((start["outcome"], start["supported"], start["can_start"]), ("OK", True, True))
		self.assertEqual(start["result_text"], "Supported — IT equipment using the standard Open Tender format.")
		self.assertEqual([c["check"] for c in start["compatibility"]], ["Procurement category", "Product", "Method", "Reservation", "Lotting", "Currency", "Award package", "Plan horizon"])
		self.assertEqual(start["summary"]["method"], "Open Tender")
		self.assertTrue(start["template"]["available"])
		self.assertEqual(frappe.db.count("Tender"), before)
		self.assertFalse(read.get_tender_start(handoff=authorised["handoff"], user=fx.HOPF)["can_start"])
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_tender_start(handoff=authorised["handoff"], user=fx.NOBODY)
		self.assertEqual(read.get_tender_start(handoff="RQH-nothing", user=fx.OFFICER)["outcome"], "SOURCE_UNAVAILABLE")
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		again = read.get_tender_start(handoff=authorised["handoff"], user=fx.OFFICER)
		self.assertEqual((again["outcome"], again["tender"], again["can_open"]), ("ALREADY_STARTED", started["tender"], True))


class TestRecordReview(TenderReadCase):
	def test_record_read_per_role_and_state(self):
		_, started = self._started()
		root = frappe.get_doc("Tender", started["tender"])
		officer = read.get_tender(tender=root.tender_reference, user=fx.OFFICER)
		self.assertEqual((officer["outcome"], officer["screen"], officer["tender"]["badge"]), ("OK", "editor", "Draft"))
		self.assertEqual(officer["tasks"], {"details": "Needs attention", "requirements": "Not started", "review": "Not started"})
		self.assertIn("save_draft", officer["allowed_actions"])
		self.assertNotIn("submit_for_approval", officer["allowed_actions"])
		self.assertEqual(officer["inherited"]["context"]["quantity"], "1 Each")
		self.assertEqual(len(officer["inherited"]["goods_lines"]), 1)
		self.assertIn("internal", officer["inherited"])
		department = read.get_tender(tender=root.name, user=fx.DEPARTMENTAL)
		self.assertEqual((department["mode"], department["screen"], department["allowed_actions"]), ("department", "record", ["view_history"]))
		self.assertNotIn("internal", department["inherited"])
		self.assertEqual(department["documents"], [])
		with self.assertRaises(frappe.DoesNotExistError):
			read.get_tender(tender=root.name, user=fx.OUTSIDER)
		self.assertEqual(api.get_tender(tender="TND-NOTHING")["outcome"], "NOT_FOUND")

		self._complete(started)
		root.reload()
		officer = read.get_tender(tender=root.name, user=fx.OFFICER)
		self.assertEqual(officer["tasks"], {"details": "Complete", "requirements": "Complete", "review": "Complete"})
		self.assertIn("submit_for_approval", officer["allowed_actions"])
		rev = read.get_tender_review(tender=root.name, user=fx.OFFICER)
		self.assertEqual((rev["review"]["result"], rev["review"]["must_fix_count"], rev["review"]["review_note_count"]), ("Ready to submit", 0, 1))
		self.assertEqual([s["key"] for s in rev["sections"]], ["details", "requirements", "pricing", "supplier", "contract", "technical"])
		self.assertEqual([s["open"] for s in rev["sections"]], [False, False, False, True, False, False])
		self.assertEqual(rev["sections"][2]["details"]["rows"][0]["unit_price"], "Completed by supplier")
		self.assertEqual(rev["submit_blocked_text"], "")

		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		hopf = read.get_tender(tender=root.name, user=fx.HOPF)
		self.assertEqual((hopf["screen"], hopf["tender"]["badge"]), ("approval", "Awaiting your approval"))
		self.assertEqual(sorted(a for a in hopf["allowed_actions"] if a != "view_history"), ["approve_tender_package", "request_requisition_correction", "return_for_correction"])
		self.assertEqual(hopf["segregation_message"], "")
		ws = read.get_tenders_workspace(user=fx.HOPF)
		row = next(r for r in ws["rows"] if r.get("tender") == root.name)
		self.assertEqual((row["status_label"], row["action_label"]), ("Awaiting your approval", "Review"))
		self.assertEqual(ws["counts"][0], {"key": "awaiting_approval", "label": "Awaiting procurement approval", "value": 1, "sub": "Tenders submitted for procurement approval"})
		rows = my_work_provider.my_work_rows(user=fx.HOPF)["assigned"]
		self.assertEqual((rows[0]["task_id"], rows[0]["route"], rows[0]["action_label"]), (submitted["task"], ["tenders", root.tender_reference], "Review Tender package"))
		self.assertEqual(my_work_provider.my_work_rows(user=fx.OFFICER)["assigned"], [])

		root.reload()
		lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		ao = read.get_tender(tender=root.name, user=fx.AO)
		self.assertEqual((ao["screen"], ao["tender"]["badge"]), ("authorisation", "Awaiting publication authorisation"))
		self.assertIn("authorise_publication", ao["allowed_actions"])
		self.assertEqual(ao["version"]["approved_by"], fx.HOPF)
		ws = read.get_tenders_workspace(user=fx.AO)
		row = next(r for r in ws["rows"] if r.get("tender") == root.name)
		self.assertEqual((row["status_label"], row["action_label"]), ("Awaiting your publication decision", "Review publication"))
		self.assertEqual(my_work_provider.my_work_rows(user=fx.AO)["assigned"][0]["action_label"], "Review publication")
		hist = history.get_tender_history(tender=root.name, user=fx.AUDITOR)
		self.assertEqual([v["version_number"] for v in hist["versions"]], [1])
		self.assertEqual([d["decision"] for d in hist["decisions"]], ["Submit for approval", "Approve Tender package"])
		self.assertEqual([e["event_type"] for e in hist["events"]], ["TenderStarted", "TenderDraftSaved", "TenderSubmitted", "TenderApproved"])
		self.assertTrue(hist["events"][0]["payload"])  # oversight readers see payloads
		officer_hist = history.get_tender_history(tender=root.name, user=fx.OFFICER)
		self.assertEqual(officer_hist["events"][0]["payload"], {})

	def test_a_returned_draft_reads_as_returned_to_you_at_the_affected_task(self):
		_, started = self._started()
		self._complete(started)
		root = frappe.get_doc("Tender", started["tender"])
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		lifecycle.return_tender_for_correction(tender=root.name, reason="Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.", affected_task="Supplier and contract requirements", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		ws = read.get_tenders_workspace(user=fx.OFFICER)
		row = next(r for r in ws["rows"] if r.get("tender") == root.name)
		self.assertEqual((row["status_key"], row["action_label"], row["route"]), ("returned", "Correct", ["tenders", root.tender_reference, "review"]))
		self.assertTrue(row["status_label"].startswith("Returned to you"))
		self.assertEqual(next(c["value"] for c in ws["counts"] if c["key"] == "returned"), 1)
		record = read.get_tender(tender=root.name, user=fx.OFFICER)
		self.assertEqual(record["returned"]["affected_task"], "requirements")
		self.assertEqual(record["returned"]["comment"], "Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.")
		self.assertEqual(record["version"]["version_number"], 2)


class TestApiSurface(TenderReadCase):
	def test_no_endpoint_declares_kwargs(self):
		path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api.py")
		with open(path, encoding="utf-8") as handle:
			tree = ast.parse(handle.read())
		offenders = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.args.kwarg is not None]
		self.assertEqual(offenders, [])
		whitelisted = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and any(getattr(d, "attr", None) == "whitelist" or getattr(getattr(d, "func", None), "attr", None) == "whitelist" for d in n.decorator_list)]
		self.assertEqual(len(whitelisted), 22)

	def test_the_journey_over_the_request_path(self):
		authorised = fx.authorised_handoff(items=(("Business laptops", 1, "Clinical training"),))
		frappe.set_user(fx.OFFICER)
		ws = self.call("get_tenders_workspace")
		self.assertEqual(ws["outcome"], "OK")
		started = self.call("start_tender", handoff=authorised["handoff"], idempotency_key=fx.key())
		self.assertEqual(started["action"], "started")
		import json

		saved = self.call("save_tender_draft", tender=started["tender"], draft_values=json.dumps(sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)), expected_record_version=started["record_version"], idempotency_key=fx.key())
		self.assertTrue(saved["ok"])
		preview = self.call("preview_tender_documents", tender=started["tender"])
		self.assertEqual(preview["outcome"], "OK")
		self.assertIn("INVITATION TO TENDER", preview["invitation_html"])
		submitted = self.call("submit_tender_for_approval", tender=started["tender"], expected_record_version=saved["record_version"], idempotency_key=fx.key())
		self.assertEqual(submitted["action"], "submitted")
		self.assertEqual(self.call("get_tender", tender="TND-NOTHING")["outcome"], "NOT_FOUND")
		frappe.set_user(fx.HOPF)
		approved = self.call("approve_tender_package", tender=started["tender"], expected_record_version=submitted["record_version"], idempotency_key=fx.key(), task=submitted["task"])
		self.assertEqual(approved["action"], "approved")
		frappe.set_user("Administrator")
		probes = technical_read.read_probes()
		self.assertEqual([p["label"] for p in probes][:3], ["tenders.get_tenders_workspace", "tenders.get_tender_start", "tenders.get_tender"])
		self.assertEqual(technical_read.reference_resolvers()[0]["route"](started["tender"]), ["tenders", started["tender_reference"]])
