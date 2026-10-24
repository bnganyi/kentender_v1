// The shared record picker (approved plan, §3): a combobox that searches a source as the reader types,
// shows who is near and recent before typing, lists but greys what cannot be chosen, and never
// lets an old answer stand in for a newer one. The server is stubbed through `fetch`.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import RecordPicker from "./RecordPicker.vue";

const LABELS = { noun: "person", plural: "people", near: "Your department", rest: "Everyone else", hint: "Only people holding an active responsibility can be named here." };
const row = (id, label, detail = "", section = "rest", disabled_reason = null) => ({ id, label, detail, section, disabled_reason });
const BEFORE = {
	rows: [
		row("brian", "Brian Achieng", "Procurement Officer · Supply Chain", "near"),
		row("rose", "Rose Odhiambo", "Human Resource Officer · HR", "recent"),
		row("amina", "Amina Hassan", "Accountant · Finance", "rest"),
		row("esther", "Esther Chebet", "ICT Officer · ICT", "rest", "Was involved in processing this Tender"),
		row("zoe", "Zoë Mwangi", "Auditor · Internal Audit", "rest"),
	],
	total: 5, limit: 20, typed: false, labels: LABELS,
};
const typed = (rows, total = rows.length) => ({ rows: rows.map((r) => ({ ...r, section: "match" })), total, limit: 20, typed: true, labels: LABELS });

let calls;
let answers;
const fetchStub = vi.fn((endpoint, args) => {
	calls.push({ endpoint, args });
	const answer = answers(endpoint, args);
	return answer instanceof Promise ? answer : Promise.resolve(answer);
});

const make = (props = {}) => {
	const changes = [];
	const w = mount(RecordPicker, {
		attachTo: document.body,
		props: { source: "bid_opening.committee_member", context: { tender: "T1" }, inputId: "p", user: "grace@example.test", fetch: fetchStub, onChange: (r) => changes.push(r), ...props },
	});
	return { w, changes };
};
const input = (w) => w.get('[data-testid="kt-picker-input"]');
const list = (w) => w.find('[data-testid="kt-picker-list"]');
const names = (w) => w.findAll(".kt-picker-name").map((n) => n.text());
const heads = (w) => w.findAll(".kt-picker-group").map((n) => n.text());
const flush = async (ms = 0) => {
	await vi.advanceTimersByTimeAsync(ms);
	await nextTick();
};
const focus = async (w) => {
	await input(w).trigger("focus");
	await flush(0);
};
const type = async (w, text) => {
	input(w).element.value = text;
	await input(w).trigger("input");
};
const key = (w, k) => input(w).trigger("keydown", { key: k });

beforeEach(() => {
	vi.useFakeTimers();
	calls = [];
	answers = (endpoint, args) => (endpoint === "resolve" ? { rows: [] } : args.query ? typed([row("amina", "Amina Hassan", "Accountant · Finance")]) : BEFORE);
	fetchStub.mockClear();
	localStorage.clear();
});
afterEach(() => {
	vi.useRealTimers();
	document.body.innerHTML = "";
});

describe("the field", () => {
	it("is a combobox in the ARIA pattern, closed until it is used", () => {
		const { w } = make();
		const el = input(w).element;
		expect(el.getAttribute("role")).toBe("combobox");
		expect(el.getAttribute("aria-autocomplete")).toBe("list");
		expect(el.getAttribute("aria-expanded")).toBe("false");
		expect(el.id).toBe("p");
		expect(list(w).exists()).toBe(false);
		expect(fetchStub).not.toHaveBeenCalled();
	});

	it("carries the invalid and required marks and speaks the error text beneath it", () => {
		const { w } = make({ invalid: true, required: true, errorText: "Choose a member." });
		expect(input(w).attributes("aria-invalid")).toBe("true");
		expect(input(w).attributes("aria-required")).toBe("true");
		const error = w.get('[data-testid="kt-picker-error"]');
		expect(error.text()).toBe("Choose a member.");
		expect(input(w).attributes("aria-describedby")).toBe(error.attributes("id"));
	});
});

