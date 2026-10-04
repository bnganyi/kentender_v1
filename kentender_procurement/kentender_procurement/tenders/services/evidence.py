# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.4 — officer-authored `TenderEvidenceRequirement`
rows. Every row must prove a published inherited requirement (a visible
inherited identity of the stated type); it cannot create a hidden
qualification threshold or a new technical obligation (TPR08-AC-016/017).
The supplier evidence the §5.2 switches imply (manufacturer authorisation,
datasheets, warranty confirmation, experience, after-sales) is generated
into the evaluation contract by the serializer, never stored as rows."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.tenders.services import snapshot as snap

EVIDENCE_TYPES = ("Declaration", "Certificate", "Datasheet or brochure", "Schedule or form", "Other document")
LINK_TYPES = tuple(snap.VISIBLE_TYPES)
FIELDS = ("label", "evidence_type", "linked_requirement_type", "linked_requirement_id", "mandatory")


def validate_values(values: dict[str, Any], snapshot: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
	errors: dict[str, str] = {}
	clean: dict[str, Any] = {}
	if not isinstance(values, dict):
		return {}, {"values": "Evidence values must be an object."}
	label = values.get("label")
	if not isinstance(label, str) or not (3 <= len(label.strip()) <= 160) or any(t in label for t in ("<", ">", "**", "```")):
		errors["label"] = "Enter plain text of 3–160 characters."
	else:
		clean["label"] = label.strip()
	if values.get("evidence_type") not in EVIDENCE_TYPES:
		errors["evidence_type"] = "Choose one of: " + ", ".join(EVIDENCE_TYPES) + "."
	else:
		clean["evidence_type"] = values["evidence_type"]
	link_type = values.get("linked_requirement_type")
	if link_type not in LINK_TYPES:
		errors["linked_requirement_type"] = "Choose one of: " + ", ".join(LINK_TYPES) + "."
	else:
		clean["linked_requirement_type"] = link_type
		visible = snap.visible_ids(snapshot).get(link_type, set())
		link_id = cstr(values.get("linked_requirement_id")).strip() or (snap.WARRANTY_ID if link_type == "Warranty/support" else "")
		if link_id not in visible:
			errors["linked_requirement_id"] = "Choose a published inherited requirement of that type."
		else:
			clean["linked_requirement_id"] = link_id
	mandatory = values.get("mandatory", True)
	if isinstance(mandatory, bool) or mandatory in (0, 1, "0", "1", "true", "false"):
		clean["mandatory"] = 1 if mandatory in (True, 1, "1", "true") else 0
	else:
		errors["mandatory"] = "Choose Yes or No."
	for name in set(values) - set(FIELDS):
		errors[name] = "Unknown field."
	return clean, errors


def next_id(version) -> str:
	existing = {r.evidence_requirement_id for r in version.get("evidence_requirements") or []}
	n = 1
	while f"EV-{n:03d}" in existing:
		n += 1
	return f"EV-{n:03d}"


def rows_as_dicts(version) -> list[dict[str, Any]]:
	return [
		{
			"evidence_requirement_id": r.evidence_requirement_id, "label": r.label, "evidence_type": r.evidence_type,
			"linked_requirement_type": r.linked_requirement_type, "linked_requirement_id": r.linked_requirement_id,
			"mandatory": bool(r.mandatory), "row_order": int(r.row_order or 0),
		}
		for r in sorted(version.get("evidence_requirements") or [], key=lambda x: x.row_order or 0)
	]


def technical_ids_with_evidence(rows: list[dict[str, Any]]) -> set[str]:
	return {r["linked_requirement_id"] for r in rows if r["linked_requirement_type"] == "Technical requirement"}


def unlinked_rows(rows: list[dict[str, Any]], snapshot: dict[str, Any]) -> list[str]:
	visible = snap.visible_ids(snapshot)
	return [r["evidence_requirement_id"] for r in rows if r["linked_requirement_id"] not in visible.get(r["linked_requirement_type"], set())]


def proves_label(row: dict[str, Any], snapshot: dict[str, Any]) -> str:
	"""§10.5 "Proves" column: the published requirement the row proves, in
	plain words (e.g. `Electrical compatibility — Yes`)."""
	from kentender_procurement.tenders.services import serializer

	link_type, link_id = row["linked_requirement_type"], row["linked_requirement_id"]
	if link_type == "Technical requirement":
		for tech in serializer.technical_rows(snapshot):
			if tech["technical_requirement_id"] == link_id:
				value = tech["required_value"] + (f" {tech['unit']}" if tech["unit"] else "")
				return f"{tech['label']} — {value}"
	if link_type == "Item":
		for item in snapshot.get("items") or []:
			if item.get("requisition_item_id") == link_id:
				return f"{item.get('item_name')} — {serializer.fmt_quantity(item.get('quantity'))} {item.get('unit') or 'Each'}"
	if link_type == "Service":
		for service in snapshot.get("related_services") or []:
			if service.get("service_requirement_id") == link_id:
				return f"{service.get('service_type')} — {service.get('required_result')}"
	if link_type == "Warranty/support":
		return f"Warranty and support — minimum {serializer.fmt_number(snapshot.get('minimum_warranty_months'))} months"
	return link_id
