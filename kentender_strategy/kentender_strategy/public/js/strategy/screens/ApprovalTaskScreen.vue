<script setup>
// STR-UI-04 Approval task (STR-DES-06..09). Route:
//   /app/strategy/approval/{plan_version_id}[/overview|structure|changes|history]
// The route binds to ONE submitted version: every tab reads that version and
// never falls back to the plan's Active version (§12.4).
import { ref, computed, watch, onActivated } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import StructureTree from "../../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../../strategy_shared/components/ConfirmDialog.vue";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import {
	getVersionReviewOverview,
	getStrategyTree,
	diffStrategyVersions,
	getVersionHistory,
	returnVersion,
	approveVersion,
} from "../data/strategyApi.js";

function eventStatusClass(eventName) {
	if (["Approve", "Approve successor"].includes(eventName)) return "is-live";
	if (eventName === "Submit for approval") return "is-pending";
	return "is-draft";
}
function statusClass(status) {
	if (status === "Active") return "is-live";
	if (status === "Submitted for approval") return "is-pending";
	return "is-draft";
}

const { route, go, epoch } = useRouteState("strategy");
const versionId = computed(() => (route.value[1] === "approval" ? route.value[2] || null : null));
const tab = computed(() => route.value[3] || "overview");

const loading = ref(true);
const refreshing = ref(false);
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

// Declared after the state it reads: usePageRail watches this computed,
// and watch() evaluates its source during setup.
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Strategy Alignment"), route: ["strategy"] },
	{ label: __("Approval tasks"), route: ["strategy", "my-work"] },
	{ label: overview.value?.version?.reference || __("Approval task") },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail);

