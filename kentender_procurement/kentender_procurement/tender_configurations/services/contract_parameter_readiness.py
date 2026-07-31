# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-09 / preview readiness for STD-declared contract parameters.

Replaces hard-coded generic IT topic checklists. Each applicable required
parameter is resolved from explicit SCC data, an authoritative tender module,
locked STD text, or a permitted Not Applicable status.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_ROUTES,
)

PLACEHOLDER_VALUES = frozenset({"as specified", "tbd", "n/a", "na", "-", ""})

# Named applicability conditions (categories are organisational only — never keys).
APP_ALWAYS = "always"
APP_WHEN_SOFTWARE_ESCROW = "when_software_escrow_enabled"
APP_WHEN_SUBCONTRACTING = "when_subcontracting_enabled"
APP_WHEN_SUPPORT_SLA = "when_support_sla_enabled"


@dataclass(frozen=True)
class ContractParameterDecl:
	"""Readiness metadata for one STD / logical contract parameter."""

	parameter_id: str
	label: str
	std_parameter_codes: tuple[str, ...]
	applicability: str
	tender_specific_required: bool
	authoritative_source: str
	allows_not_applicable: bool
	owner_step: str
	owner_field: str
	blocker_message: str
	locked_std_default: str = ""
	tds_value_keys: tuple[str, ...] = ()
	tds_na_keys: tuple[str, ...] = ()
	# When False, include even if the STD package has no matching STD Parameter row.
	require_std_parameter: bool = True


# Overlay declared manually until STD Parameter metadata carries full readiness fields.
# Intersected with STD Parameter rows for the selected digitized STD version.
# CFG-09 rows resolve by parameter_code / parameter_key / readiness_parameter_id —
# never by free-text item labels. Category remains organisational (e.g. SCC Value).
IT_STD_CONTRACT_PARAMETER_DECLARATIONS: tuple[ContractParameterDecl, ...] = (
	ContractParameterDecl(
		parameter_id="governing_law",
		label="Governing law",
		std_parameter_codes=(),
		applicability=APP_ALWAYS,
		tender_specific_required=False,
		authoritative_source="locked_std",
		allows_not_applicable=False,
		owner_step="CFG-09",
		owner_field="governing_law",
		blocker_message="Locked STD governing-law text is unavailable.",
		# Never invent jurisdiction text — resolve only from bound locked STD clauses.
		locked_std_default="",
		require_std_parameter=False,
	),
	ContractParameterDecl(
		parameter_id="scope",
		label="Scope",
		std_parameter_codes=(),
		applicability=APP_ALWAYS,
		tender_specific_required=False,
		authoritative_source="it_requirements",
		allows_not_applicable=False,
		owner_step="CFG-03",
		owner_field="requirements",
		blocker_message="IT Requirements scope is incomplete.",
		require_std_parameter=False,
	),
	ContractParameterDecl(
		parameter_id="commencement",
		label="Commencement",
		std_parameter_codes=("IT-SCC-011",),
		applicability=APP_ALWAYS,
		tender_specific_required=False,
		authoritative_source="implementation_schedule",
		allows_not_applicable=False,
		owner_step="CFG-04",
		owner_field="Implementation Schedule",
		blocker_message="Implementation Schedule delivery timing is incomplete.",
	),
	ContractParameterDecl(
		parameter_id="payment",
		label="Payment schedule",
		std_parameter_codes=("IT-SCC-014",),
		applicability=APP_ALWAYS,
		tender_specific_required=True,
		authoritative_source="cfg09",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="Payment schedule",
		blocker_message="Payment schedule value is missing.",
	),
	ContractParameterDecl(
		parameter_id="software_escrow",
		label="Source code escrow",
		std_parameter_codes=("IT-SCC-034", "IT-SCC-035"),
		applicability=APP_WHEN_SOFTWARE_ESCROW,
		tender_specific_required=True,
		authoritative_source="cfg09",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="Source code escrow",
		blocker_message="Source code escrow terms are missing.",
	),
	ContractParameterDecl(
		parameter_id="subcontracting",
		label="Subcontracting",
		std_parameter_codes=(),
		applicability=APP_WHEN_SUBCONTRACTING,
		tender_specific_required=True,
		authoritative_source="cfg09",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="Subcontracting",
		blocker_message="Subcontracting terms are missing.",
		require_std_parameter=False,
	),
	ContractParameterDecl(
		parameter_id="sla",
		label="SLA",
		std_parameter_codes=("IT-SCC-054",),
		applicability=APP_WHEN_SUPPORT_SLA,
		tender_specific_required=True,
		authoritative_source="cfg09",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="SLA",
		blocker_message="SLA / defect response terms are missing.",
	),
	ContractParameterDecl(
		parameter_id="performance_security",
		label="Performance Security",
		std_parameter_codes=("IT-SCC-028", "IT-SCC-029"),
		applicability=APP_ALWAYS,
		tender_specific_required=True,
		authoritative_source="tds",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="Performance Security",
		blocker_message="Performance security value is missing.",
		tds_value_keys=("performance_security", "performance_security_percent"),
		tds_na_keys=("performance_security_required",),
	),
	ContractParameterDecl(
		parameter_id="warranty",
		label="Warranty",
		std_parameter_codes=("IT-SCC-053",),
		applicability=APP_ALWAYS,
		tender_specific_required=True,
		authoritative_source="cfg09",
		allows_not_applicable=True,
		owner_step="CFG-09",
		owner_field="Warranty",
		blocker_message="Warranty value is missing.",
	),
)


