# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5A — the product-suitability compatibility test, run at
`PrepareITEquipmentRequisition` and rechecked at `AuthoriseRequisition`.

Every row is independently checked and independently named on failure
(REQ-AC-053 — no test is folded into a single generic suitability flag).
`plan_horizon` is deliberately absent (§5A: it changes what the drawn value
means, never whether the Requisition is compatible).

Assumption recorded here rather than left implicit: REQ-CHG-001 v1.6 names
a "Requirement type" row but defines no dedicated field for it — Planning's
own `requirement_type` (the statutory classification: Goods / Works /
Non-consulting services / Consulting services) is the nearest real field,
so this test checks that value equals "Goods", the same as the
`procurement_category` row it sits beside. This is a judgement call, not a
value the spec states explicitly; it catches a genuine data inconsistency
(a Plan Item marked Goods at category level but Consulting services at
requirement-type level) rather than inventing a new undefined field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kentender_core.services.regulatory_reference import TENDER_RENDERABLE_RESERVATION_CATEGORIES


@dataclass(frozen=True)
class CompatibilityResult:
	test: str
	required: str
	actual: str

	@property
	def ok(self) -> bool:
		return self.actual == self.required or (self.test == "reservation_category" and self.actual in TENDER_RENDERABLE_RESERVATION_CATEGORIES)


def check(projection: dict[str, Any]) -> list[CompatibilityResult]:
	"""Every §5A row, in table order. Callers check `all(r.ok for r in ...)`
	and report the first failing `test`/`required`/`actual` triple."""
	reservation_category = (projection.get("reservation_category") or "None").strip() or "None"
	return [
		CompatibilityResult("procurement_category", "Goods", projection.get("procurement_category") or ""),
		CompatibilityResult("requirement_type", "Goods", projection.get("requirement_type") or ""),
		CompatibilityResult("reservation_category", "one of " + ", ".join(TENDER_RENDERABLE_RESERVATION_CATEGORIES), reservation_category),
		CompatibilityResult("lotting_indicator", "Single lot", projection.get("lotting_indicator") or ""),
		CompatibilityResult("currency", "KES", projection.get("currency") or ""),
		CompatibilityResult("award_packages", "1", str(projection.get("award_packages") or "")),
	]


def is_compatible(projection: dict[str, Any]) -> bool:
	return all(r.ok for r in check(projection))


def first_failure(projection: dict[str, Any]) -> CompatibilityResult | None:
	for r in check(projection):
		if not r.ok:
			return r
	return None
