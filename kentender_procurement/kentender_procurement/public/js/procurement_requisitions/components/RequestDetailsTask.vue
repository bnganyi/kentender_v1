<!-- REQ-DES-03 — Request details (base, COMPLETE, RETURNED, CONTRIBUTOR,
     and the REQ-DES-12 remaining-original, stale and save-validation
     states). The form below is this actor's own draft of the values; the
     server holds the saved Draft, checks every change and says what is
     blocking. -->
<template>
	<div data-testid="req-body-request_details">
		<template v-if="!contributor">
			<div class="req-section" style="margin-bottom: var(--kt-space-4)">
				<div class="kt-label">Approved purchase</div>
				<div class="req-orientation-title">{{ purchase.title }}</div>
				<div class="req-orientation-facts">
					<span>{{ purchase.departments }}</span>
					<span>{{ purchase.available }}</span>
					<span v-if="purchase.method">{{ purchase.method }}</span>
					<span>Reserved for {{ purchase.reserved_for }}</span>
					<span v-if="purchase.county_requirement">County requirement {{ purchase.county_requirement }}</span>
					<span><span class="kt-muted">Plan completion boundary</span> {{ purchase.plan_completion_boundary }}</span>
				</div>
				<p v-if="purchase.business_need" class="req-narrative">{{ purchase.business_need }}</p>
			</div>
			<Disclosure title="Purchase and source details" testid="req-source-details" :start-open="focusSection === 'source_details'" style="margin-bottom: var(--kt-space-8)">
				<div v-for="(row, i) in sourceRows" :key="i" class="kt-meta-row" :style="i ? 'margin-top: 12px' : ''">
					<div v-for="fact in row" :key="fact.label"><span class="kt-label">{{ fact.label }}</span><span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span></div>
				</div>
			</Disclosure>

			<section data-section="request_information" tabindex="-1">
				<CardTitle title="Request information" icon="file" />
				<div class="req-grid-2" style="margin-bottom: var(--kt-space-8)">
					<div class="kt-field">
						<label for="req-title">Requirement title</label>
						<input id="req-title" v-model="form.requirement_title" class="kt-input" :class="{ 'is-invalid': fieldError('requirement_title') }" :disabled="!canShared" data-testid="req-field-title" />
						<span v-if="fieldError('requirement_title')" class="req-field-error">{{ fieldError("requirement_title") }}</span>
					</div>
					<div class="kt-field">
						<label for="req-location">Delivery location</label>
						<select id="req-location" v-model="form.delivery_location" class="kt-input" :class="{ 'is-invalid': fieldError('delivery_location') }" :disabled="!canShared" data-testid="req-field-location">
							<option value="">Select a delivery location</option>
							<option v-for="l in info.locations || []" :key="l.name" :value="l.name">{{ l.address || l.location_name }}</option>
						</select>
						<span v-if="fieldError('delivery_location')" class="req-field-error">{{ fieldError("delivery_location") }}</span>
					</div>
					<div class="kt-field">
						<label for="req-latest">Latest delivery date</label>
						<DateField id="req-latest" v-model="form.latest_delivery_date" :disabled="!canShared" :invalid="!!fieldError('latest_delivery_date')" />
						<span v-if="fieldError('latest_delivery_date')" class="req-field-error">{{ fieldError("latest_delivery_date") }}</span>
					</div>
					<div class="kt-field">
						<label id="req-services-label">Related services required</label>
						<SegYesNo v-model="form.related_services_required" name="req-services" labelledby="req-services-label" :disabled="!canShared" />
					</div>
				</div>
			</section>
		</template>

		<section data-section="amounts" tabindex="-1">
			<CardTitle title="Amounts requested from the approved plan" icon="coins" />
			<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">{{ remainingOnly ? "This request uses only the remaining amount from the original approved purchase." : "The full available amount is selected. Enter a smaller amount only when this requisition covers part of the approved purchase." }}</p>
			<table v-if="remainingOnly" class="kt-table" style="margin-top: var(--kt-space-3)" data-testid="req-remaining-original">
				<thead><tr><th>Approved purchase</th><th class="is-num">Quantity</th><th class="is-num">Value</th></tr></thead>
				<tbody>
					<tr><td>Original</td><td class="is-num">{{ remaining.original.quantity }}</td><td class="is-num">{{ remaining.original.value }}</td></tr>
					<tr><td>Previously used</td><td class="is-num">{{ remaining.used.quantity }}</td><td class="is-num">{{ remaining.used.value }}</td></tr>
					<tr><td style="font-weight: 600">Still available</td><td class="is-num" style="font-weight: 600">{{ remaining.available.quantity }}</td><td class="is-num" style="font-weight: 600">{{ remaining.available.value }}</td></tr>
				</tbody>
			</table>
			<div class="req-has-cards" style="margin-bottom: var(--kt-space-8)">
				<table class="kt-table" data-testid="req-amounts">
					<thead>
						<tr v-if="contributor">
							<th>Department and requirement</th><th class="is-num">Requested quantity</th><th class="is-num">Requested value</th><th>Access</th>
						</tr>
						<tr v-else>
							<th>Department and requirement</th><th class="is-num">Available quantity</th><th class="is-num">Requested quantity</th><th class="is-num">Available value</th><th class="is-num">Requested value</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in view.amounts" :key="row.drawdown_line_id" :class="{ 'is-own': contributor && row.editable }" data-testid="req-amount-row">
							<td><div style="font-weight: 600">{{ row.department }}</div><div class="kt-label">{{ row.requirement }}</div></td>
							<td v-if="!contributor" class="is-num">{{ row.available_quantity }}</td>
							<td class="is-num">
								<template v-if="row.editable && !locked">
									<input v-model="amounts[row.drawdown_line_id].quantity" class="kt-input req-num-input" inputmode="numeric" :aria-label="`Requested quantity for ${row.department}`" data-testid="req-amount-quantity" />
									<div class="kt-label req-field-suffix">Each</div>
								</template>
								<template v-else>{{ row.requested_quantity }}</template>
							</td>
							<td v-if="!contributor" class="is-num">{{ row.available_value }}</td>
							<td class="is-num">
								<template v-if="row.editable && !locked">
									<input v-model="amounts[row.drawdown_line_id].value" class="kt-input req-num-input is-wide" inputmode="decimal" :aria-label="`Requested value for ${row.department} in KES`" data-testid="req-amount-value" />
									<div class="kt-label req-field-suffix">KES</div>
									<button v-if="changed(row)" type="button" class="kt-btn kt-btn-ghost" data-testid="req-use-full" @click="useFull(row)">Use full available amount</button>
								</template>
								<template v-else>{{ row.requested_value }}</template>
								<div v-if="amountError(row)" class="req-field-error">{{ amountError(row) }}</div>
							</td>
							<td v-if="contributor" :class="{ 'kt-muted': !row.editable }">{{ row.editable ? "Editable" : "Read-only" }}</td>
						</tr>
					</tbody>
				</table>
				<div class="req-row-cards">
					<div v-for="row in view.amounts" :key="row.drawdown_line_id" class="req-row-card">
						<div style="font-weight: 600; font-size: 14px">{{ row.department }}</div>
						<div class="kt-label">{{ row.requirement }}</div>
						<dl>
							<dt class="kt-label">Available quantity</dt><dd>{{ row.available_quantity }}</dd>
							<dt class="kt-label">Requested quantity</dt><dd>{{ row.requested_quantity }}</dd>
							<dt class="kt-label">Available value</dt><dd>{{ row.available_value }}</dd>
							<dt class="kt-label">Requested value</dt><dd>{{ row.requested_value }}</dd>
						</dl>
					</div>
				</div>
			</div>
		</section>

		<section data-section="equipment" tabindex="-1">
			<template v-if="items.length">
				<div class="req-register-head" style="align-items: center">
					<CardTitle title="Equipment" icon="monitor" style="margin: 0" />
					<span v-if="spec" class="kt-muted" style="font-size: 13px; display: flex; align-items: center; gap: 10px">
						{{ spec.label }}
						<button v-if="canShared && !locked" type="button" class="kt-btn kt-btn-secondary" data-testid="req-edit-shared" @click="dialog = { kind: 'shared' }">Edit shared details</button>
					</span>
				</div>
				<table class="kt-table" style="margin-top: 12px; font-size: 13px" data-testid="req-equipment">
					<thead><tr><th>Item</th><th>Approved requirement</th><th class="is-num">Quantity</th><th>Intended use</th><th>Delivery</th><th style="white-space: nowrap">Action</th></tr></thead>
					<tbody>
						<tr v-for="item in items" :key="item.requisition_item_id" data-testid="req-equipment-row">
							<td>{{ item.item_name }}</td>
							<td>{{ item.approved_requirement }}</td>
							<td class="is-num">{{ item.quantity }}</td>
							<td>{{ item.intended_use }}</td>
							<td>{{ item.delivery }}</td>
							<td>
								<div v-if="item.editable && !locked" class="req-row-actions">
									<button type="button" class="kt-btn kt-btn-ghost" data-testid="req-edit-item" @click="dialog = { kind: 'item', item }">Edit quantity and use</button>
									<button type="button" class="kt-btn kt-btn-ghost" data-testid="req-remove-item" @click="dialog = { kind: 'remove', item }">Remove</button>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
				<div v-if="canAdd" style="margin-top: 12px">
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="req-add-laptops" @click="dialog = { kind: 'add' }">Add laptop request</button>
				</div>
			</template>
			<template v-else>
				<CardTitle title="Equipment" icon="monitor" />
				<div class="req-empty">
					<div class="req-empty-title">No equipment added.</div>
					<p class="kt-muted" style="font-size: 13px; margin: 6px 0 12px">Add the equipment covered by the requested quantities above.</p>
					<button v-if="canAdd" type="button" class="kt-btn kt-btn-primary" data-testid="req-add-laptops" @click="dialog = { kind: 'add' }">Add laptop request</button>
				</div>
			</template>
		</section>

		<Notice v-if="saveError" tone="warning"><span data-testid="req-save-error">{{ saveError }}</span></Notice>
		<Notice v-if="savedNotice" tone="live"><span data-testid="req-saved">{{ savedNotice }}</span></Notice>

		<div class="req-footer">
			<button type="button" class="kt-btn kt-btn-ghost" @click="ctx.go()">Back to Requisitions</button>
			<div v-if="actions.save" class="req-footer-right">
				<span v-if="!contributor && hint" class="kt-label" data-testid="req-footer-hint">{{ hint }}</span>
				<div class="req-actions">
					<template v-if="contributor">
						<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-save" @click="save()">{{ actions.save_label }}</button>
					</template>
					<template v-else>
						<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" data-testid="req-save" @click="save()">{{ actions.save_label }}</button>
						<button type="button" class="kt-btn" :class="canContinue ? 'kt-btn-primary' : 'kt-btn-secondary'" :disabled="busy || !canContinue" data-testid="req-continue" @click="saveAndContinue">Continue to requirements</button>
					</template>
				</div>
			</div>
		</div>

		<AddLaptopDialog v-if="dialog && (dialog.kind === 'add' || dialog.kind === 'shared')" :view="view" :mode="dialog.kind" @close="dialog = null" />
		<EditItemDialog v-if="dialog && dialog.kind === 'item'" :view="view" :item="dialog.item" @close="dialog = null" />
		<DialogFrame v-if="dialog && dialog.kind === 'remove'" title="Remove this equipment row?" :width="480" :busy="busy" testid="req-remove-dialog" @close="dialog = null">
			<p class="req-dialog-body">{{ dialog.item.item_name }} for {{ dialog.item.department }} ({{ dialog.item.quantity }}) will be removed from this Draft. Requirements that apply only to it are removed with it.</p>
			<Notice v-if="dialogError" tone="critical">{{ dialogError }}</Notice>
			<template #actions>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="dialog = null">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-remove-dialog-confirm" @click="removeItem(dialog.item)">Remove equipment row</button>
			</template>
		</DialogFrame>
		<DialogFrame v-if="dialog && dialog.kind === 'confirm-services'" title="Remove related services?" :width="480" :busy="busy" testid="req-services-dialog" @close="dialog = null">
			<p class="req-dialog-body">This Draft has {{ dialog.count }} related service{{ dialog.count === 1 ? "" : "s" }}. Answering No removes {{ dialog.count === 1 ? "it" : "them" }} from the Draft.</p>
			<template #actions>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="busy" @click="dialog = null">Keep related services</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="busy" data-testid="req-services-dialog-confirm" @click="confirmRemoveServices">Remove related services</button>
			</template>
		</DialogFrame>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useReq } from "../data/context.js";
