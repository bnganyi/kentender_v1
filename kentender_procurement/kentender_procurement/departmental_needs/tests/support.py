"""Shared scaffolding for the Departmental Needs test suites.

PLN-CHG-001 v1.18 §13.1 (adopted in the shared register on 12 September
2026, plan D19) dates Dr Peter Kimani's Digital Health authority from
1 December 2026 and restores Julia Njeri's acting window to 1 October –
30 November 2026. The seeds now run every command under the frozen clock at
its fixture instant, so those windows are real. These suites, however, run
at the site's *real* clock and drive Digital Health reviews as Peter
(`REVIEWER`), which no instant before 1 December permits.

`ensure_transitional_reviewer_grant` therefore grants Peter a **test-only**
Head of User Department assignment over Digital Health, in its own fixture
namespace, ending 30 November 2026 so it never overlaps his real dated row,
and releases it (revoke, then delete the fixture row) when the suite ends.
It is test scaffolding for the NDS mechanics under test — never a seed, a
persona or a Playwright fixture — and NDS FOLLOW_UPS.md §FU-07 records the
owner's option to retire it by moving these suites onto their own actors.
"""

from __future__ import annotations

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_procurement.departmental_needs.constants import ROLE_HEAD_OF_USER_DEPARTMENT
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	AUTHOR,
	DEPARTMENTAL_AUTHOR,
	REVIEWER,
	_granted_units,
)

TRANSITIONAL_NS = "KENTENDER_NDS_TEST_TRANSITIONAL_GRANT"
# The namespaces the NDS suites grant under (their `_restore_scope` re-grants
# a revoked *seeded* row under a test namespace, and the lifecycle suite
# grants extra roles). Nothing purged them before 12 Sep 2026, so Grace was
# left holding a Digital Health review grant between runs — a leak that made
# three suites fail for reasons unrelated to what they test.
NDS_TEST_GRANT_NAMESPACES = (
	TRANSITIONAL_NS,
	"KENTENDER_NDS_PERMISSIONS_TEST",
	"KENTENDER_NDS_LIFECYCLE_TEST",
)
TRANSITIONAL_UNTIL = "2026-11-30 23:59:59"
TRANSITIONAL_REFERENCE = (
	"Test-only: NDS suites run at the real clock; PLN-CHG-001 v1.18 §13.1 dates the real Digital Health authority from 1 Dec 2026."
)


def ensure_transitional_reviewer_grant(test_class=None) -> str:
	"""Grant (idempotently) and register the release as a class cleanup."""
	previous = frappe.session.user
	frappe.set_user("Administrator")
	try:
		units = _granted_units(AUTHOR, DEPARTMENTAL_AUTHOR)
		unit = units["Digital Health"]
		outcome = administration.grant(
			user=REVIEWER,
			business_role=ROLE_HEAD_OF_USER_DEPARTMENT,
			organisation_unit=unit,
			authority_reference=TRANSITIONAL_REFERENCE,
			effective_to=TRANSITIONAL_UNTIL,
			fixture_namespace=TRANSITIONAL_NS,
			actor="Administrator",
		)
		frappe.db.commit()
	finally:
		frappe.set_user(previous)
	if test_class is not None:
		test_class.addClassCleanup(restore_shared_register)
	return outcome["assignment"]


def restore_shared_register() -> dict[str, int]:
	"""Suite-end hygiene (feedback: always remove test data): revoke and delete
	every assignment row in an NDS test namespace, then re-run the canonical
	KT-STD-001 §8.3 assignment seed so any seeded row a test revoked is
	granted again exactly as the register specifies."""
	from kentender_core.seeds import site_setup

	previous = frappe.session.user
	frappe.set_user("Administrator")
	try:
		removed = 0
		for namespace in NDS_TEST_GRANT_NAMESPACES:
			names = frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": namespace}, pluck="name")
			for name in names:
				if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
					administration.revoke(name, reason="Test-only grant released at suite end.", actor="Administrator")
			if names:
				frappe.db.delete("User Responsibility Assignment", {"fixture_namespace": namespace})
				removed += len(names)
		restored = site_setup._seed_assignments()
		frappe.db.commit()
		return {"removed": removed, "register_rows": len(restored)}
	finally:
		frappe.set_user(previous)


def release_transitional_reviewer_grant() -> int:
	"""Revoke (so the Role projection is re-synced) and delete the fixture rows."""
	previous = frappe.session.user
	frappe.set_user("Administrator")
	try:
		names = frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": TRANSITIONAL_NS}, pluck="name")
		for name in names:
			if frappe.db.get_value("User Responsibility Assignment", name, "status") == "Enabled":
				administration.revoke(name, reason="Test-only transitional grant released at suite end.", actor="Administrator")
		if names:
			frappe.db.delete("User Responsibility Assignment", {"fixture_namespace": TRANSITIONAL_NS})
		frappe.db.commit()
		return len(names)
	finally:
		frappe.set_user(previous)
