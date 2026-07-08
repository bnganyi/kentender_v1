# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 8 — STD Template Governance smoke gate (§C) — automated server path.

Maps to [`8. std_template_governance_lifecycle_smoke_test_specification.md`](../../../../docs/prompts/std-production-readiness/workstream-1/8.%20std_template_governance_lifecycle_smoke_test_specification.md)
test cases **STD-GOV-ST-001** … **ST-017**, **ST-020** at the API/service layer (no Desk screenshots).

Desk UI matrix (**ST-018**, **ST-019**) is covered by Playwright:
``apps/kentender_v1/tests/ui/smoke/procurement/std-template-governance-smoke-doc8.spec.ts``.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.kentender_procurement.doctype.std_template.std_template import (
	replace_std_template_package,
)
from kentender_procurement.tender_management.seeds.std_template_governance_roles import (
	STD_TEMPLATE_GOVERNANCE_ROLES,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	SEED_MARKER,
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_lifecycle import (
	activate_std_template,
	approve_std_template,
	archive_std_template,
	reinstate_std_template,
	retire_std_template,
	return_std_template_for_correction,
	submit_std_template_for_approval,
	supersede_std_template,
	suspend_std_template,
)
from kentender_procurement.tender_management.services.std_template_governance_snapshot import (
	generate_std_template_governance_snapshot,
)
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	check_std_template_tender_creation_eligibility,
	record_std_template_usage,
)
from kentender_procurement.tender_management.services.std_template_governance_validation import (
	run_std_template_validation,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_lifecycle_gov007 import (
	_set_validated_guards,
)


DOC8_USERS: tuple[tuple[str, tuple[str, ...]], ...] = (
	("std.importer@test.local", ("STD Template Importer",)),
	("std.admin@test.local", ("STD Template Administrator",)),
	("std.reviewer@test.local", ("STD Template Reviewer",)),
	("std.approver@test.local", ("STD Template Approver",)),
	("std.activator@test.local", ("STD Template Activator",)),
	("std.inspector@test.local", ("STD Technical Inspector",)),
	("std.auditor@test.local", ("STD Template Auditor",)),
	("proc.officer@test.local", ("Procurement Officer",)),
	("system.manager@test.local", ("System Manager",)),
)


def _ensure_doc8_user(email: str, *roles: str) -> None:
	if frappe.db.exists("User", email):
		u = frappe.get_doc("User", email)
	else:
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "Doc8"
		u.enabled = 1
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
	u.save(ignore_permissions=True)
	for row in list(u.roles or []):
		u.remove(row)
	u.add_roles(*roles)
	frappe.db.commit()


def _delete_doc8_users() -> None:
	for em, _ in DOC8_USERS:
		if frappe.db.exists("User", em):
			frappe.delete_doc("User", em, force=True, ignore_permissions=True)
			frappe.db.commit()


def _ph(doc_name: str) -> str:
	ph = frappe.db.get_value("STD Template", doc_name, "package_hash")
	assert ph
	return str(ph)


def _tear_down_std_template(name: str) -> None:
	frappe.set_user("Administrator")
	if not frappe.db.exists("STD Template", name):
		return
	frappe.db.delete("STD Template Usage", {"parent": name})
	frappe.db.set_value(
		"STD Template",
		name,
		{
			"tender_usage_count": 0,
			"locked_due_to_usage": 0,
			"mutation_blocked": 0,
		},
	)
	frappe.db.delete("STD Template Validation Finding", {"parent": name})
	frappe.db.delete("STD Template Lifecycle Event", {"parent": name})
	frappe.delete_doc("STD Template", name, force=True, ignore_permissions=True)
	frappe.db.commit()


class TestStdTemplateGovernanceSmokeDoc8ST001(IntegrationTestCase):
	"""STD-GOV-ST-001 — roles + doc 8 users."""

	@classmethod
	def setUpClass(cls) -> None:
		frappe.set_user("Administrator")
		for em, roles in DOC8_USERS:
			_ensure_doc8_user(em, *roles)

	@classmethod
	def tearDownClass(cls) -> None:
		_delete_doc8_users()

	def test_std_gov_st_001_governance_roles_exist(self) -> None:
		for role in STD_TEMPLATE_GOVERNANCE_ROLES:
			self.assertTrue(frappe.db.exists("Role", role), msg=f"Missing role {role!r}")

	def test_std_gov_st_001_doc8_users_have_expected_roles(self) -> None:
		for em, roles in DOC8_USERS:
			got = set(frappe.get_roles(em))
			for r in roles:
				self.assertIn(r, got, msg=f"{em} missing {r}")

	def test_std_gov_st_001_procurement_officer_boundary(self) -> None:
		# ``Procurement Officer`` is a seeded governance-adjacent role (STD-GOV-001); doc 8
		# boundary means **no STD Template governance power roles** for tendering officers.
		forbidden = (
			"STD Template Importer",
			"STD Template Administrator",
			"STD Template Reviewer",
			"STD Template Approver",
			"STD Template Activator",
			"STD Template Auditor",
			"STD Technical Inspector",
		)
		roles = set(frappe.get_roles("proc.officer@test.local"))
		self.assertFalse(roles.intersection(forbidden))

	def test_std_gov_st_001_inspector_not_approver_or_activator(self) -> None:
		roles = set(frappe.get_roles("std.inspector@test.local"))
		self.assertNotIn("STD Template Approver", roles)
		self.assertNotIn("STD Template Activator", roles)


class TestStdTemplateGovernanceSmokeDoc8PocST002ST003(IntegrationTestCase):
	"""STD-GOV-ST-002 / ST-003 — WORKS POC import + validation (shared template)."""

	def test_std_gov_st_002_003_poc_import_and_validate(self) -> None:
		frappe.set_user("Administrator")
		upsert_std_template(commit=True)
		out = run_std_template_validation(TEMPLATE_CODE)
		self.assertTrue(out.get("ok"), msg=out)
		doc = frappe.get_doc("STD Template", TEMPLATE_CODE)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_VALIDATED)
		self.assertIn(doc.latest_validation_status, (gov.VALIDATION_PASS, gov.VALIDATION_PASS_WARNINGS))
		self.assertEqual(int(doc.validation_is_current or 0), 1)
		self.assertEqual((doc.latest_validation_package_hash or "").strip(), (doc.package_hash or "").strip())
		codes = [e.event_code for e in (doc.lifecycle_events or [])]
		self.assertIn(gov.EVT_VALIDATION_STARTED, codes)
		self.assertIn(gov.EVT_VALIDATION_COMPLETED, codes)


