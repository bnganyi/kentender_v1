<!-- PLN-CHG-001 v1.24 §10.10 U11-RETURN, ported from Artboards-U11.dc.html.
     Required multiline comment; no reason category, attachment, assignee,
     due date or optional note (§11.17). Every governance return is a
     whole-plan correction — ReturnPlanVersion takes no per-purchase target —
     so the artboard's illustrative Context selector names nothing the
     command consumes and is not built as a live control. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="rvw-return-dialog">
		<div class="kt-dialog" style="width: 520px" role="dialog" aria-modal="true" aria-labelledby="rvw-return-title">
			<div id="rvw-return-title" class="kt-dialog-title">What needs to change?</div>
			<div class="pln-field">
				<label for="rvw-return-reason">Comment</label>
				<textarea
					id="rvw-return-reason" class="kt-input" rows="4"
					data-testid="rvw-return-reason" v-model="reason"
				></textarea>
			</div>
			<p class="pln-dialog-lede">{{ dialog.lede }}</p>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="rvw-return-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="rvw-return-confirm"
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
