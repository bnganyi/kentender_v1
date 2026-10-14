# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-R-01…18 and LQ-01…06 as code (CM-CHG-001 v0.8 §19.3 and §19.7; plan D10; tracker CM8-309).

The class and source columns, the input event and the question text are the specification's, copied by script into
`reconciliation/rule_register.md`; `test_cm_rules` compares this file with that document so they cannot drift. The module, hold key,
affected commands and phase are authored (proposed, for owner review). A hold key names a scoped restriction with an owner, never a stage.
Each rule's calculation is built in the phase that first uses it (the Phase column); the register is what lets a command ask which rules
govern it before that. Pure Python, no Frappe."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
	id: str
	name: str
	source: str  # class and locator, verbatim from §19.3
	input_event: str  # the authoritative input event, verbatim
	hold_key: str  # authored
	commands: tuple[str, ...]  # §7 commands whose consequential action the rule governs (authored)
	phases: tuple[int, ...]  # the phases that build the calculation (authored)
	questions: tuple[str, ...]  # the external legal questions that bear on it
	dependent_action: bool = False  # CM-R-18 also governs "the dependent action named by the missing term"

	@property
	def classes(self) -> tuple[str, ...]:
		"""LAW = read Act provision; TERM = exact issued or signed term; CONTROL = approved KenTender policy."""
		return tuple(c for c in ("LAW", "TERM", "CONTROL") if re.search(rf"\b{c}\b", self.source))


@dataclass(frozen=True)
class LegalQuestion:
	"""A named external question (§19.7) with its approved interim treatment as a scoped hold: the held (command, branch) pairs and nothing else."""

	id: str
	hold_key: str
	reviewer: str  # the accountable reviewer, verbatim opening of the question
	holds: tuple[tuple[str, str], ...]  # (command, branch the command reports it is taking)
	rules: tuple[str, ...]
	release_gate_only: bool = False  # LQ-01 holds no runtime action


