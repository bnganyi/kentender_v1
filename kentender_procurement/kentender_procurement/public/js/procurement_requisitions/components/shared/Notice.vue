<!-- .kt-notice with its severity icon — the icon is part of the notice. -->
<template>
	<div class="kt-notice" :class="`is-${tone}`" :role="tone === 'critical' || tone === 'warning' ? 'alert' : 'status'">
		<Icon :name="ICONS[tone] || 'info'" cls="kt-notice-icon" :size="undefined" />
		<div class="kt-notice-body"><slot /></div>
	</div>
</template>

<script setup>
import Icon from "./Icon.vue";

defineProps({ tone: { type: String, default: "info" } });
const ICONS = { info: "info", critical: "x", warning: "warning", live: "check" };
</script>
