# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The one door from Bid Submission into Tenders and STD (BDS-CHG-001 v0.8
plan D3). Bid Submission reads published Tender facts, documents, answers,
candidate notices and the Published Bid Definition only through the
Tenders-owned seams named here, so a Tenders change has one place to land."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tenders.services import bidder_projection


def available_tenders(*, at) -> list[dict[str, Any]]:
	return bidder_projection.available_tenders(at=at)


def published_tender(reference: str, *, at) -> dict[str, Any] | None:
	return bidder_projection.published_tender(reference, at=at)
