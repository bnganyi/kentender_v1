// Live data adapter for STR-UI-02 (Plan workspace) / STR-UI-03 (Structure editor).

async function call(method, args) {
	const response = await frappe.call({ method, args, freeze: false });
	return response.message;
}

export const getPlanWorkspace = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_workspace", { plan_id: planId });

export const getPlanHistory = (planId) =>
	call("kentender_strategy.api.strategy_ui_api.get_plan_history", { plan_id: planId });

export const getVersionHistory = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_version_history", { plan_version_id: planVersionId });

export const getStrategyTree = (planVersionId) =>
	call("kentender_strategy.api.strategy_ui_api.get_strategy_tree", { plan_version_id: planVersionId });

export const saveStructureDraft = (planVersionId, { nodes, indicators, targets, deletes, expectedVersion }) =>
	call("kentender_strategy.api.strategy_consumer_api.save_strategy_structure_draft", {
		plan_version_id: planVersionId,
		nodes: nodes || [],
		indicators: indicators || [],
		targets: targets || [],
		deletes: deletes || [],
		expected_version: expectedVersion || null,
	});

export const submitVersion = (planVersionId) =>
	call("kentender_strategy.api.strategy_consumer_api.submit_strategy_version", {
		plan_version_id: planVersionId,
	});

export const activateVersion = (planVersionId) =>
	call("kentender_strategy.api.strategy_consumer_api.activate_strategy_version", {
		plan_version_id: planVersionId,
	});

export const createSuccessorVersion = (planId) =>
	call("kentender_strategy.api.strategy_consumer_api.create_strategy_successor_version", {
		plan_id: planId,
	});
