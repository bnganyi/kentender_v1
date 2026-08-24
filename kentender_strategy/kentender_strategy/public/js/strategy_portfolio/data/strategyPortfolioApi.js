// Live data adapter for kentender_strategy.api.strategy_ui_api (STR-UI-01)
// and strategy_consumer_api.save_strategy_plan_draft (the "New strategic
// plan" draft-create action).

export async function fetchPortfolio() {
	const response = await frappe.call({
		method: "kentender_strategy.api.strategy_ui_api.get_strategy_portfolio",
		args: {},
		freeze: false,
	});
	return response.message;
}

export async function saveNewPlanDraft(payload) {
	const response = await frappe.call({
		method: "kentender_strategy.api.strategy_consumer_api.save_strategy_plan_draft",
		args: { payload },
		freeze: false,
	});
	return response.message;
}
