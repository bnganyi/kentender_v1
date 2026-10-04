// STR-CHG-001 v1.8 §8.2 / KT-STD-001 §3, §11 — one idempotency identity per
// command attempt. The key is minted when an attempt begins, sent with the
// command, reused on retry and after a lost response (also across a browser
// reload, via sessionStorage), and discarded once the server confirms a
// result. Different commands have distinct scopes, so a structure save and
// the submission that follows it never share an identity.

function storageKey(scope) {
	return `kt-strategy-attempt:${scope}`;
}

function randomKey() {
	if (window.crypto && typeof window.crypto.randomUUID === "function") return window.crypto.randomUUID();
	return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

export function attemptKey(scope) {
	try {
		const existing = window.sessionStorage.getItem(storageKey(scope));
		if (existing) return existing;
	} catch (e) {
		// storage unavailable — an in-memory key still de-duplicates retries
	}
	const key = randomKey();
	try {
		window.sessionStorage.setItem(storageKey(scope), key);
	} catch (e) {
		// ignore
	}
	return key;
}

export function hasPendingAttempt(scope) {
	try {
		return !!window.sessionStorage.getItem(storageKey(scope));
	} catch (e) {
		return false;
	}
}

export function clearAttempt(scope) {
	try {
		window.sessionStorage.removeItem(storageKey(scope));
	} catch (e) {
		// ignore
	}
}

/**
 * Run `fn(key)` as one attempt. A confirmed result or a known rejection
 * ends the attempt. A lost response replays the same request once with the
 * same key (the server journal returns the original result if it did
 * commit); if that is lost too, the key is kept so the next user action —
 * or the page after a reload — resolves the same attempt instead of
 * inventing a new one. `onUnknown` lets the screen say "We could not
 * confirm the result. Checking the existing request…" while it replays.
 */
export async function runAttempt(scope, fn, { onUnknown } = {}) {
	const key = attemptKey(scope);
	try {
		const result = await fn(key);
		clearAttempt(scope);
		return result;
	} catch (error) {
		if (!error || !error.unknownOutcome) {
			clearAttempt(scope);
			throw error;
		}
		if (onUnknown) onUnknown();
		try {
			const result = await fn(key);
			clearAttempt(scope);
			return result;
		} catch (again) {
			if (!again || !again.unknownOutcome) clearAttempt(scope);
			throw again;
		}
	}
}
