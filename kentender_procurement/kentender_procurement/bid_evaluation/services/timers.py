# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Dated conditions (EVL-CHG-001 v0.4 §5.7, §8 EVL_EVALUATION_OVERDUE; plan
D22, C24; tracker EVL4-509; boards D07-OVERDUE, D07-EXPIRED).

The statutory evaluation deadline and the tender-validity end come from
authoritative dated rules, with the computation, source and timezone
inspectable. No authoritative evaluation-deadline rule exists yet, so the
deadline is shown only when a dated rule is recorded (on a test environment,
a simulated one); a planning assumption is never presented as the statutory
deadline. Overdue is a condition, never a state: work and truthful reporting
continue. Late appointment neither restarts nor pauses the clock. Expiry
prevents a fresh positive recommendation unless the tender owner supplies a
lawful, timely extension; Evaluation cannot extend validity."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.bid_evaluation.services import clock

EVENT = "Evaluation Source Event"


def _latest(case: str, kind: str):
	return frappe.db.get_value(EVENT, {"evaluation_case": case, "kind": kind}, ["effective_at", "detail_json", "source", "source_reference", "authority"], as_dict=True,
		order_by="received_at desc, creation desc")


def dated(doc) -> dict[str, Any]:
	deadline, deadline_rule = doc.evaluation_deadline, None
	rule = _latest(doc.name, "Dated rule")
	if rule and rule.effective_at:
		deadline, deadline_rule = rule.effective_at, {**json.loads(rule.detail_json or "{}"), "source": rule.source_reference or rule.source}
	validity, extension = doc.validity_end, _latest(doc.name, "Validity extension")
	if extension and extension.effective_at:
		validity = extension.effective_at
	now = clock.now()
	return {
		"evaluation_deadline": deadline, "evaluation_rule": deadline_rule,
		"overdue": bool(deadline and now > get_datetime(deadline)) and doc.state not in ("Report sent", "No evaluation required", "Cancelled"),
		"validity_end": validity, "validity_extended": bool(extension), "validity_expired": bool(validity and now > get_datetime(validity)),
	}
