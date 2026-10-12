# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.31 §5.5.2.2 / §5.5.2.4 — for MVP 1 the Procurement Planner
records the Treasury submission and the entity-website publication of an
approved Annual Plan in one **Confirm plan publication**, and the system then
runs the existing activation logic (PLN31-AC-001 to 017).

Owner instruction, 9 October 2026: "For MVP 1, the Planner should record
external submission and publication on behalf of the entity. The AO and CS
retain their decision responsibilities; routine evidence capture should sit
with the operational role." The flow is statutory approval, the Planner
confirms publication, and the system activates the plan if the existing
checks pass. It replaces the AO's Treasury form, the post-commit worker with
its adapter acknowledgement, and the Head of Procurement Function's Publish.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.utils import getdate, nowdate

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	plan_json,
	plan_publication,
	plan_read,
	publication_confirmation,
	publication_pipeline,
	treasury,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_publication import PublicationCase, key

PLANNER_ONLY_REFUSED = (fx.ACCOUNTING_OFFICER, fx.HOPF, fx.FINANCE_OFFICER, fx.STATUTORY, fx.AUTHOR, fx.HOD, fx.AUDITOR, fx.OUTSIDER, "Administrator")


class ConfirmationCase(PublicationCase):
	def values(self, **overrides) -> dict:
		today = str(getdate(nowdate()))
		return {
			"treasury_submitted_on": today,
			"treasury_reference": "MOH/APP/2101/001",
			"website_published_on": today,
			"public_plan_url": "https://www.moh.example.test/procurement/annual-procurement-plan",
			"confirmation_acknowledged": 1,
			**overrides,
		}

	def approved(self) -> tuple[dict, str]:
		accepted, _item = self.confirmed_item()
		approved = self.approve(accepted["annual_plan"])
		return approved, approved["plan_version"]

	def status(self, version: str) -> str:
		return frappe.db.get_value("Annual Plan Version", version, "version_status")

	def record_version(self, version: str) -> int:
		return int(frappe.db.get_value("Annual Plan Version", version, "record_version") or 0)

	def confirm(self, version: str, *, user: str = fx.PLANNER, values: dict | None = None, idempotency_key: str | None = None, expected: int | None = None) -> dict:
		frappe.set_user(user)
		return publication_confirmation.confirm_plan_publication(
			plan_version=version, values=self.values() if values is None else values,
			expected_record_version=self.record_version(version) if expected is None else expected, idempotency_key=idempotency_key or key(),
		)

	def confirmations(self, version: str, state: str | None = None) -> list[str]:
		filters = {"plan_version": version}
		if state:
			filters["confirmation_state"] = state
		frappe.set_user("Administrator")
		return frappe.get_all("Plan Publication Confirmation", filters=filters, pluck="name")


class TestApprovalCommitsOnly(ConfirmationCase):
	def test_approval_leaves_the_plan_waiting_for_the_planner_and_dispatches_nothing(self):
		approved, version = self.approved()
		self.assertEqual(self.status(version), "Approved — publication pending")
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		self.assertEqual(publication.publication_state, "Pending")
		# PLN31-AC-001: no worker, no intent, no attempt, no adapter acknowledgement
		self.assertEqual(frappe.db.count("Publication Intent", {"publication": publication.name}), 0)
		self.assertEqual(frappe.db.count("Publication Attempt", {"publication": publication.name}), 0)
		self.assertEqual(frappe.db.count("Publication Acknowledgement", {"publication": publication.name}), 0)
		self.assertEqual(self.confirmations(version), [])

	def test_the_retired_publication_commands_no_longer_exist(self):
		# PLN31-AC-013
		for name in ("publish_annual_plan", "publish_approved_plan", "receive_publication_acknowledgement", "reconcile_publication", "retry_publication"):
			with self.subTest(command=name):
				self.assertFalse(hasattr(publication_pipeline, name))
		for name in ("record_treasury_submission", "correct_treasury_submission_evidence"):
			with self.subTest(command=name):
				self.assertFalse(hasattr(treasury, name))


