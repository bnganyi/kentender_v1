<script setup>
import { ref, computed, onMounted, watch } from "vue";
import StatusPill from "../StatusPill.vue";
import ActionConfirmDialog from "../ActionConfirmDialog.vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";
import { actionLabel } from "../../data/actionLabel.js";
import { classifyApiError } from "../../data/apiError.js";

const props = defineProps({ code: { type: String, required: true } });
const emit = defineEmits(["after-action", "back", "edit"]);

const detail = ref(null);
const loading = ref(false);
const busy = ref(false);
const dialog = ref(null); // { action, title, confirmLabel, danger, reasonLabel, reasonRequired, needsEffectiveDate }
const dialogError = ref("");

async function load() {
	loading.value = true;
	try {
		detail.value = await api.getProcuringEntity(props.code);
	} finally {
		loading.value = false;
	}
}
onMounted(load);
watch(() => props.code, load);

const ACTION_CONFIG = {
	"Activate procuring entity": { key: "activate", title: __("Activate procuring entity"), confirmLabel: __("Activate") },
	"Apply amendment": { key: "activate", title: __("Apply amendment"), confirmLabel: __("Apply amendment") },
	"Suspend": { key: "suspend", title: __("Suspend procuring entity"), confirmLabel: __("Suspend"), reasonLabel: __("Reason"), reasonRequired: true },
	"Reinstate": { key: "reinstate", title: __("Reinstate procuring entity"), confirmLabel: __("Reinstate") },
	"Retire": {
		key: "retire",
		title: __("Retire procuring entity"),
		confirmLabel: __("Retire"),
		danger: true,
		reasonLabel: __("Reason"),
		reasonRequired: true,
		needsEffectiveDate: true,
	},
};

function openAction(label) {
	if (label === "Propose amendment") {
		openAmendmentPrompt();
		return;
	}
	if (label === "Edit draft") {
		emit("edit", props.code);
		return;
	}
	const cfg = ACTION_CONFIG[label];
	if (!cfg) return;
	dialogError.value = "";
	dialog.value = { label, ...cfg };
}

async function openAmendmentPrompt() {
	const changeReason = await new Promise((resolve) => {
		frappe.prompt(
			{ fieldname: "change_reason", fieldtype: "Small Text", label: __("Change reason"), reqd: 1 },
			(values) => resolve(values.change_reason),
			__("Propose amendment"),
			__("Propose amendment")
		);
	});
	if (!changeReason) return;
	busy.value = true;
	try {
		await api.proposePeAmendment(props.code, changeReason);
		await load();
		emit("after-action");
	} catch (err) {
		frappe.show_alert({ indicator: "red", message: classifyApiError(err).banner }, 5);
	} finally {
		busy.value = false;
	}
}

async function confirmAction({ reason, effectiveDate }) {
	if (!dialog.value) return;
	busy.value = true;
	dialogError.value = "";
	try {
		const extra = {};
		if (dialog.value.reasonLabel) extra.reason = reason;
		if (dialog.value.needsEffectiveDate) extra.effective_date = effectiveDate;
		await api.decidePeChange(props.code, dialog.value.key, extra);
		dialog.value = null;
		await load();
		emit("after-action");
	} catch (err) {
		dialogError.value = classifyApiError(err).banner;
	} finally {
		busy.value = false;
	}
}

const dialogContextLine = computed(() => (detail.value ? `${detail.value.pe_id} — ${detail.value.version?.legal_name || ""}` : ""));
</script>

<template>
	<div v-if="loading || !detail" style="margin:36px 48px 0">
		<div class="kt-skel" style="width:280px;height:38px"></div>
	</div>
	<template v-else>
		<div style="padding:36px 48px 0;display:flex;align-items:flex-start;gap:32px">
			<div style="flex:1;display:flex;flex-direction:column;gap:12px">
				<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ detail.pe_id }} — {{ detail.version?.legal_name }}</h1>
				<div><StatusPill :status="detail.status" /></div>
			</div>
			<div style="display:flex;gap:14px;margin-top:6px;flex:none;flex-wrap:wrap;justify-content:flex-end">
				<button
					v-for="label in detail.available_actions"
					:key="label"
					type="button"
					:class="['kt-btn', label === 'Propose amendment' || label === 'Reinstate' || label === 'Suspend' || label === 'Edit draft' ? 'kt-btn-secondary' : 'kt-btn-primary', label === 'Retire' ? 'kt-danger' : '']"
					@click="openAction(label)"
				>
					{{ label }}
				</button>
			</div>
		</div>

		<div style="margin:36px 48px 0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;align-content:start">
			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Identity") }}</h2>
				<dl style="margin:0">
					<div class="kt-row"><dt>{{ __("PE code") }}</dt><dd class="kt-tabular">{{ detail.pe_id }}</dd></div>
					<div class="kt-row"><dt>{{ __("Legal name") }}</dt><dd>{{ detail.version?.legal_name }}</dd></div>
					<div class="kt-row"><dt>{{ __("Display name") }}</dt><dd>{{ detail.version?.display_name }}</dd></div>
					<div class="kt-row"><dt>{{ __("PE type") }}</dt><dd>{{ detail.version?.pe_type_code || "—" }}</dd></div>
					<div class="kt-row"><dt>{{ __("Version") }}</dt><dd>{{ detail.version?.version_no }} ({{ detail.version?.version_state }})</dd></div>
				</dl>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>

			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Operational setting") }}</h2>
				<dl style="margin:0">
					<div class="kt-row"><dt>{{ __("Timezone") }}</dt><dd>{{ detail.version?.timezone || "Africa/Nairobi" }}</dd></div>
					<div class="kt-row"><dt>{{ __("Effective from") }}</dt><dd>{{ detail.effective_from ? frappe.datetime.str_to_user(detail.effective_from) : "—" }}</dd></div>
				</dl>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>

			<div class="kt-card kt-blueprint" style="grid-column:1 / -1">
				<h2 class="kt-card-title">{{ __("History") }}</h2>
				<table class="kt-table" style="border:0">
					<thead>
						<tr>
							<th style="width:210px">{{ __("Date and time") }}</th>
							<th>{{ __("Event") }}</th>
							<th style="width:150px">{{ __("Actor") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(h, i) in [...detail.history].reverse()" :key="i">
							<td class="kt-muted">{{ frappe.datetime.str_to_user(h.timestamp) }}</td>
							<td>{{ actionLabel(h.action) }}</td>
							<td>{{ h.performed_by }}</td>
						</tr>
					</tbody>
				</table>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>
		</div>

		<ActionConfirmDialog
			v-if="dialog"
			:title="dialog.title"
			:context-line="dialogContextLine"
			:confirm-label="dialog.confirmLabel"
			:danger="!!dialog.danger"
			:reason-label="dialog.reasonLabel || ''"
			:reason-required="!!dialog.reasonRequired"
			:needs-effective-date="!!dialog.needsEffectiveDate"
			:busy="busy"
			:error-message="dialogError"
			@confirm="confirmAction"
			@cancel="dialog = null"
			@clear-error="dialogError = ''"
		/>
	</template>
</template>
