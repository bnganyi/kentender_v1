# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-26 — Business code helpers (doc 3 §3.1, TM2-ID-008 / TM2-ID-009).

Pure string utilities for **generating** and **validating** TM2 business codes. Allocation that
requires SQL (e.g. next tender suffix **TM2-ID-003**) stays on DocType controllers; this module
captures the **shape** contracts so services and tests share one definition.

**TM2-ID-001 / TM2-ID-002** — product rules (display codes, server-side generation); not encoded as
functions here beyond validation helpers.

**TM2-ID-008** — ``assert_business_code_immutable`` rejects a business-code change when the record is
locked (published / submitted / sealed semantics delegated to the caller via ``*, locked: bool``).

**TM2-ID-009** — ``assert_business_code_immutable`` also applies when ``historical=True`` (superseded,
cancelled, or other terminal states—caller supplies the flag).
"""

from __future__ import annotations

import re
from typing import Any

from frappe.utils import cstr

__all__ = (
	"entity_slug",
	"normalize_fiscal_year",
	"tender_code_prefix",
	"parse_tender_code",
	"format_tsb",
	"format_ttl",
	"format_tac",
	"format_trd",
	"format_pub",
	"format_inv",
	"format_clr",
	"format_clrr",
	"format_add",
	"format_air",
	"format_ack",
	"format_bid",
	"format_rct",
	"format_late",
	"format_cls",
	"format_orr",
	"format_ehr",
	"format_chr",
	"format_ntf",
	"format_tae",
	"assert_business_code_immutable",
)


def entity_slug(procuring_entity_code: str, *, max_len: int = 12) -> str:
	"""Normalize procuring-entity text for ``TND-{ENTITY}-…`` (matches TM2 Tender allocation)."""
	raw = re.sub(r"[^0-9A-Za-z]+", "", cstr(procuring_entity_code).upper())
	return (raw[:max_len] if raw else "UNK")


def normalize_fiscal_year(value: Any) -> str:
	"""Normalize fiscal year for tender-code prefix (matches TM2 Tender)."""
	s = cstr(value).strip()
	if not s:
		return ""
	if s.endswith(".0") and s[:-2].isdigit():
		return s[:-2]
	return s


def tender_code_prefix(procuring_entity_code: str, fiscal_year: Any) -> str:
	"""Return ``TND-{ENTITY}-{FY}`` prefix (without the per-bench sequence suffix)."""
	fy = normalize_fiscal_year(fiscal_year)
	return f"TND-{entity_slug(procuring_entity_code)}-{fy}"


_TENDER_CODE_RE = re.compile(
	r"^TND-(?P<entity>[0-9A-Z]{1,12})-(?P<fy>\d{4})-(?P<seq>\d{4})$",
)


def parse_tender_code(tender_code: str) -> dict[str, str] | None:
	"""Parse a well-formed ``TND-…-####-####`` code; return ``None`` if shape is invalid."""
	m = _TENDER_CODE_RE.match(cstr(tender_code).strip())
	if not m:
		return None
	return {"entity": m.group("entity"), "fy": m.group("fy"), "seq": m.group("seq")}


def format_tsb(tender_code: str) -> str:
	return f"TSB-{cstr(tender_code).strip()}"


def format_ttl(tender_code: str) -> str:
	return f"TTL-{cstr(tender_code).strip()}"


def format_tac(tender_code: str) -> str:
	return f"TAC-{cstr(tender_code).strip()}"


def format_trd(tender_code: str, seq: int) -> str:
	return f"TRD-{cstr(tender_code).strip()}-{int(seq):03d}"


def format_pub(tender_code: str, seq: int) -> str:
	return f"PUB-{cstr(tender_code).strip()}-{int(seq):03d}"


def format_inv(tender_code: str, seq: int) -> str:
	return f"INV-{cstr(tender_code).strip()}-{int(seq):04d}"


def format_clr(tender_code: str, seq: int) -> str:
	return f"CLR-{cstr(tender_code).strip()}-{int(seq):04d}"


def format_clrr(clarification_code: str, seq: int) -> str:
	return f"CLRR-{cstr(clarification_code).strip()}-{int(seq):02d}"


def format_add(tender_code: str, seq: int) -> str:
	"""``ADD-{TENDER_CODE}-{##}`` — two-digit per doc 3 §3.1 / TM2-ID-006."""
	return f"ADD-{cstr(tender_code).strip()}-{int(seq):02d}"


def format_air(addendum_code: str) -> str:
	return f"AIR-{cstr(addendum_code).strip()}"


def format_ack(addendum_code: str, supplier_code: str) -> str:
	return f"ACK-{cstr(addendum_code).strip()}-{cstr(supplier_code).strip()}"


def format_bid(tender_code: str, supplier_code: str, seq: int) -> str:
	"""``BID-{TENDER}-{SUPPLIER}-{##}`` — **TM2-ID-007** two-digit sequence."""
	return f"BID-{cstr(tender_code).strip()}-{cstr(supplier_code).strip()}-{int(seq):02d}"


def format_rct(bid_code: str) -> str:
	return f"RCT-{cstr(bid_code).strip()}"


def format_late(tender_code: str, supplier_code: str, seq: int) -> str:
	return f"LATE-{cstr(tender_code).strip()}-{cstr(supplier_code).strip()}-{int(seq):02d}"


def format_cls(tender_code: str) -> str:
	return f"CLS-{cstr(tender_code).strip()}"


def format_orr(tender_code: str) -> str:
	return f"ORR-{cstr(tender_code).strip()}"


def format_ehr(tender_code: str) -> str:
	return f"EHR-{cstr(tender_code).strip()}"


def format_chr(tender_code: str) -> str:
	return f"CHR-{cstr(tender_code).strip()}"


def format_ntf(tender_code: str, seq: int) -> str:
	return f"NTF-{cstr(tender_code).strip()}-{int(seq):04d}"


def format_tae(tender_code: str, seq: int) -> str:
	return f"TAE-{cstr(tender_code).strip()}-{int(seq):04d}"


def assert_business_code_immutable(
	old_code: str,
	new_code: str,
	*,
	locked: bool,
	historical: bool = False,
) -> None:
	"""Raise ``ValueError`` if a business code would change on a locked or historical row (TM2-ID-008/009)."""
	if not locked and not historical:
		return
	if cstr(old_code).strip() == cstr(new_code).strip():
		return
	raise ValueError("Business code cannot change for published, submitted, or historical records (TM2-ID-008/009).")
