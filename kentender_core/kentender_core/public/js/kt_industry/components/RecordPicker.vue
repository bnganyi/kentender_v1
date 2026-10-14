<!-- The one record picker: a search field that opens a list of matches, for any choice of one
     person or one record from a list that can grow. The list lives on the server (the source
     registry in kentender_core.services.record_picker); this draws what it is given and reports
     what the reader chooses. It is never the authority for who may be chosen: the command that
     saves the choice checks again.

     The caller keeps its own selection and hands it back as `value` (+ `valueLabel`); this binds
     to that, never to a server echo (AGENTS.md section 6.4). `value` null is "nothing chosen";
     with `allLabel`, "" is the "All ..." choice.

     `inline` + `multiple` is the picker for adding several (approved 14 Oct 2026): the list stays open in the page beside the field,
     choosing a row adds that person (`onAdd`) and leaves the list, the search text and the reader's place where they were, and a
     person already in the caller's `staged` list stays in the list greyed. -->
<template>
	<div class="kt-picker" :class="{ 'is-invalid': isInvalid }" data-testid="kt-picker">
		<div class="kt-picker-anchor">
			<div class="kt-picker-field">
				<svg class="kt-picker-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" /></svg>
				<input
					:id="inputId || `${uid}-input`"
					ref="inputEl"
					class="input kt-picker-input"
					:class="{ 'has-choice': hasChoice }"
					type="text"
					role="combobox"
					autocomplete="off"
					spellcheck="false"
					aria-autocomplete="list"
					:aria-expanded="listOpen ? 'true' : 'false'"
					:aria-controls="listId"
					:aria-activedescendant="activeDescendant"
					:aria-invalid="isInvalid ? 'true' : 'false'"
					:aria-required="required ? 'true' : 'false'"
					:aria-describedby="noteId"
					:placeholder="placeholder || t('Search')"
					:value="inputValue"
					:disabled="disabled"
					data-testid="kt-picker-input"
					@input="onInput"
					@keydown="onKeyDown"
					@focus="onFocus"
					@blur="onBlur"
				>
				<button v-if="hasChoice" type="button" class="btn btn-ghost kt-picker-clear" :aria-label="clearLabel" data-testid="kt-picker-clear" @click="onClear">{{ t("Clear") }}</button>
			</div>
			<div
				v-if="listOpen"
				:id="listId"
				ref="listEl"
				class="kt-picker-list"
				:class="{ 'is-updating': busy, 'is-up': up, 'is-inline': inline }"
				:style="listStyle"
				role="listbox"
				:aria-label="listLabel || capitalised(pluralText)"
				:aria-busy="busy ? 'true' : 'false'"
				data-testid="kt-picker-list"
				@mousedown.prevent
			>
				<div v-if="busy && !failed" class="kt-picker-status" role="presentation">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-6.2-8.6" /></svg>
					<span>{{ busyText }}</span>
				</div>
				<div v-if="failed" class="kt-picker-status is-text is-error" role="presentation">
					<span class="kt-picker-status-text">{{ t("Could not load") }} {{ pluralText }}. {{ t("Try again.") }}</span>
					<button type="button" class="btn btn-secondary kt-picker-retry" data-testid="kt-picker-retry" @click="retry">{{ t("Try again") }}</button>
				</div>
				<div v-if="isEmpty" class="kt-picker-status is-text" role="presentation">
					<span class="kt-picker-status-text">{{ t("No") }} {{ nounText }} {{ t("matches") }} “{{ q.trim() }}”.</span>
					<span v-if="hint" class="kt-picker-status-hint">{{ hint }}</span>
				</div>
				<div v-for="group in groups" :key="group.key" role="group" :aria-labelledby="group.title ? group.headId : null" class="kt-picker-section">
					<div v-if="group.title" :id="group.headId" class="kt-picker-group" role="presentation">{{ group.title }}</div>
					<div
						v-for="item in group.rows"
						:id="item.domId"
						:key="item.domId"
						class="kt-picker-option"
						:class="{ 'is-active': item.active, 'is-disabled': !!item.row.disabled_reason }"
						role="option"
						:aria-selected="item.active ? 'true' : 'false'"
						:aria-disabled="item.row.disabled_reason ? 'true' : 'false'"
						:aria-describedby="item.row.disabled_reason ? item.reasonId : null"
						:data-testid="`kt-picker-option-${item.i}`"
						@click="choose(item.row)"
						@mouseenter="hover(item)"
					>
						<div class="kt-picker-name"><template v-for="(s, k) in item.name" :key="k"><mark v-if="s.m" class="kt-picker-mark">{{ s.t }}</mark><template v-else>{{ s.t }}</template></template></div>
						<div v-if="item.row.detail" class="kt-picker-detail"><template v-for="(s, k) in item.detail" :key="k"><mark v-if="s.m" class="kt-picker-mark">{{ s.t }}</mark><template v-else>{{ s.t }}</template></template></div>
						<div v-if="item.row.disabled_reason" :id="item.reasonId" class="kt-picker-reason">
							<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><path d="m4.9 4.9 14.2 14.2" /></svg>
							<span>{{ item.row.disabled_reason }}</span>
						</div>
					</div>
				</div>
				<div v-if="footText" class="kt-picker-foot" role="presentation" data-testid="kt-picker-foot">{{ footText }}</div>
			</div>
		</div>
		<div class="kt-picker-live" role="status" aria-live="polite">{{ liveText }}</div>
		<p v-if="errorText" :id="`${uid}-error`" class="kt-picker-note is-error" data-testid="kt-picker-error">{{ errorText }}</p>
		<p v-else-if="choiceReason" :id="`${uid}-note`" class="kt-picker-note is-error" data-testid="kt-picker-reason">{{ choiceReason }}</p>
	</div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	// A key registered through the kt_record_picker_sources hook.
	source: { type: String, required: true },
	// Opaque to the picker: the source's provider reads it (the tender, the role, who is already taken).
	context: { type: Object, default: () => ({}) },
	// The caller's own selection: null = nothing chosen; "" = the "All ..." choice when allLabel is set.
	value: { type: String, default: null },
	valueLabel: { type: String, default: "" },
	inputId: { type: String, default: "" },
	placeholder: { type: String, default: "" },
	// Wording to use until the source's own arrives with its first answer.
	noun: { type: String, default: "" },
	plural: { type: String, default: "" },
	listLabel: { type: String, default: "" },
	// A first "All ..." row, for a filter.
	allLabel: { type: String, default: "" },
	// Add several: the list stays open in the page beside the field and a choice adds the person (onAdd) instead of selecting.
	inline: { type: Boolean, default: false },
	multiple: { type: Boolean, default: false },
	// Ids the caller has already added, kept in the list greyed; "to appoint" completes "Added X. 3 to appoint."
	staged: { type: Array, default: () => [] },
	stagedReason: { type: String, default: "Added to this list" },
	stagedNoun: { type: String, default: "to add" },
	invalid: { type: Boolean, default: false },
	required: { type: Boolean, default: false },
	disabled: { type: Boolean, default: false },
	errorText: { type: String, default: "" },
	// Keys recent picks to the signed-in person; defaults to frappe.session.user.
	user: { type: String, default: "" },
	// fetch(endpoint, args) -> Promise<result>; the default calls kentender_core.api.record_picker.
	fetch: { type: Function, default: null },
	onChange: { type: Function, default: () => {} },
	onAdd: { type: Function, default: () => {} },
});

