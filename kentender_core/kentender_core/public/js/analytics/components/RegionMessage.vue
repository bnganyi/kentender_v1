<script setup>
// A region that could not be loaded: the server's sentence and Try again, in that region only (ANL §8, §11).
// Other regions keep their values. No zero, no empty chart and no partial total stand in for it.
import AnalyticsIcon from "./AnalyticsIcon.vue";

defineProps({
	message: { type: String, required: true },
	busy: { type: Boolean, default: false },
	failed: { type: Boolean, default: false },
	testid: { type: String, default: "kt-anl-region-error" },
});
defineEmits(["retry"]);
</script>

<template>
	<div class="kt-ap-region is-14" :data-testid="testid">
		<p class="kt-ap-region-msg" role="status">{{ message }}</p>
		<div>
			<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-anl-retry" @click="$emit('retry')">
				<AnalyticsIcon name="refresh-cw" />{{ __("Try again") }}
			</button>
		</div>
		<p v-if="failed" class="kt-ap-note" role="status">{{ __("Still could not be loaded.") }}</p>
	</div>
</template>
