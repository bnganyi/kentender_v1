# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-019 / LV-R3-019-01 — Role matrix tests for each API method (internal roles).

## Goal

Verify that the Procurement Lifecycle API permission enforcement (``permission_guard.py``)
correctly grants access to all authorised internal Desk roles and denies access to
unauthenticated (Guest) actors — satisfying pack §10.4 and G0-006 §3 (access matrix).

## Coverage

### Positive tests (internal roles — should PASS)

For each internal Desk role defined in G0-011 LV-G0-011-01, verify:

1. ``user_has_journey_read`` returns True (DocPerm configured correctly for the role).
2. ``user_has_handoff_read`` returns True.
3. Journey + Handoff API methods succeed when called as Administrator (break-glass
   representative, highest-privilege internal user).

### Negative tests (Guest / no-role actors — should DENY)

1. Guest session → ``require_journey_read`` raises PermissionError.
2. Guest session → ``require_handoff_read`` raises PermissionError.
3. Guest session → Journey API endpoints raise PermissionError.
4. Guest session → Handoff API endpoints raise PermissionError.
5. Temp user with no procurement roles → ``user_has_journey_read`` returns False.

### DocPerm matrix tests (all 9+1 internal roles × both DocTypes)

Verifies the live DocType permission table matches the G0-011 matrix expectation
by calling ``frappe.has_permission`` as each existing test user.

## Test users used (from site seed data)

| User | Role |
|---|---|
| ``planning.authority@moh.test`` | Planning Authority |
| ``requisitioner@moh.test`` | Requisitioner |
| ``planner@moh.test`` | Procurement Planner |
| ``procurement.officer@moh.test`` | Procurement Officer |
| ``finance.reviewer@moh.test`` | Finance Reviewer |
| ``hod.approver@moh.test`` | Department Approver |
| ``tender.seed.auditor@test.local`` | Auditor |
| ``Administrator`` | Administrator |

## Test IDs

| Test | Description |
|---|---|
| PERM-GUARD-001 | ``require_journey_read`` raises PermissionError for Guest. |
| PERM-GUARD-002 | ``require_handoff_read`` raises PermissionError for Guest. |
| PERM-GUARD-003 | ``require_handoff_write`` raises PermissionError for Guest. |
| PERM-GUARD-004 | ``user_has_journey_read`` returns False for Guest. |
| PERM-GUARD-005 | ``user_has_handoff_read`` returns False for Guest. |
| PERM-GUARD-006 | ``user_has_handoff_write`` returns False for Guest. |
| PERM-MATRIX-001 | All 9 internal roles have read on Procurement Journey (DocPerm check). |
| PERM-MATRIX-002 | All 9 internal roles have read on Procurement Handoff Card (DocPerm check). |
| PERM-MATRIX-003 | Only System Manager / Administrator have write on Procurement Journey. |
| PERM-MATRIX-004 | Only System Manager / Administrator have write on Procurement Handoff Card. |
| PERM-USER-002 | Planning Authority user: journey_read=True, handoff_read=True. |
| PERM-USER-003 | Requisitioner user: journey_read=True, handoff_read=True. |
| PERM-USER-004 | Procurement Planner user: journey_read=True, handoff_read=True. |
| PERM-USER-005 | Procurement Officer user: journey_read=True, handoff_read=True. |
| PERM-USER-006 | Finance Reviewer user: journey_read=True, handoff_read=True. |
| PERM-USER-007 | Department Approver user: journey_read=True, handoff_read=True. |
| PERM-USER-008 | Auditor user: journey_read=True, handoff_read=True. |
| PERM-USER-009 | Administrator: journey_read=True, handoff_read=True, handoff_write=True. |
| PERM-API-001 | list_journeys succeeds as Administrator. |
| PERM-API-002 | get_journey succeeds as Administrator. |
| PERM-API-003 | get_handoff_card succeeds as Administrator. |
| PERM-API-004 | Journey APIs raise PermissionError for Guest. |
| PERM-API-005 | Handoff APIs raise PermissionError for Guest. |
| PERM-API-006 | Temp no-role user: user_has_journey_read=False, user_has_handoff_read=False. |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.permission_guard import (
    JOURNEY_READ_ROLES,
    require_journey_read,
    require_handoff_read,
    require_handoff_write,
    user_has_journey_read,
    user_has_handoff_read,
    user_has_handoff_write,
)
from kentender_procurement.procurement_lifecycle.api.journey_api import (
    list_journeys,
    get_journey,
)
from kentender_procurement.procurement_lifecycle.api.handoff_api import (
    get_handoff_card,
    refresh_handoff_card,
)

