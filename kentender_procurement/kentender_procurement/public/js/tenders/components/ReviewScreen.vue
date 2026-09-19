<!-- TPR-DES-05 Review and submit, ported class-for-class: head, the three
     task cards (Review and submit selected), the result notice (Ready to
     submit / Needs attention), every finding with its route, key facts, the
     two previews, the six content sections and the sticky footer whose
     Submit is disabled with the reason while a Must fix stands. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-05 Review and submit">
		<BlueprintCard>
			<RecordHead title="Review Tender" :badge="record.tender.badge" :refs="refs" lede="Check the complete Tender and submit it to the Head of Procurement Function." />
			<div class="tnd-task-cards" data-testid="tnd-task-cards">
				<div class="kt-card kt-blueprint tnd-task-card"><div class="kt-label">Tender details</div><span class="kt-status" :class="taskClass(tasks.details)">{{ tasks.details }}</span></div>
				<div class="kt-card kt-blueprint tnd-task-card"><div class="kt-label">Supplier and contract requirements</div><span class="kt-status" :class="taskClass(tasks.requirements)">{{ tasks.requirements }}</span></div>
				<div class="kt-card kt-blueprint tnd-task-card is-selected"><div class="kt-label">Review and submit</div><span class="kt-status is-pending">Selected</span></div>
			</div>
			<div class="tnd-section">
				<div v-if="blocked" class="kt-notice is-critical" data-testid="tnd-review-result-blocked">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body"><strong>Needs attention.</strong></div>
				</div>
				<div v-else class="kt-notice is-live" data-testid="tnd-review-result-ready">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
					<div class="kt-notice-body"><strong>Ready to submit.</strong> All required information is complete. Review the note below before submitting.</div>
				</div>
			</div>
			<FindingsNotices :review="review.review || {}" @go="$emit('go-finding', $event)" />
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
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
			<div class="tnd-footer-stack">
				<span v-if="blocked" class="tnd-warn-text" data-testid="tnd-submit-blocked-text">{{ review.submit_blocked_text || "Fix the item above before submitting." }}</span>
				<button v-if="canSubmit || blocked" type="button" class="kt-btn kt-btn-primary" :disabled="blocked || pending" data-testid="tnd-submit-for-approval" @click="$emit('submit')">Submit for approval</button>
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
defineEmits(["back", "submit", "preview", "go-finding"]);

const refs = computed(() => `${props.record.tender.tender_reference} · ${props.record.tender.requisition_reference}`);
const tasks = computed(() => props.record.tasks || {});
const blocked = computed(() => ((props.review.review || {}).must_fix_count || 0) > 0);
const canSubmit = computed(() => (props.review.allowed_actions || props.record.allowed_actions || []).includes("submit_for_approval"));
function taskClass(status) {
	return status === "Complete" ? "is-live" : status === "Needs attention" ? "is-attention" : "is-pending";
}
</script>
