<!-- REQ-DES-03 — Request details (base, COMPLETE, PARTIAL, RETURNED,
     CONTRIBUTOR, and the REQ-DES-12 remaining-original, stale and
     save-validation states), REQ-CHG-001 v1.15 §13.4. Items come first: the
     quantity is typed once, on the item rows. Request summary then shows what
     the items request (read-only) beside the one amount the requester enters,
     the estimated total cost for each approved requirement. The form below is
     this actor's own draft of the values; the server holds the saved Draft,
     checks every change and says what is blocking, so the footer hint always
     refers to the saved Draft and an unsaved change is marked as unsaved. -->
<template>
	<div data-testid="req-body-request_details">
		<AttentionPanel :items="attention" :stale="dirty && !contributor" @go="goTo" />
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
					<div class="field">
						<label for="req-title">Requirement title</label>
						<input id="req-title" v-model="form.requirement_title" class="input" :class="{ 'is-invalid': fieldError('requirement_title') }" :disabled="!canShared" data-testid="req-field-title" />
						<span v-if="fieldError('requirement_title')" class="req-field-error">{{ fieldError("requirement_title") }}</span>
					</div>
					<div class="field">
						<label for="req-location">Delivery location</label>
						<select id="req-location" v-model="form.delivery_location" class="input" :class="{ 'is-invalid': fieldError('delivery_location') }" :disabled="!canShared" data-testid="req-field-location">
							<option value="">Select a delivery location</option>
							<option v-for="l in info.locations || []" :key="l.name" :value="l.name">{{ l.address || l.location_name }}</option>
						</select>
						<span v-if="fieldError('delivery_location')" class="req-field-error">{{ fieldError("delivery_location") }}</span>
					</div>
					<div class="field">
						<label for="req-latest">Latest delivery date</label>
						<DateField id="req-latest" v-model="form.latest_delivery_date" :disabled="!canShared" :invalid="!!fieldError('latest_delivery_date')" />
						<span v-if="fieldError('latest_delivery_date')" class="req-field-error">{{ fieldError("latest_delivery_date") }}</span>
					</div>
					<div class="field">
						<label id="req-services-label">Related services required</label>
						<SegYesNo v-model="form.related_services_required" name="req-services" labelledby="req-services-label" :disabled="!canShared" />
					</div>
				</div>
			</section>
		</template>

		<section data-section="equipment" tabindex="-1" style="margin-bottom: var(--kt-space-8)">
			<CardTitle title="Items" icon="monitor" />
			<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">Add each item and enter its quantity here. You enter a quantity only once.</p>
			<template v-if="groups.length">
				<div v-for="group in groups" :key="group.group_id" class="req-item-group" data-testid="req-item-group">
					<div class="req-item-group-head">
						<div>
							<div class="req-item-group-title" data-testid="req-group-title">{{ group.item_name }}<span class="kt-label" style="margin-left: 8px">{{ group.equipment_category }}</span></div>
							<div class="req-item-group-facts">
								<span v-if="group.delivery">{{ group.delivery }}</span>
								<span>{{ group.rows.length }} approved requirement{{ group.rows.length === 1 ? "" : "s" }}</span>
							</div>
						</div>
						<button v-if="canShared && !locked" type="button" class="btn btn-secondary" data-testid="req-edit-shared" @click="dialog = { kind: 'shared', group }">Edit shared details</button>
					</div>
					<table class="table" style="margin-top: 4px; font-size: 13px" data-testid="req-equipment">
						<thead><tr><th>Approved requirement</th><th class="is-num">Quantity</th><th>Intended use</th><th style="white-space: nowrap">Action</th></tr></thead>
						<tbody>
							<tr v-for="item in group.rows" :key="item.requisition_item_id" :class="{ 'is-flagged': flaggedItems.has(item.requisition_item_id) }" :data-item="item.requisition_item_id" data-testid="req-equipment-row">
								<td>
									{{ item.approved_requirement }}
									<div v-if="flaggedItems.has(item.requisition_item_id)"><span class="kt-status is-attention req-flag" data-testid="req-item-flag">Needs attention</span></div>
								</td>
								<td class="is-num">{{ item.quantity }}</td>
								<td>{{ item.intended_use }}</td>
								<td>
									<div v-if="item.editable && !locked" class="req-row-actions">
										<button type="button" class="btn btn-ghost" data-testid="req-edit-item" @click="dialog = { kind: 'item', item }">Edit quantity and use</button>
										<button type="button" class="btn btn-ghost" data-testid="req-remove-item" @click="dialog = { kind: 'remove', item }">Remove</button>
									</div>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<div v-if="canAdd" style="margin-top: 12px">
					<button type="button" class="btn btn-secondary" data-testid="req-add-item" @click="dialog = { kind: 'add' }">Add item</button>
				</div>
			</template>
			<div v-else class="req-empty">
				<div class="req-empty-title">No items added.</div>
				<p class="kt-muted" style="font-size: 13px; margin: 6px 0 12px">Add the items this requisition covers.</p>
				<button v-if="canAdd" type="button" class="btn btn-primary" data-testid="req-add-item" @click="dialog = { kind: 'add' }">Add item</button>
			</div>
		</section>

		<section data-section="amounts" tabindex="-1">
			<CardTitle title="Request summary" icon="coins" />
			<template v-if="remainingOnly">
				<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">This request uses only the remaining amount from the original approved purchase.</p>
				<table class="table" style="margin-top: var(--kt-space-3)" data-testid="req-remaining-original">
					<thead><tr><th>Approved purchase</th><th class="is-num">Quantity</th><th class="is-num">Value</th></tr></thead>
					<tbody>
						<tr><td>Original</td><td class="is-num">{{ remaining.original.quantity }}</td><td class="is-num">{{ remaining.original.value }}</td></tr>
						<tr><td>Previously used</td><td class="is-num">{{ remaining.used.quantity }}</td><td class="is-num">{{ remaining.used.value }}</td></tr>
						<tr><td style="font-weight: 600">Still available</td><td class="is-num" style="font-weight: 600">{{ remaining.available.quantity }}</td><td class="is-num" style="font-weight: 600">{{ remaining.available.value }}</td></tr>
					</tbody>
				</table>
			</template>
			<div class="req-has-cards" style="margin-bottom: var(--kt-space-8)">
				<table class="table" data-testid="req-amounts">
					<thead>
						<tr v-if="contributor">
							<th>Department and requirement</th><th class="is-num">Requested quantity</th><th class="is-num">Estimated total cost</th><th>Access</th>
						</tr>
						<tr v-else>
							<th>Department and requirement</th><th class="is-num">Available quantity</th><th class="is-num">Requested quantity</th><th class="is-num">Available value</th><th class="is-num">Estimated total cost</th><th class="is-num">Still available after this request</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in view.amounts" :key="row.drawdown_line_id" :class="{ 'is-own': contributor && row.editable, 'is-flagged': flaggedLines.has(row.drawdown_line_id) }" :data-line="row.drawdown_line_id" data-testid="req-amount-row">
							<td>
								<div style="font-weight: 600">{{ row.department }}</div>
								<div class="kt-label">{{ row.requirement }}</div>
								<span v-if="row.needs_review" class="kt-status is-attention" data-testid="req-review-required">Review required</span>
								<span v-else-if="flaggedLines.has(row.drawdown_line_id)" class="kt-status is-attention req-flag" data-testid="req-line-flag">Needs attention</span>
							</td>
							<td v-if="!contributor" class="is-num">{{ row.available_quantity }}</td>
							<td class="is-num" data-testid="req-requested-quantity">{{ row.requested_quantity }}</td>
							<td v-if="!contributor" class="is-num">{{ row.available_value }}</td>
							<td class="is-num">
								<template v-if="row.editable && !locked">
									<input v-model="amounts[row.drawdown_line_id].value" class="input req-num-input is-wide" :class="{ 'is-invalid': amountError(row) }" inputmode="decimal" placeholder="0.00" :aria-label="`Estimated total cost for ${row.department} in KES`" data-testid="req-amount-value" @blur="onAmountBlur(row)" />
									<div class="kt-label req-field-suffix">Up to {{ row.available_value }}</div>
								</template>
								<template v-else>{{ row.requested_value || "Not entered" }}</template>
								<div v-if="amountError(row)" class="req-field-error" data-testid="req-amount-error">{{ amountError(row) }}</div>
							</td>
							<td v-if="!contributor" class="is-num">{{ row.after_quantity }} · {{ row.after_value }}</td>
							<td v-if="contributor" :class="{ 'kt-muted': !row.editable }">{{ row.editable ? "Editable" : "Read-only" }}</td>
						</tr>
					</tbody>
				</table>
				<div class="req-row-cards">
					<div v-for="row in view.amounts" :key="row.drawdown_line_id" class="req-row-card" :class="{ 'is-flagged': flaggedLines.has(row.drawdown_line_id) }" :data-line="row.drawdown_line_id">
						<div style="font-weight: 600; font-size: 14px">{{ row.department }}</div>
						<div class="kt-label">{{ row.requirement }}</div>
						<dl>
							<dt class="kt-label">Available quantity</dt><dd>{{ row.available_quantity }}</dd>
							<dt class="kt-label">Requested quantity</dt><dd>{{ row.requested_quantity }}</dd>
							<dt class="kt-label">Available value</dt><dd>{{ row.available_value }}</dd>
							<dt class="kt-label">Estimated total cost</dt>
						<dd v-if="row.editable && !locked">
							<input v-model="amounts[row.drawdown_line_id].value" class="input req-num-input is-wide" :class="{ 'is-invalid': amountError(row) }" inputmode="decimal" placeholder="0.00" :aria-label="`Estimated total cost for ${row.department} in KES`" data-testid="req-amount-value-card" @blur="onAmountBlur(row)" />
							<div class="kt-label req-field-suffix">Up to {{ row.available_value }}</div>
							<div v-if="amountError(row)" class="req-field-error" data-testid="req-amount-error-card">{{ amountError(row) }}</div>
						</dd>
						<dd v-else>{{ row.requested_value || "Not entered" }}</dd>
							<dt class="kt-label">Still available after this request</dt><dd>{{ row.after_quantity }} · {{ row.after_value }}</dd>
						</dl>
					</div>
				</div>
			</div>
		</section>

		<Notice v-if="savedNotice" tone="live"><span data-testid="req-saved">{{ savedNotice }}</span></Notice>

		<div class="req-footer">
			<button type="button" class="btn btn-ghost" @click="ctx.go()">Back to Requisitions</button>
			<div v-if="actions.save" class="req-footer-right">
				<span v-if="footerStatus" class="req-footer-status" :class="{ 'is-unsaved': footerStatus.state === 'unsaved' }" :data-state="footerStatus.state" data-testid="req-footer-status" role="status">{{ footerStatus.text }}</span>
				<div class="req-actions">
					<template v-if="contributor">
						<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-save" @click="save()">{{ actions.save_label }}</button>
					</template>
					<template v-else>
						<button type="button" class="btn btn-secondary" :disabled="busy" data-testid="req-save" @click="save()">{{ actions.save_label }}</button>
						<button type="button" class="btn" :class="canContinue ? 'btn-primary' : 'btn-secondary'" :disabled="busy || !canContinue" data-testid="req-continue" @click="saveAndContinue">Continue to requirements</button>
					</template>
				</div>
			</div>
		</div>

		<AddItemDialog v-if="dialog && (dialog.kind === 'add' || dialog.kind === 'shared')" :view="view" :mode="dialog.kind" :group="dialog.group" :draft="draft" @added="itemsAdded" @close="dialog = null" />
		<EditItemDialog v-if="dialog && dialog.kind === 'item'" :view="view" :item="dialog.item" @close="dialog = null" />
		<DialogFrame v-if="dialog && dialog.kind === 'remove'" title="Remove this item?" :width="480" :busy="busy" testid="req-remove-dialog" @close="dialog = null">
			<p class="req-dialog-body">{{ dialog.item.item_name }} for {{ dialog.item.department }} ({{ dialog.item.quantity }}) will be removed from this Draft. Requirements that apply only to it are removed with it.</p>
			<Notice v-if="dialogError" tone="critical">{{ dialogError }}</Notice>
			<template #actions>
				<button type="button" class="btn btn-secondary" :disabled="busy" @click="dialog = null">Cancel</button>
				<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-remove-dialog-confirm" @click="removeItem(dialog.item)">Remove item</button>
			</template>
		</DialogFrame>
		<DialogFrame v-if="dialog && dialog.kind === 'confirm-services'" title="Remove related services?" :width="480" :busy="busy" testid="req-services-dialog" @close="dialog = null">
			<p class="req-dialog-body">This Draft has {{ dialog.count }} related service{{ dialog.count === 1 ? "" : "s" }}. Answering No removes {{ dialog.count === 1 ? "it" : "them" }} from the Draft.</p>
			<template #actions>
				<button type="button" class="btn btn-secondary" :disabled="busy" @click="dialog = null">Keep related services</button>
				<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-services-dialog-confirm" @click="confirmRemoveServices">Remove related services</button>
			</template>
		</DialogFrame>
	</div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from "vue";
