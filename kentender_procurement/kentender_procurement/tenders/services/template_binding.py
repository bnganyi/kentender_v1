# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.11 §4.1, §5.3 — bind a Tender to one installed STD release
and re-verify it at every later action, through the STD Templates owner's
published services (STD-TPL-IMP-001 v1.0 §9; owner decision OD5).

- A new Tender binds the one switched-on, intact, Available release of
  `IT-EQUIPMENT-OPEN-V1` (`TND_TEMPLATE_UNAVAILABLE` otherwise; nothing is
  created).
- Every later action re-verifies the release the Tender already bound: it
  may be Available (switched On or Off) or Superseded while its exact
  assets, digests and renderer adapter verify; Withdrawn blocks
  (`TND_TEMPLATE_RELEASE_WITHDRAWN`) and a failed check blocks
  (`TND_TEMPLATE_RELEASE_INTEGRITY_FAILED`).
- Nothing here ever rebinds a Tender to another release.
"""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.services import binding as std_binding
from kentender_procurement.std_templates.services import runtime as std_runtime
from kentender_procurement.tenders.services.errors import fail

TEMPLATE_KEY = "IT-EQUIPMENT-OPEN-V1"
STD_TEMPLATES_PAGE = "std-templates"
#: STD-TPL-001 v0.10 codes → the Tenders error each one surfaces as.
_CODE = {
	"STD_RELEASE_WITHDRAWN": "TND_TEMPLATE_RELEASE_WITHDRAWN",
	"STD_RELEASE_INTEGRITY_FAILED": "TND_TEMPLATE_RELEASE_INTEGRITY_FAILED",
	"STD_RENDERER_UNSUPPORTED": "TND_TEMPLATE_RELEASE_INTEGRITY_FAILED",
}
#: The bound-release facts a Tender and each of its Versions persist.
VERSION_FIELDS = (
	"template_release_id", "template_key", "template_release", "product_profile_id", "renderer_profile_id",
	"supported_renderer_version", "official_source_digest", "bundle_digest",
)


def _facts(facts: dict[str, Any]) -> dict[str, Any]:
	release = std_runtime.release_doc(facts["template_release_id"])
	from kentender_procurement.std_templates.services.installer import load_json

	use = load_json(release.supported_use_summary) or {}
	return {
		**{field: facts[field] for field in VERSION_FIELDS},
		"display_name": facts["display_name"],
		# Legacy display key the Start dialog reads.
		"template_version": facts["template_release"],
		"official_source_title": cstr(release.official_source_title),
		"supported_reservation_categories": list(use.get("reservation_categories") or ()),
		"lifecycle_status": facts["lifecycle_status"],
		"notice": facts.get("notice") or "",
		"std_template_route": [STD_TEMPLATES_PAGE, facts["template_release_id"]],
	}


def _session_route(release_id: str = "") -> list[str]:
	import frappe

	return inspection_route(cstr(frappe.session.user), release_id)


def _raise(exc: STDTemplateError, release_id: str = "") -> None:
	release_id = release_id or cstr(exc.identity)
	detail = {"reason": exc.message, "std_code": exc.code, "template_release_id": release_id, "std_template_route": _session_route(release_id)}
	fail(_CODE.get(exc.code, "TND_TEMPLATE_UNAVAILABLE"), detail=detail)


def bind() -> dict[str, Any]:
	"""The exact switched-on Available release a new Tender binds to. Raises
	`STDTemplateError` when there is none."""
	release = std_binding.available_release(TEMPLATE_KEY)
	return _facts(std_binding.require(release.name, "new_binding"))


def require_available() -> dict[str, Any]:
	"""`bind()` for StartTender: a missing or unusable release is
	`TND_TEMPLATE_UNAVAILABLE` and creates nothing."""
	try:
		return bind()
	except STDTemplateError as exc:
		fail("TND_TEMPLATE_UNAVAILABLE", detail={"reason": exc.message, "std_code": exc.code, "template_key": TEMPLATE_KEY, "std_template_route": _session_route()})
		return {}  # unreachable


def require_bound(record, purpose: str = "continue") -> dict[str, Any]:
	"""The release `record` (a Tender or Tender Version) already bound,
	re-verified for a later action. Never rebinds."""
	release_id = cstr(record.template_release_id)
	try:
		facts = std_binding.require(release_id, purpose)
	except STDTemplateError as exc:
		_raise(exc, release_id)
		return {}  # unreachable
	if facts["bundle_digest"] != cstr(record.bundle_digest) or facts["official_source_digest"] != cstr(record.official_source_digest):
		fail("TND_TEMPLATE_RELEASE_INTEGRITY_FAILED", detail={"reason": "The installed release no longer matches the digests this Tender bound.", "template_release_id": release_id, "std_template_route": _session_route(release_id)})
	return _facts(facts)


def verify(version, purpose: str = "continue") -> list[str]:
	"""Plain problems if the Version's bound release may not be used for
	`purpose` now; empty when it may."""
	try:
		require_bound(version, purpose)
	except Exception as exc:  # TendersError
		code = getattr(exc, "code", "")
		reason = (getattr(exc, "detail", None) or {}).get("reason") or str(exc)
		if code == "TND_TEMPLATE_RELEASE_WITHDRAWN":
			return ["This Tender cannot continue because its Tender format was withdrawn."]
		return [f"The Tender format bound to this Tender could not be verified: {reason}"]
	return []


def bound_categories(record) -> tuple[str, ...]:
	"""The reservation categories the bound release supports (no checks)."""
	from kentender_procurement.std_templates.services.installer import load_json

	try:
		release = std_runtime.release_doc(cstr(record.template_release_id))
	except STDTemplateError:
		return ()
	return tuple((load_json(release.supported_use_summary) or {}).get("reservation_categories") or ())


def bound_fields(facts: dict[str, Any]) -> dict[str, Any]:
	"""The exact facts a Tender and its Version persist at binding."""
	return {field: facts[field] for field in VERSION_FIELDS}


#: TPR-CHG-001 v0.11 §10.15 bound-release states: (tone, heading, text). The
#: published-Tender wording is the STD binding read notice (not in §10.15).
_NOTICE_UNPUBLISHED = {
	"Superseded": ("is-warning", "Tender format has a newer release", "This Tender remains on release {release}. You may continue only while its integrity checks pass; KenTender will not change the format automatically."),
	"Withdrawn": ("is-critical", "Tender format withdrawn", "This Tender cannot continue to publication because release {release} was withdrawn. Your work is preserved."),
	"Failed": ("is-critical", "Tender format could not be verified", "This Tender is preserved, but no further approval or publication action is permitted until the release owner resolves the verification failure."),
}
_NOTICE_PUBLISHED = {
	"Superseded": ("is-info", "Tender format has a newer release", "A newer release of this Tender format exists; this Tender keeps the release it was published with."),
	"Withdrawn": ("is-info", "Tender format withdrawn", "This Tender format was withdrawn after publication. The published documents and Bid definition are unchanged and remain the record."),
}


def release_notice(record, user: str) -> dict[str, Any] | None:
	"""The bound release's state as the Tender record shows it, or None when
	the release is simply usable. Reads the recorded lifecycle and last
	integrity result (no re-verification on read); never rebinds."""
	import frappe

	if not cstr(record.get("template_key")):
		return None
	row = frappe.db.get_value("Installed STD Release", cstr(record.get("template_release_id")), ["lifecycle_status", "integrity_status", "template_release"], as_dict=True)
	if not row:
		return None
	published = bool(record.get("published_at"))
	if row.lifecycle_status in ("Superseded", "Withdrawn"):
		state = row.lifecycle_status
	elif row.integrity_status == "Failed" and not published:
		state = "Failed"
	else:
		return None
	tone, heading, text = (_NOTICE_PUBLISHED if published else _NOTICE_UNPUBLISHED)[state]
	return {
		"state": state, "tone": tone, "heading": heading, "text": text.format(release=row.template_release),
		"std_template_route": inspection_route(user, cstr(record.get("template_release_id"))),
	}


def inspection_route(user: str, release_id: str = "") -> list[str]:
	"""TPR-CHG-001 v0.11 §8 **View STD Template**: only for a user STD
	Templates lets read (Administrator, System Manager, Procurement Officer,
	HOPF); everyone else gets no route. Without a bound release it opens the
	newest installed release of this Tender format, or the list."""
	import frappe

	from kentender_procurement.std_templates.services import access

	if not access.can_read(user):
		return []
	if not release_id:
		release_id = cstr(frappe.db.get_value("Installed STD Release", {"template_key": TEMPLATE_KEY}, "name", order_by="installed_at desc"))
	return [STD_TEMPLATES_PAGE, release_id] if release_id else [STD_TEMPLATES_PAGE]
