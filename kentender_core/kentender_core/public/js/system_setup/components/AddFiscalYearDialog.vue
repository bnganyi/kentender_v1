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
	<div class="kt-dialog-backdrop">
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
				<!-- The generated identity and period as separately labelled
				     facts (§11.3: dates are never user-entered) — never a
				     concatenated line the reader has to parse. -->
				<div v-if="preview" class="kt-meta-row" style="margin-top:10px" data-testid="kt-fy-preview">
					<div>
						<span class="kt-label">{{ __("Financial year") }}</span>
						<span class="kt-meta-value">{{ preview.label }}</span>
					</div>
					<div>
						<span class="kt-label">{{ __("Period") }}</span>
						<span class="kt-meta-value">{{ preview.period_label }}</span>
					</div>
				</div>
				<!-- CFG-UX-AC-05 — the exact duplicate/Company defects, never a
				     silent create; Add stays disabled for either. -->
				<div
					v-if="preview && preview.exists"
					class="kt-notice is-critical"
					role="alert"
					data-testid="kt-fy-duplicate"
				><strong>{{ __("Duplicate.") }}</strong> {{ __("This financial year already exists.") }}</div>
				<div
					v-else-if="preview && preview.company_missing"
					class="kt-notice is-critical"
					role="alert"
					data-testid="kt-fy-company-missing"
				><strong>{{ __("Company not linked.") }}</strong> {{ __("The accounting company must be configured before you can add a financial year.") }}</div>
				<p v-if="error" class="kt-inline-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:disabled="busy || !preview || preview.exists || preview.company_missing"
					data-testid="kt-fy-add-confirm"
					@click="emit('confirm', Number(startYear))"
				><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 5v14M5 12h14" /></svg>{{ __("Add financial year") }}</button>
			</div>
		</div>
	</div>
</template>
