/**
 * UI-HARD-0120 / doc §19.1 — never surface raw stack traces or noisy engine dumps in ordinary UI.
 */

const FALLBACK = "Something went wrong. Please try again or contact support if the problem continues.";

/** Heuristic: multiline stacks with `at` frames are almost never user-safe copy. */
export function isProbableStackTrace(text: string): boolean {
	const t = String(text || "").trim();
	if (t.length < 32) {
		return false;
	}
	if (/\n\s+at\s+/.test(t)) {
		return true;
	}
	if (/^\s*Error:\s*\S/m.test(t) && /\n/.test(t) && /\bat\s+/.test(t)) {
		return true;
	}
	return false;
}

/** Returns a string safe to render as primary user copy (never a raw stack). */
export function safeUserPrimaryMessage(message: string): string {
	const raw = String(message || "").trim();
	if (!raw) {
		return FALLBACK;
	}
	if (isProbableStackTrace(raw)) {
		return FALLBACK;
	}
	return raw;
}

export function sanitizeDomToken(value: string): string {
	return String(value || "").replace(/[^A-Za-z0-9_-]/g, "_");
}
