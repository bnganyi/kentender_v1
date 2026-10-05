<script setup>
// BDS-CHG-001 v0.8 §10.20 BDS-DES-17 — Receipts at /account/receipts, ported
// from "Bid Board v3 - A" (1440 table; 390 labelled cards). A read-only
// recovery register of the active organisation's submission receipts and
// withdrawal acknowledgements, also for a suspended Account; no bid-change
// action, no prices or contents, no tracker (a Register, §10.19). Each row
// opens its own receipt or acknowledgement.
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { useNarrow } from "../composables/useNarrow.js";

const METHOD = "kentender_procurement.bid_submission.api.get_receipt_history";
const props = defineProps({ initial: { type: Object, default: null } });
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const narrow = useNarrow();
const data = ref(props.initial);
const failure = ref("");
const guard = portal.createSequenceGuard();
const rows = computed(() => (data.value && data.value.rows) || []);

function tone(row) {
	return row.event_tone ? `is-${row.event_tone}` : "";
}
async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(METHOD, { organisation: route.value.query.organisation || "" });
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
watch(epoch, () => load());
onMounted(() => {
	portal.setTitle(__("Receipts"));
	if (!data.value) load();
});
</script>

<template>
	<div class="kt-page" data-testid="bds-receipts">
		<div class="kt-page-head" :class="{ 'bds-head-stack': narrow }">
			<div class="bds-head-main">
				<a href="/account" class="bds-back" data-testid="bds-receipts-back"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5" /><path d="m12 19-7-7 7-7" /></svg>{{ __("Back to Account") }}</a>
				<div class="bds-title-row">
					<h1 class="kt-page-title">{{ __("Receipts") }}</h1>
					<span v-if="data && data.suspended" class="kt-status is-critical" data-testid="bds-receipts-suspended">{{ __("Account suspended") }}</span>
				</div>
				<p class="kt-page-desc">{{ __("View submission and withdrawal records for this supplier organisation.") }}</p>
			</div>
		</div>

		<div v-if="data && data.suspended" class="kt-notice is-warning" role="status">
			<svg class="kt-notice-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3" /><path d="M12 9v4" /><path d="M12 17h.01" /></svg>
			<div class="kt-notice-body"><div>{{ data.suspended_text }}</div></div>
		</div>
		<div v-if="failure" class="kt-notice is-critical bds-load-failure" role="alert" data-testid="bds-load-failure">
			<div class="kt-notice-body">{{ failure }}</div>
			<button type="button" class="btn btn-secondary" @click="load">{{ __("Try again") }}</button>
		</div>

		<template v-if="rows.length">
			<table v-if="!narrow" class="table" data-testid="bds-receipts-table">
				<thead>
					<tr>
						<th>{{ __("Tender") }}</th>
						<th>{{ __("Document") }}</th>
						<th>{{ __("Event") }}</th>
						<th>{{ __("Date and time EAT") }}</th>
						<th>{{ __("Action") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in rows" :key="row.document" :data-testid="'bds-receipt-row-' + row.document">
						<td class="bds-tender-cell">{{ row.tender_title }}<div class="kt-label bds-tender-ref">{{ row.tender_reference }}</div></td>
						<td>{{ row.document }}</td>
						<td><span class="kt-status" :class="tone(row)">{{ row.event }}</span></td>
						<td>{{ row.at_label }}</td>
						<td><a :href="row.href">{{ __("View") }}</a></td>
					</tr>
				</tbody>
			</table>
			<div v-else data-testid="bds-receipts-cards">
				<div v-for="row in rows" :key="row.document" class="bds-card" :data-testid="'bds-receipt-row-' + row.document">
					<div class="bds-card-title">{{ row.tender_title }}<div class="kt-label bds-tender-ref">{{ row.tender_reference }}</div></div>
					<div class="bds-card-fact"><span class="kt-label">{{ __("Document") }}</span><span>{{ row.document }}</span></div>
					<div class="bds-card-fact"><span class="kt-label">{{ __("Event") }}</span><span><span class="kt-status" :class="tone(row)">{{ row.event }}</span></span></div>
					<div class="bds-card-fact"><span class="kt-label">{{ __("Date and time EAT") }}</span><span>{{ row.at_label }}</span></div>
					<div class="bds-card-actions"><a :href="row.href">{{ __("View") }}</a></div>
				</div>
			</div>
			<p class="bds-count" data-testid="bds-receipts-count">{{ data.count_text }}</p>
		</template>
		<div v-else-if="data" class="kt-empty" data-testid="bds-receipts-empty">
			<p class="bds-empty-text">{{ data.empty_text }}</p>
			<a href="/account" class="btn btn-secondary" :class="{ 'bds-btn-touch': narrow }">{{ __("Back to Account") }}</a>
		</div>
		<div v-else-if="!failure" class="bds-skeleton" aria-hidden="true" data-testid="bds-receipts-loading"></div>
	</div>
</template>
