<!-- TPR-DES-13 Requisition correction — the "Correction requested" and
     "Corrected successor ready" states (the "Returned" state is the editor
     with its returned notice; the request dialog is ReasonDialog). -->
<template>
	<div class="tnd-page tnd-page--narrow" data-screen-label="TPR-DES-13 Requisition correction">
		<BlueprintCard>
			<template v-if="successor">
				<div class="tnd-head">
					<h1 class="tnd-h1" style="margin-bottom: 6px" data-testid="tnd-record-title">{{ tender.title }}</h1>
					<p class="tnd-refs tnd-refs--last">{{ successor.requisition_reference }}</p>
				</div>
				<div class="tnd-section">
					<div class="kt-notice is-live" data-testid="tnd-successor-ready">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
						<div class="kt-notice-body"><strong>A corrected requisition is ready.</strong></div>
					</div>
				</div>
				<div class="tnd-section tnd-grid-2">
					<div class="tnd-fact"><div class="kt-label">Requisition Version {{ correction.version_number || 1 }}</div><div class="tnd-fact-value">Stopped · {{ correction.reason }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requisition Version {{ successor.requisition_version_number || successor.requisition_version }}</div><div class="tnd-fact-value">Authorised · corrected requisition{{ successor.authorised_at ? " · " + successor.authorised_at : "" }}</div></div>
				</div>
				<div class="tnd-section tnd-section--last">
					<p class="tnd-small tnd-muted-700" style="margin: 0 0 16px">Starting continues into a new Draft Version {{ (correction.version_number || 1) + 1 }}. Version {{ correction.version_number || 1 }} remains stopped and unchanged in history.</p>
					<button v-if="canStart" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-start-corrected" @click="$emit('start-corrected', successor.handoff)">Start corrected Tender Version</button>
					<span v-else class="tnd-status-text">Only a Procurement Officer can start the corrected Tender Version.</span>
				</div>
			</template>
			<template v-else>
				<RecordHead :title="tender.title" badge="Requisition correction requested" badge-tone="is-critical" :refs="tender.tender_reference" />
				<div class="tnd-section">
					<div class="kt-notice is-critical" data-testid="tnd-cannot-continue">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
						<div class="kt-notice-body"><strong>This Tender cannot continue.</strong></div>
					</div>
				</div>
				<div class="tnd-section tnd-grid-2" data-testid="tnd-correction-facts">
					<div class="tnd-fact"><div class="kt-label">Requested by</div><div class="tnd-fact-value">{{ correction.requested_by_name }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requested at</div><div class="tnd-fact-value">{{ correction.requested_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Reason</div><div class="tnd-fact-value">{{ correction.reason }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requisition</div><div class="tnd-fact-value">{{ requisition.reference }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Current owner</div><div class="tnd-fact-value">{{ ownerLabel }}</div></div>
				</div>
				<div class="tnd-section tnd-section--last tnd-actions">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-view-requisition" @click="$emit('view-requisition', requisition.name)">View requisition status</button>
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-view-history" @click="$emit('history')">View history</button>
				</div>
			</template>
		</BlueprintCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	pending: Boolean,
});
defineEmits(["start-corrected", "view-requisition", "history"]);

const tender = computed(() => props.record.tender || {});
const correction = computed(() => props.record.correction || {});
const requisition = computed(() => correction.value.requisition || {});
const successor = computed(() => correction.value.successor || null);
const canStart = computed(() => (props.record.allowed_actions || []).includes("start_corrected_tender_version"));
const ownerLabel = computed(() => {
	const state = requisition.value.state || "";
	if (/authorised/i.test(state)) return "Head of Procurement Function";
	if (/procurement/i.test(state)) return "Head of Procurement Function";
	if (/department/i.test(state)) return "Head of User Department";
	return requisition.value.owner_label || state || "Requisition owner";
});
</script>