def _parse_json(raw: Any) -> Any:
	if raw is None or raw == "":
		return None
	if isinstance(raw, (dict, list)):
		return raw
	if isinstance(raw, str):
		try:
			return json.loads(raw)
		except (TypeError, ValueError):
			return None
	return None


def _norm(text: Any) -> str:
	return cstr(text or "").strip().lower()


def _is_na_token(text: Any) -> bool:
	t = _norm(text)
	return t in {"no", "n", "false", "0", "not applicable", "n/a", "na", "none"}


def _is_yes_token(text: Any) -> bool:
	t = _norm(text)
	return t in {"yes", "y", "true", "1", "required"}


def _scc_value(row: dict[str, Any]) -> str:
	return cstr(
		row.get("value_or_obligation")
		or row.get("source_value")
		or row.get("value")
		or row.get("configured_value")
		or ""
	).strip()


def _row_is_na(row: dict[str, Any]) -> bool:
	if row.get("not_applicable") in (1, True, "1", "Yes", "yes", "true"):
		return True
	status = _norm(row.get("setup_status_label") or row.get("status") or row.get("status_label"))
	return status in {"not applicable", "n/a", "na"}


def _parameter_key_matches_code(parameter_key: str, parameter_code: str) -> bool:
	"""Match STD keys like …parameter.scc.014 to codes like IT-SCC-014."""
	key = _norm(parameter_key)
	code = cstr(parameter_code or "").strip().upper()
	if not key or not code:
		return False
	m = re.match(r"^IT-SCC-(\d+)$", code)
	if not m:
		return False
	ordinal = m.group(1).lstrip("0") or "0"
	padded = m.group(1)
	return (
		f".parameter.scc.{padded}" in key
		or f".parameter.scc.{ordinal}" in key
		or key.endswith(f"scc.{padded}")
		or key.endswith(f"scc.{ordinal}")
	)


def _row_matches(row: dict[str, Any], decl: ContractParameterDecl) -> bool:
	"""Match CFG-09 rows by structured STD binding only — never by item label text."""
	row_pid = _norm(row.get("readiness_parameter_id") or row.get("parameter_id"))
	if row_pid and row_pid == _norm(decl.parameter_id):
		return True
	row_code = cstr(row.get("parameter_code") or "").strip().upper()
	row_key = cstr(row.get("parameter_key") or "").strip()
	for code in decl.std_parameter_codes:
		if row_code and row_code == cstr(code).strip().upper():
			return True
		if row_key and _parameter_key_matches_code(row_key, code):
			return True
	return False


def _find_matching_rows(
	values: list[dict[str, Any]], decl: ContractParameterDecl
) -> list[dict[str, Any]]:
	return [r for r in (values or []) if isinstance(r, dict) and _row_matches(r, decl)]


