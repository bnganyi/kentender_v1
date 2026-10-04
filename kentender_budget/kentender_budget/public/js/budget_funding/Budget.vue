<script setup>
import { computed, provide, ref } from "vue";
import { useRouteState } from "../budget_shared/composables/useRouteState.js";
import { usePageRail, BUDGET_RAIL } from "../budget_shared/composables/usePageRail.js";
import BudgetWorkspaceScreen from "./components/BudgetWorkspaceScreen.vue";
import RegisterAllocationScreen from "./components/RegisterAllocationScreen.vue";
import BudgetVersionEditorScreen from "./components/BudgetVersionEditorScreen.vue";
import BudgetDetailScreen from "./components/BudgetDetailScreen.vue";
import BudgetClosureScreen from "./components/BudgetClosureScreen.vue";
import BudgetApprovalTaskScreen from "./components/BudgetApprovalTaskScreen.vue";
import BudgetLineDetailScreen from "./components/BudgetLineDetailScreen.vue";

// BUD-CHG-001 v1.9 §10 — the five canonical routes (plus the closure
// composition on BUD-UI-03) share one Frappe Page, "budget-funding" (not the
// spec's literal "budget": that permanently collides with ERPNext's own
// Budget DocType route in Frappe's client router — see budget_funding_page.js).
const { route } = useRouteState("budget-funding");

const screen = computed(() => {
	const seg = route.value[1];
	if (!seg) return "workspace";
	if (seg === "review") return "review";
	if (seg === "line") return "line";
	if (seg === "new") return "register";
	if (route.value[2] === "version") return "editor";
	if (route.value[2] === "close") return "closure";
	return "detail";
});

const SCREENS = {
	workspace: BudgetWorkspaceScreen,
	register: RegisterAllocationScreen,
	editor: BudgetVersionEditorScreen,
	detail: BudgetDetailScreen,
	closure: BudgetClosureScreen,
	review: BudgetApprovalTaskScreen,
	line: BudgetLineDetailScreen,
};
const screenComponent = computed(() => SCREENS[screen.value] || null);

// One rail for every screen: each screen publishes its trail here instead of
// mounting a rail of its own. KeepAlive keeps a visited screen's instance
// (and data), so coming back renders at once and revalidates in place.
const railEl = ref(null);
const trail = ref([
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding") },
]);
provide(BUDGET_RAIL, {
	setTrail(next) {
		trail.value = next;
	},
});
usePageRail(railEl, trail, { showPeSwitcher: false });
</script>

<template>
	<div class="kt-industry" data-testid="bud-shell" :data-screen="screen">
		<div ref="railEl" class="kt-rail-mount"></div>
		<KeepAlive>
			<component :is="screenComponent" />
		</KeepAlive>
		<div v-if="!screenComponent" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty">
				<h2>{{ __("This screen is not available yet.") }}</h2>
				<p class="kt-muted">{{ __("This part of Budget & Funding is still being built.") }}</p>
			</div>
		</div>
	</div>
</template>
