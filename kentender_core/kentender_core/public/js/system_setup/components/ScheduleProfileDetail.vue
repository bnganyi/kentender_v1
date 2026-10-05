<template>
	<div class="kt-schedule" data-testid="kt-procset-profile">
		<div v-if="loading" data-testid="kt-procset-profile-loading">
			<div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" />
		</div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-procset-profile-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This record isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>

		<div v-else data-testid="kt-procset-profile-table">
			<!-- The schedule's own facts, each separately labelled (§10.9). -->
			<div class="kt-meta-row" style="margin-bottom:14px">
				<div><span class="kt-label">{{ __("Name") }}</span><span class="kt-meta-value" data-testid="kt-procset-profile-title">{{ profile.profile_name }}</span></div>
				<div><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span><span class="kt-meta-value">{{ applicabilityBasisLabel(profile.applicability_basis) || __("Not yet established") }}</span></div>
				<div><span class="kt-label">{{ __("Method") }}</span><span class="kt-meta-value">{{ profile.procurement_method }}</span></div>
				<div><span class="kt-label">{{ __("Procedure") }}</span><span class="kt-meta-value">{{ profile.procedure || "—" }}</span></div>
				<div><span class="kt-label">{{ __("Category") }}</span><span class="kt-meta-value">{{ profile.procurement_category }}</span></div>
				<div><span class="kt-label">{{ __("Version") }}</span><span class="kt-meta-value" data-testid="kt-procset-profile-version">{{ profile.version_number }}</span></div>
				<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ fmtDate(profile.effective_from) }}</span></div>
				<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ fmtDate(profile.effective_until) }}</span></div>
				<div><span class="kt-label">{{ __("Source check") }}</span><span class="kt-meta-value"><span :class="sourceCheckClass(profile.verification_status)">{{ __(sourceCheckLabel(profile.verification_status)) }}</span></span></div>
			</div>

			<h6 class="kt-card-title">{{ __("Milestones") }}</h6>
			<table class="table" style="margin-bottom:16px">
				<thead><tr><th>{{ __("Milestone") }}</th><th>{{ __("Order") }}</th><th>{{ __("Applies") }}</th><th>{{ __("Role in this schedule") }}</th></tr></thead>
				<tbody>
					<tr v-for="row in profile.milestones" :key="row.milestone" :data-testid="'kt-procset-milestone-' + row.milestone">
						<td>{{ row.label }}</td>
						<td>{{ row.sequence }}</td>
						<td>{{ row.applies ? __("Yes") : __("No") }}</td>
						<td>{{ milestoneRole(row) }}</td>
					</tr>
				</tbody>
			</table>

			<h6 class="kt-card-title">{{ __("Time intervals") }}</h6>
			<div class="kt-table-scroll">
				<table class="table" data-testid="kt-procset-profile-intervals">
					<thead><tr><th>{{ __("From") }}</th><th>{{ __("To") }}</th><th>{{ __("Days counted") }}</th><th>{{ __("Minimum status") }}</th><th>{{ __("Minimum days") }}</th><th>{{ __("Maximum status") }}</th><th>{{ __("Maximum days") }}</th><th>{{ __("Default days") }}</th><th>{{ __("Default basis") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in intervals" :key="row.to.milestone" :data-testid="'kt-procset-interval-' + row.to.milestone">
							<td>{{ row.from.label }}</td>
							<td>{{ row.to.label }}</td>
							<td>{{ row.to.counting_rule }}</td>
							<td>{{ boundStatus(row.to.minimum_days) }}</td>
							<td>{{ fmtDays(row.to.minimum_days) }}</td>
							<td>{{ boundStatus(row.to.maximum_days) }}</td>
							<td>{{ fmtDays(row.to.maximum_days) }}</td>
							<td>{{ fmtDays(row.to.default_days) }}</td>
							<td>{{ basisLabel(row.to) }}</td>
						</tr>
						<tr v-if="!intervals.length"><td colspan="9" class="text-muted">{{ __("No time intervals are defined for this schedule.") }}</td></tr>
					</tbody>
				</table>
			</div>
			<div class="kt-meta-row" style="margin-top:12px">
				<div><span class="kt-label">{{ __("Estimated delivery period default") }}</span><span class="kt-meta-value" data-testid="kt-procset-profile-delivery-default">{{ profile.estimated_delivery_period_default_days === null ? __("Not set") : __("{0} calendar days", [profile.estimated_delivery_period_default_days]) }}</span></div>
			</div>

			<!-- C04 #calendar card 1 — the working-days variant. -->
			<div v-if="workingDays" class="kt-schedule-calendar" data-testid="kt-procset-profile-calendar">
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Days counted") }}</span><span class="kt-meta-value">{{ __("Working days") }}</span></div>
					<div><span class="kt-label">{{ __("Working-day calendar") }}</span><span class="kt-meta-value">{{ profile.calendar ? profile.calendar.calendar_name : "—" }}</span></div>
				</div>
				<div v-if="!profile.calendar" class="kt-notice is-critical" style="margin-top:6px" data-testid="kt-procset-profile-calendar-missing">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ __("Select a verified working-day calendar for this interval.") }}</div>
				</div>
				<a v-else href="#" data-testid="kt-procset-profile-view-calendar" @click.prevent="emit('view-calendar', profile.calendar.calendar)">{{ __("View calendar") }}</a>
			</div>

			<div v-if="detailsToComplete.length" style="margin-top:12px" data-testid="kt-procset-profile-details">
				<div style="font-weight:600;font-size:13px;margin-bottom:4px">{{ __("Details to complete") }}</div>
				<ul style="margin:0;padding-left:18px;font-size:13px"><li v-for="item in detailsToComplete" :key="item">{{ item }}</li></ul>
			</div>
			<!-- Both sentences are the owner.s 23 Sep wording (D20): incomplete,
			     then complete but not marked valid. -->
			<div v-if="!profile.complete" class="kt-notice is-warning" style="margin-top:12px" data-testid="kt-procset-profile-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ __("This schedule is missing periods, so it cannot be used to plan dates. Edit it to fill them in.") }}</div>
			</div>
			<div v-else-if="!valid" class="kt-notice is-warning" style="margin-top:12px" data-testid="kt-procset-profile-validity-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ __("This schedule is not marked valid, so a plan using it cannot be submitted.") }}</div>
			</div>

			<!-- §10.9 names two more groups the board leaves out (DEPARTURES). -->
			<div class="kt-section" style="margin-top:16px" data-testid="kt-procset-profile-sources">
				<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
				<div class="kt-panel"><div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Source instrument") }}</span><span class="kt-meta-value">{{ profile.source_instrument || __("Not yet established") }}</span></div>
					<div><span class="kt-label">{{ __("Provisions") }}</span><span class="kt-meta-value">{{ profile.provision || __("Not yet established") }}</span></div>
					<div><span class="kt-label">{{ __("Source document") }}</span><span class="kt-meta-value"><a v-if="profile.source_document" :href="profile.source_document" target="_blank" rel="noopener">{{ __("View document") }}</a><template v-else>{{ __("Not attached") }}</template></span></div>
					<div v-if="profile.change_reason"><span class="kt-label">{{ __("Reason for this version") }}</span><span class="kt-meta-value" data-testid="kt-procset-profile-change-reason">{{ profile.change_reason }}</span></div>
				</div></div>
			</div>
			<div class="kt-section" data-testid="kt-procset-profile-usage">
				<h6 class="kt-card-title">{{ __("Usage and history") }}</h6>
				<div class="kt-panel"><span class="kt-meta-value">{{ __("Which decisions used this version is not recorded yet.") }}</span></div>
			</div>

			<div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap">
				<!-- D15: correctable in place while nothing depends on it. -->
				<button v-if="profile.can_edit" type="button" class="btn btn-secondary" data-testid="kt-procset-profile-edit" @click="emit('edit-schedule')">{{ __("Edit schedule") }}</button>
				<button type="button" class="btn btn-secondary" data-testid="kt-procset-profile-new-version" @click="emit('new-version')">{{ __("Create new version") }}</button>
				<!-- D20: a schedule's validity is the administrator's own statement. -->
				<button v-if="canSetValidity" type="button" class="btn btn-secondary" :disabled="validityBusy" data-testid="kt-procset-profile-validity" @click="setValidity(!valid)">{{ valid ? __("Remove valid mark") : __("Mark as valid") }}</button>
			</div>
			<div v-if="validityError" class="kt-notice is-critical" role="alert" style="margin-top:12px" data-testid="kt-procset-profile-validity-error">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
				<div class="kt-notice-body">{{ validityError }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>
// CFG-CHG-002 v0.14 §10.9 (C04 #detail; tracker CFG14-5F) — ported from the
// board. The model's values map onto the board's columns without invention:
// a bound is "Value specified" when its days are set, else "Not yet
// established"; a statutory default reads "Legal requirement". The board's
// selected-interval editor belongs to the schedule editor, because a saved
// version is read-only (see DEPARTURES).
//
// C04 — one procedure schedule profile Version, read-only: the applicable
// milestones in order, counting rule, statutory bounds (blank = verification
// required), defaults with their basis, the delivery-period default and the
// completeness notice. It is read-only: a schedule that could already
// matter to someone is changed by a new Version, and one that could not
// is corrected in its own editor. Which action is offered is the
// server's call, not this screen's.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, fmtDate, fmtDays, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["back", "registered", "new-version", "edit-schedule", "view-calendar"]);

const loading = ref(true);
const loadError = ref("");
const profile = ref(null);

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		profile.value = await procurementSettingsApi.getScheduleProfile(props.name);
	} catch (error) {
		loadError.value = error.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

// Whether an administrator has said this version is valid — the one fact that
// governs whether a plan using it can be submitted.
const valid = computed(() => !!profile.value?.valid || profile.value?.verification_status === "Verified");
const canSetValidity = computed(() => !!profile.value?.can_set_validity);

const validityBusy = ref(false);
const validityError = ref("");

async function setValidity(next) {
	validityBusy.value = true;
	validityError.value = "";
	try {
		await procurementSettingsApi.setVersionValidity({
			doctype: "Procedure Schedule Profile",
			name: props.name,
			valid: next,
		});
		await load();
	} catch (error) {
		validityError.value = error.message;
	} finally {
		validityBusy.value = false;
	}
}

// §10.9 default basis vocabulary: Legal requirement / Planning assumption.
function basisLabel(row) {
	if (row.basis === "Statutory") return __("Legal requirement");
	if (row.basis === "Planning assumption") return __("Planning assumption");
	if (row.basis === "Source-derived") return __("Source-derived");
	return __("Not yet established");
}
const boundStatus = (days) => (days === null || days === undefined ? __("Not yet established") : __("Value specified"));

// "Details to complete", by the labels the screen shows (the server's gaps).
const detailsToComplete = computed(() =>
	(profile.value?.gaps || []).map((gap) => {
		if (gap === "working_day_calendar") return __("Working-day calendar");
		const row = (profile.value?.milestones || []).find((m) => m.milestone === gap);
		return __("Default days — {0}", [row ? row.label : gap]);
	})
);
const workingDays = computed(() => profile.value?.counting_rule === "Working days");

// §10.9 — the first applying milestone starts the schedule; the last is
// reached from the item's own delivery period; the rest are calculated from
// the interval that closes at them.
function milestoneRole(row) {
	if (!row.applies) return __("Not used in this schedule");
	const applying = (profile.value?.milestones || []).filter((m) => m.applies);
	if (applying.length && applying[0].milestone === row.milestone) return __("Starting date");
	if (row.milestone === "delivery_completion") return __("Source requirement boundary");
	return __("Calculated milestone");
}

// An interval runs from the previous applying milestone to this one, and the
// period that closes at this one is the number of days it counts.
const intervals = computed(() => {
	const applying = (profile.value?.milestones || []).filter((m) => m.applies);
	const rows = [];
	for (let index = 1; index < applying.length; index += 1) {
		rows.push({ from: applying[index - 1], to: applying[index] });
	}
	return rows;
});
</script>
