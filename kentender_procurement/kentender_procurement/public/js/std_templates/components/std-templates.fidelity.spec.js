// Structural fidelity for STD Templates against
// `docs/mvp-1-r1/07_std_configuration/design/STD Templates Artboards.dc.html`
// (STD-TPL-001 v0.10 §11). Each statically addressable board is mounted with a
// projection-shaped fixture and compared container for container; registered
// departures are the only allowed differences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import { boardSkeleton, planningScope } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { COVERED, DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/std-templates.js";

import ReleaseList from "./ReleaseList.vue";
import ReleaseDetail from "./ReleaseDetail.vue";
import ReportConcernDialog from "./ReportConcernDialog.vue";
import { detailPayload, listPayload } from "./fixtures.js";

const BOARD = "docs/mvp-1-r1/07_std_configuration/design/STD Templates Artboards.dc.html";

// STD-DES-02C draws the dialog over a dimmed copy of the detail page: the
// dialog itself is the artboard.
function stdScope(doc, id) {
	if (id === "std-des-02c") {
		const dialog = doc.querySelector("section#std-des-02c .dialog");
		if (!dialog) throw new Error("artboard std-des-02c draws no dialog");
		return { children: [dialog.cloneNode(true)] };
	}
	return planningScope(doc, id);
}

const SCREENS = [
	{ name: "ReleaseList", variant: "std-des-01", component: ReleaseList, props: { data: listPayload() } },
	{ name: "ReleaseDetail", variant: "std-des-02", component: ReleaseDetail, props: { data: detailPayload(), hashState: { tech: "1" } } },
	{ name: "ReportConcernDialog", variant: "std-des-02c", component: ReportConcernDialog, props: { release: detailPayload().release, categories: detailPayload().concerns.categories }, dialog: true },
	{ name: "ReleaseDetail", variant: "std-des-02r", component: ReleaseDetail, props: { data: {}, failed: true } },
];

function built(wrapper, dialog) {
	if (dialog) return { children: [wrapper.element.querySelector(".kt-dialog")] };
	return wrapper.element;
}

describe.each(SCREENS)("$name — the structure $variant carries", ({ name, variant, component, props, dialog }) => {
	it("is built out of the board's own elements", () => {
		const wrapper = mount(component, { props, global: { mocks: { __: (s) => s } } });
		const result = compareSkeletons(boardSkeleton(BOARD, variant, stdScope), skeletonOf(built(wrapper, dialog)), {
			departures: DEPARTURES[`${name}#${variant}`] || [],
		});
		const message = formatMismatch(`${name} / ${variant}`, result);
		expect(message, message).toBe("");
	}, 30_000);
});

describe("the COVERED claim", () => {
	it("lists exactly the variants this spec compares", () => {
		expect([...COVERED].sort()).toEqual([...new Set(SCREENS.map((s) => `${s.name}#${s.variant}`))].sort());
	});
});
