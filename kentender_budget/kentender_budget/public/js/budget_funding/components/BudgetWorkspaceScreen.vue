<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { useWorkingContext } from "../../budget_shared/composables/useWorkingContext.js";
import WorkingContextPicker from "../../budget_shared/components/WorkingContextPicker.vue";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import { getBudgetWorkspace } from "../data/budgetApi.js";

const { go } = useRouteState("budget-funding");

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding") },
]);
const railEl = ref(null);
// CTX-CHG-001 - the rail hosts the global PE switcher; a switch re-resolves
// this module's context under the new entity (its own remembered FY applies).
usePageRail(railEl, railTrail, {
	showPeSwitcher: true,
	onPeChange: async () => {
		loading.value = true;
		await refreshContext();
		if (!selectionRequired.value && workingContext.value) {
			await refresh();
		} else {
			loading.value = false;
		}
	},
});

// BUD-CHG-001 v1.2 Phase 8 — this screen has no explicit id of its own, so
// the PE/FY working context must be resolved (explicit ?context= query
// param, remembered preference, or auto-selected when the actor has
// exactly one) before it can call getBudgetWorkspace at all.
const {
	loading: contextLoading,
	mode: contextMode,
	contexts: workingContexts,
	selected: workingContext,
	selectionRequired,
	refresh: refreshContext,
	select: selectContext,
} = useWorkingContext("budget");

const loading = ref(true);
const forbidden = ref(false);
const serverError = ref(false);
const workspace = ref(null);

async function refresh() {
	loading.value = true;
	forbidden.value = false;
	serverError.value = false;
	try {
		workspace.value = await getBudgetWorkspace(workingContext.value.context_id);
	} catch (e) {
		if (e.httpStatus === 403) {
			forbidden.value = true;
		} else {
			serverError.value = true;
		}
	} finally {
		loading.value = false;
	}
}

async function initContext() {
	const requestedContext = new URLSearchParams(window.location.search).get("context") || undefined;
	await refreshContext(requestedContext);
	if (!selectionRequired.value && workingContext.value) {
		await refresh();
	} else {
		loading.value = false;
	}
}
onMounted(initContext);

async function onSelectContext(contextId) {
	// Set loading before awaiting anything — selectContext() itself flips
	// selectionRequired to false as soon as it resolves, and without this
	// the template's next re-render can land in the gap between
	// "selectionRequired is now false" and "refresh() has set loading back
	// to true", reading workspace.has_budget while workspace is still null
	// (confirmed live: a real TypeError, not hypothetical).
	loading.value = true;
	await selectContext(contextId);
	await refresh();
}

