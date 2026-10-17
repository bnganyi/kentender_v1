# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.21 §5.7A / §7.5 — the one seam from Tenders to Requisitions' whole-Tender cancellation recovery.

Tenders never writes a Requisition, Planning or Budget table. Inside the Accounting Officer's `CancelTender` transaction it asks
Requisitions to register the recovery (`register_cancellation_resource_recovery`), which records the durable Pending intent and
places Planning's hold on the affected sources; if that cannot be done the cancellation does not commit. After the cancellation
commits, Tenders only reads the recovery's status back (`read`) for its screens. Every Requisitions refusal is remapped onto the
closed Tenders error set here (`TND_MUST_FIX`, the code a cancellation guard already uses)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import cancellation_recovery as req_recovery
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.tenders.services.errors import fail

NOT_REGISTERED = "The cancellation could not be completed because the Tender's unused funding could not be marked for recovery. Nothing was cancelled."


def register(*, root, cancellation, cancellation_digest: str, decided_at, actor: str, origin: str = "Cancellation", reconciliation_version: str = "") -> dict[str, Any]:
	"""Register the recovery for this cancellation, inside the cancellation transaction (or, for a Tender cancelled before this existed, from
	the cancellation as it was decided: `origin` is then `Legacy reconciliation`). Returns Requisitions' result, with the exact consumed
	lineage the `TenderCancelled` event carries."""
	try:
		return req_recovery.register_cancellation_resource_recovery(
			tender=root.name, cancellation=cancellation.name, cancellation_digest=cancellation_digest, cancelled_at=decided_at,
			handoff=cstr(root.requisition_handoff), registered_by=actor, origin=origin, reconciliation_version=reconciliation_version,
			fixture_namespace=cstr(root.fixture_namespace),
		)
	except ProcurementRequisitionsError as exc:
		reasons = [NOT_REGISTERED]
		fail("TND_MUST_FIX", reasons[0], {"reasons": reasons, "requisitions_code": exc.code, "requisitions_detail": exc.detail})
	return {}


def section(tender: str, user: str | None = None) -> dict[str, Any] | None:
	"""The 'Unused allowance and funding' section of a cancelled Tender's screen, in Tenders' words, built from what Requisitions will show this
	reader (permitted rows only, identifiers under Technical details); None when there is none or the reader may not see it."""
	from kentender_procurement.procurement_requisitions.services import recovery_view

	return recovery_view.for_tender(tender, owner="Tenders", user=user)


def read(tender: str, user: str | None = None) -> dict[str, Any] | None:
	"""The recovery's current status and amounts for a cancelled Tender, as Requisitions will show them to this reader; None when the reader
	may not see it or there is none."""
	try:
		return req_recovery.get_cancellation_resource_recovery(tender=tender, user=user)
	except (frappe.DoesNotExistError, frappe.PermissionError):
		return None
