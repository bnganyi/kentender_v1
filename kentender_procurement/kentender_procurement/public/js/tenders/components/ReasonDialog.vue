<!-- The boards' reason dialogs: Return for correction (reason + affected
     task), Request a requisition correction (reason), Return addendum,
     Reopen, Withdraw, Recommend cancellation. One textarea bounded by the
     server's rule (shown inline), an optional select, a note, two actions. -->
<template>
	<div class="kt-dialog-backdrop" :data-testid="testid" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" :aria-labelledby="`${testid}-title`" tabindex="-1">
			<div :id="`${testid}-title`" class="kt-dialog-title">{{ title }}</div>
			<div class="tnd-dialog-body">
				<div v-if="selectLabel" class="kt-field"><label :for="`${testid}-select`">{{ selectLabel }}</label>
					<select :id="`${testid}-select`" class="kt-input" v-model="choice" :data-testid="`${testid}-select`"><option v-for="o in options" :key="o.key || o" :value="o.key || o">{{ o.label || o }}</option></select>
				</div>
				<div class="kt-field"><label :for="`${testid}-reason`">{{ reasonLabel }}</label>
					<textarea :id="`${testid}-reason`" class="kt-input" rows="3" :placeholder="placeholder" v-model="reason" :data-testid="`${testid}-reason`"></textarea>
					<p v-if="fieldError" class="tnd-field-error" :data-testid="`${testid}-field-error`">{{ fieldError }}</p>
				</div>
				<div v-if="afterLabel" class="kt-field"><label :for="`${testid}-after`">{{ afterLabel }}</label>
					<select :id="`${testid}-after`" class="kt-input" v-model="choice" :data-testid="`${testid}-select`"><option v-for="o in options" :key="o.key || o" :value="o.key || o">{{ o.label || o }}</option></select>
				</div>
				<p v-if="note" class="tnd-dialog-note">{{ note }}</p>
				<p v-if="error" class="tnd-field-error" role="alert" :data-testid="`${testid}-error`">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn" :class="danger ? 'tnd-btn-danger' : 'kt-btn-primary'" :disabled="pending" :data-testid="`${testid}-confirm`" @click="confirm">{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
	testid: { type: String, default: "tnd-reason-dialog" },
	title: { type: String, required: true },
	reasonLabel: { type: String, default: "Reason" },
	placeholder: { type: String, default: "" },
	min: { type: Number, default: 20 },
	max: { type: Number, default: 2000 },
	selectLabel: { type: String, default: "" }, // select before the reason
	afterLabel: { type: String, default: "" }, // select after the reason (TPR-DES-06 "Affected task")
	options: { type: Array, default: () => [] },
	initialChoice: { type: String, default: "" },
	note: { type: String, default: "" },
	confirmLabel: { type: String, default: "Confirm" },
	danger: Boolean,
	pending: Boolean,
	error: { type: String, default: "" },
});
const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const reason = ref("");
const choice = ref(props.initialChoice || (props.options[0] ? props.options[0].key || props.options[0] : ""));
const fieldError = ref("");

function confirm() {
	const text = reason.value.trim();
	if (text.length < props.min || text.length > props.max) {
		fieldError.value = `Enter ${props.min.toLocaleString("en-US")}–${props.max.toLocaleString("en-US")} characters.`;
		return;
	}
	fieldError.value = "";
	emit("confirm", { reason: text, choice: choice.value });
}
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
