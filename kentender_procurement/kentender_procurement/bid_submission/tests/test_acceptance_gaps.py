# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 acceptance rows the 28 Sep 2026 audit left Partial for
want of a test (`evidence/v0_8/ac_audit_2026-09-28.md`; owner: "Create the
tests"). Each test names the row it proves."""

from __future__ import annotations

import json
import os
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import (
	bid_context,
	errors,
	handoffs,
	overview,
	package,
	reads,
	receipt_view,
	signature,
	simulation,
	status_view,
	submission,
	tenders_gateway,
)
from kentender_procurement.bid_submission.test_services import trust
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, MARY, PETER, key
from kentender_procurement.bid_submission.tests.test_addendum_refresh import AddendumCase
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase
from kentender_procurement.bid_submission.tests.test_submission import COUNTED, SUBMIT_AT, SubmissionCase
from kentender_procurement.tenders.services import addenda, bid_definition, clarifications
from kentender_procurement.tenders.tests import fixtures as tender_fx
from kentender_procurement.tenders.tests.test_open_period import CHANNELS

GATEWAY = "kentender_procurement.bid_submission.services.tenders_gateway"


def _definition(case) -> dict:
	return tenders_gateway.definition_for(case.name, frappe.db.get_value("Bid Workspace", case.bid, "definition_version"))["definition"]


# -- BDS01-AC-010 / BDS03-AC-010 ---------------------------------------------------


class TestSuspendedAccount(ChangeCase):
	def test_a_suspended_account_cannot_submit_replace_or_withdraw_and_still_reads_its_receipt(self):
		self.accounts.orgs[AFYA]["account_status"] = "Suspended"
		self.assertEqual(self.code(self.prepare), "BDS_ACCOUNT_SUSPENDED")
		self.assertEqual(self.counts(), dict.fromkeys(COUNTED, 0))
		self.accounts.orgs[AFYA]["account_status"] = "Active"
		receipt = self.submitted()
		self.accounts.orgs[AFYA]["account_status"] = "Suspended"
		self.at("2027-05-31 08:30:00")
		self.assertEqual(self.code(self.replace), "BDS_ACCOUNT_SUSPENDED")
		self.assertEqual(self.code(self.withdraw, receipt=receipt), "BDS_ACCOUNT_SUSPENDED")
		self.assertEqual(self.current()[0], "Submitted")
		page = receipt_view.get_receipt_page(tender_reference=self.reference, receipt_reference=receipt, user=MARY)
		self.assertEqual({r["label"]: r["value"] for r in page["receipt"]}["Receipt reference"], receipt)
		self.assertEqual([a["key"] for a in page["actions"]], ["print"])  # no change action while suspended
		history = reads.get_receipt_history(user=MARY)
		self.assertTrue(history["suspended"])
		self.assertIn(receipt, [r["document"] for r in history["rows"]])


# -- BDS01-AC-059 --------------------------------------------------------------


class TestCertificates(SubmissionCase):
	def _only(self, **certificate):
		frappe.db.delete("Test Trust Certificate", {"certificate_ref": self.certificate})
		trust.issue_certificate(user=MARY, subject_name="Mary Wanjiku", **certificate)

	def test_an_expired_certificate_cannot_sign(self):
		self._only(organisation=AFYA, valid_from="2027-01-01 00:00:00", valid_to="2027-05-29 23:59:59")
		self.assertEqual(signature.certificate(MARY, AFYA, frappe.utils.get_datetime(SUBMIT_AT))["status"], "Expired")
		self.assertEqual(signature.check_certificate(bid_reference=self.bid, user=MARY)["status"], "Required")
		self.assertEqual(self.code(self.prepare), "BDS_SIGNATORY_CERTIFICATE_REQUIRED")
		self.assertEqual(self.counts(), dict.fromkeys(COUNTED, 0))

	def test_a_certificate_issued_for_another_organisation_cannot_sign_for_this_one(self):
		self._only(organisation=KISIWA, valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59")
		self.assertEqual(signature.certificate(MARY, AFYA, frappe.utils.get_datetime(SUBMIT_AT))["status"], "None")
		self.assertEqual(signature.check_certificate(bid_reference=self.bid, user=MARY)["status"], "Required")
		self.assertEqual(self.code(self.prepare), "BDS_SIGNATORY_CERTIFICATE_REQUIRED")
		self.assertEqual(frappe.db.count("Test Trust Signature", {"user": MARY, "organisation": AFYA}), 0)


# -- BDS08-AC-007 / BDS08-AC-010 ---------------------------------------------------------


class TestCustodyRecovery(SubmissionCase):
	def test_an_uncertain_attempt_resolved_as_rejected_allows_a_new_attempt_before_the_deadline(self):
		simulation.set_controls(deposit_outcome="Uncertain")
		pending = self.submit(self.signed())
		self.assertEqual(pending["code"], "BDS_SUBMISSION_UNCERTAIN")
		simulation.set_controls(uncertain_resolution="Reject")
		submission.reconcile_uncertain_attempts()
		self.assertEqual(frappe.db.get_value("Bid Submission Attempt", {"correlation_id": pending["correlation_id"]}, "status"), "Rejected")
		self.assertEqual(self.counts(), {**dict.fromkeys(COUNTED, 0), "Bid Submission Attempt": 1})
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "status"), "Ready to submit")
		simulation.set_controls(deposit_outcome="Accept", uncertain_resolution="Pending")
		self.assertTrue(self.submit(self.signed())["ok"])

	def test_after_the_deadline_a_rejected_attempt_offers_no_new_attempt(self):
		simulation.set_controls(deposit_outcome="Reject", rejection_reference="TBX-REJECT-033-02")
		rejected = self.submit(self.signed())
		self.assertEqual((rejected["code"], rejected["retry_allowed"]), ("BDS_CUSTODY_REJECTED", True))  # before the deadline
		self.at(str(self.deadline()))
		page = status_view.get_status_page(tender_reference=self.reference, user=MARY)
		self.assertEqual((page["state"]["key"], page["state"]["retry"]), ("custody-rejected", False))  # named, never retried
		self.assertNotIn("/submit", page["state"]["href"])
		self.assertEqual(self.code(self.prepare), "BDS_DEADLINE_PASSED")
		step = reads.get_bid_workspace(bid_reference=self.bid, user=MARY)["next_step"]
		self.assertEqual((step["kind"], [f["fix_id"] for f in step.get("fixes") or []]), ("done", []))


