# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the BUD-CHG-001 v1.16 section 11.22 screens: BUD-DES-20 (correct a Closed commitment) and BUD-DES-21/22 (fund an existing contract, review the funding).

Each builder drives the real commands as the section 15.1 actors (Josphat Mwangi records and prepares, Beatrice Kamau decides) on its own isolated `BUD19-` year, which `_remove_isolated`
removes with everything it holds (and nothing else: the canonical Budget's reservations belong to Requisitions and are never touched here), and returns one plain dict that `bench execute` prints as a JSON line. The contract is the isolated `CM-MOH-2027-EXT-001`, Afya Digital Supplies Limited, whose
figures the document gives: confirmed target-year charge KES 600,000 (prior-year supported work 400,000 reconciles to the 1,000,000 contract), real existing Budget coverage KES 100,000 (a commitment
of this contract, never inferred from a paid invoice), so KES 500,000 is new; two Entity-wide lines of the same year and funding source, each registered at KES 1,000,000: **Hardware and IT equipment**
(HWD) receives 300,000 and **IT support equipment** 200,000. Before the entry the lines hold 100,000 and 0; after it 400,000 and 200,000.

Variants (`reset_contract_funding(variant=...)`): `ready` (the Officer's turn), `submitted` (the Approver's turn), `approved`, `returned`, `shortfall`, `changed_basis`, `missing_basis`,
`already_covered`, `scope`. `reset_commitment_correction(variant=...)`: `ready` (a Closed commitment of KES 1,000,000, the Officer's turn), `awaiting` (recorded, the Approver's turn), `approved`."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_budget.seeds.kentender_mvp_v1_portfolio import FUNDING_SOURCE, GRACE, _ensure_isolated_fy, _offset_date, _unit_for
from kentender_budget.seeds.playwright_ui_fixtures import APPROVER, ISOLATED_PREFIX, OFFICER, _as, _guard, _reserve, ensure_actors
from kentender_budget.services import budget_commitment_corrections as corrections
from kentender_budget.services import budget_contract_funding as funding
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_existing_contract_entry as entries
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_reference import allocate_commitment_reference
from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.services.contract_funding_request_owner import service as request_owner
from kentender_budget.utils.version_stamp import stamped
from kentender_core.seeds.kentender_mvp_v1.clear import _delete_budget_graph
from kentender_core.services import contract_funding_request_contract as seam

CONTRACT = "CM-MOH-2027-EXT-001"
SUPPLIER = "Afya Digital Supplies Limited"
HWD_LINE = "Hardware and IT equipment"
SUPPORT_LINE = "IT support equipment"
RECONCILIATION = "Existing funding checked against the confirmed current-year charge."
FINANCE_CONFIRMER = "ruth.achieng@moh.example.test"  # a Finance approval holder in Contract Management; Budget only ever sees the name on the basis
ISOLATED_YEAR = 2051


def _remove_isolated() -> dict[str, int]:
	"""Remove the isolated `BUD19-` budgets a previous run left, with the funding requests, entries, outcomes and commitments they hold. The canonical Budget is not touched: `playwright_ui_fixtures.purge`
	would also remove every reservation on it, and those belong to Requisitions' canonical world."""
	frappe.set_user("Administrator")
	deleted: dict[str, int] = {}
	for name in frappe.get_all("Procurement Budget", filters={"generated_reference": ["like", f"{ISOLATED_PREFIX}%"]}, pluck="name"):
		_delete_budget_graph(name, deleted)
	return deleted


def remove_contract_requests(contract: str) -> dict[str, int]:
	"""Remove what one independently registered contract left in Budget: its funding requests, their outcomes and entries, the commitments those entries made, and the audit events that name the contract. For the
	Contract Management browser walk, which raises a real request against the canonical Budget and then has its world cleaned away; nothing else on the canonical Budget is touched."""
	frappe.set_user("Administrator")
	from kentender_core.services.command_write_guard import purge_doc

	deleted: dict[str, int] = {}

	def purge(doctype: str, names: list[str]) -> None:
		for name in names:
			purge_doc(doctype, name)
		deleted[doctype] = deleted.get(doctype, 0) + len(names)

	if not contract:
		return deleted
	requests = frappe.get_all("Contract Funding Request", filters={"contract": contract}, pluck="name")
	for request in requests:
		entries_of = frappe.get_all("Existing Contract Commitment Entry", filters={"request": request}, pluck="name")
		for entry in entries_of:
			purge("Procurement Commitment", frappe.get_all("Procurement Commitment", filters={"entry_row": ["like", f"{entry}/%"]}, pluck="name"))
		purge("Existing Contract Commitment Entry", entries_of)
		purge("Contract Funding Outcome", frappe.get_all("Contract Funding Outcome", filters={"request": request}, pluck="name"))
	purge("Contract Funding Request", requests)
	purge("Budget Audit Event", frappe.get_all("Budget Audit Event", filters={"downstream_reference": contract, "calling_module": "Contract Management"}, pluck="name"))
	frappe.db.commit()
	return deleted


def _isolated(code: str, fy_start_year: int) -> dict[str, Any]:
	"""One isolated year with the two Entity-wide lines of the document's fixture, built through the real commands as Josphat and Beatrice."""
	fy = _ensure_isolated_fy(fy_start_year)
	prior = frappe.session.user
	try:
		_as(OFFICER)
		made = contracts.save_budget_version_draft(stamped({"fiscal_year": fy, "approval_reference": f"{code} (Demo)", "approval_date": _offset_date(30), "authorised_total": 2_000_000,
			"approval_document": "/files/moh-approved-procurement-budget-2027-28-demo.pdf"}))
		if not made.get("ok"):
			frappe.throw(f"Funding fixtures: could not create {code}: {made}")
		budget, version = made["budget"]["id"], made["version"]["id"]
		frappe.db.set_value("Procurement Budget", budget, "generated_reference", code, update_modified=False)
		frappe.db.set_value("Procurement Budget Version", version, "generated_reference", f"{code}-V1", update_modified=False)
		saved = lines_svc.save_budget_lines_draft(stamped({"budget_version": version, "lines": [
			{"title": HWD_LINE, "owner_org_unit": "", "funding_source": FUNDING_SOURCE, "approved_amount": 1_000_000},
			{"title": SUPPORT_LINE, "owner_org_unit": "", "funding_source": FUNDING_SOURCE, "approved_amount": 1_000_000}]}))
		if not saved.get("ok"):
			frappe.throw(f"Funding fixtures: could not save lines for {code}: {saved}")
		submitted = readiness.submit_budget_version(stamped({"budget_version": version}))
		if not submitted.get("ok"):
			frappe.throw(f"Funding fixtures: could not submit {code}: {submitted}")
		_as(APPROVER)
		approved = readiness.approve_budget_version(stamped({"budget_version": version}))
		if not approved.get("ok"):
			frappe.throw(f"Funding fixtures: could not approve {code}: {approved}")
		rows = {r.title: r.budget_line for r in frappe.get_all("Procurement Budget Line Version", filters={"budget_version": version}, fields=["budget_line", "title"])}
		return {"budget": budget, "budget_code": code, "fiscal_year": fy, "version": version, "hwd_line": rows[HWD_LINE], "support_line": rows[SUPPORT_LINE],
			"hwd_code": frappe.db.get_value("Procurement Budget Line", rows[HWD_LINE], "generated_reference"), "support_code": frappe.db.get_value("Procurement Budget Line", rows[SUPPORT_LINE], "generated_reference")}
	finally:
		frappe.set_user(prior)


def _commitment(budget: str, line: str, amount: float, *, status: str = "Active", contract: str = CONTRACT, row: str = "") -> str:
	"""A real Budget commitment of this contract in this year (the existing coverage, or the Closed commitment a correction lowers): an existing-contract commitment, so it needs no reservation."""
	doc = frappe.get_doc({"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "origin": "Existing-contract entry", "budget": budget, "budget_line": line,
		"entry_row": row or f"SEED/{frappe.generate_hash(length=8)}", "contract": contract, "status": status, "current_amount": amount, "currency": "KES"})
	with budget_write():
		doc.insert(ignore_permissions=True)
	return doc.name


def _basis(fiscal_year: str, charge: str, *, digest: str = "BASIS-RUTH-1") -> dict[str, Any]:
	return {"schema": seam.BASIS_SCHEMA, "contract": CONTRACT, "target_year": fiscal_year, "currency": "KES", "confirmed_charge": charge, "digest": digest,
		"evidence": ["Signed contract 1", "Opening reconciliation 1", "Year allocation evidence 1"], "explanation": "Prior activity and the current-year obligation reconciled to the signed terms",
		"confirmers": [{"user": FINANCE_CONFIRMER, "assignment": "URA-CM-FINANCE-APPROVAL", "at": str(frappe.utils.now_datetime())}]}


def _request(fy: str, basis: dict[str, Any] | None, *, currency: str = "KES") -> dict[str, Any]:
	unit = _unit_for(GRACE, "Departmental Author", "Digital Health")
	answer = request_owner().receive(identity=f"fixture-{frappe.generate_hash(length=10)}", request={"kind": "Initial", "contract": CONTRACT, "contract_reference": CONTRACT, "agreement_version": "1",
		"supplier_name": SUPPLIER, "target_year": fy, "currency": currency, "source_organisation_unit": unit, "basis": basis or {}, "evidence": ["Signed contract 1"]})
	return answer["request"]


def reset_contract_funding(variant: str = "ready", *, commit: bool = True) -> dict[str, Any]:
	"""The document's isolated funding fixture in the state a screen is to be walked from."""
	_guard()
	ensure_actors()
	base = {"removed": _remove_isolated()}
	iso = _isolated("BUD19-FUND", ISOLATED_YEAR)
	fy = iso["fiscal_year"]
	frappe.set_user("Administrator")
	coverage = _commitment(iso["budget"], iso["hwd_line"], 600_000 if variant == "already_covered" else 100_000, row="SEED/COVERAGE-1")
	basis = None if variant == "missing_basis" else _basis(fy, "600000.00")
	request = _request(fy, basis, currency="USD" if variant == "scope" else "KES")
	out: dict[str, Any] = {**iso, "request": request["id"], "request_code": request["code"], "contract": CONTRACT, "coverage_commitment": coverage, "variant": variant}
	if variant in ("submitted", "approved", "returned", "shortfall", "changed_basis"):
		_as(OFFICER)
		entry = entries.record_existing_contract_commitment_entry({"request": request["id"], "rows": [{"budget_line": iso["hwd_line"], "amount": "300000.00"}, {"budget_line": iso["support_line"], "amount": "200000.00"}],
			"reconciliation": RECONCILIATION, "idempotency_key": f"fx-rec-{frappe.generate_hash(length=8)}"})["entry"]
		submitted = entries.submit_existing_contract_commitment_entry({"entry": entry["id"], "idempotency_key": f"fx-sub-{frappe.generate_hash(length=8)}"})
		if not submitted.get("ok"):
			frappe.throw(f"Funding fixtures: could not submit the entry: {submitted}")
		out["entry"], out["entry_code"] = entry["id"], entry["code"]
		if variant == "approved":
			_as(APPROVER)
			entries.decide_existing_contract_commitment_entry({"entry": entry["id"], "decision": "Approve", "idempotency_key": f"fx-dec-{frappe.generate_hash(length=8)}"})
		elif variant == "returned":
			_as(APPROVER)
			entries.decide_existing_contract_commitment_entry({"entry": entry["id"], "decision": "Return", "reason": "Confirm the source allocation", "idempotency_key": f"fx-ret-{frappe.generate_hash(length=8)}"})
		elif variant == "shortfall":
			_reserve(iso["support_line"], 850_000, ref="REQ-MOH-2027-099-001")  # the second line now has 150,000 available against the 200,000 asked: the decision finds the shortfall of 50,000
			_as(APPROVER)
			entries.decide_existing_contract_commitment_entry({"entry": entry["id"], "decision": "Approve", "idempotency_key": f"fx-sf-{frappe.generate_hash(length=8)}"})
		elif variant == "changed_basis":
			frappe.set_user("Administrator")
			funding.update_contract_funding_basis(funding.resolve_request(request["id"]).scope_key, _basis(fy, "650000.00", digest="BASIS-RUTH-2"), ["Annual basis 2"], f"fx-upd-{frappe.generate_hash(length=8)}",
				caller=_caller())
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {**base, **out}


def _caller():
	from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, service_caller

	return service_caller(PRINCIPAL_CONTRACT, reference=CONTRACT)  # a fixture standing in for Contract Management, as the other Budget fixtures do


def reset_commitment_correction(variant: str = "ready", *, commit: bool = True) -> dict[str, Any]:
	"""BUD-DES-20: the Closed commitment CM-MOH-2027-CLOSE-001 of KES 1,000,000 whose supported amount is 800,000."""
	_guard()
	ensure_actors()
	base = {"removed": _remove_isolated()}
	iso = _isolated("BUD19-CORR", ISOLATED_YEAR + 1)
	frappe.set_user("Administrator")
	closed = _commitment(iso["budget"], iso["hwd_line"], 1_000_000, status="Closed", contract="CM-MOH-2027-CLOSE-001", row="SEED/CLOSE-1")
	out: dict[str, Any] = {**iso, "commitment": closed, "commitment_code": frappe.db.get_value("Procurement Commitment", closed, "generated_reference"), "contract": "CM-MOH-2027-CLOSE-001", "variant": variant}
	if variant in ("awaiting", "approved"):
		_as(OFFICER)
		recorded = corrections.record_commitment_correction({"commitment": closed, "new_amount": 800_000, "reason": "Unperformed amount included in final obligation",
			"evidence": ["Final obligation review 1", "Closure 1"], "contract_reference": "CM-MOH-2027-CLOSE-001", "idempotency_key": f"fx-cr-{frappe.generate_hash(length=8)}"})
		out["correction"] = recorded["correction"]["id"]
		if variant == "approved":
			_as(APPROVER)
			corrections.decide_commitment_correction({"correction": recorded["correction"]["id"], "decision": "Approve", "idempotency_key": f"fx-cd-{frappe.generate_hash(length=8)}"})
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {**base, **out}


def result_line(value: dict[str, Any]) -> str:
	return json.dumps(value, default=str)
