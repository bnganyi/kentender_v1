<script setup>
// STR-DES-05 — Add Performance Target dialog. Own component rather than a
// generalized ConfirmDialog.vue: this dialog's fields (period select,
// comparison + value + read-only unit suffix) don't fit ConfirmDialog's
// single-reason shape. Shell (backdrop, escape-key, autofocus) mirrors
// ConfirmDialog.vue's pattern.
//
// §12.3 — Period offers only ERPNext Fiscal Years overlapping the plan
// period, plus one plan-period date option when applicable (a target "by
// the end of the plan period", stored as target_by_date).
//
// The unit suffix is styled inline rather than through a scoped style
// block: esbuild extracts SFC CSS to a file nothing links (AGENTS.md §6.6),
// so a scoped rule here silently never applies.
import { ref, reactive, nextTick, watch, computed, onBeforeUnmount } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	fiscalYears: { type: Array, default: () => [] },
	planPeriodEnd: { type: String, default: "" },
	unit: { type: String, default: "" },
	saving: { type: Boolean, default: false },
	// This dialog stays open across the async save (it only closes on
	// success), so a rejection (e.g. a duplicate Fiscal Year target) renders
	// inside it — never behind its backdrop.
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const DATE_PREFIX = "date:";
const form = reactive({ period: "", comparison: "At least", target_value: "" });
const periodInput = ref(null);

const periodOptions = computed(() => {
	const out = props.fiscalYears.map((fy) => ({ value: fy.name || fy, label: `FY ${fy.name || fy}` }));
	if (props.planPeriodEnd) {
		out.push({ value: DATE_PREFIX + props.planPeriodEnd, label: __("By end of plan period ({0})", [props.planPeriodEnd]) });
	}
	return out;
});

const suffixStyle =
	"display: flex; align-items: center; padding: 0 12px; border: 1px solid var(--kt-color-divider); " +
	"background: color-mix(in srgb, var(--kt-color-text) 6%, transparent); color: var(--kt-color-text); " +
	"opacity: 0.7; font-size: 14px; white-space: nowrap";

// Escape is listened for on the document while the dialog is open, not
// only on the backdrop: a failed save disables the confirm button for the
// duration of the request, which drops keyboard focus to <body>, and a
// backdrop-only handler would then never see the key.
function onKeydown(e) {
	if (e.key === "Escape" && props.open) emit("cancel");
}

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) {
			document.removeEventListener("keydown", onKeydown);
			return;
		}
		document.addEventListener("keydown", onKeydown);
		Object.assign(form, { period: "", comparison: "At least", target_value: "" });
		await nextTick();
		periodInput.value?.focus();
	},
	{ immediate: true }
);
onBeforeUnmount(() => document.removeEventListener("keydown", onKeydown));

function onConfirm() {
	const isDate = form.period.startsWith(DATE_PREFIX);
	emit("confirm", {
		fiscal_year: isDate ? null : form.period || null,
		target_by_date: isDate ? form.period.slice(DATE_PREFIX.length) : null,
		comparison: form.comparison,
		target_value: form.target_value === "" ? null : Number(form.target_value),
	});
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" data-testid="str-add-target-dialog" tabindex="-1">
		<div class="kt-dialog kt-blueprint" style="width: 480px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ __("Add performance target") }}</h2>
			<p class="kt-muted" style="font-size: 14px; margin: 0">
				{{ __("Set the expected value and period for this indicator.") }}
			</p>
			<p v-if="error" data-testid="str-add-target-error" style="color: oklch(0.45 0.13 28); font-size: 14px; margin: 8px 0 0">{{ error }}</p>

			<div class="kt-field" style="margin: 0 0 20px">
				<label for="kt-add-target-period">{{ __("Period") }}</label>
				<select id="kt-add-target-period" ref="periodInput" v-model="form.period" class="kt-input" data-testid="str-target-period">
					<option value="">{{ __("Select a period") }}</option>
					<option v-for="o in periodOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
				</select>
			</div>

			<div class="kt-field" style="margin: 0">
				<label>{{ __("Expected result") }}</label>
				<div style="display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 8px">
					<select v-model="form.comparison" class="kt-input" data-testid="str-target-comparison">
						<option>At least</option>
						<option>At most</option>
						<option>Equal to</option>
					</select>
					<input v-model="form.target_value" class="kt-input" type="number" data-testid="str-target-value" />
					<div :style="suffixStyle" data-testid="str-target-unit">{{ unit || "—" }}</div>
				</div>
			</div>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving || !form.period" data-testid="str-target-confirm" @click="onConfirm">
					{{ __("Add target") }}
				</button>
			</div>
		</div>
	</div>
</template>
