<script setup>
// Shared header (ANL §10A.1): title, description, quiet update time and scope, quiet Refresh at the right.
import AnalyticsIcon from "./AnalyticsIcon.vue";

defineProps({
	title: { type: String, required: true },
	description: { type: String, default: "" },
	updated: { type: String, default: "" },
	scope: { type: String, default: "" },
	refresh: { type: Boolean, default: true },
});
defineEmits(["refresh"]);
</script>

<template>
	<header class="kt-ap-header" data-testid="kt-anl-header">
		<div class="kt-ap-heading">
			<h1 class="kt-ap-title" data-testid="kt-anl-title">{{ title }}</h1>
			<p v-if="description" class="kt-ap-sub">{{ description }}</p>
			<div v-if="updated || scope" class="kt-ap-meta">
				<span v-if="updated" data-testid="kt-anl-updated"><AnalyticsIcon name="clock" size="sm" />{{ updated }}</span>
				<span v-if="scope" data-testid="kt-anl-scope"><AnalyticsIcon name="building-2" size="sm" />{{ scope }}</span>
			</div>
		</div>
		<button v-if="refresh" type="button" class="btn btn-ghost" data-testid="kt-anl-refresh" @click="$emit('refresh')">
			<AnalyticsIcon name="refresh-cw" />{{ __("Refresh") }}
		</button>
	</header>
</template>
