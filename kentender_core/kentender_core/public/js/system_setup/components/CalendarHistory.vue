<script setup>
// CFG-CHG-002 v0.14 §10.9 (C04 #calendar-history; tracker CFG14-5F) — a
// working-day calendar's usage and history: its versions (from the settings
// read the tab already holds), its source checks, its usage.
import { onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import VersionHistory from "./VersionHistory.vue";

const props = defineProps({
	name: { type: String, required: true },
	calendarVersions: { type: Array, default: () => [] },
});
const emit = defineEmits(["view-version"]);

const loading = ref(true);
const loadError = ref("");
const versions = ref([]);
const checks = ref([]);

onMounted(async () => {
	try {
		const [calendar, events] = await Promise.all([
			procurementSettingsApi.getBusinessDayCalendar(props.name),
			procurementSettingsApi.listVerificationHistory("Business Day Calendar", props.name),
		]);
		versions.value = props.calendarVersions
			.filter((row) => row.calendar_name === calendar.calendar_name)
			.map((row) => ({ ...row, id: row.calendar }));
		checks.value = events;
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
});
</script>

<template>
	<div class="kt-calendar" data-testid="kt-procset-calendar">
		<div v-if="loading" data-testid="kt-calendar-loading"><div class="kt-skel" style="width:40%" /></div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-calendar-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This record isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>
		<div v-else data-testid="kt-calendar-history">
			<h3>{{ __("Working-day calendar — usage and history") }}</h3>
			<VersionHistory :versions="versions" :checks="checks" @view-version="(id) => emit('view-version', id)" />
		</div>
	</div>
</template>
