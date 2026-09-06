<script setup>
// AUTH-ADR-001 v1.6 §13.8/§14.4 — one explicit action with a required reason.
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
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Revoke responsibility?')"
			data-testid="kt-ura-revoke"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ __("Revoke responsibility?") }}</h2>
			<p class="kt-revoke-body">
				{{ __("{0} will immediately lose {1} authority for {2}. Existing decisions and audit history will remain unchanged.",
					[assignment.user_full_name, assignment.business_role, assignment.organisation_unit_label || __("the entire entity")]) }}
			</p>
			<div class="kt-field">
				<label for="kt-revoke-reason">{{ __("Reason for revocation") }}</label>
				<textarea
					id="kt-revoke-reason"
					ref="field"
					v-model="reason"
					class="kt-input kt-textarea"
					rows="3"
					:maxlength="REASON_MAX"
					data-testid="kt-ura-revoke-reason"
				/>
				<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary kt-danger"
					:disabled="busy || reason.trim().length < REASON_MIN"
					data-testid="kt-ura-revoke-confirm"
					@click="emit('confirm', reason.trim())"
				>{{ __("Revoke responsibility") }}</button>
			</div>
		</div>
	</div>
</template>
