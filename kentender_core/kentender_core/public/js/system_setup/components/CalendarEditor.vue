<script setup>
// CFG-CHG-002 v0.14 §10.9 (C04 #calendar editor and #calendar-version;
// tracker CFG14-5F) — the working-day calendar's forms, ported from the board:
//
// - "create": a new calendar — Save calendar version;
// - "version": a successor to a saved version, with what it replaces and the
//   reason — Save new version (D16: it replaces the earlier one only when
//   their dates overlap);
// - "correct": the saved version itself, while no schedule counts days by
//   it, no source check has been recorded and it has not taken effect (D15).
//
// Holiday rows have Add row / Remove row only here, never on the saved detail.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { datesOverlap } from "../data/format.js";
import RuleFormError from "./RuleFormError.vue";

const props = defineProps({
	// The saved version a successor or correction is opened from.
	name: { type: String, default: "" },
	mode: { type: String, default: "create" }, // "create" | "version" | "correct"
});
const emit = defineEmits(["saved", "cancel"]);

const WEEKEND_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const loading = ref(props.mode !== "create");
const loadError = ref("");
const calendar = ref(null);
const error = ref("");
const form = ref({ calendar_name: "", effective_from: "", effective_until: "", weekend_days: ["Saturday", "Sunday"], source_instrument: "", provision: "", source_document: "", change_reason: "" });
const holidays = ref([]);
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

