<script setup>
// One inline Lucide icon from the Analytics boards, drawn by .kt-icon (kt_analytics_ds.bundle.css).
// The markup is generated from the boards (scripts/analytics_icons_js.py), never user data.
// `name` is an icon name, or an area key (needs, departmental_planning, annual_planning, requisitions,
// tender_proceedings), which resolves to that area's icon.
import { computed } from "vue";
import { ANALYTICS_AREA_ICONS, ANALYTICS_ICONS, ANALYTICS_ICON_VIEWBOX } from "../analytics_icons.js";

const props = defineProps({
	name: { type: String, required: true },
	size: { type: String, default: "" }, // "" | "sm" | "md" | "lg"
});
const markup = computed(() => ANALYTICS_ICONS[ANALYTICS_AREA_ICONS[props.name] || props.name] || "");
</script>

<template>
	<svg
		class="kt-icon"
		:class="size ? 'is-' + size : ''"
		:viewBox="ANALYTICS_ICON_VIEWBOX"
		aria-hidden="true"
		focusable="false"
		v-html="markup"
	></svg>
</template>
