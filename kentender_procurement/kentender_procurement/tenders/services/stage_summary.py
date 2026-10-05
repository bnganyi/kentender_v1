# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The stage summaries on the Tender record (OVS-CHG-001 v0.6 §8, §13;
`reconciliation/stage_summary_contract.md`; plan D4; tracker OVS6-03xx).

Each stage owner (Bid Opening, Bid Evaluation, Award) publishes one summary
through the hook `kt_tender_stage_summaries`, called as
`fn(tender=<Tender name>, user=<actor>)`. The owner decides first whether this
reader may know the stage exists (returning `[]` if not), then how much to
disclose. Tenders formats nothing and recomputes no outcome. This module only
gives the owners one shape to return.

An authorised stage that fails to load is returned as an explicit
`unavailable` entry (`OVS_STAGE_UNAVAILABLE`, "We could not load this stage"),
so the other stages stay usable. A denied stage is simply absent: a failure is
never the way a reader learns a stage exists."""

from __future__ import annotations

from typing import Any, Callable

import frappe

STATUS_ONLY = "status_only"
SUMMARY = "summary"  # a department-level summary of a decided outcome
FULL = "full"
UNAVAILABLE_KEY = "OVS_STAGE_UNAVAILABLE"
UNAVAILABLE_MESSAGE = "We could not load this stage"


def fact(label: str, value: Any) -> dict[str, str]:
	"""One labelled fact; a missing value is left out by the caller, never shown as zero."""
	return {"label": label, "value": "" if value is None else str(value)}


def link(key: str, label: str, route: list[str]) -> dict[str, Any]:
	return {"key": key, "label": label, "route": route}


def summary(*, key: str, label: str, status: str, disclosure: str, facts: list[dict[str, str]] | None = None, outcome: dict[str, str] | None = None, actor: str = "",
		recorded_at: str = "", reason: str = "", outstanding: dict[str, str] | None = None, version: str = "", notice: str = "",
		links: list[dict[str, Any]] | None = None) -> dict[str, Any]:
	return {"key": key, "label": label, "state": "ok", "error_key": "", "status": status, "disclosure": disclosure, "facts": [f for f in facts or [] if f["value"]],
		"outcome": outcome, "actor": actor, "recorded_at": recorded_at, "reason": reason, "outstanding": outstanding, "version": version, "notice": notice,
		"links": links or []}


def unavailable(key: str, label: str) -> dict[str, Any]:
	return {"key": key, "label": label, "state": "unavailable", "error_key": UNAVAILABLE_KEY, "message": UNAVAILABLE_MESSAGE, "status": "", "disclosure": STATUS_ONLY,
		"facts": [], "outcome": None, "actor": "", "recorded_at": "", "reason": "", "outstanding": None, "version": "", "notice": "", "links": []}


def guarded(key: str, label: str, build: Callable[[], dict[str, Any]]) -> list[dict[str, Any]]:
	"""Build an authorised stage's summary; a failure becomes the explicit unavailable entry."""
	try:
		return [build()]
	except Exception:
		frappe.log_error(title=f"Tender stage summary failed: {key}")
		return [unavailable(key, label)]