def _std_codes_present(std_version: str) -> set[str]:
	std_version = cstr(std_version or "").strip()
	if not std_version:
		return set()
	if not frappe.db.exists("STD Version", std_version):
		# Package id may equal version name; also try as package_id filter.
		pass
	rows = frappe.get_all(
		"STD Parameter",
		filters={
			"package_id": std_version,
			"parameter_key": ["like", "%.parameter.scc.%"],
		},
		fields=["metadata_json"],
		limit_page_length=500,
	)
	codes: set[str] = set()
	for row in rows:
		meta = _parse_json(row.get("metadata_json")) or {}
		code = cstr(meta.get("parameter_code") or "").strip()
		if code:
			codes.add(code)
	return codes


def load_applicable_contract_parameters(
	*,
	std_version: str = "",
	declarations: tuple[ContractParameterDecl, ...] | None = None,
) -> list[ContractParameterDecl]:
	"""Return readiness parameters declared for the selected digitized STD version."""
	decls = declarations or IT_STD_CONTRACT_PARAMETER_DECLARATIONS
	codes = _std_codes_present(std_version)
	# When STD parameters are not loaded (unit tests without DB rows), keep
	# declarations that do not require a STD Parameter row, plus those that
	# match when codes are available. If std_version is blank, use full overlay
	# so pure unit tests can exercise resolution without a live package.
	if not std_version:
		return list(decls)
	out: list[ContractParameterDecl] = []
	for decl in decls:
		if not decl.require_std_parameter:
			out.append(decl)
			continue
		if not decl.std_parameter_codes:
			out.append(decl)
			continue
		if not codes or any(c in codes for c in decl.std_parameter_codes):
			out.append(decl)
	return out


def _joined_requirements(requirements: list[dict[str, Any]] | None) -> str:
	parts: list[str] = []
	for r in requirements or []:
		if not isinstance(r, dict):
			continue
		parts.append(
			" ".join(
				cstr(r.get(k) or "")
				for k in (
					"title",
					"requirement_text",
					"description",
					"category_label",
					"group",
					"item_label",
				)
			)
		)
	return " ".join(parts).lower()


def _applicability_enabled(
	decl: ContractParameterDecl,
	*,
	values: list[dict[str, Any]],
	tds: dict[str, Any],
	requirements: list[dict[str, Any]] | None,
) -> bool:
	if decl.applicability == APP_ALWAYS:
		return True

	matched = _find_matching_rows(values, decl)
	explicit_enable = any(
		(not _row_is_na(r)) and _scc_value(r) and _norm(_scc_value(r)) not in PLACEHOLDER_VALUES
		for r in matched
	)
	# A matching row that is not N/A means the PE elected to configure the topic.
	row_present_active = any(not _row_is_na(r) for r in matched)

	if decl.applicability == APP_WHEN_SOFTWARE_ESCROW:
		flag = tds.get("software_escrow_required")
		if _is_yes_token(flag) or flag is True:
			return True
		# IT-SCC-034 is the boolean "Software escrow required" parameter.
		for r in matched:
			code = cstr(r.get("parameter_code") or "").strip().upper()
			if code == "IT-SCC-034" and _is_yes_token(_scc_value(r)):
				return True
		return explicit_enable

	if decl.applicability == APP_WHEN_SUBCONTRACTING:
		flag = tds.get("subcontracting_restriction_required")
		if _is_yes_token(flag) or flag is True:
			return True
		return row_present_active

	if decl.applicability == APP_WHEN_SUPPORT_SLA:
		flag = tds.get("support_sla_required")
		if _is_yes_token(flag) or flag is True:
			return True
		req_text = _joined_requirements(requirements)
		if re.search(r"\b(sla|service level|uptime\s+guarantee|managed[- ]service)\b", req_text):
			return True
		return explicit_enable

	return False


def _single_delivery_summary(single: dict[str, Any] | None) -> str:
	"""Build a commencement / delivery summary from CFG-04 single turnkey fields."""
	if not isinstance(single, dict) or not single:
		return ""
	duration = cstr(
		single.get("expected_delivery_duration")
		or (
			f"{cstr(single.get('expected_duration_value') or '').strip()} "
			f"{cstr(single.get('expected_duration_unit') or '').strip()}"
		).strip()
	).strip()
	trigger = cstr(single.get("delivery_trigger") or "").strip()
	deliverables = cstr(single.get("key_deliverables") or "").strip()
	acceptance = cstr(single.get("acceptance_method") or "").strip()
	# Require the same core fields the CFG-04 single-turnkey form treats as complete.
	if not duration or not trigger or not deliverables or not acceptance:
		return ""
	bits = [
		f"Single turnkey delivery within {duration}",
		f"trigger: {trigger}",
		f"deliverables: {deliverables}",
		f"acceptance: {acceptance}",
	]
	return "; ".join(bits)


