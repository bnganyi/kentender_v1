<script setup>
// STR-DES-05b — Add Performance Target dialog. Own component rather than a
// generalized ConfirmDialog.vue: this dialog's fields (FY select, comparison
// + value + read-only unit suffix) don't fit ConfirmDialog's single-reason
// shape, and touching that shared component risks its 3 existing lifecycle
// call sites (Activate/Submit/Create-successor). Shell (backdrop, escape-key,
// autofocus) mirrors ConfirmDialog.vue's pattern.
import { ref, reactive, nextTick, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	financialYears: { type: Array, default: () => [] },
	unit: { type: String, default: "" },
	saving: { type: Boolean, default: false },
	// Unlike ConfirmDialog's callers, this dialog stays open across the async
	// save (it only closes on success) — a rejection (e.g. a duplicate
	// Fiscal Year target) previously rendered into the panel behind this
	// backdrop, invisible while the dialog was up: the dialog looked like it
	// just did nothing.
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({ financial_year_id: "", comparison: "At least", target_value: "" });
const periodInput = ref(null);

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		Object.assign(form, { financial_year_id: "", comparison: "At least", target_value: "" });
		await nextTick();
		periodInput.value?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}

function onConfirm() {
	emit("confirm", {
		financial_year_id: form.financial_year_id || null,
		comparison: form.comparison,
		target_value: form.target_value,
	});
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" @keydown="onKeydown" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 480px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Add performance target") }}</h2>
			<p class="kt-muted" style="font-size: 14px; margin: 0">
				{{ __("Set the expected value and period for this indicator.") }}
			</p>
			<p v-if="error" style="color: oklch(0.45 0.13 28); font-size: 14px; margin: 8px 0 0">{{ error }}</p>

			<div class="kt-field" style="margin: 0 0 20px">
				<label for="kt-add-target-period">{{ __("Period") }}</label>
				<select id="kt-add-target-period" ref="periodInput" v-model="form.financial_year_id" class="kt-input">
					<option value="">{{ __("Select a financial year") }}</option>
					<option v-for="fy in financialYears" :key="fy" :value="fy">{{ fy }}</option>
				</select>
			</div>

			<div class="kt-field" style="margin: 0">
				<label>{{ __("Expected result") }}</label>
				<div style="display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 8px">
					<select v-model="form.comparison" class="kt-input">
						<option>At least</option>
						<option>At most</option>
						<option>Equal to</option>
					</select>
					<input v-model="form.target_value" class="kt-input" type="number" />
					<div class="kt-readonly-suffix">{{ unit || "—" }}</div>
				</div>
			</div>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="onConfirm">
					{{ __("Add target") }}
				</button>
			</div>
		</div>
	</div>
</template>

<style scoped>
.kt-readonly-suffix {
	display: flex;
	align-items: center;
	padding: 0 12px;
	border: 1px solid var(--kt-color-divider);
	background: color-mix(in srgb, var(--kt-color-text) 6%, transparent);
	color: var(--kt-color-text);
	opacity: 0.7;
	font-size: 14px;
	white-space: nowrap;
}
</style>
