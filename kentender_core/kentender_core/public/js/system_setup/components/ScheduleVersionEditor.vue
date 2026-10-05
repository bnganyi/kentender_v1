<script setup>
// CFG-CHG-002 v0.14 §10.9 (C04 #add, #detail's selected interval; tracker
// CFG14-5F) — the procurement schedule editor, ported from the board:
//
// - "create": Add procurement schedule — Name, Method, Procedure, Category,
//   the common fields, the milestones and intervals; Save schedule version.
//   A method and category that already have a schedule open that schedule's
//   new version instead of a duplicate (as D21 does for method rules).
// - "version": a successor, with the board's footer — Earlier versions this
//   replaces (only when the dates overlap, D16) and Reason for change.
// - "correct": this version itself, while nothing depends on it (D15).
//
// The intervals are the model's (D22): each runs from the previous applying
// milestone to the next, and its days, bounds, basis and reference are the
// closing milestone's. Selecting an interval opens the board's selected-
// interval controls for it. A bound is either a value or not yet established
// — "No limit stated in the verified source" and "Override allowed" have no
// field to hold them (FU-33), so they are not offered.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { datesOverlap } from "../data/format.js";
import { sourceCheckLabel } from "../data/format.js";
import RuleFormError from "./RuleFormError.vue";

