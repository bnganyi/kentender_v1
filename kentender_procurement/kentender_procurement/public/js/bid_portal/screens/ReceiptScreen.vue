<script setup>
// BDS-CHG-001 v0.8 §10.14 BDS-DES-13 — Bid submitted, and the replacement
// receipt of §10.15 (BDS-DES-14-REPLACED), ported from "Bid Board v3 - D".
// The read decides the heading, the actions this viewer may take on this
// receipt (Prepare replacement and Withdraw bid for the signatory on the
// current receipt before the deadline; Print receipt for everyone), the
// receipt facts, the summary, the lineage and the one factual sentence.
// Withdraw bid opens the withdrawal dialog; success opens its
// acknowledgement.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import WithdrawDialog from "../components/WithdrawDialog.vue";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const READ = "kentender_procurement.bid_submission.api.get_receipt_page";
const PREPARE = "kentender_procurement.bid_submission.api.prepare_replacement_bid";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
	receipt: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const withdrawing = ref(false);
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const startKey = `bds-restart-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { tender_reference: props.reference, receipt_reference: props.receipt, organisation: route.value.query.organisation || "" });
		if (!guard.isCurrent(token)) return;
		if (result && result.outcome === "NOT_FOUND") {
			emit("not-found");
			return;
		}
		data.value = result;
		failure.value = "";
		openFromRoute();
	} catch (e) {
		if (guard.isCurrent(token)) failure.value = e.message;
	}
}
// The bid page's Withdraw bid arrives with ?action=withdraw: the dialog opens
// once, and only when this person may withdraw on this receipt.
let actionTaken = false;
function openFromRoute() {
	if (actionTaken || route.value.query.action !== "withdraw" || !data.value || !data.value.withdrawal) return;
	actionTaken = true;
	withdrawing.value = true;
}
function onAction(action) {
	if (action.key === "withdraw_bid") withdrawing.value = true;
}
// BDS-DES-14-WITHDRAWN Start replacement (`PrepareReplacementBid` from a
// withdrawn bid): the new Draft opens as the bid.
function startReplacement() {
	failure.value = "";
	return runner.run(async () => {
		const result = await portal.call(PREPARE, { bid_reference: data.value.bid.reference, expected_record_version: data.value.bid.record_version, idempotency_key: startKey }, { type: "POST" });
		if (result && result.ok) go(data.value.footer.start.next_href);
		else if (result) failure.value = result.message || "";
	}, "Start replacement");
}
function onWithdrawn(result) {
	withdrawing.value = false;
	go(`/tenders/${props.reference}/bid/receipt/${result.acknowledgement_reference}`);
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(data.value ? __(data.value.page.title) : __("Bid submitted"));
	if (!data.value) load();
	else openFromRoute();
});
</script>

<template>
	<div v-if="data && data.kind === 'acknowledgement'" class="kt-page" data-testid="bds-acknowledgement">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.page.badge.tone">{{ __(data.page.badge.label) }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div class="kt-region">
			<h2>{{ __("Acknowledgement") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-acknowledgement-facts">
					<div v-for="fact in data.acknowledgement" :key="fact.label" class="bds-fact">
						<span class="kt-label">{{ __(fact.label) }}</span>
						<span class="bds-fact-value">
							<span v-if="fact.status" class="kt-status" :class="'is-' + fact.status.tone">{{ __(fact.status.label) }}</span>
							<strong v-else-if="fact.strong">{{ fact.value }}</strong>
							<template v-else>{{ fact.value }}</template>
						</span>
					</div>
				</div>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<button v-if="data.footer.start" type="button" class="btn btn-primary bds-btn-block" :disabled="pending" data-testid="bds-start-replacement" @click="startReplacement">{{ __(data.footer.start.label) }}</button>
			<a :href="data.footer.download_href" class="btn btn-secondary bds-btn-block" data-testid="bds-acknowledgement-download">{{ __("Download acknowledgement") }}</a>
			<a :href="data.footer.back_href" class="btn btn-secondary bds-btn-block">{{ __("Back to My bids") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.footer.back_href" class="btn btn-secondary">{{ __("Back to My bids") }}</a>
			<div class="bds-footer-end">
				<a :href="data.footer.download_href" class="btn btn-secondary" data-testid="bds-acknowledgement-download">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" /></svg>
					{{ __("Download acknowledgement") }}
				</a>
				<button v-if="data.footer.start" type="button" class="btn btn-primary" :disabled="pending" data-testid="bds-start-replacement" @click="startReplacement">{{ pending ? __("Starting…") : __(data.footer.start.label) }}</button>
			</div>
		</div>
	</div>
	<div v-else-if="data" class="kt-page" data-testid="bds-receipt">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.page.badge.tone" data-testid="bds-receipt-badge">{{ __(data.page.badge.label) }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
			<div class="kt-page-actions" :class="{ 'bds-actions-stack': narrow }" data-testid="bds-receipt-actions">
				<template v-for="action in data.actions" :key="action.key">
					<button
						v-if="action.key === 'withdraw_bid'"
						type="button"
						class="btn btn-primary kt-danger"
						:class="{ 'bds-btn-block': narrow }"
						data-testid="bds-receipt-withdraw"
						@click="onAction(action)"
					>
						{{ __(action.label) }}
					</button>
					<a
						v-else
						:href="action.href"
						class="btn"
						:class="[action.tone === 'primary' ? 'btn-primary' : 'btn-secondary', narrow ? 'bds-btn-block' : '']"
						:target="action.key === 'print' ? '_blank' : null"
						:rel="action.key === 'print' ? 'noopener' : null"
						:data-testid="'bds-receipt-' + action.key"
					>
						{{ __(action.label) }}
					</a>
				</template>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div class="kt-region">
			<h2>{{ __("Receipt") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-receipt-facts">
					<div v-for="fact in data.receipt" :key="fact.label" class="bds-fact">
						<span class="kt-label">{{ __(fact.label) }}</span>
						<span class="bds-fact-value">
							<span v-if="fact.status" class="kt-status" :class="'is-' + fact.status.tone">{{ __(fact.status.label) }}</span>
							<strong v-else-if="fact.strong">{{ fact.value }}</strong>
							<template v-else>{{ fact.value }}</template>
						</span>
					</div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Submission summary") }}</h2>
			<div class="bds-region-body">
				<div class="bds-facts" data-testid="bds-receipt-summary">
					<div v-for="fact in data.summary" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value"><strong v-if="fact.strong">{{ fact.value }}</strong><template v-else>{{ fact.value }}</template></span></div>
				</div>
			</div>
		</div>

		<div class="kt-notice" role="note" data-testid="bds-receipt-notice">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
			<div class="kt-notice-body"><div>{{ data.notice }}</div></div>
		</div>

		<div v-if="data.lineage" class="kt-group bds-lineage" data-testid="bds-receipt-lineage">
			<span class="kt-label">{{ __("Lineage") }}</span>
			<span class="kt-status" :class="'is-' + data.lineage.status.tone">{{ __(data.lineage.status.label) }}</span>
			<a :href="data.lineage.link.href">{{ data.lineage.link.label }}</a>
		</div>

		<p v-if="data.sentence" class="bds-muted" data-testid="bds-receipt-sentence">{{ data.sentence }}</p>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>

		<div v-if="narrow" class="bds-footer-stack">
			<a :href="data.footer.download_href" class="btn btn-secondary bds-btn-block" data-testid="bds-receipt-download">{{ __("Download receipt") }}</a>
			<a :href="data.footer.back_href" class="btn btn-secondary bds-btn-block">{{ __("Back to My bids") }}</a>
		</div>
		<div v-else class="bds-footer">
			<a :href="data.footer.back_href" class="btn btn-secondary">{{ __("Back to My bids") }}</a>
			<div class="bds-footer-end">
				<a :href="data.footer.download_href" class="btn btn-secondary" data-testid="bds-receipt-download">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" /></svg>
					{{ __("Download receipt") }}
				</a>
			</div>
		</div>

		<WithdrawDialog v-if="withdrawing && data.withdrawal" :bid="data.bid" :withdrawal="data.withdrawal" @close="withdrawing = false" @withdrawn="onWithdrawn" @stale="withdrawing = false; load()" />
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-receipt-loading"></div></div>
</template>
