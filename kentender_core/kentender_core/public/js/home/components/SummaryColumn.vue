<script setup>
// Ported from design/Home/Home.dc.html — a summary column of HOME-DES-21: no box, a rule at
// its left (the accent for My work, the page's single task rule), the region's icon and name,
// the figure in --color-figure with its label beside it. The whole column is the focus
// target for its region (§5.1 item 2). Where the count is incomplete it reads
// "Count unavailable" instead of the figure.
import HomeIcon from "./HomeIcon.vue";

const props = defineProps({ column: { type: Object, required: true } });
defineEmits(["focus-region"]);

const ICONS = { my_work: "list-checks", waiting: "hourglass", oversight: "eye" };
</script>

<template>
	<a
		:href="'#' + column.anchor"
		class="kt-kpi-card kt-home-kpi"
		:class="{ 'is-task': column.accent }"
		:data-testid="'kt-home-summary-' + column.region"
		@click.prevent="$emit('focus-region', column.region)"
	>
		<span class="kt-kpi-head">
			<span class="kt-icon-chip" :class="{ 'kt-home-chip-main': column.accent }"><HomeIcon :name="ICONS[column.region]" /></span>
			{{ column.heading }}
		</span>
		<span class="kt-home-kpi-line">
			<span class="kt-kpi-value kt-home-figure" :class="{ 'is-unavailable': column.unavailable }" data-testid="kt-home-figure">{{
				column.unavailable ? __("Count unavailable") : column.figure
			}}</span>
			<span class="kt-kpi-sub kt-home-figure-label">{{ column.label }}</span>
		</span>
	</a>
</template>
