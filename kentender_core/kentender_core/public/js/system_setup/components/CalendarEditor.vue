<script setup>
// CFG-CHG-002 v0.11 §10.9 (C04 "calendar") — the working-day calendar, which
// had a complete backend (Phase 2d) and no screen at all until now.
//
// A calendar version is immutable like every other versioned record here: a
// correction is a new version, never an edit. Holiday rows are editable only
// while the version is unsaved — the artboard is explicit that Add row /
// Remove row appear in the editor and nowhere else.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { dash, fmtDate } from "../data/format.js";

const props = defineProps({
	// Empty when adding the first version of a new calendar.
	name: { type: String, default: "" },
	creating: { type: Boolean, default: false },
});
const emit = defineEmits(["back", "saved"]);

const WEEKEND_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const loading = ref(!props.creating);
const loadError = ref("");
const calendar = ref(null);
const busy = ref(false);
const error = ref("");

const form = ref({
	calendar_name: "",
	effective_from: "",
	effective_until: "",
	weekend_days: ["Saturday", "Sunday"],
	source_instrument: "",
	provision: "",
	source_document: "",
});
const holidays = ref([]);

async function load() {
	if (props.creating) return;
	loading.value = true;
	loadError.value = "";
	try {
		calendar.value = await procurementSettingsApi.getBusinessDayCalendar(props.name);
		form.value = {
			calendar_name: calendar.value.calendar_name || "",
			effective_from: calendar.value.effective_from || "",
			effective_until: calendar.value.effective_until || "",
			weekend_days: [...(calendar.value.weekend_days || [])],
			source_instrument: calendar.value.source_instrument || "",
			provision: calendar.value.provision || "",
			source_document: calendar.value.source_document || "",
		};
		holidays.value = [...(calendar.value.holidays || [])];
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

// Saved detail is read-only; the editor is the create/new-version state.
const editing = computed(() => props.creating || successor.value);
const successor = ref(false);

function toggleWeekend(day) {
	const index = form.value.weekend_days.indexOf(day);
	if (index === -1) form.value.weekend_days.push(day);
	else form.value.weekend_days.splice(index, 1);
}
function addHoliday() {
	holidays.value.push({ holiday_date: "", holiday_name: "" });
}
function removeHoliday(index) {
	holidays.value.splice(index, 1);
}

function startSuccessor() {
	successor.value = true;
	form.value.effective_from = "";
	form.value.effective_until = "";
}

const canSave = computed(
	() => !busy.value && !!form.value.calendar_name.trim() && !!form.value.effective_from && form.value.weekend_days.length > 0
);

async function save() {
	busy.value = true;
	error.value = "";
	try {
		await procurementSettingsApi.registerBusinessDayCalendarVersion({
			calendar_name: form.value.calendar_name.trim(),
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until,
			weekend_days: form.value.weekend_days,
			holidays: holidays.value.filter((row) => (row.holiday_date || "").trim()),
			source_instrument: form.value.source_instrument,
			provision: form.value.provision,
			source_document: form.value.source_document,
		});
		emit("saved");
	} catch (e) {
		error.value = e.message;
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div class="kt-procset-view" data-testid="kt-procset-calendar">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title">{{ __("Working-day calendar") }}</h2>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-calendar-back" @click="emit('back')">← {{ __("Procurement settings") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-calendar-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:50%" />
		</div>
		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-calendar-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("This record isn't available to you") }}</h2>
			<p>{{ __("It may not exist, or you may not have access to it.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="emit('back')">{{ __("Back to Procurement settings") }}</button>
		</div>

		<template v-else>
			<div class="kt-card kt-blueprint kt-procset-wide">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />

				<div class="kt-setup-grid">
					<div class="kt-field">
						<label for="kt-cal-name">{{ __("Calendar name") }}</label>
						<input v-if="editing" id="kt-cal-name" v-model="form.calendar_name" class="kt-input" data-testid="kt-cal-name">
						<div v-else class="kt-ro" data-testid="kt-cal-name-ro">{{ dash(form.calendar_name) }}</div>
					</div>
					<div class="kt-field">
						<label for="kt-cal-from">{{ __("Applies from") }}</label>
						<input v-if="editing" id="kt-cal-from" v-model="form.effective_from" class="kt-input" type="date" data-testid="kt-cal-from">
						<div v-else class="kt-ro">{{ fmtDate(form.effective_from) }}</div>
					</div>
					<div class="kt-field">
						<label for="kt-cal-until">{{ __("Applies until") }}</label>
						<input v-if="editing" id="kt-cal-until" v-model="form.effective_until" class="kt-input" type="date" data-testid="kt-cal-until">
						<div v-else class="kt-ro">{{ fmtDate(form.effective_until) }}</div>
					</div>
					<div class="kt-field">
						<label id="kt-cal-weekend-label">{{ __("Weekend days") }}</label>
						<div v-if="editing" style="display:flex;gap:14px;flex-wrap:wrap" role="group" aria-labelledby="kt-cal-weekend-label">
							<label v-for="day in WEEKEND_DAYS" :key="day" class="kt-checkbox">
								<input
									type="checkbox"
									:checked="form.weekend_days.includes(day)"
									:data-testid="'kt-cal-weekend-' + day"
									@change="toggleWeekend(day)"
								>
								<span class="box" />{{ day }}
							</label>
						</div>
						<div v-else class="kt-ro" data-testid="kt-cal-weekend-ro">{{ form.weekend_days.join(", ") || "—" }}</div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Holiday date / Holiday name") }}</h6>
					<table class="kt-table" data-testid="kt-cal-holidays">
						<thead>
							<tr>
								<th>{{ __("Holiday date") }}</th>
								<th>{{ __("Holiday name") }}</th>
								<th v-if="editing">{{ __("Action") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="(row, index) in holidays" :key="index">
								<td>
									<input v-if="editing" v-model="row.holiday_date" class="kt-input" type="date" :data-testid="'kt-cal-holiday-date-' + index">
									<template v-else>{{ fmtDate(row.holiday_date) }}</template>
								</td>
								<td>
									<input v-if="editing" v-model="row.holiday_name" class="kt-input" :data-testid="'kt-cal-holiday-name-' + index">
									<template v-else>{{ dash(row.holiday_name) }}</template>
								</td>
								<td v-if="editing">
									<button type="button" class="kt-btn kt-btn-ghost kt-btn-sm" @click="removeHoliday(index)">{{ __("Remove row") }}</button>
								</td>
							</tr>
							<tr v-if="!holidays.length">
								<td :colspan="editing ? 3 : 2" class="kt-muted">{{ __("No holiday rows.") }}</td>
							</tr>
						</tbody>
					</table>
					<!-- Editor only, exactly as the artboard states. -->
					<button v-if="editing" type="button" class="kt-btn kt-btn-ghost kt-btn-sm" style="margin-top:8px" data-testid="kt-cal-add-holiday" @click="addHoliday">
						{{ __("Add row") }}
					</button>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div v-if="editing" class="kt-setup-grid">
						<div class="kt-field"><label for="kt-cal-instrument">{{ __("Source evidence") }}</label><input id="kt-cal-instrument" v-model="form.source_instrument" class="kt-input" data-testid="kt-cal-instrument"></div>
						<div class="kt-field"><label for="kt-cal-provision">{{ __("Provisions") }}</label><input id="kt-cal-provision" v-model="form.provision" class="kt-input" data-testid="kt-cal-provision"></div>
						<!-- A version being written is always unverified: evidence is a
						     separate appended check, never part of the save. -->
						<div class="kt-field">
							<span class="kt-label">{{ __("Source check") }}</span>
							<span class="kt-meta-value"><span class="kt-status is-attention" data-testid="kt-cal-verification-new">{{ __("Source check needed") }}</span></span>
						</div>
					</div>
					<div v-else class="kt-meta-row">
						<div><span class="kt-label">{{ __("Source evidence") }}</span><span class="kt-meta-value">{{ form.source_instrument || __("Not yet established") }}</span></div>
						<div>
							<span class="kt-label">{{ __("Source check") }}</span>
							<span class="kt-meta-value">
								<span :class="calendar && calendar.verification_status === 'Verified' ? 'kt-status is-live' : 'kt-status is-attention'" data-testid="kt-cal-verification">
									{{ calendar && calendar.verification_status === "Verified" ? __("Sources verified") : __("Source check needed") }}
								</span>
							</span>
						</div>
					</div>
				</div>

				<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-cal-error">{{ error }}</p>

				<div class="kt-procset-card-actions">
					<template v-if="editing">
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-cal-cancel" @click="emit('back')">{{ __("Cancel") }}</button>
						<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-cal-save" @click="save">{{ __("Save calendar version") }}</button>
					</template>
					<template v-else>
						<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-cal-new-version" @click="startSuccessor">{{ __("Create new version") }}</button>
					</template>
				</div>
			</div>
		</template>
	</div>
</template>