class TestWhoMayConfirm(ConfirmationCase):
	def test_only_the_planner_may_save_a_draft_confirm_or_correct(self):
		_approved, version = self.approved()
		for user in PLANNER_ONLY_REFUSED:
			with self.subTest(user=user):
				frappe.set_user(user)
				with self.assertRaises(frappe.DoesNotExistError):
					publication_confirmation.save_publication_draft(plan_version=version, values=self.values(), idempotency_key=key())
				with self.assertRaises(frappe.DoesNotExistError):
					self.confirm(version, user=user)
		self.assertEqual(self.confirmations(version), [])
		self.assertEqual(self.status(version), "Approved — publication pending")


class TestSaveDraft(ConfirmationCase):
	def test_an_incomplete_draft_is_saved_changes_nothing_and_is_not_evidence(self):
		_approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		saved = publication_confirmation.save_publication_draft(
			plan_version=version, values={"treasury_reference": "MOH/APP/2101/001"}, idempotency_key=key(),
		)
		self.assertEqual(saved["action"], "publication_draft_saved")
		self.assertEqual(self.status(version), "Approved — publication pending")
		self.assertEqual(self.confirmations(version, "Current"), [])
		draft = frappe.get_doc("Plan Publication Confirmation", saved["confirmation"])
		self.assertEqual((draft.confirmation_state, draft.treasury_reference), ("Draft", "MOH/APP/2101/001"))

	def test_saving_again_updates_the_one_draft_and_a_stale_draft_is_refused(self):
		_approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		first = publication_confirmation.save_publication_draft(plan_version=version, values={"treasury_reference": "A"}, idempotency_key=key())
		second = publication_confirmation.save_publication_draft(
			plan_version=version, values={"public_plan_url": "https://www.moh.example.test/p"}, expected_record_version=first["record_version"], idempotency_key=key(),
		)
		self.assertEqual(second["confirmation"], first["confirmation"])
		self.assertEqual(len(self.confirmations(version, "Draft")), 1)
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_confirmation.save_publication_draft(
				plan_version=version, values={"treasury_reference": "B"}, expected_record_version=first["record_version"], idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_STALE_WRITE")

	def test_a_draft_keeps_what_was_typed_even_where_it_would_not_yet_confirm(self):
		# Found live 9 Oct 2026: an address without http:// or https:// refused the whole Draft, so nothing
		# typed was kept. A Draft is unfinished work; the rules apply when the Planner confirms.
		_approved, version = self.approved()
		tomorrow = str(frappe.utils.add_days(getdate(nowdate()), 1))
		frappe.set_user(fx.PLANNER)
		saved = publication_confirmation.save_publication_draft(
			plan_version=version, idempotency_key=key(),
			values={"treasury_submitted_on": tomorrow, "treasury_reference": "ST-003", "public_plan_url": "www.xyz.com", "website_published_on": str(getdate(nowdate()))},
		)
		draft = frappe.get_doc("Plan Publication Confirmation", saved["confirmation"])
		self.assertEqual(
			(str(draft.treasury_submitted_on), draft.treasury_reference, draft.public_plan_url, str(draft.website_published_on), draft.confirmation_state),
			(tomorrow, "ST-003", "www.xyz.com", str(getdate(nowdate())), "Draft"),
		)
		# and it is still not evidence: confirming the same values is refused, naming the address
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version, values=self.values(public_plan_url="www.xyz.com"))
		self.assertIn("public_plan_url", caught.exception.detail["fields"])
		self.assertEqual(self.status(version), "Approved — publication pending")

	def test_a_draft_still_refuses_a_value_it_cannot_store(self):
		_approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_confirmation.save_publication_draft(plan_version=version, values={"treasury_submitted_on": "not a date"}, idempotency_key=key())
		self.assertIn("treasury_submitted_on", caught.exception.detail["fields"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_confirmation.save_publication_draft(plan_version=version, values={"public_plan_url": "https://x.test/" + "a" * 600}, idempotency_key=key())
		self.assertIn("public_plan_url", caught.exception.detail["fields"])

	def test_the_read_model_says_when_the_draft_was_saved(self):
		approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		publication_confirmation.save_publication_draft(plan_version=version, values={"treasury_reference": "ST-003"}, idempotency_key=key())
		view = plan_read.get_publication_task(publication=approved["publication"])
		self.assertEqual(view["draft"]["treasury_reference"], "ST-003")
		self.assertTrue(view["draft"]["saved_display"].endswith("EAT"))


class TestConfirm(ConfirmationCase):
	def test_a_complete_confirmation_stores_the_evidence_and_activates_the_plan(self):
		_approved, version = self.approved()
		result = self.confirm(version)
		self.assertEqual(result["action"], "publication_confirmed")
		self.assertEqual(result["activation"], "activated")
		self.assertEqual(self.status(version), "Active")
		current = self.confirmations(version, "Current")
		self.assertEqual(current, [result["confirmation"]])
		row = frappe.get_doc("Plan Publication Confirmation", current[0])
		# PLN31-AC-005: actor, assignment and instant come from the server; the document identity is linked
		self.assertEqual(row.actor, fx.PLANNER)
		self.assertTrue(row.recorded_at)
		self.assertTrue(row.authority_snapshot)
		snapshot = frappe.db.get_value("Approved Plan Snapshot", {"plan_version": version}, ["name", "content_digest"], as_dict=True)
		self.assertEqual((row.snapshot, row.document_hash), (snapshot.name, snapshot.content_digest))
		self.assertEqual(row.package_hash, frappe.db.get_value("Plan Publication", {"plan_version": version}, "package_hash"))
		self.assertEqual(frappe.db.get_value("Plan Publication", {"plan_version": version}, "publication_state"), "Confirmed")
		# no adapter attempt, acknowledgement or Accounting Officer Treasury record
		publication = frappe.db.get_value("Plan Publication", {"plan_version": version}, "name")
		self.assertEqual(frappe.db.count("Publication Attempt", {"publication": publication}), 0)
		self.assertEqual(frappe.db.count("Treasury Submission Evidence", {"plan_version": version}), 0)
		self.assertEqual(frappe.db.get_value("Annual Plan", frappe.db.get_value("Annual Plan Version", version, "annual_plan"), "active_version"), version)

	def test_a_missing_item_is_refused_naming_it_and_nothing_changes(self):
		_approved, version = self.approved()
		for field, value in (
			("treasury_submitted_on", ""), ("website_published_on", ""), ("public_plan_url", ""), ("confirmation_acknowledged", 0),
		):
			with self.subTest(field=field):
				with self.assertRaises(ProcurementPlanningError) as caught:
					self.confirm(version, values=self.values(**{field: value}))
				self.assertEqual(caught.exception.code, "PLN_TREASURY_EVIDENCE_REQUIRED")
				self.assertIn(field, caught.exception.detail["fields"])
		self.assertEqual(self.status(version), "Approved — publication pending")
		self.assertEqual(self.confirmations(version, "Current"), [])

	def test_a_reference_or_an_attachment_is_required_but_not_both(self):
		_approved, version = self.approved()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version, values=self.values(treasury_reference=""))
		self.assertIn("treasury_reference", caught.exception.detail["fields"])
		frappe.set_user(fx.PLANNER)
		from kentender_core.seeds.fixture_files import labelled_pdf

		upload = frappe.get_doc({"doctype": "File", "file_name": "treasury-dispatch.pdf", "is_private": 1, "content": labelled_pdf("Treasury dispatch evidence")}).insert()
		result = self.confirm(version, values=self.values(treasury_reference="", treasury_attachment=upload.name))
		row = frappe.get_doc("Plan Publication Confirmation", result["confirmation"])
		self.assertTrue(row.treasury_attachment)
		attached = frappe.db.get_value("File", upload.name, ["attached_to_doctype", "attached_to_name"], as_dict=True)
		self.assertEqual((attached.attached_to_doctype, attached.attached_to_name), ("Plan Publication Confirmation", row.name))

	def test_the_dates_and_url_follow_the_rules(self):
		_approved, version = self.approved()
		today = getdate(nowdate())
		tomorrow = str(frappe.utils.add_days(today, 1))
		yesterday = str(frappe.utils.add_days(today, -1))
		cases = {
			"treasury_submitted_on": self.values(treasury_submitted_on=tomorrow),          # in the future
			"website_published_on": self.values(website_published_on=tomorrow),            # in the future
			"treasury_submitted_on ": self.values(treasury_submitted_on=yesterday),        # before the approval date
			"website_published_on ": self.values(treasury_submitted_on=str(today), website_published_on=yesterday),  # before the Treasury date
			"public_plan_url": self.values(public_plan_url="ftp://example.test/plan"),
		}
		for label, values in cases.items():
			with self.subTest(case=label):
				with self.assertRaises(ProcurementPlanningError) as caught:
					self.confirm(version, values=values)
				self.assertEqual(caught.exception.code, "PLN_TREASURY_EVIDENCE_REQUIRED")
		self.assertEqual(self.status(version), "Approved — publication pending")

	def test_the_refusal_names_the_field_and_what_is_wrong_and_the_detail_reaches_the_browser(self):
		# Found live 9 Oct 2026: "www.xyz.com" was refused with only the generic sentence, so the Planner
		# could not tell which of five filled-in fields was wrong.
		_approved, version = self.approved()
		frappe.local.message_log = []
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version, values=self.values(public_plan_url="www.xyz.com"))
		message = str(caught.exception)
		self.assertIn("Public plan URL", message)
		self.assertIn("http:// or https://", message)
		self.assertNotIn("Treasury submission date", message)  # only what is wrong is named
		self.assertEqual(caught.exception.detail["fields"], {"public_plan_url": "Enter the address of the published plan, starting with http:// or https://."})
		# the code and the per-field detail travel on the message log, which Frappe returns to the page
		structured = [m["kt_pln"] for m in frappe.local.message_log if isinstance(m, dict) and m.get("kt_pln")]
		self.assertEqual(structured[-1]["code"], "PLN_TREASURY_EVIDENCE_REQUIRED")
		self.assertEqual(list(structured[-1]["detail"]["fields"]), ["public_plan_url"])

	def test_a_wrong_stale_or_unapproved_version_is_refused(self):
		_approved, version = self.approved()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version, expected=self.record_version(version) + 7)
		self.assertEqual(caught.exception.code, "PLN_STALE_WRITE")
		draft = frappe.db.get_value("Annual Plan Version", {"version_status": "Draft"}, "name")
		if draft:
			with self.assertRaises((ProcurementPlanningError, frappe.DoesNotExistError)):
				self.confirm(draft, expected=self.record_version(draft))
		with self.assertRaises(frappe.DoesNotExistError):
			self.confirm("PLN-DOES-NOT-EXIST-V1", expected=0)
		self.assertEqual(self.confirmations(version, "Current"), [])

	def test_a_historical_publication_failed_version_can_be_confirmed(self):
		_approved, version = self.approved()
		frappe.db.set_value("Annual Plan Version", version, "version_status", "Publication failed", update_modified=False)
		result = self.confirm(version)
		self.assertEqual(result["activation"], "activated")
		self.assertEqual(self.status(version), "Active")


