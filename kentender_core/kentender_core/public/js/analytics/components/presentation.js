// Presentation helpers for the Analytics page. They draw what the server sent: nothing here makes a count,
// a percentage, a label, a band, a date or an amount (ANL §16). The arithmetic that remains is geometry,
// and that lives in the chart components.

/** A plain click follows the page's own route; a modified click keeps the browser's behaviour on the href. */
export function isPlainClick(event) {
	return !(event.defaultPrevented || event.button > 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
}

/** An icon name as the icon table spells it: a payload's `departmental-planning` is the area `departmental_planning`. */
export function iconKey(name) {
	return String(name || "").replace(/-/g, "_");
}

/** "2 Needs accepted for planning" is drawn as the figure "2" (display size) and "Needs accepted for planning"
 * beside it, as the boards draw it: the sentence the server sent, with the figure it already starts with
 * shown separately. A sentence that does not start with the figure (a "totals are unavailable" line) is drawn whole. */
export function splitLead(sentence, figure) {
	const text = String(sentence || "");
	const lead = String(figure === undefined || figure === null ? "" : figure);
	if (lead && text.startsWith(lead + " ")) return { figure: lead, rest: text.slice(lead.length + 1) };
	return { figure: "", rest: text };
}

// The tones the charts do not know (`pair-mid`, `muted`) and the Tender bucket tones are drawn the way the
// BOARDS draw them, in this wrapper, never in the chart components (lead's instruction, 5 Oct 2026):
//   pair-mid (Partly covered)   ANL-DES-21 draws it with the design system's family-2 swatch;
//   muted + Status unavailable  ANL-DES-31F draws neutral-400, which is the charts' own fallback for an unknown tone;
//   muted + Closed              ANL-DES-21 and 22 draw Closed with cat-5.
// ANL-DES-21 and 22 also draw the Tender buckets Preparation, Open, Evaluation, Award, Closed with cat-1 to cat-5
// in that order, where the payload leaves cat-3 free and shifts Evaluation and Award up; with Closed on cat-5 that
// would put Award and Closed on one swatch, so the five Tender buckets take the board's tones. Other tones are the server's.
const TENDER_BOARD_TONES = { preparation: "cat-1", open: "cat-2", evaluation: "cat-3", award: "cat-4", closed: "cat-5" };

export function boardTone(areaKey, segment) {
	if (areaKey === "tender_proceedings" && TENDER_BOARD_TONES[segment.key]) return TENDER_BOARD_TONES[segment.key];
	if (segment.tone === "pair-mid") return "family-2";
	return segment.tone;
}
