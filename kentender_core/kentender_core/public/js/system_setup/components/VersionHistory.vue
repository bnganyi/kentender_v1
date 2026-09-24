<script setup>
// CFG-CHG-002 v0.14 §10.8/§10.9 (C03D #history, C04 #calendar-history;
// tracker CFG14-5E/5F) — the three history tables every versioned setting
// shows: its versions, its source checks, its usage. Shared by Check sources
// and a calendar's usage and history view.
import { dash, fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	// Each: { id, version_number, effective_from, effective_until, recorded_at,
	// recorded_by, supersedes_version_ids, verification_status }.
	versions: { type: Array, default: () => [] },
	checks: { type: Array, default: () => [] },
});
const emit = defineEmits(["view-version"]);

const OUTCOMES = { Pending: "Source check needed", Verified: "Sources verified", Rejected: "Source check rejected" };
function outcomeClass(value) {
	if (value === "Verified") return "kt-status is-live";
	if (value === "Rejected") return "kt-status is-critical";
	return "kt-status is-attention";
}
// "Earlier versions replaced": the version numbers, not a count.
function replacedLabel(row) {
	const ids = row.supersedes_version_ids || [];
	if (!ids.length) return "—";
	const numbers = ids.map((id) => (props.versions.find((v) => v.id === id) || {}).version_number).filter(Boolean);
	return numbers.length ? numbers.map((n) => __("Version {0}", [n])).join(", ") : String(ids.length);
}
</script>

<template>
	<div class="kt-sc-history" data-testid="kt-source-check-history">
		<div>
			<h6 class="kt-card-title">{{ __("Version history") }}</h6>
			<div class="kt-table-scroll">
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Version") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Recorded at") }}</th><th>{{ __("Recorded by") }}</th><th>{{ __("Earlier versions replaced") }}</th><th>{{ __("Source check") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in versions" :key="row.id" :data-testid="'kt-sc-version-' + row.version_number">
							<td>{{ row.version_number }}</td>
							<td>{{ row.effective_from ? fmtDate(row.effective_from) : __("Not yet established") }}</td>
							<td>{{ row.effective_until ? fmtDate(row.effective_until) : __("Not yet established") }}</td>
							<td>{{ fmtDate(row.recorded_at) }}</td>
							<td>{{ dash(row.recorded_by) }}</td>
							<td>{{ replacedLabel(row) }}</td>
							<td><span :class="sourceCheckClass(row.verification_status)">{{ __(sourceCheckLabel(row.verification_status)) }}</span></td>
							<td><a href="#" :data-testid="'kt-sc-version-view-' + row.version_number" @click.prevent="emit('view-version', row.id)">{{ __("View") }}</a></td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		<div>
			<h6 class="kt-card-title">{{ __("Source-check history") }}</h6>
			<div class="kt-table-scroll">
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Result") }}</th><th>{{ __("Source-check date") }}</th><th>{{ __("Recorded at") }}</th><th>{{ __("Recorded by") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Reason") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in checks" :key="row.event" data-testid="kt-sc-history-row">
							<td><span :class="outcomeClass(row.outcome)">{{ __(OUTCOMES[row.outcome] || row.outcome) }}</span></td>
							<td>{{ fmtDate(row.source_check_date) }}</td>
							<td>{{ fmtDate(row.recorded_at) }}</td>
							<td>{{ dash(row.recorded_by) }}</td>
							<td>{{ row.evidence_complete ? __("Complete") : __("Incomplete") }}</td>
							<td>{{ dash(row.change_reason || row.unresolved_points) }}</td>
						</tr>
						<tr v-if="!checks.length"><td colspan="6" class="text-muted">{{ __("No source check has been recorded yet.") }}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
		<div>
			<h6 class="kt-card-title">{{ __("Usage") }}</h6>
			<div class="kt-table-scroll">
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Consumer") }}</th><th>{{ __("Record reference") }}</th><th>{{ __("Exact version") }}</th><th>{{ __("Decision date") }}</th><th>{{ __("Action") }}</th></tr>
					</thead>
					<tbody>
						<!-- Nothing records which decisions used a version yet (FU-15). -->
						<tr><td colspan="5" class="text-muted" data-testid="kt-sc-usage-none">{{ __("Which decisions used this version is not recorded yet.") }}</td></tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>