# -- BDS01-AC-047 ----------------------------------------------------------------------


class TestAddendumAfterSubmission(ChangeCase):
	def setUp(self):
		super().setUp()
		self._flag("kt_tenders_notice_sync", True)
		self._flag("kt_tenders_notice_transport", lambda notice: {"result": "Delivered", "provider_reference": f"test:{notice.name}", "failure_reason": ""})

	def issue_addendum(self) -> str:
		frappe.flags.kt_tenders_clock = "2027-05-31 08:30:00"
		name = self._addendum(values={**self.FIXTURE_ADDENDUM, "revised_submission_deadline": "2027-06-12 11:00:00"})
		addenda.submit_addendum_for_issue(tender=self.name, addendum=name, expected_record_version=self._root().record_version, idempotency_key=tender_fx.key(), user=tender_fx.OFFICER)
		frappe.flags.kt_tenders_clock = "2027-05-31 09:00:00"
		addenda.issue_addendum(tender=self.name, addendum=name, expected_record_version=self._root().record_version, idempotency_key=tender_fx.key(), user=tender_fx.HOPF)
		for channel in CHANNELS:
			self._confirm("addendum", channel, addendum=name, available_at="2027-05-31 09:00:00")
		return name

	def test_a_submitted_bid_stays_sealed_and_a_change_needs_a_replacement_on_the_current_definition(self):
		receipt = self.submitted()
		_status, v1 = self.current()
		sealed = frappe.db.get_value("Bid Submission Version", v1, ["definition_version", "definition_digest", "package_digest", "tender_box_envelope"], as_dict=True)
		self.issue_addendum()
		self.assertEqual(bid_definition.current(self.name)["definition_version"], 2)
		self.at("2027-06-01 12:00:00")
		self.assertEqual(frappe.db.get_value("Bid Submission Version", v1, ["definition_version", "definition_digest", "package_digest", "tender_box_envelope"], as_dict=True), sealed)
		self.assertEqual((self.current(), frappe.db.get_value("Bid Workspace", self.bid, "definition_version")), (("Submitted", v1), 1))
		self.assertEqual(frappe.db.get_value("Tender Box Envelope", sealed.tender_box_envelope, "box_state"), "Sealed")
		# a change is a replacement, and it moves to the current definition before it can be submitted
		self.assertTrue(self.replace()["ok"])
		self.assertEqual(self.code(self.prepare), "BDS_ADDENDUM_REVIEW_REQUIRED")
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		self.at("2027-06-01 12:10:00")
		from kentender_procurement.bid_submission.services import save

		moved = save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: "ApexBook Pro 14 G3"}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)
		self.assertEqual((moved["ok"], moved["code"], moved["refreshed"]), (False, "BDS_ADDENDUM_REVIEW_REQUIRED", True))  # the first change moves the Draft
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, "definition_version"), 2)
		self.assertEqual(frappe.db.get_value("Bid Receipt", {"receipt_reference": receipt}, "receipt_reference"), receipt)