describe("before typing", () => {
	it("opens on focus and shows near, recent, then everyone else, under their own headings", async () => {
		const { w } = make();
		await focus(w);
		expect(input(w).attributes("aria-expanded")).toBe("true");
		expect(heads(w)).toEqual(["Your department", "Recent", "Everyone else"]);
		expect(names(w)).toEqual(["Brian Achieng", "Rose Odhiambo", "Amina Hassan", "Esther Chebet", "Zoë Mwangi"]);
		expect(calls[0]).toMatchObject({ endpoint: "search", args: { source: "bid_opening.committee_member", query: "", limit: 20 } });
		expect(JSON.parse(calls[0].args.context)).toEqual({ tender: "T1" });
	});

	it("says it is loading until the first answer, and then the first choosable row is active", async () => {
		let release;
		answers = () => new Promise((resolve) => (release = resolve));
		const { w } = make({ noun: "person", plural: "people" }); // the screen's wording, until the source's own arrives
		await focus(w);
		expect(w.get(".kt-picker-status").text()).toBe("Loading people…");
		expect(list(w).attributes("aria-busy")).toBe("true");
		release(BEFORE);
		await flush();
		expect(w.find(".kt-picker-status").exists()).toBe(false);
		expect(input(w).attributes("aria-activedescendant")).toBe(w.findAll('[role="option"]')[0].attributes("id"));
	});

	it("puts no heading over a list that is only everyone else, and keeps the headings when there are parts to tell apart", async () => {
		answers = () => ({ ...BEFORE, rows: BEFORE.rows.filter((r) => r.section === "rest") });
		const { w } = make();
		await focus(w);
		expect(heads(w)).toEqual([]);
		expect(names(w).length).toBe(3);
		w.unmount();
		answers = () => BEFORE;
		const again = make({ inputId: "q" });
		await focus(again.w);
		expect(heads(again.w)).toEqual(["Your department", "Recent", "Everyone else"]);
	});

	it("says how many more there are and how to find them", async () => {
		answers = () => ({ ...BEFORE, total: 216 });
		const { w } = make();
		await focus(w);
		expect(w.get('[data-testid="kt-picker-foot"]').text()).toBe("Showing 5 of 216. Type to search.");
	});

	it("sends the reader's recent picks for this source, and only theirs", async () => {
		localStorage.setItem("kt.picker.recent.grace@example.test.bid_opening.committee_member", JSON.stringify(["rose", "zoe"]));
		localStorage.setItem("kt.picker.recent.other@example.test.bid_opening.committee_member", JSON.stringify(["amina"]));
		const { w } = make();
		await focus(w);
		expect(JSON.parse(calls[0].args.recent)).toEqual(["rose", "zoe"]);
	});

	it("starts with no recent picks and a blocked store changes nothing", async () => {
		const original = Object.getOwnPropertyDescriptor(window, "localStorage");
		Object.defineProperty(window, "localStorage", { configurable: true, get() { throw new Error("blocked"); } });
		try {
			const { w, changes } = make();
			await focus(w);
			expect(JSON.parse(calls[0].args.recent)).toEqual([]);
			await key(w, "Enter");
			await flush();
			expect(changes.length).toBe(1);
		} finally {
			Object.defineProperty(window, "localStorage", original);
		}
	});
});

