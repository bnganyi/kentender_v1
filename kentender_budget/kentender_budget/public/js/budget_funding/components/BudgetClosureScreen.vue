<script setup>
import { ref, computed, onMounted, onActivated, watch } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatKes, mintKey } from "../../budget_shared/data/formatKes.js";
import { getBudgetClosureStatus, closeBudget } from "../data/budgetApi.js";

// BUD-DES-17 — Close budget on the existing BUD-UI-03 (BUD-CHG-001 v1.9
// §9.4, §11.18, §12.8): before year end, blocked, unavailable, ready,
// confirm, closed. Check again and refresh create no business effect; the
// close command revalidates every guard at commit.
const { route, go, epoch } = useRouteState("budget-funding");
const budgetIdParam = computed(() => route.value[1]);
const status = ref(null);
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: status.value?.budget?.code || budgetIdParam.value, route: ["budget-funding", budgetIdParam.value] },
	{ label: __("Close budget") },
]);
const railEl = ref(null);
usePageRail(railEl, railTrail, { showPeSwitcher: false });

const guard = kentender_core.desk_page.createSequenceGuard();
const loading = ref(true);
const refreshing = ref(false);
const forbidden = ref(null);
const notFound = ref(false);
const serverError = ref(false);
const actingError = ref(null);
const confirmOpen = ref(false);

