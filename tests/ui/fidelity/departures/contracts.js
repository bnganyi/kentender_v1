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

// The completion certificate's delivery to the contractor is a fact the head of procurement confirms with evidence (CM-CHG-001 v0.8 section 19.5: "Signed and actually issued to supplier are separate facts"). D22-P draws the
// state (issued, delivery pending) but no way to take the step, so the form is drawn under the certificate summary, for the head only; everyone else sees the state alone.
const DELIVERY_FORM = {
	path: "region > field",
	because: "The artboard draws the pending state without the form that confirms delivery; the head of procurement needs the day, the way, the reference and the proof, and nothing else records them.",
	authority: "CM-CHG-001 v0.8 sections 5.9 and 19.5 (signed and delivered are separate facts); plan Phase 9, D22",
};
// After a reopening the head's next step is the same confirmation (D38-R names it: "Confirm certificate delivery."); the board draws the history but again no way to take the step.
const DELIVERY_AGAIN = {
	path: "region",
	because: "The artboard draws the reopening's history and the head's next step but no form to confirm the certificate's delivery again; the same form as D22-P is drawn under the history, for the head only.",
	authority: "CM-CHG-001 v0.8 section 5.21 (a reopening asks for the corrected fact); plan Phase 9, D38",
};

// The artboard draws five filters on the list: Search and Status in the bar, and Source, Responsible person and Managing unit under a "Filters" disclosure. The build draws three, all in the one row, because
// a disclosure over the single remaining select was a heavy band over a lone, stretched field (the Project Owner, 17 October 2026: "the layout of filters is wrong"). Responsible person and Managing unit are
// each a choice of one person or unit from a list that can grow, which AGENTS.md section 6.12 gives to the shared picker, and the picker has no register-filter source yet (plan Phase 10).
const FILTERS_INLINE = {
	omits: ["disclosure"],
	because: "The artboard draws two more filters than the build offers and puts three under a disclosure; with three filters the build draws them all in the one row and the disclosure of a single select is not drawn.",
	authority: "Project Owner, 17 October 2026 (the filter layout was wrong); AGENTS.md section 6.12 (a person or unit filter is the shared picker); plan Phase 10",
};

export const DEPARTURES = { "D01": [FILTERS_INLINE], "D01-F": [FILTERS_INLINE], "D01-T": [FILTERS_INLINE], "D01-AUD": [FILTERS_INLINE], "D01-E": [REGISTER, FILTERS_INLINE], "D25 · Verify": [CONFIRMATION], "D22-P": [DELIVERY_FORM], "D38-R": [DELIVERY_AGAIN] };
// Phase 4 (CM8-414) needed none: the built screens use the boards' own containers. What the structural instrument cannot see, and the tracker lists as known simplifications: the list's
// "Responsible person" and "Managing unit" filters are not drawn (each is a choice of one person or unit from a list that can grow, which AGENTS.md section 6.12 gives to the shared picker, and
// the picker has no register-filter source yet: plan Phase 10), the invoice form has no file field (attaching the supplier's invoice file arrives with the Invoices package), and the
// design's "Illustrative test record" caption is not drawn (DEC-044).


