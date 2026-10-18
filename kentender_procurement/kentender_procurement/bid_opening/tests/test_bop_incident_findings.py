# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.16 §5.2, §6, §7.2, §10.8 and TRUST-OPS-001 v0.2 §5, §9, §10 (BOP-OF-AC-001, 002, 003, 008, 009, 010).

Support records an attributed, append-only finding on an incident — Unresolved, Recovered or Cannot recover — with a reason, safe evidence references, the
exact incident revision, the opening revision and the last committed step. A finding alone changes no ceremony state. Only a Recovered finding lets the chair
retry, resume or begin, still under the full roster and custody checks; Cannot recover blocks every chair route and gives the Accounting Officer the one open
decision item. A later finding appends evidence and never erases an earlier failed attempt. After a lawful cancellation the incident closes with the reason
"Closed after tender cancellation", keeping its findings and the service defect as a separately owned follow-up. Reads follow the access matrix: support, the
chair, the Accounting Officer and the Auditor, each audited; Administrator and System Manager status adds nothing; a business responsibility counts on its own."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
from kentender_core.services import next_step as ns
from kentender_core.tests import v16_fixtures as fx
from kentender_procurement.bid_opening.services import ceremony, decision_context, incident_access, incidents, not_held, reads, simulation
from kentender_procurement.bid_opening.services.errors import BidOpeningError
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER, SUPPORT
from kentender_procurement.bid_opening.tests.test_bop_cancellation_consumption import CancelCase
from kentender_procurement.bid_submission.services import simulation as bds_simulation
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.tenders.test_services import ground_verifier

SYSTEM_MANAGER = "kt.test.bop.findings.sysmgr@example.test"
NOT_RECOVERED = "Opening could not be recovered. The Accounting Officer must review the next step."


