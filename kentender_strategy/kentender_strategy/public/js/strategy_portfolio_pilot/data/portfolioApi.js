// Live data adapter for kentender_strategy.api.strategy_api.get_strategy_portfolio.
// Response shape verified directly against the real endpoint (bench execute), not assumed.

const METHOD = "kentender_strategy.api.strategy_api.get_strategy_portfolio";

const STATUS_TONE = {
	Active: "accent",
	Approved: "accent",
};

function statusTone(status) {
	return STATUS_TONE[status] || "outline";
}

// Server rows only expose attention_kind "none" | "risk" (no per-row "due" flag) —
// the quick-stat "Measurements due" tile is display-only for that reason (see StrategyPortfolioPilot.vue).
export function toPortfolioRow(row) {
	return {
		code: row.code,
		title: row.name,
		type: row.plan_type,
		period: row.effective_period_label,
		version: `v${row.version_number}`,
		status: row.status,
		statusTone: statusTone(row.status),
		attention: row.attention,
		attentionMuted: row.attention_tone === "muted",
		isRisk: row.attention_kind === "risk",
		entity: row.procuring_entity_name,
	};
}

export function toWorkItem(item) {
	return { label: item.label, ref: item.plan_code };
}

export async function fetchPortfolio(procuringEntity) {
	const response = await frappe.call({
		method: METHOD,
		args: procuringEntity ? { procuring_entity: procuringEntity } : {},
		freeze: false,
	});
	return response.message;
}
