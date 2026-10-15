<!-- One block of a board region or dialog (CM-CHG-001 v0.8 section 10): facts, rows, table, fields, text, strong, help, links, buttons or a preview. Ported from the design template's block
     markup, class for class; the dialog variant uses the design's compact dialog markup. A block with `when` is drawn only while another field has that value (the declaration's description
     appears once a conflict is chosen). -->
<template>
	<template v-if="visible">
		<div v-if="b.isFacts" class="kt-meta-row" style="align-items: start">
			<div v-for="it in b.items" :key="it.l"><span class="kt-label">{{ it.l }}</span><span style="font-size: 17px; font-weight: 600; color: var(--color-heading); font-variant-numeric: tabular-nums">{{ it.v }}</span></div>
		</div>

		<div v-if="b.isRows" :style="dialog ? 'display: grid; grid-template-columns: 170px minmax(0, 1fr); border-top: 1px solid var(--color-divider)' : 'display: grid; grid-template-columns: 260px minmax(0, 1fr); border-top: 1px solid var(--color-divider)'">
			<template v-for="it in b.items" :key="it.l">
				<div :style="dialog ? 'padding: 8px 0; border-bottom: 1px solid var(--color-divider); font-size: 13px; color: var(--color-neutral-700)' : 'padding: 9px 0; border-bottom: 1px solid var(--color-divider); font-size: 14px; color: var(--color-neutral-700)'">{{ it.l }}</div>
				<div :style="dialog ? 'padding: 8px 0; border-bottom: 1px solid var(--color-divider); font-size: 14px; color: var(--color-text)' : 'padding: 9px 0; border-bottom: 1px solid var(--color-divider); font-size: 14px; font-weight: 500; color: var(--color-text)'">{{ it.v }}</div>
			</template>
		</div>

		<table v-if="b.isTable && !dialog" class="table">
			<thead><tr><th v-for="h in b.head" :key="h.v" :class="h.cls">{{ h.v }}</th></tr></thead>
			<tbody>
				<tr v-for="(r, ri) in b.body" :key="ri">
					<td v-for="(c, ci) in r.cells" :key="ci" :class="c.cls">
						<template v-if="c.live">{{ unitRange(form[c.live]) }}</template>
						<template v-else-if="c.isT">{{ c.v }}</template>
						<a v-else-if="c.isL" href="#" @click.prevent="$emit('act', c.v)">{{ c.v }}</a>
						<span v-else-if="c.isS" class="kt-status" :class="c.sc">{{ c.v }}</span>
						<input v-else-if="c.isI" v-model="form[c.name]" class="input" :class="{ 'is-invalid': errors[c.name] }" style="text-align: inherit" :disabled="disabled" :data-testid="`cm-input-${c.name}`" />
						<select v-else-if="c.isSel" v-model="form[c.name]" class="input" :disabled="disabled" :data-testid="`cm-input-${c.name}`"><option v-for="o in c.opts" :key="o" :value="o">{{ o }}</option></select>
					</td>
				</tr>
			</tbody>
		</table>
		<div v-if="b.isTable && dialog" :style="`display: grid; grid-template-columns: ${b.gcols}; font-size: 13px`">
			<div v-for="h in b.head" :key="h.v" style="padding: 6px 8px 6px 0; font-weight: 600; color: var(--color-neutral-700); border-bottom: 1px solid var(--color-divider)">{{ h.v }}</div>
			<div v-for="(c, ci) in b.flat" :key="ci" style="padding: 6px 8px 6px 0; border-bottom: 1px solid var(--color-divider); display: flex; align-items: center; min-width: 0">
				<template v-if="c.isT">{{ c.v }}</template>
				<span v-else-if="c.isS" class="kt-status" :class="c.sc">{{ c.v }}</span>
				<input v-else-if="c.isI" v-model="form[c.name]" class="input" :disabled="disabled" :data-testid="`cm-input-${c.name}`" />
				<select v-else-if="c.isSel" v-model="form[c.name]" class="input" :disabled="disabled" :data-testid="`cm-input-${c.name}`"><option v-for="o in c.opts" :key="o" :value="o">{{ o }}</option></select>
			</div>
		</div>

		<div v-if="b.isFields" :style="dialog ? 'display: grid; gap: 14px' : 'display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 24px'">
			<template v-for="f in b.items" :key="f.name">
				<div v-if="shown(f)" class="field" :style="dialog ? '' : `grid-column: ${f.span}`">
					<label :for="`cm-f-${f.name}`">{{ f.l }}</label>
					<input v-if="f.t === 'tx'" :id="`cm-f-${f.name}`" v-model="form[f.name]" class="input" :class="{ 'is-invalid': errors[f.name] }" :disabled="disabled" :data-testid="`cm-input-${f.name}`" />
					<input v-else-if="f.t === 'dt'" :id="`cm-f-${f.name}`" v-model="form[f.name]" class="input" :type="f.o && f.o.time ? 'datetime-local' : 'date'" :class="{ 'is-invalid': errors[f.name] }" :disabled="disabled" :data-testid="`cm-input-${f.name}`" />
					<select v-else-if="f.t === 'sel'" :id="`cm-f-${f.name}`" v-model="form[f.name]" class="input" :class="{ 'is-invalid': errors[f.name] }" :disabled="disabled" :data-testid="`cm-input-${f.name}`">
						<option v-for="o in f.options" :key="o.value" :value="o.value">{{ o.label }}</option>
					</select>
					<textarea v-else-if="f.t === 'ta'" :id="`cm-f-${f.name}`" v-model="form[f.name]" class="input" :class="{ 'is-invalid': errors[f.name] }" :rows="f.rows" :disabled="disabled" :data-testid="`cm-input-${f.name}`"></textarea>
					<div v-else-if="f.t === 'ro'" style="min-height: 36px; display: flex; align-items: center; font-size: 14px; font-weight: 500; color: var(--color-text)">{{ f.v }}</div>
					<div v-else-if="f.t === 'rad'" style="display: grid; gap: 10px; padding-top: 4px" role="radiogroup" :data-testid="`cm-input-${f.name}`">
						<label v-for="o in f.options" :key="o.index" class="radio"><input v-model="form[f.name]" type="radio" :name="f.radioName" :value="String(o.index)" :disabled="disabled" /><span class="dot"></span>{{ o.label }}</label>
					</div>
					<RecordPickerHost
						v-else-if="f.t === 'pick'"
						v-model="form[f.name]"
						:source="f.source"
						:context="f.context"
						:value-label="f.valueLabel"
						:input-id="`cm-f-${f.name}`"
						:noun="f.noun"
						:invalid="!!errors[f.name]"
						:disabled="disabled"
						:data-testid="`cm-pick-${f.name}`"
					/>
					<span v-if="errors[f.name]" class="kt-field-error" role="alert">{{ errors[f.name] }}</span>
				</div>
			</template>
		</div>

		<p v-if="b.isText" :style="dialog ? 'margin: 0' : 'margin: 0; font-size: 14px; color: var(--color-text); max-width: 80ch; text-wrap: pretty'">{{ b.v }}</p>
		<p v-if="b.isStrong" style="margin: 0; font-size: 15px; font-weight: 600; color: var(--color-heading); max-width: 80ch; text-wrap: pretty">{{ b.v }}</p>
		<p v-if="b.isHelp" style="margin: 0; font-size: 13px; color: var(--color-neutral-700); max-width: 80ch; text-wrap: pretty">{{ b.v }}</p>
		<div v-if="b.isLinks" style="display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 14px"><a v-for="l in b.items" :key="l" href="#" @click.prevent="$emit('act', l)">{{ l }}</a></div>
		<div v-if="b.isBtns" style="display: flex; flex-wrap: wrap; gap: 8px"><button v-for="l in b.items" :key="l" type="button" class="btn btn-secondary" :disabled="disabled" @click="$emit('act', l)">{{ l }}</button></div>
		<div v-if="b.isPreview" class="kt-disclosure">
			<div class="kt-disclosure-head" style="padding-left: 0; padding-right: 0" role="button" tabindex="0" @click="open = !open" @keydown.enter="open = !open">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ b.t }}</span></div>
				<svg class="kt-icon is-sm kt-disclosure-chevron" :class="{ 'is-open': open }" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"></path></svg>
			</div>
			<div v-if="open" class="kt-disclosure-body" style="padding-left: 0; padding-right: 0">
				<div style="display: grid; grid-template-columns: 260px minmax(0, 1fr)">
					<template v-for="it in b.items" :key="it.l">
						<div style="padding: 7px 0; font-size: 14px; color: var(--color-neutral-700)">{{ it.l }}</div>
						<div style="padding: 7px 0; font-size: 14px; color: var(--color-text)">{{ it.v }}</div>
					</template>
				</div>
			</div>
		</div>
	</template>
</template>

<script setup>
import { computed, ref } from "vue";
import RecordPickerHost from "../../record_picker_shared/RecordPickerHost.vue";
import { blockView, unitRange } from "../board_view.js";

const props = defineProps({
	block: { type: Object, required: true },
	form: { type: Object, required: true },
	errors: { type: Object, default: () => ({}) },
	board: { type: Object, required: true },
	dialog: { type: Boolean, default: false },
	disabled: { type: Boolean, default: false },
});
defineEmits(["act"]);

const b = computed(() => blockView(props.block, props.board.id, 0));
const open = ref(props.block.open !== false);

function holds(when) {
	return !when || Object.entries(when).every(([name, value]) => String(props.form[name] ?? "") === String(value));
}

const visible = computed(() => holds(props.block.when));
const shown = (field) => holds(field.when);
</script>
