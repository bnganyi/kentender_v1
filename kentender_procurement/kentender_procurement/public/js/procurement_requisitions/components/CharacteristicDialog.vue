<!-- REQ-DES-05's "Add characteristic" dialog (§13.7). Not in the artboard
     file itself, same as ItemDialog.vue — built on kt_industry_tokens.css's
     shared .kt-dialog chrome. The Required-value control is derived from the
     selected characteristic's own catalogue control type (§6.3), never a
     single generic text box: the server independently re-validates whatever
     is posted against the same catalogue (services/catalogue.py), so this
     dialog only has to get the common case right, not be the source of
     truth. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-characteristic-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">{{ prefillRow ? "Confirm characteristic" : "Add characteristic" }}</div>
			<p v-if="prefillRow" class="req-table-caption">This proposed baseline characteristic has no default value — supply one to confirm it.</p>

			<div class="kt-field">
				<label for="ch-applies-to">Applies to</label>
				<select id="ch-applies-to" class="kt-input" v-model="appliesTo" :disabled="!!prefillRow">
					<option value="__all__">All items</option>
					<option v-for="item in items" :key="item.requisition_item_id" :value="item.requisition_item_id">{{ item.item_name }} — {{ item.plan_item_line_id }}</option>
				</select>
			</div>

			<div class="kt-field">
				<label for="ch-key">Characteristic</label>
				<select id="ch-key" class="kt-input" v-model="characteristicKey" :disabled="!!prefillRow">
					<option value="" disabled>Select a characteristic</option>
					<option v-for="c in availableCharacteristics" :key="c.key" :value="c.key">{{ c.label }}</option>
				</select>
				<p v-if="errors.characteristic_key" class="req-field-error">{{ errors.characteristic_key }}</p>
			</div>

			<template v-if="characteristic">
				<div class="req-field-grid">
					<div class="kt-field">
						<label>Comparison</label>
						<input class="kt-ro" :value="characteristic.comparison" disabled />
					</div>
					<div class="kt-field">
						<label>Unit</label>
						<input class="kt-ro" :value="characteristic.unit || '—'" disabled />
					</div>
				</div>

				<div class="kt-field" v-if="characteristic.control === 'YES_NO'">
					<label id="ch-value-lbl">Required value</label>
					<div class="req-seg" role="radiogroup" aria-labelledby="ch-value-lbl">
						<label v-for="opt in characteristic.options" :key="opt" class="req-seg-opt">
							<input type="radio" :checked="value === opt" @change="value = opt" />{{ opt }}
						</label>
					</div>
				</div>

				<div class="kt-field" v-else-if="characteristic.control === 'INTEGER' || characteristic.control === 'DECIMAL'">
					<label for="ch-value">Required value{{ characteristic.unit ? ` (${characteristic.unit})` : "" }}</label>
					<input id="ch-value" type="number" class="kt-input" :step="characteristic.control === 'DECIMAL' ? '0.1' : '1'" :value="value" @input="value = $event.target.value" />
				</div>

				<div class="kt-field" v-else-if="characteristic.control === 'SELECT'">
					<label for="ch-value">Required value</label>
					<select id="ch-value" class="kt-input" v-model="value">
						<option value="" disabled>Select a value</option>
						<option v-for="opt in characteristic.options" :key="opt" :value="opt">{{ opt }}</option>
						<option v-if="characteristic.allows_other" value="Other">Other</option>
					</select>
					<input v-if="value === 'Other'" class="kt-input" style="margin-top: 8px" placeholder="Other value" :value="otherValue" @input="otherValue = $event.target.value" />
				</div>

				<div class="kt-field" v-else-if="characteristic.control === 'MULTI_SELECT'">
					<label id="ch-value-lbl">Required value</label>
					<div class="req-check-list" aria-labelledby="ch-value-lbl">
						<label v-for="opt in characteristic.options" :key="opt" class="req-check-opt">
							<input type="checkbox" :value="opt" v-model="multiValue" />{{ opt }}
						</label>
					</div>
				</div>

				<div class="kt-field" v-else-if="characteristic.control === 'TEXT'">
					<label for="ch-value">Required value</label>
					<textarea id="ch-value" class="kt-input" rows="3" :maxlength="characteristic.max_length || undefined" :value="value" @input="value = $event.target.value"></textarea>
					<label v-if="characteristic.allows_other" style="margin-top: 8px; display: block">
						<input type="checkbox" v-model="isOther" /> Other essential characteristic
					</label>
					<input v-if="isOther" class="kt-input" style="margin-top: 8px" placeholder="Other value" :value="otherValue" @input="otherValue = $event.target.value" />
				</div>

				<div class="kt-field" v-else-if="characteristic.control === 'PORT_LIST'">
					<label id="ch-ports-lbl">Required ports</label>
					<div class="req-port-row" v-for="(port, idx) in ports" :key="idx">
						<select class="kt-input" v-model="port.port_type">
							<option value="" disabled>Port type</option>
							<option v-for="opt in characteristic.port_options" :key="opt" :value="opt">{{ opt }}</option>
						</select>
						<input type="number" min="1" class="kt-input req-qty-input" placeholder="Min ×" :value="port.minimum_count" @input="port.minimum_count = Number($event.target.value)" />
						<a href="#" class="req-quiet-link" @click.prevent="ports.splice(idx, 1)">Remove</a>
					</div>
					<button type="button" class="kt-btn kt-btn-secondary" @click="ports.push({ port_type: '', minimum_count: 1 })">Add port</button>
				</div>

				<p v-if="errors.value" class="req-field-error">{{ errors.value }}</p>

				<div class="kt-field" v-if="characteristic.key === 'other_essential_characteristic'">
					<label for="ch-reason">Reason</label>
					<textarea id="ch-reason" class="kt-input" rows="2" minlength="20" maxlength="300" :value="reason" @input="reason = $event.target.value"></textarea>
					<p v-if="errors.reason" class="req-field-error">{{ errors.reason }}</p>
				</div>
			</template>

			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>

			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-characteristic-dialog-confirm" @click="confirm">{{ prefillRow ? "Confirm" : "Add characteristic" }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";

