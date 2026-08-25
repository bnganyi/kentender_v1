// Live data adapter for kentender_strategy.api.strategy_ui_api (STR-UI-01)
// and strategy_consumer_api.save_strategy_plan_draft (the "New strategic
// plan" draft-create action).
import { frappeCall } from "../../strategy_shared/data/frappeCall.js";

export const fetchPortfolio = () =>
	frappeCall("kentender_strategy.api.strategy_ui_api.get_strategy_portfolio", {});

export const saveNewPlanDraft = (payload) =>
	frappeCall("kentender_strategy.api.strategy_consumer_api.save_strategy_plan_draft", { payload });