describe("typing", () => {
	it("waits a quarter of a second after the last keystroke and asks once", async () => {
		const { w } = make();
		await focus(w);
		calls.length = 0;
		await type(w, "a");
		await flush(100);
		await type(w, "am");
		await flush(100);
		await type(w, "ami");
		expect(calls.length).toBe(0);
		await flush(249);
		expect(calls.length).toBe(0);
		await flush(1);
		expect(calls.map((c) => c.args.query)).toEqual(["ami"]);
	});

	it("never lets a slow answer for an earlier text replace the answer for the later one", async () => {
		const pending = {};
		answers = (endpoint, args) => (args.query === "" ? BEFORE : new Promise((resolve) => (pending[args.query] = resolve)));
		const { w } = make();
		await focus(w);
		await type(w, "ami");
		await flush(250);
		await type(w, "amina");
		await flush(250);
		pending.amina(typed([row("amina", "Amina Hassan", "Accountant · Finance")]));
		await flush();
		pending.ami(typed([row("wrong", "Amir Wrong"), row("wrong2", "Amit Wrong")]));
		await flush();
		expect(names(w)).toEqual(["Amina Hassan"]);
	});

	it("keeps the old rows on screen but greyed and unchoosable until the new answer arrives", async () => {
		let release;
		answers = (endpoint, args) => (args.query === "" ? BEFORE : new Promise((resolve) => (release = resolve)));
		const { w, changes } = make();
		await focus(w);
		await type(w, "amina");
		await flush(250);
		expect(list(w).classes()).toContain("is-updating");
		expect(w.get(".kt-picker-status").text()).toBe("Updating results for “amina”…");
		expect(w.findAll('[role="option"]').length).toBe(5);
		await w.findAll('[role="option"]')[2].trigger("click");
		await key(w, "Enter");
		expect(changes).toEqual([]);
		release(typed([row("amina", "Amina Hassan", "Accountant · Finance")]));
		await flush();
		expect(list(w).classes()).not.toContain("is-updating");
	});

	it("emphasises the text that matched, ignoring case and accents", async () => {
		answers = () => typed([row("zoe", "Zoë Mwangi", "Auditor · Internal Audit")]);
		const { w } = make();
		await focus(w);
		await type(w, "ZOE");
		await flush(250);
		expect(w.findAll(".kt-picker-name mark").map((m) => m.text())).toEqual(["Zoë"]);
		await type(w, "aud");
		await flush(250);
		expect(w.findAll(".kt-picker-detail mark").map((m) => m.text())).toEqual(["Aud", "Aud"]);
	});

	it("says how many matched when there are more than are shown", async () => {
		answers = (endpoint, args) => (args.query ? typed([row("a", "Amina A"), row("b", "Amina B")], 143) : BEFORE);
		const { w } = make();
		await focus(w);
		await type(w, "amina");
		await flush(250);
		expect(w.get('[data-testid="kt-picker-foot"]').text()).toBe("Showing 2 of 143. Keep typing to narrow.");
	});

	it("says nothing matched, with the source's hint", async () => {
		answers = (endpoint, args) => (args.query ? typed([]) : BEFORE);
		const { w } = make();
		await focus(w);
		await type(w, "xyz");
		await flush(250);
		const status = w.get(".kt-picker-status");
		expect(status.text()).toContain("No person matches “xyz”.");
		expect(status.text()).toContain("Only people holding an active responsibility can be named here.");
	});

	it("says it could not load, and Try again asks again without losing the field", async () => {
		let fail = true;
		answers = (endpoint, args) => (args.query && fail ? Promise.reject(new Error("boom")) : args.query ? typed([row("amina", "Amina Hassan")]) : BEFORE);
		const { w } = make();
		await focus(w);
		await type(w, "ami");
		await flush(250);
		expect(w.get(".kt-picker-status").text()).toContain("Could not load people. Try again.");
		expect(w.findAll('[role="option"]').length).toBe(0);
		fail = false;
		const retry = w.get('[data-testid="kt-picker-retry"]');
		const down = new MouseEvent("mousedown", { bubbles: true, cancelable: true });
		retry.element.dispatchEvent(down);
		expect(down.defaultPrevented).toBe(true); // the list does not close under the click
		await retry.trigger("click");
		await flush();
		expect(names(w)).toEqual(["Amina Hassan"]);
		expect(input(w).element.value).toBe("ami");
	});
});

