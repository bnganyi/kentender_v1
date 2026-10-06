<!-- Edit one technical requirement (REQ-DES-05 row action). The board draws
     the row, not this dialog; it is built from the shared dialog and field
     primitives. The control follows the released characteristic (§13.1): the
     catalogue, not this dialog, owns units, options and ranges — the server
     re-validates every value. -->
<template>
	<DialogFrame :title="`Edit ${row.label}`" :width="480" :busy="busy" testid="req-technical-dialog" @close="$emit('close')">
		<p class="req-dialog-body kt-muted">{{ row.comparison }}<template v-if="characteristic.unit"> · {{ characteristic.unit }}</template></p>
		<div v-if="control === 'YES_NO' || control === 'SELECT'" class="field">
			<label :for="id">Required value</label>
			<select :id="id" v-model="single" class="input" data-testid="req-technical-value">
				<option v-for="o in characteristic.options" :key="o" :value="o">{{ o }}</option>
			</select>
		</div>
		<div v-else-if="control === 'INTEGER' || control === 'DECIMAL'" class="field">
			<label :for="id">Minimum or required value<template v-if="characteristic.unit"> ({{ characteristic.unit }})</template></label>
			<input :id="id" v-model="single" class="input" :inputmode="control === 'INTEGER' ? 'numeric' : 'decimal'" data-testid="req-technical-value" />
			<div v-if="characteristic.minimum !== null || characteristic.maximum !== null" class="kt-field-hint">Between {{ characteristic.minimum }} and {{ characteristic.maximum }}</div>
		</div>
		<div v-else-if="control === 'TEXT'" class="field">
			<label :for="id">Minimum or required value</label>
			<textarea :id="id" v-model="single" class="input" rows="2" data-testid="req-technical-value"></textarea>
		</div>
		<fieldset v-else-if="control === 'MULTI_SELECT'" class="field req-fieldset">
			<legend>Every selected capability is required</legend>
			<label v-for="o in characteristic.options" :key="o" class="kt-checkbox req-check-line">
				<input v-model="many" type="checkbox" :value="o" /><span class="box"></span>{{ o }}
			</label>
		</fieldset>
		<div v-else-if="control === 'PORT_LIST'" class="field">
			<label>Required ports</label>
			<div v-for="(port, i) in ports" :key="i" class="req-port-row">
				<select v-model="port.port_type" class="input" :aria-label="`Port ${i + 1} type`">
					<option v-for="o in characteristic.port_options" :key="o" :value="o">{{ o }}</option>
				</select>
				<input v-model="port.minimum_count" class="input req-num-input" inputmode="numeric" :aria-label="`Port ${i + 1} minimum count`" />
				<button type="button" class="btn btn-ghost" @click="ports.splice(i, 1)">Remove</button>
			</div>
			<button type="button" class="btn btn-ghost" @click="ports.push({ port_type: characteristic.port_options[0], minimum_count: '1' })">Add port</button>
		</div>
		<Notice v-if="error" tone="critical"><span data-testid="req-technical-error">{{ error }}</span></Notice>
		<template #actions>
			<button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Cancel</button>
			<button type="button" class="btn btn-primary" :disabled="busy" data-testid="req-technical-confirm" @click="confirm">{{ local ? "Use this value" : "Save requirement" }}</button>
		</template>
	</DialogFrame>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useReq } from "../data/context.js";
import DialogFrame from "./shared/DialogFrame.vue";
import Notice from "./shared/Notice.vue";

const props = defineProps({
	view: { type: Object, required: true },
	row: { type: Object, required: true },
	// A Proposed row is edited in the page's own review copy; a Confirmed row
	// is saved at once.
	local: { type: Boolean, default: false },
	value: { type: Object, default: null },
});
const emit = defineEmits(["close", "local"]);
const ctx = useReq();
const busy = computed(() => ctx.pending.value);
const id = `req-tech-${Math.random().toString(36).slice(2, 8)}`;
const characteristic = computed(() => ((props.view.catalogue || {}).characteristics || []).find((c) => c.key === props.row.characteristic_key) || { options: [], port_options: [] });
const control = computed(() => characteristic.value.control);

const start = props.value || props.row.value || {};
const single = ref(start.value === undefined ? "" : String(start.value));
const many = ref(Array.isArray(start.values) ? [...start.values] : []);
const ports = reactive((start.ports || []).map((p) => ({ port_type: p.port_type, minimum_count: String(p.minimum_count) })));

const commandError = computed(() => (ctx.commandError.value && ctx.commandError.value.label === "update-technical" ? ctx.commandError.value.message : ""));
const localError = ref("");
const error = computed(() => localError.value || commandError.value);

function raw() {
	if (control.value === "MULTI_SELECT") return [...many.value];
	if (control.value === "PORT_LIST") return ports.map((p) => ({ port_type: p.port_type, minimum_count: String(p.minimum_count).trim() }));
	return String(single.value).trim();
}
// The stored shape the server returns, so the review copy shows what was chosen.
function stored() {
	if (control.value === "MULTI_SELECT") return { values: raw() };
	if (control.value === "PORT_LIST") return { ports: raw().map((p) => ({ port_type: p.port_type, minimum_count: Number(p.minimum_count) })) };
	return { value: raw() };
}

async function confirm() {
	localError.value = "";
	if (props.local) {
		const value = raw();
		if ((Array.isArray(value) && !value.length) || value === "") {
			localError.value = `Enter the value for ${props.row.label}.`;
			return;
		}
		emit("local", { raw: value, stored: stored() });
		emit("close");
		return;
	}
	const done = await ctx.run("update-technical", (key) =>
		ctx.api.updateTechnical({
			requisition: props.view.header.requisition,
			technical_requirement_id: props.row.technical_requirement_id,
			values: { value: raw() },
			expected_record_version: props.view.package_record_version,
			idempotency_key: key,
		})
	);
	if (done) emit("close");
}
</script>
