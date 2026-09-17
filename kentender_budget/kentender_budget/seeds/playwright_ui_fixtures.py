# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the BUD-CHG-001 v1.9 §16 browser journeys.

The browser specs drive the real §15.3 Ministry of Health budget through its
real commands as the §15.1 actors (Josphat Mwangi records and updates,
Beatrice Kamau reviews and closes, Naomi Chebet reads, Samuel Otieno holds no
Budget responsibility and is the Forbidden fixture actor). Every actor and
assignment comes from `kentender_core.seeds.site_setup` and the canonical
Budget portfolio seed — this module grants nothing itself; it guarantees the
standard test password so a browser can log in, and puts the Budget world
back into one documented state before each spec:

- `reset_default`             the §15.3 baseline Active at Version 1, nothing else.
- `reset_initial_draft`       default + an isolated year whose allocation is a
                              saved Draft with lines (Continue draft).
- `reset_initial_submitted`   the same, submitted (Awaiting Budget Approver review).
- `reset_returned_draft`      the same, returned by Beatrice (Changes requested).
- `reset_successor_draft`     default + the §15.6 DHI 80m hold + Josphat's Draft
                              Version 2 transfer (Update in progress).
- `reset_successor_submitted` the §15.6 review fixture: Version 2 submitted.
- `reset_live_breach`         §15.8 BUD19-SC-LIVE-BREACH: Version 2 submitted,
                              then the DHI hold grows to 95m (5m shortfall).
- `reset_omission`            §15.8 BUD19-SC-OMISSION: a Reduction draft where
                              HWD (no hold) may be omitted and DHI (80m) may not.
- `reset_close_blocked`       §15.8 BUD19-SC-CLOSE-BLOCKED: an ended year with a
                              20m remaining hold.
- `reset_close_ready`         §15.8 BUD19-SC-CLOSE-READY: an ended year, no hold,
                              60m active commitment.
- `reset_partial_conversion`  §15.8 BUD19-SC-PARTIAL-CONVERSION-UI: 100m line,
                              80m reserved, 60m converted, 20m still reserved.
- `reset_requires_review`     the partial-conversion line whose hold is flagged
                              Requires review after an owner revalidation.
- `reset_no_budget_year`      default + an empty year (No baseline).

Each builder returns a plain dict that `bench execute` prints as one JSON
line; a spec reads every id from it and never hardcodes one. Every isolated
budget carries the `BUD19-` reference prefix, and every reset removes them
all plus anything a browser run left on the canonical budget.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils.password import update_password

from kentender_core.seeds import site_setup
from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_core.seeds.kentender_mvp_v1.clear import _delete_budget_graph
from kentender_budget.seeds.kentender_mvp_v1_portfolio import (
	FUNDING_SOURCE,
	_ensure_isolated_fy,
	_offset_date,
	ensure_budget_actor_assignments,
	upsert_isolated_successor_version,
	upsert_kentender_mvp_v1_portfolio,
)
from kentender_budget.services.budget_authorization import ensure_budget_governance_roles

OFFICER = C.USER_BUD_OFFICER
APPROVER = C.USER_BUD_APPROVER
AUDITOR = C.USER_BUD_AUDITOR
NOBODY = "samuel.otieno@moh.example.test"
ACTORS = (OFFICER, APPROVER, AUDITOR, NOBODY)

CANONICAL_BUDGET = C.BUD_ACTIVE  # MOH-BUD-2027-001
CANONICAL_V1 = C.BUD_ACTIVE_V1
CANONICAL_V2 = C.BUD_ACTIVE_V2
ISOLATED_PREFIX = "BUD19-"
EMPTY_FY_START = 2063
RETURN_REASON = "Attach the signed approval instrument; the uploaded file is a draft memo, not the approved allocation."
RETURN_REASON_SUCCESSOR = "Attach the signed transfer instrument; the uploaded file is the September baseline approval, not the March transfer."
DHI_TITLE = "Digital health infrastructure programme"
HWD_TITLE = "Digital health workforce development"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw("Budget Playwright fixtures are test data. Enable developer_mode or allow_tests on this site before building them.")