// Boards compared by a fidelity spec in `kentender_contracts/.../public/js`:
// listed here only when a spec importing this registry really compares them.
export const LIST_PAGES = [{ fixture: "D01", board: "D01" }, { fixture: "D01-S", board: "D01-S" }, { fixture: "D01-E", board: "D01-E" }, { fixture: "D01-F", board: "D01-F" },
	// Phase 12 (plan CM8-1201): the list as the technical reader and the auditor read it (every contract, nothing to register) and the supplier with no contract yet.
	{ fixture: "D01-T", board: "D01-T" }, { fixture: "D01-AUD", board: "D01-AUD" }, { fixture: "D01-S-E", board: "D01-S-E" }];
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
	{ fixture: "D08-L", board: "D08-L" }, { fixture: "D17-H", board: "D17-H" }, { fixture: "D28", board: "D28" }, { fixture: "D28-C", board: "D28-C" }, { fixture: "D28-V", board: "D28-V" },
	{ fixture: "D29", board: "D29" }, { fixture: "D29-H", board: "D29-H" }, { fixture: "D29-R", board: "D29-R" }, { fixture: "D33-U", board: "D33-U" }, { fixture: "D09-T", board: "D09-T" }, { fixture: "D09-AUD", board: "D09-AUD" },
	{ fixture: "D24-S", board: "D24-S" }, { fixture: "D24-X", board: "D24-X" }, { fixture: "D05-M", board: "D05-M" }, { fixture: "D31", board: "D31" }, { fixture: "D31-A", board: "D31-A" },
	// Phase 8 (plan CM8-801..807): issues, changes, warranty, delay, security actions, termination, reporting.
	{ fixture: "D13", board: "D13" }, { fixture: "D13-S", board: "D13-S" }, { fixture: "D13-C", board: "D13-C" },
	{ fixture: "D27", board: "D27" }, { fixture: "D27-R", board: "D27-R" }, { fixture: "D27-A", board: "D27-A" }, { fixture: "D14", board: "D14" }, { fixture: "D14-P", board: "D14-P" },
	{ fixture: "D34", board: "D34" }, { fixture: "D34-R", board: "D34-R" }, { fixture: "D34-A", board: "D34-A" }, { fixture: "D34-P", board: "D34-P" }, { fixture: "D34-H", board: "D34-H" }, { fixture: "D34-L", board: "D34-L" }, { fixture: "D34-X", board: "D34-X" },
	{ fixture: "D16-W", board: "D16-W" }, { fixture: "D16-P", board: "D16-P" }, { fixture: "D16", board: "D16" },
	{ fixture: "D35", board: "D35" }, { fixture: "D35-V", board: "D35-V" }, { fixture: "D35-C", board: "D35-C" }, { fixture: "D35-H", board: "D35-H" },
	{ fixture: "D36", board: "D36" }, { fixture: "D36-A", board: "D36-A" }, { fixture: "D36-E", board: "D36-E" }, { fixture: "D36-S", board: "D36-S" }, { fixture: "D36-H", board: "D36-H" },
	{ fixture: "D37", board: "D37" }, { fixture: "D37-A", board: "D37-A" }, { fixture: "D37-P", board: "D37-P" }, { fixture: "D37-X", board: "D37-X" },
	{ fixture: "D20", board: "D20" }, { fixture: "D20-P", board: "D20-P" }, { fixture: "D20-T", board: "D20-T" },
	{ fixture: "D39-P", board: "D39-P" }, { fixture: "D39", board: "D39" }, { fixture: "D39-C", board: "D39-C" }, { fixture: "D39-H", board: "D39-H" },
	{ fixture: "D15", board: "D15" }, { fixture: "D15-L", board: "D15-L" },
	// Phase 9 (plan CM8-901..906): final acceptance, completion and its delivery, the close-out and its correction.
	{ fixture: "D32", board: "D32" }, { fixture: "D32-H", board: "D32-H" }, { fixture: "D22-P", board: "D22-P" }, { fixture: "D11-B", board: "D11-B" }, { fixture: "D11-C", board: "D11-C" },
	{ fixture: "D38-P", board: "D38-P" }, { fixture: "D38", board: "D38" }, { fixture: "D38-R", board: "D38-R" }, { fixture: "D38-T", board: "D38-T" },
];
// A board that is another board's page in a state the person reaches by choosing: drawn from the fixture, the choice made, then compared. `radio` names the radio group (its `cm-input-` test id) and
// `choose` the option to pick; `shows` is what must then be on the page. The comparison collapses identical sibling fields, so what the choice reveals is asserted directly as well.
export const BOARD_STATES = [{ fixture: "D24", board: "D24-C", radio: "declaration", choose: 1, shows: { textareas: 1, text: "You will not be able to inspect or sign this contract while this conflict remains unresolved." } }];
export const BOARD_DIALOGS = [
	{ fixture: "D23", action: "Appoint inspectors", board: "D23 · Appoint" }, { fixture: "D23", action: "Return for correction", board: "D23 · Return" },
	{ fixture: "D04", action: "Enter unit references", board: "D04 · Units" }, { fixture: "D05", action: "Record observations", board: "D05 · Record" },
	{ fixture: "D05", action: "View all observations", board: "D05 · All" }, { fixture: "D08", action: "Request correction", board: "D08 · Correction" },
	{ fixture: "D33-A", action: "Return invoice for correction", board: "D33-A · Return" }, { fixture: "D17", action: "Return payment for correction", board: "D17 · Return" },
	{ fixture: "D25", action: "Verify security", board: "D25 · Verify" }, { fixture: "D25", action: "Reject security", board: "D25 · Reject" },
	{ fixture: "D14", action: "Approve extension", board: "D14 · Approve" }, { fixture: "D14", action: "Decline", board: "D14 · Decline" }, { fixture: "D34-A", action: "Approve change", board: "D34-A · Decide" },
	{ fixture: "D35", action: "Record return", board: "D35 · Return" }, { fixture: "D36-A", action: "Approve adjustment", board: "D36-A · Decide" }, { fixture: "D37-P", action: "Record claim outcome", board: "D37-P · Outcome" },
	{ fixture: "D20", action: "Decline", board: "D20 · Decline" }, { fixture: "D39", action: "Complete settlement", board: "D39 · Complete" }, { fixture: "D15-L", action: "Record source evidence", board: "D15-L · Evidence" },
	{ fixture: "D32", action: "Return for correction", board: "D32 · Return" }, { fixture: "D11", action: "Return for correction", board: "D11 · Return" }, { fixture: "D38", action: "Reopen contract", board: "D38 · Reopen" },
];
export const COVERED = ["D-ERR", "D-DENIED", ...LIST_PAGES.map((p) => p.board), ...BOARD_PAGES.map((p) => p.board), ...BOARD_STATES.map((p) => p.board), ...BOARD_DIALOGS.map((d) => d.board)];