def _phased_milestones_summary(milestones: list[dict[str, Any]] | None) -> str:
	for m in milestones or []:
		if not isinstance(m, dict):
			continue
		name = cstr(m.get("name") or m.get("milestone_name") or "").strip()
		dur = cstr(
			m.get("expected_duration_value")
			or m.get("expected_delivery_duration")
			or m.get("duration")
			or ""
		).strip()
		unit = cstr(m.get("expected_duration_unit") or "").strip()
		if name or dur:
			bits = [b for b in (name, f"{dur} {unit}".strip()) if b]
			return "; ".join(bits)
	return ""


def _locked_std_inherited_marker(std_version: str) -> str:
	"""Return a non-invented inheritance marker when the bound STD has locked clauses.

	Does not fabricate jurisdiction wording (e.g. never invents "Laws of Kenya").
	"""
	std_version = cstr(std_version or "").strip()
	if not std_version:
		return ""
	try:
		if frappe.db.count("STD Clause", {"package_id": std_version}) > 0:
			return "Inherited from locked STD / GCC text"
	except Exception:
		return ""
	return ""


def _module_value(
	decl: ContractParameterDecl,
	*,
	tds: dict[str, Any],
	requirements: list[dict[str, Any]] | None,
	milestones: list[dict[str, Any]] | None,
	single_delivery: dict[str, Any] | None = None,
	delivery_approach: str = "",
	std_version: str = "",
) -> str:
	src = decl.authoritative_source
	if src == "locked_std":
		# Prefer explicit overlay default only when non-empty (tests); never ship invented law text.
		explicit = cstr(decl.locked_std_default or "").strip()
		if explicit:
			return explicit
		return _locked_std_inherited_marker(std_version)
	if src == "tds":
		for key in decl.tds_value_keys:
			val = cstr(tds.get(key) or "").strip()
			if val and _norm(val) not in PLACEHOLDER_VALUES:
				return val
		return ""
	if src == "it_requirements":
		if requirements:
			# Scope is derived from the technical requirement set.
			titles = [
				cstr(r.get("title") or r.get("requirement_text") or "").strip()
				for r in requirements
				if isinstance(r, dict)
			]
			titles = [t for t in titles if t]
			if titles:
				return f"As specified in Part 2 technical requirements ({len(titles)} items)."
		return ""
	if src == "implementation_schedule":
		approach = cstr(delivery_approach or "").strip().lower()
		# Prefer the configured approach; fall back so either shape can resolve.
		if "single" in approach or "turnkey" in approach or not approach:
			single_summary = _single_delivery_summary(single_delivery)
			if single_summary:
				return single_summary
		phased = _phased_milestones_summary(milestones)
		if phased:
			return phased
		# If approach was phased but empty, still try single turnkey data.
		return _single_delivery_summary(single_delivery)
	return ""


def _tds_marks_na(decl: ContractParameterDecl, tds: dict[str, Any]) -> bool:
	if not decl.allows_not_applicable:
		return False
	for key in decl.tds_na_keys:
		if key in tds and _is_na_token(tds.get(key)):
			return True
	return False