RULES: tuple[Rule, ...] = (
	Rule("CM-R-01", "Formation authority", "LAW, §§134(1), 135(1)–(5)", "Frozen agreement version; signature request; each commit", "FORMATION_AUTHORITY", ('RequestContractSignatures', 'SignContractVersion'), (5,), ('LQ-05',)),
	Rule("CM-R-02", "Signing window", "LAW, §135(3); TERM notification/validity", "Award's evidenced notification and signing-window result (consumed, never recomputed)", "SIGNING_WINDOW_UNESTABLISHED", ('RequestContractSignatures', 'SignContractVersion'), (5,), ()),
	Rule("CM-R-03", "AG clearance", "LAW, §134(2), (5)", "Contract value and entity type at send-for-signature", "AG_CLEARANCE_REQUIRED", ('RequestContractSignatures',), (5,), ()),
	Rule("CM-R-04", "Incorporated package", "LAW, §135(6); TERM Form No. 4", "Package manifest entries and file digests", "PACKAGE_INCOMPLETE", ('RequestContractSignatures',), (4, 5), ('LQ-05',)),
	Rule("CM-R-05", "Inspection route", "LAW, §48; CONTROL CM-OD-05", "Appointment version, declarations, conflicts", "APPOINTMENT_MISSING", ('RecordInspectionObservations', 'PrepareAcceptanceReport', 'SignAcceptanceReport'), (6,), ()),
	Rule("CM-R-06", "Acceptance and technical proof", "LAW, §§146, 150(1)–(3)", "Acceptance report; decision-maker's written authority record", "ACCEPTANCE_AUTHORITY_NOT_EVIDENCED", ('PostAcceptedReceipt', 'SignContractCertification'), (6,), ()),
	Rule("CM-R-07", "Advances", "LAW, §§146–148; TERM issued tender and agreement", "Issued tender and agreement advance clause; guarantee verification", "ADVANCE_UNSUPPORTED", ('PrepareContractAdvance', 'SignAdvanceCertification'), (7,), ()),
	Rule("CM-R-08", "Performance security", "LAW, §§142–144; TERM issued security clauses", "Issued security clause; security record verification; exemption basis", "SECURITY_REQUIRED_NOT_VERIFIED", ('RequestContractSignatures',), (5,), ('LQ-03',)),
	Rule("CM-R-09", "Security return", "LAW, §145; TERM final-acceptance requirements", "Actual AO final-acceptance event", "FINAL_ACCEPTANCE_NOT_EVIDENCED", ('RecordSecurityAction',), (9,), ('LQ-03',)),
	Rule("CM-R-10", "Extensions", "LAW, §139(2A); TERM signed agreement", "Supplier justification, recommendation or agreed route, AO decision", "EXTENSION_ROUTE_INCOMPLETE", ('SubmitContractChangeForDecision', 'DecideContractChange', 'ActivateContractChange'), (8,), ()),
	Rule("CM-R-11", "Price/quantity change", "LAW, §139(1), (3)–(7); TERM signed change route", "Change request against original baselines and cumulative changes", "CHANGE_LIMIT_EXCEEDED", ('SubmitContractChangeForDecision', 'DecideContractChange'), (8,), ('LQ-02',)),
	Rule("CM-R-12", "Delay/interest", "LAW, §140; TERM issued remedies", "Operative due date, actual delivery events, extension effect", "DELAY_METHOD_UNVERIFIED", ('PrepareContractAdjustment', 'DecideContractAdjustment'), (8,), ('LQ-04',)),
	Rule("CM-R-13", "Award publicity/reporting", "LAW, §138", "`AwardDecisionRecorded v1`; signing; amendments — original trigger times", "PUBLICATION_REQUIREMENT_UNRESOLVED", ('RecordContractAwardPublication',), (5, 8), ('LQ-06',)),
	Rule("CM-R-14", "Monthly monitoring", "LAW, §152", "Period, covered cases, source versions, cutoff", "REPORT_SOURCE_INCOMPLETE", ('GenerateContractReport', 'SubmitContractReport'), (8,), ()),
	Rule("CM-R-15", "Quarterly variations", "LAW, §139(5)", "Effective amendments in the quarter", "REPORT_SOURCE_INCOMPLETE", ('GenerateContractReport', 'SubmitContractReport', 'RecordContractReportSubmission'), (8,), ()),
	Rule("CM-R-16", "Completion and termination", "LAW, §§153–154; TERM grounds/procedures/completion", "Completion criteria evidence; termination request, notice, effective record", "COMPLETION_CRITERIA_UNMET", ('IssueCompletionCertificate', 'SignContractCloseout', 'DecideContractTermination', 'RecordTerminationNotice'), (8, 9), ()),
	Rule("CM-R-17", "Complexity boundary", "LAW, §§151, 154(b); CONTROL scope", "Registered or received product classification", "OUT_OF_SCOPE_PRODUCT", ('StartContractManagement', 'ReceiveAwardPackage'), (5,), ()),
	Rule("CM-R-18", "Commercial particulars", "TERM issued SCC/GCC, accepted tender and effective amendments", "Typed values mapped from issued SCC/GCC, accepted tender, effective amendments", "TERM_MAPPING_MISSING", ('RequestContractSignatures',), (4, 5), (), dependent_action=True),
)

QUESTIONS: tuple[LegalQuestion, ...] = (
	LegalQuestion("LQ-01", "LEGAL_BASELINE_UNREVIEWED", "legal/procurement owner", (), tuple(r.id for r in RULES), release_gate_only=True),
	LegalQuestion("LQ-02", "CHANGE_EARLY_TOTAL_INCREASE", "procurement/legal partner", (("SubmitContractChangeForDecision", "early_total_increase"), ("DecideContractChange", "early_total_increase")), ("CM-R-11",)),
	LegalQuestion("LQ-03", "SECURITY_EXEMPTION_UNSUPPORTED", "procurement/legal partner", (("RequestContractSignatures", "security_exemption"), ("RecordSecurityAction", "discharge_clause_conflict")), ("CM-R-08", "CM-R-09")),
	LegalQuestion("LQ-04", "DELAY_DEDUCTION_METHOD_UNVERIFIED", "procurement/legal and Finance policy owners", (("DecideContractAdjustment", "automatic_deduction"),), ("CM-R-12",)),
	LegalQuestion("LQ-05", "EXECUTION_METHOD_UNSUPPORTED", "legal/Trust owner", (("RequestContractSignatures", "production_execution_of_form_no_4"),), ("CM-R-01", "CM-R-04")),
	LegalQuestion("LQ-06", "PUBLICATION_DIRECTION_UNCONFIRMED", "procurement/reporting owner", (("RecordContractAwardPublication", "publication_deadline_or_channel"),), ("CM-R-13",)),
)

BY_ID = {r.id: r for r in RULES}
QUESTION_BY_ID = {q.id: q for q in QUESTIONS}


def governing(command: str) -> list[Rule]:
	"""The rules whose consequential action this command is."""
	return [r for r in RULES if command in r.commands]