let loadSeq = 0;
async function load(opts) {
	if (!versionId.value) return;
	const quiet = !!(opts && opts.quiet === true) && !!overview.value;
	const seq = ++loadSeq;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	notFound.value = false;
	forbidden.value = false;
	try {
		const data = await getVersionReviewOverview(versionId.value);
		if (seq !== loadSeq) return;
		if (data.not_found) {
			notFound.value = true;
		} else if (data.forbidden) {
			forbidden.value = true;
		} else {
			overview.value = data;
			tree.value = await getStrategyTree(data.version.id);
			// A direct load landing on Changes/History must fetch that tab's
			// data too — watch(tab) only fires on a later client-side change.
			diff.value = null;
			historyLoaded.value = false;
			if (tab.value === "changes") loadDiff();
			if (tab.value === "history") loadHistory();
		}
	} catch (e) {
		if (seq === loadSeq) actingError.value = e.message || String(e);
	} finally {
		if (seq === loadSeq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

async function loadDiff() {
	if (!overview.value || diff.value) return;
	diff.value = await diffStrategyVersions(overview.value.version.id, overview.value.version.based_on_plan_version_id || null);
}

async function loadHistory() {
	if (!overview.value || historyLoaded.value) return;
	history.value = await getVersionHistory(overview.value.version.id);
	historyLoaded.value = true;
}

watch(
	versionId,
	(id, old) => {
		if (!id) return;
		if (id !== old) {
			overview.value = null;
			diff.value = null;
			history.value = [];
			historyLoaded.value = false;
			actingError.value = null;
			load();
		}
	},
	{ immediate: true }
);
watch(epoch, () => {
	if (overview.value) load({ quiet: true });
});
let activations = 0;
onActivated(() => {
	if (activations++ > 0 && overview.value) load({ quiet: true });
});
watch(tab, (t) => {
	if (t === "changes") loadDiff();
	if (t === "history") loadHistory();
});

function switchTab(t) {
	go("approval", versionId.value, t);
}

const canApprove = computed(() => (overview.value?.allowed_actions || []).includes("Approve"));
const canReturn = computed(() => (overview.value?.allowed_actions || []).includes("Return"));

async function submitReturn(reason) {
	acting.value = true;
	actingError.value = null;
	try {
		await returnVersion(overview.value.version.id, reason, overview.value.expected_version);
		frappe.show_alert({ message: __("Returned"), indicator: "orange" });
		showReturnDialog.value = false;
		await load({ quiet: true });
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		acting.value = false;
	}
}

const showApproveConfirm = ref(false);

async function submitApprove() {
	acting.value = true;
	actingError.value = null;
	showApproveConfirm.value = false;
	try {
		await approveVersion(overview.value.version.id, overview.value.expected_version);
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
	<div
		class="kt-shell"
		data-testid="str-approval"
		:data-tab="tab"
		:data-loading="loading ? 'true' : 'false'"
		:data-refreshing="refreshing ? 'true' : 'false'"
		style="padding-bottom: 90px"
	>
		<div v-if="loading" class="kt-card kt-blueprint" data-testid="str-loading">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="i in 5" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>
		<div v-else-if="notFound" class="kt-card kt-empty" data-testid="str-not-found"><h2>{{ __("This version could not be found.") }}</h2></div>
		<div v-else-if="forbidden" class="kt-card kt-empty" data-testid="str-forbidden">
			<h2>{{ __("You do not have access to this approval task.") }}</h2>
			<p>{{ __("This area needs the Strategy Approver responsibility. Ask your KenTender administrator to assign it in System setup.") }}</p>
		</div>
		<template v-else-if="overview">
			<header>
				<div class="kt-muted" style="text-transform: uppercase; font-size: 11px" data-testid="str-approval-eyebrow">
					{{ overview.plan.reference }} · {{ __("VERSION") }} {{ overview.version.version_number }}
				</div>
				<h1 style="font-size: 26px; display: inline-flex; align-items: center; gap: 10px">
					{{ __("Approve strategic plan version") }}
					<span class="kt-status" data-testid="str-approval-status" :class="statusClass(overview.version.status)">{{ overview.version.status }}</span>
				</h1>
			</header>

			<p v-if="actingError" data-testid="str-action-error" style="color: oklch(0.45 0.13 28)">{{ actingError }}</p>
			<p v-if="overview.version.status !== 'Submitted for approval'" class="kt-muted" data-testid="str-approval-settled">
				{{ __("This version is no longer awaiting a decision.") }}
				<a href="#" data-testid="str-open-plan" @click.prevent="frappe.set_route(...overview.routes.plan)">{{ __("Open plan") }}</a>
			</p>

			<div class="kt-tabs">
				<div class="kt-tab" data-testid="str-atab-overview" :aria-selected="tab === 'overview'" @click="switchTab('overview')">{{ __("Overview") }}</div>
				<div class="kt-tab" data-testid="str-atab-structure" :aria-selected="tab === 'structure'" @click="switchTab('structure')">{{ __("Structure") }}</div>
				<div class="kt-tab" data-testid="str-atab-changes" :aria-selected="tab === 'changes'" @click="switchTab('changes')">{{ __("Changes") }}</div>
				<div class="kt-tab" data-testid="str-atab-history" :aria-selected="tab === 'history'" @click="switchTab('history')">{{ __("History") }}</div>
			</div>

			<template v-if="tab === 'overview'">
				<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
					<div class="kt-card kt-blueprint" data-testid="str-identity-card">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title">{{ __("Plan identity") }}</div>
						<div class="kt-row"><dt>{{ __("Strategic plan") }}</dt><dd>{{ overview.plan.title }}</dd></div>
						<div class="kt-row"><dt>{{ __("Plan role") }}</dt><dd>{{ overview.plan.plan_role }}</dd></div>
						<div class="kt-row"><dt>{{ __("Plan period") }}</dt><dd>{{ overview.plan.period_label }}</dd></div>
						<div class="kt-row"><dt>{{ __("Submitted version") }}</dt><dd>Version {{ overview.version.version_number }}</dd></div>
						<div class="kt-row"><dt>{{ __("Version effective period") }}</dt><dd>{{ overview.version.effective_period_label || "—" }}</dd></div>
					</div>
					<div style="display: flex; flex-direction: column; gap: 16px">
						<div class="kt-card kt-blueprint" data-testid="str-submission-card">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Submission authority") }}</div>
							<div class="kt-row"><dt>{{ __("Submitted by") }}</dt><dd data-testid="str-submitted-by">{{ overview.submission_authority.submitted_by?.actor_name || overview.submission_authority.submitted_by?.actor || "—" }}</dd></div>
							<div class="kt-row"><dt>{{ __("Submitted") }}</dt><dd>{{ overview.submission_authority.submitted_by?.at_label || overview.submission_authority.submitted_by?.at || "—" }}</dd></div>
						</div>
						<div class="kt-card kt-blueprint" data-testid="str-readiness-card">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div class="kt-card-title">{{ __("Readiness") }}</div>
							<div v-for="c in overview.readiness.checks" :key="c.check" class="kt-row" data-testid="str-readiness-row">
								<dt>{{ c.check }}</dt>
								<dd><span class="kt-status" :class="c.ready ? 'is-live' : 'is-pending'">{{ c.ready ? __("Ready") : __("Not ready") }}</span></dd>
							</div>
						</div>
					</div>
					<div class="kt-card kt-blueprint" style="grid-column: 1 / -1" data-testid="str-summary-card">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-card-title" style="margin-bottom: 16px">{{ __("Structure summary") }}</div>
						<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 24px">
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="6" height="16"/><rect x="14" y="4" width="6" height="16"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Pillars") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ overview.structure_summary.pillars }}</div></div>
							</div>
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12.83 2.18 8.58 3.9a1 1 0 0 1 0 1.83l-8.58 3.9a2 2 0 0 1-1.66 0L2.6 7.91a1 1 0 0 1 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Programmes") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ overview.structure_summary.programmes }}</div></div>
							</div>
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#003d9b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Sub-programmes") }}</div><div class="kt-figure" style="font-size: 16px; font-weight: 600; color: #003d9b">{{ overview.structure_summary.sub_programmes }}</div></div>
							</div>
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#047857" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Strategic objectives") }}</div><div class="kt-figure is-live" style="font-size: 16px; font-weight: 600">{{ overview.structure_summary.strategic_objectives }}</div></div>
							</div>
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Performance indicators") }}</div><div class="kt-figure is-attention" style="font-size: 16px; font-weight: 600">{{ overview.structure_summary.performance_indicators }}</div></div>
							</div>
							<div style="display: flex; align-items: center; gap: 12px">
								<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92610a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/></svg>
								<div><div class="kt-muted" style="font-size: 12px">{{ __("Performance targets") }}</div><div class="kt-figure is-attention" style="font-size: 16px; font-weight: 600">{{ overview.structure_summary.performance_targets }}</div></div>
							</div>
						</div>
					</div>
				</div>
			</template>

			<template v-else-if="tab === 'structure'">
				<div class="kt-card kt-blueprint" data-testid="str-approval-structure">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Submitted Version {0} structure", [overview.version.version_number]) }}</div>
					<p class="kt-muted">{{ __("Read-only plan hierarchy") }}</p>
					<StructureTree :nodes="tree.tree" :read-only="true" />
				</div>
			</template>

			<template v-else-if="tab === 'changes'">
				<div class="kt-card" data-testid="str-approval-changes">
					<div class="kt-card-title">
						<template v-if="overview.active_version">{{ __("Changes from Active Version {0}", [overview.active_version.version_number]) }}</template>
						<template v-else>{{ __("Changes") }}</template>
					</div>
					<table v-if="diff && diff.changes.length" class="kt-table">
						<thead><tr><th>{{ __("Changed item") }}</th><th>{{ __("Active") }}</th><th>{{ __("Submitted") }}</th></tr></thead>
						<tbody>
							<tr v-for="(c, i) in diff.changes" :key="i" data-testid="str-changes-row">
								<td>{{ c.item }}</td>
								<td>{{ c.active }}</td>
								<td>{{ c.submitted }}</td>
							</tr>
						</tbody>
					</table>
					<p v-else-if="diff" class="kt-muted" data-testid="str-no-changes">{{ __("No other plan identity or structure items changed.") }}</p>
					<p v-else class="kt-muted">{{ __("Loading...") }}</p>
					<p v-if="diff && diff.changes.length" class="kt-muted" style="margin-top: 8px">{{ __("No other plan identity or structure items changed.") }}</p>
				</div>
			</template>

			<template v-else-if="tab === 'history'">
				<div class="kt-card" data-testid="str-approval-history">
					<div class="kt-card-title">{{ __("Version history") }}</div>
					<table class="kt-table">
						<thead><tr><th>{{ __("Date and time") }}</th><th>{{ __("Event") }}</th><th>{{ __("Actor") }}</th><th>{{ __("Reason") }}</th></tr></thead>
						<tbody>
							<tr v-for="(h, i) in history" :key="i" data-testid="str-history-row">
								<td>{{ h.at_label || h.at }}</td>
								<td><span class="kt-status" :class="eventStatusClass(h.event)">{{ h.event }}</span></td>
								<td>{{ h.actor_name || h.actor }}</td>
								<td>{{ h.reason || "—" }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</template>

		<div v-if="overview && (canReturn || canApprove)" class="kt-sticky-footer" data-testid="str-decision-footer">
			<button v-if="canReturn" type="button" class="kt-btn kt-btn-secondary kt-danger" data-testid="str-return" @click="showReturnDialog = true">
				{{ __("Return") }}
			</button>
			<button v-if="canApprove" type="button" class="kt-btn kt-btn-primary" :disabled="acting" data-testid="str-approve" @click="showApproveConfirm = true">
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
			:reason-placeholder="__('Return reason (10-500 characters)')"
			:reason-min-length="10"
			:reason-max-length="500"
			:confirm-label="__('Return')"
			@confirm="submitReturn"
			@cancel="showReturnDialog = false"
		/>
	</div>
</template>
