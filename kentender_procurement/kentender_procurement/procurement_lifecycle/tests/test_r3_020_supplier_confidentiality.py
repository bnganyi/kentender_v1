# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-020 / LV-R3-020-01 — Supplier confidentiality guard: negative tests.

## Goal (why this test exists)

Prove that **supplier portal actors** (Guest + users with ``KenTender External Supplier``
role) are **denied by default** on **all five** Procurement Lifecycle API operations,
matching the G0-006 threat model §3 access matrix and pack §10.4 confidentiality rule:

  *"Supplier cannot access internal journey evidence by default."*

The **evidence timeline** endpoint is the highest-risk surface (G0-006 §4 mitigation 4,
PLC-SMOKE-014 / PLC-NB-005) and is the primary target of the named test path
**NEG-SUP-EVIDENCE-ACCESS-001**.

## G0-006 access matrix — supplier row

| API operation | Supplier / Guest | Reason |
|---|---|---|
| ``list_journeys`` | **Deny** | List leaks programme existence / titles. |
| ``get_journey`` | **Deny** | Full spine exposes cross-module state. |
| ``get_journey_by_object`` | **Deny** | Object enumeration bypass risk. |
| ``get_journey_evidence`` | **Deny** (highest risk) | Internal timeline, handoff payloads, audit joins. |
| ``get_handoff_card`` | **Deny** | Internal handoff narrative + evidence links. |

## Actors tested

1. **Guest** — unauthenticated Frappe session.
2. **KenTender External Supplier** (``smoke.b@kentender.test``) — authenticated but
   has no ``read`` DocPerm on ``Procurement Journey`` or ``Procurement Handoff Card``.
3. **Temp supplier-like user** — created ad hoc with only ``KenTender External Supplier``
   role, proving the gate works regardless of which pre-existing user is in the data.

## Test IDs

