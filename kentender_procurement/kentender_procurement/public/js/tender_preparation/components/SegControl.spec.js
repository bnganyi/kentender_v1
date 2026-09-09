// §8.0 "Two choices — Yes/No switch or radio; never free text".
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import SegControl from "./SegControl.vue";

describe("SegControl — §8.0 finite choice", () => {
	it("renders exactly the listed values as radios, never a text input, and marks the selection", () => {
		const w = mount(SegControl, { props: { name: "x", label: "Pre-tender meeting", modelValue: false } });
		expect(w.findAll("input[type='radio']").length).toBe(2);
		expect(w.findAll("input[type='text']").length).toBe(0);
		expect(w.findAll("label").map((l) => l.text())).toEqual(["Yes", "No"]);
		expect(w.findAll("label")[1].classes()).toContain("is-selected");
		expect(w.attributes("aria-label")).toBe("Pre-tender meeting");
	});

	it("emits the typed option value (boolean or string) and never the DOM string for booleans", async () => {
		const w = mount(SegControl, { props: { name: "y", modelValue: null } });
		await w.findAll("input")[0].setValue();
		expect(w.emitted("update:modelValue")[0]).toEqual([true]);
		const modes = mount(SegControl, { props: { name: "m", options: ["Physical", "Online"], modelValue: "Physical" } });
		await modes.findAll("input")[1].setValue();
		expect(modes.emitted("update:modelValue")[0]).toEqual(["Online"]);
	});

	it("disables every radio when disabled (read-only viewers)", () => {
		const w = mount(SegControl, { props: { name: "z", modelValue: true, disabled: true } });
		expect(w.findAll("input").every((i) => i.attributes("disabled") !== undefined)).toBe(true);
	});
});
