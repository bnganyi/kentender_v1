<script setup>
// Ported from design/Home/Home.dc.html — one region of HOME-DES-21: a heading (18 px with its
// icon in the main column, 15 px in the rail), its rows, and underneath either the Show more
// footer (HOME-DES-26, 26B) or the region's own failure message with Try again (HOME-DES-28B,
// 28C). A failed region keeps the rows it has (§8 "safe rows retained").
import { computed } from "vue";
import HomeIcon from "./HomeIcon.vue";
import RailRow from "./RailRow.vue";
import WorkRow from "./WorkRow.vue";
import { REGION_IDS, regionHeading } from "../composables/useHomeWorkspace.js";
import { followLink } from "../composables/openDestination.js";

const props = defineProps({
	name: { type: String, required: true },
	region: { type: Object, required: true },
	variant: { type: String, required: true }, // main | rail
	busy: { type: Boolean, default: false },
	retryFailed: { type: Boolean, default: false },
	moreFailed: { type: Boolean, default: false },
	analytics: { type: Object, default: null },
});
defineEmits(["retry", "more"]);

const ICONS = { my_work: "list-checks", coming_up: "calendar-clock", oversight: "eye" };
const id = computed(() => REGION_IDS[props.name]);
const failed = computed(() => props.region.coverage === "partial" || props.region.coverage === "unavailable" || props.retryFailed);
const nothingLoaded = computed(() => props.region.entries.length === 0);
const failureText = computed(() => (nothingLoaded.value ? __("We could not load this section.") : __("Some work in this section could not be loaded.")));
const footerText = computed(() =>
	props.region.total === null || props.region.total === undefined
		? __("Showing {0}", [props.region.shown])
		: __("Showing {0} of {1}", [props.region.shown, props.region.total])
);
const showFooter = computed(() => props.region.paged && props.region.entries.length > 0);
</script>

<template>
	<section :id="id" class="kt-home-region" :class="'is-' + variant" :data-testid="'kt-home-region-' + name" :aria-labelledby="id + '-heading'">
		<h2 :id="id + '-heading'" class="kt-home-h2" :class="'is-' + variant" tabindex="-1">
			<HomeIcon v-if="variant === 'main'" :name="ICONS[name] || 'list-checks'" />{{ regionHeading(name) }}
		</h2>

		<template v-if="variant === 'main'">
			<WorkRow v-for="entry in region.entries" :key="entry.key" :entry="entry" :region="name" />
		</template>
		<template v-else>
			<RailRow v-for="entry in region.entries" :key="entry.key" :entry="entry" :region="name" />
		</template>

		<a
			v-if="name === 'oversight' && analytics && analytics.allowed"
			href="/app/analytics"
			class="kt-home-meta-link kt-home-analytics-link"
			data-testid="kt-home-analytics-link"
			@click="followLink($event, { route: analytics.route })"
		>{{ analytics.see_all }}</a>

		<div v-if="failed" class="kt-home-failure" :class="{ 'is-compact': variant === 'rail' }" role="alert" data-testid="kt-home-failure">
			<span class="kt-home-failure-text"><HomeIcon name="circle-alert" size="sm" />{{ failureText }}</span>
			<button type="button" class="btn btn-secondary kt-home-retry" :disabled="busy" data-testid="kt-home-retry" @click="$emit('retry', name)">
				<HomeIcon name="refresh-cw" />{{ __("Try again") }}
			</button>
		</div>

		<div v-if="showFooter" class="kt-home-more" data-testid="kt-home-more">
			<span class="kt-home-quiet" data-testid="kt-home-showing">{{ footerText }}</span>
			<button
				v-if="region.next_cursor"
				type="button"
				class="btn btn-ghost"
				:disabled="busy"
				data-testid="kt-home-show-more"
				@click="$emit('more', name)"
			>
				{{ __("Show {0} more", [region.next_count]) }}<HomeIcon name="chevron-down" />
			</button>
		</div>
		<div v-if="moreFailed" class="kt-home-failure is-compact" role="alert" data-testid="kt-home-more-failed">
			<span class="kt-home-failure-text"><HomeIcon name="circle-alert" size="sm" />{{ __("Some work in this section could not be loaded.") }}</span>
			<button type="button" class="btn btn-secondary kt-home-retry" :disabled="busy" @click="$emit('more', name)">
				<HomeIcon name="refresh-cw" />{{ __("Try again") }}
			</button>
		</div>
	</section>
</template>
