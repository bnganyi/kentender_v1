# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §6, §8 and §9 (BOP10-204): PRC-N03 separation of
authority, protected Not found, attendance grants no read, and the closed
§8 error contract."""

from __future__ import annotations

from kentender_procurement.proceedings.services import errors
from kentender_procurement.proceedings.tests.support import CHAIR, OUTSIDER, OWNER_TYPE, ROSTER, VISITOR, ProceedingsCase, attendance, lifecycle, reads


class TestSeparation(ProceedingsCase):
	def test_prc_n03_administrator_cannot_start_sign_or_read(self):
		created = self.create()
		self.assertCode("PRC_OWNER_UNAVAILABLE", lifecycle.start_proceeding, **self.ref(created), roster=ROSTER, custody_reference="C", owner_event_id="s",
			idempotency_key=self.key(), actor="Administrator")
		self.assertCode("PRC_OWNER_UNAVAILABLE", reads.read_proceeding, owner_type=OWNER_TYPE, owner_id=self.owner_id(created), user="Administrator")
		self.assertCode("PRC_OWNER_UNAVAILABLE", reads.export_proceeding, owner_type=OWNER_TYPE, owner_id=self.owner_id(created), user="Administrator")

	def test_attendance_grants_no_read(self):
		created = self.create()
		self.start(created)
		attendance.record_attendance(**self.ref(created), person_name="Test Visitor", user=VISITOR, capacity="Tenderer representative",
			represented_tenderer="Example Test Supplier Ltd", movement="Arrival", idempotency_key=self.key(), actor=CHAIR)
		for user in (VISITOR, OUTSIDER):
			with self.subTest(user=user):
				self.assertCode("PRC_OWNER_UNAVAILABLE", reads.read_proceeding, owner_type=OWNER_TYPE, owner_id=self.owner_id(created), user=user)
		self.assertCode("PRC_OWNER_UNAVAILABLE", reads.read_proceeding, owner_type=OWNER_TYPE, owner_id="SIM-DOES-NOT-EXIST", user=CHAIR)

	def test_only_the_recorder_records_attendance(self):
		created = self.create()
		self.assertCode("PRC_OWNER_UNAVAILABLE", attendance.record_attendance, **self.ref(created), person_name="x", capacity="Public observer", movement="Arrival",
			idempotency_key=self.key(), actor=OUTSIDER)

	def owner_id(self, created) -> str:
		import frappe

		return frappe.db.get_value("Proceeding", created["proceeding"], "owner_id")


class TestErrorContract(ProceedingsCase):
	def test_the_contract_is_the_closed_section_8_set(self):
		self.assertEqual(sorted(errors.ERROR_CODES), sorted([
			"PRC_OWNER_UNAVAILABLE", "PRC_START_BLOCKED", "PRC_MEMBER_REQUIRED", "PRC_TARGET_CHANGED", "PRC_PROOF_UNVERIFIED", "PRC_EVIDENCE_INCOMPLETE",
			"PRC_VERSION_CONFLICT", "PRC_ALREADY_FINALIZED",
		]))
		self.assertEqual(errors.MESSAGES["PRC_TARGET_CHANGED"], "The opening record changed. Review the latest version before signing.")
		with self.assertRaises(ValueError):
			errors.fail("PRC_SOMETHING_NEW")
