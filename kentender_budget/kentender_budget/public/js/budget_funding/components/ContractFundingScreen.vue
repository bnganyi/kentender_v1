<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import ConfirmDialog from "../../budget_shared/components/ConfirmDialog.vue";
import AccessDenied from "../../budget_shared/components/AccessDenied.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatExact, sumExact, toMinor, fromMinor } from "../../budget_shared/data/formatExact.js";
import { mintKey } from "../../budget_shared/data/formatKes.js";
import { declineContractRequest, decideContractEntry, getContractFunding, recordContractEntry, submitContractEntry } from "../data/budgetApi.js";

// BUD-DES-21 Contract funding (the Officer's preparation) and BUD-DES-22 Review contract funding (the Approver's
// decision), with their variants (BUD-CHG-001 v1.16 §11.22). One screen, one route, because it is one request: the
// server states who has the turn, what each person may do and why not, and this screen draws exactly that. The
// amount requiring funding is the server's calculation and has no editor; the allocation table has Budget line,
// Available, Amount and Remove, with source and year read-only. Typing is bound to this screen's own state, never
// to the server echo, so a refresh in place cannot overwrite what the Officer is typing (AGENTS.md §6.4).
const { route, go, epoch } = useRouteState("budget-funding");
const requestParam = computed(() => route.value[2]);
const view = ref(null);
const reviewing = computed(() => !!(view.value?.entry && view.value.actions.approve !== undefined && view.value.entry.status === "Awaiting approval"));
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	{ label: reviewing.value ? __("Review contract funding") : __("Contract funding") },
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
const fieldErrors = ref({});
const shortfalls = ref([]);

const form = reactive({ rows: [], reconciliation: "" });
const dirty = ref(false);
let loadedEntry = "";
let loadedRevision = "";

const request = computed(() => view.value?.request || null);
const entry = computed(() => view.value?.entry || null);
const actions = computed(() => view.value?.actions || {});
const currency = computed(() => request.value?.currency || "KES");
const eligible = computed(() => view.value?.eligible_lines || []);
const lineById = computed(() => Object.fromEntries(eligible.value.map((l) => [l.id, l])));

async function load(opts) {
	if (!requestParam.value) return;
	const quiet = !!(opts && opts.quiet) && !!view.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	forbidden.value = null;
	notFound.value = false;
	serverError.value = false;
	try {
		const data = await getContractFunding(requestParam.value);
		if (!guard.isCurrent(token)) return;
		view.value = data;
		adopt(data);
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this funding request"), text: "" };
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

// The form takes the saved entry once per entry revision, and never while the person has typed something the server
// has not seen: a revalidating return to this route keeps what is typed.
function adopt(data) {
	const e = data.entry;
	const identity = e ? e.id : "";
	const revision = e ? e.revision : "";
	if (dirty.value && identity === loadedEntry) return;
	if (identity === loadedEntry && revision === loadedRevision) return;
	loadedEntry = identity;
	loadedRevision = revision;
	form.rows = (e ? e.rows : []).map((r) => ({ row_id: r.row_id, budget_line: r.budget_line, amount: r.amount }));
	form.reconciliation = e ? e.reconciliation : "";
	dirty.value = false;
	fieldErrors.value = {};
	shortfalls.value = [];
}

onMounted(load);
watch(requestParam, (v, prev) => v && v !== prev && ((view.value = null), (dirty.value = false), (loadedEntry = ""), load()));
let activations = 0;
onActivated(() => activations++ > 0 && view.value && load({ quiet: true }));
watch(epoch, () => view.value && load({ quiet: true }));

// ---- what the screen says ------------------------------------------------------------------------------------------
const required = computed(() => request.value?.amount_requiring_funding || null);
const total = computed(() => sumExact(form.rows.map((r) => r.amount || "0")));
const remaining = computed(() => (required.value === null ? null : fromMinor(toMinor(required.value) - toMinor(total.value), 100)));
const editable = computed(() => !!actions.value.save);
const status = computed(() => request.value?.display_status || "");
const nextStep = computed(() => {
	const r = request.value;
	if (!r) return "";
	if (r.status === "Completed") return __("Done — {0}", [status.value]);
	if (r.status !== "Open") return status.value;
	if (r.year_allocation_status !== "Confirmed") {
		const w = r.waiting_for || {};
		return w.holder ? __("Waiting for Finance — {0}", [w.holder]) : __("Waiting for Finance");
	}
	if (actions.value.save && required.value) return __("Your turn — Allocate {0} to budget lines", [formatExact(required.value, currency.value)]);
	if (actions.value.approve !== undefined && entry.value?.status === "Awaiting approval") return actions.value.blocked ? __("Waiting on another Budget Approver") : __("Your turn — Review the funding entry");
	return r.holder ? __("Waiting on {0}", [r.holder]) : "";
});
const entryStale = computed(() => !!entry.value?.basis_stale);
const sameBadge = computed(() => (status.value === "Funding shortfall" ? "is-critical" : request.value?.status === "Completed" ? "is-live" : "is-attention"));
const closedMessage = computed(() => {
	const r = request.value;
	if (!r || r.status === "Open") return "";
	if (r.outcome === "Already covered") return __("Already covered — no new entry required");
	if (r.outcome === "No charge to this year") return __("No charge to this year");
	if (r.status === "Declined") return __("This request was declined. {0}", [r.closed_reason || ""]);
	if (r.status === "Withdrawn") return __("Contract Management withdrew this request. {0}", [r.closed_reason || ""]);
	return __("Funding entry approved");
});
const contractRoute = computed(() => (request.value ? `/app/contracts/${encodeURIComponent(request.value.contract)}` : "#"));

function lineTitle(id) {
	return lineById.value[id]?.title || entry.value?.rows.find((r) => r.budget_line === id)?.title || id;
}
function lineAvailable(id) {
	const l = lineById.value[id];
	if (l) return String(l.available);
	return entry.value?.rows.find((r) => r.budget_line === id)?.available ?? null;
}
function shortfallOf(id) {
	return shortfalls.value.find((s) => s.budget_line === id);
}
const unusedLines = computed(() => eligible.value.filter((l) => !form.rows.some((r) => r.budget_line === l.id)));

function touch() {
	dirty.value = true;
}
function addRow() {
	const next = unusedLines.value[0];
	form.rows.push({ row_id: "", budget_line: next ? next.id : "", amount: "" });
	touch();
}
function removeRow(index) {
	form.rows.splice(index, 1);
	touch();
}

// ---- commands ------------------------------------------------------------------------------------------------------
const runner = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			actingError.value = null;
			fieldErrors.value = {};
			shortfalls.value = [];
		},
		onError: (e) => {
			actingError.value = (e && e.message) || __("We could not confirm the result. Checking the existing request…");
		},
		mintKey: (label) => mintKey(label),
	}
);
const acting = runner.pending;

