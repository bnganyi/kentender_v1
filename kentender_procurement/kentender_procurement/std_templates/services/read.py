# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`InstalledSTDReleaseProjection v1` — the read projections behind
**STD Templates** (STD-TPL-001 v0.10 §11; STD-TPL-IMP-001 v1.0 §6, §11).

`ListInstalledSTDReleases`, `GetInstalledSTDRelease`,
`ListSTDReleaseCoverage` and `GetSTDReleaseChangeReport`. Every value the
screens show is composed here from the installed release row and its exact
installed assets; the browser never parses a bundle, PDF, filename or raw
manifest to fill a gap. A missing owner fact displays as "Not recorded".
Reads create no business event beyond ordinary access logging.

Owner decision OD5 (26 Sep 2026): a release is usable when it is switched On
on this site, intact and its renderer is registered. Blockers are therefore
derived live from those three facts; the gate results and open review items
recorded at build time are shown as evidence only.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.std_templates.compiler import formats
from kentender_procurement.std_templates.compiler.errors import fail
from kentender_procurement.std_templates.release import coverage as coverage_module
from kentender_procurement.std_templates.services import access, runtime
from kentender_procurement.std_templates.services.installer import load_json

DOCTYPE = "Installed STD Release"
STATUSES: tuple[str, ...] = ("Available", "Unavailable", "Superseded", "Withdrawn")
STATUS_CLASS = {"Available": "is-live", "Unavailable": "is-attention", "Superseded": "is-pending", "Withdrawn": "is-critical"}
RESULT_CLASS = {"Passed": "is-live", "Incomplete": "is-attention", "Pending": "is-pending", "Failed": "is-critical", "On": "is-live", "Off": "is-attention"}
NOT_RECORDED = "Not recorded"
LIST_CONSEQUENCE = "This release cannot be used to publish a Tender. Open it to see why."
CONSEQUENCE = {
	"Available": "This release may be used only for the supported procurements below.",
	"Unavailable": "This release cannot be used to publish a Tender.",
	"Switched off": "New Tenders cannot start on this release while it is switched off on this site. Tenders already started on it may continue.",
	"Superseded": "New Tenders cannot bind this release. Tenders already bound but not yet published may continue only while integrity and renderer checks pass. Published outputs remain readable.",
	"Withdrawn": "New binding is blocked, and Tenders already bound but not yet published cannot be published. Historical published outputs remain readable.",
}
NEXT_STEP = {
	"Available": ("Ready for supported Tenders.", "Next: Procurement Officer."),
	"Unavailable": ("Switched off on this site.", "Whoever manages this site can switch it on."),
	"Failed": ("Release verification failed.", "Waiting on the controlled release owner."),
	"Renderer": ("The document renderer is missing.", "Whoever manages this site must install the renderer this release needs."),
	"Superseded": ("Use the current approved release for new Tenders.", "Next: Procurement Officer."),
	"Withdrawn": ("This release cannot be used.", "Waiting on the controlled release owner."),
}
EMPTY_INSTALLED = "No STD Templates are installed. Ask whoever manages this site to install a release."
SITE_ADMIN = "Site administrator"
VERIFICATION_CAPTION = "These checks were recorded when this release was built. They are for information only; whether this site can use the release depends on its switch, its integrity and its renderer."
SWITCH_ROW = "Site switch"
EMPTY_FILTERED = "No STD Templates match these filters."

_PREFIX_WORDS: tuple[tuple[str, str], ...] = (
	("procuring_entity", "Procuring Entity details"),
	("requisition", "requisition lineage"),
	("plan_item", "plan lineage"),
	("goods", "goods and delivery"),
	("technical_requirements", "technical requirements"),
	("warranty_support", "warranty and support"),
	("acceptance_requirements", "acceptance checks"),
	("related_services", "related services"),
	("supporting_materials", "supporting materials"),
	("reservation", "reservation"),
	("tender.tender_security", "tender security"),
	("tender.approval", "approval record"),
	("tender", "Tender details and dates"),
	("submission", "supplier evidence"),
	("contract", "contract terms"),
	("price", "price treatment"),
	("platform", "platform identity"),
)


