# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The opening record: the official minutes of the opening (BOP-CHG-001 v0.10
§4, §5 Awaiting attestations, §7 SelectOpeningTargets / FreezeOpeningMinutes /
SupersedeFrozenMinutes, §7.1 "Roster and target scope", §10.4; TRUST-ADR-001
v0.1 §1(4); binding rows → PRC `FreezeMinutes`, `SupersedeFrozenMinutes`).

- Prepare opening record shows a draft built from the register, attendance
  and the session; opening it records nothing.
- Finish opening record freezes one exact version: its content, digest and
  pages, and every target each member must attest. Each bid's designated
  page(s) are signed and its price page initialled by the members of the
  roster that was active when that bid was revealed; every member who took
  part initials each record page and signs the final page with full name
  and designation. A successor signs only their own scope; nobody signs for
  a departed member.
- Before completion the recorder may correct the record with a reason: a new
  version with fresh targets; earlier signatures stay in history but no
  longer count. After completion only a correction supplement is possible.
- An empty opening has only the opening-record targets."""

from __future__ import annotations

import hashlib
import io
from typing import Any

import frappe
from frappe.utils import cint, cstr, escape_html

from kentender_procurement.bid_opening.services import (
	appointment, ceremony, clock, errors, finish, labels, people, prc, records, renders, session,
)

SIGN, INITIAL = "Sign", "Initial"


def _roster_segments(case: str) -> dict[int, list[dict[str, Any]]]:
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	out: dict[int, list[dict[str, Any]]] = {}
	for m in frappe.get_doc("Proceeding", proceeding).members:
		out.setdefault(cint(m.roster_segment), []).append({"member_user": m.member_user, "full_name": m.full_name, "designation": m.designation,
			"committee_capacity": m.committee_capacity})
	return out


def _segment_at(case: str, event_id: str) -> int:
	"""The roster segment active when an event happened."""
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	sequence = cint(frappe.db.get_value("Proceeding Event", event_id, "sequence"))
	changes = frappe.db.count("Proceeding Event", {"proceeding": proceeding, "event_type": "RosterSegmentStarted", "sequence": ("<", sequence)})
	return changes + 1


def participants(case: str) -> list[dict[str, Any]]:
	seen: dict[str, dict[str, Any]] = {}
	for segment in sorted(_roster_segments(case).items()):
		for m in segment[1]:
			seen.setdefault(m["member_user"], m)
	return list(seen.values())


def content(doc, *, correction: dict[str, str] | None = None) -> str:
	"""The opening record's exact text (HTML); page 1 committee, attendance and
	register, page 2 what happened and the names for signature (board r2)."""
	from kentender_procurement.proceedings.services import attendance

	e = escape_html
	members = participants(doc.name)
	rows = finish.register_rows(doc.name)
	parts = [
		"<html><head><meta charset='utf-8'><style>body{font-family:sans-serif;font-size:10.5pt}table{border-collapse:collapse;width:100%}"
		"td,th{border:1px solid #999;padding:3px 5px;text-align:left}.page{page-break-before:always}</style></head><body>",
		f"<h1>Opening record</h1><p>{e(doc.tender_reference)} · {e(doc.tender_title or '')}</p>",
		f"<p>Opening started {e(labels.when(doc.started_at))}. Ended {e(labels.when(doc.ended_at))}.</p>",
		"<h2>Opening committee</h2><table><tr><th>Member</th><th>Designation</th><th>Role on committee</th></tr>",
		*[f"<tr><td>{e(m['full_name'])}</td><td>{e(m['designation'] or '')}</td><td>{e(m['committee_capacity'])}</td></tr>" for m in members],
		"</table><h2>Attendance</h2><table><tr><th>Name</th><th>Capacity</th><th>Says they represent</th><th>Movement</th><th>Time</th></tr>",
		*[f"<tr><td>{e(r['person_name'])}</td><td>{e(r['capacity'])}</td><td>{e(r['represented_tenderer'] or '')}</td><td>{e(r['movement'])}</td>"
			f"<td>{e(labels.time(r['occurred_at']))}</td></tr>" for r in attendance.rows(doc.proceeding)],
		"</table><h2>Register</h2>",
	]
	if rows:
		parts.append("<table><tr><th>No.</th><th>Tenderer</th><th>Submitted total</th><th>Security given</th><th>Recorded at</th></tr>")
		parts += [f"<tr><td>{r['number']}</td><td>{e(r['tenderer'])}</td><td>{e(r['submitted_total'])}</td><td>{e(r['security_given'])}</td>"
			f"<td>{e(labels.time_seconds(r['recorded_at']))}</td></tr>" for r in rows]
		parts.append("</table>")
	else:
		parts.append("<p>Empty register. There were no current bids.</p>")
	parts.append("<div class='page'><h2>What happened</h2><table><tr><th>Time</th><th>Who</th><th>What happened</th></tr>")
	parts += [f"<tr><td>{e(c['time'])}</td><td>{e(c['who'])}</td><td>{e(c['what'])}{(' (' + e(c['reported']) + ')') if c['reported'] else ''}</td></tr>"
		for c in session.chronology(doc.name)]
	parts.append("</table>")
	if correction:
		parts.append(f"<h2>Recorder’s correction</h2><p>{e(correction['note'])}</p><p>Reason: {e(correction['reason'])}</p>")
	parts.append("<h2>Names and designations for signature</h2><table><tr><th>Member</th><th>Designation</th><th>Signature</th></tr>")
	parts += [f"<tr><td>{e(m['full_name'])}</td><td>{e(m['designation'] or '')}</td><td>&nbsp;</td></tr>" for m in members]
	parts.append("</table></div></body></html>")
	return "".join(parts)


def render(html: str) -> tuple[bytes, int]:
	from frappe.utils.pdf import get_pdf
	from pypdf import PdfReader

	pdf = get_pdf(html, options={"page-size": "A4", "margin-top": "15mm", "margin-bottom": "15mm", "margin-left": "15mm", "margin-right": "15mm"})
	return pdf, len(PdfReader(io.BytesIO(pdf)).pages)


def _digest(base: str, page: int) -> str:
	return hashlib.sha256(f"{base}:{page}".encode()).hexdigest()


def targets(doc, *, content_digest: str, pages: int, prefix: str) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	segments = _roster_segments(doc.name)
	for entry in ceremony.entries(doc.name):
		if entry.status != "Read out":
			continue
		segment = segments.get(_segment_at(doc.name, entry.proceeding_event), [])
		for m in segment:
			for page in [cint(p) for p in cstr(entry.designated_pages).split(",") if p]:
				out.append({"target_id": f"{entry.entry_id}-P{page}", "target_type": "Tender page", "target_reference": entry.entry_id, "page_number": page,
					"target_digest": _digest(entry.render_digest, page), "required_member": m["member_user"], "roster_segment": _segment_at(doc.name, entry.proceeding_event)})
			out.append({"target_id": f"{entry.entry_id}-PRICE", "target_type": "Price location", "target_reference": entry.entry_id, "page_number": cint(entry.price_page),
				"target_digest": _digest(entry.render_digest, cint(entry.price_page)), "required_member": m["member_user"],
				"roster_segment": _segment_at(doc.name, entry.proceeding_event)})
	for m in participants(doc.name):
		for page in range(1, pages + 1):
			out.append({"target_id": f"{prefix}-M{page}", "target_type": "Minutes page", "target_reference": prefix, "page_number": page,
				"target_digest": _digest(content_digest, page), "required_member": m["member_user"], "roster_segment": 0})
		out.append({"target_id": f"{prefix}-FINAL", "target_type": "Final minutes page", "target_reference": prefix, "page_number": pages,
			"target_digest": _digest(content_digest, pages), "required_member": m["member_user"], "roster_segment": 0})
	return out


def what_you_do(target_type: str) -> tuple[str, str]:
	"""(the board r2/r3 'What you do' wording, the attestation action)."""
	return {
		"Tender page": ("Sign the page", SIGN), "Price location": ("Initial the price", INITIAL), "Change location": ("Initial the change", INITIAL),
		"Minutes page": ("Initial each page", INITIAL), "Final minutes page": ("Sign with full name and designation", SIGN),
	}[target_type]


def draft(doc) -> dict[str, Any]:
	"""Board r2: the generated draft and what each member will sign. Records nothing."""
	html = content(doc)
	_pdf, pages = render(html)
	digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
	return {"pages": pages, "prepared_label": labels.when(clock.now()), "targets": targets(doc, content_digest=digest, pages=pages, prefix="DRAFT")}


def _owner_events(case: str) -> list[str]:
	proceeding = frappe.db.get_value(records.CASE, case, "proceeding")
	return frappe.get_all("Proceeding Event", filters={"proceeding": proceeding, "source": "Owner"}, pluck="event_id")


def _freeze_payload(doc, *, correction: dict[str, str] | None = None) -> dict[str, Any]:
	html = content(doc, correction=correction)
	pdf, pages = render(html)
	digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
	number = frappe.db.count("Proceeding Minutes Version", {"proceeding": doc.proceeding}) + 1
	prefix = f"{doc.proceeding}-M{number:02d}"
	register = frappe.get_doc(finish.REGISTER, doc.register)
	return {"html": html, "pdf": pdf, "pages": pages, "prefix": prefix, "register": register,
		"targets": targets(doc, content_digest=digest, pages=pages, prefix=prefix)}


def freeze_opening_minutes(*, tender: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import minutes

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Readout complete":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if any(e.status != "Read out" or not e.designated_pages for e in ceremony.entries(doc.name)):
			errors.fail("BOP_READOUT_INCOMPLETE")
		p = _freeze_payload(doc)
		frozen = minutes.freeze_minutes(**prc.ref(doc.name), content=p["html"], page_count=p["pages"], register_reference=p["register"].register_id,
			register_digest=p["register"].register_digest, event_ids=_owner_events(doc.name), targets=p["targets"], idempotency_key=prc.key(idempotency_key, "freeze"),
			actor=user)
		renders.save(frozen["minutes_version"], p["pdf"])
		records.bump(doc, state="Awaiting attestations", last_committed_event=frozen["event_id"])
		return records.summary(doc, minutes_version=frozen["minutes_version"], version_number=frozen["version_number"], pages=p["pages"], targets=len(p["targets"]))

	return records.command("FreezeOpeningMinutes", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"expected_version": expected_version}, body=body)


def supersede_opening_minutes(*, tender: str, reason: str, correction_note: str, expected_version: int, idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import minutes

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Awaiting attestations":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if not cstr(reason).strip() or not cstr(correction_note).strip():
			return {"ok": False, "errors": {"reason": "Give the reason and the corrected information."}}
		p = _freeze_payload(doc, correction={"note": cstr(correction_note).strip(), "reason": cstr(reason).strip()})
		frozen = minutes.supersede_minutes(**prc.ref(doc.name), reason=cstr(reason).strip(), content=p["html"], page_count=p["pages"],
			register_reference=p["register"].register_id, register_digest=p["register"].register_digest, event_ids=_owner_events(doc.name), targets=p["targets"],
			idempotency_key=prc.key(idempotency_key, "supersede"), actor=user)
		renders.save(frozen["minutes_version"], p["pdf"])
		records.bump(doc, last_committed_event=frozen["event_id"])
		return records.summary(doc, minutes_version=frozen["minutes_version"], version_number=frozen["version_number"])

	return records.command("SupersedeFrozenMinutes", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"reason": reason, "note": correction_note, "expected_version": expected_version}, body=body)