def resolve_contract_parameters(
	*,
	std_version: str = "",
	contract_values: list[dict[str, Any]] | None = None,
	tds: dict[str, Any] | None = None,
	requirements: list[dict[str, Any]] | None = None,
	milestones: list[dict[str, Any]] | None = None,
	single_delivery: dict[str, Any] | None = None,
	delivery_approach: str = "",
	declarations: tuple[ContractParameterDecl, ...] | None = None,
) -> dict[str, Any]:
	"""Resolve applicable required contract parameters for CFG-09 / preview.

	Resolution order per parameter:
	1. Explicit tender-specific CFG-09 value
	2. Value from authoritative module
	3. Locked STD / GCC default
	4. Explicit Not applicable when permitted (CFG-09 or TDS)
	5. Blocker only if still unresolved
	"""
	values = [r for r in (contract_values or []) if isinstance(r, dict)]
	tds = tds if isinstance(tds, dict) else {}
	requirements = requirements or []
	milestones = milestones or []
	single_delivery = single_delivery if isinstance(single_delivery, dict) else {}

	params = load_applicable_contract_parameters(
		std_version=std_version, declarations=declarations
	)
	resolved: list[dict[str, Any]] = []
	unresolved: list[dict[str, Any]] = []
	not_applicable: list[dict[str, Any]] = []

	for decl in params:
		applicable = _applicability_enabled(
			decl, values=values, tds=tds, requirements=requirements
		)
		base = {
			"parameter_id": decl.parameter_id,
			"label": decl.label,
			"owner_step": decl.owner_step,
			"owner_field": decl.owner_field,
			"owner_route": STEP_ROUTES.get(decl.owner_step, ""),
			"allows_not_applicable": decl.allows_not_applicable,
			"authoritative_source": decl.authoritative_source,
		}
		if not applicable:
			not_applicable.append({**base, "reason": "applicability_condition_false"})
			continue

		matched = _find_matching_rows(values, decl)
		explicit_val = ""
		explicit_id = ""
		for row in matched:
			if _row_is_na(row):
				continue
			val = _scc_value(row)
			if val and _norm(val) not in PLACEHOLDER_VALUES:
				explicit_val = val
				explicit_id = cstr(row.get("contract_value_id") or "")
				break

		# 1) Explicit tender-specific CFG-09 value
		if explicit_val:
			resolved.append(
				{
					**base,
					"resolution": "explicit_scc",
					"value": explicit_val,
					"contract_value_id": explicit_id,
				}
			)
			continue

		# 2 / 3) Authoritative module or locked STD default
		module_val = _module_value(
			decl,
			tds=tds,
			requirements=requirements,
			milestones=milestones,
			single_delivery=single_delivery,
			delivery_approach=delivery_approach,
			std_version=std_version,
		)
		if module_val and _norm(module_val) not in PLACEHOLDER_VALUES:
			resolved.append(
				{
					**base,
					"resolution": (
						"locked_std"
						if decl.authoritative_source == "locked_std"
						else "authoritative_module"
					),
					"value": module_val,
				}
			)
			continue

		# 4) Explicit Not applicable when permitted (CFG-09 or TDS)
		cfg09_na = any(_row_is_na(r) for r in matched)
		tds_na = _tds_marks_na(decl, tds)
		if decl.allows_not_applicable and (cfg09_na or tds_na):
			# CFG-09 N/A without reason remains a row_issue; parameter counts resolved
			# only when TDS marks N/A or a CFG-09 reason is present.
			na_reason = ""
			for r in matched:
				if _row_is_na(r):
					na_reason = cstr(r.get("not_applicable_reason") or "").strip()
					break
			if tds_na or na_reason:
				if not na_reason and tds_na:
					na_reason = "Marked Not applicable in TDS"
				resolved.append(
					{
						**base,
						"resolution": "not_applicable",
						"value": "Not applicable",
						"not_applicable_reason": na_reason,
					}
				)
				continue

		# Locked STD inheritance with no bound clause text: do not invent jurisdiction
		# wording and do not invent a CFG-09 field the PE cannot complete.
		if decl.authoritative_source == "locked_std" and not decl.tender_specific_required:
			not_applicable.append({**base, "reason": "locked_std_text_unavailable"})
			continue

		# 5) Blocker — applicable required parameter still unresolved
		unresolved.append(
			{
				**base,
				"resolution": "unresolved",
				"message": decl.blocker_message,
			}
		)

	# Row-level integrity for entered CFG-09 values (empty / placeholders)
	row_issues: list[dict[str, Any]] = []
	for row in values:
		label = cstr(row.get("item_label") or row.get("contract_value_id") or "Contract value")
		if _row_is_na(row):
			if not cstr(row.get("not_applicable_reason") or "").strip():
				row_issues.append(
					{
						"parameter_id": "row_na_reason",
						"label": label,
						"owner_step": "CFG-09",
						"owner_field": "not_applicable_reason",
						"owner_route": STEP_ROUTES.get("CFG-09", ""),
						"message": (
							f"{label}: provide a Not applicable reason on CFG-09."
						),
					}
				)
			continue
		val = _scc_value(row)
		if not val:
			row_issues.append(
				{
					"parameter_id": "row_empty",
					"label": label,
					"owner_step": "CFG-09",
					"owner_field": "value_or_obligation",
					"owner_route": STEP_ROUTES.get("CFG-09", ""),
					"message": f"{label}: enter a value / obligation on CFG-09.",
				}
			)
		elif _norm(val) in PLACEHOLDER_VALUES - {""}:
			row_issues.append(
				{
					"parameter_id": "row_placeholder",
					"label": label,
					"owner_step": "CFG-09",
					"owner_field": "value_or_obligation",
					"owner_route": STEP_ROUTES.get("CFG-09", ""),
					"message": (
						f"{label}: replace placeholder value on CFG-09 with a concrete obligation."
					),
				}
			)

	blockers = [
		{
			"code": f"param_{u['parameter_id']}",
			"message": u["message"],
			"owner_step": u["owner_step"],
			"owner_field": u["owner_field"],
			"owner_route": u.get("owner_route") or "",
			"parameter_id": u["parameter_id"],
			"label": u["label"],
		}
		for u in unresolved
	]
	for issue in row_issues:
		blockers.append(
			{
				"code": issue["parameter_id"],
				"message": issue["message"],
				"owner_step": issue["owner_step"],
				"owner_field": issue["owner_field"],
				"owner_route": issue.get("owner_route") or "",
				"parameter_id": issue["parameter_id"],
				"label": issue["label"],
			}
		)

	return {
		"resolved": resolved,
		"unresolved": unresolved,
		"not_applicable": not_applicable,
		"row_issues": row_issues,
		"blockers": blockers,
		"can_continue": len(blockers) == 0,
	}


