# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A browser walk signs in as the seed world's own people, so a world that walks them gives them a password it knows. Those people are shared with every other module's browser specs, which sign in with the seed
password: a world that leaves its own behind locks them out (Home's specs failed with "Invalid Login" for exactly this reason). So the password each person had is kept the first time it is changed, in the
repository's artifacts folder, and put back, byte for byte, when the world is removed. MariaDB test and demonstration sites only."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.utils.password import update_password

_SELECT = "select password from `__Auth` where doctype = 'User' and name = %s and fieldname = 'password' and encrypted = 0"


def store() -> Path:
	return Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "artifacts/cm-original-passwords.json"


def _load() -> dict[str, str | None]:
	return json.loads(store().read_text()) if store().exists() else {}


def _current(address: str) -> str | None:
	rows = frappe.db.sql(_SELECT, (address,))
	return rows[0][0] if rows else None


def set_known(addresses, password: str) -> None:
	"""Give each existing person `password`, keeping what they had the first time (a person already changed by an earlier world keeps that original, not the earlier world's password)."""
	saved = _load()
	for address in sorted(set(addresses)):
		if not frappe.db.exists("User", address):
			continue
		if address not in saved:
			saved[address] = _current(address)
		update_password(address, password)
	store().parent.mkdir(parents=True, exist_ok=True)
	store().write_text(json.dumps(saved, indent=1, sort_keys=True))


def restore() -> list[str]:
	"""Put every kept password back and forget it. Returns the people restored."""
	saved = _load()
	for address, hashed in saved.items():
		if not frappe.db.exists("User", address):
			continue
		if hashed is None:
			frappe.db.delete("__Auth", {"doctype": "User", "name": address, "fieldname": "password"})
		else:
			frappe.db.sql(
				"insert into `__Auth` (doctype, name, fieldname, password, encrypted) values ('User', %s, 'password', %s, 0) on duplicate key update password = %s, encrypted = 0", (address, hashed, hashed)
			)
	if store().exists():
		store().unlink()
	frappe.db.commit()
	return sorted(saved)
