<script setup>
import { ref, computed, watch, onActivated, onMounted } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import ConfirmDialog from "../../budget_shared/components/ConfirmDialog.vue";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import {
	getBudgetApprovalTask,
	getBudgetApprovalTaskLines,
	getBudgetApprovalTaskChanges,
	getBudgetVersionHistory,
	returnBudgetVersion,
	approveBudgetVersion,
} from "../data/budgetApi.js";

const { route, go } = useRouteState("budget-funding");

const versionIdParam = computed(() => route.value[2]);
const tab = computed(() => route.value[3] || "overview");

const task = ref(null);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: __("Approval tasks") },
	{ label: task.value?.budget?.code ? `${task.value.budget.code} · V${task.value.version.version_number}` : versionIdParam.value },
]);
const railEl = ref(null);
// BUD-CHG-001 v1.3 Phase 4/7 — one site is one Procuring Entity: no global
// PE switcher on this rail any more.
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const forbiddenCopy = ref(null);
const serverError = ref(false);
const actingError = ref(null);
const acting = ref(false);

const linesTask = ref(null);
const linesLoaded = ref(false);
const changes = ref(null);
const changesLoaded = ref(false);
const history = ref(null);
const historyLoaded = ref(false);

const showReturnDialog = ref(false);
const showApproveConfirm = ref(false);

