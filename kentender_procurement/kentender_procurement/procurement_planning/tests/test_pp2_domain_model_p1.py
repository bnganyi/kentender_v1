# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1 — PP2 domain model schema and constraint tests."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_ALLOWED_TRANSITIONS,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_VALID_STATUSES,
	PLAN_ACTIVE,
	PLAN_ALLOWED_TRANSITIONS,
	PLAN_DRAFT,
	PLAN_VALID_STATUSES,
)


class TestPP2DomainModelP1(IntegrationTestCase):
	"""Validate PP2 DocTypes, fields, and transition constants after migrate."""

	def test_procurement_plan_pp2_status_options(self):
		meta = frappe.get_meta("Procurement Plan")
		status_df = meta.get_field("status")
		self.assertIsNotNone(status_df)
		options = {o.strip() for o in (status_df.options or "").split("\n") if o.strip()}
		self.assertEqual(options, set(PLAN_VALID_STATUSES))
		self.assertIn("is_master_seed", {f.fieldname for f in meta.fields})

	def test_procurement_package_pp2_fields(self):
		meta = frappe.get_meta("Procurement Package")
		required = {
			"readiness_status",
			"locked_after_release",
			"planning_inclusion_code",
			"demand_id",
			"budget_line_id",
			"procurement_category",
			"release_code",
			"tender_code",
			"journey_code",
			"consumed_at",
			"is_master_seed",
		}
		names = {f.fieldname for f in meta.fields}
		missing = required - names
		self.assertFalse(missing, f"Missing PP2 package fields: {missing}")
		status_df = meta.get_field("status")
		options = {o.strip() for o in (status_df.options or "").split("\n") if o.strip()}
		self.assertEqual(options, set(PKG_VALID_STATUSES))

	def test_procurement_package_line_pp2_fields(self):
		meta = frappe.get_meta("Procurement Package Line")
		required = {"demand_item_code", "line_title", "procurement_category", "line_status", "is_master_seed"}
		names = {f.fieldname for f in meta.fields}
		missing = required - names
		self.assertFalse(missing, f"Missing PP2 line fields: {missing}")

	def test_pp2_supporting_doctypes_exist(self):
		for dt in (
			"Package Method Decision",
			"Package Readiness Result",
			"Package Review Decision",
			"Planning Release Consumption Record",
			"Planning Correction Supersession Record",
			"Planning Audit Event",
		):
			self.assertTrue(frappe.db.exists("DocType", dt), f"Missing DocType {dt}")

	def test_unique_business_code_fields(self):
		cases = (
			("Package Method Decision", "method_decision_code"),
			("Package Readiness Result", "readiness_code"),
			("Planning Release Consumption Record", "consumption_code"),
			("Planning Audit Event", "event_code"),
		)
		for doctype, fieldname in cases:
			meta = frappe.get_meta(doctype)
			df = meta.get_field(fieldname)
			self.assertTrue(df.unique, f"{doctype}.{fieldname} must be unique")

	def test_pp2_package_transition_constants(self):
		self.assertIn(PKG_IN_REVIEW, PKG_ALLOWED_TRANSITIONS[PKG_DRAFT])

	def test_plan_transition_constants(self):
		self.assertIn(PLAN_ACTIVE, PLAN_ALLOWED_TRANSITIONS[PLAN_DRAFT])

	def test_planning_inclusion_service_exports(self):
		from kentender_procurement.procurement_planning.services import planning_inclusion_service

		self.assertTrue(callable(planning_inclusion_service.create_planning_inclusion))
		self.assertTrue(callable(planning_inclusion_service.get_planning_inclusion))
