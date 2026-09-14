<script setup>
// STR-UI-04 Approval task (STR-DES-06..09, STR-DES-06-Return). Route:
//   /app/strategy/approval/{plan_version_id}[/overview|structure|changes|history]
// The route binds to ONE submitted version: every tab reads that version
// and its fixed comparison baseline; nothing falls back to the plan's
// Current version (§12.4). The decision area is on every tab; the Overview
// leads with what changed; one deliberate click decides — no added
// confirmation stage, reason, checklist or tab tour (§11.6, STR-AC-030).
import { ref, computed, watch, onActivated } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import { runAttempt } from "../../strategy_shared/data/attempts.js";
import StructureTree from "../../strategy_shared/components/StructureTree.vue";
import ReturnDialog from "../../strategy_shared/components/ReturnDialog.vue";
import ObjectivesAndTargets from "../components/ObjectivesAndTargets.vue";
import StructureSummary from "../components/StructureSummary.vue";
import VersionTimeline from "../components/VersionTimeline.vue";
import { typeLabel } from "../../strategy_shared/nodeIcons.js";
import { getVersionReviewOverview, getStrategyTree, getVersionHistory, returnVersion, approveVersion } from "../data/strategyApi.js";

const { route, go, epoch } = useRouteState("strategy");
const versionId = computed(() => (route.value[1] === "approval" ? route.value[2] || null : null));
const tab = computed(() => route.value[3] || "overview");

const loading = ref(true);
const refreshing = ref(false);
const notFound = ref(false);
const forbidden = ref(false);
const loadError = ref(null);
const overview = ref(null);
const tree = ref({ tree: [] });
const history = ref([]);
const historyLoaded = ref(false);
const actingError = ref(null);
const acting = ref(false);
const unknownOutcome = ref(false);
const showReturnDialog = ref(false);
const selectedNode = ref(null);

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
	loadError.value = null;
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
			historyLoaded.value = false;
			if (tab.value === "history") loadHistory();
		}
	} catch (e) {
		if (seq === loadSeq) loadError.value = e;
	} finally {
		if (seq === loadSeq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
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
			history.value = [];
			historyLoaded.value = false;
			actingError.value = null;
			selectedNode.value = null;
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
	if (t === "history") loadHistory();
});

function switchTab(t) {
	go("approval", versionId.value, t);
}

const isSubmitted = computed(() => overview.value?.version?.status === "Submitted for approval");
const decision = computed(() => overview.value?.decision || {});
const blockers = computed(() => overview.value?.blockers || { blocked: false, failures: [] });
const readinessFailures = computed(() => (overview.value?.readiness?.failures || []).filter(Boolean));
const showFooter = computed(() => !!overview.value && isSubmitted.value && (decision.value.can_return || decision.value.can_approve || (overview.value.role === "approver" && blockers.value.blocked)));
const comparison = computed(() => overview.value?.comparison || null);
const previousByTargetId = computed(() => {
	const out = {};
	for (const c of comparison.value?.changes || []) {
		if (c.kind === "target" && c.proposed_id && c.previous && c.previous !== "—") out[c.proposed_id] = c.previous;
	}
	return out;
});
const tagClass = (c) => (c.kind === "date" ? "kt-tag kt-tag-accent-2" : "kt-tag kt-tag-accent");

function selectNode(node) {
	selectedNode.value = node;
}
function nodePath(node) {
	return (node.path || []).join(" / ");
}

async function submitReturn(reason) {
	acting.value = true;
	actingError.value = null;
	try {
		await runAttempt(
			`return:${overview.value.version.id}`,
			(key) => returnVersion(overview.value.version.id, reason, overview.value.expected_version, key),
			{ onUnknown: () => (unknownOutcome.value = true) }
		);
		unknownOutcome.value = false;
		frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" });
		showReturnDialog.value = false;
		await load({ quiet: true });
	} catch (e) {
		actingError.value = e.unknownOutcome ? __("We could not confirm the result. Checking the existing request…") : e.message || String(e);
	} finally {
		acting.value = false;
	}
}

