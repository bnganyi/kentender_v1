// ANL-CHG-001 v0.8 plan Phase 4, D8 — shared helpers for the Analytics chart components.
// The browser computes no count, percentage, label or axis from rows (ANL §10A.1, KT-STD-001 §2.6.10):
// the server supplies every number and every piece of text. The only arithmetic here is geometry
// (a width or height from the numbers given) and the choice of which supplied item is drawn.

/** Tone keys a chart accepts, one per data-colour role (ANL §10A.1 rule 3). Each maps to a design-system
 * swatch class (`is-cat-1`, ...). Status red, amber and green are deliberately not tones. */
export const TONES = Object.freeze([
	"cat-1", "cat-2", "cat-3", "cat-4", "cat-5", "cat-6", // categorical set: stages, states, monthly series
	"seq-1", "seq-2", "seq-3", "seq-4", // sequential ramp, light to dark: waiting bands
	"pair-strong", "pair-tint", // paired tones: Covered / Not yet covered
	"family-1", "family-2", "family-3", // one family, darkest to lightest: Reserved / Committed / Available
]);

/** The swatch class for a tone key; an unknown key draws the design system's neutral fallback. */
export function toneClass(tone) {
	return TONES.includes(tone) ? "is-" + tone : "";
}

/** Fixed interface words only (table headings); every data word arrives from the server. */
export function t(text) {
	return typeof globalThis.__ === "function" ? globalThis.__(text) : text;
}

/** The text drawn for a value: the server's `text` when it sent one, otherwise the integer it sent. */
export function textOf(item) {
	if (item && item.text !== undefined && item.text !== null && item.text !== "") return String(item.text);
	return item && item.count !== undefined && item.count !== null ? String(item.count) : "";
}

/** A number as a CSS percentage with at most two decimals, clamped to 0..100 (geometry only). */
export function percent(part, whole) {
	if (!(whole > 0) || !(part > 0)) return "0%";
	return Math.round(Math.min(100, (part / whole) * 100) * 100) / 100 + "%";
}

export function keepSet(keepZero) {
	return new Set(Array.isArray(keepZero) ? keepZero : keepZero ? [keepZero] : []);
}