const props = defineProps({
	editor: { type: Object, required: true },
	pending: Boolean,
	error: { type: String, default: "" },
	// Set only when this dialog is confirming an existing value-less
	// Proposed baseline row (StepTechnical.vue's own "Confirm" link on such
	// a row) rather than adding a brand new characteristic — the Applies-to
	// and Characteristic controls lock to that row's own values.
	prefillRow: { type: Object, default: null },
});

const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const items = computed(() => (props.editor.package || {}).items || []);
const characteristics = computed(() => (props.editor.catalogue || {}).characteristics || []);

// The Add-characteristic dialog offers every characteristic the catalogue
// makes available to any equipment category present on this Draft — the
// server independently re-checks applicability for the actual chosen scope.
const categoriesInUse = computed(() => new Set(items.value.map((i) => i.equipment_category)));
const availableCharacteristics = computed(() =>
	characteristics.value.filter((c) => !c.applies_to || c.applies_to.some((cat) => categoriesInUse.value.has(cat)))
);

const appliesTo = ref(props.prefillRow ? props.prefillRow.applies_to_id || "__all__" : "__all__");
const characteristicKey = ref(props.prefillRow ? props.prefillRow.characteristic_key : "");
const value = ref("");
const otherValue = ref("");
const isOther = ref(false);
const multiValue = ref([]);
const ports = ref([{ port_type: "", minimum_count: 1 }]);
const reason = ref("");
const errors = ref({});

const characteristic = computed(() => characteristics.value.find((c) => c.key === characteristicKey.value) || null);

function confirm() {
	const next = {};
	if (!characteristicKey.value) next.characteristic_key = "A characteristic is required.";
	let rawValue = value.value;
	if (characteristic.value) {
		if (characteristic.value.control === "MULTI_SELECT") rawValue = multiValue.value;
		if (characteristic.value.control === "PORT_LIST") rawValue = ports.value;
		if (characteristic.value.control === "TEXT" && isOther.value) rawValue = "Other";
		if (!rawValue || (Array.isArray(rawValue) && !rawValue.length)) next.value = "A required value is required.";
	}
	if (characteristic.value && characteristic.value.key === "other_essential_characteristic" && (reason.value.trim().length < 20 || reason.value.trim().length > 300)) {
		next.reason = "A reason of 20-300 characters is required.";
	}
	errors.value = next;
	if (Object.keys(next).length) return;
	emit("confirm", {
		applies_to_scope: appliesTo.value === "__all__" ? "All items" : "Item",
		applies_to_id: appliesTo.value === "__all__" ? "" : appliesTo.value,
		characteristic_key: characteristicKey.value,
		value: rawValue,
		other_value: otherValue.value,
		reason: reason.value,
	});
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
