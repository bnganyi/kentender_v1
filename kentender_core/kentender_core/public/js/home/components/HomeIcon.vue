<script setup>
// One inline Lucide icon from the Home board, drawn by .kt-icon (kt_home_ds.bundle.css).
// The markup is generated from the board (scripts/home_icons_js.py), never user data.
import { computed } from "vue";
import { HOME_ICONS, HOME_ICON_VIEWBOX } from "../home_icons.js";

const props = defineProps({
	name: { type: String, required: true },
	size: { type: String, default: "" }, // "" | "sm" | "lg"
});
const markup = computed(() => HOME_ICONS[props.name] || "");
</script>

<template>
	<svg
		class="kt-icon"
		:class="size ? 'is-' + size : ''"
		:viewBox="HOME_ICON_VIEWBOX"
		aria-hidden="true"
		focusable="false"
		v-html="markup"
	></svg>
</template>
