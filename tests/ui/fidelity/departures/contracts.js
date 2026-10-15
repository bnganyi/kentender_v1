// Structural departures for the Contract Management screens (CM-CHG-001 v0.8,
// boards in `docs/mvp-1-r1/21_contract_management/design/CM Artboards.dc.html`
// and `cm-data-1…4.js`, addressed by board id; `cmKit` in
// `tests/ui/fidelity/board.js` renders each through the page's own template).
//
// Keyed by board id. Every entry names what the build adds or omits that the
// board does not draw, why, and the authority for it. Unregistered additions
// fail; stale entries fail too. Never resolve a departure by deleting an
// enhancement the spec requires.
//
// Phase 0 (tracker CM8-011): no screen was built, so all three registries were empty.
// Phase 3 (CM8-315): D-ERR and D-DENIED are built and compared by
// `kentender_contracts/.../public/js/contracts/contracts.fidelity.spec.js`.
// `cm-boards.spec.js` checks that they only ever name real boards.

// The head's one action, "Register existing contract", is built (plan Phase 5, D12): D01 and D01-F draw it for the head of procurement. D01-E is the empty list of a person who prepares no contracts
// (the receiver in the test world), so it cannot offer registration; the artboard draws it for a registering person.
const REGISTER = {
	omits: ["page-head > page-actions"],
	because: "The captured empty list is a receiver's, who may not register a contract signed before KenTender; the artboard draws the action for a person who prepares contracts.",
	authority: "CM-CHG-001 v0.8 section 5.13 (a registering person is an authorised preparer); plan Phase 5",
};

// The Verify dialog of D25 draws the issuer's confirmation as already received ("Confirmation TEST-CONF-01 · Received 2 Jul 2027"). No source delivers that confirmation to Contract Management, so the
// person verifying enters the three facts a verification needs (the reference, the date received and the basis): "a file upload is not verification" (CM-CHG-001 v0.8 section 5.10).
const CONFIRMATION = {
	path: "field",
	because: "The board shows the issuer's confirmation as already received; no source delivers it to Contract Management, so the verifier enters the confirmation reference, the date received and the basis.",
	authority: "CM-CHG-001 v0.8 section 5.10 (a verification needs the issuer's confirmation); plan Phase 5 security",
};

export const DEPARTURES = { "D01-E": [REGISTER], "D25 · Verify": [CONFIRMATION] };
// Phase 4 (CM8-414) needed none: the built screens use the boards' own containers. What the structural instrument cannot see, and the tracker lists as known simplifications: the list's
// "Responsible person" and "Managing unit" filters are not drawn (each is a choice of one person or unit from a list that can grow, which AGENTS.md section 6.12 gives to the shared picker, and
// the picker has no register-filter source yet: plan Phase 10), the invoice form has no file field (attaching the supplier's invoice file arrives with the Invoices package), and the
// design's "Illustrative test record" caption is not drawn (DEC-044).


// Boards compared by a fidelity spec in `kentender_contracts/.../public/js`:
// listed here only when a spec importing this registry really compares them.
export const LIST_PAGES = [{ fixture: "D01", board: "D01" }, { fixture: "D01-S", board: "D01-S" }, { fixture: "D01-E", board: "D01-E" }, { fixture: "D01-F", board: "D01-F" }];
export const BOARD_PAGES = [
	{ fixture: "D02", board: "D02" }, { fixture: "D02-V", board: "D02-V" }, { fixture: "D03", board: "D03" }, { fixture: "D03-W", board: "D03-W" }, { fixture: "D03-A", board: "D03-A" },
	{ fixture: "D23-R", board: "D23-R" }, { fixture: "D23", board: "D23" }, { fixture: "D23-P", board: "D23-P" }, { fixture: "D24", board: "D24" },
	{ fixture: "D04", board: "D04" }, { fixture: "D05", board: "D05" }, { fixture: "D19", board: "D19" }, { fixture: "D06", board: "D06" }, { fixture: "D07", board: "D07" },
	{ fixture: "D18", board: "D18" }, { fixture: "D18-R", board: "D18-R" }, { fixture: "D18-C", board: "D18-C" }, { fixture: "D08", board: "D08" }, { fixture: "D08-C", board: "D08-C" },
	{ fixture: "D33", board: "D33" }, { fixture: "D33-A", board: "D33-A" }, { fixture: "D09-F", board: "D09-F" }, { fixture: "D17", board: "D17" }, { fixture: "D17-S", board: "D17-S" },
	{ fixture: "D22", board: "D22" }, { fixture: "D11", board: "D11" },
	{ fixture: "D25-R", board: "D25-R" }, { fixture: "D25", board: "D25" }, { fixture: "D25-J", board: "D25-J" },
	{ fixture: "D26", board: "D26" }, { fixture: "D26-H", board: "D26-H" }, { fixture: "D26-E", board: "D26-E" },
	{ fixture: "D12", board: "D12" }, { fixture: "D12-G", board: "D12-G" }, { fixture: "D21", board: "D21" }, { fixture: "D21-H", board: "D21-H" },
];
export const BOARD_DIALOGS = [
	{ fixture: "D23", action: "Appoint inspectors", board: "D23 · Appoint" }, { fixture: "D23", action: "Return for correction", board: "D23 · Return" },
	{ fixture: "D04", action: "Enter unit references", board: "D04 · Units" }, { fixture: "D05", action: "Record observations", board: "D05 · Record" },
	{ fixture: "D05", action: "View all observations", board: "D05 · All" }, { fixture: "D08", action: "Request correction", board: "D08 · Correction" },
	{ fixture: "D33-A", action: "Return invoice for correction", board: "D33-A · Return" }, { fixture: "D17", action: "Return payment for correction", board: "D17 · Return" },
	{ fixture: "D25", action: "Verify security", board: "D25 · Verify" }, { fixture: "D25", action: "Reject security", board: "D25 · Reject" },
];
export const COVERED = ["D-ERR", "D-DENIED", ...LIST_PAGES.map((p) => p.board), ...BOARD_PAGES.map((p) => p.board), ...BOARD_DIALOGS.map((d) => d.board)];

// Rare-branch boards recorded as not compared. Each needs a reason that names
// the authority for leaving it out (tracker rule 14).
export const NOT_COMPARED = {};