import CardTitle from "./shared/CardTitle.vue";
import DateField from "./shared/DateField.vue";
import DialogFrame from "./shared/DialogFrame.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import SegYesNo from "./shared/SegYesNo.vue";
import AddLaptopDialog from "./AddLaptopDialog.vue";
import EditItemDialog from "./EditItemDialog.vue";

const props = defineProps({
	view: { type: Object, required: true },
	locked: { type: Boolean, default: false },
	focusSection: { type: String, default: "" },
});
const emit = defineEmits(["continue"]);
const ctx = useReq();

const actions = computed(() => props.view.actions || {});
const contributor = computed(() => props.view.mode === "contributor");
const canShared = computed(() => !!actions.value.edit_shared && !props.locked);
const purchase = computed(() => props.view.purchase || {});
const info = computed(() => props.view.request_information || {});
const items = computed(() => (props.view.equipment || {}).rows || []);
const spec = computed(() => (props.view.equipment || {}).shared_specification);
const remaining = computed(() => props.view.remaining_original || { shown: false });
const remainingOnly = computed(() => !!remaining.value.shown);
const canAdd = computed(() => !props.locked && ((props.view.equipment || {}).add_rows || []).some((r) => r.editable && r.quantity > 0));
const busy = computed(() => ctx.pending.value);