# -- BDS08-AC-003 / BDS06-AC-014 ----------------------------------------------------


class TestAddendumReview(AddendumCase):
	def test_the_review_item_clears_when_the_acknowledgement_is_saved(self):
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:05:00")
		handoffs.sweep()
		self.assertEqual(frappe.db.count("Bid Hand-off", {"bid_workspace": self.bid, "kind": "Review addendum", "status": "Open"}), 1)
		self.at("2027-06-01 12:10:00")
		moved = self.save("documents", {})
		self.assertEqual((moved["ok"], moved["code"]), (False, "BDS_ADDENDUM_REVIEW_REQUIRED"))
		self.assertEqual(frappe.db.count("Bid Hand-off", {"bid_workspace": self.bid, "kind": "Review addendum", "status": "Open"}), 1)  # still open: not yet acknowledged
		task = reads.get_bid_task(bid_reference=self.bid, task="documents", user=DAVID)
		ack = next(a for a in task["addenda"] if a["reference"] == reference)["acknowledgement"]
		self.assertTrue(self.save("documents", {ack["handle"]: True})["ok"])
		affected = json.loads(frappe.db.get_value("Bid Workspace", self.bid, "attention_json") or "[]")
		if affected:  # §5.14: "Acknowledgement and affected responses complete"
			self.assertEqual(frappe.db.count("Bid Hand-off", {"bid_workspace": self.bid, "kind": "Review addendum", "status": "Open"}), 1)
			for task in affected:
				self.save(task, {})
		self.assertEqual(json.loads(frappe.db.get_value("Bid Workspace", self.bid, "attention_json") or "[]"), [])
		self.assertEqual(frappe.db.count("Bid Hand-off", {"bid_workspace": self.bid, "kind": "Review addendum", "status": "Open"}), 0)

	def test_a_successor_definition_whose_digest_fails_is_refused_at_refresh(self):
		self.issue_addendum()
		self.at("2027-06-01 12:10:00")
		current = bid_definition.current(self.name)
		tampered = dict(current, definition=dict(current["definition"], submission_deadline="2099-01-01T00:00:00+03:00"))
		before = frappe.db.get_value("Bid Workspace", self.bid, ["definition_version", "definition_digest"])
		with mock.patch(f"{GATEWAY}.current_definition", return_value=tampered):
			with self.assertRaises(errors.BidSubmissionError) as refused:
				self.save("documents", {})
		self.assertEqual(refused.exception.code, "BDS_DEFINITION_UNSUPPORTED")
		self.assertEqual(frappe.db.get_value("Bid Workspace", self.bid, ["definition_version", "definition_digest"]), before)


# -- BDS01-AC-021 / -022 / -024 / -028B, BDS06-AC-007 ---------------------------------


