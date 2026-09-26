# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 8 — §16.2 draft assistance.

Covers: proposal-shape validation (a bad proposal creates no batch at all);
real Draft-scoped content created on accept, passing the same validators as
direct entry (a malformed accepted payload is rejected, not silently saved);
no "Accept all" (empty/omitted item list is refused); staleness once the
Draft's `record_version` moves past the batch's snapshot; rejection creates
no content; and the double-decision guard (an already-decided item can't be
decided again).
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.std_configuration.api import std_configuration_api as api
from kentender_procurement.std_configuration.services import std_assistance, std_authorization, std_lifecycle

PACKAGE_CODE = "KE-TEST-STD-P8"


class TestSTDChg001Phase8DraftAssistance(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.suffix = uuid.uuid4().hex[:8]
		self._users: list[str] = []
		self._cleanup()
		std_authorization.ensure_std_configuration_governance_roles()
		self.configurator = self._user("configurator", "STD Configurator")
		self.package = frappe.get_doc(
			{
				"doctype": "STD Cfg Package",
				"package_code": PACKAGE_CODE,
				"official_title": "Test Package for Phase 8",
				"requirement_profile": "Information Technology",
			}
		).insert(ignore_permissions=True)
		self.draft = std_lifecycle.create_draft(PACKAGE_CODE, "April 2021 edition", actor=self.configurator)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._cleanup()
		for email in self._users:
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _cleanup(self):
		# Scoped to THIS test's own package's Draft names throughout — a
		# blanket `{"draft_id": ["like", "%"]}` or
		# `{"reference_doctype": ["in", [...]]}` (no reference_name filter)
		# here would delete every OTHER package's content too, including the
		# real golden `KE-PPRA-IT` fixture (Phase 9). Confirmed live: this
		# exact bug class silently passed for 8 phases because each phase's
		# tests were the only content on the site at the time — only Phase 9's
		# persistent fixture surfaced it.
		draft_names = frappe.get_all("STD Cfg Draft", {"package_id": PACKAGE_CODE}, pluck="name")
		if draft_names:
			frappe.db.delete("STD Cfg Assistance Batch", {"draft_id": ["in", draft_names]})
			for doctype in std_lifecycle.REFERENCE_SCOPED_CONTENT_DOCTYPES:
				frappe.db.delete(doctype, {"reference_name": ["in", draft_names]})
		frappe.db.delete("STD Cfg Source Document", {"official_title": ["like", "Test Source%"]})
		frappe.db.delete("STD Cfg Draft", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Package", {"package_code": PACKAGE_CODE})
		frappe.db.commit()

	def _user(self, label: str, role: str) -> str:
		email = f"std.p8.{label}.{self.suffix}@example.test"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": label,
				"enabled": 1,
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)
		self._users.append(email)
		return email

	def _valid_parameter_proposal(self, key="fixture.assist.param"):
		return {
			"proposed_item_label": "Tender validity",
			"owning_area": "PCFG-03",
			"target_entity": "STD Cfg Parameter Definition",
			"proposed_payload": {
				"parameter_key": key,
				"label": "Tender validity",
				"value_type": "Duration",
				"runtime_owner": "Tender Preparation",
				"render_binding": "TDS.validity",
			},
		}

	# --- proposal shape validation --------------------------------------------

	def test_prepare_rejects_empty_proposal_list(self):
		with self.assertRaises(frappe.ValidationError):
			std_assistance.prepare_proposal(
				self.draft.name, "Prior configuration", "ref.json", [], actor=self.configurator
			)
		self.assertEqual(frappe.db.count("STD Cfg Assistance Batch", {"draft_id": self.draft.name}), 0)

	def test_prepare_rejects_disallowed_target_entity(self):
		bad = self._valid_parameter_proposal()
		bad["target_entity"] = "User"  # not a governed proposal target
		with self.assertRaises(frappe.ValidationError):
			std_assistance.prepare_proposal(
				self.draft.name, "Prior configuration", "ref.json", [bad], actor=self.configurator
			)
		self.assertEqual(frappe.db.count("STD Cfg Assistance Batch", {"draft_id": self.draft.name}), 0)

	def test_prepare_rejects_missing_required_field(self):
		bad = self._valid_parameter_proposal()
		del bad["proposed_payload"]
		with self.assertRaises(frappe.ValidationError):
			std_assistance.prepare_proposal(
				self.draft.name, "Prior configuration", "ref.json", [bad], actor=self.configurator
			)

	def test_prepare_creates_real_batch_with_proposed_items(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		self.assertEqual(batch.assistance_type, "Prior configuration")
		self.assertEqual(len(batch.proposals), 1)
		self.assertEqual(batch.proposals[0].status, "Proposed")
		self.assertEqual(batch.draft_record_version_snapshot, self.draft.record_version)

	# --- accept ----------------------------------------------------------------

	def test_accept_creates_real_content_passing_normal_validators(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		result = std_assistance.accept_items(batch.name, [batch.proposals[0].name], actor=self.configurator)
		created_name = result["accepted"][0]["created"]
		self.assertTrue(
			frappe.db.exists(
				"STD Cfg Parameter Definition",
				{"name": created_name, "reference_doctype": "STD Cfg Draft", "reference_name": self.draft.name},
			)
		)
		batch.reload()
		self.assertEqual(batch.proposals[0].status, "Accepted")
		self.assertEqual(batch.proposals[0].accepted_entity_name, created_name)

	def test_accept_rejects_malformed_payload_via_normal_doctype_guard(self):
		bad = self._valid_parameter_proposal()
		bad["proposed_payload"]["value_type"] = "Choice"  # Choice requires allowed_values — Phase 2's own guard
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [bad], actor=self.configurator
		)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.accept_items(batch.name, [batch.proposals[0].name], actor=self.configurator)

	def test_accept_requires_explicit_item_names_no_accept_all(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.accept_items(batch.name, [], actor=self.configurator)

	def test_cannot_decide_an_already_decided_item(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		item_name = batch.proposals[0].name
		std_assistance.accept_items(batch.name, [item_name], actor=self.configurator)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.accept_items(batch.name, [item_name], actor=self.configurator)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.reject_items(batch.name, [item_name], actor=self.configurator)

	def test_accept_bumps_draft_record_version(self):
		before = frappe.db.get_value("STD Cfg Draft", self.draft.name, "record_version")
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		std_assistance.accept_items(batch.name, [batch.proposals[0].name], actor=self.configurator)
		after = frappe.db.get_value("STD Cfg Draft", self.draft.name, "record_version")
		self.assertGreater(int(after), int(before or 0))

	# --- reject ------------------------------------------------------------------

	def test_reject_creates_no_content(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		std_assistance.reject_items(batch.name, [batch.proposals[0].name], actor=self.configurator)
		batch.reload()
		self.assertEqual(batch.proposals[0].status, "Rejected")
		self.assertFalse(
			frappe.db.exists(
				"STD Cfg Parameter Definition",
				{"reference_doctype": "STD Cfg Draft", "reference_name": self.draft.name},
			)
		)

	# --- staleness -----------------------------------------------------------------

	def test_stale_batch_rejected_on_accept_and_reject(self):
		batch = std_assistance.prepare_proposal(
			self.draft.name, "Prior configuration", "ref.json", [self._valid_parameter_proposal()], actor=self.configurator
		)
		# Simulate the Draft moving since this batch was prepared (e.g. a real
		# area-save through the front door would also bump record_version).
		frappe.db.set_value("STD Cfg Draft", self.draft.name, "record_version", (self.draft.record_version or 0) + 5)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.accept_items(batch.name, [batch.proposals[0].name], actor=self.configurator)
		with self.assertRaises(frappe.ValidationError):
			std_assistance.reject_items(batch.name, [batch.proposals[0].name], actor=self.configurator)

	# --- API layer -----------------------------------------------------------------

	def test_full_path_through_api_layer(self):
		frappe.set_user(self.configurator)
		prepared = api.prepare_prior_configuration_proposal(
			self.draft.name, "IT_STD_Config_Control_Pack_v3.json", [self._valid_parameter_proposal("fixture.api.param")]
		)
		self.assertEqual(prepared["proposal_count"], 1)

		batch = frappe.get_doc("STD Cfg Assistance Batch", prepared["batch_id"])
		result = api.accept_assistance_items(batch.name, [batch.proposals[0].name])
		frappe.set_user("Administrator")
		self.assertEqual(len(result["accepted"]), 1)
