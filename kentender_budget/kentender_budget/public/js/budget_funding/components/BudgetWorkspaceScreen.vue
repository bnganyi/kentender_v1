<script setup>
import { ref, computed, onActivated, onMounted } from "vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { useFiscalYearFilter } from "../../budget_shared/composables/useFiscalYearFilter.js";
import { formatKes } from "../../budget_shared/data/formatKes.js";
import { getBudgetWorkspace } from "../data/budgetApi.js";

const { go } = useRouteState("budget-funding");

const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding") },
]);
const railEl = ref(null);
// BUD-CHG-001 v1.3 Phase 4/7 — one site is one Procuring Entity: no global
// PE switcher on this rail any more.
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const fyFilter = useFiscalYearFilter();

const loading = ref(true);
const forbidden = ref(null);
const serverError = ref(false);
const workspace = ref(null);
let refreshSeq = 0;

async function refresh(opts) {
	const quiet = !!(opts && opts.quiet === true);
	const seq = ++refreshSeq;
	if (!quiet) loading.value = true;
	forbidden.value = null;
	serverError.value = false;
	try {
		const result = await getBudgetWorkspace(fyFilter.selected.value);
		if (seq !== refreshSeq) return;
		if (result && result.outcome === "FORBIDDEN") {
			workspace.value = null;
			forbidden.value = result.forbidden;
		} else {
			workspace.value = result;
		}
	} catch (e) {
		if (seq === refreshSeq) serverError.value = true;
	} finally {
		if (seq === refreshSeq) loading.value = false;
	}
}

onMounted(async () => {
	// KT-STD-001 v1.2 §3A.1 — the Forbidden verdict is resolved from the same
	// first call as everything else, whether or not a Fiscal Year is already
	// selected, so it renders before the fiscal-year selector itself.
	await Promise.all([fyFilter.load(), refresh()]);
});

// KeepAlive brings this instance back with its rows still on screen; the
// year may have been changed on the editor screen (shared filter), so
// re-read it and revalidate in place. The first activation is the mount.
let activations = 0;
onActivated(async () => {
	if (activations++ === 0) return;
	await fyFilter.load();
	refresh({ quiet: true });
});

async function onSelectFy(fy) {
	fyFilter.select(fy);
	if (!fy) {
		workspace.value = null;
		return;
	}
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
				<p class="kt-page-lede">
					{{ __("View the registered procurement budget and the funding position used by Procurement Planning.") }}
				</p>
			</header>

			<!-- Filter row (BUD-DES-01) — a local view filter, never a gate: it
			     grants nothing and is remembered only with this visible reset. -->
			<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 16px; margin-bottom: 16px; border-bottom: 1px solid var(--kt-color-divider)">
				<label class="kt-field-label" style="margin: 0" for="bud-ws-fy">{{ __("Fiscal Year") }}</label>
				<select
					id="bud-ws-fy"
					class="kt-input"
					style="width: auto; min-width: 160px"
					:disabled="fyFilter.loading.value"
					:value="fyFilter.selected.value"
					data-testid="budget-fy-filter"
					@change="onSelectFy($event.target.value)"
				>
					<option value="" disabled>{{ __("Select a fiscal year") }}</option>
					<option v-for="fy in fyFilter.fiscalYears.value" :key="fy" :value="fy">{{ fy }}</option>
				</select>
			</div>

			<!-- Loading (BUD-DES-16) -->
			<template v-if="loading">
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
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-forbidden">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="5" y="11" width="14" height="10" rx="1" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
				</svg>
				<h2>{{ __(forbidden.heading) }}</h2>
				<p class="kt-muted">{{ __(forbidden.text) }}</p>
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

			<!-- No fiscal year selected yet — never auto-picked (§12.1). -->
			<div v-else-if="!fyFilter.selected.value" class="kt-card kt-blueprint kt-empty" data-testid="budget-select-fy">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<h2>{{ __("Select a fiscal year to view its procurement budget.") }}</h2>
			</div>

			<!-- No baseline (BUD-DES-16) -->
			<div v-else-if="!workspace.has_budget" class="kt-card kt-blueprint kt-empty" data-testid="budget-no-baseline">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9h18" /><path d="M8 2v4" /><path d="M16 2v4" />
				</svg>
				<h2>{{ __("No approved procurement budget is registered for {0}.", [workspace.fiscal_year?.label || "—"]) }}</h2>
				<p class="kt-muted">{{ __("Register the externally approved budget before Procurement Planning requests funding confirmation.") }}</p>
				<button v-if="workspace.can_register" type="button" class="kt-btn kt-btn-primary" @click="registerBudget" data-testid="budget-register-btn">
					{{ __("Register approved budget") }}
				</button>
			</div>

			<!-- Budget exists but nothing Active yet — no artboard covers this
			     directly; reuses the empty-state shell with a status-appropriate
			     action instead of "Register" (registering again would violate
			     the one-Budget-per-fiscal-year rule). A reader with no edit/
			     approve capability never sees this branch: the server omits
			     pending_version entirely for them, so they fall through to the
			     "No baseline" branch above instead. -->
			<div v-else-if="!workspace.version" class="kt-card kt-blueprint kt-empty" data-testid="budget-pending-draft">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--kt-color-accent-800)">
					<rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9h18" /><path d="M8 2v4" /><path d="M16 2v4" />
				</svg>
				<h2>{{ __("A Draft budget is in progress for {0}.", [workspace.fiscal_year?.label || "—"]) }}</h2>
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

<style scoped>
.kt-field-label {
	font-size: 12px;
	color: color-mix(in srgb, var(--kt-color-text) 70%, transparent);
}
</style>
