<script setup>
import { ref, computed, watch, onActivated, onMounted, nextTick } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes, formatSignedKes, mintKey } from "../../budget_shared/data/formatKes.js";
import { getBudgetApprovalTask, getBudgetApprovalTaskLines, getBudgetApprovalTaskChanges, getBudgetVersionHistory, returnBudgetVersion, approveBudgetVersion } from "../data/budgetApi.js";

// BUD-UI-04 — BUD-DES-08/09/10/11 (Review allocation changes) and BUD-DES-13
// (Review registered allocation): the decision and its evidence together
// (BUD-CHG-001 v1.9 §9.4, §11.8–§11.13, §12.5). One approval decides and
// activates; no readiness checklist, no repeat confirmation.
const { route, go, epoch } = useRouteState("budget-funding");
const versionIdParam = computed(() => route.value[2]);
const tab = computed(() => route.value[3] || "overview");
const task = ref(null);

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: __("Approval tasks") },
	{ label: task.value?.version?.code || versionIdParam.value },
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
const stale = ref(false);
const lines = ref(null);
const changes = ref(null);
const history = ref(null);
const returnOpen = ref(false);
const returnReason = ref("");
const returnInput = ref(null);
const docPreviewFailed = ref(false);
const docAvailable = ref(null); // null = not checked, true/false = HEAD result

// §11.8 — a preview failure must not conceal an unavailable file: check the
// exact submitted file before framing it, and say so when it cannot be opened.
async function checkDocument(url) {
	docAvailable.value = null;
	docPreviewFailed.value = false;
	if (!url) return;
	try {
		const r = await fetch(url, { method: "HEAD", credentials: "same-origin" });
		docAvailable.value = r.ok;
	} catch (e) {
		docAvailable.value = false;
	}
}

