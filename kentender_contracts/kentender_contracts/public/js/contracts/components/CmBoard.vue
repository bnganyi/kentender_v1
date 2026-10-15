<!-- CmBoard — one Contract Management record screen, drawn from the server's board (CM-CHG-001 v0.8 section 10). The markup is `design/CM Artboards.dc.html` ported class for class
     (page head, tabs, next step, regions of blocks, the "Evidence and history" disclosure, the footer, the dialog): the board and the live screen are built from the same decisions, and
     `contracts.fidelity.spec.js` compares the containers they use. The server decides what the viewer may do; this draws its answer and carries the form the person fills in.

     Choosing one person or one native record is the shared record picker (AGENTS.md section 6.12), never a dropdown. The text "Illustrative test record" the design prints beside the heading is
     not drawn (DEC-044: no test labels on a user-facing surface). -->
<template>
	<div class="kt-page" :data-testid="`cm-board-${board.id}`" :data-board="board.id" :data-tab="board.tab">
		<div class="kt-page-head">
			<div>
				<h1 class="kt-page-title">{{ board.title }}</h1>
				<p class="kt-page-desc">{{ board.sub }}</p>
				<div style="display: flex; align-items: center; gap: 10px; margin-top: 10px; font-size: 13px; color: var(--color-neutral-700)">
					<span data-testid="cm-ref">{{ board.ref }}</span><span class="kt-status" :class="statusClass(board.st)" data-testid="cm-status">{{ board.st }}</span>
				</div>
			</div>
			<div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px">
				<button type="button" class="btn btn-ghost" data-testid="cm-back" @click="$emit('back')">
					<svg class="kt-icon is-sm" viewBox="0 0 24 24"><path d="m12 19-7-7 7-7"></path><path d="M19 12H5"></path></svg>{{ board.back }}
				</button>
			</div>
		</div>

		<div v-if="board.tab" class="kt-tabs" role="tablist">
			<label v-for="tab in board.tabs" :key="tab.label" class="kt-tab" :data-testid="`cm-tab-${tab.label.toLowerCase()}`">
				<input type="radio" :name="`tab-${board.id}`" :checked="tab.label === board.tab" @change="$emit('tab', tab.label)" />{{ tab.label }}
			</label>
		</div>

		<div v-if="refusal" class="kt-notice is-critical" role="alert" data-testid="cm-refusal">
			<div class="kt-notice-body">
				<strong>{{ refusal.message }}</strong>
				<ul v-if="refusal.reasons && refusal.reasons.length > 1" style="margin: 6px 0 0 18px">
					<li v-for="reason in refusal.reasons" :key="reason.code + JSON.stringify(reason.detail)">{{ reason.message }} <span style="color: var(--color-neutral-700)">{{ reason.fix }}</span></li>
				</ul>
				<p v-else-if="refusal.reasons && refusal.reasons[0]" style="margin: 4px 0 0; color: var(--color-neutral-700)">{{ refusal.reasons[0].detail && refusal.reasons[0].detail.reason ? refusal.reasons[0].detail.reason + " " : "" }}{{ refusal.reasons[0].fix }}</p>
			</div>
		</div>

		<div v-if="next" style="padding: 2px 0 4px" data-testid="cm-next-step">
			<div v-if="next.turn" class="kt-next-step is-turn" data-kt="next-step"><div class="kt-next-step-label">{{ __("Your turn") }}</div><p class="kt-next-step-headline">{{ next.h }}</p><p v-if="next.s" class="kt-next-step-sentence">{{ next.s }}</p></div>
			<div v-if="next.wait" class="kt-next-step is-waiting" data-kt="next-step"><div class="kt-next-step-label">{{ __("Waiting on someone") }}</div><p class="kt-next-step-headline">{{ next.h }}</p><p v-if="next.s" class="kt-next-step-sentence">{{ next.s }}</p></div>
			<div v-if="next.done" class="kt-next-step is-done" data-kt="next-step"><div class="kt-next-step-label">{{ __("Done") }}</div><p class="kt-next-step-headline">{{ next.h }}</p><p v-if="next.s" class="kt-next-step-sentence">{{ next.s }}</p></div>
			<div v-if="next.blk" class="kt-notice is-warning kt-next-step" role="status" data-kt="next-step">
				<div class="kt-notice-body">
					<div class="kt-next-step-label">{{ __("Your turn, blocked") }}</div>
					<p class="kt-next-step-headline">{{ next.h }}</p>
					<p v-if="next.s2" class="kt-next-step-sentence">{{ next.s2 }}</p>
					<p v-if="next.s" class="kt-next-step-sentence">{{ next.s }}</p>
					<div v-if="next.fixes.length" class="kt-next-step-fixes">
						<template v-for="fix in next.fixes" :key="fix.l">
							<button v-if="fix.primary" type="button" class="btn btn-primary" @click="act(fix.l)">{{ fix.l }}</button>
							<button v-if="fix.sec" type="button" class="btn btn-secondary" @click="act(fix.l)">{{ fix.l }}</button>
						</template>
					</div>
				</div>
			</div>
		</div>

		<section v-for="(region, ri) in regions" :key="ri" class="kt-region">
			<h2 v-if="region.t">{{ region.t }}</h2>
			<div style="display: flex; flex-direction: column; gap: 16px">
				<template v-for="(b, bi) in region.b" :key="bi">
					<BoardBlock :block="b" :form="form" :errors="errors" :board="board" :disabled="busy" @act="act" />
				</template>
			</div>
		</section>

		<div class="kt-disclosure">
			<div class="kt-disclosure-head" style="padding-left: 0; padding-right: 0" role="button" tabindex="0" @click="evidenceOpen = !evidenceOpen" @keydown.enter="evidenceOpen = !evidenceOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ __("Evidence and history") }}</span></div>
				<svg class="kt-icon is-sm kt-disclosure-chevron" :class="{ 'is-open': evidenceOpen }" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"></path></svg>
			</div>
			<div v-if="evidenceOpen" class="kt-disclosure-body" style="padding-left: 0; padding-right: 0">
				<div v-if="board.ev.length" style="display: flex; flex-direction: column; gap: 8px; font-size: 14px">
					<a v-for="e in board.ev" :key="e" href="#" @click.prevent="act('History')">{{ e }}</a>
				</div>
				<p v-else style="margin: 0; font-size: 14px; color: var(--color-neutral-700)">{{ __("No evidence links are supplied for this view.") }}</p>
			</div>
		</div>

		<div v-if="board.p || secondary.length" style="display: flex; flex-wrap: wrap; gap: 10px; padding-top: 20px; border-top: 1px solid var(--color-divider)" data-testid="cm-footer">
			<button v-if="board.p" type="button" class="btn btn-primary" :disabled="busy" data-testid="cm-primary" @click="act(board.p)">{{ board.p }}</button>
			<button v-for="a in secondary" :key="a.l" type="button" class="btn btn-secondary" :disabled="busy || a.off" :data-testid="`cm-secondary-${slug(a.l)}`" @click="act(a.l)">{{ a.l }}</button>
		</div>

		<div v-if="dialog" class="dialog-backdrop" data-testid="cm-dialog-backdrop" @keydown.esc="closeDialog">
			<div class="dialog" role="dialog" aria-modal="true" :aria-label="dialog.t" style="width: 520px; max-width: 520px" data-testid="cm-dialog">
				<div class="dialog-title">{{ dialog.t }}</div>
				<div class="dialog-body" style="display: flex; flex-direction: column; gap: 14px">
					<template v-for="(b, bi) in dialog.b" :key="bi">
						<BoardBlock :block="b" :form="form" :errors="errors" :board="board" :dialog="true" :disabled="busy" @act="act" />
					</template>
				</div>
				<div class="dialog-actions">
					<button v-for="label in dialog.s2" :key="label" type="button" class="btn btn-secondary" :disabled="busy" @click="closeDialog">{{ label }}</button>
					<button v-if="dialog.p" type="button" class="btn btn-primary" :disabled="busy" data-testid="cm-dialog-primary" @click="submitDialog">{{ dialog.p }}</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import BoardBlock from "./BoardBlock.vue";
