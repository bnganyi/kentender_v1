# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic package-level render preview from imported STD data."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

import frappe

from kentender_procurement.std_engine.services.tender_binding_service import assert_version_is_bindable

WATERMARK = "DRAFT PREVIEW — NOT FOR PUBLICATION"
NSSF_COMPRESSED_MARKERS = (
	"WARNING_LOCKED_ITT_TEXT_COMPRESSED",
	"WARNING_LOCKED_GCC_TEXT_COMPRESSED",
)


def compute_render_hash(html: str) -> str:
	normalized = re.sub(r"\s+", " ", (html or "").strip())
	return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def resolve_placeholders(text: str, parameter_values: dict[str, str] | None) -> str:
	if not text:
		return ""
	values = parameter_values or {}
	output = text
	for key, value in values.items():
		for pattern in (f"{{{{{key}}}}}", f"[[{key}]]", f"{{{key}}}"):
			output = output.replace(pattern, str(value))
	return output


def render_section_preview(
	package_id: str,
	section_key: str,
	*,
	parameter_values: dict[str, str] | None = None,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	assert_version_is_bindable(package_id, simulate_active_for_test=simulate_active_for_test)
	section_key = (section_key or "").strip()
	clauses = frappe.get_all(
		"STD Clause",
		filters={"package_id": package_id, "section": section_key},
		fields=["clause_key", "clause_text", "title"],
		order_by="clause_key asc",
	)
	if not clauses:
		clauses = frappe.get_all(
			"STD Clause",
			filters={"package_id": package_id, "section": ["like", f"%{section_key}%"]},
			fields=["clause_key", "clause_text", "title"],
			order_by="clause_key asc",
		)
	body_parts = []
	for clause in clauses:
		text = resolve_placeholders(clause.get("clause_text") or "", parameter_values)
		title = clause.get("title") or clause.get("clause_key")
		body_parts.append(f"<section data-clause-key=\"{frappe.utils.escape_html(clause['clause_key'])}\">")
		body_parts.append(f"<h3>{frappe.utils.escape_html(title)}</h3>")
		body_parts.append(f"<div class=\"clause-text\">{frappe.utils.escape_html(text)}</div>")
		body_parts.append("</section>")

	html = _wrap_html(section_key, "\n".join(body_parts))
	render_hash = compute_render_hash(html)
	_assert_no_nssf_compressed_markers(html)
	return {
		"packageId": package_id,
		"sectionKey": section_key,
		"html": html,
		"renderHash": render_hash,
		"clauseCount": len(clauses),
		"watermark": WATERMARK,
	}


def render_block_preview(
	package_id: str,
	block_key: str,
	*,
	parameter_values: dict[str, str] | None = None,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	block_key = (block_key or "").strip()
	block = frappe.db.get_value(
		"STD Render Block",
		block_key,
		["name", "render_block_key", "object_key", "title", "metadata_json"],
		as_dict=True,
	)
	if not block:
		block = frappe.db.get_value(
			"STD Render Block",
			{"package_id": package_id, "object_key": block_key},
			["name", "render_block_key", "object_key", "title", "metadata_json"],
			as_dict=True,
		)
	if not block:
		frappe.throw(f"Render block {block_key} not found.", title="RENDER_BLOCK_NOT_FOUND")

	metadata = _parse_metadata(block.metadata_json)
	section_key = metadata.get("applies_to_section_key") or _section_key_from_block(block)
	preview = render_section_preview(
		package_id,
		section_key,
		parameter_values=parameter_values,
		simulate_active_for_test=simulate_active_for_test,
	)
	_record_render_probe(block.name, preview["renderHash"])
	preview["blockKey"] = block.render_block_key or block.name
	preview["blockTitle"] = block.title
	return preview


def probe_all_render_blocks(
	package_id: str,
	*,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	rows = frappe.get_all(
		"STD Render Block",
		filters={"package_id": package_id},
		fields=["name", "render_block_key", "object_key"],
		order_by="render_block_key asc",
	)
	results = []
	for row in rows:
		try:
			preview = render_block_preview(
				package_id,
				row.render_block_key or row.name,
				simulate_active_for_test=simulate_active_for_test,
			)
			results.append(
				{
					"blockKey": preview.get("blockKey"),
					"ok": True,
					"renderHash": preview.get("renderHash"),
				}
			)
		except Exception as exc:
			results.append(
				{
					"blockKey": row.render_block_key or row.name,
					"ok": False,
					"error": str(exc),
				}
			)
	return {
		"packageId": package_id,
		"total": len(rows),
		"passed": sum(1 for item in results if item.get("ok")),
		"results": results,
	}


def get_render_probe_status(package_id: str) -> dict[str, Any]:
	rows = frappe.get_all(
		"STD Render Block",
		filters={"package_id": package_id},
		fields=["render_block_key", "object_key", "metadata_json"],
		order_by="render_block_key asc",
	)
	items = []
	for row in rows:
		metadata = _parse_metadata(row.metadata_json)
		items.append(
			{
				"blockKey": row.render_block_key or row.object_key,
				"lastRenderTest": metadata.get("last_render_test") or "NOT_RUN",
				"lastRenderHash": metadata.get("last_render_hash"),
				"lastRenderAt": metadata.get("last_render_at"),
			}
		)
	return {"packageId": package_id, "items": items, "count": len(items)}


def _wrap_html(section_key: str, body: str) -> str:
	return (
		f"<article class=\"std-render-preview\" data-section=\"{frappe.utils.escape_html(section_key)}\">"
		f"<header><p class=\"watermark\">{WATERMARK}</p></header>"
		f"{body}"
		"</article>"
	)


def _record_render_probe(block_name: str, render_hash: str) -> None:
	metadata = _parse_metadata(frappe.db.get_value("STD Render Block", block_name, "metadata_json"))
	metadata["last_render_test"] = "SUCCESS"
	metadata["last_render_hash"] = render_hash
	metadata["last_render_at"] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
	frappe.db.set_value(
		"STD Render Block",
		block_name,
		"metadata_json",
		json.dumps(metadata, sort_keys=True, default=str),
		update_modified=False,
	)


def _assert_no_nssf_compressed_markers(html: str) -> None:
	for marker in NSSF_COMPRESSED_MARKERS:
		if marker in (html or ""):
			frappe.throw(
				f"Render must use official STD text, not NSSF compressed substitute ({marker}).",
				title="CAL_NSSF_012_VIOLATION",
			)


def _section_key_from_block(block) -> str:
	object_key = (block.object_key or block.render_block_key or "").strip()
	if ".render." in object_key:
		return object_key.replace(".render.", ".section.", 1)
	return object_key


def _parse_metadata(raw: str | None) -> dict[str, Any]:
	if not raw:
		return {}
	try:
		parsed = json.loads(raw)
	except json.JSONDecodeError:
		return {}
	return parsed if isinstance(parsed, dict) else {}
