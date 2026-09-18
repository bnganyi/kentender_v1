<script setup>
import { ref, computed, onActivated, onMounted, watch } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { useFiscalYearFilter } from "../../budget_shared/composables/useFiscalYearFilter.js";
import { formatKes, mintKey } from "../../budget_shared/data/formatKes.js";
import KtErrorBanner from "./KtErrorBanner.vue";
import { getBudgetWorkspace, createBudgetSuccessorVersion } from "../data/budgetApi.js";

// BUD-UI-01 — BUD-DES-01 / 01A / 01B / 16 (BUD-CHG-001 v1.9 §11.1, §11.1A,
// §11.1B, §11.16, §12.1). The server decides the state and the permitted
// actions; this screen only composes them.
const { go, epoch } = useRouteState("budget-funding");

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding") },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const fyFilter = useFiscalYearFilter();
const guard = kentender_core.desk_page.createSequenceGuard();

const loading = ref(true);
const refreshing = ref(false);
const forbidden = ref(null);
const serverError = ref(false);
const workspace = ref(null);
const actingError = ref(null);

async function refresh(opts) {
	const quiet = !!(opts && opts.quiet === true) && !!workspace.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	forbidden.value = null;
	serverError.value = false;
	try {
		const result = await getBudgetWorkspace(fyFilter.selected.value);
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "FORBIDDEN") {
			workspace.value = null;
			forbidden.value = result.forbidden;
		} else if (result && result.selection_required) {
			workspace.value = null;
		} else {
			workspace.value = result;
		}
	} catch (e) {
		if (guard.isCurrent(token)) serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

onMounted(async () => {
	// The remembered Fiscal Year must be known before the first workspace
	// call (§12.1: the filter is remembered only with a visible reset).
	await fyFilter.load();
	await refresh();
});
let activations = 0;
onActivated(async () => {
	if (activations++ === 0) return;
	await fyFilter.load();
	refresh({ quiet: true });
});
watch(epoch, () => refresh({ quiet: true }));

async function onSelectFy(fy) {
	fyFilter.select(fy);
	if (!fy) {
		workspace.value = null;
		return;
	}
	await refresh();
}

const state = computed(() => workspace.value?.state || "");
const pending = computed(() => workspace.value?.pending_version || null);
const actions = computed(() => workspace.value?.available_actions || []);
const currency = computed(() => workspace.value?.budget?.currency || "KES");
const hasCurrent = computed(() => !!workspace.value?.version);
const isClosed = computed(() => state.value === "closed");
const canRecord = computed(() => actions.value.includes("record_allocation"));

const ACTION_LABELS = {
	record_allocation: __("Record approved allocation"),
	continue_draft: __("Continue draft"),
	view_draft: __("View draft"),
	view_submission: __("View submission"),
	review: __("Review"),
	continue_update: __("Continue update"),
	correct_and_resubmit: __("Correct and resubmit"),
	view_version_readonly: __("View version (read-only)"),
	view_budget: __("View budget"),
	update_allocation: __("Update registered allocation"),
};

// §11.1B — the main message per state; the server's action is the button.
const pendingCopy = computed(() => {
	const p = pending.value;
	const fy = workspace.value?.fiscal_year?.label || "";
	if (!p) return null;
	if (p.is_returned) {
		return {
			heading: __("Changes requested"),
			status: __("Draft"),
			statusClass: "is-attention",
			body: p.is_successor
				? __("Correct the returned update and submit it again. The current allocation stays in use; the earlier submission and its document are retained.")
				: __("Correct the returned allocation and submit it again. The earlier submission and its document are retained."),
			whoLabel: __("Submitted by"),
			whenLabel: __("Returned"),
			when: p.return?.at_display || "",
		};
	}
	if (p.status === "Submitted for approval") {
		return {
			heading: p.is_successor ? __("Allocation update awaiting Budget Approver review") : __("Awaiting Budget Approver review"),
			status: __("Submitted for approval"),
			statusClass: "is-pending",
			body: p.is_successor
				? __("The current allocation stays in use. Version {0} is read-only until the Budget Approver decides it.", [p.version_number])
				: __("No allocation is current in KenTender yet. The submitted allocation is read-only until the Budget Approver decides it."),
			whoLabel: __("Submitted by"),
			whenLabel: __("Submitted"),
			when: p.submitted_at_display || "",
		};
	}
	return {
		heading: p.is_successor ? __("Update in progress") : __("Allocation draft"),
		status: __("Draft"),
		statusClass: "is-draft",
		body: p.is_successor
			? __("The current allocation stays in use until this update is approved.")
			: __("Continue recording the approved allocation for FY {0}. No allocation is current in KenTender yet.", [fy]),
		whoLabel: __("Created by"),
		whenLabel: __("Last saved"),
		when: p.last_saved_display || "",
	};
});
const pendingAction = computed(() => (pending.value ? pending.value.action : null));
const pendingActionLabel = computed(() => (pendingAction.value ? ACTION_LABELS[pendingAction.value] : ""));
const pendingIsPrimary = computed(() => ["continue_draft", "correct_and_resubmit", "review"].includes(pendingAction.value));

const updating = ref(false);
async function runAction(action) {
	const ws = workspace.value;
	const p = ws?.pending_version;
	actingError.value = null;
	if (action === "record_allocation") return go("new");
	if (action === "view_budget") return go(ws.budget.code);
	if (action === "review" && p) return go("review", p.id);
	if (action === "update_allocation") return updateAllocation();
	if (p) return go(ws.budget.code, "version", String(p.version_number), "edit");
}

// §12.3 — one server-side copy of the Active Version; a second open
// successor is refused and the existing route is returned instead.
async function updateAllocation() {
	if (updating.value) return;
	updating.value = true;
	try {
		const result = await createBudgetSuccessorVersion(workspace.value.budget.code, { revision_type: "Transfer", idempotency_key: mintKey("successor") });
		if (result.ok) {
			go(workspace.value.budget.code, "version", String(result.version.version_number), "edit");
			return;
		}
		if (result.route) {
			go(...result.route.slice(1));
			return;
		}
		actingError.value = Object.values(result.errors || {}).join(" ") || __("Could not start the update.");
	} catch (e) {
		actingError.value = e.message || String(e);
	} finally {
		updating.value = false;
	}
}

function openLine(line) {
	go("line", line.code);
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-ws" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>

		<!-- BUD-DES-16 Forbidden: only the inline panel — no header, filter or protected content painted. -->
		<div v-if="!loading && forbidden" class="kt-shell">
			<div class="kt-card kt-blueprint kt-empty" data-testid="bud-forbidden">
				<h2>{{ __(forbidden.heading) }}</h2>
				<p class="kt-muted">{{ __(forbidden.text) }}</p>
			</div>
		</div>

		<div v-else class="kt-shell">
			<!-- Loading (BUD-DES-16): plain header, one skeleton current-budget card, four position cards, two rows. -->
			<template v-if="loading">
				<header style="margin-bottom: 4px">
					<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
					<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
					<p class="kt-page-lede">{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}</p>
				</header>
				<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
					<label class="kt-label" style="margin: 0" for="bud-ws-fy">{{ __("Financial year") }}</label>
					<select id="bud-ws-fy" class="kt-input" style="width: auto; min-width: 160px" :disabled="fyFilter.loading.value" :value="fyFilter.selected.value" data-testid="budget-fy-filter" @change="onSelectFy($event.target.value)">
						<option value="" disabled>{{ __("Select a financial year") }}</option>
						<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
					</select>
				</div>
				<div class="kt-card kt-blueprint" data-testid="bud-ws-skeleton">
					<div class="kt-skel" style="width: 300px; height: 16px; margin-bottom: 14px"></div>
					<div class="kt-skel" style="width: 200px; height: 12px"></div>
				</div>
				<div class="kt-kpi-row" style="margin-bottom: 16px">
					<div v-for="i in 4" :key="i" class="kt-kpi-card"><div class="kt-skel" style="width: 70%; height: 14px"></div></div>
				</div>
				<div class="kt-card kt-blueprint">
					<div class="kt-skel" style="height: 14px; margin-bottom: 16px"></div>
					<div class="kt-skel" style="height: 14px"></div>
				</div>
			</template>

			<!-- Server error (BUD-DES-16) — plain header, simple centered card. -->
			<template v-else-if="serverError">
				<header style="margin-bottom: 4px">
					<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
					<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
					<p class="kt-page-lede">{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}</p>
				</header>
				<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
					<label class="kt-label" style="margin: 0" for="bud-ws-fy">{{ __("Financial year") }}</label>
					<select id="bud-ws-fy" class="kt-input" style="width: auto; min-width: 160px" :disabled="fyFilter.loading.value" :value="fyFilter.selected.value" data-testid="budget-fy-filter" @change="onSelectFy($event.target.value)">
						<option value="" disabled>{{ __("Select a financial year") }}</option>
						<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
					</select>
				</div>
				<div class="kt-card kt-blueprint kt-empty" data-testid="bud-ws-server-error">
					<h2>{{ __("Budget & Funding could not be loaded.") }}</h2>
					<p class="kt-muted">{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
					<button type="button" class="kt-btn kt-btn-primary" @click="refresh()">{{ __("Try again") }}</button>
				</div>
			</template>

			<!-- No financial year selected yet — never auto-picked (§12.1). Plain header, the picker is the content. -->
			<template v-else-if="!fyFilter.selected.value">
				<header style="margin-bottom: 4px">
					<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
					<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
					<p class="kt-page-lede">{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}</p>
				</header>
				<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
					<label class="kt-label" style="margin: 0" for="bud-ws-fy">{{ __("Financial year") }}</label>
					<select id="bud-ws-fy" class="kt-input" style="width: auto; min-width: 160px" :disabled="fyFilter.loading.value" :value="fyFilter.selected.value" data-testid="budget-fy-filter" @change="onSelectFy($event.target.value)">
						<option value="" disabled>{{ __("Select a financial year") }}</option>
						<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
					</select>
				</div>
				<div class="kt-card kt-blueprint kt-empty" data-testid="budget-select-fy">
					<h2>{{ __("Select a financial year to view its procurement budget.") }}</h2>
				</div>
			</template>

			<!-- No record (BUD-DES-16 No baseline) — plain header, the notice is the content. -->
			<template v-else-if="!workspace || state === 'no_record'">
				<header style="margin-bottom: 4px">
					<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
					<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
					<p class="kt-page-lede">{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}</p>
				</header>
				<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
					<label class="kt-label" style="margin: 0" for="bud-ws-fy">{{ __("Financial year") }}</label>
					<select id="bud-ws-fy" class="kt-input" style="width: auto; min-width: 160px" :disabled="fyFilter.loading.value" :value="fyFilter.selected.value" data-testid="budget-fy-filter" @change="onSelectFy($event.target.value)">
						<option value="" disabled>{{ __("Select a financial year") }}</option>
						<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
					</select>
				</div>
				<div class="kt-card kt-blueprint kt-empty" data-testid="budget-no-baseline">
					<h2>{{ __("No procurement allocation has been recorded for FY {0}.", [workspace?.fiscal_year?.label || fyFilter.selected.value]) }}</h2>
					<p class="kt-muted">{{ __("Record the externally approved allocation for this financial year.") }}</p>
					<button v-if="canRecord" type="button" class="kt-btn kt-btn-primary" data-testid="budget-register-btn" @click="runAction('record_allocation')">
						{{ ACTION_LABELS.record_allocation }}
					</button>
				</div>
			</template>

			<!-- Active/pending (BUD-DES-01/01A/01B): header + filter are the FIRST section of the one card, matching the board. -->
			<template v-else>
				<div class="kt-card kt-blueprint" style="padding: 0">
					<div style="padding: 28px 24px 20px; border-bottom: 1px solid var(--kt-color-divider)">
						<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
						<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
						<p class="kt-page-lede" style="margin: 0 0 16px">{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}</p>
						<select id="bud-ws-fy" class="kt-input" style="width: auto; min-width: 160px" :disabled="fyFilter.loading.value" :value="fyFilter.selected.value" data-testid="budget-fy-filter" @change="onSelectFy($event.target.value)">
							<option value="" disabled>{{ __("Select a financial year") }}</option>
							<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
						</select>
						<KtErrorBanner :message="actingError" style="margin-top: 16px; margin-bottom: 0" @dismiss="actingError = null" />
					</div>

					<!-- BUD-DES-01A/01B pending section: initial draft/submission, returned, or an update on a current allocation. -->
					<div v-if="pending && pendingCopy" style="padding: 18px 24px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="budget-pending-card" :data-state="state" :data-action="pendingAction">
						<div style="display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 14px">
							<div style="display: flex; align-items: center; gap: 12px">
								<h2 style="margin: 0; font-size: 19px">{{ pendingCopy.heading }}</h2>
								<span class="kt-status" :class="pendingCopy.statusClass">{{ pendingCopy.status }}</span>
							</div>
							<button type="button" class="kt-btn" :class="pendingIsPrimary ? 'kt-btn-primary' : 'kt-btn-secondary'" data-testid="budget-pending-action-btn" @click="runAction(pendingAction)">
								{{ pendingActionLabel }}
							</button>
						</div>
						<p style="font-size: 14px; margin: 0 0 12px" class="kt-muted">{{ pendingCopy.body }}</p>
						<div v-if="pending.is_returned && pending.return" class="kt-notice is-warning" style="margin-bottom: 12px" data-testid="budget-pending-return">
							<div class="kt-notice-body">
								<strong>{{ __("Changes requested by {0}, {1}.", [pending.return.by, pending.return.at_display]) }}</strong>
								{{ pending.return.reason }}
							</div>
						</div>
						<div class="kt-ws-facts" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px 24px">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Version") }}</div><div style="font-size: 14px">{{ __("Version {0}", [pending.version_number]) }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ pendingCopy.whoLabel }}</div><div style="font-size: 14px">{{ pending.submitted_by || "—" }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ pendingCopy.whenLabel }}</div><div style="font-size: 14px">{{ pendingCopy.when || "—" }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Financial Year") }}</div><div style="font-size: 14px">{{ workspace.fiscal_year.label }}</div></div>
						</div>
					</div>

					<!-- Pending initial work the caller may not read: nothing current, nothing invented. -->
					<div v-if="!hasCurrent && !pending" class="kt-empty" style="padding: 22px 24px" data-testid="budget-pending-hidden">
						<h2>{{ __("No allocation is current in KenTender yet for FY {0}.", [workspace.fiscal_year.label]) }}</h2>
						<p class="kt-muted">{{ __("An allocation record exists for this financial year and is being prepared.") }}</p>
					</div>

					<!-- Current budget section (BUD-DES-01) or the Closed variant (§11.1B). -->
					<template v-if="hasCurrent">
						<div data-testid="budget-summary-card">
							<div style="padding: 20px 24px; border-bottom: 1px solid var(--kt-color-divider)">
							<div style="display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 14px">
								<div style="display: flex; align-items: center; gap: 12px">
									<h2 style="margin: 0; font-size: 19px">{{ workspace.budget.title }}</h2>
									<span class="kt-status" :class="isClosed ? 'is-critical' : 'is-live'">{{ isClosed ? __("Closed") : __("Current") }}</span>
								</div>
								<button type="button" class="kt-btn kt-btn-secondary" data-testid="budget-view-btn" @click="runAction('view_budget')">{{ ACTION_LABELS.view_budget }}</button>
							</div>
							<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px 24px" class="kt-ws-facts">
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Budget reference") }}</div><div style="font-size: 14px">{{ workspace.budget.code }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Current version") }}</div><div style="font-size: 14px">{{ __("Version {0}", [workspace.version.version_number]) }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Currency") }}</div><div style="font-size: 14px">{{ currency }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval reference") }}</div><div style="font-size: 14px">{{ workspace.version.approval_reference }}</div></div>
								<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Approval date") }}</div><div style="font-size: 14px">{{ workspace.version.approval_date_display }}</div></div>
							</div>
							<div v-if="isClosed" class="kt-notice is-info" style="margin-top: 14px" data-testid="budget-closed-note">
								<div class="kt-notice-body">
									<strong>{{ __("Closed by {0}, {1}.", [workspace.closure.closed_by, workspace.closure.closed_at_display]) }}</strong>
									{{ __("No new reservations, conversions or commitment increases. Existing commitments and history remain.") }}
								</div>
							</div>
							<div v-else-if="actions.includes('update_allocation')" style="margin-top: 14px">
								<button type="button" class="kt-btn kt-btn-secondary" data-testid="budget-update-btn" :disabled="updating" @click="runAction('update_allocation')">{{ ACTION_LABELS.update_allocation }}</button>
							</div>
						</div>

						<div style="padding: 20px 24px; border-bottom: 1px solid var(--kt-color-divider)">
							<div class="kt-kpi-row" style="margin-bottom: 8px" data-testid="budget-position-cards">
								<div class="kt-kpi-card">
									<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="3" x2="21" y1="22" y2="22" /><line x1="6" x2="6" y1="18" y2="11" /><line x1="10" x2="10" y1="18" y2="11" /><line x1="14" x2="14" y1="18" y2="11" /><line x1="18" x2="18" y1="18" y2="11" /><polygon points="12 2 20 7 4 7" /></svg>
									<div class="kt-kpi-value">{{ formatKes(workspace.positions.approved, currency) }}</div>
									<div class="kt-kpi-sub">{{ __("Registered allocation") }}</div>
								</div>
								<div class="kt-kpi-card">
									<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" /></svg>
									<div class="kt-kpi-value" :class="{ 'is-zero': !workspace.positions.reserved }">{{ formatKes(workspace.positions.reserved, currency) }}</div>
									<div class="kt-kpi-sub">{{ __("Reserved for requisitions") }}</div>
								</div>
								<div class="kt-kpi-card">
									<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6" /><path d="m9 15 2 2 4-4" /></svg>
									<div class="kt-kpi-value" :class="{ 'is-zero': !workspace.positions.committed }">{{ formatKes(workspace.positions.committed, currency) }}</div>
									<div class="kt-kpi-sub">{{ __("Committed to contracts") }}</div>
								</div>
								<div class="kt-kpi-card" :class="workspace.positions.available > 0 ? 'is-live' : 'is-critical'">
									<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 9.9-1" /></svg>
									<div class="kt-kpi-value">{{ formatKes(workspace.positions.available, currency) }}</div>
									<div class="kt-kpi-sub">{{ __("Available to reserve") }}</div>
								</div>
							</div>
							<p class="kt-muted" style="font-size: 12px; margin: 0" data-testid="budget-position-as-at">{{ __("Funding position as at {0}", [workspace.positions_as_at_display]) }}</p>
						</div>

						<div>
							<h3 class="kt-card-title" style="margin: 0; padding: 20px 20px 4px; display: flex; align-items: center; gap: 6px">
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" x2="21" y1="6" y2="6" /><line x1="8" x2="21" y1="12" y2="12" /><line x1="8" x2="21" y1="18" y2="18" /><line x1="3" x2="3.01" y1="6" y2="6" /><line x1="3" x2="3.01" y1="12" y2="12" /><line x1="3" x2="3.01" y1="18" y2="18" /></svg>
								{{ __("Budget Lines") }}
							</h3>
							<div style="overflow-x: auto">
								<table class="kt-table" data-testid="budget-lines-preview">
									<thead>
										<tr>
											<th>{{ __("Budget Line") }}</th>
											<th>{{ __("Available to") }}</th>
											<th class="is-num">{{ __("Registered allocation") }}</th>
											<th class="is-num">{{ __("Reserved for requisitions") }}</th>
											<th class="is-num">{{ __("Committed to contracts") }}</th>
											<th class="is-num">{{ __("Available to reserve") }}</th>
											<th></th>
										</tr>
									</thead>
									<tbody>
										<tr v-for="line in workspace.lines_preview" :key="line.id">
											<td><div>{{ line.title }}</div><div class="kt-muted" style="font-size: 11px; margin-top: 2px">{{ line.code }}</div></td>
											<td>{{ line.owner_org_unit }}</td>
											<td class="is-num">{{ formatKes(line.approved, currency) }}</td>
											<td class="is-num" :class="{ 'is-zero': !line.reserved }">{{ formatKes(line.reserved, currency) }}</td>
											<td class="is-num" :class="{ 'is-zero': !line.committed }">{{ formatKes(line.committed, currency) }}</td>
											<td class="is-num">{{ formatKes(line.available, currency) }}</td>
											<td><a href="#" @click.prevent="openLine(line)">{{ __("View") }}</a></td>
										</tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>
				</template>
				</div>
			</template>
		</div>
	</div>
</template>

<style scoped>
@media (max-width: 900px) {
	.kt-ws-facts {
		grid-template-columns: 1fr 1fr !important;
	}
}
</style>
