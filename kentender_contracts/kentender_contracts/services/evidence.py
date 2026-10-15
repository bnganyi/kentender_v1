# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Evidence files Contract Management records (a signed copy, a guarantee, a discharge): the shared integrity check, applied to the person's own upload.

The screen uploads the file first as the signed-in person's own private File (the pattern Requisitions and Tenders use); the command is then sent with that File's name. Nothing is recorded from a
file the person did not upload, a file that is public, or one that fails the shared check (type, size, readability, digest, scan result). The result is the file's name, its digest and the
check result, so a record can say exactly which bytes it relies on."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_contracts.services import records
from kentender_contracts.services.errors import invalid
from kentender_core.services import file_integrity


def checked(file_name: str, actor: str, *, field: str, required: bool = True) -> dict[str, Any] | None:
	"""The checked evidence file, or None when the field is optional and empty. A refusal names the field to correct."""
	if not cstr(file_name).strip():
		if required:
			invalid({field: "Attach the file."})
		return None
	if not frappe.db.exists("File", file_name):
		invalid({field: "The file could not be found. Attach it again."})
	row = frappe.db.get_value("File", file_name, ["owner", "is_private", "file_name"], as_dict=True)
	if cstr(row.owner).lower() != cstr(actor).lower() or not row.is_private:
		invalid({field: "Attach a file you have just uploaded."})

	def refuse(message: str) -> None:
		invalid({field: message})

	found = file_integrity.check_file(file_name, fail=refuse)
	return {"file": file_name, "name": cstr(row.file_name), **found}


def attached(case: str) -> set[str]:
	"""Every evidence file this contract's records rely on: a download is offered only for these, to a reader the contract allows."""
	names = set(frappe.get_all("Contract Security", filters={"contract_case": case}, pluck="attachment")) | set(frappe.get_all("Contract Signature", filters={"contract_case": case}, pluck="copy_reference"))
	for raw in frappe.get_all("Contract Agreement Version", filters={"contract_case": case}, pluck="intake_json"):
		held = (records.loads(raw).get("evidence") or {}).get("file") if raw else ""
		if held:
			names.add(held)
	return {n for n in names if n}