const t = (text) => (typeof window !== "undefined" && typeof window.__ === "function" ? window.__(text) : text);
const DEBOUNCE_MS = 250;
const LIMIT = 20;
const RECENT_SHOWN = 5;
const UP_NEEDS_PX = 340;
const LIST_MAX_PX = 340;
const LIST_MIN_PX = 120;
const GAP_PX = 4;
const EDGE_PX = 8;

let counter = 0;
const uid = `ktp${++counter}-${Math.random().toString(36).slice(2, 6)}`;
const listId = `${uid}-list`;

const inputEl = ref(null);
const listEl = ref(null);
const q = ref("");
const open = ref(false);
const status = ref("idle"); // idle | loading | updating | ready | error
const result = ref(null);
const labels = ref(null);
const active = ref(null);
const up = ref(false);
const listStyle = ref({});
const lastAdded = ref("");
const selected = ref(initialSelected());

function initialSelected() {
	if (props.value === null || props.value === undefined) return null;
	return { id: props.value, label: props.valueLabel || (props.value === "" ? props.allLabel : ""), reason: null, all: props.value === "" };
}

// -- who we are talking about ---------------------------------------------------------------------
const nounText = computed(() => labels.value?.noun || props.noun || t("record"));
const pluralText = computed(() => labels.value?.plural || props.plural || t("results"));
const hint = computed(() => labels.value?.hint || "");
const capitalised = (text) => text.charAt(0).toUpperCase() + text.slice(1);

