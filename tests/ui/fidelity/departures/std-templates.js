// Structural departures for STD Templates (STD-TPL-001 v0.10 §11; board
// `docs/mvp-1-r1/07_std_configuration/design/STD Templates Artboards.dc.html`).
//
// Keyed `Component#variant`. Every entry names what the build adds or omits
// that the board does not draw, why, and the authority for it. Unregistered
// additions fail; stale entries fail too.
//
// Boards compared structurally: STD-DES-01, 02, 02C and 02R. The variant
// boards STD-DES-01F/01E/01R and 02A/02F/02S/02W are generated inside the
// design tool's `sc-for` loops (`id="{{ st.anchor }}"`), so their raw markup
// is a template with every `sc-if` branch present, not a drawable state; they
// are proven by the browser journeys in tests/ui/smoke/std_templates/ instead
// (plan ruling R6: the board wins on layout, the projection on values).
export const DEPARTURES = {};

export const COVERED = [
	"ReleaseList#std-des-01",
	"ReleaseDetail#std-des-02",
	"ReportConcernDialog#std-des-02c",
	"ReleaseDetail#std-des-02r",
];
