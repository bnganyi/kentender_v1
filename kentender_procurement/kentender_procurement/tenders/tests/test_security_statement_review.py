# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Project Owner, 10 October 2026: a Tender published before it had to state how its tender security may be submitted is
listed for an explicit review; nothing invents a physical requirement for it or changes what it published."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F, world as W  # noqa: F401
import json

import frappe

from kentender_procurement.tenders.services import addenda, bid_definition, draft_commands as cmd, security_statement, template_binding, security_statement_review as review
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests.test_open_period import OpenPeriodCase


class StatementCase(OpenPeriodCase):
	def setUp(self):
		super().setUp()
		self.reference = self._root().tender_reference

	def _strip(self):
		"""Make this published Tender look as one published before the statements existed."""
		current = bid_definition.current(self.name)
		definition = current["definition"]
		for section in definition["sections"]:
			for group in section["groups"]:
				if group["rule_id"] == review.SECURITY_RULE:
					group["published_facts"].pop("submission_method", None)
					group["published_facts"].pop("original_delivery", None)
		frappe.db.set_value("Tender Bid Definition", current["name"], "definition_json", json.dumps(definition), update_modified=False)
		# and the officer's own state, which such a Tender never carried
		version = self._root().approved_version or self._root().current_version
		state = json.loads(frappe.db.get_value("Tender Version", version, "officer_payload_json") or "{}")
		state["tender_security_method"] = state["tender_security_original"] = None
		frappe.db.set_value("Tender Version", version, "officer_payload_json", json.dumps(state), update_modified=False)



class TestSecurityStatementReview(StatementCase):
	def test_a_tender_that_states_both_is_not_listed(self):
		self.assertNotIn(self.reference, [r["tender_reference"] for r in review.unstated()])

	def test_a_tender_published_without_them_is_listed_and_nothing_is_changed(self):
		self._strip()
		before = frappe.db.get_value("Tender Bid Definition", bid_definition.current(self.name)["name"], "definition_json")
		listed = [r["tender_reference"] for r in review.unstated()]
		self.assertIn(self.reference, listed)
		self.assertEqual(frappe.db.get_value("Tender Bid Definition", bid_definition.current(self.name)["name"], "definition_json"), before)  # reading writes nothing

	def test_the_review_is_for_the_people_who_run_tenders(self):
		self._strip()
		view = review.get_security_statement_review(user=fx.OFFICER)
		self.assertIn(self.reference, [r["tender_reference"] for r in view["rows"]])
		self.assertIn("do not state how tender security may be submitted", view["text"])
		with self.assertRaises(frappe.DoesNotExistError):
			review.get_security_statement_review(user=fx.NOBODY)


UPLOAD, ISSUER, PAPER = "Bidder uploads an electronic instrument", "Issuer supplies the instrument directly", "Paper instrument requiring an original"
BASIS = "Schedule 2 of the issued Tender Data Sheet already requires the original to be delivered before the deadline."


