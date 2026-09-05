<script setup>
import { ref, computed, onActivated, onMounted, watch } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import { getBudgetLinePosition } from "../data/budgetApi.js";

const { route } = useRouteState("budget-funding");

const lineIdParam = computed(() => route.value[2]);

const line = ref(null);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: line.value?.code || lineIdParam.value },
]);
const railEl = ref(null);
// BUD-CHG-001 v1.3 Phase 4/7 — one site is one Procuring Entity: no global
// PE switcher on this rail any more.
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const serverError = ref(false);

async function load(opts) {
	if (!lineIdParam.value) return;
	if (!(opts && opts.quiet === true)) loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	serverError.value = false;
	try {
		line.value = await getBudgetLinePosition(lineIdParam.value);
	} catch (e) {
		if (e.httpStatus === 403) forbidden.value = true;
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		loading.value = false;
	}
}

onMounted(load);
watch(lineIdParam, (v, prev) => {
	if (v && v !== prev) load();
});
// KeepAlive brings this instance back with the record still on screen:
// revalidate in place rather than re-showing the skeleton.
let activations = 0;
onActivated(() => {
	if (activations++ === 0 || !line.value) return;
	load({ quiet: true });
});
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div class="kt-shell">
			<template v-if="loading">
				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-skel" style="width: 280px; height: 20px"></div>
				</div>
			</template>

			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-not-found">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This Budget Line could not be found.") }}</h2>
			</div>

			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-forbidden">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("You do not have access to this Budget Line.") }}</h2>
			</div>

			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-server-error">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This Budget Line could not be loaded.") }}</h2>
				<button type="button" class="kt-btn kt-btn-primary" @click="load">{{ __("Try again") }}</button>
			</div>

			<!-- BUD-DES-06/06A -->
			<template v-else-if="line">
				<div style="margin-bottom: 16px" data-testid="bud-line-header">
					<div class="kt-eyebrow" style="margin-bottom: 8px">{{ line.code }}</div>
					<div style="display: flex; align-items: center; gap: 12px">
						<h1 style="margin: 0">{{ line.title }}</h1>
						<span class="kt-status is-live">{{ line.version.status }}</span>
					</div>
				</div>

				<div style="display: flex; gap: 40px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Budget") }}</div>
						<div style="font-size: 15px; font-weight: 500">{{ line.budget.code }} · {{ __("Version {0}", [line.version.version_number]) }}</div>
					</div>
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Financial Year") }}</div>
						<div style="font-size: 15px; font-weight: 500">{{ line.budget.fiscal_year.label }}</div>
					</div>
				</div>

				<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px" data-testid="bud-line-position-cards">
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Approved") }}</div>
						<div class="kt-figure" style="font-size: 26px">{{ formatKes(line.positions.approved, line.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Reserved") }}</div>
						<div class="kt-figure is-attention" style="font-size: 26px">{{ formatKes(line.positions.reserved, line.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Committed") }}</div>
						<div class="kt-figure" style="font-size: 26px; color: #1d4ed8">{{ formatKes(line.positions.committed, line.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Available") }}</div>
						<div class="kt-figure is-live" style="font-size: 26px">{{ formatKes(line.positions.available, line.currency) }}</div>
					</div>
				</div>

				<div class="kt-card kt-blueprint" style="margin-bottom: 16px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Line identity") }}</div>
					<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px">
						<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Owner scope") }}</div><div style="font-size: 14px; font-weight: 500">{{ line.owner_org_unit }}</div></div>
						<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Funding source") }}</div><div style="font-size: 14px; font-weight: 500">{{ line.funding_source }}</div></div>
						<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Active version") }}</div><div style="font-size: 14px; font-weight: 500">{{ __("Version {0}", [line.version.version_number]) }}</div></div>
					</div>
				</div>

				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Active reservations") }}</div>

					<!-- BUD-DES-06 empty state -->
					<div v-if="!line.reservations.length" style="display: flex; flex-direction: column; align-items: center; text-align: center; padding: 32px 0; gap: 6px" data-testid="bud-line-reservations-empty">
						<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 17px">{{ __("No active reservations") }}</div>
						<div class="kt-muted" style="font-size: 14px; max-width: 44ch">{{ __("This Budget Line has no confirmed funding reservations.") }}</div>
					</div>

					<!-- BUD-DES-06A reservations table -->
					<table v-else class="kt-table" data-testid="bud-line-reservations-table">
						<thead>
							<tr>
								<th>{{ __("Reservation") }}</th>
								<th>{{ __("Plan Item") }}</th>
								<th style="text-align: right">{{ __("Original amount") }}</th>
								<th style="text-align: right">{{ __("Remaining amount") }}</th>
								<th>{{ __("Status") }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="rsv in line.reservations" :key="rsv.id">
								<td>{{ rsv.code }}</td>
								<td>{{ rsv.plan_item_label }}</td>
								<td style="text-align: right">{{ formatKes(rsv.original_amount, line.currency) }}</td>
								<td style="text-align: right">{{ formatKes(rsv.remaining_amount, line.currency) }}</td>
								<td><span class="kt-status is-live">{{ rsv.status }}</span></td>
								<td style="white-space: nowrap">
									<a v-if="rsv.plan_item_url" :href="rsv.plan_item_url" style="font-size: 13px; font-weight: 500; text-decoration: none">{{ __("View Plan Item") }}</a>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</div>
	</div>
</template>
