# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The arithmetic of the Award funding allocation (AWD-CHG-001 v0.7 section 7.1).

An awarded price is distributed over the Requisition sources that asked for the goods, for funding only. Nothing here changes a supplier price, an evaluated amount or a submitted sum; it
distributes a supported existing total. The rules, as the section states them:

* A separately priced item's awarded amount belongs to its exact source.
* One identically priced commercial row that combines several source-linked items is split by their exact awarded quantities. Sources with different rates are separate rows.
* A genuinely unallocated common charge or discount follows the proportion of the amounts of its covered commercial rows, after row-specific adjustments and before the common one. A zero
  denominator, or coverage that is not known, is a source issue: the caller refuses and no split is guessed.
* Exact decimal arithmetic. Only derived shares are rounded, to the currency scale: floor the nonnegative absolute minor-unit shares, give the residual minor units to the largest fractional
  remainders, with the source identity as the stable tie-break, then apply the sign of a common discount. Final amounts are nonnegative and add up to the supported price exactly.
* Input money is never rounded, and no epsilon is introduced. Input with more places than the scale is a discrepancy and is refused.

`allocate` is pure: it reads no record, so its cases are proven without a database."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_FLOOR, Decimal
from fractions import Fraction
from typing import Iterable, Sequence

SCALE = 2


class SourceIssue(Exception):
	"""The awarded price cannot be traced to its sources. The positive Award path stays blocked, with this reason, until the source is corrected by its owner. Never an officer price editor."""

	def __init__(self, reason: str, **detail):
		super().__init__(reason)
		self.reason = reason
		self.detail = detail


@dataclass(frozen=True)
class Coverage:
	"""The awarded quantity of one source-linked item inside a commercial row."""

	source: str
	quantity: Decimal


@dataclass(frozen=True)
class Row:
	"""One awarded commercial row. `amount` is its awarded amount after its own discounts and taxes, as recorded."""

	row_id: str
	amount: Decimal
	coverage: tuple[Coverage, ...]


@dataclass(frozen=True)
class Common:
	"""A common charge (positive) or discount (negative) that no row owns. `covers` names the rows whose amounts it follows; empty means every row."""

	adjustment_id: str
	amount: Decimal
	covers: tuple[str, ...] = ()


@dataclass
class Allocation:
	totals: dict[str, Decimal] = field(default_factory=dict)  # source -> amount
	rows: list[dict] = field(default_factory=list)  # evidence: how each derived share was rounded

	def total(self) -> Decimal:
		return sum(self.totals.values(), Decimal("0"))


def _minor(value: Decimal, label: str, scale: int = SCALE) -> int:
	"""Money in minor units. More places than the scale is a discrepancy to refuse, never something to round."""
	if not isinstance(value, Decimal) or not value.is_finite():
		raise SourceIssue(f"{label} is not an exact amount.", item=label)
	scaled = value.scaleb(scale)
	if scaled != scaled.to_integral_value():
		raise SourceIssue(f"{label} has more decimal places than the currency allows.", item=label)
	return int(scaled)