import { useReq } from "../data/context.js";
import AttentionPanel from "./shared/AttentionPanel.vue";
import CardTitle from "./shared/CardTitle.vue";
import DateField from "./shared/DateField.vue";
import DialogFrame from "./shared/DialogFrame.vue";
import Disclosure from "./shared/Disclosure.vue";
import Notice from "./shared/Notice.vue";
import SegYesNo from "./shared/SegYesNo.vue";
import { formatMoneyText, plainMoneyText } from "./shared/money.js";
import AddItemDialog from "./AddItemDialog.vue";
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
// Items that share one specification are shown, and edited, together (v1.17 §13.4C).
const groups = computed(() => {
	const byId = new Map(items.value.map((i) => [i.requisition_item_id, i]));
	return ((props.view.equipment || {}).groups || [])
		.map((g) => ({ ...g, rows: (g.requisition_item_ids || []).map((id) => byId.get(id)).filter(Boolean) }))
		.filter((g) => g.rows.length);
});
const remaining = computed(() => props.view.remaining_original || { shown: false });
const remainingOnly = computed(() => !!remaining.value.shown);
const canAdd = computed(() => !props.locked && ((props.view.equipment || {}).add_rows || []).some((r) => r.editable && r.room > 0));
const busy = computed(() => ctx.pending.value);

