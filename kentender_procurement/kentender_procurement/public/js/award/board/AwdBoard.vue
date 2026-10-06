<!-- One Award screen, drawn exactly as the artboards draw it (AWD-CHG-001 v0.4
     §10; `16_award/design/Award Artboards.dc.html`, the <main> page template):
     the page head with its kicker, the guidance region (the server's journey
     and next step, through kentender_core's shared components; a supplier or
     workspace screen draws its own next step as the board does), the
     sections, the decision bar or action row, the disclosures and a dialog.
     The markup and classes are the template's, container for container, with
     the design tool's `btn`/`field`/`input`/`dialog` names mapped to the
     Industry `kt-` classes; the only differences are live ones: inputs edit
     `form`, and every button emits the action its screen named. -->
<template>
	<div class="kt-page awd-board" style="max-width:none" data-testid="awd-board">
		<div class="kt-page-head">
			<div>
				<div v-if="m.hasKicker" style="display:flex;align-items:center;gap:6px;margin-bottom:8px;font-size:13px;font-weight:600;color:var(--kt-color-accent-700)"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path v-for="(p, i) in m.kIco" :key="i" :d="p.d"></path></svg><span>{{ m.kicker }}</span></div>
				<h1 class="kt-page-title" data-testid="awd-title">{{ m.title }}</h1>
				<p v-if="m.hasDesc" class="kt-page-desc" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center" data-testid="awd-desc"><span>{{ m.desc }}</span><span v-if="m.hasChip" :class="m.chipCls" data-testid="awd-chip">{{ m.chipLabel }}</span></p>
			</div>
		</div>

		<AwdGuidance v-if="m.guidance" :answer="m.guidance.answer" :journey="m.guidance.journey" :pending="pending" @fix="emit('action', { action: 'fix', args: $event })" />
		<div v-else-if="m.hasLocalNext" class="kt-guidance" style="padding-left:0;padding-right:0">
			<div :class="m.nextCls" data-kt="next-step" data-testid="awd-next-step">
				<div class="kt-next-step-label">{{ m.nl }}</div>
				<p class="kt-next-step-headline" data-testid="awd-next-step-headline">{{ m.nh }}</p>
				<p v-if="m.hasNs" class="kt-next-step-sentence">{{ m.ns }}</p>
			</div>
		</div>

		<div v-for="(sec, si) in m.sections" :key="si" :class="sec.cls" :id="`awd-${sec.anchor}`" :data-testid="sec.testid || `awd-section-${sec.anchor}`">
			<h2 style="display:flex;align-items:center;gap:8px"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-accent-700)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none"><path v-for="(p, i) in sec.ico" :key="i" :d="p.d"></path></svg><span>{{ sec.t }}</span></h2>
			<div style="display:grid;gap:16px">
				<div v-if="sec.hasP" style="display:grid;gap:6px">
					<div v-for="(para, pi) in sec.p" :key="pi" style="display:flex;gap:8px;align-items:flex-start">
						<svg v-if="para.ok" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--kt-status-live)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none;margin-top:2px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><path d="M22 4 12 14.01l-3-3"></path></svg>
						<svg v-if="para.warn" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--kt-status-attention)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="flex:none;margin-top:2px"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
						<p style="margin:0;font-size:15px;line-height:1.5;max-width:72ch;text-wrap:pretty">{{ para.t }}</p>
					</div>
				</div>
				<div v-if="sec.hasF" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0 24px">
					<div v-for="fa in sec.f" :key="fa.l" style="display:flex;flex-direction:column;gap:6px;padding:10px 0 12px;border-top:1px solid var(--kt-color-divider)">
						<span class="kt-label">{{ fa.l }}</span>
						<span v-if="fa.hasChip"><span :class="fa.chip">{{ fa.v }}</span></span>
						<span v-if="fa.noChip" class="kt-meta-value" style="font-size:15px;font-weight:600" :data-testid="`awd-fact-${slug(fa.l)}`">{{ fa.v }}</span>
					</div>
				</div>
				<div v-if="sec.hasD" style="display:grid;gap:12px">
					<div v-for="de in sec.d" :key="de.l" style="display:grid;gap:4px"><span class="kt-label">{{ de.l }}</span><p style="margin:0;font-size:15px;line-height:1.5;max-width:72ch;text-wrap:pretty" :data-testid="`awd-def-${slug(de.l)}`">{{ de.v }}</p></div>
				</div>
				<div v-if="sec.hasTbl" style="overflow-x:auto">
					<table class="table">
						<thead><tr><th v-for="h in sec.th" :key="h.t" :class="h.cls">{{ h.t }}</th></tr></thead>
						<tbody>
							<tr v-for="(r, ri) in rowsOf(sec)" :key="ri">
								<td v-for="(c, ci) in r.cells" :key="ci" :class="c.cls"><span v-if="c.hasChip" :class="c.chip">{{ c.t }}</span><template v-if="c.noChip">{{ c.t }}</template></td>
								<td v-if="r.hasA" style="text-align:right"><button type="button" class="btn btn-primary" :disabled="pending" :data-testid="`awd-row-action-${ri}`" @click="emit('action', r.action)">{{ r.a }}</button></td>
							</tr>
						</tbody>
					</table>
					<TablePagerHost
						v-if="sec.paged"
						:total="sec.rows.length"
						:page="pagedView(sec.paged, sec.rows).page"
						:page-size="pagedView(sec.paged, sec.rows).pageSize"
						noun="award task"
						@update:page="(n) => setPagedPage(sec.paged, n)"
						@update:page-size="(n) => setPagedSize(sec.paged, n)"
					/>
				</div>
				<div v-if="sec.hasEmpty" class="kt-empty">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="1"></rect><path d="M3 10h18"></path></svg>
					<p style="margin:0" data-testid="awd-empty">{{ sec.empty }}</p>
				</div>
				<div v-if="sec.hasFld" style="display:grid;gap:16px;max-width:720px">
					<div v-for="fd in sec.fld" :key="fd.label" class="field">
						<label :for="fd.name ? `awd-${fd.name}` : undefined">{{ fd.label }}</label>
						<div v-if="fd.isRadio" style="display:flex;gap:20px;flex-wrap:wrap;padding-top:4px">
							<label v-for="o in fd.opts" :key="o.label" class="radio"><input type="radio" :name="o.name" :checked="o.checked" :data-testid="`awd-choice-${slug(o.label)}`" @change="set(fd.name, o.value)"><span class="dot"></span>{{ o.label }}</label>
						</div>
						<textarea v-if="fd.isArea" :id="`awd-${fd.name}`" class="input" :value="fd.value" :readonly="!fd.name" :data-testid="`awd-field-${fd.name || slug(fd.label)}`" @input="set(fd.name, $event.target.value)"></textarea>
						<input v-if="fd.isInput" :id="`awd-${fd.name}`" class="input" :value="fd.value" :readonly="!fd.name" :data-testid="`awd-field-${fd.name || slug(fd.label)}`" @input="set(fd.name, $event.target.value)">
						<p v-if="fieldError(fd)" style="margin:0;font-size:14px;font-weight:600;color:var(--kt-status-critical)" :data-testid="`awd-error-${fd.name}`">{{ fieldError(fd) }}</p>
					</div>
				</div>
				<div v-if="sec.hasNote" class="kt-group"><p style="margin:0;font-size:14px;color:var(--kt-color-neutral-800)" data-testid="awd-note">{{ sec.note }}</p></div>
			</div>
		</div>

		<div v-if="error" class="kt-notice is-critical" data-testid="awd-error" role="alert"><div class="kt-notice-body"><strong>{{ error }}</strong><div v-for="(r, ri) in reasons" :key="ri" style="margin-top:2px">{{ r }}</div></div></div>

		<div v-if="m.hasDecision" class="kt-decision" data-testid="awd-actions">
			<div style="display:flex;justify-content:flex-end;gap:12px;flex-wrap:wrap">
				<button v-for="a in m.acts" :key="a.label" type="button" :class="a.cls" :disabled="a.disabled || pending" :data-testid="`awd-action-${slug(a.label)}`" @click="emit('action', a)">{{ a.label }}</button>
			</div>
		</div>
		<div v-if="m.hasRow" style="display:flex;gap:12px;flex-wrap:wrap" data-testid="awd-actions">
			<button v-for="a in m.acts" :key="a.label" type="button" :class="a.cls" :disabled="a.disabled || pending" :data-testid="`awd-action-${slug(a.label)}`" @click="emit('action', a)">{{ a.label }}</button>
		</div>

		<div v-if="m.hasDisc">
			<div v-for="dc in m.disc" :key="dc.key" class="kt-disclosure" :data-testid="`awd-disclosure-${slug(dc.t)}`">
				<div class="kt-disclosure-head" style="cursor:pointer" @click="toggle(dc.key)">
					<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ dc.t }}</span></div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': !!open[dc.key] }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
				</div>
				<div v-if="open[dc.key]" class="kt-disclosure-body" style="display:grid;gap:8px">
					<p v-for="(ln, li) in dc.lines" :key="li" style="margin:0;font-size:14px">{{ ln }}</p>
					<div v-if="dc.a"><button type="button" class="btn btn-secondary" :disabled="pending" :data-testid="`awd-disclosure-action-${slug(dc.a.label)}`" @click="emit('action', dc.a)">{{ dc.a.label }}</button></div>
				</div>
			</div>
		</div>

		<div v-if="m.isDialog" class="dialog-backdrop" data-testid="awd-dialog" style="position:fixed;inset:0;align-items:start;padding-top:160px" @click.self="emit('action', { action: 'close-dialog' })" @keydown.esc.stop="emit('action', { action: 'close-dialog' })">
			<div class="dialog" role="dialog" aria-modal="true" style="width:520px;max-width:calc(100% - 32px)">
				<div class="dialog-title">{{ m.dt }}</div>
				<div v-if="m.hasDb" class="dialog-body" data-testid="awd-dialog-body">{{ m.db }}</div>
				<div v-for="fd in m.dfld" :key="fd.label" class="field">
					<label :for="fd.name ? `awd-dlg-${fd.name}` : undefined">{{ fd.label }}</label>
					<p v-if="fd.isRo" style="margin:0;font-size:14px;font-weight:600">{{ fd.value }}</p>
					<div v-if="fd.isRadio" style="display:grid;gap:8px;padding-top:4px">
						<label v-for="o in fd.opts" :key="o.label" class="radio"><input type="radio" :name="o.name" :checked="o.checked" :data-testid="`awd-dialog-choice-${slug(o.label)}`" @change="set(fd.name, o.value)"><span class="dot"></span>{{ o.label }}</label>
					</div>
					<textarea v-if="fd.isArea" :id="`awd-dlg-${fd.name}`" class="input" :value="fd.value" :data-testid="`awd-dialog-field-${fd.name}`" @input="set(fd.name, $event.target.value)"></textarea>
					<input v-if="fd.isInput" :id="`awd-dlg-${fd.name}`" class="input" :value="fd.value" :data-testid="`awd-dialog-field-${fd.name}`" @input="set(fd.name, $event.target.value)">
					<p v-if="fieldError(fd)" style="margin:0;font-size:14px;font-weight:600;color:var(--kt-status-critical)" :data-testid="`awd-dialog-error-${fd.name}`">{{ fieldError(fd) }}</p>
				</div>
				<div v-if="error" class="kt-notice is-critical" role="alert" data-testid="awd-dialog-refusal"><div class="kt-notice-body"><strong>{{ error }}</strong><div v-for="(r, ri) in reasons" :key="ri" style="margin-top:2px">{{ r }}</div></div></div>
				<div class="dialog-actions">
					<button v-for="a in m.dacts" :key="a.label" type="button" :class="a.cls" :disabled="a.action !== 'close-dialog' && pending" :data-testid="`awd-dialog-${slug(a.label)}`" @click="emit('action', a)">{{ a.label }}</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { norm, slug } from "./model.js";
import AwdGuidance from "./AwdGuidance.vue";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { pagedView, setPagedPage, setPagedSize } from "../../pager_shared/usePagedRows.js";

const props = defineProps({
	board: { type: Object, required: true },
	form: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: { type: String, default: "" },
	reasons: { type: Array, default: () => [] },
	fields: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["action", "update"]);
const m = computed(() => norm(props.board, props.form));
// The table-pagination standard (AGENTS.md §6.11): a table the screen marks `paged` shows one page of its rows.
const rowsOf = (sec) => (sec.paged ? pagedView(sec.paged, sec.rows).rows : sec.rows);
const open = reactive({});

const toggle = (key) => { open[key] = !open[key]; };
const fieldError = (fd) => (fd.name && props.fields ? props.fields[fd.name] || "" : "") || fd.err || "";
function set(name, value) {
	if (name) emit("update", { name, value });
}
</script>
