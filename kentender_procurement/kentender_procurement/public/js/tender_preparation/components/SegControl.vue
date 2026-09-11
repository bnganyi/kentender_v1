<!-- §8.0 "Two choices — Yes/No switch or radio; never free text" and
     "Finite choice — radio containing only listed values". Ported from the
     artboard's .seg/.seg-opt. -->
<template>
	<div class="tpr-seg" role="radiogroup" :aria-label="label">
		<label v-for="opt in normalised" :key="String(opt.value)" class="tpr-seg-opt" :class="{ 'is-selected': modelValue === opt.value }">
			<input type="radio" :name="name" :value="String(opt.value)" :checked="modelValue === opt.value" :disabled="disabled" @change="$emit('update:modelValue', opt.value)" />{{ opt.label }}
		</label>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	modelValue: { default: null },
	options: { type: Array, default: () => [{ value: true, label: "Yes" }, { value: false, label: "No" }] },
	name: { type: String, required: true },
	label: { type: String, default: "" },
	disabled: Boolean,
});
defineEmits(["update:modelValue"]);
const normalised = computed(() => props.options.map((o) => (typeof o === "object" ? o : { value: o, label: String(o) })));
</script>
