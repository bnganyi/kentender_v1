<script setup>
import { ref, reactive, computed, onMounted, onActivated, watch } from "vue";
import KtErrorBanner from "./KtErrorBanner.vue";
import ConfirmDialog from "../../budget_shared/components/ConfirmDialog.vue";
import AccessDenied from "../../budget_shared/components/AccessDenied.vue";
import { useRouteState } from "../../budget_shared/composables/useRouteState.js";
import { usePageRail } from "../../budget_shared/composables/usePageRail.js";
import { formatExact, toMinor, fromMinor } from "../../budget_shared/data/formatExact.js";
import { mintKey } from "../../budget_shared/data/formatKes.js";
import { decideCommitmentCorrection, getCommitmentCorrection, recordCommitmentCorrection } from "../data/budgetApi.js";

// BUD-DES-20 Correct commitment (BUD-CHG-001 v1.16 §11.22): the Officer's Form, then the Approver's decision on the
// same record. The Officer sees the contract, the Closed status and the retained amount read-only, and edits the
// corrected amount, the reason and the evidence references; the reduction is calculated. The Approver sees the exact
// saved comparison and the recorder, and approves or returns (a reason is required to return). A correction only
// ever lowers an amount, and after the financial year is closed it is a historical correction that authorises no
// spending. Routes: budget-funding/correct/<commitment>, budget-funding/correction/<correction>.
const { route, go, epoch } = useRouteState("budget-funding");
const kind = computed(() => route.value[1]);
const keyParam = computed(() => route.value[2]);
const view = ref(null);
const railTrail = computed(() => [
	{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
	{ label: __("Budget & Funding"), route: ["budget-funding"] },
	...(view.value ? [{ label: view.value.commitment.budget_line_title, route: ["budget-funding", "line", view.value.commitment.budget_line] }] : []),
	{ label: __("Correct commitment") },
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

const form = reactive({ new_amount: "", reason: "", evidence: "" });
const dirty = ref(false);
let loadedKey = "";

const commitment = computed(() => view.value?.commitment || null);
const correction = computed(() => view.value?.correction || null);
const actions = computed(() => view.value?.actions || {});
const currency = computed(() => commitment.value?.currency || "KES");
const recording = computed(() => !!actions.value.record && !(correction.value && correction.value.status === "Awaiting approval"));
const deciding = computed(() => !!correction.value && correction.value.status === "Awaiting approval");

async function load(opts) {
	if (!keyParam.value) return;
	const quiet = !!(opts && opts.quiet) && !!view.value;
	const token = guard.next();
	if (quiet) refreshing.value = true;
	else loading.value = true;
	forbidden.value = null;
	notFound.value = false;
	serverError.value = false;
	try {
		const data = kind.value === "correction" ? await getCommitmentCorrection("", keyParam.value) : await getCommitmentCorrection(keyParam.value, "");
		if (!guard.isCurrent(token)) return;
		view.value = data;
		adopt(data);
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.httpStatus === 403) forbidden.value = { heading: __("You do not have access to this commitment"), text: "" };
		else if (/not found/i.test(e.message || "")) notFound.value = true;
		else serverError.value = true;
	} finally {
		if (guard.isCurrent(token)) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}

// A new commitment starts blank; a revalidating return to the same one keeps what is typed.
function adopt(data) {
	const identity = data.commitment.id;
	if (identity === loadedKey && dirty.value) return;
	if (identity === loadedKey) return;
	loadedKey = identity;
	form.new_amount = "";
	form.reason = "";
	form.evidence = "";
	dirty.value = false;
	fieldErrors.value = {};
}

onMounted(load);
watch(keyParam, (v, prev) => v && v !== prev && ((view.value = null), (loadedKey = ""), load()));
let activations = 0;
onActivated(() => activations++ > 0 && view.value && load({ quiet: true }));
watch(epoch, () => view.value && load({ quiet: true }));

const retained = computed(() => (commitment.value ? String(commitment.value.retained_amount.toFixed ? commitment.value.retained_amount.toFixed(2) : commitment.value.retained_amount) : null));
const reduction = computed(() => {
	if (!retained.value || form.new_amount === "" || !/^\d+(\.\d{1,2})?$/.test(form.new_amount.trim())) return null;
	const diff = toMinor(retained.value) - toMinor(form.new_amount.trim());
	return diff > 0 ? fromMinor(diff, 100) : null;
});
const evidenceList = computed(() => form.evidence.split("\n").map((l) => l.trim()).filter(Boolean));
const nextStep = computed(() => {
	if (!view.value) return "";
	if (deciding.value) return actions.value.blocked ? __("Waiting on another Budget Approver") : actions.value.decide ? __("Your turn — Review the correction") : __("Waiting on a Budget Approver");
	if (recording.value) return __("Your turn — Record the supported correction");
	if (correction.value && correction.value.status === "Approved") return __("Done — the correction is approved");
	if (correction.value && correction.value.status === "Returned") return __("Returned — {0}", [correction.value.decision_reason]);
	return "";
});

function touch() {
	dirty.value = true;
}

const runner = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{
		onStart: () => {
			actingError.value = null;
			fieldErrors.value = {};
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
	actingError.value = Object.values(result.errors || {}).join(" ") || __("That could not be done.");
	if (result.code === "BUDGET_STALE_REVISION") load({ quiet: true });
}

function submitCorrection() {
	return runner.run(async (key) => {
		const result = await recordCommitmentCorrection({
			commitment: commitment.value.id,
			new_amount: form.new_amount.trim(),
			reason: form.reason.trim(),
			evidence: evidenceList.value,
			contract_reference: commitment.value.contract,
			expected_revision: commitment.value.revision,
			idempotency_key: key,
		});
		if (!result.ok) return refusal(result);
		dirty.value = false;
		loadedKey = "";
		go("correction", result.correction.id);
	}, "correct-record");
}

const approving = ref(false);
const returning = ref(false);
function decide(decision, reason) {
	approving.value = false;
	returning.value = false;
	return runner.run(async (key) => {
		const result = await decideCommitmentCorrection({ correction: correction.value.id, decision, reason: reason || "", idempotency_key: key });
		if (!result.ok) return refusal(result);
		await load({ quiet: true });
	}, `correct-${decision.toLowerCase()}`);
}
</script>

<template>
	<div class="kt-industry" data-testid="bud-correction" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
		<div ref="railEl" class="kt-rail-mount"></div>

		<div v-if="!loading && forbidden" class="kt-shell">
			<div class="kt-page" data-testid="bud-correction-forbidden"><AccessDenied :heading="__(forbidden.heading)" :text="__(forbidden.text || '')" /></div>
		</div>
		<div v-else class="kt-shell" style="max-width: 900px">
			<div v-if="loading" class="card blueprint"><div class="kt-skel" style="width: 300px; height: 20px"></div></div>
			<div v-else-if="notFound" class="card blueprint kt-empty" data-testid="bud-correction-not-found"><h2>{{ __("This commitment could not be found.") }}</h2></div>
			<div v-else-if="serverError" class="card blueprint kt-empty" data-testid="bud-correction-server-error">
				<h2>{{ __("This commitment could not be loaded.") }}</h2>
				<button type="button" class="btn btn-primary" @click="load()">{{ __("Try again") }}</button>
			</div>

			<template v-else-if="commitment">
				<div class="card blueprint" style="padding: 0">
					<div style="padding: 28px 28px 20px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="bud-correction-header">
						<div class="kt-eyebrow" style="margin-bottom: 6px">{{ commitment.commitment_code }}</div>
						<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
							<h1 style="margin: 0">{{ __("Correct commitment") }}</h1>
							<span class="kt-status" :class="correction && correction.status === 'Approved' ? 'is-live' : 'is-attention'" data-testid="bud-correction-status">{{ correction ? correction.status : __("Closed") }}</span>
						</div>
						<p v-if="nextStep" class="kt-muted" style="margin: 10px 0 0; font-size: 14px" data-testid="bud-correction-next">{{ nextStep }}</p>
					</div>

					<div style="padding: 22px 28px; border-bottom: 1px solid var(--kt-color-divider)">
						<KtErrorBanner :message="actingError || ''" @dismiss="actingError = null" />
						<div v-if="view.closed_year" class="kt-notice is-info" style="margin-bottom: 14px" data-testid="bud-correction-closed-year">
							<div class="kt-notice-body"><strong>{{ __("This financial year is closed. The correction does not authorise spending.") }}</strong></div>
						</div>
						<div v-if="view.stale" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-correction-stale">
							<div class="kt-notice-body"><strong>{{ __("The commitment has changed. Review the current amount.") }}</strong></div>
						</div>
						<div v-if="actions.blocked" class="kt-notice is-warning" style="margin-bottom: 14px" data-testid="bud-correction-same-person">
							<div class="kt-notice-body"><strong>{{ actions.blocked }}</strong></div>
						</div>

						<div class="kt-grid-3" style="gap: 16px" data-testid="bud-correction-facts">
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Contract") }}</div><div style="font-size: 14px">{{ commitment.contract }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Budget line") }}</div><div style="font-size: 14px">{{ commitment.budget_line_title }}</div></div>
							<div><div class="kt-label" style="margin-bottom: 3px">{{ __("Status") }}</div><div style="font-size: 14px">{{ commitment.status }}</div></div>
						</div>
						<div style="margin-top: 16px"><div class="kt-label" style="margin-bottom: 3px">{{ correction ? __("Original amount") : __("Retained amount") }}</div><div class="kt-kpi-value" data-testid="bud-correction-original">{{ formatExact(correction ? correction.before_amount.toFixed(2) : retained, currency) }}</div></div>
					</div>

					<!-- Officer: the form -->
					<div v-if="recording" style="padding: 22px 28px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="bud-correction-form">
						<div>
							<label class="kt-label" for="bud-corr-amount">{{ __("Corrected amount") }}</label>
							<input id="bud-corr-amount" v-model="form.new_amount" class="input" inputmode="decimal" style="width: 220px; text-align: right" data-testid="bud-correction-amount" @input="touch" />
							<div v-if="fieldErrors.new_amount" class="kt-field-error">{{ fieldErrors.new_amount }}</div>
							<p class="kt-muted" style="margin: 6px 0 0; font-size: 13px" data-testid="bud-correction-reduction">{{ reduction ? __("Reduction {0}", [formatExact(reduction, currency)]) : __("A correction can only lower the amount.") }}</p>
						</div>
						<div style="margin-top: 16px">
							<label class="kt-label" for="bud-corr-reason">{{ __("Reason") }}</label>
							<textarea id="bud-corr-reason" v-model="form.reason" class="input" rows="2" style="width: 100%" maxlength="500" data-testid="bud-correction-reason" @input="touch"></textarea>
							<div v-if="fieldErrors.reason" class="kt-field-error">{{ fieldErrors.reason }}</div>
						</div>
						<div style="margin-top: 16px">
							<label class="kt-label" for="bud-corr-evidence">{{ __("Evidence (one reference per line)") }}</label>
							<textarea id="bud-corr-evidence" v-model="form.evidence" class="input" rows="3" style="width: 100%" data-testid="bud-correction-evidence" @input="touch"></textarea>
							<div v-if="fieldErrors.evidence" class="kt-field-error">{{ fieldErrors.evidence }}</div>
						</div>
					</div>

					<!-- the saved comparison, for the Approver and for the record afterwards -->
					<div v-if="correction" style="padding: 22px 28px; border-bottom: 1px solid var(--kt-color-divider)" data-testid="bud-correction-record">
						<table class="table">
							<tbody>
								<tr><td>{{ __("Original amount") }}</td><td class="is-num">{{ formatExact(correction.before_amount.toFixed(2), currency) }}</td></tr>
								<tr><td>{{ __("Corrected amount") }}</td><td class="is-num" data-testid="bud-correction-after">{{ formatExact(correction.after_amount.toFixed(2), currency) }}</td></tr>
								<tr><td>{{ __("Reduction") }}</td><td class="is-num" data-testid="bud-correction-decrease">{{ formatExact(correction.decrease.toFixed(2), currency) }}</td></tr>
								<tr><td>{{ __("Reason") }}</td><td>{{ correction.reason }}</td></tr>
								<tr><td>{{ __("Evidence") }}</td><td><span v-for="e in correction.evidence" :key="e" style="display: block">{{ e }}</span></td></tr>
								<tr><td>{{ __("Recorded by") }}</td><td>{{ correction.recorded_by }}</td></tr>
								<tr v-if="correction.decided_by"><td>{{ correction.status === "Approved" ? __("Approved by") : __("Returned by") }}</td><td>{{ correction.decided_by }}<span v-if="correction.decision_reason" class="kt-muted"> — {{ correction.decision_reason }}</span></td></tr>
							</tbody>
						</table>
					</div>

					<div style="padding: 18px 28px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center" data-testid="bud-correction-actions">
						<button v-if="recording" type="button" class="btn btn-primary" :disabled="acting || !form.new_amount || !form.reason || !evidenceList.length" data-testid="bud-correction-submit" @click="submitCorrection">{{ __("Submit correction") }}</button>
						<button v-if="recording" type="button" class="btn btn-ghost" data-testid="bud-correction-cancel" @click="go('line', commitment.budget_line)">{{ __("Cancel") }}</button>
						<template v-if="deciding">
							<button type="button" class="btn btn-primary" :disabled="!actions.decide || acting" data-testid="bud-correction-approve" @click="approving = true">{{ __("Approve correction") }}</button>
							<button type="button" class="btn btn-ghost" :disabled="!actions.decide || acting" data-testid="bud-correction-return" @click="returning = true">{{ __("Return for correction") }}</button>
						</template>
						<a v-if="correction" :href="`/app/contracts/${encodeURIComponent(commitment.contract)}`" class="btn btn-ghost" data-testid="bud-correction-open-contract">{{ __("Open contract") }}</a>
					</div>
				</div>
			</template>
		</div>

		<ConfirmDialog :open="approving" :title="__('Approve correction')" :message="correction ? __('This lowers the commitment from {0} to {1}. Exactly the reduction returns to Available.', [formatExact(correction.before_amount.toFixed(2), currency), formatExact(correction.after_amount.toFixed(2), currency)]) : ''" :confirm-label="__('Approve correction')" @cancel="approving = false" @confirm="decide('Approve')" />
		<ConfirmDialog :open="returning" :title="__('Return for correction')" :message="__('Say what the Budget Officer should correct.')" :confirm-label="__('Return for correction')" require-reason :reason-min-length="10" :reason-placeholder="__('Reason (10 to 500 characters)')" @cancel="returning = false" @confirm="(reason) => decide('Return', reason)" />
	</div>
</template>
