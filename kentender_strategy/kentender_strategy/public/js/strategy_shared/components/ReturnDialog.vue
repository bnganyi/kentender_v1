<script setup>
// STR-DES-06-Return / §11.9 — "What needs to change?": one required field,
// Correction required, 10–500 characters, Cancel / Return for correction.
// The reason is recorded verbatim by return_strategy_version; nothing else
// is asked (no Reject, no score, no approval opinion form).
import { ref, computed, nextTick, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	busy: { type: Boolean, default: false },
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const MIN = 10;
const MAX = 500;
const reason = ref("");
const input = ref(null);
const length = computed(() => reason.value.trim().length);
const valid = computed(() => length.value >= MIN && length.value <= MAX);

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		reason.value = "";
		await nextTick();
		input.value?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" tabindex="-1" @keydown="onKeydown">
		<div class="kt-dialog" role="dialog" aria-modal="true" style="width: 520px" data-testid="str-return-dialog">
			<h2 class="kt-dialog-title">{{ __("What needs to change?") }}</h2>
			<div class="kt-field" style="margin: 0">
				<label for="str-return-reason">{{ __("Correction required") }}</label>
				<textarea
					id="str-return-reason"
					ref="input"
					v-model="reason"
					class="kt-input"
					rows="4"
					style="height: auto"
					:maxlength="MAX"
					data-testid="str-confirm-reason"
					:placeholder="__('Explain how the revised target will be measured and confirm the date these changes should take effect.')"
				></textarea>
				<div class="kt-field-hint" data-testid="str-return-count">{{ __("{0}–{1} characters", [MIN, MAX]) }} · {{ length }}</div>
				<p v-if="error" class="kt-field-error" data-testid="str-return-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary kt-danger"
					:disabled="!valid || busy"
					data-testid="str-confirm-ok"
					@click="$emit('confirm', reason.trim())"
				>
					{{ __("Return for correction") }}
				</button>
			</div>
		</div>
	</div>
</template>
