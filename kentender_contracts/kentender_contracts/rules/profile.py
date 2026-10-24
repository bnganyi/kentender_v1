# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Rule profiles and their verified parameters (CM-CHG-001 v0.8 §4.1 "Production profile guard", §19.3; plan D10; CM-AC-30, 36, 71).

A profile is **code-owned** and is Draft, Verified or Suspended. Verification is recorded through the shared legal/configuration owner,
never by a business form that edits an executable parameter, and a profile or result already used is immutable (a correction is a
successor). A Draft or Suspended rule blocks only the consequential actions it governs: reads, saved preparation, factual arrival,
restriction evidence, incident recording and protective correction stay possible (`gate.py`).

The numeric limits below are the read Act provisions the specification states, each with its rule and locator; they are parameters of a
profile, not constants of the code. The production profile is **Draft** until the legal/procurement owner records the current applicable
profile (LQ-01), so on a live site the consequential actions it governs refuse with `CM_RULE`. The *Illustrative test terms* profile is a
labelled synthetic one for mechanism tests (D34 early quantity change, D02 no-security setting, D36 daily percentage). It exists only on a
simulation site, is stored as a **classification** and never drawn as a banner (DEC-044), and keeps every statutory ceiling: test mode does
not skip them (CM-AC-36). No 14-day, 30-day, 60-day or Regulations-only deadline is a constant of the code (CM-AC-30)."""

from __future__ import annotations

from dataclasses import dataclass

DRAFT, VERIFIED, SUSPENDED = "Draft", "Verified", "Suspended"


@dataclass(frozen=True)
class Parameter:
	name: str
	value: float | int
	unit: str
	rule: str
	locator: str  # the Act provision, or the mechanism example, the value comes from


STATUTORY: tuple[Parameter, ...] = (
	Parameter("ag_clearance_threshold", 5_000_000_000, "KES, value exceeding", "CM-R-03", "§134(2), (5)"),
	Parameter("advance_cap_percent", 20, "% of tender price", "CM-R-07", "§§146–148"),
	Parameter("performance_security_cap_percent", 10, "% of contract amount", "CM-R-08", "§§142–144"),
	Parameter("security_return_days", 30, "days from actual AO final acceptance", "CM-R-09", "§145"),
	Parameter("goods_quantity_increase_ceiling_percent", 15, "% of original quantity", "CM-R-11", "§139"),
	Parameter("cumulative_goods_value_increase_ceiling_percent", 25, "% of original value", "CM-R-11", "§139"),
	Parameter("upward_price_variation_bar_months", 12, "months from signing", "CM-R-11", "§139(3)"),
)

SYNTHETIC_ONLY: tuple[Parameter, ...] = (
	Parameter("delay_rate_per_day", 0.001, "fraction of eligible principal per day", "CM-R-12", "D36 mechanism example, not a verified statutory rate"),
	Parameter("delay_cap_percent", 10, "% of eligible principal", "CM-R-12", "D36 mechanism example, not a verified statutory cap"),
)


@dataclass(frozen=True)
class Profile:
	id: str
	label: str
	status: str
	synthetic: bool
	parameters: tuple[Parameter, ...]
	resolved_questions: tuple[str, ...] = ()  # LQ ids the synthetic profile answers illustratively; a production profile answers none until reviewed
	suspended_rules: tuple[str, ...] = ()

	def rule_status(self, rule_id: str) -> str:
		return SUSPENDED if rule_id in self.suspended_rules else self.status

	def parameter(self, name: str) -> Parameter:
		for p in self.parameters:
			if p.name == name:
				return p
		raise KeyError(f"{self.id} has no parameter {name!r}")


PRODUCTION = Profile("KE-PPADA-2015", "Public Procurement and Asset Disposal Act, 2015", DRAFT, False, STATUTORY)
SYNTHETIC = Profile("SYNTHETIC-ILLUSTRATIVE", "Illustrative test terms", VERIFIED, True, STATUTORY + SYNTHETIC_ONLY, resolved_questions=("LQ-02", "LQ-03", "LQ-04"))
PROFILES = {p.id: p for p in (PRODUCTION, SYNTHETIC)}
