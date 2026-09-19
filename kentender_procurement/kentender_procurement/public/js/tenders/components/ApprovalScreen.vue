<!-- TPR-DES-06 HOPF approval, ported class-for-class: head, the Ready to
     approve / segregation notice, review notes, the submitted-by row, key
     facts, previews, the six sections, and the footer with Return /
     Approve — absent entirely when segregation blocks the actor. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-06 HOPF approval">
		<BlueprintCard>
			<RecordHead title="Review Tender package" :badge="record.tender.badge" :refs="refs" lede="Decide whether this Tender may proceed to Accounting Officer publication review." />
			<div class="tnd-section">
				<div v-if="record.segregation_message" class="kt-notice is-critical" data-testid="tnd-segregation">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body"><strong>{{ segregationHead }}</strong> {{ segregationTail }}</div>
				</div>
				<div v-else class="kt-notice is-live" data-testid="tnd-ready-to-approve">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
					<div class="kt-notice-body"><strong>Ready to approve.</strong> Approval locks this package for the Accounting Officer's publication decision. It does not publish the Tender.</div>
				</div>
			</div>
			<FindingsNotices :review="review.review || {}" :linkable="false" />
			<div class="tnd-section tnd-section--tight tnd-grid-3" data-testid="tnd-submitted-row">
				<div class="tnd-fact"><div class="kt-label">Submitted by</div><div class="tnd-fact-value">{{ version.submitted_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Submitted at</div><div class="tnd-fact-value">{{ version.submitted_at_label }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Version</div><div class="tnd-fact-value">Version {{ version.version_number }}</div></div>
			</div>
			<KpiFacts :facts="review.key_facts || []" />
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-invitation" @click="$emit('preview', 'invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>Preview Invitation</button>
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-complete" @click="$emit('preview', 'complete')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>Preview complete Tender</button>
			</div>
			<div class="tnd-section tnd-section--content">
				<ContentSections :sections="review.sections || []" :findings="(review.review || {}).findings || []" />
			</div>
		</BlueprintCard>
		<div class="tnd-footer">
			<div class="tnd-actions" style="align-items: center">
				<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
				<button v-if="canRequestCorrection" type="button" class="kt-btn kt-btn-ghost" :disabled="pending" data-testid="tnd-request-correction" @click="$emit('request-correction')">Request requisition correction</button>
			</div>
			<div v-if="canDecide" class="tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tnd-return-for-correction" @click="$emit('return')">Return for correction</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-approve-package" @click="$emit('approve')">Approve Tender package</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import FindingsNotices from "./FindingsNotices.vue";
import KpiFacts from "./KpiFacts.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	review: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["back", "return", "approve", "preview", "request-correction"]);

const refs = computed(() => `${props.record.tender.tender_reference} · ${props.record.tender.requisition_reference}`);
const version = computed(() => props.record.version || {});
const canDecide = computed(() => (props.record.allowed_actions || []).includes("approve_tender_package"));
const canRequestCorrection = computed(() => (props.record.allowed_actions || []).includes("request_requisition_correction"));
const segregationHead = computed(() => (props.record.segregation_message || "").split(". ")[0] + ".");
const segregationTail = computed(() => (props.record.segregation_message || "").split(". ").slice(1).join(". "));
</script>
