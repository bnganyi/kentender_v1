# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which task raises a bell alert (CM-CHG-001 v0.8 section 5.10; FU-CM-123).

The Project Owner's decision of 16 October 2026: "Follow the approved notification table. Remove alerts added beyond it. Deduplicate retries; waiting and scheduled items remain visible without generating
alerts on every read." Section 5.10 names, for each handoff, who is notified. A task raises an alert for its holder only when its command is a handoff of that table: `NOTIFY` maps each such command to the
row (the event column) that names it, and `QUIET` lists every other command the services assign, with the reason. A waiting item, a scheduled item and a replay of the same task are never alerts (`work.assign`),
and the alert that tells a supplier a notice or report was delivered is raised by the dispatch, once per identity, not by a task.

`test_cm_notifications` scans the services for every command they assign and fails on one that is in neither list, so a new kind of task has to be placed in the table or named quiet; a row it cites must be a row
of the specification's table."""

from __future__ import annotations

#: command -> the section 5.10 row (its Event cell) whose Notification cell names the holder of this task
NOTIFY: dict[str, str] = {
	"RequestContractSignatures": "Eligible Award package durably received",
	"VerifyContractSecurity": "Required security received",
	"SignContractVersion": "Signature request frozen",
	"AppointContractInspectors": "Appointment recommendation",
	"DeclareContractInterest": "Appointment effective",
	"RecordInspectionObservations": "Arrival recorded",
	"SignTechnicalCertificate": "Technical certificate ready",
	"PrepareAcceptanceReport": "Findings ready",
	"SignAcceptanceReport": "Report frozen / each required proof outstanding",
	"RequestInvoiceCorrection": "Invoice discrepancies / supplier correction required",
	"ResolveInvoiceDuplicate": "Invoice discrepancies / supplier correction required",
	"CorrectContractInvoice": "Invoice discrepancies / supplier correction required",
	"SignContractCertification": "Certification ready",
	"SignAdvanceCertification": "Certification ready",
	"SaveNativeFinanceDraft": "Supported native draft",
	"ApproveNativeFinanceRecord": "Supported native draft",
	"RecordFinanceSettlement": "Payment entry posted",
	"AppointContractChangeReviewers": "Change requested / review complete",
	"RecordContractChangeReview": "Change requested / review complete",
	"SignContractChangeReview": "Change requested / review complete",
	"SubmitContractChangeForDecision": "Change requested / review complete",
	"DecideContractChange": "Change requested / review complete",
	"RequestContractChange": "Change requested / review complete",
	"DecideContractTermination": "Termination request ready",
	"RecordTerminationNotice": "Termination request ready",
	"RequestContractTermination": "Termination request ready",
	"SubmitContractReport": "Reporting/publication duty triggered",
	"SignFinalContractAcceptance": "Required final acceptance / completion certificate ready",
	"IssueCompletionCertificate": "Required final acceptance / completion certificate ready",
	"ConfirmCertificateDelivery": "Required final acceptance / completion certificate ready",
	"RecordSecurityAction": "Security return authorised / due",
	"SignContractCloseout": "Completion review supported",
	"DecideContractAdjustment": "Delay adjustment reviewed",
	"DecideSecurityClaim": "Security claim prepared / approved",
	"RecordSecurityClaimCommunication": "Security claim prepared / approved",
	"RecordSecurityClaimOutcome": "Security claim prepared / approved",
	"RequestSecurityClaim": "Security claim prepared / approved",
	"ReconcileWarrantyReturn": "Warranty remedy verified",
	"ConfirmContractClosure": "Close-out correction prepared",
	"PrepareTerminationSettlement": "Termination settlement reconciled",
	"CompleteTerminationSettlement": "Termination settlement reconciled",
	"ConfirmOpeningPosition": "External opening facts complete",
	"StartContractManagement": "External opening facts complete",
	"ReviewAwardRestriction": "Restriction / missing appointment / legal rule unresolved",
	"RestoreContractOperation": "Effective agreement requires Budget/order update",  # also Accepted posting intent fails, Commitment closure acknowledgement absent: the technical operator
}

#: every other command the services assign, and why it raises no alert: the table names no notification for it, the person is told another way, or it is a continuation of the holder's own step
QUIET: dict[str, str] = {
	"RecordContractSecurity": "the table starts at the security received (its verification); recording the instrument is the holder's own step",
	"RecommendContractInspectors": "the table notifies the Accounting Officer at the appointment recommendation, not the head who prepares it",
	"RecordOutsideContractSignature": "an alternative to the signature rows; the table names no notification for it",
	"ConfirmOutsideSignatureEvidence": "an alternative to the signature rows; the table names no notification for it",
	"ReviseContractIntake": "the preparer's own step on an existing contract",
	"ResolveDeliveryException": "no row names it",
	"DecideContractAcceptance": "no row names it (the final acceptance row is a different step)",
	"ReconcileInvoiceLiability": "no row names it",
	"SubmitNativeFinanceForApproval": "the maker continuing their own draft",
	"SendContractCorrespondence": "the table notifies the permitted supplier holder, who is alerted when the message is delivered",
	"ReplyContractCorrespondence": "the supplier is alerted when the message is delivered, once per identity",
	"ResolveContractIssue": "the owner reviewing a supplier reply; the table names no notification for it",
	"RecordWarrantyClaim": "scheduled for the day the warranty ends",
	"RecordWarrantyReturn": "no row names it",
	"VerifyContractRemedy": "the table notifies the missing-evidence or Finance holder, not the verifier",
	"PrepareContractAdjustment": "the table notifies the holder who decides the adjustment, not the head who prepares it",
	"PrepareContractCloseout": "a return to the head; the table notifies the Accounting Officer at the completion review",
	"PrepareContractClosureCorrection": "a return to the head; the table notifies the Accounting Officer at the correction",
	"ActivateContractChange": "the table notifies the current signatory of the amendment",
	"RecordTerminationEffect": "scheduled for the date the notice names",
	"RecordContractReportSubmission": "scheduled amendment report",
	"RecordContractNotProceeding": "no row names it",
}


def raises_alert(command: str) -> bool:
	"""True when a task of this command alerts its holder. The key of a sender's waiting item (`Command:waiting:who`) is never an alert."""
	if ":waiting:" in command:
		return False
	return command in NOTIFY
