<script setup>
// The centred state panel of the boards (ANL-DES-31B, 31D, 31H): an optional spot illustration, one
// sentence and, where there is one, one action. The text is the server's; the illustration is only on 31B,
// 31D and 31H (rule 9). 31B draws a plain large icon, 31D and 31H a spot.
import AnalyticsIcon from "./AnalyticsIcon.vue";

defineProps({
	text: { type: String, required: true },
	spot: { type: String, default: "" }, // "" | "error" | "neutral"
	icon: { type: String, default: "" },
});
</script>

<template>
	<div class="kt-empty">
		<span v-if="spot" class="kt-spot" :class="'is-' + spot"><AnalyticsIcon :name="icon" /></span>
		<AnalyticsIcon v-else-if="icon" :name="icon" size="lg" />
		<p class="kt-ap-panel-text" role="status">{{ text }}</p>
		<slot />
	</div>
</template>