import { initialValues, nextView, statusClass } from "../board_view.js";

const props = defineProps({
	board: { type: Object, required: true },
	busy: { type: Boolean, default: false },
	errors: { type: Object, default: () => ({}) },
	refusal: { type: Object, default: null },
});
const emit = defineEmits(["run", "route", "tab", "back"]);

const evidenceOpen = ref(false);
const dialogKey = ref("");
const form = reactive({});

const next = computed(() => nextView(props.board.next));
const regions = computed(() => props.board.regions || []);
const secondary = computed(() => (props.board.s2 || []).map((l) => ({ l: l.replace(/^-/, ""), off: l[0] === "-" })));
const dialog = computed(() => (dialogKey.value ? props.board.dialogs[dialogKey.value] : null));

// A new board (another screen, or the same one after a command) starts from the values it was built with; the same board drawn again keeps what the person typed.
watch(
	() => [props.board.id, props.board.case, props.board.version],
	() => {
		for (const key of Object.keys(form)) delete form[key];
		Object.assign(form, initialValues(props.board));
		for (const d of Object.values(props.board.dialogs || {})) Object.assign(form, initialValues({ regions: [{ b: d.b }] }));
		dialogKey.value = "";
	},
	{ immediate: true }
);

function slug(label) {
	return String(label).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function closeDialog() {
	dialogKey.value = "";
}

// Values of the screen's own fields (not a dialog's), or of one dialog's.
function valuesFor(blocks) {
	const names = Object.keys(initialValues({ regions: [{ b: blocks }] }));
	return Object.fromEntries(names.map((n) => [n, form[n]]));
}

function act(label) {
	const spec = (props.board.actions || {})[label];
	if (!spec) return;
	if (spec.do === "dialog") dialogKey.value = spec.dialog;
	else if (spec.do === "tab") emit("tab", spec.tab);
	else if (spec.do === "route") emit("route", spec.route);
	else if (spec.do === "download") {
		const link = document.createElement("a");
		link.href = spec.url;
		link.download = "";
		document.body.appendChild(link);
		link.click();
		link.remove();
	} else if (spec.do === "command") {
		// the screen's own fields, and those of a dialog that only gathers input for it (the unit references typed in a dialog belong to the delivery the page records)
		const local = Object.values(props.board.dialogs || {}).filter((d) => d.local).flatMap((d) => d.b);
		emit("run", { spec, values: valuesFor([...regions.value.flatMap((r) => r.b), ...local]) });
	}
}

function submitDialog() {
	const d = dialog.value;
	if (!d) return;
	if (d.local) {
		closeDialog();
		return;
	}
	emit("run", { spec: { do: "command", command: d.command, args: d.args || {} }, values: valuesFor(d.b), dialog: true });
}

defineExpose({ closeDialog, form });
</script>