# ---------------------------------------------------------------------------
# small formatters
# ---------------------------------------------------------------------------


def eat(value) -> str:
	if not value:
		return ""
	dt = get_datetime(value)
	iso = dt.isoformat()
	if dt.tzinfo is None:
		iso += "+03:00" if (frappe.utils.get_system_timezone() or "") == "Africa/Nairobi" else "+00:00"
	return formats.eat_datetime(iso)


def long_date_or_raw(value: str) -> str:
	value = cstr(value)
	if len(value) >= 10 and value[4] == "-" and value[7] == "-":
		try:
			return formats.long_date(value[:10])
		except ValueError:
			return value
	return value


def _renderer_registered(row) -> bool:
	from kentender_procurement.std_templates.renderers import registry

	return registry.is_registered(row.get("renderer_profile_id"), row.get("supported_renderer_version"))


def availability(row) -> str:
	"""§14.1 as changed by OD5: `Unavailable` is the administrative
	projection of a release switched Off, failing integrity or missing its
	renderer; never a lifecycle value."""
	status = row.get("lifecycle_status")
	if status in ("Superseded", "Withdrawn"):
		return status
	if status == "Available" and row.get("site_switch") == "On" and row.get("integrity_status") == "Verified" and _renderer_registered(row):
		return "Available"
	return "Unavailable"


def use_blockers(release) -> list[dict[str, Any]]:
	"""What stops this site using the release right now, failures first."""
	out: list[dict[str, Any]] = []
	if release.integrity_status == "Failed":
		out.append({"summary": release.integrity_problem or "Release integrity check failed.", "owner": "Controlled template-release owner (bnganyi)", "gate_id": "GATE-INTEGRITY", "severity": "Failed", "kind": "Failed"})
	if not _renderer_registered(release):
		out.append({"summary": "The document renderer this release needs is not installed on this site.", "owner": SITE_ADMIN, "gate_id": "GATE-RENDERER", "severity": "Failed", "kind": "Renderer"})
	if release.lifecycle_status == "Available" and release.site_switch != "On":
		out.append({"summary": "This release is switched off on this site.", "owner": SITE_ADMIN, "gate_id": "", "severity": "Pending", "kind": "Unavailable"})
	return out


def _switch_row(release) -> dict[str, Any]:
	state = "On" if release.site_switch == "On" else "Off"
	who = release.switched_by or NOT_RECORDED
	when = eat(release.switched_at) or NOT_RECORDED
	return {"check": SWITCH_ROW, "result": state, "explanation": f"Switched {state.lower()} by {who} on {when}."}


def _supported_line(use: dict[str, Any]) -> tuple[str, str]:
	cats = [c for c in use.get("reservation_categories", []) if c != "None"]
	first = f"{use.get('procurement_category')} · {use.get('procurement_method')} · {'single lot' if use.get('lotting_indicator') == 'Single lot' else use.get('lotting_indicator')}"
	second = "None/" + "/".join(cats) + "; County restriction conditional" if cats else "No reservation"
	return first, second


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

_LIST_FIELDS = [
	"name", "display_name", "template_key", "template_release", "lifecycle_status", "site_switch", "integrity_status", "renderer_profile_id",
	"supported_renderer_version", "official_source_title", "last_verified_at", "supported_use_summary", "installed_at",
]


