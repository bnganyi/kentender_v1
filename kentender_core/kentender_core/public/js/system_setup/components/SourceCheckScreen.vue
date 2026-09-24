<script setup>
// CFG-CHG-002 v0.14 §10.8 (C03D #pending/#verified/#rejected/#history;
// tracker CFG14-5E) — Check sources against one exact immutable version,
// plus the version, source-check and usage histories, ported from the board.
// The board draws the three evidence groups as fact panels; the spec calls
// them blank inputs, so each panel holds fields (see DEPARTURES). A second
// check recorded meanwhile is caught by the event this form was opened on.
//
// The target and version are fixed facts here, never editable: a source check
// is evidence *about* a version, and recording it can never alter the legal
// payload (§4.6). "Sources verified" requires the three evidence groups to be
// complete; the other two outcomes require the unresolved point instead — the
// server enforces both and this states them before the round trip.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { dash, fmtDate, sourceCheckClass, sourceCheckLabel } from "../data/format.js";
import RuleFormError from "./RuleFormError.vue";

const props = defineProps({
	name: { type: String, required: true },
	targetDoctype: { type: String, default: "Regulatory Reference" },
});
const emit = defineEmits(["back", "recorded", "view-version"]);

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
const priorEvent = ref("");
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
	if (!version.value) loading.value = true;
	loadError.value = "";
	try {
		const first = !version.value;
		version.value = await procurementSettingsApi.getRegulatoryReferenceVersion(props.name);
		// Prefilled once from the version; a re-read after a stale save keeps
		// what was typed for review.
		if (first) {
			form.value.instrument_edition = version.value.source_instrument || "";
			form.value.provisions = version.value.provision || "";
			form.value.source_document = version.value.source_document || "";
		}
		const [allVersions, events] = await Promise.all([
			procurementSettingsApi.listRegulatoryReferenceVersions(version.value.reference_set),
			procurementSettingsApi.listVerificationHistory(props.targetDoctype, props.name),
		]);
		versions.value = allVersions;
		history.value = events;
		// The latest check this form was opened on; recording against a
		// different one means someone else recorded meanwhile (stale).
		priorEvent.value = events[0]?.event || "";
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
// §10.8 "errors at the missing controls": each missing evidence field says so.
const invalid = (field) => form.value.outcome === "Verified" && !(form.value[field] || "").trim();

async function record() {
	busy.value = true;
	error.value = "";
	try {
		await procurementSettingsApi.recordReferenceVerification({
			target_doctype: props.targetDoctype,
			target_name: props.name,
			...form.value,
			expected_prior_event: priorEvent.value,
		});
		emit("recorded");
	} catch (e) {
		error.value = e.message;
	} finally {
		busy.value = false;
	}
}

// "Earlier versions replaced": the version numbers, not a count.
function replacedLabel(row) {
	const ids = row.supersedes_version_ids || [];
	if (!ids.length) return "—";
	const numbers = ids.map((id) => (versions.value.find((v) => v.reference === id) || {}).version_number).filter(Boolean);
	return numbers.length ? numbers.map((n) => __("Version {0}", [n])).join(", ") : String(ids.length);
}
</script>

<template>
	<div class="kt-source-check" data-testid="kt-procset-source-check">
		<div v-if="loading" data-testid="kt-source-check-loading">
			<div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" />
		</div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-source-check-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This record isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>

		<template v-else>
			<!-- C03D #pending — the form. -->
			<div data-testid="kt-source-check-form">
				<h3>{{ __("Check sources") }}</h3>
				<!-- Fixed target: the check is about this exact version. -->
				<div class="kt-meta-row" style="margin-bottom:14px">
					<div><span class="kt-label">{{ __("Record kind") }}</span><span class="kt-meta-value">{{ __("Procurement rule") }}</span></div>
					<div><span class="kt-label">{{ __("Rule") }}</span><span class="kt-meta-value" data-testid="kt-source-check-rule">{{ version.display_name || version.reference_kind }}</span></div>
					<div><span class="kt-label">{{ __("Version") }}</span><span class="kt-meta-value" data-testid="kt-source-check-version">{{ version.version_number }}</span></div>
				</div>
				<div class="kt-field">
					<label for="kt-sc-result">{{ __("Result") }}</label>
					<select id="kt-sc-result" v-model="form.outcome" class="kt-input" data-testid="kt-sc-result">
						<option v-for="option in OUTCOMES" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field" style="margin-top:10px">
					<label for="kt-sc-date">{{ __("Source-check date") }}</label>
					<input id="kt-sc-date" v-model="form.source_check_date" class="kt-input" type="date" data-testid="kt-sc-date">
				</div>

				<h6 class="kt-card-title" style="margin-top:16px">{{ __("1. Source documents") }}</h6>
				<div class="kt-panel" style="margin-bottom:10px">
					<div class="kt-sc-grid">
						<div class="kt-field"><label for="kt-sc-instrument">{{ __("Instrument and edition") }}</label><input id="kt-sc-instrument" v-model="form.instrument_edition" class="kt-input" :aria-invalid="invalid('instrument_edition') ? 'true' : 'false'" data-testid="kt-sc-instrument"></div>
						<div class="kt-field"><label for="kt-sc-provisions">{{ __("Provisions") }}</label><input id="kt-sc-provisions" v-model="form.provisions" class="kt-input" data-testid="kt-sc-provisions"></div>
						<div class="kt-field"><label for="kt-sc-document">{{ __("Source document") }}</label><input id="kt-sc-document" v-model="form.source_document" class="kt-input" :placeholder="__('Not attached')" data-testid="kt-sc-document"></div>
					</div>
				</div>
				<h6 class="kt-card-title">{{ __("2. What the source establishes") }}</h6>
				<div class="kt-panel" style="margin-bottom:10px">
					<div class="kt-sc-grid">
						<div class="kt-field"><label for="kt-sc-dates">{{ __("Effective dates and amendments") }}</label><input id="kt-sc-dates" v-model="form.effective_dates_and_amendments" class="kt-input" :aria-invalid="invalid('effective_dates_and_amendments') ? 'true' : 'false'" data-testid="kt-sc-dates"></div>
						<div class="kt-field"><label for="kt-sc-applicability">{{ __("Applicability and date basis") }}</label><input id="kt-sc-applicability" v-model="form.applicability_date_basis_explanation" class="kt-input" :aria-invalid="invalid('applicability_date_basis_explanation') ? 'true' : 'false'" data-testid="kt-sc-applicability"></div>
						<div class="kt-field"><label for="kt-sc-interpretation">{{ __("Interpretation evidence") }}</label><textarea id="kt-sc-interpretation" v-model="form.interpretation_evidence" class="kt-input" rows="2" :aria-invalid="invalid('interpretation_evidence') ? 'true' : 'false'" data-testid="kt-sc-interpretation" /></div>
					</div>
				</div>
				<h6 class="kt-card-title">{{ __("3. Outstanding work and record") }}</h6>
				<div class="kt-panel">
					<div class="kt-sc-grid">
						<div class="kt-field"><label for="kt-sc-unresolved">{{ __("Unresolved points") }}</label><textarea id="kt-sc-unresolved" v-model="form.unresolved_points" class="kt-input" rows="2" :aria-invalid="needsUnresolved ? 'true' : 'false'" data-testid="kt-sc-unresolved" /></div>
						<div class="kt-field"><label for="kt-sc-reason">{{ form.outcome === "Rejected" ? __("Reason") : __("Reason for this entry") }}</label><textarea id="kt-sc-reason" v-model="form.change_reason" class="kt-input" rows="2" data-testid="kt-sc-reason" /></div>
					</div>
				</div>

				<!-- Each outcome states its own consequence before the save
				     (C03D #pending, #verified, #rejected). -->
				<div v-if="missingEvidence.length" class="kt-notice is-critical" role="alert" style="margin-top:10px" data-testid="kt-sc-evidence-required">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ __("Complete the source, applicability and interpretation evidence before recording a verified source check.") }}</div>
				</div>
				<div v-else-if="needsUnresolved" class="kt-notice is-critical" role="alert" style="margin-top:10px" data-testid="kt-sc-unresolved-required">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ __("Record the missing or contradictory point for this outcome.") }}</div>
				</div>
				<div v-else-if="form.outcome === 'Pending'" class="kt-notice is-warning" style="margin-top:10px" data-testid="kt-sc-pending-note">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
					<div class="kt-notice-body">{{ __("This records outstanding work; it does not verify the rule.") }}</div>
				</div>
				<div v-else-if="form.outcome === 'Rejected'" class="kt-notice is-critical" style="margin-top:10px" data-testid="kt-sc-rejected-note">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
					<div class="kt-notice-body">{{ __("Affected new decisions are blocked; historical evidence is retained.") }}</div>
				</div>

				<RuleFormError :error="error" style="margin-top:10px" @refresh="load" />

				<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
					<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-sc-cancel" @click="emit('back')">{{ __("Cancel") }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="!canRecord" data-testid="kt-sc-record" @click="record">{{ __("Record source check") }}</button>
				</div>
			</div>

			<!-- C03D #history — version, source-check and usage histories. -->
			<div class="kt-sc-history" data-testid="kt-source-check-history">
				<div>
					<h6 class="kt-card-title">{{ __("Version history") }}</h6>
					<div class="kt-table-scroll">
						<table class="kt-table">
							<thead>
								<tr><th>{{ __("Version") }}</th><th>{{ __("Applies from") }}</th><th>{{ __("Applies until") }}</th><th>{{ __("Recorded at") }}</th><th>{{ __("Recorded by") }}</th><th>{{ __("Earlier versions replaced") }}</th><th>{{ __("Source check") }}</th><th>{{ __("Action") }}</th></tr>
							</thead>
							<tbody>
								<tr v-for="row in versions" :key="row.reference" :data-testid="'kt-sc-version-' + row.version_number">
									<td>{{ row.version_number }}</td>
									<td>{{ fmtDate(row.effective_from) }}</td>
									<td>{{ fmtDate(row.effective_until) }}</td>
									<td>{{ fmtDate(row.recorded_at) }}</td>
									<td>{{ dash(row.recorded_by) }}</td>
									<td>{{ replacedLabel(row) }}</td>
									<td><span :class="sourceCheckClass(row.verification_status)">{{ __(sourceCheckLabel(row.verification_status)) }}</span></td>
									<td><a href="#" :data-testid="'kt-sc-version-view-' + row.version_number" @click.prevent="emit('view-version', row.reference)">{{ __("View") }}</a></td>
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
								<tr v-for="row in history" :key="row.event" data-testid="kt-sc-history-row">
									<td><span :class="outcomeClass(row.outcome)">{{ outcomeLabel(row.outcome) }}</span></td>
									<td>{{ fmtDate(row.source_check_date) }}</td>
									<td>{{ fmtDate(row.recorded_at) }}</td>
									<td>{{ dash(row.recorded_by) }}</td>
									<td>{{ row.evidence_complete ? __("Complete") : __("Incomplete") }}</td>
									<td>{{ dash(row.change_reason || row.unresolved_points) }}</td>
								</tr>
								<tr v-if="!history.length"><td colspan="6" class="text-muted">{{ __("No source check has been recorded yet.") }}</td></tr>
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
	</div>
</template>