// Purchase and source details: the board's grouping of the six facts.
const sourceRows = computed(() => {
	const facts = purchase.value.source_details || [];
	return [facts.slice(0, 3), facts.slice(3, 4), facts.slice(4, 5), facts.slice(5, 6)].filter((r) => r.length);
});

// This actor's own draft of the values. It is reset from the server only
// when there is nothing unsaved to lose, or when the actor asks for it.
const form = reactive({ requirement_title: "", delivery_location: "", latest_delivery_date: "", related_services_required: false });
const amounts = reactive({});
function resetFromServer() {
	form.requirement_title = info.value.requirement_title || "";
	form.delivery_location = info.value.delivery_location || "";
	form.latest_delivery_date = info.value.latest_delivery_date || "";
	form.related_services_required = !!info.value.related_services_required;
	for (const key of Object.keys(amounts)) delete amounts[key];
	for (const row of props.view.amounts || []) amounts[row.drawdown_line_id] = { quantity: row.requested_quantity_value, value: row.requested_value_value };
}
resetFromServer();

const serverForm = computed(() => ({
	requirement_title: info.value.requirement_title || "",
	delivery_location: info.value.delivery_location || "",
	latest_delivery_date: info.value.latest_delivery_date || "",
	related_services_required: !!info.value.related_services_required,
}));
const dirtyInfo = computed(() => Object.keys(form).some((k) => form[k] !== serverForm.value[k]));
const dirtyAmounts = computed(() =>
	(props.view.amounts || []).some((r) => {
		const a = amounts[r.drawdown_line_id];
		return a && (a.quantity !== r.requested_quantity_value || a.value !== r.requested_value_value);
	})
);
watch(
	() => props.view.header && props.view.header.version_record_version,
	() => {
		if (!dirtyInfo.value && !dirtyAmounts.value) resetFromServer();
		else {
			// Keep what is being typed; pick up rows the server added or dropped.
			for (const row of props.view.amounts || []) {
				if (!amounts[row.drawdown_line_id]) amounts[row.drawdown_line_id] = { quantity: row.requested_quantity_value, value: row.requested_value_value };
			}
		}
	}
);

