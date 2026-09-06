<script setup>
// CFG-DES-04 — one numeric input; the summary is the server's preview, never
// composed here (§11.3: dates are never user-entered).
import { nextTick, onMounted, ref, watch } from "vue";
import { siteConfigApi } from "../data/siteConfigApi.js";

defineProps({
	error: { type: String, default: "" },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const startYear = ref("");
const preview = ref(null);
const field = ref(null);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});

let token = 0;
watch(startYear, async (value) => {
	preview.value = null;
	if (!/^\d{4}$/.test(value || "")) return;
	const current = ++token;
	try {
		const result = await siteConfigApi.previewFiscalYear(Number(value));
		if (current === token) preview.value = result;
	} catch (e) {
		if (current === token) preview.value = null;
	}
});
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div
			class="kt-dialog kt-blueprint kt-narrow"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Add financial year')"
			data-testid="kt-fy-add"
			@keydown.esc="emit('cancel')"
		>
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ __("Add financial year") }}</h2>
			<div class="kt-dialog-fields">
				<div class="kt-field">
					<label for="kt-fy-start">{{ __("Start year") }}</label>
					<input
						id="kt-fy-start"
						ref="field"
						v-model="startYear"
						class="kt-input"
						inputmode="numeric"
						maxlength="4"
						data-testid="kt-fy-start-year"
						@keydown.enter.prevent="preview && !preview.exists && emit('confirm', Number(startYear))"
					>
				</div>
				<!-- CFG-DES-04 — "FY 2028/29 · 1 Jul 2028 – 30 Jun 2029" -->
				<div v-if="preview" class="kt-summary" data-testid="kt-fy-preview">
					{{ preview.label }} · {{ preview.period_label }}
					<template v-if="preview.exists"> — {{ __("already exists") }}</template>
				</div>
				<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="busy || !preview || preview.exists"
					data-testid="kt-fy-add-confirm"
					@click="emit('confirm', Number(startYear))"
				>{{ __("Add financial year") }}</button>
			</div>
		</div>
	</div>
</template>
