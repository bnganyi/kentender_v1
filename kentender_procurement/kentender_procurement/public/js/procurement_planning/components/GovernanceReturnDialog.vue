<!-- PLN-DES-15 — the two governance return dialogs, differing only in their
     title/intro text (served by the read model per stage, DES-15's exact
     copy). Required multiline "Correction required"; no reason category,
     attachment, assignee, due date or optional note (§11.17). -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pgt-return-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pgt-return-title">
			<div id="pgt-return-title" class="kt-dialog-title">{{ dialog.title }}</div>
			<p class="pln-dialog-lede">{{ dialog.lede }}</p>
			<div class="pln-field">
				<label for="pgt-return-reason">Correction required</label>
				<textarea
					id="pgt-return-reason" class="kt-input" rows="3"
					data-testid="pgt-return-reason" v-model="reason"
				></textarea>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pgt-return-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pgt-return-confirm"
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
	dialog: { type: Object, default: () => ({ title: "Return Plan Version for correction?", lede: "" }) },
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