class TestPublishedIdentities(SubmissionCase):
	GROUPS = {"RR-TECHNICAL": 11, "RR-WARRANTY-SUPPORT": 6, "RR-ACCEPTANCE": 5}

	def test_the_signed_package_accounts_for_every_technical_warranty_and_acceptance_group(self):
		definition = _definition(self)
		rows = [r for r in definition["response_rows"] if r["group_key"].split("/")[0] in self.GROUPS]
		groups = {c: {r["group_key"] for r in rows if r["group_key"].split("/")[0] == c} for c in self.GROUPS}
		self.assertEqual({c: len(g) for c, g in groups.items()}, self.GROUPS)
		ctx = bid_context.load(self.bid, actor=MARY)
		body = json.loads(package.build(ctx, signatory=signature.signatory_of(ctx, MARY), confirmed=True).content)
		carried = {e["response_id"]: e for e in body["responses"] + body["evidence"]}
		for composition, keys in groups.items():
			for group in keys:
				with self.subTest(group=group):
					members = [r for r in rows if r["group_key"] == group]
					present = [r for r in members if r["response_id"] in carried]
					self.assertTrue(present, f"{group} is not in the signed package")
					for r in present:
						self.assertEqual((carried[r["response_id"]]["evaluation_mapping_id"], carried[r["response_id"]]["contract_mapping_id"]), (r.get("evaluation_mapping_id") or "", r.get("contract_mapping_id") or ""))

	def test_the_requirements_read_lists_each_published_requirement_once_in_published_order(self):
		definition = _definition(self)
		def published(composition):
			ordered = sorted((r for r in definition["response_rows"] if r["group_key"].split("/")[0] == composition), key=lambda r: r["sequence"])
			return list(dict.fromkeys(r["group_key"] for r in ordered))
		read = reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)
		from kentender_procurement.bid_submission.services import projection

		ctx = bid_context.load(self.bid, actor=DAVID)
		published_key = {projection.group_handle(ctx, g): g.group_key for g in ctx.model.groups_of("requirements")}
		for region, composition in (("technical", "RR-TECHNICAL"), ("warranty", "RR-WARRANTY-SUPPORT"), ("acceptance", "RR-ACCEPTANCE")):
			with self.subTest(region=region):
				shown = [published_key[row["key"]] for row in read[region]]
				self.assertEqual(shown, published(composition))  # every row, once, in order

	def test_each_declaration_shows_its_full_published_text_unconfirmed_and_signs_against_the_bound_definition(self):
		definition = _definition(self)
		texts = {t["text_id"]: (t.get("resolved_text") or t.get("locked_text")) for t in definition.get("declaration_texts") or []}
		start = bid_context.load(self.bid, actor=DAVID)
		shown = {g.published_facts.get("text_id"): g for g in start.model.groups_of("company") if g.published_facts.get("text_id")}
		self.assertTrue(shown)
		read = reads.get_bid_task(bid_reference=self.bid, task="company", user=DAVID)
		statements = [d["statement"] for d in read["declarations"] if d["statement"]]
		for text_id, group in shown.items():
			with self.subTest(text_id=text_id):
				published = texts[text_id]
				if group.published_facts.get("form_id") == "FORM-TENDER":
					self.assertTrue(any(s.startswith(published.split("_____")[0].strip()[:40]) for s in statements))
				else:
					self.assertIn(published, statements)  # the whole text, never shortened
		# the confirmation is bound to the exact definition the declarations came from
		ctx = bid_context.load(self.bid, actor=MARY)
		body = json.loads(package.build(ctx, signatory=signature.signatory_of(ctx, MARY), confirmed=True).content)
		self.assertEqual(body["tender"]["definition_digest"], frappe.db.get_value("Bid Workspace", self.bid, "definition_digest"))
		self.assertEqual(body["tender"]["definition_digest"], definition["definition_digest"])

	def test_the_bound_definition_names_the_installed_release_exactly(self):
		definition = _definition(self)
		release = frappe.get_doc("Installed STD Release", definition["template_release_id"])
		self.assertEqual(
			(definition["template_family"], definition["product_profile_id"], definition["renderer_profile_id"], definition["supported_renderer_version"]),
			(release.template_key, release.product_profile_id, release.renderer_profile_id, release.supported_renderer_version),
		)

	def test_account_facts_never_answer_a_reservation_response(self):
		# the published MOH definition carries the Youth reservation (the test
		# world's Tender has none): its rows are the bidder's own answers and
		# evidence — none is filled from the Account (BDS01-AC-028B)
		from kentender_procurement.bid_submission.services.definition_model import DefinitionModel

		expected = os.path.join(os.path.dirname(frappe.get_app_path("kentender_procurement")), "..", "docs", "mvp-1-r1", "07_tender_templates", "it_equipment_open_v1", "06_runtime", "moh_published_bid_definition_expected.json")
		definition = json.load(open(expected))
		reservation = {r["response_id"] for r in definition["response_rows"] if r["group_key"].startswith("RR-RESERVATION/")}
		self.assertEqual(len(reservation), 5)
		fields = [f for f in DefinitionModel(definition).all_fields() if f.response_id in reservation]
		self.assertEqual(len(fields), 5)
		self.assertEqual([f.field_key for f in fields if f.supplied], [])
		self.assertTrue(any(f.kind == "evidence" for f in fields))  # the bidder supplies the published evidence


# -- BDS01-AC-043 / -050, BDS07-AC-007 -------------------------------------------------


