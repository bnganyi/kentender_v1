# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award notice letters (AWD-CHG-001 v0.4 §5.4). Generated deterministically
from one decision, the signed findings and the issued terms: the tender, the
decision, the successful supplier, the amount where required, the
recipient's own result and reasons, the reply deadline and the published
review and explanation information. A letter never carries another bidder's
confidential evidence or any internal deliberation. The same inputs always
give the same bytes, so a retry sends exactly the letter the Accounting
Officer authorised."""

from __future__ import annotations

import html
from decimal import Decimal, InvalidOperation
from typing import Any

from frappe.utils import cstr

REVIEW_INFO = ("You may ask the procuring entity to explain this result. A request for an explanation is not a request for review and does not change any "
	"period. A formal request for review is made to the Public Procurement Administrative Review Board within the period the Act allows.")


def money(value, currency: str = "KES") -> str:
	if value in (None, ""):
		return ""
	try:
		amount = Decimal(cstr(value))
	except InvalidOperation:
		# A bid that failed a mandatory requirement has no evaluated price:
		# Evaluation sends its words ("Not assessed — mandatory requirement not met").
		return cstr(value)
	return f"{currency} {amount:,.0f}" if amount == amount.to_integral() else f"{currency} {amount:,.2f}"


def unsuccessful_reason(row: dict[str, Any]) -> str:
	if cstr(row.get("responsiveness")) == "Responsive":
		return "Your tender met the requirements. Another responsive tender had a lower evaluated price."
	return "Your tender did not meet the published requirements recorded in the signed evaluation report."


def content(*, doc, decision, recipient: dict[str, Any], row: dict[str, Any] | None, notice_label: str, reply_deadline: str, kind: str) -> dict[str, Any]:
	successful = recipient.get("organisation") == decision.supplier_organisation
	out = {
		"notice": notice_label, "kind": kind, "tender_reference": doc.tender_reference, "tender_title": doc.tender_title, "procuring_entity": doc.procuring_entity,
		"decision": decision.name, "decision_version": decision.version, "recipient": recipient.get("organisation_name"), "bid": recipient.get("bid_reference"),
		"result": "Successful" if successful else "Unsuccessful", "successful_supplier": decision.supplier_name,
		"award_amount": money(decision.submitted_amount, decision.currency), "review_information": REVIEW_INFO,
	}
	if successful:
		out.update(reply_deadline=reply_deadline, statement="Your tender was successful.", no_contract="Accepting this award does not create a contract.",
			reason="The signed evaluation report identifies your tender as the lowest evaluated responsive tender.")
	else:
		row = row or {}
		out.update(statement="Your tender was unsuccessful.", own_amount=money(row.get("submitted_total"), decision.currency),
			own_evaluated=money(row.get("evaluated_total"), decision.currency), reason=unsuccessful_reason(row))
	return out


def render(c: dict[str, Any]) -> str:
	e = lambda v: html.escape(cstr(v))  # noqa: E731
	rows = [("Tender", f"{c['tender_reference']} — {c['tender_title']}"), ("Notice", c["notice"]), ("Result", c["result"]),
		("Successful supplier", c["successful_supplier"]), ("Award amount", c["award_amount"])]
	if c["result"] == "Successful":
		rows.append(("Reply by", c.get("reply_deadline")))
	else:
		rows += [("Your submitted amount", c.get("own_amount")), ("Your evaluated amount", c.get("own_evaluated"))]
	table = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in rows if v)
	extra = f"<p><strong>{e(c['no_contract'])}</strong></p>" if c.get("no_contract") else ""
	return (f"<article class=\"kt-award-letter\"><p>{e(c['procuring_entity'])}</p><h1>{e(c['statement'])}</h1>"
		f"<p>To {e(c['recipient'])}</p><table>{table}</table><p>{e(c['reason'])}</p>{extra}<p>{e(c['review_information'])}</p></article>")
