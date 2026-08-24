<script setup>
import { ref, computed, watch } from "vue";
import { useRouteState } from "../strategy_shared/composables/useRouteState.js";
import StructureTree from "../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../strategy_shared/components/ConfirmDialog.vue";
import PageRail from "../strategy_shared/components/PageRail.vue";
import {
	getVersionReviewOverview,
	getStrategyTree,
	diffStrategyVersions,
	getVersionHistory,
	reviewVersion,
	approveVersion,
} from "./data/strategyReviewApi.js";

function eventStatusClass(eventName) {
	if (["Approve", "Activate", "Activate successor"].includes(eventName)) return "is-live";
	if (["Submit for review", "Recommend for approval"].includes(eventName)) return "is-pending";
	return "is-draft";
}

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Strategy Alignment"), route: ["strategy-portfolio"] },
	{ label: __("Review Task") },
]);

const { route, go } = useRouteState("strategy-review-task");
const versionId = computed(() => route.value[1] || null);
const tab = computed(() => route.value[2] || "overview");

const loading = ref(true);
const notFound = ref(false);
const forbidden = ref(false);
const overview = ref(null);
const tree = ref({ tree: [] });
const diff = ref(null);
const history = ref([]);
const historyLoaded = ref(false);
const actingError = ref(null);
const acting = ref(false);
const showReturnDialog = ref(false);

async function load() {
	if (!versionId.value) return;
	loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	try {
		const data = await getVersionReviewOverview(versionId.value);
		if (data.not_found) {
			notFound.value = true;
		} else if (data.forbidden) {
			forbidden.value = true;
		} else {
			overview.value = data;
			tree.value = await getStrategyTree(versionId.value);
			// A direct load (or reload) landing straight on the Changes/History
			// tab must still fetch that tab's data — watch(tab, ...) below only
			// fires on a later CLIENT-SIDE tab change, never for the tab value
			// the route already had on mount (AGENTS.md §6.4: verify direct
			// load, not just in-page navigation).
			if (tab.value === "changes") loadDiff();
			if (tab.value === "history") loadHistory();
		}
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		loading.value = false;
	}
}

async function loadDiff() {
	if (!overview.value || diff.value) return;
	diff.value = await diffStrategyVersions(versionId.value, overview.value.active_version?.name || null);
}

async function loadHistory() {
	if (!overview.value || historyLoaded.value) return;
	history.value = await getVersionHistory(versionId.value);
	historyLoaded.value = true;
}

watch(versionId, load, { immediate: true });
watch(tab, (t) => {
	if (t === "changes") loadDiff();
	if (t === "history") loadHistory();
});

function switchTab(t) {
	go(versionId.value, t);
}

const isApprover = computed(() => overview.value?.role === "approver");
const headerTitle = computed(() =>
	isApprover.value ? __("Approve strategic plan version") : __("Review strategic plan version")
);
const canRecommend = computed(() => (overview.value?.allowed_actions || []).includes("Recommend for approval"));
const canApprove = computed(() => (overview.value?.allowed_actions || []).includes("Approve"));
const canReturn = computed(() => (overview.value?.allowed_actions || []).includes("Return"));