function changed(row) {
	const a = amounts[row.drawdown_line_id];
	return a && (a.quantity !== row.remaining_quantity_value || a.value !== row.remaining_value_value);
}
function useFull(row) {
	amounts[row.drawdown_line_id] = { quantity: row.remaining_quantity_value, value: row.remaining_value_value };
}

// Refusals from the last save, bound to the field they name.
const lastError = computed(() => {
	const e = ctx.commandError.value;
	return e && (e.label === "save-summary" || e.label === "remove-item") ? e : null;
});
function fieldError(field) {
	const e = lastError.value;
	return e && e.detail && e.detail.fields ? e.detail.fields[field] || "" : "";
}
function amountError(row) {
	const e = lastError.value;
	if (!e || !e.detail) return "";
	if (e.detail.drawdown_line_id === row.drawdown_line_id) return e.message;
	return "";
}
const saveError = computed(() => {
	const e = lastError.value;
	if (!e || e.code === "REQ_STALE_VERSION" || (e.detail && (e.detail.fields || e.detail.requires_confirmation || e.detail.drawdown_line_id))) return "";
	return e.message;
});
const dialogError = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "remove-item" ? ctx.commandError.value.message : ""));

const savedNotice = ref("");
const hint = computed(() => (props.view.footer_hints || {}).request_details || "");
const canContinue = computed(() => !hint.value || dirtyInfo.value || dirtyAmounts.value);

