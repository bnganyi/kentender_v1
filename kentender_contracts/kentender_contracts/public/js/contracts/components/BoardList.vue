<!-- BoardList — the contracts list (boards D01 and D01-S), drawn from the server's board (CM-CHG-001 v0.8 section 10). Ported from the design template's list markup class for class: the page
     head, the My work / All contracts switch, the filter bar with every filter in one row, the table or the empty state. The register is paged on the server and drawn with the
     one shared pager (AGENTS.md section 6.11); the root screen owns the page and the filters so a visit to a contract and back keeps them. -->
<template>
	<div class="kt-page" :data-testid="`cm-board-${board.id}`" :data-board="board.id">
		<div class="kt-page-head">
			<div><h1 class="kt-page-title">{{ board.title }}</h1></div>
			<div v-if="board.headP" class="kt-page-actions"><button type="button" class="btn btn-primary" @click="$emit('head')">{{ board.headP }}</button></div>
		</div>
		<div v-if="board.views.length" class="seg" role="radiogroup" style="width: fit-content">
			<label v-for="(v, i) in board.views" :key="v" class="seg-opt" :data-testid="`cm-view-${i}`"><input type="radio" name="cm-view" :checked="i === board.view" @change="$emit('view', v)" />{{ v }}</label>
		</div>
		<div>
			<div class="kt-filter-bar">
				<div v-for="(f, i) in fields" :key="f.name" class="field" :class="{ 'is-wide': i === 0 }">
					<label :for="`cm-filter-${f.name}`">{{ f.l }}</label>
					<input v-if="f.t === 'tx'" :id="`cm-filter-${f.name}`" v-model="local[f.name]" class="input" :data-testid="`cm-filter-${f.name}`" @change="apply" @keydown.enter="apply" />
					<RecordPickerHost
						v-else-if="f.t === 'pick'"
						:model-value="local[f.name] ?? ''"
						:source="f.source"
						:context="f.context"
						:value-label="labelOf(f)"
						:input-id="`cm-filter-${f.name}`"
						:noun="f.noun"
						:all-label="(f.o && f.o.allLabel) || ''"
						:data-testid="`cm-pick-${f.name}`"
						@update:model-value="(v) => pickFilter(f.name, v)"
						@change="(row) => (chosen[f.name] = row ? row.label : '')"
					/>
					<select v-else :id="`cm-filter-${f.name}`" v-model="local[f.name]" class="input" :data-testid="`cm-filter-${f.name}`" @change="apply"><option v-for="o in f.options" :key="o.value" :value="o.value">{{ o.label }}</option></select>
				</div>
			</div>
			<table v-if="board.rows.length" class="table" data-testid="cm-list">
				<thead><tr><th v-for="h in table.head" :key="h.v" :class="h.cls">{{ h.v }}</th></tr></thead>
				<tbody>
					<tr v-for="(r, ri) in table.body" :key="ri" :data-testid="`cm-row-${board.rowRoutes[ri][0]}`">
						<td v-for="(c, ci) in r.cells" :key="ci" :class="c.cls">
							<template v-if="c.isT">{{ c.v }}</template>
							<a v-else-if="c.isL" href="#" @click.prevent="$emit('open', board.rowRoutes[ri])">{{ c.v }}</a>
							<span v-else-if="c.isS" class="kt-status" :class="c.sc">{{ c.v }}</span>
						</td>
					</tr>
				</tbody>
			</table>
			<div v-else class="kt-empty" data-testid="cm-empty">
				<div class="kt-spot is-neutral"><svg class="kt-icon" viewBox="0 0 24 24"><path d="M22 12h-6l-2 3h-4l-2-3H2"></path><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg></div>
				<p>{{ board.empty }}</p>
				<button v-if="board.emptyAct" type="button" class="btn btn-secondary" @click="clear">{{ board.emptyAct }}</button>
			</div>
			<TablePagerHost v-if="board.rows.length" :total="board.paging.total" :page="board.paging.page" :page-size="board.paging.page_size" noun="contract" @update:page="(n) => $emit('page', n)" @update:page-size="(n) => $emit('size', n)" />
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import RecordPickerHost from "../../record_picker_shared/RecordPickerHost.vue";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { fieldView, tableView } from "../board_view.js";

const props = defineProps({ board: { type: Object, required: true } });
const emit = defineEmits(["filter", "view", "open", "page", "size", "head"]);

const local = reactive({});
const fields = computed(() => props.board.filters.map((f, i) => fieldView(f, `list-${i}`, i)));
// The design draws all five filters in the one bar, the first (Search) wide.
const table = computed(() => tableView({ cols: props.board.cols, rows: props.board.rows, num: [] }));

// The filters the server applied are what the screen shows; a typed value waits for the reader to apply it.
watch(() => props.board.filters, (filters) => { for (const f of filters) local[f.name] = f.v ?? ""; }, { immediate: true });

function apply() {
	emit("filter", { search: local.search ?? "", status: local.status ?? "", source: local.source ?? "", responsible: local.responsible ?? "", unit: local.unit ?? "" });
}

// A person or a unit is chosen with the shared picker, which hands back the chosen id, or nothing for "All". The picker is given the reader's own choice and its name, never the server's echo of the
// last answer (which still names the old choice for a moment after a Clear).
const chosen = reactive({});
const labelOf = (f) => (local[f.name] ? chosen[f.name] || f.valueLabel || "" : "");
function pickFilter(name, value) {
	local[name] = value || "";
	apply();
}

function clear() {
	Object.assign(local, { search: "", status: props.board.filters.find((f) => f.name === "status")?.opts?.[0] ?? "", source: props.board.filters.find((f) => f.name === "source")?.opts?.[0] ?? "", responsible: "", unit: "" });
	apply();
}
</script>
