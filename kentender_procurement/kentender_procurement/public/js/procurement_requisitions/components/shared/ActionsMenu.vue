<!-- "Other actions ▾" — quiet secondary actions beside the footer (§13.7). -->
<template>
	<div class="req-menu" @keydown.esc="open = false">
		<button type="button" class="kt-btn kt-btn-ghost" :aria-expanded="open ? 'true' : 'false'" data-testid="req-other-actions" :disabled="disabled" @click="open = !open">Other actions ▾</button>
		<div v-if="open" class="req-menu-list" role="menu">
			<button v-for="action in actions" :key="action.key" type="button" role="menuitem" :data-testid="`req-action-${action.key}`" @click="choose(action.key)">{{ action.label }}</button>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({ actions: { type: Array, required: true }, disabled: { type: Boolean, default: false } });
const emit = defineEmits(["choose"]);
const open = ref(false);
function choose(key) {
	open.value = false;
	emit("choose", key);
}
</script>
