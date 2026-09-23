<script setup>
// CFG-CHG-002 v0.11 §10.9 (C04) — the editor for a procedure schedule.
//
// Changing how long a procedure's stages take is ordinary configuration work,
// and until now the only way to do it was a dialog that offered the milestone
// day counts and nothing else — not the counting rule, not the working-day
// calendar, not whether a milestone applies at all, not the delivery default.
// This screen edits the whole schedule, in one of two modes the server picks:
//
// - "correct" changes this Version itself, while no plan pins it and it has
//   not taken effect. A schedule in that state is unfinished configuration.
// - "version" saves a new Version that supersedes the one it was opened from,
//   with the administrator's reason recorded beside it.
//
// The seven milestones are a fixed, ordered set (§10.1), so rows are edited
// rather than added and removed — which is the one way this differs from the
// method eligibility editor.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { fmtDate, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	mode: { type: String, default: "version" },
	calendars: { type: Array, default: () => [] },
	applicabilityBases: { type: Array, default: () => [] },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel"]);

const correcting = computed(() => props.mode === "correct");

const COUNTING_RULES = ["Calendar days", "Working days"];
const MILESTONE_BASES = ["Statutory", "Planning assumption", "Source-derived"];

const loading = ref(true);
const loadError = ref("");
const current = ref(null);
const busy = ref(false);
const error = ref("");
const form = ref(null);
const milestones = ref([]);

// §10.9 — a working-day schedule may only count by a calendar that is
// verified, active and covers its whole period. Offering any other would be
// offering a choice the server is bound to refuse.
const usableCalendars = computed(() =>
	(props.calendars || []).filter((row) => row.status === "Active" && row.verification_status === "Verified")
);
const basisOptions = computed(() => {
	const stored = form.value?.applicability_basis;
	const options = [...props.applicabilityBases];
	if (stored && !options.includes(stored)) options.unshift(stored);
	return options;
});

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		const version = await procurementSettingsApi.getScheduleProfile(props.name);
		current.value = version;
		form.value = {
			profile_name: version.profile_name || "",
			procedure: version.procedure || "",
			effective_from: version.effective_from || "",
			effective_until: version.effective_until || "",
			applicability_basis: version.applicability_basis || "",
			counting_rule: version.counting_rule || "Calendar days",
			calendar: version.calendar?.calendar || "",
			estimated_delivery_period_default_days:
				version.estimated_delivery_period_default_days === null || version.estimated_delivery_period_default_days === undefined
					? ""
					: String(version.estimated_delivery_period_default_days),
			verification_status: version.verification_status || "",
			source_instrument: version.source_instrument || "",
			provision: version.provision || "",
			source_document: version.source_document || "",
			change_reason: "",
		};
		milestones.value = (version.milestones || []).map((row) => ({
			...row,
			minimum_days: row.minimum_days === null ? "" : String(row.minimum_days),
			maximum_days: row.maximum_days === null ? "" : String(row.maximum_days),
			default_days: row.default_days === null ? "" : String(row.default_days),
		}));
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

function num(value) {
	return value === "" || value === null || value === undefined ? 0 : Number(value);
}

// The server refuses each of these; saying so here means the administrator is
// not told only after losing the form to a failed save.
const blocked = computed(() => {
	if (!form.value) return __("Loading…");
	if (!form.value.profile_name.trim()) return __("Give this schedule a name.");
	if (!form.value.effective_from) return __("Enter the date this version applies from.");
	if (form.value.counting_rule === "Working days" && !form.value.calendar) {
		return __("Select a verified working-day calendar for this schedule.");
	}
	for (const row of milestones.value) {
		const minimum = num(row.minimum_days);
		const maximum = num(row.maximum_days);
		const value = num(row.default_days);
		if (minimum && value && value < minimum) return __("{0}: the default is below the minimum.", [row.label]);
		if (maximum && value && value > maximum) return __("{0}: the default exceeds the maximum.", [row.label]);
	}
	if (!correcting.value && !form.value.change_reason.trim()) return __("Say why this version replaces the earlier one.");
	return "";
});
const canSave = computed(() => !busy.value && !blocked.value);