describe("choosing", () => {
	it("chooses with Enter, reports the row, shows the name with a Clear, and remembers the pick", async () => {
		const { w, changes } = make();
		await focus(w);
		await key(w, "Enter");
		await flush();
		expect(changes[0]).toMatchObject({ id: "brian", label: "Brian Achieng" });
		expect(input(w).element.value).toBe("Brian Achieng");
		expect(input(w).attributes("aria-expanded")).toBe("false");
		expect(list(w).exists()).toBe(false);
		expect(w.get('[data-testid="kt-picker-clear"]').attributes("aria-label")).toBe("Clear Brian Achieng");
		expect(JSON.parse(localStorage.getItem("kt.picker.recent.grace@example.test.bid_opening.committee_member"))).toEqual(["brian"]);
	});

	it("keeps five recent picks, newest first, each once", async () => {
		const key5 = "kt.picker.recent.grace@example.test.bid_opening.committee_member";
		localStorage.setItem(key5, JSON.stringify(["a", "b", "c", "d", "e"]));
		const { w } = make();
		await focus(w);
		await key(w, "Enter"); // brian
		expect(JSON.parse(localStorage.getItem(key5))).toEqual(["brian", "a", "b", "c", "d"]);
	});

	it("chooses with a click", async () => {
		const { w, changes } = make();
		await focus(w);
		await w.findAll('[role="option"]')[4].trigger("click");
		expect(changes[0].id).toBe("zoe");
	});

	it("Clear forgets the choice, tells the screen, and opens the list again", async () => {
		const { w, changes } = make({ value: "amina", valueLabel: "Amina Hassan" });
		await w.get('[data-testid="kt-picker-clear"]').trigger("click");
		await flush(10);
		expect(changes).toEqual([null]);
		expect(input(w).element.value).toBe("");
		expect(input(w).attributes("aria-expanded")).toBe("true");
	});

	it("typing over a chosen name clears the choice and searches for what was typed", async () => {
		const { w, changes } = make({ value: "amina", valueLabel: "Amina Hassan" });
		input(w).element.value = "Amina Hassanx";
		await input(w).trigger("input");
		await flush(250);
		expect(changes).toEqual([null]);
		expect(calls.at(-1).args.query).toBe("x");
	});

	it("shows the saved name from the screen's own selection, and asks the server for it when it has no name", async () => {
		const { w } = make({ value: "amina", valueLabel: "Amina Hassan" });
		expect(input(w).element.value).toBe("Amina Hassan");
		expect(calls.length).toBe(0);
		answers = (endpoint) => (endpoint === "resolve" ? { rows: [row("kevin", "Kevin Mwangi", "", "match")] } : BEFORE);
		const bare = make({ value: "kevin" }).w;
		await flush();
		expect(calls.at(-1)).toMatchObject({ endpoint: "resolve" });
		expect(JSON.parse(calls.at(-1).args.ids)).toEqual(["kevin"]);
		expect(input(bare).element.value).toBe("Kevin Mwangi");
	});

	it("follows the screen when it changes the selection, and does not move by itself", async () => {
		const { w } = make({ value: "amina", valueLabel: "Amina Hassan" });
		await w.setProps({ value: "zoe", valueLabel: "Zoë Mwangi" });
		expect(input(w).element.value).toBe("Zoë Mwangi");
		await w.setProps({ value: null, valueLabel: "" });
		expect(input(w).element.value).toBe("");
		expect(w.find('[data-testid="kt-picker-clear"]').exists()).toBe(false);
	});

	it("shows why a saved choice is no longer allowed once the screen's context changes it", async () => {
		const { w, changes } = make({ value: "amina", valueLabel: "Amina Hassan", context: { tender: "T1", role: "Member" } });
		answers = (endpoint) => (endpoint === "resolve" ? { rows: [row("amina", "Amina Hassan", "", "match", "Was involved in processing this Tender")] } : BEFORE);
		await w.setProps({ context: { tender: "T1", role: "Independent member" } });
		await flush();
		expect(changes.at(-1)).toMatchObject({ id: "amina", disabled_reason: "Was involved in processing this Tender" });
		expect(w.get('[data-testid="kt-picker-reason"]').text()).toBe("Was involved in processing this Tender");
		expect(input(w).attributes("aria-invalid")).toBe("true");
		answers = (endpoint) => (endpoint === "resolve" ? { rows: [row("amina", "Amina Hassan", "", "match")] } : BEFORE);
		await w.setProps({ context: { tender: "T1", role: "Member" } });
		await flush();
		expect(w.find('[data-testid="kt-picker-reason"]').exists()).toBe(false);
		expect(changes.at(-1)).toMatchObject({ id: "amina", disabled_reason: null });
	});

	it("an equal context object does not search again", async () => {
		const { w } = make({ context: { tender: "T1" } });
		await focus(w);
		const before = calls.length;
		await w.setProps({ context: { tender: "T1" } });
		await flush(300);
		expect(calls.length).toBe(before);
	});
});

