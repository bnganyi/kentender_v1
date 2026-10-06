<!-- TPR-DES-06 HOPF approval (§10.7), ported class-for-class: the header
     (no awaiting-action badge), the §10.17 guidance region — Your turn to
     decide, or the waiting line that explains a segregation block — the
     review note, the submitted-by row, key facts, previews, the six
     read-only sections and the footer with Return / Approve, absent when the
     server does not permit the decision. -->
<template>
	<div class="tnd-page" data-screen-label="TPR-DES-06 HOPF approval">
		<BlueprintCard>
			<RecordHead title="Review Tender package" :refs="refs" lede="Decide whether this Tender may proceed to Accounting Officer publication review." />
			<TenderGuidance :guidance="review.guidance || record.guidance || null" :pending="pending" />
			<ReviewNote :notes="(review.review || {}).review_notes || []" @go="openNote" />
			<div class="tnd-section tnd-section--tight tnd-fact-grid tnd-fact-grid--3" data-testid="tnd-submitted-row">
				<div class="tnd-fact"><div class="kt-label">Submitted by</div><div class="tnd-fact-value">{{ version.submitted_by_name }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Submitted at</div><div class="tnd-fact-value">{{ version.submitted_at_label }}</div></div>
				<div class="tnd-fact"><div class="kt-label">Version</div><div class="tnd-fact-value">Version {{ version.version_number }}</div></div>
			</div>
			<KeyFacts :facts="review.key_facts || []" />
			<div class="tnd-section tnd-section--tight tnd-actions">
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-invitation" @click="$emit('preview', 'invitation')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></svg>Preview Invitation</button>
				<button type="button" class="btn btn-secondary tnd-inline-btn" :disabled="pending" data-testid="tnd-preview-complete" @click="$emit('preview', 'complete')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>Preview complete Tender</button>
			</div>
			<div class="tnd-section tnd-section--content tnd-section--last">
				<ContentSections ref="sectionsRef" :sections="review.sections || []" />
			</div>
		</BlueprintCard>
		<div class="tnd-footer">
			<div class="tnd-actions" style="align-items: center">
				<a href="#" class="tnd-footer-back" data-testid="tnd-back" @click.prevent="$emit('back')">Back to Tenders</a>
				<button v-if="canRequestCorrection" type="button" class="btn btn-ghost" :disabled="pending" data-testid="tnd-request-correction" @click="$emit('request-correction')">Request requisition correction</button>
			</div>
			<div v-if="canDecide" class="tnd-actions">
				<button type="button" class="btn btn-secondary" :disabled="pending" data-testid="tnd-return-for-correction" @click="$emit('return')">Return for correction</button>
				<button type="button" class="btn btn-primary" :disabled="pending" data-testid="tnd-approve-package" @click="$emit('approve')">Approve Tender package</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import BlueprintCard from "./BlueprintCard.vue";
import RecordHead from "./RecordHead.vue";
import TenderGuidance from "./TenderGuidance.vue";
import ReviewNote from "./ReviewNote.vue";
import KeyFacts from "./KeyFacts.vue";
import ContentSections from "./ContentSections.vue";

const props = defineProps({
	record: { type: Object, default: () => ({ tender: {} }) },
	review: { type: Object, default: () => ({}) },
	pending: Boolean,
});
defineEmits(["back", "return", "approve", "preview", "request-correction"]);

const sectionsRef = ref(null);
const refs = computed(() => `${props.record.tender.tender_reference} · ${props.record.tender.requisition_reference}`);
const version = computed(() => props.record.version || {});
const canDecide = computed(() => (props.record.allowed_actions || []).includes("approve_tender_package"));
const canRequestCorrection = computed(() => (props.record.allowed_actions || []).includes("request_requisition_correction"));
// The HOPF reviews, never edits: a review note's link opens its section in place.
function openNote(note) {
	const key = note.field && /inspection|payment|performance|delay|contract_contact/.test(note.field) ? "contract" : note.task === "details" ? "details" : "supplier";
	if (sectionsRef.value) sectionsRef.value.openSection(key);
}
</script>
