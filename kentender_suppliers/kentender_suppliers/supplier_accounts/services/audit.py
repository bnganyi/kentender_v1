# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Supplier Account audit (BDS-CHG-001 v0.8 §12.1) through the platform
Audit Event service: one event per successful command, stamped with the
trusted clock. No evidence bytes, tokens or other secrets are recorded."""

from __future__ import annotations

from typing import Any

from kentender_core.services.audit_event_service import log_audit_event
from kentender_suppliers.supplier_accounts.services import clock

EVENT_TYPE = "supplier_account"
ENTITY = "Supplier Accounts"


def record(*, doctype: str, name: str, action: str, actor: str, metadata: dict[str, Any] | None = None) -> str:
	return log_audit_event(event_type=EVENT_TYPE, entity=ENTITY, document_type=doctype, document_name=name, action=action, performed_by=actor, timestamp=clock.now(), metadata=metadata or {})