describe("what cannot be chosen", () => {
	it("is listed greyed with its reason, skipped by the arrows, and does nothing when clicked", async () => {
		const { w, changes } = make();
		await focus(w);
		const options = w.findAll('[role="option"]');
		expect(options[3].attributes("aria-disabled")).toBe("true");
		expect(options[3].get(".kt-picker-reason").text()).toBe("Was involved in processing this Tender");
		expect(options[3].attributes("aria-describedby")).toBe(options[3].get(".kt-picker-reason").attributes("id"));
		await key(w, "ArrowDown"); // rose
		await key(w, "ArrowDown"); // amina
		await key(w, "ArrowDown"); // zoe — esther is skipped
		expect(input(w).attributes("aria-activedescendant")).toBe(options[4].attributes("id"));
		await options[3].trigger("click");
		expect(changes).toEqual([]);
	});
});

describe("the keyboard", () => {
	it("Down and Up move through the choosable rows and stop at the ends; Home and End jump", async () => {
		const { w } = make();
		await focus(w);
		const options = w.findAll('[role="option"]');
		const active = () => input(w).attributes("aria-activedescendant");
		await key(w, "ArrowUp");
		expect(active()).toBe(options[0].attributes("id"));
		await key(w, "End");
		expect(active()).toBe(options[4].attributes("id"));
		await key(w, "ArrowDown");
		expect(active()).toBe(options[4].attributes("id"));
		await key(w, "Home");
		expect(active()).toBe(options[0].attributes("id"));
	});

	it("Down opens a closed picker", async () => {
		const { w } = make();
		await key(w, "ArrowDown");
		await flush();
		expect(input(w).attributes("aria-expanded")).toBe("true");
	});

	it("Esc closes the list and only the list; a second Esc is left for the dialog", async () => {
		const outer = vi.fn();
		const host = document.createElement("div");
		host.addEventListener("keydown", (e) => e.key === "Escape" && outer());
		document.body.appendChild(host);
		const w = mount(RecordPicker, { attachTo: host, props: { source: "s.s", fetch: fetchStub } });
		await input(w).trigger("focus");
		await flush();
		const first = new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true });
		input(w).element.dispatchEvent(first);
		await nextTick();
		expect(input(w).attributes("aria-expanded")).toBe("false");
		expect(outer).not.toHaveBeenCalled();
		input(w).element.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
		expect(outer).toHaveBeenCalledTimes(1);
	});

	it("Tab chooses nothing and closes the list", async () => {
		const { w, changes } = make();
		await focus(w);
		await key(w, "Tab");
		expect(changes).toEqual([]);
		expect(input(w).attributes("aria-expanded")).toBe("false");
	});

	it("Enter in an open list does not submit a form around it", async () => {
		const { w } = make();
		await focus(w);
		const event = new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true });
		input(w).element.dispatchEvent(event);
		expect(event.defaultPrevented).toBe(true);
	});
});

describe("an All row for a filter", () => {
	it("is drawn first before typing, and choosing it is a choice, distinct from nothing chosen", async () => {
		const { w, changes } = make({ allLabel: "All units" });
		await focus(w);
		expect(names(w)[0]).toBe("All units");
		await key(w, "Enter");
		await flush();
		expect(changes[0]).toMatchObject({ id: "", label: "All units", all: true });
		expect(input(w).element.value).toBe("All units");
		expect(w.find('[data-testid="kt-picker-clear"]').exists()).toBe(true);
		await w.get('[data-testid="kt-picker-clear"]').trigger("click");
		expect(changes.at(-1)).toBe(null);
	});

	it("is drawn from the screen's own selection too", () => {
		const { w } = make({ allLabel: "All units", value: "" });
		expect(input(w).element.value).toBe("All units");
	});
});

