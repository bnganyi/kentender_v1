<script setup>
// AUTH-DES-07, ported from C06 #auth-des-07 — one explicit action with a
// required reason.
// Built in-Vue rather than with frappe.confirm(), which renders outside the
// Vue root and inherits neither its state nor its Industry styles.
import { nextTick, onMounted, ref } from "vue";

defineProps({
	assignment: { type: Object, required: true },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const REASON_MIN = 10;
const REASON_MAX = 500;
const reason = ref("");
const field = ref(null);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});
</script>

<template>
	<div class="dialog-backdrop">
		<div
			class="dialog kt-narrow"
			role="alertdialog"
			aria-modal="true"
			aria-labelledby="kt-revoke-title"
			data-testid="kt-ura-revoke"
			@keydown.esc.stop="emit('cancel')"
		>
			<h2 id="kt-revoke-title" class="dialog-title">{{ __("Revoke responsibility?") }}</h2>
			<div class="dialog-body" style="display:flex;flex-direction:column;gap:14px">
				<p style="margin:0">
					{{ __("{0} will immediately lose {1} authority for {2}. Existing decisions and audit history will remain unchanged.",
						[assignment.user_full_name, assignment.business_role, assignment.organisation_unit_label || __("the entire entity")]) }}
				</p>
				<div class="field">
					<label for="kt-revoke-reason">{{ __("Reason for revocation") }}</label>
					<textarea
						id="kt-revoke-reason"
						ref="field"
						v-model="reason"
						class="input kt-textarea"
						rows="3"
						:maxlength="REASON_MAX"
						data-testid="kt-ura-revoke-reason"
					/>
				</div>
				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="kt-ura-revoke-error">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ error }}</div>
				</div>
			</div>
			<div class="dialog-actions">
				<button type="button" class="btn btn-secondary" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="btn btn-primary kt-danger"
					:disabled="busy || reason.trim().length < REASON_MIN"
					data-testid="kt-ura-revoke-confirm"
					@click="emit('confirm', reason.trim())"
				>{{ __("Revoke responsibility") }}</button>
			</div>
		</div>
	</div>
</template>
