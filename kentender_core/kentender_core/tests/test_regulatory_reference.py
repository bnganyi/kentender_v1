"""CFG-CHG-002 v0.11 §4.6-§4.10, §7 — the regulator reference register:
Regulatory Reference Set/Version, append-only Reference Verification Event,
the §5 selection algorithm (`resolve_reference`) and Planning's unchanged
`get_regulatory_reference(fiscal_year)` compatibility read.

CFG10-AC-033/034/040-045 (immutable versions, verification evidence,
overlap/supersession, date-basis resolution); FU-08 (threshold_matrix now
derived from Procurement Method Profile, closing the old duplicate-write).

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_regulatory_reference
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import regulatory_reference as register
from kentender_core.services import site_configuration as configuration
from kentender_core.services.configuration_errors import ConfigurationError
from kentender_core.tests import v16_fixtures as fx

NS = "KT_TEST_REGREF"
Y = 2094  # far-future, purged by fiscal-year cleanup in the shared purge


class RegulatoryReferenceTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.ensure_site_configured()
		site_setup._seed_catalogues()
		cls.fy = configuration._fy_name(Y)
		if not frappe.db.exists("Fiscal Year", cls.fy):
			configuration.add_fiscal_year(start_year=Y)
		from kentender_core.services import procurement_settings as settings

		# This module also registers method profiles (threshold_matrix is
		# derived from them); purge those too, or a leftover open-ended Open
		# Tender version overlaps every later suite's (D16 refuses that).
		register.purge_fixture_references(NS)
		settings.purge_fixture_profiles(NS)
		cls.addClassCleanup(lambda: (register.purge_fixture_references(NS), settings.purge_fixture_profiles(NS), frappe.db.commit()))
		frappe.db.commit()

	def code(self, caught) -> str:
		return getattr(caught.exception, "code", "")

	def _create(self, key: str, kind: str = "Reservation rules"):
		return register.create_regulatory_reference(reference_key=key, reference_kind=kind, display_name=key, fixture_namespace=NS)

	def _save_reservation_version(self, reference_set: str, target_percent=30, effective_from="2094-07-01", effective_until="", **kwargs):
		return register.save_regulatory_reference_version(
			reference_set=reference_set,
			payload={
				"obligation_code": "ANNUAL-RESERVATION-TARGET",
				"measure_stage": "PlanningAllocation",
				"target_percent": target_percent,
				"county_target_percent": 20,
				"categories": [
					{"category": "None", "advantage_rank": 0},
					{"category": "Youth", "advantage_rank": 1},
				],
			},
			effective_from=effective_from,
			effective_until=effective_until,
			applicability_basis="FiscalYearStart",
			fixture_namespace=NS,
			**kwargs,
		)


class TestReferenceSets(RegulatoryReferenceTestCase):
	def test_create_then_a_second_call_with_the_same_key_is_idempotent_by_key(self):
		"""§7.3 — Create set then Save first version are two separate,
		individually idempotent commands."""
		out = self._create("KT-TEST-SET-A")
		self.assertTrue(out["created"])
		self.assertEqual(out["reference_kind"], "Reservation rules")

	def test_rejects_an_unknown_kind(self):
		with self.assertRaises(ConfigurationError) as caught:
			register.create_regulatory_reference(reference_key="KT-TEST-BAD-KIND", reference_kind="Not a kind")
		self.assertEqual(self.code(caught), "CFG_PROFILE_INVALID")

	def test_an_empty_set_lists_no_version_and_supports_resume(self):
		"""§7.3 — "Resumed empty set: List shows No version saved and Add
		first version"."""
		out = self._create("KT-TEST-EMPTY-SET")
		read = register.get_reference_set(out["reference_set"])
		self.assertEqual(read["versions"], [])
		self.assertIsNone(read["latest"])

	def test_rename_changes_only_the_display_name(self):
		out = self._create("KT-TEST-RENAME-SET")
		renamed = register.rename_regulatory_reference(reference_set=out["reference_set"], display_name="Renamed Rule")
		self.assertEqual(renamed["display_name"], "Renamed Rule")
		read = register.get_reference_set(out["reference_set"])
		self.assertEqual(read["reference_key"], "KT-TEST-RENAME-SET")
		self.assertEqual(read["reference_kind"], "Reservation rules")


