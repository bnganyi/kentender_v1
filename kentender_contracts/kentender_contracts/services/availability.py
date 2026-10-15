# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Is every source an award's agreement is made from available and verified? (CM-CHG-001 v0.8 section 19.4; plan D20; tracker CM8-520.)

For one award this lists, source by source (S1 to S12), whether its owner supplies it, whether what the owner supplies verifies, and if not exactly why and whose it is. It reads through the core source
seam only. An agreement is formed only when the answer is "all of them"; until then the report is the owner-facing list of what is missing, which is what the head of procurement sees on the contract
and what the release evidence carries."""

from __future__ import annotations

from typing import Any

from kentender_contracts.services import source_package
from kentender_core.services import contract_source_contract as seam


def report(award_case: str) -> dict[str, Any]:
	"""`{"sources": [{source, category, owner, available, verified, reason}], "formable": bool}` for one award."""
	handoff = seam.handoff(award_case)
	found = source_package.gather(handoff)
	failed = {f["source"]: f for f in found["failed"]}
	rows = []
	for number in source_package.REQUIRED:
		row = next((r for r in handoff if r["source"] == number), {})
		bad = failed.get(number)
		rows.append({"source": number, "category": source_package.CATEGORIES[number], "owner": (bad or {}).get("owner") or row.get("owner", ""), "available": bool(row) and "unavailable" not in row,
			"verified": number in found["sources"], "reason": (bad or {}).get("reason", ""), "version": row.get("version", ""), "reference": row.get("reference", "")})
	return {"award_case": award_case, "sources": rows, "formable": not failed}
