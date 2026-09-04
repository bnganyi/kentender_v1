<!-- NDS-DES-15 — Create target choice (§11.16, §12.1). Shown only when the
     actor has more than one eligible Organisation Unit while one Fiscal Year
     is open for Needs submission; a single eligible OU skips this dialog
     entirely (NDS-UI-01). Every department option is an authorised OU
     assignment from list_need_create_targets; the Fiscal Year is read-only
     and never selected here — there is no PE control, closed/unauthorised
     option, global-context checkbox, remember-context option or date field. -->
<template>
	<div class="kt-dialog-backdrop" @mousedown.self="$emit('cancel')">
		<div
			ref="dialogEl"
			class="kt-dialog"
			role="dialog"
			aria-modal="true"
			:aria-labelledby="titleId"
			style="width: 520px"
			@keydown.esc.prevent="$emit('cancel')"
			@keydown.tab="trapFocus"
		>
			<div :id="titleId" class="kt-dialog-title">Create need for</div>
			<div class="kt-dialog-body">
				<p style="margin: 0 0 16px; font-size: 14.5px; color: var(--color-neutral-700)">
					Choose the department for this need.
				</p>
				<div class="kt-field" style="margin-bottom: 16px">
					<label for="nds-create-target-ou">Department</label>
					<select
						id="nds-create-target-ou"
						ref="selectEl"
						class="kt-input"
						data-testid="nds-create-target-ou"
						v-model="selected"
					>
						<option
							v-for="option in organisationUnits"
							:key="option.organisation_unit"
							:value="option.organisation_unit"
						>
							{{ option.organisation_unit_label }}
						</option>
					</select>
				</div>
				<div class="kt-readonly-row">
					<div class="kt-readonly-label">Financial Year</div>
					<div class="kt-readonly-value is-strong">{{ financialYearLabel }}</div>
				</div>
			</div>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" data-testid="nds-dialog-cancel" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary"
					data-testid="nds-create-target-continue"
					:disabled="pending || !selected"
					@click="$emit('continue', selected)"
				>
					Continue
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	organisationUnits: { type: Array, default: () => [] },
	financialYearLabel: { type: String, default: "" },
	pending: Boolean,
});
defineEmits(["continue", "cancel"]);

const dialogEl = ref(null);
const selectEl = ref(null);
const selected = ref(props.organisationUnits[0]?.organisation_unit || "");
const titleId = `nds-create-target-title-${Math.random().toString(16).slice(2)}`;
let restoreTo = null;

watch(
	() => props.organisationUnits,
	(units) => {
		if (!units.some((unit) => unit.organisation_unit === selected.value)) {
			selected.value = units[0]?.organisation_unit || "";
		}
	}
);

onMounted(() => {
	restoreTo = document.activeElement;
	selectEl.value?.focus();
});
onBeforeUnmount(() => {
	if (restoreTo && typeof restoreTo.focus === "function") restoreTo.focus();
});

function trapFocus(event) {
	const focusable = dialogEl.value?.querySelectorAll("select, button:not([disabled])");
	if (!focusable || !focusable.length) return;
	const first = focusable[0];
	const last = focusable[focusable.length - 1];
	if (event.shiftKey && document.activeElement === first) {
		event.preventDefault();
		last.focus();
	} else if (!event.shiftKey && document.activeElement === last) {
		event.preventDefault();
		first.focus();
	}
}
</script>
