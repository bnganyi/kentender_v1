// The Award workspace (AWD-CHG-001 v0.4 §9, §10.2 D01; boards D01, D01e):
// the viewer's own award work — no metrics, tracker or next-step block.
import { btn } from "../board/model.js";

export function workspaceBoard(work) {
	const hdr = { title: "Award" };
	if (work && work.forbidden) return { hdr, sec: [{ t: "Your award tasks", empty: "You have no award tasks." }], screen: "workspace-forbidden" };
	const tasks = (work && work.tasks) || [];
	if (!tasks.length) return { hdr, sec: [{ t: "Your award tasks", empty: "You have no award tasks." }], screen: "workspace-empty" };
	return { hdr, screen: "workspace", sec: [{ t: "Your award tasks", tbl: { h: ["Award record", "Tender", "Task", "Holder"], a: "Open award",
		r: tasks.map((t) => [t.award, t.tender_title, t.task, t.holder]), actions: tasks.map((t) => ({ action: "open", args: { award: t.award } })) } }] };
}

export const openAward = (award) => btn("Open award", "open", { award });
