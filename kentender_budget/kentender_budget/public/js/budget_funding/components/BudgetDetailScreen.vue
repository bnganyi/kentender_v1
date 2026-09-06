<script setup>
import { ref, computed, onActivated, onMounted, watch } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import {
	getBudgetDetail,
	getBudgetLinesActive,
	getFundingActivity,
	getBudgetVersionHistory,
	createBudgetSuccessorVersion,
} from "../data/budgetApi.js";

const { route, go } = useRouteState("budget-funding");

const budgetIdParam = computed(() => route.value[1]);
const tab = computed(() => route.value[2] || "overview");

const detail = ref(null);

// usePageRail's watch() reads railTrail.value synchronously the moment it's
// called (see BudgetVersionEditorScreen.vue's own note / the
// vue-desk-bundle-globalproperties-gotcha memory) — declare everything its
// callback touches (detail, budgetIdParam) before the usePageRail() call.
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: detail.value?.budget?.code || budgetIdParam.value },
]);
const railEl = ref(null);
// BUD-CHG-001 v1.3 Phase 4/7 — one site is one Procuring Entity: no global
// PE switcher on this rail any more.
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const serverError = ref(false);
const creatingRevision = ref(false);

const linesActive = ref(null);
const linesLoaded = ref(false);
const activity = ref(null);
const activityLoaded = ref(false);
const activityFilterLine = ref("");
const activityFilterEvent = ref("");
const history = ref(null);
const historyLoaded = ref(false);

async function loadDetail(opts) {
	if (!(opts && opts.quiet === true)) loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	serverError.value = false;
	linesLoaded.value = false;
	activityLoaded.value = false;
	historyLoaded.value = false;
	try {
		detail.value = await getBudgetDetail(budgetIdParam.value);
		if (tab.value === "lines") await loadLines();
		else if (tab.value === "activity") await loadActivity();
		else if (tab.value === "history") await loadHistory();
	} catch (e) {
		if (e.httpStatus === 403) forbidden.value = true;
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		loading.value = false;
	}
}

async function loadLines() {
	linesActive.value = await getBudgetLinesActive(budgetIdParam.value);
	linesLoaded.value = true;
}

async function loadActivity() {
	activity.value = await getFundingActivity(budgetIdParam.value, activityFilterLine.value || undefined, activityFilterEvent.value || undefined);
	activityLoaded.value = true;
}

async function loadHistory() {
	history.value = await getBudgetVersionHistory(detail.value.version.id);
	historyLoaded.value = true;
}

watch(tab, (t) => {
	// A direct load landing on a non-Overview tab is already covered by
	// loadDetail() itself; this only fires on a later client-side tab switch.
	if (t === "lines" && !linesLoaded.value) loadLines();
	else if (t === "activity" && !activityLoaded.value) loadActivity();
	else if (t === "history" && !historyLoaded.value) loadHistory();
});

watch([activityFilterLine, activityFilterEvent], () => {
	if (tab.value === "activity") loadActivity();
});

onMounted(loadDetail);
watch(budgetIdParam, (v, prev) => {
	if (v && v !== prev) loadDetail();
});
// KeepAlive brings this instance back with the record still on screen:
// revalidate in place rather than re-showing the skeleton.
let activations = 0;
onActivated(() => {
	if (activations++ === 0 || !detail.value) return;
	loadDetail({ quiet: true });
});

function switchTab(t) {
	go(budgetIdParam.value, t);
}

function approvalDocumentName(url) {
	return (url || "").split("/").pop();
}

function openLine(line) {
	go("line", line.code);
}

