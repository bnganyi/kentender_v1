# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender-bound STD Instance domain package (STDINST-0001).

Maps the Cursor pack ``backend/src/modules/std-engine/domain`` layout to Frappe
``kentender_procurement.tender_management.std_instance``.

Tracker: ``apps/kentender_v1/docs/prompts/std-production-readiness/workstream-2/IMPLEMENTATION_TRACKER.md``

Submodule → ticket:

- ``instance`` — STDINST-0100 (aggregate)
- ``binding`` — STDINST-0110 (TenderStdBindingService)
- ``state`` — STDINST-0120 (lifecycle state machine)
- ``parameter`` — STDINST-0200
- ``attachment`` — STDINST-0210
- ``works_requirement`` — STDINST-0220
- ``boq`` — STDINST-0300
- ``generated_output`` — STDINST-0400
- ``snapshot`` — STDINST-0500
- ``publication_lock`` — STDINST-0600
- ``readiness`` — STDINST-0700
- ``addendum`` — STDINST-0800
- ``downstream`` — STDINST-0900 (consumption contracts)
- ``authorization`` — STDINST-1000
- ``audit`` — STDINST-1100
- ``jobs`` — background generation enqueue (STDINST-0400+)
- ``events`` — domain events payload shapes (audit-adjacent)
"""

from __future__ import annotations

from . import (
	addendum,
	attachment,
	audit,
	authorization,
	binding,
	boq,
	downstream,
	drawing_register,
	events,
	generated_output,
	instance,
	jobs,
	parameter,
	publication_lock,
	readiness,
	snapshot,
	state,
	works_requirement,
)

__all__ = [
	"addendum",
	"attachment",
	"audit",
	"authorization",
	"binding",
	"boq",
	"downstream",
	"drawing_register",
	"events",
	"generated_output",
	"instance",
	"jobs",
	"parameter",
	"publication_lock",
	"readiness",
	"snapshot",
	"state",
	"works_requirement",
]