// Purchase and source details: the board's grouping of the six facts.
const sourceRows = computed(() => {
	const facts = purchase.value.source_details || [];
	return [facts.slice(0, 3), facts.slice(3, 4), facts.slice(4, 5), facts.slice(5, 6)].filter((r) => r.length);
});

// This actor's own draft of the values. It is reset from the server only
// when there is nothing unsaved to lose, or when the actor asks for it. The
// inputs bind to these, never to the server's echo (AGENTS.md §6.4).
const form = reactive({ requirement_title: "", delivery_location: "", latest_delivery_date: "", related_services_required: false });
const amounts = reactive({});
function resetFromServer() {
	form.requirement_title = info.value.requirement_title || "";
	form.delivery_location = info.value.delivery_location || "";
	form.latest_delivery_date = info.value.latest_delivery_date || "";
	form.related_services_required = !!info.value.related_services_required;
	for (const key of Object.keys(amounts)) delete amounts[key];
	for (const row of props.view.amounts || []) amounts[row.drawdown_line_id] = { value: formatMoneyText(row.requested_value_value) };
}
resetFromServer();

// An amount as the requester typed it, for comparing with what is saved:
// thousands separators and a trailing ".00" are not a different amount.
function plain(value) {
	const text = String(value === undefined || value === null ? "" : value).replace(/[,\s]/g, "");
	return /^\d+\.\d*$/.test(text) ? text.replace(/0+$/, "").replace(/\.$/, "") : text;
}
const MONEY_TEXT = /^\d{1,15}(\.\d{1,2})?$/;

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
		return !!a && r.editable && plain(a.value) !== plain(r.requested_value_value);
	})
);
const dirty = computed(() => !props.locked && (dirtyInfo.value || dirtyAmounts.value));
// The request on screen as the requester sees it — saved or not. The item
// dialog starts from this (v1.15 §13.5).
const draft = computed(() => ({ requirement_title: form.requirement_title, delivery_location: form.delivery_location, latest_delivery_date: form.latest_delivery_date }));