class TestAnswersOnThePortal(AddendumCase):
	QUESTION = "May the two comparable contracts be from different customers?"
	ANSWER = "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer."

	def ask_and_answer(self, *, affects: bool = False) -> str:
		arrangement = frappe.db.get_value("Bidder Arrangement", frappe.db.get_value("Bid Workspace", self.bid, "bidder_arrangement"), "bidder_arrangement_id")
		frappe.flags.kt_tenders_clock = "2027-05-26 09:00:00"
		received = clarifications.receive_tender_clarification(tender=self.name, candidate_registration_id=arrangement, question=self.QUESTION, received_at="2027-05-26 09:00:00", inbound_event_id=key(), user=tender_fx.PRODUCER)
		frappe.flags.kt_tenders_clock = "2027-05-26 11:00:00"
		clarifications.respond_to_tender_clarification(
			tender=self.name, clarification=received["clarification"], response=self.ANSWER, affects_published_tender=affects, response_audience="All registered candidates",
			expected_record_version=self._root().record_version, idempotency_key=tender_fx.key(), user=tender_fx.OFFICER,
		)
		return received["clarification"]

	def test_a_general_answer_reaches_every_reader_without_naming_the_asker(self):
		self.ask_and_answer()
		self.at("2027-05-26 12:00:00")
		for user in ("Guest", PETER, DAVID):
			with self.subTest(user=user):
				tender = overview.get_tender_overview(tender_reference=self.reference, user=user)
				self.assertEqual([(a["question"], a["answer"]) for a in tender["answers"]], [(self.QUESTION, self.ANSWER)])
				self.assertNotIn("Afya", json.dumps(tender["answers"]))
		documents = reads.get_bid_task(bid_reference=self.bid, task="documents", user=DAVID)
		self.assertIn(self.ANSWER, json.dumps(documents))

	def test_an_answer_that_would_change_the_tender_waits_for_its_addendum(self):
		self.ask_and_answer(affects=True)
		self.at("2027-05-26 12:00:00")
		self.assertEqual(overview.get_tender_overview(tender_reference=self.reference, user="Guest")["answers"], [])
		self.assertNotIn(self.ANSWER, json.dumps(reads.get_bid_task(bid_reference=self.bid, task="documents", user=DAVID)))

	def test_an_issued_addendum_is_listed_on_the_tender_page(self):
		name = self.issue_addendum()
		reference = frappe.db.get_value("Tender Addendum", name, "addendum_reference")
		self.at("2027-06-01 12:00:00")
		tender = overview.get_tender_overview(tender_reference=self.reference, user="Guest")
		self.assertEqual([a["reference"] for a in tender["addenda"]], [reference])
		self.assertEqual(tender["tender"]["deadline"], "12 Jun 2027, 11:00 EAT")


# -- BDS01-AC-002 / -027 / -085 ----------------------------------------------------------

INTERNAL_IDS = r"\b(RSP|COMP|CTL|RR|EVG|DM|TSR|TCERT|VAL|RQ)-[A-Z0-9]|\bstdr-[0-9a-f]{8}|\b[0-9a-f]{64}\b|/private/files|kt_test_tender_box"
VOCABULARY = r"(?i)\b(schema|renderer|manifest|digest|sha-?256|canonical json|payload|idempotency|composition|evaluation mapping|contract mapping|response id|stable key|signing request|workflow state)\b"
INTERNAL_KEYS = {"response_id", "definition_digest", "package_digest", "template_release_id", "evaluation_mapping_id", "contract_mapping_id", "values_json", "file_url", "stable_key", "composition_id"}


def _strings_and_keys(value, strings, keys):
	if isinstance(value, dict):
		for k, v in value.items():
			keys.add(k)
			_strings_and_keys(v, strings, keys)
	elif isinstance(value, (list, tuple)):
		for v in value:
			_strings_and_keys(v, strings, keys)
	elif isinstance(value, str):
		strings.append(value)


class TestNothingInternalReachesThePortal(ChangeCase):
	def assertClean(self, name, dto):
		import re

		strings, keys = [], set()
		_strings_and_keys(dto, strings, keys)
		text = "\n".join(strings)
		self.assertIsNone(re.search(INTERNAL_IDS, text), f"{name}: {re.search(INTERNAL_IDS, text) and re.search(INTERNAL_IDS, text).group(0)}")
		self.assertIsNone(re.search(VOCABULARY, text), f"{name}: {re.search(VOCABULARY, text) and re.search(VOCABULARY, text).group(0)}")
		self.assertEqual(keys & INTERNAL_KEYS, set(), name)

	def test_every_supplier_and_public_read_carries_no_internal_identity_or_vocabulary(self):
		from kentender_procurement.bid_submission.services import changes_view
		reads_before = {
			"overview (guest)": lambda: overview.get_tender_overview(tender_reference=self.reference, user="Guest"),
			"overview (David)": lambda: overview.get_tender_overview(tender_reference=self.reference, user=DAVID),
			"overview (Peter)": lambda: overview.get_tender_overview(tender_reference=self.reference, user=PETER),
			"available tenders": lambda: reads.get_available_tenders(),
			"workspace": lambda: reads.get_bid_workspace(bid_reference=self.bid, user=DAVID),
			"review": lambda: reads.get_bid_review(bid_reference=self.bid, user=MARY),
			"submit page": lambda: reads.get_submit_page(tender_reference=self.reference, user=MARY),
			"my bids": lambda: reads.get_my_bids(user=DAVID),
			**{f"task {t}": (lambda t=t: reads.get_bid_task(bid_reference=self.bid, task=t, user=DAVID)) for t in ("documents", "company", "requirements", "price", "review")},
		}
		for name, read in reads_before.items():
			with self.subTest(read=name):
				self.assertClean(name, read())
		receipt = self.submitted()
		after = {
			"receipt page": lambda: receipt_view.get_receipt_page(tender_reference=self.reference, receipt_reference=receipt, user=MARY),
			"status page": lambda: status_view.get_status_page(tender_reference=self.reference, user=MARY),
			"receipt history": lambda: reads.get_receipt_history(user=MARY),
			"replacement page": lambda: changes_view.get_replacement_page(tender_reference=self.reference, user=MARY),
			"overview (Mary)": lambda: overview.get_tender_overview(tender_reference=self.reference, user=MARY),
		}
		for name, read in after.items():
			with self.subTest(read=name):
				self.assertClean(name, read())
		self.at("2027-05-31 08:30:00")
		acknowledgement = self.withdraw(receipt=receipt)["acknowledgement_reference"]
		self.assertClean("acknowledgement page", changes_view.get_acknowledgement_page(tender_reference=self.reference, acknowledgement_reference=acknowledgement, user=MARY))


