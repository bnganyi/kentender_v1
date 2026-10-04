<script setup>
// CFG-CHG-002 v0.14 §10.9 (C04 #calendar-detail; tracker CFG14-5F) — one saved
// working-day calendar version, read-only: its facts in one row, its
// holidays, its source evidence, and the actions. It is corrected in place
// only while the server allows (D15, "Edit calendar"); otherwise the
// read-only state says a new version is the way to change it.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { dash, fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
});
const emit = defineEmits(["edit", "new-version", "check-sources", "history"]);

const loading = ref(true);
const loadError = ref("");
const calendar = ref(null);

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		calendar.value = await procurementSettingsApi.getBusinessDayCalendar(props.name);
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

const notEstablished = __("Not yet established");
const weekend = computed(() => (calendar.value?.weekend_days || []).join(", ") || notEstablished);
</script>

<template>
	<div class="kt-calendar" data-testid="kt-procset-calendar">
		<div v-if="loading" data-testid="kt-calendar-loading">
			<div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" />
		</div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-calendar-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This record isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>
		<div v-else data-testid="kt-calendar-detail">
			<h3>{{ __("Working-day calendar") }}</h3>
			<div class="kt-meta-row" style="margin:16px 0">
				<div><span class="kt-label">{{ __("Calendar name") }}</span><span class="kt-meta-value" data-testid="kt-cal-name-ro">{{ calendar.calendar_name || notEstablished }}</span></div>
				<div><span class="kt-label">{{ __("Version") }}</span><span class="kt-meta-value" data-testid="kt-cal-version">{{ calendar.version_number }}</span></div>
				<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ calendar.effective_from ? fmtDate(calendar.effective_from) : notEstablished }}</span></div>
				<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ calendar.effective_until ? fmtDate(calendar.effective_until) : notEstablished }}</span></div>
				<div><span class="kt-label">{{ __("Weekend days") }}</span><span class="kt-meta-value" data-testid="kt-cal-weekend-ro">{{ weekend }}</span></div>
				<div><span class="kt-label">{{ __("Source check") }}</span><span class="kt-meta-value"><span :class="sourceCheckClass(calendar.verification_status)" data-testid="kt-cal-verification">{{ __(sourceCheckLabel(calendar.verification_status)) }}</span></span></div>
			</div>
			<h6 class="kt-card-title">{{ __("Holidays") }}</h6>
			<table class="kt-table" data-testid="kt-cal-holidays">
				<thead><tr><th>{{ __("Holiday date") }}</th><th>{{ __("Holiday name") }}</th><th>{{ __("Source evidence") }}</th></tr></thead>
				<tbody>
					<tr v-for="row in calendar.holidays" :key="row.holiday_date">
						<td>{{ fmtDate(row.holiday_date) }}</td>
						<td>{{ dash(row.holiday_name) }}</td>
						<td>{{ dash(row.source_reference) }}</td>
					</tr>
					<tr v-if="!calendar.holidays.length"><td colspan="3" class="text-muted">{{ __("No holiday rows.") }}</td></tr>
				</tbody>
			</table>
			<div class="kt-meta-row" style="margin-top:12px">
				<div><span class="kt-label">{{ __("Source evidence") }}</span><span class="kt-meta-value">{{ calendar.source_instrument || notEstablished }}</span></div>
				<div v-if="calendar.change_reason"><span class="kt-label">{{ __("Reason for this version") }}</span><span class="kt-meta-value" data-testid="kt-cal-change-reason">{{ calendar.change_reason }}</span></div>
			</div>
			<div v-if="!calendar.can_edit" class="kt-notice is-info" style="margin-top:12px" data-testid="kt-cal-readonly">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
				<div class="kt-notice-body">{{ __("This version is read-only. Create a new version to change it.") }}</div>
			</div>
			<div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap">
				<!-- D15: a version nothing depends on yet is corrected in place. -->
				<button v-if="calendar.can_edit" type="button" class="kt-btn kt-btn-secondary" data-testid="kt-cal-edit" @click="emit('edit')">{{ __("Edit calendar") }}</button>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-cal-new-version" @click="emit('new-version')">{{ __("Create new version") }}</button>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-cal-check-sources" @click="emit('check-sources')">{{ __("Check sources") }}</button>
				<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-cal-history" @click="emit('history')">{{ __("View usage and history") }}</button>
			</div>
		</div>
	</div>
</template>
