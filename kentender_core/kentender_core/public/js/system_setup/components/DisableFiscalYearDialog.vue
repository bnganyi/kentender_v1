<script setup>
// CFG-CHG-002 v0.11 §10.3 (C02 "disable") / CFG11-CHG-003 — disable is
// blocked while a KenTender-owned blocker applies (the primary control is
// disabled and names the exact blocker, never a generic denial); otherwise
// it is a plain, non-destructive-styled confirmation. History and shared
// records are retained either way (§7 `SetFiscalYearDisabled`).
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
	row: { type: Object, required: true },
	blockers: { type: Array, default: () => [] },
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const field = ref(null);
onMounted(async () => {
	await nextTick();
	field.value?.focus();
});
</script>

<template>
	<div class="kt-dialog-backdrop">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="blockers.length ? __('This financial year cannot be disabled') : __('Disable {0}?', [row.label])"
			data-testid="kt-fy-disable"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<template v-if="blockers.length">
				<h2 class="kt-dialog-title">{{ __("This financial year cannot be disabled") }}</h2>
				<p v-for="(blocker, index) in blockers" :key="index" class="kt-confirm-body" data-testid="kt-fy-disable-blocker">
					{{ blocker }}
				</p>
			</template>
			<template v-else>
				<h2 class="kt-dialog-title">{{ __("Disable {0}?", [row.label]) }}</h2>
				<p class="kt-confirm-body">{{ __("This year will be unavailable for new use.") }}</p>
			</template>
			<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button ref="field" type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="busy || !!blockers.length"
					data-testid="kt-fy-disable-confirm"
					@click="emit('confirm')"
				>{{ __("Disable financial year") }}</button>
			</div>
		</div>
	</div>
</template>