class TestStdTemplateGovernanceSmokeDoc8ST004(IntegrationTestCase):
	"""STD-GOV-ST-004 — invalid package cannot submit."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"DOC8INV-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._code)
		frappe.db.set_value("STD Template", self._code, "package_json", "{}")
		frappe.db.commit()

	def tearDown(self) -> None:
		_tear_down_std_template(self._code)

	def test_std_gov_st_004_invalid_validation_blocks_submit(self) -> None:
		out = run_std_template_validation(self._code)
		self.assertFalse(out.get("ok"))
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_VALIDATION_FAILED)
		self.assertGreater(int(doc.critical_finding_count or 0), 0)
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			submit_std_template_for_approval(self._code, comment="should fail")


class TestStdTemplateGovernanceSmokeDoc8FullChain(IntegrationTestCase):
	"""STD-GOV-ST-005 … ST-015 — isolated two-template server path."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._a = f"DOC8A-{frappe.generate_hash(length=8)}"
		self._b = f"DOC8B-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._a)
		_new_gov005_std_template(self._b)

	def tearDown(self) -> None:
		_tear_down_std_template(self._a)
		_tear_down_std_template(self._b)

	def test_std_gov_st_005_through_st_015_lifecycle_usage_supersede_retire(self) -> None:
		ph_a = _ph(self._a)
		_set_validated_guards(self._a)
		submit_std_template_for_approval(self._a, comment="doc8 smoke")
		approve_std_template(self._a, "approved", override_reason="break-glass")
		frappe.db.set_value(
			"STD Template",
			self._a,
			{"approval_package_hash": ph_a, "latest_validation_package_hash": ph_a},
		)
		frappe.db.commit()
		activate_std_template(self._a, reason="doc8 activate A")

		# ST-008
		el = check_std_template_tender_creation_eligibility(self._a, None)
		self.assertTrue(el["eligible"], msg=el)

		# ST-009
		self.assertTrue(
			record_std_template_usage(self._a, "Tender", tender="TND-DOC8-1", payload={"smoke": True})["ok"]
		)
		doc_a = frappe.get_doc("STD Template", self._a)
		self.assertGreaterEqual(int(doc_a.tender_usage_count or 0), 1)
		self.assertIn(gov.EVT_USED_FOR_TENDER, [e.event_code for e in (doc_a.lifecycle_events or [])])

		# ST-010 mutation + delete
		doc_a = frappe.get_doc("STD Template", self._a)
		doc_a.package_json = '{"mutate": true}'
		with self.assertRaises(frappe.ValidationError):
			doc_a.save()
		self.assertIn(
			gov.EVT_MUTATION_BLOCKED,
			[e.event_code for e in (frappe.get_doc("STD Template", self._a).lifecycle_events or [])],
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("STD Template", self._a, force=True, ignore_permissions=True)
		self.assertIn(
			gov.EVT_DELETE_BLOCKED,
			[e.event_code for e in (frappe.get_doc("STD Template", self._a).lifecycle_events or [])],
		)

		# ST-011 snapshot
		self.assertTrue(generate_std_template_governance_snapshot(self._a)["ok"])
		doc_a = frappe.get_doc("STD Template", self._a)
		self.assertTrue((doc_a.latest_governance_snapshot_hash or "").strip())
		self.assertIn(gov.EVT_SNAPSHOT_GENERATED, [e.event_code for e in (doc_a.lifecycle_events or [])])

		# ST-013 suspend / reinstate
		frappe.set_user("Administrator")
		self.assertTrue(suspend_std_template(self._a, reason="doc8 pause")["ok"])
		self.assertFalse(check_std_template_tender_creation_eligibility(self._a, None)["eligible"])
		self.assertIn(gov.EVT_SUSPENDED, [e.event_code for e in (frappe.get_doc("STD Template", self._a).lifecycle_events or [])])
		self.assertTrue(reinstate_std_template(self._a, reason="doc8 resume")["ok"])
		self.assertTrue(check_std_template_tender_creation_eligibility(self._a, None)["eligible"])
		self.assertIn(gov.EVT_REINSTATED, [e.event_code for e in (frappe.get_doc("STD Template", self._a).lifecycle_events or [])])

		# ST-012 — audit trail contains key governance codes (after ST-013 so suspend/reinstate rows exist)
		doc_a = frappe.get_doc("STD Template", self._a)
		codes = {e.event_code for e in (doc_a.lifecycle_events or [])}
		for req in (
			gov.EVT_SUBMITTED,
			gov.EVT_APPROVED,
			gov.EVT_ACTIVATED,
			gov.EVT_USED_FOR_TENDER,
			gov.EVT_SNAPSHOT_GENERATED,
			gov.EVT_MUTATION_BLOCKED,
			gov.EVT_DELETE_BLOCKED,
			gov.EVT_SUSPENDED,
			gov.EVT_REINSTATED,
		):
			self.assertIn(req, codes, msg=f"missing audit {req}")

		# Prepare B for supersession (ST-014)
		ph_b = _ph(self._b)
		_set_validated_guards(self._b)
		submit_std_template_for_approval(self._b, comment="doc8 B")
		approve_std_template(self._b, "ok", override_reason="x")
		frappe.db.set_value(
			"STD Template",
			self._b,
			{"approval_package_hash": ph_b, "latest_validation_package_hash": ph_b},
		)
		frappe.db.commit()
		activate_std_template(self._b, reason="doc8 activate B")

		self.assertTrue(supersede_std_template(self._a, self._b, reason="doc8 supersede")["ok"])
		doc_a = frappe.get_doc("STD Template", self._a)
		self.assertEqual(doc_a.lifecycle_status, gov.STATUS_SUPERSEDED)
		self.assertFalse(check_std_template_tender_creation_eligibility(self._a, None)["eligible"])
		self.assertIn(gov.EVT_SUPERSEDED, [e.event_code for e in (doc_a.lifecycle_events or [])])

		# ST-015 retire replacement B
		self.assertTrue(retire_std_template(self._b, reason="doc8 retire B")["ok"])
		doc_b = frappe.get_doc("STD Template", self._b)
		self.assertEqual(doc_b.lifecycle_status, gov.STATUS_RETIRED)
		self.assertFalse(check_std_template_tender_creation_eligibility(self._b, None)["eligible"])
		self.assertIn(gov.EVT_RETIRED, [e.event_code for e in (doc_b.lifecycle_events or [])])

		self.assertTrue(archive_std_template(self._b, reason="doc8 archive B")["ok"])
		self.assertEqual(frappe.db.get_value("STD Template", self._b, "lifecycle_status"), gov.STATUS_ARCHIVED)


class TestStdTemplateGovernanceSmokeDoc8ST016(IntegrationTestCase):
	"""STD-GOV-ST-016 — permission negatives (server)."""

	@classmethod
	def setUpClass(cls) -> None:
		frappe.set_user("Administrator")
		for em, roles in DOC8_USERS:
			_ensure_doc8_user(em, *roles)

	@classmethod
	def tearDownClass(cls) -> None:
		_delete_doc8_users()

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"DOC8P-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		_tear_down_std_template(self._code)

	def test_std_gov_st_016_permission_negatives(self) -> None:
		ph = _ph(self._code)
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="admin submit for importer test")
		frappe.set_user("std.importer@test.local")
		with self.assertRaises(frappe.PermissionError):
			approve_std_template(self._code, "importer cannot approve")

		frappe.set_user("std.approver@test.local")
		approve_std_template(self._code, "ok")
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"approval_package_hash": ph, "latest_validation_package_hash": ph},
		)
		frappe.db.commit()
		frappe.set_user("std.admin@test.local")
		with self.assertRaises(frappe.PermissionError):
			activate_std_template(self._code, reason="no activator role")

		frappe.set_user("std.inspector@test.local")
		with self.assertRaises(frappe.PermissionError):
			approve_std_template(self._code, "nope")

		frappe.set_user("proc.officer@test.local")
		self.assertFalse(frappe.has_permission("STD Template", "read", doc=frappe.get_doc("STD Template", self._code)))

		frappe.set_user("std.auditor@test.local")
		with self.assertRaises(frappe.PermissionError):
			approve_std_template(self._code, "audit")

		sm_code = f"DOC8SM-{frappe.generate_hash(length=6)}"
		_new_gov005_std_template(sm_code)
		try:
			_set_validated_guards(sm_code)
			frappe.set_user("system.manager@test.local")
			submit_std_template_for_approval(sm_code, comment="sm self submit")
			with self.assertRaises(frappe.ValidationError):
				approve_std_template(sm_code, "x", override_reason=None)
		finally:
			_tear_down_std_template(sm_code)

		frappe.set_user("Administrator")
		activate_std_template(self._code, reason="doc8 activate for sm mutate test")
		record_std_template_usage(self._code, "Tender", tender="TND-DOC8-2", payload={})
		frappe.set_user("system.manager@test.local")
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"x": 1}'
		with self.assertRaises(frappe.ValidationError):
			d.save()


