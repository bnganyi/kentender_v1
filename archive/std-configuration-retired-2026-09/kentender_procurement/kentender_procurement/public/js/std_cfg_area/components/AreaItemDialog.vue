<script setup>
// Generic add/edit dialog for one PCFG-03..09 item, shape driven by
// areaRegistry.js's `fields` list. Same kt-dialog shell as CreateVersionModal.
import { reactive, watch, nextTick, ref } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	title: { type: String, default: "" },
	fields: { type: Array, default: () => [] },
	item: { type: Object, default: null },
	saving: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const form = reactive({});
const dialogEl = ref(null);

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		Object.keys(form).forEach((k) => delete form[k]);
		for (const f of props.fields) {
			form[f.key] = props.item ? props.item[f.key] : f.type === "checkbox" ? 0 : "";
		}
		await nextTick();
		dialogEl.value?.querySelector("input, select, textarea")?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}

function onConfirm() {
	emit("confirm", { ...form });
}
</script>

<template>
	<div v-if="open" class="kt-dialog-backdrop" @keydown="onKeydown" tabindex="-1">
		<div ref="dialogEl" class="kt-dialog kt-blueprint" style="width: 560px; max-height: 80vh; overflow-y: auto">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<h2 class="kt-dialog-title">{{ title }}</h2>

			<div v-for="f in fields" :key="f.key" class="kt-field" style="margin: 0 0 14px">
				<label :for="`kt-area-field-${f.key}`">{{ f.label }}</label>
				<select v-if="f.type === 'select'" :id="`kt-area-field-${f.key}`" v-model="form[f.key]" class="kt-input">
					<option value=""></option>
					<option v-for="opt in f.options" :key="opt" :value="opt">{{ opt }}</option>
				</select>
				<textarea
					v-else-if="f.type === 'textarea'"
					:id="`kt-area-field-${f.key}`"
					v-model="form[f.key]"
					class="kt-input"
					rows="2"
				></textarea>
				<label v-else-if="f.type === 'checkbox'" style="display: flex; align-items: center; gap: 8px; font-weight: normal">
					<input :id="`kt-area-field-${f.key}`" type="checkbox" v-model="form[f.key]" :true-value="1" :false-value="0" />
					{{ __("Yes") }}
				</label>
				<input
					v-else
					:id="`kt-area-field-${f.key}`"
					v-model="form[f.key]"
					class="kt-input"
					:type="f.type === 'int' ? 'number' : 'text'"
				/>
			</div>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="onConfirm">
					{{ item ? __("Save") : __("Add") }}
				</button>
			</div>
		</div>
	</div>
</template>
