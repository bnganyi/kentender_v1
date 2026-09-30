# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Disclosure and next steps (EVL-CHG-001 v0.4 §3, §7.1, §7.2 "Reads", §9.10;
KT-STD-001 §3A.6, §3B.7; plan D10, D20; tracker EVL4-1003, EVL4-1006,
EVL4-1007; acceptance EVL-A14, EVL-A16 (read parts)).

No bid name, count or amount reaches the Accounting Officer, an unappointed
person, an undeclared or conflicted member, the Head of Procurement before
delivery or a technical reader, through a read, an error or a task title; an
eligible member, the secretary and an auditor read the bids; an outsider
gets Not found. Every actor in every state reached here has a sound next
step: an action, a named holder and reason, or a truthful done."""

from __future__ import annotations

import json

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.bid_evaluation.services import appointment, my_work_provider, next_steps, preparation, reads
from kentender_procurement.bid_evaluation.services.errors import EvaluationError
from kentender_procurement.bid_evaluation.tests.support import (
	AO, AUDITOR, CHAIR, HOP, MEMBER, MEMBER_2, OUTSIDER, REPLACEMENT, ROSTER, SECRETARY, EvaluationCase,
)
from kentender_procurement.bid_submission.tests.support import key

BIDDER = "Afya Digital Supplies Limited"


def dump(value) -> str:
	return json.dumps(value, default=str)


class TestDisclosure(EvaluationCase):
	def resolve(self, user):
		return reads.resolve(tender_reference=self.reference, user=user)

	def test_who_reads_what(self):
		case = self.reviewing()
		total = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "submitted_total")
		for user in (AO, HOP):
			view = self.resolve(user)
			self.assertNotIn("comparison", view, user)
			self.assertNotIn(BIDDER, dump(view), user)
			self.assertNotIn(total, dump(view), user)
			self.assertNotIn(BIDDER, dump(my_work_provider.my_work_rows(user)), user)
		for user in (CHAIR, MEMBER, SECRETARY, AUDITOR):
			view = self.resolve(user)
			self.assertEqual(view["comparison"]["rows"][0]["bidder"], BIDDER, user)
		with self.assertRaises(frappe.DoesNotExistError):
			self.resolve(OUTSIDER)
		technical = self.resolve("Administrator")
		self.assertEqual(set(technical) & {"comparison", "committee", "source"}, set())
		self.assertEqual(technical["guidance"]["primary_action"], "")
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name")
		with self.assertRaises(frappe.DoesNotExistError):
			reads.bid(tender_reference=self.reference, bid=bid, user=AO)
		detail = reads.bid(tender_reference=self.reference, bid=bid, user=MEMBER)
		self.assertTrue(any(r["label"] == "Memory" for r in detail["requirements"]))
		evidence = next(e for r in detail["requirements"] for e in r["evidence"])
		content = reads.evidence(tender_reference=self.reference, bid=bid, digest=evidence["digest"], user=MEMBER)
		self.assertTrue(content["content"].startswith(b"%PDF"))
		with self.assertRaises(frappe.DoesNotExistError):
			reads.evidence(tender_reference=self.reference, bid=bid, digest=evidence["digest"], user=HOP)

	def test_an_undeclared_member_sees_no_bids(self):
		case = preparation.ensure_preparation(tender=self.name)["evaluation"]
		appointment.appoint_committee(tender=self.name, members=ROSTER, appointment_reference="MOH/EVAL/TEST", expected_version=frappe.db.get_value(
			"Evaluation Case", case, "record_version"), idempotency_key=key(), user=AO)
		self.completed_opening()
		from kentender_procurement.bid_evaluation.services import intake

		intake.receive_opening_package(tender=self.name)
		view = self.resolve(MEMBER)
		self.assertNotIn("comparison", view)
		self.assertNotIn(BIDDER, dump(view))
		self.assertEqual(view["guidance"]["headline"], "Complete your declaration before viewing bids.")
		self.assertEqual([s["marker"] for s in view["tracker"]["stages"]], ["current", "not_started", "not_started"])  # D02-DECLARE-FIRST
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name")
		with self.assertRaises(EvaluationError) as ctx:
			reads.bid(tender_reference=self.reference, bid=bid, user=MEMBER)
		self.assertEqual(ctx.exception.code, "EVL_DECLARATION_REQUIRED")
		ao = self.resolve(AO)
		self.assertNotIn(BIDDER, dump(ao))


class TestNextSteps(EvaluationCase):
	"""A small dead-end matrix over the states this world reaches."""

	def sound(self, label: str, users) -> None:
		doc = frappe.get_doc("Evaluation Case", {"tender": self.name})
		for user in users:
			with self.subTest(state=label, user=user):
				answer = next_steps.answer(doc, user)
				self.assertEqual(ns.problems(answer), [], (label, user, answer))

	def test_every_actor_has_a_sound_answer(self):
		everyone = (AO, HOP, CHAIR, MEMBER, MEMBER_2, SECRETARY, AUDITOR, REPLACEMENT, "Administrator")
		preparation.ensure_preparation(tender=self.name)
		self.sound("prepared", everyone)
		view = reads.resolve(tender_reference=self.reference, user=AO)
		self.assertEqual(view["guidance"]["headline"], "Appoint the members who will evaluate this tender.")
		self.assertEqual([s["marker"] for s in view["tracker"]["stages"]], ["current", "not_started", "not_started"])
		self.resolve_all_state()

	def resolve_all_state(self) -> None:
		from kentender_procurement.bid_evaluation.seeds import clear

		clear.wipe(tenders=[self.name])
		case = self.reviewing()
		everyone = (AO, HOP, CHAIR, MEMBER, MEMBER_2, SECRETARY, AUDITOR, "Administrator")
		self.sound("reviewing", everyone)
		member = reads.resolve(tender_reference=self.reference, user=MEMBER)
		self.assertTrue(member["guidance"]["headline"].startswith("Review the evidence for the "))
		self.assertEqual([s["marker"] for s in member["tracker"]["stages"]], ["done", "current", "not_started"])
		self.resolve_all(case)
		self.sound("ready", everyone)
		self.assertEqual(reads.resolve(tender_reference=self.reference, user=SECRETARY)["guidance"]["headline"],
			"Check the report and send it to members for signing.")
