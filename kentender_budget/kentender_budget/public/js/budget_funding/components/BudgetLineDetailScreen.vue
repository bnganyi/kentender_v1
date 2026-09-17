<script setup>
import { ref, computed, onActivated, onMounted, watch } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import { getBudgetLinePosition } from "../data/budgetApi.js";

// BUD-UI-05 — BUD-DES-06/06A/06B (BUD-CHG-001 v1.9 §11.6, §11.6A, §11.19,
// §12.4): the live position, then each reservation led by its Requisition
// and source department, with original/still reserved and the requires-
// review reason. Read-only; links only where the server returned them.
const { route, epoch } = useRouteState("budget-funding");
const lineIdParam = computed(() => route.value[2]);
const line = ref(null);
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: line.value?.budget?.code || "", route: line.value ? ["budget-funding", line.value.budget.code] : undefined },
	{ label: line.value?.code || lineIdParam.value },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const guard = kentender_core.desk_page.createSequenceGuard();
const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(null);
const serverError = ref(false);

async function load(opts) {
	if (!lineIdParam.value) return;
	const quiet = !!(opts && opts.quiet) && !!line.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	notFound.value = false;
	forbidden.value = null;
	serverError.value = false;
	try {
		const data = await getBudgetLinePosition(lineIdParam.value);
		if (!guard.isCurrent(token)) return;
		if (data && data.outcome === "FORBIDDEN") {
			line.value = null;
			forbidden.value = data.forbidden;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			line.value = null;
			notFound.value = true;
			return;
		}
		line.value = data;
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this budget line"), text: "" };
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}
onMounted(load);
watch(lineIdParam, (v, prev) => v && v !== prev && (line.value = null, load()));
let activations = 0;
onActivated(() => activations++ > 0 && line.value && load({ quiet: true }));
watch(epoch, () => line.value && load({ quiet: true }));

const currency = computed(() => line.value?.currency || "KES");
const availablePct = computed(() => (line.value?.positions.approved ? (line.value.positions.available / line.value.positions.approved) * 100 : 100));
const availableClass = computed(() => (availablePct.value <= 0 ? "is-critical" : availablePct.value < 50 ? "is-attention" : "is-live"));
const barCommitted = computed(() => (line.value?.positions.approved ? Math.min(100, (line.value.positions.committed / line.value.positions.approved) * 100) : 0));
const barReserved = computed(() => (line.value?.positions.approved ? Math.min(100 - barCommitted.value, (line.value.positions.reserved / line.value.positions.approved) * 100) : 0));
function pad(i) {
	return String(i + 1).padStart(2, "0");
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-line" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" style="max-width: 1000px">
			<div v-if="loading" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 280px; height: 20px"></div></div>
			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-not-found"><h2>{{ __("This budget line could not be found.") }}</h2></div>
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-forbidden"><h2>{{ __(forbidden.heading) }}</h2><p v-if="forbidden.text" class="kt-muted">{{ __(forbidden.text) }}</p></div>
			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="bud-line-server-error"><h2>{{ __("This budget line could not be loaded.") }}</h2><button type="button" class="kt-btn kt-btn-primary" @click="load()">{{ __("Try again") }}</button></div>

			<template v-else-if="line">
				<div style="margin-bottom: 16px" data-testid="bud-line-header">
					<div class="kt-eyebrow" style="margin-bottom: 6px">{{ line.code }}</div>
					<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
						<h1 style="margin: 0">{{ line.title }}</h1>
						<span class="kt-status" :class="line.version.status === 'Closed' ? 'is-critical' : 'is-live'">{{ line.version.status === "Closed" ? __("Closed") : __("Current") }}</span>
					</div>
				</div>
				<div style="display: flex; gap: 32px; padding: 14px 0; border-top: 1px solid var(--kt-color-divider); border-bottom: 1px solid var(--kt-color-divider); margin-bottom: 24px; flex-wrap: wrap">
					<div><span class="kt-label">{{ __("Budget") }}</span> <span style="font-size: 14px; margin-left: 6px">{{ line.budget.code }} · {{ __("Version {0}", [line.version.version_number]) }}</span></div>
					<div><span class="kt-label">{{ __("Financial Year") }}</span> <span style="font-size: 14px; margin-left: 6px">{{ line.budget.fiscal_year.label }}</span></div>
				</div>

				<div class="kt-kpi-row" style="margin-bottom: 10px" data-testid="bud-line-position-cards">
					<div class="kt-kpi-card"><div class="kt-kpi-value">{{ formatKes(line.positions.approved, currency) }}</div><div class="kt-kpi-sub">{{ __("Registered allocation") }}</div></div>
					<div class="kt-kpi-card"><div class="kt-kpi-value" :class="{ 'is-zero': !line.positions.reserved }">{{ formatKes(line.positions.reserved, currency) }}</div><div class="kt-kpi-sub">{{ __("Reserved for requisitions") }}</div></div>
					<div class="kt-kpi-card"><div class="kt-kpi-value" :class="{ 'is-zero': !line.positions.committed }">{{ formatKes(line.positions.committed, currency) }}</div><div class="kt-kpi-sub">{{ __("Committed to contracts") }}</div></div>
					<div class="kt-kpi-card" :class="availableClass"><div class="kt-kpi-value">{{ formatKes(line.positions.available, currency) }}</div><div class="kt-kpi-sub">{{ __("Available to reserve") }}</div></div>
				</div>
				<div class="kt-bar" style="margin-bottom: 8px"><i class="kt-bar-committed" :style="{ width: barCommitted + '%' }"></i><i class="kt-bar-reserved" :style="{ width: barReserved + '%' }"></i></div>
				<p class="kt-muted" style="font-size: 12px; margin: 0 0 24px" data-testid="bud-line-as-at">{{ __("Funding position as at {0}", [line.as_at_display]) }}</p>

				<div v-if="line.explanation" class="kt-notice is-info" style="margin-bottom: 24px" data-testid="bud-line-explanation"><div class="kt-notice-body">{{ line.explanation }}</div></div>

				<div class="kt-card kt-blueprint" style="margin-bottom: 24px">
					<h3 class="kt-card-title">{{ __("Line identity") }}</h3>
					<div class="kt-grid-3" style="gap: 16px">
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Available to") }}</div><div style="font-size: 14px">{{ line.owner_org_unit }}</div></div>
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Funding source") }}</div><div style="font-size: 14px">{{ line.funding_source }}</div></div>
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Current version") }}</div><div style="font-size: 14px">{{ __("Version {0}", [line.version.version_number]) }}</div></div>
					</div>
				</div>

				<h3 class="kt-card-title" style="margin: 0 0 14px">{{ __("Active reservations") }}</h3>
				<div v-if="!line.reservations.length" class="kt-notice is-info" style="margin-bottom: 40px" data-testid="bud-line-reservations-empty">
					<div class="kt-notice-body"><strong>{{ __("No active reservations.") }}</strong> {{ __("This Budget Line has no confirmed funding reservations.") }}</div>
				</div>
				<div v-else class="kt-record-list" style="margin-bottom: 40px" data-testid="bud-line-reservations">
					<details v-for="(rsv, i) in line.reservations" :key="rsv.id" class="kt-record" :open="rsv.requires_review || rsv.converted > 0 ? true : undefined" data-testid="bud-line-reservation">
						<summary>
							<div class="kt-record-main">
								<div class="kt-record-index">{{ pad(i) }}</div>
								<div class="kt-record-body">
									<div class="kt-record-ref">{{ rsv.code }}</div>
									<div class="kt-record-title">{{ rsv.title }}</div>
									<div class="kt-record-meta"><span class="kt-status" :class="rsv.requires_review ? 'is-attention' : 'is-live'">{{ rsv.status_label }}</span><span v-if="rsv.plan_item_label">{{ __("Plan Item {0}", [rsv.plan_item_label]) }}</span></div>
								</div>
								<div class="kt-record-value">
									<div class="kt-record-amount">{{ formatKes(rsv.still_reserved, currency) }}</div>
									<div class="kt-record-sub">{{ __("Still reserved · originally {0}", [formatKes(rsv.originally_reserved, currency)]) }}</div>
								</div>
							</div>
							<div class="kt-record-footer">
								<span>
									<a v-if="rsv.requisition_url" :href="rsv.requisition_url" @click.stop>{{ __("View Requisition") }}</a>
									<span v-else-if="rsv.requisition_reference" class="kt-muted">{{ rsv.requisition_reference }}</span>
									<a v-if="rsv.plan_item_url" :href="rsv.plan_item_url" style="margin-left: 12px" @click.stop>{{ __("View Plan Item") }}</a>
								</span>
								<span class="kt-record-toggle"><span class="when-closed">{{ __("Show detail") }}</span><span class="when-open">{{ __("Hide detail") }}</span></span>
							</div>
						</summary>
						<div class="kt-record-detail" style="padding: 0">
							<div v-if="rsv.requires_review && rsv.review" class="kt-notice is-warning" style="margin: 14px" data-testid="bud-line-requires-review">
								<div class="kt-notice-body"><strong>{{ __("Requires review — funds remain reserved.") }}</strong> {{ rsv.review.reason }} {{ rsv.review.owner_hint }} {{ __("Nothing is released from this screen.") }}</div>
							</div>
							<table class="kt-table">
								<thead><tr><th>{{ __("Value") }}</th><th class="is-num">{{ __("Amount") }}</th></tr></thead>
								<tbody>
									<tr><td>{{ __("Originally reserved") }}</td><td class="is-num">{{ formatKes(rsv.originally_reserved, currency) }}</td></tr>
									<tr><td>{{ __("Converted into commitments") }}</td><td class="is-num" :class="{ 'is-zero': !rsv.converted }">{{ formatKes(rsv.converted, currency) }}</td></tr>
									<tr><td>{{ __("Released from this reservation") }}</td><td class="is-num" :class="{ 'is-zero': !rsv.released }">{{ formatKes(rsv.released, currency) }}</td></tr>
									<tr><td>{{ __("Still reserved") }}</td><td class="is-num">{{ formatKes(rsv.still_reserved, currency) }}</td></tr>
								</tbody>
							</table>
							<p class="kt-muted" style="font-size: 13px; margin: 0; padding: 14px">
								<template v-if="rsv.source_department">{{ __("Sourced from the {0} requisition line.", [rsv.source_department]) }} </template>
								<template v-if="rsv.converted > 0">{{ __("Contract records are shown once the Contract module publishes them; no payment is recorded here.") }}</template>
							</p>
						</div>
					</details>
				</div>
				<p class="kt-muted" style="font-size: 12px">{{ __("There is no release, convert or adjust action here; those belong to the owning Requisition and Contract processes.") }}</p>
			</template>
		</div>
	</div>
</template>
