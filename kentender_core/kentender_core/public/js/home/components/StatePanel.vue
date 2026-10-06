<script setup>
// Ported from design/Home/Home.dc.html — the centred state panel of HOME-DES-28A, 28D and 28F:
// a spot (outline circle with an icon), one sentence and, where there is one, one action.
import HomeIcon from "./HomeIcon.vue";

defineProps({
	spot: { type: String, required: true }, // success | error | neutral
	icon: { type: String, required: true },
	text: { type: String, required: true },
});
</script>

<template>
	<div class="kt-home-panel">
		<span class="kt-spot" :class="'is-' + spot"><HomeIcon :name="icon" /></span>
		<p class="kt-home-panel-text">{{ text }}</p>
		<slot />
	</div>
</template>
