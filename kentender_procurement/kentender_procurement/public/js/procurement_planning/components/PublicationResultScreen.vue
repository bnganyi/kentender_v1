<!-- PLN-UI-13 Publication result (§12.11), rendering PLN-DES-13 class-for-
     class: the approved Version, destination, latest attempt, result and
     acknowledgement reference read-only, the quiet system-action notice, and
     — only for a technical user on a failed publication — "Retry exact
     approved payload", which edits nothing and creates no new approval. -->
<template>
	<div>
		<p class="kt-page-kicker">{{ task.header?.eyebrow }}</p>
		<h1 class="kt-page-title">{{ task.header?.title }}</h1>
		<p class="pln-quiet-ref">{{ task.header?.reference_line }}</p>
		<span class="kt-status" :class="badgeClass" data-testid="pub-badge">{{ task.header?.badge }}</span>

		<div v-if="errorSummary" class="pln-notice is-critical" role="alert" data-testid="pub-error">
			<p class="pln-notice-title">The retry could not be completed</p>
			<p>{{ errorSummary }}</p>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pub-approved-plan">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Approved Plan</div>
			<div class="pln-field-grid pln-field-grid-3">
				<div class="pln-ro-field"><label>Financial Year</label><div class="pln-val">{{ task.approved_plan?.financial_year }}</div></div>
				<div class="pln-ro-field"><label>Plan Items</label><div class="pln-val">{{ task.approved_plan?.plan_items }}</div></div>
				<div class="pln-ro-field"><label>Approved value</label><div class="pln-val">{{ task.approved_plan?.value_display }}</div></div>
				<div class="pln-ro-field"><label>Statutory approval</label><div class="pln-val">{{ task.approved_plan?.statutory_approval_line }}</div></div>
			</div>
		</div>

		<div class="kt-card kt-blueprint pln-card-pad" data-testid="pub-publication">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title">Publication</div>
			<div class="pln-field-grid pln-field-grid-3">
				<div class="pln-ro-field"><label>Destination</label><div class="pln-val">{{ task.destination?.title }}</div></div>
				<div class="pln-ro-field"><label>Configuration</label><div class="pln-val">{{ task.configuration }}</div></div>
				<div class="pln-ro-field"><label>Latest attempt</label><div class="pln-val">{{ task.attempted_display }}</div></div>
				<div class="pln-ro-field"><label>Result</label><div class="pln-val" data-testid="pub-result">{{ task.result_display }}</div></div>
				<div class="pln-ro-field"><label>Acknowledgement reference</label><div class="pln-val" data-testid="pub-reference">{{ task.acknowledgement_reference }}</div></div>
			</div>
		</div>

		<!-- PLN-DES-16 — publication was not acknowledged -->
		<div v-if="task.result === 'Failed'" class="kt-card kt-blueprint pln-state-card" data-testid="pub-failed">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h3>Publication was not acknowledged</h3>
			<p>The approved Plan is unchanged. Retry the same publication when the destination is available.</p>
			<button
				v-if="task.can_retry"
				type="button"
				class="kt-btn kt-btn-secondary"
				data-testid="pub-retry"
				:disabled="pending"
				@click="$emit('retry')"
			>
				Retry exact approved payload
			</button>
		</div>

		<p class="pln-quiet-notice" data-testid="pub-quiet-notice">{{ task.quiet_notice }}</p>

		<div class="pln-footer-bar">
			<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('back')">Back to Annual Plan</button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	task: { type: Object, default: () => ({}) },
	pending: Boolean,
	errorSummary: String,
});

defineEmits(["retry", "back"]);

const KIND_CLASS = { live: "is-live", critical: "is-critical", attention: "is-attention" };
const badgeClass = computed(() => KIND_CLASS[props.task.header?.badge_kind] || "is-attention");
</script>
