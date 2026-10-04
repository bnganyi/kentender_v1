# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Filling a Draft through the real commands (BDS-CHG-001 v0.8 plan Phases
11–12): every visible editable answer from the field's own published limits,
every required file, and the Tender contact's telephone. Used by the tests,
the browser worlds and the canonical seed — never by a user."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe


def key() -> str:
	return f"bds-fill-{uuid4().hex}"


def pdf(text: str = "") -> bytes:
	"""A readable one-page PDF (Frappe parses uploads, so the bytes must be real)."""
	from io import BytesIO

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=595, height=842)
	if text:
		writer.add_metadata({"/Title": text})
	buffer = BytesIO()
	writer.write(buffer)
	return buffer.getvalue()


def _sample_row(table: dict[str, Any]) -> dict[str, Any]:
	"""One row the table accepts: a total, where one is published, is met by this single row."""
	totals = {t["column"]: t["equals"] for t in table.get("totals") or []}
	row: dict[str, Any] = {}
	for column in table["columns"]:
		kind = column["type"]
		if column["key"] in totals:
			row[column["key"]] = totals[column["key"]]
		elif kind == "choice":
			row[column["key"]] = column["options"][0]
		elif kind == "integer":
			row[column["key"]] = 1
		elif kind == "decimal":
			row[column["key"]] = "1.00"
		else:
			row[column["key"]] = "Seeded entry"
	return row


def sample_value(field: dict[str, Any]):
	"""A value the field's own published limits accept (answers only; the bid
	does not evaluate them)."""
	kind, limits, options = field["kind"], field.get("limits") or {}, field.get("options") or []
	if kind == "confirmation":
		return True
	if kind in ("yes_no", "single_choice"):
		return options[0]
	if kind == "multi_select":
		return [options[0]]
	if kind == "ports":
		return [{"port_type": options[0], "count": 1}]
	if kind == "row_group":
		return [_sample_row(field["row_group"])]
	if kind in ("short_text", "long_text"):
		text = "Seeded answer for the canonical bid."
		low, high = int(limits.get("min_length", 0)), int(limits.get("max_length", 500))
		return (text * (low // len(text) + 1))[: max(low, min(len(text), high))]
	if kind == "integer":
		return int(limits.get("minimum", 1))
	if kind in ("decimal", "money"):
		return str(limits.get("minimum", "1.00"))
	if kind == "date":
		return str(limits.get("not_before") or limits.get("not_after") or "2027-06-01")
	raise ValueError(kind)


def fill_everything(bid: str, *, user: str, tasks: tuple[str, ...] = ("company", "requirements", "price"), answers: dict[str, dict[str, object]] | None = None) -> None:
	"""Answer every visible editable field, add every required file and give the
	Tender contact's telephone, through the real commands. `tasks` limits the
	tasks answered; `answers` gives a task's values by field handle (the
	canonical seed's §10.1 facts), used in place of the sample value."""
	from kentender_procurement.bid_submission.services import evidence, reads, save, tender_contact

	def version():
		return frappe.db.get_value("Bid Workspace", bid, "record_version")

	arrangement = frappe.db.get_value("Bid Workspace", bid, "bidder_arrangement")
	tender_contact.update_tender_contact(bid_reference=bid, email=user, phone="+254 709 555 015", expected_record_version=frappe.db.get_value("Bidder Arrangement", arrangement, "record_version"), idempotency_key=key(), user=user)
	from kentender_procurement.bid_submission.services import bid_context, clock, consistency

	model = bid_context.load(bid, actor=user, organisation="", at=clock.now()).model

	def answer(field: dict[str, Any]):
		# an offered value is truthful: one that meets the requirement it is offered against (Compliance says Comply)
		if field["label"] == "Offered value":
			meeting = consistency.meeting_value(model.by_handle(field["handle"]).group.published_facts or {})
			if meeting is not None:
				return meeting
		return sample_value(field)

	for _round in range(3):  # a controlling answer can reveal a field
		for task in tasks:
			view = reads.get_bid_task(bid_reference=bid, task=task, user=user)
			given = (answers or {}).get(task) or {}
			values = {
				f["handle"]: given.get(f["handle"], answer(f)) for g in view["groups"] for f in g["fields"]
				if f["editable"] and f["visible"] and f["kind"] != "evidence" and (f["value"] in (None, "", []) or f.get("issue") or (f["handle"] in given and f["value"] != given[f["handle"]]))
			}
			if values:
				saved = save.save_bid_task(bid_reference=bid, task=task, values=values, expected_record_version=version(), idempotency_key=key(), user=user)
				assert saved.get("ok"), saved
			for g in reads.get_bid_task(bid_reference=bid, task=task, user=user)["groups"]:
				for f in g["fields"]:
					if f["kind"] == "evidence" and f["visible"] and f.get("issue"):
						for n in range(max(1, f["evidence"]["minimum"]) - len([x for x in f["evidence"]["files"] if x["status"] == "Accepted"])):
							added = evidence.upload_bid_evidence(bid_reference=bid, handle=f["handle"], filename=f"evidence-{n + 1}.pdf", content=pdf(f"{task}-{n}"), expected_record_version=version(), idempotency_key=key(), user=user)
							assert added.get("ok"), added
