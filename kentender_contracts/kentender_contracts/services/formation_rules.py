# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The facts behind the formation rules (CM-CHG-001 v0.8 section 19.3 CM-R-01, 02, 03, 04, 17, 18; section 19.4 "Coverage result"; plan Phase 5, tracker CM8-509).

`rules/gate.py` answers whether a rule's *profile* is verified; this module answers whether the *facts* the rule is about are in order for one contract. Each finding is a hold with a stable key, the rule
it comes from, the person who can clear it and what clears it, so the person sending the agreement sees exactly what to fix and a hold on one dependent action stops nothing else. Nothing here is
a constant of law: every threshold comes from the contract's rule profile, and the signing window is what Award evidenced, never a date this module works out.

* R-01 the agreement is made with the successful tenderer the award names;
* R-02 the notification, its signing-window result and counting basis are present, the waiting period has ended, and the window has not;
* R-03 above the Attorney-General threshold a clearance is recorded before signature (unless the entity is one the section does not apply to);
* R-04 the eight minimum categories resolve and the addenda are listed explicitly (an empty list is explicit, not a missing document);
* R-17 a complex or specialised contract is outside this product;
* R-18 each commercial term is typed from the issued clauses; a missing term names the exact item and holds only the action that depends on it."""

from __future__ import annotations

from typing import Any

from frappe.utils import flt, get_datetime, getdate

HOLDER = "Head of procurement function"
SIMPLE = {"goods", "it goods", "simple goods", "non-complex goods", "supply of goods"}
#: entity types the Attorney-General clearance section does not apply to (section 19.3 CM-R-03: "Preserve the Parliament/Judiciary exception")
AG_EXEMPT = {"parliament", "judiciary"}
#: the eight minimum categories of section 19.4 and the source each resolves from
CATEGORIES = (("agreement", "S7"), ("tender_form", "S2"), ("price_schedule", "S3"), ("requirements_schedule", "S4"), ("technical_specifications", "S4"), ("gcc", "S5"), ("scc", "S5"),
	("award_notification", "S8"))


def _hold(key: str, rule: str, reason: str, clears: str, **extra: Any) -> dict[str, Any]:
	return {"hold": key, "kind": "Rule", "rule": rule, "reason": reason, "holder": HOLDER, "clears_with": clears, "consequence": "RequestContractSignatures", **extra}


def tenderer(package: dict[str, Any], terms: dict[str, Any]) -> list[dict[str, Any]]:
	"""CM-R-01: the supplier the award names is the supplier the agreement is made with."""
	named = (package.get("decision") or {}).get("organisation")
	made = ((terms.get("parties") or {}).get("supplier") or {}).get("organisation")
	if named and made and named != made:
		return [_hold("FORMATION_AUTHORITY", "CM-R-01", "The agreement names a different supplier from the one the award names.", "Award and the supplier's identity agree", awarded=named, agreement=made)]
	return []


def window(terms: dict[str, Any], now) -> list[dict[str, Any]]:
	"""CM-R-02: Award's evidenced notification and signing-window result, consumed and never recomputed. Missing or inconsistent means HOP resolves it with Award before sending."""
	signing = terms.get("signing_window") or {}
	notice, result = signing.get("notification") or {}, signing.get("signing_window") or {}
	if not (notice.get("id") and notice.get("given_at") and result.get("result") and result.get("counting_basis")):
		return [_hold("SIGNING_WINDOW_UNESTABLISHED", "CM-R-02", "Award has not supplied the evidenced notification and signing-window result.", "Award supplies the notification and the signing-window result with its counting basis")]
	found = []
	earliest = result.get("earliest_signing_at")
	if earliest and get_datetime(now) < get_datetime(earliest):
		found.append(_hold("SIGNING_WINDOW_UNESTABLISHED", "CM-R-02", "The waiting period after the notification has not ended.", "The waiting period Award evidenced ends", earliest=str(earliest)))
	if result.get("ends_on") and getdate(result["ends_on"]) < getdate(now):
		found.append(_hold("SIGNING_WINDOW_UNESTABLISHED", "CM-R-02", "The signing window for this award has ended.", "Award extends the window or the contract does not proceed", ended_on=str(result["ends_on"])))
	return found


