<script setup>
// STR-DES-03/06 "Structure summary" — secondary detail rows, one per type,
// in the type's own icon and tone. Counts come from the server tree.
import { iconPath, iconTone } from "../../strategy_shared/nodeIcons.js";

defineProps({ counts: { type: Object, required: true } });

const ROWS = [
	["Pillar", "Pillars", "pillars"],
	["Programme", "Programmes", "programmes"],
	["Sub-programme", "Sub-programmes", "sub_programmes"],
	["Strategic Objective", "Strategic objectives", "strategic_objectives"],
	["Performance Indicator", "Performance indicators", "performance_indicators"],
	["Performance Target", "Performance targets", "performance_targets"],
];
</script>

<template>
	<div style="display: flex; flex-direction: column; gap: 2px" data-testid="str-summary-card">
		<div
			v-for="([type, label, key], index) in ROWS"
			:key="key"
			style="display: flex; align-items: center; gap: 10px; padding: 7px 2px"
			:style="index < ROWS.length - 1 ? 'border-bottom: 1px solid var(--kt-color-divider)' : ''"
			:data-testid="`str-count-${key}`"
		>
			<svg width="15" height="15" viewBox="0 0 24 24" fill="none" :stroke="iconTone(type)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex: none" v-html="iconPath(type)"></svg>
			<span style="font-size: 13px; flex: 1">{{ __(label) }}</span>
			<span style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 15px">{{ counts[key] ?? 0 }}</span>
		</div>
	</div>
</template>
