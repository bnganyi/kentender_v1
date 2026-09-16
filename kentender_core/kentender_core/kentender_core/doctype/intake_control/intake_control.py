# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.3 — one row per module key (`needs`/`dpp`/`disposal_plan`).

A pure serialization-lock-and-token primitive: it never stores which Fiscal
Year is open (the Fiscal Year flags remain authoritative), is never a window
or business lifecycle, and is only ever touched through
`kentender_core.services.site_configuration`'s `_acquire_intake_control`.
"""

from __future__ import annotations

from frappe.model.document import Document


class IntakeControl(Document):
	pass
