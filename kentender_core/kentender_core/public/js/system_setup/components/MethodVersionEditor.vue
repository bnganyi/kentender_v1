<script setup>
// CFG-CHG-002 v0.11 §4.6 / §10.6 (C03-BC "Method eligibility", C03-B
// "version") — the full editor for a method eligibility rule.
//
// Changing which purchases qualify, what the limits are, or what evidence a
// condition needs is ordinary configuration work, and until now the only way
// to do it was a thin dialog that let three fields of an existing row be
// retyped. This screen edits the whole rule — conditions added, removed and
// rewritten — in one of two modes, which the server chooses:
//
// - "correct" changes this Version itself, while nothing has pinned it and it
//   has not taken effect. A rule in that state is unfinished configuration,
//   and correcting it should not leave a dead Version behind (owner decision,
//   23 Sep 2026).
// - "version" saves a new Version that supersedes the one it was opened from,
//   with the administrator's reason recorded beside it. That is the only way
//   to change a rule once it could matter to anyone.
//
// Every choice offered here is the server's own vocabulary (condition kinds,
// value bases, categories, source-check statuses), read from the settings
// projection rather than restated in the browser.
//
// CFG-CHG-002 v0.14 (tracker CFG14-5D, D21): the model stays as built; the
// new-version top is the board's (#version, shared RuleVersionHeader), and a
// "create" mode serves Add rule → Method eligibility for a method with no
// rule yet.
import { computed, onMounted, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { datesOverlap, sourceCheckLabel } from "../data/format.js";
import RuleVersionHeader from "./RuleVersionHeader.vue";
import RuleFormError from "./RuleFormError.vue";

const props = defineProps({
	// The Version being worked on; its values seed the form.
	name: { type: String, default: "" },
	// "create": the method a first rule is being written for (no load).
	method: { type: String, default: "" },
	// "version" registers a replacement; "correct" edits this Version in
	// place, which the server allows only while nothing has pinned it and it
	// has not taken effect. Which one is offered is the server's call, read
	// from the rule's own `can_edit`.
	mode: { type: String, default: "version" },
	categories: { type: Array, default: () => [] },
	conditionKinds: { type: Array, default: () => [] },
	cumulativeBases: { type: Array, default: () => [] },
	applicabilityBases: { type: Array, default: () => [] },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["saved", "cancel", "refresh", "review"]);

const correcting = computed(() => props.mode === "correct");
const creating = computed(() => props.mode === "create");

const loading = ref(true);
const loadError = ref("");
const current = ref(null);
const busy = ref(false);
const error = ref("");
const form = ref(null);
const conditions = ref([]);

function blankCondition() {
	return {
		condition_id: "",
		kind: props.conditionKinds[0] || "Known fact",
		description: "",
		procurement_category: "",
		minimum_amount: 0,
		maximum_amount: 0,
		cumulative_basis: "None",
		mandatory: true,
		required_evidence: "",
		authorisation_actor: "",
		authorisation_stage: "",
		statutory_reference: "",
	};
}

// A Version seeded outside this screen may carry a basis this release does
// not list; offering the stored value keeps opening the editor from silently
// rewriting a rule the administrator never touched.
const basisOptions = computed(() => {
	const stored = form.value?.applicability_basis;
	const options = [...props.applicabilityBases];
	if (stored && !options.includes(stored)) options.unshift(stored);
	return options;
});

function blankForm() {
	return { effective_from: "", effective_until: "", applicability_basis: "", verification_status: "", source_instrument: "", provision: "", source_document: "", change_reason: "" };
}

async function load() {
	if (creating.value) {
		current.value = { procurement_method: props.method, version_number: 0 };
		form.value = blankForm();
		conditions.value = [blankCondition()];
		loading.value = false;
		return;
	}
	loading.value = true;
	loadError.value = "";
	try {
		const version = await procurementSettingsApi.getMethodProfile(props.name);
		current.value = version;
		form.value = {
			effective_from: version.effective_from || "",
			effective_until: version.effective_until || "",
			applicability_basis: version.applicability_basis || "",
			verification_status: version.verification_status || "",
			source_instrument: version.source_instrument || "",
			provision: version.provision || "",
			source_document: version.source_document || "",
			change_reason: "",
		};
		conditions.value = (version.conditions || []).map((row) => ({ ...row }));
	} catch (e) {
		loadError.value = e.message;
	} finally {
		loading.value = false;
	}
}
onMounted(load);

function addCondition() {
	conditions.value.push(blankCondition());
}
function removeCondition(index) {
	conditions.value.splice(index, 1);
}

// The server refuses an empty or duplicated condition id and a rule with no
// conditions at all; saying so here means the administrator is not told only
// after losing the form to a failed save.
const blocked = computed(() => {
	if (!form.value) return __("Loading…");
	if (!form.value.effective_from) return __("Enter the date this version applies from.");
	if (!conditions.value.length) return __("Add at least one condition.");
	const ids = [];
	for (const row of conditions.value) {
		const id = (row.condition_id || "").trim();
		if (!id) return __("Give every condition an identifier.");
		if (ids.includes(id)) return __("Condition identifiers must be different from each other: {0} is used twice.", [id]);
		ids.push(id);
	}
	if (!correcting.value && !creating.value && !form.value.change_reason.trim()) return __("Say why this version replaces the earlier one.");
	return "";
});
const canSave = computed(() => !busy.value && !blocked.value);
const replaces = computed(
	() =>
		!creating.value &&
		!!props.name &&
		!!current.value &&
		datesOverlap(current.value.effective_from, current.value.effective_until, form.value?.effective_from, form.value?.effective_until)
);
const ruleName = computed(() => `${__("Method eligibility")} — ${current.value?.procurement_method || props.method}`);

async function save() {
	busy.value = true;
	error.value = "";
	try {
		const payload = {
			effective_from: form.value.effective_from,
			effective_until: form.value.effective_until || null,
			verification_status: form.value.verification_status || null,
			applicability_basis: form.value.applicability_basis || null,
			source_instrument: form.value.source_instrument,
			provision: form.value.provision,
			source_document: form.value.source_document,
			conditions: conditions.value.map((row) => ({
				condition_id: (row.condition_id || "").trim(),
				kind: row.kind,
				description: row.description,
				procurement_category: row.procurement_category || "",
				minimum_amount: Number(row.minimum_amount) || 0,
				maximum_amount: Number(row.maximum_amount) || 0,
				cumulative_basis: row.cumulative_basis || "None",
				mandatory: !!row.mandatory,
				required_evidence: row.required_evidence,
				authorisation_actor: row.authorisation_actor,
				authorisation_stage: row.authorisation_stage,
				statutory_reference: row.statutory_reference,
			})),
		};
		const saved = correcting.value
			? await procurementSettingsApi.updateMethodProfile({
				...payload,
				profile: props.name,
				expected_version: current.value.expected_version,
			})
			: await procurementSettingsApi.registerMethodProfileVersion({
				...payload,
				procurement_method: current.value.procurement_method,
				change_reason: form.value.change_reason.trim(),
				// D16 — declared only when the new dates overlap it.
				replaces: replaces.value ? props.name : "",
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
	<div class="kt-rule-editor" data-testid="kt-procset-method-editor">
		<div v-if="loading" data-testid="kt-mve-loading">
			<div class="kt-skel" style="width:40%" /><div class="kt-skel" style="width:70%" />
		</div>
		<div v-else-if="loadError" class="kt-notice is-critical" role="alert" data-testid="kt-mve-load-error">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
			<div class="kt-notice-body"><strong>{{ __("This rule isn't available to you.") }}</strong> {{ __("It may not exist, or you may not have access to it.") }}</div>
		</div>

		<template v-else>
			<div data-testid="kt-mve-card">
				<template v-if="correcting">
					<h3 style="margin-bottom:4px" data-testid="kt-mve-title">{{ __("{0} — edit rule", [ruleName]) }}</h3>
					<span class="tag tag-neutral" data-testid="kt-mve-unsaved">{{ __("Unsaved changes") }}</span>
				</template>
				<RuleVersionHeader v-else-if="!creating" v-model="form.change_reason" :rule-name="ruleName" :current="current" :replaces="replaces" />

				<!-- A correction changes this Version itself, so the screen says
				     so before anything is typed, and says what ends it. -->
				<div v-if="correcting" class="kt-notice is-info" style="margin:12px 0" data-testid="kt-mve-correcting-notice">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
					<div class="kt-notice-body">
						{{ __("This rule has not taken effect and no plan uses it yet, so it can be changed here. Once either happens, changing it means a new version.") }}
					</div>
				</div>

				<!-- C03-BC card 1, "Which purchases qualify?". The method a rule
				     governs is its identity: a version for a different method is a
				     different rule, not a correction of this one. -->
				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Which purchases qualify?") }}</h6>
					<div class="kt-setup-grid">
						<div class="field">
							<label for="kt-mve-method">{{ __("Method") }}</label>
							<div id="kt-mve-method" class="kt-ro" data-testid="kt-mve-method">{{ current.procurement_method || method }}</div>
						</div>
						<div class="field">
							<label for="kt-mve-currency">{{ __("Currency") }}</label>
							<div id="kt-mve-currency" class="kt-ro" data-testid="kt-mve-currency">{{ __("KES") }}</div>
						</div>
					</div>
					<p class="kt-muted" style="font-size:13px">
						{{ __("Which categories and values qualify is set on each condition below.") }}
					</p>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("When this rule applies") }}</h6>
					<div class="kt-setup-grid">
						<div class="field">
							<label for="kt-mve-from">{{ __("Applies from") }}</label>
							<input id="kt-mve-from" v-model="form.effective_from" class="input" type="date" data-testid="kt-mve-from">
						</div>
						<div class="field">
							<label for="kt-mve-until">{{ __("Applies until") }}</label>
							<input id="kt-mve-until" v-model="form.effective_until" class="input" type="date" data-testid="kt-mve-until">
						</div>
					</div>
					<div class="field">
						<label for="kt-mve-basis">{{ __("Which date determines the rule to use?") }}</label>
						<select id="kt-mve-basis" v-model="form.applicability_basis" class="input" data-testid="kt-mve-basis">
							<option value="">{{ __("— Select —") }}</option>
							<option v-for="basis in basisOptions" :key="basis" :value="basis">{{ basis }}</option>
						</select>
					</div>
				</div>

				<!-- C03-BC "Conditions and evidence". Each condition carries its own
				     category and value range, so a rule that treats goods and works
				     differently is one version with two conditions, never two rules. -->
				<div class="kt-section" data-testid="kt-mve-conditions">
					<h6 class="kt-card-title">{{ __("Conditions and evidence") }}</h6>
					<p v-if="!conditions.length" class="kt-muted" style="font-size:13px" data-testid="kt-mve-no-conditions">
						{{ __("Required conditions not yet completed.") }}
					</p>
					<div
						v-for="(row, index) in conditions"
						:key="index"
						class="kt-panel kt-mve-condition"
						:data-testid="'kt-mve-condition-' + index"
					>
						<div class="kt-mve-condition-head">
							<span class="kt-label">{{ __("Condition {0}", [index + 1]) }}</span>
							<button
								type="button"
								class="btn btn-ghost btn-sm"
								:data-testid="'kt-mve-remove-' + index"
								@click="removeCondition(index)"
							>
								{{ __("Remove condition") }}
							</button>
						</div>
						<div class="kt-setup-grid">
							<div class="field">
								<label :for="'kt-mve-id-' + index">{{ __("Condition identifier") }}</label>
								<input :id="'kt-mve-id-' + index" v-model="row.condition_id" class="input" :data-testid="'kt-mve-id-' + index">
							</div>
							<div class="field">
								<label :for="'kt-mve-kind-' + index">{{ __("Kind") }}</label>
								<select :id="'kt-mve-kind-' + index" v-model="row.kind" class="input" :data-testid="'kt-mve-kind-' + index">
									<option v-for="option in conditionKinds" :key="option" :value="option">{{ option }}</option>
								</select>
							</div>
							<div class="field">
								<label :for="'kt-mve-category-' + index">{{ __("Category") }}</label>
								<select :id="'kt-mve-category-' + index" v-model="row.procurement_category" class="input" :data-testid="'kt-mve-category-' + index">
									<option value="">{{ __("All categories") }}</option>
									<option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
								</select>
							</div>
							<!-- The checkbox sits in its own wrapper: `.field > label`
							     is a block field caption, and applying it to the
							     checkbox's own label flattens the box out of sight. -->
							<div class="field">
								<label :id="'kt-mve-requirement-' + index">{{ __("Requirement") }}</label>
								<div role="group" :aria-labelledby="'kt-mve-requirement-' + index">
									<label class="kt-checkbox">
										<input type="checkbox" v-model="row.mandatory" :data-testid="'kt-mve-mandatory-' + index">
										<span class="box" />{{ __("Must be met") }}
									</label>
								</div>
							</div>
						</div>
						<div class="field">
							<label :for="'kt-mve-description-' + index">{{ __("Condition") }}</label>
							<textarea :id="'kt-mve-description-' + index" v-model="row.description" class="input kt-textarea" rows="2" :data-testid="'kt-mve-description-' + index" />
						</div>
						<div class="kt-setup-grid">
							<div class="field">
								<label :for="'kt-mve-basis-' + index">{{ __("Value measured against") }}</label>
								<select :id="'kt-mve-basis-' + index" v-model="row.cumulative_basis" class="input" :data-testid="'kt-mve-basis-' + index">
									<option v-for="option in cumulativeBases" :key="option" :value="option">{{ option }}</option>
								</select>
							</div>
							<div class="field">
								<label :for="'kt-mve-min-' + index">{{ __("Minimum amount") }}</label>
								<input :id="'kt-mve-min-' + index" v-model="row.minimum_amount" class="input" type="number" min="0" :data-testid="'kt-mve-min-' + index">
							</div>
							<div class="field">
								<label :for="'kt-mve-max-' + index">{{ __("Maximum amount") }}</label>
								<input :id="'kt-mve-max-' + index" v-model="row.maximum_amount" class="input" type="number" min="0" :data-testid="'kt-mve-max-' + index">
							</div>
						</div>
						<p class="kt-muted" style="font-size:12px;margin:0 0 8px">{{ __("Leave an amount at 0 where the source states no limit.") }}</p>
						<div class="kt-setup-grid">
							<div class="field">
								<label :for="'kt-mve-evidence-' + index">{{ __("Required evidence") }}</label>
								<input :id="'kt-mve-evidence-' + index" v-model="row.required_evidence" class="input" :data-testid="'kt-mve-evidence-' + index">
							</div>
							<div class="field">
								<label :for="'kt-mve-actor-' + index">{{ __("Required authority") }}</label>
								<input :id="'kt-mve-actor-' + index" v-model="row.authorisation_actor" class="input" :data-testid="'kt-mve-actor-' + index">
							</div>
							<div class="field">
								<label :for="'kt-mve-stage-' + index">{{ __("Checked at") }}</label>
								<input :id="'kt-mve-stage-' + index" v-model="row.authorisation_stage" class="input" :data-testid="'kt-mve-stage-' + index">
							</div>
							<div class="field">
								<label :for="'kt-mve-reference-' + index">{{ __("Source reference") }}</label>
								<input :id="'kt-mve-reference-' + index" v-model="row.statutory_reference" class="input" :data-testid="'kt-mve-reference-' + index">
							</div>
						</div>
					</div>
					<button type="button" class="btn btn-ghost btn-sm" style="margin-top:8px" data-testid="kt-mve-add" @click="addCondition">
						{{ __("Add condition") }}
					</button>
				</div>

				<div class="kt-section">
					<h6 class="kt-card-title">{{ __("Sources and interpretation") }}</h6>
					<div class="kt-setup-grid">
						<div class="field">
							<label for="kt-mve-instrument">{{ __("Instrument") }}</label>
							<input id="kt-mve-instrument" v-model="form.source_instrument" class="input" data-testid="kt-mve-instrument">
						</div>
						<div class="field">
							<label for="kt-mve-provisions">{{ __("Provisions") }}</label>
							<input id="kt-mve-provisions" v-model="form.provision" class="input" data-testid="kt-mve-provisions">
						</div>
						<div class="field">
							<label for="kt-mve-url">{{ __("Source URL") }}</label>
							<input id="kt-mve-url" v-model="form.source_document" class="input" data-testid="kt-mve-url">
						</div>
						<div class="field">
							<label for="kt-mve-check">{{ __("Source check") }}</label>
							<select id="kt-mve-check" v-model="form.verification_status" class="input" data-testid="kt-mve-check">
								<option v-for="status in verificationStatuses" :key="status" :value="status">{{ __(sourceCheckLabel(status)) }}</option>
							</select>
						</div>
					</div>
				</div>

				<RuleFormError :error="error" style="margin-top:16px" @refresh="emit('refresh')" @review="emit('review')" />
			</div>

			<div style="display:flex;gap:8px;justify-content:flex-end;align-items:center;margin-top:16px;flex-wrap:wrap">
				<span v-if="blocked" class="kt-blocked" data-testid="kt-mve-blocked">{{ blocked }}</span>
				<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="kt-mve-cancel" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="btn btn-primary" :disabled="!canSave" data-testid="kt-mve-save" @click="save">{{ correcting ? __("Save changes") : creating ? __("Save rule version") : __("Save new version") }}</button>
			</div>
		</template>
	</div>
</template>
