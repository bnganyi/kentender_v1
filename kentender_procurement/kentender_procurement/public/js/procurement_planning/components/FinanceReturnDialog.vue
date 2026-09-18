<!-- §10.9 U10-RETURN — the dialog is headed by the question the Officer is
     answering, names the whole plan as its read-only context, and asks for one
     actionable reason. No reservation is created. No reason category,
     attachment, assignee, due date or optional note (§11.17's own absences
     apply here too). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="fnt-return-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="fnt-return-title">
			<div id="fnt-return-title" class="kt-dialog-title">What needs to change?</div>
			<div class="kt-meta-row">
				<div>
					<span class="kt-label">Applies to</span>
					<span class="kt-meta-value" data-testid="fnt-return-context">Whole annual plan</span>
				</div>
			</div>
			<p class="pln-dialog-lede">
				No reservation is created. State the correction required.
			</p>
			<div class="pln-field">
				<label for="fnt-return-reason">Reason</label>
				<textarea
					id="fnt-return-reason" class="kt-input" rows="3"
					data-testid="fnt-return-reason" v-model="reason"
				></textarea>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="fnt-return-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="fnt-return-confirm"
					:disabled="pending || reason.trim().length < 10"
					@click="$emit('confirm', reason.trim())"
				>
					Return to planner
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