def ensure_actors() -> dict[str, Any]:
	"""The §15.1 actors with the standard test password and their real
	Site-wide assignments. Runs the canonical site seed only when an actor
	is missing (idempotent either way)."""
	_guard()
	frappe.set_user("Administrator")
	if not all(frappe.db.exists("User", email) for email in ACTORS):
		site_setup.run(commit=False)
	ensure_budget_governance_roles()
	ensure_budget_actor_assignments()
	for email in ACTORS:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
			if not user.enabled:
				user.enabled = 1
				user.save(ignore_permissions=True)
			if "Desk User" not in [r.role for r in user.roles]:
				user.add_roles("Desk User")
			update_password(email, TEST_PASSWORD)
	if not frappe.db.exists("Funding Source", FUNDING_SOURCE):
		frappe.get_doc({"doctype": "Funding Source", "label": FUNDING_SOURCE, "record_status": "Available"}).insert(ignore_permissions=True)
	ensure_fixture_documents()
	return {"actors": list(ACTORS)}


FIXTURE_DOCUMENTS = (
	"moh-approved-procurement-budget-2027-28-demo.pdf",
	"moh-approved-procurement-budget-transfer-2027-28-demo.pdf",
)
# A structurally valid one-page PDF (xref table + startxref), generated once —
# Frappe validates uploaded PDFs with pypdf, and a bare stub is rejected.
_MINIMAL_PDF = __import__("base64").b64decode(
	"JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50IDE+PgplbmRvYmoKMyAwIG9iago8PC9UeXBlL1BhZ2UvUGFyZW50IDIgMCBSL01lZGlhQm94WzAgMCA1OTUgODQyXS9Db250ZW50cyA0IDAgUi9SZXNvdXJjZXM8PC9Gb250PDwvRjEgNSAwIFI+Pj4+Pj4KZW5kb2JqCjQgMCBvYmoKPDwvTGVuZ3RoIDk2Pj5zdHJlYW0KQlQgL0YxIDE0IFRmIDYwIDc2MCBUZCAoS2VuVGVuZGVyIGRlbW8gYXBwcm92YWwgZG9jdW1lbnQgLSBmaXh0dXJlLCBub3QgYSByZWFsIGluc3RydW1lbnQpIFRqIEVUCmVuZHN0cmVhbQplbmRvYmoKNSAwIG9iago8PC9UeXBlL0ZvbnQvU3VidHlwZS9UeXBlMS9CYXNlRm9udC9IZWx2ZXRpY2E+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTQgMDAwMDAgbiAKMDAwMDAwMDEwNSAwMDAwMCBuIAowMDAwMDAwMjE3IDAwMDAwIG4gCjAwMDAwMDAzNjAgMDAwMDAgbiAKdHJhaWxlcjw8L1NpemUgNi9Sb290IDEgMCBSPj4Kc3RhcnR4cmVmCjQyMwolJUVPRgo="
)


def ensure_fixture_documents() -> list[str]:
	"""The approval documents the §15.3/§15.6 fixtures link (`/files/…`) exist
	as real public files, so Open approval document and the in-page preview
	resolve instead of 404-ing on a bare filename."""
	import os

	# Absolute: `bench execute` may run from the bench root or from sites/,
	# and frappe.get_site_path() is relative to the current directory.
	public = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.local.site, "public", "files")
	os.makedirs(public, exist_ok=True)
	created = []
	for name in FIXTURE_DOCUMENTS:
		path = os.path.join(public, name)
		if not os.path.exists(path):
			with open(path, "wb") as fh:
				fh.write(_MINIMAL_PDF)
			created.append(name)
	return created


def _canonical_budget_name() -> str | None:
	return frappe.db.get_value("Procurement Budget", {"generated_reference": CANONICAL_BUDGET}, "name")


def _as(user: str):
	frappe.set_user(user)