def assert_applicable_contract_parameters_resolved(
	contract_values: list[dict[str, Any]] | None = None,
	*,
	std_version: str = "",
	tds: dict[str, Any] | None = None,
	requirements: list[dict[str, Any]] | None = None,
	milestones: list[dict[str, Any]] | None = None,
	single_delivery: dict[str, Any] | None = None,
	delivery_approach: str = "",
) -> dict[str, str] | None:
	"""Preview / readiness hard-fail when an applicable required parameter is unresolved."""
	from kentender_procurement.tender_configurations.services.preview_presentation import (
		generation_block,
	)

	report = resolve_contract_parameters(
		std_version=std_version,
		contract_values=contract_values,
		tds=tds,
		requirements=requirements,
		milestones=milestones,
		single_delivery=single_delivery,
		delivery_approach=delivery_approach,
	)
	if report["can_continue"]:
		return None

	# Prefer a single actionable blocker — pack-style one-liners, not prose.
	first = (report["blockers"] or [{}])[0]
	owner_step = cstr(first.get("owner_step") or "CFG-09")
	owner_field = cstr(first.get("owner_field") or "Contract Values")
	message = cstr(first.get("message") or "Required contract parameter is incomplete.")
	return generation_block(
		blocking_area=f"{owner_step} Contract Values",
		message=message,
		action=f"Complete '{owner_field}' on {owner_step}.",
		owner_step=owner_step,
	)


def _schedule_parts_from_doc(doc: Any) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
	sched = _parse_json(getattr(doc, "implementation_schedule", None)) or {}
	if not isinstance(sched, dict):
		return "", [], {}
	approach = cstr(sched.get("delivery_approach") or "")
	milestones = [m for m in (sched.get("milestones") or []) if isinstance(m, dict)]
	single = sched.get("single_delivery") if isinstance(sched.get("single_delivery"), dict) else {}
	return approach, milestones, single


def _std_parameter_titles_by_code(std_version: str) -> dict[str, str]:
	std_version = cstr(std_version or "").strip()
	if not std_version:
		return {}
	rows = frappe.get_all(
		"STD Parameter",
		filters={
			"package_id": std_version,
			"parameter_key": ["like", "%.parameter.scc.%"],
		},
		fields=["title", "metadata_json"],
		limit_page_length=500,
	)
	out: dict[str, str] = {}
	for row in rows:
		meta = _parse_json(row.get("metadata_json")) or {}
		code = cstr(meta.get("parameter_code") or "").strip().upper()
		title = cstr(row.get("title") or meta.get("display_label") or "").strip()
		if code and title:
			out[code] = title
	return out


