<script setup>
import { ref, onMounted, watch } from "vue";
import StatusPill from "../StatusPill.vue";
import ActionConfirmDialog from "../ActionConfirmDialog.vue";
import { referenceDataApi as api } from "../../data/referenceDataApi.js";
import { classifyApiError } from "../../data/apiError.js";

const props = defineProps({ code: { type: String, required: true } });
const emit = defineEmits(["after-action", "open-context"]);

const detail = ref(null);
const loading = ref(false);
const busy = ref(false);
const dialog = ref(null);
const dialogError = ref("");

async function load() {
	loading.value = true;
	try {
		detail.value = await api.getFinancialYear(props.code);
	} finally {
		loading.value = false;
	}
}
onMounted(load);
watch(() => props.code, load);

const ACTION_CONFIG = {
	"Make available": { fn: () => api.makeFinancialYearAvailable(props.code), title: __("Make available"), confirmLabel: __("Make available") },
	Retire: { fn: () => api.retireFinancialYear(props.code), title: __("Retire financial year"), confirmLabel: __("Retire"), danger: true },
};

function openAction(label) {
	const cfg = ACTION_CONFIG[label];
	if (!cfg) return;
	dialogError.value = "";
	dialog.value = { label, ...cfg };
}

async function confirmAction() {
	if (!dialog.value) return;
	busy.value = true;
	dialogError.value = "";
	try {
		await dialog.value.fn();
		dialog.value = null;
		await load();
		emit("after-action");
	} catch (err) {
		dialogError.value = classifyApiError(err).banner;
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div v-if="loading || !detail" style="margin:36px 48px 0">
		<div class="kt-skel" style="width:280px;height:38px"></div>
	</div>
	<template v-else>
		<div style="padding:36px 48px 0;display:flex;align-items:flex-start;gap:32px">
			<div style="flex:1;display:flex;flex-direction:column;gap:12px">
				<h1 style="margin:0;font-size:38px;line-height:1.05;letter-spacing:.005em">{{ __("Financial year {0}", [detail.label]) }}</h1>
				<div><StatusPill :status="detail.record_status" /></div>
			</div>
			<div style="display:flex;gap:14px;margin-top:6px;flex:none">
				<button
					v-for="label in detail.available_actions"
					:key="label"
					type="button"
					:class="['kt-btn', label === 'Retire' ? 'kt-btn-secondary kt-danger' : 'kt-btn-primary']"
					@click="openAction(label)"
				>
					{{ label }}
				</button>
			</div>
		</div>

		<div style="margin:36px 48px 0;display:grid;grid-template-columns:minmax(0,0.85fr) minmax(0,1.15fr);gap:24px;align-items:start">
			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Calendar") }}</h2>
				<dl style="margin:0">
					<div class="kt-row"><dt>{{ __("Financial Year ID") }}</dt><dd class="kt-tabular">{{ detail.financial_year_id }}</dd></div>
					<div class="kt-row"><dt>{{ __("Start date") }}</dt><dd>{{ frappe.datetime.str_to_user(detail.start_date) }}</dd></div>
					<div class="kt-row"><dt>{{ __("End date") }}</dt><dd>{{ frappe.datetime.str_to_user(detail.end_date) }}</dd></div>
					<div class="kt-row"><dt>{{ __("Timezone") }}</dt><dd>{{ detail.timezone }}</dd></div>
					<div class="kt-row"><dt>{{ __("Calendar phase") }}</dt><dd>{{ detail.calendar_phase }}</dd></div>
				</dl>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>

			<div class="kt-card kt-blueprint">
				<h2 class="kt-card-title">{{ __("Declared PE/FY Contexts") }}</h2>
				<table class="kt-table" style="border:0">
					<thead>
						<tr>
							<th style="width:210px">{{ __("Context") }}</th>
							<th>{{ __("Procuring entity") }}</th>
							<th style="width:110px">{{ __("Status") }}</th>
							<th style="width:90px;text-align:right">{{ __("Action") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="c in detail.contexts" :key="c.context_id">
							<td class="kt-tabular">{{ c.context_id }}</td>
							<td>{{ c.procuring_entity }}</td>
							<td><StatusPill :status="c.status" /></td>
							<td style="text-align:right"><button type="button" class="kt-btn kt-btn-ghost" @click="emit('open-context', c.context_id)">{{ __("View") }}</button></td>
						</tr>
					</tbody>
				</table>
				<div style="padding-top:16px;font-size:13px;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">
					{{ __("{0} declared contexts", [detail.contexts.length]) }}
				</div>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
			</div>
		</div>

		<ActionConfirmDialog
			v-if="dialog"
			:title="dialog.title"
			:context-line="detail.label"
			:confirm-label="dialog.confirmLabel"
			:danger="!!dialog.danger"
			:busy="busy"
			:error-message="dialogError"
			@confirm="confirmAction"
			@cancel="dialog = null"
			@clear-error="dialogError = ''"
		/>
	</template>
</template>