// `quiet` refreshes in place — used after Approve/Return, which redisplay
// the same task's (now updated) state rather than navigating away.
async function load(opts) {
	if (!versionIdParam.value) return;
	const quiet = !!(opts && opts.quiet === true);
	if (!quiet) loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	serverError.value = false;
	linesLoaded.value = false;
	changesLoaded.value = false;
	historyLoaded.value = false;
	try {
		const data = await getBudgetApprovalTask(versionIdParam.value);
		// KT-STD-001 §3A.2 / §12.5 — a read-only actor is denied as data
		// (inline panel), never shown the task with its controls removed.
		if (data && data.outcome === "FORBIDDEN") {
			task.value = null;
			forbidden.value = true;
			forbiddenCopy.value = data.forbidden || null;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			task.value = null;
			notFound.value = true;
			return;
		}
		task.value = data;
		if (tab.value === "lines") await loadLines();
		else if (tab.value === "changes") await loadChanges();
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
	linesTask.value = await getBudgetApprovalTaskLines(versionIdParam.value);
	linesLoaded.value = true;
}
async function loadChanges() {
	changes.value = await getBudgetApprovalTaskChanges(versionIdParam.value);
	changesLoaded.value = true;
}
async function loadHistory() {
	history.value = await getBudgetVersionHistory(versionIdParam.value);
	historyLoaded.value = true;
}

watch(tab, (t) => {
	if (t === "lines" && !linesLoaded.value) loadLines();
	else if (t === "changes" && !changesLoaded.value) loadChanges();
	else if (t === "history" && !historyLoaded.value) loadHistory();
});

onMounted(load);
watch(versionIdParam, (v, prev) => {
	if (v && v !== prev) load();
});
// KeepAlive brings this instance back with the task still on screen:
// revalidate in place rather than re-showing the skeleton.
let activations = 0;
onActivated(() => {
	if (activations++ === 0 || !task.value) return;
	load({ quiet: true });
});

function switchTab(t) {
	go("review", versionIdParam.value, t);
}

async function submitReturn(reason) {
	acting.value = true;
	actingError.value = null;
	try {
		const result = await returnBudgetVersion(versionIdParam.value, reason, task.value.version.modified);
		if (!result.ok) {
			actingError.value = Object.values(result.errors || {}).join(" ") || __("Could not return.");
			return;
		}
		frappe.show_alert({ message: __("Returned"), indicator: "orange" });
		showReturnDialog.value = false;
		await load({ quiet: true });
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

async function submitApprove() {
	acting.value = true;
	actingError.value = null;
	showApproveConfirm.value = false;
	try {
		const result = await approveBudgetVersion(versionIdParam.value, task.value.version.modified);
		if (!result.ok) {
			actingError.value = (result.blockers || []).map((b) => b.message).join(" ") || __("Not ready to approve.");
			return;
		}
		frappe.show_alert({ message: __("Approved and activated"), indicator: "green" });
		await load({ quiet: true });
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div class="kt-shell" style="padding-bottom: 96px">
			<template v-if="loading">
				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-skel" style="width: 280px; height: 20px"></div>
				</div>
			</template>

			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-not-found">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This approval task could not be found.") }}</h2>
			</div>

			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-forbidden">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ forbiddenCopy ? __(forbiddenCopy.heading) : __("You do not have access to this approval task.") }}</h2>
				<p v-if="forbiddenCopy" class="kt-muted">{{ __(forbiddenCopy.text) }}</p>
			</div>

			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-server-error">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("This approval task could not be loaded.") }}</h2>
				<button type="button" class="kt-btn kt-btn-primary" @click="load">{{ __("Try again") }}</button>
			</div>

			<template v-else-if="task">
				<div style="margin-bottom: 16px" data-testid="bud-task-header">
					<div class="kt-eyebrow" style="margin-bottom: 8px">{{ task.budget.code }} · {{ __("VERSION {0}", [task.version.version_number]) }}</div>
					<div style="display: flex; align-items: center; gap: 12px">
						<h1 style="margin: 0">{{ __("Approve budget version") }}</h1>
						<span class="kt-status is-pending">{{ task.version.status }}</span>
					</div>
				</div>

				<p v-if="actingError" style="color: oklch(0.45 0.13 28)" data-testid="bud-task-error">{{ actingError }}</p>

				<div class="kt-tabs">
					<div class="kt-tab" :aria-selected="tab === 'overview'" @click="switchTab('overview')" data-testid="bud-task-tab-overview">{{ __("Overview") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'lines'" @click="switchTab('lines')" data-testid="bud-task-tab-lines">{{ __("Budget Lines") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'changes'" @click="switchTab('changes')" data-testid="bud-task-tab-changes">{{ __("Changes") }}</div>
					<div class="kt-tab" :aria-selected="tab === 'history'" @click="switchTab('history')" data-testid="bud-task-tab-history">{{ __("History") }}</div>
				</div>

				<!-- BUD-DES-08/13 Overview -->
				<template v-if="tab === 'overview'">
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px">
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Version identity") }}</div>
							<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px">
								<div style="grid-column: 1 / -1"><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Procurement budget") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.budget.title }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Financial Year") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.budget.fiscal_year.label }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Currency") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.budget.currency }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Submitted version") }}</div><div style="font-size: 14px; font-weight: 500">{{ __("Version {0}", [task.version.version_number]) }}</div></div>
								<template v-if="task.based_on">
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Based on") }}</div><div style="font-size: 14px; font-weight: 500">{{ __("Active Version {0}", [task.based_on.version_number]) }}</div></div>
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Revision type") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.revision_type }}</div></div>
								</template>
							</div>
						</div>

						<div style="display: flex; flex-direction: column; gap: 16px">
							<div class="kt-card kt-blueprint">
								<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
								<div class="kt-card-title">{{ __("External approval") }}</div>
								<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px">
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval reference") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.version.approval_reference }}</div></div>
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval date") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.version.approval_date_display }}</div></div>
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Authorised total") }}</div><div style="font-size: 14px; font-weight: 500">{{ formatKes(task.version.authorised_total, task.budget.currency) }}</div></div>
									<div>
										<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval document") }}</div>
										<a v-if="task.approval_document" :href="task.approval_document" target="_blank" rel="noopener" style="font-size: 14px; font-weight: 500; text-decoration: underline">{{ task.approval_document.split("/").pop() }}</a>
										<div v-else style="font-size: 14px; font-weight: 500">—</div>
									</div>
								</div>
							</div>

							<div class="kt-card kt-blueprint">
								<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
								<div class="kt-card-title">{{ __("Submission authority") }}</div>
								<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px">
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Submitted by") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.submission.submitted_by || "—" }}</div></div>
									<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Submitted") }}</div><div style="font-size: 14px; font-weight: 500">{{ task.submission.submitted_at_display || "—" }}</div></div>
								</div>
							</div>
						</div>
					</div>

					<div class="kt-card kt-blueprint" data-testid="bud-task-readiness">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("Readiness") }}</div>
						<div :style="{ display: 'grid', gridTemplateColumns: `repeat(${task.readiness.length}, 1fr)`, gap: '16px' }">
							<div v-for="c in task.readiness" :key="c.key" style="display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 12px 14px; border: 1px solid var(--kt-color-divider)">
								<div style="font-size: 13px; font-weight: 500">{{ c.label }}</div>
								<span class="kt-status" :class="c.result === 'Ready' ? 'is-live' : 'is-attention'">{{ c.result === "Ready" ? __("Ready") : __("Needs attention") }}</span>
							</div>
						</div>
					</div>
				</template>

				<!-- BUD-DES-09/13 Budget Lines -->
				<template v-else-if="tab === 'lines'">
					<div v-if="!linesLoaded" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 240px; height: 16px"></div>
					</div>
					<div v-else class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<table class="kt-table" data-testid="bud-task-lines-table">
							<thead>
								<tr>
									<th>{{ __("Budget Line") }}</th>
									<th>{{ __("Owner scope") }}</th>
									<th>{{ __("Funding source") }}</th>
									<!-- BUD-DES-09 (successor) says "Proposed amount"; BUD-DES-13's Budget
									     Lines duplicate (initial baseline, no predecessor) says "Submitted
									     amount" instead — same column, worded for whether there is a prior
									     Active version to propose a change against. -->
									<th style="text-align: right">{{ linesTask.is_successor ? __("Proposed amount") : __("Submitted amount") }}</th>
									<th v-if="linesTask.is_successor" style="text-align: right">{{ __("Current floor") }}</th>
									<th v-if="linesTask.is_successor" style="text-align: right">{{ __("Headroom") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="line in linesTask.rows" :key="line.budget_line">
									<td>
										<div>{{ line.title }}</div>
										<div class="kt-muted" style="font-size: 12px; margin-top: 2px">{{ line.budget_line_code }}</div>
									</td>
									<td>{{ line.owner_org_unit }}</td>
									<td>{{ line.funding_source }}</td>
									<td style="text-align: right">{{ formatKes(line.amount, task.budget.currency) }}</td>
									<td v-if="linesTask.is_successor" style="text-align: right">{{ formatKes(line.floor, task.budget.currency) }}</td>
									<td v-if="linesTask.is_successor" style="text-align: right">{{ formatKes(line.headroom, task.budget.currency) }}</td>
								</tr>
								<tr style="font-weight: 600">
									<td>{{ __("Total") }}</td>
									<td>—</td>
									<td>—</td>
									<td style="text-align: right">{{ formatKes(linesTask.total_amount, task.budget.currency) }}</td>
									<td v-if="linesTask.is_successor" style="text-align: right">{{ formatKes(linesTask.total_floor, task.budget.currency) }}</td>
									<td v-if="linesTask.is_successor" style="text-align: right">{{ formatKes(linesTask.total_headroom, task.budget.currency) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>

				<!-- BUD-DES-10/13 Changes -->
				<template v-else-if="tab === 'changes'">
					<template v-if="!changesLoaded">
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-skel" style="width: 240px; height: 16px"></div>
						</div>
					</template>
					<template v-else-if="changes.is_initial_baseline">
						<div class="kt-card kt-blueprint" data-testid="bud-task-changes-baseline">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Initial baseline") }}</div>
							<p class="kt-muted" style="max-width: 70ch; margin-bottom: 16px">{{ __("Version 1 has no predecessor. Review the complete submitted Budget Lines.") }}</p>
							<table class="kt-table">
								<thead>
									<tr>
										<th>{{ __("Budget Line") }}</th>
										<th style="text-align: right">{{ __("Submitted Version {0}", [task.version.version_number]) }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in changes.rows" :key="row.budget_line">
										<td>
											<div>{{ row.title }}</div>
											<div class="kt-muted" style="font-size: 12px; margin-top: 2px">{{ row.budget_line_code }}</div>
										</td>
										<td style="text-align: right">{{ formatKes(row.submitted_amount, task.budget.currency) }}</td>
									</tr>
									<tr style="font-weight: 600">
										<td>{{ __("Total") }}</td>
										<td style="text-align: right">{{ formatKes(changes.total_submitted, task.budget.currency) }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</template>
					<template v-else>
						<div class="kt-card kt-blueprint" style="margin-bottom: 16px" data-testid="bud-task-changes-table">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Changes from Active Version {0}", [task.based_on.version_number]) }}</div>
							<table class="kt-table">
								<thead>
									<tr>
										<th>{{ __("Budget Line") }}</th>
										<th style="text-align: right">{{ __("Active Version {0}", [task.based_on.version_number]) }}</th>
										<th style="text-align: right">{{ __("Submitted Version {0}", [task.version.version_number]) }}</th>
										<th style="text-align: right">{{ __("Change") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in changes.rows" :key="row.budget_line">
										<td>
											<div>{{ row.title }}</div>
											<div class="kt-muted" style="font-size: 12px; margin-top: 2px">{{ row.budget_line_code }}</div>
										</td>
										<td style="text-align: right">{{ formatKes(row.active_amount, task.budget.currency) }}</td>
										<td style="text-align: right">{{ formatKes(row.submitted_amount, task.budget.currency) }}</td>
										<td style="text-align: right" :style="{ color: row.change < 0 ? '#b91c1c' : row.change > 0 ? '#047857' : undefined, fontWeight: 500 }">
											{{ row.change === 0 ? formatKes(0, task.budget.currency) : (row.change > 0 ? "+ " : "− ") + formatKes(Math.abs(row.change), task.budget.currency) }}
										</td>
									</tr>
									<tr style="font-weight: 600">
										<td>{{ __("Total") }}</td>
										<td style="text-align: right">{{ formatKes(changes.total_active, task.budget.currency) }}</td>
										<td style="text-align: right">{{ formatKes(changes.total_submitted, task.budget.currency) }}</td>
										<td style="text-align: right">{{ formatKes(changes.total_change, task.budget.currency) }}</td>
									</tr>
								</tbody>
							</table>
						</div>

						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Funding impact") }}</div>
							<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px">
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Active reservations affected") }}</div><div style="font-size: 14px; font-weight: 500">{{ changes.impact.active_reservations_affected }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Active commitments affected") }}</div><div style="font-size: 14px; font-weight: 500">{{ changes.impact.active_commitments_affected }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Floor breaches") }}</div><div style="font-size: 14px; font-weight: 500">{{ changes.impact.floor_breaches }}</div></div>
								<div><div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Transfer difference") }}</div><div style="font-size: 14px; font-weight: 500">{{ formatKes(changes.impact.transfer_difference, task.budget.currency) }}</div></div>
							</div>
						</div>
					</template>
				</template>

				<!-- BUD-DES-11/13 History -->
				<template v-else-if="tab === 'history'">
					<div v-if="!historyLoaded" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 240px; height: 16px"></div>
					</div>
					<div v-else class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("Version history") }}</div>
						<table class="kt-table" data-testid="bud-task-history-table">
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

		<div v-if="task && (task.capabilities.can_return || task.capabilities.can_approve)" class="kt-sticky-footer">
			<button v-if="task.capabilities.can_return" type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="acting" @click="showReturnDialog = true" data-testid="bud-task-return-btn">
				{{ __("Return") }}
			</button>
			<button v-if="task.capabilities.can_approve" type="button" class="kt-btn kt-btn-primary" :disabled="acting" @click="showApproveConfirm = true" data-testid="bud-task-approve-btn">
				{{ __("Approve") }}
			</button>
		</div>

		<ConfirmDialog
			:open="showApproveConfirm"
			:title="__('Approve this version?')"
			:message="__('The version will move to Active. The previous Active version, if any, will be superseded.')"
			:confirm-label="__('Approve')"
			@confirm="submitApprove"
			@cancel="showApproveConfirm = false"
		/>
		<ConfirmDialog
			:open="showReturnDialog"
			:title="__('Return this version?')"
			require-reason
			:reason-placeholder="__('Reason (10-500 characters)')"
			:reason-min-length="10"
			:reason-max-length="500"
			:confirm-label="__('Return')"
			@confirm="submitReturn"
			@cancel="showReturnDialog = false"
		/>
	</div>
</template>
