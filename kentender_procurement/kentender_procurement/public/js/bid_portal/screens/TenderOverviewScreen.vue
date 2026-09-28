<script setup>
// BDS-CHG-001 v0.8 §10.3 BDS-DES-02 — Published Tender overview, ported from
// "Bid Board v3 - A" (1440 tables; 390 labelled cards). The server
// (`GetPublishedTenderForBidder` + the viewer's own bid) decides every fact,
// the one action and the notices; nothing here derives a status. A cancelled
// Tender is its reference, the Cancelled status and View notice alone. While
// the supplier portal information is incomplete the server names the §10.17
// variant for this viewer (new visitor, Draft holder, submitted bidder).
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { useNarrow } from "../composables/useNarrow.js";
import CommonState from "../components/CommonState.vue";
import QuestionDialog from "../components/QuestionDialog.vue";
import StartBidDialog from "../components/StartBidDialog.vue";

const METHOD = "kentender_procurement.bid_submission.api.get_tender_overview";
const props = defineProps({
	initial: { type: Object, default: null },
	reference: { type: String, required: true },
});
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();
const starting = ref(false);
const asking = ref(false);

const tender = computed(() => (data.value && data.value.tender) || {});
const cancelled = computed(() => tender.value.availability === "cancelled");
const action = computed(() => (data.value && data.value.action) || null);
const bid = computed(() => (data.value && data.value.bid) || null);
const statusClass = computed(() => (bid.value && bid.value.status === "Submitted" ? "is-live" : "is-draft"));

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(METHOD, { tender_reference: props.reference });
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
function started() {
	starting.value = false;
	return load();
}
watch(epoch, () => load());
watch(
	() => tender.value.title,
	(title) => title && portal.setTitle(cancelled.value ? tender.value.reference : title),
	{ immediate: true },
);
onMounted(() => {
	if (!data.value) load();
});
</script>