// Rare-branch boards recorded as not compared. Each needs a reason that names
// the authority for leaving it out (tracker rule 14).
// The register of boards that are not compared, each with its reason (tracker rule 14; plan Phase 12, CM8-1201). Every one of the design's 157 boards is either compared above or named here.
const WORK_REGISTER = "The work register is not a page of its own: every reader opens the Obligations tab (D10), which since Phases 8 and 9 also carries the Issues, Contract changes, Reports, Duties and close-out regions the artboard predates; the reader variants differ only in which of those regions their audience may see, and that is tested directly in test_cm_leakage. The structural comparison waits for the designer to redraw D10 and D40 with those regions (FU-CM-125).";
const NEXT_STEP_VARIANT = "A state variant of a compared board whose difference is the next-step block (a blocked or waiting step with its reason and holder, and no primary action); the block is drawn by the shared next-step answer and every stage of a whole contract is checked for it by test_cm_dead_end. A separate fixture of this exact state was not captured, so it is not compared (FU-CM-125).";
export const NOT_COMPARED = {
	"D11-T": "The terminated contract whose settlement continues is the state the Obligations tab already draws as D20-T (the specification gives D11-T and D20-T the same accepted-delivery settlement message, and the same isolated contract), with the same facts, wording and next step; a second page for it would repeat that screen, so it is compared there (CM-CHG-001 v0.8 section 5.21). D20-P is the state before the notice takes effect and is not this one.",
	"D09": "The Invoices summary is drawn for a contract owner who has a replacement follow-up as the next step, with a payment region that has no title of its own; the built screen titles the region and carries the reader's real next step. The payment screens that carry the money are compared as D09-F, D09-T and D09-AUD (FU-CM-125).",
	"D10": WORK_REGISTER, "D40": WORK_REGISTER, "D40-AO": WORK_REGISTER, "D40-HOD": WORK_REGISTER, "D40-F": WORK_REGISTER, "D40-AUD": WORK_REGISTER, "D40-S": WORK_REGISTER, "D40-T": WORK_REGISTER,
	"D40-D": "A Departmental Author who holds no Contract Management responsibility is refused: the shared denied page is the built screen and it is compared as D-DENIED.",
	"D02-H": NEXT_STEP_VARIANT, "D02-S": NEXT_STEP_VARIANT, "D07-P": NEXT_STEP_VARIANT, "D33-W": NEXT_STEP_VARIANT, "D09-F · Submitted": NEXT_STEP_VARIANT, "D09-F · Stale": NEXT_STEP_VARIANT,
	"D17 · Posted": NEXT_STEP_VARIANT, "D17 · Pending": NEXT_STEP_VARIANT, "D28-F": NEXT_STEP_VARIANT, "D27 · Blocked": NEXT_STEP_VARIANT,
	"D07 · Correction": "The dialog that asks for a correction of an acceptance report is built as the request-correction dialog of the report screen; its own fixture was not captured, so it is not compared (FU-CM-125).",
	"D33-A · Posted": "The accounting invoice once posted is the same screen as D33-A with its primary action gone and the posting result in its next step; it was not captured as its own fixture (FU-CM-125).",
	"D28-F · Editor": "The payment editor for the remaining amount is the payment editor of D09-F with the remaining amount filled in; it was not captured as its own fixture (FU-CM-125).",
};
