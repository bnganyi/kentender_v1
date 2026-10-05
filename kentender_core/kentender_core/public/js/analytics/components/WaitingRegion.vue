<script setup>
// ANL §10A.3 — Outstanding matters by waiting time: segmented bars, one row per area that has outstanding
// matters, a shared legend of the four bands above, the count of each band inside its segment, and the
// quiet sentence for the areas with none. The ramp is its own hue (rule 11).
import { SegmentedBarRows } from "./charts/index.js";
import RegionHeading from "./RegionHeading.vue";

defineProps({ waiting: { type: Object, required: true } });
</script>

<template>
	<div class="kt-ap-region is-14" data-testid="kt-anl-waiting">
		<RegionHeading icon="hourglass" :title="__('Outstanding matters by waiting time')" />
		<SegmentedBarRows
			v-if="waiting.rows.length"
			variant="bands"
			:rows="waiting.rows"
			:legend="waiting.legend"
			:title="__('Outstanding matters by waiting time')"
			:table-headers="[__('Area'), __('Waiting time'), __('Matters')]"
		/>
		<p v-if="waiting.none_text" class="kt-ap-text">{{ waiting.none_text }}</p>
		<p v-if="waiting.incomplete_text" class="kt-ap-incomplete" role="status">{{ waiting.incomplete_text }}</p>
		<p class="kt-ap-note">{{ waiting.caption }}</p>
	</div>
</template>