class TestCorrectionAndAddendum(StatementCase):
	"""Project Owner, 10 October 2026: missing system data for a requirement the published Tender already makes explicit is an
	auditable correction; a requirement that genuinely changes is a formal addendum before closing. Closed Tenders keep theirs."""

	def correct(self, **kw):
		values = dict(tender=self.name, submission_method=PAPER, original_delivery="Required", source_reference="Tender Data Sheet, ITT 18.1", basis=BASIS, expected_record_version=self._root().record_version, idempotency_key=fx.key(), user=fx.HOPF)
		values.update(kw)
		return security_statement.correct_security_statement(**values)

	def test_a_correction_records_the_published_requirement_and_changes_nothing_published(self):
		self._strip()
		before = frappe.db.get_value("Tender Bid Definition", bid_definition.current(self.name)["name"], "definition_json")
		done = self.correct()
		self.assertTrue(done["ok"], done)
		row = frappe.get_doc("Tender Security Statement", done["statement"])
		self.assertEqual((row.submission_method, row.original_delivery, row.corrected_by, row.source_reference), (PAPER, "Required", fx.HOPF, "Tender Data Sheet, ITT 18.1"))
		self.assertEqual(frappe.db.get_value("Tender Bid Definition", bid_definition.current(self.name)["name"], "definition_json"), before)  # the published definition is untouched
		self.assertEqual(security_statement.overlay(self.name), {"submission_method": PAPER, "original_delivery": "Required"})
		self.assertNotIn(self.reference, [r["tender_reference"] for r in review.unstated()])  # no longer awaiting review
		event = frappe.get_all("Tender Event", filters={"tender": self.name, "event_type": "TenderSecurityStatementCorrected"}, fields=["name"])
		self.assertEqual(len(event), 1)

	def test_only_the_head_corrects_only_a_tender_without_statements_and_only_once(self):
		with self.assertRaises(frappe.DoesNotExistError):
			self.correct(user=fx.OFFICER)
		with self.assertRaises(TendersError):  # this Tender already states both
			self.correct()
		self._strip()
		refused = self.correct(basis="Too short", source_reference="")
		self.assertEqual((refused["ok"], sorted(refused["errors"])), (False, ["basis", "source_reference"]))
		inconsistent = self.correct(submission_method=PAPER, original_delivery="Not required")
		self.assertEqual(sorted(inconsistent["errors"]), ["original_delivery"])
		self.assertTrue(self.correct()["ok"])
		with self.assertRaises(TendersError):  # one correction per Tender: a change is an addendum
			self.correct(submission_method=ISSUER, original_delivery="Not required")

	def test_the_security_rows_are_amendable_by_addendum_and_never_material(self):
		rows = {r["key"]: r for r in addenda.affected_references(self._root())}
		for key, options in (("tender_security_method", [UPLOAD, ISSUER, PAPER]), ("tender_security_original", ["Required", "Not required"])):
			self.assertEqual((rows[key]["material"], rows[key]["options"]), (False, options))
		self.assertEqual((rows["tender_security_method"]["value"], rows["tender_security_original"]["value"]), (UPLOAD, "Required"))

	def test_a_change_is_a_formal_addendum_with_a_deadline_and_a_successor_definition(self):
		frappe.flags.kt_tenders_clock = W("2027-05-31 08:30:00")  # inside the late-amendment window: a revised deadline is required
		values = {"change_class": "Non-material correction", "affected_area": "Submission or opening detail", "affected_reference_key": "tender_security_method", "revised_value": ISSUER,
			"reason": "The issuer will supply the instrument directly to the Procuring Entity.", "materiality_statement": "No change to the amount, form, expiry or evaluation basis."}
		name = self._addendum(values=values)
		doc = frappe.get_doc("Tender Addendum", name)
		self.assertEqual((doc.previous_value, doc.deadline_extension_required), (UPLOAD, 1))
		root = self._root()
		with self.assertRaises(TendersError) as caught:
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(caught.exception.code, "TND_ADDENDUM_DEADLINE_REQUIRED")
		bad = addenda.update_addendum_draft(tender=self.name, addendum=name, values={"revised_value": "Courier"}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertIn("revised_value", bad["errors"])
		root.reload()
		addenda.update_addendum_draft(tender=self.name, addendum=name, values={"revised_submission_deadline": W("2027-06-12 11:00:00")}, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		root.reload()
		frappe.flags.kt_tenders_clock = W("2027-05-31 09:00:00")
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		successor = frappe.get_doc("Tender Bid Definition", frappe.db.get_value("Tender Addendum", name, "successor_bid_definition"))
		facts = next(g["published_facts"] for s in json.loads(successor.definition_json)["sections"] for g in s["groups"] if g["rule_id"].startswith("RR-TENDER-SECURITY"))
		self.assertEqual(facts["submission_method"], ISSUER)  # the successor carries the amended statement; the prior definition stays bidder-current until confirmed
		self.assertEqual(bid_definition.current(self.name)["definition_version"], 1)

	def test_a_paper_instrument_cannot_be_amended_to_no_original(self):
		frappe.flags.kt_tenders_clock = W("2027-05-31 08:30:00")
		self._strip()
		self.assertTrue(self.correct()["ok"])  # the published requirement: paper, original required
		name = self._addendum(values={"change_class": "Non-material correction", "affected_area": "Submission or opening detail", "affected_reference_key": "tender_security_original", "revised_value": "Not required",
			"reason": "The original is no longer needed at the office.", "materiality_statement": "No change to the amount, form, expiry or evaluation basis.", "revised_submission_deadline": W("2027-06-12 11:00:00")})
		root = self._root()
		with self.assertRaises(TendersError) as caught:
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(caught.exception.code, "TND_CONTROL_INVALID")

	def test_a_closed_tender_keeps_its_issued_requirement(self):
		frappe.flags.kt_tenders_clock = W("2027-05-20 09:00:00")
		name = self._addendum(values={"change_class": "Non-material correction", "affected_area": "Submission or opening detail", "affected_reference_key": "tender_security_original", "revised_value": "Not required",
			"reason": "The original is no longer needed at the office.", "materiality_statement": "No change to the amount, form, expiry or evaluation basis."})
		frappe.flags.kt_tenders_clock = W("2027-06-06 09:00:00")  # after the 5 June deadline
		root = self._root()
		with self.assertRaises(TendersError):
			addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)


class TestDraftUpdatesToTheCurrentRelease(StatementCase):
	"""A new template release reaches new Tenders and unpublished drafts only through an explicit, recorded update."""

	def test_a_published_tender_is_never_moved_and_an_unchanged_draft_says_so(self):
		root = self._root()
		with self.assertRaises(TendersError):
			cmd.update_draft_template_release(tender=self.name, expected_record_version=root.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(frappe.db.get_value("Tender", self.name, "template_release_id"), root.template_release_id)

	def test_an_unpublished_draft_moves_only_by_the_explicit_update_and_it_is_recorded(self):
		from kentender_procurement.tenders.tests import sample

		fx.wipe_all()
		authorised = fx.authorised_handoff()
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		draft = frappe.get_doc("Tender", started["tender"])
		cmd.save_tender_draft(tender=draft.name, values=sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE), expected_record_version=draft.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		draft.reload()
		current = draft.template_release_id
		unchanged = cmd.update_draft_template_release(tender=draft.name, expected_record_version=draft.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(unchanged["action"], "unchanged")
		# make the Draft look like one started on the earlier release 1.4 (installed, switched Off), then update it
		earlier = frappe.db.get_value("Installed STD Release", {"template_release": "1.4"}, "name")
		self.assertTrue(earlier, "release 1.4 is installed on the site")
		for doctype, name in (("Tender", draft.name), ("Tender Version", draft.current_version)):
			frappe.db.set_value(doctype, name, "template_release_id", earlier, update_modified=False)
		draft.reload()
		notice = template_binding.release_notice(draft, fx.OFFICER)
		self.assertEqual((notice["state"], notice["can_update"], notice["update_to"], notice["full_page"]), ("Superseded", True, "1.5", True))
		self.assertFalse(template_binding.release_notice(draft, fx.HOPF)["can_update"])  # only a Procurement Officer updates
		with self.assertRaises(frappe.DoesNotExistError):  # only a Procurement Officer
			cmd.update_draft_template_release(tender=draft.name, expected_record_version=draft.record_version, idempotency_key=fx.key(), user=fx.HOPF)
		moved = cmd.update_draft_template_release(tender=draft.name, expected_record_version=draft.record_version, idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(moved["action"], "updated")
		draft.reload()
		self.assertEqual((draft.template_release_id, frappe.db.get_value("Tender Version", draft.current_version, "template_release_id")), (current, current))
		self.assertIsNone(template_binding.release_notice(draft, fx.OFFICER))  # on the current release there is nothing to offer
		event = frappe.get_all("Tender Event", filters={"tender": draft.name, "event_type": "TenderTemplateReleaseUpdated"}, fields=["name"])
		self.assertEqual(len(event), 1)