const props = defineProps({
	name: { type: String, default: "" },
	mode: { type: String, default: "version" }, // "create" | "version" | "correct"
	calendars: { type: Array, default: () => [] },
	applicabilityBases: { type: Array, default: () => [] },
	verificationStatuses: { type: Array, default: () => [] },
	methods: { type: Array, default: () => [] },
	categories: { type: Array, default: () => [] },
	// The seven milestones ({ milestone, label }) a new schedule starts from.
	milestoneCatalogue: { type: Array, default: () => [] },
	// Existing schedules, so "create" can point to one that already covers
	// the chosen method and category.
	schedules: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel", "open-version", "refresh"]);

const creating = computed(() => props.mode === "create");
const correcting = computed(() => props.mode === "correct");

const COUNTING_RULES = ["Calendar days", "Working days"];
const BASES = [
	{ value: "Statutory", label: __("Legal requirement") },
	{ value: "Planning assumption", label: __("Planning assumption") },
	{ value: "Source-derived", label: __("Source-derived") },
];

const loading = ref(!creating.value);
const loadError = ref("");
const current = ref(null);
const error = ref("");
const form = ref(null);
const milestones = ref([]);
const selected = ref("");
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

// A working-day schedule counts only by a verified, active calendar.
const usableCalendars = computed(() => (props.calendars || []).filter((row) => row.status === "Active" && row.verification_status === "Verified"));
const basisOptions = computed(() => {
	const stored = form.value?.applicability_basis;
	const options = [...props.applicabilityBases];
	if (stored && !options.includes(stored)) options.unshift(stored);
	return options;
});

function blankForm() {
	return {
		profile_name: "", procedure: "", procurement_method: "", procurement_category: "", effective_from: "", effective_until: "",
		applicability_basis: "", counting_rule: "Calendar days", calendar: "", estimated_delivery_period_default_days: "",
		verification_status: "", source_instrument: "", provision: "", source_document: "", change_reason: "",
	};
}
const text = (value) => (value === null || value === undefined ? "" : String(value));

async function load() {
	if (creating.value) {
		current.value = { version_number: 0 };
		form.value = blankForm();
		milestones.value = props.milestoneCatalogue.map((row, index) => ({
			milestone: row.milestone, label: row.label, sequence: index + 1, applies: true, counting_rule: "",
			minimum_days: "", maximum_days: "", default_days: "", basis: "", statutory_reference: "",
		}));
		return;
	}
	loading.value = true;
	loadError.value = "";
	try {
		const version = await procurementSettingsApi.getScheduleProfile(props.name);
		current.value = version;
		form.value = {
			...blankForm(),
			profile_name: version.profile_name || "",
			procedure: version.procedure || "",
			procurement_method: version.procurement_method,
			procurement_category: version.procurement_category,
			effective_from: version.effective_from || "",
			effective_until: version.effective_until || "",
			applicability_basis: version.applicability_basis || "",
			counting_rule: version.counting_rule || "Calendar days",
			calendar: version.calendar?.calendar || "",
			estimated_delivery_period_default_days: text(version.estimated_delivery_period_default_days),
			verification_status: version.verification_status || "",
			source_instrument: version.source_instrument || "",
			provision: version.provision || "",
			source_document: version.source_document || "",
		};
		milestones.value = (version.milestones || []).map((row) => ({
			...row,
			minimum_days: text(row.minimum_days),
			maximum_days: text(row.maximum_days),
			default_days: text(row.default_days),
		}));
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
// A new schedule has nothing to read: its form exists before the first render.
if (creating.value) load();
else onMounted(load);

const ruleName = computed(() => form.value?.profile_name || current.value?.profile_name || __("Procurement schedule"));
const title = computed(() => {
	if (creating.value) return __("Add procurement schedule");
	if (correcting.value) return __("{0} — edit schedule", [ruleName.value]);
	return __("{0} — new version", [ruleName.value]);
});
const existing = computed(() =>
	creating.value && form.value?.procurement_method && form.value?.procurement_category
		? props.schedules.find((row) => row.status === "Active" && row.procurement_method === form.value.procurement_method && row.procurement_category === form.value.procurement_category) || null
		: null
);
const replaces = computed(
	() => props.mode === "version" && !!current.value && datesOverlap(current.value.effective_from, current.value.effective_until, form.value?.effective_from, form.value?.effective_until)
);

// Intervals: from the previous applying milestone to each later one.
const intervals = computed(() => {
	const applying = milestones.value.filter((row) => row.applies);
	return applying.slice(1).map((to, index) => ({ from: applying[index], to }));
});
const selectedInterval = computed(() => intervals.value.find((row) => row.to.milestone === selected.value) || null);
const boundStatus = (days) => (days === "" ? "Not yet established" : "Value specified");
function setBound(row, field, status) {
	if (status === "Not yet established") row[field] = "";
	else if (row[field] === "") row[field] = "1";
}
const basisLabel = (value) => (BASES.find((b) => b.value === value) || {}).label || __("Not yet established");
// "Details to complete": a default for each applying period, and a calendar
// when days are working days — the same gaps the server reports on save.
const detailsToComplete = computed(() => {
	const items = intervals.value.filter((row) => row.to.milestone !== "delivery_completion" && row.to.default_days === "").map((row) => __("Default days — {0}", [row.to.label]));
	if (form.value?.counting_rule === "Working days" && !form.value.calendar) items.push(__("Working-day calendar"));
	return items;
});

function num(value) {
	return value === "" || value === null || value === undefined ? 0 : Number(value);
}
// Refusals the server makes, said before the round trip.
const blocked = computed(() => {
	if (!form.value) return __("Loading…");
	if (!form.value.profile_name.trim()) return __("Give this schedule a name.");
	if (creating.value && (!form.value.procurement_method || !form.value.procurement_category)) return __("Select the method and category.");
	if (existing.value) return __("This method and category already have a schedule.");
	if (!form.value.effective_from) return __("Enter the date this version applies from.");
	if (form.value.counting_rule === "Working days" && !form.value.calendar) return __("Select a verified working-day calendar for this schedule.");
	for (const row of milestones.value) {
		const minimum = num(row.minimum_days);
		const maximum = num(row.maximum_days);
		const value = num(row.default_days);
		if (minimum && value && value < minimum) return __("{0}: the default is below the minimum.", [row.label]);
		if (maximum && value && value > maximum) return __("{0}: the default exceeds the maximum.", [row.label]);
	}
	if (props.mode === "version" && !form.value.change_reason.trim()) return __("Say why this version replaces the earlier one.");
	return "";
});
const canSave = computed(() => !busy.value && !blocked.value);

function save() {
	return run(async () => {
		const payload = {
			profile_name: form.value.profile_name.trim(),
			procedure: form.value.procedure,
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until || null,
			counting_rule: form.value.counting_rule,
			calendar: form.value.counting_rule === "Working days" ? form.value.calendar : null,
			estimated_delivery_period_default_days: form.value.estimated_delivery_period_default_days === "" ? null : Number(form.value.estimated_delivery_period_default_days),
			verification_status: form.value.verification_status || null,
			applicability_basis: form.value.applicability_basis || null,
			source_instrument: form.value.source_instrument,
			provision: form.value.provision,
			source_document: form.value.source_document,
			milestones: milestones.value.map((row) => ({
				milestone: row.milestone,
				label: row.label,
				sequence: row.sequence,
				applies: !!row.applies,
				counting_rule: row.counting_rule || form.value.counting_rule,
				minimum_days: num(row.minimum_days),
				maximum_days: num(row.maximum_days),
				default_days: num(row.default_days),
				basis: row.basis || "Statutory",
				statutory_reference: row.statutory_reference,
			})),
		};
		const saved = correcting.value
			? await procurementSettingsApi.updateScheduleProfile({ ...payload, profile: props.name, expected_version: current.value.expected_version })
			: await procurementSettingsApi.registerScheduleProfileVersion({
				...payload,
				procurement_method: form.value.procurement_method,
				procurement_category: form.value.procurement_category,
				supersedes_version_ids: replaces.value ? [props.name] : [],
				change_reason: form.value.change_reason.trim(),
			});
		emit("saved", saved.profile);
	});
}
</script>

<template>
	<div class="kt-schedule" data-testid="kt-procset-schedule-editor">
		<div v-if="loading" data-testid="kt-sve-loading"><div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" /></div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-sve-load-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This schedule isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>

		<div v-else data-testid="kt-sve-card" :data-mode="mode">
			<h3 data-testid="kt-sve-title">{{ title }}</h3>
			<span v-if="!creating" class="tag tag-neutral" data-testid="kt-sve-unsaved">{{ __("Unsaved changes") }}</span>
			<div v-if="correcting" class="kt-notice is-info" style="margin-top:12px" data-testid="kt-sve-correcting-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
				<div class="kt-notice-body">{{ __("This schedule has not taken effect and no plan uses it yet, so it can be changed here. Once either happens, changing it means a new version.") }}</div>
			</div>

			<!-- C04 #add — the schedule's identity. Method and category are
			     what it covers: fixed once saved (a different pair is a
			     different schedule). -->
			<div class="kt-sve-grid" data-testid="kt-sve-identity">
				<div class="field"><label for="kt-sve-name">{{ __("Name") }}</label><input id="kt-sve-name" v-model="form.profile_name" class="input" data-testid="kt-sve-name"></div>
				<div class="field">
					<label for="kt-sve-method">{{ __("Method") }}</label>
					<select id="kt-sve-method" v-model="form.procurement_method" class="input" :disabled="!creating" data-testid="kt-sve-method">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="method in (creating ? methods : [form.procurement_method])" :key="method" :value="method">{{ method }}</option>
					</select>
				</div>
				<div class="field"><label for="kt-sve-procedure">{{ __("Procedure") }}</label><input id="kt-sve-procedure" v-model="form.procedure" class="input" data-testid="kt-sve-procedure"></div>
				<div class="field">
					<label for="kt-sve-category">{{ __("Category") }}</label>
					<select id="kt-sve-category" v-model="form.procurement_category" class="input" :disabled="!creating" data-testid="kt-sve-category">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="category in (creating ? categories : [form.procurement_category])" :key="category" :value="category">{{ category }}</option>
					</select>
				</div>
			</div>
			<div v-if="existing" class="kt-notice is-info" style="flex-direction:column;align-items:flex-start;margin-bottom:12px" data-testid="kt-sve-exists">
				<div style="display:flex;gap:12px;align-items:flex-start">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
					<div class="kt-notice-body">{{ __("{0} already covers {1} — {2}. Change it by creating a new version.", [existing.profile_name, form.procurement_method, form.procurement_category]) }}</div>
				</div>
				<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-sve-open-existing" @click.prevent="emit('open-version', existing.profile)">{{ __("Create new version") }}</a>
			</div>

			<h6 class="kt-card-title">{{ __("When this schedule applies") }}</h6>
			<div class="kt-sve-grid">
				<div class="field"><label for="kt-sve-from">{{ __("Applies from") }}</label><input id="kt-sve-from" v-model="form.effective_from" class="input" type="date" data-testid="kt-sve-from"></div>
				<div class="field"><label for="kt-sve-until">{{ __("Applies until") }}</label><input id="kt-sve-until" v-model="form.effective_until" class="input" type="date" data-testid="kt-sve-until"></div>
				<div class="field" style="grid-column:1/-1">
					<label for="kt-sve-basis">{{ __("Which date determines the rule to use?") }}</label>
					<select id="kt-sve-basis" v-model="form.applicability_basis" class="input" data-testid="kt-sve-basis">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="basis in basisOptions" :key="basis" :value="basis">{{ basis }}</option>
					</select>
				</div>
				<div class="field">
					<label for="kt-sve-counting">{{ __("Days counted") }}</label>
					<select id="kt-sve-counting" v-model="form.counting_rule" class="input" data-testid="kt-sve-counting">
						<option v-for="rule in COUNTING_RULES" :key="rule" :value="rule">{{ __(rule) }}</option>
					</select>
				</div>
				<div v-if="form.counting_rule === 'Working days'" class="field">
					<label for="kt-sve-calendar">{{ __("Working-day calendar") }}</label>
					<select id="kt-sve-calendar" v-model="form.calendar" class="input" :aria-invalid="form.calendar ? 'false' : 'true'" data-testid="kt-sve-calendar">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="row in usableCalendars" :key="row.calendar" :value="row.calendar">{{ row.calendar_name }} · {{ __("Version {0}", [row.version_number]) }}</option>
					</select>
				</div>
				<div class="field"><label for="kt-sve-delivery">{{ __("Estimated delivery period default") }}</label><input id="kt-sve-delivery" v-model="form.estimated_delivery_period_default_days" class="input" type="number" min="0" :placeholder="__('Not set')" data-testid="kt-sve-delivery"></div>
			</div>
			<div v-if="form.counting_rule === 'Working days' && !form.calendar" class="kt-notice is-critical" style="margin-bottom:12px" data-testid="kt-sve-calendar-missing">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
				<div class="kt-notice-body">{{ __("Select a verified working-day calendar for this interval.") }}</div>
			</div>

			<h6 class="kt-card-title">{{ __("Milestones") }}</h6>
			<table class="table" style="margin-bottom:16px" data-testid="kt-sve-milestones">
				<thead><tr><th>{{ __("Milestone") }}</th><th>{{ __("Order") }}</th><th>{{ __("Applies") }}</th></tr></thead>
				<tbody>
					<tr v-for="(row, index) in milestones" :key="row.milestone" :data-testid="'kt-sve-milestone-' + row.milestone">
						<td>{{ row.label }}</td>
						<td>{{ row.sequence }}</td>
						<td><label class="kt-checkbox"><input v-model="row.applies" type="checkbox" :aria-label="__('Applies: {0}', [row.label])" :data-testid="'kt-sve-applies-' + index"><span class="box" /></label></td>
					</tr>
				</tbody>
			</table>

			<h6 class="kt-card-title">{{ __("Time intervals") }}</h6>
			<div class="kt-table-scroll">
				<table class="table" data-testid="kt-sve-intervals">
					<thead><tr><th>{{ __("From") }}</th><th>{{ __("To") }}</th><th>{{ __("Days counted") }}</th><th>{{ __("Minimum status") }}</th><th>{{ __("Minimum days") }}</th><th>{{ __("Maximum status") }}</th><th>{{ __("Maximum days") }}</th><th>{{ __("Default days") }}</th><th>{{ __("Default basis") }}</th><th><span class="kt-visually-hidden">{{ __("Action") }}</span></th></tr></thead>
					<tbody>
						<tr v-for="row in intervals" :key="row.to.milestone" :class="{ 'is-selected': selected === row.to.milestone }" :data-testid="'kt-sve-interval-' + row.to.milestone">
							<td>{{ row.from.label }}</td>
							<td>{{ row.to.label }}</td>
							<td>{{ __(row.to.counting_rule || form.counting_rule) }}</td>
							<td>{{ __(boundStatus(row.to.minimum_days)) }}</td>
							<td>{{ row.to.minimum_days || "—" }}</td>
							<td>{{ __(boundStatus(row.to.maximum_days)) }}</td>
							<td>{{ row.to.maximum_days || "—" }}</td>
							<td>{{ row.to.default_days || "—" }}</td>
							<td>{{ basisLabel(row.to.basis) }}</td>
							<td><a href="#" :aria-pressed="selected === row.to.milestone ? 'true' : 'false'" :data-testid="'kt-sve-select-' + row.to.milestone" @click.prevent="selected = selected === row.to.milestone ? '' : row.to.milestone">{{ selected === row.to.milestone ? __("Close") : __("Edit") }}</a></td>
						</tr>
					</tbody>
				</table>
			</div>

			<!-- C04 #detail — the selected interval's own controls. -->
			<template v-if="selectedInterval">
				<h6 class="kt-card-title" style="margin-top:20px" data-testid="kt-sve-selected-title">{{ __("Selected interval — {0}", [selectedInterval.to.label]) }}</h6>
				<div class="kt-sve-interval-grid" data-testid="kt-sve-selected">
					<div class="field"><label for="kt-sve-i-from">{{ __("From") }}</label><select id="kt-sve-i-from" class="input" disabled><option>{{ selectedInterval.from.label }}</option></select></div>
					<div class="field"><label for="kt-sve-i-to">{{ __("To") }}</label><select id="kt-sve-i-to" class="input" disabled><option>{{ selectedInterval.to.label }}</option></select></div>
					<div class="field">
						<label for="kt-sve-i-counting">{{ __("Days counted") }}</label>
						<select id="kt-sve-i-counting" v-model="selectedInterval.to.counting_rule" class="input" data-testid="kt-sve-i-counting">
							<option value="">{{ __("As the schedule ({0})", [__(form.counting_rule)]) }}</option>
							<option v-for="rule in COUNTING_RULES" :key="rule" :value="rule">{{ __(rule) }}</option>
						</select>
					</div>
					<div class="field"><label for="kt-sve-i-convention">{{ __("Counting convention") }}</label><input id="kt-sve-i-convention" class="input" :value="__('Excludes the start date; includes the end date')" readonly></div>
					<div class="field">
						<label for="kt-sve-i-min-status">{{ __("Minimum status") }}</label>
						<select id="kt-sve-i-min-status" class="input" :value="boundStatus(selectedInterval.to.minimum_days)" data-testid="kt-sve-i-min-status" @change="setBound(selectedInterval.to, 'minimum_days', $event.target.value)">
							<option value="Value specified">{{ __("Value specified") }}</option>
							<option value="Not yet established">{{ __("Not yet established") }}</option>
						</select>
					</div>
					<div class="field"><label for="kt-sve-i-min">{{ __("Minimum days") }}</label><input id="kt-sve-i-min" v-model="selectedInterval.to.minimum_days" class="input" type="number" min="1" :disabled="selectedInterval.to.minimum_days === ''" data-testid="kt-sve-i-min"></div>
					<div class="field">
						<label for="kt-sve-i-max-status">{{ __("Maximum status") }}</label>
						<select id="kt-sve-i-max-status" class="input" :value="boundStatus(selectedInterval.to.maximum_days)" data-testid="kt-sve-i-max-status" @change="setBound(selectedInterval.to, 'maximum_days', $event.target.value)">
							<option value="Value specified">{{ __("Value specified") }}</option>
							<option value="Not yet established">{{ __("Not yet established") }}</option>
						</select>
					</div>
					<div class="field"><label for="kt-sve-i-max">{{ __("Maximum days") }}</label><input id="kt-sve-i-max" v-model="selectedInterval.to.maximum_days" class="input" type="number" min="1" :disabled="selectedInterval.to.maximum_days === ''" data-testid="kt-sve-i-max"></div>
					<div class="field"><label for="kt-sve-i-default">{{ __("Default days") }}</label><input id="kt-sve-i-default" v-model="selectedInterval.to.default_days" class="input" type="number" min="0" data-testid="kt-sve-i-default"></div>
					<div class="field">
						<label for="kt-sve-i-basis">{{ __("Default basis") }}</label>
						<select id="kt-sve-i-basis" v-model="selectedInterval.to.basis" class="input" data-testid="kt-sve-i-basis">
							<option value="">{{ __("Not yet established") }}</option>
							<option v-for="basis in BASES" :key="basis.value" :value="basis.value">{{ basis.label }}</option>
						</select>
					</div>
					<div class="field"><label for="kt-sve-i-reference">{{ __("Source reference") }}</label><input id="kt-sve-i-reference" v-model="selectedInterval.to.statutory_reference" class="input" data-testid="kt-sve-i-reference"></div>
				</div>
			</template>

			<div v-if="detailsToComplete.length" style="margin-top:12px" data-testid="kt-sve-details">
				<div style="font-weight:600;font-size:13px;margin-bottom:4px">{{ __("Details to complete") }}</div>
				<ul style="margin:0;padding-left:18px;font-size:13px"><li v-for="item in detailsToComplete" :key="item">{{ item }}</li></ul>
			</div>

			<h6 class="kt-card-title" style="margin-top:20px">{{ __("Sources and interpretation") }}</h6>
			<div class="kt-sve-grid">
				<div class="field"><label for="kt-sve-instrument">{{ __("Instrument") }}</label><input id="kt-sve-instrument" v-model="form.source_instrument" class="input" data-testid="kt-sve-instrument"></div>
				<div class="field"><label for="kt-sve-provisions">{{ __("Provisions") }}</label><input id="kt-sve-provisions" v-model="form.provision" class="input" data-testid="kt-sve-provisions"></div>
				<div class="field"><label for="kt-sve-url">{{ __("Source URL") }}</label><input id="kt-sve-url" v-model="form.source_document" class="input" data-testid="kt-sve-url"></div>
				<div v-if="verificationStatuses.length" class="field">
					<label for="kt-sve-check">{{ __("Source check") }}</label>
					<select id="kt-sve-check" v-model="form.verification_status" class="input" data-testid="kt-sve-check">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="status in verificationStatuses" :key="status" :value="status">{{ __(sourceCheckLabel(status)) }}</option>
					</select>
				</div>
			</div>

			<RuleFormError :error="error" style="margin-top:12px" @refresh="emit('refresh')" />

			<!-- C04 #add card 2 — the new-version footer: what it replaces and why. -->
			<div v-if="mode === 'version'" class="kt-sve-version-footer" data-testid="kt-sve-replacement">
				<p class="card-body" data-testid="kt-sve-replaces">
					{{ replaces ? __("Earlier versions this replaces: {0} Version {1}.", [ruleName, current.version_number]) : __("These dates do not overlap Version {0}, so it is not replaced.", [current.version_number]) }}
				</p>
				<div class="field"><label for="kt-sve-reason">{{ __("Reason for change") }}</label><textarea id="kt-sve-reason" v-model="form.change_reason" class="input" rows="2" data-testid="kt-sve-reason" /></div>
			</div>
			<div style="display:flex;gap:8px;justify-content:flex-end;align-items:center;margin-top:12px;flex-wrap:wrap">
				<span v-if="blocked" class="kt-blocked" data-testid="kt-sve-blocked">{{ blocked }}</span>
				<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-sve-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="!canSave" data-testid="kt-sve-save" @click="save">
					{{ correcting ? __("Save changes") : creating ? __("Save schedule version") : __("Save new version") }}
				</button>
			</div>
		</div>
	</div>
</template>
