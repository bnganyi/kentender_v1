<script setup>
// Ported from design/Home/Home.dc.html — the rail row of HOME-DES-21: a neutral module icon
// with no chip fill, the title as the link to the record, then the state and, on its own
// quiet line, the timing. The rail uses text links, not buttons (§10B.1).
import HomeIcon from "./HomeIcon.vue";
import { moduleIcon } from "../homeModules.js";
import { followLink, hrefOf } from "../composables/openDestination.js";

const props = defineProps({
	entry: { type: Object, required: true },
	region: { type: String, required: true }, // waiting | oversight | completed
});
</script>

<template>
	<div class="kt-home-rail-row" :data-key="props.entry.key" tabindex="-1" data-testid="kt-home-row">
		<span class="kt-icon-chip kt-home-chip-rail" :title="entry.module"><HomeIcon :name="moduleIcon(entry.owner)" /></span>
		<div class="kt-home-rail-body">
			<a
				:href="hrefOf(entry.destination)"
				class="kt-home-rail-title"
				:aria-label="entry.module + ': ' + entry.title"
				@click="followLink($event, entry.destination)"
				>{{ entry.title }}</a
			>
			<span class="kt-home-rail-state">{{ region === "completed" ? entry.sentence : entry.action }}</span>
			<span v-if="region !== 'completed' && (entry.timing || entry.due || entry.fact)" class="kt-home-rail-time">
				<span v-if="entry.timing">{{ entry.timing }}</span>
				<span v-if="entry.due">{{ entry.due }}</span>
				<span v-if="entry.fact" data-testid="kt-home-fact">{{ entry.fact }}</span>
			</span>
			<a
				v-if="entry.link"
				:href="hrefOf(entry.link.destination)"
				class="kt-home-link"
				:aria-label="entry.link.label + ': ' + entry.title"
				data-testid="kt-home-view"
				@click="followLink($event, entry.link.destination)"
			>
				{{ entry.link.label }}<HomeIcon name="arrow-right" size="sm" />
			</a>
		</div>
	</div>
</template>
