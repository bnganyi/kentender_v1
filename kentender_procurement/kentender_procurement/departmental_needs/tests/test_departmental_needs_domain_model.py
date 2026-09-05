"""Phase 1 domain-model tests for NDS-CHG-001 v1.6 §4.

Covers the reshaped schema: the thin root (§4.2), the version record and its
field bounds and immutability (§4.3, §13), the review task and withdrawal
request single-open guards (§4.4, §4.6), the decision record's reason contract
(§4.5, NDS-BR-011), and the absence of every concept §1.1/§16.4.11 removes —
including `procuring_entity` (AUTH-ADR-001 v1.6 §1.1: the site is exactly one
implicit Procuring Entity) and the `Needs Intake Window` doctype itself.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.departmental_needs.constants import (
	STATE_ACCEPTED,
	STATE_DRAFT,
	VERSION_DRAFT,
	VERSION_SUBMITTED,
	WITHDRAWAL_AWAITING_REVIEW,
)
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	FY,
	_granted_units,
	upsert_departmental_needs,
)

RETIRED_DOCTYPES = (
	"Departmental Need Item",
	"Departmental Need Attachment",
	"Departmental Need Review",
	# NDS-CHG-001 v1.6 §4.1/§16.4.11 — the windowed intake mechanism is
	# retired outright; the Needs-submission flag lives on ERPNext `Fiscal
	# Year` (kentender_needs_submission_open/_closes_at), owned by
	# Configuration & Governance.
	"Needs Intake Window",
)

# §1.1 / §16.4 / §17 — none of these may exist on the Need or its version.
PROHIBITED_FIELDS = (
	"business_justification",
	"delivery_or_use_location",
	"indicative_cost",
	"currency",
	"other_unit",
	"submitted_by",
	"pe_fy_context",
	"revision_no",
	# AUTH-ADR-001 v1.6 §1.1 — the site is exactly one implicit Procuring
	# Entity; no NDS doctype carries this field any more.
	"procuring_entity",
)


class TestDepartmentalNeedsDomainModel(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()
		# Two real, distinct Organisation Units Grace is actually granted
		# Departmental Author over (§14.2) — used to build ad-hoc fixture
		# records below without guessing a Procuring-Entity-scoped doc name
		# that no longer exists.
		units = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)
		cls.ou_digital_health = units["Digital Health"]
		cls.ou_hrmd = units["Human Resources Management and Development"]

	def _new_need(self, state: str = STATE_DRAFT):
		reference = f"NDS-TEST-{uuid4().hex[:10].upper()}"
		need = frappe.get_doc(
			{
				"doctype": "Departmental Need",
				"need_reference": reference,
				"organisation_unit": self.ou_digital_health,
				"financial_year": FY,
				"current_state": state,
				"record_version": 1,
			}
		).insert(ignore_permissions=True)
		return need

	def _new_version(self, need, **overrides):
		values = {
			"doctype": "Departmental Need Version",
			"need_version_id": f"{need.need_reference}-V001",
			"departmental_need": need.name,
			"version_number": 1,
			"version_status": VERSION_DRAFT,
			"title": "Clinical deployment laptops for rollout",
			"description": "Laptop computers for deployment at priority health facilities.",
			"expected_operational_result": "Facilities can use the deployed digital health services.",
			"indicative_quantity": 10,
			"unit": "Each",
			"required_by_date": "2027-12-31",
		}
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	# --- §4.2 root ---------------------------------------------------------

	def test_retired_doctypes_are_absent(self):
		for doctype in RETIRED_DOCTYPES:
			self.assertFalse(
				frappe.db.exists("DocType", doctype),
				msg=f"{doctype} is removed by NDS-CHG-001 v1.6 §1.1/§16.4.11",
			)

	def test_root_carries_no_prohibited_or_content_field(self):
		fields = {f.fieldname for f in frappe.get_meta("Departmental Need").fields}
		for prohibited in PROHIBITED_FIELDS:
			self.assertNotIn(prohibited, fields)
		# Requirement content belongs to the version, never the root (§4.2/§4.3).
		for content in ("title", "description", "expected_operational_result", "required_by_date"):
			self.assertNotIn(content, fields)

	def test_review_task_carries_no_procuring_entity_field(self):
		fields = {f.fieldname for f in frappe.get_meta("Departmental Need Review Task").fields}
		self.assertNotIn("procuring_entity", fields)

	def test_financial_year_links_to_the_erpnext_doctype(self):
		"""§3/§16.2/§16.4.11 — no KenTender-owned `Financial Year` doctype."""
		meta = frappe.get_meta("Departmental Need")
		self.assertEqual(meta.get_field("financial_year").options, "Fiscal Year")

	def test_root_scope_is_immutable(self):
		need = self._new_need()
		need.organisation_unit = self.ou_hrmd
		with self.assertRaises(frappe.ValidationError):
			need.save(ignore_permissions=True)

	def test_need_cannot_be_deleted(self):
		# §13 retains every business record. Deletion is simply an invalid
		# command for it, which is §9's NDS_STATE_CONFLICT — the same typed
		# result the other four retention guards return.
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError) as caught:
			need.delete()
		self.assertEqual(caught.exception.code, "NDS_STATE_CONFLICT")

	# --- §4.3 version ------------------------------------------------------

	def test_version_holds_the_six_requester_values(self):
		fields = {f.fieldname for f in frappe.get_meta("Departmental Need Version").fields}
		for value in (
			"title",
			"description",
			"expected_operational_result",
			"indicative_quantity",
			"unit",
			"required_by_date",
		):
			self.assertIn(value, fields)
		self.assertNotIn("business_justification", fields)

	def test_unit_links_to_the_governed_catalogue(self):
		"""§1.1 "New in v1.6" — ERPNext native `UOM`, not the retired custom doctype."""
		meta = frappe.get_meta("Departmental Need Version")
		self.assertEqual(meta.get_field("unit").options, "UOM")

	def test_title_bounds_are_enforced(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._new_version(need, title="abc")

	def test_expected_operational_result_bounds_are_enforced(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._new_version(need, expected_operational_result="too short")

	def test_quantity_rejects_more_than_three_decimals(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._new_version(need, indicative_quantity=1.23456)

	def test_quantity_must_be_positive(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._new_version(need, indicative_quantity=-1)

	def test_submitted_version_content_is_immutable(self):
		need = self._new_need()
		version = self._new_version(need)
		frappe.db.set_value(
			"Departmental Need Version",
			version.name,
			"version_status",
			VERSION_SUBMITTED,
			update_modified=False,
		)
		reloaded = frappe.get_doc("Departmental Need Version", version.name)
		reloaded.indicative_quantity = 999
		with self.assertRaises(DepartmentalNeedError):
			reloaded.save(ignore_permissions=True)

	def test_draft_version_content_is_editable(self):
		need = self._new_need()
		version = self._new_version(need)
		version.indicative_quantity = 42
		version.save(ignore_permissions=True)
		self.assertEqual(
			frappe.db.get_value("Departmental Need Version", version.name, "indicative_quantity"), 42
		)

	# --- §4.4 review task --------------------------------------------------

	def _open_task(self, need, task_type="Initial acceptance"):
		return frappe.get_doc(
			{
				"doctype": "Departmental Need Review Task",
				"review_task_id": f"NDT-{uuid4().hex.upper()}",
				"departmental_need": need.name,
				"task_type": task_type,
				"organisation_unit": need.organisation_unit,
				"financial_year": need.financial_year,
				"status": "Open",
				"decision_token": uuid4().hex,
				"opened_at": frappe.utils.now_datetime(),
			}
		).insert(ignore_permissions=True)

	def test_only_one_open_review_task_per_need(self):
		need = self._new_need()
		self._open_task(need)
		with self.assertRaises(DepartmentalNeedError):
			self._open_task(need)

	# --- §4.5 decision -----------------------------------------------------

	def _decision(self, need, **overrides):
		values = {
			"doctype": "Departmental Need Decision",
			"decision_id": f"NDD-{uuid4().hex.upper()}",
			"departmental_need": need.name,
			"action": "Create",
			"actor": AUTHOR,
			"occurred_at": frappe.utils.now_datetime(),
			"prior_state": STATE_DRAFT,
			"result_state": STATE_DRAFT,
			"idempotency_key": uuid4().hex,
		}
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_return_requires_a_reason(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._decision(need, action="Return for correction", reason="too short")

	def test_accept_collects_no_reason(self):
		need = self._new_need()
		with self.assertRaises(DepartmentalNeedError):
			self._decision(
				need,
				action="Accept for planning",
				reason="An accept decision must not carry a reason at all.",
			)

	def test_decision_is_immutable_once_recorded(self):
		need = self._new_need()
		decision = self._decision(need)
		decision.result_state = STATE_ACCEPTED
		with self.assertRaises(DepartmentalNeedError):
			decision.save(ignore_permissions=True)

	def test_idempotency_key_is_unique(self):
		need = self._new_need()
		key = uuid4().hex
		self._decision(need, idempotency_key=key)
		with self.assertRaises(frappe.UniqueValidationError):
			self._decision(need, idempotency_key=key)

	# --- §4.6 withdrawal request -------------------------------------------

	def _withdrawal(self, need, version, **overrides):
		values = {
			"doctype": "Need Withdrawal Request",
			"withdrawal_request_id": f"NDS-WDR-{uuid4().hex[:12].upper()}",
			"departmental_need": need.name,
			"accepted_version": version.name,
			"requested_by": AUTHOR,
			"reason": "The department no longer requires this equipment in the current year.",
			"status": WITHDRAWAL_AWAITING_REVIEW,
			"record_version": 1,
		}
		values.update(overrides)
		return frappe.get_doc(values).insert(ignore_permissions=True)

	def test_only_one_open_withdrawal_request_per_need(self):
		need = self._new_need(STATE_ACCEPTED)
		version = self._new_version(need)
		self._withdrawal(need, version)
		with self.assertRaises(DepartmentalNeedError):
			self._withdrawal(need, version)

	def test_withdrawal_reason_bounds_are_enforced(self):
		need = self._new_need(STATE_ACCEPTED)
		version = self._new_version(need)
		with self.assertRaises(DepartmentalNeedError):
			self._withdrawal(need, version, reason="too short")

	# --- §14.3 seed shape ---------------------------------------------------

	def test_seed_creates_the_four_default_needs_with_versions(self):
		for reference in (
			"NDS-MOH-2027-0001",
			"NDS-MOH-2027-0002",
			"NDS-MOH-2027-0003",
			"NDS-MOH-2027-0004",
		):
			self.assertTrue(frappe.db.exists("Departmental Need", reference))
			current = frappe.db.get_value("Departmental Need", reference, "current_version")
			self.assertTrue(current, msg=f"{reference} must point at a current version")
			self.assertTrue(
				frappe.db.get_value("Departmental Need Version", current, "expected_operational_result")
			)

	def test_the_harmonized_laptop_needs_are_accepted_on_their_first_version(self):
		"""SEED-001 §3.2 — 0003/0004 (the combined item's two source Needs)
		reach Accepted directly on V1; nothing is Returned."""
		for reference in ("NDS-MOH-2027-0003", "NDS-MOH-2027-0004"):
			row = frappe.db.get_value(
				"Departmental Need", reference, ["current_state", "current_accepted_version"], as_dict=True
			)
			self.assertEqual(row.current_state, STATE_ACCEPTED, reference)
			self.assertEqual(row.current_accepted_version, f"{reference}-V001", reference)

	def test_accepted_seed_need_points_at_its_accepted_version(self):
		row = frappe.db.get_value(
			"Departmental Need",
			"NDS-MOH-2027-0001",
			["current_state", "current_accepted_version"],
			as_dict=True,
		)
		self.assertEqual(row.current_state, STATE_ACCEPTED)
		self.assertEqual(row.current_accepted_version, "NDS-MOH-2027-0001-V001")
