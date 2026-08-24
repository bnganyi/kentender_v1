<script setup>
import { ref, computed, watch } from "vue";
import { useRouteState } from "../strategy_shared/composables/useRouteState.js";
import StructureTree from "../strategy_shared/components/StructureTree.vue";
import ConfirmDialog from "../strategy_shared/components/ConfirmDialog.vue";
import {
	getVersionReviewOverview,
	getStrategyTree,
	diffStrategyVersions,
	getPlanHistory,
	reviewVersion,
	approveVersion,
} from "./data/strategyReviewApi.js";

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
const returnReason = ref("");
const showReturnBox = ref(false);

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
	history.value = await getPlanHistory(overview.value.plan.id);
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

async function submitReturn() {
	acting.value = true;
	actingError.value = null;
	try {
		const fn = isApprover.value ? approveVersion : reviewVersion;
		await fn(versionId.value, "Return", returnReason.value);
		frappe.show_alert({ message: __("Returned"), indicator: "orange" });
		showReturnBox.value = false;
		returnReason.value = "";
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
						<div class="kt-card">
							<div class="kt-card-title">{{ __("Plan identity") }}</div>
							<div class="kv-row"><span class="kv-label">{{ __("Strategic plan") }}</span><span class="kv-value">{{ overview.plan.title }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Procuring Entity") }}</span><span class="kv-value">{{ overview.plan.procuring_entity?.name }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Plan role") }}</span><span class="kv-value">{{ overview.plan.plan_role }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Plan period") }}</span><span class="kv-value">{{ overview.plan.period_label }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Submitted version") }}</span><span class="kv-value">Version {{ overview.version.version_number }}</span></div>
							<div class="kv-row"><span class="kv-label">{{ __("Version effective period") }}</span><span class="kv-value">{{ overview.version.effective_period_label || "—" }}</span></div>
						</div>
						<div style="display: flex; flex-direction: column; gap: 16px">
							<div class="kt-card">
								<div class="kt-card-title">{{ __("Submission authority") }}</div>
								<div class="kv-row"><span class="kv-label">{{ __("Submitted by") }}</span><span class="kv-value">{{ overview.submission_authority.submitted_by?.actor || "—" }}</span></div>
								<div v-if="isApprover" class="kv-row"><span class="kv-label">{{ __("Reviewed by") }}</span><span class="kv-value">{{ overview.submission_authority.reviewed_by?.actor || "—" }}</span></div>
							</div>
							<div class="kt-card">
								<div class="kt-card-title">{{ __("Readiness") }}</div>
								<div v-for="c in overview.readiness.checks" :key="c.check" class="kv-row">
									<span class="kv-label">{{ c.check }}</span>
									<span class="kt-status is-live">{{ c.ready ? __("Ready") : __("Not ready") }}</span>
								</div>
							</div>
						</div>
						<div class="kt-card" style="grid-column: 1 / -1">
							<div class="kt-card-title">{{ __("Structure summary") }}</div>
							<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px">
								<div><div class="kv-label">{{ __("Pillars") }}</div><div style="font-size: 22px">{{ overview.structure_summary.pillars }}</div></div>
								<div><div class="kv-label">{{ __("Programmes") }}</div><div style="font-size: 22px">{{ overview.structure_summary.programmes }}</div></div>
								<div><div class="kv-label">{{ __("Sub-programmes") }}</div><div style="font-size: 22px">{{ overview.structure_summary.sub_programmes }}</div></div>
								<div><div class="kv-label">{{ __("Strategic objectives") }}</div><div style="font-size: 22px">{{ overview.structure_summary.strategic_objectives }}</div></div>
								<div><div class="kv-label">{{ __("Strategic outcomes") }}</div><div style="font-size: 22px">{{ overview.structure_summary.strategic_outcomes }}</div></div>
								<div><div class="kv-label">{{ __("Performance indicators") }}</div><div style="font-size: 22px">{{ overview.structure_summary.performance_indicators }}</div></div>
								<div><div class="kv-label">{{ __("Performance targets") }}</div><div style="font-size: 22px">{{ overview.structure_summary.performance_targets }}</div></div>
							</div>
						</div>
					</div>
				</template>

				<template v-else-if="tab === 'structure'">
					<div class="kt-card">
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
									<td><span class="kt-status is-pending">{{ h.event }}</span></td>
									<td>{{ h.actor }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>
			</template>
		</div>

		<div v-if="overview && (canReturn || canRecommend || canApprove)" class="kt-sticky-footer">
			<template v-if="showReturnBox">
				<input
					v-model="returnReason"
					class="kt-input"
					style="width: 360px"
					:placeholder="__('Reason (10-500 characters)')"
				/>
				<button type="button" class="kt-btn kt-btn-ghost" @click="showReturnBox = false">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-danger-outline" :disabled="acting" @click="submitReturn">
					{{ __("Confirm return") }}
				</button>
			</template>
			<template v-else>
				<button v-if="canReturn" type="button" class="kt-btn kt-btn-danger-outline" @click="showReturnBox = true">
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
			</template>
		</div>

		<ConfirmDialog
			:open="showAdvanceConfirm"
			:title="canApprove ? __('Approve this version?') : __('Recommend this version for approval?')"
			:message="canApprove ? __('The version will move to Approved and become eligible for activation.') : __('The version will move to Awaiting Approval.')"
			:confirm-label="canApprove ? __('Approve') : __('Recommend for approval')"
			@confirm="submitAdvance"
			@cancel="showAdvanceConfirm = false"
		/>
	</div>
</template>
