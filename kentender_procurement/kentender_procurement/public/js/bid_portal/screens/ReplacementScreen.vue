<script setup>
// BDS-CHG-001 v0.8 §10.15 BDS-DES-14 — Prepare replacement bid, ported from
// "Bid Board v3 - D". The submitted Version and its receipt stay current
// until a replacement is accepted; Create replacement Draft
// (`PrepareReplacementBid`) is offered only when the read says this person
// may, and opens the new Draft as the bid. Once a replacement Draft is open
// the page says so and leads to it.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import PortalGuidance from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/PortalGuidance.vue";
import CommonState from "../components/CommonState.vue";
import { conflictState } from "../composables/commonStates.js";
import { fixRoute } from "../composables/fixRoute.js";
import { useNarrow } from "../composables/useNarrow.js";

const READ = "kentender_procurement.bid_submission.api.get_replacement_page";
const PREPARE = "kentender_procurement.bid_submission.api.prepare_replacement_bid";
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
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const problem = ref(null); // a refused change's §10.17 state
const key = `bds-replace-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(READ, { tender_reference: props.reference, organisation: route.value.query.organisation || "" });
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
function create() {
	failure.value = "";
	problem.value = null;
	return runner.run(async () => {
		let result;
		try {
			result = await portal.call(PREPARE, { bid_reference: data.value.bid.reference, expected_record_version: data.value.bid.record_version, idempotency_key: key }, { type: "POST" });
		} catch (e) {
			problem.value = conflictState(e, props.reference);
			if (!problem.value) throw e;
			return;
		}
		if (result && result.ok) go(data.value.decision.next_href);
		else if (result) {
			const message = result.message || "";
			await load(); // the page may have changed (a Draft opened, the deadline passed)
			failure.value = message; // …and the refusal stays named
		}
	}, "Create replacement Draft");
}
function onFix(fix) {
	const href = fixRoute(fix, props.reference);
	if (href && href !== route.value.path) go(href);
}
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Prepare replacement bid"));
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bds-replacement">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __(data.page.title) }}</h1>
					<span class="kt-status" :class="'is-' + data.page.badge.tone">{{ data.page.badge.label }}</span>
				</div>
				<p class="kt-page-desc">{{ __(data.page.description) }}</p>
			</div>
		</div>

		<PortalGuidance :journey="data.journey" :answer="data.next_step" :label="__('Bid journey')" @fix="onFix" />

		<div class="kt-notice" role="note" data-testid="bds-replacement-notice">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg>
			<div class="kt-notice-body"><div>{{ data.notice.text }} <a :href="data.notice.link.href">{{ __(data.notice.link.label) }}</a></div></div>
		</div>

		<div class="bds-facts" data-testid="bds-replacement-facts">
			<div v-for="fact in data.facts" :key="fact.label" class="bds-fact"><span class="kt-label">{{ __(fact.label) }}</span><span class="bds-fact-value">{{ fact.value }}</span></div>
		</div>
		<p class="bds-muted" data-testid="bds-replacement-text">{{ data.text }}</p>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure"><div class="kt-notice-body">{{ failure }}</div></div>
		<CommonState v-if="problem" inline :state="problem.key" :figures="problem.figures" :action-href="problem.href" @action="problem = null; load()" />

		<div v-if="data.decision && !problem" :class="narrow ? 'bds-footer-stack' : 'bds-footer'">
			<a :href="data.decision.cancel_href" class="btn btn-secondary" :class="{ 'bds-btn-block': narrow }">{{ __("Cancel") }}</a>
			<div :class="narrow ? '' : 'bds-footer-end'">
				<button type="button" class="btn btn-primary" :class="{ 'bds-btn-block': narrow }" :disabled="pending" data-testid="bds-replacement-create" @click="create">{{ pending ? __("Creating…") : __(data.decision.create_label) }}</button>
			</div>
		</div>
		<div v-else-if="data.continue" :class="narrow ? 'bds-footer-stack' : 'bds-footer'">
			<a :href="data.continue.href" class="btn btn-primary" :class="{ 'bds-btn-block': narrow }" data-testid="bds-replacement-continue">{{ __(data.continue.label) }}</a>
		</div>
	</div>
	<CommonState v-else-if="failure" state="load-failure" @action="load" />
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-replacement-loading"></div></div>
</template>
