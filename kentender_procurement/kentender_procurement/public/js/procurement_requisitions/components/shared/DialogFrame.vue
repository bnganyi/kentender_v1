<!-- In-Vue dialog (AGENTS.md §6.3): backdrop, focus on open, Escape closes,
     focus returns to the opener. -->
<template>
	<div class="dialog-backdrop" @click.self="!busy && $emit('close')" @keydown.esc="!busy && $emit('close')">
		<div ref="dialog" class="dialog" :class="widthClass" role="dialog" aria-modal="true" :aria-labelledby="titleId" tabindex="-1" :data-testid="testid">
			<div :id="titleId" class="dialog-title">{{ title }}</div>
			<slot />
			<div class="dialog-actions"><slot name="actions" /></div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({ title: { type: String, required: true }, width: { type: Number, default: 480 }, busy: { type: Boolean, default: false }, testid: { type: String, default: "" } });
defineEmits(["close"]);
const dialog = ref(null);
const titleId = `req-dialog-${Math.random().toString(36).slice(2, 9)}`;
const widthClass = `req-dialog-${props.width}`;
let opener = null;
onMounted(async () => {
	opener = document.activeElement;
	await nextTick();
	const first = dialog.value && dialog.value.querySelector("input:not([type=hidden]):not(:disabled), select, textarea, button");
	(first || dialog.value)?.focus();
});
onBeforeUnmount(() => { if (opener && opener.focus) opener.focus(); });
</script>
