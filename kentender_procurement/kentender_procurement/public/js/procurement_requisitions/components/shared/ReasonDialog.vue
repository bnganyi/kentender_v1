<!-- One governed reason dialog: returns, withdrawal, revocation, Planning
     correction and a lead change all use it (§13.7–§13.11). -->
<template>
	<DialogFrame :title="title" :width="480" :busy="busy" :testid="testid" @close="$emit('close')">
		<div v-if="options" class="kt-field">
			<label :for="`${id}-option`">{{ optionLabel }}</label>
			<select :id="`${id}-option`" v-model="option" class="kt-input" :disabled="busy">
				<option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
			</select>
		</div>
		<div class="kt-field">
			<label :for="`${id}-reason`">{{ reasonLabel }}</label>
			<textarea :id="`${id}-reason`" v-model="reason" class="kt-input" :class="{ 'is-invalid': showError }" :rows="rows" :placeholder="placeholder" :disabled="busy" :aria-describedby="`${id}-hint`" :aria-invalid="showError ? 'true' : 'false'"></textarea>
			<div v-if="hint" :id="`${id}-hint`" class="kt-field-hint">{{ hint }}</div>
			<span v-if="showError" class="req-field-error" role="alert">Enter {{ min }}–{{ max.toLocaleString("en-GB") }} characters.</span>
		</div>
		<div v-if="sections" class="kt-field">
			<label :for="`${id}-section`">Affected section (optional)</label>
			<select :id="`${id}-section`" v-model="section" class="kt-input" :disabled="busy">
				<option value="">Not specified</option>
				<option v-for="s in sections" :key="s" :value="s">{{ s }}</option>
			</select>
		</div>
		<Notice v-if="notice" :tone="noticeTone">{{ notice }}</Notice>
		<p v-if="bodyText" class="req-dialog-body">{{ bodyText }}</p>
		<Notice v-if="error" tone="critical">{{ error }}</Notice>
		<template #actions>
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="kt-btn kt-btn-primary" :class="{ 'kt-danger': danger }" :disabled="busy" :data-testid="`${testid}-confirm`" @click="submit">{{ confirmLabel }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, ref } from "vue";
import DialogFrame from "./DialogFrame.vue";
import Notice from "./Notice.vue";

const props = defineProps({
	title: { type: String, required: true }, reasonLabel: { type: String, default: "Reason (required, 20–1,000 characters)" },
	confirmLabel: { type: String, required: true }, min: { type: Number, default: 20 }, max: { type: Number, default: 1000 },
	initial: { type: String, default: "" }, hint: { type: String, default: "" }, placeholder: { type: String, default: "" },
	sections: { type: Array, default: null }, options: { type: Array, default: null }, optionLabel: { type: String, default: "" }, initialOption: { type: String, default: "" },
	notice: { type: String, default: "" }, noticeTone: { type: String, default: "info" }, bodyText: { type: String, default: "" },
	danger: { type: Boolean, default: false }, busy: { type: Boolean, default: false }, error: { type: String, default: "" },
	rows: { type: Number, default: 2 }, testid: { type: String, default: "req-reason-dialog" },
});
const emit = defineEmits(["close", "confirm"]);
const id = `req-reason-${Math.random().toString(36).slice(2, 8)}`;
const reason = ref(props.initial);
const section = ref("");
const option = ref(props.initialOption || (props.options && props.options[0] ? props.options[0].value : ""));
const touched = ref(false);
const trimmed = computed(() => reason.value.replace(/\s+/g, " ").trim());
const showError = computed(() => touched.value && (trimmed.value.length < props.min || trimmed.value.length > props.max));
function submit() {
	touched.value = true;
	if (showError.value) return;
	emit("confirm", { reason: trimmed.value, affected_section: section.value, option: option.value });
}
</script>
