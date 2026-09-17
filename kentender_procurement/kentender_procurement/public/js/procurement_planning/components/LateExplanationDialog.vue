<!-- PLN-CHG-001 v1.18 §7.2, ported class-for-class from U21-late-explanation.
     Confirms `RecordLateActivationExplanation` for an initial Plan Version
     adopted after its financial year began; the caller owns the actual API
     call, idempotency key, and the three fact values (already formatted via
     data/format.js's formatEat). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-late-explanation-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-late-explanation-title">
			<div id="pln-late-explanation-title" class="kt-dialog-title">Record late activation explanation</div>
			<div class="pln-facts-row">
				<div class="pln-fact">
					<span class="kt-label">Initial Plan Version</span>
					<span class="pln-fact-val">{{ initialVersion }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Financial year started</span>
					<span class="pln-fact-val">{{ financialYearStarted }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Activated</span>
					<span class="pln-fact-val">{{ activatedAt }}</span>
				</div>
			</div>
			<div class="pln-field">
				<label for="pln-late-explanation-reason">Explanation</label>
				<input
					id="pln-late-explanation-reason" class="kt-input" type="text"
					data-testid="pln-late-explanation-reason" v-model="reason"
				>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-late-explanation-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-late-explanation-confirm"
					:disabled="pending || reason.trim().length === 0"
					@click="$emit('confirm', reason.trim())"
				>
					Record explanation
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	initialVersion: { type: [String, Number], default: "" },
	financialYearStarted: { type: String, default: "" },
	activatedAt: { type: String, default: "" },
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