# -- BDS01-AC-079 / -081 -----------------------------------------------------------------


class TestSideChannels(ChangeCase):
	BUSINESS = (tender_fx.OFFICER, tender_fx.HOPF, tender_fx.AO, tender_fx.AUDITOR, tender_fx.BOTH)

	def test_procuring_entity_users_see_no_bid_record_list_report_or_search_before_opening(self):
		self.submitted()
		doctypes = [d for d in frappe.get_all("DocType", filters={"module": "Bid Submission", "istable": 0, "issingle": 0}, pluck="name") if not d.startswith("Test ")]
		self.assertIn("Bid Workspace", doctypes)
		for user in self.BUSINESS:
			frappe.set_user(user)
			try:
				for doctype in doctypes:
					with self.subTest(user=user, doctype=doctype):
						self.assertFalse(frappe.has_permission(doctype, "read", user=user), f"{user} may read {doctype}")
						try:
							rows = frappe.get_list(doctype, fields=["name"], limit_page_length=5)
						except frappe.PermissionError:
							rows = []
						self.assertEqual(rows, [])
				from frappe.utils.global_search import search

				found = search("Afya", limit=50)
				self.assertEqual([r for r in found if r.get("doctype") in doctypes], [])
			finally:
				frappe.set_user("Administrator")

	def test_bid_values_reach_neither_the_error_log_nor_the_search_index(self):
		marker = "SIDE-CHANNEL-MARKER-7Q2"
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		logs = frappe.db.count("Error Log")
		self.at("2027-05-30 14:00:00")
		from kentender_procurement.bid_submission.services import save

		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: marker}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])
		with self.assertRaises(errors.BidSubmissionError):  # a refused save carrying the value
			save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: marker}, expected_record_version=0, idempotency_key=key(), user=DAVID)
		self.assertEqual(frappe.db.sql("select count(*) from `tabError Log` where creation >= now() - interval 1 hour and (error like %s or method like %s)", (f"%{marker}%", f"%{marker}%"))[0][0], 0)
		self.assertGreaterEqual(frappe.db.count("Error Log"), logs)
		self.assertEqual(frappe.db.sql("select count(*) from `__global_search` where content like %s", (f"%{marker}%",))[0][0], 0)
		self.assertEqual(frappe.db.sql("select count(*) from `tabVersion` where data like %s", (f"%{marker}%",))[0][0], 0)


# -- BDS01-AC-084 / BDS04-AC-002 ------------------------------------------------------

REGISTER = frappe.get_app_path("kentender_procurement", "bid_submission", "action_register.json")
CATALOGUE = frappe.get_app_path("kentender_procurement", "bid_submission", "common_states.json")
SPEC = os.path.join(os.path.dirname(frappe.get_app_path("kentender_procurement")), "..", "docs", "mvp-1-r1", "12_bid_submission", "KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_8.md")


def _actions(value, found: set[str]) -> None:
	"""Every action-shaped entry in a read: a label with where it leads (href),
	what it runs (command, fix_id) or its action kind."""
	if isinstance(value, dict):
		label = value.get("label")
		if isinstance(label, str) and label and any(k in value for k in ("href", "command", "fix_id", "kind")) and "value" not in value and "headline" not in value:
			found.add(label)
		for v in value.values():
			_actions(v, found)
	elif isinstance(value, (list, tuple)):
		for v in value:
			_actions(v, found)