def list_installed_releases(*, search: str = "", status: str = "", user: str | None = None) -> dict[str, Any]:
	access.require_reader(user)
	search = cstr(search).strip()
	status = cstr(status).strip()
	if status and status not in STATUSES:
		status = ""
	rows = frappe.get_all(DOCTYPE, fields=_LIST_FIELDS, order_by="template_key asc, installed_at desc", limit_page_length=0)
	installed = len(rows)
	out = []
	needle = search.lower()
	for row in rows:
		state = availability(row)
		if status and state != status:
			continue
		if needle and needle not in cstr(row.display_name).lower() and needle not in cstr(row.template_key).lower():
			continue
		use = load_json(row.supported_use_summary) or {}
		first, second = _supported_line(use)
		out.append(
			{
				"release_id": row.name,
				"display_name": row.display_name,
				"template_key": row.template_key,
				"template_release": row.template_release,
				"supported_use": {"line": first, "detail": second, "label": f"{first} · {second}"},
				"status": state,
				"status_class": STATUS_CLASS[state],
				"consequence": LIST_CONSEQUENCE if state == "Unavailable" else "",
				"official_source": row.official_source_title or NOT_RECORDED,
				"last_verified": eat(row.last_verified_at) or "Not yet verified",
			}
		)
	filtered = bool(search or status)
	return {
		"outcome": "OK",
		"releases": out,
		"installed_count": installed,
		"filters": {"search": search, "status": status, "statuses": ["All statuses", *STATUSES]},
		"empty": (EMPTY_FILTERED if filtered else EMPTY_INSTALLED) if not out else "",
		"empty_kind": ("filtered" if filtered else "installed") if not out else "",
	}


# ---------------------------------------------------------------------------
# detail
# ---------------------------------------------------------------------------


def _plain_areas(labels_and_keys: list[tuple[str, str]]) -> str:
	words: list[str] = []
	for key in labels_and_keys:
		word = next((w for prefix, w in _PREFIX_WORDS if key == prefix or key.startswith(prefix + ".") or key.startswith(prefix)), None)
		if word and word not in words:
			words.append(word)
	if not words:
		return NOT_RECORDED
	text = ", ".join(words[:-1]) + (f" and {words[-1]}" if len(words) > 1 else words[0])
	return text[0].upper() + text[1:]


def _insertion_keys(release) -> dict[str, list[str]]:
	_, rows = coverage_module.read_csv(runtime.asset_bytes(release, "03_registers/insertion_points.csv"))
	by: dict[str, list[str]] = {}
	for row in rows:
		by.setdefault(row["source_treatment"], []).append(row["key"])
	return by


def _change_summary(report: dict[str, Any]) -> dict[str, Any]:
	result = report.get("overall_result") or NOT_RECORDED
	previous = report.get("preceding_release")
	totals = report.get("totals") or {}
	chips = []
	for category, counts in totals.items():
		parts = [f"{n} {kind}" for kind, n in counts.items() if n]
		if parts:
			chips.append(f"{category}: {', '.join(parts)}")
	if previous:
		summary = f"Compared with release {previous}: {len(report.get('changes') or [])} changes."
		heading = f"Changes from release {previous}"
	else:
		summary = "No preceding approved release exists. This release is recorded as an initial inventory."
		heading = "Release comparison"
	return {"heading": heading, "result": result, "summary": summary, "chips": chips, "preceding_release": previous}


