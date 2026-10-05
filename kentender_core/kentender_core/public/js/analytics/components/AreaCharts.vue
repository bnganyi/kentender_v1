<script setup>
// ANL §10A.4 to §10A.8 — the charts of one area tab, each as its board draws them:
//   Tender proceedings   Tenders by stage | Recorded each month            (side by side), then the step strip
//   Requisitions         Requisitions by current state | Recorded each month, then the step strip
//   Needs, departmental  one monthly chart
//   Annual planning      Coverage by Plan item; Coverage by department | Tender invitation timing
// The stage (state) bar mirrors the state select: it shows the caller's own selection and a click on a bar
// asks the page to select that state (the select stays the keyboard route). The chart and the area result are
// the whole area, never the filtered rows, and are labelled so (31A, 23).
import { computed } from "vue";
import { FromZeroBars, HorizontalBar, MonthlyGroupedBars, SegmentedBarRows } from "./charts/index.js";
import RegionHeading from "./RegionHeading.vue";
import { boardTone, iconKey } from "./presentation.js";

const props = defineProps({
	area: { type: Object, required: true },
	selectedState: { type: String, default: "" }, // the route's own state, never the server's echo
});
const emit = defineEmits(["select-state"]);

const charts = computed(() => props.area.charts || {});
const areaIcon = computed(() => iconKey(props.area.icon));
const split = computed(() => !!(charts.value.stages || charts.value.states));
const bars = computed(() => charts.value.stages || charts.value.states || null);
const barRows = computed(() =>
	bars.value ? bars.value.rows.map((row) => ({ key: row.key, label: row.label, count: row.count, valueText: row.value_text, tone: boardTone(props.area.key, row) })) : [],
);

function slotsOf(monthly) {
	return monthly.months.map((month, index) => ({
		key: month.key,
		label: month.label,
		axisLines: month.axis_lines,
		values: Object.fromEntries(monthly.series.map((series) => [series.key, series.counts[index]])),
	}));
}
const monthlyIcon = computed(() => (props.area.key === "needs" || props.area.key === "departmental_planning" ? areaIcon.value : "chart-column"));

const itemRows = computed(() => {
	const by = charts.value.by_item;
	if (!by) return [];
	return by.rows.map((row) => ({
		key: row.key,
		label: row.share_note ? row.label + " " + row.share_note : row.label,
		segments: row.segments.map((s) => ({ key: s.key, label: s.label, count: s.value, text: s.text, tone: s.tone, muted: s.key === "not_covered" })),
	}));
});
const itemLegend = computed(() => (charts.value.by_item && charts.value.by_item.legend) || []);
const deptRows = computed(() => {
	const by = charts.value.by_department;
	if (!by) return [];
	return by.rows.map((row) => ({
		key: row.key,
		label: row.label,
		endLabel: row.percent_text,
		segments: row.segments.map((s) => ({ key: s.key, label: s.label, count: s.value, text: s.text, tone: s.tone, muted: s.key === "not_covered" })),
	}));
});
const timing = computed(() => charts.value.timing || null);
</script>

<template>
	<!-- stage or state bars beside the monthly chart -->
	<section v-if="split && charts.monthly" class="kt-ap-split" data-testid="kt-anl-charts">
		<div>
			<div class="kt-ap-region">
				<RegionHeading :icon="areaIcon" :title="bars.title" />
				<span v-if="area.scope_label" class="kt-ap-note" data-testid="kt-anl-scope-label">{{ area.scope_label }}</span>
				<HorizontalBar
					:rows="barRows"
					:value-heading="bars.value_header"
					:selected="selectedState || null"
					selectable
					:title="bars.title"
					:table-headers="[__('Item'), __('Count'), bars.value_header]"
					@select="emit('select-state', $event)"
				/>
				<p v-if="bars.note" class="kt-ap-text">{{ bars.note }}</p>
			</div>
		</div>
		<div>
			<div class="kt-ap-region">
				<RegionHeading :icon="monthlyIcon" :title="charts.monthly.title" />
				<MonthlyGroupedBars
					:slots="slotsOf(charts.monthly)"
					:series="charts.monthly.series.map((s) => ({ key: s.key, label: s.label, tone: s.tone }))"
					:title="charts.monthly.title"
				/>
				<p v-if="charts.monthly.empty_text" class="kt-ap-text">{{ charts.monthly.empty_text }}</p>
			</div>
		</div>
	</section>

	<!-- one monthly chart (Needs, departmental planning) -->
	<section v-else-if="charts.monthly" class="kt-ap-section is-ruled" data-testid="kt-anl-charts">
		<div class="kt-ap-region">
			<RegionHeading :icon="monthlyIcon" :title="charts.monthly.title" />
			<MonthlyGroupedBars
				:slots="slotsOf(charts.monthly)"
				:series="charts.monthly.series.map((s) => ({ key: s.key, label: s.label, tone: s.tone }))"
				:title="charts.monthly.title"
			/>
			<p v-if="charts.monthly.empty_text" class="kt-ap-text">{{ charts.monthly.empty_text }}</p>
		</div>
	</section>

	<!-- annual planning -->
	<template v-if="charts.by_item">
		<section class="kt-ap-section is-ruled" data-testid="kt-anl-charts-items">
			<RegionHeading :icon="areaIcon" :title="charts.by_item.title" />
			<SegmentedBarRows
				v-if="itemRows.length"
				variant="items"
				:rows="itemRows"
				:legend="itemLegend"
				:title="charts.by_item.title"
				:table-headers="[__('Plan item'), __('Segment'), __('Value')]"
			/>
		</section>
		<section class="kt-ap-split" data-testid="kt-anl-charts-split">
			<div>
				<div class="kt-ap-region">
					<RegionHeading icon="building-2" :title="charts.by_department.title" />
					<SegmentedBarRows
						v-if="deptRows.length"
						variant="stacked"
						:rows="deptRows"
						:title="charts.by_department.title"
						:table-headers="[__('Department'), __('Segment'), __('Value'), __('Covered share')]"
					/>
					<p v-if="charts.by_department.caption" class="kt-ap-note">{{ charts.by_department.caption }}</p>
				</div>
			</div>
			<div>
				<div v-if="timing" class="kt-ap-region">
					<RegionHeading icon="clock" :title="timing.title" />
					<FromZeroBars
						:rows="timing.rows.map((r) => ({ key: r.key, label: r.label, value: r.days, text: r.text }))"
						:half-range="timing.span || 1"
						:earlier-label="__('Earlier')"
						:later-label="__('Later')"
						:caption="timing.caption"
						:title="timing.title"
					/>
				</div>
			</div>
		</section>
	</template>
</template>