async function load(opts) {
	if (!versionIdParam.value) return;
	const quiet = !!(opts && opts.quiet) && !!task.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	notFound.value = false;
	forbidden.value = null;
	serverError.value = false;
	try {
		const data = await getBudgetApprovalTask(versionIdParam.value);
		if (!guard.isCurrent(token)) return;
		if (data && data.outcome === "FORBIDDEN") {
			task.value = null;
			forbidden.value = data.forbidden;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			task.value = null;
			notFound.value = true;
			return;
		}
		task.value = data;
		lines.value = null;
		changes.value = null;
		history.value = null;
		checkDocument(data.evidence?.document?.url);
		await loadTab(tab.value);
		// The Overview's Submission and history disclosure reads the same trail.
		if (!history.value) history.value = await getBudgetVersionHistory(versionIdParam.value);
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this approval task"), text: "" };
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
	if (!task.value) return;
	if (t === "lines" && !lines.value) lines.value = await getBudgetApprovalTaskLines(versionIdParam.value);
	else if (t === "changes" && !changes.value) changes.value = await getBudgetApprovalTaskChanges(versionIdParam.value);
	else if (t === "history" && !history.value) history.value = await getBudgetVersionHistory(versionIdParam.value);
}
watch(tab, (t) => loadTab(t));
onMounted(load);
watch(versionIdParam, (v, prev) => v && v !== prev && (task.value = null, load()));
let activations = 0;
onActivated(() => activations++ > 0 && task.value && load({ quiet: true }));
watch(epoch, () => task.value && load({ quiet: true }));

function switchTab(t) {
	go("review", versionIdParam.value, t === "overview" ? undefined : t);
}

const isSuccessor = computed(() => task.value?.kind === "successor");
const currency = computed(() => task.value?.budget?.currency || "KES");
const heading = computed(() => (isSuccessor.value ? __("Review allocation changes") : __("Review registered allocation")));
const statusLabel = computed(() => {
	const v = task.value?.version;
	if (!v) return "";
	if (v.status === "Submitted for approval") return isSuccessor.value && task.value.revision_type ? `${task.value.revision_type} · ${__("Awaiting review")}` : __("Awaiting review");
	if (v.status === "Active") return __("Approved and activated");
	if (v.status === "Draft") return __("Returned for correction");
	return v.status;
});
const statusClass = computed(() => {
	const s = task.value?.version?.status;
	return s === "Active" ? "is-live" : s === "Draft" ? "is-attention" : "is-pending";
});
const approveLabel = computed(() => (isSuccessor.value ? __("Approve allocation update") : __("Approve registered allocation")));
const consequence = computed(() =>
	isSuccessor.value
		? __("Approval makes these registered amounts current in KenTender. Existing reservations and commitments remain in place. This does not release cash.")
		: __("Approval makes this recorded allocation current for KenTender procurement control. It does not approve the public budget or release cash.")
);
const breach = computed(() => (task.value?.blockers || []).find((b) => b.rule === "BUDGET_REVISION_FLOOR_BREACH"));
const otherBlockers = computed(() => (task.value?.blockers || []).filter((b) => b.rule !== "BUDGET_REVISION_FLOOR_BREACH"));
const showFooter = computed(() => !!task.value && (task.value.capabilities.can_return || task.value.version.status === "Submitted for approval") && !task.value.capabilities.is_technical_reader);
const canApprove = computed(() => !!task.value?.capabilities.can_approve);
const approveReason = computed(() => {
	if (!task.value || canApprove.value) return "";
	if (task.value.protection?.unavailable) return __("The live funding position could not be checked.");
	if (breach.value) return __("The update does not cover the amount already reserved or committed.");
	if (otherBlockers.value.length) return otherBlockers.value[0].message;
	return "";
});
const isPdf = computed(() => /\.pdf(\?|$)/i.test(task.value?.evidence?.document?.url || ""));

const runner = kentender_core.desk_page.createCommandRunner({ ref }, { onStart: () => ((actingError.value = null), (stale.value = false)), onError: (e) => (actingError.value = (e && e.message) || __("We could not confirm the result. Checking the existing request…")), mintKey: (l) => mintKey(l) });
const busy = runner.pending;

function applyTyped(result) {
	if (result.code === "BUDGET_STALE_WRITE" || result.code === "BUDGET_INVALID_STATE") {
		stale.value = true;
		actingError.value = Object.values(result.errors || {}).join(" ");
		return;
	}
	if (result.blockers) {
		actingError.value = result.blockers.map((b) => b.message).join(" ");
		return;
	}
	actingError.value = Object.values(result.errors || {}).join(" ") || __("The decision could not be recorded.");
}

async function openReturn() {
	returnReason.value = "";
	returnOpen.value = true;
	await nextTick();
	returnInput.value?.focus();
}
const returnValid = computed(() => returnReason.value.trim().length >= 10 && returnReason.value.trim().length <= 500);
function submitReturn() {
	if (!returnValid.value) return;
	returnOpen.value = false;
	return runner.run(async (key) => {
		const result = await returnBudgetVersion(versionIdParam.value, returnReason.value.trim(), task.value.version.modified, key);
		if (!result.ok) return applyTyped(result);
		frappe.show_alert({ message: __("Returned for correction"), indicator: "orange" });
		await load({ quiet: true });
	}, "return");
}
// One decision, no repeat confirmation (§11.8): the footer button runs the command.
function approve() {
	return runner.run(async (key) => {
		let result;
		try {
			result = await approveBudgetVersion(versionIdParam.value, task.value.version.modified, key);
		} catch (e) {
			actingError.value = __("We could not confirm the result. Checking the existing request…");
			result = await approveBudgetVersion(versionIdParam.value, task.value.version.modified, key);
			actingError.value = null;
		}
		if (!result.ok) {
			applyTyped(result);
			await load({ quiet: true });
			return;
		}
		frappe.show_alert({ message: isSuccessor.value ? __("Allocation update approved") : __("Registered allocation approved"), indicator: "green" });
		await load({ quiet: true });
	}, "approve");
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-task" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" :style="{ paddingBottom: showFooter ? '96px' : '32px' }">
			<div v-if="loading" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 280px; height: 20px"></div></div>
			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-not-found"><h2>{{ __("This approval task could not be found.") }}</h2></div>
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-forbidden"><h2>{{ __(forbidden.heading) }}</h2><p v-if="forbidden.text" class="kt-muted">{{ __(forbidden.text) }}</p></div>
			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty" data-testid="bud-task-server-error"><h2>{{ __("This approval task could not be loaded.") }}</h2><button type="button" class="kt-btn kt-btn-primary" @click="load()">{{ __("Try again") }}</button></div>

			<template v-else-if="task">
				<div class="kt-card kt-blueprint" style="padding: 0">
				<div style="padding: 28px 24px 0">
				<div style="margin-bottom: 20px" data-testid="bud-task-header">
					<div class="kt-eyebrow" style="margin-bottom: 6px">{{ __("FY {0}", [task.budget.fiscal_year.label]) }} · {{ task.budget.title }}</div>
					<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
						<h1 style="margin: 0">{{ heading }}</h1>
						<span class="kt-status" :class="statusClass" data-testid="bud-task-status">{{ statusLabel }}</span>
					</div>
					<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">
						{{ __("Submitted by {0} · {1}", [task.submission.submitted_by || "—", task.submission.submitted_at_display || "—"]) }} · {{ task.version.code }}<template v-if="task.based_on"> · {{ __("Compared with Version {0}", [task.based_on.version_number]) }}</template>
					</p>
				</div>

				<KtErrorBanner :message="actingError" style="margin-bottom: 12px" @dismiss="actingError = null" />
				<div v-if="stale" class="kt-notice is-warning" style="margin-bottom: 12px" data-testid="bud-task-stale">
					<div class="kt-notice-body">{{ __("This budget has changed since you opened it.") }} <a href="#" @click.prevent="load({ quiet: true })">{{ __("Refresh to see the current details") }}</a></div>
				</div>
				<div v-if="task.capabilities.is_technical_reader" class="kt-notice is-info" style="margin-bottom: 12px" data-testid="bud-task-technical">
					<div class="kt-notice-body">{{ __("Read-only technical view. Decisions on this review need the Budget Approver responsibility.") }}</div>
				</div>
				<div v-if="task.decision && task.version.status !== 'Submitted for approval'" class="kt-notice" :class="task.version.status === 'Active' ? 'is-live' : 'is-warning'" style="margin-bottom: 12px" data-testid="bud-task-decided">
					<div class="kt-notice-body">
						<strong>{{ task.version.status === "Active" ? __("Approved and activated by {0}, {1}.", [task.decision.decided_by, task.decision.decided_at_display]) : __("Returned for correction by {0}, {1}.", [task.decision.decided_by, task.decision.decided_at_display]) }}</strong>
						<template v-if="task.decision.return_reason"> {{ task.decision.return_reason }}</template>
					</div>
				</div>

				<div class="kt-tabs" role="tablist" style="margin-bottom: 0">
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'overview'" data-testid="bud-task-tab-overview" @click="switchTab('overview')" @keydown.enter="switchTab('overview')">{{ __("Overview") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'lines'" data-testid="bud-task-tab-lines" @click="switchTab('lines')" @keydown.enter="switchTab('lines')">{{ __("Budget Lines") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'changes'" data-testid="bud-task-tab-changes" @click="switchTab('changes')" @keydown.enter="switchTab('changes')">{{ __("Changes") }}</div>
					<div class="kt-tab" role="tab" tabindex="0" :aria-selected="tab === 'history'" data-testid="bud-task-tab-history" @click="switchTab('history')" @keydown.enter="switchTab('history')">{{ __("History") }}</div>
				</div>
				</div>

				<!-- Live breach banner: outside collapsed sections, on every tab (§11.20). -->
				<div v-if="breach && task.version.status === 'Submitted for approval'" class="kt-notice is-critical" style="margin: 0; border-top: 1px solid var(--kt-color-divider)" data-testid="bud-task-breach">
					<div class="kt-notice-body"><strong>{{ breach.message }}</strong> {{ __("Approval is unavailable until the update covers this amount; you can still return it for correction.") }}</div>
				</div>
				<div v-if="task.protection.unavailable" class="kt-notice is-warning" style="margin: 0; border-top: 1px solid var(--kt-color-divider)" data-testid="bud-task-protection-unavailable">
					<div class="kt-notice-body">{{ __("The live funding position could not be checked. Refresh before deciding; approval is unavailable until it can be checked.") }}</div>
				</div>

				<!-- Overview (BUD-DES-08 / BUD-DES-13) -->
				<template v-if="tab === 'overview'">
					<template v-if="isSuccessor">
						<div style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)">
							<h3 class="kt-card-title" style="margin: 0 0 12px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><path d="M11 18H8a2 2 0 0 1-2-2V9" /></svg>{{ __("What changed") }}</h3>
							<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto; margin-bottom: 12px">
								<table class="kt-table" data-testid="bud-task-changes-table">
									<thead><tr><th>{{ __("Budget line") }}</th><th class="is-num">{{ __("Current allocation") }}</th><th class="is-num">{{ __("Proposed allocation") }}</th><th class="is-num">{{ __("Change") }}</th></tr></thead>
									<tbody>
										<tr v-for="r in task.changes.rows" :key="r.budget_line">
											<td>{{ r.title }} <span v-if="r.omitted" class="kt-tag kt-tag-neutral" style="margin-left: 6px">{{ __("Omitted from this update") }}</span></td>
											<td class="is-num">{{ formatKes(r.current_amount, currency) }}</td>
											<td class="is-num">{{ formatKes(r.proposed_amount, currency) }}</td>
											<td class="is-num">{{ formatSignedKes(r.change, currency) }}</td>
										</tr>
										<tr style="font-weight: 600"><td>{{ __("Total") }}</td><td class="is-num">{{ formatKes(task.changes.total_current, currency) }}</td><td class="is-num">{{ formatKes(task.changes.total_proposed, currency) }}</td><td class="is-num">{{ formatSignedKes(task.changes.total_change, currency) }}</td></tr>
									</tbody>
								</table>
							</div>
							<p style="font-size: 15px; margin: 0" data-testid="bud-task-summary"><strong>{{ task.changes.summary }}</strong></p>
						</div>

						<div style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)">
							<h3 class="kt-card-title" style="margin: 0 0 12px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>{{ __("Amounts already reserved or committed") }}</h3>
							<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto; margin-bottom: 8px">
								<table class="kt-table" data-testid="bud-task-protection-table">
									<thead><tr><th>{{ __("Budget line") }}</th><th class="is-num">{{ __("Reserved + committed") }}</th><th class="is-num">{{ breach ? __("Available after update / Shortfall") : __("Available after update") }}</th></tr></thead>
									<tbody>
										<tr v-for="r in task.protection.rows" :key="r.budget_line">
											<td>{{ r.title }}</td>
											<td class="is-num" :class="{ 'is-zero': !r.protected_amount }">{{ r.protected_amount === null ? __("Unavailable") : formatKes(r.protected_amount, currency) }}</td>
											<td class="is-num" :style="r.breached ? 'color: var(--kt-status-critical)' : ''">
												<template v-if="r.breached">{{ __("Shortfall {0}", [formatKes(r.shortfall, currency)]) }}</template>
												<template v-else-if="r.available_after_update === null">{{ __("Unavailable") }}</template>
												<template v-else>{{ formatKes(r.available_after_update, currency) }}</template>
											</td>
										</tr>
									</tbody>
								</table>
							</div>
							<p class="kt-muted" style="font-size: 12px; margin: 0 0 4px">{{ __("This amount must remain covered.") }}</p>
							<p class="kt-muted" style="font-size: 12px; margin: 0" data-testid="bud-task-live-caption">{{ __("Live funding position · {0}. KenTender checks these amounts again when you approve.", [task.protection.as_at_display]) }}</p>
						</div>
					</template>
					<template v-else>
						<div style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)">
							<h3 class="kt-card-title" style="margin: 0 0 12px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" x2="21" y1="6" y2="6" /><line x1="8" x2="21" y1="12" y2="12" /><line x1="8" x2="21" y1="18" y2="18" /><line x1="3" x2="3.01" y1="6" y2="6" /><line x1="3" x2="3.01" y1="12" y2="12" /><line x1="3" x2="3.01" y1="18" y2="18" /></svg>{{ __("Submitted budget lines") }}</h3>
							<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto">
								<table class="kt-table" data-testid="bud-task-initial-table">
									<thead><tr><th>{{ __("Budget line") }}</th><th>{{ __("Available to") }}</th><th>{{ __("Funding source") }}</th><th class="is-num">{{ __("Submitted amount") }}</th></tr></thead>
									<tbody>
										<tr v-for="r in task.line_details" :key="r.budget_line">
											<td><div>{{ r.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ r.budget_line_code }}</div></td>
											<td>{{ r.available_to }}</td><td>{{ r.funding_source }}</td><td class="is-num">{{ formatKes(r.amount, currency) }}</td>
										</tr>
										<tr style="font-weight: 600"><td>{{ __("Total") }}</td><td>—</td><td>—</td><td class="is-num">{{ formatKes(task.changes.total_proposed, currency) }}</td></tr>
									</tbody>
								</table>
							</div>
						</div>
					</template>

					<ul v-if="otherBlockers.length" class="kt-card kt-blueprint" style="margin: 16px 24px 0; padding: 14px 14px 14px 30px; font-size: 14px" data-testid="bud-task-blockers">
						<li v-for="b in otherBlockers" :key="b.code">{{ b.message }}</li>
					</ul>

					<div style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)" data-testid="bud-task-evidence">
						<h3 class="kt-card-title" style="margin: 0 0 14px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m9 12 2 2 4-4" /></svg>{{ __("External approval") }}</h3>
						<div class="kt-grid-2" style="gap: 16px">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval reference") }}</div><div style="font-size: 14px">{{ task.evidence.approval_reference }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval date") }}</div><div style="font-size: 14px">{{ task.evidence.approval_date_display }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approved allocation") }}</div><div style="font-size: 14px">{{ formatKes(task.evidence.approved_allocation, currency) }}</div></div>
							<div>
								<div class="kt-label" style="margin-bottom: 3px">{{ __("Approval document") }}</div>
								<div style="font-size: 14px; margin-bottom: 8px">{{ task.evidence.document.name || __("No document attached") }}</div>
								<button v-if="task.evidence.document.url" type="button" class="kt-btn kt-btn-secondary" style="font-size: 13px; padding: 6px 12px" data-testid="bud-task-open-document" @click="window.open(task.evidence.document.url, '_blank', 'noopener')">{{ __("Open approval document") }}</button>
							</div>
						</div>
						<div v-if="task.evidence.document.url && docAvailable === false" class="kt-notice is-warning" style="margin-top: 16px" data-testid="bud-task-document-unavailable">
							<div class="kt-notice-body">{{ __("The submitted approval document could not be opened. Try again.") }}</div>
						</div>
						<div v-else-if="task.evidence.document.url && isPdf && docAvailable === true && !docPreviewFailed" style="margin-top: 16px">
							<iframe :src="task.evidence.document.url" :title="task.evidence.document.name" style="width: 100%; height: 420px; border: 1px solid var(--kt-color-divider)" data-testid="bud-task-document-preview" @error="docPreviewFailed = true"></iframe>
						</div>
					</div>

					<div style="padding: 16px 24px; border-top: 1px solid var(--kt-color-divider); display: flex; flex-direction: column; gap: 10px">
						<details class="kt-record" data-testid="bud-task-line-details">
							<summary><div class="kt-record-main"><div class="kt-record-body"><div class="kt-record-title">{{ __("Budget line details") }}</div><div class="kt-record-meta"><span>{{ __("Department and funding source") }}</span></div></div><div class="kt-record-toggle"><span class="when-closed">{{ __("Show") }}</span><span class="when-open">{{ __("Hide") }}</span></div></div></summary>
							<div class="kt-record-detail" style="padding: 0; overflow-x: auto">
								<table class="kt-table">
									<thead><tr><th>{{ __("Budget line") }}</th><th>{{ __("Available to") }}</th><th>{{ __("Funding source") }}</th></tr></thead>
									<tbody>
										<tr v-for="r in task.line_details" :key="r.budget_line"><td><div>{{ r.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ r.budget_line_code }}</div></td><td>{{ r.available_to }}</td><td>{{ r.funding_source }}</td></tr>
									</tbody>
								</table>
							</div>
						</details>
						<details class="kt-record" data-testid="bud-task-submission">
							<summary><div class="kt-record-main"><div class="kt-record-body"><div class="kt-record-title">{{ __("Submission and history") }}</div><div class="kt-record-meta"><span>{{ __("Submitted by {0} · {1}", [task.submission.submitted_by || "—", task.submission.submitted_at_display || "—"]) }}</span></div></div><div class="kt-record-toggle"><span class="when-closed">{{ __("Show") }}</span><span class="when-open">{{ __("Hide") }}</span></div></div></summary>
							<div class="kt-record-detail">
								<table v-if="history" class="kt-table">
									<thead><tr><th>{{ __("When") }}</th><th>{{ __("Event") }}</th><th>{{ __("Actor") }}</th></tr></thead>
									<tbody><tr v-for="row in history.rows" :key="row.id"><td style="white-space: nowrap">{{ row.event_at_display }}</td><td>{{ row.event_type_label }}</td><td>{{ row.actor }}</td></tr></tbody>
								</table>
							</div>
						</details>
					</div>

					<div class="kt-notice is-info" style="margin: 0; border-top: 1px solid var(--kt-color-divider)" data-testid="bud-task-consequence"><div class="kt-notice-body">{{ consequence }}</div></div>
				</template>

				<!-- Budget Lines (BUD-DES-09 / 13) -->
				<template v-else-if="tab === 'lines'">
					<div v-if="!lines" style="padding: 20px 24px; border-top: 1px solid var(--kt-color-divider)"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<div v-else style="border-top: 1px solid var(--kt-color-divider); overflow-x: auto">
						<table class="kt-table" data-testid="bud-task-lines-table">
							<thead>
								<tr>
									<th>{{ __("Budget Line") }}</th><th>{{ __("Available to") }}</th><th>{{ __("Funding source") }}</th>
									<th class="is-num">{{ lines.is_successor ? __("Proposed amount") : __("Submitted amount") }}</th>
									<th v-if="lines.is_successor" class="is-num">{{ __("Reserved + committed") }}</th>
									<th v-if="lines.is_successor" class="is-num">{{ __("Available after update") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="line in lines.rows" :key="line.budget_line">
									<td><div>{{ line.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ line.budget_line_code }}</div></td>
									<td>{{ line.available_to }}</td><td>{{ line.funding_source }}</td>
									<td class="is-num">{{ formatKes(line.amount, currency) }}</td>
									<td v-if="lines.is_successor" class="is-num" :class="{ 'is-zero': !line.protected_amount }">{{ line.protected_amount === null ? __("Unavailable") : formatKes(line.protected_amount, currency) }}</td>
									<td v-if="lines.is_successor" class="is-num" :style="line.breached ? 'color: var(--kt-status-critical)' : ''">{{ line.breached ? __("Shortfall {0}", [formatKes(line.shortfall, currency)]) : line.available_after_update === null ? __("Unavailable") : formatKes(line.available_after_update, currency) }}</td>
								</tr>
								<tr style="font-weight: 600">
									<td>{{ __("Total") }}</td><td>—</td><td>—</td>
									<td class="is-num">{{ formatKes(lines.total_amount, currency) }}</td>
									<td v-if="lines.is_successor" class="is-num">{{ formatKes(lines.total_protected, currency) }}</td>
									<td v-if="lines.is_successor" class="is-num">{{ lines.total_shortfall ? __("Shortfall {0}", [formatKes(lines.total_shortfall, currency)]) : formatKes(lines.total_available_after_update, currency) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</template>

				<!-- Changes (BUD-DES-10 / 13) -->
				<template v-else-if="tab === 'changes'">
					<div v-if="!changes" style="padding: 20px 24px; border-top: 1px solid var(--kt-color-divider)"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<template v-else-if="changes.is_initial_baseline">
						<div style="padding: 22px 24px 16px; border-top: 1px solid var(--kt-color-divider)">
							<h3 class="kt-card-title" style="margin: 0 0 6px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" x2="21" y1="6" y2="6" /><line x1="8" x2="21" y1="12" y2="12" /><line x1="8" x2="21" y1="18" y2="18" /><line x1="3" x2="3.01" y1="6" y2="6" /><line x1="3" x2="3.01" y1="12" y2="12" /><line x1="3" x2="3.01" y1="18" y2="18" /></svg>{{ __("Initial allocation") }}</h3>
							<p class="kt-muted" style="margin: 0">{{ __("Review the complete submitted budget lines.") }}</p>
						</div>
						<div style="overflow-x: auto" data-testid="bud-task-changes-baseline">
							<table class="kt-table">
								<thead><tr><th>{{ __("Budget Line") }}</th><th class="is-num">{{ __("Submitted Version {0}", [task.version.version_number]) }}</th></tr></thead>
								<tbody>
									<tr v-for="row in changes.rows" :key="row.budget_line"><td><div>{{ row.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ row.budget_line_code }}</div></td><td class="is-num">{{ formatKes(row.submitted_amount, currency) }}</td></tr>
									<tr style="font-weight: 600"><td>{{ __("Total") }}</td><td class="is-num">{{ formatKes(changes.total_submitted, currency) }}</td></tr>
								</tbody>
							</table>
						</div>
					</template>
					<template v-else>
						<h3 class="kt-card-title" style="margin: 0; padding: 22px 24px 14px; border-top: 1px solid var(--kt-color-divider); display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><path d="M13 6h3a2 2 0 0 1 2 2v7" /><path d="M11 18H8a2 2 0 0 1-2-2V9" /></svg>{{ __("Changes from Active Version {0}", [task.based_on.version_number]) }}</h3>
						<div style="overflow-x: auto" data-testid="bud-task-changes-diff">
							<table class="kt-table">
								<thead><tr><th>{{ __("Budget Line") }}</th><th class="is-num">{{ __("Active Version {0}", [task.based_on.version_number]) }}</th><th class="is-num">{{ __("Submitted Version {0}", [task.version.version_number]) }}</th><th class="is-num">{{ __("Change") }}</th></tr></thead>
								<tbody>
									<tr v-for="row in changes.rows" :key="row.budget_line"><td><div>{{ row.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ row.budget_line_code }}</div></td><td class="is-num">{{ formatKes(row.active_amount, currency) }}</td><td class="is-num">{{ formatKes(row.submitted_amount, currency) }}</td><td class="is-num">{{ formatSignedKes(row.change, currency) }}</td></tr>
									<tr style="font-weight: 600"><td>{{ __("Total") }}</td><td class="is-num">{{ formatKes(changes.total_active, currency) }}</td><td class="is-num">{{ formatKes(changes.total_submitted, currency) }}</td><td class="is-num">{{ formatSignedKes(changes.total_change, currency) }}</td></tr>
								</tbody>
							</table>
						</div>
						<h3 class="kt-card-title" style="margin: 0; padding: 22px 24px 14px; border-top: 1px solid var(--kt-color-divider); display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z" /><path d="m9 12 2 2 4-4" /></svg>{{ __("External approval changes") }}</h3>
						<div style="overflow-x: auto" data-testid="bud-task-evidence-changes">
							<table class="kt-table">
								<thead><tr><th>{{ __("Evidence") }}</th><th>{{ __("Active Version {0}", [task.based_on.version_number]) }}</th><th>{{ __("Submitted Version {0}", [task.version.version_number]) }}</th></tr></thead>
								<tbody>
									<tr><td>{{ __("Approval reference") }}</td><td>{{ changes.evidence_changes.approval_reference.from }}</td><td :style="changes.evidence_changes.approval_reference.changed ? 'font-weight: 600' : ''">{{ changes.evidence_changes.approval_reference.to }}</td></tr>
									<tr><td>{{ __("Approval date") }}</td><td>{{ changes.evidence_changes.approval_date.from }}</td><td :style="changes.evidence_changes.approval_date.changed ? 'font-weight: 600' : ''">{{ changes.evidence_changes.approval_date.to }}</td></tr>
									<tr><td>{{ __("Approval document") }}</td><td>{{ changes.evidence_changes.document.from }}</td><td :style="changes.evidence_changes.document.changed ? 'font-weight: 600' : ''">{{ changes.evidence_changes.document.to }}</td></tr>
								</tbody>
							</table>
						</div>
						<div style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)">
							<h3 class="kt-card-title" style="margin: 0 0 12px; display: flex; align-items: center; gap: 6px"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>{{ __("Funding impact") }}</h3>
							<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto; margin-bottom: 8px">
								<table class="kt-table">
									<thead><tr><th>{{ __("Budget line") }}</th><th class="is-num">{{ __("Reserved + committed") }}</th><th class="is-num">{{ __("Available after update") }}</th></tr></thead>
									<tbody>
										<tr v-for="r in changes.protection.rows" :key="r.budget_line"><td>{{ r.title }}</td><td class="is-num" :class="{ 'is-zero': !r.protected_amount }">{{ r.protected_amount === null ? __("Unavailable") : formatKes(r.protected_amount, currency) }}</td><td class="is-num" :style="r.breached ? 'color: var(--kt-status-critical)' : ''">{{ r.breached ? __("Shortfall {0}", [formatKes(r.shortfall, currency)]) : r.available_after_update === null ? __("Unavailable") : formatKes(r.available_after_update, currency) }}</td></tr>
									</tbody>
								</table>
							</div>
							<p class="kt-muted" style="font-size: 12px; margin: 0">{{ __("Live funding position · {0}.", [changes.protection.as_at_display]) }}</p>
						</div>
					</template>
				</template>

				<!-- History (BUD-DES-11 / 13) -->
				<template v-else-if="tab === 'history'">
					<div v-if="!history" style="padding: 20px 24px; border-top: 1px solid var(--kt-color-divider)"><div class="kt-skel" style="width: 240px; height: 16px"></div></div>
					<div v-else style="padding: 22px 24px; border-top: 1px solid var(--kt-color-divider)" data-testid="bud-task-history-table">
						<h3 class="kt-card-title">{{ __("Version history") }}</h3>
						<div class="kt-timeline">
							<div v-for="(row, i) in history.rows" :key="row.id" class="kt-timeline-row">
								<div class="kt-timeline-dot-col"><i class="kt-timeline-dot is-live"></i><i v-if="i < history.rows.length - 1" class="kt-timeline-line"></i></div>
								<div class="kt-timeline-item"><div class="kt-timeline-item-title">{{ row.event_type_label }}</div><div class="kt-timeline-item-meta">{{ row.event_at_display }} · {{ row.actor }}</div></div>
							</div>
						</div>
					</div>
				</template>
				</div>
			</template>
		</div>

		<div v-if="showFooter" class="kt-sticky-footer" data-testid="bud-task-footer">
			<button v-if="task.capabilities.can_return" type="button" class="kt-btn kt-btn-secondary kt-danger" :disabled="busy" data-testid="bud-task-return-btn" @click="openReturn">{{ __("Return for correction") }}</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="busy || !canApprove" :title="approveReason" data-testid="bud-task-approve-btn" @click="approve">{{ approveLabel }}</button>
		</div>

		<div v-if="returnOpen" class="kt-dialog-backdrop" tabindex="-1" @keydown.esc="returnOpen = false">
			<div class="kt-dialog" style="width: 520px" role="dialog" aria-modal="true" :aria-label="__('What needs to change?')" data-testid="bud-task-return-dialog">
				<h2 class="kt-dialog-title">{{ __("What needs to change?") }}</h2>
				<div class="kt-field">
					<label for="bud-task-return-reason">{{ __("Correction required") }}</label>
					<textarea id="bud-task-return-reason" ref="returnInput" v-model="returnReason" class="kt-input" style="width: 100%; height: auto" rows="4" maxlength="500" data-testid="bud-task-return-reason"></textarea>
					<p class="kt-field-hint">{{ __("10–500 characters. The Officer sees this reason on the returned draft; the submitted attempt and its document are retained.") }}</p>
				</div>
				<div class="kt-dialog-actions">
					<button type="button" class="kt-btn kt-btn-ghost" @click="returnOpen = false">{{ __("Cancel") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="!returnValid" data-testid="bud-task-return-confirm" @click="submitReturn">{{ __("Return for correction") }}</button>
				</div>
			</div>
		</div>
	</div>
</template>
