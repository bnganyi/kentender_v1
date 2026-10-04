// The asking bidder's own questions: a waiting question says so, an answered
// one shows the answer, an answer sent to the asker only says so, and no
// questions draws nothing.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import MyQuestions from "./MyQuestions.vue";

const WAITING = { key: "q1", question: "May the contracts be from different customers?", received: "Received 26 May 2027, 09:00 EAT", answered: "", status: "Received", status_label: "Received · waiting for an answer", tone: "pending", answer: "", private: false };
const ANSWERED = { ...WAITING, key: "q2", status: "Answered", status_label: "Answered", tone: "live", answer: "Yes.", answered: "Answered 26 May 2027, 11:00 EAT", private: true };

function render(questions) {
	return mount(MyQuestions, { props: { questions }, global: { config: { globalProperties: { __: (s) => s } } } });
}

describe("MyQuestions", () => {
	it("draws nothing when the bid has asked nothing", () => {
		expect(render([]).find('[data-testid="bds-my-questions"]').exists()).toBe(false);
	});
	it("shows a waiting question with when it was received and that it awaits an answer", () => {
		const wrapper = render([WAITING]);
		expect(wrapper.text()).toContain(WAITING.question);
		expect(wrapper.text()).toContain("Received 26 May 2027, 09:00 EAT");
		expect(wrapper.find('[data-testid="bds-my-questions-status"]').text()).toBe("Received · waiting for an answer");
		expect(wrapper.find('[data-testid="bds-my-questions-answer"]').exists()).toBe(false);
	});
	it("shows the answer, and says when it was sent to the asker only", () => {
		const wrapper = render([ANSWERED]);
		expect(wrapper.find('[data-testid="bds-my-questions-answer"]').text()).toBe("Yes.");
		expect(wrapper.text()).toContain("This answer was sent to you only.");
		expect(wrapper.text()).toContain("Answered 26 May 2027, 11:00 EAT");
	});
});
