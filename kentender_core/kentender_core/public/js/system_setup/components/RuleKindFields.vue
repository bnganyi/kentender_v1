<script setup>
// CFG-CHG-002 v0.14 §10.7 (C03BC #kinds cards 2–7; tracker CFG14-5D) — the
// selected rule kind's own groups, ported card by card from the board. Only
// the chosen kind renders. Every value is the server's validated payload
// field; nothing here decides validity. Method eligibility keeps its own
// full editor (owner decision D21), so it is not a case here.
//
// Not drawn again here, because the rule's common fields already hold them
// (one control per fact): Reservation "County applicability", Market price
// index "Applies from/until", Publication "Which date determines the rule
// to use?". See DEPARTURES.
import { computed } from "vue";

const props = defineProps({
	kind: { type: String, required: true },
	// The payload object, edited in place by the parent's form.
	payload: { type: Object, required: true },
	priceRows: { type: Array, default: () => [] },
	categories: { type: Array, default: () => [] },
	methods: { type: Array, default: () => [] },
});
const emit = defineEmits(["add-price-row", "remove-price-row"]);

const MEASURES = [
	{ value: "PlanningAllocation", label: __("Planned allocation"), against: __("Eligible value of the current Annual Plan") },
	{ value: "ImplementationAchievement", label: __("Actual achievement"), against: __("Applicable actual procurement value") },
];
const DESIGNATIONS = ["Youth", "Women", "Persons with disabilities"];
const OVERLAPS = [
	{ value: "Independent", label: __("Targets apply independently") },
	{ value: "MutuallyExclusive", label: __("Targets are mutually exclusive") },
	{ value: "SpecifiedOverlap", label: __("Specified overlap") },
];
const COMPARATORS = [
	{ value: "Equal", label: __("Equal to") },
	{ value: "NotEqual", label: __("Not equal to") },
	{ value: "In", label: __("In") },
	{ value: "NotIn", label: __("Not in") },
	{ value: "LessThan", label: __("Less than") },
	{ value: "LessThanOrEqual", label: __("Less than or equal to") },
	{ value: "GreaterThan", label: __("Greater than") },
	{ value: "GreaterThanOrEqual", label: __("Greater than or equal to") },
];
const ENTITY_TYPES = [
	"National Government Ministry",
	"State Department",
	"State Corporation",
	"County Government",
	"County Corporation",
	"Constitutional Commission",
	"Public University",
	"Other Public Entity",
];
const COUNTY = [
	{ value: "All", label: __("All") },
	{ value: "County", label: __("County") },
	{ value: "NonCounty", label: __("Non-county") },
];
const APPROVAL_ROUTES = ["Cabinet Secretary", "County Executive Committee Member", "Board of Directors", "Council"];
const DUE_RULES = [
	{ value: "Immediate", label: __("Immediate") },
	{ value: "CalendarDaysAfter", label: __("Calendar days after") },
	{ value: "WorkingDaysAfter", label: __("Working days after") },
	{ value: "PeriodEndPlusDays", label: __("Period end plus days") },
];

// Follows the prop: the parent replaces the payload object when it re-seeds.
const p = computed(() => props.payload);
const measuredAgainst = computed(() => (MEASURES.find((m) => m.value === p.value.measure_stage) || MEASURES[0]).against);
// The board's single "Eligible planned designation" over the stored list.
const designation = computed({
	get: () => (p.value.eligible_designations || [])[0] || "",
	set: (value) => (p.value.eligible_designations = value ? [value] : []),
});
const relatedObligations = computed({
	get: () => (p.value.related_obligation_codes || []).join(", "),
	set: (value) => (p.value.related_obligation_codes = value.split(",").map((code) => code.trim()).filter(Boolean)),
});
const entityType = computed({
	get: () => (p.value.entity_types || [])[0] || "",
	set: (value) => (p.value.entity_types = value ? [value] : []),
});
const exclusiveIncomplete = computed(() => {
	const v = p.value;
	return !(v.restriction_code && v.category && v.comparator && v.amount !== "" && v.amount != null);
});
</script>

