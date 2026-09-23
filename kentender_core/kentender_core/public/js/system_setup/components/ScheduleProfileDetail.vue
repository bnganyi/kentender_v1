<script setup>
// C04 — one procedure schedule profile Version, read-only: the applicable
// milestones in order, counting rule, statutory bounds (blank = verification
// required), defaults with their basis, the delivery-period default and the
// completeness notice. It is read-only: a schedule that could already
// matter to someone is changed by a new Version, and one that could not
// is corrected in its own editor. Which action is offered is the
// server's call, not this screen's.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, fmtDate, fmtDays } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["back", "registered", "new-version", "edit-schedule"]);

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

function basisCell(row) {
	if (row.basis === "Planning assumption") return { kind: "tag", text: __("Planning assumption") };
	if (row.basis === "Source-derived") return { kind: "tag", text: __("Source-derived") };
	if (profile.value?.verification_status === "Verified") return { kind: "live", text: __("Statutory") };
	return { kind: "attention", text: __("Verification required") };
}

// §10.9 — the first applying milestone starts the schedule; the last is
// reached from the item's own delivery period; the rest are calculated from
// the interval that closes at them.
function milestoneRole(row) {
	if (!row.applies) return __("Not used in this schedule");
	const applying = (profile.value?.milestones || []).filter((m) => m.applies);
	if (applying.length && applying[0].milestone === row.milestone) return __("Starting date");
	if (row.milestone === "delivery_completion") return __("From the estimated delivery period");
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

<template>
	<div class="kt-procset-view" data-testid="kt-procset-profile">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Schedule profile") }}</span>
				<!-- The title sits above the loading/error branches, so it has to
				     stand on its own when the schedule could not be read at all:
				     dereferencing it there threw and took the whole panel down,
				     leaving a blank screen instead of the not-available state. -->
				<h2 class="kt-section-title" data-testid="kt-procset-profile-title">
					{{ loading ? __("Loading…") : profile ? profile.profile_name : __("Procurement schedule") }}
				</h2>
				<!-- §10.9 — the schedule's own facts, in the artboard's order and
				     vocabulary: the name it is known by, then the date basis that
				     decides which version applies. -->
				<div v-if="!loading && profile" class="kt-procset-meta">
					<span><span class="kt-label">{{ __("Name") }}</span> {{ profile.profile_name }}</span>
					<span><span class="kt-label">{{ __("Which date determines the rule to use?") }}</span> {{ applicabilityBasisLabel(profile.applicability_basis) || __("Not yet established") }}</span>
					<span><span class="kt-label">{{ __("Method") }}</span> {{ profile.procurement_method }}</span>
					<span><span class="kt-label">{{ __("Procedure") }}</span> {{ profile.procedure || "—" }}</span>
					<span><span class="kt-label">{{ __("Version") }}</span> {{ profile.version_number }}</span>
					<span><span class="kt-label">{{ __("Applies") }}</span> {{ fmtDate(profile.effective_from) }} – {{ fmtDate(profile.effective_until) }}</span>
				</div>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-procset-profile-back" @click="emit('back')">← {{ __("Procurement settings") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-procset-profile-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:50%" />
		</div>
		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-procset-profile-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("This record isn't available to you") }}</h2>
			<p>{{ __("It may not exist, or you may not have access to it.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="emit('back')">{{ __("Back to Procurement settings") }}</button>
		</div>

		<template v-else>
			<!-- §10.9 — the artboard separates what the milestones ARE from the
			     intervals BETWEEN them: the first table is the sequence and each
			     milestone's role, the second is the period each one closes. One
			     combined table conflated the two. -->
			<div class="kt-card kt-blueprint kt-table-card" data-testid="kt-procset-profile-table">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h6 class="kt-card-title">{{ __("Milestones") }}</h6>
				<table class="kt-table" style="margin-bottom:16px">
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
				<table class="kt-table" data-testid="kt-procset-profile-intervals">
					<thead><tr><th>{{ __("From") }}</th><th>{{ __("To") }}</th><th>{{ __("Days counted") }}</th><th>{{ __("Minimum status") }}</th><th>{{ __("Maximum status") }}</th><th>{{ __("Default days") }}</th><th>{{ __("Default basis") }}</th></tr></thead>
					<tbody>
						<tr v-for="row in intervals" :key="row.to.milestone" :data-testid="'kt-procset-interval-' + row.to.milestone">
							<td>{{ row.from.label }}</td>
							<td>{{ row.to.label }}</td>
							<td>{{ row.to.counting_rule }}</td>
							<td>{{ fmtDays(row.to.minimum_days) }}</td>
							<td>{{ fmtDays(row.to.maximum_days) }}</td>
							<td>{{ fmtDays(row.to.default_days) }}</td>
							<td>
								<span v-if="basisCell(row.to).kind === 'tag'" class="kt-tag kt-tag-neutral">{{ basisCell(row.to).text }}</span>
								<span v-else-if="basisCell(row.to).kind === 'live'" class="kt-status is-live">{{ basisCell(row.to).text }}</span>
								<span v-else class="kt-status is-attention">{{ basisCell(row.to).text }}</span>
							</td>
						</tr>
						<tr v-if="!intervals.length"><td colspan="7" class="kt-muted">{{ __("No time intervals are defined for this schedule.") }}</td></tr>
					</tbody>
				</table>
			</div>
			<div class="kt-fact kt-procset-fact"><span class="kt-label">{{ __("Estimated delivery period default") }}</span><span class="kt-fact-val" data-testid="kt-procset-profile-delivery-default">{{ profile.estimated_delivery_period_default_days === null ? __("Not set") : __("{0} calendar days", [profile.estimated_delivery_period_default_days]) }}</span></div>
			<!-- Two different facts, said separately, each with something to do
			     about it — rather than one sentence blaming "rules and sources"
			     that named neither. -->
			<div v-if="!profile.complete" class="kt-card kt-blueprint kt-procset-attention kt-procset-narrow" data-testid="kt-procset-profile-notice">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<p class="kt-card-body">{{ __("This schedule is missing periods, so it cannot be used to plan dates. Edit it to fill them in.") }}</p>
			</div>
			<div v-else-if="!valid" class="kt-card kt-blueprint kt-procset-attention kt-procset-narrow" data-testid="kt-procset-profile-validity-notice">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<p class="kt-card-body">{{ __("This schedule is not marked valid, so a plan using it cannot be submitted.") }}</p>
			</div>
			<div class="kt-procset-card-actions">
				<button
					v-if="profile.can_edit"
					type="button"
					class="kt-btn kt-btn-secondary"
					data-testid="kt-procset-profile-edit"
					@click="emit('edit-schedule')"
				>
					{{ __("Edit schedule") }}
				</button>
				<button
					v-if="canSetValidity"
					type="button"
					class="kt-btn kt-btn-secondary"
					:disabled="validityBusy"
					data-testid="kt-procset-profile-validity"
					@click="setValidity(!valid)"
				>
					{{ valid ? __("Remove valid mark") : __("Mark as valid") }}
				</button>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-procset-profile-new-version" @click="emit('new-version')">{{ __("Create new version") }}</button>
			</div>
			<p v-if="validityError" class="kt-inline-error" role="alert" data-testid="kt-procset-profile-validity-error">{{ validityError }}</p>

		</template>
	</div>
</template>