def get_installed_release(release_id: str, *, user: str | None = None) -> dict[str, Any]:
	viewer = access.require_reader(user)
	release = runtime.release_doc(release_id)
	state = availability(release)
	use = load_json(release.supported_use_summary) or {}
	rejected = load_json(release.rejected_use_summary) or []
	document = load_json(release.document_summary) or {}
	response = load_json(release.response_summary) or {}
	evaluation = load_json(release.evaluation_summary) or {}
	contract = load_json(release.contract_summary) or {}
	reservation = load_json(release.reservation_support) or {}
	verification = [v for v in (load_json(release.verification_results) or []) if v.get("check") != "Owner approval"]
	blockers = use_blockers(release)
	failed = any(b["severity"] == "Failed" for b in blockers)
	coverage = document.get("coverage") or {}
	try:
		report = runtime.asset_json(release, "05_review/release_change_report.json")
	except Exception:
		report = {}
	keys = _insertion_keys(release)

	head, holder = NEXT_STEP[blockers[0]["kind"] if blockers and state == "Unavailable" else state]
	cats = [c for c in use.get("reservation_categories", []) if c != "None"]
	supported = [
		{"label": "Procurement category", "value": f"{use.get('procurement_category', NOT_RECORDED)} — {use.get('product_pattern', '')}".rstrip(" —")},
		{"label": "Procurement method", "value": use.get("procurement_method") or NOT_RECORDED},
		{"label": "Typical products", "value": ", ".join(use.get("equipment_categories") or []) or NOT_RECORDED},
		{"label": "Related services", "value": use.get("related_service_boundary") or NOT_RECORDED},
		{"label": "Lots", "value": "One lot" if use.get("lotting_indicator") == "Single lot" else cstr(use.get("lotting_indicator") or NOT_RECORDED)},
		{"label": "Currency", "value": use.get("currency") or NOT_RECORDED},
		{"label": "Price", "value": use.get("price_treatment") or NOT_RECORDED},
		{"label": "Reservation support", "value": ("None, " + ", ".join(cats) + "; County residents is a separate conditional restriction") if cats else "None"},
	]
	fixture = response.get("fixture") or {}
	moh = (
		f"{'One grouped' if fixture.get('goods_lines') == 1 else fixture.get('goods_lines')} Goods line from {fixture.get('requisition_items_grouped')} Requisition items; "
		f"{fixture.get('technical_requirements')} technical requirements; {fixture.get('warranty_support_facts')} warranty/support facts; "
		f"{fixture.get('acceptance_checks')} acceptance checks; {'no' if not fixture.get('related_services') else fixture.get('related_services')} related services; "
		f"{'one' if fixture.get('goods_price_schedules') == 1 else fixture.get('goods_price_schedules')} Goods price schedule"
		if fixture
		else NOT_RECORDED
	)
	families = response.get("response_family_rule_counts") or {}
	families_text = (
		f"{len(families)} response families from {sum(families.values())} released response rules: "
		+ ", ".join(f"{name.replace('_', ' ')} {count}" for name, count in sorted(families.items(), key=lambda kv: (-kv[1], kv[0])))
		if families
		else NOT_RECORDED
	)
	destinations = {d["contract_destination_id"]: d for d in (contract.get("destinations") or [])}
	carried = [d["label"] for d in destinations.values() if d.get("response_rule_ids")]
	not_carried_rules = {n["response_rule_id"] for n in contract.get("not_carried_forward") or []}
	not_carried = []
	if any(r.startswith("RR-DECL") or r.startswith("RR-EVIDENCE") or r in ("RR-RESERVATION", "RR-TENDER-SECURITY", "RR-EXPERIENCE") for r in not_carried_rules):
		not_carried.append("Eligibility-only evidence")
	if any(r in ("RR-DOC-ACK", "RR-SUPPLIER-DETAILS", "RR-SUBMISSION") for r in not_carried_rules):
		not_carried.append("Administrative acknowledgements")
	eval_groups = [
		{
			"n": index,
			"name": g["label"],
			"note": "One shared pass/fail gate" if g["evaluation_group_id"] == "EVG-TECHNICAL-COMPLIANCE" else ("Consumes the prior results" if g["evaluation_group_id"] == "EVG-AWARD" else ""),
			"rule_count": g.get("response_rule_count", 0),
		}
		for index, g in enumerate(evaluation.get("groups") or [], start=1)
	]
	treatments = [{"label": label, "n": (coverage.get("treatment_totals") or {}).get(label, 0)} for label in coverage_module.BUCKETS]
	source_check = {
		"last_checked": long_date_or_raw(release.source_checked_at) or NOT_RECORDED,
		"checked_by": release.source_checked_by or NOT_RECORDED,
		"outcome": release.source_check_outcome or NOT_RECORDED,
	}
	technical = [
		{"label": "Release ID", "value": release.release_id},
		{"label": "Manifest identity", "value": release.manifest_digest},
		{"label": "Product profile", "value": release.product_profile_id},
		{"label": "Renderer profile", "value": release.renderer_profile_id},
		{"label": "Supported renderer version", "value": release.supported_renderer_version},
		{
			"label": "Constituent digests",
			"value": "; ".join(
				f"{label} {getattr(release, field)}"
				for label, field in (
					("bundle", "bundle_digest"), ("input", "input_bundle_digest"), ("source", "official_source_digest"),
					("product profile", "product_profile_digest"), ("response rules", "response_rules_digest"),
					("downstream rules", "downstream_rules_digest"), ("addendum rules", "addendum_identity_rules_digest"),
					("gates", "release_gates_digest"), ("change report", "release_change_report_digest"), ("validation report", "validation_report_digest"),
				)
			),
			"copy": True,
		},
		{"label": "Repository commit", "value": release.repository_commit or NOT_RECORDED},
		{
			"label": "Owner decision",
			"value": f"{release.owner_decision} by {release.owner_approved_by} on {long_date_or_raw(release.owner_approved_at)}" if release.owner_decision else NOT_RECORDED,
		},
		{"label": "Schema versions", "value": "Runtime assets 1; manifest 1; InstalledSTDReleaseProjection 1; PublishedBidDefinition 1"},
	]
	variant: dict[str, Any] = {}
	if failed:
		variant["earlier_success"] = (
			f"Last successful verification {eat(release.last_successful_verification_at)}" if release.last_successful_verification_at else "No earlier successful verification is recorded."
		)
	if release.lifecycle_status == "Superseded":
		variant["successor"] = _release_label(release.superseded_by_release_id) or ""
	if release.lifecycle_status == "Withdrawn":
		variant["withdrawal"] = [
			{"label": "Reason", "value": release.withdrawal_reason or ""},
			{"label": "Recorded", "value": eat(release.withdrawn_at)},
			{"label": "Actor", "value": release.withdrawn_by or ""},
			{"label": "Successor", "value": _release_label(release.withdrawal_successor_release_id) or ""},
		]
	from kentender_procurement.std_templates.services import concerns

	return {
		"outcome": "OK",
		"release": {
			"release_id": release.name,
			"display_name": release.display_name,
			"template_key": release.template_key,
			"template_release": release.template_release,
			"status": state,
			"status_class": STATUS_CLASS[state],
			"lifecycle_status": release.lifecycle_status,
			"failed_verification": failed,
			"consequence": CONSEQUENCE["Switched off" if state == "Unavailable" and blockers and blockers[0]["kind"] == "Unavailable" else state],
			"next_step": {"head": head, "holder": holder},
		},
		"blockers": [
			{"n": index, "text": b["summary"], "owner": b["owner"], "failed": b.get("severity") == "Failed", "gate_id": b.get("gate_id") or ""}
			for index, b in enumerate(blockers, start=1)
		],
		"overview": {
			"supported": supported,
			"not_supported": [r["statement"] for r in rejected],
			"release": {"template_release": release.template_release, "status": state, "status_class": STATUS_CLASS[state]},
			"official_source": {
				"title": release.official_source_title or NOT_RECORDED,
				"source_owner": "Public Procurement Regulatory Authority (PPRA)" if "PPRA" in cstr(release.official_source_title) else NOT_RECORDED,
				"retrieval_date": long_date_or_raw(release.source_retrieved_at) or NOT_RECORDED,
			},
		},
		"tender_content": {
			"outputs": [
				{"output_id": o["output_id"], "title": o["title"], "summary": o["summary"]}
				for o in document.get("outputs") or []
			],
			"coverage_line": (
				f"{coverage.get('source_rows_reviewed')} of {coverage.get('source_rows_total')} rows reviewed; {coverage.get('forms_total')} forms accounted for"
				if coverage
				else NOT_RECORDED
			),
			"inherited": _plain_areas(keys.get("Inherited", [])),
			"entered": _plain_areas(keys.get("Officer value", [])),
			"generated": _plain_areas(keys.get("Generated", [])) + "; the Invitation, issued Tender, response definition and price calculations",
		},
		"bid_response": {
			"tasks": [{"n": t["order"], "name": t["label"], "purpose": t["purpose"]} for t in response.get("tasks") or []],
			"controls": response.get("controls") or [],
			"response_families": families_text,
			"fixture_content": moh,
			"reservation_evidence": (
				"Evaluated as eligibility pass/fail. The category and result are kept as Award and reporting context, not as a contract obligation."
				if reservation.get("eligibility_group_id") == "EVG-ELIGIBILITY"
				else NOT_RECORDED
			),
			"declarations": response.get("declaration_treatment") or NOT_RECORDED,
			"evidence": response.get("evidence_treatment") or NOT_RECORDED,
			"price": response.get("price_treatment") or NOT_RECORDED,
			"evaluation_groups": eval_groups,
			"carried": carried,
			"not_carried": not_carried,
		},
		"coverage": {
			"treatments": treatments,
			"total": coverage.get("source_rows_total", 0),
			"forms_total": coverage.get("forms_total", 0),
			"mapping_rule": coverage.get("mapping_rule", ""),
			"changes": _change_summary(report),
		},
		"verification": {
			"caption": VERIFICATION_CAPTION,
			"rows": [
				{"check": v["check"], "result": v["result"], "result_class": RESULT_CLASS.get(v["result"], "is-pending"), "note": v["explanation"]}
				for v in [*verification, _switch_row(release)]
			],
			"source": source_check,
		},
		"variant": variant,
		"technical": technical,
		"last_verified": eat(release.last_verified_at) or "Not yet verified",
		"concerns": concerns.summary_for(release.name, user=user),
		"allowed_actions": ["preview", "download_review_pack", "view_coverage", "view_changes", "report_concern"],
		"viewer": {"technical": viewer["technical"]},
	}