async function load(opts) {
	const quiet = !!(opts && opts.quiet) && !!status.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	forbidden.value = null;
	notFound.value = false;
	serverError.value = false;
	try {
		const data = await getBudgetClosureStatus(budgetIdParam.value);
		if (!guard.isCurrent(token)) return;
		if (data && data.outcome === "FORBIDDEN") {
			status.value = null;
			forbidden.value = data.forbidden;
			return;
		}
		if (data && data.outcome === "NOT_FOUND") {
			status.value = null;
			notFound.value = true;
			return;
		}
		status.value = data;
	} catch (e) {
		if (guard.isCurrent(token)) serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}
onMounted(load);
watch(budgetIdParam, (v, prev) => v && v !== prev && load());
let activations = 0;
onActivated(() => activations++ > 0 && status.value && load({ quiet: true }));
watch(epoch, () => status.value && load({ quiet: true }));

const runner = kentender_core.desk_page.createCommandRunner({ ref }, { onStart: () => (actingError.value = null), onError: (e) => (actingError.value = (e && e.message) || __("We could not confirm the result. Checking the existing request…")), mintKey: (l) => mintKey(l) });
const busy = runner.pending;
const currency = computed(() => status.value?.currency || "KES");
const state = computed(() => status.value?.state || "");
const fyLabel = computed(() => status.value?.fiscal_year?.label || "");

function confirmClose() {
	confirmOpen.value = false;
	return runner.run(async (key) => {
		let result;
		try {
			result = await closeBudget(budgetIdParam.value, status.value.version.modified, key);
		} catch (e) {
			actingError.value = __("We could not confirm the result. Checking the existing request…");
			result = await closeBudget(budgetIdParam.value, status.value.version.modified, key);
			actingError.value = null;
		}
		if (!result.ok) {
			actingError.value = Object.values(result.errors || {}).join(" ");
			if (result.closure) status.value = { ...status.value, ...result.closure };
			else await load({ quiet: true });
			return;
		}
		frappe.show_alert({ message: __("Budget closed"), indicator: "green" });
		status.value = result.closure;
	}, "close");
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-close" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" style="max-width: 900px">
			<div v-if="loading" class="kt-card kt-blueprint"><div class="kt-skel" style="width: 280px; height: 20px"></div></div>
			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="bud-close-forbidden"><h2>{{ __(forbidden.heading) }}</h2><p class="kt-muted">{{ __(forbidden.text) }}</p></div>
			<div v-else-if="notFound" class="kt-card kt-blueprint kt-empty"><h2>{{ __("This budget could not be found.") }}</h2></div>
			<div v-else-if="serverError" class="kt-card kt-blueprint kt-empty"><h2>{{ __("The funding position could not be checked. Try again before closing this budget.") }}</h2><button type="button" class="kt-btn kt-btn-primary" @click="load()">{{ __("Try again") }}</button></div>

			<template v-else-if="status">
				<h1 style="margin: 0 0 6px" data-testid="bud-close-heading">{{ __("Close budget for FY {0}", [fyLabel]) }}</h1>
				<p class="kt-muted" style="margin: 0 0 20px">{{ status.budget.title }} · {{ status.budget.code }}</p>
				<KtErrorBanner :message="actingError" style="margin-bottom: 12px" @dismiss="actingError = null" />

				<div v-if="state === 'before_year_end'" class="kt-notice is-info" data-testid="bud-close-before" style="margin-bottom: 20px">
					<div class="kt-notice-body">{{ __("This budget can be closed only after {0}.", [status.fiscal_year.end_date_display]) }}</div>
				</div>

				<template v-else-if="state === 'blocked'">
					<div class="kt-notice is-critical" style="margin-bottom: 16px" data-testid="bud-close-blocked">
						<div class="kt-notice-body">
							<strong>{{ __("This budget cannot be closed yet.") }}</strong>
							{{ __("{0} remains reserved for requisitions. Resolve the remaining reservations through their owning Requisition or Contract process, then check again.", [formatKes(status.remaining_total, currency)]) }}
						</div>
					</div>
					<div class="kt-card kt-blueprint" style="padding: 0; overflow-x: auto; margin-bottom: 12px">
						<table class="kt-table" data-testid="bud-close-rows">
							<thead><tr><th>{{ __("Budget line") }}</th><th class="is-num">{{ __("Still reserved") }}</th><th>{{ __("Next step") }}</th></tr></thead>
							<tbody>
								<tr v-for="row in status.rows" :key="row.budget_line">
									<td>{{ row.title }} <span v-if="row.requires_review" class="kt-status is-attention" style="margin-left: 8px">{{ __("Requires review") }}</span></td>
									<td class="is-num">{{ formatKes(row.still_reserved, currency) }}</td>
									<td><a href="#" @click.prevent="go('line', row.budget_line_code)">{{ __("Open the authorised reservation details") }}</a></td>
								</tr>
							</tbody>
						</table>
					</div>
					<p class="kt-muted" style="font-size: 13px; margin: 0 0 20px">{{ __("Funds requiring review still count as reserved. You cannot release them from this screen.") }}</p>
				</template>

				<div v-else-if="state === 'unavailable'" class="kt-notice is-warning" style="margin-bottom: 20px" data-testid="bud-close-unavailable">
					<div class="kt-notice-body">{{ __("The funding position could not be checked. Try again before closing this budget.") }}</div>
				</div>

				<template v-else-if="state === 'ready'">
					<div class="kt-notice is-live" style="margin-bottom: 16px" data-testid="bud-close-ready">
						<div class="kt-notice-body"><strong>{{ __("The financial year has ended and no reservation remains.") }}</strong> {{ __("Closing stops new reservations, conversions and commitment increases. Existing commitments and history remain.") }}</div>
					</div>
					<div class="kt-card kt-blueprint" style="margin-bottom: 20px">
						<h3 class="kt-card-title">{{ __("Funding position") }}</h3>
						<p class="kt-muted" style="font-size: 12px; margin: 0 0 12px">{{ __("As at {0}", [status.as_at_display]) }}</p>
						<div class="kt-grid-3" style="gap: 16px">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Reserved for requisitions") }}</div><div style="font-size: 14px">{{ formatKes(status.remaining_total, currency) }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Committed to contracts") }}</div><div style="font-size: 14px">{{ formatKes(status.active_commitments_total, currency) }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Active commitments") }}</div><div style="font-size: 14px">{{ __("Do not block closure") }}</div></div>
						</div>
					</div>
				</template>

				<div v-else-if="state === 'closed'" class="kt-card kt-blueprint" data-testid="bud-close-closed">
					<h3 class="kt-card-title">{{ __("Closed") }}</h3>
					<div class="kt-grid-3" style="gap: 16px">
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Closed by") }}</div><div style="font-size: 14px">{{ status.closed_by }}</div></div>
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Closed") }}</div><div style="font-size: 14px">{{ status.closed_at_display }}</div></div>
						<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Financial Year") }}</div><div style="font-size: 14px">{{ fyLabel }}</div></div>
					</div>
					<p class="kt-muted" style="font-size: 13px; margin: 12px 0 0">{{ __("No new reservations, conversions or commitment increases. Existing commitments and history remain.") }}</p>
				</div>

				<div style="display: flex; gap: 12px; flex-wrap: wrap">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="bud-close-back" @click="go(budgetIdParam)">{{ __("Back to budget") }}</button>
					<button v-if="state !== 'closed'" type="button" class="kt-btn kt-btn-secondary" data-testid="bud-close-check" :disabled="busy" @click="load({ quiet: true })">{{ __("Check again") }}</button>
					<button v-if="state !== 'closed'" type="button" class="kt-btn kt-btn-primary" data-testid="bud-close-btn" :disabled="busy || state !== 'ready' || !status.can_close" :title="state !== 'ready' ? __('Closure is unavailable until every guard passes') : ''" @click="confirmOpen = true">{{ __("Close budget") }}</button>
				</div>

				<div v-if="confirmOpen" class="kt-dialog-backdrop" tabindex="-1" @keydown.esc="confirmOpen = false">
					<div class="kt-dialog" style="width: 480px" role="dialog" aria-modal="true" data-testid="bud-close-confirm">
						<h2 class="kt-dialog-title">{{ __("Close budget for FY {0}?", [fyLabel]) }}</h2>
						<p style="margin: 0 0 8px">{{ status.budget.title }} · {{ status.budget.code }}</p>
						<p class="kt-muted">{{ __("Closing stops new reservations, conversions and commitment increases. Existing commitments and history remain.") }}</p>
						<div class="kt-dialog-actions">
							<button type="button" class="kt-btn kt-btn-ghost" @click="confirmOpen = false">{{ __("Cancel") }}</button>
							<button type="button" class="kt-btn kt-btn-primary" data-testid="bud-close-confirm-btn" @click="confirmClose">{{ __("Close budget") }}</button>
						</div>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>