watch(
	() => props.view.header && props.view.header.version_record_version,
	() => {
		// An item added, changed or removed moves the Version's record version
		// too; a reload that finds unsaved typing keeps it.
		if (!dirtyInfo.value && !dirtyAmounts.value) resetFromServer();
		else {
			// Keep what is being typed; pick up rows the server added or dropped.
			for (const row of props.view.amounts || []) {
				if (!amounts[row.drawdown_line_id]) amounts[row.drawdown_line_id] = { value: formatMoneyText(row.requested_value_value) };
			}
		}
	}
);

// When the dialog set the request's delivery location (it had none), show the
// requester's own choice rather than the stale page value, so the page and the
// items give the same answer.
async function itemsAdded(shared) {
	await nextTick();
	if (shared && shared.delivery_location && info.value.delivery_location === shared.delivery_location) form.delivery_location = shared.delivery_location;
}

// Refusals from the last save, bound to the field they name.
const lastError = computed(() => {
	const e = ctx.commandError.value;
	return e && (e.label === "save-summary" || e.label === "remove-item") ? e : null;
});
// What was sent for each line: a refusal is the server's verdict on that text,
// and stops being shown once the requester changes it.
const sent = reactive({});
function fieldError(field) {
	const e = lastError.value;
	return e && e.detail && e.detail.fields ? e.detail.fields[field] || "" : "";
}
// The estimated total cost reads with thousands separators and two decimals once the field loses focus.
// The text is left exactly as typed while it is being edited, so the caret never jumps. Display only:
// what is compared and saved has no separators.
function onAmountBlur(row) {
	const a = amounts[row.drawdown_line_id];
	if (a) a.value = formatMoneyText(a.value);
}
function amountError(row) {
	const e = lastError.value;
	const typed = amounts[row.drawdown_line_id];
	if (!e || !typed || plain(typed.value) !== sent[row.drawdown_line_id]) return "";
	if (e.detail && e.detail.drawdown_line_id === row.drawdown_line_id) return e.message;
	// An amount with more than two decimal places is refused, never rounded.
	if (e.code === "REQ_MONEY_PRECISION_INVALID" && sent[row.drawdown_line_id] && !MONEY_TEXT.test(sent[row.drawdown_line_id])) return e.message;
	return "";
}
// What the server found wrong with the SAVED draft on this task. Each is said once, in the attention panel;
// the item or approved requirement it concerns carries only a marker.
const blockingHere = computed(() => (props.view.findings || []).filter((f) => f.severity === "Blocking" && f.task === "request_details"));
const flaggedItems = computed(() => new Set(blockingHere.value.filter((f) => f.row && f.row.kind === "item").map((f) => f.row.id)));
const flaggedLines = computed(() => new Set(blockingHere.value.filter((f) => f.row && f.row.kind === "drawdown_line").map((f) => f.row.id)));
function targetOf(f) {
	if (f.row && f.row.kind === "item") return `[data-item="${f.row.id}"]`;
	if (f.row && f.row.kind === "drawdown_line") return `[data-line="${f.row.id}"]`;
	return f.section ? `[data-section="${f.section}"]` : "";
}
const attention = computed(() => {
	const out = [];
	if (saveError.value) out.push({ message: saveError.value });
	if (contributor.value) return out;
	const seen = new Set(out.map((i) => i.message));
	for (const f of blockingHere.value) {
		if (seen.has(f.message)) continue;
		seen.add(f.message);
		out.push({ message: f.message, go: targetOf(f) });
	}
	return out;
});
// Take the reader to what a finding is about, and show which it is. The visible match wins, because the
// narrow layout draws the same row twice and hides one.
function goTo(selector) {
	if (!selector) return;
	nextTick(() => {
		const el = Array.from(document.querySelectorAll(selector)).find((e) => e.offsetParent !== null);
		if (!el) return;
		el.scrollIntoView({ block: "center", behavior: "smooth" });
		if (el.hasAttribute("tabindex")) el.focus({ preventScroll: true });
		el.classList.add("req-flash");
		setTimeout(() => el.classList.remove("req-flash"), 1700);
	});
}
const saveError = computed(() => {
	const e = lastError.value;
	if (!e || e.code === "REQ_STALE_VERSION" || (e.detail && (e.detail.fields || e.detail.requires_confirmation || e.detail.drawdown_line_id))) return "";
	if (e.code === "REQ_MONEY_PRECISION_INVALID" && (props.view.amounts || []).some((r) => amountError(r))) return "";
	return e.message;
});
const dialogError = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "remove-item" ? ctx.commandError.value.message : ""));

