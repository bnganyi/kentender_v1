# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The required statements of the certificate and decision outputs (CM-CHG-001 v0.8 section 19.5), in one place.

"The following is the required meaning and substantive text ... It may be laid out clearly but must not be shortened into a different legal assertion." Each statement below is the specification's own
wording with its placeholders; `tests/test_cm_outputs.py` compares every one with section 19.5 so they cannot drift, and the boards and records draw them from here."""

from __future__ import annotations

TECHNICAL = "I confirm the quality and quantity of the goods or services identified in the attached coverage schedule against the cited contract requirements, subject to the recorded exceptions."
ACCEPTANCE = "We record the inspection findings and the accept/reject disposition for the goods or services identified in the coverage schedule, with the stated exceptions and evidence."
CERTIFICATION = ("I certify that invoice {invoice}, for {amount}, is supported by the cited effective contract and accepted goods or services, "
	"after the adjustments and recoveries shown in the certification schedule.")
COMPLETION = ("I confirm delivery and acceptance of the goods and services identified in the contract completion schedule, under contract {contract}, completed on {date}, "
	"with the surviving obligations expressly listed.")
CLOSEOUT = ("I close this procurement contract following the evidenced completion recorded below. The surviving obligations and their accountable owners are listed in the attached schedule.")

#: output -> (statement, the placeholder text the specification writes in its place)
OUTPUTS = {
	"technical certificate": (TECHNICAL, {}),
	"acceptance report": (ACCEPTANCE, {}),
	"invoice certification": (CERTIFICATION, {"invoice": "[ID/version]", "amount": "[currency/amount]"}),
	"completion certificate": (COMPLETION, {"contract": "[ID/version]", "date": "[evidenced date]"}),
	"close-out decision": (CLOSEOUT, {}),
}