def purge(*, commit: bool = True) -> dict[str, Any]:
	"""Remove what a browser run leaves behind: every `BUD19-` isolated
	budget (whole graph), every non-Active version on the canonical budget
	with its lines and ledger rows, every reservation/commitment on the
	canonical budget, and a superseded/closed canonical Version 1 is put
	back to Active (the §15.3 baseline)."""
	_guard()
	frappe.set_user("Administrator")
	deleted: dict[str, int] = {}
	for name in frappe.get_all("Procurement Budget", filters={"generated_reference": ["like", f"{ISOLATED_PREFIX}%"]}, pluck="name"):
		_delete_budget_graph(name, deleted)
	canonical = _canonical_budget_name()
	if canonical:
		reservations = frappe.get_all("Funding Reservation", filters={"budget": canonical}, pluck="name")
		if reservations:
			for name in frappe.get_all("Procurement Commitment", filters={"reservation": ["in", reservations]}, pluck="name"):
				frappe.delete_doc("Procurement Commitment", name, force=1, ignore_permissions=True)
				deleted["Procurement Commitment"] = deleted.get("Procurement Commitment", 0) + 1
			for name in reservations:
				frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)
				deleted["Funding Reservation"] = deleted.get("Funding Reservation", 0) + 1
		first = frappe.db.get_value("Procurement Budget Version", {"budget": canonical, "version_number": 1}, "name")
		for version in frappe.get_all("Procurement Budget Version", filters={"budget": canonical, "version_number": [">", 1]}, pluck="name"):
			for lv in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, pluck="name"):
				frappe.delete_doc("Procurement Budget Line Version", lv, force=1, ignore_permissions=True)
			frappe.flags.allow_budget_audit_purge = True
			try:
				for ev in frappe.get_all("Budget Audit Event", filters={"budget_version": version}, pluck="name"):
					frappe.delete_doc("Budget Audit Event", ev, force=1, ignore_permissions=True)
			finally:
				frappe.flags.allow_budget_audit_purge = False
			frappe.delete_doc("Procurement Budget Version", version, force=1, ignore_permissions=True)
			deleted["Procurement Budget Version"] = deleted.get("Procurement Budget Version", 0) + 1
		# Ledger rows of a browser run against the canonical budget that are
		# not the baseline's own lifecycle trail (reservations, replays).
		frappe.flags.allow_budget_audit_purge = True
		try:
			for ev in frappe.get_all("Budget Audit Event", filters={"budget": canonical, "event_type": ["in", ["Funding reserved", "Check funding performed", "Reservation revalidated", "Reservation released", "Reservation partially converted", "Contract commitment recorded", "Commitment adjusted", "Command recorded"]]}, pluck="name"):
				frappe.delete_doc("Budget Audit Event", ev, force=1, ignore_permissions=True)
		finally:
			frappe.flags.allow_budget_audit_purge = False
		if first and frappe.db.get_value("Procurement Budget Version", first, "status") != "Active":
			frappe.db.set_value("Procurement Budget Version", first, {"status": "Active", "closed_by": None, "closed_at": None, "superseded_at": None}, update_modified=False)
	if commit:
		frappe.db.commit()
	return deleted


def _canonical_ids() -> dict[str, Any]:
	budget = _canonical_budget_name()
	v1 = frappe.db.get_value("Procurement Budget Version", {"generated_reference": CANONICAL_V1}, "name")
	lines = {
		r.title: {"id": r.budget_line, "code": frappe.db.get_value("Procurement Budget Line", r.budget_line, "generated_reference")}
		for r in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": v1}, fields=["budget_line", "title"])
	}
	return {
		"budget": budget,
		"budget_code": CANONICAL_BUDGET,
		"fiscal_year": C.FY if hasattr(C, "FY") else "2027-2028",
		"version": v1,
		"version_code": CANONICAL_V1,
		"dhi_line": lines.get(DHI_TITLE, {}).get("id"),
		"dhi_code": lines.get(DHI_TITLE, {}).get("code"),
		"hwd_line": lines.get(HWD_TITLE, {}).get("id"),
		"hwd_code": lines.get(HWD_TITLE, {}).get("code"),
	}


def reset_default(*, commit: bool = True) -> dict[str, Any]:
	_guard()
	ensure_actors()
	removed = purge(commit=False)
	frappe.set_user("Administrator")
	upsert_kentender_mvp_v1_portfolio(include_test_edges=False, commit=False)
	if commit:
		frappe.db.commit()
	return {**_canonical_ids(), "removed": removed}


def _reserve(line: str, amount: float, *, ref: str, source_allocation: str | None = None) -> str:
	"""A real authorised-requisition hold through check/reserve, as Josphat
	(Finance Confirmation Officer). Returns the reservation name."""
	from kentender_budget.services import budget_check_reserve_contracts as check_reserve

	tag = frappe.generate_hash(length=6)
	prior = frappe.session.user
	try:
		_as(OFFICER)
		token = check_reserve.check_funding(
			plan_item=f"PPI-{tag}", plan_version=f"PLN-{tag}", finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}",
			allocations=[{"budget_line": line, "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": source_allocation or f"PSA-{tag}"}],
			correlation_id=frappe.generate_hash(length=12), calling_module="Procurement Requisitions", caller_reference=ref,
		)
		result = check_reserve.reserve_funding(token=token["token"], finance_task=f"FNT-{tag}", source_set_hash=f"HASH-{tag}", idempotency_key=f"IDEM-{tag}")
		if not result.get("ok"):
			frappe.throw(f"Budget fixtures: could not reserve {amount} on {line}: {result}")
		return result["reservations"][0]["reservation_id"]
	finally:
		frappe.set_user(prior)


