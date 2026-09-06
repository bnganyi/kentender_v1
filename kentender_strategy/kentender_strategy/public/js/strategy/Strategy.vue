<script setup>
import { computed, provide, ref } from "vue";
import { useRouteState } from "../strategy_shared/composables/useRouteState.js";
import { usePageRail, STRATEGY_RAIL } from "../strategy_shared/composables/usePageRail.js";
import PortfolioScreen from "./screens/PortfolioScreen.vue";
import PlanWorkspaceScreen from "./screens/PlanWorkspaceScreen.vue";
import ApprovalTaskScreen from "./screens/ApprovalTaskScreen.vue";

// STR-CHG-001 v1.7 §10 — the four canonical screens share one Frappe Page
// ("strategy"); the route segments pick the screen. KeepAlive keeps a
// visited screen's instance (and its data), so coming back to it renders at
// once and revalidates in place (AGENTS.md §6.4).
const { route } = useRouteState("strategy");

const screen = computed(() => {
	const seg = route.value[1];
	if (seg === "plan") return "plan";
	if (seg === "approval") return "approval";
	return "portfolio";
});

const SCREENS = {
	portfolio: PortfolioScreen,
	plan: PlanWorkspaceScreen,
	approval: ApprovalTaskScreen,
};
const screenComponent = computed(() => SCREENS[screen.value]);

// One rail for every screen: each screen publishes its trail here instead of
// mounting a rail of its own (which was torn down on every screen switch).
const railEl = ref(null);
const trail = ref([
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Strategy Alignment") },
]);
provide(STRATEGY_RAIL, {
	setTrail(next) {
		trail.value = next;
	},
});
usePageRail(railEl, trail, { showPeSwitcher: false });
</script>

<template>
	<div class="kt-industry" data-testid="str-shell" :data-screen="screen">
		<div ref="railEl" class="kt-rail-mount"></div>
		<KeepAlive>
			<component :is="screenComponent" />
		</KeepAlive>
	</div>
</template>