def _release_label(release_id: str | None) -> str:
	if not release_id:
		return ""
	row = frappe.db.get_value(DOCTYPE, release_id, ["display_name", "template_release"], as_dict=True)
	return f"{row.display_name} · Release {row.template_release}" if row else release_id


# ---------------------------------------------------------------------------
# coverage and change details (server-paged)
# ---------------------------------------------------------------------------


def _page(rows: list[dict[str, Any]], page: int, page_length: int) -> dict[str, Any]:
	page_length = max(10, min(int(page_length or 25), 100))
	total = len(rows)
	pages = max(1, (total + page_length - 1) // page_length)
	page = max(1, min(int(page or 1), pages))
	start = (page - 1) * page_length
	return {"rows": rows[start : start + page_length], "total": total, "page": page, "pages": pages, "page_length": page_length}


def list_release_coverage(release_id: str, *, search: str = "", treatment: str = "", page: int = 1, page_length: int = 25, user: str | None = None) -> dict[str, Any]:
	access.require_reader(user)
	release = runtime.release_doc(release_id)
	_, cov = coverage_module.read_csv(runtime.asset_bytes(release, "03_registers/coverage_register.csv"))
	_, ins = coverage_module.read_csv(runtime.asset_bytes(release, "03_registers/insertion_points.csv"))
	rows = coverage_module.coverage_rows(cov, ins)
	treatment = cstr(treatment).strip()
	if treatment in coverage_module.BUCKETS:
		rows = [r for r in rows if r["treatment"] == treatment]
	needle = cstr(search).strip().lower()
	if needle:
		rows = [r for r in rows if needle in (r["coverage_id"] + " " + r["source_locator"] + " " + r["title"] + " " + r["output_anchor"] + " " + r["reason"]).lower()]
	return {"outcome": "OK", "filters": {"search": cstr(search).strip(), "treatment": treatment, "treatments": list(coverage_module.BUCKETS)}, **_page(rows, page, page_length)}


def get_release_change_report(release_id: str, *, category: str = "", page: int = 1, page_length: int = 25, user: str | None = None) -> dict[str, Any]:
	access.require_reader(user)
	release = runtime.release_doc(release_id)
	report = runtime.asset_json(release, "05_review/release_change_report.json")
	changes = report.get("changes") or []
	categories = [c for c in (report.get("totals") or {}) if any(ch["category"] == c for ch in changes)]
	category = cstr(category).strip()
	if category in categories:
		changes = [c for c in changes if c["category"] == category]
	order = {"Breaking": 0, "Compatible": 1}
	changes = sorted(changes, key=lambda c: (categories.index(c["category"]) if c["category"] in categories else 99, order.get(c["compatibility_effect"], 2), c["identity"]))
	return {
		"outcome": "OK",
		"summary": _change_summary(report),
		"filters": {"category": category, "categories": categories},
		**_page(
			[
				{"category": c["category"], "change": c["change_kind"].capitalize(), "identity": c["identity"], "summary": c["summary"], "effect": c["compatibility_effect"]}
				for c in changes
			],
			page,
			page_length,
		),
	}
