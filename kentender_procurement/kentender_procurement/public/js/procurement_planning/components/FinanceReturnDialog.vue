<!-- §12.9 — Return to planner requires one actionable correction reason and
     creates no reservation. No artboard names this dialog; it follows the
     same title/intro/required-multiline/Cancel+Return shape PLN-DES-15 uses
     for the two governance return dialogs (§11.17), adapted to Finance's
     own copy. No reason category, attachment, assignee, due date or
     optional note (§11.17's own absences apply here too). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="fnt-return-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="fnt-return-title">
			<div id="fnt-return-title" class="kt-dialog-title">Return to planner?</div>
			<p class="pln-dialog-lede">
				No reservation is created. State the correction required.
			</p>
			<div class="pln-field">
				<label for="fnt-return-reason">Correction required</label>
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
					Return for correction
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