def _apportion(total_minor: int, weights: Sequence[tuple[str, Fraction]]) -> dict[str, int]:
	"""Distribute a nonnegative whole number of minor units by weight: floor every share, then give the residual units to the largest fractional remainders, ties to the lowest source identity."""
	if total_minor < 0:
		raise ValueError("apportion takes the absolute amount")
	denominator = sum((w for _s, w in weights), Fraction(0))
	if denominator <= 0:
		raise SourceIssue("The covered rows have no amount to follow, so the share of a common charge or split cannot be derived.")
	exact = {source: Fraction(total_minor) * weight / denominator for source, weight in weights}
	floors = {source: value.numerator // value.denominator for source, value in exact.items()}
	remainder = total_minor - sum(floors.values())
	order = sorted(exact, key=lambda source: (-(exact[source] - floors[source]), source))
	for source in order[:remainder]:
		floors[source] += 1
	return floors


def allocate(rows: Iterable[Row], common: Iterable[Common] = (), *, scale: int = SCALE) -> Allocation:
	"""The awarded amount per source. Raises `SourceIssue` when a share cannot be derived without a guess."""
	rows, common = list(rows), list(common)
	if not rows:
		raise SourceIssue("The awarded price has no commercial rows to trace.")
	seen: set[str] = set()
	for row in rows:
		if row.row_id in seen:
			raise SourceIssue(f"Commercial row {row.row_id} appears more than once.", row=row.row_id)
		seen.add(row.row_id)
	unit = Decimal(1).scaleb(-scale)
	out = Allocation()
	attributed: dict[str, dict[str, int]] = {}  # row -> source -> minor units, before any common adjustment
	for row in rows:
		minor = _minor(row.amount, f"Row {row.row_id}", scale)
		if minor < 0:
			raise SourceIssue(f"Row {row.row_id} has a negative awarded amount; a common discount is recorded as a common adjustment.", row=row.row_id)
		if not row.coverage:
			raise SourceIssue(f"Row {row.row_id} names no source item, so its funding source is not known.", row=row.row_id)
		quantities: dict[str, Fraction] = {}
		for cover in row.coverage:
			if not cover.source:
				raise SourceIssue(f"Row {row.row_id} names an item with no source.", row=row.row_id)
			if not isinstance(cover.quantity, Decimal) or not cover.quantity.is_finite() or cover.quantity <= 0:
				raise SourceIssue(f"Row {row.row_id} has a source quantity that is not above zero.", row=row.row_id, source=cover.source)
			quantities[cover.source] = quantities.get(cover.source, Fraction(0)) + Fraction(cover.quantity)
		shares = _apportion(minor, list(quantities.items())) if len(quantities) > 1 else {next(iter(quantities)): minor}
		attributed[row.row_id] = shares
		for source, value in shares.items():
			out.totals[source] = out.totals.get(source, Decimal("0")) + Decimal(value) * unit
		out.rows.append({"row": row.row_id, "amount": str(row.amount), "shares": {s: str(Decimal(v) * unit) for s, v in sorted(shares.items())}, "split": len(quantities) > 1})
	for adjustment in common:
		minor = _minor(adjustment.amount, f"Common adjustment {adjustment.adjustment_id}", scale)
		if minor == 0:
			continue
		covered = list(adjustment.covers) or [row.row_id for row in rows]
		unknown = [r for r in covered if r not in attributed]
		if unknown:
			raise SourceIssue(f"Common adjustment {adjustment.adjustment_id} covers a row that is not in the award.", adjustment=adjustment.adjustment_id, rows=unknown)
		weights: dict[str, Fraction] = {}
		for row_id in covered:
			for source, value in attributed[row_id].items():
				weights[source] = weights.get(source, Fraction(0)) + Fraction(value)
		shares = _apportion(abs(minor), list(weights.items()))
		sign = -1 if minor < 0 else 1
		for source, value in shares.items():
			out.totals[source] = out.totals.get(source, Decimal("0")) + sign * Decimal(value) * unit
		out.rows.append({"adjustment": adjustment.adjustment_id, "amount": str(adjustment.amount), "shares": {s: str(sign * Decimal(v) * unit) for s, v in sorted(shares.items())}})
	negative = [source for source, value in out.totals.items() if value < 0]
	if negative:
		raise SourceIssue("A common discount is larger than the amount of the source it follows.", sources=sorted(negative))
	return out


def check_total(allocation: Allocation, supported_price: Decimal) -> None:
	"""The split must add up to the supported award price exactly. Anything else is an unsupported discrepancy, never something to absorb."""
	if allocation.total() != supported_price:
		raise SourceIssue("The funding shares do not add up to the supported award price.", shares=str(allocation.total()), price=str(supported_price))


def fraction_of(value: Decimal) -> Fraction:
	return Fraction(value)


__all__ = ["Allocation", "Common", "Coverage", "Row", "SourceIssue", "allocate", "check_total", "ROUND_FLOOR"]
