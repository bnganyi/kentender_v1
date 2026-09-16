<script setup>
// "Create new version" for a method eligibility profile or a schedule
// profile (§11.6: a referenced Version is immutable; an update is a new
// Version with its own effective dates, source facts and verification
// status). The current rule values are copied in for correction; the server
// validates and supersedes any overlapping Active Version.
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { procurementSettingsApi } from "../data/procurementSettingsApi.js";
import { sourceCheckLabel } from "../data/format.js";

const props = defineProps({
	mode: { type: String, required: true }, // "method" | "schedule"
	current: { type: Object, required: true },
	verificationStatuses: { type: Array, default: () => [] },
});
const emit = defineEmits(["registered", "cancel"]);

const error = ref("");
const field = ref(null);
const { pending: busy, run } = kentender_core.desk_page.createCommandRunner(
	{ ref },
	{ onStart: () => (error.value = ""), onError: (e) => (error.value = e.message) }
);

const form = reactive({
	effective_from: props.current.effective_from || "",
	effective_until: props.current.effective_until || "",
	verification_status: props.current.verification_status || "Production verification pending",
	source_instrument: props.current.source_instrument || "",
	provision: props.current.provision || "",
	source_document: props.current.source_document || "",
	applicability_basis: props.current.applicability_basis || "",
	profile_name: props.current.profile_name || "",
	procedure: props.current.procedure || "",
	counting_rule: props.current.counting_rule || "Calendar days",
	estimated_delivery_period_default_days:
		props.current.estimated_delivery_period_default_days === null || props.current.estimated_delivery_period_default_days === undefined
			? ""
			: String(props.current.estimated_delivery_period_default_days),
});
const conditions = ref((props.current.conditions || []).map((row) => ({ ...row })));
const milestones = ref((props.current.milestones || []).map((row) => ({ ...row })));

const title = computed(() => (props.mode === "method" ? __("Create new method eligibility version") : __("Create new schedule profile version")));
const canSave = computed(() => !busy.value && !!form.effective_from);

onMounted(async () => {
	await nextTick();
	field.value?.focus();
});

function num(value) {
	return value === "" || value === null || value === undefined ? null : Number(value);
}

function submit() {
	return run(async () => {
		if (props.mode === "method") {
			await procurementSettingsApi.registerMethodProfileVersion({
				procurement_method: props.current.procurement_method,
				effective_from: form.effective_from,
				effective_until: form.effective_until || null,
				verification_status: form.verification_status,
				applicability_basis: form.applicability_basis || null,
				source_instrument: form.source_instrument || null,
				provision: form.provision || null,
				source_document: form.source_document || null,
				conditions: conditions.value.map((row) => ({
					condition_id: row.condition_id,
					kind: row.kind,
					description: row.description,
					procurement_category: row.procurement_category || "",
					minimum_amount: num(row.minimum_amount) || 0,
					maximum_amount: num(row.maximum_amount) || 0,
					cumulative_basis: row.cumulative_basis || "None",
					mandatory: row.mandatory !== false,
					required_evidence: row.required_evidence || "",
					authorisation_actor: row.authorisation_actor || "",
					authorisation_stage: row.authorisation_stage || "",
					statutory_reference: row.statutory_reference || "",
				})),
			});
		} else {
			await procurementSettingsApi.registerScheduleProfileVersion({
				procurement_method: props.current.procurement_method,
				procurement_category: props.current.procurement_category,
				profile_name: form.profile_name,
				procedure: form.procedure || null,
				effective_from: form.effective_from,
				effective_until: form.effective_until || null,
				counting_rule: form.counting_rule,
				estimated_delivery_period_default_days: form.estimated_delivery_period_default_days === "" ? null : Number(form.estimated_delivery_period_default_days),
				verification_status: form.verification_status,
				applicability_basis: form.applicability_basis || null,
				source_instrument: form.source_instrument || null,
				provision: form.provision || null,
				source_document: form.source_document || null,
				milestones: milestones.value.map((row) => ({
					milestone: row.milestone,
					label: row.label,
					sequence: row.sequence,
					applies: row.applies !== false,
					counting_rule: row.counting_rule || form.counting_rule,
					minimum_days: num(row.minimum_days),
					maximum_days: num(row.maximum_days),
					default_days: num(row.default_days),
					basis: row.basis,
					statutory_reference: row.statutory_reference || "",
				})),
			});
		}
		emit("registered");
	});
}
</script>

