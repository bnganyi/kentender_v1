# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 4.1, 5.7, 5.15, 7, 8 (CM_REPORT), 19.3 (CM-R-13 to CM-R-15), LQ-06 and boards D15, D15-L (plan Phase 8; tracker CM8-806): obligations and generated reports.

An obligation keeps its trigger with its instant and never invents a deadline; unknown applicability opens review work at once. A report is derived once per type and period with its exact cutoff; a source that
cannot be read leaves an Incomplete draft that is never submitted; a regeneration is a successor and a submitted report keeps its rows exactly; dispatch and delivery are tracked apart."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.services import change, errors, events, obligations, records, reporting, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


class ReportCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		world.ensure_workflow()
		cls.addClassCleanup(world.drop_workflow)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_dispatch_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()

	def delivered(self):
		"""Ten laptops ordered: eight accepted, two rejected and replaced; eight invoiced, certified and paid (KES 800,000)."""
		self.t.appointed()
		units = tw.fresh_serials(10)
		arrival = self.t.arrive(units, received_at="2027-07-12 10:00:00")["arrival"]
		self.t.inspect(arrival, units, bad=tuple(units[8:]))
		frappe.flags.kt_cm_clock = "2027-07-20 10:00:00"
		self.t.accept(arrival)
		from kentender_contracts.services import delivery

		new = tw.fresh_serials(2)
		again = delivery.record_arrival(self.case, expected_version=self.t.version(), idempotency_key=self.t.key("rarr"), actor=self.p["grace"], received_at="2027-07-26 10:00:00", destination="Afya House store",
			items=[{"line_id": "L1", "quantity": 2, "units": new, "replaces": units[8:]}])["arrival"]
		self.t.inspect(again, new)
		frappe.flags.kt_cm_clock = "2027-07-27 10:00:00"
		self.t.accept(again)
		invoice = self.t.claim("INV-R-1", 8)["invoice"]
		self.t.certify_invoice(invoice)
		self.t.pay(invoice, "RPT-BANK-1")

	def generate(self, report_type="Progress", start="2027-07-01", who="charles"):
		return reporting.generate(report_type, period_start=start, idempotency_key=self.t.key("gen"), actor=self.p[who])

	def report(self, out):
		return reporting.get(out["report"])

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}


