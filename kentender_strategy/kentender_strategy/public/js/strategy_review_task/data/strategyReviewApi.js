// Live data adapter for STR-UI-04 (Review task).

async function call(method, args) {
	const response = await frappe.call({ method, args, freeze: false });
	return response.message;
}

export const getVersionReviewOverview = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_review_overview", { plan_version_id: planVersionId });

export const getStrategyTree = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_tree", { plan_version_id: planVersionId });

export const diffStrategyVersions = (compareVersionId, baseVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.diff_strategy_versions", {
		compare_version_id: compareVersionId,
		base_version_id: baseVersionId || null,
	});

export const getPlanHistory = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_history", { plan_id: planId });

export const reviewVersion = (planVersionId, action, reason) =>
	call("kentender_strategy.api.strategy_consumer_api.review_strategy_version", {
		plan_version_id: planVersionId,
		action,
		reason: reason || null,
	});

export const approveVersion = (planVersionId, action, reason) =>
	call("kentender_strategy.api.strategy_consumer_api.approve_strategy_version", {
		plan_version_id: planVersionId,
		action,
		reason: reason || null,
	});