class TestRepeatedPresses(ConfirmationCase):
	def test_the_same_key_returns_the_first_result_and_a_new_key_is_refused(self):
		_approved, version = self.approved()
		repeat_key = key()
		first = self.confirm(version, idempotency_key=repeat_key)
		again = self.confirm(version, idempotency_key=repeat_key, expected=self.record_version(version))
		self.assertEqual(again["confirmation"], first["confirmation"])
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")
		# PLN31-AC-010: one record, one activation
		self.assertEqual(len(self.confirmations(version, "Current")), 1)
		self.assertEqual(self.status(version), "Active")

	def test_the_same_key_with_other_values_is_a_conflict(self):
		_approved, version = self.approved()
		repeat_key = key()
		self.confirm(version, idempotency_key=repeat_key)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version, idempotency_key=repeat_key, values=self.values(treasury_reference="OTHER"), expected=self.record_version(version))
		self.assertEqual(caught.exception.code, "PLN_IDEMPOTENCY_CONFLICT")


class TestHoldAndWithdrawal(ConfirmationCase):
	def hold(self, version: str) -> None:
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		publication_pipeline.hold_plan_publication(
			plan_version=version, reason="A purchase quantity is wrong in the approved plan.",
			hold_kind="Accounting Officer correction request", idempotency_key=key(),
		)

	def test_a_hold_refuses_confirmation_but_still_allows_a_draft(self):
		_approved, version = self.approved()
		self.hold(version)
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version)
		self.assertEqual(caught.exception.code, "PLN_PUBLICATION_HELD")
		frappe.set_user(fx.PLANNER)
		publication_confirmation.save_publication_draft(plan_version=version, values={"treasury_reference": "X"}, idempotency_key=key())
		self.assertEqual(self.status(version), "Approved — publication pending")

	def test_withdrawal_is_possible_only_while_nothing_is_confirmed(self):
		_approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		publication_confirmation.save_publication_draft(plan_version=version, values={"treasury_reference": "X"}, idempotency_key=key())
		# a saved Draft is not evidence: the content is still confirmed unpublished
		frappe.set_user("Administrator")
		self.assertTrue(treasury._confirmed_unpublished(frappe.get_doc("Annual Plan Version", version)))
		self.confirm(version)
		frappe.set_user("Administrator")
		self.assertFalse(treasury._confirmed_unpublished(frappe.get_doc("Annual Plan Version", version)))
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			treasury.request_plan_withdrawal(plan_version=version, reason="Wrongly quantified purchase.", idempotency_key=key())
		self.assertEqual(caught.exception.code, "PLN_WITHDRAWAL_NOT_PERMITTED")


