// BDS-CHG-001 v0.8 §10.17: the common state a refused command answers to,
// from the one catalogue the server also reads. A page shows these in place
// of the part the command was changing.
import catalogue from "../../../../bid_submission/common_states.json";

const CONFLICTS = new Set(["BDS_STALE_VERSION", "BDS_IDEMPOTENCY_CONFLICT", "BDS_REPLACEMENT_CONFLICT"]);

export function stateForCode(code) {
	const entry = catalogue.states.find((state) => state.code === code);
	return entry ? entry.key : "";
}

/** The in-place state for a refused change (another person changed the bid,
 *  a repeated request, a newer submission), or null for any other refusal. */
export function conflictState(error, reference) {
	if (!error || !CONFLICTS.has(error.code)) return null;
	const receipt = (error.detail && error.detail.current_receipt) || "";
	return {
		key: stateForCode(error.code),
		figures: { receipt_reference: receipt },
		href: error.code === "BDS_REPLACEMENT_CONFLICT" && receipt ? `/tenders/${reference}/bid/receipt/${receipt}` : "",
	};
}