function openBudget() {
	go(workspace.value.budget.code);
}
function openLine(line) {
	go("line", line.code);
}
function openPending() {
	const pending = workspace.value.pending_version;
	if (pending.action === "open_task") go("review", pending.id);
	// Budget Version references are deterministic (§15.3: "{budget_reference}-V{n}")
	// — build the editor route from the Budget's own code, not the pending
	// version's id, which belongs in the review route above instead.
	else go(workspace.value.budget.code, "version", pending.version_number, "edit");
}
function registerBudget() {
	go("new");
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div class="kt-shell">
			<header style="margin-bottom: 4px">
				<span class="kt-eyebrow">{{ __("BUDGET & FUNDING") }}</span>
				<h1 style="margin: 0 0 8px 0; font-size: 32px">{{ __("Budget & Funding") }}</h1>
				<p class="kt-muted" style="margin: 0; max-width: 70ch">
					{{ __("View the approved procurement budget and the funding position used by Procurement Planning.") }}
				</p>
			</header>

			<div style="display: flex; gap: 40px; padding-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
				<div>
					<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Procuring Entity") }}</div>
					<div style="font-size: 15px; font-weight: 500">{{ workspace?.procuring_entity?.name || "—" }}</div>
				</div>
				<div>
					<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Financial Year") }}</div>
					<div style="font-size: 15px; font-weight: 500">{{ workspace?.financial_year?.label || "—" }}</div>
				</div>
				<div>
					<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Currency") }}</div>
					<div style="font-size: 15px; font-weight: 500">{{ workspace?.budget?.currency || "KES" }}</div>
				</div>
			</div>

			<!-- Working-context selection (BUD-CHG-001 v1.2 Phase 8) — precedes
			     every other state; the screen below can't resolve anything
			     without a PE/FY context first. -->
			<WorkingContextPicker
				v-if="contextLoading || selectionRequired || contextMode === 'none'"
				:loading="contextLoading"
				:mode="contextMode"
				:contexts="workingContexts"
				:selected="workingContext"
				@select="onSelectContext"
			/>

			<!-- Loading (BUD-DES-16) -->
			<template v-else-if="loading">
				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-skel" style="width: 280px; height: 20px; margin-bottom: 16px"></div>
					<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px">
						<div v-for="i in 4" :key="i">
							<div class="kt-skel" style="width: 70%; height: 11px; margin-bottom: 8px"></div>
							<div class="kt-skel" style="width: 85%; height: 16px"></div>
						</div>
					</div>
				</div>
				<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px">
					<div v-for="i in 4" :key="i" class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-skel" style="width: 60%; height: 11px; margin-bottom: 10px"></div>
						<div class="kt-skel" style="width: 80%; height: 26px"></div>
					</div>
				</div>
				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-skel" style="width: 140px; height: 16px; margin-bottom: 16px"></div>
					<div v-for="i in 2" :key="i" style="display: flex; gap: 24px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--kt-color-divider)">
						<div class="kt-skel" style="width: 220px; height: 14px"></div>
						<div class="kt-skel" style="width: 140px; height: 14px"></div>
						<div class="kt-skel" style="width: 90px; height: 14px; margin-left: auto"></div>
						<div class="kt-skel" style="width: 90px; height: 14px"></div>
						<div class="kt-skel" style="width: 90px; height: 14px"></div>
						<div class="kt-skel" style="width: 90px; height: 14px"></div>
					</div>
				</div>
			</template>

			<!-- Forbidden (BUD-DES-16) -->
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="5" y="11" width="14" height="10" rx="1" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
				</svg>
				<h2>{{ __("You do not have access to this Budget & Funding context.") }}</h2>
				<p class="kt-muted">{{ __("Ask your KenTender administrator to review your Budget assignment.") }}</p>
			</div>

			<!-- Server error (BUD-DES-16) -->
			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: oklch(0.45 0.13 28)">
					<path d="M12 9v4" /><path d="M12 17h.01" /><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
				</svg>
				<h2>{{ __("Budget & Funding could not be loaded.") }}</h2>
				<p class="kt-muted">{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
				<button type="button" class="kt-btn kt-btn-primary" @click="refresh">{{ __("Try again") }}</button>
			</div>

			<!-- No baseline (BUD-DES-16) -->
			<div v-else-if="!workspace.has_budget" class="kt-card kt-blueprint kt-empty" data-testid="budget-no-baseline">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9h18" /><path d="M8 2v4" /><path d="M16 2v4" />
				</svg>
				<h2>{{ __("No approved procurement budget is registered for {0}.", [workspace.financial_year?.label || "—"]) }}</h2>
				<p class="kt-muted">{{ __("Register the externally approved budget before Procurement Planning requests funding confirmation.") }}</p>
				<button v-if="workspace.can_register" type="button" class="kt-btn kt-btn-primary" @click="registerBudget" data-testid="budget-register-btn">
					{{ __("Register approved budget") }}
				</button>
			</div>

			<!-- Budget exists but nothing Active yet — no artboard covers this
			     directly; reuses the empty-state shell with a status-appropriate
			     action instead of "Register" (registering again would violate
			     the one-Budget-per-PE/FY rule). A Viewer never sees this branch:
			     the server omits pending_version entirely for them, so they fall
			     through to the "No baseline" branch above instead. -->
			<div v-else-if="!workspace.version" class="kt-card kt-blueprint kt-empty" data-testid="budget-pending-draft">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9h18" /><path d="M8 2v4" /><path d="M16 2v4" />
				</svg>
				<h2>{{ __("A Draft budget is in progress for {0}.", [workspace.financial_year?.label || "—"]) }}</h2>
				<p class="kt-muted">{{ __("Continue the draft before it can go Active.") }}</p>
				<button
					v-if="workspace.pending_version"
					type="button"
					class="kt-btn kt-btn-primary"
					@click="openPending"
					data-testid="budget-pending-action-btn"
				>
					{{ workspace.pending_version.action === "open_task" ? __("Open task") : __("Open draft") }}
				</button>
			</div>

			<!-- Active (BUD-DES-01) -->
			<template v-else>
				<div class="kt-card kt-blueprint" data-testid="budget-summary-card">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px">
						<div style="display: flex; align-items: center; gap: 12px">
							<h3 style="margin: 0">{{ workspace.budget.title }}</h3>
							<span class="kt-status is-live">{{ workspace.version.status }}</span>
						</div>
						<button type="button" class="kt-btn kt-btn-secondary" @click="openBudget" data-testid="budget-view-btn">
							{{ __("View budget") }}
						</button>
					</div>
					<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px">
						<div>
							<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Budget reference") }}</div>
							<div style="font-size: 14px; font-weight: 500">{{ workspace.budget.code }}</div>
						</div>
						<div>
							<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Active version") }}</div>
							<div style="font-size: 14px; font-weight: 500">{{ __("Version {0}", [workspace.version.version_number]) }}</div>
						</div>
						<div>
							<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval reference") }}</div>
							<div style="font-size: 14px; font-weight: 500">{{ workspace.version.approval_reference }}</div>
						</div>
						<div>
							<div class="kt-eyebrow" style="margin-bottom: 4px">{{ __("Approval date") }}</div>
							<div style="font-size: 14px; font-weight: 500">{{ workspace.version.approval_date_display }}</div>
						</div>
					</div>
				</div>

				<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px" data-testid="budget-position-cards">
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Approved") }}</div>
						<div class="kt-figure" style="font-size: 26px">{{ formatKes(workspace.positions.approved, workspace.budget.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Reserved") }}</div>
						<div class="kt-figure is-attention" style="font-size: 26px">{{ formatKes(workspace.positions.reserved, workspace.budget.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Committed") }}</div>
						<div class="kt-figure" style="font-size: 26px; color: #1d4ed8">{{ formatKes(workspace.positions.committed, workspace.budget.currency) }}</div>
					</div>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div class="kt-eyebrow">{{ __("Available") }}</div>
						<div class="kt-figure is-live" style="font-size: 26px">{{ formatKes(workspace.positions.available, workspace.budget.currency) }}</div>
					</div>
				</div>

				<div class="kt-card kt-blueprint">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Budget Lines") }}</div>
					<table class="kt-table" data-testid="budget-lines-preview">
						<thead>
							<tr>
								<th>{{ __("Budget Line") }}</th>
								<th>{{ __("Owner scope") }}</th>
								<th style="text-align: right">{{ __("Approved") }}</th>
								<th style="text-align: right">{{ __("Reserved") }}</th>
								<th style="text-align: right">{{ __("Committed") }}</th>
								<th style="text-align: right">{{ __("Available") }}</th>
								<th></th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="line in workspace.lines_preview" :key="line.id">
								<td>
									<div>{{ line.title }}</div>
									<div class="kt-muted" style="font-size: 12px; margin-top: 2px">{{ line.code }}</div>
								</td>
								<td>{{ line.owner_org_unit }}</td>
								<td style="text-align: right">{{ formatKes(line.approved, workspace.budget.currency) }}</td>
								<td style="text-align: right">{{ formatKes(line.reserved, workspace.budget.currency) }}</td>
								<td style="text-align: right">{{ formatKes(line.committed, workspace.budget.currency) }}</td>
								<td style="text-align: right">{{ formatKes(line.available, workspace.budget.currency) }}</td>
								<td style="text-align: right">
									<a href="#" style="font-size: 13px; font-weight: 500; text-decoration: none" @click.prevent="openLine(line)">{{ __("View") }}</a>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</div>
	</div>
</template>
