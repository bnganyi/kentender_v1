<script setup>
// CFG-CHG-002 v0.11 §10.6/§10.7 (C03-B "add", C03-C kind editors, C03-B
// "version") — one form for every rule kind: the shared shell (identity,
// when it applies, sources) plus the kind's own validated field group.
//
// §7.3's creation is two commands, and the recovery matters: if the set is
// created and the version save then fails, the set exists with no version
// and the administrator's entries must survive so they can finish. That is
// exactly what `setCreated` tracks — a retry reuses the set instead of
// creating a second one.
//
// Method eligibility is owned by `Procedure Method Profile` (plan D10), so
// this editor states that rather than offering a second, divergent form for
// the same rule.
import { computed, ref, watch } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, fmtDate } from "../data/format.js";

const props = defineProps({
	// Creating a rule: no set yet. Creating a new version: the set and its
	// current version, whose values seed the form (§11.6 — correction copies
	// the current rule, never edits it in place).
	referenceSet: { type: String, default: "" },
	currentVersion: { type: Object, default: null },
	kinds: { type: Array, default: () => [] },
	entityTypes: { type: Array, default: () => [] },
	categories: { type: Array, default: () => [] },
	methods: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel"]);

const creating = computed(() => !props.referenceSet);

const APPLICABILITY_BASES = [
	"FiscalYearStart",
	"PlanSubmissionDate",
	"PlanApprovalDate",
	"ProceedingAuthorizationDate",
	"InvitationDate",
	"ContractSigningDate",
];
const COUNTY_APPLICABILITY = [
	{ value: "All", label: __("All") },
	{ value: "County", label: __("County") },
	{ value: "NonCounty", label: __("Non-county") },
];
const COMPARATORS = ["Equal", "NotEqual", "In", "NotIn", "LessThan", "LessThanOrEqual", "GreaterThan", "GreaterThanOrEqual"];
const DUE_RULES = [
	{ value: "Immediate", label: __("Immediately") },
	{ value: "CalendarDaysAfter", label: __("Calendar days after the trigger") },
	{ value: "WorkingDaysAfter", label: __("Working days after the trigger") },
	{ value: "PeriodEndPlusDays", label: __("Days after the reporting period ends") },
];
const DENOMINATOR_BASES = [
	{ value: "AnnualProcurementBudget", label: __("Annual procurement budget") },
	{ value: "AnnualProcurementValue", label: __("Annual procurement value") },
];
const OVERLAP_POLICIES = [
	{ value: "Independent", label: __("Targets apply independently") },
	{ value: "MutuallyExclusive", label: __("Targets are mutually exclusive") },
	{ value: "SpecifiedOverlap", label: __("Specified overlap") },
];
const APPROVAL_ROUTES = ["Cabinet Secretary", "County Executive Committee Member", "Board of Directors", "Council"];

const current = computed(() => props.currentVersion || {});
// "Method eligibility" is maintained as a Procedure Method Profile (D10);
// this form only shows a redirect notice for it (`delegated` below), never a
// savable form. Defaulting a new rule to it silently traps an administrator
// who starts typing without touching the dropdown — confirmed live
// 2026-09-18 — so the default here skips it in favour of the first kind
// this form can actually save.
const kind = ref(current.value.reference_kind || defaultKind());
function defaultKind() {
	return props.kinds.find((option) => option !== "Method eligibility") || props.kinds[0] || "Reservation rules";
}
const form = ref({
	display_name: "",
	reference_key: "",
	effective_from: "",
	effective_until: "",
	applicability_basis: "",
	applicability_entity_types: [],
	applicability_county: "All",
	applicability_categories: [],
	applicability_currency: "KES",
	source_instrument: "",
	provision: "",
	source_document: "",
	interpretation: "",
	change_reason: "",
});
const payload = ref({});
const priceRows = ref([]);

function seed() {
	const version = current.value;
	kind.value = version.reference_kind || defaultKind();
	form.value = {
		display_name: version.reference_key ? version.reference_kind || "" : "",
		reference_key: "",
		effective_from: version.effective_from || "",
		effective_until: version.effective_until || "",
		applicability_basis: version.applicability_basis || "",
		applicability_entity_types: [...(version.applicability_entity_types || [])],
		applicability_county: version.applicability_county || "All",
		applicability_categories: [...(version.applicability_categories || [])],
		applicability_currency: version.applicability_currency || "KES",
		source_instrument: version.source_instrument || "",
		provision: version.provision || "",
		source_document: version.source_document || "",
		interpretation: version.interpretation || "",
		change_reason: "",
	};
	payload.value = { ...(version.payload || {}) };
	priceRows.value = [...((version.payload || {}).rows || [])];
}
seed();
watch(() => props.currentVersion, seed);

// §7.3 — the set that already exists after a half-completed creation. A
// retry must reuse it, or a second empty set is left behind every attempt.
const setCreated = ref("");
const busy = ref(false);
const error = ref("");
const partial = computed(() => !!setCreated.value);

const delegated = computed(() => kind.value === "Method eligibility");
const canSave = computed(() => {
	if (busy.value || delegated.value) return false;
	if (!form.value.effective_from) return false;
	if (creating.value && !partial.value) {
		return !!(form.value.reference_key.trim() && form.value.display_name.trim() && kind.value);
	}
	return true;
});

function toggle(list, value) {
	const index = list.indexOf(value);
	if (index === -1) list.push(value);
	else list.splice(index, 1);
}

function addPriceRow() {
	priceRows.value.push({ item: "", category: "", unit: "", currency: "KES", price: "" });
}
function removePriceRow(index) {
	priceRows.value.splice(index, 1);
}

function builtPayload() {
	const values = { ...payload.value };
	if (kind.value === "Market price index") values.rows = priceRows.value;
	return values;
}

async function save() {
	busy.value = true;
	error.value = "";
	try {
		let target = props.referenceSet || setCreated.value;
		if (!target) {
			// §7.3 step 1: the set alone. Recorded before step 2 so a failure
			// there leaves a recoverable rule, not a lost form.
			const created = await procurementSettingsApi.createRegulatoryReference({
				reference_key: form.value.reference_key.trim(),
				reference_kind: kind.value,
				display_name: form.value.display_name.trim(),
			});
			target = created.reference_set;
			setCreated.value = target;
		}
		await procurementSettingsApi.saveRegulatoryReferenceVersion({
			reference_set: target,
			payload: builtPayload(),
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until,
			applicability_basis: form.value.applicability_basis,
			applicability_entity_types: form.value.applicability_entity_types,
			applicability_county: form.value.applicability_county,
			applicability_categories: form.value.applicability_categories,
			applicability_currency: form.value.applicability_currency,
			source_instrument: form.value.source_instrument,
			provision: form.value.provision,
			source_document: form.value.source_document,
			interpretation: form.value.interpretation,
			supersedes_version_ids: current.value.reference ? [current.value.reference] : [],
			change_reason: form.value.change_reason,
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
	<div class="kt-procset-view" data-testid="kt-procset-rule-editor">
		<div class="kt-section-head">
			<div>
				<span class="kt-eyebrow">{{ __("Procurement settings") }}</span>
				<h2 class="kt-section-title">
					{{ creating ? __("Add procurement rule") : __("{0} — new version", [current.reference_kind || __("Procurement rule")]) }}
				</h2>
			</div>
			<button type="button" class="kt-btn kt-btn-ghost" data-testid="kt-procset-rule-editor-back" @click="emit('cancel')">← {{ __("Procurement settings") }}</button>
		</div>

		<!-- §7.3 recovery — the set exists, the version does not, and the
		     entries below are still here to finish with. -->
		<div v-if="partial" class="kt-notice is-warning" data-testid="kt-procset-rule-partial">
			<div class="kt-notice-body">
				<strong>{{ __("Rule created; version not saved.") }}</strong>
				{{ __("Your entries are retained so you can finish saving this version.") }}
			</div>
		</div>

		<div class="kt-card kt-blueprint kt-procset-wide">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />

			<div v-if="creating" class="kt-setup-grid">
				<div class="kt-field">
					<label for="kt-rule-name">{{ __("Rule name") }}</label>
					<input id="kt-rule-name" v-model="form.display_name" class="kt-input" :disabled="partial" data-testid="kt-rule-name">
				</div>
				<div class="kt-field">
					<label for="kt-rule-key">{{ __("Rule identifier") }}</label>
					<input id="kt-rule-key" v-model="form.reference_key" class="kt-input" :disabled="partial" data-testid="kt-rule-key">
				</div>
			</div>
			<div v-if="creating" class="kt-field">
				<label for="kt-rule-kind">{{ __("Rule kind") }}</label>
				<select id="kt-rule-kind" v-model="kind" class="kt-input" :disabled="partial" data-testid="kt-rule-kind">
					<option v-for="option in kinds" :key="option" :value="option">{{ option }}</option>
				</select>
			</div>
			<div v-else class="kt-meta-row">
				<div><span class="kt-label">{{ __("Earlier version") }}</span><span class="kt-meta-value">{{ current.version_number }}</span></div>
				<div><span class="kt-label">{{ __("Applies from") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_from) }}</span></div>
				<div><span class="kt-label">{{ __("Applies until") }}</span><span class="kt-meta-value">{{ fmtDate(current.effective_until) }}</span></div>
			</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("When this rule applies") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label for="kt-rule-from">{{ __("Applies from") }}</label>
							<input id="kt-rule-from" v-model="form.effective_from" class="kt-input" type="date" data-testid="kt-rule-from">
						</div>
						<div class="kt-field">
							<label for="kt-rule-until">{{ __("Applies until") }}</label>
							<input id="kt-rule-until" v-model="form.effective_until" class="kt-input" type="date" data-testid="kt-rule-until">
						</div>
					</div>
					<div class="kt-field">
						<label for="kt-rule-basis">{{ __("Which date determines the rule to use?") }}</label>
						<select id="kt-rule-basis" v-model="form.applicability_basis" class="kt-input" data-testid="kt-rule-basis">
							<option value="">{{ __("— Select —") }}</option>
							<option v-for="basis in APPLICABILITY_BASES" :key="basis" :value="basis">{{ applicabilityBasisLabel(basis) }}</option>
						</select>
					</div>
					<div class="kt-setup-grid">
						<div class="kt-field">
							<label id="kt-rule-entity-types">{{ __("Entity types") }}</label>
							<div style="display:flex;flex-direction:column;gap:4px" role="group" aria-labelledby="kt-rule-entity-types">
								<label v-for="type in entityTypes" :key="type" class="kt-checkbox">
									<input
										type="checkbox"
										:checked="form.applicability_entity_types.includes(type)"
										:data-testid="'kt-rule-entity-' + type"
										@change="toggle(form.applicability_entity_types, type)"
									>
									<span class="box" />{{ type }}
								</label>
							</div>
						</div>
						<div class="kt-field">
							<label for="kt-rule-county">{{ __("County applicability") }}</label>
							<select id="kt-rule-county" v-model="form.applicability_county" class="kt-input" data-testid="kt-rule-county">
								<option v-for="option in COUNTY_APPLICABILITY" :key="option.value" :value="option.value">{{ option.label }}</option>
							</select>
						</div>
						<div class="kt-field">
							<label id="kt-rule-categories">{{ __("Categories") }}</label>
							<div style="display:flex;gap:14px" role="group" aria-labelledby="kt-rule-categories">
								<label v-for="category in categories" :key="category" class="kt-checkbox">
									<input
										type="checkbox"
										:checked="form.applicability_categories.includes(category)"
										:data-testid="'kt-rule-category-' + category"
										@change="toggle(form.applicability_categories, category)"
									>
									<span class="box" />{{ category }}
								</label>
							</div>
						</div>
						<div class="kt-field">
							<label for="kt-rule-currency">{{ __("Currency") }}</label>
							<input id="kt-rule-currency" v-model="form.applicability_currency" class="kt-input" data-testid="kt-rule-currency">
						</div>
					</div>
				</div>

				<!-- C03-C — the kind's own validated fields. -->
				<div class="kt-section" data-testid="kt-rule-kind-fields">
					<h6 class="kt-card-title">{{ kind }}</h6>

					<!-- D10 — Method eligibility is maintained as a Procedure Method
					     Profile, with its own conditions and evidence; a second
					     field group here would be a divergent copy of the same rule. -->
					<div v-if="delegated" class="kt-notice is-warning" data-testid="kt-rule-delegated">
						<div class="kt-notice-body">
							{{ __("Method eligibility is maintained as a method profile, with its own conditions and evidence. Open the method profile to add a version.") }}
						</div>
					</div>

					<div v-else-if="kind === 'Reservation rules'" class="kt-setup-grid">
						<div class="kt-field"><label for="kt-rr-code">{{ __("Obligation code") }}</label><input id="kt-rr-code" v-model="payload.obligation_code" class="kt-input" data-testid="kt-rr-code"></div>
						<div class="kt-field"><label for="kt-rr-target">{{ __("Target") }}</label><input id="kt-rr-target" v-model="payload.target_percent" class="kt-input" type="number" data-testid="kt-rr-target"></div>
						<div class="kt-field"><label for="kt-rr-county-target">{{ __("County target") }}</label><input id="kt-rr-county-target" v-model="payload.county_target_percent" class="kt-input" type="number" data-testid="kt-rr-county-target"></div>
						<div class="kt-field">
							<label for="kt-rr-basis">{{ __("Measured against") }}</label>
							<select id="kt-rr-basis" v-model="payload.denominator_basis" class="kt-input" data-testid="kt-rr-basis">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="option in DENOMINATOR_BASES" :key="option.value" :value="option.value">{{ option.label }}</option>
							</select>
						</div>
						<div class="kt-field">
							<label for="kt-rr-overlap">{{ __("How targets overlap") }}</label>
							<select id="kt-rr-overlap" v-model="payload.overlap_policy" class="kt-input" data-testid="kt-rr-overlap">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="option in OVERLAP_POLICIES" :key="option.value" :value="option.value">{{ option.label }}</option>
							</select>
						</div>
					</div>

					<div v-else-if="kind === 'Exclusive preference'" class="kt-setup-grid">
						<div class="kt-field"><label for="kt-xp-code">{{ __("Restriction code") }}</label><input id="kt-xp-code" v-model="payload.restriction_code" class="kt-input" data-testid="kt-xp-code"></div>
						<div class="kt-field">
							<label for="kt-xp-category">{{ __("Category") }}</label>
							<select id="kt-xp-category" v-model="payload.category" class="kt-input" data-testid="kt-xp-category">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
							</select>
						</div>
						<div class="kt-field">
							<label for="kt-xp-comparator">{{ __("Comparison") }}</label>
							<select id="kt-xp-comparator" v-model="payload.comparator" class="kt-input" data-testid="kt-xp-comparator">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="option in COMPARATORS" :key="option" :value="option">{{ option }}</option>
							</select>
						</div>
						<div class="kt-field"><label for="kt-xp-amount">{{ __("Amount") }}</label><input id="kt-xp-amount" v-model="payload.amount" class="kt-input" type="number" data-testid="kt-xp-amount"></div>
						<div class="kt-field"><label for="kt-xp-party">{{ __("Eligible party classification") }}</label><input id="kt-xp-party" v-model="payload.eligible_party_classification" class="kt-input" data-testid="kt-xp-party"></div>
					</div>

					<div v-else-if="kind === 'Preference margins'" class="kt-setup-grid">
						<div class="kt-field"><label for="kt-pm-scheme">{{ __("Scheme code") }}</label><input id="kt-pm-scheme" v-model="payload.scheme_code" class="kt-input" data-testid="kt-pm-scheme"></div>
						<div class="kt-field"><label for="kt-pm-margin">{{ __("Margin") }}</label><input id="kt-pm-margin" v-model="payload.margin_percent" class="kt-input" type="number" data-testid="kt-pm-margin"></div>
						<div class="kt-field"><label for="kt-pm-from">{{ __("Shareholding from") }}</label><input id="kt-pm-from" v-model="payload.shareholding_from" class="kt-input" type="number" data-testid="kt-pm-from"></div>
						<div class="kt-field"><label for="kt-pm-to">{{ __("Shareholding to") }}</label><input id="kt-pm-to" v-model="payload.shareholding_to" class="kt-input" type="number" data-testid="kt-pm-to"></div>
						<div class="kt-field"><label for="kt-pm-origin">{{ __("Origin condition") }}</label><input id="kt-pm-origin" v-model="payload.origin_condition" class="kt-input" data-testid="kt-pm-origin"></div>
						<div class="kt-field"><label for="kt-pm-basis">{{ __("Evaluation basis") }}</label><input id="kt-pm-basis" v-model="payload.evaluation_basis" class="kt-input" data-testid="kt-pm-basis"></div>
					</div>

					<div v-else-if="kind === 'Market price index'">
						<table class="kt-table" data-testid="kt-mpi-rows">
							<thead>
								<tr><th>{{ __("Item") }}</th><th>{{ __("Category") }}</th><th>{{ __("Unit") }}</th><th>{{ __("Currency") }}</th><th>{{ __("Price") }}</th><th>{{ __("Action") }}</th></tr>
							</thead>
							<tbody>
								<tr v-for="(row, index) in priceRows" :key="index">
									<td><input v-model="row.item" class="kt-input" :data-testid="'kt-mpi-item-' + index"></td>
									<td>
										<select v-model="row.category" class="kt-input">
											<option value="">{{ __("— Select —") }}</option>
											<option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
										</select>
									</td>
									<td><input v-model="row.unit" class="kt-input"></td>
									<td><input v-model="row.currency" class="kt-input"></td>
									<td><input v-model="row.price" class="kt-input" type="number"></td>
									<td><button type="button" class="kt-btn kt-btn-ghost kt-btn-sm" @click="removePriceRow(index)">{{ __("Remove row") }}</button></td>
								</tr>
								<tr v-if="!priceRows.length"><td colspan="6" class="kt-muted">{{ __("No price index has been published for this period.") }}</td></tr>
							</tbody>
						</table>
						<button type="button" class="kt-btn kt-btn-ghost kt-btn-sm" style="margin-top:8px" data-testid="kt-mpi-add" @click="addPriceRow">{{ __("Add row") }}</button>
					</div>

					<div v-else-if="kind === 'Approval applicability'" class="kt-setup-grid">
						<div class="kt-field">
							<label id="kt-aa-entity-types">{{ __("Entity types") }}</label>
							<div style="display:flex;flex-direction:column;gap:4px" role="group" aria-labelledby="kt-aa-entity-types">
								<label v-for="type in entityTypes" :key="type" class="kt-checkbox">
									<input
										type="checkbox"
										:checked="(payload.entity_types || []).includes(type)"
										:data-testid="'kt-aa-entity-' + type"
										@change="payload.entity_types = payload.entity_types || []; toggle(payload.entity_types, type)"
									>
									<span class="box" />{{ type }}
								</label>
							</div>
						</div>
						<div class="kt-field">
							<label for="kt-aa-county">{{ __("County applicability") }}</label>
							<select id="kt-aa-county" v-model="payload.county_applicability" class="kt-input" data-testid="kt-aa-county">
								<option v-for="option in COUNTY_APPLICABILITY" :key="option.value" :value="option.value">{{ option.label }}</option>
							</select>
						</div>
						<div class="kt-field">
							<label for="kt-aa-route">{{ __("Plan approval authority") }}</label>
							<select id="kt-aa-route" v-model="payload.approval_route" class="kt-input" data-testid="kt-aa-route">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="route in APPROVAL_ROUTES" :key="route" :value="route">{{ route }}</option>
							</select>
						</div>
						<div class="kt-field"><label for="kt-aa-evidence">{{ __("Required entity evidence") }}</label><input id="kt-aa-evidence" v-model="payload.required_entity_evidence" class="kt-input" data-testid="kt-aa-evidence"></div>
					</div>

					<div v-else-if="kind === 'Publication obligations'" class="kt-setup-grid">
						<div class="kt-field"><label for="kt-po-id">{{ __("Obligation") }}</label><input id="kt-po-id" v-model="payload.obligation_id" class="kt-input" data-testid="kt-po-id"></div>
						<div class="kt-field"><label for="kt-po-actor">{{ __("Accountable actor") }}</label><input id="kt-po-actor" v-model="payload.accountable_actor_role" class="kt-input" data-testid="kt-po-actor"></div>
						<div class="kt-field"><label for="kt-po-recipient">{{ __("Recipient") }}</label><input id="kt-po-recipient" v-model="payload.recipient" class="kt-input" data-testid="kt-po-recipient"></div>
						<div class="kt-field"><label for="kt-po-channel">{{ __("Channel") }}</label><input id="kt-po-channel" v-model="payload.channel" class="kt-input" data-testid="kt-po-channel"></div>
						<div class="kt-field"><label for="kt-po-trigger">{{ __("Trigger") }}</label><input id="kt-po-trigger" v-model="payload.trigger_event" class="kt-input" data-testid="kt-po-trigger"></div>
						<div class="kt-field">
							<label for="kt-po-due">{{ __("Due rule") }}</label>
							<select id="kt-po-due" v-model="payload.due_rule" class="kt-input" data-testid="kt-po-due">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="option in DUE_RULES" :key="option.value" :value="option.value">{{ option.label }}</option>
							</select>
						</div>
						<div class="kt-field"><label for="kt-po-days">{{ __("Days") }}</label><input id="kt-po-days" v-model="payload.days" class="kt-input" type="number" data-testid="kt-po-days"></div>
						<div class="kt-field"><label for="kt-po-period">{{ __("Reporting period") }}</label><input id="kt-po-period" v-model="payload.reporting_period" class="kt-input" data-testid="kt-po-period"></div>
					</div>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div class="kt-setup-grid">
						<div class="kt-field"><label for="kt-rule-instrument">{{ __("Instrument") }}</label><input id="kt-rule-instrument" v-model="form.source_instrument" class="kt-input" data-testid="kt-rule-instrument"></div>
						<!-- §4.6 — edition, amendment history and the attached document
						     are verification evidence, appended by a source check; they
						     cannot sit on the version, which is immutable once saved.
						     Shown here so the reader knows where they are captured. -->
						<div class="kt-field">
							<label for="kt-rule-edition">{{ __("Edition") }}</label>
							<div id="kt-rule-edition" class="kt-ro" data-testid="kt-rule-edition">{{ __("Recorded with the source check") }}</div>
						</div>
						<div class="kt-field"><label for="kt-rule-provisions">{{ __("Provisions") }}</label><input id="kt-rule-provisions" v-model="form.provision" class="kt-input" data-testid="kt-rule-provisions"></div>
						<div class="kt-field"><label for="kt-rule-url">{{ __("Source URL") }}</label><input id="kt-rule-url" v-model="form.source_document" class="kt-input" data-testid="kt-rule-url"></div>
						<div class="kt-field">
							<label for="kt-rule-document">{{ __("Source document") }}</label>
							<div id="kt-rule-document" class="kt-ro" data-testid="kt-rule-document">{{ __("Not attached") }}</div>
						</div>
						<div class="kt-field">
							<label for="kt-rule-amendments">{{ __("Effective dates and amendments") }}</label>
							<div id="kt-rule-amendments" class="kt-ro" data-testid="kt-rule-amendments">{{ __("Recorded with the source check") }}</div>
						</div>
					</div>
					<div class="kt-field">
						<label for="kt-rule-interpretation">{{ __("Interpretation") }}</label>
						<textarea id="kt-rule-interpretation" v-model="form.interpretation" class="kt-input kt-textarea" rows="2" data-testid="kt-rule-interpretation" />
					</div>
				</div>

				<!-- C03-B "version" — the replacement and its effect, stated before
				     the save, never after. -->
				<div v-if="!creating" class="kt-section" data-testid="kt-rule-replacement">
					<div class="kt-field">
						<label for="kt-rule-reason">{{ __("Reason for change") }}</label>
						<textarea id="kt-rule-reason" v-model="form.change_reason" class="kt-input kt-textarea" rows="2" data-testid="kt-rule-reason" />
					</div>
					<p class="kt-muted" style="font-size:13px">
						{{ __("Earlier versions this replaces: Version {0}.", [current.version_number]) }}
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

			<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-rule-error">{{ error }}</p>
		</div>

		<div class="kt-procset-footer kt-procset-wide">
			<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-rule-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
			<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-rule-save" @click="save">
				{{ creating ? __("Save rule version") : __("Save new version") }}
			</button>
		</div>
	</div>
</template>
