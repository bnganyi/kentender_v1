# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared Procuring Entity code aliases for Home queries."""

from __future__ import annotations


def pe_aliases(pe: str) -> list[str]:
	pe = (pe or "").strip()
	aliases = {pe}
	if pe in ("MOH", "PE-MOH"):
		aliases |= {"MOH", "PE-MOH"}
	return sorted(a for a in aliases if a)
