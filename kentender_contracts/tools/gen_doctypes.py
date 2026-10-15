"""Generates the Contract Management record types (DocType JSON, controller, package marker) from one compact table, so every record is built the same way:
named `CM-<PREFIX>-#####`, written only by Contract Management commands (`CommandWriteGuardMixin`, family "Contract Management"), every field read-only, System Manager
read-only permission (every other reader goes through the audience-filtered services). Immutable snapshots are stored as JSON in Long Text fields.

Usage, from the repo root:  python3 kentender_contracts/tools/gen_doctypes.py            (writes the files)
A record that already exists as a file is only rewritten when it is listed in this table, so hand edits to others are never lost. Run `bench --site <site> migrate` after."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "kentender_contracts" / "contract_management" / "doctype"
MODIFIED = "2026-10-15 12:00:00.000000"

# (fieldname, label, fieldtype, options, extras)
def F(name, ftype="Data", options="", **extra):
	return (name, ftype, options, extra)


RECORDS = {
	"Contract Agreement Version": ("AGR", "One generated version of the agreement: exact terms, rendered text and its digest, the frozen source package, and where it stands.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int", reqd=1),
		F("state", "Select", "Draft\nFrozen\nAwaiting signatures\nEffective\nSuperseded\nEnded", reqd=1), F("source_package", "Link", "Contract Source Package"),
		F("amount", "Currency"), F("currency", "Link", "Currency"), F("operative_date", "Date"),
		F("terms_json", "Long Text"), F("items_json", "Long Text"), F("missing_json", "Long Text"), F("intake_json", "Long Text"), F("rendered_html", "Long Text"), F("rendered_digest"),
		F("frozen_at", "Datetime"), F("effective_at", "Datetime"), F("change"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Source Package": ("PKG", "The complete incorporated package frozen with its source versions and digests (CM v0.8 section 19.4).", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("agreement_version", "Int"), F("state", "Select", "Assembling\nFrozen\nSuperseded"),
		F("manifest_json", "Long Text"), F("package_digest"), F("frozen_at", "Datetime"), F("fixture_namespace")]),
	"Contract Signature": ("SIG", "One signer slot of one agreement version, with its proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("agreement_version", "Int", reqd=1), F("party", "Select", "Supplier\nEntity", reqd=1), F("sequence", "Int"),
		F("signer", "Data"), F("capacity"), F("state", "Select", "Waiting\nRequested\nEvidence recorded\nSigned\nPending\nFailed\nRefused\nSuperseded"),
		F("correlation_id"), F("proof_reference"), F("method"), F("signed_at", "Datetime"), F("signed_on", "Date"), F("copy_reference"), F("copy_digest"), F("evidence_json", "Long Text"), F("witness_json", "Long Text"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Appointment": ("APP", "A written appointment of inspectors and certifiers for a contract, with each member's personal declaration.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Recommended\nAppointed\nReturned\nReplaced\nSuperseded"),
		F("scope"), F("acceptance", "Select", "Committee accepts\nAccounting Officer decides"), F("reference"), F("members_json", "Long Text"), F("recommended_by"), F("appointed_by"), F("reason", "Small Text"),
		F("effective_from", "Datetime"), F("effective_to", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Arrival": ("ARR", "One physical arrival: what was observed, when, by whom, where. Immutable; corrections are linked.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("arrival_no", "Int"), F("delivery_reference"), F("received_at", "Datetime"), F("recorded_at", "Datetime"), F("receiver"),
		F("destination"), F("supplier_reference"), F("items_json", "Long Text"), F("exceptions_json", "Long Text"), F("notes", "Small Text"), F("state", "Select", "Recorded\nCorrected"), F("evidence_json", "Long Text"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Inspection": ("INS", "One inspector's observations of an arrival against the frozen criteria, with the calculated findings.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("arrival", "Link", "Contract Arrival"), F("version_no", "Int"), F("inspector"),
		F("state", "Select", "Recorded\nSuperseded"), F("coverage"), F("observations_json", "Long Text"), F("findings_json", "Long Text"), F("recorded_at", "Datetime"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Certificate": ("CRT", "A certificate bound to an exact subject by a personal proof: technical, completion, final acceptance, close-out.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("kind", "Select", "Technical\nCompletion\nFinal acceptance\nProcurement certification"), F("subject"), F("subject_version", "Int"),
		F("state", "Select", "Awaiting signature\nSigned\nSuperseded"), F("signer"), F("proof_reference"), F("signed_at", "Datetime"), F("content_json", "Long Text"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Acceptance": ("ACC", "One acceptance report version: quantities accepted, rejected and deferred per arrival item, the signers and the effective decision.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Draft\nAwaiting signatures\nRecommended\nEffective\nSuperseded"),
		F("arrivals_json", "Long Text"), F("lines_json", "Long Text"), F("signers_json", "Long Text"), F("decision_json", "Long Text"), F("technical_certificate"), F("chair"), F("correction_reason", "Small Text"),
		F("decision_at", "Datetime"), F("posting_intent"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Invoice": ("INV", "A supplier's claim against the contract, with its automatic matching and its native invoice.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice_no", "Int"), F("claim_reference"), F("invoice_date", "Date"), F("received_at", "Datetime"), F("claimed_amount", "Currency"),
		F("state", "Select", "Submitted\nHeld\nCertified\nPartly paid\nPaid\nSuperseded\nSet aside"), F("lines_json", "Long Text"), F("matching_json", "Long Text"), F("first_received_at", "Datetime"),
		F("native_invoice"), F("accounting_state", "Select", "Not prepared\nDraft saved\nSubmitted for approval\nPosted"), F("finance_maker"), F("successor_of"), F("submitted_by"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Certification": ("CTF", "The contractual support for one invoice: the frozen matching, the supported amount and the certifier's proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice", "Link", "Contract Invoice"), F("state", "Select", "Awaiting signature\nSigned\nSuperseded"),
		F("matching_json", "Long Text"), F("certified_amount", "Currency"), F("certifier"), F("proof_reference"), F("certified_at", "Datetime"),
		F("acceptance_versions_json", "Long Text"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Settlement": ("STL", "Settlement of a native payment, confirmed only by attributable evidence.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice", "Link", "Contract Invoice"), F("native_payment"), F("amount", "Currency"),
		F("state", "Select", "Recorded\nConfirmed\nReversed\nCorrected"), F("evidence_json", "Long Text"), F("recorder"), F("effective_date", "Date"), F("recorded_at", "Datetime"),
		F("corrects"), F("advance"), F("reason", "Small Text"), F("reversed_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Advance": ("ADV", "An advance the issued terms allow: the claim, the guarantee it rests on, the certified amount and the recovery plan. Its cash is paid and confirmed like any payment; its recovery is set against later invoices.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("advance_no", "Int"), F("claim_reference"), F("state", "Select", "Prepared\nCertified\nPaid\nSuperseded"), F("amount", "Currency"), F("percent", "Float"),
		F("clause_json", "Long Text"), F("guarantee", "Link", "Contract Security"), F("recovery_json", "Long Text"), F("certified_amount", "Currency"), F("certifier"), F("proof_reference"), F("certified_at", "Datetime"),
		F("submitted_by"), F("received_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Issue": ("ISS", "A matter the parties must settle: a delivery issue, a warranty claim or any other. The thread of messages, the facts, the remedy asked for and its disposition; a hold it causes is scoped to what it affects.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("issue_no", "Int"), F("kind", "Select", "Delivery issue\nWarranty claim\nOther"), F("title"), F("state", "Select", "Open\nAwaiting reply\nReplied\nRemedy proposed\nClosed"),
		F("facts_json", "Long Text"), F("requested_remedy"), F("reply_by", "Date"), F("owner_user"), F("messages_json", "Long Text"), F("units_json", "Long Text"), F("links_json", "Long Text"),
		F("resolution", "Small Text"), F("resolved_by"), F("closed_at", "Datetime"), F("linked_issue"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Change": ("CHG", "A request to change the contract (an extension, a quantity variation): the baseline it starts from, the proposal, the reviews, the Accounting Officer's decision and the amendment that makes it effective. Terms change only on activation.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("change_no", "Int"), F("kind", "Select", "Extension\nQuantity"), F("state", "Select", "Requested\nReviewed\nSubmitted\nApproved\nDeclined\nReturned\nEffective\nWithdrawn"),
		F("baseline_json", "Long Text"), F("proposal_json", "Long Text"), F("reason", "Small Text"), F("evidence_json", "Long Text"), F("reviews_json", "Long Text"), F("decision_json", "Long Text"), F("rule_json", "Long Text"),
		F("amendment_version", "Int"), F("requested_by"), F("requested_at", "Datetime"), F("decided_by"), F("decided_at", "Datetime"), F("effective_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Adjustment": ("ADJ", "A contractual adjustment worked out from the operative rule (a delay deduction): the inputs, the calculation, the causation, the supplier's response and the decision. A supported adjustment, never an editable figure or a ledger write.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("adjustment_no", "Int"), F("kind", "Select", "Delay"), F("state", "Select", "Prepared\nSubmitted\nApproved\nDeclined\nReturned\nApplied\nSuperseded"),
		F("calculation_json", "Long Text"), F("causation"), F("supplier_response", "Small Text"), F("decision_json", "Long Text"), F("amount", "Currency"), F("invoice", "Link", "Contract Invoice"),
		F("prepared_by"), F("prepared_at", "Datetime"), F("decided_by"), F("decided_at", "Datetime"), F("supersedes"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Security Claim": ("SCL", "A claim on a verified security: the grounds and amount, the claimant's mandate, the decision, the communication to the issuer and the issuer's actual outcome, each its own fact. A request or decision never means the issuer paid.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("security", "Link", "Contract Security"), F("claim_no", "Int"), F("state", "Select", "Prepared\nRequested\nApproved\nDeclined\nReturned\nCommunicated\nOutcome recorded"),
		F("grounds", "Small Text"), F("amount", "Currency"), F("mandate"), F("recipient"), F("evidence_json", "Long Text"), F("decision_json", "Long Text"), F("communication_json", "Long Text"), F("outcome_json", "Long Text"),
		F("prepared_by"), F("prepared_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Obligation": ("OBL", "A duty triggered by an event (a publication, a report, a retention, a security action): the trigger kept with its instant, the rule and due date where verified, the recipient, the owner and the evidence. Never a fabricated deadline.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("kind", "Select", "Publication\nProgress report\nVariation report\nTermination record\nSecurity action\nOther"), F("state", "Select", "Open\nNeeds review\nSatisfied\nNot applicable\nSuperseded"),
		F("rule"), F("trigger_event"), F("trigger_at", "Datetime"), F("due_at", "Datetime"), F("due_basis", "Small Text"), F("recipient"), F("owner_user"), F("evidence_json", "Long Text"), F("disposition", "Small Text"),
		F("subject"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Report": ("RPT", "A generated report for one period: its exact cutoff and source versions, the rows, the recipient and the submission evidence. Derived once for a type and period; a regeneration is a successor and a submitted version is never overwritten.", [
		F("contract_case", "Link", "Contract Case"), F("report_type", "Select", "Progress\nVariation\nPayment follow-up\nTermination record\nAward publication"), F("period_start", "Datetime"), F("period_end", "Datetime"), F("version_no", "Int"),
		F("state", "Select", "Draft\nIncomplete\nSubmitted\nSuperseded"), F("cutoff", "Datetime"), F("sources_json", "Long Text"), F("rows_json", "Long Text"), F("recipient"), F("prepared_by"), F("prepared_at", "Datetime"),
		F("submission_json", "Long Text"), F("submitted_by"), F("submitted_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Termination": ("TRM", "A termination: the grounds and notice, what had been accepted and paid, the Accounting Officer's decision, the notice as actually delivered, the effective instant and the settlement. Terminated is neither Completed nor Settled.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("termination_no", "Int"), F("state", "Select", "Requested\nReturned\nApproved\nDeclined\nNotice delivered\nEffective\nSettlement prepared\nSettled"),
		F("grounds", "Small Text"), F("basis_json", "Long Text"), F("financial_json", "Long Text"), F("decision_json", "Long Text"), F("notice_json", "Long Text"), F("effective_at", "Datetime"), F("settlement_json", "Long Text"),
		F("requested_by"), F("requested_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Closeout": ("CLS", "A close-out version: the fulfilment review, surviving obligations and the authorised proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Draft\nAwaiting signature\nClosed\nSuperseded"),
		F("review_json", "Long Text"), F("signer"), F("proof_reference"), F("closed_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Task": ("TSK", "One obligation of one holder (command, subject, version, holder): the work and the handoff.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("identity", "Data", "", unique=1, reqd=1), F("command"), F("title"), F("subject"), F("subject_version", "Int"),
		F("holder"), F("holder_role"), F("state", "Select", "Open\nBlocked\nWaiting\nScheduled\nDone\nSuperseded"), F("assigned_at", "Datetime"), F("due", "Datetime"),
		F("due_verified", "Check"), F("completed_at", "Datetime"), F("history_json", "Long Text"), F("fixture_namespace")]),
	"Contract Security": ("SEC", "A performance security (or advance guarantee) the supplier supplied: the instrument as recorded, the issuer's confirmation and the verification or rejection, each superseded by a replacement and never edited.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("kind", "Select", "Performance security\nAdvance guarantee"), F("state", "Select", "Recorded\nVerified\nRejected\nSuperseded\nReturned"),
		F("issuer"), F("beneficiary"), F("reference"), F("amount", "Currency"), F("issued_on", "Date"), F("expires_on", "Date"), F("attachment"), F("return_json", "Long Text"),
		F("confirmation_reference"), F("confirmation_received_on", "Date"), F("verification_basis", "Small Text"), F("verified_by"), F("verified_at", "Datetime"), F("rejection_reason", "Small Text"),
		F("recorded_by"), F("recorded_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Award Inbox": ("AWI", "One thing Award handed to Contracting, kept exactly as received with its receipt: a package, a decision event or a later update. Immutable; applying it is a separate fact.", [
		F("reference", "Data", "", unique=1, reqd=1), F("kind", "Select", "Package\nDecision event\nUpdate", reqd=1), F("award_case"), F("outcome"), F("payload_json", "Long Text"), F("receipt"), F("received_at", "Datetime"),
		F("contract_case", "Link", "Contract Case"), F("state", "Select", "Received\nApplied\nReleased"), F("release_reason", "Small Text"), F("released_by"), F("released_at", "Datetime"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Simulated Funding": ("SFD", "Development-only funding owner: the conversions a simulation site's synthetic funding provider holds, idempotent on the operation identity. Never present on a live site.", [
		F("identity", "Data", "", unique=1, reqd=1), F("contract"), F("amount", "Currency"), F("reference"), F("outcome", "Select", "Converted\nRefused\nAdjusted\nClosed"), F("received_at", "Datetime"),
		F("fixture_namespace")]),
	"Contract Event": ("EVT", "An append-only entry of the contract's history: what happened, who, when.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("event_type"), F("occurred_at", "Datetime"), F("actor"), F("summary", "Small Text"), F("detail_json", "Long Text"),
		F("fixture_namespace")]),
}


def label(name: str) -> str:
	return re.sub(r"_", " ", name).strip().capitalize()


def build(title: str, prefix: str, description: str, fields: list) -> dict:
	out = []
	for name, ftype, options, extra in fields:
		spec = {"fieldname": name, "label": label(name), "fieldtype": ftype, "read_only": 1}
		if options:
			spec["options"] = options
		spec.update(extra)
		if extra.get("unique"):
			spec["unique"] = 1
		out.append(spec)
	return {
		"actions": [], "allow_rename": 0, "autoname": f"format:CM-{prefix}-{{#####}}", "creation": MODIFIED, "description": description, "doctype": "DocType",
		"engine": "InnoDB", "field_order": [f["fieldname"] for f in out], "fields": out, "grid_page_length": 50, "issingle": 0, "istable": 0, "links": [],
		"modified": MODIFIED, "modified_by": "Administrator", "module": "Contract Management", "name": title, "owner": "Administrator",
		"permissions": [{"role": "System Manager", "read": 1, "report": 0, "export": 0, "print": 0, "email": 0, "share": 0, "write": 0, "create": 0, "delete": 0}],
		"row_format": "Dynamic", "sort_field": "creation", "sort_order": "DESC", "states": [], "track_changes": 0,
	}


def controller(title: str) -> str:
	cls = "".join(part.capitalize() for part in title.split())
	return f'''# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class {cls}(CommandWriteGuardMixin, Document):
	"""Written only by Contract Management commands (`command_write("Contract Management")`); never by a Desk save (plan D3)."""

	command_write_family = "Contract Management"
'''


def main() -> None:
	for title, (prefix, description, fields) in RECORDS.items():
		folder = ROOT / title.lower().replace(" ", "_")
		folder.mkdir(parents=True, exist_ok=True)
		(folder / "__init__.py").touch()
		(folder / f"{folder.name}.json").write_text(json.dumps(build(title, prefix, description, fields), indent=1) + "\n")
		(folder / f"{folder.name}.py").write_text(controller(title))
		print("wrote", title)


if __name__ == "__main__":
	main()
