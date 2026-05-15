# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §8.2 / §8.4 — TM2 STD adapter entrypoints (stub-aligned).

``get_eligible_std_templates`` is implemented via planning handoff
:class:`~kentender_procurement.tender_management.services.std_template_handoff_resolution.HandoffStdResolution`
(the same deterministic resolution path as B3/B6 release). When the full STD
Engine is wired, replace the internals here without changing the public
function signatures expected by §9.1 / P3-01 / **P3-02** / **P3-03** / **P3-04** (``get_current_*``)
/ **P3-05** (``create_or_get_publication_snapshot``) / **P3-06** (addendum impact + regenerate) / **P3-07** (§8.3 return contract).

**§8.4 stub (P3-08):** canonical Works open-tender **codes** and §8.3-shaped ``output_refs_v83`` live in
``tender_management/fixtures/tm2_seed_works_open_tender.json`` and are loaded by
:mod:`kentender_procurement.tender_management.services.tm2_stub_seed` for CI/tests **without**
assuming a full STD engine or N-pack DB seed. Runtime adapter paths still read Frappe rows.
"""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	check_std_template_tender_creation_eligibility,
)
from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	HandoffStdPath,
	resolve_std_template_for_handoff,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_CREATED
from kentender_procurement.tender_management.std_instance.addendum import StdAddendumImpactService
from kentender_procurement.tender_management.std_instance.downstream import try_resolve_current_output
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService


def load_procurement_package_by_code(package_code: str) -> Document | None:
	pc = (package_code or "").strip()
	if not pc:
		return None
	if frappe.db.exists("Procurement Package", pc):
		return frappe.get_doc("Procurement Package", pc)
	name = frappe.db.get_value("Procurement Package", {"package_code": pc}, "name")
	if name and frappe.db.exists("Procurement Package", name):
		return frappe.get_doc("Procurement Package", name)
	return None


def _std_template_discovery_dict(std_name: str, resolution_path: HandoffStdPath | str) -> dict[str, Any]:
	row = frappe.db.get_value(
		"STD Template",
		std_name,
		["template_code", "template_name", "lifecycle_status"],
		as_dict=True,
	) or {}
	return {
		"std_template": std_name,
		"template_code": cstr(row.get("template_code") or "").strip(),
		"template_name": cstr(row.get("template_name") or "").strip(),
		"lifecycle_status": cstr(row.get("lifecycle_status") or "").strip(),
		"resolution_path": str(resolution_path),
	}


def get_eligible_std_templates(package_code: str) -> list[dict[str, Any]]:
	"""Doc 9 §8.2 — eligible ``STD Template`` rows for ``package_code`` (handoff / stub path).

	Each dict includes ``std_template`` (row name), ``template_code``, ``template_name``,
	``lifecycle_status``, and ``resolution_path`` (same labels as
	:class:`~kentender_procurement.tender_management.services.std_template_handoff_resolution.HandoffStdResolution`).

	Returns **zero** rows when the package is unknown or handoff is **unresolved** /
	**invalid_default**. Returns **one** row for **default_std_template**, **mapping_service**,
	or **works_poc_fallback**. Returns **all** mapping candidates when the handoff path is
	**ambiguous** (doc 2 sec. 12.1).

	Stub limitation: discovery is driven by planning handoff resolution, not the full STD
	engine catalogue (§8.4). Preserve this signature when wiring P3-02+.
	"""
	pc = cstr(package_code or "").strip()
	if not pc:
		return []
	pkg = load_procurement_package_by_code(pc)
	if not pkg:
		return []
	res = resolve_std_template_for_handoff(pkg)
	if res.is_ambiguous:
		return [_std_template_discovery_dict(n, "ambiguous") for n in res.ambiguous_candidates]
	if not res.std_name:
		return []
	return [_std_template_discovery_dict(res.std_name, res.path)]


def getEligibleStdTemplates(package_code: str) -> list[dict[str, Any]]:
	"""CamelCase alias for :func:`get_eligible_std_templates`."""
	return get_eligible_std_templates(package_code)


def _resolve_tm2_name_from_tender_code(tender_code: str) -> str | None:
	tc = (tender_code or "").strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name:
		return name
	if frappe.db.exists("TM2 Tender", tc):
		return tc
	return None


def resolve_std_template_for_version_profile(
	std_template_version_code: str,
	applicability_profile_code: str,
) -> str | None:
	"""Return ``STD Template`` row name when version + applicability profile match uniquely."""
	v = (std_template_version_code or "").strip()
	p = (applicability_profile_code or "").strip().lower()
	if not v or not p:
		return None
	candidates = frappe.get_all("STD Template", filters={"template_version": v}, pluck="name")
	out: list[str] = []
	for name in candidates:
		try:
			ev, ep = TenderStdBindingService._codes_from_std_template(name)
		except Exception:
			continue
		if ev.strip() == v and ep.strip().lower() == p:
			out.append(name)
	if len(out) == 1:
		return out[0]
	if len(out) > 1:
		# Several STD rows can share the same ``template_version`` + profile (e.g. copies).
		# Deterministic pick so §8.2 ``create_tender_std_instance`` does not fail closed.
		out.sort()
		return out[0]
	return None


def _eligibility_context_from_tm2(tm2: Document, std_template_name: str) -> dict[str, Any]:
	"""Build §7 / governance eligibility context aligned to the **STD Template** row."""
	raw = (frappe.db.get_value("STD Template", std_template_name, "procurement_category") or "WORKS").strip()
	u = raw.upper().replace(" ", "_")
	if "WORK" in u:
		u = "WORKS"
	ctx: dict[str, Any] = {
		"emit_usage_blocked_event": False,
		"procurement_category": u,
		"template_code": std_template_name,
	}
	tf = (frappe.db.get_value("STD Template", std_template_name, "template_family") or "").strip()
	if tf:
		ctx["template_family"] = tf
	return ctx


def _tm2_to_instance_procurement_method(tm2: Document) -> str:
	pm = (tm2.get("procurement_method") or "").strip()
	if pm == "Restricted Tender":
		return "RESTRICTED_COMPETITIVE_TENDERING"
	return "OPEN_COMPETITIVE_TENDERING"


def create_tender_std_instance(
	tender_code: str,
	std_template_version_code: str,
	profile_code: str,
) -> dict[str, Any]:
	"""Doc 9 §8.2 / §9.2 step 3 — create ``Tender STD Instance`` for a **TM2 Tender**.

	Caller must already have enforced §7.3 (e.g. ``TND2_BIND_STD``). This function
	performs template eligibility, duplicate-instance guard, insert, and
	``EVT_STDINST_CREATED`` audit emission.

	Tests: ``tender_management.tests.test_p3_02_create_tender_std_instance`` (P3-02);
	``bind_tender_std_instance`` integration (P4-02).
	"""
	tc = (tender_code or "").strip()
	vcode = (std_template_version_code or "").strip()
	pcode = (profile_code or "").strip()
	if not tc or not vcode or not pcode:
		return {
			"ok": False,
			"denial_code": DenialCode.STD_AUTH_TENDER_CONTEXT_REQUIRED.value,
			"message": _("Tender code, template version code, and profile code are required."),
		}

	tm2_name = _resolve_tm2_name_from_tender_code(tc)
	if not tm2_name:
		return {
			"ok": False,
			"denial_code": DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			"message": _("TM2 Tender {0} was not found.").format(tc),
		}

	tm2 = frappe.get_doc("TM2 Tender", tm2_name)
	std_name = resolve_std_template_for_version_profile(vcode, pcode)
	if not std_name:
		return {
			"ok": False,
			"denial_code": DenialCode.STD_TEMPLATE_INCOMPATIBLE.value,
			"message": _("No STD Template matches the given version and applicability profile."),
		}

	exp_v, exp_p = TenderStdBindingService._codes_from_std_template(std_name)
	if exp_v.strip() != vcode or exp_p.strip().lower() != pcode.lower():
		return {
			"ok": False,
			"denial_code": DenialCode.STD_TEMPLATE_INCOMPATIBLE.value,
			"message": _("STD template version or profile does not match the resolved template."),
		}

	if TenderStdBindingService.get_current_std_instance_for_tm2_tender(tm2_name):
		return {
			"ok": False,
			"denial_code": DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			"message": _("An active Tender STD Instance already exists for this TM2 tender."),
		}

	ctx = _eligibility_context_from_tm2(tm2, std_name)
	elig = check_std_template_tender_creation_eligibility(std_name, ctx)
	if not elig.get("eligible"):
		reasons = list(elig.get("reasons") or [])
		return {
			"ok": False,
			"denial_code": DenialCode.STD_TEMPLATE_NOT_ACTIVE.value,
			"message": _("STD Template is not eligible for instance creation: {0}").format(
				", ".join(reasons) or (elig.get("lifecycle_status") or "")
			),
			"eligibility": elig,
		}

	cat_map = {
		"Works": "WORKS",
		"Goods": "GOODS",
		"Services": "SERVICES",
		"Consultancy": "CONSULTING",
	}
	std_pc = cat_map.get((tm2.get("procurement_category") or "").strip(), "WORKS")

	si = frappe.new_doc("Tender STD Instance")
	si.tm2_tender = tm2_name
	pp = (tm2.get("procurement_package") or "").strip()
	if pp:
		si.procurement_package = pp
	si.template_version_code = vcode
	si.applicability_profile_code = pcode
	si.procurement_category = std_pc
	si.procurement_method = _tm2_to_instance_procurement_method(tm2)
	si.instance_status = "Draft"
	si.readiness_status = "Not Ready"
	si.created_from_tender_context = 1
	try:
		si.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		return {
			"ok": False,
			"denial_code": DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value,
			"message": _("Duplicate Tender STD Instance."),
		}

	emit_std_instance_event(
		EVT_STDINST_CREATED,
		instance_code=si.name,
		details={
			"tm2_tender": tm2_name,
			"tender_code": tm2.tender_code,
			"std_template": std_name,
			"template_version_code": vcode,
			"applicability_profile_code": pcode,
		},
	)
	return {
		"ok": True,
		"tender_std_instance": si.name,
		"tender_std_instance_code": si.name,
		"std_template": std_name,
	}


def createTenderStdInstance(
	tender_code: str,
	std_template_version_code: str,
	profile_code: str,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`create_tender_std_instance`."""
	return create_tender_std_instance(tender_code, std_template_version_code, profile_code)