class TestActionRegister(ChangeCase):
	def register(self) -> dict[str, dict]:
		entries = json.load(open(REGISTER))["actions"]
		labels = [e["label"] for e in entries]
		self.assertEqual(len(labels), len(set(labels)), "a label is registered twice")
		return {e["label"]: e for e in entries}

	def test_each_registered_section_11_control_is_the_specs_own_row(self):
		spec = open(SPEC, encoding="utf-8").read()
		section = spec[spec.index("## 11. Functional interaction contract"):spec.index("## 12.")]
		controls = {line.split(" | ")[0].lstrip("| ").strip() for line in section.splitlines() if line.startswith("| ") and not line.startswith("| Visible control") and not line.startswith("|---")}
		for label, entry in self.register().items():
			with self.subTest(label=label):
				if entry["spec"].startswith("§11."):
					self.assertIn(entry["control"], controls)
				else:
					self.assertTrue(entry.get("note"), f"{label}: a non-§11 action must say why")

	def test_every_action_a_read_emits_has_exactly_one_mapping(self):
		from kentender_procurement.bid_submission.services import changes_view

		register = self.register()
		catalogue = {s["action"] for s in json.load(open(CATALOGUE))["states"] if s.get("action")} | {s["retry_action"] for s in json.load(open(CATALOGUE))["states"] if s.get("retry_action")}
		found: set[str] = set()

		def read_everything(users=(DAVID, MARY, PETER, "Guest")):
			for user in users:
				for call in (
					lambda: overview.get_tender_overview(tender_reference=self.reference, user=user),
					lambda: reads.get_my_bids(user=user) if user != "Guest" else {},
					lambda: reads.get_receipt_history(user=user) if user != "Guest" else {},
				):
					try:
						_actions(call(), found)
					except (errors.BidSubmissionError, frappe.DoesNotExistError, frappe.PermissionError):
						pass
			for user in (DAVID, MARY):
				ws = frappe.db.get_value("Bid Workspace", self.bid, ["current_submission_version", "status"], as_dict=True)
				calls = [lambda: reads.get_bid_workspace(bid_reference=self.bid, user=user), lambda: reads.get_submit_page(tender_reference=self.reference, user=user), lambda: status_view.get_status_page(tender_reference=self.reference, user=user)]
				calls += [(lambda t=t: reads.get_bid_task(bid_reference=self.bid, task=t, user=user)) for t in ("documents", "company", "requirements", "price", "review")]
				receipt = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, "receipt") if ws.current_submission_version else None
				if receipt:
					calls += [lambda: receipt_view.get_receipt_page(tender_reference=self.reference, receipt_reference=receipt, user=user), lambda: changes_view.get_replacement_page(tender_reference=self.reference, user=user)]
				for call in calls:
					try:
						_actions(call(), found)
					except (errors.BidSubmissionError, frappe.DoesNotExistError):
						pass

		read_everything()  # ready Draft
		simulation.set_controls(gate_closed=1)
		read_everything()
		simulation.set_controls(gate_closed=0, trust_service_down=1)
		read_everything()
		simulation.reset_controls()
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete"}):
			read_everything()
		simulation.set_controls(bound_release_state="Withdrawn")
		read_everything()
		simulation.reset_controls()
		simulation.set_controls(deposit_outcome="Reject", rejection_reference="TBX-REJECT-033-03")
		self.submit(self.signed())
		read_everything()
		simulation.reset_controls()
		receipt = self.submitted()
		read_everything()
		self.at("2027-05-31 08:30:00")
		self.replace()
		read_everything()
		self.at(str(self.deadline()))
		read_everything()
		tasks = {t.label for t in bid_context.load(self.bid, actor=DAVID).model.tasks}  # the task list: §11.4 Task View / Continue / Fix
		unmapped = sorted(label for label in found if label not in register and label.split(":")[0] not in register and label not in catalogue and label not in tasks)
		self.assertEqual(unmapped, [], "actions with no §11 mapping")
		self.assertTrue(receipt)


# -- BDS01-AC-089 ------------------------------------------------------------------------


