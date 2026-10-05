<script setup>
// The tab row (ANL §9.1): six peer views of one page. The selected tab is the caller's own (the route's tab),
// never the server's echo (AGENTS.md 6.4). Each tab is a radio in the design system's .kt-tab label, so the
// group is one Tab stop and the arrow keys move between tabs.
import AnalyticsIcon from "./AnalyticsIcon.vue";
import { iconKey } from "./presentation.js";

defineProps({
	tabs: { type: Array, required: true }, // [{ key, label, icon }]
	selected: { type: String, required: true },
});
defineEmits(["select"]);
</script>

<template>
	<div class="kt-tabs" role="tablist" :aria-label="__('Analytics areas')" data-testid="kt-anl-tabs">
		<label v-for="tab in tabs" :key="tab.key" class="kt-tab" :data-tab="tab.key">
			<input type="radio" name="kt-analytics-tabs" :value="tab.key" :checked="tab.key === selected" @change="$emit('select', tab.key)" />
			<AnalyticsIcon v-if="tab.icon" :name="iconKey(tab.icon)" />{{ tab.label }}
		</label>
	</div>
</template>
