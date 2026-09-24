<!-- The board's inline Yes/No control over real radio inputs. -->
<template>
	<div class="kt-seg kt-seg-inline" role="radiogroup" :aria-labelledby="labelledby">
		<label v-for="choice in CHOICES" :key="choice.label" class="kt-seg-opt">
			<input type="radio" :name="name" :checked="modelValue === choice.value" :disabled="disabled" @change="$emit('update:modelValue', choice.value)" />{{ choice.label }}
		</label>
	</div>
</template>

<script setup>
defineProps({ modelValue: { type: Boolean, default: false }, name: { type: String, required: true }, disabled: { type: Boolean, default: false }, labelledby: { type: String, default: "" } });
defineEmits(["update:modelValue"]);
const CHOICES = [{ label: "Yes", value: true }, { label: "No", value: false }];
</script>
