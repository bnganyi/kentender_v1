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
		F("terms_json", "Long Text"), F("items_json", "Long Text"), F("missing_json", "Long Text"), F("rendered_html", "Long Text"), F("rendered_digest"),
		F("frozen_at", "Datetime"), F("effective_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Source Package": ("PKG", "The complete incorporated package frozen with its source versions and digests (CM v0.8 section 19.4).", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("agreement_version", "Int"), F("state", "Select", "Assembling\nFrozen\nSuperseded"),
		F("manifest_json", "Long Text"), F("package_digest"), F("frozen_at", "Datetime"), F("fixture_namespace")]),
	"Contract Signature": ("SIG", "One signer slot of one agreement version, with its proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("agreement_version", "Int", reqd=1), F("party", "Select", "Supplier\nEntity", reqd=1), F("sequence", "Int"),
		F("signer", "Data"), F("capacity"), F("state", "Select", "Waiting\nRequested\nEvidence recorded\nSigned\nPending\nFailed\nRefused\nSuperseded"),
		F("correlation_id"), F("proof_reference"), F("method"), F("signed_at", "Datetime"), F("signed_on", "Date"), F("copy_reference"), F("copy_digest"), F("witness_json", "Long Text"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Appointment": ("APP", "A written appointment of inspectors and certifiers for a contract, with each member's personal declaration.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Recommended\nAppointed\nReturned\nReplaced\nSuperseded"),
		F("scope"), F("reference"), F("members_json", "Long Text"), F("recommended_by"), F("appointed_by"), F("reason", "Small Text"),
		F("effective_from", "Datetime"), F("effective_to", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Arrival": ("ARR", "One physical arrival: what was observed, when, by whom, where. Immutable; corrections are linked.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("arrival_no", "Int"), F("delivery_reference"), F("received_at", "Datetime"), F("recorded_at", "Datetime"), F("receiver"),
		F("destination"), F("items_json", "Long Text"), F("notes", "Small Text"), F("state", "Select", "Recorded\nCorrected"), F("evidence_json", "Long Text"),
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
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Draft\nAwaiting signatures\nEffective\nSuperseded"),
		F("arrivals_json", "Long Text"), F("lines_json", "Long Text"), F("signers_json", "Long Text"), F("technical_certificate"), F("chair"),
		F("decision_at", "Datetime"), F("posting_intent"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Invoice": ("INV", "A supplier's claim against the contract, with its automatic matching and its native invoice.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice_no", "Int"), F("claim_reference"), F("invoice_date", "Date"), F("received_at", "Datetime"), F("claimed_amount", "Currency"),
		F("state", "Select", "Submitted\nHeld\nCertified\nPartly paid\nPaid\nSuperseded"), F("lines_json", "Long Text"), F("matching_json", "Long Text"),
		F("native_invoice"), F("accounting_state", "Select", "Not prepared\nDraft saved\nSubmitted for approval\nPosted"), F("finance_maker"), F("successor_of"), F("submitted_by"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Certification": ("CTF", "The contractual support for one invoice: the frozen matching, the supported amount and the certifier's proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice", "Link", "Contract Invoice"), F("state", "Select", "Awaiting signature\nSigned\nSuperseded"),
		F("matching_json", "Long Text"), F("certified_amount", "Currency"), F("certifier"), F("proof_reference"), F("certified_at", "Datetime"),
		F("acceptance_versions_json", "Long Text"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Settlement": ("STL", "Settlement of a native payment, confirmed only by attributable evidence.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("invoice", "Link", "Contract Invoice"), F("native_payment"), F("amount", "Currency"),
		F("state", "Select", "Recorded\nConfirmed\nReversed"), F("evidence_json", "Long Text"), F("recorder"), F("effective_date", "Date"), F("recorded_at", "Datetime"),
		F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Closeout": ("CLS", "A close-out version: the fulfilment review, surviving obligations and the authorised proof.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("state", "Select", "Draft\nAwaiting signature\nClosed\nSuperseded"),
		F("review_json", "Long Text"), F("signer"), F("proof_reference"), F("closed_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Task": ("TSK", "One obligation of one holder (command, subject, version, holder): the work and the handoff.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("identity", "Data", "", unique=1, reqd=1), F("command"), F("title"), F("subject"), F("subject_version", "Int"),
		F("holder"), F("holder_role"), F("state", "Select", "Open\nBlocked\nWaiting\nScheduled\nDone\nSuperseded"), F("assigned_at", "Datetime"), F("due", "Datetime"),
		F("due_verified", "Check"), F("completed_at", "Datetime"), F("history_json", "Long Text"), F("fixture_namespace")]),
	"Contract Security": ("SEC", "A performance security (or advance guarantee) the supplier supplied: the instrument as recorded, the issuer's confirmation and the verification or rejection, each superseded by a replacement and never edited.", [
		F("contract_case", "Link", "Contract Case", reqd=1), F("version_no", "Int"), F("kind", "Select", "Performance security\nAdvance guarantee"), F("state", "Select", "Recorded\nVerified\nRejected\nSuperseded"),
		F("issuer"), F("beneficiary"), F("reference"), F("amount", "Currency"), F("issued_on", "Date"), F("expires_on", "Date"), F("attachment"),
		F("confirmation_reference"), F("confirmation_received_on", "Date"), F("verification_basis", "Small Text"), F("verified_by"), F("verified_at", "Datetime"), F("rejection_reason", "Small Text"),
		F("recorded_by"), F("recorded_at", "Datetime"), F("record_version", "Int"), F("fixture_namespace")]),
	"Contract Simulated Funding": ("SFD", "Development-only funding owner: the conversions a simulation site's synthetic funding provider holds, idempotent on the operation identity. Never present on a live site.", [
		F("identity", "Data", "", unique=1, reqd=1), F("contract"), F("amount", "Currency"), F("reference"), F("outcome", "Select", "Converted\nRefused"), F("received_at", "Datetime"),
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