class TestActivationHeld(ConfirmationCase):
	def test_failed_activation_preserves_the_evidence_and_a_repeat_creates_nothing(self):
		_approved, version = self.approved()
		with patch.object(publication_pipeline, "_activation_blockers", return_value=["funding_not_current"]):
			result = self.confirm(version)
		self.assertEqual(result["activation"], "activation_held")
		self.assertEqual(result["blockers"], ["funding_not_current"])
		self.assertEqual(self.status(version), "Published — activation held")
		self.assertEqual(len(self.confirmations(version, "Current")), 1)
		# a second press neither duplicates the evidence nor activates
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.confirm(version)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")
		self.assertEqual(len(self.confirmations(version, "Current")), 1)
		self.assertEqual(self.status(version), "Published — activation held")
		plan = frappe.db.get_value("Annual Plan Version", version, "annual_plan")
		self.assertFalse(frappe.db.get_value("Annual Plan", plan, "active_version"))


class TestCorrection(ConfirmationCase):
	def test_a_correction_appends_keeps_the_earlier_record_and_changes_nothing_else(self):
		_approved, version = self.approved()
		first = self.confirm(version)
		activated_at = frappe.db.get_value("Annual Plan Version", version, "activated_at")
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError):
			publication_confirmation.correct_publication_details(
				confirmation=first["confirmation"], values={"treasury_reference": "MOH/APP/2101/002"}, reason="too short", idempotency_key=key(),
			)
		corrected = publication_confirmation.correct_publication_details(
			confirmation=first["confirmation"], values={"treasury_reference": "MOH/APP/2101/002"},
			reason="The reference was typed from the wrong letter.", idempotency_key=key(),
		)
		self.assertEqual(corrected["action"], "publication_details_corrected")
		frappe.set_user("Administrator")
		old = frappe.get_doc("Plan Publication Confirmation", first["confirmation"])
		new = frappe.get_doc("Plan Publication Confirmation", corrected["confirmation"])
		self.assertEqual((old.confirmation_state, old.superseded_by, old.treasury_reference), ("Superseded", new.name, "MOH/APP/2101/001"))
		self.assertEqual((new.confirmation_state, new.treasury_reference), ("Current", "MOH/APP/2101/002"))
		self.assertEqual(new.public_plan_url, old.public_plan_url)
		# PLN31-AC-011: no second activation, no change of state, nothing repeated
		self.assertEqual(self.status(version), "Active")
		self.assertEqual(frappe.db.get_value("Annual Plan Version", version, "activated_at"), activated_at)

	def test_only_the_planner_may_correct_and_only_the_current_record(self):
		_approved, version = self.approved()
		first = self.confirm(version)
		for user in PLANNER_ONLY_REFUSED:
			with self.subTest(user=user):
				frappe.set_user(user)
				with self.assertRaises(frappe.DoesNotExistError):
					publication_confirmation.correct_publication_details(
						confirmation=first["confirmation"], values={"treasury_reference": "Z"}, reason="A long enough reason.", idempotency_key=key(),
					)
		frappe.set_user(fx.PLANNER)
		publication_confirmation.correct_publication_details(
			confirmation=first["confirmation"], values={"treasury_reference": "Y"}, reason="A long enough reason.", idempotency_key=key(),
		)
		with self.assertRaises(ProcurementPlanningError) as caught:
			publication_confirmation.correct_publication_details(
				confirmation=first["confirmation"], values={"treasury_reference": "W"}, reason="A long enough reason.", idempotency_key=key(),
			)
		self.assertEqual(caught.exception.code, "PLN_REVIEW_STALE")


