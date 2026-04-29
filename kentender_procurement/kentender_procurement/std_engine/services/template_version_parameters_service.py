"""STD workbench: Template Version parameter catalogue (STD-CURSOR-1009)."""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)

# Pack order for stable UI grouping (unknown groups sort after these, alphabetically).
PARAMETER_GROUP_ORDER: tuple[str, ...] = (
	"Tender Identity",
	"Procurement Method",
	"Dates and Deadlines",
	"Tender Security",
	"Currency and Exchange",
	"Site Visit",
	"Pre-Tender Meeting",
	"Eligibility",
	"Qualification",
	"Evaluation",
	"Works Site",
	"BOQ",
	"Contract",
	"Complaints",
)


def _short_trigger_value(raw: object, max_len: int = 96) -> str:
	if raw is None:
		return "—"
	if isinstance(raw, (dict, list)):
		s = frappe.as_json(raw)
	else:
		s = str(raw)
	s = s.replace("\n", " ").strip()
	if len(s) > max_len:
		return s[: max_len - 3] + "..."
	return s


def _group_sort_key(name: str) -> tuple[int, int | str]:
	n = (name or "").strip()
	if n in PARAMETER_GROUP_ORDER:
		return (0, PARAMETER_GROUP_ORDER.index(n))
	return (1, n.lower())


def _human_dependency_outgoing(
	trigger_label: str,
	trigger_code: str,
	operator: str,
	trigger_value_short: str,
	dependent_label: str,
	dependent_code: str,
	effect: str,
) -> str:
	return (
		"When "
		f'"{trigger_label}"'
		f" ({trigger_code}) {operator} {trigger_value_short}, "
		f'"{dependent_label}"'
		f" ({dependent_code}) is affected: {effect}."
	)


def _human_dependency_incoming(
	trigger_label: str,
	trigger_code: str,
	operator: str,
	trigger_value_short: str,
	effect: str,
) -> str:
	return (
		f'Controlled by "{trigger_label}" ({trigger_code}) when {operator} {trigger_value_short}: {effect}.'
	)


def build_std_template_version_parameter_catalogue(version_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return grouped parameter definitions + dependency summaries for workbench Parameters tab."""
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

	sections = frappe.get_all(
		"STD Section Definition",
		filters={"version_code": code},
		fields=["section_code", "section_title"],
	)
	section_title_by_code: dict[str, str] = {
		str(s.get("section_code") or ""): str(s.get("section_title") or "") for s in sections if s.get("section_code")
	}

	param_fields = [
		"parameter_code",
		"label",
		"reference",
		"parameter_group",
		"section_code",
		"data_type",
		"required",
		"value_resolution_stage",
		"drives_bundle",
		"drives_dsm",
		"drives_dom",
		"drives_dem",
		"drives_dcm",
		"addendum_change_requires_acknowledgement",
		"addendum_change_requires_deadline_review",
		"source_document_code",
		"source_page_start",
		"source_page_end",
	]
	params_raw = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": code},
		fields=param_fields,
		order_by="parameter_group asc, label asc, parameter_code asc",
	)

	deps_raw = frappe.get_all(
		"STD Parameter Dependency",
		filters={"version_code": code},
		fields=[
			"dependency_code",
			"trigger_parameter_code",
			"trigger_operator",
			"trigger_value",
			"dependent_parameter_code",
			"effect",
			"condition_expression",
		],
		order_by="dependency_code asc",
	)

	label_by_code: dict[str, str] = {}
	for p in params_raw:
		pc = str(p.get("parameter_code") or "")
		if pc:
			label_by_code[pc] = str(p.get("label") or pc)

	incoming: dict[str, list[str]] = defaultdict(list)
	outgoing: dict[str, list[str]] = defaultdict(list)
	for d in deps_raw:
		trig = str(d.get("trigger_parameter_code") or "")
		depc = str(d.get("dependent_parameter_code") or "")
		if not trig or not depc:
			continue
		tl = label_by_code.get(trig, trig)
		dl = label_by_code.get(depc, depc)
		op = str(d.get("trigger_operator") or "")
		tv = _short_trigger_value(d.get("trigger_value"))
		effect = str(d.get("effect") or "")
		outgoing[trig].append(
			_human_dependency_outgoing(tl, trig, op, tv, dl, depc, effect),
		)
		incoming[depc].append(
			_human_dependency_incoming(tl, trig, op, tv, effect),
		)

	parameters_flat: list[dict[str, object]] = []
	for p in params_raw:
		pcode = str(p.get("parameter_code") or "")
		sc = str(p.get("section_code") or "")
		parameters_flat.append(
			{
				"parameter_code": pcode,
				"label": p.get("label"),
				"reference": p.get("reference"),
				"parameter_group": str(p.get("parameter_group") or "").strip() or str(_("Ungrouped")),
				"section_code": sc or None,
				"section_title": section_title_by_code.get(sc) if sc else None,
				"data_type": p.get("data_type"),
				"required": bool(int(p.get("required") or 0)),
				"value_resolution_stage": p.get("value_resolution_stage"),
				"source_document_code": p.get("source_document_code"),
				"source_page_start": p.get("source_page_start"),
				"source_page_end": p.get("source_page_end"),
				"incoming_dependencies": list(incoming.get(pcode, [])),
				"outgoing_dependencies": list(outgoing.get(pcode, [])),
				"impact": {
					"drives_bundle": bool(int(p.get("drives_bundle") or 0)),
					"drives_dsm": bool(int(p.get("drives_dsm") or 0)),
					"drives_dom": bool(int(p.get("drives_dom") or 0)),
					"drives_dem": bool(int(p.get("drives_dem") or 0)),
					"drives_dcm": bool(int(p.get("drives_dcm") or 0)),
					"addendum_change_requires_acknowledgement": bool(
						int(p.get("addendum_change_requires_acknowledgement") or 0)
					),
					"addendum_change_requires_deadline_review": bool(
						int(p.get("addendum_change_requires_deadline_review") or 0)
					),
				},
			}
		)

	by_group: dict[str, list[dict[str, object]]] = defaultdict(list)
	for row in parameters_flat:
		gname = str(row.get("parameter_group") or str(_("Ungrouped")))
		by_group[gname].append(row)

	group_names = sorted(by_group.keys(), key=_group_sort_key)
	groups_out = [{"group_name": gn, "parameters": by_group[gn]} for gn in group_names]

	return {
		"ok": True,
		"version_code": code,
		"read_only": read_only,
		"groups": groups_out,
	}