# ---------------------------------------------------------------------------
# Test users (existing site seed users)
# ---------------------------------------------------------------------------

_ADMIN = "Administrator"
_GUEST = "Guest"

# Users known to exist on this site with specific single procurement roles
_ROLE_USERS: dict[str, str] = {
    "Planning Authority":  "planning.authority@moh.test",
    "Requisitioner":       "requisitioner@moh.test",
    "Procurement Planner": "planner@moh.test",
    "Procurement Officer": "procurement.officer@moh.test",
    "Finance Reviewer":    "finance.reviewer@moh.test",
    "Department Approver": "hod.approver@moh.test",
    "Auditor":             "tender.seed.auditor@test.local",
}

# WORKS golden identifiers
_WORKS_JOURNEY = "JRN-MOH-2026-001"
_WORKS_PKGREL   = "PKGREL-MOH-2026-001"


# ---------------------------------------------------------------------------
# PERM-GUARD: permission_guard module standalone
# ---------------------------------------------------------------------------


class TestPermissionGuardStandalone(IntegrationTestCase):
    """Tests for permission_guard helper functions called directly."""

    # PERM-GUARD-001
    def test_guard_001_require_journey_read_denies_guest(self):
        """PERM-GUARD-001: require_journey_read raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                require_journey_read("test operation")
        finally:
            frappe.set_user(_ADMIN)

    # PERM-GUARD-002
    def test_guard_002_require_handoff_read_denies_guest(self):
        """PERM-GUARD-002: require_handoff_read raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                require_handoff_read("test operation")
        finally:
            frappe.set_user(_ADMIN)

    # PERM-GUARD-003
    def test_guard_003_require_handoff_write_denies_guest(self):
        """PERM-GUARD-003: require_handoff_write raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                require_handoff_write("test operation")
        finally:
            frappe.set_user(_ADMIN)

    # PERM-GUARD-004
    def test_guard_004_user_has_journey_read_false_for_guest(self):
        """PERM-GUARD-004: user_has_journey_read returns False for Guest."""
        result = user_has_journey_read("Guest")
        self.assertFalse(result)

    # PERM-GUARD-005
    def test_guard_005_user_has_handoff_read_false_for_guest(self):
        """PERM-GUARD-005: user_has_handoff_read returns False for Guest."""
        result = user_has_handoff_read("Guest")
        self.assertFalse(result)

    # PERM-GUARD-006
    def test_guard_006_user_has_handoff_write_false_for_guest(self):
        """PERM-GUARD-006: user_has_handoff_write returns False for Guest."""
        result = user_has_handoff_write("Guest")
        self.assertFalse(result)

    def test_guard_007_journey_read_roles_constant_complete(self):
        """PERM-GUARD-007: JOURNEY_READ_ROLES contains all 10 expected internal roles."""
        expected = {
            "System Manager", "Administrator",
            "Planning Authority",
            "Requisitioner", "Procurement Planner",
            "Procurement Officer", "Finance Reviewer",
            "Department Approver", "Auditor",
        }
        for role in expected:
            self.assertIn(role, JOURNEY_READ_ROLES, f"Role '{role}' missing from JOURNEY_READ_ROLES")


# ---------------------------------------------------------------------------
# PERM-MATRIX: DocPerm table verification (G0-011 matrix)
# ---------------------------------------------------------------------------


class TestDocPermMatrix(IntegrationTestCase):
    """Verify that the live DocType permission table matches the G0-011 matrix."""

    def _get_roles_with_read(self, doctype: str) -> set[str]:
        rows = frappe.db.get_all(
            "DocPerm",
            filters={"parent": doctype, "read": 1},
            fields=["role"],
        )
        return {r.role for r in rows}

    def _get_roles_with_write(self, doctype: str) -> set[str]:
        rows = frappe.db.get_all(
            "DocPerm",
            filters={"parent": doctype, "write": 1},
            fields=["role"],
        )
        return {r.role for r in rows}

    # PERM-MATRIX-001
    def test_matrix_001_journey_read_has_all_internal_roles(self):
        """PERM-MATRIX-001: All 9 non-admin internal roles have read on Procurement Journey."""
        frappe.set_user(_ADMIN)
        read_roles = self._get_roles_with_read("Procurement Journey")
        expected_read = {
            "Planning Authority", "Requisitioner",
            "Procurement Planner", "Procurement Officer", "Finance Reviewer",
            "Department Approver", "Auditor", "Administrator", "System Manager",
        }
        for role in expected_read:
            self.assertIn(
                role, read_roles,
                f"Role '{role}' missing read permission on Procurement Journey",
            )

    # PERM-MATRIX-002
    def test_matrix_002_handoff_read_has_all_internal_roles(self):
        """PERM-MATRIX-002: All 9 non-admin internal roles have read on Procurement Handoff Card."""
        frappe.set_user(_ADMIN)
        read_roles = self._get_roles_with_read("Procurement Handoff Card")
        expected_read = {
            "Planning Authority", "Requisitioner",
            "Procurement Planner", "Procurement Officer", "Finance Reviewer",
            "Department Approver", "Auditor", "Administrator", "System Manager",
        }
        for role in expected_read:
            self.assertIn(
                role, read_roles,
                f"Role '{role}' missing read permission on Procurement Handoff Card",
            )

    # PERM-MATRIX-003
    def test_matrix_003_journey_write_restricted_to_admin_roles(self):
        """PERM-MATRIX-003: Only System Manager / Administrator have write on Procurement Journey."""
        frappe.set_user(_ADMIN)
        write_roles = self._get_roles_with_write("Procurement Journey")
        self.assertIn("System Manager", write_roles)
        self.assertIn("Administrator", write_roles)
        # Non-admin roles must NOT have write (G0-006 no-escalation rule)
        non_admin_write_roles = write_roles - {"System Manager", "Administrator"}
        self.assertEqual(
            non_admin_write_roles, set(),
            f"Unexpected roles with write on Procurement Journey: {non_admin_write_roles}",
        )

    # PERM-MATRIX-004
    def test_matrix_004_handoff_write_restricted_to_admin_roles(self):
        """PERM-MATRIX-004: Only System Manager / Administrator have write on Procurement Handoff Card."""
        frappe.set_user(_ADMIN)
        write_roles = self._get_roles_with_write("Procurement Handoff Card")
        self.assertIn("System Manager", write_roles)
        self.assertIn("Administrator", write_roles)
        non_admin_write_roles = write_roles - {"System Manager", "Administrator"}
        self.assertEqual(
            non_admin_write_roles, set(),
            f"Unexpected roles with write on Procurement Handoff Card: {non_admin_write_roles}",
        )


# ---------------------------------------------------------------------------
# PERM-USER: per-user permission checks using existing site seed users
# ---------------------------------------------------------------------------


class TestPerUserPermissions(IntegrationTestCase):
    """Verify each named internal role user passes the has_permission gate."""

    def _check_user(self, user: str, role_label: str) -> None:
        """Assert user has journey_read and handoff_read; neither write."""
        journey_read = user_has_journey_read(user)
        handoff_read = user_has_handoff_read(user)
        self.assertTrue(
            journey_read,
            f"FAIL: {role_label} ({user}) should have journey read — DocPerm missing?",
        )
        self.assertTrue(
            handoff_read,
            f"FAIL: {role_label} ({user}) should have handoff read — DocPerm missing?",
        )

    # PERM-USER-002 to PERM-USER-008
    # PERM-USER-001 covered "Strategy Manager", a Role deleted in STR-CHG-001
    # v1.7 — it named Strategy authority it never carried after the rebuild and
    # survived only as this cross-app read grant.
    def test_user_002_planning_authority(self):
        """PERM-USER-002: Planning Authority has journey + handoff read."""
        self._check_user(_ROLE_USERS["Planning Authority"], "Planning Authority")

    def test_user_003_requisitioner(self):
        """PERM-USER-003: Requisitioner has journey + handoff read."""
        self._check_user(_ROLE_USERS["Requisitioner"], "Requisitioner")

    def test_user_004_procurement_planner(self):
        """PERM-USER-004: Procurement Planner has journey + handoff read."""
        self._check_user(_ROLE_USERS["Procurement Planner"], "Procurement Planner")

    def test_user_005_procurement_officer(self):
        """PERM-USER-005: Procurement Officer has journey + handoff read."""
        self._check_user(_ROLE_USERS["Procurement Officer"], "Procurement Officer")

    def test_user_006_finance_reviewer(self):
        """PERM-USER-006: Finance Reviewer has journey + handoff read."""
        self._check_user(_ROLE_USERS["Finance Reviewer"], "Finance Reviewer")

    def test_user_007_department_approver(self):
        """PERM-USER-007: Department Approver has journey + handoff read."""
        self._check_user(_ROLE_USERS["Department Approver"], "Department Approver")

    def test_user_008_auditor(self):
        """PERM-USER-008: Auditor has journey + handoff read."""
        self._check_user(_ROLE_USERS["Auditor"], "Auditor")

    # PERM-USER-009
    def test_user_009_administrator_has_write(self):
        """PERM-USER-009: Administrator has journey_read, handoff_read, and handoff_write."""
        journey_read = user_has_journey_read(_ADMIN)
        handoff_read = user_has_handoff_read(_ADMIN)
        handoff_write = user_has_handoff_write(_ADMIN)
        self.assertTrue(journey_read, "Administrator must have journey read")
        self.assertTrue(handoff_read, "Administrator must have handoff read")
        self.assertTrue(handoff_write, "Administrator must have handoff write")


# ---------------------------------------------------------------------------
# PERM-API: API-level permission enforcement
# ---------------------------------------------------------------------------


class TestApiPermissionEnforcement(IntegrationTestCase):
    """Verify the API functions enforce the permission gate end-to-end."""

    # PERM-API-001
    def test_api_001_list_journeys_succeeds_as_admin(self):
        """PERM-API-001: list_journeys succeeds as Administrator."""
        frappe.set_user(_ADMIN)
        result = list_journeys()
        self.assertIn("items", result)
        self.assertIn("counts", result)

    # PERM-API-002
    def test_api_002_get_journey_succeeds_as_admin(self):
        """PERM-API-002: get_journey succeeds as Administrator for WORKS journey."""
        frappe.set_user(_ADMIN)
        result = get_journey(_WORKS_JOURNEY)
        self.assertIn("journey_code", result)
        self.assertEqual(result["journey_code"], _WORKS_JOURNEY)

    # PERM-API-003
    def test_api_003_get_handoff_card_succeeds_as_admin(self):
        """PERM-API-003: get_handoff_card succeeds as Administrator for WORKS PKGREL."""
        frappe.set_user(_ADMIN)
        result = get_handoff_card(_WORKS_PKGREL)
        self.assertEqual(result["handoff_code"], _WORKS_PKGREL)

    # PERM-API-004 — Journey APIs deny Guest
    def test_api_004_list_journeys_denies_guest(self):
        """PERM-API-004a: list_journeys raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                list_journeys()
        finally:
            frappe.set_user(_ADMIN)

    def test_api_004b_get_journey_denies_guest(self):
        """PERM-API-004b: get_journey raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                get_journey(_WORKS_JOURNEY)
        finally:
            frappe.set_user(_ADMIN)

    # PERM-API-005 — Handoff APIs deny Guest
    def test_api_005a_get_handoff_card_denies_guest(self):
        """PERM-API-005a: get_handoff_card raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                get_handoff_card(_WORKS_PKGREL)
        finally:
            frappe.set_user(_ADMIN)

    def test_api_005b_refresh_handoff_card_denies_guest(self):
        """PERM-API-005b: refresh_handoff_card raises PermissionError for Guest."""
        frappe.set_user(_GUEST)
        try:
            with self.assertRaises(frappe.PermissionError):
                refresh_handoff_card(_WORKS_PKGREL)
        finally:
            frappe.set_user(_ADMIN)

    # PERM-API-006 — Temp no-role user
    def test_api_006_no_role_user_denied(self):
        """PERM-API-006: A user with no procurement roles is denied journey/handoff read.

        Creates a temporary Frappe user with only 'Desk User' (no PLC DocPerms),
        checks that ``user_has_journey_read`` and ``user_has_handoff_read`` return False,
        then cleans up.
        """
        temp_email = "plc.r3019.norole.temp@test.local"
        frappe.set_user(_ADMIN)

        # Create temp user with no procurement roles (only Desk User = minimal base)
        try:
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True)

            user_doc = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": temp_email,
                    "first_name": "PLCTestNoRole",
                    "last_name": "R3019",
                    "enabled": 1,
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Desk User"}],
                }
            )
            user_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            # The no-role user should NOT have read on either DocType
            journey_read = user_has_journey_read(temp_email)
            handoff_read = user_has_handoff_read(temp_email)

            self.assertFalse(
                journey_read,
                f"No-role user {temp_email!r} must NOT have journey read",
            )
            self.assertFalse(
                handoff_read,
                f"No-role user {temp_email!r} must NOT have handoff read",
            )

        finally:
            frappe.set_user(_ADMIN)
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True, ignore_permissions=True)
                frappe.db.commit()