async function save() {
	busy.value = true;
	error.value = "";
	try {
		const payload = {
			profile_name: form.value.profile_name.trim(),
			procedure: form.value.procedure,
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until || null,
			counting_rule: form.value.counting_rule,
			calendar: form.value.counting_rule === "Working days" ? form.value.calendar : null,
			estimated_delivery_period_default_days:
				form.value.estimated_delivery_period_default_days === "" ? null : Number(form.value.estimated_delivery_period_default_days),
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
				basis: row.basis,
				statutory_reference: row.statutory_reference,
			})),
		};
		const saved = correcting.value
			? await procurementSettingsApi.updateScheduleProfile({
				...payload,
				profile: props.name,
				expected_version: current.value.expected_version,
			})
			: await procurementSettingsApi.registerScheduleProfileVersion({
				...payload,
				procurement_method: current.value.procurement_method,
				procurement_category: current.value.procurement_category,
			});
		emit("saved", saved.profile);
	} catch (e) {
		error.value = e.message;
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div class="kt-procset-view" data-testid="kt-procset-schedule-editor">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title" data-testid="kt-sve-title">
					{{ correcting ? __("Procurement schedule — edit schedule") : __("Procurement schedule — new version") }}
				</h2>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-sve-back" @click="emit('cancel')">← {{ __("Procurement settings") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-sve-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:50%" />
		</div>
		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-sve-load-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("This schedule isn't available to you") }}</h2>
			<p>{{ __("It may not exist, or you may not have access to it.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="emit('cancel')">{{ __("Back to Procurement settings") }}</button>
		</div>

		<template v-else>
			<div class="kt-card kt-blueprint kt-procset-wide" data-testid="kt-sve-card">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />

				<span class="kt-tag kt-tag-neutral" data-testid="kt-sve-unsaved">{{ __("Unsaved changes") }}</span>
				<div class="kt-meta-row" style="margin:12px 0">
					<div><span class="kt-label">{{ correcting ? __("Version") : __("Earlier version") }}</span><span class="kt-meta-value">{{ current.version_number }}</span></div>
					<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_from) }}</span></div>
					<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_until) }}</span></div>
				</div>

				<div v-if="correcting" class="kt-notice" data-testid="kt-sve-correcting-notice">
					<div class="kt-notice-body">
						{{ __("This schedule has not taken effect and no plan uses it yet, so it can be changed here. Once either happens, changing it means a new version.") }}
					</div>
				</div>

				<!-- Which purchases this schedule governs is its identity: a
				     version for a different method or category is a different
				     schedule, not a correction of this one. -->
				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Which purchases does it cover?") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label for="kt-sve-method">{{ __("Method") }}</label>
							<div id="kt-sve-method" class="kt-ro" data-testid="kt-sve-method">{{ current.procurement_method }}</div>
						</div>
						<div class="kt-field">
							<label for="kt-sve-category">{{ __("Category") }}</label>
							<div id="kt-sve-category" class="kt-ro" data-testid="kt-sve-category">{{ current.procurement_category }}</div>
						</div>
						<div class="kt-field">
							<label for="kt-sve-name">{{ __("Schedule name") }}</label>
							<input id="kt-sve-name" v-model="form.profile_name" class="kt-input" data-testid="kt-sve-name">
						</div>
						<div class="kt-field">
							<label for="kt-sve-procedure">{{ __("Procedure") }}</label>
							<input id="kt-sve-procedure" v-model="form.procedure" class="kt-input" data-testid="kt-sve-procedure">
						</div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("When this schedule applies") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label for="kt-sve-from">{{ __("Applies from") }}</label>
							<input id="kt-sve-from" v-model="form.effective_from" class="kt-input" type="date" data-testid="kt-sve-from">
						</div>
						<div class="kt-field">
							<label for="kt-sve-until">{{ __("Applies until") }}</label>
							<input id="kt-sve-until" v-model="form.effective_until" class="kt-input" type="date" data-testid="kt-sve-until">
						</div>
					</div>
					<div class="kt-field">
						<label for="kt-sve-basis">{{ __("Which date determines the rule to use?") }}</label>
						<select id="kt-sve-basis" v-model="form.applicability_basis" class="kt-input" data-testid="kt-sve-basis">
							<option value="">{{ __("— Select —") }}</option>
							<option v-for="basis in basisOptions" :key="basis" :value="basis">{{ basis }}</option>
						</select>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("How days are counted") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label for="kt-sve-counting">{{ __("Counting rule") }}</label>
							<select id="kt-sve-counting" v-model="form.counting_rule" class="kt-input" data-testid="kt-sve-counting">
								<option v-for="rule in COUNTING_RULES" :key="rule" :value="rule">{{ rule }}</option>
							</select>
						</div>
						<div v-if="form.counting_rule === 'Working days'" class="kt-field">
							<label for="kt-sve-calendar">{{ __("Working-day calendar") }}</label>
							<select id="kt-sve-calendar" v-model="form.calendar" class="kt-input" data-testid="kt-sve-calendar">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="row in usableCalendars" :key="row.calendar" :value="row.calendar">
									{{ row.calendar_name }} · {{ __("Version {0}", [row.version_number]) }}
								</option>
							</select>
							<!-- §10.9 — only a verified, active calendar covering the
							     schedule's period can be counted by, so an unverified
							     one is not offered rather than offered and refused. -->
							<p class="kt-hint" data-testid="kt-sve-calendar-hint">
								{{ usableCalendars.length ? __("Only verified calendars can be counted by.") : __("No verified calendar exists yet. Add one before counting working days.") }}
							</p>
						</div>
						<div class="kt-field">
							<label for="kt-sve-delivery">{{ __("Estimated delivery period default (days)") }}</label>
							<input id="kt-sve-delivery" v-model="form.estimated_delivery_period_default_days" class="kt-input" type="number" min="0" :placeholder="__('Not set')" data-testid="kt-sve-delivery">
						</div>
					</div>
				</div>

				<!-- §10.1's seven milestones, in order. A blank statutory bound
				     means the source has not been checked yet, not "no limit". -->
				<div class="kt-section" data-testid="kt-sve-milestones">
					<h6 class="kt-card-title">{{ __("Milestones and periods") }}</h6>
					<table class="kt-table">
						<thead>
							<tr>
								<th>{{ __("Milestone") }}</th>
								<th>{{ __("Used") }}</th>
								<th>{{ __("Minimum days") }}</th>
								<th>{{ __("Maximum days") }}</th>
								<th>{{ __("Default days") }}</th>
								<th>{{ __("Basis") }}</th>
								<th>{{ __("Source reference") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="(row, index) in milestones" :key="row.milestone" :data-testid="'kt-sve-milestone-' + row.milestone">
								<td>{{ row.sequence }}. {{ row.label }}</td>
								<td>
									<label class="kt-checkbox">
										<input type="checkbox" v-model="row.applies" :data-testid="'kt-sve-applies-' + index">
										<span class="box" />
									</label>
								</td>
								<td><input v-model="row.minimum_days" class="kt-input kt-procset-num" type="number" min="0" :placeholder="__('Not set')" :data-testid="'kt-sve-min-' + index"></td>
								<td><input v-model="row.maximum_days" class="kt-input kt-procset-num" type="number" min="0" :placeholder="__('Not set')" :data-testid="'kt-sve-max-' + index"></td>
								<td><input v-model="row.default_days" class="kt-input kt-procset-num" type="number" min="0" :placeholder="__('Not set')" :data-testid="'kt-sve-default-' + index"></td>
								<td>
									<select v-model="row.basis" class="kt-input" :data-testid="'kt-sve-basis-' + index">
										<option v-for="basis in MILESTONE_BASES" :key="basis" :value="basis">{{ basis }}</option>
									</select>
								</td>
								<td><input v-model="row.statutory_reference" class="kt-input" :data-testid="'kt-sve-reference-' + index"></td>
							</tr>
						</tbody>
					</table>
					<p class="kt-muted" style="font-size:12px;margin-top:6px">
						{{ __("A blank statutory bound means the source has not been checked yet, not that there is no limit.") }}
					</p>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label for="kt-sve-instrument">{{ __("Instrument") }}</label>
							<input id="kt-sve-instrument" v-model="form.source_instrument" class="kt-input" data-testid="kt-sve-instrument">
						</div>
						<div class="kt-field">
							<label for="kt-sve-provisions">{{ __("Provisions") }}</label>
							<input id="kt-sve-provisions" v-model="form.provision" class="kt-input" data-testid="kt-sve-provisions">
						</div>
						<div class="kt-field">
							<label for="kt-sve-url">{{ __("Source URL") }}</label>
							<input id="kt-sve-url" v-model="form.source_document" class="kt-input" data-testid="kt-sve-url">
						</div>
						<div class="kt-field">
							<label for="kt-sve-check">{{ __("Source check") }}</label>
							<select id="kt-sve-check" v-model="form.verification_status" class="kt-input" data-testid="kt-sve-check">
								<option v-for="status in verificationStatuses" :key="status" :value="status">{{ __(sourceCheckLabel(status)) }}</option>
							</select>
						</div>
					</div>
				</div>

				<div v-if="!correcting" class="kt-section" data-testid="kt-sve-replacement">
					<div class="kt-field">
						<label for="kt-sve-reason">{{ __("Reason for change") }}</label>
						<textarea id="kt-sve-reason" v-model="form.change_reason" class="kt-input kt-textarea" rows="2" data-testid="kt-sve-reason" />
					</div>
					<p class="kt-muted" style="font-size:13px">
						{{ __("Earlier versions this replaces: Procurement schedule Version {0}.", [current.version_number]) }}
					</p>
					<h6 class="kt-card-title">{{ __("Effect of this replacement") }}</h6>
					<div class="kt-panel">
						<div class="kt-meta-row">
							<div><span class="kt-label">{{ __("Coverage replaced") }}</span><span class="kt-meta-value">{{ __("Version {0}, for matching applicability within the displayed period", [current.version_number]) }}</span></div>
							<div><span class="kt-label">{{ __("Current readiness") }}</span><span class="kt-meta-value">{{ current.verification_status === "Verified" ? __("Version {0} is verified", [current.version_number]) : __("Version {0} already needs source checks", [current.version_number]) }}</span></div>
							<div><span class="kt-label">{{ __("Historical decisions") }}</span><span class="kt-meta-value">{{ __("Keep the exact evidence used at the time") }}</span></div>
						</div>
					</div>
					<div class="kt-notice is-warning" style="margin-top:12px">
						<div class="kt-notice-body">{{ __("The replacement will not be usable for affected new decisions until its required details and source checks are complete.") }}</div>
					</div>
				</div>

				<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-sve-error">{{ error }}</p>
			</div>

			<div class="kt-procset-footer kt-procset-wide">
				<span v-if="blocked" class="kt-blocked" data-testid="kt-sve-blocked">{{ blocked }}</span>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-sve-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-sve-save" @click="save">
					{{ correcting ? __("Save changes") : __("Save new version") }}
				</button>
			</div>
		</template>
	</div>
</template>
