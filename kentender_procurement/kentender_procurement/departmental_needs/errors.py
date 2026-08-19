from __future__ import annotations

import frappe


class DepartmentalNeedError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail(code: str, message: str) -> None:
	raise DepartmentalNeedError(code, message)