async function submitReturn(reason) {
	acting.value = true;
	actingError.value = null;
	try {
		const fn = isApprover.value ? approveVersion : reviewVersion;
		await fn(versionId.value, "Return", reason);
		frappe.show_alert({ message: __("Returned"), indicator: "orange" });
		showReturnDialog.value = false;
		await load();
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

const showAdvanceConfirm = ref(false);

async function submitAdvance() {
	acting.value = true;
	actingError.value = null;
	showAdvanceConfirm.value = false;
	try {
		if (canApprove.value) {
			await approveVersion(versionId.value, "Approve");
			frappe.show_alert({ message: __("Approved"), indicator: "green" });
		} else {
			await reviewVersion(versionId.value, "Recommend for approval");
			frappe.show_alert({ message: __("Recommended for approval"), indicator: "green" });
		}
		await load();
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}
</script>

<template>
	<div class="kt-strategy-ui">
		<PageRail :trail="railTrail" />
		<div class="kt-shell" style="padding-bottom: 90px">
			<div v-if="loading">{{ __("Loading...") }}</div>
			<div v-else-if="notFound" class="kt-card kt-empty"><h3>{{ __("This version could not be found.") }}</h3></div>
			<div v-else-if="forbidden" class="kt-card kt-empty"><h3>{{ __("You do not have access to this version.") }}</h3></div>
			<template v-else-if="overview">
				<header>
					<div class="kt-text-muted" style="text-transform: uppercase; font-size: 11px">
						{{ overview.plan.reference }} · {{ __("VERSION") }} {{ overview.version.version_number }}
					</div>
					<h1 style="font-size: 26px; display: inline-flex; align-items: center; gap: 10px">
						{{ headerTitle }}
						<span class="kt-status is-pending">{{ overview.version.status }}</span>
					</h1>
				</header>

				<p v-if="actingError" style="color: var(--ktstr-color-danger)">{{ actingError }}</p>

				<div class="kt-tabs">
					<div class="kt-tab" :class="{ active: tab === 'overview' }" @click="switchTab('overview')">{{ __("Overview") }}</div>
					<div class="kt-tab" :class="{ active: tab === 'structure' }" @click="switchTab('structure')">{{ __("Structure") }}</div>
					<div class="kt-tab" :class="{ active: tab === 'changes' }" @click="switchTab('changes')">{{ __("Changes") }}</div>
					<div class="kt-tab" :class="{ active: tab === 'history' }" @click="switchTab('history')">{{ __("History") }}</div>
				</div>

				<template v-if="tab === 'overview'">
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Plan identity") }}</div>
							<div class="kv-row"><span class="kv-label">{{ __("Strategic plan") }}</span><span class="kv-value">{{ overview.plan.title }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Procuring Entity") }}</span><span class="kv-value">{{ overview.plan.procuring_entity?.name }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Organisation scope") }}</span><span class="kv-value">{{ __("PE-wide") }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Plan role") }}</span><span class="kv-value">{{ overview.plan.plan_role }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Plan period") }}</span><span class="kv-value">{{ overview.plan.period_label }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Submitted version") }}</span><span class="kv-value">Version {{ overview.version.version_number }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Version effective period") }}</span><span class="kv-value">{{ overview.version.effective_period_label || "—" }}</span></div>
						</div>
						<div style="display: flex; flex-direction: column; gap: 16px">
							<div class="kt-card kt-blueprint">
								<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
								<div class="kt-card-title">{{ __("Submission authority") }}</div>
								<div class="kv-row"><span class="kv-label">{{ __("Submitted by") }}</span><span class="kv-value">{{ overview.submission_authority.submitted_by?.actor || "—" }}</span></div>
								<div class="kv-row"><span class="kv-label">{{ __("Submitted") }}</span><span class="kv-value">{{ overview.submission_authority.submitted_by?.at || "—" }}</span></div>
								<template v-if="isApprover">
									<div class="kv-row"><span class="kv-label">{{ __("Reviewed by") }}</span><span class="kv-value">{{ overview.submission_authority.reviewed_by?.actor || "—" }}</span></div>
									<div class="kv-row"><span class="kv-label">{{ __("Recommended") }}</span><span class="kv-value">{{ overview.submission_authority.reviewed_by?.at || "—" }}</span></div>
								</template>
							</div>
							<div class="kt-card kt-blueprint">
								<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
								<div class="kt-card-title">{{ __("Readiness") }}</div>
								<div v-for="c in overview.readiness.checks" :key="c.check" class="kv-row">
									<span class="kv-label">{{ c.check }}</span>
									<span class="kt-status is-live">{{ c.ready ? __("Ready") : __("Not ready") }}</span>
								</div>
							</div>
						</div>
						<div class="kt-card kt-blueprint" style="grid-column: 1 / -1">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Structure summary") }}</div>
							<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px 24px">
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="6" height="16"/><rect x="14" y="4" width="6" height="16"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Pillars") }}</div><div class="kt-figure">{{ overview.structure_summary.pillars }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.91a1 1 0 0 1 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Programmes") }}</div><div class="kt-figure">{{ overview.structure_summary.programmes }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Sub-programmes") }}</div><div class="kt-figure">{{ overview.structure_summary.sub_programmes }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Strategic objectives") }}</div><div class="kt-figure is-live">{{ overview.structure_summary.strategic_objectives }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Strategic outcomes") }}</div><div class="kt-figure is-live">{{ overview.structure_summary.strategic_outcomes }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Performance indicators") }}</div><div class="kt-figure is-attention">{{ overview.structure_summary.performance_indicators }}</div></div>
								</div>
								<div style="display: flex; align-items: center; gap: 12px">
									<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>
									<div><div class="kv-label" style="font-size: 12px">{{ __("Performance targets") }}</div><div class="kt-figure is-attention">{{ overview.structure_summary.performance_targets }}</div></div>
								</div>
							</div>
						</div>
					</div>
				</template>

				<template v-else-if="tab === 'structure'">
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("Submitted Version") }} {{ overview.version.version_number }} {{ __("structure") }}</div>
						<p class="kt-text-muted">{{ __("Read-only plan hierarchy") }}</p>
						<StructureTree :nodes="tree.tree" :read-only="true" />
					</div>
				</template>

				<template v-else-if="tab === 'changes'">
					<div class="kt-card">
						<div class="kt-card-title">
							{{ __("Changes from Active Version") }} {{ overview.active_version ? overview.active_version.version_number : "—" }}
						</div>
						<table v-if="diff && diff.changes.length" class="kt-table">
							<thead><tr><th>{{ __("Changed item") }}</th><th>{{ __("Active") }}</th><th>{{ __("Submitted") }}</th></tr></thead>
							<tbody>
								<tr v-for="(c, i) in diff.changes" :key="i">
									<td>{{ c.item }}</td>
									<td>{{ c.active }}</td>
									<td>{{ c.submitted }}</td>
								</tr>
							</tbody>
						</table>
						<p v-else class="kt-text-muted">{{ __("No other plan identity or structure items changed.") }}</p>
						<p v-if="diff" class="kt-text-muted" style="margin-top: 8px">{{ diff.limitation }}</p>
					</div>
				</template>

				<template v-else-if="tab === 'history'">
					<div class="kt-card">
						<div class="kt-card-title">{{ __("Version history") }}</div>
						<table class="kt-table">
							<thead><tr><th>{{ __("Date and time") }}</th><th>{{ __("Event") }}</th><th>{{ __("Actor") }}</th></tr></thead>
							<tbody>
								<tr v-for="(h, i) in history" :key="i">
									<td>{{ h.at }}</td>
									<td><span class="kt-status" :class="eventStatusClass(h.event)">{{ h.event }}</span></td>
									<td>{{ h.actor }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>
			</template>
		</div>

		<div v-if="overview && (canReturn || canRecommend || canApprove)" class="kt-sticky-footer">
			<button v-if="canReturn" type="button" class="kt-btn kt-btn-danger-outline" @click="showReturnDialog = true">
				{{ __("Return") }}
			</button>
			<button
				v-if="canRecommend || canApprove"
				type="button"
				class="kt-btn kt-btn-primary"
				:disabled="acting"
				@click="showAdvanceConfirm = true"
			>
				{{ canApprove ? __("Approve") : __("Recommend for approval") }}
			</button>
		</div>

		<ConfirmDialog
			:open="showAdvanceConfirm"
			:title="canApprove ? __('Approve this version?') : __('Recommend this version for approval?')"
			:message="canApprove ? __('The version will move to Approved and become eligible for activation.') : __('The version will move to Awaiting Approval.')"
			:confirm-label="canApprove ? __('Approve') : __('Recommend for approval')"
			@confirm="submitAdvance"
			@cancel="showAdvanceConfirm = false"
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
