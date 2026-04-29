"""STD workbench: Template Version extraction mappings (STD-CURSOR-1012)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)

TARGET_MODELS: tuple[str, ...] = ("Bundle", "DSM", "DOM", "DEM", "DCM")


def _to_bool(value) -> bool:
	try:
		return bool(int(value or 0))
	except (TypeError, ValueError):
		return False


def _norm_type(t: str | None) -> str:
	return (t or "").strip().lower()


def _mapping_key(target_model: str, source_type: str | None, source_code: str | None) -> tuple[str, str, str]:
	return (str(target_model or ""), _norm_type(source_type), str(source_code or "").strip())


def build_std_template_version_mappings_catalogue(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return extraction mappings grouped by target model + coverage gaps."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (version_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Version code is required."))}

	resolved = resolve_std_document("Template Version", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this version code.")),
			"version_code": code,
		}
	doctype, name, doc = resolved
	if doctype != "STD Template Version":
		return {"ok": False, "error": "invalid", "message": str(_("Not a template version."))}
	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	status = str(doc.get("version_status") or "")
	try:
		immutable = int(doc.get("immutable_after_activation") or 0)
	except (TypeError, ValueError):
		immutable = 0
	read_only = status == "Active" and immutable == 1

	rows = frappe.get_all(
		"STD Extraction Mapping",
		filters={"version_code": code},
		fields=[
			"mapping_code",
			"source_object_type",
			"source_object_code",
			"target_model",
			"target_component_type",
			"mandatory",
			"validation_status",
		],
		order_by="target_model asc, mapping_code asc",
	)
	for r in rows:
		r["mandatory"] = _to_bool(r.get("mandatory"))

	present: set[tuple[str, str, str]] = set()
	for r in rows:
		tm = str(r.get("target_model") or "")
		if tm in TARGET_MODELS:
			present.add(_mapping_key(tm, str(r.get("source_object_type") or ""), str(r.get("source_object_code") or "")))

	by_model: dict[str, list[dict[str, object]]] = {m: [] for m in TARGET_MODELS}
	for r in rows:
		tm = str(r.get("target_model") or "")
		if tm in by_model:
			by_model[tm].append(dict(r))

	sections = frappe.get_all(
		"STD Section Definition",
		filters={"version_code": code},
		fields=["section_code", "section_number", "section_title"],
	)
	section_meta = {str(s["section_code"]): s for s in sections if s.get("section_code")}

	forms = frappe.get_all(
		"STD Form Definition",
		filters={"version_code": code},
		fields=[
			"form_code",
			"section_code",
			"drives_dsm",
			"drives_dem",
			"drives_dcm",
		],
	)
	for f in forms:
		for fld in ("drives_dsm", "drives_dem", "drives_dcm"):
			f[fld] = _to_bool(f.get(fld))

	params = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": code},
		fields=[
			"parameter_code",
			"drives_bundle",
			"drives_dsm",
			"drives_dom",
			"drives_dem",
			"drives_dcm",
		],
	)
	for p in params:
		for fld in ("drives_bundle", "drives_dsm", "drives_dom", "drives_dem", "drives_dcm"):
			p[fld] = _to_bool(p.get(fld))

	components = frappe.get_all(
		"STD Works Requirement Component Definition",
		filters={"version_code": code},
		fields=[
			"component_code",
			"drives_dsm",
			"drives_dem",
			"drives_dcm",
		],
	)
	for c in components:
		for fld in ("drives_dsm", "drives_dem", "drives_dcm"):
			c[fld] = _to_bool(c.get(fld))

	def _has(model: str, source_type: str, source_code: str) -> bool:
		return _mapping_key(model, source_type, source_code) in present

	missing: list[dict[str, object]] = []

	for r in rows:
		vs = str(r.get("validation_status") or "")
		if vs in ("Missing Source", "Missing Target"):
			missing.append(
				{
					"kind": "validation",
					"target_model": str(r.get("target_model") or ""),
					"mapping_code": str(r.get("mapping_code") or ""),
					"source_object_type": r.get("source_object_type"),
					"source_object_code": r.get("source_object_code"),
					"validation_status": vs,
					"label": str(_("Mapping row flagged: {0}").format(vs)),
				}
			)

	def _add_gap(model: str, source_type: str, source_code: str, label: str) -> None:
		if not source_code:
			return
		if _has(model, source_type, source_code):
			return
		missing.append(
			{
				"kind": "gap",
				"target_model": model,
				"source_object_type": source_type,
				"source_object_code": source_code,
				"label": label,
			}
		)

	model_flags_form = (
		("drives_dsm", "DSM"),
		("drives_dem", "DEM"),
		("drives_dcm", "DCM"),
	)
	model_flags_param = (
		("drives_bundle", "Bundle"),
		("drives_dsm", "DSM"),
		("drives_dom", "DOM"),
		("drives_dem", "DEM"),
		("drives_dcm", "DCM"),
	)
	model_flags_works = (
		("drives_dsm", "DSM"),
		("drives_dem", "DEM"),
		("drives_dcm", "DCM"),
	)

	for f in forms:
		fc = str(f.get("form_code") or "")
		for flag, model in model_flags_form:
			if _to_bool(f.get(flag)):
				_add_gap(model, "Form", fc, str(_("Form {0} drives {1} but has no extraction mapping.").format(fc, model)))

	for p in params:
		pc = str(p.get("parameter_code") or "")
		for flag, model in model_flags_param:
			if _to_bool(p.get(flag)):
				_add_gap(model, "Parameter", pc, str(_("Parameter {0} drives {1} but has no extraction mapping.").format(pc, model)))

	for c in components:
		cc = str(c.get("component_code") or "")
		for flag, model in model_flags_works:
			if _to_bool(c.get(flag)):
				_add_gap(
					model,
					"Works Requirement Component",
					cc,
					str(_("Works component {0} drives {1} but has no extraction mapping.").format(cc, model)),
				)

	boq = frappe.get_all(
		"STD BOQ Definition",
		filters={"version_code": code},
		fields=["boq_definition_code"],
		limit=1,
	)
	if boq:
		bcode = str(boq[0].get("boq_definition_code") or "")
		if bcode:
			for model in ("DEM", "DCM"):
				if not any(
					_norm_type(r.get("source_object_type")) in ("boq definition", "boq", "boq_definition")
					and str(r.get("source_object_code") or "") == bcode
					and str(r.get("target_model") or "") == model
					for r in rows
				):
					missing.append(
						{
							"kind": "gap",
							"target_model": model,
							"source_object_type": "BOQ Definition",
							"source_object_code": bcode,
							"label": str(
								_("BOQ definition {0} has no {1} extraction mapping (BOQ pricing / evaluation linkage).").format(
									bcode, model
								)
							),
						}
					)

	def _section_number(sec_code: str | None) -> str:
		if not sec_code:
			return ""
		meta = section_meta.get(str(sec_code)) or {}
		return str(meta.get("section_number") or "").strip().upper()

	def _section_num_matches(sn: str, roman: str) -> bool:
		u = (sn or "").strip().upper()
		w = roman.upper()
		if not u or not w:
			return False
		if u == w:
			return True
		return u.startswith(w + ".") or u.startswith(w + "-")

	section_iv_dsm: list[dict[str, object]] = []
	for r in by_model["DSM"]:
		st = _norm_type(str(r.get("source_object_type") or ""))
		scode = str(r.get("source_object_code") or "")
		if st != "form":
			continue
		fm = next((x for x in forms if str(x.get("form_code") or "") == scode), None)
		if not fm:
			continue
		sn = _section_number(str(fm.get("section_code") or ""))
		if _section_num_matches(sn, "IV"):
			section_iv_dsm.append(dict(r))

	section_iii_dem: list[dict[str, object]] = []
	seen_dem_highlight: set[str] = set()
	for r in by_model["DEM"]:
		st = _norm_type(str(r.get("source_object_type") or ""))
		mc = str(r.get("mapping_code") or "")
		if st == "evaluation rule":
			if mc and mc not in seen_dem_highlight:
				seen_dem_highlight.add(mc)
				section_iii_dem.append(dict(r))
			continue
		scode = str(r.get("source_object_code") or "")
		for f in forms:
			if str(f.get("form_code") or "") != scode:
				continue
			sn = _section_number(str(f.get("section_code") or ""))
			if _section_num_matches(sn, "III"):
				if mc and mc not in seen_dem_highlight:
					seen_dem_highlight.add(mc)
					section_iii_dem.append(dict(r))

	return {
		"ok": True,
		"version_code": code,
		"read_only": read_only,
		"tabs": {m: by_model[m] for m in TARGET_MODELS},
		"missing_coverage": missing[:200],
		"highlights": {
			"section_iv_dsm": section_iv_dsm,
			"section_iii_dem": section_iii_dem,
		},
	}
