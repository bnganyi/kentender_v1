"""Command-only write guard: one reusable way to make a doctype writable only
by its owning service (AUD-XC-010 pilot; WP2.1).

Why this exists
---------------
A lifecycle or ledger doctype must change only through the owning service's
commands, which enforce permission, scope, state, segregation of duties and
audit. A DocPerm that lets a role `write` or `delete` the doctype, plus a bare
controller, lets that role bypass every command by saving the record from the
Desk form, `PUT /api/resource/...` or `frappe.client.set_value`. Award and Bid
Evaluation already refuse such saves unless a command sets a flag on the
document (`doc.flags.kt_awd_command` / `kt_evl_command`); this module
generalises that pattern and tightens it in two ways:

* The authorisation is held on `frappe.local`, in-process, opened only by the
  service through `command_write(family)`. It is never read from `doc.flags`,
  the request, `frappe.form_dict` or the posted document, so a client cannot
  spoof it (a posted JSON body can carry a `flags` key that Frappe copies onto
  the document; this guard ignores `doc.flags` entirely).
* Refusals carry a typed `CommandWriteError.code`, and a per-field allow-list
  lets a Draft keep the few fields its author may edit directly.

What the guard covers, and what it cannot
-----------------------------------------
Covered (they all run the document controller): Desk form save, list-view
delete, `/api/resource` POST/PUT/DELETE, `frappe.client.insert/save/
set_value/delete/bulk_update`, `frappe.desk.form.save.savedocs`, and any
server code that calls `doc.insert()`, `doc.save()` or `frappe.delete_doc()`.
Not covered, by design of Frappe: `frappe.db.set_value`, `frappe.db.sql`,
`frappe.db.delete`, `doc.db_set`, `doc.db_insert`, `doc.db_update`. They skip
the controller. They are in-process server code only (no endpoint reaches
them), so review them like any other service write; the guard does not make
raw SQL safe, and a database trigger would be the only defence there.

How a later work package adopts it for a doctype
------------------------------------------------
1. Controller. Add the mixin and name the family:

       class StrategicPlanVersion(CommandWriteGuardMixin, Document):
           command_write_family = "Strategy"
           command_user_editable_fields = ("title", "summary")   # optional
           command_user_insert = True                            # optional

           def user_editable_when(self, before) -> bool:         # optional
               return before.status == "Draft"

   A controller that defines its own `validate` / `on_trash` must call
   `super().validate()` / `super().on_trash()` (or the two `guard_command_*`
   functions) first. Without an allow-list the mixin refuses every user save
   and every user delete.
2. Wrap the service writes. Every service function that inserts, saves or
   deletes a record of the family does so inside
   `with command_write("Strategy"):`. The family name is shared by all the
   doctypes one service owns, so one `with` covers a command that writes
   several records. Keep the `with` as narrow as the writes it authorises and
   never open it from an endpoint before the command has checked permission.
3. Remove the write path from DocPerm. Delete `write`, `create` and `delete`
   from every role on the doctype's lifecycle fields (and the doctype), keep
   `read`, and keep `create`/`write` only for the roles that author a Draft
   directly when step 1 declares an allow-list. Migrate. The guard is the
   second lock; the DocPerm is the first.
4. Tests. For each doctype: a user save (System Manager included) is refused
   with `COMMAND_ONLY_WRITE`; a changed lifecycle field on an editable Draft is
   refused with `COMMAND_ONLY_FIELD`; an allow-listed field is accepted; a
   delete is refused with `COMMAND_ONLY_DELETE`; the service command still
   works; test cleanup uses an explicit maintenance path (`maintenance_write`),
   never a standing exemption.

Test and seed clean-up
----------------------
`maintenance_write(family, reason=...)` authorises in-process deletes/writes
for clean-up helpers and seeds. It is refused inside an HTTP request and off
a development/test site, so no endpoint and no production process can use it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import contextmanager, nullcontext
from typing import Any

import frappe
from frappe.model import no_value_fields
from frappe.utils import cstr

ERROR_CODES: frozenset[str] = frozenset(
	{
		"COMMAND_ONLY_WRITE",  # a user save/insert outside the owning service
		"COMMAND_ONLY_FIELD",  # a user changed a field outside the allow-list
		"COMMAND_ONLY_DELETE",  # a user delete outside the owning service
		"COMMAND_MAINTENANCE_REFUSED",  # maintenance path used where it is not allowed
	}
)

_MESSAGES = {
	"COMMAND_ONLY_WRITE": "{doctype} records change only through their own commands.",
	"COMMAND_ONLY_FIELD": "{doctype} records change only through their own commands; these fields cannot be edited directly: {fields}.",
	"COMMAND_ONLY_DELETE": "{doctype} records are never deleted directly.",
	"COMMAND_MAINTENANCE_REFUSED": "Maintenance writes are not available here.",
}

_LOCAL_KEY = "kt_command_write_families"

# Fields that Frappe maintains itself on every save; never a user edit.
_SYSTEM_FIELDS = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "doctype", "parent", "parenttype", "parentfield"}
)


class CommandWriteError(frappe.PermissionError):
	"""A write refused because it did not come through the owning service."""

	def __init__(self, code: str, *, doctype: str = "", fields: Iterable[str] = ()):
		assert code in ERROR_CODES, f"{code} is not a command-write error code"
		self.code = code
		self.doctype_name = doctype
		self.fields = tuple(fields)
		super().__init__(_MESSAGES[code].format(doctype=doctype or "These", fields=", ".join(self.fields)))


def _active() -> dict[str, int]:
	families = getattr(frappe.local, _LOCAL_KEY, None)
	if families is None:
		families = {}
		setattr(frappe.local, _LOCAL_KEY, families)
	return families


@contextmanager
def command_write(family: str):
	"""Open the owning service's write window for `family`. In-process only:
	the state lives on `frappe.local`, nothing reads it from a request."""
	families = _active()
	families[family] = families.get(family, 0) + 1
	try:
		yield
	finally:
		families[family] -= 1
		if families[family] <= 0:
			families.pop(family, None)


def command_write_active(family: str) -> bool:
	return bool(_active().get(family))


@contextmanager
def maintenance_write(family: str, *, reason: str):
	"""Clean-up and seed path (test and development sites only, never inside an
	HTTP request). `reason` is required so every use names what it is for."""
	if not reason:
		raise ValueError("maintenance_write needs a reason")
	in_request = getattr(frappe.local, "request", None) is not None
	allowed_site = bool(frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"))
	if in_request or not allowed_site:
		raise CommandWriteError("COMMAND_MAINTENANCE_REFUSED", doctype=family)
	with command_write(family):
		yield


def purge_doc(doctype: str, name: str, *, reason: str = "test and seed clean-up") -> bool:
	"""Delete one document for test/seed clean-up, opening the maintenance
	window of its own command-write family when its controller has one (so the
	caller need not know which family guards the doctype). Same restrictions as
	`maintenance_write`: never inside an HTTP request, never off a development
	or test site. Returns False when the document is already gone."""
	if not frappe.db.exists(doctype, name):
		return False
	doc = frappe.get_doc(doctype, name)
	family = getattr(doc, "command_write_family", "")
	with maintenance_write(family, reason=reason) if family else nullcontext():
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	return True


def fixture_insert(doc, *, reason: str = "test fixture row", **insert_kwargs):
	"""Insert one fixture row of a command-only doctype for a test, under the
	maintenance window of the doctype's own family. Same restrictions as
	`maintenance_write`. Returns the inserted document."""
	family = getattr(doc, "command_write_family", "")
	insert_kwargs.setdefault("ignore_permissions", True)
	with maintenance_write(family, reason=reason) if family else nullcontext():
		doc.insert(**insert_kwargs)
	return doc


# -- field comparison ---------------------------------------------------------


def _row_values(row) -> dict[str, str]:
	return {k: cstr(v) for k, v in row.as_dict().items() if k not in ("modified", "creation", "modified_by", "owner", "name")}


def _changed_fields(doc, before) -> list[str]:
	changed: list[str] = []
	for df in doc.meta.fields:
		if df.fieldtype in no_value_fields and df.fieldtype not in frappe.model.table_fields:
			continue
		if df.fieldtype in frappe.model.table_fields:
			if [_row_values(r) for r in doc.get(df.fieldname) or []] != [_row_values(r) for r in before.get(df.fieldname) or []]:
				changed.append(df.fieldname)
		elif cstr(doc.get(df.fieldname)) != cstr(before.get(df.fieldname)):
			changed.append(df.fieldname)
	return changed


def _not_at_default(doc, allowed: frozenset[str]) -> list[str]:
	"""Fields of a new record that carry a value other than their default."""
	offending: list[str] = []
	for df in doc.meta.fields:
		if df.fieldname in allowed or df.fieldname in _SYSTEM_FIELDS:
			continue
		if df.fieldtype in no_value_fields and df.fieldtype not in frappe.model.table_fields:
			continue
		value = doc.get(df.fieldname)
		if df.fieldtype in frappe.model.table_fields:
			if value:
				offending.append(df.fieldname)
			continue
		if cstr(df.default) in ("Now", "Today") or cstr(df.default).startswith("__"):
			continue  # filled by Frappe at creation (current time, date, user)
		default = df.default or ""
		if cstr(value) not in ("", "0", "None") and cstr(value) != cstr(default):
			offending.append(df.fieldname)
	return offending


# -- the guards ---------------------------------------------------------------


def guard_command_write(
	doc,
	family: str,
	*,
	user_editable_fields: Iterable[str] = (),
	user_editable_when: Callable[[Any], bool] | None = None,
	user_insert: bool = False,
) -> None:
	"""Call from `validate` (it runs for insert and update). Passes when the
	owning service has opened `command_write(family)`. Otherwise:

	* insert is refused (`COMMAND_ONLY_WRITE`) unless `user_insert`, in which
	  case every field outside `user_editable_fields` must still be at its default;
	* an update is refused (`COMMAND_ONLY_WRITE`) unless `user_editable_when(before)`
	  returns true for the stored record; then only `user_editable_fields` may
	  differ from the stored values (`COMMAND_ONLY_FIELD` names the others).
	"""
	if command_write_active(family):
		return
	allowed = frozenset(user_editable_fields)
	if doc.is_new():
		if not user_insert:
			raise CommandWriteError("COMMAND_ONLY_WRITE", doctype=doc.doctype)
		offending = _not_at_default(doc, allowed)
		if offending:
			raise CommandWriteError("COMMAND_ONLY_FIELD", doctype=doc.doctype, fields=offending)
		return
	before = doc.get_doc_before_save()
	if before is None or user_editable_when is None or not user_editable_when(before):
		raise CommandWriteError("COMMAND_ONLY_WRITE", doctype=doc.doctype)
	offending = [f for f in _changed_fields(doc, before) if f not in allowed and f not in _SYSTEM_FIELDS]
	if offending:
		raise CommandWriteError("COMMAND_ONLY_FIELD", doctype=doc.doctype, fields=offending)


def guard_command_delete(doc, family: str, *, user_deletable_when: Callable[[Any], bool] | None = None) -> None:
	"""Call from `on_trash`. Passes inside `command_write(family)`, or when
	`user_deletable_when(doc)` allows a direct delete (for example a Draft)."""
	if command_write_active(family):
		return
	if user_deletable_when is not None and user_deletable_when(doc):
		return
	raise CommandWriteError("COMMAND_ONLY_DELETE", doctype=doc.doctype)


class CommandWriteGuardMixin:
	"""Controller mixin: list it before `Document` in the bases. See the module
	docstring for the adoption steps."""

	command_write_family: str = ""
	command_user_editable_fields: tuple[str, ...] = ()
	command_user_insert: bool = False

	def user_editable_when(self, before) -> bool:  # noqa: ARG002 - override point
		return False

	def user_deletable_when(self) -> bool:
		return False

	def validate(self) -> None:
		guard_command_write(
			self,
			self.command_write_family,
			user_editable_fields=self.command_user_editable_fields,
			user_editable_when=self.user_editable_when,
			user_insert=self.command_user_insert,
		)

	def on_trash(self) -> None:
		guard_command_delete(self, self.command_write_family, user_deletable_when=lambda doc: doc.user_deletable_when())