// -- sequence token: a slower, older answer can never overwrite a newer one (AGENTS.md section 6.4)
const guard = (typeof window !== "undefined" && window.kentender_core?.desk_page?.createSequenceGuard?.()) || (() => {
	let token = 0;
	return { next: () => ++token, isCurrent: (candidate) => candidate === token };
})();
let timer = null;

// -- recent picks: ids only, this person, this source; a convenience, so a blocked store is no store
const recentKey = () => `kt.picker.recent.${props.user || window.frappe?.session?.user || ""}.${props.source}`;
function readRecent() {
	try {
		const stored = JSON.parse(window.localStorage.getItem(recentKey()) || "[]");
		return Array.isArray(stored) ? stored.filter((id) => typeof id === "string").slice(0, RECENT_SHOWN) : [];
	} catch (error) {
		return [];
	}
}
function pushRecent(id) {
	try {
		window.localStorage.setItem(recentKey(), JSON.stringify([id, ...readRecent().filter((x) => x !== id)].slice(0, RECENT_SHOWN)));
	} catch (error) {
		// a blocked store only means no recent picks
	}
}

async function call(endpoint, args) {
	if (props.fetch) return props.fetch(endpoint, args);
	const response = await window.frappe.call({ method: `kentender_core.api.record_picker.${endpoint}`, args, freeze: false, silent: true });
	return response.message;
}
const contextText = () => JSON.stringify(props.context || {});

// -- search ---------------------------------------------------------------------------------------
function search(query, { debounce = false } = {}) {
	clearTimeout(timer);
	const token = guard.next();
	open.value = true;
	status.value = result.value ? "updating" : "loading";
	const go = async () => {
		try {
			const answer = await call("search", { source: props.source, query, context: contextText(), recent: JSON.stringify(readRecent()), limit: LIMIT });
			if (!guard.isCurrent(token)) return;
			labels.value = answer.labels || labels.value;
			result.value = answer;
			status.value = "ready";
			active.value = firstChoosable();
		} catch (error) {
			if (!guard.isCurrent(token)) return;
			result.value = null;
			status.value = "error";
			active.value = null;
		}
	};
	if (debounce) timer = setTimeout(go, DEBOUNCE_MS);
	else go();
}

// The list floats over the page (fixed, placed from the field's own position and sized to the room there is), so
// no dialog, table row or scroll area around the field can clip it. It opens upward when there is no room beneath.
function placeList() {
	const el = inputEl.value;
	if (!el || props.inline) return;
	const rect = el.getBoundingClientRect();
	const below = window.innerHeight - rect.bottom - EDGE_PX;
	const above = rect.top - EDGE_PX;
	up.value = below < UP_NEEDS_PX && above > below;
	const room = up.value ? above : below;
	const style = { position: "fixed", left: `${rect.left}px`, width: `${rect.width}px`, maxHeight: `${Math.max(LIST_MIN_PX, Math.min(LIST_MAX_PX, room))}px` };
	if (up.value) style.bottom = `${window.innerHeight - rect.top + GAP_PX}px`;
	else style.top = `${rect.bottom + GAP_PX}px`;
	listStyle.value = style;
}

