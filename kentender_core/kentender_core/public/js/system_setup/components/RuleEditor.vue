<script setup>
// CFG-CHG-002 v0.14 §10.6/§10.7 (C03BC #add, #kinds, #version; tracker
// CFG14-5D) — one form for every rule kind, ported from the board: identity
// (new rule) or the shared new-version header, the kind's own card
// (RuleKindFields), when it applies, and its sources.
//
// §7.3's creation is two commands, and the recovery matters: if the set is
// created and the version save then fails, the set exists with no version
// and the administrator's entries must survive so they can finish. That is
// exactly what `setCreated` tracks — a retry reuses the set instead of
// creating a second one.
//
// Method eligibility keeps its own model and full editor (D10, D21): choosing
// it here picks the method, then opens that method's rule — a new version
// when it already has one, the full editor for a first one.
import { computed, ref, watch } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { applicabilityBasisLabel, datesOverlap } from "../data/format.js";
import RuleKindFields from "./RuleKindFields.vue";
import RuleVersionHeader from "./RuleVersionHeader.vue";
import RuleFormError from "./RuleFormError.vue";
import MethodVersionEditor from "./MethodVersionEditor.vue";

const props = defineProps({
	// Creating a rule: no set yet. Creating a new version: the set and its
	// current version, whose values seed the form (§11.6 — correction copies
	// the current rule, never edits it in place).
	referenceSet: { type: String, default: "" },
	currentVersion: { type: Object, default: null },
	// "correct" edits `currentVersion` itself, which the server allows only
	// while no source check has been recorded against it and it has not taken
	// effect. Anything else saves a new version.
	mode: { type: String, default: "version" },
	kinds: { type: Array, default: () => [] },
	entityTypes: { type: Array, default: () => [] },
	categories: { type: Array, default: () => [] },
	methods: { type: Array, default: () => [] },
	// Existing method eligibility rules ({ profile, procurement_method }), so
	// choosing a method that already has one opens it instead of a duplicate.
	methodRules: { type: Array, default: () => [] },
	// The method editor's closed vocabularies, for a first method rule.
	conditionKinds: { type: Array, default: () => [] },
	cumulativeBases: { type: Array, default: () => [] },
	applicabilityBases: { type: Array, default: () => [] },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel", "refresh", "review", "open-method-version", "method-saved"]);

const creating = computed(() => !props.referenceSet);
const correcting = computed(() => props.mode === "correct" && !!current.value.reference);

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
const SELECT_DEFAULTS = {
	overlap_policy: "",
	category: "",
	method: "",
	currency: "",
	comparator: "",
	county_applicability: "All",
	approval_route: "",
	due_rule: "",
};
const current = computed(() => props.currentVersion || {});
// A new rule defaults to the first kind this form saves itself; Method
// eligibility opens its own editor once a method is chosen (D21).
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
	delete payload.value.denominator_basis;
	if (!payload.value.measure_stage) payload.value.measure_stage = "PlanningAllocation";
	// Every select in the kind card needs a defined value, or it renders blank
	// instead of its "— Select —" / "Not yet established" / "All" option.
	for (const [field, blank] of Object.entries(SELECT_DEFAULTS)) {
		if (payload.value[field] === undefined || payload.value[field] === null) payload.value[field] = blank;
	}
	priceRows.value = [...((version.payload || {}).rows || [])];
}
seed();
// Re-seed only when a different version arrives. A re-read of the same one
// (Review latest details after a stale save) keeps the entries for review.
watch(
	() => props.currentVersion,
	(now, before) => {
		if ((now?.reference || "") !== (before?.reference || "")) seed();
		error.value = "";
	}
);

// §7.3 — the set that already exists after a half-completed creation. A
// retry must reuse it, or a second empty set is left behind every attempt.
const setCreated = ref("");
const busy = ref(false);
const error = ref("");
const partial = computed(() => !!setCreated.value);

const delegated = computed(() => creating.value && kind.value === "Method eligibility");
const methodChoice = ref("");
const existingMethodRule = computed(() => props.methodRules.find((row) => row.procurement_method === methodChoice.value) || null);
// D16 — the version this was opened from is replaced only when the new dates
// overlap it; the header says which.
const replaces = computed(
	() =>
		!!current.value.reference &&
		datesOverlap(current.value.effective_from, current.value.effective_until, form.value.effective_from, form.value.effective_until)
);
const ruleName = computed(() => current.value.display_name || current.value.reference_kind || __("Procurement rule"));
const canSave = computed(() => {
	if (busy.value || delegated.value) return false;
	if (!form.value.effective_from) return false;
	if (correcting.value) return true;
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
	priceRows.value.push({ item: "", category: "", unit: "", currency: "KES", price: "", observation_date: "" });
}
function removePriceRow(index) {
	priceRows.value.splice(index, 1);
}

function builtPayload() {
	const values = { ...payload.value };
	if (kind.value !== "Reservation rules") delete values.measure_stage;
	if (kind.value === "Market price index") values.rows = priceRows.value;
	return values;
}

async function save() {
	busy.value = true;
	error.value = "";
	try {
		if (correcting.value) {
			// The same rule, changed in place: no new version, so nothing is
			// superseded and no reason for a replacement is asked for.
			await procurementSettingsApi.updateRegulatoryReferenceVersion({
				reference: current.value.reference,
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
				expected_version: current.value.expected_version,
			});
			emit("saved");
			return;
		}
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
			// D16 — the version this was opened from is declared replaced only
			// when the new dates overlap it; the server refuses both an
			// undeclared overlap and a declared non-overlap.
			supersedes_version_ids: replaces.value ? [current.value.reference] : [],
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
	<div class="kt-rule-editor" data-testid="kt-procset-rule-editor">
		<!-- §7.3 recovery (C03BC #list card 3) — the rule exists, its version
		     does not, and the entries below are still here to finish with. -->
		<div v-if="partial" class="kt-notice is-warning" style="flex-direction:column;align-items:flex-start;margin-bottom:16px" data-testid="kt-procset-rule-partial">
			<div style="display:flex;gap:12px;align-items:flex-start">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l9 16H3z" /><path d="M12 10v4M12 17h.01" /></svg>
				<div class="kt-notice-body"><strong>{{ __("Rule created; version not saved.") }}</strong> {{ __("Your entries are retained so you can finish saving this version.") }}</div>
			</div>
			<button type="button" class="kt-btn kt-btn-primary" style="margin-left:30px" :disabled="!canSave" data-testid="kt-procset-rule-partial-save" @click="save">{{ __("Save rule version") }}</button>
		</div>

		<template v-if="creating">
			<h3 data-testid="kt-rule-editor-title">{{ __("Add procurement rule") }}</h3>
			<div class="kt-rule-grid" style="margin:16px 0">
				<div class="kt-field">
					<label for="kt-rule-name">{{ __("Rule name") }}</label>
					<input id="kt-rule-name" v-model="form.display_name" class="kt-input" :disabled="partial" data-testid="kt-rule-name">
				</div>
				<div class="kt-field">
					<label for="kt-rule-key">{{ __("Rule identifier") }}</label>
					<input id="kt-rule-key" v-model="form.reference_key" class="kt-input" :disabled="partial" data-testid="kt-rule-key">
				</div>
				<div class="kt-field" style="grid-column:1/-1">
					<label for="kt-rule-kind">{{ __("Rule kind") }}</label>
					<select id="kt-rule-kind" v-model="kind" class="kt-input" :disabled="partial" data-testid="kt-rule-kind">
						<option v-for="option in kinds" :key="option" :value="option">{{ option }}</option>
					</select>
				</div>
			</div>
		</template>
		<template v-else-if="correcting">
			<h3 style="margin-bottom:4px" data-testid="kt-rule-editor-title">{{ __("{0} — edit rule", [ruleName]) }}</h3>
			<span class="kt-tag kt-tag-neutral">{{ __("Unsaved changes") }}</span>
			<div class="kt-notice is-info" style="margin:12px 0" data-testid="kt-rule-correcting-notice">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
				<div class="kt-notice-body">{{ __("No source check has been recorded against this rule and it has not taken effect, so it can be changed here. Once either happens, changing it means a new version.") }}</div>
			</div>
		</template>
		<RuleVersionHeader v-else v-model="form.change_reason" :rule-name="ruleName" :current="current" :replaces="replaces" />

		<!-- D21 — Method eligibility: pick the method; a method that already has
		     a rule opens it, a new one opens the full method editor. -->
		<template v-if="delegated">
			<div class="kt-rule-grid" style="margin-bottom:12px">
				<div class="kt-field">
					<label for="kt-rule-method">{{ __("Method") }}</label>
					<select id="kt-rule-method" v-model="methodChoice" class="kt-input" data-testid="kt-rule-method">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="method in methods" :key="method" :value="method">{{ method }}</option>
					</select>
				</div>
			</div>
			<div v-if="existingMethodRule" class="kt-notice is-info" style="flex-direction:column;align-items:flex-start" data-testid="kt-rule-method-exists">
				<div style="display:flex;gap:12px;align-items:flex-start">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
					<div class="kt-notice-body">{{ __("Method eligibility — {0} already exists. Change it by creating a new version.", [methodChoice]) }}</div>
				</div>
				<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-rule-method-open" @click.prevent="emit('open-method-version', existingMethodRule.profile)">{{ __("Create new version") }}</a>
			</div>
			<MethodVersionEditor
				v-else-if="methodChoice"
				:key="methodChoice"
				name=""
				mode="create"
				:method="methodChoice"
				:categories="categories"
				:condition-kinds="conditionKinds"
				:cumulative-bases="cumulativeBases"
				:applicability-bases="applicabilityBases"
				:verification-statuses="verificationStatuses"
				@saved="(profile) => emit('method-saved', profile)"
				@cancel="emit('cancel')"
			/>
			<div v-else style="display:flex;gap:8px;justify-content:flex-end">
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-rule-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
			</div>
		</template>

		<template v-else>
			<RuleKindFields
				:kind="kind"
				:payload="payload"
				:price-rows="priceRows"
				:categories="categories"
				:methods="methods"
				@add-price-row="addPriceRow"
				@remove-price-row="removePriceRow"
			/>

			<h6 class="kt-card-title" style="margin-top:20px">{{ __("When this rule applies") }}</h6>
			<div class="kt-rule-grid" style="gap:14px;margin-bottom:14px">
				<div class="kt-field">
					<label for="kt-rule-from">{{ __("Applies from") }}</label>
					<input id="kt-rule-from" v-model="form.effective_from" class="kt-input" type="date" data-testid="kt-rule-from">
				</div>
				<div class="kt-field">
					<label for="kt-rule-until">{{ __("Applies until") }}</label>
					<input id="kt-rule-until" v-model="form.effective_until" class="kt-input" type="date" data-testid="kt-rule-until">
				</div>
				<div class="kt-field" style="grid-column:1/-1">
					<label for="kt-rule-basis">{{ __("Which date determines the rule to use?") }}</label>
					<select id="kt-rule-basis" v-model="form.applicability_basis" class="kt-input" data-testid="kt-rule-basis">
						<option value="">{{ __("— Select —") }}</option>
						<option v-for="basis in APPLICABILITY_BASES" :key="basis" :value="basis">{{ applicabilityBasisLabel(basis) }}</option>
					</select>
				</div>
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
					<div style="display:flex;gap:14px;flex-wrap:wrap" role="group" aria-labelledby="kt-rule-categories">
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
					<select id="kt-rule-currency" v-model="form.applicability_currency" class="kt-input" data-testid="kt-rule-currency">
						<option value="">{{ __("— Select —") }}</option>
						<option value="KES">KES</option>
					</select>
				</div>
			</div>

			<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
			<div class="kt-rule-grid" style="gap:14px">
				<div class="kt-field"><label for="kt-rule-instrument">{{ __("Instrument") }}</label><input id="kt-rule-instrument" v-model="form.source_instrument" class="kt-input" data-testid="kt-rule-instrument"></div>
				<!-- §4.6 — edition and amendment history are verification evidence,
				     appended by a source check; the version itself is immutable. -->
				<div class="kt-field"><label for="kt-rule-edition">{{ __("Edition") }}</label><input id="kt-rule-edition" class="kt-input" :value="__('Recorded with the source check')" disabled data-testid="kt-rule-edition"></div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-rule-provisions">{{ __("Provisions") }}</label><input id="kt-rule-provisions" v-model="form.provision" class="kt-input" data-testid="kt-rule-provisions"></div>
				<div class="kt-field"><label for="kt-rule-url">{{ __("Source URL") }}</label><input id="kt-rule-url" v-model="form.source_document" class="kt-input" data-testid="kt-rule-url"></div>
				<div class="kt-field"><label for="kt-rule-document">{{ __("Source document") }}</label><input id="kt-rule-document" class="kt-input" :value="__('Not attached')" disabled data-testid="kt-rule-document"></div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-rule-amendments">{{ __("Effective dates and amendments") }}</label><input id="kt-rule-amendments" class="kt-input" :value="__('Recorded with the source check')" disabled data-testid="kt-rule-amendments"></div>
				<div class="kt-field" style="grid-column:1/-1"><label for="kt-rule-interpretation">{{ __("Interpretation") }}</label><textarea id="kt-rule-interpretation" v-model="form.interpretation" class="kt-input" rows="2" data-testid="kt-rule-interpretation" /></div>
			</div>

			<RuleFormError :error="error" style="margin-top:16px" @refresh="emit('refresh')" @review="emit('review')" />

			<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="kt-rule-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-rule-save" @click="save">
					{{ creating ? __("Save rule version") : correcting ? __("Save changes") : __("Save new version") }}
				</button>
			</div>
		</template>
	</div>
</template>