| Test | Description |
|---|---|
| NEG-SUP-EVIDENCE-ACCESS-001 | **Primary.** Supplier cannot call ``get_journey_evidence`` (evidence timeline). |
| NEG-SUP-001 | Guest cannot call ``list_journeys``. |
| NEG-SUP-002 | Guest cannot call ``get_journey``. |
| NEG-SUP-003 | Guest cannot call ``get_journey_by_object``. |
| NEG-SUP-004 | Guest cannot call ``get_handoff_card``. |
| NEG-SUP-005 | Guest cannot call ``refresh_handoff_card``. |
| NEG-SUP-006 | KenTender External Supplier user cannot read Procurement Journey (DocPerm = 0). |
| NEG-SUP-007 | KenTender External Supplier user cannot read Procurement Handoff Card (DocPerm = 0). |
| NEG-SUP-008 | Supplier user (smoke.b) → ``list_journeys`` raises PermissionError. |
| NEG-SUP-009 | Supplier user (smoke.b) → ``get_journey`` raises PermissionError. |
| NEG-SUP-010 | Supplier user (smoke.b) → ``get_journey_evidence`` (NEG-SUP-EVIDENCE-ACCESS-001 via named user). |
| NEG-SUP-011 | Supplier user (smoke.b) → ``get_handoff_card`` raises PermissionError. |
| NEG-SUP-012 | Temp supplier user → ``user_has_journey_read`` returns False. |
| NEG-SUP-013 | Temp supplier user → ``user_has_handoff_read`` returns False. |
| NEG-SUP-DOCPERM-001 | ``KenTender External Supplier`` role has no read DocPerm on Procurement Journey. |
| NEG-SUP-DOCPERM-002 | ``KenTender External Supplier`` role has no read DocPerm on Procurement Handoff Card. |
| NEG-SUP-DOCPERM-003 | ``Supplier`` role has no read DocPerm on Procurement Journey. |
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.api.permission_guard import (
    user_has_journey_read,
    user_has_handoff_read,
)
from kentender_procurement.procurement_lifecycle.api.journey_api import (
    list_journeys,
    get_journey,
    get_journey_by_object,
    get_journey_steps,
    get_journey_evidence,
)
from kentender_procurement.procurement_lifecycle.api.handoff_api import (
    get_handoff_card,
    refresh_handoff_card,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ADMIN = "Administrator"
_GUEST = "Guest"

# Existing supplier seed user on this site with KenTender External Supplier role
_SUPPLIER_USER = "smoke.b@kentender.test"

# WORKS golden codes
_WORKS_JOURNEY = "JRN-MOH-2026-001"
_WORKS_PKGREL   = "PKGREL-MOH-2026-001"

# Supplier roles that must have NO read on PLC DocTypes
_SUPPLIER_ROLE_NAMES = [
    "KenTender External Supplier",
    "Supplier",
    "KenTender Supplier Registry Officer",
    "KenTender Supplier Auditor",
    "KenTender Supplier Blacklist Authority",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _assert_denied(test_case, func, *args, actor_label: str = "", **kwargs):
    """Call *func* and assert PermissionError is raised; restore Administrator after."""
    try:
        with test_case.assertRaises(frappe.PermissionError,
                                    msg=f"{actor_label} must not access {func.__name__}"):
            func(*args, **kwargs)
    finally:
        frappe.set_user(_ADMIN)


# ---------------------------------------------------------------------------
# NEG-SUP-DOCPERM: DocType permission table — supplier roles have no read
# ---------------------------------------------------------------------------


class TestSupplierDocPermMatrix(IntegrationTestCase):
    """Verify supplier roles carry no DocPerm on PLC DocTypes (structural deny)."""

    def _role_has_read(self, doctype: str, role: str) -> bool:
        result = frappe.db.get_value(
            "DocPerm",
            {"parent": doctype, "role": role, "read": 1},
            "name",
        )
        return bool(result)

    # NEG-SUP-DOCPERM-001
    def test_docperm_001_external_supplier_no_journey_read(self):
        """NEG-SUP-DOCPERM-001: KenTender External Supplier has no read on Procurement Journey."""
        frappe.set_user(_ADMIN)
        self.assertFalse(
            self._role_has_read("Procurement Journey", "KenTender External Supplier"),
            "KenTender External Supplier must NOT have read on Procurement Journey",
        )

    # NEG-SUP-DOCPERM-002
    def test_docperm_002_external_supplier_no_handoff_read(self):
        """NEG-SUP-DOCPERM-002: KenTender External Supplier has no read on Procurement Handoff Card."""
        frappe.set_user(_ADMIN)
        self.assertFalse(
            self._role_has_read("Procurement Handoff Card", "KenTender External Supplier"),
            "KenTender External Supplier must NOT have read on Procurement Handoff Card",
        )

    # NEG-SUP-DOCPERM-003
    def test_docperm_003_supplier_role_no_journey_read(self):
        """NEG-SUP-DOCPERM-003: Generic 'Supplier' role has no read on Procurement Journey."""
        frappe.set_user(_ADMIN)
        self.assertFalse(
            self._role_has_read("Procurement Journey", "Supplier"),
            "'Supplier' role must NOT have read on Procurement Journey",
        )

    def test_docperm_004_all_supplier_roles_no_journey_read(self):
        """NEG-SUP-DOCPERM-004: None of the supplier role names have read on Procurement Journey."""
        frappe.set_user(_ADMIN)
        for role in _SUPPLIER_ROLE_NAMES:
            has = self._role_has_read("Procurement Journey", role)
            self.assertFalse(
                has,
                f"Role '{role}' must NOT have read on Procurement Journey — found unexpected DocPerm",
            )

    def test_docperm_005_all_supplier_roles_no_handoff_read(self):
        """NEG-SUP-DOCPERM-005: None of the supplier role names have read on Procurement Handoff Card."""
        frappe.set_user(_ADMIN)
        for role in _SUPPLIER_ROLE_NAMES:
            has = self._role_has_read("Procurement Handoff Card", role)
            self.assertFalse(
                has,
                f"Role '{role}' must NOT have read on Procurement Handoff Card — found unexpected DocPerm",
            )


# ---------------------------------------------------------------------------
# NEG-SUP: Guest session denials
# ---------------------------------------------------------------------------


class TestGuestDeniedAllOps(IntegrationTestCase):
    """Verify Guest (unauthenticated) is denied every PLC API operation."""

    # NEG-SUP-001
    def test_neg_sup_001_guest_list_journeys_denied(self):
        """NEG-SUP-001: Guest cannot call list_journeys."""
        frappe.set_user(_GUEST)
        _assert_denied(self, list_journeys, actor_label="Guest")

    # NEG-SUP-002
    def test_neg_sup_002_guest_get_journey_denied(self):
        """NEG-SUP-002: Guest cannot call get_journey."""
        frappe.set_user(_GUEST)
        _assert_denied(self, get_journey, _WORKS_JOURNEY, actor_label="Guest")

    # NEG-SUP-003
    def test_neg_sup_003_guest_get_journey_by_object_denied(self):
        """NEG-SUP-003: Guest cannot call get_journey_by_object."""
        frappe.set_user(_GUEST)
        _assert_denied(self, get_journey_by_object, "TM2 Tender", "TND-MOH-2026-001", actor_label="Guest")

    # NEG-SUP-EVIDENCE-ACCESS-001 (Guest variant)
    def test_neg_sup_evidence_access_001_guest_evidence_denied(self):
        """NEG-SUP-EVIDENCE-ACCESS-001: Guest cannot access internal evidence timeline.

        This is the primary named test path for the supplier confidentiality guard.
        The evidence endpoint is the highest-risk surface per G0-006 §4 — internal
        timeline, handoff payloads, audit joins.  Default deny is non-negotiable.
        """
        frappe.set_user(_GUEST)
        _assert_denied(self, get_journey_evidence, _WORKS_JOURNEY, actor_label="Guest")

    # NEG-SUP-004
    def test_neg_sup_004_guest_get_handoff_card_denied(self):
        """NEG-SUP-004: Guest cannot call get_handoff_card."""
        frappe.set_user(_GUEST)
        _assert_denied(self, get_handoff_card, _WORKS_PKGREL, actor_label="Guest")

    # NEG-SUP-005
    def test_neg_sup_005_guest_refresh_handoff_denied(self):
        """NEG-SUP-005: Guest cannot call refresh_handoff_card."""
        frappe.set_user(_GUEST)
        _assert_denied(self, refresh_handoff_card, _WORKS_PKGREL, actor_label="Guest")

    # NEG-SUP-006
    def test_neg_sup_006_guest_journey_read_false(self):
        """NEG-SUP-006: user_has_journey_read returns False for Guest."""
        self.assertFalse(user_has_journey_read("Guest"))

    # NEG-SUP-007
    def test_neg_sup_007_guest_handoff_read_false(self):
        """NEG-SUP-007: user_has_handoff_read returns False for Guest."""
        self.assertFalse(user_has_handoff_read("Guest"))


# ---------------------------------------------------------------------------
# NEG-SUP: Named supplier user (smoke.b) denials
# ---------------------------------------------------------------------------


class TestSupplierUserDeniedAllOps(IntegrationTestCase):
    """Verify the named External Supplier seed user is denied every PLC API operation.

    smoke.b@kentender.test has KenTender External Supplier role — no procurement DocPerms.
    """

    # NEG-SUP-008 (permission helper)
    def test_neg_sup_008_supplier_user_journey_read_false(self):
        """NEG-SUP-008: KenTender External Supplier user has user_has_journey_read=False."""
        frappe.set_user(_ADMIN)
        result = user_has_journey_read(_SUPPLIER_USER)
        self.assertFalse(
            result,
            f"Supplier user {_SUPPLIER_USER!r} must NOT have journey read",
        )

    # NEG-SUP-009
    def test_neg_sup_009_supplier_user_handoff_read_false(self):
        """NEG-SUP-009: KenTender External Supplier user has user_has_handoff_read=False."""
        frappe.set_user(_ADMIN)
        result = user_has_handoff_read(_SUPPLIER_USER)
        self.assertFalse(
            result,
            f"Supplier user {_SUPPLIER_USER!r} must NOT have handoff read",
        )

    # NEG-SUP-EVIDENCE-ACCESS-001 (named supplier user variant)
    def test_neg_sup_evidence_access_001_supplier_user_evidence_denied(self):
        """NEG-SUP-EVIDENCE-ACCESS-001 (named user): External Supplier cannot access evidence timeline.

        This is the second facet of the primary test path.  A real authenticated
        supplier user (smoke.b@kentender.test with KenTender External Supplier role)
        must be denied when calling get_journey_evidence — mirroring the threat model
        G0-006 §3 row for 'Supplier / Guest' on evidence timeline.
        """
        frappe.set_user(_SUPPLIER_USER)
        _assert_denied(self, get_journey_evidence, _WORKS_JOURNEY, actor_label="Supplier user")

    # NEG-SUP-010
    def test_neg_sup_010_supplier_user_list_journeys_denied(self):
        """NEG-SUP-010: External Supplier user cannot call list_journeys."""
        frappe.set_user(_SUPPLIER_USER)
        _assert_denied(self, list_journeys, actor_label="Supplier user")

    # NEG-SUP-011
    def test_neg_sup_011_supplier_user_get_journey_denied(self):
        """NEG-SUP-011: External Supplier user cannot call get_journey."""
        frappe.set_user(_SUPPLIER_USER)
        _assert_denied(self, get_journey, _WORKS_JOURNEY, actor_label="Supplier user")

    # NEG-SUP-012
    def test_neg_sup_012_supplier_user_get_handoff_card_denied(self):
        """NEG-SUP-012: External Supplier user cannot call get_handoff_card."""
        frappe.set_user(_SUPPLIER_USER)
        _assert_denied(self, get_handoff_card, _WORKS_PKGREL, actor_label="Supplier user")

    # NEG-SUP-013
    def test_neg_sup_013_supplier_user_journey_steps_denied(self):
        """NEG-SUP-013: External Supplier user cannot call get_journey_steps."""
        frappe.set_user(_SUPPLIER_USER)
        _assert_denied(self, get_journey_steps, _WORKS_JOURNEY, actor_label="Supplier user")


# ---------------------------------------------------------------------------
# NEG-SUP: Temp supplier-like user (created ad hoc)
# ---------------------------------------------------------------------------


class TestTempSupplierUserDenied(IntegrationTestCase):
    """Verify a freshly created user with only supplier role is denied (not data-dependent)."""

    # NEG-SUP-012 / NEG-SUP-013
    def test_neg_sup_temp_supplier_has_no_journey_or_handoff_read(self):
        """NEG-SUP-TEMP: Temp External Supplier user → journey_read=False, handoff_read=False.

        This proves the deny is role-based and not dependent on the specific pre-existing
        supplier seed user.
        """
        temp_email = "plc.r3020.supplier.temp@test.local"
        frappe.set_user(_ADMIN)

        try:
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True)

            user_doc = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": temp_email,
                    "first_name": "PLCSupplierTemp",
                    "last_name": "R3020",
                    "enabled": 1,
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "KenTender External Supplier"}],
                }
            )
            user_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            journey_read = user_has_journey_read(temp_email)
            handoff_read = user_has_handoff_read(temp_email)

            self.assertFalse(
                journey_read,
                f"Temp supplier user {temp_email!r} must NOT have journey read",
            )
            self.assertFalse(
                handoff_read,
                f"Temp supplier user {temp_email!r} must NOT have handoff read",
            )

        finally:
            frappe.set_user(_ADMIN)
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True, ignore_permissions=True)
                frappe.db.commit()

    def test_neg_sup_temp_supplier_evidence_endpoint_denied(self):
        """NEG-SUP-TEMP-EVIDENCE: Temp External Supplier user denied on evidence timeline.

        End-to-end API call from a fresh supplier user — proves the gate is enforced
        independent of pre-existing data.
        """
        temp_email = "plc.r3020.supplier.evidencetest@test.local"
        frappe.set_user(_ADMIN)

        try:
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True)

            user_doc = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": temp_email,
                    "first_name": "PLCSupplierEvidenceTemp",
                    "last_name": "R3020",
                    "enabled": 1,
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "KenTender External Supplier"}],
                }
            )
            user_doc.insert(ignore_permissions=True)
            frappe.db.commit()

            frappe.set_user(temp_email)
            with self.assertRaises(
                frappe.PermissionError,
                msg="Temp External Supplier user must be denied on get_journey_evidence",
            ):
                get_journey_evidence(_WORKS_JOURNEY)

        finally:
            frappe.set_user(_ADMIN)
            if frappe.db.exists("User", temp_email):
                frappe.delete_doc("User", temp_email, force=True, ignore_permissions=True)
                frappe.db.commit()