function refusal(result) {
	fieldErrors.value = result.errors || {};
	shortfalls.value = result.shortfalls || [];
	actingError.value = Object.values(result.errors || {}).join(" ") || __("That could not be done.");
	if (result.entry || result.request) load({ quiet: true });
}

function payload(key) {
	return { request: request.value.id, entry: entry.value?.id || "", expected_revision: entry.value?.revision || "", rows: form.rows.map((r) => ({ row_id: r.row_id, budget_line: r.budget_line, amount: r.amount })), reconciliation: form.reconciliation, idempotency_key: key };
}

function saveDraft() {
	return runner.run(async (key) => {
		const result = await recordContractEntry(payload(key));
		if (!result.ok) return refusal(result);
		dirty.value = false;
		loadedRevision = "";
		await load({ quiet: true });
	}, "fund-save");
}

function submit() {
	return runner.run(async (key) => {
		const saved = await recordContractEntry(payload(`${key}-s`));
		if (!saved.ok) return refusal(saved);
		const result = await submitContractEntry({ entry: saved.entry.id, expected_revision: saved.entry.revision, idempotency_key: key });
		if (!result.ok) return refusal(result);
		dirty.value = false;
		loadedRevision = "";
		await load({ quiet: true });
	}, "fund-submit");
}

const declining = ref(false);
function decline(reason) {
	declining.value = false;
	return runner.run(async (key) => {
		const result = await declineContractRequest({ request: request.value.id, reason, idempotency_key: key });
		if (!result.ok) return refusal(result);
		await load({ quiet: true });
	}, "fund-decline");
}

