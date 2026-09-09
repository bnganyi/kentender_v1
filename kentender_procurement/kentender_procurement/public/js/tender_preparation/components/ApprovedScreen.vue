<!-- TPR-DES-06 Approved Tender (§13.8): the notice, approver and time,
     digests, publication-handoff status, both renders, the structured
     mappings, and Reopen before publication (Head of Procurement Function,
     only while unconsumed). No edit action. -->
<template>
	<div>
		<div style="margin-bottom: 24px">
			<div class="tpr-cap">{{ tender.tender_reference }} · Version {{ tender.version_number }}</div>
			<h1 class="kt-page-title" style="font-size: 28px; margin: 4px 0">{{ tender.requirement_title }}</h1>
			<span class="kt-status is-live">Approved for publication</span>
		</div>
		<p v-if="error" class="tpr-error-banner" role="alert">{{ error }}</p>
		<div class="kt-card kt-blueprint tpr-card-pad tpr-card-narrow" style="margin-bottom: 24px"><i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="tpr-card-kicker">Notice</div>
			<p class="tpr-card-body">{{ view.notice }}</p>
		</div>
		<div class="tpr-grid-3" style="margin-bottom: 24px">
			<div class="tpr-ro-field"><span class="kt-label">Approved by</span><span class="tpr-ro-val">{{ approvedBy.name }}, {{ approvedBy.at }}</span></div>
			<div class="tpr-ro-field"><span class="kt-label">Requisition digest</span><span class="tpr-ro-val tpr-mono">{{ shortDigest(binding.requisition_content_digest) }}</span></div>
			<div class="tpr-ro-field"><span class="kt-label">Template digest</span><span class="tpr-ro-val tpr-mono">{{ shortDigest(binding.bundle_digest) }}</span></div>
			<div class="tpr-ro-field"><span class="kt-label">Package digest</span><span class="tpr-ro-val tpr-mono">{{ shortDigest(handoff.package_digest) }}</span></div>
			<div class="tpr-ro-field"><span class="kt-label">Publication handoff</span><span class="tpr-ro-val">{{ handoff.status === "Ready" ? "Ready · not yet consumed" : handoff.status }}</span></div>
			<div class="tpr-ro-field"><span class="kt-label">Publication consumption</span><span class="kt-status" :class="handoff.consumed_at ? 'is-live' : 'is-pending'" data-testid="tpr-consumption-status">{{ handoff.consumed_at ? "Consumed " + handoff.consumed_at : "Awaiting downstream acknowledgment" }}</span></div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Complete renders</div>
			<div class="tpr-tags">
				<a class="tpr-tag is-outline" :href="files.invitation_pdf_file || '#'" target="_blank" rel="noopener">Invitation.pdf — digest verified</a>
				<a class="tpr-tag is-outline" :href="files.issued_tender_pdf_file || '#'" target="_blank" rel="noopener">Issued Tender.pdf — digest verified</a>
			</div>
		</div>
		<div class="tpr-section">
			<div class="kt-card-title">Structured mappings</div>
			<div class="tpr-tags">
				<span class="tpr-tag is-accent">Supplier-response schema · {{ mappings.supplier_response_schema ? "complete" : "missing" }}</span>
				<span class="tpr-tag is-accent">Evaluation contract · {{ mappings.evaluation_contract ? "complete" : "missing" }}</span>
				<span class="tpr-tag is-accent">Contract-obligation projection · {{ mappings.contract_obligations ? "complete" : "missing" }}</span>
			</div>
		</div>
		<div v-if="canReopen"><button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" data-testid="tpr-reopen" @click="$emit('reopen')">Reopen before publication</button></div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { shortDigest } from "../data/format.js";

const props = defineProps({ view: { type: Object, default: () => ({}) }, pending: Boolean, error: { type: String, default: "" } });
defineEmits(["reopen"]);
const tender = computed(() => props.view.tender || {});
const binding = computed(() => props.view.binding || {});
const handoff = computed(() => props.view.publication_handoff || {});
const approvedBy = computed(() => props.view.approved_by || {});
const files = computed(() => (props.view.renders || {}).files || {});
const mappings = computed(() => props.view.mappings || {});
const canReopen = computed(() => !!(props.view.permitted_actions || {}).can_reopen);
</script>
