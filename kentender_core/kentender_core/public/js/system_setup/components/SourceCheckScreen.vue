<script setup>
// CFG-CHG-002 v0.11 §10.8 (C03-D / CUX-04) — Check sources against one exact
// immutable version, plus the two histories.
//
// The target and version are fixed facts here, never editable: a source check
// is evidence *about* a version, and recording it can never alter the legal
// payload (§4.6). "Sources verified" requires the three evidence groups to be
// complete; the other two outcomes require the unresolved point instead — the
// server enforces both and this states them before the round trip.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { dash, fmtDate } from "../data/format.js";

const props = defineProps({
	name: { type: String, required: true },
	targetDoctype: { type: String, default: "Regulatory Reference" },
});
const emit = defineEmits(["back", "recorded"]);

// §8.1's plain result vocabulary over the model's own outcome values.
const OUTCOMES = [
	{ value: "Pending", label: __("Source check needed") },
	{ value: "Verified", label: __("Sources verified") },
	{ value: "Rejected", label: __("Source check rejected") },
];

const loading = ref(true);
const loadError = ref("");
const version = ref(null);
const versions = ref([]);
const history = ref([]);
const busy = ref(false);
const error = ref("");

const form = ref({
	outcome: "Pending",
	source_check_date: new Date().toISOString().slice(0, 10),
	instrument_edition: "",
	provisions: "",
	source_document: "",
	effective_dates_and_amendments: "",
	applicability_date_basis_explanation: "",
	interpretation_evidence: "",
	unresolved_points: "",
	change_reason: "",
});