const approving = ref(false);
const returning = ref(false);
function decide(decision, reason) {
	approving.value = false;
	returning.value = false;
	return runner.run(async (key) => {
		const result = await decideContractEntry({ entry: entry.value.id, decision, reason: reason || "", expected_revision: entry.value.revision, idempotency_key: key });
		if (!result.ok) return refusal(result);
		await load({ quiet: true });
	}, `fund-${decision.toLowerCase()}`);
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-funding" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div v-if="!loading && forbidden" class="kt-shell">
			<div class="kt-page" data-testid="bud-funding-forbidden"><AccessDenied :heading="__(forbidden.heading)" :text="__(forbidden.text || '')" /></div>
		</div>
		<div v-else class="kt-shell" style="max-width: 1000px">
			<div v-if="loading" class="card blueprint"><div class="kt-skel" style="width: 320px; height: 20px"></div></div>
			<div v-else-if="notFound" class="card blueprint kt-empty" data-testid="bud-funding-not-found"><h2>{{ __("This funding request could not be found.") }}</h2></div>
			<div v-else-if="serverError" class="card blueprint kt-empty" data-testid="bud-funding-server-error">
				<h2>{{ __("This funding request could not be loaded.") }}</h2>
				<button type="button" class="btn btn-primary" @click="load()">{{ __("Try again") }}</button>
			</div>

			<template v-else-if="request">
				<div class="card blueprint" style="padding: 0">
					<div style="padding: 28px 28px 20px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="bud-funding-header">
						<div class="kt-eyebrow" style="margin-bottom: 6px">{{ request.contract_reference || request.contract }}</div>
						<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
							<h1 style="margin: 0">{{ reviewing ? __("Review contract funding") : __("Contract funding") }}</h1>
							<span class="kt-status" :class="sameBadge" data-testid="bud-funding-status">{{ status }}</span>
							<span v-if="entry" class="kt-status" data-testid="bud-funding-entry-state">{{ entry.status === "Awaiting approval" ? __("Awaiting approval") : entry.status === "Approved" ? __("Funding entry approved") : entry.status === "Returned" ? __("Returned") : __("Draft") }}</span>
						</div>
						<p v-if="nextStep" class="kt-muted" style="margin: 10px 0 0; font-size: 14px" data-testid="bud-funding-next">{{ nextStep }}</p>
					</div>

					<div style="padding: 22px 28px; border-bottom: 1px solid var(--kt-color-divider)">
						<KtErrorBanner :message="actingError || ''" @dismiss="actingError = null" />

						<div v-if="entryStale" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-funding-basis-changed">
							<div class="kt-notice-body"><strong>{{ __("The opening review has changed. Return this entry for an updated allocation.") }}</strong></div>
						</div>
						<div v-if="closedMessage" class="kt-notice is-info" style="margin-bottom: 14px" data-testid="bud-funding-closed">
							<div class="kt-notice-body"><strong>{{ closedMessage }}</strong></div>
						</div>
						<div v-if="request.status === 'Open' && request.year_allocation_status === 'Scope review required'" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-funding-scope">
							<div class="kt-notice-body"><strong>{{ __("This funding is outside the supported scope") }}</strong> {{ (request.basis_issues || []).join(" ") }}</div>
						</div>
						<div v-if="request.status === 'Open' && request.year_allocation_status === 'Year allocation required'" class="kt-notice is-info" style="margin-bottom: 14px" data-testid="bud-funding-waiting">
							<div class="kt-notice-body">
								<strong>{{ __("Year allocation required") }}</strong>
								<template v-if="request.waiting_for && request.waiting_for.holder"> — {{ __("Waiting for Finance: {0} ({1})", [request.waiting_for.holder, request.waiting_for.responsibility]) }}.</template>
								<a :href="contractRoute" style="margin-left: 8px">{{ request.waiting_for && request.waiting_for.action ? request.waiting_for.action : __("Open contract review") }}</a>
							</div>
						</div>
						<div v-if="entry && entry.status === 'Returned' && entry.decision_reason" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-funding-returned">
							<div class="kt-notice-body"><strong>{{ status === "Funding shortfall" ? __("Funding shortfall") : __("Returned for correction") }}</strong> — {{ entry.decision_reason }}</div>
						</div>
						<div v-if="actions.blocked" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-funding-same-person">
							<div class="kt-notice-body"><strong>{{ actions.blocked }}</strong></div>
						</div>

						<div class="kt-grid-3" style="gap: 16px" data-testid="bud-funding-figures">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Contract") }}</div><div style="font-size: 14px">{{ request.contract_reference || request.contract }}</div><div class="kt-muted" style="font-size: 12px">{{ request.supplier_name }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Confirmed funding charge for {0}", [request.fiscal_year]) }}</div><div style="font-size: 14px" data-testid="bud-funding-charge">{{ request.confirmed_charge ? formatExact(request.confirmed_charge, currency) : "—" }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Already covered") }}</div><div style="font-size: 14px" data-testid="bud-funding-covered">{{ request.coverage_total !== null ? formatExact(request.coverage_total, currency) : "—" }}</div></div>
						</div>
						<div style="margin-top: 16px"><div class="kt-label" style="margin-bottom: 3px">{{ __("Amount requiring funding") }}</div><div class="kt-kpi-value" data-testid="bud-funding-required">{{ required !== null ? formatExact(required, currency) : "—" }}</div></div>

						<details style="margin-top: 16px" data-testid="bud-funding-evidence">
							<summary class="kt-label">{{ __("Opening review and source evidence") }}</summary>
							<ul style="margin: 8px 0 0; padding-left: 18px">
								<li v-for="e in request.evidence" :key="e">{{ e }}</li>
								<li v-if="!request.evidence.length" class="kt-muted">{{ __("No evidence reference has been given yet.") }}</li>
							</ul>
						</details>
						<details style="margin-top: 10px" data-testid="bud-funding-coverage">
							<summary class="kt-label">{{ __("Existing budget coverage") }}</summary>
							<table v-if="request.coverage.length" class="table" style="margin-top: 8px">
								<thead><tr><th>{{ __("Commitment") }}</th><th>{{ __("Status") }}</th><th class="is-num">{{ __("Amount") }}</th></tr></thead>
								<tbody><tr v-for="c in request.coverage" :key="c.commitment"><td>{{ c.code }}</td><td>{{ c.status }}</td><td class="is-num">{{ formatExact(c.amount, currency) }}</td></tr></tbody>
							</table>
							<p v-else class="kt-muted" style="margin: 8px 0 0">{{ __("Budget holds no commitment of this contract for {0}.", [request.fiscal_year]) }}</p>
						</details>
					</div>

					<!-- the allocation: editable for the Officer, frozen for the Approver -->
					<div v-if="(request.status === 'Open' && (request.year_allocation_status === 'Confirmed' || request.year_allocation_status === 'Year allocation required') && (editable || entry)) || (request.status === 'Completed' && entry && entry.status === 'Approved')" style="padding: 22px 28px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="bud-funding-allocation">
						<h3 class="kt-card-title" style="margin: 0 0 14px">{{ __("Allocation") }}</h3>
						<table class="table">
							<thead><tr><th>{{ __("Budget line") }}</th><th class="is-num">{{ __("Available") }}</th><th class="is-num">{{ __("Amount") }}</th><th v-if="editable"></th></tr></thead>
							<tbody>
								<tr v-for="(row, index) in form.rows" :key="row.row_id || `new-${index}`" data-testid="bud-funding-row">
									<td>
										<select v-if="editable" v-model="row.budget_line" class="input" :aria-label="__('Budget line')" data-testid="bud-funding-line" @change="touch">
											<option value="" disabled>{{ __("Choose a budget line") }}</option>
											<option v-for="l in eligible" :key="l.id" :value="l.id" :disabled="l.id !== row.budget_line && form.rows.some((r) => r.budget_line === l.id)">{{ l.title }}</option>
										</select>
										<span v-else>{{ lineTitle(row.budget_line) }}</span>
										<div class="kt-muted" style="font-size: 12px">{{ __("{0} · {1}", [request.source_organisation_unit || __("All departments"), request.fiscal_year]) }}</div>
										<div v-if="fieldErrors[`rows.${row.row_id}.budget_line`]" class="kt-field-error">{{ fieldErrors[`rows.${row.row_id}.budget_line`] }}</div>
									</td>
									<td class="is-num">{{ row.budget_line && lineAvailable(row.budget_line) !== null ? formatExact(lineAvailable(row.budget_line), currency) : "—" }}<div v-if="shortfallOf(row.budget_line)" class="kt-field-error" data-testid="bud-funding-shortfall-row">{{ __("Shortfall {0}", [formatExact(shortfallOf(row.budget_line).shortfall, currency)]) }}</div></td>
									<td class="is-num">
										<input v-if="editable" v-model="row.amount" class="input" inputmode="decimal" style="width: 150px; text-align: right" :aria-label="__('Amount')" data-testid="bud-funding-amount" @input="touch" />
										<span v-else>{{ formatExact(row.amount, currency) }}</span>
										<div v-if="fieldErrors[`rows.${row.row_id}.amount`]" class="kt-field-error">{{ fieldErrors[`rows.${row.row_id}.amount`] }}</div>
									</td>
									<td v-if="editable"><button type="button" class="btn btn-ghost" data-testid="bud-funding-remove" @click="removeRow(index)">{{ __("Remove") }}</button></td>
								</tr>
							</tbody>
							<tfoot>
								<tr><td colspan="2"><strong>{{ __("Total") }}</strong></td><td class="is-num" data-testid="bud-funding-total"><strong>{{ formatExact(total, currency) }}</strong></td><td v-if="editable"></td></tr>
								<tr v-if="editable && remaining !== null"><td colspan="2">{{ __("Remaining to allocate") }}</td><td class="is-num" data-testid="bud-funding-remaining">{{ formatExact(remaining, currency) }}</td><td></td></tr>
							</tfoot>
						</table>
						<div v-if="fieldErrors.rows" class="kt-field-error" data-testid="bud-funding-rows-error">{{ fieldErrors.rows }}</div>
						<button v-if="editable" type="button" class="btn btn-ghost" style="margin-top: 8px" :disabled="!unusedLines.length" data-testid="bud-funding-add" @click="addRow">{{ __("Add budget line") }}</button>

						<div style="margin-top: 18px">
							<label class="kt-label" for="bud-funding-recon">{{ __("Reconciliation to the confirmed charge") }}</label>
							<textarea v-if="editable" id="bud-funding-recon" v-model="form.reconciliation" class="input" rows="2" style="width: 100%" maxlength="500" data-testid="bud-funding-recon" @input="touch"></textarea>
							<p v-else style="margin: 4px 0 0" data-testid="bud-funding-recon-text">{{ entry ? entry.reconciliation : "" }}</p>
							<div v-if="fieldErrors.reconciliation" class="kt-field-error">{{ fieldErrors.reconciliation }}</div>
						</div>

						<div v-if="entry && entry.status === 'Awaiting approval'" class="kt-muted" style="font-size: 13px; margin-top: 14px" data-testid="bud-funding-submitter">{{ __("Submitted by {0} on {1}", [entry.submitted_by_name || entry.submitted_by, entry.submitted_at_display || entry.submitted_at]) }}</div>
						<div v-if="entry && entry.status === 'Approved'" style="margin-top: 14px" data-testid="bud-funding-approved">
							<strong>{{ __("Funding entry approved") }}</strong>
							<ul style="margin: 6px 0 0; padding-left: 18px"><li v-for="r in entry.rows" :key="r.row_id">{{ lineTitle(r.budget_line) }} — {{ formatExact(r.amount, currency) }} <span v-if="r.commitment" class="kt-muted">({{ __("commitment {0}", [r.commitment]) }})</span></li></ul>
						</div>
					</div>

					<div style="padding: 18px 28px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center" data-testid="bud-funding-actions">
						<template v-if="request.status === 'Open'">
							<button v-if="actions.submit !== undefined && editable" type="button" class="btn btn-primary" :disabled="!actions.submit || acting" data-testid="bud-funding-submit" @click="submit">{{ __("Submit for review") }}</button>
							<button v-if="editable" type="button" class="btn btn-ghost" :disabled="acting" data-testid="bud-funding-save" @click="saveDraft">{{ __("Save draft") }}</button>
							<button v-if="actions.decline" type="button" class="btn btn-ghost" :disabled="acting" data-testid="bud-funding-decline" @click="declining = true">{{ __("Decline request") }}</button>
							<button v-if="actions.approve !== undefined && entry && entry.status === 'Awaiting approval'" type="button" class="btn btn-primary" :disabled="!actions.approve || acting" data-testid="bud-funding-approve" @click="approving = true">{{ __("Approve funding entry") }}</button>
							<button v-if="actions.return !== undefined && entry && entry.status === 'Awaiting approval'" type="button" class="btn btn-ghost" :disabled="!actions.return || acting" data-testid="bud-funding-return" @click="returning = true">{{ __("Return for correction") }}</button>
						</template>
						<a :href="contractRoute" class="btn btn-ghost" data-testid="bud-funding-open-contract">{{ __("Open contract") }}</a>
					</div>
				</div>
			</template>
		</div>

		<ConfirmDialog :open="approving" :title="__('Approve funding entry')" :message="entry ? __('This funds {0} on {1} budget line(s): {2}. This cannot be undone here.', [formatExact(entry.rows_total, currency), entry.rows.length, entry.rows.map((r) => lineTitle(r.budget_line)).join(', ')]) : ''" :confirm-label="__('Confirm approval')" @cancel="approving = false" @confirm="decide('Approve')" />
		<ConfirmDialog :open="returning" :title="__('Return for correction')" :message="__('Say what the Budget Officer should correct.')" :confirm-label="__('Return for correction')" require-reason :reason-min-length="10" :reason-placeholder="__('Reason (10 to 500 characters)')" @cancel="returning = false" @confirm="(reason) => decide('Return', reason)" />
		<ConfirmDialog :open="declining" :title="__('Decline request')" :message="__('Say why this contract is not being funded here. Contract Management is told.')" :confirm-label="__('Decline request')" require-reason :reason-min-length="10" :reason-placeholder="__('Reason (10 to 500 characters)')" @cancel="declining = false" @confirm="decline" />
	</div>
</template>
