<!-- PLN-CHG-001 v1.23 §10.14 U21-LATE-ACTIVATION — `RecordLateActivation
     Explanation` for an initial Plan Version that only became active after
     its financial year had begun. The two facts are read-only and there is
     no editable date: nothing here may change when the year started or when
     the plan became active, only say why the gap exists. The caller owns the
     API call, the idempotency key and the already-formatted fact values. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-late-explanation-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-late-explanation-title">
			<div id="pln-late-explanation-title" class="kt-dialog-title">Explain late start of the annual plan</div>
			<div class="pln-facts-row">
				<div class="pln-fact">
					<span class="kt-label">Financial year started</span>
					<span class="pln-fact-val" data-testid="pln-late-explanation-year-started">{{ financialYearStarted }}</span>
				</div>
				<div class="pln-fact">
					<span class="kt-label">Plan became active</span>
					<span class="pln-fact-val" data-testid="pln-late-explanation-activated">{{ activatedAt }}</span>
				</div>
			</div>
			<div class="pln-field">
				<label for="pln-late-explanation-reason">Explanation</label>
				<textarea
					id="pln-late-explanation-reason" class="kt-input" rows="3"
					data-testid="pln-late-explanation-reason" v-model="reason"
				></textarea>
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
	financialYearStarted: { type: String, default: "" },
	activatedAt: { type: String, default: "" },
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
