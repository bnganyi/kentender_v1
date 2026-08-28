// Matches kentender_budget.services.budget_contracts.format_kes_full exactly
// ("{currency} {amount:,.0f}") — the display convention every Budget
// artboard uses (e.g. "KES 160,000,000").
export function formatKes(amount, currency) {
	const value = Math.round(Number(amount) || 0);
	return `${currency || "KES"} ${value.toLocaleString("en-US")}`;
}
