<script setup>
import { reactive, computed, onMounted } from "vue";
import QuickStatsStrip from "./components/QuickStatsStrip.vue";
import PortfolioFilterBar from "./components/PortfolioFilterBar.vue";
import PortfolioTable from "./components/PortfolioTable.vue";
import MyWorkList from "./components/MyWorkList.vue";
import ErrorState from "./components/ErrorState.vue";
import PlanDetailDrawer from "./components/PlanDetailDrawer.vue";
import { usePortfolio } from "./composables/usePortfolio.js";
import { useRouteState } from "./composables/useRouteState.js";

const { plans, counts, entities, myWork, capabilities, loading, error, refresh } = usePortfolio();
onMounted(refresh);

const { selectedCode, openPlan, closePlan } = useRouteState();

const filters = reactive({ q: "", type: "", period: "", status: "", entity: "" });
const quick = reactive({ active: "" }); // '' | 'active' | 'review' | 'attention'

function setQuick(key) {
	quick.active = quick.active === key ? "" : key;
}

function clearFilters() {
	filters.q = "";
	filters.type = "";
	filters.period = "";
	filters.status = "";
	filters.entity = "";
	quick.active = "";
}

const filteredRows = computed(() => {
	const needle = filters.q.trim().toLowerCase();
	return plans.value.filter((plan) => {
		if (
			needle &&
			!(plan.code.toLowerCase().includes(needle) || plan.title.toLowerCase().includes(needle))
		)
			return false;
		if (filters.type && plan.type !== filters.type) return false;
		if (filters.period && plan.period !== filters.period) return false;
		if (filters.status && plan.status !== filters.status) return false;
		if (filters.entity && plan.entity !== filters.entity) return false;
		if (quick.active === "active" && plan.status !== "Active") return false;
		if (quick.active === "review" && plan.status !== "Submitted") return false;
		if (quick.active === "attention" && !plan.isRisk) return false;
		return true;
	});
});

const countLabel = computed(() => {
	const n = filteredRows.value.length;
	return n === plans.value.length ? `${n} plans` : `${n} of ${plans.value.length} plans`;
});

const isServerEmpty = computed(() => !loading.value && !error.value && plans.value.length === 0);

// "Measurements due" has no per-row flag in the API response (only attention_kind
// none|risk) — the tile shows the server's real count but isn't clickable as a filter.
const statItems = computed(() => [
	{ key: "active", count: counts.value.active ?? 0, label: "Active plans" },
	{ key: "review", count: counts.value.submitted ?? 0, label: "Awaiting review" },
	{ key: "due", count: counts.value.measurements_due ?? 0, label: "Measurements due", filterable: false },
	{ key: "attention", count: counts.value.measurement_attention ?? 0, label: "Needs attention" },
]);

const periodOptions = computed(() =>
	[...new Set(plans.value.map((p) => p.period))].sort()
);
</script>

<template>
	<div class="kt-portfolio-pilot">
		<div class="kt-pp-banner">
			Pilot spike — Claude Design → Vue 3, live kentender_strategy data. Not a production screen.
		</div>

		<div class="kt-pp-shell">
			<header class="kt-pp-header">
				<div class="kt-pp-header__intro">
					<div class="kt-pp-header__eyebrow">KenTender · Strategic Alignment</div>
					<h1>Strategy Alignment</h1>
					<p>
						Govern strategic outcomes, public-value commitments and performance targets used
						across procurement.
					</p>
				</div>
				<button
					type="button"
					class="kt-pp-btn kt-pp-btn--primary"
					:disabled="!capabilities.create_plan"
					:title="
						capabilities.create_plan
							? 'Pilot — permitted by your role, but not wired to a live action'
							: 'Your role is not permitted to create plans'
					"
				>
					Create strategic plan
				</button>
			</header>

			<QuickStatsStrip :items="statItems" :active-key="quick.active" @select="setQuick" />

			<PortfolioFilterBar
				v-model="filters"
				:cross-entity="true"
				:period-options="periodOptions"
				:entity-options="entities"
				@clear="clearFilters"
			/>

			<ErrorState v-if="error" :error="error" @retry="refresh" />
			<PortfolioTable
				v-else
				:rows="filteredRows"
				:count-label="countLabel"
				:loading="loading"
				:is-server-empty="isServerEmpty"
				@clear-filters="clearFilters"
				@open-plan="openPlan"
			/>

			<MyWorkList v-if="myWork.length" :items="myWork" />
		</div>

		<PlanDetailDrawer
			v-if="selectedCode"
			:code="selectedCode"
			@close="closePlan"
			@after-action="refresh"
		/>
	</div>
</template>

<style scoped>
.kt-pp-banner {
	background: #fff4d6;
	color: #6b4f00;
	font-size: 12px;
	padding: 6px 12px;
	text-align: center;
	border-bottom: 1px solid color-mix(in srgb, #6b4f00 25%, transparent);
}
.kt-pp-shell {
	max-width: 1160px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	gap: 27px;
	padding-top: 27px;
}
.kt-pp-header {
	display: flex;
	align-items: flex-start;
	gap: 34px;
}
.kt-pp-header__intro {
	max-width: 640px;
}
.kt-pp-header__eyebrow {
	font-size: 11px;
	letter-spacing: 0.1em;
	text-transform: uppercase;
	color: var(--ktpp-color-accent-700);
	margin-bottom: 8px;
}
.kt-pp-header h1 {
	font-size: 40px;
	margin-bottom: 6px;
}
.kt-pp-header p {
	margin: 0;
	font-size: 15px;
	color: color-mix(in srgb, var(--ktpp-color-text) 65%, transparent);
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	padding: 9px 16px;
	border-radius: var(--ktpp-radius-md);
	border: 1px solid transparent;
	margin-left: auto;
	margin-top: 26px;
}
.kt-pp-btn--primary {
	background: var(--ktpp-color-accent);
	color: var(--ktpp-color-bg);
	border-color: var(--ktpp-color-accent);
}
.kt-pp-btn--primary:hover:not(:disabled) {
	background: var(--ktpp-color-accent-600);
}
.kt-pp-btn--primary:disabled {
	opacity: 0.45;
	cursor: not-allowed;
}
</style>