async function load() {
	loading.value = true;
	loadError.value = "";
	try {
		version.value = await procurementSettingsApi.getRegulatoryReferenceVersion(props.name);
		form.value.instrument_edition = version.value.source_instrument || "";
		form.value.provisions = version.value.provision || "";
		form.value.source_document = version.value.source_document || "";
		const [allVersions, events] = await Promise.all([
			procurementSettingsApi.listRegulatoryReferenceVersions(version.value.reference_set),
			procurementSettingsApi.listVerificationHistory(props.targetDoctype, props.name),
		]);
		versions.value = allVersions;
		history.value = events;
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

function outcomeLabel(value) {
	return (OUTCOMES.find((option) => option.value === value) || {}).label || value;
}
function outcomeClass(value) {
	if (value === "Verified") return "kt-status is-live";
	if (value === "Rejected") return "kt-status is-critical";
	return "kt-status is-attention";
}

// The same completeness rule the server applies, stated before the submit so
// "Sources verified" is never offered as if it would be accepted.
const missingEvidence = computed(() => {
	if (form.value.outcome !== "Verified") return [];
	return [
		["instrument and edition", form.value.instrument_edition],
		["effective dates and amendments", form.value.effective_dates_and_amendments],
		["applicability and date basis", form.value.applicability_date_basis_explanation],
		["interpretation evidence", form.value.interpretation_evidence],
	]
		.filter(([, value]) => !(value || "").trim())
		.map(([label]) => label);
});
const needsUnresolved = computed(
	() => form.value.outcome !== "Verified" && !form.value.unresolved_points.trim()
);
const canRecord = computed(() => !busy.value && !missingEvidence.value.length && !needsUnresolved.value);

async function record() {
	busy.value = true;
	error.value = "";
	try {
		await procurementSettingsApi.recordReferenceVerification({
			target_doctype: props.targetDoctype,
			target_name: props.name,
			...form.value,
		});
		emit("recorded");
	} catch (e) {
		error.value = e.message;
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div class="kt-procset-view" data-testid="kt-procset-source-check">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title">{{ __("Check sources") }}</h2>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-source-check-back" @click="emit('back')">← {{ __("Procurement settings") }}</button>
		</div>

		<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-source-check-loading">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<div class="kt-skel" style="width:70%" /><div class="kt-skel" style="width:50%" />
		</div>
		<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-source-check-error">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2>{{ __("This record isn't available to you") }}</h2>
			<p>{{ __("It may not exist, or you may not have access to it.") }}</p>
			<button type="button" class="kt-btn kt-btn-secondary" @click="emit('back')">{{ __("Back to Procurement settings") }}</button>
		</div>

		<template v-else>
			<div class="kt-card kt-blueprint kt-procset-wide">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<!-- Fixed target: the check is about this exact version. -->
				<div class="kt-meta-row">
					<div><span class="kt-label">{{ __("Record kind") }}</span><span class="kt-meta-value">{{ __("Procurement rule") }}</span></div>
					<div><span class="kt-label">{{ __("Rule") }}</span><span class="kt-meta-value" data-testid="kt-source-check-rule">{{ version.reference_kind }}</span></div>
					<div><span class="kt-label">{{ __("Version") }}</span><span class="kt-meta-value" data-testid="kt-source-check-version">{{ version.version_number }}</span></div>
				</div>

				<div class="kt-field">
					<label for="kt-sc-result">{{ __("Result") }}</label>
					<select id="kt-sc-result" v-model="form.outcome" class="kt-input" data-testid="kt-sc-result">
						<option v-for="option in OUTCOMES" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-sc-date">{{ __("Source-check date") }}</label>
					<input id="kt-sc-date" v-model="form.source_check_date" class="kt-input" type="date" data-testid="kt-sc-date">
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("1. Source documents") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field"><label for="kt-sc-instrument">{{ __("Instrument and edition") }}</label><input id="kt-sc-instrument" v-model="form.instrument_edition" class="kt-input" data-testid="kt-sc-instrument"></div>
						<div class="kt-field"><label for="kt-sc-provisions">{{ __("Provisions") }}</label><input id="kt-sc-provisions" v-model="form.provisions" class="kt-input" data-testid="kt-sc-provisions"></div>
						<div class="kt-field"><label for="kt-sc-document">{{ __("Source document") }}</label><input id="kt-sc-document" v-model="form.source_document" class="kt-input" :placeholder="__('Not attached')" data-testid="kt-sc-document"></div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("2. What the source establishes") }}</h6>
					<div class="kt-field"><label for="kt-sc-dates">{{ __("Effective dates and amendments") }}</label><input id="kt-sc-dates" v-model="form.effective_dates_and_amendments" class="kt-input" data-testid="kt-sc-dates"></div>
					<div class="kt-field"><label for="kt-sc-applicability">{{ __("Applicability and date basis") }}</label><input id="kt-sc-applicability" v-model="form.applicability_date_basis_explanation" class="kt-input" data-testid="kt-sc-applicability"></div>
					<div class="kt-field">
						<label for="kt-sc-interpretation">{{ __("Interpretation evidence") }}</label>
						<textarea id="kt-sc-interpretation" v-model="form.interpretation_evidence" class="kt-input kt-textarea" rows="2" data-testid="kt-sc-interpretation" />
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("3. Outstanding work and record") }}</h6>
					<div class="kt-field">
						<label for="kt-sc-unresolved">{{ __("Unresolved points") }}</label>
						<textarea id="kt-sc-unresolved" v-model="form.unresolved_points" class="kt-input kt-textarea" rows="2" data-testid="kt-sc-unresolved" />
					</div>
					<div class="kt-field">
						<label for="kt-sc-reason">{{ __("Reason for this entry") }}</label>
						<textarea id="kt-sc-reason" v-model="form.change_reason" class="kt-input kt-textarea" rows="2" data-testid="kt-sc-reason" />
					</div>
				</div>

				<!-- Each outcome states its own consequence before the save. -->
				<div v-if="missingEvidence.length" class="kt-notice is-critical" role="alert" data-testid="kt-sc-evidence-required">
					<div class="kt-notice-body">{{ __("Complete the source, applicability and interpretation evidence before recording a verified source check.") }}</div>
				</div>
				<div v-else-if="needsUnresolved" class="kt-notice is-critical" role="alert" data-testid="kt-sc-unresolved-required">
					<div class="kt-notice-body">{{ __("Record the missing or contradictory point for this outcome.") }}</div>
				</div>
				<div v-else-if="form.outcome === 'Pending'" class="kt-notice is-warning" data-testid="kt-sc-pending-note">
					<div class="kt-notice-body">{{ __("This records outstanding work; it does not verify the rule.") }}</div>
				</div>
				<div v-else-if="form.outcome === 'Rejected'" class="kt-notice is-critical" data-testid="kt-sc-rejected-note">
					<div class="kt-notice-body">{{ __("Affected new decisions are blocked; historical evidence is retained.") }}</div>
				</div>

				<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-sc-error">{{ error }}</p>

				<div class="kt-procset-card-actions">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('back')">{{ __("Cancel") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="!canRecord" data-testid="kt-sc-record" @click="record">{{ __("Record source check") }}</button>
				</div>
			</div>

			<div class="kt-card kt-blueprint kt-table-card kt-procset-wide" data-testid="kt-source-check-history">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h6 class="kt-card-title">{{ __("Version history") }}</h6>
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Version") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Earlier versions replaced") }}</th><th>{{ __("Source check") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in versions" :key="row.reference" :data-testid="'kt-sc-version-' + row.version_number">
							<td>{{ row.version_number }}</td>
							<td>{{ fmtDate(row.effective_from) }}</td>
							<td>{{ fmtDate(row.effective_until) }}</td>
							<td>{{ (row.supersedes_version_ids || []).length ? (row.supersedes_version_ids || []).length : "—" }}</td>
							<td><span :class="row.verification_status === 'Verified' ? 'kt-status is-live' : 'kt-status is-attention'">{{ row.verification_status === "Verified" ? __("Sources verified") : __("Source check needed") }}</span></td>
						</tr>
					</tbody>
				</table>

				<h6 class="kt-card-title" style="margin-top:16px">{{ __("Source-check history") }}</h6>
				<table class="kt-table">
					<thead>
						<tr><th>{{ __("Result") }}</th><th>{{ __("Source-check date") }}</th><th>{{ __("Recorded by") }}</th><th>{{ __("Evidence") }}</th><th>{{ __("Reason") }}</th></tr>
					</thead>
					<tbody>
						<tr v-for="(row, index) in history" :key="index" data-testid="kt-sc-history-row">
							<td><span :class="outcomeClass(row.outcome)">{{ outcomeLabel(row.outcome) }}</span></td>
							<td>{{ fmtDate(row.source_check_date) }}</td>
							<td>{{ dash(row.recorded_by) }}</td>
							<td>{{ row.outcome === "Verified" ? __("Complete") : __("Incomplete") }}</td>
							<td>{{ dash(row.change_reason || row.unresolved_points) }}</td>
						</tr>
						<tr v-if="!history.length"><td colspan="5" class="kt-muted">{{ __("No source check has been recorded yet.") }}</td></tr>
					</tbody>
				</table>
			</div>
		</template>
	</div>
</template>