def clearance_required(terms: dict[str, Any], threshold: float) -> bool:
	entity_type = str(((terms.get("parties") or {}).get("entity") or {}).get("entity_type") or "").strip().lower()
	return flt(terms.get("total")) > flt(threshold) and entity_type not in AG_EXEMPT


def clearance(terms: dict[str, Any], threshold: float) -> list[dict[str, Any]]:
	"""CM-R-03: value above the threshold needs the Attorney-General's clearance recorded before signature."""
	if clearance_required(terms, threshold) and not (terms.get("particulars") or {}).get("ag_clearance"):
		return [_hold("AG_CLEARANCE_REQUIRED", "CM-R-03", "The contract value needs the Attorney-General's clearance before signature.", "The clearance reference is recorded", total=flt(terms.get("total")))]
	return []


def coverage(sources: dict[str, Any], addenda: Any) -> list[dict[str, Any]]:
	"""CM-R-04: every minimum category resolves to a verified source with content, and the addenda are listed (an empty list is stated, not a document)."""
	found = []
	absent = [name for name, number in CATEGORIES if not sources.get(number) or sources[number].get("data") in (None, "", {}, [])]
	if absent:
		found.append(_hold("PACKAGE_INCOMPLETE", "CM-R-04", "The incorporated package does not cover every minimum category.", "Each category resolves to its issued document", categories=absent))
	if not isinstance(addenda, list):
		found.append(_hold("PACKAGE_INCOMPLETE", "CM-R-04", "The issued tender does not say whether it has addenda.", "The issued tender lists its addenda, an empty list if there are none"))
	return found


def terms_typed(terms: dict[str, Any]) -> list[dict[str, Any]]:
	"""CM-R-18: each commercial term is a typed value from the issued clauses. A gap names the exact term and holds only the action that depends on it."""
	gaps = []
	if not (terms.get("delivery") or {}).get("due"):
		gaps.append("the delivery date")
	warranty = terms.get("warranty") or {}
	if not warranty.get("months"):
		gaps.append("the warranty period")
	payment = terms.get("payment") or {}
	if not (payment.get("terms") or payment.get("days") or payment.get("basis")):
		gaps.append("the payment terms")
	if "required" not in (terms.get("security") or {}):
		gaps.append("whether a performance security is required")
	if "allowed" not in (terms.get("advance") or {}):
		gaps.append("whether an advance is allowed")
	return [_hold("TERM_MAPPING_MISSING", "CM-R-18", f"The issued terms do not give {item} as a value.", "The term is mapped from the issued conditions", term=item) for item in gaps]


def scope(package: dict[str, Any], sources: dict[str, Any] | None = None) -> str:
	"""CM-R-17: the classification Award or the issued tender states, or "" when neither does."""
	stated = package.get("procurement_category") or package.get("classification")
	if not stated and sources and sources.get("S1"):
		stated = (sources["S1"].get("data") or {}).get("procurement_category")
	return str(stated or "").strip()


def in_scope(classification: str) -> bool:
	return not classification or classification.lower() in SIMPLE


def sending(package: dict[str, Any], terms: dict[str, Any], sources: dict[str, Any], now, threshold: float) -> list[dict[str, Any]]:
	"""Every finding that stops the agreement being sent, together."""
	addenda = (sources.get("S1", {}).get("data") or {}).get("addenda")
	return [*tenderer(package, terms), *window(terms, now), *clearance(terms, threshold), *coverage(sources, addenda), *terms_typed(terms)]


def at_commit(terms: dict[str, Any], now) -> list[dict[str, Any]]:
	"""The checks repeated at each signature commit: the window may have closed since the request was sent (section 5.3)."""
	return window(terms, now)
