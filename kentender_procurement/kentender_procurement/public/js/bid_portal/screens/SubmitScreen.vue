<script setup>
// BDS-CHG-001 v0.8 §10.13 BDS-DES-12 — Submit bid, ported from "Bid Board v3
// - D". The read decides the state: the final confirmation only when
// `SubmitBid`'s own checks pass; the pending attempt (no new Submit, View
// status); one notice per operating state; Check certificate, Try
// confirmation again and Contact support as the next step's fixes. Submit
// bid confirms in a dialog, then prepares the signature, signs through the
// test trust service on a test environment, and submits with one request key
// per confirmation; success opens the receipt, anything else re-reads.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import ConfirmSubmitDialog from "../components/ConfirmSubmitDialog.vue";
import { conflictState } from "../composables/commonStates.js";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const API = "kentender_procurement.bid_submission.api.";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const confirmed = ref(false);
const confirmError = ref("");
const dialog = ref(false);
const retrying = ref(false);
const certificateText = ref("");
const problem = ref(null); // a refused change's §10.17 state, in place of the confirmation
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const decision = computed(() => (data.value && (data.value.decision || (retrying.value ? data.value.retry : null))) || null);
let submitKey = "";

function key(kind) {
	return `bds-${kind}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(API + "get_submit_page", { tender_reference: props.reference, organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
function openDialog() {
	confirmError.value = "";
	if (!confirmed.value) {
		confirmError.value = __("Confirm the statement before submitting.");
		return;
	}
	submitKey = submitKey || key("submit");
	dialog.value = true;
}
function submit() {
	failure.value = "";
	problem.value = null;
	return runner.run(async () => {
		const bid = data.value.bid;
		try {
			const prepared = await portal.call(API + "prepare_bid_signature", { bid_reference: bid.reference, confirmed: 1, expected_record_version: bid.record_version, idempotency_key: key("sign") }, { type: "POST" });
			if (!prepared || !prepared.ok) {
				dialog.value = false;
				await load(); // the page may have changed; the refusal stays named
				if (prepared && prepared.errors) confirmError.value = prepared.errors.confirmed || prepared.message || "";
				else failure.value = (prepared && prepared.message) || "";
				return;
			}
			if (!prepared.simulation) {
				failure.value = __("The signing service is not available on this site. Your bid remains saved and has not been submitted.");
				dialog.value = false;
				return;
			}
			const signed = await portal.call(API + "sign_with_test_trust_service", { signing_request: prepared.signing_request }, { type: "POST" });
			const result = await portal.call(API + "submit_bid", { bid_reference: bid.reference, signature: signed.signature, confirmed: 1, expected_record_version: bid.record_version, idempotency_key: submitKey, replaces: data.value.replaces || "" }, { type: "POST" });
			dialog.value = false;
			if (result && result.ok) return go(`/tenders/${props.reference}/bid/receipt/${result.receipt_reference}`);
			submitKey = ""; // a definite rejection or an uncertain attempt: the page now says which
			retrying.value = false;
			confirmed.value = false;
			return load();
		} catch (e) {
			dialog.value = false;
			await load();
			problem.value = conflictState(e, props.reference);
			if (!problem.value) failure.value = e.message;
		}
	}, "Submit bid");
}
async function onFix(fix) {
	if (fix.fix_id === "check_certificate") {
		const result = await portal.call(API + "check_certificate", { bid_reference: data.value.bid.reference, organisation: route.value.query.organisation || "" });
		certificateText.value = (result && result.text) || "";
		return load();
	}
	if (fix.fix_id === "submit_bid") {
		retrying.value = true;
		confirmed.value = false;
		return;
	}
	if (fix.fix_id === "contact_support") {
		if (data.value.support_href) window.location.assign(data.value.support_href);
		return;
	}
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Submit bid"));
	if (!data.value) load();
});
</script>

<template>
	<CommonState v-if="data && data.state" :state="data.state.key" :figures="data.state.figures" :action-href="data.state.href" />
	<div v-else-if="data" class="kt-page" data-testid="bds-submit">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a :href="data.page.back_href" class="bds-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __(data.page.back_label) }}</a>
				<div class="bds-title-row"><h1 class="kt-page-title">{{ __(data.page.title) }}</h1></div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />
		<p v-if="certificateText" class="bds-muted" role="status" data-testid="bds-certificate-check">{{ certificateText }}</p>

		<div v-if="data.consequence" class="kt-notice" :class="'is-' + data.consequence.tone" data-testid="bds-submit-consequence">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
			<div class="kt-notice-body"><div>{{ data.consequence.text }}</div></div>
		</div>
		<div v-if="data.notice" class="kt-notice" :class="'is-' + data.notice.tone" role="status" data-testid="bds-submit-notice">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>
			<div class="kt-notice-body">
				<strong>{{ data.notice.title }}</strong>
				<div class="bds-notice-text">
					{{ data.notice.text }}
					<template v-for="(link, i) in data.notice.links" :key="link.href"><template v-if="i"> · </template> <a :href="link.href">{{ __(link.label) }}</a></template>
				</div>
			</div>
		</div>
		<div v-if="data.action"><a :href="data.action.href" class="kt-btn" :class="[data.action.tone === 'primary' ? 'kt-btn-primary' : 'kt-btn-secondary', narrow ? 'bds-btn-block' : '']" data-testid="bds-submit-action">{{ __(data.action.label) }}</a></div>

		<div class="kt-meta-row is-tight bds-meta-tight" data-testid="bds-submit-time">
			<div v-for="fact in data.meta" :key="fact.label"><span class="kt-label">{{ __(fact.label) }}</span><span class="kt-meta-value">{{ fact.value }}</span></div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Submission summary") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-submit-summary">
					<div v-for="fact in data.summary" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value"><strong v-if="fact.strong">{{ fact.value }}</strong><template v-else>{{ fact.value }}</template></span></div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Authorised Signatory") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-submit-signatory">
					<div v-for="fact in data.signatory" :key="fact.label" class="bds-fact">
						<span class="kt-label">{{ __(fact.label) }}</span>
						<span class="bds-fact-value"><span v-if="fact.status" class="kt-status" :class="'is-' + fact.status.tone">{{ __(fact.status.label) }}</span><template v-else>{{ fact.value }}</template></span>
					</div>
				</div>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>
		<CommonState v-if="problem" inline :state="problem.key" :figures="problem.figures" :action-href="problem.href" @action="problem = null; load()" />

		<div v-if="decision && decision.kind === 'confirm' && !problem" class="kt-decision bds-decision" data-testid="bds-submit-decision">
			<label class="kt-checkbox">
				<input v-model="confirmed" type="checkbox" :aria-invalid="!!confirmError" data-testid="bds-submit-confirmation" />
				<span class="box"></span>
				<span>{{ decision.confirmation }}</span>
			</label>
			<p v-if="confirmError" class="kt-field-error">{{ confirmError }}</p>
			<div class="bds-decision-actions">
				<a :href="decision.cancel_href" class="kt-btn kt-btn-secondary" :class="{ 'bds-btn-block': narrow }">{{ __("Cancel") }}</a>
				<button type="button" class="kt-btn kt-btn-primary" :class="{ 'bds-btn-block': narrow }" :disabled="!confirmed || pending" data-testid="bds-submit-open" @click="openDialog">{{ __(decision.submit_label) }}</button>
			</div>
		</div>
		<div v-else-if="decision && decision.kind === 'pending'" class="kt-decision bds-decision" data-testid="bds-submit-pending">
			<p class="bds-muted">{{ decision.text }}</p>
			<div class="bds-decision-actions">
				<a :href="decision.status_href">{{ __("View status") }}</a>
				<button type="button" class="kt-btn kt-btn-primary" :class="{ 'bds-btn-block': narrow }" disabled>{{ __(decision.submit_label) }}</button>
			</div>
		</div>

		<ConfirmSubmitDialog v-if="dialog" :dialog="data.dialog" :pending="pending" @close="dialog = false" @confirm="submit" />
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-submit-loading"></div></div>
</template>
