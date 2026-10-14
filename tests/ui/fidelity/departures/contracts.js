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

export const DEPARTURES = {};

// Boards compared by a fidelity spec in `kentender_contracts/.../public/js`:
// listed here only when a spec importing this registry really compares them.
export const COVERED = ["D-ERR", "D-DENIED"];

// Rare-branch boards recorded as not compared. Each needs a reason that names
// the authority for leaving it out (tracker rule 14).
export const NOT_COMPARED = {};