<template>
	<div class="kt-dialog-backdrop" @click.self="emit('cancel')">
		<div class="kt-dialog kt-blueprint kt-procset-dialog" role="dialog" aria-modal="true" :aria-label="title" data-testid="kt-procset-new-version" @keydown.esc="emit('cancel')">
			<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<p class="kt-confirm-body">{{ __("The current Version stays as it is. The new Version applies from its effective date and supersedes any Version whose period it overlaps.") }}</p>
			<div class="kt-dialog-fields">
				<div v-if="mode === 'schedule'" class="kt-field">
					<label for="kt-nv-name">{{ __("Profile name") }}</label>
					<input id="kt-nv-name" v-model="form.profile_name" class="kt-input" data-testid="kt-nv-profile-name">
				</div>
				<div class="kt-facts-row">
					<div class="kt-field">
						<label for="kt-nv-from">{{ __("Applies from") }}</label>
						<input id="kt-nv-from" ref="field" v-model="form.effective_from" class="kt-input" type="date" data-testid="kt-nv-effective-from">
					</div>
					<div class="kt-field">
						<label for="kt-nv-until">{{ __("Applies until") }}</label>
						<input id="kt-nv-until" v-model="form.effective_until" class="kt-input" type="date" data-testid="kt-nv-effective-until">
					</div>
				</div>
				<div class="kt-field">
					<!-- §8.1 — the same plain source-check vocabulary the rest of
					     the module reads, not the stored model value. -->
					<label for="kt-nv-verification">{{ __("Source check") }}</label>
					<select id="kt-nv-verification" v-model="form.verification_status" class="kt-input" data-testid="kt-nv-verification">
						<option v-for="status in verificationStatuses" :key="status" :value="status">{{ __(sourceCheckLabel(status)) }}</option>
					</select>
					<p class="kt-hint">{{ __("Record Sources verified only with the primary source, provision and document below.") }}</p>
				</div>
				<div class="kt-field">
					<label for="kt-nv-instrument">{{ __("Source instrument") }}</label>
					<input id="kt-nv-instrument" v-model="form.source_instrument" class="kt-input" data-testid="kt-nv-instrument">
				</div>
				<div class="kt-facts-row">
					<div class="kt-field">
						<label for="kt-nv-provision">{{ __("Provision") }}</label>
						<input id="kt-nv-provision" v-model="form.provision" class="kt-input" data-testid="kt-nv-provision">
					</div>
					<div class="kt-field">
						<label for="kt-nv-document">{{ __("Source document") }}</label>
						<input id="kt-nv-document" v-model="form.source_document" class="kt-input" :placeholder="__('File URL, optional')" data-testid="kt-nv-document">
					</div>
				</div>

				<div v-if="mode === 'method'" class="kt-procset-rows" data-testid="kt-nv-conditions">
					<span class="kt-label">{{ __("Eligibility conditions") }}</span>
					<div v-for="row in conditions" :key="row.condition_id" class="kt-procset-row">
						<span class="kt-muted">{{ row.condition_id }} · {{ row.kind }}<template v-if="row.procurement_category"> · {{ row.procurement_category }}</template></span>
						<input v-model="row.description" class="kt-input" :aria-label="__('Condition')">
						<input v-model="row.maximum_amount" class="kt-input kt-procset-num" inputmode="numeric" :aria-label="__('Maximum amount')">
						<input v-model="row.required_evidence" class="kt-input" :placeholder="__('Required evidence')" :aria-label="__('Required evidence')">
					</div>
				</div>
				<div v-else class="kt-procset-rows" data-testid="kt-nv-milestones">
					<span class="kt-label">{{ __("Milestones and periods") }}</span>
					<div v-for="row in milestones" :key="row.milestone" class="kt-procset-row">
						<span class="kt-muted">{{ row.sequence }}. {{ row.label }}</span>
						<input v-model="row.minimum_days" class="kt-input kt-procset-num" inputmode="numeric" :placeholder="__('Min')" :aria-label="__('Minimum days')">
						<input v-model="row.maximum_days" class="kt-input kt-procset-num" inputmode="numeric" :placeholder="__('Max')" :aria-label="__('Maximum days')">
						<input v-model="row.default_days" class="kt-input kt-procset-num" inputmode="numeric" :placeholder="__('Default')" :aria-label="__('Default days')">
						<select v-model="row.basis" class="kt-input" :aria-label="__('Basis')">
							<option value="Statutory">{{ __("Statutory") }}</option>
							<option value="Planning assumption">{{ __("Planning assumption") }}</option>
							<option value="Source-derived">{{ __("Source-derived") }}</option>
						</select>
					</div>
					<div class="kt-field kt-procset-days">
						<label for="kt-nv-delivery">{{ __("Estimated delivery period default (days)") }}</label>
						<input id="kt-nv-delivery" v-model="form.estimated_delivery_period_default_days" class="kt-input" inputmode="numeric" :placeholder="__('Not set')" data-testid="kt-nv-delivery-default">
					</div>
				</div>
				<p v-if="error" class="kt-inline-error" role="alert" data-testid="kt-nv-error">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="emit('cancel')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="!canSave" data-testid="kt-nv-confirm" @click="submit">{{ __("Create new version") }}</button>
			</div>
		</div>
	</div>
</template>
