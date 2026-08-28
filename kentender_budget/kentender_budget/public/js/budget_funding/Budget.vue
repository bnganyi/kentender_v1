<script setup>
import { computed } from "vue";
import { useRouteState } from "../budget_shared/composables/useRouteState.js";
import BudgetWorkspaceScreen from "./components/BudgetWorkspaceScreen.vue";
import BudgetVersionEditorScreen from "./components/BudgetVersionEditorScreen.vue";
import BudgetDetailScreen from "./components/BudgetDetailScreen.vue";
import BudgetApprovalTaskScreen from "./components/BudgetApprovalTaskScreen.vue";
import BudgetLineDetailScreen from "./components/BudgetLineDetailScreen.vue";

// BUD-CHG-001 v1.2 §10 — all five Budget screens share one Frappe Page
// ("budget-funding", not the spec's literal "budget" — that collides with
// the existing Budget doctype's own List View route in Frappe's client
// router, see budget_funding_page.js). Each screen owns its own
// usePageRail() call (mirrors kentender_strategy's separate pages, just
// dispatched from one root instead of five bundles) — only ever one is
// mounted at a time via v-if, so only one PageRail instance is ever active.
const { route } = useRouteState("budget-funding");

const screen = computed(() => {
	const seg = route.value[1];
	if (!seg) return "workspace";
	if (seg === "review") return "review";
	if (seg === "line") return "line";
	if (seg === "new" || route.value[2] === "version") return "editor";
	return "detail";
});
</script>

<template>
	<BudgetWorkspaceScreen v-if="screen === 'workspace'" />
	<BudgetVersionEditorScreen v-else-if="screen === 'editor'" />
	<BudgetDetailScreen v-else-if="screen === 'detail'" />
	<BudgetApprovalTaskScreen v-else-if="screen === 'review'" />
	<BudgetLineDetailScreen v-else-if="screen === 'line'" />
	<div v-else class="kt-industry">
		<div class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This screen is not available yet.") }}</h2>
				<p class="kt-muted">{{ __("This part of Budget & Funding is still being built.") }}</p>
			</div>
		</div>
	</div>
</template>
