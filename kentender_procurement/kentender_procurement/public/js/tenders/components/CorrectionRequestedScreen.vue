<!-- TPR-DES-13 Requisition correction (§10.14), ported class-for-class: the
     "Correction requested" state (the §10.17 waiting line on the
     Departmental Author replaces the "This Tender cannot continue" result;
     the request facts; View requisition status / View history as page
     links, never next-step actions) and the "Corrected successor available"
     state (Requisition Version 1 and 2 separately, the consequence of
     starting, and Start corrected Tender Version). The "Returned" state is
     the editor with its returned notice; the request dialog is ReasonDialog. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-13 Requisition correction">
		<BlueprintCard>
			<RecordHead :title="tender.title" :badge="successor ? '' : 'Requisition correction requested'" badge-tone="is-critical" :refs="refs" />
			<TenderGuidance :guidance="record.guidance || null" :pending="pending" @fix="$emit('fix', $event)" />
			<template v-if="successor">
				<div class="tnd-section tnd-fact-grid tnd-fact-grid--2" data-testid="tnd-successor-facts">
					<div class="tnd-fact"><div class="kt-label">Requisition Version {{ correction.basis_requisition_version_number || 1 }}</div><div class="tnd-fact-value">Basis of stopped Tender Version {{ correction.version_number }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requisition Version {{ successor.requisition_version_number || "" }}</div><div class="tnd-fact-value">Authorised{{ successor.authorised_at_label ? ` ${successor.authorised_at_label}` : "" }}</div></div>
				</div>
				<div class="tnd-section tnd-section--last">
					<p class="tnd-body-text" data-testid="tnd-successor-consequence">Starting creates a new Draft Version {{ (correction.version_number || 1) + 1 }}. Version {{ correction.version_number || 1 }} stays stopped and unchanged in history.</p>
				</div>
			</template>
			<template v-else>
				<div class="tnd-section tnd-fact-grid" data-testid="tnd-correction-facts">
					<div class="tnd-fact"><div class="kt-label">Requested by</div><div class="tnd-fact-value">{{ correction.requested_by_name }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requested at</div><div class="tnd-fact-value">{{ correction.requested_at_label }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Stopped Version</div><div class="tnd-fact-value">Version {{ correction.version_number }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Current owner</div><div class="tnd-fact-value">{{ correction.owner_label || "Requisition owner" }}</div></div>
					<div class="tnd-fact tnd-span-4"><div class="kt-label">Reason</div><div class="tnd-fact-value">{{ correction.reason }}</div></div>
				</div>
				<div class="tnd-section tnd-section--last tnd-actions">
					<a href="#" class="tnd-page-link" data-testid="tnd-view-requisition" @click.prevent="$emit('view-requisition', requisition.name)">View requisition status</a>
					<a href="#" class="tnd-page-link" data-testid="tnd-view-history" @click.prevent="$emit('history')">View history</a>
				</div>
			</template>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back to Tenders</a>
			<button v-if="successor && canStart" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-start-corrected" @click="$emit('start-corrected', successor.handoff)">Start corrected Tender Version</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	pending: Boolean,
});
defineEmits(["start-corrected", "view-requisition", "history", "back", "fix"]);

const tender = computed(() => props.record.tender || {});
const correction = computed(() => props.record.correction || {});
const requisition = computed(() => correction.value.requisition || {});
const successor = computed(() => correction.value.successor || null);
const refs = computed(() => [tender.value.tender_reference, tender.value.requisition_reference].filter(Boolean).join(" · "));
const canStart = computed(() => (props.record.allowed_actions || []).includes("start_corrected_tender_version"));
</script>