class TestEventMinimum(ChangeCase):
	def event(self, event_type: str):
		rows = frappe.get_all("Bid Submission Event", filters={"bid_workspace": self.bid, "event_type": event_type}, fields=["*"], order_by="creation desc", limit_page_length=1)
		self.assertTrue(rows, event_type)
		return rows[0]

	def test_a_command_event_records_the_section_12_1_minimum(self):
		import hashlib

		from kentender_core.utils.instants import to_utc_iso

		from kentender_procurement.bid_submission.services import save

		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		request = key()
		self.at("2027-05-30 14:00:00")
		before = frappe.db.get_value("Bid Workspace", self.bid, "status")
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: "ApexBook Pro 14 G2"}, expected_record_version=self.version(), idempotency_key=request, user=DAVID)["ok"])
		saved = self.event("BidTaskSaved")
		assignment = bid_context.load(self.bid, actor=DAVID).assignment["assignment_id"]
		after = frappe.db.get_value("Bid Workspace", self.bid, ["status", "record_version"], as_dict=True)
		self.assertEqual(
			(saved.schema_version, saved.command, saved.idempotency_key_hash, saved.actor, saved.assignment),
			(1, "SaveBidTask", hashlib.sha256(request.encode()).hexdigest(), DAVID, assignment),
		)
		self.assertEqual((saved.occurred_at_utc, saved.occurred_at_eat), (to_utc_iso(saved.occurred_at), "30 May 2027, 14:00:00 EAT"))
		self.assertEqual((saved.previous_status, saved.resulting_status, saved.record_version), (before, after.status, after.record_version))
		self.assertNotIn("ApexBook", saved.payload_json)
		# the lifecycle change of a submission, and its §12.2 facts
		self.at(SUBMIT_AT)
		receipt = self.submitted()
		submitted = self.event("BidSubmitted")
		self.assertEqual((submitted.command, submitted.previous_status, submitted.resulting_status), ("SubmitBid", "Ready to submit", "Submitted"))
		facts = json.loads(submitted.payload_json)
		self.assertEqual((facts["receipt"], bool(facts["package_digest"]), bool(facts["envelope"])), (receipt, True, True))
		signed = self.event("BidSignatureRequested")
		self.assertEqual((signed.command, json.loads(signed.payload_json)["signatory_assignment"]), ("PrepareBidSignature", bid_context.load(self.bid, actor=MARY).assignment["assignment_id"]))
		# a withdrawal names the exact Version, signatory, reason and acknowledgement
		self.at("2027-05-31 08:30:00")
		acknowledgement = self.withdraw(receipt=receipt)["acknowledgement_reference"]
		withdrawn = self.event("BidWithdrawn")
		facts = json.loads(withdrawn.payload_json)
		self.assertEqual((withdrawn.command, withdrawn.previous_status, withdrawn.resulting_status), ("WithdrawBid", "Submitted", "Withdrawn"))
		self.assertIn(acknowledgement, json.dumps(facts))


# -- BDS03-AC-001 / BDS08-AC-009 ---------------------------------------------------------


class TestCanonicalChronology(IntegrationTestCase):
	"""The canonical bid lifecycle's instants (§13.3) fall in order inside the
	Tender's own timeline: every fact a step relies on exists before it."""

	def test_each_bid_step_follows_the_tender_facts_it_relies_on(self):
		from frappe.utils import get_datetime

		from kentender_procurement.bid_submission.seeds import kentender_mvp_v1 as bid
		from kentender_procurement.tenders.seeds import kentender_mvp_v1 as tender

		t = {k: get_datetime(v) for k, v in tender.CLOCK.items()}
		b = {k: get_datetime(v) for k, v in bid.CLOCK.items()}
		self.assertEqual(list(b.values()), sorted(b.values()), "the bid steps are not in time order")
		self.assertEqual(list(t.values()), sorted(t.values()), "the Tender steps are not in time order")
		published, candidate = t["confirm_4"], t["candidate"]
		self.assertLess(published, candidate)  # a bid starts on a published Tender
		self.assertLess(candidate, b["fill"])  # tasks are filled after Start bid
		self.assertLess(t["addendum_confirm_4"], b["acknowledge"])  # an addendum is acknowledged once it is effective
		self.assertLess(b["acknowledge"], b["intake"])
		self.assertLess(b["complete"], b["submit"])  # the bid is complete before it is signed and submitted
		self.assertLess(b["submit"], t["close"])  # strictly before the deadline
		self.assertEqual(b["close"], t["close"])  # Bid Submission closes when Tenders ends the period


# -- BDS01-AC-001 ----------------------------------------------------------------------


class TestCancelledTender(ChangeCase):
	def test_a_guest_reads_a_cancelled_tender_and_is_offered_its_notice_only(self):
		real = tenders_gateway.published_tender

		def cancelled(reference, *, at):
			published = real(reference, at=at) or {}
			return {**published, "availability": "cancelled", "cancellation": {"notice_key": "cancellation-notice", "cancelled_at": "2027-05-28 10:00:00"}}

		with mock.patch.object(tenders_gateway, "published_tender", cancelled):
			guest = overview.get_tender_overview(tender_reference=self.reference, user="Guest")
			david = overview.get_tender_overview(tender_reference=self.reference, user=DAVID)
		self.assertEqual((guest["tender"]["availability"], guest["tender"]["status_label"]), ("cancelled", "Cancelled"))
		self.assertEqual([(a["kind"], a["label"]) for a in guest["actions"]], [("view_notice", "View notice")])
		self.assertIn("cancellation-notice", guest["action"]["href"])
		self.assertIn("inline=1", guest["action"]["href"])
		self.assertEqual(guest["cancellation"]["cancelled"], "28 May 2027, 10:00 EAT")
		self.assertIsNone(guest["start"])
		self.assertEqual([a["kind"] for a in david["actions"]], ["view_notice"])  # not Continue bid on a cancelled Tender
