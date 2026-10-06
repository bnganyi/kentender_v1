<script setup>
// A region title in the ordinary section heading style, preceded by its icon (ANL §10A.1 rule 6): the icon
// in a chip where the region belongs to an area's charts, or a plain muted icon for outstanding work and the register.
import AnalyticsIcon from "./AnalyticsIcon.vue";

defineProps({
	icon: { type: String, required: true },
	title: { type: String, required: true },
	chip: { type: Boolean, default: true },
	id: { type: String, default: "" },
});
</script>

<template>
	<h2 :id="id || undefined" class="kt-ap-h2">
		<span v-if="chip" class="kt-icon-chip"><AnalyticsIcon :name="icon" /></span>
		<AnalyticsIcon v-else :name="icon" />{{ title }}
	</h2>
</template>