def as_user(_user, fn, *args, **kwargs):
	frappe.set_user(_user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


class FindingsCase(CancelCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		assert fx.user("bop.findings.sysmgr", "BOP Findings System Manager", roles=("System Manager",)) == SYSTEM_MANAGER

	def unreadable(self):
		"""Started, the only bid unreadable: the opening is paused with its one open incident."""
		self.started_with_one_bid()
		simulation.set_controls(render_outcome="Unreadable")
		self.at(self.minutes_after(1))
		self.assertFalse(self.open_next()["ok"])
		[incident] = incidents.open_incidents(self.case_doc().name)
		return incident

	def finding(self, incident, finding, reason="Checked with the permitted diagnostics.", user=SUPPORT, **kwargs):
		return incidents.record_finding(tender=self.name, incident=incident.incident_id, finding=finding, reason=reason, idempotency_key=kwargs.pop("idempotency_key", key()),
			user=user, **kwargs)

	def rows(self, incident):
		return frappe.get_all(incidents.FINDING, filters={"incident": incident.incident_id}, fields=["finding_no", "finding", "reason", "evidence_refs", "recorded_by", "incident_revision",
			"opening_revision", "last_committed_event", "request_key"], order_by="finding_no asc")

	def incident_row(self, incident):
		return frappe.get_doc(incidents.INCIDENT, {"incident_id": incident.incident_id})

	def items(self, status=None):
		filters = {"opening_case": self.case_doc().name}
		if status:
			filters["status"] = status
		return frappe.get_all(not_held.DECISION, filters=filters, fields=["name", "kind", "status", "clearing_event", "reason", "tender", "escalation_ref"], order_by="creation asc")


class TestFindings(FindingsCase):
	def test_a_finding_is_appended_never_overwritten_and_changes_no_ceremony_state(self):
		incident = self.unreadable()
		doc = self.case_doc()
		version, state = doc.record_version, doc.state
		self.at(self.minutes_after(2))
		first = self.finding(incident, "Cannot recover", "The package cannot be rendered.", evidence_refs="LOG-1\nDIGEST-CHECK-1")
		self.assertTrue(first["ok"], first)
		self.at(self.minutes_after(5))
		second = self.finding(incident, "Recovered", "Renderer restored; digest comparison equals.", evidence_refs="DIGEST-CHECK-2", expected_revision=first["incident_revision"])
		self.assertTrue(second["ok"], second)
		rows = self.rows(incident)
		self.assertEqual([(r.finding_no, r.finding, r.incident_revision) for r in rows], [(1, "Cannot recover", 1), (2, "Recovered", 2)])  # the failed attempt is still there
		self.assertEqual((rows[0].reason, rows[0].evidence_refs, rows[0].recorded_by), ("The package cannot be rendered.", "LOG-1\nDIGEST-CHECK-1", SUPPORT))
		self.assertTrue(rows[0].opening_revision is not None and rows[0].last_committed_event)  # exact opening revision and last committed step
		row = self.incident_row(incident)
		self.assertEqual((row.current_finding, row.incident_revision, row.status), ("Recovered", 2, "Open"))
		after = self.case_doc()
		self.assertEqual((after.record_version, after.state), (version, state))  # a finding alone changes no ceremony state
		self.assertEqual(frappe.db.count("Opening Entry", {"opening_case": after.name}), 0)

	def test_a_finding_needs_a_reason_the_exact_revision_and_an_opening_access_support_holder(self):
		incident = self.unreadable()
		blank = self.finding(incident, "Recovered", "  ")
		self.assertEqual((blank["ok"], blank["errors"]), (False, {"reason": "Record what you found."}))
		self.assertEqual(self.rows(incident), [])
		first = self.finding(incident, "Unresolved", "Still checking the renderer.")
		with self.assertRaises(BidOpeningError) as stale:
			self.finding(incident, "Recovered", "Fixed.", expected_revision=first["incident_revision"] + 5)
		self.assertEqual(stale.exception.code, "BOP_VERSION_CONFLICT")
		for user in (CHAIR, AO, MEMBER, AUDITOR, OUTSIDER, SYSTEM_MANAGER, "Administrator"):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				self.finding(incident, "Recovered", "I should not be able to.", user=user)
		self.assertEqual(len(self.rows(incident)), 1)
		# a repeat with the same key returns the same answer and writes nothing more; the same key with another fact conflicts
		repeat_key = key()
		a = self.finding(incident, "Cannot recover", "Cannot be rendered.", idempotency_key=repeat_key)
		b = self.finding(incident, "Cannot recover", "Cannot be rendered.", idempotency_key=repeat_key)
		self.assertEqual(a, b)
		self.assertEqual(len(self.rows(incident)), 2)
		with self.assertRaises(BidOpeningError):
			self.finding(incident, "Recovered", "A different fact under the same key.", idempotency_key=repeat_key)
		self.assertEqual(len(self.rows(incident)), 2)

	def test_the_finding_carries_no_sealed_content_only_opaque_references(self):
		incident = self.unreadable()
		out = self.finding(incident, "Cannot recover", "Cannot be rendered.", evidence_refs="LOG-7")
		self.assertTrue(out["ok"])
		blob = repr(out) + repr(self.rows(incident))
		self.assertNotIn("Afya", blob)


class TestChairRoutes(FindingsCase):
	def test_recovered_lets_the_chair_retry_the_same_bid_once_and_clears_only_that_escalation(self):
		incident = self.unreadable()
		refused = ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual(refused["reason"], "incident_not_resolved")  # no Recovered finding yet
		self.finding(incident, "Cannot recover", "Cannot be rendered.")
		self.assertEqual([i["status"] for i in self.items()], ["Open"])
		cannot = ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual((cannot["ok"], cannot["reason"], cannot["message"]), (False, "cannot_recover", NOT_RECOVERED))
		resumed = ceremony.resume_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertEqual((resumed["ok"], resumed["reason"], resumed["message"]), (False, "cannot_recover", NOT_RECOVERED))  # Resume after Cannot recover is refused
		self.assertEqual(self.case_doc().state, "Interrupted")
		# a changed technical finding appends; the escalation instance stays until a committed Resume/Retry
		simulation.set_controls(render_outcome="Render")
		self.at(self.minutes_after(5))
		self.finding(incident, "Recovered", "Renderer restored.")
		self.assertEqual([i["status"] for i in self.items()], ["Open"])  # a finding never clears the item
		retried = ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.assertTrue(retried["ok"], retried)
		self.assertEqual(self.case_doc().state, "Opening")
		[item] = self.items()
		self.assertEqual(item["status"], "Cleared")  # cleared by the committed resume, not by the finding
		self.assertEqual(frappe.db.count("Opening Entry", {"opening_case": self.case_doc().name}), 1)  # the held bid was opened once

	def test_before_start_a_recovered_finding_lets_the_chair_begin_and_creates_no_start_until_then(self):
		self.ready_to_open()
		simulation.set_controls(opening_profile_down=1)
		self.at(self.minutes_after(5 / 60))
		self.heartbeat_all()
		self.assertEqual(self.sweep()["incidents"], 1)
		[incident] = incidents.open_incidents(self.case_doc().name)
		refused = self.begin()
		self.assertFalse(refused["ok"])
		self.assertEqual(self.case_doc().state, "Ready to open")
		simulation.set_controls(opening_profile_down=0)
		still = self.begin()  # the service is back, but support has recorded nothing: the open incident still blocks
		self.assertFalse(still["ok"])
		self.finding(incident, "Recovered", "The opening profile service is back.")
		self.assertEqual(frappe.db.get_value("Proceeding", self.case_doc().proceeding, "actual_start"), None)  # a finding creates no Start
		self.heartbeat_all()
		started = self.begin()
		self.assertTrue(started["ok"], started)
		self.assertEqual(self.case_doc().state, "Opening")
		row = self.incident_row(incident)
		self.assertEqual((row.status, row.closure), ("Closed", "Recovered and the opening continued"))  # closed by the committed Start, not by the finding

	def test_before_start_cannot_recover_gives_the_accounting_officer_the_one_item_and_not_held_reuses_it(self):
		self.ready_to_open()
		simulation.set_controls(opening_profile_down=1)
		self.at(self.minutes_after(5 / 60))
		self.heartbeat_all()
		self.sweep()
		[incident] = incidents.open_incidents(self.case_doc().name)
		self.finding(incident, "Cannot recover", "The opening profile cannot be restored.")
		[item] = self.items("Open")
		self.assertEqual((item["kind"], item["tender"], item["escalation_ref"]), ("Opening cannot proceed", self.name, incident.incident_id))
		self.assertFalse(self.begin()["ok"])
		# the Accounting Officer's turn is blocked while the Tender's verdict has a blocker (no verified ground here): every blocker is named, with its holder
		blocked = self.next_step(AO)
		self.assertEqual((blocked["kind"], blocked["headline"], blocked["primary_action"]), (ns.KIND_BLOCKED, "A tender decision is needed", "tender_decision"))
		self.assertEqual([b["reason_code"] for b in blocked["blockers"]], ["TND_CANCEL_GROUND_UNVERIFIED"])
		self.assertIn("Head of Procurement Function", blocked["blockers"][0]["figures"]["holder"])
		ground_verifier.set_controls(verified_cancellation_grounds="INADEQUATE_BUDGET")  # the legal basis is verified: the same item becomes an executable decision
		turn = self.next_step(AO)
		self.assertEqual((turn["kind"], turn["headline"], turn["primary_action"]), (ns.KIND_YOUR_TURN, "Decide what happens next", "tender_decision"))
		self.at(self.minutes_after(15))
		recorded = not_held.record_opening_not_held(tender=self.name, reason="The opening service could not be recovered.", expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.assertTrue(recorded["ok"], recorded)
		[same] = self.items()  # one item, relabelled, not a second
		self.assertEqual((same["name"], same["kind"], same["status"]), (item["name"], "Not held", "Open"))


class TestClosureAfterCancellation(FindingsCase):
	def test_a_cancelled_proceeding_closes_its_incident_with_the_reason_and_keeps_the_service_defect_open(self):
		incident = self.unreadable()
		self.finding(incident, "Cannot recover", "The package cannot be rendered.")
		result = self.cancel_tender()
		self.deliver()
		self.assertEqual(self.case_doc().state, "Cancelled after start")
		row = self.incident_row(incident)
		self.assertEqual((row.status, row.closure, row.closure_ref, row.current_finding, row.service_followup), ("Closed", "Closed after tender cancellation", result["cancellation"],
			"Cannot recover", "Open"))  # the service is NOT claimed repaired
		self.assertEqual(len(self.rows(incident)), 1)  # the finding survives
		self.assertEqual([i["status"] for i in self.items()], ["Cleared"])
		# a later finding on the closed incident settles only the separately owned service defect; the proceeding is untouched
		version = self.case_doc().record_version
		self.finding(incident, "Recovered", "The renderer was repaired after the proceeding ended.")
		self.assertEqual((self.incident_row(incident).service_followup, self.incident_row(incident).status), ("Resolved", "Closed"))
		self.assertEqual((self.case_doc().record_version, self.case_doc().state), (version, "Cancelled after start"))

	def test_a_recovered_incident_closes_with_the_committed_continuation_not_before(self):
		incident = self.unreadable()
		simulation.set_controls(render_outcome="Render")
		self.finding(incident, "Recovered", "Renderer restored.")
		self.assertEqual(self.incident_row(incident).status, "Open")  # recovered is a finding, not a closure
		self.at(self.minutes_after(5))
		self.assertTrue(ceremony.retry_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)["ok"])
		row = self.incident_row(incident)
		self.assertEqual((row.status, row.closure), ("Closed", "Recovered and the opening continued"))

	def test_a_decision_item_cannot_be_dismissed_by_a_note_or_an_acknowledgement(self):
		incident = self.unreadable()
		self.finding(incident, "Cannot recover", "Cannot be rendered.")
		for fn in (lambda: reads.get_opening(tender=self.name, user=AO), lambda: incident_access.get_details(tender=self.name, incident=incident.incident_id,
				purpose="Account for the opening", idempotency_key=key(), user=AO)):
			fn()
		self.assertEqual([i["status"] for i in self.items()], ["Open"])
		self.assertFalse(hasattr(incidents, "acknowledge"))
		self.assertFalse(hasattr(not_held, "acknowledge"))


class TestAccessMatrix(FindingsCase):
	def details(self, incident, user, purpose):
		return as_user(user, incident_access.get_details, tender=self.name, incident=incident.incident_id, purpose=purpose, idempotency_key=key(), user=user)

	def test_support_chair_accounting_officer_and_auditor_read_details_and_nobody_else_does(self):
		incident = self.unreadable()
		self.finding(incident, "Cannot recover", "Cannot be rendered.", evidence_refs="LOG-9")
		cases = (
			(SUPPORT, "Investigate the problem", True, True),
			(CHAIR, "Check the problem as a committee member", True, False),
			(AO, "Account for the opening", True, False),
			(AUDITOR, "Audit the opening", True, False),
		)
		for user, purpose, allowed, sees_envelope in cases:
			out = self.details(incident, user, purpose)
			self.assertTrue(out["ok"], user)
			details = out["details"]
			self.assertEqual(bool(details.get("envelope")), sees_envelope, user)  # the opaque identifier is the support holder's alone
			self.assertEqual([f["finding"] for f in details["findings"]], ["Cannot recover"], user)
			self.assertEqual(details["findings"][0]["evidence_refs"], "LOG-9", user)
			self.assertEqual(details["current_finding"], "Cannot recover", user)
		for user in (MEMBER, OUTSIDER, SYSTEM_MANAGER, "Administrator"):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				self.details(incident, user, "Investigate the problem")

	def test_every_detail_read_is_audited_with_its_purpose_and_outcome_and_the_trail_is_for_the_auditor_and_the_ao_only(self):
		incident = self.unreadable()
		self.details(incident, AUDITOR, "Audit the opening")
		with self.assertRaises(frappe.DoesNotExistError):
			self.details(incident, MEMBER, "Investigate the problem")
		trail = as_user(AUDITOR, incident_access.trail, tender=self.name, user=AUDITOR)
		self.assertEqual([(r["capacity"], r["outcome"]) for r in trail["rows"]], [("Auditor", "Allowed"), ("No capacity on this opening", "Refused")])
		self.assertEqual(as_user(AO, incident_access.trail, tender=self.name, user=AO)["rows"], trail["rows"])
		for user in (SUPPORT, CHAIR, SYSTEM_MANAGER, "Administrator"):
			with self.assertRaises(frappe.DoesNotExistError, msg=user):
				as_user(user, incident_access.trail, tender=self.name, user=user)

	def test_the_auditor_reads_but_records_nothing_and_a_page_refresh_audits_nothing(self):
		incident = self.unreadable()
		before = frappe.db.count(incident_access.EVENT, {"opening_case": self.case_doc().name})
		for user in (AUDITOR, AO, CHAIR, SUPPORT):
			as_user(user, reads.get_opening, tender=self.name, user=user)  # a refresh or poll
		self.assertEqual(frappe.db.count(incident_access.EVENT, {"opening_case": self.case_doc().name}), before)
		with self.assertRaises(frappe.DoesNotExistError):
			self.finding(incident, "Recovered", "An auditor may not record a finding.", user=AUDITOR)

	def test_an_administrator_or_system_manager_sees_no_incident_summary_on_the_opening_page(self):
		self.unreadable()
		for user in (SYSTEM_MANAGER, "Administrator"):
			try:
				view = as_user(user, reads.get_opening, tender=self.name, user=user)
			except frappe.DoesNotExistError:
				continue
			self.assertEqual(view["incidents"], [], user)
			self.assertIsNone(view["decision"], user)


class TestDecisionContext(FindingsCase):
	def test_the_tender_decision_screen_reads_the_opening_through_one_published_context(self):
		incident = self.unreadable()
		self.finding(incident, "Cannot recover", "Cannot be rendered.")
		[item] = self.items("Open")
		item_id = frappe.db.get_value(not_held.DECISION, item["name"], "decision_item_id")
		context = decision_context.get(tender=self.name, user=AO)
		self.assertEqual((context["item"], context["kind"], context["state"], context["finding"], context["incident"]), (item_id, item["kind"], "Interrupted", "Cannot recover", incident.incident_id))
		self.assertEqual(context["message"], NOT_RECOVERED)
		self.assertNotIn("envelope", repr(context))
		for user in (MEMBER, OUTSIDER, SYSTEM_MANAGER, SUPPORT):
			self.assertIsNone(decision_context.get(tender=self.name, user=user), user)  # the decision is the Accounting Officer's; support cannot decide for them
		view = reads.get_opening(tender=self.name, user=AO)["decision"]
		self.assertEqual((view["item"], view["tender_reference"], view["tender"]), (item_id, self.reference, self.name))
