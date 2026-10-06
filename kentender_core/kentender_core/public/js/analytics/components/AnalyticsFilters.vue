<script setup>
// The filter row (ANL §10A.1, §11): Financial year, Department, Apply filters, Clear filters. The two selects are
// bound to the caller's own pending selection, which becomes the route only when Apply filters is pressed;
// they never follow the server's echo (AGENTS.md 6.4). The server's messages for an invalid choice are drawn
// under the row and the valid parts of the selection stay.
import AnalyticsIcon from "./AnalyticsIcon.vue";

import { computed } from "vue";

const props = defineProps({
	fy: { type: String, default: "" },
	dept: { type: String, default: "" },
	fyOptions: { type: Array, default: () => [] }, // [{ id, label }]
	deptOptions: { type: Array, default: () => [] },
	messages: { type: Array, default: () => [] },
	clearHref: { type: String, default: "#" },
});
const emit = defineEmits(["update:fy", "update:dept", "apply", "clear"]);

// v-model re-applies the selection every time the options change (the options arrive after the first
// paint), which a plain :value would not; the value is still the caller's own, never the server echo.
const fyModel = computed({ get: () => props.fy, set: (value) => emit("update:fy", value) });
const deptModel = computed({ get: () => props.dept, set: (value) => emit("update:dept", value) });

function clear(event) {
	event.preventDefault();
	emit("clear");
}
</script>

<template>
	<div class="kt-ap-filters-wrap" data-testid="kt-anl-filters">
		<div class="kt-ap-filters">
			<div class="field kt-ap-field-year">
				<label for="kt-anl-fy">{{ __("Financial year") }}</label>
				<select id="kt-anl-fy" class="input" data-testid="kt-anl-fy" v-model="fyModel">
					<option value="">{{ __("All years") }}</option>
					<option v-for="option in fyOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
				</select>
			</div>
			<div class="field kt-ap-field-dept">
				<label for="kt-anl-dept">{{ __("Department") }}</label>
				<select id="kt-anl-dept" class="input" data-testid="kt-anl-dept" v-model="deptModel">
					<option value="">{{ __("All departments") }}</option>
					<option v-for="option in deptOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
				</select>
			</div>
			<button type="button" class="btn btn-secondary" data-testid="kt-anl-apply" @click="emit('apply')">{{ __("Apply filters") }}</button>
			<a :href="clearHref" class="kt-ap-clear" data-testid="kt-anl-clear-filters" @click="clear">{{ __("Clear filters") }}</a>
		</div>
		<ul v-if="messages.length" class="kt-ap-filter-messages" role="status" data-testid="kt-anl-filter-messages">
			<li v-for="message in messages" :key="message" class="kt-ap-filter-message"><AnalyticsIcon name="info" size="sm" />{{ message }}</li>
		</ul>
	</div>
</template>