class TestObligations(ReportCase):
	def row(self):
		return obligations.get(self.case, "Publication", "publication")

	def test_the_award_opens_a_publication_duty_with_its_own_instant_and_no_invented_deadline(self):
		row = self.row()
		self.assertEqual((row.state, row.rule, row.trigger_event, str(row.trigger_at)), ("Needs review", "CM-R-13", "Award decision recorded", "2027-06-17 10:00:00"))
		self.assertIsNone(row.due_at)
		self.assertIn("Not confirmed", row.due_basis)
		events_ = [e["event"] for e in obligations.detail(row)["events"]]
		self.assertEqual(events_, ["Award decision recorded", "Contract signed"])  # the signing is a separate fact and does not replace the award event
		self.assertEqual(obligations.detail(row)["events"][0]["at"], "2027-06-17 10:00:00")

	def test_the_duty_is_review_work_in_the_contracts_duties_without_a_countdown_or_a_standing_task(self):
		self.assertFalse([t for t in work.live(self.case) if t["command"] == "RecordContractAwardPublication"])  # a blocked item that never clears would sit on the head's work for ever
		from kentender_contracts.boards import router

		board = router.board_for(self.case, self.p["charles"], tab="Obligations")
		duties = next(r for r in board["regions"] if r["t"] == "Duties")
		self.assertEqual(duties["b"][0]["rows"][0][:3], ["Publication: Award decision recorded", "Needs review", "Not confirmed — set by current directions"])
		self.assertEqual(duties["b"][0]["rows"][0][4], "@Review publication")
		self.assertIsNone(self.row().due_at)

	def test_source_evidence_is_a_proposal_for_the_legal_owner_not_a_rule_a_deadline_or_a_verification(self):
		row = self.row()
		self.assertIn("reference", refusal(obligations.record_source_evidence, self.case, obligation=row.name, reference=" ", dated="2027-07-02", copy="", notes="", expected_version=self.t.version(), idempotency_key=self.t.key("e"), actor=self.p["charles"]).fields)
		obligations.record_source_evidence(self.case, obligation=row.name, reference="PPRA circular 4/2027", dated="2027-06-30", copy="/private/files/circular.pdf", notes="Names a 14-day period", expected_version=self.t.version(),
			idempotency_key=self.t.key("e2"), actor=self.p["charles"])
		now = self.row()
		self.assertEqual(now.state, "Needs review")
		self.assertIsNone(now.due_at)
		self.assertEqual(obligations.detail(now)["evidence"][0]["status"], "Proposed for the legal owner's review")
		self.assertIn(("RecordContractAwardPublication", "Waiting for the legal and reporting owner to confirm the requirement.", "waiting"), self.tasks("charles"))
		self.assertEqual(refusal(obligations.record_source_evidence, self.case, obligation=row.name, reference="x", dated="2027-06-30", copy="", notes="", expected_version=self.t.version(), idempotency_key=self.t.key("e3"), actor=self.p["stranger"]).code, "CM_AUTHORITY")

	def test_a_publication_is_recorded_as_it_happened_and_only_under_a_verified_profile(self):
		row = self.row()
		args = dict(obligation=row.name, channel="Notice board and website", published_on="2027-07-05", evidence=[{"label": "Notice board photograph", "file": "/private/files/board.jpg"}])
		self.assertIn("channel", refusal(obligations.record_publication, self.case, **{**args, "channel": " "}, expected_version=self.t.version(), idempotency_key=self.t.key("p0"), actor=self.p["charles"]).fields)
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")
		self.assertEqual(refusal(obligations.record_publication, self.case, **args, expected_version=self.t.version(), idempotency_key=self.t.key("p1"), actor=self.p["charles"]).code, "CM_RULE")
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "SYNTHETIC-ILLUSTRATIVE")
		out = obligations.record_publication(self.case, **args, expected_version=self.t.version(), idempotency_key=self.t.key("p2"), actor=self.p["charles"])
		self.assertEqual((out["state"], self.row().state, self.row().disposition), ("Satisfied", "Satisfied", "Published on 5 July 2027 (Notice board and website)"))
		self.assertEqual(str(self.row().trigger_at), "2027-06-17 10:00:00")  # the original trigger is untouched
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "RecordContractAwardPublication" and t[2] != "done"})

	def test_an_effective_amendment_opens_a_variation_duty_and_a_termination_opens_an_internal_record(self):
		self.t.change_through("Extension")
		variation = obligations.get(self.case, "Variation report", "amendment 1")
		self.assertEqual((variation.state, variation.rule, variation.trigger_event, variation.due_at), ("Needs review", "CM-R-15", "Amendment 1 effective", None))
		from kentender_contracts.services import termination

		termination.request(self.case, grounds="Material non-delivery", clause="Contract clause 8", recommendation="Terminate", evidence=[{"label": "Default notice", "file": "/private/files/d.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("t1"), actor=self.p["charles"])
		termination.decide(self.case, termination=1, decision="Approve", reason="Established.", expected_version=self.t.version(), idempotency_key=self.t.key("t2"), actor=self.p["amina"])
		termination.record_notice(self.case, termination=1, delivered_on="2027-07-02", method="Post", reference="RP-1", effective_on="2027-07-02", evidence=[{"label": "Proof", "file": "/private/files/p.pdf"}],
			expected_version=self.t.version(), idempotency_key=self.t.key("t3"), actor=self.p["charles"])
		record = obligations.get(self.case, "Termination record", "termination 1")
		self.assertEqual((record.state, record.rule), ("Open", "CM-R-16"))
		self.assertIn("no statutory deadline", record.due_basis)


class TestGeneration(ReportCase):
	def setUp(self):
		super().setUp()
		self.delivered()
		frappe.flags.kt_cm_clock = "2027-08-01 09:00:00"

	def test_the_july_progress_report_is_derived_from_the_records_with_its_cutoff_and_sources(self):
		out = self.generate()
		report = self.report(out)
		row = reporting.rows_of(report)[0]
		self.assertEqual((out["state"], out["rows"], out["version"], report.recipient), ("Draft", 1, 1, "Accounting Officer"))
		self.assertEqual((str(report.period_start)[:10], str(report.period_end)[:10], str(report.cutoff)), ("2027-07-01", "2027-08-01", "2027-08-01 09:00:00"))
		self.assertEqual((row["contract"], row["value"], row["status"], row["cash_confirmed"], row["accepted"], row["ordered"], row["replacements"], row["unpaid"], row["noncash"], row["open_issues"]),
			(frappe.db.get_value("Contract Case", self.case, "contract_id"), 1_000_000, "Active", 800_000, 10, 10, 2, 200_000, 0, 0))
		self.assertEqual((row["commenced"], row["expected_completion"]), ("2027-07-02", "2028-07-27"))  # delivery complete: the warranty of the last accepted unit
		self.assertEqual(reporting.sources(report)["cases"], [{"case": self.case, "version": int(frappe.db.get_value("Contract Case", self.case, "record_version")), "read": True}])
		self.assertIn(("SubmitContractReport", "Review and submit the July 2027 report.", "actionable"), self.tasks("charles"))

	def test_a_period_is_generated_when_it_has_ended_and_only_by_the_head_of_procurement(self):
		self.assertEqual(refusal(self.generate, who="stranger").code, "CM_AUTHORITY")
		frappe.flags.kt_cm_clock = "2027-07-31 09:00:00"
		self.assertIn("period_start", refusal(self.generate).fields)  # July has not ended
		frappe.flags.kt_cm_clock = "2027-08-01 09:00:00"
		self.assertIn("period_start", refusal(self.generate, start="2027-07-15").fields)  # a month starts on its first day
		self.assertIn("report_type", refusal(self.generate, "Weekly").fields)

	def test_the_production_profile_refuses_until_it_is_verified(self):
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")
		out = refusal(self.generate)
		self.assertEqual(out.code, "CM_RULE")
		self.assertFalse(frappe.db.count("Contract Report"))

	def test_a_regeneration_is_a_successor_and_a_submitted_report_keeps_its_rows(self):
		first = self.generate()
		again = self.generate()
		self.assertEqual((again["version"], self.report(first).state, self.report(again).state), (2, "Superseded", "Draft"))
		self.assertEqual(reporting.sources(self.report(again))["supersedes"], first["report"])
		reporting.submit(again["report"], idempotency_key=self.t.key("sub"), actor=self.p["charles"])
		submitted = reporting.rows_of(self.report(again))
		self.t.claim("INV-R-2", 1)  # the world moves on after the report
		third = self.generate()
		self.assertEqual((third["version"], self.report(again).state, self.report(third).state), (3, "Submitted", "Draft"))
		self.assertEqual(reporting.rows_of(self.report(again)), submitted)  # never overwritten

	def test_a_source_that_cannot_be_read_leaves_an_incomplete_draft_that_is_never_submitted(self):
		with mock.patch.object(reporting, "progress_row", side_effect=RuntimeError("The position could not be read.")):
			out = self.generate()
		report = self.report(out)
		self.assertEqual((out["state"], out["empty"], report.state), ("Incomplete", False, "Incomplete"))
		failed = reporting.sources(report)["failed"]
		self.assertEqual((failed[0]["case"], failed[0]["owner"]), (self.case, "Technical operator"))
		self.assertIn("The position could not be read", failed[0]["reason"])
		self.assertIn(("RestoreContractOperation", "Restore the report source", "actionable"), self.tasks("daniel"))
		out = refusal(reporting.submit, out["report"], idempotency_key=self.t.key("sub"), actor=self.p["charles"])
		self.assertEqual(out.code, "CM_REPORT")
		self.assertEqual(refusal(reporting.record_submission, report.name, destination="PPRA", reference="R-1", submitted_on="2027-08-02", copy="/private/files/c.pdf", idempotency_key=self.t.key("x"), actor=self.p["charles"]).code, "CM_REPORT")

	def test_no_records_in_this_period_is_said_only_when_every_source_was_read(self):
		frappe.flags.kt_cm_clock = "2027-07-01 09:00:00"
		empty = self.generate(start="2027-06-01")  # nothing had taken effect before the end of June
		self.assertEqual((empty["rows"], empty["empty"], empty["state"]), (0, True, "Draft"))

	def test_the_scheduled_run_makes_one_report_for_a_completed_period_and_never_two(self):
		first = reporting.generate_scheduled()
		again = reporting.generate_scheduled()
		self.assertTrue(first)
		self.assertEqual(again, [])
		self.assertEqual(frappe.db.count("Contract Report", {"report_type": "Progress", "period_start": "2027-07-01"}), 1)


class TestSubmission(ReportCase):
	def setUp(self):
		super().setUp()
		self.delivered()
		frappe.flags.kt_cm_clock = "2027-08-01 09:00:00"
		self.out = self.generate()

	def submit(self, who="charles", key=None):
		return reporting.submit(self.out["report"], idempotency_key=key or self.t.key("sub"), actor=self.p[who])

	def test_the_head_of_procurement_submits_the_reviewed_report_and_it_is_delivered_with_evidence(self):
		self.assertEqual(refusal(self.submit, who="stranger").code, "CM_AUTHORITY")
		out = self.submit()
		report = self.report(self.out)
		self.assertEqual((out["state"], report.state, str(report.submitted_by)), ("Submitted", "Submitted", self.p["charles"]))
		detail = reporting.submission(report)
		self.assertEqual((detail["kind"], detail["delivery"], detail["recipient"]), ("Internal", "Delivered", "Accounting Officer"))
		self.assertTrue(detail["delivery_evidence"].startswith("DLV-"))
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "SubmitContractReport"})
		self.assertEqual(refusal(self.submit).code, "CM_CHANGED")  # a different submission of a submitted report

	def test_a_replayed_submission_is_one_submission(self):
		key = self.t.key("once")
		first = self.submit(key=key)
		self.assertEqual(self.submit(key=key), first)
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Report dispatch"}), 1)

	def test_a_failed_delivery_leaves_the_rows_untouched_pending_delivery_and_retries_the_same_dispatch(self):
		told = {"subject": "Monthly contract progress", "for_user": self.p["amina"], "document_name": self.case}
		before = frappe.db.count("Notification Log", told)  # logs outlive the tests that made them, and the contract id repeats from run to run
		frappe.flags.kt_cm_dispatch_fault = "fail"
		self.submit()
		report = self.report(self.out)
		rows = reporting.rows_of(report)
		self.assertEqual((report.state, reporting.submission(report)["delivery"]), ("Submitted", "Pending delivery"))
		self.assertIn(("RestoreContractOperation", "Restore the report delivery", "actionable"), self.tasks("daniel"))
		frappe.flags.kt_cm_dispatch_fault = None
		from kentender_contracts.services import formation

		formation.restore_operations(self.case, actor=self.p["daniel"])
		formation.restore_operations(self.case, actor=self.p["daniel"])
		self.assertEqual(reporting.submission(self.report(self.out))["delivery"], "Delivered")
		self.assertEqual(reporting.rows_of(self.report(self.out)), rows)
		self.assertEqual(frappe.db.count("Notification Log", told), before + 1)  # told once, however often the delivery was retried

	def test_an_external_submission_is_recorded_as_what_happened_with_its_destination_reference_date_and_copy(self):
		args = dict(destination="PPRA", reference="PPRA/2027/118", submitted_on="2027-08-02", copy="/private/files/submitted.pdf")
		self.assertIn("destination", refusal(reporting.record_submission, self.out["report"], **{**args, "destination": " "}, idempotency_key=self.t.key("x0"), actor=self.p["charles"]).fields)
		self.assertIn("copy", refusal(reporting.record_submission, self.out["report"], **{**args, "copy": ""}, idempotency_key=self.t.key("x1"), actor=self.p["charles"]).fields)
		reporting.record_submission(self.out["report"], **args, idempotency_key=self.t.key("x2"), actor=self.p["charles"])
		report = self.report(self.out)
		self.assertEqual((report.state, reporting.submission(report)["external"][0]["reference"]), ("Submitted", "PPRA/2027/118"))
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "SubmitContractReport"})

	def test_a_variation_report_submission_satisfies_the_amendments_duty(self):
		self.t.change_through("Extension")
		frappe.flags.kt_cm_clock = "2027-10-02 09:00:00"
		out = reporting.generate("Variation", period_start="2027-07-01", idempotency_key=self.t.key("v"), actor=self.p["charles"])
		report = self.report(out)
		row = reporting.rows_of(report)[0]
		self.assertEqual((out["rows"], row["amendment"], row["kind"], row["original_amount"], row["current_amount"], row["funding"], row["due"]), (1, 1, "Extension", 1_000_000, 1_000_000, "Not needed", "2027-07-27"))
		self.assertEqual(reporting.sources(report)["label"], "Q3 2027")
		self.assertEqual(obligations.get(self.case, "Variation report", "amendment 1").state, "Needs review")
		reporting.submit(out["report"], idempotency_key=self.t.key("vs"), actor=self.p["charles"])
		self.assertEqual(obligations.get(self.case, "Variation report", "amendment 1").state, "Satisfied")
