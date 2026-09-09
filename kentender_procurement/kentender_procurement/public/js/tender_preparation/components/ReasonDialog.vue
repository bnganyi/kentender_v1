<!-- §13.9 dialogs — Request upstream correction, Return for correction,
     Reopen before publication: one required reason, an optional fixed
     notice, Cancel + the named primary action. 520 px per the artboards.
     Built in Vue (never frappe.confirm — AGENTS.md §6.3). -->
<template>
	<div class="kt-dialog-backdrop" :data-testid="testid" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog tpr-dialog kt-blueprint" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-dialog-title">{{ title }}</div>
			<div class="tpr-dialog-body">
				<div class="tpr-field"><label :for="`${testid}-reason`">{{ fieldLabel }}</label><textarea :id="`${testid}-reason`" class="kt-input" rows="3" :value="reason" @input="reason = $event.target.value"></textarea><p v-if="fieldError" class="tpr-field-error">{{ fieldError }}</p></div>
				<p v-if="notice" class="tpr-muted" style="font-size: 12px; margin: 0">{{ notice }}</p>
				<p v-if="error" class="tpr-field-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" :data-testid="`${testid}-confirm`" @click="confirm">{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

defineProps({ title: { type: String, required: true }, fieldLabel: { type: String, default: "Reason" }, confirmLabel: { type: String, required: true }, notice: { type: String, default: "" }, testid: { type: String, required: true }, pending: Boolean, error: { type: String, default: "" } });
const emit = defineEmits(["confirm", "cancel"]);
const dialogEl = ref(null);
const reason = ref("");
const fieldError = ref("");
function confirm() {
	const trimmed = reason.value.trim();
	if (trimmed.length < 10 || trimmed.length > 1000) {
		fieldError.value = "A reason of 10–1,000 characters is required.";
		return;
	}
	fieldError.value = "";
	emit("confirm", trimmed);
}
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