async function createRevision() {
	creatingRevision.value = true;
	try {
		// A successor Budget Version requires a revision_type from its first
		// insert (Budget Version.validate()); the editor's own Overview tab
		// defaults to the same value and lets the Officer change it before
		// Save/Submit (BUD-DES-14) — this is just the initial value.
		const result = await createBudgetSuccessorVersion(budgetIdParam.value, { revision_type: "Transfer" });
		go(budgetIdParam.value, "version", result.version.version_number, "edit");
	} catch (e) {
		frappe.show_alert({ message: e.message || String(e), indicator: "red" });
	} finally {
		creatingRevision.value = false;
	}
}
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

			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-not-found">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This Budget could not be found.") }}</h2>
			</div>

			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-forbidden">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("You do not have access to this Budget.") }}</h2>
			</div>

			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-server-error">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This Budget could not be loaded.") }}</h2>
				<button type="button" class="kt-btn kt-btn-primary" @click="loadDetail">{{ __("Try again") }}</button>
			</div>

			<template v-else-if="detail">
				<!-- BUD-DES-04/04A page content header, reused verbatim across all 4 tabs -->
				<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px" data-testid="budget-detail-header">
					<div>
						<div class="kt-eyebrow" style="margin-bottom: 8px">{{ detail.budget.code }} · {{ __("VERSION {0}", [detail.version.version_number]) }}</div>
						<div style="display: flex; align-items: center; gap: 12px">
							<h1 style="margin: 0">{{ detail.budget.title }}</h1>
							<span class="kt-status is-live">{{ detail.version.status }}</span>
						</div>
					</div>
					<button
						v-if="detail.can_create_revision"
						type="button"
						class="kt-btn kt-btn-primary"
						style="flex: none; margin-top: 4px"
						:disabled="creatingRevision"
						@click="createRevision"
						data-testid="budget-detail-create-revision-btn"
					>
						{{ __("Create revision") }}
					</button>
				</div>

				<div class="kt-tabs">
					<div class="kt-tab" :aria-selected="tab === 'overview'" @click="switchTab('overview')" data-testid="budget-detail-tab-overview">{{ __("Overview") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'lines'" @click="switchTab('lines')" data-testid="budget-detail-tab-lines">{{ __("Budget Lines") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'activity'" @click="switchTab('activity')" data-testid="budget-detail-tab-activity">{{ __("Funding Activity") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'history'" @click="switchTab('history')" data-testid="budget-detail-tab-history">{{ __("History") }}</div>
				</div>

				<!-- BUD-DES-04/04A Overview -->
				<template v-if="tab === 'overview'">
					<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px" data-testid="budget-detail-position-cards">
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-eyebrow">{{ __("Approved") }}</div>
							<div class="kt-figure" style="font-size: 26px">{{ formatKes(detail.positions.approved, detail.budget.currency) }}</div>
						</div>
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-eyebrow">{{ __("Reserved") }}</div>
							<div class="kt-figure is-attention" style="font-size: 26px">{{ formatKes(detail.positions.reserved, detail.budget.currency) }}</div>
						</div>
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-eyebrow">{{ __("Committed") }}</div>
							<div class="kt-figure" style="font-size: 26px; color: #1d4ed8">{{ formatKes(detail.positions.committed, detail.budget.currency) }}</div>
						</div>
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-eyebrow">{{ __("Available") }}</div>
							<div class="kt-figure is-live" style="font-size: 26px">{{ formatKes(detail.positions.available, detail.budget.currency) }}</div>
						</div>
					</div>

					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px">
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Budget context") }}</div>
							<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px">
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Financial Year") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.budget.fiscal_year.label }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Currency") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.budget.currency }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Active version") }}</div><div style="font-size: 14px; font-weight: 500">{{ __("Version {0}", [detail.version.version_number]) }}</div></div>
							</div>
						</div>

						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("External approval") }}</div>
							<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px">
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval reference") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.version.approval_reference }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval date") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.version.approval_date_display }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Authorised total") }}</div><div style="font-size: 14px; font-weight: 500">{{ formatKes(detail.version.authorised_total, detail.budget.currency) }}</div></div>
								<div>
									<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval document") }}</div>
									<a v-if="detail.approval_document" :href="detail.approval_document" target="_blank" rel="noopener" style="font-size: 14px; font-weight: 500; text-decoration: underline">{{ approvalDocumentName(detail.approval_document) }}</a>
									<div v-else style="font-size: 14px; font-weight: 500">—</div>
								</div>
							</div>
						</div>
					</div>

					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("Activation") }}</div>
						<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px">
							<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Submitted by") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.activation.submitted_by || "—" }}</div></div>
							<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approved and activated by") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.activation.decided_by || "—" }}</div></div>
							<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Activated") }}</div><div style="font-size: 14px; font-weight: 500">{{ detail.activation.decided_at || "—" }}</div></div>
						</div>
					</div>
				</template>

				<!-- BUD-DES-05 Budget Lines -->
				<template v-else-if="tab === 'lines'">
					<div v-if="!linesLoaded" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 240px; height: 16px"></div>
					</div>
					<div v-else class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" data-testid="budget-detail-lines-table">
							<thead>
								<tr>
									<th>{{ __("Budget Line") }}</th>
									<th>{{ __("Owner scope") }}</th>
									<th>{{ __("Funding source") }}</th>
									<th style="text-align: right">{{ __("Approved") }}</th>
									<th style="text-align: right">{{ __("Reserved") }}</th>
									<th style="text-align: right">{{ __("Committed") }}</th>
									<th style="text-align: right">{{ __("Available") }}</th>
									<th></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="line in linesActive.rows" :key="line.budget_line">
									<td>
										<div>{{ line.title }}</div>
										<div class="kt-muted" style="font-size: 12px; margin-top: 2px">{{ line.code }}</div>
									</td>
									<td>{{ line.owner_org_unit }}</td>
									<td>{{ line.funding_source }}</td>
									<td style="text-align: right">{{ line.approved_display }}</td>
									<td style="text-align: right">{{ line.reserved_display }}</td>
									<td style="text-align: right">{{ line.committed_display }}</td>
									<td style="text-align: right">{{ line.available_display }}</td>
									<td style="text-align: right">
										<a href="#" style="font-size: 13px; font-weight: 500; text-decoration: none" @click.prevent="openLine(line)" data-testid="budget-detail-line-view-link">{{ __("View") }}</a>
									</td>
								</tr>
								<tr style="font-weight: 600">
									<td>{{ __("Total") }}</td>
									<td>—</td>
									<td>—</td>
									<td style="text-align: right">{{ formatKes(linesActive.total.approved, detail.budget.currency) }}</td>
									<td style="text-align: right">{{ formatKes(linesActive.total.reserved, detail.budget.currency) }}</td>
									<td style="text-align: right">{{ formatKes(linesActive.total.committed, detail.budget.currency) }}</td>
									<td style="text-align: right">{{ formatKes(linesActive.total.available, detail.budget.currency) }}</td>
									<td></td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>

				<!-- BUD-DES-07 Funding Activity -->
				<template v-else-if="tab === 'activity'">
					<div style="display: flex; gap: 12px; margin-bottom: 16px">
						<select v-model="activityFilterLine" class="kt-input" style="width: 220px" data-testid="budget-detail-activity-filter-line">
							<option value="">{{ __("All Budget Lines") }}</option>
							<option v-for="l in activity?.budget_lines || []" :key="l.id" :value="l.id">{{ l.title }}</option>
						</select>
						<select v-model="activityFilterEvent" class="kt-input" style="width: 220px" data-testid="budget-detail-activity-filter-event">
							<option value="">{{ __("All funding events") }}</option>
							<option v-for="opt in activity?.event_type_options || []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
						</select>
					</div>

					<div v-if="!activityLoaded" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 240px; height: 16px"></div>
					</div>
					<div v-else-if="!activity.rows.length" class="kt-card kt-blueprint kt-empty" data-testid="budget-detail-activity-empty">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<h2>{{ __("No funding activity has been recorded for this budget.") }}</h2>
					</div>
					<div v-else class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" style="margin-bottom: 12px" data-testid="budget-detail-activity-table">
							<thead>
								<tr>
									<th>{{ __("Date and time") }}</th>
									<th>{{ __("Event") }}</th>
									<th>{{ __("Budget Line") }}</th>
									<th>{{ __("Downstream reference") }}</th>
									<th style="text-align: right">{{ __("Amount") }}</th>
									<th>{{ __("Actor") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in activity.rows" :key="row.id">
									<td style="white-space: nowrap">{{ row.event_at_display }}</td>
									<td>{{ row.event_type_label }}</td>
									<td>{{ row.budget_line_code }}</td>
									<td>{{ row.downstream_reference }}</td>
									<td style="text-align: right">{{ formatKes(row.amount, row.currency || detail.budget.currency) }}</td>
									<td>{{ row.actor }}</td>
								</tr>
							</tbody>
						</table>
						<div class="kt-muted" style="font-size: 13px">{{ activity.summary_label }}</div>
					</div>
				</template>

				<!-- BUD-DES-07A History -->
				<template v-else-if="tab === 'history'">
					<div v-if="!historyLoaded" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 240px; height: 16px"></div>
					</div>
					<div v-else class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" data-testid="budget-detail-history-table">
							<thead>
								<tr>
									<th>{{ __("Date and time") }}</th>
									<th>{{ __("Event") }}</th>
									<th>{{ __("Actor") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="row in history.rows" :key="row.id">
									<td style="white-space: nowrap">{{ row.event_at_display }}</td>
									<td>{{ row.event_type_label }}</td>
									<td>{{ row.actor }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>
			</template>
		</div>
	</div>
</template>
