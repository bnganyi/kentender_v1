<script setup>
import { ref, computed, onActivated, onMounted, watch } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes, mintKey } from "../../budget_shared/data/formatKes.js";
import { getBudgetDetail, getBudgetLinesActive, getFundingActivity, getBudgetVersionHistory, createBudgetSuccessorVersion } from "../data/budgetApi.js";

// BUD-UI-03 — BUD-DES-04/04A/05/07/07A (BUD-CHG-001 v1.9 §11.4–§11.7A,
// §12.3); the Approver's Close budget entry routes to the closure screen
// (§11.18). Read-only; actions come from the server's available_actions.
const { route, go, epoch } = useRouteState("budget-funding");

const budgetIdParam = computed(() => route.value[1]);
const tab = computed(() => route.value[2] || "overview");
const detail = ref(null);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: detail.value?.budget?.code || budgetIdParam.value },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const guard = kentender_core.desk_page.createSequenceGuard();
const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(null);
const serverError = ref(false);
const actingError = ref(null);
const updating = ref(false);

const linesActive = ref(null);
const activity = ref(null);
const activityFilterLine = ref("");
const activityFilterEvent = ref("");
const history = ref(null);

async function loadDetail(opts) {
	const quiet = !!(opts && opts.quiet) && !!detail.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	notFound.value = false;
	forbidden.value = null;
	serverError.value = false;
	try {
		const data = await getBudgetDetail(budgetIdParam.value);
		if (!guard.isCurrent(token)) return;
		if (data && data.outcome === "FORBIDDEN") {
			detail.value = null;
			forbidden.value = data.forbidden;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			detail.value = null;
			notFound.value = true;
			return;
		}
		detail.value = data;
		linesActive.value = null;
		activity.value = null;
		history.value = null;
		await loadTab(tab.value);
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this budget"), text: "" };
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}
async function loadTab(t) {
	if (!detail.value) return;
	if (t === "lines" && !linesActive.value) linesActive.value = await getBudgetLinesActive(budgetIdParam.value);
	else if (t === "activity") activity.value = await getFundingActivity(budgetIdParam.value, activityFilterLine.value || undefined, activityFilterEvent.value || undefined);
	else if (t === "history" && !history.value) history.value = await getBudgetVersionHistory(detail.value.version.id);
}
watch(tab, (t) => loadTab(t));
watch([activityFilterLine, activityFilterEvent], () => tab.value === "activity" && loadTab("activity"));
function clearActivityFilters() {
	activityFilterLine.value = "";
	activityFilterEvent.value = "";
}
onMounted(loadDetail);
watch(budgetIdParam, (v, prev) => {
	if (v && v !== prev) {
		detail.value = null;
		loadDetail();
	}
});
let activations = 0;
onActivated(() => {
	if (activations++ === 0 || !detail.value) return;
	loadDetail({ quiet: true });
});
watch(epoch, () => detail.value && loadDetail({ quiet: true }));

function switchTab(t) {
	go(budgetIdParam.value, t === "overview" ? undefined : t);
}
function openLine(line) {
	go("line", line.code);
}
const actions = computed(() => detail.value?.available_actions || []);
const pending = computed(() => detail.value?.pending_version || null);
const isClosed = computed(() => detail.value?.version?.status === "Closed");
const currency = computed(() => detail.value?.budget?.currency || "KES");
const PENDING_LABELS = { continue_draft: __("Continue draft"), view_draft: __("View draft"), view_submission: __("View submission"), review: __("Review"), continue_update: __("Continue update"), correct_and_resubmit: __("Correct and resubmit"), view_version_readonly: __("View version (read-only)") };
function openPending() {
	const p = pending.value;
	if (p.action === "review") go("review", p.id);
	else go(budgetIdParam.value, "version", String(p.version_number), "edit");
}
async function updateAllocation() {
	if (updating.value) return;
	updating.value = true;
	actingError.value = null;
	try {
		const result = await createBudgetSuccessorVersion(budgetIdParam.value, { revision_type: "Transfer", idempotency_key: mintKey("successor") });
		if (result.ok) return go(budgetIdParam.value, "version", String(result.version.version_number), "edit");
		if (result.route) return go(...result.route.slice(1));
		actingError.value = Object.values(result.errors || {}).join(" ");
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		updating.value = false;
	}
}
const barCommitted = computed(() => (detail.value?.positions.approved ? Math.min(100, (detail.value.positions.committed / detail.value.positions.approved) * 100) : 0));
const barReserved = computed(() => (detail.value?.positions.approved ? Math.min(100 - barCommitted.value, (detail.value.positions.reserved / detail.value.positions.approved) * 100) : 0));
</script>

<template>
	<div class="kt-industry" data-testid="bud-detail" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell">
			<div v-if="loading" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 280px; height: 20px"></div></div>
			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-not-found"><h2>{{ __("This budget could not be found.") }}</h2></div>
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-forbidden"><h2>{{ __(forbidden.heading) }}</h2><p v-if="forbidden.text" class="kt-muted">{{ __(forbidden.text) }}</p></div>
			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-server-error"><h2>{{ __("This budget could not be loaded.") }}</h2><button type="button" class="kt-btn kt-btn-primary" @click="loadDetail()">{{ __("Try again") }}</button></div>

			<template v-else-if="detail">
				<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 16px" data-testid="budget-detail-header">
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 6px">{{ detail.budget.code }} · {{ __("VERSION {0}", [detail.version.version_number]) }}</div>
						<div style="display: flex; align-items: center; gap: 12px">
							<h1 style="margin: 0">{{ detail.budget.title }}</h1>
							<span class="kt-status" :class="isClosed ? 'is-critical' : 'is-live'" data-testid="budget-detail-status">{{ isClosed ? __("Closed") : __("Current") }}</span>
						</div>
					</div>
					<div style="display: flex; gap: 10px; flex: none; flex-wrap: wrap">
						<button v-if="pending" type="button" class="kt-btn kt-btn-secondary" data-testid="budget-detail-pending-action-btn" @click="openPending">{{ PENDING_LABELS[pending.action] || __("Open") }}</button>
						<button v-if="actions.includes('update_allocation')" type="button" class="kt-btn kt-btn-primary" :disabled="updating" data-testid="budget-detail-update-btn" @click="updateAllocation">{{ __("Update registered allocation") }}</button>
						<button v-if="actions.includes('close_budget')" type="button" class="kt-btn kt-btn-secondary" data-testid="budget-detail-close-btn" @click="go(budgetIdParam, 'close')">{{ __("Close budget") }}</button>
					</div>
				</div>
				<KtErrorBanner :message="actingError" style="margin-bottom: 12px" @dismiss="actingError = null" />

				<div class="kt-tabs" role="tablist">
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'overview'" data-testid="budget-detail-tab-overview" @click="switchTab('overview')" @keydown.enter="switchTab('overview')">{{ __("Overview") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'lines'" data-testid="budget-detail-tab-lines" @click="switchTab('lines')" @keydown.enter="switchTab('lines')">{{ __("Budget Lines") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'activity'" data-testid="budget-detail-tab-activity" @click="switchTab('activity')" @keydown.enter="switchTab('activity')">{{ __("Funding Activity") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'history'" data-testid="budget-detail-tab-history" @click="switchTab('history')" @keydown.enter="switchTab('history')">{{ __("History") }}</div>
				</div>

				<!-- Overview (BUD-DES-04/04A + closure notes §11.18) -->
				<template v-if="tab === 'overview'">
					<div v-if="isClosed" class="kt-card kt-blueprint" data-testid="budget-detail-closure">
						<h3 class="kt-card-title">{{ __("Closure") }}</h3>
						<div class="kt-grid-3" style="gap: 16px">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Closed by") }}</div><div style="font-size: 14px">{{ detail.closure.closed_by }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Closed") }}</div><div style="font-size: 14px">{{ detail.closure.closed_at_display }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Financial Year") }}</div><div style="font-size: 14px">{{ detail.budget.fiscal_year.label }}</div></div>
						</div>
						<p class="kt-muted" style="font-size: 13px; margin: 12px 0 0">{{ __("No new reservations, conversions or commitment increases. Existing commitments and history remain.") }}</p>
					</div>

					<div class="kt-kpi-row" style="margin-bottom: 8px" data-testid="budget-detail-position-cards">
						<div class="kt-kpi-card"><div class="kt-kpi-value">{{ formatKes(detail.positions.approved, currency) }}</div><div class="kt-kpi-sub">{{ __("Registered allocation") }}</div></div>
						<div class="kt-kpi-card"><div class="kt-kpi-value" :class="{ 'is-zero': !detail.positions.reserved }">{{ formatKes(detail.positions.reserved, currency) }}</div><div class="kt-kpi-sub">{{ __("Reserved for requisitions") }}</div></div>
						<div class="kt-kpi-card"><div class="kt-kpi-value" :class="{ 'is-zero': !detail.positions.committed }">{{ formatKes(detail.positions.committed, currency) }}</div><div class="kt-kpi-sub">{{ __("Committed to contracts") }}</div></div>
						<div class="kt-kpi-card" :class="detail.positions.available > 0 ? 'is-live' : 'is-critical'"><div class="kt-kpi-value">{{ formatKes(detail.positions.available, currency) }}</div><div class="kt-kpi-sub">{{ __("Available to reserve") }}</div></div>
					</div>
					<div class="kt-bar" style="margin-bottom: 8px"><i class="kt-bar-committed" :style="{ width: barCommitted + '%' }"></i><i class="kt-bar-reserved" :style="{ width: barReserved + '%' }"></i></div>
					<p class="kt-muted" style="font-size: 12px; margin: 0 0 20px" data-testid="budget-detail-as-at">{{ __("Funding position as at {0}", [detail.positions_as_at_display]) }}</p>

					<div class="kt-grid-2" style="margin-bottom: 16px">
						<div class="kt-card kt-blueprint" style="margin: 0">
							<h3 class="kt-card-title">{{ __("Budget context") }}</h3>
							<div style="display: grid; gap: 12px">
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Financial Year") }}</div><div style="font-size: 14px">{{ detail.budget.fiscal_year.label }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Currency") }}</div><div style="font-size: 14px">{{ currency }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Current version") }}</div><div style="font-size: 14px">{{ __("Version {0}", [detail.version.version_number]) }}</div></div>
							</div>
						</div>
						<div class="kt-card kt-blueprint" style="margin: 0">
							<h3 class="kt-card-title">{{ __("External approval") }}</h3>
							<div style="display: grid; gap: 12px">
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval reference") }}</div><div style="font-size: 14px">{{ detail.version.approval_reference }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval date") }}</div><div style="font-size: 14px">{{ detail.version.approval_date_display }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approved allocation") }}</div><div style="font-size: 14px">{{ formatKes(detail.version.authorised_total, currency) }}</div></div>
								<div>
									<div class="kt-label" style="margin-bottom: 3px">{{ __("Approval document") }}</div>
									<a v-if="detail.document.url" :href="detail.document.url" target="_blank" rel="noopener" style="font-size: 13px" data-testid="budget-detail-document">{{ detail.document.name }}</a>
									<div v-else style="font-size: 14px">—</div>
								</div>
							</div>
						</div>
					</div>

					<div class="kt-card kt-blueprint">
						<h3 class="kt-card-title">{{ __("Activation") }}</h3>
						<div class="kt-grid-3" style="gap: 16px">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Submitted by") }}</div><div style="font-size: 14px">{{ detail.activation.submitted_by || "—" }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approved and activated by") }}</div><div style="font-size: 14px">{{ detail.activation.decided_by || "—" }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Activated") }}</div><div style="font-size: 14px">{{ detail.activation.decided_at || "—" }}</div></div>
						</div>
					</div>
					<div v-if="actions.includes('close_budget') && detail.closure.fy_end_date_display" class="kt-notice is-info" style="margin-top: 16px" data-testid="budget-detail-close-note">
						<div class="kt-notice-body">{{ __("This budget can be closed only after {0}.", [detail.closure.fy_end_date_display]) }} <a href="#" @click.prevent="go(budgetIdParam, 'close')">{{ __("Check closure") }}</a></div>
					</div>
				</template>

				<!-- Budget Lines (BUD-DES-05) -->
				<template v-else-if="tab === 'lines'">
					<div v-if="!linesActive" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<div v-else class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto">
						<table class="kt-table" data-testid="budget-detail-lines-table">
							<thead>
								<tr>
									<th>{{ __("Budget Line") }}</th>
									<th>{{ __("Available to") }}</th>
									<th>{{ __("Funding source") }}</th>
									<th class="is-num">{{ __("Registered allocation") }}</th>
									<th class="is-num">{{ __("Reserved for requisitions") }}</th>
									<th class="is-num">{{ __("Committed to contracts") }}</th>
									<th class="is-num">{{ __("Available to reserve") }}</th>
									<th></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="line in linesActive.rows" :key="line.budget_line">
									<td><div>{{ line.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ line.code }}</div></td>
									<td>{{ line.owner_org_unit }}</td>
									<td>{{ line.funding_source }}</td>
									<td class="is-num">{{ formatKes(line.approved, currency) }}</td>
									<td class="is-num" :class="{ 'is-zero': !line.reserved }">{{ formatKes(line.reserved, currency) }}</td>
									<td class="is-num" :class="{ 'is-zero': !line.committed }">{{ formatKes(line.committed, currency) }}</td>
									<td class="is-num">{{ formatKes(line.available, currency) }}</td>
									<td><a href="#" data-testid="budget-detail-line-view-link" @click.prevent="openLine(line)">{{ __("View") }}</a></td>
								</tr>
								<tr style="font-weight: 600">
									<td>{{ __("Total") }}</td><td>—</td><td>—</td>
									<td class="is-num">{{ formatKes(linesActive.total.approved, currency) }}</td>
									<td class="is-num" :class="{ 'is-zero': !linesActive.total.reserved }">{{ formatKes(linesActive.total.reserved, currency) }}</td>
									<td class="is-num" :class="{ 'is-zero': !linesActive.total.committed }">{{ formatKes(linesActive.total.committed, currency) }}</td>
									<td class="is-num">{{ formatKes(linesActive.total.available, currency) }}</td><td></td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>

				<!-- Funding Activity (BUD-DES-07) -->
				<template v-else-if="tab === 'activity'">
					<div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
						<select v-model="activityFilterLine" class="kt-input" style="width: 220px" data-testid="budget-detail-activity-filter-line">
							<option value="">{{ __("All Budget Lines") }}</option>
							<option v-for="l in activity?.budget_lines || []" :key="l.id" :value="l.id">{{ l.title }}</option>
						</select>
						<select v-model="activityFilterEvent" class="kt-input" style="width: 220px" data-testid="budget-detail-activity-filter-event">
							<option value="">{{ __("All funding events") }}</option>
							<option v-for="opt in activity?.event_type_options || []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
						</select>
					</div>
					<div v-if="!activity" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<div v-else-if="!activity.rows.length" class="kt-notice is-info" data-testid="budget-detail-activity-empty">
						<div class="kt-notice-body">
							<template v-if="activityFilterLine || activityFilterEvent">{{ __("No funding events match these filters.") }} <a href="#" data-testid="budget-detail-activity-clear-filters" @click.prevent="clearActivityFilters">{{ __("Clear filters") }}</a></template>
							<template v-else>{{ __("No funding activity has been recorded for this budget.") }}</template>
						</div>
					</div>
					<div v-else class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto">
						<table class="kt-table" data-testid="budget-detail-activity-table">
							<thead><tr><th>{{ __("Date and time") }}</th><th>{{ __("Event") }}</th><th>{{ __("Budget Line") }}</th><th>{{ __("Requisition / reservation") }}</th><th class="is-num">{{ __("Amount") }}</th><th>{{ __("Initiating actor") }}</th></tr></thead>
							<tbody>
								<tr v-for="row in activity.rows" :key="row.id">
									<td style="white-space: nowrap">{{ row.event_at_display }}</td>
									<td>{{ row.event_type_label }}</td>
									<td>{{ row.budget_line_code }}</td>
									<td>{{ row.downstream_reference }}</td>
									<td class="is-num">{{ row.amount === null ? "—" : formatKes(row.amount, row.currency || currency) }}</td>
									<td>{{ row.initiating_actor }}</td>
								</tr>
							</tbody>
						</table>
						<p class="kt-muted" style="font-size: 13px; padding: 12px 16px; margin: 0">{{ activity.summary_label }}</p>
					</div>
				</template>

				<!-- History (BUD-DES-07A) -->
				<template v-else-if="tab === 'history'">
					<div v-if="!history" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<div v-else class="kt-card kt-blueprint" data-testid="budget-detail-history-table">
						<h3 class="kt-card-title">{{ __("Version history") }}</h3>
						<div class="kt-timeline">
							<div v-for="(row, i) in history.rows" :key="row.id" class="kt-timeline-row">
								<div class="kt-timeline-dot-col"><i class="kt-timeline-dot is-live"></i><i v-if="i < history.rows.length - 1" class="kt-timeline-line"></i></div>
								<div class="kt-timeline-item"><div class="kt-timeline-item-title">{{ row.event_type_label }}</div><div class="kt-timeline-item-meta">{{ row.event_at_display }} · {{ row.actor }}</div></div>
							</div>
						</div>
					</div>
				</template>
			</template>
		</div>
	</div>
</template>