class TestVersionsAndSupersession(RegulatoryReferenceTestCase):
	def test_a_new_version_supersedes_the_overlapping_one_and_is_never_edited_in_place(self):
		out = self._create("KT-TEST-SUPERSEDE")
		first = self._save_reservation_version(out["reference_set"], target_percent=30, effective_from="2094-07-01", effective_until="2095-06-30")
		self.assertTrue(first["created"])
		self.assertEqual(first["version_number"], 1)

		# Owner decision 23 Sep 2026 — a version freezes once a source check
		# is recorded against it or once it takes effect, whichever comes
		# first. This one is future-dated and unchecked, so it is still
		# ordinary unfinished configuration and is corrected in place.
		self.assertTrue(register.get_regulatory_reference_version(first["reference"])["can_edit"])
		register.update_regulatory_reference_version(
			reference=first["reference"],
			payload={"obligation_code": "KT-TEST-SUPERSEDE", "measure_stage": "PlanningAllocation", "target_percent": 32},
			effective_from="2094-07-01",
			effective_until="2095-06-30",
			interpretation="Corrected before anything used it",
		)
		corrected = register.get_regulatory_reference_version(first["reference"])
		self.assertEqual(corrected["version_number"], 1, "a correction is not a new version")
		self.assertEqual(corrected["payload"]["target_percent"], 32)
		self.assertEqual(corrected["interpretation"], "Corrected before anything used it")

		# Once a source check is recorded against it, it is evidenced and frozen.
		register.record_reference_verification(
			target_doctype=register.DOCTYPE,
			target_name=first["reference"],
			outcome="Pending",
			unresolved_points="Awaiting the gazette copy.",
			fixture_namespace=NS,
		)
		frozen = register.get_regulatory_reference_version(first["reference"])
		self.assertFalse(frozen["can_edit"])
		self.assertIn("source check has been recorded", frozen["edit_blocked_reason"])
		doc = frappe.get_doc(register.DOCTYPE, first["reference"])
		doc.interpretation = "Changed after the fact"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(register.DOCTYPE, first["reference"], ignore_permissions=True)

		second = self._save_reservation_version(out["reference_set"], target_percent=35, effective_from="2094-09-01", supersedes_version_ids=[first["reference"]])
		self.assertEqual(second["version_number"], 2)
		self.assertIn(first["reference"], second["superseded"])
		self.assertEqual(frappe.db.get_value(register.DOCTYPE, first["reference"], "status"), "Superseded")
		self.assertTrue(frappe.db.exists(register.DOCTYPE, first["reference"]))

	def test_rejects_an_out_of_range_target_percent(self):
		out = self._create("KT-TEST-BAD-TARGET")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"],
				payload={"obligation_code": "X", "measure_stage": "PlanningAllocation", "target_percent": 150},
				effective_from="2094-07-01",
				fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_saving_a_version_for_an_unimplemented_kind_is_refused(self):
		"""Phase 2c work; not silently accepted as an untyped blob."""
		out = self._create("KT-TEST-UNSUPPORTED-KIND", kind="Exclusive preference")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={}, effective_from="2094-07-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")


