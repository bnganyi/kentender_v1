<!-- TPR-DES-05 Review and submit (§10.6), ported class-for-class: the
     header, the §10.17 guidance region (Your turn to submit, or Your turn,
     blocked naming each must-fix item with its fix — it replaces the old
     result notice and the must-fix notices), the separate review-note
     notice, key facts, the two previews, the six content sections and the
     sticky footer. Submit is shown only while the server permits it; a
     blocked review explains itself in the guidance, not in the footer. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-05 Review and submit">
		<BlueprintCard>
			<RecordHead title="Review Tender" :badge="record.tender.badge" :refs="refs" lede="Check the complete Tender and submit it to the Head of Procurement Function." />
			<TenderGuidance :guidance="review.guidance || null" :pending="pending" @fix="$emit('fix', $event)" />
			<div v-if="notes.length" class="tnd-section tnd-section--plain" data-testid="tnd-review-notes">
				<div class="kt-notice is-attention">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
					<div class="kt-notice-body"><strong>{{ notes.length }} review note{{ notes.length === 1 ? "" : "s" }}.</strong> {{ notes.map((n) => n.message).join(" ") }} <button v-if="notes[0].link_label" type="button" class="tnd-link-btn" data-testid="tnd-review-note-link" @click="$emit('go-finding', notes[0])">{{ notes[0].link_label }}</button></div>
				</div>
			</div>
			<KeyFacts :facts="review.key_facts || []" />
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-invitation" @click="$emit('preview', 'invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>Preview Invitation</button>
				<button type="button" class="kt-btn kt-btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-complete" @click="$emit('preview', 'complete')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>Preview complete Tender</button>
			</div>
			<div class="tnd-section tnd-section--content tnd-section--last">
				<ContentSections :sections="review.sections || []" />
			</div>
		</BlueprintCard>
		<div class="tnd-footer">
			<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back</a>
			<button v-if="canSubmit" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="tnd-submit-for-approval" @click="$emit('submit')">Submit for approval</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";
import KeyFacts from "./KeyFacts.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	review: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["back", "submit", "preview", "go-finding", "fix"]);

const refs = computed(() => `${props.record.tender.tender_reference} · ${props.record.tender.requisition_reference}`);
const notes = computed(() => (props.review.review || {}).review_notes || []);
const canSubmit = computed(() => (props.review.allowed_actions || props.record.allowed_actions || []).includes("submit_for_approval"));
</script>
