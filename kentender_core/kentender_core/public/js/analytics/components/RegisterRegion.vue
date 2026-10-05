<script setup>
// ANL §10A.4 to §10A.8, §11 — the record register of an area tab: a heading with the list icon, the search
// input (Enter submits the server search; the text never enters the URL), the state select (applies at once and
// is the route's `state`, bound to the caller's own selection), the table or compact rows, the footer the
// server worded, Previous / Next on a cursor read, and the clear control the server names. "View record" goes
// to the owner's own route, the route array the server sent; a row with no permitted route has no action.
import { computed } from "vue";
import AnalyticsIcon from "./AnalyticsIcon.vue";
import RegionHeading from "./RegionHeading.vue";
import { isPlainClick } from "./presentation.js";
import { recordHref } from "../composables/useRouteState.js";

const props = defineProps({
	area: { type: Object, required: true },
	selectedState: { type: String, default: "" }, // the route's own state, never the server's echo
	searchText: { type: String, default: "" }, // the input's own text
	hasPrevious: { type: Boolean, default: false },
});
const emit = defineEmits(["update:searchText", "submit-search", "select-state", "clear", "next", "previous", "open-record"]);

const register = computed(() => props.area.register);
// The select shows the route's own state and a change asks the page to apply it at once (v-model re-applies the
// selection whenever the options change).
const stateModel = computed({ get: () => props.selectedState, set: (value) => emit("select-state", value) });
const heading = computed(() => register.value.title);
const COLGROUP = {
	annual_planning: [20, 32, 18, 20, 10],
	requisitions: [28, 22, 20, 20, 10],
	tender_proceedings: [24, 30, 16, 20, 10],
};
const widths = computed(() => COLGROUP[props.area.key] || []);
const NUMERIC = ["authorised_requisition_value", "requisition_value", "planned_value", "covered_by_authorised_requisitions"];
const isNum = (column) => NUMERIC.includes(column.key);
const dataColumns = computed(() => register.value.columns.filter((column) => column.key !== "action"));
const actionLabel = computed(() => (register.value.columns.find((column) => column.key === "action") || {}).label || "");
const placeholder = computed(() => register.value.search_label);
const noRows = computed(() => register.value.rows.length === 0);
// The server's clear control sits beside the select for a stage/state filter, and in the empty block for a search.
const clearBeside = computed(() => register.value.clear && (register.value.clear.kind === "state" || (register.value.clear.kind === "search" && !noRows.value)));
const clearInEmpty = computed(() => register.value.clear && register.value.clear.kind === "search" && noRows.value);
const pagingShown = computed(() => !!register.value.next_cursor || props.hasPrevious);

function openRecord(event, route) {
	if (!isPlainClick(event)) return;
	event.preventDefault();
	emit("open-record", route);
}
function clear(event) {
	event.preventDefault();
	emit("clear", register.value.clear.kind);
}
</script>

<template>
	<section class="kt-ap-section is-ruled" data-testid="kt-anl-register">
		<RegionHeading icon="list" :title="heading" :chip="false" />
		<div class="kt-ap-controls">
			<div class="field kt-ap-field-search">
				<label for="kt-anl-search">{{ __("Search") }}</label>
				<div class="kt-ap-search-wrap">
					<AnalyticsIcon name="search" size="sm" />
					<input
						id="kt-anl-search"
						class="input"
						type="search"
						autocomplete="off"
						:placeholder="placeholder"
						:aria-label="placeholder"
						:value="searchText"
						data-testid="kt-anl-search"
						@input="emit('update:searchText', $event.target.value)"
						@keydown.enter.prevent="emit('submit-search')"
					/>
				</div>
			</div>
			<div v-if="register.state_options.length" class="field kt-ap-field-state">
				<label for="kt-anl-state">{{ __("State") }}</label>
				<select id="kt-anl-state" class="input" data-testid="kt-anl-state" v-model="stateModel">
					<option value="">{{ register.state_all }}</option>
					<option v-for="option in register.state_options" :key="option.key" :value="option.key">{{ option.label }}</option>
				</select>
			</div>
			<a v-if="clearBeside" href="#" class="kt-ap-clear-inline" data-testid="kt-anl-clear-register" @click="clear">
				<AnalyticsIcon name="x" size="sm" />{{ register.clear.label }}
			</a>
		</div>

		<div v-if="noRows" class="kt-ap-nomatch" data-testid="kt-anl-nomatch">
			<AnalyticsIcon name="search" size="lg" />
			<p v-if="register.empty_text">{{ register.empty_text }}</p>
			<a v-if="clearInEmpty" href="#" class="kt-ap-link is-md" data-testid="kt-anl-clear-register" @click="clear">{{ register.clear.label }}</a>
		</div>

		<!-- table layout: Plan items, Requisitions, Tenders -->
		<div v-else-if="register.layout === 'table'" class="kt-ap-table-scroll">
			<table class="table kt-ap-table" data-testid="kt-anl-table">
				<colgroup>
					<col v-for="(width, i) in widths" :key="i" :style="{ width: width + '%' }" />
				</colgroup>
				<thead>
					<tr>
						<th v-for="column in dataColumns" :key="column.key" :class="{ 'is-num': isNum(column) }">{{ column.label }}</th>
						<th>{{ actionLabel }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="(row, rowIndex) in register.rows" :key="row.key" data-testid="kt-anl-row">
						<td v-for="(column, index) in dataColumns" :key="column.key" :class="{ 'is-num': isNum(column) }">
							<div v-if="index === 0" class="kt-ap-cell-title">
								<span>{{ row.cells[column.key].text }}</span>
								<span v-if="row.cells[column.key].secondary" class="kt-ap-cell-secondary">{{ row.cells[column.key].secondary }}</span>
							</div>
							<template v-else>
								<span :class="{ 'kt-ap-cell-muted': row.cells[column.key].quiet }">{{ row.cells[column.key].text }}</span>
								<span v-if="row.cells[column.key].secondary" class="kt-ap-cell-secondary">{{ row.cells[column.key].secondary }}</span>
							</template>
						</td>
						<td>
							<a
								v-if="row.action && row.action.route"
								class="kt-ap-link"
								:href="recordHref(row.action.route)"
								:data-row-index="rowIndex"
								@click="openRecord($event, row.action.route)"
							>{{ row.action.label }}</a>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- compact layout: Needs and departmental plans, no table -->
		<div v-else class="kt-ap-compact" data-testid="kt-anl-compact">
			<div v-for="row in register.rows" :key="row.key" class="kt-ap-compact-row" data-testid="kt-anl-row">
				<span class="kt-ap-compact-title">{{ row.title }}</span>
				<span class="kt-ap-compact-pos">{{ row.position }}</span>
				<span class="kt-ap-compact-act">
					<a v-if="row.action && row.action.route" class="kt-ap-link" :href="recordHref(row.action.route)" @click="openRecord($event, row.action.route)">{{ row.action.label }}</a>
				</span>
			</div>
		</div>

		<div class="kt-ap-footer">
			<p class="kt-ap-note" data-testid="kt-anl-footer">{{ register.footer }}</p>
			<span v-if="register.partial" class="kt-ap-partial" data-testid="kt-anl-partial">{{ __("Partial list") }}</span>
			<template v-if="pagingShown">
				<button type="button" class="btn btn-secondary" :disabled="!hasPrevious" data-testid="kt-anl-previous" @click="emit('previous')">{{ __("Previous") }}</button>
				<button type="button" class="btn btn-secondary" :disabled="!register.next_cursor" data-testid="kt-anl-next" @click="emit('next')">{{ __("Next") }}</button>
			</template>
		</div>
	</section>
</template>