describe("the live region and placement", () => {
	it("announces the count, the empty result and the failure politely", async () => {
		const live = (w) => w.get('[role="status"][aria-live="polite"]').text();
		answers = (endpoint, args) => (args.query === "xyz" ? typed([]) : args.query === "boom" ? Promise.reject(new Error("x")) : args.query ? typed([row("a", "Amina A"), row("b", "Amina B")], 143) : BEFORE);
		const { w } = make();
		await focus(w);
		expect(live(w)).toBe("5 results");
		await type(w, "amina");
		await flush(250);
		expect(live(w)).toBe("2 of 143 results");
		await type(w, "xyz");
		await flush(250);
		expect(live(w)).toBe("No person matches xyz");
		await type(w, "boom");
		await flush(250);
		expect(live(w)).toBe("Could not load people.");
	});

	it("floats over the page, placed from the field, so no dialog or table around it can clip it", async () => {
		const original = window.innerHeight;
		Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
		const { w } = make();
		vi.spyOn(input(w).element, "getBoundingClientRect").mockReturnValue({ top: 100, bottom: 136, left: 40, right: 440, width: 400, height: 36 });
		await focus(w);
		const style = list(w).element.style;
		expect([style.position, style.left, style.width, style.top, style.maxHeight]).toEqual(["fixed", "40px", "400px", "140px", "340px"]);
		expect(style.bottom).toBe("");
		Object.defineProperty(window, "innerHeight", { configurable: true, value: original });
	});

	it("opens upward when there is no room beneath the field, and never taller than the room it has", async () => {
		const original = window.innerHeight;
		Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
		const { w } = make();
		vi.spyOn(input(w).element, "getBoundingClientRect").mockReturnValue({ top: 600, bottom: 636, left: 40, right: 440, width: 400, height: 36 });
		await focus(w);
		expect(list(w).classes()).toContain("is-up");
		const style = list(w).element.style;
		expect([style.position, style.bottom, style.maxHeight]).toEqual(["fixed", "104px", "340px"]);
		expect(style.top).toBe("");
		Object.defineProperty(window, "innerHeight", { configurable: true, value: original });
	});

	it("is never shorter than a few rows, and takes the larger side when neither has room", async () => {
		const original = window.innerHeight;
		Object.defineProperty(window, "innerHeight", { configurable: true, value: 300 });
		const { w } = make();
		vi.spyOn(input(w).element, "getBoundingClientRect").mockReturnValue({ top: 120, bottom: 156, left: 0, right: 400, width: 400, height: 36 });
		await focus(w);
		expect(parseInt(list(w).element.style.maxHeight, 10)).toBeGreaterThanOrEqual(120);
		Object.defineProperty(window, "innerHeight", { configurable: true, value: original });
	});

	it("follows the field when the page scrolls or resizes while it is open", async () => {
		const { w } = make();
		const rect = vi.spyOn(input(w).element, "getBoundingClientRect").mockReturnValue({ top: 100, bottom: 136, left: 40, right: 440, width: 400, height: 36 });
		await focus(w);
		expect(list(w).element.style.top).toBe("140px");
		rect.mockReturnValue({ top: 60, bottom: 96, left: 40, right: 440, width: 400, height: 36 });
		window.dispatchEvent(new Event("scroll"));
		await nextTick();
		expect(list(w).element.style.top).toBe("100px");
	});

	it("opens downward when there is room", async () => {
		const { w } = make();
		vi.spyOn(input(w).element, "getBoundingClientRect").mockReturnValue({ top: 100, bottom: 136, left: 0, right: 400, width: 400, height: 36 });
		await focus(w);
		expect(list(w).classes()).not.toContain("is-up");
	});

	it("a disabled picker does not open", async () => {
		const { w } = make({ disabled: true });
		await focus(w);
		expect(input(w).attributes("disabled")).toBeDefined();
		expect(calls.length).toBe(0);
	});
});