class TestStdTemplateGovernanceSmokeDoc8ST017(IntegrationTestCase):
	"""STD-GOV-ST-017 — stale validation / replace resets."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"DOC8ST-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		_tear_down_std_template(self._code)

	def test_std_gov_st_017_replace_resets_validation_blocks_submit_until_revalidate(self) -> None:
		_set_validated_guards(self._code)
		submit_std_template_for_approval(self._code, comment="c")
		with self.assertRaises(frappe.ValidationError):
			replace_std_template_package(
				self._code,
				package_json="{}",
				manifest_json="{}",
				reason="doc8 replace under submitted",
			)
		frappe.set_user("Administrator")
		return_std_template_for_correction(self._code, reason="doc8 return for replace")
		replace_std_template_package(
			self._code,
			package_json="{}",
			manifest_json="{}",
			reason="doc8 replace after return",
		)
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(doc.lifecycle_status, gov.STATUS_IMPORTED)
		with self.assertRaises(frappe.ValidationError):
			submit_std_template_for_approval(self._code, comment="stale")


class TestStdTemplateGovernanceSmokeDoc8ST020(IntegrationTestCase):
	"""STD-GOV-ST-020 — WORKS POC governance seed."""

	def test_std_gov_st_020_poc_seed_governed(self) -> None:
		frappe.set_user("Administrator")
		upsert_std_template(commit=True)
		out = seed_std_template_governance_for_existing_works_poc(force_mode="approved")
		self.assertTrue(out.get("ok"), msg=out)
		doc = frappe.get_doc("STD Template", TEMPLATE_CODE)
		self.assertTrue((doc.package_hash or "").strip())
		self.assertIn(doc.lifecycle_status, (gov.STATUS_APPROVED, gov.STATUS_ACTIVE))
		payloads = " ".join((e.payload_json or "") for e in (doc.lifecycle_events or []))
		self.assertIn(SEED_MARKER, payloads)


class TestStdTemplateGovernanceSmokeDoc8C3Principle(IntegrationTestCase):
	"""§C3 — server-side enforcement (not cosmetic status)."""

	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"DOC8C3-{frappe.generate_hash(length=8)}"
		_new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		_tear_down_std_template(self._code)

	def test_std_gov_c3_clamped_allowed_for_tender_creation_when_not_active(self) -> None:
		d = frappe.get_doc("STD Template", self._code)
		d.allowed_for_tender_creation = 1
		d.save(ignore_permissions=True)
		d.reload()
		self.assertEqual(int(d.allowed_for_tender_creation or 0), 0)

	def test_std_gov_c3_submitted_blocks_package_edit(self) -> None:
		frappe.db.set_value("STD Template", self._code, {"lifecycle_status": gov.STATUS_SUBMITTED})
		frappe.db.commit()
		d = frappe.get_doc("STD Template", self._code)
		d.package_json = '{"hack": true}'
		with self.assertRaises(frappe.ValidationError):
			d.save()
