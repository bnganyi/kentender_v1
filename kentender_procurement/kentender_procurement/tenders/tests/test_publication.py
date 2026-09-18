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
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import channel_confirmation, configuration_gateway, draft_commands as cmd, events, lifecycle, planning_gateway, publication, read
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
		self.assertEqual(frappe.db.count("Tender Publication"), 0)

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
		self.assertEqual(frappe.db.count("Tender Channel Confirmation", {"publication": root.publication, "status": "Confirmed"}), 0)

	def test_confirmations_are_attested_idempotent_and_conflicts_are_preserved(self):
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
		row.reload()
		self.assertEqual(str(row.available_at), AVAILABLE)
		self.assertTrue(events.exists(tender=name, event_type="ConfirmationConflictRejected"))
		self.assertEqual(frappe.db.get_value("Tender", name, "overall_status"), "Publication authorised")

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
		ws = read.get_tenders_workspace(user=fx.AUDITOR)
		row = next(r for r in ws["rows"] if r.get("tender") == name)
		self.assertEqual(row["status_label"], "Published — open until 5 Jun 2027, 11:00 EAT")
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
		self.assertTrue(frappe.db.exists("Tender Task", {"tender": name, "task_type": "AO publication authorisation", "status": "Open"}))
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