describe("choosing several (inline and multiple)", () => {
	const added = [];
	const several = (props = {}) => {
		added.length = 0;
		return make({ inline: true, multiple: true, stagedNoun: "to appoint", onAdd: (r) => added.push(r), ...props });
	};

	it("keeps its list open beside the field from the start, floating nowhere, and a blur or Tab does not close it", async () => {
		const { w } = several();
		await flush(10);
		expect(list(w).exists()).toBe(true);
		expect(list(w).classes()).toContain("is-inline");
		expect(list(w).element.style.position).toBe("");
		expect(heads(w)).toEqual(["Your department", "Recent", "Everyone else"]);
		await input(w).trigger("blur");
		await key(w, "Tab");
		expect(list(w).exists()).toBe(true);
		expect(input(w).attributes("aria-expanded")).toBe("true");
	});

	it("adds the person with Enter or a click without choosing, closing or clearing anything", async () => {
		const { w, changes } = several();
		await flush(10);
		await key(w, "Enter");
		await flush(10);
		expect(added.map((r) => r.id)).toEqual(["brian"]);
		expect(changes).toEqual([]); // nothing is "chosen": the list is a way of adding
		expect(list(w).exists()).toBe(true);
		expect(w.find('[data-testid="kt-picker-clear"]').exists()).toBe(false);
		await w.findAll('[role="option"]')[4].trigger("click");
		expect(added.map((r) => r.id)).toEqual(["brian", "zoe"]);
	});

	it("shows an added person greyed with 'Added to this list', moves on to the next choosable row, and keeps the reader's place", async () => {
		const { w } = several();
		await flush(10);
		const input$ = input(w);
		await key(w, "Enter"); // brian
		await w.setProps({ staged: ["brian"] });
		await flush(10);
		const options = w.findAll('[role="option"]');
		expect(options[0].attributes("aria-disabled")).toBe("true");
		expect(options[0].get(".kt-picker-reason").text()).toBe("Added to this list");
		expect(input$.attributes("aria-activedescendant")).toBe(options[1].attributes("id")); // rose: the next choosable
		expect(names(w).length).toBe(5); // the list is the same list
		await key(w, "Enter");
		await w.setProps({ staged: ["brian", "rose"] });
		await flush(10);
		expect(added.map((r) => r.id)).toEqual(["brian", "rose"]);
	});

	it("selects the search text after an add, so typing starts a new search", async () => {
		const { w } = several();
		await flush(10);
		const el = input(w).element;
		el.focus();
		await type(w, "ami");
		await flush(250);
		await key(w, "Enter");
		await flush(10);
		expect(document.activeElement).toBe(el);
		expect([el.selectionStart, el.selectionEnd]).toEqual([0, 3]);
		expect(el.value).toBe("ami");
	});

	it("announces each add and the running count, until the reader types again", async () => {
		const { w } = several();
		await flush(10);
		const live = () => w.get('[role="status"][aria-live="polite"]').text();
		await key(w, "Enter");
		await w.setProps({ staged: ["brian"] });
		await flush(10);
		expect(live()).toBe("Added Brian Achieng. 1 to appoint.");
		await key(w, "Enter");
		await w.setProps({ staged: ["brian", "rose"] });
		await flush(10);
		expect(live()).toBe("Added Rose Odhiambo. 2 to appoint.");
		await type(w, "a");
		expect(live()).not.toContain("Added");
	});

	it("remembers an added person as a recent pick", async () => {
		const { w } = several();
		await flush(10);
		await key(w, "Enter");
		expect(JSON.parse(localStorage.getItem("kt.picker.recent.grace@example.test.bid_opening.committee_member"))).toEqual(["brian"]);
	});

	it("Esc clears the search first, and only a second Esc reaches the dialog around it", async () => {
		const outer = vi.fn();
		const host = document.createElement("div");
		host.addEventListener("keydown", (e) => e.key === "Escape" && outer());
		document.body.appendChild(host);
		const w = mount(RecordPicker, { attachTo: host, props: { source: "s.s", inline: true, multiple: true, fetch: fetchStub } });
		await flush(10);
		input(w).element.value = "ami";
		await input(w).trigger("input");
		await flush(300);
		input(w).element.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
		await flush(10);
		expect(outer).not.toHaveBeenCalled();
		expect(input(w).element.value).toBe("");
		input(w).element.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
		expect(outer).toHaveBeenCalledTimes(1);
	});

	it("an unavailable person is still unavailable, and adding one does nothing", async () => {
		const { w } = several();
		await flush(10);
		await w.findAll('[role="option"]')[3].trigger("click"); // esther, involved
		expect(added).toEqual([]);
	});
});
