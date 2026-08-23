<script setup>
import { reactive, computed } from "vue";

// Generic in-Vue confirm dialog for the simple lifecycle transitions (Submit,
// Approve, Suspend, Reinstate, Retire, Recommend...). §12's dedicated Close Context
// dialog (with its acknowledgment checkbox) is its own component — this one covers
// every other action, with an optional reason/date field per action.
const props = defineProps({
	title: { type: String, required: true },
	contextLine: { type: String, default: "" },
	bodyText: { type: String, default: "" },
	confirmLabel: { type: String, required: true },
	danger: { type: Boolean, default: false },
	reasonLabel: { type: String, default: "" }, // non-empty enables the reason field
	reasonRequired: { type: Boolean, default: false },
	needsEffectiveDate: { type: Boolean, default: false },
	busy: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({ reason: "", effectiveDate: frappe.datetime.get_today() });

const canConfirm = computed(() => {
	if (props.reasonLabel && props.reasonRequired && !form.reason.trim()) return false;
	if (props.needsEffectiveDate && !form.effectiveDate) return false;
	return true;
});

function confirm() {
	if (!canConfirm.value || props.busy) return;
	emit("confirm", { reason: form.reason.trim(), effectiveDate: form.effectiveDate });
}
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div class="kt-dialog kt-blueprint">
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<div v-if="contextLine" style="font-size:14px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">{{ contextLine }}</div>
			<p v-if="bodyText" style="margin:0;font-size:14px;line-height:1.55">{{ bodyText }}</p>

			<div v-if="reasonLabel" class="kt-field">
				<label>{{ reasonLabel }}</label>
				<textarea class="kt-input" style="height:auto;min-height:80px;padding:10px" v-model="form.reason"></textarea>
			</div>

			<div v-if="needsEffectiveDate" class="kt-field">
				<label>{{ __("Effective date") }}</label>
				<input class="kt-input" type="date" v-model="form.effectiveDate" />
			</div>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="emit('cancel')" :disabled="busy">{{ __("Cancel") }}</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:class="{ 'kt-danger': danger }"
					:disabled="!canConfirm || busy"
					@click="confirm"
				>
					{{ confirmLabel }}
				</button>
			</div>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
		</div>
	</div>
</template>
