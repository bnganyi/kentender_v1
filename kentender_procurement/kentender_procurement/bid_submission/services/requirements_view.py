# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-09 shows (BDS-CHG-001 v0.8 §10.10; plan Phase 11, slice
11.9), grouped by the definition's own compositions — never by board rows:

- one link per region with its state (offered goods, technical requirements,
  warranty and support, experience, acceptance where the Tender has it,
  evidence);
- the offered goods form beside the published quantity, delivery location
  and latest delivery;
- one row per technical and per warranty/support requirement: the published
  requirement, this bid's response, its files and state; the row's fields
  open in the response drawer;
- the comparable contracts the Tender asks for, one row each;
- the supporting evidence the Tender lists, with each file and its check;
- what must be fixed, or reviewed after an addendum, before submitting.

Nothing here saves anything."""

from __future__ import annotations

import json
from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import controls, labels

TITLE = "Requirements and supporting evidence"
DESCRIPTION = "State what you are offering and attach the evidence requested by the Tender."
REGIONS = (
	("goods", "Offered goods", ("COMP-GOODS-OFFER",)),
	("technical", "Technical requirements", ("COMP-TECHNICAL-COMPLIANCE",)),
	("warranty", "Warranty and support", ("COMP-WARRANTY-SUPPORT",)),
	("experience", "Experience", ("COMP-EXPERIENCE",)),
	("acceptance", "Acceptance terms", ("COMP-ACCEPTANCE",)),
	("evidence", "Evidence", ("COMP-EVIDENCE-LIST",)),
)
BADGE_TONES = {"Complete": "live", "Needs attention": "attention"}


def _display(field: dict[str, Any]) -> str:
	value = field.get("value")
	if value in (None, "", []):
		return ""
	if field["kind"] == "ports" and isinstance(value, list):
		return "; ".join(f"{cstr(p.get('port_type'))} ×{p.get('count')}" for p in value)
	if field["kind"] == "row_group":
		return controls.describe_rows((field.get("row_group") or {}).get("columns") or [], value)
	if isinstance(value, list):
		return ", ".join(cstr(v) for v in value)
	if field["kind"] == "date":
		return labels.date_label(value)
	if field["kind"] == "confirmation":
		return "Confirmed" if value else ""
	return cstr(value)


def _files(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
	return [f for field in fields if field["kind"] == "evidence" for f in (field.get("evidence") or {}).get("files") or []]


def _files_status(files: list[dict[str, Any]]) -> str:
	"""One status for a requirement's files: none is Missing; a refused file
	outranks the rest, then any not yet accepted (Pending); otherwise Accepted."""
	if not files:
		return "Missing"
	for status in ("Rejected", "Pending"):
		if any(f["status"] == status for f in files):
			return status
	return next((f["status"] for f in files if f["status"] != "Accepted"), "Accepted")


def _summary(files: list[dict[str, Any]]) -> dict[str, Any]:
	"""What a table cell says about a row's files: how many it holds and, for a
	hover only, their names; a refused file is not held, only reported (a row can
	hold one file and have another refused)."""
	held = [f["name"] for f in files if f["status"] != "Rejected"]
	return {"evidence_count": len(held), "evidence_names": held, "evidence_rejected": any(f["status"] == "Rejected" for f in files)}


def _accepted(field: dict[str, Any]) -> bool:
	return any(x["status"] == "Accepted" for x in (field.get("evidence") or {}).get("files") or [])


def _row_status(fields: list[dict[str, Any]]) -> str:
	shown = [f for f in fields if f.get("visible", True) and f["editable"]]
	answered = [f for f in shown if f["kind"] != "evidence" and f.get("value") not in (None, "", [], False)]
	rejected = any(file["status"] == "Rejected" for file in _files(shown))
	missing_proof = bool(answered) and any(f["kind"] == "evidence" and f.get("required") and not _accepted(f) for f in shown)
	if rejected or missing_proof:
		return "Needs evidence"
	if any(f.get("issue") and f["issue"].get("severity") == "Must fix" and f.get("value") not in (None, "", []) for f in shown):
		return "Needs attention"
	if not answered and not _files(shown):
		return "Not started"
	if any(f.get("issue") and f["issue"].get("severity") == "Must fix" for f in shown):
		return "In progress"
	return "Complete"


def _tone(status: str) -> str:
	return {"Complete": "live", "Needs evidence": "attention", "Needs attention": "attention"}.get(status, "draft")


NUMERIC_CONTROLS = ("INTEGER", "DECIMAL")


def _requirement(published: dict[str, Any]) -> str:
	"""The requirement as the Tender states it: its comparison, value and unit."""
	display = cstr(published.get("required_value_display"))
	if not display:
		return cstr(published.get("requirement_text") or "")
	unit = cstr(published.get("unit"))
	if unit and not display.endswith(unit):
		display = f"{display} {unit}"
	comparison = cstr(published.get("comparison"))
	if comparison in ("Minimum", "Maximum") and cstr(published.get("control")) in NUMERIC_CONTROLS:
		return f"{comparison} {display}"
	return display


def _label(group: dict[str, Any], published: dict[str, Any], composition: str) -> str:
	if composition == "COMP-EXPERIENCE" and published.get("entry_number"):
		return f"Contract {published['entry_number']}"
	if composition == "COMP-ACCEPTANCE" and published.get("pass_condition"):
		return f"{cstr(published.get('check_type'))}: {cstr(published['pass_condition'])}" if published.get("check_type") else cstr(published["pass_condition"])
	return group["heading"]


def _response(fields: list[dict[str, Any]]) -> str:
	offered = next((f for f in fields if f["kind"] not in ("evidence", "long_text") and "compliance" not in f["label"].lower()), None)
	comment = next((f for f in fields if f["kind"] == "long_text" and f.get("value")), None)
	text = _display(offered) if offered else ""
	if comment:
		text = f"{text} — {cstr(comment['value'])}" if text else cstr(comment["value"])
	return text


def _row(group: dict[str, Any], composition: str, published: dict[str, Any]) -> dict[str, Any]:
	fields = group["fields"]
	status = _row_status(fields)
	files = _files(fields)
	row = {
		"key": group["key"], "label": _label(group, published, composition), "requirement": _requirement(published), "response": _response(fields),
		"evidence": ", ".join(f["name"] for f in files if f["status"] != "Rejected") or ("Rejected file" if files else "—"),
		# the table shows how many files the row holds; the names are for a hover, never the layout
		**_summary(files),
		"status": status, "tone": _tone(status), "facts": group.get("facts") or [], "statement": group.get("statement", ""), "fields": fields,
	}
	if composition == "COMP-ACCEPTANCE":
		row.update(_term(row))
	return row


def _term(row: dict[str, Any]) -> dict[str, Any]:
	"""An acceptance requirement reads as a contract term the bidder accepts,
	not as an answer: what is checked, when it passes, the record it needs, and
	whether the bidder has accepted it yet."""
	facts = {f["label"]: cstr(f["value"]) for f in row["facts"]}
	accepted = row["status"] == "Complete"
	return {
		"term": {"check": facts.get("Check", ""), "passes_when": facts.get("Passes when", ""), "evidence": facts.get("Evidence", ""), "applies_to": facts.get("Applies to", "")},
		"accepted": accepted, "accept_status": "Accepted" if accepted else "Not accepted yet", "accept_tone": "live" if accepted else "draft",
	}


# the page's own order: the regions as the bidder meets them
FIX_ORDER = ("goods", "technical", "warranty", "experience", "acceptance", "evidence")


def must_fix(by_region: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
	"""Every row that blocks submission, in page order, saying what is missing: the
	row, the first field that is wrong and why, and how many more. A row with a
	refused file keeps its plain wording. Untouched rows with nothing required, and
	fields the bidder is not asked, do not block."""
	items = []
	for region in FIX_ORDER:
		for r in by_region.get(region, []):
			if r["status"] == "Complete":
				continue
			rejected = r["status"] == "Needs evidence" and (r.get("evidence_rejected") or "Rejected" in r.get("evidence", ""))  # a row may hold one good file and have another refused
			problems = [f for f in r["fields"] if f.get("visible", True) and f.get("editable") and f.get("issue") and f["issue"].get("severity") == "Must fix"]
			if rejected:
				label = f"Replace the rejected file for {r['label'].lower()}"
			elif problems:
				first = problems[0]
				label = f"{r['label']}: {first['label']} — {first['issue']['text']}" + (f" (and {len(problems) - 1} more)" if len(problems) > 1 else "")
			elif r["status"] in ("Needs attention", "Needs evidence"):
				label = f"Complete {r['label'].lower()}"
			else:
				continue
			items.append({"key": r["key"], "label": label})
	return items


_must_fix = must_fix

# the section bar says it in the same words as the terms
TERMS_STATE = {"Complete": "Accepted", "Not started": "Not accepted yet", "In progress": "Partly accepted"}


def view(ctx, tasks, task_view: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	by_region: dict[str, list[dict[str, Any]]] = {key: [] for key, _label, _c in REGIONS}
	region_of = {c: key for key, _label, comps in REGIONS for c in comps}
	for group, shown in zip(ctx.model.groups_of("requirements"), task_view["groups"]):
		region = region_of.get(group.composition_id)
		if region:
			by_region[region].append(_row(shown, group.composition_id, group.published_facts or {}))

	goods = by_region["goods"][0] if by_region["goods"] else None
	experience_facts = {}
	if by_region["experience"]:
		experience_facts = {f["label"]: f["value"] for f in by_region["experience"][0]["facts"]}
	count, years = experience_facts.get("Contracts required"), experience_facts.get("Within the last (years)")
	experience_rows = []
	for row in by_region["experience"]:
		values = {f["label"]: _display(f) for f in row["fields"] if f["kind"] != "evidence"}
		experience_rows.append({
			**row, "customer": values.get("Client", ""), "supply": values.get("Contract name or reference", "") or values.get("Description", ""),
			"completed": values.get("Completion date", ""), "evidence": ", ".join(f["name"] for f in _files(row["fields"])) or "—",
			**_summary(_files(row["fields"])),
		})
	evidence_rows = []
	for row in by_region["evidence"]:
		files = _files(row["fields"])
		file = files[-1] if files else None
		status = _files_status(files)
		evidence_rows.append({**row, "file": file["name"] if file else "", "file_status": status, "file_tone": {"Accepted": "live", "Rejected": "critical", "Missing": "draft"}.get(status, "attention")})

	sections = []
	for key, label, _comps in REGIONS:
		rows = by_region[key]
		if not rows:
			continue
		worst = next((s for s in ("Needs attention", "Needs evidence", "In progress", "Not started") if any(r["status"] == s for r in rows)), "Complete")
		state = "Needs attention" if worst in ("Needs attention", "Needs evidence") else ("Complete" if worst == "Complete" else "In progress" if any(r["status"] == "Complete" for r in rows) or worst == "In progress" else "Not started")
		tone = BADGE_TONES.get(state, "draft")
		if key == "acceptance":
			state = TERMS_STATE.get(state, state)
		sections.append({"key": key, "label": label, "status": state, "tone": tone})

	must_fix = _must_fix(by_region)
	attention = None
	changed = "requirements" in json.loads(ctx.workspace.attention_json or "[]")
	if must_fix:
		attention = {"tone": "critical", "title": f"Fix {len(must_fix)} item{'s' if len(must_fix) != 1 else ''}", "items": must_fix}
	elif changed:
		review = [{"key": r["key"], "label": f"Review {r['label'].lower()}"} for r in by_region["goods"] + by_region["technical"] + by_region["warranty"]][:1]
		attention = {"tone": "warning", "title": "Review 1 changed response", "items": review} if review else None

	status = tasks["requirements"].status
	published_goods = []
	if goods:
		wanted = ("Quantity", "Delivery location", "Latest delivery")
		published_goods = [{"label": f"{f['label']} · published", "value": f["value"]} for f in goods["facts"] if f["label"] in wanted]
	return {
		"page": {"title": TITLE, "description": DESCRIPTION, "back_href": f"/tenders/{ws.tender_reference}/bid"},
		"badge": {"label": status, "tone": BADGE_TONES.get(status, "draft")},
		"sections": sections, "attention": attention,
		"goods": {"key": goods["key"], "fields": goods["fields"], "published": published_goods} if goods else None,
		"technical": by_region["technical"], "warranty": by_region["warranty"],
		"experience": {"text": f"Provide at least {count} comparable contracts completed within the last {years} years." if count and years else "", "rows": experience_rows} if experience_rows else None,
		"acceptance": by_region["acceptance"], "evidence": evidence_rows,
		"footer": {"save_label": "Save and continue", "next_href": f"/tenders/{ws.tender_reference}/bid/price"},
	}