// §12.4 — one deliberate click carries the expected token, the exact
// submitted ID and a stable attempt identity; the server revalidates
// everything and activates atomically. No confirmation stage.
async function submitApprove() {
	if (!decision.value.can_approve || acting.value) return;
	acting.value = true;
	actingError.value = null;
	try {
		await runAttempt(
			`approve:${overview.value.version.id}`,
			(key) => approveVersion(overview.value.version.id, overview.value.expected_version, key),
			{ onUnknown: () => (unknownOutcome.value = true) }
		);
		unknownOutcome.value = false;
		frappe.show_alert({ message: __("Approved and in use"), indicator: "green" });
		await load({ quiet: true });
	} catch (e) {
		actingError.value = e.unknownOutcome ? __("We could not confirm the result. Checking the existing request…") : e.message || String(e);
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
		style="padding-bottom: 120px"
	>
		<div v-if="loading" class="kt-card kt-blueprint" data-testid="str-loading">
			<p class="kt-muted" style="margin: 0 0 8px; font-size: 12px">{{ __("Loading strategic plans…") }}</p>
			<div v-for="i in 5" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
		</div>
		<div v-else-if="notFound" class="kt-notice is-warning" data-testid="str-not-found">
			<div class="kt-notice-body"><strong>{{ __("This plan record is not available to you.") }}</strong></div>
		</div>
		<div v-else-if="forbidden" class="kt-notice is-critical" data-testid="str-forbidden">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
			<div class="kt-notice-body">
				<strong>{{ __("You do not have access to this Strategy approval page.") }}</strong>
				{{ __("Decision access requires Strategy Approver responsibility. Administrator and System Manager can inspect the record read-only. Ask your KenTender administrator to check your access in System setup.") }}
			</div>
		</div>
		<div v-else-if="loadError && !overview" data-testid="str-error">
			<div class="kt-notice is-warning">
				<div class="kt-notice-body"><strong>{{ __("Strategy information could not be loaded.") }}</strong> {{ __("Try again. If the problem continues, contact KenTender support.") }}</div>
			</div>
			<div style="margin-top: 10px"><button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button></div>
		</div>
		<template v-else-if="overview">
			<header>
				<div class="kt-eyebrow" style="text-transform: uppercase; font-size: 11px; letter-spacing: 0.1em; color: var(--kt-color-accent); margin-bottom: 6px" data-testid="str-approval-eyebrow">
					{{ overview.plan.reference }} &middot; {{ __("VERSION") }} {{ overview.version.version_number }}
				</div>
				<h1 style="font-size: 28px; margin: 0 0 4px" data-testid="str-approval-title">{{ overview.title }}</h1>
				<div style="font-size: 16px; font-weight: 600; margin-bottom: 6px" data-testid="str-approval-plan-title">{{ overview.plan.title }}</div>
				<div style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--kt-color-neutral-700)">
					<span v-if="overview.submission_authority.submitted_by" data-testid="str-submitted-by">
						{{ __("Submitted by {0}, {1}", [overview.submission_authority.submitted_by.actor_name || overview.submission_authority.submitted_by.actor, overview.submission_authority.submitted_by.at_label]) }}
					</span>
					<span class="kt-status" :class="overview.version.status_tone" data-testid="str-approval-status">{{ overview.version.status_label }}</span>
				</div>
			</header>

			<p v-if="actingError" class="kt-field-error" data-testid="str-action-error" style="font-size: 14px; margin: 0">{{ actingError }}</p>

			<div v-if="!isSubmitted" class="kt-notice" data-testid="str-approval-settled">
				<div class="kt-notice-body">
					{{ __("This version is no longer awaiting a decision.") }}
					<a href="#" data-testid="str-open-plan" @click.prevent="frappe.set_route(...overview.routes.plan)">{{ __("Open plan") }}</a>
				</div>
			</div>

			<!-- §11.6 future-effective variant — on every tab, approval disabled, Return available. -->
			<div v-if="isSubmitted && blockers.future_effective" class="kt-notice is-warning" data-testid="str-future-effective">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
				<div class="kt-notice-body">
					<strong>{{ blockers.future_effective.headline }}</strong>
					{{ blockers.future_effective.guidance }}
				</div>
			</div>
			<div v-if="isSubmitted && readinessFailures.length" class="kt-notice is-critical" data-testid="str-readiness-failures">
				<div class="kt-notice-body">
					<strong>{{ __("This version cannot be approved yet.") }}</strong>
					<span v-for="f in readinessFailures" :key="f.rule" style="display: block">{{ f.message }}</span>
				</div>
			</div>
			<div v-if="isSubmitted && overview.self_approval_blocked" class="kt-notice" data-testid="str-self-approval">
				<div class="kt-notice-body"><strong>{{ __("Another Strategy Approver must review this version.") }}</strong></div>
			</div>

			<div class="kt-tabs" role="tablist">
				<button type="button" role="tab" class="kt-tab" data-testid="str-atab-overview" :aria-selected="tab === 'overview'" @click="switchTab('overview')">{{ __("Overview") }}</button>
				<button type="button" role="tab" class="kt-tab" data-testid="str-atab-structure" :aria-selected="tab === 'structure'" @click="switchTab('structure')">{{ __("Structure") }}</button>
				<button type="button" role="tab" class="kt-tab" data-testid="str-atab-changes" :aria-selected="tab === 'changes'" @click="switchTab('changes')">{{ __("Changes") }}</button>
				<button type="button" role="tab" class="kt-tab" data-testid="str-atab-history" :aria-selected="tab === 'history'" @click="switchTab('history')">{{ __("History") }}</button>
			</div>

			<template v-if="tab === 'overview'">
				<div v-if="comparison" class="kt-card kt-blueprint" data-testid="str-what-changed">
					<div class="kt-card-title">{{ __("What changed") }}</div>
					<template v-if="comparison.available">
						<table v-if="comparison.changes.length" class="kt-table">
							<thead><tr><th>{{ __("Item") }}</th><th>{{ __("Previous accepted baseline") }} &middot; V{{ comparison.base_version_number }}</th><th>{{ __("Proposed") }} &middot; V{{ overview.version.version_number }}</th></tr></thead>
							<tbody>
								<tr v-for="(c, i) in comparison.changes" :key="i" data-testid="str-changes-row" :data-kind="c.kind">
									<td><span :class="tagClass(c)" style="margin-right: 8px">{{ c.tag }}</span>{{ c.item }}<div v-if="c.path" class="kt-muted" style="font-size: 12px">{{ c.path }}</div></td>
									<td>{{ c.previous }}</td>
									<td>{{ c.proposed }}</td>
								</tr>
							</tbody>
						</table>
						<p style="font-size: 13px; color: var(--kt-color-neutral-700); margin: 10px 0 0" data-testid="str-no-other-changes">
							{{ comparison.changes.length ? __("No other submitted identity, effective-date or structure values changed.") : comparison.message }}
						</p>
					</template>
					<template v-else>
						<p class="kt-field-error" style="font-size: 14px; margin: 0" data-testid="str-comparison-failed">{{ __("The changes could not be loaded. Try again.") }}</p>
						<div><button type="button" class="kt-btn kt-btn-secondary" @click="load({ quiet: true })">{{ __("Try again") }}</button></div>
					</template>
				</div>

				<div class="kt-card kt-blueprint" data-testid="str-proposed-plan">
					<div class="kt-card-title">{{ __("Proposed plan") }}</div>
					<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 13.6px; margin-bottom: 13.6px">
						<div><div class="kt-label">{{ __("Plan type") }}</div><div style="font-size: 14px; margin-top: 3px">{{ overview.plan.plan_type_label }}</div></div>
						<div><div class="kt-label">{{ __("Plan period") }}</div><div style="font-size: 14px; margin-top: 3px">{{ overview.plan.period_label }}</div></div>
						<div><div class="kt-label">{{ __("Proposed version applies") }}</div><div style="font-size: 14px; margin-top: 3px" data-testid="str-proposed-applies">{{ overview.version.effective_period_label || "—" }}</div></div>
					</div>
					<div style="border-top: 1px solid var(--kt-color-divider); padding-top: 13.6px">
						<ObjectivesAndTargets :objectives="overview.objectives" :previous-by-target-id="previousByTargetId" />
					</div>
				</div>

				<div class="kt-grid-2">
					<div class="kt-card kt-blueprint" data-testid="str-submission-card">
						<div class="kt-card-title">{{ __("Submission authority") }}</div>
						<VersionTimeline
							:events="overview.submission_authority.submitted_by ? [{ event: 'Submit for approval', event_label: __('Submitted by {0}', [overview.submission_authority.submitted_by.actor_name || overview.submission_authority.submitted_by.actor]), at_label: overview.submission_authority.submitted_by.at_label, actor_name: '', tone: 'is-pending' }] : []"
						/>
					</div>
					<div class="kt-card kt-blueprint">
						<div class="kt-card-title">{{ __("Structure summary") }}</div>
						<StructureSummary :counts="overview.structure_summary" />
					</div>
				</div>
			</template>

			<template v-else-if="tab === 'structure'">
				<div class="kt-editor-grid">
					<div class="kt-card kt-blueprint" data-testid="str-approval-structure">
						<div class="kt-card-title" style="margin-bottom: 4px">{{ __("Proposed plan") }}</div>
						<div style="font-size: 12px; color: var(--kt-color-neutral-700); margin-bottom: 13.6px">{{ __("Read-only submitted plan structure") }}</div>
						<StructureTree :nodes="tree.tree" :read-only="true" :selected-id="selectedNode?.id" @select="selectNode" />
					</div>
					<div class="kt-card kt-blueprint" style="position: sticky; top: 80px" data-testid="str-approval-node-facts">
						<template v-if="selectedNode">
							<div class="kt-card-title" style="margin-bottom: 4px">{{ typeLabel(selectedNode.node_type) }}</div>
							<div v-if="nodePath(selectedNode)" style="font-size: 12px; color: var(--kt-color-neutral-700); margin-bottom: 13.6px">{{ nodePath(selectedNode) }}</div>
							<div v-if="selectedNode.node_type === 'Performance Target'">
								<div class="kt-label">{{ __("Target") }}</div>
								<div style="font-size: 14px; margin-top: 3px">{{ selectedNode.result_label }} &middot; {{ selectedNode.period_label }}</div>
							</div>
							<template v-else-if="selectedNode.node_type === 'Performance Indicator'">
								<div><div class="kt-label">{{ __("Indicator") }}</div><div style="font-size: 14px; margin-top: 3px">{{ selectedNode.title }}</div></div>
								<div style="margin-top: 10px"><div class="kt-label">{{ __("How it is measured") }}</div><div style="font-size: 13px; margin-top: 3px; color: var(--kt-color-neutral-800)">{{ selectedNode.definition }}</div></div>
								<div style="margin-top: 10px"><div class="kt-label">{{ __("Unit") }}</div><div style="font-size: 14px; margin-top: 3px">{{ selectedNode.unit }}</div></div>
								<div v-if="selectedNode.children.length" style="margin-top: 10px">
									<div class="kt-label">{{ __("Targets") }}</div>
									<div v-for="t in selectedNode.children" :key="t.id" style="font-size: 14px; margin-top: 3px">{{ t.result_label }} &middot; {{ t.period_label }}</div>
								</div>
							</template>
							<div v-else><div class="kt-label">{{ typeLabel(selectedNode.node_type) }}</div><div style="font-size: 14px; margin-top: 3px">{{ selectedNode.title }}</div></div>
						</template>
						<p v-else class="kt-muted" style="margin: 0">{{ __("Select an item to read its complete facts.") }}</p>
					</div>
				</div>
			</template>

			<template v-else-if="tab === 'changes'">
				<div class="kt-card kt-blueprint" data-testid="str-approval-changes">
					<template v-if="!comparison">
						<div class="kt-card-title">{{ __("Changes") }}</div>
						<p style="margin: 0; font-size: 14px" data-testid="str-first-version">
							{{ __("This is the first version of this plan.") }}
							<a href="#" @click.prevent="switchTab('structure')">{{ __("Proposed plan") }}</a>
						</p>
					</template>
					<template v-else-if="!comparison.available">
						<div class="kt-card-title">{{ __("Changes") }}</div>
						<p class="kt-field-error" style="font-size: 14px; margin: 0" data-testid="str-comparison-failed">{{ __("The changes could not be loaded. Try again.") }}</p>
						<div><button type="button" class="kt-btn kt-btn-secondary" @click="load({ quiet: true })">{{ __("Try again") }}</button></div>
					</template>
					<template v-else>
						<div class="kt-card-title">{{ comparison.heading }}</div>
						<table v-if="comparison.changes.length" class="kt-table">
							<thead><tr><th>{{ __("Item") }}</th><th>{{ __("Previous accepted baseline") }} &middot; V{{ comparison.base_version_number }}</th><th>{{ __("Proposed") }} &middot; V{{ overview.version.version_number }}</th></tr></thead>
							<tbody>
								<tr v-for="(c, i) in comparison.changes" :key="i" data-testid="str-changes-row" :data-kind="c.kind">
									<td><span :class="tagClass(c)" style="margin-right: 8px">{{ c.tag }}</span>{{ c.item }}<div v-if="c.path" class="kt-muted" style="font-size: 12px">{{ c.path }}</div></td>
									<td style="white-space: normal">{{ c.previous }}</td>
									<td style="white-space: normal">{{ c.proposed }}</td>
								</tr>
							</tbody>
						</table>
						<p style="font-size: 13px; color: var(--kt-color-neutral-700); margin: 10px 0 0" data-testid="str-no-other-changes">
							{{ comparison.changes.length ? __("No other submitted identity, effective-date or structure values changed.") : comparison.message }}
						</p>
					</template>
				</div>
			</template>

			<template v-else-if="tab === 'history'">
				<div class="kt-card kt-blueprint" data-testid="str-approval-history">
					<div class="kt-card-title">{{ __("Submission and history") }}</div>
					<VersionTimeline :events="history" />
				</div>
			</template>
		</template>

		<div v-if="showFooter" class="kt-sticky-footer" style="align-items: center; gap: 13.6px" data-testid="str-decision-footer">
			<div style="font-size: 12px; color: var(--kt-color-neutral-700); max-width: 480px; text-align: right" data-testid="str-decision-consequence">{{ decision.consequence }}</div>
			<div style="display: flex; gap: 10.2px; flex: none">
				<button v-if="decision.can_return" type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="acting" data-testid="str-return" @click="showReturnDialog = true">
					{{ decision.return_label }}
				</button>
				<button
					v-if="decision.can_approve || blockers.blocked"
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="acting || !decision.can_approve"
					:data-blocked="blockers.blocked ? 'true' : 'false'"
					data-testid="str-approve"
					@click="submitApprove"
				>
					{{ decision.approve_label }}
				</button>
			</div>
		</div>

		<ReturnDialog :open="showReturnDialog" :busy="acting" :error="showReturnDialog ? actingError || '' : ''" @confirm="submitReturn" @cancel="showReturnDialog = false" />
	</div>
</template>
