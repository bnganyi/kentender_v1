<!-- REQ-DES-05 — Requirements (REVIEW-REQUIRED base, COMPLETE, validation).
     While the standard package is Review required, the suggested rows are
     this page's own review copy: Use / Edit / Clear change only the copy, and
     "Use selected requirements" sends the whole visible selection once
     (§10.2 ApplySelectedRequirementPackage). Confirmed rows are saved one at a
     time. The server validates everything and says what still blocks. -->
<template>
	<div data-testid="req-body-requirements">
		<Notice v-if="issue" tone="warning"><a href="#" data-testid="req-requirements-issue" @click.stop.prevent="focus(issueSection)">{{ issue }}</a></Notice>

		<div class="req-workbench" :class="{ 'is-reviewed': !reviewRequired }" data-section="technical" tabindex="-1">
			<div v-if="reviewRequired" class="req-workbench-head">
				<div>
					<CardTitle title="Standard laptop requirements to review" icon="sliders" style="margin-bottom: 6px" />
					<p class="kt-muted" style="font-size: 13px; margin: 0; max-width: 66ch">These suggested requirements are not confirmed until you use the action below. Review every value, change what is necessary and clear any suggestion that does not apply.</p>
				</div>
				<span class="kt-status is-attention" data-testid="req-review-state">Review required</span>
			</div>
			<div v-else class="req-register-head" style="margin-bottom: var(--kt-space-3)">
				<span class="req-subhead">Laptop requirements</span>
				<span class="kt-status is-live" data-testid="req-review-state">Reviewed</span>
			</div>

			<CardTitle title="Technical requirements" icon="monitor" class="req-register-title">
				<span class="kt-muted req-title-note">· Target: All equipment</span>
			</CardTitle>
			<template v-for="group in groups" :key="group.group">
				<div class="kt-label req-group-label">{{ group.group }}</div>
				<table class="table" style="margin-bottom: var(--kt-space-4)" :data-testid="`req-technical-${group.group}`">
					<thead>
						<tr><th v-if="reviewRequired">Use</th><th>Requirement</th><th>Minimum or required value</th><th>Unit</th><th>Action</th></tr>
					</thead>
					<tbody>
						<tr v-for="row in group.rows" :key="row.technical_requirement_id" :class="{ 'is-cleared': isProposed(row) && !techCopy[row.technical_requirement_id].selected }" data-testid="req-technical-row">
							<td v-if="reviewRequired">
								<label v-if="isProposed(row)" class="kt-checkbox"><input v-model="techCopy[row.technical_requirement_id].selected" type="checkbox" :disabled="!canEdit" :aria-label="`Use ${row.label}`" /><span class="box"></span></label>
							</td>
							<td>{{ row.label }}<div class="kt-muted req-comparison">{{ row.comparison }}</div></td>
							<td>{{ displayOf(row) }}</td>
							<td>{{ row.unit }}</td>
							<td>
								<div v-if="canEdit" class="req-row-actions">
									<button type="button" class="btn btn-ghost" data-testid="req-technical-edit" @click="dialog = { kind: 'technical', row }">Edit</button>
									<button v-if="isProposed(row)" type="button" class="btn btn-ghost" data-testid="req-technical-clear" @click="techCopy[row.technical_requirement_id].selected = !techCopy[row.technical_requirement_id].selected">{{ techCopy[row.technical_requirement_id].selected ? "Clear" : "Use" }}</button>
									<button v-else type="button" class="btn btn-ghost" data-testid="req-technical-remove" @click="removeRow('technical', row)">Remove</button>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</template>

			<section data-section="warranty_support" tabindex="-1">
				<CardTitle title="Warranty and support" icon="sliders" class="req-register-title" />
				<div class="req-grid-2" style="margin-bottom: var(--kt-space-6)">
					<div class="field">
						<label for="req-warranty">Minimum warranty</label>
						<input id="req-warranty" v-model="support.minimum_warranty_months" class="input" inputmode="numeric" :class="{ 'is-invalid': supportError('minimum_warranty_months') }" :disabled="!canEdit" data-testid="req-support-warranty" />
						<div class="kt-field-hint req-field-suffix">months</div>
						<span v-if="supportError('minimum_warranty_months')" class="req-field-error">{{ supportError("minimum_warranty_months") }}</span>
					</div>
					<div class="field">
						<label id="req-onsite-label">On-site support required</label>
						<SegYesNo v-model="support.onsite_support_required" name="req-onsite" labelledby="req-onsite-label" :disabled="!canEdit" />
					</div>
					<div class="field">
						<label for="req-response">Maximum support response</label>
						<input id="req-response" v-model="support.maximum_support_response_hours" class="input" inputmode="numeric" :class="{ 'is-invalid': supportError('maximum_support_response_hours') }" :disabled="!canEdit" />
						<div class="kt-field-hint req-field-suffix">hours</div>
						<span v-if="supportError('maximum_support_response_hours')" class="req-field-error">{{ supportError("maximum_support_response_hours") }}</span>
					</div>
					<div class="field">
						<label id="req-manufacturer-label">Manufacturer support required</label>
						<SegYesNo v-model="support.manufacturer_support_required" name="req-manufacturer" labelledby="req-manufacturer-label" :disabled="!canEdit" />
					</div>
					<div class="field">
						<label for="req-service-location">Service location constraint</label>
						<select id="req-service-location" v-model="support.service_location_constraint" class="input" :disabled="!canEdit">
							<option v-for="l in catalogue.service_locations || []" :key="l" :value="l">{{ l }}</option>
						</select>
					</div>
					<div class="field">
						<label for="req-support-description">Support description</label>
						<textarea id="req-support-description" v-model="support.support_description" class="input" rows="2" :disabled="!canEdit"></textarea>
					</div>
				</div>
			</section>

			<section data-section="acceptance" tabindex="-1">
				<CardTitle title="Acceptance checks" icon="check-square" class="req-register-title" />
				<div class="req-has-cards">
					<table class="table" data-testid="req-acceptance">
						<thead><tr><th v-if="reviewRequired">Use</th><th>Check</th><th>Applies to</th><th>Pass condition</th><th>Evidence</th><th>Action</th></tr></thead>
						<tbody>
							<tr v-for="row in acceptance" :key="row.acceptance_requirement_id" :class="{ 'is-cleared': isProposed(row) && !accCopy[row.acceptance_requirement_id].selected }" data-testid="req-acceptance-row">
								<td v-if="reviewRequired">
									<label v-if="isProposed(row)" class="kt-checkbox"><input v-model="accCopy[row.acceptance_requirement_id].selected" type="checkbox" :disabled="!canEdit" :aria-label="`Use ${row.check_type}`" /><span class="box"></span></label>
								</td>
								<td>{{ accOf(row).check_type }}</td>
								<td>{{ row.applies_to }}</td>
								<td>{{ accOf(row).pass_condition }}</td>
								<td>{{ accOf(row).evidence_type === "Other stated record" ? accOf(row).other_evidence_name : accOf(row).evidence_type }}</td>
								<td>
									<div v-if="canEdit" class="req-row-actions">
										<button type="button" class="btn btn-ghost" data-testid="req-acceptance-edit" @click="dialog = { kind: 'acceptance', row }">Edit</button>
										<button v-if="isProposed(row)" type="button" class="btn btn-ghost" data-testid="req-acceptance-clear" @click="accCopy[row.acceptance_requirement_id].selected = !accCopy[row.acceptance_requirement_id].selected">{{ accCopy[row.acceptance_requirement_id].selected ? "Clear" : "Use" }}</button>
										<button v-else type="button" class="btn btn-ghost" data-testid="req-acceptance-remove" @click="removeRow('acceptance', row)">Remove</button>
									</div>
								</td>
							</tr>
						</tbody>
					</table>
					<div class="req-row-cards">
						<div v-for="row in acceptance" :key="row.acceptance_requirement_id" class="req-row-card">
							<div style="font-weight: 600; font-size: 14px">{{ accOf(row).check_type }}</div>
							<dl>
								<dt class="kt-label">Applies to</dt><dd>{{ row.applies_to }}</dd>
								<dt class="kt-label">Pass condition</dt><dd>{{ accOf(row).pass_condition }}</dd>
								<dt class="kt-label">Evidence</dt><dd>{{ accOf(row).evidence_type }}</dd>
							</dl>
						</div>
					</div>
				</div>
				<div v-if="canEdit && !reviewRequired" style="margin-top: var(--kt-space-3)">
					<button type="button" class="btn btn-secondary" data-testid="req-acceptance-add" @click="dialog = { kind: 'acceptance', row: null }">Add acceptance check</button>
				</div>
			</section>

			<Notice v-if="packageError" tone="warning"><span data-testid="req-package-error">{{ packageError }}</span></Notice>
			<div v-if="reviewRequired && canEdit" class="req-footer" style="justify-content: flex-end; margin-top: var(--kt-space-4)">
				<div class="req-actions">
					<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-reset-standard" @click="reset">Reset standard values</button>
					<button type="button" class="btn btn-primary" :disabled="busy || !canApply" data-testid="req-use-selected" @click="apply">Use selected requirements</button>
				</div>
			</div>
		</div>

		<section class="req-section" data-section="services" tabindex="-1">
			<CardTitle title="Related services" icon="wrench" />
			<div v-if="!servicesRequired" class="req-compact-row" style="justify-content: space-between; margin-bottom: var(--kt-space-8)">
				<span class="kt-muted" style="font-size: 13px">No related services requested.</span>
				<button v-if="canEdit" type="button" class="btn btn-secondary" data-testid="req-services-change" @click="$emit('back')">Change answer</button>
			</div>
			<template v-else>
				<table v-if="services.length" class="table" data-testid="req-services">
					<thead><tr><th>Service</th><th>Applies to</th><th>Required result</th><th>Quantity or coverage</th><th>Completion</th><th>Action</th></tr></thead>
					<tbody>
						<tr v-for="s in services" :key="s.service_requirement_id" data-testid="req-service-row">
							<td>{{ s.service_type }}</td><td>{{ s.applies_to }}</td><td>{{ s.required_result }}</td><td>{{ s.quantity_or_coverage }}</td><td>{{ s.completion_date_label }}</td>
							<td><div v-if="canEdit" class="req-row-actions"><button type="button" class="btn btn-ghost" @click="dialog = { kind: 'service', row: s }">Edit</button><button type="button" class="btn btn-ghost" @click="removeRow('service', s)">Remove</button></div></td>
						</tr>
					</tbody>
				</table>
				<p v-else class="kt-muted" style="font-size: 13px">Add each related service the supplier must perform.</p>
				<div v-if="canEdit" style="margin: var(--kt-space-3) 0 var(--kt-space-8)"><button type="button" class="btn btn-secondary" data-testid="req-service-add" @click="dialog = { kind: 'service', row: null }">Add service</button></div>
			</template>
		</section>

		<section data-section="supporting_materials" tabindex="-1">
			<CardTitle title="Supporting materials" icon="paperclip" />
			<table v-if="materials.length" class="table" data-testid="req-materials">
				<thead><tr><th>Title</th><th>Type</th><th>Treatment</th><th>Version</th><th>Action</th></tr></thead>
				<tbody>
					<tr v-for="m in materials" :key="m.supporting_material_id" data-testid="req-material-row">
						<td>{{ m.title }}</td><td>{{ m.document_type }}</td><td>{{ m.treatment }}</td><td>{{ m.document_version }}</td>
						<td><button v-if="canEdit" type="button" class="btn btn-ghost" @click="removeRow('material', m)">Remove</button></td>
					</tr>
				</tbody>
			</table>
			<div v-else class="req-empty">
				<div class="req-empty-title">No supporting materials added.</div>
				<p class="kt-muted" style="font-size: 13px; margin: 6px 0 12px">Files may support a structured requirement but cannot replace it.</p>
				<button v-if="canEdit" type="button" class="btn btn-secondary" data-testid="req-material-add" @click="dialog = { kind: 'material' }">Add supporting material</button>
			</div>
			<div v-if="materials.length && canEdit" style="margin-top: var(--kt-space-3)"><button type="button" class="btn btn-secondary" data-testid="req-material-add" @click="dialog = { kind: 'material' }">Add supporting material</button></div>
		</section>

		<div class="req-footer">
			<button type="button" class="btn btn-ghost" @click="$emit('back')">Back to request details</button>
			<div v-if="canEdit" class="req-footer-right">
				<span v-if="hint" class="kt-label" data-testid="req-footer-hint">{{ hint }}</span>
				<div class="req-actions">
					<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-save" @click="saveDraft">Save draft</button>
					<button type="button" class="btn" :class="canContinue ? 'btn-primary' : 'btn-secondary'" :disabled="busy || !canContinue" data-testid="req-continue" @click="saveAndContinue">Continue to review</button>
				</div>
			</div>
		</div>

		<TechnicalRowDialog
			v-if="dialog && dialog.kind === 'technical'"
			:view="view"
			:row="dialog.row"
			:local="isProposed(dialog.row)"
			:value="isProposed(dialog.row) ? techCopy[dialog.row.technical_requirement_id].stored : null"
			@local="(v) => setTechnical(dialog.row, v)"
			@close="dialog = null"
		/>
		<AcceptanceRowDialog
			v-if="dialog && dialog.kind === 'acceptance'"
			:view="view"
			:row="dialog.row ? accOf(dialog.row) : null"
			:local="!!dialog.row && isProposed(dialog.row)"
			@local="(v) => Object.assign(accCopy[dialog.row.acceptance_requirement_id], v)"
			@close="dialog = null"
		/>
		<ServiceDialog v-if="dialog && dialog.kind === 'service'" :view="view" :row="dialog.row" @close="dialog = null" />
		<MaterialDialog v-if="dialog && dialog.kind === 'material'" :view="view" @close="dialog = null" />
	</div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import { useReq } from "../data/context.js";
