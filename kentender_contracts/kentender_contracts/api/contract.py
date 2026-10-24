# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The contract screens' endpoints (CM-CHG-001 v0.8 sections 7, 9.0, 10.3; plan Phase 4).

* `get_contract_board` -- the screen for the signed-in person on one contract and tab, or the stable denial as data.
* `run_contract_command` -- any command in `commands.COMMANDS`, as the signed-in person. A refusal comes back as data (`ok: false`, the stable code, its message and every reason, or the form
  fields to correct), never as an exception, so the screen keeps what the person typed. A person who may not read the contract is told it is not found, whatever they ask.
The server holds every rule; the browser only carries the request."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.api.commands import COMMANDS
from kentender_contracts.boards import router
from kentender_contracts.services import audience
from kentender_contracts.services.errors import ContractError, InputError, as_data


def _denied() -> dict[str, Any]:
	return {"ok": True, "screen": "contract-forbidden"}


@frappe.whitelist()
def get_contract_board(contract: str, tab: str = "", subject: Any = None) -> dict[str, Any]:
	segments = tuple(s for s in (frappe.parse_json(subject) if subject else []) if s)
	try:
		return {"ok": True, "screen": "board", "board": router.board_for(contract, frappe.session.user, tab=tab or None, subject=segments)}
	except ContractError as exc:
		if exc.detail.get("denied"):
			return _denied()
		return as_data(exc)


@frappe.whitelist()
def run_contract_command(command: str, contract: str, expected_version: int, idempotency_key: str, args: Any = None, values: Any = None) -> dict[str, Any]:
	user = frappe.session.user
	handler = COMMANDS.get(command)
	if handler is None:
		return {"ok": False, "code": "CM_CHANGED", "message": "This action is not available.", "detail": {"command": command}, "reasons": []}
	try:
		if contract == "register":  # a contract that does not exist yet: only its registration is asked here
			if command != "RegisterExistingContract":
				return _denied()
			contract = ""
		elif not frappe.db.exists("Contract Case", contract) or not audience.readable(user, contract):
			return _denied()
		result = handler(contract, frappe.parse_json(args) if args else {}, frappe.parse_json(values) if values else {}, int(expected_version), idempotency_key, user)
		return {**result, "ok": True}
	except ContractError as exc:
		frappe.db.rollback()
		return as_data(exc)
	except InputError as exc:
		frappe.db.rollback()
		return {"ok": False, "code": exc.code, "message": str(exc), "detail": exc.detail, "fields": exc.fields, "reasons": []}


@frappe.whitelist()
def download_evidence(contract: str, file: str) -> None:
	"""A signed copy or guarantee the contract relies on, to a reader the contract allows. Any other file, or a contract the reader may not open, is simply not found."""
	from kentender_contracts.services import evidence
	from kentender_core.services import file_integrity

	user = frappe.session.user
	found = audience.readable(user, contract) if frappe.db.exists("Contract Case", contract) else []
	if not found or not ({"terms", "history"} & set(audience.field_sets(found))) or file not in evidence.attached(contract):
		raise frappe.DoesNotExistError("Not found")
	content = file_integrity.read_bytes(file)
	frappe.local.response.filename = frappe.db.get_value("File", file, "file_name") or "evidence"
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
