<script setup>
// ANL §10A.9, §10A.10 (ANL-DES-28, 29F) — Funding position, after Time between key steps. Four shapes, all the
// server's: the quiet choose-a-year line (not an error), an unavailable region with Try again, the site-wide
// view (registered allocation, one segmented bar with its legend, the caption) and the department view (two
// subheadings: its own budget lines with a bar, and the shared lines with two figures and no bar).
import { computed } from "vue";
import { SegmentedBar } from "./charts/index.js";
import RegionHeading from "./RegionHeading.vue";
import RegionMessage from "./RegionMessage.vue";

const props = defineProps({
	funding: { type: Object, required: true },
	busy: { type: Boolean, default: false },
	failed: { type: Boolean, default: false },
});
defineEmits(["retry"]);

const bar = (segments) => (segments || []).map((s) => ({ key: s.key, label: s.label, count: s.value, text: s.text, tone: s.tone }));
const keep = (segments) => (segments || []).filter((s) => s.keep_zero).map((s) => s.key);
const own = computed(() => props.funding.own || null);
const fundingBar = computed(() => bar(props.funding.segments));
const ownBar = computed(() => bar(own.value && own.value.segments));
</script>

<template>
	<p v-if="funding.status === 'message'" class="kt-ap-note" data-testid="kt-anl-funding-message">{{ funding.message }}</p>
	<section v-else class="kt-ap-section is-ruled" data-testid="kt-anl-funding">
		<RegionHeading icon="wallet" :title="__('Funding position')" />
		<RegionMessage v-if="funding.status === 'unavailable'" :message="funding.message" :busy="busy" :failed="failed" @retry="$emit('retry')" />
		<template v-else>
			<div class="kt-ap-fund-head">
				<span class="is-title">{{ funding.title }}</span>
				<span class="is-quiet">{{ funding.version_text }}</span>
				<span v-if="funding.scope" class="is-quiet">{{ funding.scope }}</span>
			</div>

			<template v-if="own">
				<div class="kt-ap-fund-grid">
					<div class="kt-ap-fund-col">
						<h3 class="kt-ap-h3">{{ own.heading }}</h3>
						<span class="kt-ap-fund-registered">
							<span>{{ __("Registered allocation") }}</span>
							<span class="kt-result-value is-md">{{ own.registered }}</span>
						</span>
						<SegmentedBar :segments="ownBar" :keep-zero="keep(own.segments)" size="sm" :title="own.heading" />
					</div>
					<div class="kt-ap-fund-col">
						<h3 class="kt-ap-h3">{{ funding.shared.heading }}</h3>
						<div class="kt-ap-fund-figures">
							<span v-for="figure in funding.shared.figures" :key="figure.label" class="kt-ap-fund-figure">
								<span>{{ figure.label }}</span>
								<span>{{ figure.value }}</span>
							</span>
						</div>
					</div>
				</div>
			</template>
			<template v-else>
				<span class="kt-ap-fund-registered">
					<span>{{ __("Registered allocation") }}</span>
					<span class="kt-result-value is-md">{{ funding.registered }}</span>
				</span>
				<SegmentedBar :segments="fundingBar" :keep-zero="keep(funding.segments)" size="sm" :title="__('Funding position')" />
			</template>
			<p class="kt-ap-note">{{ funding.caption }}</p>
		</template>
	</section>
</template>
