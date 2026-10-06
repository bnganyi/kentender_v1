<script setup>
// ANL §10A.1 — "How these figures are counted", collapsed at the bottom of every page. The head is a button
// that carries aria-expanded; the text is the server's. Toggling changes no calculation or query (§11).
import { ref } from "vue";
import AnalyticsIcon from "./AnalyticsIcon.vue";

defineProps({ text: { type: String, default: "" } });
const open = ref(false);
</script>

<template>
	<section class="kt-ap-section is-ruled" data-testid="kt-anl-definitions">
		<div class="kt-disclosure kt-ap-disclosure" :class="{ 'is-open': open }">
			<button
				type="button"
				class="kt-disclosure-head kt-ap-disclosure-head"
				:aria-expanded="open ? 'true' : 'false'"
				aria-controls="kt-anl-definitions-body"
				data-testid="kt-anl-definitions-toggle"
				@click="open = !open"
			>
				<span class="kt-disclosure-title-row">
					<AnalyticsIcon name="info" size="sm" />
					<span class="kt-disclosure-title">{{ __("How these figures are counted") }}</span>
				</span>
				<span class="kt-disclosure-chevron"><AnalyticsIcon name="chevron-down" size="sm" /></span>
			</button>
			<div v-if="open" id="kt-anl-definitions-body" class="kt-disclosure-body kt-ap-disclosure-body" data-testid="kt-anl-definitions-body">{{ text }}</div>
		</div>
	</section>
</template>
