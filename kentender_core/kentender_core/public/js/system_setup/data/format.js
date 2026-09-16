// Display helpers shared by the System setup tabs (KT-STD-001 §2.2: dates as
// "1 Jul 2027"; blanks as an em dash, never an empty cell).
export function fmtDate(iso) {
	if (!iso) return "—";
	const date = new Date(String(iso).slice(0, 10) + "T00:00:00");
	if (Number.isNaN(date.getTime())) return String(iso);
	return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function fmtDays(value) {
	return value === null || value === undefined || value === "" ? "—" : String(value);
}

export function dash(value) {
	return value === null || value === undefined || value === "" ? "—" : String(value);
}

// The `datetime-local` input takes "YYYY-MM-DDTHH:mm" in the browser's own
// timezone; the server already renders instants in the site timezone (EAT),
// so this is a plain reformat, not a timezone conversion.
export function toDatetimeLocal(value) {
	if (!value) return "";
	const iso = String(value).slice(0, 16).replace(" ", "T");
	return iso.length === 16 ? iso : "";
}

// §4.10's applicability bases in the plain language §10.6 asks for — the
// stored enum is a model value and is never shown to an administrator.
const APPLICABILITY_BASIS_LABELS = {
	FiscalYearStart: "Financial year start",
	PlanSubmissionDate: "Plan submission date",
	PlanApprovalDate: "Plan approval date",
	ProceedingAuthorizationDate: "Proceeding authorisation date",
	InvitationDate: "Invitation date",
	ContractSigningDate: "Contract signing date",
};

export function applicabilityBasisLabel(value) {
	if (!value) return "";
	return APPLICABILITY_BASIS_LABELS[value] || String(value);
}

// §8.1 — the source-check vocabulary an administrator reads. The stored
// values are model state ("Production verification pending"); every screen
// shows the plain result instead, and they must all show the same one.
const SOURCE_CHECK_LABELS = {
	Verified: "Sources verified",
	"Fixture-verified — not production law": "Fixture-verified — not production law",
	"Production verification pending": "Source check needed",
	Rejected: "Source check rejected",
};

export function sourceCheckLabel(value) {
	return SOURCE_CHECK_LABELS[value] || "Source check needed";
}

export function sourceCheckClass(value) {
	if (value === "Verified") return "kt-status is-live";
	if (value === "Rejected") return "kt-status is-critical";
	return "kt-status is-attention";
}

// The exact server message for `CFG_VERSION_CONFLICT` (configuration_errors.py)
// — matched verbatim so a stale control token gets its own recoverable
// notice instead of the generic error paragraph (CFG-UX-AC-08).
export const CFG_VERSION_CONFLICT_MESSAGE = "This record changed after you opened it. Refresh and review the latest version.";
