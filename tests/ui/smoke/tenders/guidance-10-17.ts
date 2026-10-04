/**
 * TPR-CHG-001 v0.12 §10.17 — the next-step and journey content for every
 * record variant, transcribed from the spec table. The boards embed the
 * guidance through a design-tool import the fidelity gates cannot read, so
 * the browser specs assert it against this table instead.
 *
 * `markers` is the P/H/A/C/O tuple (D done, C current, B blocked, N not
 * started); `kind` the next-step kind; `headline` the exact headline, or a
 * RegExp where the server states a fixture fact from the record (the
 * departure is recorded beside the row).
 */
export type GuidanceRow = { markers: string; kind: "your_turn" | "your_turn_blocked" | "waiting" | "done" | "not_involved"; headline?: string | RegExp; fixes?: string[] };

export const GUIDANCE: Record<string, GuidanceRow> = {
	"DES-03": { markers: "C/N/N/N/N", kind: "your_turn", headline: "Set the Tender dates, security and meeting details." },
	"DES-04": { markers: "C/N/N/N/N", kind: "your_turn", headline: "Set supplier evidence and contract terms." },
	"DES-05": { markers: "C/N/N/N/N", kind: "your_turn", headline: "Submit this Tender for approval." },
	"DES-05-NEEDS-ATTENTION": { markers: "B/N/N/N/N", kind: "your_turn_blocked", headline: "Enter the inspection and acceptance location.", fixes: ["Review contract terms"] },
	"DES-06": { markers: "D/C/N/N/N", kind: "your_turn", headline: "Decide whether to approve this Tender package." },
	"DES-06-SEGREGATION": { markers: "D/B/N/N/N", kind: "waiting", headline: "A System Manager must assign an eligible Head of Procurement Function to decide this Version." },
	"DES-07": { markers: "D/D/C/N/N", kind: "your_turn", headline: "Authorise publication of the approved Tender package." },
	"DES-07-SEGREGATION": { markers: "D/D/B/N/N", kind: "waiting", headline: "A System Manager must assign an eligible Accounting Officer to decide this Version." },
	// the server names the outstanding channels and the count from the record
	"DES-08": { markers: "D/D/D/C/N", kind: "your_turn", headline: /^Confirm publication through .+; \d+ of \d+ channels are confirmed\.$/ },
	"DES-08-INVALID": { markers: "D/D/D/B/N", kind: "your_turn_blocked", headline: /evidence could not be accepted\.$/, fixes: ["Choose evidence file", "Confirm publication"] },
	"DES-08-CONFLICT": { markers: "D/D/D/C/N", kind: "your_turn", headline: "Continue with the channels still awaiting confirmation." },
	"DES-09-HOPF": { markers: "D/D/D/D/C", kind: "your_turn", headline: "Prepare an addendum or recommend cancellation if the open Tender needs it." },
	"DES-09-OFFICER": { markers: "D/D/D/D/C", kind: "your_turn", headline: "Prepare an addendum if the published Tender needs a non-material correction." },
	"DES-09-AO": { markers: "D/D/D/D/C", kind: "your_turn", headline: "You can cancel this open Tender on an applicable ground." },
	"DES-09-READER": { markers: "D/D/D/D/C", kind: "not_involved" },
	"DES-09-ENDED": { markers: "D/D/D/D/D", kind: "done", headline: /^The system closed supplier submission at .+\.$/ },
	"DES-10-DRAFT": { markers: "D/D/D/D/C", kind: "your_turn", headline: "Submit the non-material addendum for issue." },
	"DES-10-ISSUE": { markers: "D/D/D/D/C", kind: "your_turn", headline: "Decide whether to issue this addendum." },
	"DES-10-CHANNELS": { markers: "D/D/D/D/C", kind: "your_turn", headline: /^Confirm publication of ADD-.+ through the remaining original channels\.$/ },
	"DES-10-ISSUED": { markers: "D/D/D/D/C", kind: "done", headline: /completed addendum publication on .+\.$/ },
	"DES-10-MATERIAL": { markers: "D/D/D/D/B", kind: "your_turn_blocked", headline: /cannot be issued as an addendum\.$/ },
	"DES-10-REVIEW-REQUESTED": { markers: "D/D/D/D/B", kind: "waiting", headline: /is considering cancellation of TND-.+\.$/ },
	"DES-10-REVIEW-CLOSED": { markers: "D/D/D/D/B", kind: "your_turn_blocked", headline: /remains unissuable; .+ closed the cancellation review with a recorded reason\.$/, fixes: ["Discard addendum draft"] },
	"DES-11": { markers: "D/D/D/D/C", kind: "your_turn", headline: "Send the answer to all registered candidates." },
	"DES-11-PUBLISHED-CHANGE": { markers: "D/D/D/D/B", kind: "your_turn_blocked", headline: "Issue an addendum before sending this answer.", fixes: ["Prepare addendum"] },
	"DES-11-DELIVERY-FAILURE": { markers: "D/D/D/D/B", kind: "your_turn_blocked", headline: /candidate notices? failed delivery; the Tender remains open\.$/, fixes: ["Retry notice"] },
	"DES-12-AO": { markers: "D/D/D/D/C", kind: "your_turn", headline: /^Decide whether to cancel this Tender (for .+|on an applicable ground)\.$/ },
	"DES-12-REVIEW": { markers: "D/D/D/D/C", kind: "your_turn", headline: /^Consider the request to cancel TND-.+ because .+ cannot be issued by addendum\.$/ },
	"DES-12-CANCELLED-HOLDER": { markers: "D/D/D/D/C", kind: "your_turn", headline: /^Record the outstanding cancellation notices and PPRA report by .+\.$/ },
	"DES-12-CANCELLED-READER": { markers: "D/D/D/D/D", kind: "done", headline: /cancelled this Tender on .+\.$/ },
	"DES-13-RETURNED": { markers: "C/N/N/N/N", kind: "your_turn", headline: /^Address .+'s return comment about .+\.$/ },
	"DES-13-CORRECTION": { markers: "B/N/N/N/N", kind: "waiting", headline: /is correcting the requisition/ },
	"DES-13-SUCCESSOR": { markers: "C/N/N/N/N", kind: "your_turn", headline: /^Start a corrected Tender Version from .+\.$/ },
};

const MARKER_CLASS: Record<string, string> = { D: "is-done", C: "is-current", B: "is-blocked", N: "is-not-started" };
export function markerClasses(markers: string): string[] {
	return markers.split("/").map((m) => MARKER_CLASS[m]);
}
