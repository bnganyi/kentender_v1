<!-- One Bid Evaluation screen, drawn exactly as the artboards draw it
     (EVL-CHG-001 v0.4 §9; `15_bid_evaluation/design/Bid Evaluation Artboards.dc.html`,
     the <main> page template): the page head with its icon, the page tabs,
     the guidance region (journey and next step), the blocks, the action bar
     with its consequence line, and a 520 px dialog. The markup and classes are
     the board template's, container for container; the only differences are
     live ones: inputs edit `form`, and every button, tab, link and table
     button emits the action the screen named. Disclosures start closed. -->
<template>
	<div class="kt-page evl-board" :class="{ 'is-mobile': m.isMobile }" data-testid="evl-board" :style="m.isMobile ? 'padding:16px' : ''">
		<a v-if="m.hasBack" href="#" style="font-size:14px" data-testid="evl-back" @click.prevent="emit('action', { action: m.backAction || 'back' })">← {{ m.back }}</a>
		<div v-if="m.hasHead" class="kt-page-head" style="justify-content:flex-start;align-items:center;gap:16px">
			<div style="width:48px;height:48px;flex:none;display:grid;place-items:center;background:var(--color-accent-100);color:var(--color-accent-700)"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="m.icon"></path></svg></div>
			<div style="display:grid;gap:6px;min-width:0"><h1 class="kt-page-title" data-testid="evl-title">{{ m.title }}</h1><p v-if="m.hasDesc" class="kt-page-desc" style="margin:0" data-testid="evl-desc">{{ m.desc }}</p></div>
		</div>
		<div v-if="m.hasTabs" class="kt-tabs" role="tablist">
			<button v-for="t in m.tabs" :key="t.t" type="button" role="tab" class="kt-tab" :aria-selected="t.on ? 'true' : 'false'" :data-testid="`evl-tab-${slug(t.t)}`" @click="!t.on && emit('action', { action: t.action, args: t.args })">{{ t.t }}</button>
		</div>

		<EvlGuidance v-if="board.guidance" :answer="board.guidance.answer" :journey="board.guidance.journey" :pending="pending" @fix="emit('action', { action: 'fix', args: $event })" />
		<p v-if="m.hasNotInvolved" style="margin:0;font-size:14px;color:var(--color-neutral-800)">{{ m.notInvolved }}</p>

		<div v-for="(b, bi) in m.blocks" :key="bi" :id="b.anchor ? `evl-${slug(b.anchor)}` : undefined" style="display:grid;gap:10px;min-width:0" :data-testid="b.testid || `evl-block-${bi}`">
			<h2 v-if="b.titleMain" style="display:flex;align-items:center;gap:8px;margin:0;font-family:var(--font-heading);font-weight:600;font-size:21px;line-height:1.2"><span v-if="b.hasIcon" style="color:var(--color-accent-700);display:flex"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="b.icon"></path></svg></span>{{ b.title }}</h2>
			<h2 v-if="b.titleSec" style="display:flex;align-items:center;gap:8px;margin:0;font-family:var(--font-heading);font-weight:600;font-size:17px;line-height:1.2;color:var(--color-neutral-800)"><span v-if="b.hasIcon" style="color:var(--color-accent-700);display:flex"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="b.icon"></path></svg></span>{{ b.title }}</h2>

			<template v-if="b.is_p">
				<p v-if="b.plain" style="margin:0;font-size:15px;max-width:78ch;text-wrap:pretty">{{ b.t }}</p>
				<p v-if="b.isMuted" style="margin:0;font-size:15px;color:var(--color-neutral-700)">{{ b.t }}</p>
				<p v-if="b.isStrong" style="margin:0;font-size:17px;font-weight:600;max-width:78ch;text-wrap:pretty">{{ b.t }}</p>
			</template>

			<div v-if="b.is_facts" class="kt-group"><div class="kt-meta-row">
				<div v-for="it in b.itemList" :key="it.l"><span class="kt-label">{{ it.l }}</span><span v-if="it.plain" style="font-size:15px;font-weight:600">{{ it.v }}</span><span v-if="it.chip"><span class="kt-status" :class="it.cls">{{ it.v }}</span></span><span v-if="it.person" style="display:flex;align-items:center;gap:8px;font-size:15px;font-weight:600"><span class="kt-sidebar-avatar">{{ it.ini }}</span>{{ it.v }}</span></div>
			</div></div>

			<div v-if="b.is_kv" style="display:grid;gap:10px">
				<div v-for="r in b.rowList" :key="r.l" :style="`display:grid;grid-template-columns:${b.cols};gap:2px 24px;font-size:15px;padding-bottom:10px;border-bottom:1px solid var(--color-divider)`">
					<div style="font-size:14px;font-weight:600;color:var(--color-neutral-700)">{{ r.l }}</div>
					<div style="text-wrap:pretty"><template v-if="r.plain">{{ r.v }}</template><span v-if="r.chip" class="kt-status" :class="r.cls">{{ r.v }}</span><span v-if="r.person" style="display:inline-flex;align-items:center;gap:8px"><span class="kt-sidebar-avatar">{{ r.ini }}</span>{{ r.v }}</span></div>
				</div>
			</div>

			<template v-if="b.is_table">
				<table class="kt-table">
					<thead><tr><th v-for="h in b.ths" :key="h.t" :class="h.td">{{ h.t }}</th></tr></thead>
					<tbody>
						<tr v-for="(r, ri) in b.trs" :key="ri">
							<td v-for="(c, ci) in r.cells" :key="ci" :class="c.td">
								<template v-if="c.txt">{{ c.t }}</template>
								<strong v-if="c.strong">{{ c.t }}</strong><span v-if="c.person" style="display:inline-flex;align-items:center;gap:8px;white-space:nowrap"><span class="kt-sidebar-avatar">{{ c.ini }}</span>{{ c.t }}</span>
								<span v-if="c.chip" class="kt-status" :class="c.cls">{{ c.t }}</span>
								<button v-if="c.btn" type="button" class="kt-btn kt-btn-secondary" style="padding:4px 10px;font-size:13px" :disabled="pending" :data-testid="c.testid || undefined" @click="emit('action', { action: c.action, args: c.args })">{{ c.t }}</button>
								<div v-if="c.inp" class="kt-input" style="padding:6px 10px">{{ c.t }}</div>
								<select v-if="c.sel" class="kt-input" style="padding:6px 10px" :value="form[c.name] ?? ''" :data-testid="c.testid || undefined" @change="set(c.name, $event.target.value)"><option v-for="o in c.options" :key="o.value" :value="o.value">{{ o.label }}</option></select>
								<input v-if="c.field" class="kt-input" style="padding:6px 10px" :value="form[c.name] ?? ''" :data-testid="c.testid || undefined" @input="set(c.name, $event.target.value)">
								<p v-if="c.err" style="margin:4px 0 0;font-size:13px;font-weight:600;color:var(--status-critical)">{{ c.err }}</p>
							</td>
						</tr>
					</tbody>
				</table>
				<p v-if="b.hasCaption" style="margin:0;font-size:14px;color:var(--color-neutral-700)">{{ b.caption }}</p>
			</template>

			<div v-if="b.is_notice" class="kt-notice" :class="b.cls">
				<svg v-if="b.iWarn" class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3l9 16H3z"></path><path d="M12 10v4M12 17h.01"></path></svg>
				<svg v-if="b.iCrit" class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 6L6 18M6 6l12 12"></path></svg>
				<svg v-if="b.iInfo" class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"></circle><path d="M12 8h.01M11 12h1v5h1"></path></svg>
				<div class="kt-notice-body"><strong>{{ b.t }}</strong><div v-if="b.hasD" style="margin-top:2px">{{ b.d }}</div></div>
			</div>

			<div v-if="b.is_field" class="kt-field" style="max-width:720px">
				<label style="display:flex;gap:4px" :for="`evl-${b.name}`">{{ b.label }}<span v-if="b.req" style="color:var(--status-critical)">*</span></label>
				<input v-if="b.isInput" :id="`evl-${b.name}`" class="kt-input" :type="b.type || 'text'" :placeholder="b.ph || ''" :readonly="!b.name" :value="valueOf(b)" :data-testid="`evl-field-${b.name || bi}`" @input="set(b.name, $event.target.value)">
				<textarea v-if="b.isArea" :id="`evl-${b.name}`" class="kt-input" :rows="b.rowsN" :readonly="!b.name" :value="valueOf(b)" :data-testid="`evl-field-${b.name || bi}`" @input="set(b.name, $event.target.value)"></textarea>
				<div v-if="b.isSelect && !b.options" class="kt-input" style="display:flex;justify-content:space-between;align-items:center;gap:12px"><span>{{ b.value }}</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg></div>
				<select v-if="b.isSelect && b.options" :id="`evl-${b.name}`" class="kt-input" :value="valueOf(b)" :data-testid="`evl-field-${b.name}`" @change="set(b.name, $event.target.value)"><option v-for="o in b.options" :key="o.value" :value="o.value">{{ o.label }}</option></select>
				<div v-if="b.isFile" class="kt-input" style="display:flex;align-items:center;gap:12px"><button type="button" class="kt-btn kt-btn-secondary" style="padding:4px 10px;font-size:13px" @click="emit('action', { action: b.action || 'choose-file', args: { name: b.name } })">Choose file</button><span style="color:var(--color-neutral-700)">{{ b.fileName || "No file chosen" }}</span></div>
				<p v-if="b.hasHelp" style="margin:0;font-size:13px;color:var(--color-neutral-700)">{{ b.help }}</p>
				<p v-if="b.hasErr || fieldError(b)" style="margin:0;font-size:14px;font-weight:600;color:var(--status-critical)" :data-testid="`evl-error-${b.name}`">{{ fieldError(b) || b.err }}</p>
				<p v-if="b.hasErrd" style="margin:0;font-size:13px;color:var(--color-neutral-800)">{{ b.errd }}</p>
			</div>

			<div v-if="b.is_radios" class="kt-field"><label>{{ b.label }}</label>
				<div style="display:grid;gap:6px">
					<label v-for="o in b.options" :key="o.t" class="kt-radio"><input type="radio" :name="b.name || `r${bi}`" :checked="checked(b, o)" :data-testid="`evl-choice-${slug(o.t)}`" @change="set(b.name, o.value)"><span class="dot"></span>{{ o.t }}</label>
				</div>
			</div>

			<div v-if="b.is_seg" class="kt-field"><label>{{ b.label }}</label>
				<div class="kt-seg kt-seg-inline" role="radiogroup" style="width:max-content">
					<label v-for="o in b.options" :key="o.t" class="kt-seg-opt"><input type="radio" :name="b.name || `s${bi}`" :checked="checked(b, o)" :data-testid="`evl-seg-${slug(o.t)}`" @change="set(b.name, o.value); b.action && emit('action', { action: b.action, args: { value: o.value } })">{{ o.t }}</label>
				</div>
			</div>

			<label v-if="b.is_check" class="kt-checkbox"><input type="checkbox" :checked="b.name ? !!form[b.name] : b.on" :data-testid="`evl-check-${b.name || bi}`" @change="set(b.name, $event.target.checked)"><span class="box"></span>{{ b.t }}</label>

			<div v-if="b.is_attn" class="kt-group" style="display:flex;gap:12px;align-items:flex-start;border-left-color:var(--color-accent-300)">
				<span v-if="b.hasWho" class="kt-sidebar-avatar" style="margin-top:2px">{{ b.ini }}</span>
				<div style="display:grid;gap:2px;min-width:0">
					<div style="font-size:16px;font-weight:600;text-wrap:pretty">{{ b.t }}</div>
					<div v-if="b.hasMeta" style="font-size:14px;color:var(--color-neutral-700)">{{ b.meta }}</div>
				</div>
			</div>

			<div v-if="b.is_disc" class="kt-disclosure">
				<div class="kt-disclosure-head" style="cursor:pointer" :data-testid="`evl-disclosure-${slug(b.t)}`" @click="toggle(b, bi)">
					<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ b.t }}</span></div>
					<svg class="kt-disclosure-chevron" :class="{ 'is-open': isOpen(b, bi) }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
				</div>
				<div v-if="isOpen(b, bi)" class="kt-disclosure-body" style="display:grid;gap:6px">
					<p v-for="(ln, li) in b.lineList" :key="li" style="margin:0;font-size:14px">{{ ln.t }}</p>
					<div v-if="b.hasLinks" style="display:flex;gap:16px;flex-wrap:wrap;font-size:14px"><a v-for="l in b.linkList" :key="l.t" href="#" @click.prevent="emit('action', { action: l.action, args: l.args })">{{ l.t }}</a></div>
				</div>
			</div>

			<div v-if="b.is_links" style="display:flex;gap:8px 20px;flex-wrap:wrap;font-size:14px"><a v-for="l in b.linkList" :key="l.t" href="#" :data-testid="`evl-link-${slug(l.t)}`" @click.prevent="emit('action', { action: l.action, args: l.args })">{{ l.t }}</a></div>

			<div v-if="b.is_evid" style="display:flex;gap:12px 28px;flex-wrap:wrap">
				<div v-for="(it, ii) in b.itemList" :key="ii" style="display:flex;align-items:center;gap:10px"><span style="width:32px;height:32px;display:grid;place-items:center;border:1px solid var(--color-divider);color:var(--color-accent-700)"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8"></path></svg></span><span style="font-size:14px;font-weight:600">{{ it.t }}</span><button type="button" class="kt-btn kt-btn-secondary" style="padding:4px 10px;font-size:13px" @click="emit('action', { action: it.action, args: it.args })">{{ it.b }}</button></div>
			</div>

			<div v-if="b.is_task" class="kt-task-row" :data-testid="`evl-task-${bi}`">
				<div style="width:40px;height:40px;flex:none;display:grid;place-items:center;background:var(--color-accent-100);color:var(--color-accent-700)"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2h6v4H9z M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M9 14l2 2 4-4"></path></svg></div>
				<div style="flex:1;min-width:0;display:grid;gap:2px">
					<div style="font-family:var(--font-heading);font-size:20px;font-weight:600;line-height:1.15">{{ b.tt }}</div>
					<div style="font-size:13px;color:var(--color-neutral-700)">{{ b.ref }}</div>
					<div style="font-size:14px;color:var(--color-neutral-800)">{{ b.state }}</div>
				</div>
				<button type="button" class="kt-btn kt-btn-primary" @click="emit('action', { action: b.button.action, args: b.button.args })">{{ b.button.t }}</button>
			</div>

			<div v-if="b.is_filter" class="kt-filter-bar">
				<div v-for="c in b.cellList" :key="c.l" class="kt-field" :class="c.cls"><label>{{ c.l }}</label>
					<input v-if="c.inp" class="kt-input" :placeholder="c.ph" :value="c.name ? form[c.name] || '' : c.v" :data-testid="`evl-filter-${c.name}`" @input="set(c.name, $event.target.value)">
					<select v-if="c.sel" class="kt-input" :value="c.name ? form[c.name] || '' : c.v" :data-testid="`evl-filter-${c.name}`" @change="set(c.name, $event.target.value)"><option v-for="o in c.options" :key="o.value" :value="o.value">{{ o.label }}</option></select>
				</div>
			</div>

			<div v-if="b.is_empty" class="kt-empty">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="b.eicon"></path></svg>
				<p style="margin:0 0 12px;font-size:17px;font-weight:600">{{ b.t }}</p><p v-if="b.hasSub" style="margin:0 auto 12px;max-width:62ch;font-size:15px;text-wrap:pretty">{{ b.sub }}</p>
				<button v-if="b.hasBtn" type="button" class="kt-btn kt-btn-secondary" @click="emit('action', { action: b.btnAction })">{{ b.btn }}</button>
			</div>
		</div>

		<div v-if="error" class="kt-notice is-critical" data-testid="evl-error" role="alert"><div class="kt-notice-body"><strong>{{ error }}</strong><div v-for="(r, ri) in reasons" :key="ri" style="margin-top:2px">{{ r }}</div></div></div>

		<div v-if="m.hasPri" class="kt-decision" data-testid="evl-actions">
			<div style="display:flex;align-items:center;gap:var(--space-4);flex-wrap:wrap">
				<p v-if="m.hasCons" style="margin:0;flex:1;min-width:240px;font-size:14px;color:var(--color-neutral-800);text-wrap:pretty">{{ m.cons }}</p>
				<div style="display:flex;gap:var(--space-3);margin-left:auto;flex-wrap:wrap;justify-content:flex-end">
					<button v-for="s in m.sec" :key="s.t" type="button" class="kt-btn kt-btn-secondary" :disabled="s.dis || pending" style="display:inline-flex;align-items:center;gap:8px" :data-testid="`evl-action-${slug(s.t)}`" @click="emit('action', { action: s.action, args: s.args })"><svg v-if="s.hasIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="s.icon"></path></svg>{{ s.t }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="m.pri.dis || pending" style="display:inline-flex;align-items:center;gap:8px" :data-testid="`evl-action-${slug(m.pri.t)}`" @click="emit('action', { action: m.pri.action, args: m.pri.args })"><svg v-if="m.pri.hasIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="m.pri.icon"></path></svg>{{ m.pri.t }}</button>
				</div>
			</div>
		</div>
		<div v-if="m.onlySec" style="display:flex;gap:var(--space-3);justify-content:flex-end;flex-wrap:wrap;padding-top:var(--space-4);border-top:1px solid var(--color-divider)" data-testid="evl-actions">
			<button v-for="s in m.sec" :key="s.t" type="button" class="kt-btn kt-btn-secondary" :disabled="s.dis || pending" style="display:inline-flex;align-items:center;gap:8px" :data-testid="`evl-action-${slug(s.t)}`" @click="emit('action', { action: s.action, args: s.args })"><svg v-if="s.hasIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="s.icon"></path></svg>{{ s.t }}</button>
		</div>

		<div v-if="m.hasDlg" class="kt-dialog-backdrop" data-testid="evl-dialog" style="position:fixed;inset:0;align-items:start;padding-top:180px" @click.self="emit('action', { action: 'close-dialog' })" @keydown.esc.stop="emit('action', { action: 'close-dialog' })">
			<div class="kt-dialog" role="dialog" aria-modal="true" style="width:520px;max-width:calc(100% - 32px)">
				<div class="kt-dialog-title">{{ m.dlg.t }}</div>
				<div class="dialog-body" style="display:grid;gap:14px">
					<template v-for="(b, di) in m.dlg.blocks" :key="di">
						<div v-if="b.is_kv" style="display:grid;gap:6px"><div v-for="r in b.rowList" :key="r.l" style="font-size:14px"><span style="font-weight:600;color:var(--color-neutral-700)">{{ r.l }}: </span>{{ r.v }}</div></div>
						<div v-if="b.is_field" class="kt-field"><label style="display:flex;gap:4px" :for="`evl-dlg-${b.name}`">{{ b.label }}<span v-if="b.req" style="color:var(--status-critical)">*</span></label>
							<textarea v-if="b.isArea" :id="`evl-dlg-${b.name}`" class="kt-input" :rows="b.rowsN" :value="valueOf(b)" :data-testid="`evl-dialog-field-${b.name}`" @input="set(b.name, $event.target.value)"></textarea>
							<input v-if="b.isInput" :id="`evl-dlg-${b.name}`" class="kt-input" :value="valueOf(b)" :data-testid="`evl-dialog-field-${b.name}`" @input="set(b.name, $event.target.value)">
							<p v-if="fieldError(b)" style="margin:0;font-size:14px;font-weight:600;color:var(--status-critical)">{{ fieldError(b) }}</p>
						</div>
					</template>
					<p v-if="m.dlg.hasCons" style="margin:0;font-size:14px;color:var(--color-neutral-800)">{{ m.dlg.cons }}</p>
				</div>
				<div class="kt-dialog-actions">
					<button v-for="s in m.dlg.sec" :key="s.t" type="button" class="kt-btn kt-btn-secondary" :data-testid="`evl-dialog-${slug(s.t)}`" @click="emit('action', { action: s.action || 'close-dialog', args: s.args })">{{ s.t }}</button>
					<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" style="display:inline-flex;align-items:center;gap:8px" :data-testid="`evl-dialog-${slug(m.dlg.pri.t)}`" @click="emit('action', { action: m.dlg.pri.action, args: m.dlg.pri.args })"><svg v-if="m.dlg.pri.hasIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="flex:none"><path :d="m.dlg.pri.icon"></path></svg>{{ m.dlg.pri.t }}</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive } from "vue";
import { norm } from "./model.js";
import EvlGuidance from "./EvlGuidance.vue";

const props = defineProps({
	board: { type: Object, required: true },
	form: { type: Object, default: () => ({}) },
	people: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: { type: String, default: "" },
	reasons: { type: Array, default: () => [] },
	fields: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["action", "update"]);
const m = computed(() => norm(props.board, { people: props.people }));
const open = reactive({});

const slug = (t) => String(t || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
const isOpen = (b, i) => (open[i] === undefined ? !!b.open : open[i]);
const toggle = (b, i) => { open[i] = !isOpen(b, i); };
const valueOf = (b) => (b.name ? (props.form[b.name] ?? "") : b.value || "");
const checked = (b, o) => (b.name && props.form[b.name] !== undefined ? props.form[b.name] === o.value : o.on);
const fieldError = (b) => (b.name && props.fields ? props.fields[b.name] || "" : "");
function set(name, value) {
	if (name) emit("update", { name, value });
}
</script>