def _isolated_budget(*, code: str, fy_start_year: int, dhi: float, hwd: float | None = 60_000_000, submit=True, approve=True, approval_reference: str | None = None) -> dict[str, Any]:
	"""One isolated `BUD19-*` budget on its own Fiscal Year, built through the
	real commands as Josphat/Beatrice. Returns ids and codes."""
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc
	from kentender_budget.services import budget_readiness_contracts as readiness
	from kentender_budget.seeds.kentender_mvp_v1_portfolio import GRACE, _unit_for

	fy = _ensure_isolated_fy(fy_start_year)
	prior = frappe.session.user
	try:
		_as(OFFICER)
		result = contracts.save_budget_version_draft(
			{
				"fiscal_year": fy,
				"approval_reference": approval_reference or f"{code} (Demo)",
				"approval_date": _offset_date(30),
				"authorised_total": dhi + (hwd or 0),
				"approval_document": "/files/moh-approved-procurement-budget-2027-28-demo.pdf",
			}
		)
		if not result.get("ok"):
			frappe.throw(f"Budget fixtures: could not create {code}: {result}")
		budget_name, version_name = result["budget"]["id"], result["version"]["id"]
		frappe.db.set_value("Procurement Budget", budget_name, "generated_reference", code, update_modified=False)
		frappe.db.set_value("Procurement Budget Version", version_name, "generated_reference", f"{code}-V1", update_modified=False)
		lines = [{"title": DHI_TITLE, "owner_org_unit": _unit_for(GRACE, "Departmental Author", "Digital Health"), "funding_source": FUNDING_SOURCE, "approved_amount": dhi}]
		if hwd:
			lines.append({"title": HWD_TITLE, "owner_org_unit": "", "funding_source": FUNDING_SOURCE, "approved_amount": hwd})
		saved = lines_svc.save_budget_lines_draft({"budget_version": version_name, "lines": lines})
		if not saved.get("ok"):
			frappe.throw(f"Budget fixtures: could not save lines for {code}: {saved}")
		if submit:
			submitted = readiness.submit_budget_version({"budget_version": version_name})
			if not submitted.get("ok"):
				frappe.throw(f"Budget fixtures: could not submit {code}: {submitted}")
		if submit and approve:
			_as(APPROVER)
			approved = readiness.approve_budget_version({"budget_version": version_name})
			if not approved.get("ok"):
				frappe.throw(f"Budget fixtures: could not approve {code}: {approved}")
		line_rows = frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version_name}, fields=["budget_line", "title"])
		out = {"budget": budget_name, "budget_code": code, "fiscal_year": fy, "version": version_name, "version_code": f"{code}-V1", "version_number": 1}
		for r in line_rows:
			key = "dhi" if r.title == DHI_TITLE else "hwd"
			out[f"{key}_line"] = r.budget_line
			out[f"{key}_code"] = frappe.db.get_value("Procurement Budget Line", r.budget_line, "generated_reference")
		return out
	finally:
		frappe.set_user(prior)


def _finish(base: dict[str, Any], extra: dict[str, Any], *, commit: bool) -> dict[str, Any]:
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {**base, **extra}


def reset_initial_draft(*, commit: bool = True) -> dict[str, Any]:
	"""§11.1B initial Draft on an isolated year: Continue draft / View draft."""
	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-PENDING", fy_start_year=2041, dhi=100_000_000, submit=False)
	return _finish(base, {"pending": iso}, commit=commit)


def reset_initial_submitted(*, commit: bool = True) -> dict[str, Any]:
	"""§11.1B initial submission awaiting Beatrice: Review / View submission."""
	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-PENDING", fy_start_year=2041, dhi=100_000_000, submit=True, approve=False)
	return _finish(base, {"pending": iso}, commit=commit)


