<script setup>
// ANL §10A.3 — the area summary strip: five columns, each a unit headline, one segmented bar with its legend,
// one outstanding line and one text link; beneath, the note that the counts are not added together. Ported
// from the Analytics Overview board (ANL-DES-21, 31C, 31E). A column that could not be read draws the server's
// sentence and Try again in place of headline, bar, line and link (31C).
import AnalyticsIcon from "./AnalyticsIcon.vue";
import { SegmentedBar } from "./charts/index.js";
import { boardTone, iconKey, isPlainClick } from "./presentation.js";

defineProps({
	strip: { type: Object, required: true },
	hrefFor: { type: Function, required: true }, // tab key -> address with the applied fy and dept
	busy: { type: Object, default: () => ({}) },
	failed: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["open", "retry"]);

const segments = (column) => (column.segments || []).map((segment) => ({ key: segment.key, label: segment.label, count: segment.count, tone: boardTone(column.key, segment) }));
function open(event, tab) {
	if (!isPlainClick(event)) return;
	event.preventDefault();
	emit("open", tab);
}
</script>

<template>
	<section class="kt-ap-section" data-testid="kt-anl-strip">
		<div class="kt-ap-strip">
			<div
				v-for="column in strip.columns"
				:key="column.key"
				class="kt-kpi-card kt-ap-kpi"
				:data-testid="'kt-anl-strip-' + column.key"
			>
				<span class="kt-kpi-head">
					<span class="kt-icon-chip"><AnalyticsIcon :name="iconKey(column.icon)" /></span>{{ column.label }}
				</span>

				<template v-if="column.status === 'unavailable'">
					<p class="kt-ap-kpi-msg" role="status">{{ column.message }}</p>
					<div>
						<button
							type="button"
							class="btn btn-secondary"
							:disabled="!!busy['strip:' + column.key]"
							data-testid="kt-anl-retry"
							@click="emit('retry', 'strip:' + column.key)"
						>
							<AnalyticsIcon name="refresh-cw" />{{ __("Try again") }}
						</button>
					</div>
					<p v-if="failed['strip:' + column.key]" class="kt-ap-note" role="status">{{ __("Still could not be loaded.") }}</p>
				</template>

				<template v-else-if="column.status === 'incomplete'">
					<p class="kt-ap-kpi-msg" role="status">{{ column.message }}</p>
					<a v-if="column.link" class="kt-ap-link" :href="hrefFor(column.link.tab)" @click="open($event, column.link.tab)">{{ column.link.label }}</a>
				</template>

				<template v-else>
					<span class="kt-ap-kpi-line">
						<span v-if="column.figure !== ''" class="kt-kpi-value">{{ column.figure }}</span>
						<span class="kt-ap-kpi-unit">{{ column.unit }}</span>
					</span>
					<p v-if="column.coverage_unavailable" class="kt-ap-note">{{ column.coverage_unavailable }}</p>
					<SegmentedBar v-else-if="(column.segments || []).length" :segments="segments(column)" size="xs" :title="column.label" />
					<span class="kt-ap-out" :class="{ 'has-matters': column.has_matters }">
						<AnalyticsIcon v-if="column.has_matters" name="hourglass" size="sm" />{{ column.outstanding }}
					</span>
					<a class="kt-ap-link" :href="hrefFor(column.link.tab)" @click="open($event, column.link.tab)">{{ column.link.label }}</a>
				</template>
			</div>
		</div>
		<p class="kt-ap-note" data-testid="kt-anl-strip-note">{{ strip.note }}</p>
	</section>
</template>
