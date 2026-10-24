# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A verified applicable cancellation ground (TPR-CHG-001 v0.24 §5.12, §7.6, §8 `TND_CANCEL_GROUND_UNVERIFIED`).

The existing ground catalogue (`cancellation.CANCELLATION_GROUNDS`) names the lawful grounds the Accounting Officer chooses from; its wording is still
marked for verification (FU-06). The post-close route does not rest on the catalogue alone: it needs a ground the legal profile has verified as
applicable at that stage. That fact belongs to no Tenders record — Tenders asks each registered verifier (`kt_tender_cancellation_ground_verifiers`) and
believes only what a verifier returns. A technical failure alone verifies nothing: nothing here reads an incident or a fault. With no verifier registered,
or none that verifies a ground, the route is blocked with `TND_CANCEL_GROUND_UNVERIFIED`; HOPF coordinates the documented review and the Accounting
Officer keeps the decision. No role can create a per-Tender override.

Each verifier is `fn(*, tender, stage) -> {"grounds": [{"key", "verified", "source", "reference", "version", "checked_at"}]}`."""

from __future__ import annotations

from typing import Any, Iterable

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import clock

HOOK = "kt_tender_cancellation_ground_verifiers"


def verified(*, tender: str, stage: str, known: Iterable[str]) -> dict[str, Any]:
	"""`{"grounds": {key: evidence}, "checked_at": ...}` — only keys in the catalogue (`known`) that a verifier marked verified."""
	known = set(known)
	grounds: dict[str, dict[str, Any]] = {}
	for path in frappe.get_hooks(HOOK) or []:
		try:
			answer = frappe.get_attr(path)(tender=tender, stage=stage) or {}
		except Exception:
			frappe.log_error(title="Cancellation ground verifier failed")
			continue
		for row in answer.get("grounds") or []:
			key = cstr(row.get("key"))
			if key in known and row.get("verified", True) and key not in grounds:
				grounds[key] = {"key": key, "source": cstr(row.get("source")), "reference": cstr(row.get("reference")), "version": cstr(row.get("version")),
					"checked_at": cstr(row.get("checked_at"))}
	return {"grounds": grounds, "checked_at": clock.now()}