async function load() {
	if (props.mode === "create") return;
	loading.value = true;
	loadError.value = "";
	try {
		calendar.value = await procurementSettingsApi.getBusinessDayCalendar(props.name);
		const c = calendar.value;
		form.value = {
			calendar_name: c.calendar_name || "",
			// A successor covers a different period, so it starts without one
			// rather than silently inheriting the dates it replaces.
			effective_from: props.mode === "correct" ? c.effective_from || "" : "",
			effective_until: props.mode === "correct" ? c.effective_until || "" : "",
			weekend_days: [...(c.weekend_days || [])],
			source_instrument: c.source_instrument || "",
			provision: c.provision || "",
			source_document: c.source_document || "",
			change_reason: "",
		};
		holidays.value = (c.holidays || []).map((row) => ({ ...row }));
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

const title = computed(() => {
	if (props.mode === "version") return __("Working-day calendar — new version");
	if (props.mode === "correct") return __("Working-day calendar — edit calendar");
	return __("Working-day calendar");
});
const replaces = computed(
	() => props.mode === "version" && !!calendar.value && datesOverlap(calendar.value.effective_from, calendar.value.effective_until, form.value.effective_from, form.value.effective_until)
);

function toggleWeekend(day) {
	const index = form.value.weekend_days.indexOf(day);
	if (index === -1) form.value.weekend_days.push(day);
	else form.value.weekend_days.splice(index, 1);
}
function addHoliday() {
	holidays.value.push({ holiday_date: "", holiday_name: "", source_reference: "" });
}
function removeHoliday(index) {
	holidays.value.splice(index, 1);
}

const canSave = computed(
	() => !busy.value && !!form.value.calendar_name.trim() && !!form.value.effective_from && form.value.weekend_days.length > 0
);

function save() {
	return run(async () => {
		const payload = {
			calendar_name: form.value.calendar_name.trim(),
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until,
			weekend_days: form.value.weekend_days,
			holidays: holidays.value.filter((row) => (row.holiday_date || "").trim()),
			source_instrument: form.value.source_instrument,
			provision: form.value.provision,
			source_document: form.value.source_document,
		};
		let saved;
		if (props.mode === "correct") {
			saved = await procurementSettingsApi.updateBusinessDayCalendar({ ...payload, calendar: props.name, expected_version: calendar.value.expected_version });
		} else {
			saved = await procurementSettingsApi.registerBusinessDayCalendarVersion({
				...payload,
				supersedes_version_ids: replaces.value ? [props.name] : [],
				change_reason: form.value.change_reason.trim(),
			});
		}
		emit("saved", saved?.calendar || props.name);
	});
}
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
		<div v-else data-testid="kt-calendar-editor" :data-mode="mode">
			<h3 data-testid="kt-cal-title">{{ title }}</h3>
			<div v-if="mode === 'correct'" class="kt-notice is-info" style="margin-top:12px" data-testid="kt-cal-correcting-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
				<div class="kt-notice-body">{{ __("No schedule counts days by this calendar, no source check has been recorded and it has not taken effect, so it can be changed here. Once any of those happens, changing it means a new version.") }}</div>
			</div>
			<div class="kt-cal-grid">
				<div class="field"><label for="kt-cal-name">{{ __("Calendar name") }}</label><input id="kt-cal-name" v-model="form.calendar_name" class="input" :disabled="mode === 'version'" data-testid="kt-cal-name"></div>
				<div class="field"><label for="kt-cal-from">{{ __("Applies from") }}</label><input id="kt-cal-from" v-model="form.effective_from" class="input" type="date" data-testid="kt-cal-from"></div>
				<div class="field"><label for="kt-cal-until">{{ __("Applies until") }}</label><input id="kt-cal-until" v-model="form.effective_until" class="input" type="date" data-testid="kt-cal-until"></div>
				<div class="field">
					<label id="kt-cal-weekend-label">{{ __("Weekend days") }}</label>
					<div style="display:flex;gap:14px;flex-wrap:wrap" role="group" aria-labelledby="kt-cal-weekend-label">
						<label v-for="day in WEEKEND_DAYS" :key="day" class="kt-checkbox">
							<input type="checkbox" :checked="form.weekend_days.includes(day)" :data-testid="'kt-cal-weekend-' + day" @change="toggleWeekend(day)">
							<span class="box" />{{ __(day) }}
						</label>
					</div>
				</div>
				<template v-if="mode === 'version'">
					<div class="field"><label for="kt-cal-replaces">{{ __("Earlier versions this replaces") }}</label><input id="kt-cal-replaces" class="input" :value="replaces ? __('Version {0}', [calendar.version_number]) : __('None — these dates do not overlap Version {0}', [calendar.version_number])" disabled data-testid="kt-cal-replaces"></div>
					<div class="field" style="grid-column:1/-1"><label for="kt-cal-reason">{{ __("Reason for change") }}</label><textarea id="kt-cal-reason" v-model="form.change_reason" class="input" rows="2" data-testid="kt-cal-reason" /></div>
				</template>
			</div>

			<h6 class="kt-card-title">{{ __("Holidays") }}</h6>
			<table class="table" data-testid="kt-cal-holidays">
				<thead><tr><th>{{ __("Holiday date") }}</th><th>{{ __("Holiday name") }}</th><th>{{ __("Source evidence") }}</th><th><span class="kt-visually-hidden">{{ __("Action") }}</span></th></tr></thead>
				<tbody>
					<tr v-for="(row, index) in holidays" :key="index">
						<td><input v-model="row.holiday_date" class="input" type="date" :aria-label="__('Holiday date')" :data-testid="'kt-cal-holiday-date-' + index"></td>
						<td><input v-model="row.holiday_name" class="input" :aria-label="__('Holiday name')" :data-testid="'kt-cal-holiday-name-' + index"></td>
						<td><input v-model="row.source_reference" class="input" :aria-label="__('Source evidence')" :data-testid="'kt-cal-holiday-source-' + index"></td>
						<td><button type="button" class="btn btn-ghost btn-sm" :data-testid="'kt-cal-holiday-remove-' + index" @click="removeHoliday(index)">{{ __("Remove row") }}</button></td>
					</tr>
					<tr v-if="!holidays.length"><td colspan="4" class="text-muted">{{ __("No holiday rows.") }}</td></tr>
				</tbody>
			</table>
			<div style="margin-top:8px"><button type="button" class="btn btn-ghost" data-testid="kt-cal-add-holiday" @click="addHoliday">{{ __("Add row") }}</button></div>
			<div class="field" style="margin-top:14px"><label for="kt-cal-instrument">{{ __("Source evidence") }}</label><textarea id="kt-cal-instrument" v-model="form.source_instrument" class="input" rows="2" data-testid="kt-cal-instrument" /></div>

			<RuleFormError :error="error" style="margin-top:12px" @refresh="load" />

			<div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;justify-content:flex-end">
				<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-cal-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="!canSave" data-testid="kt-cal-save" @click="save">
					{{ mode === "correct" ? __("Save changes") : mode === "version" ? __("Save new version") : __("Save calendar version") }}
				</button>
			</div>
		</div>
	</div>
</template>
