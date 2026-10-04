// Matches kentender_budget.services.budget_contracts.format_kes_full exactly
// ("{currency} {amount:,.0f}") — the display convention every Budget
// artboard uses (e.g. "KES 160,000,000").
export function formatKes(amount, currency) {
	const value = Math.round(Number(amount) || 0);
	return `${currency || "KES"} ${value.toLocaleString("en-US")}`;
}

// "+ KES 10,000,000" / "− KES 10,000,000" / "KES 0" — the Change column
// convention on BUD-DES-08/10/15 (BUD-CHG-001 v1.9 §11.8).
export function formatSignedKes(amount, currency) {
	const value = Number(amount) || 0;
	if (Math.abs(value) < 0.005) return formatKes(0, currency);
	return `${value > 0 ? "+ " : "− "}${formatKes(Math.abs(value), currency)}`;
}

// One client-minted command key per user attempt (BUD-CHG-001 v1.9 §9.3;
// tracker D7). Replaying the same key returns the recorded result.
export function mintKey(label) {
	const random =
		typeof crypto !== "undefined" && crypto.randomUUID
			? crypto.randomUUID()
			: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
	return `${label || "cmd"}-${random}`;
}