function summaryValues(extra) {
	const values = {};
	if (actions.value.edit_shared) {
		for (const k of Object.keys(form)) if (form[k] !== serverForm.value[k]) values[k] = form[k];
	}
	const lines = (props.view.amounts || [])
		.filter((r) => r.editable)
		.map((r) => ({ drawdown_line_id: r.drawdown_line_id, requested_quantity: String(amounts[r.drawdown_line_id].quantity).trim(), requested_value: String(amounts[r.drawdown_line_id].value).trim() }));
	if (lines.length) values.drawdown_lines = lines;
	return { ...values, ...(extra || {}) };
}

async function save(extra) {
	savedNotice.value = "";
	const done = await ctx.run("save-summary", (key) =>
		ctx.api.saveSummary({
			requisition: props.view.header.requisition,
			summary_values: summaryValues(extra),
			expected_record_version: props.view.header.version_record_version,
			idempotency_key: key,
		})
	);
	const e = ctx.commandError.value;
	if (!done && e && e.detail && e.detail.requires_confirmation === "remove_services") {
		dialog.value = { kind: "confirm-services", count: e.detail.services };
		return false;
	}
	if (done) {
		resetFromServer();
		if (contributor.value) savedNotice.value = "Your changes are saved in the combined requisition.";
	}
	return !!done;
}

async function saveAndContinue() {
	const ok = await save();
	if (ok && !((props.view.footer_hints || {}).request_details || "")) emit("continue");
}

async function confirmRemoveServices() {
	dialog.value = null;
	await save({ confirm_remove_services: true });
}

const dialog = ref(null);
async function removeItem(item) {
	const done = await ctx.run("remove-item", (key) =>
		ctx.api.removeItem({ requisition: props.view.header.requisition, requisition_item_id: item.requisition_item_id, expected_record_version: props.view.package_record_version, idempotency_key: key })
	);
	if (done) dialog.value = null;
}

defineExpose({ resetFromServer });
</script>