class TestSuccessor(ConfirmationCase):
	def test_a_successor_needs_its_own_confirmation_and_the_current_plan_stays_operative(self):
		_approved, v1 = self.approved()
		self.confirm(v1)
		plan_name = frappe.db.get_value("Annual Plan Version", v1, "annual_plan")
		plan_reference = frappe.db.get_value("Annual Plan", plan_name, "plan_reference")
		frappe.set_user(fx.PLANNER)
		begun = plan_publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=key())
		successor = begun["successor_version"]
		self.assertNotEqual(successor, v1)
		# the successor is a Draft: nothing to confirm, the predecessor is untouched
		with self.assertRaises((ProcurementPlanningError, frappe.DoesNotExistError)):
			self.confirm(successor, expected=self.record_version(successor))
		self.assertEqual(frappe.db.get_value("Annual Plan", plan_name, "active_version"), v1)
		self.assertEqual(self.status(v1), "Active")


class TestReadModel(ConfirmationCase):
	def test_the_planner_is_offered_the_confirmation_and_everyone_else_reads_the_waiting_line(self):
		approved, version = self.approved()
		frappe.set_user(fx.PLANNER)
		view = plan_read.get_publication_task(publication=approved["publication"])
		self.assertTrue(view["can_confirm"])
		self.assertEqual(view["next_step"]["kind"], "your_turn")
		self.assertEqual(view["next_step"]["headline"], "Confirm plan publication")
		self.assertEqual([r["label"] for r in view["status_rows"]], ["Plan approval", "Treasury submission", "Website publication", "Use for procurement"])
		self.assertEqual(view["status_rows"][1]["state"], "Not yet confirmed")
		self.assertEqual(view["status_rows"][2]["state"], "Not yet confirmed")
		for user in (fx.ACCOUNTING_OFFICER, fx.HOPF):
			with self.subTest(user=user):
				frappe.set_user(user)
				other = plan_read.get_publication_task(publication=approved["publication"])
				self.assertFalse(other["can_confirm"])
				self.assertFalse(other["can_save_draft"])
				self.assertEqual(other["next_step"]["kind"], "waiting")
				self.assertIn("confirm publication", other["next_step"]["headline"])
		# an Auditor reads the record and is not involved in the task (PLN-CHG-001 v1.31 §10.1A.6)
		frappe.set_user(fx.AUDITOR)
		auditor = plan_read.get_publication_task(publication=approved["publication"])
		self.assertFalse(auditor["can_confirm"])
		self.assertEqual(auditor["next_step"]["kind"], "not_involved")
		frappe.set_user("Administrator")
		technical = plan_read.get_publication_task(publication=approved["publication"])
		self.assertFalse(technical["can_confirm"])
		self.assertNotIn("can_retry", technical)
		self.assertNotIn("can_reconcile", technical)
		self.assertNotIn("can_publish", technical)
		self.assertNotIn("can_record_treasury", technical)

	def test_the_approved_plan_can_be_downloaded_as_the_exact_frozen_package(self):
		# PLN31-AC-003 — "Download approved plan": the frozen file the Planner submits and publishes
		approved, version = self.approved()
		publication = frappe.get_doc("Plan Publication", approved["publication"])
		for user in (fx.PLANNER, fx.ACCOUNTING_OFFICER, fx.AUDITOR, "Administrator"):
			with self.subTest(user=user):
				frappe.set_user(user)
				package = plan_read.build_approved_package(publication=publication.name)
				self.assertEqual(package["filename"], "annual-procurement-plan.json")
				self.assertEqual(plan_json.content_digest(package["payload"]), publication.package_hash)
				self.assertEqual(package["payload"]["publicationId"], publication.publication_id)
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.DoesNotExistError):
			plan_read.build_approved_package(publication=publication.name)

	def test_after_confirmation_the_page_shows_the_recorded_facts_and_the_correction(self):
		approved, version = self.approved()
		self.confirm(version)
		frappe.set_user(fx.PLANNER)
		view = plan_read.get_publication_task(publication=approved["publication"])
		self.assertFalse(view["can_confirm"])
		self.assertTrue(view["can_correct"])
		self.assertEqual([r["state"] for r in view["status_rows"]][1:], ["Confirmed", "Confirmed", "Current plan"])
		self.assertEqual(view["confirmation"]["treasury_reference"], "MOH/APP/2101/001")
		self.assertEqual(view["confirmation"]["recorded_by_name"], frappe.db.get_value("User", fx.PLANNER, "full_name"))
		self.assertEqual(view["next_step"]["kind"], "done")

	def test_the_active_plan_card_states_the_confirmation_not_an_acknowledgement(self):
		approved, version = self.approved()
		self.confirm(version)
		reference = frappe.db.get_value("Annual Plan", frappe.db.get_value("Annual Plan Version", version, "annual_plan"), "plan_reference")
		frappe.set_user(fx.AUDITOR)
		card = plan_read.get_annual_plan(plan_reference=reference)["active_view"]["governance_card"]
		self.assertTrue(card["publication_line"].startswith("Confirmed · "), card["publication_line"])
		self.assertEqual(card["publication"], approved["publication"])
		self.assertEqual(card["publication_route"][1:], ["publication", approved["publication"]])

	def test_the_annual_plan_page_links_the_your_turn_line_to_the_task(self):
		# PLN31-AC-016 — the headline is itself the link to its action
		_approved, version = self.approved()
		reference = frappe.db.get_value("Annual Plan", frappe.db.get_value("Annual Plan Version", version, "annual_plan"), "plan_reference")
		frappe.set_user(fx.PLANNER)
		plan = plan_read.get_annual_plan(plan_reference=reference)
		self.assertEqual(plan["next_step"]["kind"], "your_turn")
		self.assertEqual(plan["next_step"]["headline"], "Confirm plan publication")
		routes = [f for f in plan["next_step"]["fixes"] if f["kind"] == "route"]
		self.assertEqual(len(routes), 1)
		self.assertEqual(routes[0]["target"][1], "publication")
		self.assertEqual(plan["open_task"]["label"], "Confirm plan publication")
		frappe.set_user(fx.ACCOUNTING_OFFICER)
		waiting = plan_read.get_annual_plan(plan_reference=reference)["next_step"]
		self.assertEqual(waiting["kind"], "waiting")
		self.assertEqual([f for f in waiting["fixes"] if f["kind"] == "route"], [])
