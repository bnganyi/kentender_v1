<!-- TPR-DES-02 Start Tender dialog (520px), ported class-for-class over the
     blurred workspace: the six facts, the Supported/Unsupported verdict, the
     two disclosures, and Start Tender — disabled, with the reason shown,
     when the requisition is unsupported or the actor cannot start. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="tnd-start-dialog" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog tnd-dialog--start" role="dialog" aria-modal="true" aria-labelledby="tnd-start-title" tabindex="-1" data-screen-label="TPR-DES-02 Start Tender dialog">
			<div id="tnd-start-title" class="kt-dialog-title">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/></svg>
				Start this Tender?
			</div>
			<div class="tnd-dialog-body">
				<p style="margin: 0 0 16px">A Draft Tender will be created from the authorised requisition below.</p>
				<div class="tnd-grid-2 tnd-grid-2--dialog">
					<div class="tnd-fact"><div class="kt-label">Purchase</div><div class="tnd-fact-value" data-testid="tnd-start-purchase">{{ summary.purchase }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Requisition</div><div class="tnd-fact-value">{{ summary.requisition_reference }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Quantity</div><div class="tnd-fact-value">{{ summary.quantity }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Approved value</div><div class="tnd-fact-value">{{ summary.approved_value }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Method</div><div class="tnd-fact-value">{{ summary.method }}</div></div>
					<div class="tnd-fact"><div class="kt-label">Latest delivery</div><div class="tnd-fact-value">{{ summary.latest_delivery }}</div></div>
				</div>

				<template v-if="detail.supported">
					<div class="kt-notice is-live" style="margin-bottom: 14px" data-testid="tnd-start-supported">
						<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 6L9 17l-5-5"/></svg>
						<div class="kt-notice-body"><strong>Supported</strong> — IT equipment using the standard Open Tender format.</div>
					</div>
					<div class="kt-disclosure" style="margin-bottom: 10px">
						<div class="kt-disclosure-head" role="button" tabindex="0" @click="whyOpen = !whyOpen" @keydown.enter.prevent="whyOpen = !whyOpen">
							<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Why this requisition is supported</span></div>
							<svg class="kt-disclosure-chevron" :class="{ 'is-open': whyOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"/></svg>
						</div>
						<div v-if="whyOpen" class="kt-disclosure-body">
							<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; font-size: 13px" data-testid="tnd-start-checks">
								<div v-for="c in detail.compatibility" :key="c.check">{{ c.check }}: {{ c.actual }}</div>
							</div>
						</div>
					</div>
					<div class="kt-disclosure">
						<div class="kt-disclosure-head" role="button" tabindex="0" @click="templateOpen = !templateOpen" @keydown.enter.prevent="templateOpen = !templateOpen">
							<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Template and source details</span></div>
							<svg class="kt-disclosure-chevron" :class="{ 'is-open': templateOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"/></svg>
						</div>
						<div v-if="templateOpen" class="kt-disclosure-body">
							<div style="font-size: 13px">Template: {{ template.display_name }} · Version {{ template.template_version }}<br />Official source: {{ summary.requisition_reference }}</div>
						</div>
					</div>
				</template>

				<div v-else class="kt-notice is-critical" data-testid="tnd-start-unsupported">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
					<div class="kt-notice-body">{{ detail.result_text || "This requisition is not supported by the current IT-equipment Tender format." }}<span v-if="failedCheck"> ({{ failedCheck.check }}: {{ failedCheck.actual }})</span></div>
				</div>
				<p v-if="error" class="tnd-field-error" role="alert" data-testid="tnd-start-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="tnd-start-cancel" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!detail.can_start || pending" :title="detail.can_start ? '' : 'Only a Procurement Officer can start a supported requisition.'" data-testid="tnd-start-confirm" @click="$emit('confirm')">Start Tender</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({
	detail: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: { type: String, default: "" },
});
defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const whyOpen = ref(false);
const templateOpen = ref(false);
const summary = computed(() => props.detail.summary || {});
const template = computed(() => props.detail.template || {});
const failedCheck = computed(() => (props.detail.compatibility || []).find((c) => !c.ok) || null);

onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