<template>
	<div class="kt-card kt-rule-kind" data-testid="kt-rule-kind-fields" :data-kind="kind">
		<div class="card-kicker">{{ __(kind) }}</div>

		<template v-if="kind === 'Reservation rules'">
			<div class="kt-notice is-warning" style="margin:8px 0 14px">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ __("Illustrative values; source checks are still needed.") }}</div>
			</div>
			<h6 class="kt-card-title">{{ __("Measure") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-rr-code">{{ __("Obligation code") }}</label><input id="kt-rr-code" v-model="p.obligation_code" class="kt-input" data-testid="kt-rr-code"></div>
				<div class="kt-field">
					<label for="kt-rr-measure">{{ __("Measure") }}</label>
					<select id="kt-rr-measure" v-model="p.measure_stage" class="kt-input" data-testid="kt-rr-measure">
						<option v-for="option in MEASURES" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
			</div>
			<h6 class="kt-card-title">{{ __("Annual target") }}</h6>
			<div class="kt-field" style="margin-bottom:12px;max-width:200px">
				<label for="kt-rr-target">{{ __("Target") }}</label>
				<div style="display:flex;align-items:center;gap:8px"><input id="kt-rr-target" v-model="p.target_percent" class="kt-input" type="number" data-testid="kt-rr-target"><span>%</span></div>
			</div>
			<h6 class="kt-card-title">{{ __("What the target is measured against") }}</h6>
			<div class="kt-field" style="margin-bottom:4px">
				<label for="kt-rr-basis">{{ __("Measured against") }}</label>
				<input id="kt-rr-basis" class="kt-input" :value="measuredAgainst" readonly disabled data-testid="kt-rr-basis">
			</div>
			<p class="text-muted" style="font-size:12px;margin:0 0 12px">{{ __("Fixed for Planned allocation by the controlled interpretation. Actual achievement is measured against Applicable actual procurement value.") }}</p>
			<h6 class="kt-card-title">{{ __("Who qualifies") }}</h6>
			<div class="kt-rule-kind-grid" style="margin-bottom:6px">
				<div class="kt-field">
					<label for="kt-rr-designation">{{ __("Eligible planned designation") }}</label>
					<select id="kt-rr-designation" v-model="designation" class="kt-input" data-testid="kt-rr-designation">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="option in DESIGNATIONS" :key="option" :value="option">{{ __(option) }}</option>
					</select>
				</div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-rr-conditions">{{ __("Applicability conditions") }}</label><input id="kt-rr-conditions" v-model="p.applicability_conditions" class="kt-input" data-testid="kt-rr-conditions"></div>
			</div>
			<p class="text-muted" style="font-size:12px;margin:0 0 12px">{{ __("County residents is maintained as its own reservation rule, not as a planned designation.") }}</p>
			<h6 class="kt-card-title">{{ __("How targets overlap") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field">
					<label for="kt-rr-overlap">{{ __("How targets overlap") }}</label>
					<select id="kt-rr-overlap" v-model="p.overlap_policy" class="kt-input" data-testid="kt-rr-overlap">
						<option value="">{{ __("Not yet established") }}</option>
						<option v-for="option in OVERLAPS" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-rr-related">{{ __("Related obligations") }}</label>
					<input
						id="kt-rr-related"
						v-model.lazy="relatedObligations"
						class="kt-input"
						:disabled="p.overlap_policy !== 'SpecifiedOverlap'"
						:placeholder="p.overlap_policy === 'SpecifiedOverlap' ? '' : __('Used with Specified overlap')"
						data-testid="kt-rr-related"
					>
				</div>
			</div>
			<div class="kt-field"><label for="kt-rr-sources">{{ __("Source references") }}</label><input id="kt-rr-sources" v-model="p.source_references" class="kt-input" data-testid="kt-rr-sources"></div>
		</template>

		<template v-else-if="kind === 'Exclusive preference'">
			<h6 class="kt-card-title">{{ __("Which purchases are restricted?") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-xp-code">{{ __("Restriction code") }}</label><input id="kt-xp-code" v-model="p.restriction_code" class="kt-input" data-testid="kt-xp-code"></div>
				<div class="kt-field">
					<label for="kt-xp-category">{{ __("Category") }}</label>
					<select id="kt-xp-category" v-model="p.category" class="kt-input" data-testid="kt-xp-category">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-xp-method">{{ __("Method") }}</label>
					<select id="kt-xp-method" v-model="p.method" class="kt-input" data-testid="kt-xp-method">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="method in methods" :key="method" :value="method">{{ method }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-xp-currency">{{ __("Currency") }}</label>
					<select id="kt-xp-currency" v-model="p.currency" class="kt-input" data-testid="kt-xp-currency">
						<option value="">{{ __("— Select —") }}</option>
						<option value="KES">KES</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-xp-comparator">{{ __("Comparison") }}</label>
					<select id="kt-xp-comparator" v-model="p.comparator" class="kt-input" data-testid="kt-xp-comparator">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="option in COMPARATORS" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field"><label for="kt-xp-amount">{{ __("Amount") }}</label><input id="kt-xp-amount" v-model="p.amount" class="kt-input" inputmode="decimal" data-testid="kt-xp-amount"></div>
			</div>
			<h6 class="kt-card-title">{{ __("Eligible suppliers") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-xp-party">{{ __("Eligible party classification") }}</label><input id="kt-xp-party" v-model="p.eligible_party_classification" class="kt-input" data-testid="kt-xp-party"></div>
			</div>
			<h6 class="kt-card-title">{{ __("Conditions") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-xp-funding">{{ __("Funding-origin condition") }}</label><input id="kt-xp-funding" v-model="p.funding_origin_condition" class="kt-input" data-testid="kt-xp-funding"></div>
				<div class="kt-field"><label for="kt-xp-local">{{ __("Local-origin condition") }}</label><input id="kt-xp-local" v-model="p.local_origin_condition" class="kt-input" data-testid="kt-xp-local"></div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-xp-source">{{ __("Source reference") }}</label><input id="kt-xp-source" v-model="p.source_reference" class="kt-input" data-testid="kt-xp-source"></div>
			</div>
			<div v-if="exclusiveIncomplete" class="kt-notice is-warning" style="margin-top:4px" data-testid="kt-xp-incomplete">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ __("Required conditions not yet completed.") }}</div>
			</div>
		</template>

		<template v-else-if="kind === 'Preference margins'">
			<h6 class="kt-card-title">{{ __("Margin") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-pm-scheme">{{ __("Scheme") }}</label><input id="kt-pm-scheme" v-model="p.scheme_code" class="kt-input" data-testid="kt-pm-scheme"></div>
				<div class="kt-field"><label for="kt-pm-procedure">{{ __("Procedure") }}</label><input id="kt-pm-procedure" v-model="p.procedure" class="kt-input" data-testid="kt-pm-procedure"></div>
				<div class="kt-field"><label for="kt-pm-margin">{{ __("Margin") }}</label><div style="display:flex;align-items:center;gap:8px"><input id="kt-pm-margin" v-model="p.margin_percent" class="kt-input" inputmode="decimal" data-testid="kt-pm-margin"><span>%</span></div></div>
			</div>
			<h6 class="kt-card-title">{{ __("Qualifying conditions") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-pm-origin">{{ __("Origin condition") }}</label><input id="kt-pm-origin" v-model="p.origin_condition" class="kt-input" data-testid="kt-pm-origin"></div>
				<div class="kt-field"><label for="kt-pm-from">{{ __("Shareholding from") }}</label><div style="display:flex;align-items:center;gap:8px"><input id="kt-pm-from" v-model="p.shareholding_from" class="kt-input" inputmode="decimal" data-testid="kt-pm-from"><span>%</span></div></div>
				<div class="kt-field"><label for="kt-pm-to">{{ __("Shareholding to") }}</label><div style="display:flex;align-items:center;gap:8px"><input id="kt-pm-to" v-model="p.shareholding_to" class="kt-input" inputmode="decimal" data-testid="kt-pm-to"><span>%</span></div></div>
				<div class="kt-field">
					<label id="kt-pm-lower-l">{{ __("Lower bound included") }}</label>
					<div style="display:flex;gap:16px" role="radiogroup" aria-labelledby="kt-pm-lower-l">
						<label class="kt-radio"><input type="radio" name="kt-pm-lower" :checked="p.shareholding_from_included !== false" data-testid="kt-pm-lower-yes" @change="p.shareholding_from_included = true"><span class="dot" />{{ __("Yes") }}</label>
						<label class="kt-radio"><input type="radio" name="kt-pm-lower" :checked="p.shareholding_from_included === false" data-testid="kt-pm-lower-no" @change="p.shareholding_from_included = false"><span class="dot" />{{ __("No") }}</label>
					</div>
				</div>
				<div class="kt-field">
					<label id="kt-pm-upper-l">{{ __("Upper bound included") }}</label>
					<div style="display:flex;gap:16px" role="radiogroup" aria-labelledby="kt-pm-upper-l">
						<label class="kt-radio"><input type="radio" name="kt-pm-upper" :checked="p.shareholding_to_included !== false" data-testid="kt-pm-upper-yes" @change="p.shareholding_to_included = true"><span class="dot" />{{ __("Yes") }}</label>
						<label class="kt-radio"><input type="radio" name="kt-pm-upper" :checked="p.shareholding_to_included === false" data-testid="kt-pm-upper-no" @change="p.shareholding_to_included = false"><span class="dot" />{{ __("No") }}</label>
					</div>
				</div>
			</div>
			<h6 class="kt-card-title">{{ __("Evaluation basis") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-pm-basis">{{ __("Evaluation basis") }}</label><input id="kt-pm-basis" v-model="p.evaluation_basis" class="kt-input" data-testid="kt-pm-basis"></div>
				<div class="kt-field"><label for="kt-pm-source">{{ __("Source reference") }}</label><input id="kt-pm-source" v-model="p.source_reference" class="kt-input" data-testid="kt-pm-source"></div>
			</div>
			<div class="kt-notice is-info" style="margin-top:4px">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
				<div class="kt-notice-body">{{ __("Used during evaluation; this does not decide supplier entitlement in Planning.") }}</div>
			</div>
		</template>

		<template v-else-if="kind === 'Market price index'">
			<h6 class="kt-card-title">{{ __("Published prices") }}</h6>
			<table class="kt-table" data-testid="kt-mpi-rows">
				<thead>
					<tr><th>{{ __("Item") }}</th><th>{{ __("Category") }}</th><th>{{ __("Unit") }}</th><th>{{ __("Currency") }}</th><th>{{ __("Price") }}</th><th>{{ __("Observation date") }}</th><th v-if="priceRows.length"><span class="kt-visually-hidden">{{ __("Action") }}</span></th></tr>
				</thead>
				<tbody>
					<tr v-for="(row, index) in priceRows" :key="index">
						<td><input v-model="row.item" class="kt-input" :aria-label="__('Item')" :data-testid="'kt-mpi-item-' + index"></td>
						<td>
							<select v-model="row.category" class="kt-input" :aria-label="__('Category')">
								<option value="">{{ __("— Select —") }}</option>
								<option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
							</select>
						</td>
						<td><input v-model="row.unit" class="kt-input" :aria-label="__('Unit')"></td>
						<td><input v-model="row.currency" class="kt-input" :aria-label="__('Currency')"></td>
						<td><input v-model="row.price" class="kt-input" inputmode="decimal" :aria-label="__('Price')"></td>
						<td><input v-model="row.observation_date" class="kt-input" type="date" :aria-label="__('Observation date')"></td>
						<td><button type="button" class="kt-btn kt-btn-ghost kt-btn-sm" :data-testid="'kt-mpi-remove-' + index" @click="emit('remove-price-row', index)">{{ __("Remove row") }}</button></td>
					</tr>
					<tr v-if="!priceRows.length"><td colspan="6" class="text-muted"><span class="kt-tag kt-tag-neutral" style="margin-right:8px">{{ __("Not published") }}</span>{{ __("No price index has been published for this period.") }}</td></tr>
				</tbody>
			</table>
			<button type="button" class="kt-btn kt-btn-ghost kt-btn-sm" style="margin-top:8px" data-testid="kt-mpi-add" @click="emit('add-price-row')">{{ __("Add row") }}</button>
			<h6 class="kt-card-title" style="margin-top:12px">{{ __("Publication and coverage") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-mpi-date">{{ __("Publication date") }}</label><input id="kt-mpi-date" v-model="p.publication_date" class="kt-input" type="date" data-testid="kt-mpi-date"></div>
				<div class="kt-field"><label for="kt-mpi-ref">{{ __("Publication reference") }}</label><input id="kt-mpi-ref" v-model="p.publication_reference" class="kt-input" data-testid="kt-mpi-ref"></div>
			</div>
		</template>

		<template v-else-if="kind === 'Approval applicability'">
			<h6 class="kt-card-title">{{ __("Entity facts") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field">
					<label for="kt-aa-entity">{{ __("Entity type") }}</label>
					<select id="kt-aa-entity" v-model="entityType" class="kt-input" data-testid="kt-aa-entity">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="type in ENTITY_TYPES" :key="type" :value="type">{{ type }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-aa-county">{{ __("County applicability") }}</label>
					<select id="kt-aa-county" v-model="p.county_applicability" class="kt-input" data-testid="kt-aa-county">
						<option v-for="option in COUNTY" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-aa-evidence">{{ __("Required entity evidence") }}</label><input id="kt-aa-evidence" v-model="p.required_entity_evidence" class="kt-input" data-testid="kt-aa-evidence"></div>
			</div>
			<p v-if="!(p.required_entity_evidence || '').trim()" class="text-muted" style="font-size:12px;margin:-4px 0 12px">{{ __("Required entity evidence: Not yet established.") }}</p>
			<h6 class="kt-card-title">{{ __("Plan approval authority") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field">
					<label for="kt-aa-route">{{ __("Plan approval authority") }}</label>
					<select id="kt-aa-route" v-model="p.approval_route" class="kt-input" data-testid="kt-aa-route">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="route in APPROVAL_ROUTES" :key="route" :value="route">{{ route }}</option>
					</select>
				</div>
				<div class="kt-field"><label for="kt-aa-capacity">{{ __("Required business capacity") }}</label><input id="kt-aa-capacity" class="kt-input" :value="p.required_capacity_code || __('Configured statutory capacity')" disabled data-testid="kt-aa-capacity"></div>
			</div>
			<h6 class="kt-card-title">{{ __("Supporting instrument") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-aa-source">{{ __("Source reference") }}</label><input id="kt-aa-source" v-model="p.source_reference" class="kt-input" data-testid="kt-aa-source"></div>
			</div>
		</template>

		<template v-else-if="kind === 'Publication obligations'">
			<h6 class="kt-card-title">{{ __("What must be published or reported?") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-po-id">{{ __("Obligation") }}</label><input id="kt-po-id" v-model="p.obligation_id" class="kt-input" data-testid="kt-po-id"></div>
				<div class="kt-field"><label for="kt-po-integration">{{ __("Integration or evidence requirement") }}</label><input id="kt-po-integration" v-model="p.integration_evidence_contract_code" class="kt-input" data-testid="kt-po-integration"></div>
			</div>
			<h6 class="kt-card-title">{{ __("Who is responsible?") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-po-actor">{{ __("Accountable actor") }}</label><input id="kt-po-actor" v-model="p.accountable_actor_role" class="kt-input" data-testid="kt-po-actor"></div>
				<div class="kt-field"><label for="kt-po-recipient">{{ __("Recipient") }}</label><input id="kt-po-recipient" v-model="p.recipient" class="kt-input" data-testid="kt-po-recipient"></div>
				<div class="kt-field"><label for="kt-po-channel">{{ __("Channel") }}</label><input id="kt-po-channel" v-model="p.channel" class="kt-input" data-testid="kt-po-channel"></div>
			</div>
			<h6 class="kt-card-title">{{ __("When and where?") }}</h6>
			<div class="kt-rule-kind-grid">
				<div class="kt-field"><label for="kt-po-trigger">{{ __("Trigger") }}</label><input id="kt-po-trigger" v-model="p.trigger_event" class="kt-input" data-testid="kt-po-trigger"></div>
				<div class="kt-field">
					<label for="kt-po-due">{{ __("Due rule") }}</label>
					<select id="kt-po-due" v-model="p.due_rule" class="kt-input" data-testid="kt-po-due">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="option in DUE_RULES" :key="option.value" :value="option.value">{{ option.label }}</option>
					</select>
				</div>
				<div class="kt-field"><label for="kt-po-days">{{ __("Days") }}</label><input id="kt-po-days" v-model="p.days" class="kt-input" type="number" min="0" data-testid="kt-po-days"></div>
				<div class="kt-field"><label for="kt-po-period">{{ __("Reporting period") }}</label><input id="kt-po-period" v-model="p.reporting_period" class="kt-input" data-testid="kt-po-period"></div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-po-source">{{ __("Source reference") }}</label><input id="kt-po-source" v-model="p.source_reference" class="kt-input" data-testid="kt-po-source"></div>
			</div>
			<div class="kt-notice is-warning" style="margin-top:4px">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body">{{ __("Operating-model verification required.") }}</div>
			</div>
		</template>
	</div>
</template>