def _parameter_key_for_code(std_version: str, parameter_code: str) -> str:
	std_version = cstr(std_version or "").strip()
	code = cstr(parameter_code or "").strip().upper()
	m = re.match(r"^IT-SCC-(\d+)$", code)
	if not std_version or not m:
		return ""
	return f"{std_version}.parameter.scc.{m.group(1)}"


def _category_for_decl(decl: ContractParameterDecl) -> str:
	return {
		"payment": "SCC Value",
		"commencement": "SCC Value",
		"performance_security": "Securities & Guarantees",
		"warranty": "Support & Warranty",
		"sla": "Support & Warranty",
		"software_escrow": "Security & Compliance Obligation",
		"subcontracting": "SCC Value",
	}.get(decl.parameter_id, "SCC Value")


def _source_for_decl(decl: ContractParameterDecl) -> str:
	return {
		"tds": "Tender Data Sheet",
		"implementation_schedule": "Implementation Schedule",
		"it_requirements": "IT Requirements",
		"cfg09": "User entered",
		"locked_std": "Standard Tender Document",
	}.get(decl.authoritative_source, "User entered")


def _carry_forward_schedule_value(doc: Any) -> tuple[str, str]:
	"""Return (value, source_item_label) from CFG-04 only — never invent text."""
	approach, milestones, single = _schedule_parts_from_doc(doc)
	summary = _module_value(
		ContractParameterDecl(
			parameter_id="commencement",
			label="Commencement",
			std_parameter_codes=("IT-SCC-011",),
			applicability=APP_ALWAYS,
			tender_specific_required=False,
			authoritative_source="implementation_schedule",
			allows_not_applicable=False,
			owner_step="CFG-04",
			owner_field="Implementation Schedule",
			blocker_message="",
		),
		tds={},
		requirements=None,
		milestones=milestones,
		single_delivery=single,
		delivery_approach=approach,
	)
	if not summary:
		return "", ""
	label = "Single Turnkey Delivery" if "single" in approach.lower() or "turnkey" in approach.lower() else "Implementation Schedule"
	return summary, label


# Closed migration map for rows created by the retired pack-sample hydrate.
# Exact item_label match only — not general description search.
_LEGACY_HYDRATE_LABEL_BINDINGS: dict[str, tuple[str, str]] = {
	"performance security": ("performance_security", "IT-SCC-029"),
	"warranty": ("warranty", "IT-SCC-053"),
	"warranty period": ("warranty", "IT-SCC-053"),
	"delivery period": ("commencement", "IT-SCC-011"),
	"payment": ("payment", "IT-SCC-014"),
	"payment schedule": ("payment", "IT-SCC-014"),
}


def _legacy_binding_for_label(item_label: str) -> tuple[str, str] | None:
	return _LEGACY_HYDRATE_LABEL_BINDINGS.get(_norm(item_label))


def build_std_declared_contract_value_drafts(doc: Any) -> list[dict[str, Any]]:
	"""Build CFG-09 draft rows from the bound STD version only.

	Hard rules:
	- No pack-sample invention (Data Residency, On-site Support, etc.).
	- No pre-filled obligation text unless carried from a real upstream module value.
	- Every row carries structured STD binding keys.
	- Empty when no std_version or the package has no SCC STD Parameter rows.
	"""
	std_version = cstr(getattr(doc, "std_version", None) or "").strip()
	if not std_version:
		return []

	codes_present = _std_codes_present(std_version)
	if not codes_present:
		return []

	titles = _std_parameter_titles_by_code(std_version)
	schedule_value, schedule_item = _carry_forward_schedule_value(doc)

	drafts: list[dict[str, Any]] = []
	for decl in IT_STD_CONTRACT_PARAMETER_DECLARATIONS:
		# Hydrate only always-applicable parameters that require tender-specific CFG-09 entry,
		# plus commencement when CFG-04 can supply a real carry-forward value.
		if decl.applicability != APP_ALWAYS:
			continue
		needs_cfg09 = decl.tender_specific_required or decl.authoritative_source == "cfg09"
		is_commencement = decl.parameter_id == "commencement"
		if not needs_cfg09 and not is_commencement:
			continue
		if decl.require_std_parameter and decl.std_parameter_codes:
			if not any(c in codes_present for c in decl.std_parameter_codes):
				continue
		if not decl.std_parameter_codes:
			continue

		primary_code = decl.std_parameter_codes[0]
		title = titles.get(primary_code) or decl.label
		value = ""
		source = _source_for_decl(decl)
		source_item = ""
		if is_commencement and schedule_value:
			value = schedule_value
			source = "Implementation Schedule"
			source_item = schedule_item

		drafts.append(
			{
				"item_label": title,
				"category": _category_for_decl(decl),
				"source_screen": source,
				"source_item_label": source_item,
				"contract_location": "SCC / Contract Data",
				"value_or_obligation": value,
				"editable_here": 1,
				"parameter_code": primary_code,
				"parameter_key": _parameter_key_for_code(std_version, primary_code),
				"readiness_parameter_id": decl.parameter_id,
			}
		)
	return drafts


