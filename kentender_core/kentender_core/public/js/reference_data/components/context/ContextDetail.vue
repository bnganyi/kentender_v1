<script setup>
import { ref, computed, onMounted, watch } from "vue";
import StatusPill from "../StatusPill.vue";
import ActionConfirmDialog from "../ActionConfirmDialog.vue";
import CloseContextDialog from "../CloseContextDialog.vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";

const props = defineProps({ code: { type: String, required: true } });
const emit = defineEmits(["after-action"]);

const detail = ref(null);
const loading = ref(false);
const busy = ref(false);
const dialog = ref(null);
const closeDialogOpen = ref(false);

async function load() {
	loading.value = true;
	try {
		detail.value = await api.getPeFyContext(props.code);
	} finally {
		loading.value = false;
	}
}
onMounted(load);
watch(() => props.code, load);

const ACTION_CONFIG = {
	"Submit for review": { key: "submit", title: __("Submit for review"), confirmLabel: __("Submit") },
	Recommend: { key: "recommend", title: __("Recommend context"), confirmLabel: __("Recommend") },
	Approve: { key: "approve", title: __("Approve context"), confirmLabel: __("Approve") },
	Suspend: { key: "suspend", title: __("Suspend context"), confirmLabel: __("Suspend"), reasonLabel: __("Reason"), reasonRequired: true },
	Reinstate: { key: "reinstate", title: __("Reinstate context"), confirmLabel: __("Reinstate") },
	"Propose exceptional reopen": { key: "propose_reopen", title: __("Propose exceptional reopen"), confirmLabel: __("Propose reopen"), reasonLabel: __("Reason"), reasonRequired: true },
};

function openAction(label) {
	if (label === "Close") {
		closeDialogOpen.value = true;
		return;
	}
	const cfg = ACTION_CONFIG[label];
	if (!cfg) return;
	dialog.value = { label, ...cfg };
}

async function confirmAction({ reason }) {
	if (!dialog.value) return;
	busy.value = true;
	try {
		const extra = dialog.value.reasonLabel ? { reason } : {};
		await api.decidePeFyContext(props.code, dialog.value.key, detail.value.expected_version, extra);
		dialog.value = null;
		await load();
		emit("after-action");
	} finally {
		busy.value = false;
	}
}

async function confirmClose({ reason }) {
	busy.value = true;
	try {
		await api.decidePeFyContext(props.code, "close", detail.value.expected_version, { reason, acknowledged: 1 });
		closeDialogOpen.value = false;
		await load();
		emit("after-action");
	} finally {
		busy.value = false;
	}
}

const contextLine = computed(() =>
	detail.value ? `${detail.value.procuring_entity.id} — ${detail.value.procuring_entity.name} · ${detail.value.financial_year.label}` : ""
);
</script>

<template>
	<div v-if="loading || !detail" style="margin:36px 48px 0">
		<div class="kt-skel" style="width:280px;height:38px"></div>
	</div>
	<template v-else>
		<div style="padding:36px 48px 0;display:flex;align-items:flex-start;gap:32px">
			<div style="flex:1;display:flex;flex-direction:column;gap:10px">
				<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ detail.procuring_entity.id }} | FY {{ detail.financial_year.label }}</h1>
				<p style="margin:0;font-size:15px;color:color-mix(in srgb, var(--kt-color-text) 72%, transparent)">
					{{ __("Declared PE/FY Context for {0}.", [detail.procuring_entity.name]) }}
				</p>
				<div style="margin-top:2px"><StatusPill :status="detail.status" /></div>
			</div>
			<div style="display:flex;gap:14px;margin-top:6px;flex:none;flex-wrap:wrap;justify-content:flex-end">
				<button
					v-for="label in detail.available_actions"
					:key="label"
					type="button"
					:class="['kt-btn', label === 'Approve' || label === 'Submit for review' || label === 'Recommend' ? 'kt-btn-primary' : 'kt-btn-secondary', label === 'Close' ? 'kt-danger' : '']"
					@click="openAction(label)"
				>
					{{ label }}
				</button>
			</div>
		</div>

		<div style="margin:32px 48px 0;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:24px;align-content:start">
			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Context") }}</h2>
				<dl style="margin:0">
					<div class="kt-row"><dt>{{ __("Context ID") }}</dt><dd class="kt-tabular">{{ detail.context_id }}</dd></div>
					<div class="kt-row"><dt>{{ __("Procuring Entity") }}</dt><dd>{{ detail.procuring_entity.id }} — {{ detail.procuring_entity.name }}</dd></div>
					<div class="kt-row"><dt>{{ __("Financial Year") }}</dt><dd>{{ detail.financial_year.id }} — {{ detail.financial_year.label }}</dd></div>
					<div class="kt-row"><dt>{{ __("Active from") }}</dt><dd>{{ frappe.datetime.str_to_user(detail.active_from) }}</dd></div>
					<div class="kt-row"><dt>{{ __("Active to") }}</dt><dd>{{ frappe.datetime.str_to_user(detail.active_to) }}</dd></div>
				</dl>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>

			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Core readiness") }}</h2>
				<dl style="margin:0">
					<div class="kt-row" v-for="c in detail.core_readiness" :key="c.label">
						<dt>{{ __(c.label) }}</dt>
						<dd><StatusPill :status="c.status" /></dd>
					</div>
				</dl>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>

			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Governance history") }}</h2>
				<table class="kt-table" style="border:0">
					<thead>
						<tr>
							<th style="width:190px">{{ __("Date and time") }}</th>
							<th>{{ __("Event") }}</th>
							<th style="width:150px">{{ __("Actor") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(h, i) in [...detail.history].reverse()" :key="i">
							<td class="kt-muted">{{ frappe.datetime.str_to_user(h.timestamp) }}</td>
							<td>{{ h.action }}</td>
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
			:context-line="contextLine"
			:confirm-label="dialog.confirmLabel"
			:reason-label="dialog.reasonLabel || ''"
			:reason-required="!!dialog.reasonRequired"
			:busy="busy"
			@confirm="confirmAction"
			@cancel="dialog = null"
		/>
		<CloseContextDialog v-if="closeDialogOpen" :context-line="contextLine" :busy="busy" @confirm="confirmClose" @cancel="closeDialogOpen = false" />
	</template>
</template>
