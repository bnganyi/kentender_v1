from __future__ import annotations

import frappe


class DepartmentalNeedError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail(code: str, message: str) -> None:
	# frappe.throw()/msgprint() populates _server_messages, which the client
	# reads to show the real rejection reason. A bare `raise` skips that, so
	# every rejection in this module rendered as a generic "Request failed"
	# regardless of cause — passing an already-constructed instance preserves
	# `.code` (msgprint reuses it as-is; see frappe.utils.messages.msgprint).
	frappe.throw(message, exc=DepartmentalNeedError(code, message))
