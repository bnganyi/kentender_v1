# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §6.3 — brand/restrictive-term detection.

"A brand, model, proprietary certification or named technology triggers a
Blocking finding unless the text includes an approved 'or equivalent'
treatment and a recorded functional reason." A code-owned list, versioned
with the catalogue; operational users cannot extend it (§6.3's own rule for
the characteristic catalogue applies equally here).
"""

from __future__ import annotations

import re

# Manufacturer / brand names.
_BRANDS: tuple[str, ...] = (
	"Dell", "HP", "Hewlett-Packard", "Lenovo", "Apple", "MacBook", "Microsoft Surface",
	"Cisco", "HPE", "Aruba", "Ubiquiti", "TP-Link", "Netgear", "Canon", "Epson", "Brother",
	"Samsung", "LG", "Asus", "Acer", "Toshiba", "Fujitsu", "Huawei", "Xerox", "Kyocera",
)

# Chip / platform families.
_PLATFORMS: tuple[str, ...] = (
	"Core i3", "Core i5", "Core i7", "Core i9", "Ryzen", "Snapdragon", "Apple Silicon",
	"Xeon", "Celeron", "Pentium", "MediaTek",
)

# Proprietary certifications / named technologies.
_CERTIFICATIONS: tuple[str, ...] = (
	"Intel vPro", "ENERGY STAR", "TCO Certified", "MIL-STD-810",
)

_MODEL_PATTERN = re.compile(r"\b[A-Z]{1,4}-?\d{3,5}[A-Z]?\b")

# Words that make an otherwise-restrictive mention safe (§6.3's own escape
# hatch) — checked case-insensitively alongside a recorded functional reason.
_EQUIVALENT_PHRASES: tuple[str, ...] = ("or equivalent", "or better", "or functionally equivalent")

# Not a restrictive term even though it looks brand-like in this fixture's
# own text (§16.3 TECH-009: "Approved organisational Windows environment").
_OS_ALLOWLIST: tuple[str, ...] = ("Windows", "Linux", "macOS", "Android", "iOS", "ChromeOS")


def _strip_allowlisted(text: str) -> str:
	out = text
	for name in _OS_ALLOWLIST:
		out = re.sub(rf"\b{re.escape(name)}\b", "", out)
	return out


def find_restrictive_terms(text: str) -> list[str]:
	"""Every brand/platform/certification/model-pattern hit in `text`,
	ignoring OS-family names (§16.3's fixture explicitly needs "Windows" to
	pass — it names an approved environment, not a restrictive brand)."""
	if not text:
		return []
	scanned = _strip_allowlisted(text)
	hits: list[str] = []
	for term in _BRANDS + _PLATFORMS + _CERTIFICATIONS:
		if re.search(rf"\b{re.escape(term)}\b", scanned, re.IGNORECASE):
			hits.append(term)
	hits.extend(_MODEL_PATTERN.findall(scanned))
	return hits


def has_equivalent_treatment(text: str) -> bool:
	lowered = (text or "").lower()
	return any(phrase in lowered for phrase in _EQUIVALENT_PHRASES)


def is_restrictive(text: str, *, reason: str = "") -> bool:
	"""True only when a restrictive term is present AND it is not excused by
	both an 'or equivalent'-style phrase and a recorded functional reason
	(§6.3: "unless the text includes an approved 'or equivalent' treatment
	and a recorded functional reason")."""
	if not find_restrictive_terms(text):
		return False
	if has_equivalent_treatment(text) and len((reason or "").strip()) >= 20:
		return False
	return True