def _readiness_output_flags_from_eval(eval_out: dict[str, Any]) -> dict[str, bool]:
	codes = {str(b.get("code") or "") for b in (eval_out.get("blockers") or [])}
	has_stale = "STALE_OUTPUTS_PRESENT" in codes

	def _ok(missing_code: str) -> bool:
		if missing_code in codes:
			return False
		if has_stale:
			return False
		return True

	return {
		"bundle_current": _ok("BUNDLE_MISSING"),
		"dsm_current": _ok("DSM_MISSING"),
		"dom_current": _ok("DOM_MISSING"),
		"dem_current": _ok("DEM_MISSING"),
		"dcm_current": _ok("DCM_MISSING"),
	}


def validate_tender_std_readiness(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — evaluate ``Tender STD Instance`` publication readiness (blockers + output flags).

	Delegates to :meth:`StdInstanceReadinessService.evaluate` with ``persist=True``,
	``emit_audit=False``, ``skip_sec_enforcement=True`` (TM2 orchestration owns §7.3).

	**Response contract**

	- ``ok``: ``False`` only when the instance row is missing or ``tender_std_instance_code`` is empty;
	  otherwise ``True`` (evaluation ran). A **Blocked** readiness still returns ``ok: True``;
	  use ``status == \"Ready\"`` for the strict ready gate.
	- ``status``: ``Ready`` or ``Blocked`` (from evaluator).
	- ``blockers``: ordered list of ``{\"code\": str, \"message\": str}`` (see ``BLOCKER_ORDER`` in
	  :mod:`kentender_procurement.tender_management.std_instance.readiness`).
	- ``warnings``: list (often empty).
	- ``instance``: resolved instance name.
	- ``bundle_current``, ``dsm_current``, ``dom_current``, ``dem_current``, ``dcm_current``: booleans
	  derived from blocker codes and stale-output rules.

	Tests: ``tender_management.tests.test_p3_03_validate_tender_std_readiness``; see also
	``run_publication_readiness`` (P4-03).
	"""
	ic = cstr(tender_std_instance_code or "").strip()
	if not ic or not frappe.db.exists("Tender STD Instance", ic):
		return {
			"ok": False,
			"status": "Blocked",
			"blockers": [{"code": "INSTANCE_NOT_FOUND", "message": _("Tender STD Instance not found.")}],
			"warnings": [],
			"instance": ic,
			"bundle_current": False,
			"dsm_current": False,
			"dom_current": False,
			"dem_current": False,
			"dcm_current": False,
		}
	out = StdInstanceReadinessService.evaluate(
		ic,
		persist=True,
		emit_audit=False,
		skip_sec_enforcement=True,
	)
	flags = _readiness_output_flags_from_eval(out)
	return {
		"ok": True,
		"status": out.get("status"),
		"blockers": out.get("blockers") or [],
		"warnings": out.get("warnings") or [],
		"instance": ic,
		**flags,
	}


def validateTenderStdReadiness(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`validate_tender_std_readiness`."""
	return validate_tender_std_readiness(tender_std_instance_code)


def _adapter_try_current_output(tender_std_instance_code: str, output_type: str) -> dict[str, Any]:
	"""§8.2 — delegate to :func:`try_resolve_current_output` (no auth; TM2 layer owns §7.3)."""
	return try_resolve_current_output(cstr(tender_std_instance_code or "").strip(), output_type)


def get_current_bundle(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — current Bundle generated output for ``tender_std_instance_code``."""
	return _adapter_try_current_output(tender_std_instance_code, "Bundle")


def get_current_dsm(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — current DSM generated output."""
	return _adapter_try_current_output(tender_std_instance_code, "DSM")


def get_current_dom(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — current DOM generated output."""
	return _adapter_try_current_output(tender_std_instance_code, "DOM")


def get_current_dem(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — current DEM generated output."""
	return _adapter_try_current_output(tender_std_instance_code, "DEM")


def get_current_dcm(tender_std_instance_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — current DCM generated output."""
	return _adapter_try_current_output(tender_std_instance_code, "DCM")


def getCurrentBundle(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_current_bundle`."""
	return get_current_bundle(tender_std_instance_code)


def getCurrentDsm(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_current_dsm`."""
	return get_current_dsm(tender_std_instance_code)


def getCurrentDom(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_current_dom`."""
	return get_current_dom(tender_std_instance_code)


def getCurrentDem(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_current_dem`."""
	return get_current_dem(tender_std_instance_code)


def getCurrentDcm(tender_std_instance_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_current_dcm`."""
	return get_current_dcm(tender_std_instance_code)


_SNAPSHOT_OUTPUT_REF_KEYS: tuple[str, ...] = (
	"bundle_output_code",
	"dsm_output_code",
	"dom_output_code",
	"dem_output_code",
	"dcm_output_code",
)


def _normalize_snapshot_output_refs(output_refs: Any) -> dict[str, str]:
	"""Return non-empty string values for known §8.3 output ref keys only."""
	if output_refs is None or not isinstance(output_refs, dict):
		return {}
	known = frozenset(_SNAPSHOT_OUTPUT_REF_KEYS)
	out: dict[str, str] = {}
	for k, v in output_refs.items():
		if not isinstance(k, str):
			continue
		kn = k.strip()
		if kn not in known:
			continue
		val = cstr(v or "").strip()
		if val:
			out[kn] = val
	return out


def _generated_output_hash_for_name(output_name: str) -> str:
	if not output_name or not frappe.db.exists("Tender STD Generated Output", output_name):
		return ""
	return cstr(frappe.db.get_value("Tender STD Generated Output", output_name, "output_hash") or "").strip()


def _compute_publication_snapshot_binding_hash(
	tender_code: str,
	bc: str,
	h_b: str,
	dsm: str,
	h_dsm: str,
	dom: str,
	h_dom: str,
	dem: str,
	h_dem: str,
	dcm: str,
	h_dcm: str,
) -> str:
	"""Deterministic SHA-256 over tender code + ordered output codes and row hashes (doc 9 §8.3)."""
	body = "|".join(
		[
			tender_code,
			"Bundle",
			bc,
			h_b,
			"DSM",
			dsm,
			h_dsm,
			"DOM",
			dom,
			h_dom,
			"DEM",
			dem,
			h_dem,
			"DCM",
			dcm,
			h_dcm,
		]
	)
	return hashlib.sha256(body.encode("utf-8")).hexdigest()


# --- Doc 9 §8.3 — canonical adapter output-reference return contract (P3-07) ----

STD_ADAPTER_OUTPUT_REFS_V83_KEYS: tuple[str, ...] = (
	"bundle_output_code",
	"dsm_output_code",
	"dom_output_code",
	"dem_output_code",
	"dcm_output_code",
	"publication_snapshot_code",
	"snapshot_hash",
	"status",
)


def extract_std_output_refs_contract_v83(snap: dict[str, Any]) -> dict[str, str]:
	"""Return **only** the eight doc 9 §8.3 keys from a **successful** snapshot-style payload.

	:param snap: Must be a dict with ``ok: True`` and the §8.3 fields (e.g. from
		:func:`create_or_get_publication_snapshot`).
	"""
	if not snap.get("ok"):
		frappe.throw(
			_("Cannot extract §8.3 output refs unless the snapshot payload is successful."),
			title=_("STD Adapter"),
		)
	out: dict[str, str] = {}
	for k in STD_ADAPTER_OUTPUT_REFS_V83_KEYS:
		if k == "status":
			out[k] = cstr(snap.get("status") or "").strip() or "CURRENT"
		else:
			out[k] = cstr(snap.get(k) or "").strip()
	return out


def get_tender_std_output_refs(tender_code: str) -> dict[str, Any]:
	"""Doc 9 §8.3 — canonical output-reference object for ``tender_code`` (tender-scoped).

	On success returns ``{"ok": True, **v83}`` where ``v83`` has **exactly** the eight keys from
	doc 9 §8.3. On failure forwards the denial envelope from :func:`create_or_get_publication_snapshot`.
	"""
	snap = create_or_get_publication_snapshot(tender_code, {})
	if not snap.get("ok"):
		return dict(snap)
	v83 = extract_std_output_refs_contract_v83(snap)
	return {"ok": True, **v83}


def getTenderStdOutputRefs(tender_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`get_tender_std_output_refs`."""
	return get_tender_std_output_refs(tender_code)


def create_or_get_publication_snapshot(tender_code: str, output_refs: Any = None) -> dict[str, Any]:
	"""Doc 9 §8.2 / §8.3 — resolve or validate publication snapshot binding for ``tender_code``.

	``output_refs`` may include a subset of ``bundle_output_code`` … ``dcm_output_code``; each
	non-empty value must equal the active ``Tender STD Instance`` current pointer or the call
	returns ``AUTH_CONTEXT_DENIED``.

	On success returns ``publication_snapshot_code`` (stable ``PUBSNAP-{tender_code}-TM2``),
	``snapshot_hash`` (64-char hex fingerprint of bound output codes + ``output_hash`` values),
	``status`` ``CURRENT``, and per-output hashes when ``Tender STD Generated Output`` rows exist.

	Stub limitation (§8.4): snapshot is not persisted as a ``Tender Publication Snapshot`` row here;
	that remains the §9.6 publish path. Hashing uses DB-backed ``output_hash`` when present.
	"""
	tc = (tender_code or "").strip()
	if not tc:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": _("Tender code is required."),
		}
	tm2_name = _resolve_tm2_name_from_tender_code(tc)
	if not tm2_name:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": _("TM2 Tender {0} was not found.").format(tc),
		}

	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		fields=["name", "tender_std_instance"],
		limit=1,
	)
	if not rows:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": _("No active TM2 Tender STD Binding exists for this tender."),
		}

	si = cstr(rows[0].tender_std_instance or "").strip()
	if not si or not frappe.db.exists("Tender STD Instance", si):
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": _("Active binding has no Tender STD Instance."),
		}

	row = (
		frappe.db.get_value(
			"Tender STD Instance",
			si,
			[
				"name",
				"current_bundle_output_code",
				"current_dsm_output_code",
				"current_dom_output_code",
				"current_dem_output_code",
				"current_dcm_output_code",
			],
			as_dict=True,
		)
		or {}
	)

	def _code(field: str) -> str:
		return cstr(row.get(field) or "").strip()

	bc, dsm, dom, dem, dcm = (
		_code("current_bundle_output_code"),
		_code("current_dsm_output_code"),
		_code("current_dom_output_code"),
		_code("current_dem_output_code"),
		_code("current_dcm_output_code"),
	)
	missing: list[str] = []
	if not bc:
		missing.append("current_bundle_output_code")
	if not dsm:
		missing.append("current_dsm_output_code")
	if not dom:
		missing.append("current_dom_output_code")
	if not dem:
		missing.append("current_dem_output_code")
	if not dcm:
		missing.append("current_dcm_output_code")
	if missing:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value,
			"message": _("Publication snapshot cannot be built: missing STD output references."),
			"missing_fields": missing,
			"tender_std_instance": si,
		}

	resolved_by_key = {
		"bundle_output_code": bc,
		"dsm_output_code": dsm,
		"dom_output_code": dom,
		"dem_output_code": dem,
		"dcm_output_code": dcm,
	}
	refs_norm = _normalize_snapshot_output_refs(output_refs)
	for key, val in refs_norm.items():
		if val != resolved_by_key.get(key):
			return {
				"ok": False,
				"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
				"message": _("Publication snapshot output refs do not match the active STD instance bindings."),
				"mismatched_field": key,
				"tender_std_instance": si,
			}

	h_b = _generated_output_hash_for_name(bc)
	h_dsm = _generated_output_hash_for_name(dsm)
	h_dom = _generated_output_hash_for_name(dom)
	h_dem = _generated_output_hash_for_name(dem)
	h_dcm = _generated_output_hash_for_name(dcm)

	snapshot_hash = _compute_publication_snapshot_binding_hash(
		tc, bc, h_b, dsm, h_dsm, dom, h_dom, dem, h_dem, dcm, h_dcm
	)
	pub_snap = f"PUBSNAP-{tc}-TM2"
	base: dict[str, Any] = {
		"ok": True,
		"status": "CURRENT",
		"tender_std_instance": si,
		"tm2_tender_std_binding": cstr(rows[0].name).strip(),
		"publication_snapshot_code": pub_snap,
		"snapshot_hash": snapshot_hash,
		"bundle_output_code": bc,
		"bundle_output_hash": h_b,
		"dsm_output_code": dsm,
		"dsm_output_hash": h_dsm,
		"dom_output_code": dom,
		"dom_output_hash": h_dom,
		"dem_output_code": dem,
		"dem_output_hash": h_dem,
		"dcm_output_code": dcm,
		"dcm_output_hash": h_dcm,
	}
	base["output_refs_contract_v83"] = extract_std_output_refs_contract_v83(base)
	return base


def create_or_get_publication_snapshot_for_tm2(tender_code: str) -> dict[str, Any]:
	"""Same as :func:`create_or_get_publication_snapshot` with empty ``output_refs`` (§9.6)."""
	return create_or_get_publication_snapshot(tender_code, {})


def createOrGetPublicationSnapshot(tender_code: str, output_refs: Any = None) -> dict[str, Any]:
	"""CamelCase alias for :func:`create_or_get_publication_snapshot`."""
	return create_or_get_publication_snapshot(tender_code, output_refs)


# --- P3-06 — doc 9 §8.2 addendum impact + regeneration (stub; §8.4) -----------------

_ADDENDUM_CT_CACHE_KEY = "tm2_std_adapter:addendum_change_types:{0}"
_ADDENDUM_CT_TTL_SEC = 86_400

_PRIMARY_IMPACT_TO_CHANGE_TYPES: dict[str, tuple[str, ...]] = {
	"No Structural Impact": (),
	"Parameter Change": ("specification_attachment",),
	"Deadline Change": ("submission_deadline",),
	"Works Requirement Change": ("specification_attachment",),
	"BOQ Change": ("boq_quantity",),
	"Submission Model Change": ("submission_deadline",),
	"Opening Model Change": ("submission_deadline",),
	"Evaluation Model Change": ("evaluation_criteria",),
	"Contract Carry-Forward Change": ("contract_condition",),
	"Cancellation / Reissue Required": ("specification_attachment",),
}

_OUTPUT_PAIR_META: tuple[tuple[str, str, str], ...] = (
	("bundle", "current_bundle_output_code", "Bundle"),
	("dsm", "current_dsm_output_code", "DSM"),
	("dom", "current_dom_output_code", "DOM"),
	("dem", "current_dem_output_code", "DEM"),
	("dcm", "current_dcm_output_code", "DCM"),
)


def _cache_remember_addendum_change_types(addendum_code: str, change_types: list[str]) -> None:
	frappe.cache().set_value(
		_ADDENDUM_CT_CACHE_KEY.format(addendum_code),
		list(change_types),
		expires_in_sec=_ADDENDUM_CT_TTL_SEC,
	)


def _cache_recall_addendum_change_types(addendum_code: str) -> list[str] | None:
	raw = frappe.cache().get_value(_ADDENDUM_CT_CACHE_KEY.format(addendum_code))
	if not raw:
		return None
	return [cstr(x).strip() for x in raw if cstr(x).strip()]


def _cache_clear_addendum_change_types(addendum_code: str) -> None:
	frappe.cache().delete_value(_ADDENDUM_CT_CACHE_KEY.format(addendum_code))


def _get_tm2_addendum_doc(addendum_code: str) -> Document | None:
	ac = (addendum_code or "").strip()
	if not ac:
		return None
	name = frappe.db.get_value("TM2 Addendum", {"addendum_code": ac}, "name")
	if not name:
		return None
	return frappe.get_doc("TM2 Addendum", name)


def _active_tender_code_and_si(tm2_tender_name: str) -> tuple[str, str] | None:
	rows = frappe.get_all(
		"TM2 Tender STD Binding",
		filters={
			"tm2_tender": tm2_tender_name,
			"is_active": 1,
			"binding_status": ["not in", ["Cancelled", "Superseded"]],
		},
		fields=["name", "tender_std_instance"],
		limit=1,
	)
	if not rows:
		return None
	si = cstr(rows[0].tender_std_instance or "").strip()
	if not si or not frappe.db.exists("Tender STD Instance", si):
		return None
	tc = cstr(frappe.db.get_value("TM2 Tender", tm2_tender_name, "tender_code") or "").strip()
	if not tc:
		return None
	return (tc, si)


def _change_types_from_proposed_or_addendum(
	add_doc: Document,
	proposed_changes: Any,
) -> list[str]:
	pc = proposed_changes if isinstance(proposed_changes, dict) else {}
	raw_ct = pc.get("change_types")
	if isinstance(raw_ct, (list, tuple)):
		out = [cstr(x).strip() for x in raw_ct if cstr(x).strip()]
		if out:
			return out
	if isinstance(raw_ct, str) and raw_ct.strip():
		return [x.strip() for x in raw_ct.split(",") if x.strip()]

	pit = cstr(add_doc.get("primary_impact_type") or "").strip()
	return list(_PRIMARY_IMPACT_TO_CHANGE_TYPES.get(pit, ()))


def _si_row_output_bundle(si_name: str) -> dict[str, Any]:
	return (
		frappe.db.get_value(
			"Tender STD Instance",
			si_name,
			[
				"name",
				"current_bundle_output_code",
				"current_dsm_output_code",
				"current_dom_output_code",
				"current_dem_output_code",
				"current_dcm_output_code",
			],
			as_dict=True,
		)
		or {}
	)


def _output_prev_rev_fields(si_row: dict[str, Any], affected: frozenset[str], addendum_code: str) -> dict[str, str]:
	out: dict[str, str] = {}
	for short, field, label in _OUTPUT_PAIR_META:
		prev_v = cstr(si_row.get(field) or "").strip()
		out[f"previous_{short}_output_code"] = prev_v
		if label in affected:
			out[f"revised_{short}_output_code"] = f"REV-PENDING-{addendum_code}-{label}"
		else:
			out[f"revised_{short}_output_code"] = prev_v
	return out


def _publication_snapshot_prev_rev(
	tender_code: str,
	affected: frozenset[str],
	addendum_code: str,
) -> dict[str, Any]:
	snap = create_or_get_publication_snapshot(tender_code, {})
	if not snap.get("ok"):
		return {
			"previous_publication_snapshot_code": "",
			"revised_publication_snapshot_code": "",
			"previous_snapshot_hash": "",
			"revised_snapshot_hash": "",
		}
	prev_c = cstr(snap.get("publication_snapshot_code") or "").strip()
	prev_h = cstr(snap.get("snapshot_hash") or "").strip()
	if affected:
		rev_c = f"{prev_c}-REV-STUB-{addendum_code}"
		rev_h = ""
	else:
		rev_c = prev_c
		rev_h = prev_h
	return {
		"previous_publication_snapshot_code": prev_c,
		"revised_publication_snapshot_code": rev_c,
		"previous_snapshot_hash": prev_h,
		"revised_snapshot_hash": rev_h,
	}


def analyze_addendum_impact(addendum_code: str, proposed_changes: Any) -> dict[str, Any]:
	"""Doc 9 §8.2 / §10.4 — impact analysis for ``addendum_code`` + ``proposed_changes`` (stub).

	Returns previous vs revised output reference keys expected on **TM2 Addendum Impact Record**
	(doc 9 §10.4). ``revised_*`` for affected outputs are **REV-PENDING-…** placeholders until
	:func:`regenerate_outputs_for_addendum` runs.

	``proposed_changes`` may include ``change_types`` (``list[str]`` or comma-separated ``str``);
	otherwise ``primary_impact_type`` on **TM2 Addendum** maps to
	:class:`~kentender_procurement.tender_management.std_instance.addendum.StdAddendumImpactService`
	change types. Resolved ``change_types`` are cached 24h for the matching regenerate call.

	Stub (§8.4): uses ``StdAddendumImpactService`` + SI pointers; no TM2 AIR row insert here.
	"""
	ac = (addendum_code or "").strip()
	if not ac:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("Addendum code is required."),
		}
	ad = _get_tm2_addendum_doc(ac)
	if not ad:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("TM2 Addendum {0} was not found.").format(ac),
		}
	tpair = _active_tender_code_and_si(ad.tm2_tender)
	if not tpair:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("No active TM2 Tender STD Binding for this addendum."),
			"addendum_code": ac,
		}
	tc, si = tpair
	change_types = _change_types_from_proposed_or_addendum(ad, proposed_changes)
	_cache_remember_addendum_change_types(ac, change_types)

	try:
		impact = StdAddendumImpactService.analyse_impact(
			si,
			change_types,
			source_addendum_code=ac,
		)
	except frappe.ValidationError as exc:
		_cache_clear_addendum_change_types(ac)
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": cstr(exc),
			"addendum_code": ac,
		}

	affected = frozenset(str(x) for x in (impact.get("affected_outputs") or []) if x)
	si_row = _si_row_output_bundle(si)
	out_refs = _output_prev_rev_fields(si_row, affected, ac)
	pub_refs = _publication_snapshot_prev_rev(tc, affected, ac)

	output_refs_contract_v83: dict[str, str] | None = None
	if all(cstr(si_row.get(field) or "").strip() for _short, field, _label in _OUTPUT_PAIR_META):
		snap_v83 = create_or_get_publication_snapshot(tc, {})
		if snap_v83.get("ok"):
			output_refs_contract_v83 = extract_std_output_refs_contract_v83(snap_v83)

	return {
		"ok": True,
		"addendum_code": ac,
		"tender_code": tc,
		"tender_std_instance": si,
		"tm2_tender": cstr(ad.tm2_tender or "").strip(),
		"change_types": change_types,
		"affected_outputs": sorted(affected),
		"requires_supplier_notification": bool(impact.get("requires_supplier_notification")),
		"requires_addendum_snapshot": bool(impact.get("requires_addendum_snapshot")),
		**out_refs,
		**pub_refs,
		"output_refs_contract_v83": output_refs_contract_v83,
	}


def regenerate_outputs_for_addendum(addendum_code: str) -> dict[str, Any]:
	"""Doc 9 §8.2 — execute controlled regeneration for ``addendum_code`` (stub).

	Uses :meth:`~kentender_procurement.tender_management.std_instance.addendum.StdAddendumImpactService.create_regeneration_plan`
	with ``execute=True`` and ``publish_outputs=True``. ``change_types`` default to the last
	:func:`analyze_addendum_impact` cache for this addendum, else ``primary_impact_type`` mapping.

	Returns doc §10.4-style ``previous_*`` / ``revised_*`` with **revised** populated from the
	``Tender STD Instance`` after regeneration and :func:`create_or_get_publication_snapshot`.
	"""
	ac = (addendum_code or "").strip()
	if not ac:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("Addendum code is required."),
		}
	ad = _get_tm2_addendum_doc(ac)
	if not ad:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("TM2 Addendum {0} was not found.").format(ac),
		}
	tpair = _active_tender_code_and_si(ad.tm2_tender)
	if not tpair:
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": _("No active TM2 Tender STD Binding for this addendum."),
			"addendum_code": ac,
		}
	tc, si = tpair
	si_row_before = _si_row_output_bundle(si)
	snap_before = create_or_get_publication_snapshot(tc, {})
	prev_pub_c = cstr(snap_before.get("publication_snapshot_code") or "").strip() if snap_before.get("ok") else ""
	prev_pub_h = cstr(snap_before.get("snapshot_hash") or "").strip() if snap_before.get("ok") else ""

	cts = _cache_recall_addendum_change_types(ac) or _change_types_from_proposed_or_addendum(ad, {})

	try:
		plan = StdAddendumImpactService.create_regeneration_plan(
			si,
			cts,
			source_addendum_code=ac,
			execute=True,
			publish_outputs=True,
		)
	except frappe.ValidationError as exc:
		_cache_clear_addendum_change_types(ac)
		return {
			"ok": False,
			"denial_code": DenialCode.AUTH_CONTEXT_DENIED.value,
			"message": cstr(exc),
			"addendum_code": ac,
		}
	_cache_clear_addendum_change_types(ac)

	si_row_after = _si_row_output_bundle(si)
	snap_after = create_or_get_publication_snapshot(tc, {})
	rev_pub_c = cstr(snap_after.get("publication_snapshot_code") or "").strip() if snap_after.get("ok") else ""
	rev_pub_h = cstr(snap_after.get("snapshot_hash") or "").strip() if snap_after.get("ok") else ""

	prev_out: dict[str, str] = {}
	for short, field, _label in _OUTPUT_PAIR_META:
		prev_out[f"previous_{short}_output_code"] = cstr(si_row_before.get(field) or "").strip()
		prev_out[f"revised_{short}_output_code"] = cstr(si_row_after.get(field) or "").strip()

	affected = frozenset(str(x) for x in (plan.get("affected_outputs") or []) if x)

	extras: dict[str, Any] = {}
	if snap_before.get("ok"):
		extras["previous_output_refs_contract_v83"] = extract_std_output_refs_contract_v83(snap_before)
	if snap_after.get("ok"):
		extras["revised_output_refs_contract_v83"] = extract_std_output_refs_contract_v83(snap_after)

	return {
		"ok": True,
		"addendum_code": ac,
		"tender_code": tc,
		"tender_std_instance": si,
		"tm2_tender": cstr(ad.tm2_tender or "").strip(),
		"change_types": cts,
		"affected_outputs": sorted(affected),
		"addendum_snapshot_code": plan.get("addendum_snapshot_code"),
		"executed_outputs": plan.get("executed_outputs"),
		**prev_out,
		"previous_publication_snapshot_code": prev_pub_c,
		"revised_publication_snapshot_code": rev_pub_c,
		"previous_snapshot_hash": prev_pub_h,
		"revised_snapshot_hash": rev_pub_h,
		**extras,
	}


def analyzeAddendumImpact(addendum_code: str, proposed_changes: Any) -> dict[str, Any]:
	"""CamelCase alias for :func:`analyze_addendum_impact`."""
	return analyze_addendum_impact(addendum_code, proposed_changes)


def regenerateOutputsForAddendum(addendum_code: str) -> dict[str, Any]:
	"""CamelCase alias for :func:`regenerate_outputs_for_addendum`."""
	return regenerate_outputs_for_addendum(addendum_code)