def reset_returned_draft(*, commit: bool = True) -> dict[str, Any]:
	"""§11.1B Changes requested: the initial submission returned with a reason."""
	from kentender_budget.services import budget_readiness_contracts as readiness

	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-PENDING", fy_start_year=2041, dhi=100_000_000, submit=True, approve=False)
	_as(APPROVER)
	returned = readiness.return_budget_version({"budget_version": iso["version"], "return_reason": RETURN_REASON})
	if not returned.get("ok"):
		frappe.throw(f"Budget fixtures: could not return {iso['version_code']}: {returned}")
	return _finish(base, {"pending": iso, "return_reason": RETURN_REASON}, commit=commit)


def _successor_draft(base: dict[str, Any], *, dhi: float, hwd: float, revision_type: str = "Transfer") -> dict[str, Any]:
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc

	prior = frappe.session.user
	try:
		_as(OFFICER)
		created = contracts.create_budget_successor_version(
			base["budget_code"],
			{"revision_type": revision_type, "approval_reference": "MOH-FIN-BUD-2027-02 (Demo)", "approval_date": _offset_date(15), "authorised_total": dhi + hwd, "approval_document": "/files/moh-approved-procurement-budget-transfer-2027-28-demo.pdf"},
		)
		if not created.get("ok"):
			frappe.throw(f"Budget fixtures: could not create successor: {created}")
		version = created["version"]["id"]
		editor = lines_svc.get_budget_version_lines_editor(version)
		rows = [
			{"budget_line": r["budget_line"], "title": r["title"], "owner_org_unit": r["owner_org_unit"], "funding_source": r["funding_source"], "approved_amount": dhi if r["title"] == DHI_TITLE else hwd}
			for r in editor["rows"]
		]
		saved = lines_svc.save_budget_lines_draft({"budget_version": version, "lines": rows})
		if not saved.get("ok"):
			frappe.throw(f"Budget fixtures: could not save successor lines: {saved}")
		return {"v2": version, "v2_code": created["version"]["code"], "v2_number": created["version"]["version_number"]}
	finally:
		frappe.set_user(prior)


def reset_successor_draft(*, commit: bool = True) -> dict[str, Any]:
	"""§15.6 with the successor still a Draft (Update in progress)."""
	base = reset_default(commit=False)
	hold = _reserve(base["dhi_line"], 80_000_000, ref="REQ-MOH-2027-021-001")
	v2 = _successor_draft(base, dhi=90_000_000, hwd=70_000_000)
	return _finish(base, {**v2, "reservation": hold}, commit=commit)


def reset_successor_submitted(*, commit: bool = True) -> dict[str, Any]:
	"""§15.6 BUD-SC-REVISION: the 80m DHI hold and Version 2 submitted by
	Josphat (the review fixture for BUD-DES-08–11 and 01A)."""
	base = reset_default(commit=False)
	hold = _reserve(base["dhi_line"], 80_000_000, ref="REQ-MOH-2027-021-001")
	frappe.set_user("Administrator")
	successor = upsert_isolated_successor_version()
	v2 = successor["version"]
	return _finish(base, {"v2": v2, "v2_code": CANONICAL_V2, "v2_number": 2, "reservation": hold}, commit=commit)


def reset_successor_returned(*, commit: bool = True) -> dict[str, Any]:
	"""Version 2 returned by Beatrice: Josphat's correction starting point."""
	from kentender_budget.services import budget_readiness_contracts as readiness

	fixture = reset_successor_submitted(commit=False)
	_as(APPROVER)
	returned = readiness.return_budget_version({"budget_version": fixture["v2"], "return_reason": RETURN_REASON_SUCCESSOR})
	if not returned.get("ok"):
		frappe.throw(f"Budget fixtures: could not return V2: {returned}")
	return _finish(fixture, {"return_reason": RETURN_REASON_SUCCESSOR}, commit=commit)


def reset_live_breach(*, commit: bool = True) -> dict[str, Any]:
	"""§15.8 BUD19-SC-LIVE-BREACH: Version 2 (DHI 90m) submitted, then a
	further 15m authorised on DHI — live Reserved + committed 95m, Shortfall 5m."""
	fixture = reset_successor_submitted(commit=False)
	extra = _reserve(fixture["dhi_line"], 15_000_000, ref="REQ-MOH-2027-022-001")
	return _finish(fixture, {"extra_reservation": extra, "protected_amount": 95_000_000, "shortfall": 5_000_000}, commit=commit)