import CardTitle from "./shared/CardTitle.vue";
import Notice from "./shared/Notice.vue";
import SegYesNo from "./shared/SegYesNo.vue";
import AcceptanceRowDialog from "./AcceptanceRowDialog.vue";
import MaterialDialog from "./MaterialDialog.vue";
import ServiceDialog from "./ServiceDialog.vue";
import TechnicalRowDialog from "./TechnicalRowDialog.vue";

const props = defineProps({ view: { type: Object, required: true }, locked: { type: Boolean, default: false }, focusSection: { type: String, default: "" } });
const emit = defineEmits(["continue", "back"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);

const req = computed(() => props.view.requirements || {});
const catalogue = computed(() => props.view.catalogue || {});
const canEdit = computed(() => !!(props.view.actions || {}).edit_shared && !props.locked);
const reviewRequired = computed(() => req.value.review_state === "Review required");
const groups = computed(() => req.value.technical_groups || []);
const acceptance = computed(() => req.value.acceptance || []);
const services = computed(() => req.value.services || []);
const materials = computed(() => req.value.materials || []);
const servicesRequired = computed(() => !!(props.view.request_information || {}).related_services_required);
const isProposed = (row) => row && row.state === "Proposed";

// This page's review copy of the suggested rows and the support values.
const techCopy = reactive({});
const accCopy = reactive({});
const support = reactive({});
function rawOf(value) {
	if (!value) return "";
	if (value.ports) return value.ports.map((p) => ({ port_type: p.port_type, minimum_count: String(p.minimum_count) }));
	if (value.values) return [...value.values];
	return value.value === undefined ? "" : value.value;
}
function supportFromServer() {
	const s = req.value.support || {};
	return {
		minimum_warranty_months: s.minimum_warranty_months == null ? "" : String(s.minimum_warranty_months),
		onsite_support_required: !!s.onsite_support_required,
		maximum_support_response_hours: s.maximum_support_response_hours == null ? "" : String(s.maximum_support_response_hours),
		manufacturer_support_required: !!s.manufacturer_support_required,
		service_location_constraint: s.service_location_constraint || "None",
		support_description: s.support_description || "",
	};
}
function resetFromServer() {
	for (const k of Object.keys(techCopy)) delete techCopy[k];
	for (const k of Object.keys(accCopy)) delete accCopy[k];
	for (const g of groups.value) {
		for (const row of g.rows) techCopy[row.technical_requirement_id] = { selected: true, raw: rawOf(row.value), stored: row.value, edited: false };
	}
	for (const row of acceptance.value) {
		accCopy[row.acceptance_requirement_id] = { selected: true, check_type: row.check_type, pass_condition: row.pass_condition, evidence_type: row.evidence_type, other_evidence_name: row.other_evidence_name || "", applies_to_scope: row.applies_to_scope, applies_to_id: row.applies_to_id || "" };
	}
	Object.assign(support, supportFromServer());
}
resetFromServer();

const dirty = computed(() => {
	const server = supportFromServer();
	if (Object.keys(server).some((k) => server[k] !== support[k])) return true;
	return Object.values(techCopy).some((t) => t.edited || !t.selected) || Object.values(accCopy).some((a) => !a.selected);
});
watch(
	() => props.view.package_record_version,
	() => {
		if (!dirty.value) resetFromServer();
	}
);

function setTechnical(row, value) {
	Object.assign(techCopy[row.technical_requirement_id], { raw: value.raw, stored: value.stored, edited: true });
}
function displayOf(row) {
	const copy = techCopy[row.technical_requirement_id];
	if (!copy || !copy.edited) return row.display;
	const v = copy.stored || {};
	if (v.ports) return v.ports.map((p) => `${p.port_type} ×${p.minimum_count}`).join("; ");
	if (v.values) return v.values.join(" and ");
	return String(v.value);
}
function accOf(row) {
	return accCopy[row.acceptance_requirement_id] || row;
}

function supportPayload() {
	const n = (v) => (String(v).trim() === "" ? null : String(v).trim());
	return {
		minimum_warranty_months: n(support.minimum_warranty_months),
		onsite_support_required: support.onsite_support_required,
		maximum_support_response_hours: support.onsite_support_required ? n(support.maximum_support_response_hours) : null,
		manufacturer_support_required: support.manufacturer_support_required,
		service_location_constraint: support.service_location_constraint,
		support_description: support.support_description,
	};
}
function proposalPayload() {
	const technical = [];
	for (const g of groups.value) {
		for (const row of g.rows.filter(isProposed)) {
			const c = techCopy[row.technical_requirement_id];
			technical.push({ technical_requirement_id: row.technical_requirement_id, characteristic_key: row.characteristic_key, value: c.raw, other_value: row.other_value || "", selected: c.selected, applies_to_scope: row.applies_to_scope, applies_to_id: row.applies_to_id || "" });
		}
	}
	const acceptanceRows = acceptance.value.filter(isProposed).map((row) => ({ acceptance_requirement_id: row.acceptance_requirement_id, ...accCopy[row.acceptance_requirement_id] }));
	return {
		requisition: props.view.header.requisition, profile_key: req.value.profile_key, profile_version: req.value.profile_version, proposal_digest: req.value.proposal_digest,
		technical_rows: technical, acceptance_rows: acceptanceRows, support_values: supportPayload(), expected_record_version: props.view.package_record_version,
	};
}

const selectedAcceptance = computed(() => acceptance.value.filter((r) => !isProposed(r) || accCopy[r.acceptance_requirement_id].selected).length);
const canApply = computed(() => selectedAcceptance.value > 0 && String(support.minimum_warranty_months).trim() !== "");

const LABELS = ["apply-package", "save-proposal", "reset-package", "save-support", "remove-row"];
const error = computed(() => (ctx.commandError.value && LABELS.includes(ctx.commandError.value.label) ? ctx.commandError.value : null));
function supportError(field) {
	return (error.value && error.value.detail && error.value.detail.fields && error.value.detail.fields[field]) || "";
}
const packageError = computed(() => (error.value && !(error.value.detail && error.value.detail.fields && Object.keys(error.value.detail.fields).some((f) => f in support)) ? error.value.message : ""));

// The exact issue above the affected section (§13.6 validation variant).
const blocking = computed(() => (props.view.findings || []).filter((f) => f.severity === "Blocking" && f.task === "requirements"));
const issue = computed(() => {
	if (reviewRequired.value) return "Review the standard laptop requirements before continuing.";
	return blocking.value.length ? blocking.value[0].message : "";
});
const issueSection = computed(() => (reviewRequired.value ? "technical" : (blocking.value[0] || {}).section || "technical"));
const hint = computed(() => (props.view.footer_hints || {}).requirements || "");
const canContinue = computed(() => !hint.value);

function focus(section) {
	nextTick(() => {
		const el = document.querySelector(`[data-section="${section}"]`);
		if (el) {
			el.scrollIntoView({ block: "start" });
			el.focus({ preventScroll: true });
		}
	});
}
if (props.focusSection) focus(props.focusSection);

async function apply() {
	const done = await ctx.run("apply-package", (key) => ctx.api.applyPackage({ ...proposalPayload(), idempotency_key: key }));
	if (done) resetFromServer();
}
async function reset() {
	const done = await ctx.run("reset-package", (key) => ctx.api.resetStandardValues({ requisition: props.view.header.requisition, expected_record_version: props.view.package_record_version, idempotency_key: key }));
	if (done) resetFromServer();
}
async function saveDraft() {
	const done = reviewRequired.value
		? await ctx.run("save-proposal", (key) => ctx.api.saveProposalDraft({ ...proposalPayload(), idempotency_key: key }))
		: await ctx.run("save-support", (key) => ctx.api.saveWarrantyAndSupport({ requisition: props.view.header.requisition, warranty_values: supportPayload(), expected_record_version: props.view.package_record_version, idempotency_key: key }));
	if (done) resetFromServer();
	return !!done;
}
async function saveAndContinue() {
	const server = supportFromServer();
	const supportDirty = Object.keys(server).some((k) => server[k] !== support[k]);
	if (supportDirty && !(await saveDraft())) return;
	if (!((props.view.footer_hints || {}).requirements || "")) emit("continue");
}

const REMOVE = {
	technical: (row, key) => ctx.api.removeTechnical({ requisition: props.view.header.requisition, technical_requirement_id: row.technical_requirement_id, expected_record_version: props.view.package_record_version, idempotency_key: key }),
	acceptance: (row, key) => ctx.api.removeAcceptance({ requisition: props.view.header.requisition, acceptance_requirement_id: row.acceptance_requirement_id, expected_record_version: props.view.package_record_version, idempotency_key: key }),
	service: (row, key) => ctx.api.removeService({ requisition: props.view.header.requisition, service_requirement_id: row.service_requirement_id, expected_record_version: props.view.package_record_version, idempotency_key: key }),
	material: (row, key) => ctx.api.removeMaterial({ requisition: props.view.header.requisition, supporting_material_id: row.supporting_material_id, expected_record_version: props.view.package_record_version, idempotency_key: key }),
};
async function removeRow(kind, row) {
	await ctx.run("remove-row", (key) => REMOVE[kind](row, key));
}

const dialog = ref(null);
defineExpose({ resetFromServer });
</script>
