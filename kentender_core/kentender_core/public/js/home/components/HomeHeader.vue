<script setup>
// Ported from design/Home/Home.dc.html — header row of HOME-DES-21 and HOME-DES-27:
// the greeting as the page heading with the responsibilities line beneath it, the quiet
// Updated time at the right and, for technical readers only, the Technical record search link.
import HomeIcon from "./HomeIcon.vue";
import { followLink } from "../composables/openDestination.js";

defineProps({
	viewer: { type: Object, required: true },
	updated: { type: String, default: "" },
	analytics: { type: Object, default: null },
});

const SEARCH = { route: ["technical-search"] };
const ANALYTICS = { route: ["analytics"] };
</script>

<template>
	<header class="kt-home-header" data-testid="kt-home-header">
		<div class="kt-home-heading">
			<h1 class="kt-home-title" data-testid="kt-home-title">{{ viewer.greeting }}, {{ viewer.first_name }}</h1>
			<p v-if="viewer.responsibilities && viewer.responsibilities.line" class="kt-home-sub" data-testid="kt-home-responsibilities">
				{{ viewer.responsibilities.line }}
			</p>
		</div>
		<div class="kt-home-meta">
			<a
				v-if="viewer.technical"
				href="/app/technical-search"
				class="kt-home-meta-link"
				data-testid="kt-home-technical-link"
				@click="followLink($event, SEARCH)"
			>
				<HomeIcon name="search" size="sm" />{{ __("Technical record search") }}
			</a>
			<a
				v-if="viewer.technical && analytics && analytics.allowed"
				href="/app/analytics"
				class="kt-home-meta-link"
				data-testid="kt-home-header-analytics-link"
				@click="followLink($event, ANALYTICS)"
			>
				{{ analytics.label }}
			</a>
			<span class="kt-home-updated" data-testid="kt-home-updated">
				<HomeIcon name="clock" size="sm" />{{ __("Updated {0}", [updated]) }}
			</span>
		</div>
	</header>
</template>
