<!-- The board's date field: "30 Sep 2027" over a native date input, so the
     control stays keyboard- and picker-native while reading as drawn. -->
<template>
	<div class="req-date-field">
		<input :id="id" type="date" class="input" :class="{ 'is-invalid': invalid }" :value="modelValue" :max="max" :disabled="disabled" :aria-invalid="invalid ? 'true' : 'false'" @input="$emit('update:modelValue', $event.target.value)" />
		<span class="req-date-display">{{ label }}</span>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { dateLabel } from "../../data/format.js";

const props = defineProps({ modelValue: { type: String, default: "" }, id: { type: String, required: true }, max: { type: String, default: "" }, disabled: { type: Boolean, default: false }, invalid: { type: Boolean, default: false } });
defineEmits(["update:modelValue"]);
const label = computed(() => dateLabel(props.modelValue) || "Select a date");
</script>
