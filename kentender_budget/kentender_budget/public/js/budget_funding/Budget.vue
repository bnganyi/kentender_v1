<script setup>
import { computed, provide, ref } from "vue";
import { useRouteState } from "../budget_shared/composables/useRouteState.js";
import { usePageRail, BUDGET_RAIL } from "../budget_shared/composables/usePageRail.js";
import BudgetWorkspaceScreen from "./components/BudgetWorkspaceScreen.vue";
import BudgetVersionEditorScreen from "./components/BudgetVersionEditorScreen.vue";
import BudgetDetailScreen from "./components/BudgetDetailScreen.vue";
import BudgetApprovalTaskScreen from "./components/BudgetApprovalTaskScreen.vue";
import BudgetLineDetailScreen from "./components/BudgetLineDetailScreen.vue";

// BUD-CHG-001 v1.3 §10/D5 — all five Budget screens share one Frappe Page
// ("budget-funding", not the spec's literal "budget" — that permanently
// collides with ERPNext's own restored Budget DocType's List View route in
// Frappe's client router, see budget_funding_page.js's own note).
const { route } = useRouteState("budget-funding");

const screen = computed(() => {
	const seg = route.value[1];
	if (!seg) return "workspace";
	if (seg === "review") return "review";
	if (seg === "line") return "line";
	if (seg === "new" || route.value[2] === "version") return "editor";
	return "detail";
});

const SCREENS = {
	workspace: BudgetWorkspaceScreen,
	editor: BudgetVersionEditorScreen,
	detail: BudgetDetailScreen,
	review: BudgetApprovalTaskScreen,
	line: BudgetLineDetailScreen,
};
const screenComponent = computed(() => SCREENS[screen.value] || null);

// One rail for every screen: each screen publishes its trail here instead of
// mounting a rail of its own, which was torn down and rebuilt on every
// screen switch. KeepAlive keeps a visited screen's instance (and data), so
// coming back to it renders at once and revalidates in place.
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
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<KeepAlive>
			<component :is="screenComponent" />
		</KeepAlive>
		<div v-if="!screenComponent" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This screen is not available yet.") }}</h2>
				<p class="kt-muted">{{ __("This part of Budget & Funding is still being built.") }}</p>
			</div>
		</div>
	</div>
</template>
