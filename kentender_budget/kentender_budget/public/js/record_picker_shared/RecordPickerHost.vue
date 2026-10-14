<!-- Hosts kentender_core's shared record picker (kt_industry_record_picker.bundle.js) on this
     bundle's own Vue instance - AGENTS.md section 6.6: a component cannot cross a bundle boundary, so
     the core publishes a mount helper and every module reaches it through this one wrapper. The
     caller keeps its own selection (v-model, a string id or null) and hands back the label it
     knows; this only draws it and reports what the reader chooses (`change` carries the whole
     row, including `disabled_reason` when the screen's context makes a saved choice invalid).
     With `inline` and `multiple` the picker adds several: each choice is `add` (the whole row), the screen keeps the list and hands
     the ids back as `staged`, and `modelValue` is not used. -->
<template>
	<div ref="host" class="kt-picker-host" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	source: { type: String, required: true },
	context: { type: Object, default: () => ({}) },
	modelValue: { type: String, default: null },
	valueLabel: { type: String, default: "" },
	inputId: { type: String, default: "" },
	placeholder: { type: String, default: "" },
	noun: { type: String, default: "" },
	plural: { type: String, default: "" },
	listLabel: { type: String, default: "" },
	allLabel: { type: String, default: "" },
	inline: { type: Boolean, default: false },
	multiple: { type: Boolean, default: false },
	staged: { type: Array, default: () => [] },
	stagedReason: { type: String, default: "" },
	stagedNoun: { type: String, default: "" },
	invalid: { type: Boolean, default: false },
	required: { type: Boolean, default: false },
	disabled: { type: Boolean, default: false },
	errorText: { type: String, default: "" },
	fetch: { type: Function, default: null },
});
const emit = defineEmits(["update:modelValue", "change", "add"]);

const host = ref(null);
let handle = null;

const options = () => ({
	source: props.source,
	context: props.context,
	value: props.modelValue,
	valueLabel: props.valueLabel,
	inputId: props.inputId,
	placeholder: props.placeholder,
	noun: props.noun,
	plural: props.plural,
	listLabel: props.listLabel,
	allLabel: props.allLabel,
	inline: props.inline,
	multiple: props.multiple,
	staged: props.staged,
	...(props.stagedReason ? { stagedReason: props.stagedReason } : {}),
	...(props.stagedNoun ? { stagedNoun: props.stagedNoun } : {}),
	invalid: props.invalid,
	required: props.required,
	disabled: props.disabled,
	errorText: props.errorText,
	fetch: props.fetch,
});

onMounted(() => {
	const mount = window.kentender_core?.industry?.mountRecordPicker;
	if (!mount) {
		// Without the bundle nothing would draw and nothing would say why.
		console.error("kt_industry_record_picker.bundle.js is not loaded: add it to the page controller's bundles list.");
		return;
	}
	if (!host.value) return;
	handle = mount(host.value, {
		...options(),
		onChange: (row) => {
			emit("update:modelValue", row ? row.id : null);
			emit("change", row);
		},
		onAdd: (row) => emit("add", row),
	});
});

watch(
	() => [props.source, JSON.stringify(props.context), props.modelValue, props.valueLabel, props.inputId, props.placeholder, props.noun, props.plural, props.listLabel, props.allLabel, props.inline, props.multiple, JSON.stringify(props.staged), props.stagedReason, props.stagedNoun, props.invalid, props.required, props.disabled, props.errorText],
	() => handle?.update(options())
);

onBeforeUnmount(() => {
	handle?.unmount();
	handle = null;
});

defineExpose({ focus: () => handle?.focus() });
</script>
