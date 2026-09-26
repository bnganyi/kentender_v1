# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission's portal surface (`kt_portal_surfaces`; BDS-CHG-001 v0.8
plan OD-B). `resolve` answers every path the surface owns with the verdict
and the first payload the screen paints from (KT-STD-001 §3A.1). Screens are
added slice by slice (plan Phase 11); a path with no screen yet is
NOT_FOUND, never a guess."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services import reads

FILTER_KEYS = ("search", "method", "reservation", "closing")


def resolve(*, path: str, query: dict[str, Any], user: str) -> dict[str, Any]:
	segments = [s for s in path.split("/") if s]
	if segments == ["tenders"]:
		filters = {k: str(query.get(k) or "") for k in FILTER_KEYS if query.get(k)}
		return {"verdict": "OK", "title": "Available Tenders", "payload": {"screen": "available-tenders", "data": reads.get_available_tenders(**filters)}}
	return {"verdict": "NOT_FOUND", "title": "Page not found", "payload": {"screen": "not-found"}}
