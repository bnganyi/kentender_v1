# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Fixture removal for Tender Preparation — the canonical §16 walkthrough
(through `reset_tender_preparation_seed`, which releases the handoff
consumption via Requisitions' seam first) and the Playwright world's rows.
Called by `kentender_core.seeds.kentender_mvp_v1.clear` before Requisitions'
own clear, in reverse dependency order."""

from __future__ import annotations

from typing import Any


def clear_tender_fixture_rows(*, include_canonical: bool = False, include_playwright: bool = True) -> dict[str, Any]:
	deleted: dict[str, Any] = {}
	if include_canonical:
		from kentender_procurement.tender_preparation.seeds.kentender_mvp_v1 import reset_tender_preparation_seed

		deleted["canonical"] = reset_tender_preparation_seed(commit=False)
	if include_playwright:
		from kentender_procurement.tender_preparation.seeds import playwright_ui_fixtures as pw

		pw.wipe_tender_rows(commit=False)
		deleted["playwright_namespace"] = pw.NS_PW
	return {"ok": True, "deleted": deleted}