const savedNotice = ref("");
// The server's words about the SAVED draft. While there are unsaved changes
// the screen must not speak for them: it says to save instead.
const hint = computed(() => (props.view.footer_hints || {}).request_details || "");
const canContinue = computed(() => !hint.value || dirty.value);
// One line in the footer, never two: what is unsaved, what was saved, or what stops Continue.
const footerStatus = computed(() => {
	if (dirty.value) return { state: "unsaved", text: "Unsaved changes. Save to check this request." };
	if (!contributor.value && hint.value) return { state: "blocked", text: attention.value.length ? "Fix what needs attention above to continue." : hint.value };
	return null;
});

function summaryValues(extra) {
	const values = {};
	if (actions.value.edit_shared) {
		for (const k of Object.keys(form)) if (form[k] !== serverForm.value[k]) values[k] = form[k];
	}
	// A quantity is never sent: it comes from the items. Each line this actor can
	// edit sends its estimated total cost (empty clears it).
	const lines = (props.view.amounts || [])
		.filter((r) => r.editable && amounts[r.drawdown_line_id])
		.map((r) => ({ drawdown_line_id: r.drawdown_line_id, requested_value: plainMoneyText(amounts[r.drawdown_line_id].value) }));
	if (lines.length) values.drawdown_lines = lines;
	return { ...values, ...(extra || {}) };
}

async function save(extra) {
	savedNotice.value = "";
	const values = summaryValues(extra);
	for (const key of Object.keys(sent)) delete sent[key];
	for (const line of values.drawdown_lines || []) sent[line.drawdown_line_id] = plain(line.requested_value);
	const done = await ctx.run("save-summary", (key) =>
		ctx.api.saveSummary({
			requisition: props.view.header.requisition,
			summary_values: values,
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

// Continue saves the whole Draft and has the server check it together. It
// moves on only when the saved Draft has nothing blocking this task; otherwise
// the screen stays and the footer says, once, what to do.
async function saveAndContinue() {
	const ok = await save();
	await nextTick();
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