def reset_omission(*, commit: bool = True) -> dict[str, Any]:
	"""§15.8 BUD19-SC-OMISSION: a Reduction Draft where HWD (no hold) may be
	omitted and DHI (80m held) may not."""
	base = reset_default(commit=False)
	hold = _reserve(base["dhi_line"], 80_000_000, ref="REQ-MOH-2027-021-001")
	v2 = _successor_draft(base, dhi=100_000_000, hwd=60_000_000, revision_type="Reduction")
	return _finish(base, {**v2, "reservation": hold}, commit=commit)


def reset_close_blocked(*, commit: bool = True) -> dict[str, Any]:
	"""§15.8 BUD19-SC-CLOSE-BLOCKED: an ended year (1990/91) whose DHI line
	still has a 20m remaining hold."""
	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-CLOSE", fy_start_year=1990, dhi=100_000_000, hwd=60_000_000)
	hold = _reserve(iso["dhi_line"], 20_000_000, ref="REQ-MOH-2027-031-001")
	return _finish(base, {"closure": iso, "reservation": hold, "remaining_total": 20_000_000}, commit=commit)


def reset_close_ready(*, commit: bool = True) -> dict[str, Any]:
	"""§15.8 BUD19-SC-CLOSE-READY: an ended year, no remaining hold, a 60m
	active commitment (which alone does not block closure)."""
	from kentender_budget.services import budget_commitment_contracts as commit_svc

	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-CLOSE", fy_start_year=1990, dhi=100_000_000, hwd=60_000_000)
	hold = _reserve(iso["dhi_line"], 80_000_000, ref="REQ-MOH-2027-031-001")
	_as(OFFICER)
	commit_svc.convert_reservation(reservation=hold, contract="KT-CON-2027-004", amount=60_000_000, idempotency_key=frappe.generate_hash(length=12))
	commit_svc.release_reservation(reservation=hold, amount=20_000_000, downstream_event_id="REQ-REV-2027-031", downstream_event_type="Requisition revocation", idempotency_key=frappe.generate_hash(length=12))
	return _finish(base, {"closure": iso, "reservation": hold, "active_commitments_total": 60_000_000}, commit=commit)


def reset_partial_conversion(*, commit: bool = True) -> dict[str, Any]:
	"""§15.8 BUD19-SC-PARTIAL-CONVERSION-UI on an isolated year: 100m line,
	80m reserved for REQ-MOH-2027-021-001, 60m converted, 20m still reserved."""
	from kentender_budget.services import budget_commitment_contracts as commit_svc

	base = reset_default(commit=False)
	iso = _isolated_budget(code="BUD19-CONVERT", fy_start_year=2043, dhi=100_000_000, hwd=None)
	hold = _reserve(iso["dhi_line"], 80_000_000, ref="REQ-MOH-2027-021-001")
	_as(OFFICER)
	commit_svc.convert_reservation(reservation=hold, contract="KT-CON-2027-004", amount=60_000_000, idempotency_key=frappe.generate_hash(length=12))
	return _finish(base, {"conversion": iso, "reservation": hold}, commit=commit)


def reset_requires_review(*, commit: bool = True) -> dict[str, Any]:
	"""The partial-conversion line whose remaining hold is flagged Requires
	review by an owner revalidation (a floor breach observed and then
	corrected, leaving the typed reason on the ledger)."""
	from kentender_budget.services import budget_commitment_contracts as commit_svc

	fixture = reset_partial_conversion(commit=False)
	line, version = fixture["conversion"]["dhi_line"], fixture["conversion"]["version"]
	frappe.db.set_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, "approved_amount", 50_000_000, update_modified=False)
	_as(OFFICER)
	commit_svc.revalidate_reservations(reservations=[fixture["reservation"]], downstream_event_id="CON-VAR-2027-004-01", downstream_event_type="Contract variation", idempotency_key=frappe.generate_hash(length=12))
	frappe.db.set_value("Procurement Budget Line Version", {"budget_version": version, "budget_line": line}, "approved_amount", 100_000_000, update_modified=False)
	return _finish(fixture, {"requires_review": True}, commit=commit)


def reset_no_budget_year(*, commit: bool = True) -> dict[str, Any]:
	"""§11.16 No baseline: an existing year with no allocation recorded."""
	base = reset_default(commit=False)
	fy = _ensure_isolated_fy(EMPTY_FY_START)
	for name in frappe.get_all("Procurement Budget", filters={"fiscal_year": fy}, pluck="name"):
		_delete_budget_graph(name, {})
	return _finish(base, {"empty_fiscal_year": fy}, commit=commit)