function watchPlacement(on) {
	if (props.inline) return;
	const method = on ? "addEventListener" : "removeEventListener";
	window[method]("scroll", placeList, true);
	window[method]("resize", placeList);
}

function openList() {
	placeList();
	watchPlacement(true);
	search(q.value);
}

function close() {
	clearTimeout(timer);
	guard.next();
	watchPlacement(false);
	open.value = false;
	if (status.value === "error") status.value = "idle";
}

const busy = computed(() => status.value === "loading" || status.value === "updating");
const failed = computed(() => status.value === "error");
const listOpen = computed(() => (props.inline ? open.value : open.value && !selected.value));
const isEmpty = computed(() => status.value === "ready" && !!result.value?.typed && result.value.rows.length === 0);

// -- what is drawn --------------------------------------------------------------------------------
const norm = (text) => String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const words = (text) => norm(text).split(/[^a-z0-9]+/).filter(Boolean);

function segments(text, tokens) {
	if (!text) return [];
	if (!tokens.length) return [{ t: text, m: false }];
	const out = [];
	let last = 0;
	const pattern = /[\p{L}\p{N}']+/gu;
	let match;
	while ((match = pattern.exec(text))) {
		const word = norm(match[0]);
		const token = tokens.filter((x) => word.startsWith(x)).sort((a, b) => b.length - a.length)[0];
		if (!token) continue;
		if (match.index > last) out.push({ t: text.slice(last, match.index), m: false });
		out.push({ t: match[0].slice(0, token.length), m: true });
		last = match.index + token.length;
	}
	if (last < text.length) out.push({ t: text.slice(last), m: false });
	return out;
}

const sections = computed(() => {
	const r = result.value;
	if (!r || failed.value) return [];
	const heads = { near: labels.value?.near || t("Your department"), recent: t("Recent"), rest: labels.value?.rest || t("Everyone else") };
	const out = [];
	if (!r.typed && props.allLabel) out.push({ key: "all", title: "", rows: [{ id: "", label: props.allLabel, detail: "", disabled_reason: null, all: true }] });
	for (const key of ["near", "recent", "rest", "match"]) {
		const rows = r.rows.filter((row) => row.section === key).map((row) => (props.staged.includes(row.id) && !row.disabled_reason ? { ...row, disabled_reason: props.stagedReason } : row));
		if (rows.length) out.push({ key, title: key === "match" ? "" : heads[key], rows });
	}
	// a list that is only "everyone else" needs no heading over it: the heading is for telling parts apart
	const parts = out.filter((s) => s.key !== "all");
	if (parts.length === 1 && parts[0].key === "rest") parts[0].title = "";
	return out;
});
const flat = computed(() => sections.value.flatMap((s) => s.rows));
const firstChoosable = () => (flat.value.find((r) => !r.disabled_reason) || {}).id ?? null;

const groups = computed(() => {
	const tokens = busy.value ? [] : words(q.value);
	let i = -1;
	return sections.value.map((s) => ({
		key: s.key,
		title: s.title,
		headId: `${uid}-g-${s.key}`,
		rows: s.rows.map((row) => {
			i += 1;
			return {
				i,
				row,
				domId: `${uid}-o-${i}`,
				reasonId: `${uid}-r-${i}`,
				active: !busy.value && active.value !== null && row.id === active.value,
				name: segments(row.label, tokens),
				detail: segments(row.detail, tokens),
			};
		}),
	}));
});
const activeDescendant = computed(() => {
	if (!listOpen.value || busy.value || active.value === null) return null;
	const i = flat.value.findIndex((r) => r.id === active.value);
	return i < 0 ? null : `${uid}-o-${i}`;
});

const shownCount = computed(() => (result.value ? result.value.rows.length : 0));
const footText = computed(() => {
	const r = result.value;
	if (!r || busy.value || failed.value || shownCount.value >= r.total) return "";
	return `${t("Showing")} ${shownCount.value} ${t("of")} ${r.total}. ${r.typed ? t("Keep typing to narrow.") : t("Type to search.")}`;
});
const busyText = computed(() => (status.value === "loading" || !q.value.trim() ? `${t("Loading")} ${props.plural || labels.value?.plural || ""}`.trim() + "…" : `${t("Updating results for")} “${q.value.trim()}”…`));
const liveText = computed(() => {
	if (!listOpen.value) return "";
	if (lastAdded.value) return `${t("Added")} ${lastAdded.value}. ${props.staged.length} ${props.stagedNoun}.`;
	if (failed.value) return `${t("Could not load")} ${pluralText.value}.`;
	if (isEmpty.value) return `${t("No")} ${nounText.value} ${t("matches")} ${q.value.trim()}`;
	const r = result.value;
	if (!r || busy.value) return "";
	return shownCount.value < r.total ? `${shownCount.value} ${t("of")} ${r.total} ${t("results")}` : `${r.total} ${t("results")}`;
});

// -- the chosen record ----------------------------------------------------------------------------
const hasChoice = computed(() => !!selected.value && (selected.value.id !== "" || !!selected.value.all));
const inputValue = computed(() => (selected.value ? selected.value.label + q.value : q.value));
const clearLabel = computed(() => `${t("Clear")} ${selected.value ? selected.value.label : ""}`.trim());
const choiceReason = computed(() => (props.errorText ? "" : selected.value?.reason || ""));
const isInvalid = computed(() => props.invalid || !!choiceReason.value);
const noteId = computed(() => (props.errorText ? `${uid}-error` : choiceReason.value ? `${uid}-note` : null));

function choose(row) {
	if (!row || row.disabled_reason || busy.value) return;
	if (row.id) pushRecent(row.id);
	if (props.multiple) return add(row);
	close();
	selected.value = { id: row.id, label: row.label, reason: null, all: !!row.all };
	q.value = "";
	result.value = null;
	props.onChange(row.all ? { id: "", label: row.label, all: true } : row);
}

// Adding several: the person goes to the caller's list and the reader stays where they were: the same list, the same search,
// the next choosable row active, the search text selected so typing begins a new search.
function add(row) {
	const choosable = flat.value.filter((r) => !r.disabled_reason);
	const at = choosable.findIndex((r) => r.id === row.id);
	const next = (choosable[at + 1] || choosable[at - 1] || {}).id ?? null;
	props.onAdd(row);
	lastAdded.value = row.label;
	setTimeout(() => {
		const still = flat.value.some((r) => r.id === next && !r.disabled_reason);
		active.value = still ? next : firstChoosable();
		const el = inputEl.value;
		if (el) {
			el.focus();
			el.select();
		}
	}, 0);
}

function onClear() {
	selected.value = null;
	q.value = "";
	result.value = null;
	props.onChange(null);
	nextTick(() => inputEl.value && inputEl.value.focus());
}

function hover(item) {
	if (!item.row.disabled_reason && !busy.value && active.value !== item.row.id) active.value = item.row.id;
}

function retry() {
	search(q.value);
}

function onFocus() {
	if (!props.inline && !selected.value && !open.value && !props.disabled) openList();
}

function onBlur() {
	if (!props.inline) close();
}

function onInput(event) {
	let text = event.target.value;
	if (selected.value) {
		const label = selected.value.label;
		text = text.startsWith(label) ? text.slice(label.length) : text;
		selected.value = null;
		props.onChange(null);
	}
	q.value = text;
	lastAdded.value = "";
	search(text, { debounce: true });
}

function move(direction) {
	const rows = flat.value.filter((r) => !r.disabled_reason);
	if (!rows.length) return;
	let index = rows.findIndex((r) => r.id === active.value);
	if (direction === "home") index = 0;
	else if (direction === "end") index = rows.length - 1;
	else index = index < 0 ? (direction > 0 ? 0 : rows.length - 1) : Math.min(rows.length - 1, Math.max(0, index + direction));
	active.value = rows[index].id;
	nextTick(() => {
		const el = listEl.value && listEl.value.querySelector(".kt-picker-option.is-active");
		const list = listEl.value;
		if (!el || !list) return;
		if (el.offsetTop < list.scrollTop) list.scrollTop = el.offsetTop - 30;
		else if (el.offsetTop + el.offsetHeight > list.scrollTop + list.clientHeight) list.scrollTop = el.offsetTop + el.offsetHeight - list.clientHeight + 4;
	});
}

function onKeyDown(event) {
	const key = event.key;
	if (key === "ArrowDown" || key === "ArrowUp") {
		event.preventDefault();
		if (selected.value) return;
		if (!open.value) openList();
		else move(key === "ArrowDown" ? 1 : -1);
	} else if ((key === "Home" || key === "End") && listOpen.value && result.value) {
		event.preventDefault();
		move(key === "Home" ? "home" : "end");
	} else if (key === "Enter") {
		if (listOpen.value) {
			event.preventDefault();
			choose(flat.value.find((r) => r.id === active.value));
		}
	} else if (key === "Escape") {
		if (props.inline) {
			// the search first; with nothing to clear, Esc is left for the dialog around it
			if (q.value) {
				event.preventDefault();
				event.stopPropagation();
				q.value = "";
				lastAdded.value = "";
				search("");
			}
		} else if (listOpen.value) {
			// the list first; a second Esc is left for the dialog around it
			event.preventDefault();
			event.stopPropagation();
			close();
		}
	} else if (key === "Tab") {
		if (!props.inline) close();
	}
}

// -- keeping the saved choice in step with the screen --------------------------------------------
async function resolveSelected({ announce = false } = {}) {
	const current = selected.value;
	if (!current || !current.id) return;
	try {
		const answer = await call("resolve", { source: props.source, ids: JSON.stringify([current.id]), context: contextText() });
		const found = (answer.rows || []).find((r) => r.id === current.id);
		if (!found || !selected.value || selected.value.id !== current.id) return;
		const reason = found.disabled_reason || null;
		const changed = reason !== (selected.value.reason || null);
		selected.value = { ...selected.value, label: selected.value.label || found.label, reason };
		if (announce && changed) props.onChange({ ...found, label: selected.value.label });
	} catch (error) {
		// the name stays as it was; the command still checks the choice when it is saved
	}
}

watch(
	() => [props.value, props.valueLabel],
	([value, label]) => {
		if (value === null || value === undefined) {
			selected.value = null;
		} else if (!selected.value || selected.value.id !== value) {
			selected.value = { id: value, label: label || (value === "" ? props.allLabel : ""), reason: null, all: value === "" };
			if (!label && value) resolveSelected();
		} else if (label && label !== selected.value.label) {
			selected.value = { ...selected.value, label };
		}
	}
);

// What a provider decides can depend on the context (the committee role, who is already taken),
// so a change re-checks the saved choice and refreshes an open list. An equal object does neither.
watch(
	() => JSON.stringify(props.context || {}),
	() => {
		if (selected.value && selected.value.id) resolveSelected({ announce: true });
		if (listOpen.value) search(q.value);
	}
);

onMounted(() => {
	if (selected.value && selected.value.id && !selected.value.label) resolveSelected();
	if (props.inline) search("");
});

onBeforeUnmount(() => {
	clearTimeout(timer);
	guard.next();
	watchPlacement(false);
});

defineExpose({ focus: () => inputEl.value && inputEl.value.focus() });
</script>
