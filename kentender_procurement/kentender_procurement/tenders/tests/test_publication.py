# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.5 / §7.3 / §15.3 — publication authorisation, channel
confirmation with evidence and attestation, the internal publication
confirmation, withdrawal, the Planning invitation actual, and every §15.3
integrity/concurrency boundary. TPR08-AC-039, 041..055."""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe

from kentender_core.tests.test_file_integrity import _hooks_with as no_file_scanners
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import channel_confirmation, configuration_gateway, draft_commands as cmd, events, lifecycle, my_work_provider, planning_gateway, publication, read, review
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample

CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")
AVAILABLE = "2027-05-15 08:00:00"


class PublicationCase(IntegrationTestCase):
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
		frappe.flags.kt_tenders_clock = "2027-05-15 07:55:00"
		self.addCleanup(setattr, frappe.flags, "kt_tenders_clock", None)

	def _approved(self, *, officer=fx.OFFICER) -> tuple[str, dict]:
		authorised = fx.authorised_handoff()
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=officer)
		root = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=root.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=root.record_version, idempotency_key=fx.key(), user=officer)
		root.reload()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=officer)
		root.reload()
		approved = lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		return root.name, approved

	def _authorised(self) -> tuple[str, dict]:
		name, approved = self._approved()
		root = frappe.get_doc("Tender", name)
		out = publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		return name, out

	def _confirm(self, name: str, channel: str, *, available_at=AVAILABLE, reference=None, evidence=None, url=None, key=None, user=fx.HOPF, notes="", attest=True, digest=None):
		root = frappe.get_doc("Tender", name)
		online = channel in configuration_gateway.ONLINE_CHANNELS
		return publication.confirm_publication_channel(
			tender=name, channel=channel, available_at=available_at, evidence_reference=reference or f"REF-{channel}", evidence_file=evidence or fx.evidence_file(f"{channel}.png"),
			public_url=(url if url is not None else (f"https://portal.example.test/{channel}" if online else "")), url_not_applicable_reason="" if online else "Physical channel",
			package_digest=digest or frappe.db.get_value("Tender Publication", root.publication, "package_digest"), expected_record_version=root.record_version, idempotency_key=key or fx.key(), evidence_notes=notes,
			attestation_confirmed=attest, user=user,
		)


class TestAuthorise(PublicationCase):
	def test_authorisation_records_the_decision_rule_snapshot_and_four_evidence_based_channels_and_nothing_else(self):
		name, out = self._authorised()
		root = frappe.get_doc("Tender", name)
		pub = frappe.get_doc("Tender Publication", out["publication"])
		self.assertEqual((root.overall_status, pub.publication_status, pub.authorised_by), ("Publication authorised", "Evidence required", fx.AO))
		self.assertEqual(pub.rule_snapshot_id, "PUB-RULE-MOH-OT-2027-01")
		# The canonical profile carries 21 days; a Planning test world in force on
		# this site may have superseded it (its fixture-verified minimum) — the
		# snapshot must equal whatever the resolver returned at authorisation.
		rule = configuration_gateway.resolve_publication_rule(applicability_date="2027-05-15")
		self.assertEqual(pub.minimum_preparation_days, rule["minimum_preparation_days"])
		self.assertGreater(pub.minimum_preparation_days, 0)
		self.assertEqual(pub.package_digest, frappe.db.get_value("Tender Version", pub.tender_version, "package_digest"))
		rows = frappe.get_all("Tender Channel Confirmation", filters={"publication": pub.name}, fields=["channel", "channel_label", "confirmation_mode", "status", "subject_digest"], order_by="creation asc")
		self.assertEqual([r.channel for r in rows], list(CHANNELS))
		self.assertEqual([r.channel_label for r in rows], ["State Portal", "Ministry website", "Notice board", "Two national newspapers"])
		self.assertTrue(all(r.confirmation_mode == "Evidence based" and r.status == "Awaiting confirmation" and r.subject_digest == pub.package_digest for r in rows))
		self.assertIsNone(root.published_at)
		event = [e for e in events.list_for_tender(name) if e["event_type"] == "PublicationAuthorised"][0]
		self.assertIsNone(event["payload"]["external_call"])
		self.assertEqual(len(event["payload"]["contributing_versions"]), 4)
		self.assertEqual(frappe.db.get_value("Tender Task", out["task"], "task_type"), "HOPF channel confirmation")
		ws = read.get_tenders_workspace(user=fx.HOPF)
		row = next(r for r in ws["rows"] if r.get("tender") == name)
		self.assertEqual((row["status_label"], row["action_label"], row["secondary"]), ("Publication confirmation required", "Complete confirmations", "State Portal and ministry website and notice board and two national newspapers confirmations"))

	def test_only_a_segregated_accounting_officer_authorises(self):
		name, approved = self._approved(officer=fx.BOTH)
		root = frappe.get_doc("Tender", name)
		with self.assertRaises(frappe.DoesNotExistError):  # not an AO: masked
			publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=approved["task"])
		with self.assertRaises(TendersError) as ctx:
			publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.BOTH, task=approved["task"])
		self.assertEqual(ctx.exception.code, "TND_SOD_BLOCKED")
		self.assertEqual(read.get_tender(tender=name, user=fx.BOTH)["segregation_message"], "You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function. Another Accounting Officer must decide it.")

	def test_an_infeasible_minimum_period_and_a_missing_rule_refuse_authorisation(self):
		name, approved = self._approved()
		root = frappe.get_doc("Tender", name)
		frappe.flags.kt_tenders_clock = "2027-06-03 09:00:00"  # 5 Jun is now only 2 days away
		with self.assertRaises(TendersError) as ctx:
			publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_PERIOD_INVALID")
		frappe.flags.kt_tenders_clock = "2027-05-15 07:55:00"
		with patch.object(configuration_gateway, "_versions_in_force", return_value=[]):
			with self.assertRaises(TendersError) as ctx:
				publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_RULE_UNAVAILABLE")
		self.assertEqual(frappe.db.count("Tender Publication", {"tender": root.name}), 0)

	def _draft_with(self, **changes):
		authorised = fx.authorised_handoff()
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		root = frappe.get_doc("Tender", started["tender"])
		values = {**sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), **changes}
		cmd.save_tender_draft(tender=root.name, values=values, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		return cmd.load(root.name)

	def _findings(self, root, version, code):
		return [f for f in review.run(root, version, with_renders=False)["findings"] if f["finding_code"] == code]

	def test_a_deadline_below_the_legal_minimum_is_caught_when_the_officer_reviews_it(self):
		# 5 days after the 15 May issue date; the verified legal minimum is 7
		root, version = self._draft_with(clarification_deadline="2027-05-17 17:00:00", submission_deadline="2027-05-20 11:00:00")
		found = [f for f in self._findings(root, version, "PUBLICATION_PERIOD") if f["severity"] == review.MUST_FIX]
		self.assertEqual([(f["task"], f["field"]) for f in found], [("details", "submission_deadline")])
		self.assertIn("at least 7 days after publication (the legal minimum)", found[0]["message"])
		root.reload()
		with self.assertRaises(TendersError) as ctx:
			lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(ctx.exception.code, "TND_MUST_FIX")

	def test_a_period_between_the_minimum_and_the_usual_needs_a_reason_but_never_blocks(self):
		# 15 days: lawful (7 or more) but shorter than the usual 21
		root, version = self._draft_with(submission_deadline="2027-05-30 11:00:00")
		self.assertFalse(self._findings(root, version, "PUBLICATION_PERIOD"))
		need = self._findings(root, version, "PERIOD_REASON")
		self.assertEqual([(f["severity"], f["field"]) for f in need], [(review.MUST_FIX, "shortened_period_reason")])
		self.assertIn("15 days, shorter than the usual 21", need[0]["message"])
		# with the reason: no blocker, and the reason stays in front of the approvers as a Review note
		root.reload()
		cmd.save_tender_draft(tender=root.name, values={"shortened_period_reason": "The clinics need these laptops before the October training."}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root, version = cmd.load(root.name)
		self.assertFalse(self._findings(root, version, "PERIOD_REASON"))
		note = self._findings(root, version, "NOTE_SHORT_PERIOD")
		self.assertEqual([f["severity"] for f in note], [review.REVIEW_NOTE])
		self.assertIn("Reason given: The clinics need these laptops before the October training.", note[0]["message"])
		root.reload()
		submitted = lifecycle.submit_tender_for_approval(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		lifecycle.approve_tender_package(tender=root.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF, task=submitted["task"])
		# both approvers read the note and the reason itself
		for user in (fx.HOPF, fx.AO):
			pub = publication.get_tender_publication(tender=root.name, user=user)
			self.assertEqual([n["finding_code"] for n in pub["review"]["review_notes"] if n["finding_code"] == "NOTE_SHORT_PERIOD"], ["NOTE_SHORT_PERIOD"])
			facts = {f["label"]: f["value"] for sec in pub["sections"] for blk in sec.get("blocks", []) if blk.get("kind") == "facts" for f in blk["facts"]}
			self.assertEqual(facts.get("Reason for a shorter tendering period"), "The clinics need these laptops before the October training.")
		# 15 days is lawful, so authorisation is open to the Accounting Officer
		self.assertIn("authorise_publication", read.get_tender(tender=root.name, user=fx.AO)["allowed_actions"])
		self.assertIsNone(read.get_tender(tender=root.name, user=fx.AO)["period_problem"])

	def test_the_form_is_given_the_two_numbers_to_pre_fill_and_hint_from(self):
		root, version = self._draft_with()
		rule = read.get_tender(tender=root.name, user=fx.OFFICER)["period_rule"]
		self.assertEqual(rule, {"minimum_days": 7, "default_days": 21, "closing_time": "11:00"})

	def test_a_period_that_ran_short_after_approval_is_stated_up_front_with_the_way_out(self):
		name, approved = self._approved()
		frappe.flags.kt_tenders_clock = "2027-06-03 09:00:00"  # 5 Jun is now only 2 days away
		ao = read.get_tender_publication(tender=name, user=fx.AO) if hasattr(read, "get_tender_publication") else publication.get_tender_publication(tender=name, user=fx.AO)
		self.assertNotIn("authorise_publication", ao["allowed_actions"])
		self.assertEqual({k: ao["period_problem"][k] for k in ("minimum_days", "earliest_deadline")}, {"minimum_days": 7, "earliest_deadline": "2027-06-10"})
		step = ao["guidance"]["next_step"]
		self.assertEqual((step["kind"], step["blockers"][0]["reason_code"]), ("your_turn_blocked", "TND_PUBLICATION_PERIOD_INVALID"))
		fixes = {f["label"]: f for f in step["blockers"][0]["fixes"]}
		self.assertEqual((fixes["Return to Head of Procurement Function"]["responsibility"], fixes["Return to Head of Procurement Function"]["kind"]), ("Accounting Officer", "command"))
		self.assertEqual(fixes["Reopen Tender"]["responsibility"], "Head of Procurement Function")
		hopf = publication.get_tender_publication(tender=name, user=fx.HOPF)
		self.assertIn("reopen_tender", hopf["allowed_actions"])
		self.assertEqual((hopf["guidance"]["next_step"]["kind"], hopf["guidance"]["next_step"]["primary_action"]), ("your_turn", "reopen_tender"))
		officer = publication.get_tender_publication(tender=name, user=fx.OFFICER)
		self.assertEqual(officer["guidance"]["next_step"]["kind"], "waiting")
		self.assertEqual(officer["guidance"]["next_step"]["holder"]["role"], "Head of Procurement Function")
		# the same Tender with time to spare shows no problem and the AO's decision
		frappe.flags.kt_tenders_clock = "2027-05-15 07:55:00"
		ok = publication.get_tender_publication(tender=name, user=fx.AO)
		self.assertIsNone(ok["period_problem"])
		self.assertIn("authorise_publication", ok["allowed_actions"])

	def test_a_blocked_authorisation_puts_the_reopen_on_the_head_of_procurements_work_list(self):
		name, approved = self._approved()
		ref = frappe.db.get_value("Tender", name, "tender_reference")
		title = f"Reopen Tender {ref} — submission deadline too short"
		# enough time: nothing for anyone
		for user in (fx.HOPF, fx.AO, fx.OFFICER):
			rows = my_work_provider.my_work_rows(user=user)
			self.assertFalse([r for r in rows["assigned"] + rows["waiting"] if "Reopen Tender" in r["title"] or "to reopen Tender" in r["title"]])
		frappe.flags.kt_tenders_clock = "2027-06-03 09:00:00"  # 5 Jun is now only 2 days away
		hopf = my_work_provider.my_work_rows(user=fx.HOPF)["assigned"]
		row = next(r for r in hopf if r["title"] == title)
		self.assertEqual((row["action_label"], row["route"], row["status"]), ("Reopen Tender", ["tenders", ref], "Assigned"))
		self.assertIn("7 are required", row["comment"])
		ao = my_work_provider.my_work_rows(user=fx.AO)
		waiting = [r["title"] for r in ao["waiting"] if "reopen" in r["title"]]
		self.assertEqual(len(waiting), 1)  # every current Head of Procurement Function is named, as for any hand-off with no named person
		self.assertTrue(waiting[0].startswith("Waiting for ") and waiting[0].endswith(f" to reopen Tender {ref}") and frappe.db.get_value("User", fx.HOPF, "full_name") in waiting[0])
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.OFFICER)["assigned"] if "Reopen" in r["title"]])
		# the business transition clears it: once the Tender is reopened it is no longer Approved
		root = frappe.get_doc("Tender", name)
		lifecycle.reopen_approved_tender(tender=name, reason="The submission deadline must leave 21 days after publication.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.HOPF)["assigned"] if r["title"] == title])
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.AO)["waiting"] if "reopen" in r["title"]])

	def test_the_accounting_officer_can_return_an_approved_package_to_the_head_of_procurement(self):
		name, approved = self._approved()
		root = frappe.get_doc("Tender", name)
		ref = root.tender_reference
		ao = publication.get_tender_publication(tender=name, user=fx.AO)
		self.assertIn("return_to_hopf", ao["allowed_actions"])
		self.assertIn("authorise_publication", ao["allowed_actions"])
		reason = "The delivery location in the package does not match the stores plan; please correct before I authorise."
		with self.assertRaises(TendersError) as ctx:  # a reason is required
			publication.return_approved_tender(tender=name, reason="too short", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		self.assertEqual(ctx.exception.code, "TND_CONTROL_INVALID")
		with self.assertRaises(frappe.DoesNotExistError):  # only an Accounting Officer: masked
			publication.return_approved_tender(tender=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		key = fx.key()
		out = publication.return_approved_tender(tender=name, reason=reason, expected_record_version=root.record_version, idempotency_key=key, user=fx.AO)
		self.assertEqual((out["action"], out["idempotent"]), ("returned", False))
		root.reload()
		# the approved Version is kept and nothing is published; the decision is recorded with its reason
		self.assertEqual((root.overall_status, root.publication), ("Approved", None))
		self.assertEqual(frappe.db.get_value("Tender Decision", {"tender": name, "decision": "Return approved Tender to Head of Procurement Function"}, ["actor", "reason"], as_dict=True), {"actor": fx.AO, "reason": reason})
		self.assertEqual(publication.return_approved_tender(tender=name, reason=reason, expected_record_version=root.record_version, idempotency_key=key, user=fx.AO)["idempotent"], True)
		with self.assertRaises(TendersError) as ctx:  # one open return at a time
			publication.return_approved_tender(tender=name, reason=reason + " again", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		# hand-off: the head of procurement holds it with the reason; the AO waits; nobody else is offered a decision
		item = next(r for r in my_work_provider.my_work_rows(user=fx.HOPF)["assigned"] if r["title"] == f"Review Tender {ref} returned by the Accounting Officer")
		self.assertEqual((item["action_label"], item["comment"]), ("Reopen Tender", reason))
		waiting = [r["title"] for r in my_work_provider.my_work_rows(user=fx.AO)["waiting"] if "to reopen Tender" in r["title"]]
		self.assertEqual(len(waiting), 1)
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.AO)["assigned"] if r["title"].startswith("Authorise publication of Tender " + ref)])
		after = publication.get_tender_publication(tender=name, user=fx.AO)
		self.assertNotIn("authorise_publication", after["allowed_actions"])
		self.assertNotIn("return_to_hopf", after["allowed_actions"])
		self.assertEqual(after["guidance"]["next_step"]["kind"], "waiting")
		self.assertEqual(after["guidance"]["next_step"]["holder"]["role"], "Head of Procurement Function")
		hopf = publication.get_tender_publication(tender=name, user=fx.HOPF)
		step = hopf["guidance"]["next_step"]
		self.assertEqual((step["kind"], step["primary_action"]), ("your_turn", "reopen_tender"))
		self.assertIn(reason, step["sentence"])
		# the HOPF's Reopen is the existing mechanics: copied Draft, officer correction task, and the return item clears
		root.reload()
		lifecycle.reopen_approved_tender(tender=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.HOPF)["assigned"] if "returned by the Accounting Officer" in r["title"]])
		self.assertFalse([r for r in my_work_provider.my_work_rows(user=fx.AO)["waiting"] if "to reopen Tender" in r["title"]])
		self.assertTrue([r for r in my_work_provider.my_work_rows(user=fx.OFFICER)["assigned"] if r["title"] == f"Correct reopened Tender {ref}"])

	def test_the_accounting_officer_cannot_authorise_while_their_return_is_open(self):
		"""AUD-TND-003 (§5.1, TPR16-AC-015): an open return leaves the AO neither Authorise nor Return, on the server and not only in the read."""
		name, approved = self._approved()
		root = frappe.get_doc("Tender", name)
		reason = "The delivery location in the package does not match the stores plan; please correct before I authorise."
		publication.return_approved_tender(tender=name, reason=reason, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		root.reload()
		with self.assertRaises(TendersError) as ctx:
			publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		with self.assertRaises(TendersError) as ctx:  # even carrying the (now cancelled) task it was offered before the return
			publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.assertEqual(ctx.exception.code, "TND_STALE_VERSION")
		root.reload()
		self.assertEqual((root.overall_status, root.publication), ("Approved", None))
		# the HOPF's return item is still theirs to clear by Reopen
		self.assertTrue([r for r in my_work_provider.my_work_rows(user=fx.HOPF)["assigned"] if "returned by the Accounting Officer" in r["title"]])

	def test_digests_and_rule_identifiers_stay_under_technical_details(self):
		"""v0.16 §10.8 item 2 and §10.9 item 4 (owner, 2 Oct 2026): no digest or rule identifier in a business-facing line."""
		name, approved = self._approved()
		trail = publication.get_tender_publication(tender=name, user=fx.AO)["approval_trail"]
		self.assertNotIn("package_digest", trail)
		self.assertEqual(sorted(trail), ["approved_at_label", "approved_by_name", "prepared_by_name", "version_number"])
		root = frappe.get_doc("Tender", name)
		out = publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		summary = publication.get_tender_publication(tender=name, user=fx.HOPF)["publication"]
		self.assertNotRegex(summary["rule_line"], r"digest|PUB-RULE|[0-9a-f]{32}")
		technical = {f["label"]: f["value"] for f in summary["technical_facts"]}
		self.assertEqual(technical["Publication rule"], "PUB-RULE-MOH-OT-2027-01")
		self.assertEqual(technical["Package digest"], frappe.db.get_value("Tender Publication", out["publication"], "package_digest"))

	def test_an_integrated_channel_is_refused(self):
		name, approved = self._approved()
		root = frappe.get_doc("Tender", name)
		original = configuration_gateway._versions_in_force

		def with_integration(date, *, trigger):
			rows = original(date, trigger=trigger)
			if rows:
				rows[0]["payload"]["integration_evidence_contract_code"] = "STATE-PORTAL-API-1"
			return rows

		with patch.object(configuration_gateway, "_versions_in_force", side_effect=with_integration):
			with self.assertRaises(TendersError) as ctx:
				publication.authorise_tender_publication(tender=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO, task=approved["task"])
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_RULE_UNAVAILABLE")


class TestConfirmChannels(PublicationCase):
	def test_each_channel_needs_evidence_reference_url_rule_file_and_attestation(self):
		name, _ = self._authorised()
		root = frappe.get_doc("Tender", name)
		digest_value = frappe.db.get_value("Tender Publication", root.publication, "package_digest")
		for user in (fx.AO, fx.OFFICER, fx.AUDITOR):
			with self.assertRaises((TendersError, frappe.DoesNotExistError)):
				self._confirm(name, "NOTICE_BOARD", user=user)
		with self.assertRaises(TendersError) as ctx:
			publication.confirm_publication_channel(tender=name, channel="NOTICE_BOARD", available_at="", evidence_reference="", evidence_file="", package_digest=digest_value, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_CONFIRMATION_INCOMPLETE")
		self.assertEqual(set(ctx.exception.detail["fields"]), {"available_at", "evidence_reference", "evidence_file", "attestation"})
		with self.assertRaises(TendersError) as ctx:
			self._confirm(name, "STATE_PORTAL", url="")
		self.assertIn("public_url", ctx.exception.detail["fields"])
		with self.assertRaises(TendersError) as ctx:
			self._confirm(name, "NOTICE_BOARD", notes="x" * 501)
		self.assertIn("evidence_notes", ctx.exception.detail["fields"])
		with self.assertRaises(TendersError) as ctx:
			self._confirm(name, "NOTICE_BOARD", digest="0" * 64)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_DIGEST_MISMATCH")
		with self.assertRaises(TendersError) as ctx:  # §15.3(5) invalid media
			self._confirm(name, "STATE_PORTAL", evidence=frappe.get_doc({"doctype": "File", "file_name": "PPIP-MOH-2027-035.exe", "is_private": 1, "content": b"MZ\x00\x00"}).insert(ignore_permissions=True).name)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_EVIDENCE_INVALID")
		# §10.17 DES-08: the refusal carries its blocked next step and fixes
		step = ctx.exception.detail["next_step"]
		self.assertEqual((step["kind"], step["headline"], step["stage"]), ("your_turn_blocked", "State Portal evidence could not be accepted.", "PUBLICATION"))
		self.assertEqual([f["label"] for f in step["blockers"][0]["fixes"]], ["Choose evidence file", "Confirm publication"])
		self.assertEqual([s["marker"] for s in ctx.exception.detail["guidance"]["journey"]["stages"]], ["done", "done", "done", "blocked", "not_started"])
		self.assertEqual(frappe.db.count("Tender Channel Confirmation", {"publication": root.publication, "status": "Confirmed"}), 0)

	def test_confirmations_are_attested_idempotent_and_conflicts_are_preserved(self):
		self.enterContext(no_file_scanners([]))  # the no-scanner verdict, whatever the site registers
		name, _ = self._authorised()
		key = fx.key()
		first = self._confirm(name, "STATE_PORTAL", key=key)
		self.assertEqual((first["status"], first["attested_by"], first["all_confirmed"]), ("Confirmed", fx.HOPF, False))
		row = frappe.get_doc("Tender Channel Confirmation", first["confirmation"])
		self.assertEqual(row.attestation_text, "I confirm that the exact approved Tender package was publicly available through the State Portal at the date and time stated above.")
		self.assertEqual(row.evidence_check_result, "Not scanned — no scanner configured")
		self.assertEqual(len(row.evidence_digest), 64)
		replay = self._confirm(name, "STATE_PORTAL", key=key, evidence=row.evidence_file)  # §15.3(2) identical replay by key
		self.assertTrue(replay["idempotent"])
		same_again = self._confirm(name, "STATE_PORTAL", evidence=row.evidence_file)  # identical content, new key
		self.assertEqual(same_again["action"], "already_confirmed")
		with self.assertRaises(TendersError) as ctx:  # §15.3(3) different availability time
			self._confirm(name, "STATE_PORTAL", available_at="2027-05-15 09:30:00", evidence=row.evidence_file)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_ALREADY_CONFIRMED")
		step = ctx.exception.detail["next_step"]
		self.assertEqual((step["kind"], step["headline"], [f["label"] for f in step["fixes"]]), ("your_turn", "Continue with the channels still awaiting confirmation.", ["View confirmation for State Portal"]))
		row.reload()
		self.assertEqual(str(row.available_at), AVAILABLE)
		self.assertTrue(events.exists(tender=name, event_type="ConfirmationConflictRejected"))
		self.assertEqual(frappe.db.get_value("Tender", name, "overall_status"), "Publication authorised")

	def test_a_conflicting_confirmation_audit_record_survives_the_refusal_the_request_rolls_back(self):
		"""AUD-TND-005 (§5.8(10), §12.1): the refusal ends the request in a rollback; the audit fact must already be committed."""
		from kentender_procurement.tenders import api

		self.enterContext(no_file_scanners([]))
		name, _ = self._authorised()
		first = self._confirm(name, "STATE_PORTAL")
		row = frappe.get_doc("Tender Channel Confirmation", first["confirmation"])
		root = frappe.get_doc("Tender", name)
		frappe.db.commit()  # the world under test is durable; only the refusal's own writes are in question
		frappe.set_user(fx.HOPF)
		with self.assertRaises(TendersError) as ctx:
			api.confirm_publication_channel(
				tender=name, channel="STATE_PORTAL", available_at="2027-05-15 09:30:00", evidence_reference="REF-STATE_PORTAL", evidence_file=row.evidence_file, package_digest=frappe.db.get_value("Tender Publication", root.publication, "package_digest"),
				expected_record_version=root.record_version, idempotency_key=fx.key(), public_url="https://portal.example.test/STATE_PORTAL", attestation_confirmed=True,
			)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_ALREADY_CONFIRMED")
		frappe.db.rollback()  # what Frappe does with an uncaught exception in a request
		event = frappe.db.get_value("Tender Event", {"tender": name, "event_type": "ConfirmationConflictRejected"}, ["subject_id", "payload"], as_dict=True)
		self.assertIsNotNone(event, "the conflict audit event was rolled back with the refusal")
		self.assertEqual(event.subject_id, row.name)
		self.assertEqual(frappe.db.get_value("Tender Channel Confirmation", row.name, "status"), "Confirmed")

	def test_the_final_channel_publishes_once_at_the_latest_availability_and_writes_planning_once(self):
		name, _ = self._authorised()
		root = frappe.get_doc("Tender", name)
		self._confirm(name, "STATE_PORTAL")
		self._confirm(name, "MINISTRY_WEBSITE", available_at="2027-05-15 08:20:00")
		self._confirm(name, "NOTICE_BOARD")
		self.assertEqual(frappe.db.get_value("Tender", name, "overall_status"), "Publication authorised")
		with self.assertRaises(TendersError) as ctx:  # AC-055: withdrawal blocked once a channel is confirmed
			publication.withdraw_publication_authorisation(tender=name, reason="Publication did not take place through any channel.", evidence="Portal log shows no posting.", expected_record_version=frappe.db.get_value("Tender", name, "record_version"), idempotency_key=fx.key(), user=fx.AO)
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_WITHDRAWAL_BLOCKED")
		final = self._confirm(name, "NATIONAL_NEWSPAPERS")
		self.assertTrue(final["all_confirmed"])
		root.reload()
		pub = frappe.get_doc("Tender Publication", root.publication)
		self.assertEqual((root.overall_status, pub.publication_status), ("Published — open", "Published"))
		self.assertEqual(str(root.published_at), "2027-05-15 08:20:00")  # latest available_at, not the entry time
		self.assertEqual(str(pub.published_at), "2027-05-15 08:20:00")
		self.assertTrue(pub.publication_digest)
		actual = planning_gateway.current_invitation_actual(root)
		self.assertEqual(str(actual), "2027-05-15")
		planning_events = [e for e in events.list_for_tender(name) if e["event_type"] == "TenderPublished"]
		self.assertEqual([(e["status"], e["consumer"]) for e in planning_events], [("Delivered", "planning")])
		self.assertEqual(final["completed"]["planning"]["ok"], True)
		# §15.3(8) replay of the internal event emits nothing new
		again = planning_gateway.publish_invitation_actual(root=root, publication=pub, published_at=root.published_at, actor=fx.HOPF, idempotency_key=fx.key())
		self.assertTrue(again["idempotent"])
		self.assertEqual(frappe.db.count("Tender Event", {"tender": name, "event_type": "TenderPublished"}), 1)
		self.assertEqual(frappe.db.count("Milestone Actual Event", {"plan_item_id": root.plan_item_id, "milestone": "invitation"}), 1)
		self.assertEqual(frappe.db.get_value("Tender Event", {"tender": name, "event_type": "TenderOpenForSubmission"}, "status"), "Pending")
		ws = read.get_tenders_workspace(user=fx.HOPF)
		row = next(r for r in ws["rows"] if r.get("tender") == name)
		self.assertEqual(row["status_label"], "Published — open until 5 Jun 2027, 11:00 EAT")
		# TPR-DES-01-READER: an Auditor sees the neutral status only
		ws = read.get_tenders_workspace(user=fx.AUDITOR)
		row = next(r for r in ws["rows"] if r.get("tender") == name)
		self.assertEqual(row["status_label"], "Published — open")
		record = read.get_tender(tender=name, user=fx.HOPF)
		self.assertEqual(record["screen"], "published")
		self.assertEqual(sorted(a for a in record["allowed_actions"] if a != "view_history"), ["prepare_addendum", "recommend_cancellation", "view_publication"])
		self.assertEqual(record["publication"]["progress_text"], "4 of 4 required channels confirmed")

	def test_withdrawal_before_any_confirmation_returns_the_tender_to_approved(self):
		name, out = self._authorised()
		root = frappe.get_doc("Tender", name)
		withdrawn = publication.withdraw_publication_authorisation(tender=name, reason="The portal placement was never made; the notice must be re-timed.", evidence="Portal placement log shows no entry for this reference.", expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.AO)
		root.reload()
		pub = frappe.get_doc("Tender Publication", withdrawn["publication"])
		self.assertEqual((root.overall_status, root.publication, pub.publication_status, pub.withdrawn_by), ("Approved", None, "Withdrawn before confirmation", fx.AO))
		self.assertEqual(frappe.db.get_value("Tender Task", out["task"], "status"), "Cancelled")
		# §5.11: the HOPF reviews the withdrawn authorisation (not a new AO item)
		self.assertTrue(frappe.db.exists("Tender Task", {"tender": name, "task_type": "Review withdrawn authorisation", "status": "Open"}))
		self.assertIn("reopen_tender", read.get_tender(tender=name, user=fx.HOPF)["allowed_actions"])


class TestIntegrity(PublicationCase):
	def test_a_failed_confirmation_transaction_leaves_no_confirmed_state_and_the_upload_reusable(self):
		"""§15.3(4): the evidence upload succeeds, the confirmation write fails."""
		name, _ = self._authorised()
		evidence = fx.evidence_file("NB-MOH-2027-033.png")
		with patch.object(events, "emit", side_effect=RuntimeError("boom")):
			with self.assertRaises(RuntimeError):
				self._confirm(name, "NOTICE_BOARD", evidence=evidence)
		self.assertEqual(frappe.db.count("Tender Channel Confirmation", {"tender": name, "status": "Confirmed"}), 0)
		self.assertTrue(frappe.db.exists("File", evidence))
		ok = self._confirm(name, "NOTICE_BOARD", evidence=evidence)
		self.assertEqual(ok["status"], "Confirmed")

	def test_an_infected_scan_cannot_confirm_a_channel(self):
		"""§15.3(5): a registered scanner verdict of Infected refuses the file."""
		name, _ = self._authorised()
		real = frappe.get_hooks

		def hooks(hook=None, *args, **kwargs):
			return ["kentender_core.tests.test_file_integrity._scanner_infected"] if hook == "kt_file_scanners" else real(hook, *args, **kwargs)

		with patch.object(frappe, "get_hooks", side_effect=hooks):
			with self.assertRaises(TendersError) as ctx:
				self._confirm(name, "NOTICE_BOARD")
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_EVIDENCE_INVALID")
		self.assertEqual(frappe.db.count("Tender Channel Confirmation", {"tender": name, "status": "Confirmed"}), 0)

	def test_a_late_deadline_cannot_become_published_and_the_final_confirmation_is_serialised(self):
		"""§5.5(6) and §15.3(7): with `published_at` after the deadline minus
		the minimum period the Tender stays unpublished; the final channel's
		publication runs once under the Publication row lock, so a second
		identical final confirmation returns the same result."""
		name, _ = self._authorised()
		for channel in CHANNELS[:3]:
			self._confirm(name, channel)
		with self.assertRaises(TendersError) as ctx:
			self._confirm(name, "NATIONAL_NEWSPAPERS", available_at="2027-06-04 08:00:00")
		self.assertEqual(ctx.exception.code, "TND_PUBLICATION_PERIOD_INVALID")
		self.assertEqual(frappe.db.get_value("Tender Channel Confirmation", {"tender": name, "channel": "NATIONAL_NEWSPAPERS"}, "status"), "Awaiting confirmation")
		self.assertEqual(frappe.db.get_value("Tender", name, "overall_status"), "Publication authorised")
		key = fx.key()
		first = self._confirm(name, "NATIONAL_NEWSPAPERS", key=key)
		second = self._confirm(name, "NATIONAL_NEWSPAPERS", key=key, evidence=frappe.db.get_value("Tender Channel Confirmation", first["confirmation"], "evidence_file"))
		self.assertEqual((first["completed"]["published_at"], second["idempotent"]), (str(frappe.db.get_value("Tender", name, "published_at")), True))
		self.assertEqual(frappe.db.count("Tender Event", {"tender": name, "event_type": "TenderPublishedOpen"}), 1)
		self.assertEqual(json.loads(frappe.db.get_value("Tender Event", {"tender": name, "event_type": "TenderPublishedOpen"}, "payload"))["resulting_status"], "Published — open")