<template>
	<div v-if="data && cancelled" class="kt-page" data-testid="bds-tender-overview">
		<div class="kt-page-head">
			<div class="bds-head-main">
				<a href="/tenders" class="bds-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to Tenders") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ tender.reference }}</h1>
					<span class="kt-status is-critical">{{ __("Cancelled") }}</span>
				</div>
				<p class="kt-page-desc">{{ __("This Tender is not accepting bids.") }}</p>
			</div>
			<div v-if="action" class="kt-page-actions" :class="{ 'bds-actions-stack': narrow }">
				<a :href="action.href" class="kt-btn kt-btn-secondary" :class="{ 'bds-btn-block': narrow }" data-testid="bds-overview-action">{{ __(action.label) }}</a>
			</div>
		</div>
	</div>

	<div v-else-if="data" class="kt-page" data-testid="bds-tender-overview">
		<div class="kt-page-head" :class="{ 'bds-head-stack': narrow }">
			<div class="bds-head-main">
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ tender.title }}</h1>
					<span v-if="bid && bid.status_text" class="kt-status" :class="statusClass" data-testid="bds-overview-status">{{ bid.status_text }}</span>
					<span v-else-if="tender.status_label" class="kt-status is-draft">{{ tender.status_label }}</span>
				</div>
				<div class="bds-reference">{{ tender.reference }}</div>
				<p class="kt-page-desc">{{ tender.description }}</p>
			</div>
			<div v-if="action" class="kt-page-actions" :class="{ 'bds-actions-stack': narrow }">
				<button v-if="action.kind === 'start_bid'" type="button" class="kt-btn kt-btn-primary" :class="{ 'bds-btn-block': narrow }" data-testid="bds-overview-action" @click="starting = true">{{ __(action.label) }}</button>
				<a v-else :href="action.href" class="kt-btn kt-btn-primary" :class="{ 'bds-btn-block': narrow }" data-testid="bds-overview-action">{{ __(action.label) }}</a>
			</div>
		</div>

		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>
		<div v-if="data.notice" class="kt-notice" :class="data.notice.kind === 'outage' ? 'is-critical' : 'is-warning'" role="status" data-testid="bds-overview-notice">
			<div class="kt-notice-body"><strong>{{ data.notice.title }}</strong> {{ data.notice.text }}</div>
		</div>
		<CommonState v-if="data.state" inline :state="data.state.key" :figures="data.state.figures" :action-href="data.state.href" @action="load" />

		<div class="kt-region">
			<h2>{{ __("Key dates") }}</h2>
			<div class="bds-region-body">
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Submissions close") }}</span><span class="kt-meta-value">{{ tender.deadline }}</span></div>
					<div v-if="tender.clarification_deadline"><span class="kt-label">{{ __(tender.clarification_label) }}</span><span class="kt-meta-value">{{ tender.clarification_deadline }}</span></div>
					<div><span class="kt-label">{{ __("Published") }}</span><span class="kt-meta-value">{{ tender.published }}</span></div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("What is being procured") }}</h2>
			<div class="bds-region-body">
				<div class="kt-meta-row">
					<div v-if="data.facts.quantity"><span class="kt-label">{{ __("Quantity") }}</span><span class="kt-meta-value">{{ data.facts.quantity }}</span></div>
					<div v-if="data.facts.delivery_location" class="bds-span-2"><span class="kt-label">{{ __("Delivery location") }}</span><span class="kt-meta-value">{{ data.facts.delivery_location }}</span></div>
					<div v-if="data.facts.latest_delivery"><span class="kt-label">{{ __("Latest delivery") }}</span><span class="kt-meta-value">{{ data.facts.latest_delivery }}</span></div>
					<div><span class="kt-label">{{ __("Currency") }}</span><span class="kt-meta-value">{{ data.facts.currency }}</span></div>
					<div><span class="kt-label">{{ __("Tender security") }}</span><span class="kt-meta-value">{{ data.facts.tender_security }}</span></div>
					<div v-if="data.facts.bid_validity"><span class="kt-label">{{ __("Bid validity") }}</span><span class="kt-meta-value">{{ data.facts.bid_validity }}</span></div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Tender documents") }}</h2>
			<div class="bds-region-body">
				<table v-if="!narrow" class="kt-table" data-testid="bds-documents-table">
					<thead><tr><th>{{ __("Document") }}</th><th>{{ __("Published") }}</th><th>{{ __("Action") }}</th></tr></thead>
					<tbody>
						<tr v-for="d in data.documents" :key="d.key">
							<td class="bds-strong">{{ d.label }}</td>
							<td>{{ d.published }}</td>
							<td><a :href="d.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="d.download_href">{{ __("Download") }}</a></td>
						</tr>
					</tbody>
				</table>
				<div v-else data-testid="bds-documents-cards">
					<div v-for="d in data.documents" :key="d.key" class="bds-card">
						<div class="bds-card-title">{{ d.label }}</div>
						<div class="bds-card-fact"><span class="kt-label">{{ __("Published") }}</span><span>{{ d.published }}</span></div>
						<div class="bds-card-actions"><a :href="d.view_href" target="_blank" rel="noopener">{{ __("View") }}</a> · <a :href="d.download_href">{{ __("Download") }}</a></div>
					</div>
				</div>
			</div>
		</div>

		<div class="kt-region">
			<div v-if="data.clarification.can_ask" class="bds-region-head">
				<h2>{{ __("Addenda and clarification answers") }}</h2>
				<div class="bds-region-actions">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="bds-ask-question" @click="asking = true">{{ __("Ask a question") }}</button>
				</div>
			</div>
			<h2 v-else>{{ __("Addenda and clarification answers") }}</h2>
			<div class="bds-region-body">
				<template v-if="data.addenda.length">
					<table v-if="!narrow" class="kt-table" data-testid="bds-addenda-table">
						<thead><tr><th>{{ __("Addendum") }}</th><th>{{ __("Issued") }}</th><th>{{ __("Current deadline") }}</th><th>{{ __("Action") }}</th></tr></thead>
						<tbody>
							<tr v-for="a in data.addenda" :key="a.reference">
								<td class="bds-strong">{{ a.reference }} · {{ a.summary }}</td>
								<td>{{ a.issued }}</td>
								<td>{{ a.current_deadline }}</td>
								<td><a v-if="a.view_href" :href="a.view_href" target="_blank" rel="noopener">{{ __("View") }}</a></td>
							</tr>
						</tbody>
					</table>
					<div v-else data-testid="bds-addenda-cards">
						<div v-for="a in data.addenda" :key="a.reference" class="bds-card">
							<div class="bds-card-title">{{ a.reference }} · {{ a.summary }}</div>
							<div class="bds-card-fact"><span class="kt-label">{{ __("Issued") }}</span><span>{{ a.issued }}</span></div>
							<div class="bds-card-fact"><span class="kt-label">{{ __("Current deadline") }}</span><span>{{ a.current_deadline }}</span></div>
							<div class="bds-card-actions"><a v-if="a.view_href" :href="a.view_href" target="_blank" rel="noopener">{{ __("View") }}</a></div>
						</div>
					</div>
				</template>
				<p v-else class="bds-muted" data-testid="bds-no-addenda">{{ __("No addenda have been issued.") }}</p>
				<div v-for="(q, i) in data.answers" :key="i" class="kt-group bds-answer">
					<span class="kt-label">{{ __("Clarification answer · answered {0}", [q.answered]) }}</span>
					<span class="bds-strong">{{ q.question }}</span>
					<span class="bds-answer-text">{{ q.answer }}</span>
				</div>
				<p v-if="!data.answers.length" class="bds-muted" data-testid="bds-no-answers">{{ __("No answers published yet.") }}</p>
				<p v-if="data.clarification.helper" class="bds-muted">{{ data.clarification.helper }}</p>
				<p v-if="data.clarification.closed_text" class="bds-muted" data-testid="bds-clarifications-closed">{{ data.clarification.closed_text }}</p>
			</div>
		</div>

		<div class="kt-region">
			<h2>{{ __("Before you start") }}</h2>
			<div class="bds-region-body">
				<ul class="bds-bullets">
					<li v-for="line in data.before_you_start" :key="line">{{ line }}</li>
				</ul>
			</div>
		</div>

		<StartBidDialog v-if="starting && data.start" :tender="tender" :start="data.start" @close="starting = false" @started="started" />
		<QuestionDialog v-if="asking" :tender="tender" :organisation="data.organisation" @close="asking = false" @sent="load" />
	</div>
	<div v-else-if="failure" class="kt-page">
		<div class="kt-notice is-critical bds-load-failure" role="alert">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="kt-btn kt-btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>
	</div>
	<div v-else class="kt-page" aria-hidden="true"><div class="bds-skeleton" data-testid="bds-overview-loading"></div></div>
</template>