class TestTypedPayloads(RegulatoryReferenceTestCase):
	"""CFG-CHG-002 v0.11 §4.7/§10.7 Phase 2c — the four remaining kinds'
	typed payload validators (Method eligibility deliberately stays
	refused here — it is fronted by Procedure Method Profile, D1/D10)."""

	def test_method_eligibility_is_still_refused_through_this_path(self):
		out = self._create("KT-TEST-METHOD-KIND", kind="Method eligibility")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={}, effective_from="2094-07-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_exclusive_preference_round_trip_and_validation(self):
		out = self._create("KT-TEST-EXPREF", kind="Exclusive preference")
		saved = register.save_regulatory_reference_version(
			reference_set=out["reference_set"],
			payload={
				"restriction_code": "WORKS-LOCAL-CONTENT",
				"category": "Works",
				"comparator": "LessThanOrEqual",
				"amount": 1_000_000_000,
				"funding_origin_condition": "GoK-funded",
				"local_origin_condition": "Kenyan-registered",
				"eligible_party_classification": "Citizen contractor",
				"source_reference": "reg 163",
			},
			effective_from="2094-07-01",
			fixture_namespace=NS,
		)
		read = register.get_regulatory_reference_version(saved["reference"])
		self.assertEqual(read["payload"]["restriction_code"], "WORKS-LOCAL-CONTENT")
		self.assertEqual(read["payload"]["amount"], 1_000_000_000)
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"restriction_code": "X", "comparator": "Nonsense"},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_preference_margins_round_trip_and_validation(self):
		out = self._create("KT-TEST-PREFMARGIN", kind="Preference margins")
		saved = register.save_regulatory_reference_version(
			reference_set=out["reference_set"],
			payload={
				"scheme_code": "MSME-MARGIN",
				"procedure": "Open Tender",
				"margin_percent": 15,
				"shareholding_from": 51,
				"shareholding_to": 100,
				"evaluation_basis": "Financial evaluation",
				"source_reference": "s.155",
			},
			effective_from="2094-07-01",
			fixture_namespace=NS,
		)
		read = register.get_regulatory_reference_version(saved["reference"])
		self.assertEqual(read["payload"]["margin_percent"], 15)
		self.assertTrue(read["payload"]["shareholding_from_included"])
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"scheme_code": "X", "margin_percent": 150},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"scheme_code": "X", "shareholding_from": 80, "shareholding_to": 20},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_approval_applicability_round_trip_and_validation(self):
		out = self._create("KT-TEST-APPROVALAPP", kind="Approval applicability")
		saved = register.save_regulatory_reference_version(
			reference_set=out["reference_set"],
			payload={
				"entity_types": ["National Government Ministry"],
				"county_applicability": "NonCounty",
				"approval_route": "Cabinet Secretary",
				"required_capacity_code": "CONFIGURED_STATUTORY_CAPACITY",
				"source_reference": "reg 40(4)",
			},
			effective_from="2094-07-01",
			fixture_namespace=NS,
		)
		read = register.get_regulatory_reference_version(saved["reference"])
		self.assertEqual(read["payload"]["approval_route"], "Cabinet Secretary")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"approval_route": "Made Up Route"},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_publication_obligations_round_trip_and_validation(self):
		out = self._create("KT-TEST-PUBOBL", kind="Publication obligations")
		saved = register.save_regulatory_reference_version(
			reference_set=out["reference_set"],
			payload={
				"obligation_id": "LAW-OB-009",
				"accountable_actor_role": "Head of Procurement Function",
				"due_rule": "CalendarDaysAfter",
				"days": 14,
				"source_reference": "s.138",
			},
			effective_from="2094-07-01",
			fixture_namespace=NS,
		)
		read = register.get_regulatory_reference_version(saved["reference"])
		self.assertEqual(read["payload"]["days"], 14)
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"obligation_id": "X", "due_rule": "CalendarDaysAfter"},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")
		with self.assertRaises(ConfigurationError) as caught:
			register.save_regulatory_reference_version(
				reference_set=out["reference_set"], payload={"obligation_id": "X", "days": -1},
				effective_from="2094-08-01", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")


class TestVerification(RegulatoryReferenceTestCase):
	def test_verified_requires_complete_evidence(self):
		out = self._create("KT-TEST-VERIFY")
		version = self._save_reservation_version(out["reference_set"])
		with self.assertRaises(ConfigurationError) as caught:
			register.record_reference_verification(
				target_doctype=register.DOCTYPE, target_name=version["reference"], outcome="Verified", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_VERIFICATION_EVIDENCE_REQUIRED")
		self.assertEqual(frappe.db.get_value(register.DOCTYPE, version["reference"], "verification_status"), register.VERIFICATION_PENDING)

	def test_verified_with_complete_evidence_updates_the_projection_and_history(self):
		out = self._create("KT-TEST-VERIFY-OK")
		version = self._save_reservation_version(out["reference_set"])
		result = register.record_reference_verification(
			target_doctype=register.DOCTYPE,
			target_name=version["reference"],
			outcome="Verified",
			instrument_edition="Act, 2024 edition",
			effective_dates_and_amendments="No amendments.",
			applicability_date_basis_explanation="Fiscal year start.",
			interpretation_evidence="Section 157(4).",
			fixture_namespace=NS,
		)
		self.assertEqual(result["verification_status"], register.VERIFICATION_VERIFIED)
		self.assertEqual(frappe.db.get_value(register.DOCTYPE, version["reference"], "verification_status"), register.VERIFICATION_VERIFIED)
		history = register.list_verification_history(register.DOCTYPE, version["reference"])
		self.assertEqual(len(history), 1)
		self.assertEqual(history[0]["outcome"], "Verified")

	def test_rejected_requires_the_unresolved_point_and_stays_at_pending(self):
		out = self._create("KT-TEST-REJECT")
		version = self._save_reservation_version(out["reference_set"])
		with self.assertRaises(ConfigurationError) as caught:
			register.record_reference_verification(
				target_doctype=register.DOCTYPE, target_name=version["reference"], outcome="Rejected", fixture_namespace=NS,
			)
		self.assertEqual(self.code(caught), "CFG_VERIFICATION_EVIDENCE_REQUIRED")
		result = register.record_reference_verification(
			target_doctype=register.DOCTYPE,
			target_name=version["reference"],
			outcome="Rejected",
			unresolved_points="The cited source does not establish the stated applicability.",
			fixture_namespace=NS,
		)
		self.assertEqual(result["verification_status"], register.VERIFICATION_PENDING)

	def test_a_verification_event_is_never_edited_in_place(self):
		out = self._create("KT-TEST-EVENT-IMMUTABLE")
		version = self._save_reservation_version(out["reference_set"])
		result = register.record_reference_verification(
			target_doctype=register.DOCTYPE, target_name=version["reference"], outcome="Pending",
			unresolved_points="Still checking.", fixture_namespace=NS,
		)
		doc = frappe.get_doc(register.EVENT_DOCTYPE, result["event"])
		doc.unresolved_points = "Changed after the fact"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)


class TestSelection(RegulatoryReferenceTestCase):
	def test_missing_basis_and_missing_and_ambiguous_and_unverified_and_resolved(self):
		out = self._create("KT-TEST-SELECT")
		none_yet = register.resolve_reference(reference_kind="Reservation rules", applicability_date="")
		self.assertEqual(none_yet["status"], "MissingBasis")

		gap = register.resolve_reference(reference_kind="Reservation rules", applicability_date="2050-01-01")
		self.assertEqual(gap["status"], "Missing")

		version = self._save_reservation_version(out["reference_set"], effective_from="2094-07-01", effective_until="2095-06-30")
		unverified = register.resolve_reference(reference_kind="Reservation rules", applicability_date="2094-08-01")
		self.assertEqual(unverified["status"], "Unverified")
		self.assertEqual(unverified["reference"], version["reference"])

		register.record_reference_verification(
			target_doctype=register.DOCTYPE, target_name=version["reference"], outcome="Verified",
			instrument_edition="e", effective_dates_and_amendments="e", applicability_date_basis_explanation="e",
			interpretation_evidence="e", fixture_namespace=NS,
		)
		resolved = register.resolve_reference(reference_kind="Reservation rules", applicability_date="2094-08-01")
		self.assertEqual(resolved["status"], "Resolved")
		self.assertEqual(resolved["payload"]["target_percent"], 30)

		# A second, non-overlapping set of the same kind does not create
		# ambiguity outside its own window; an overlapping one does.
		other = self._create("KT-TEST-SELECT-2")
		self._save_reservation_version(other["reference_set"], target_percent=40, effective_from="2094-07-01", effective_until="2095-06-30")
		ambiguous = register.resolve_reference(reference_kind="Reservation rules", applicability_date="2094-08-01")
		self.assertEqual(ambiguous["status"], "Ambiguous")
		self.assertEqual(len(ambiguous["candidates"]), 2)

	def test_rejects_an_unsupported_kind(self):
		with self.assertRaises(ConfigurationError) as caught:
			register.resolve_reference(reference_kind="Not a kind", applicability_date="2094-08-01")
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")


class TestPlanningCompatibilityRead(RegulatoryReferenceTestCase):
	def test_missing_year_reports_unavailable_without_raising(self):
		"""The consumer decides what fails closed; the read never raises."""
		out = register.get_regulatory_reference(configuration._fy_name(Y + 1))
		self.assertFalse(out["available"])
		self.assertEqual(out["threshold_matrix"], [])
		self.assertFalse(out["reservation"]["published"])
		self.assertFalse(out["market_price_index"]["published"])

	def test_reservation_figures_and_threshold_matrix_from_method_profiles(self):
		"""FU-08 — threshold_matrix is derived from Procurement Method
		Profile, never a second independently-writable copy."""
		out = self._create("KT-TEST-COMPAT")
		self._save_reservation_version(out["reference_set"], target_percent=30, effective_from=str(frappe.db.get_value("Fiscal Year", self.fy, "year_start_date")), effective_until=str(frappe.db.get_value("Fiscal Year", self.fy, "year_end_date")))
		from kentender_core.services import procurement_settings as settings

		settings.register_method_profile_version(
			procurement_method="Open Tender",
			effective_from=frappe.db.get_value("Fiscal Year", self.fy, "year_start_date"),
			conditions=[
				{"condition_id": "G-VALUE", "kind": "Known fact", "description": "Test cap.", "procurement_category": "Goods", "maximum_amount": 42_000, "cumulative_basis": "Funds allocated"},
			],
			fixture_namespace=NS,
		)
		out2 = register.get_regulatory_reference(self.fy)
		self.assertTrue(out2["available"])
		self.assertEqual(out2["reservation"]["target_percent"], 30)
		by_method = {r["procurement_method"]: r["max_amount"] for r in out2["threshold_matrix"]}
		self.assertEqual(by_method.get("Open Tender"), 42_000)

	def test_canonical_seed_registers_the_reservation_figures_for_the_planning_year(self):
		"""PLN-CHG-001 v1.12 §14.1 — the seed carries the exact statutory
		reservation figures; threshold_matrix reflects the seeded method
		profiles (FU-08), not a second copy."""
		fy = configuration._fy_name(site_setup.DPP_INTAKE["start_year"])
		if not frappe.db.exists("Fiscal Year", fy):
			configuration.add_fiscal_year(start_year=site_setup.DPP_INTAKE["start_year"])
		site_setup._seed_regulatory_reference()
		site_setup._seed_method_profiles()
		out = register.get_regulatory_reference(fy)
		self.assertTrue(out["available"])
		self.assertEqual(out["reservation"]["target_percent"], 30)
		self.assertEqual(out["reservation"]["county_target_percent"], 20)
		self.assertEqual(out["reservation"]["measure_stage"], "PlanningAllocation")
		self.assertEqual(out["reservation"]["denominator_basis"], "EligibleCurrentAPPValue")
		self.assertEqual({c["category"] for c in out["reservation"]["categories"]} >= {"None", "Youth", "Women", "Persons with disabilities"}, True)
		# `market_price_index` is a different rule kind this test does not
		# seed itself (CFG-CHG-002 Phase 2c seeds it separately, via
		# `_seed_market_price_index`); whether it is published on the real
		# canonical FY is not this test's concern.
		by_key = {(r["procurement_category"], r["procurement_method"]): r for r in out["threshold_matrix"]}
		self.assertEqual(by_key[("Services", "Restricted Tender")]["max_amount"], 20_000_000)
		self.assertEqual(by_key[("Works", "Request for Quotations")]["max_amount"], 5_000_000)
		self.assertTrue(frappe.db.exists("Requirement Type", "Works"))

	def test_canonical_seed_covers_all_seven_rule_kinds_usably(self):
		"""CFG-CHG-002 Phase 2c (tracker CFG11-202/304, FU-13) — the seed used
		to stop at three of the seven Regulatory Reference kinds (Reservation
		rules, Publication obligations, plus Method eligibility on its own
		doctype); Exclusive preference, Preference margins, Market price
		index and Approval applicability had validators and UI but no seeded
		row. Every one of the four new seeders must produce a real, findable,
		idempotent row — not just insert without raising."""
		window = {
			"effective_from": str(frappe.db.get_value("Fiscal Year", self.fy, "year_start_date")),
			"effective_until": str(frappe.db.get_value("Fiscal Year", self.fy, "year_end_date")),
		}
		mid_year = str(frappe.db.get_value("Fiscal Year", self.fy, "year_start_date"))

		first = site_setup._seed_exclusive_preference(effective=window, fixture_namespace=NS)
		self.assertEqual(first["created"], 2)
		second = site_setup._seed_exclusive_preference(effective=window, fixture_namespace=NS)
		self.assertEqual(second["created"], 0, "a rerun over the same window must not register a second version")
		works = register.resolve_reference(reference_kind="Exclusive preference", applicability_date=mid_year, category="Works")
		self.assertEqual(works["status"], "Unverified", works)
		self.assertEqual(works["payload"]["amount"], site_setup.REGULATORY_REFERENCE["exclusive_preference_works_amount"])
		goods = register.resolve_reference(reference_kind="Exclusive preference", applicability_date=mid_year, category="Goods")
		self.assertEqual(goods["status"], "Unverified", goods)
		self.assertEqual(goods["payload"]["amount"], site_setup.REGULATORY_REFERENCE["exclusive_preference_goods_services_amount"])
		self.assertNotEqual(works["reference"], goods["reference"], "Works and Goods must resolve to distinct rule versions")

		self.assertEqual(site_setup._seed_preference_margins(effective=window, fixture_namespace=NS)["created"], 1)
		self.assertEqual(site_setup._seed_preference_margins(effective=window, fixture_namespace=NS)["created"], 0)
		margin = register.resolve_reference(reference_kind="Preference margins", applicability_date=mid_year)
		self.assertEqual(margin["status"], "Unverified", margin)
		self.assertEqual(margin["payload"]["margin_percent"], 15)

		self.assertEqual(site_setup._seed_market_price_index(effective=window, fixture_namespace=NS)["created"], 1)
		self.assertEqual(site_setup._seed_market_price_index(effective=window, fixture_namespace=NS)["created"], 0)
		out = register.get_regulatory_reference(self.fy)
		self.assertTrue(out["market_price_index"]["published"])
		self.assertTrue(any(r["item"].startswith("Laptop") for r in out["market_price_index"]["rows"]))

		self.assertEqual(site_setup._seed_approval_applicability(effective=window, fixture_namespace=NS)["created"], 1)
		self.assertEqual(site_setup._seed_approval_applicability(effective=window, fixture_namespace=NS)["created"], 0)
		approval = register.resolve_reference(
			reference_kind="Approval applicability", applicability_date=mid_year,
			entity_type=site_setup.SITE["pe_type"], county=False,
		)
		self.assertEqual(approval["status"], "Unverified", approval)
		self.assertEqual(approval["payload"]["approval_route"], site_setup.SITE["statutory_approval_route"])

		# Every seeded row carries a real reason and (where the doctype has
		# the field) a real interpretation — never the blank "Not recorded" /
		# "Not yet established" state the seed used to leave behind.
		for name in (works["reference"], goods["reference"], margin["reference"], approval["reference"]):
			doc = frappe.get_doc("Regulatory Reference", name)
			self.assertTrue(doc.change_reason.strip(), f"{name} has no change_reason")
			self.assertTrue(doc.interpretation.strip(), f"{name} has no interpretation")
			self.assertNotIn("verification pending", doc.source_instrument.lower())

	def test_tender_renderable_reservation_categories_is_a_governed_subset(self):
		"""REQ-CHG-001 v1.6 §5A / STD-TPL-001 v0.4 §6.1 — the one list a
		Requisition's compatibility test and Tender Preparation's own
		rendering both check against; every entry is a real governed
		category, in the governed register's own order."""
		governed_order = [name for name, _rank, _regional, _ref in site_setup.RESERVATION_CATEGORIES]
		renderable = list(register.TENDER_RENDERABLE_RESERVATION_CATEGORIES)
		self.assertEqual(
			renderable,
			[name for name in governed_order if name in renderable],
			"renderable categories must appear in the governed register's own order",
		)
		self.assertEqual(
			renderable,
			["None", "Youth", "Women", "Persons with disabilities", "Other disadvantaged group"],
		)


class TestReservationMeasure(RegulatoryReferenceTestCase):
	"""CFG-CHG-002 v0.13/v0.14 §4.7 + LAW-REG-001 v1.2 §5.1 (CFG13-AC-001,
	002, 004; CFG10-AC-047) — a reservation obligation states its measure
	stage, and the stage fixes what it is measured against: planned
	allocation against the eligible value of the current Annual Plan, actual
	achievement against applicable actual procurement value. The approved
	Budget (and its unused headroom) is never a denominator."""

	def _save(self, key, payload, effective_from="2094-07-01"):
		ref = self._create(key)
		return register.save_regulatory_reference_version(
			reference_set=ref["reference_set"],
			payload={"obligation_code": "AGPO-30", "target_percent": 30, **payload},
			effective_from=effective_from,
			applicability_basis="FiscalYearStart",
			fixture_namespace=NS,
		)

	def _payload(self, out):
		import json

		return json.loads(frappe.db.get_value("Regulatory Reference", out["reference"], "payload_json"))

	def test_planned_allocation_is_measured_against_the_eligible_current_annual_plan(self):
		out = self._save("KT-TEST-RES-PLAN", {"measure_stage": "PlanningAllocation"})
		payload = self._payload(out)
		self.assertEqual(payload["measure_stage"], "PlanningAllocation")
		self.assertEqual(payload["denominator_basis"], "EligibleCurrentAPPValue")

	def test_actual_achievement_is_measured_against_applicable_actual_procurement_value(self):
		out = self._save("KT-TEST-RES-ACTUAL", {"measure_stage": "ImplementationAchievement"})
		payload = self._payload(out)
		self.assertEqual(payload["denominator_basis"], "ApplicableActualProcurementValue")

	def test_a_measure_stage_is_required(self):
		with self.assertRaises(ConfigurationError) as caught:
			self._save("KT-TEST-RES-NOSTAGE", {})
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_the_retired_budget_based_denominators_are_refused(self):
		for index, retired in enumerate(("AnnualProcurementBudget", "AnnualProcurementValue")):
			with self.assertRaises(ConfigurationError) as caught:
				self._save(f"KT-TEST-RES-OLD-{index}", {"measure_stage": "PlanningAllocation", "denominator_basis": retired})
			self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_a_stage_cannot_be_paired_with_the_other_stage_denominator(self):
		with self.assertRaises(ConfigurationError) as caught:
			self._save(
				"KT-TEST-RES-MISMATCH",
				{"measure_stage": "PlanningAllocation", "denominator_basis": "ApplicableActualProcurementValue"},
			)
		self.assertEqual(self.code(caught), "CFG_SCHEMA_UNSUPPORTED")

	def test_planning_read_names_the_exact_rule_version_and_its_measure(self):
		"""CFG13-AC-002 — Planning receives the exact version and the basis it
		must calculate on, and an actual-achievement rule in force for the same
		year does not make the planning rule ambiguous."""
		# Other tests in this module leave open-ended planning rules in force
		# from 2094; clear this module's own rules so only these two compete.
		# Years from 2095 on are removed by the shared test purge.
		register.purge_fixture_references(NS)
		fy = configuration._fy_name(2096)
		if not frappe.db.exists("Fiscal Year", fy):
			configuration.add_fiscal_year(start_year=2096)
		plan = self._save("KT-TEST-RES-READ-PLAN", {"measure_stage": "PlanningAllocation"}, effective_from="2096-07-01")
		self._save("KT-TEST-RES-READ-ACTUAL", {"measure_stage": "ImplementationAchievement"}, effective_from="2096-07-01")
		read = register.get_regulatory_reference(fy)
		self.assertEqual(read["reference"], plan["reference"])
		self.assertEqual(read["reservation"]["measure_stage"], "PlanningAllocation")
		self.assertEqual(read["reservation"]["denominator_basis"], "EligibleCurrentAPPValue")