def ensure_std_declared_contract_values(
	doc: Any, existing: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
	"""Merge STD-declared parameters into CFG-09 so blockers always map to visible rows.

	1. Stamp structured bindings onto known legacy hydrate orphans (closed label map).
	2. Append any still-missing STD-declared tender-specific parameters as empty rows.
	3. Never invent pack-sample rows (Data Residency, On-site Support, etc.).
	"""
	rows = [dict(r) for r in (existing or []) if isinstance(r, dict)]
	std_version = cstr(getattr(doc, "std_version", None) or "").strip()
	drafts = build_std_declared_contract_value_drafts(doc)
	if not drafts:
		return rows

	# 1) Migrate legacy orphans created by the retired pack-sample hydrate.
	for row in rows:
		if cstr(row.get("parameter_code") or "").strip() or cstr(
			row.get("readiness_parameter_id") or ""
		).strip():
			continue
		binding = _legacy_binding_for_label(cstr(row.get("item_label") or ""))
		if not binding:
			continue
		pid, code = binding
		row["readiness_parameter_id"] = pid
		row["parameter_code"] = code
		row["parameter_key"] = _parameter_key_for_code(std_version, code) or cstr(
			row.get("parameter_key") or ""
		)

	bound_pids = {
		_norm(r.get("readiness_parameter_id"))
		for r in rows
		if cstr(r.get("readiness_parameter_id") or "").strip()
	}
	bound_codes = {
		cstr(r.get("parameter_code") or "").strip().upper()
		for r in rows
		if cstr(r.get("parameter_code") or "").strip()
	}

	# 2) Append missing STD-declared parameters so every blocker has a table row.
	for draft in drafts:
		pid = _norm(draft.get("readiness_parameter_id"))
		code = cstr(draft.get("parameter_code") or "").strip().upper()
		if pid and pid in bound_pids:
			continue
		if code and code in bound_codes:
			continue
		rows.append(dict(draft))
		if pid:
			bound_pids.add(pid)
		if code:
			bound_codes.add(code)

	return rows


def readiness_blockers_for_doc(doc: Any) -> list[dict[str, str]]:
	"""CFG-09 readiness blockers from STD-declared parameter resolution."""
	tds = _parse_json(getattr(doc, "tds_values", None)) or {}
	if not isinstance(tds, dict):
		tds = {}
	req_blob = _parse_json(getattr(doc, "it_requirements", None)) or {}
	requirements = []
	if isinstance(req_blob, dict):
		requirements = [
			r for r in (req_blob.get("requirements") or []) if isinstance(r, dict)
		]
	elif isinstance(req_blob, list):
		requirements = [r for r in req_blob if isinstance(r, dict)]

	approach, milestones, single = _schedule_parts_from_doc(doc)

	cv_blob = _parse_json(getattr(doc, "contract_values", None)) or {}
	values = []
	if isinstance(cv_blob, dict):
		values = [r for r in (cv_blob.get("contract_values") or []) if isinstance(r, dict)]
	elif isinstance(cv_blob, list):
		values = [r for r in cv_blob if isinstance(r, dict)]

	report = resolve_contract_parameters(
		std_version=cstr(getattr(doc, "std_version", None) or ""),
		contract_values=values,
		tds=tds,
		requirements=requirements,
		milestones=milestones,
		single_delivery=single,
		delivery_approach=approach,
	)
	return [
		{"code": b["code"], "message": b["message"]}
		for b in report["blockers"]
	]
