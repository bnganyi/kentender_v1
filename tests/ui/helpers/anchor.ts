import { execSync } from "node:child_process";
import path from "node:path";

/**
 * The seed world's calendar for browser specs (SEED-002 v0.8 §A3; `kentender_core/seeds/calendar.py`).
 *
 * A spec that names an instant of the seeded story ("18 June 2027, 10:00") writes it in story coordinates and
 * asks `world()` for where the site has it. `world()`, `world0()` and `fiscal()` repeat the rules of the same
 * three Python functions from the numbers `calendar.describe()` returns, read once through `bench execute`
 * (no browser, no write). On a site whose world is not anchored they are the identity, so a spec written with
 * them reads the v0.7 world exactly as before.
 *
 * The labels a screen prints (`longDate`, `longDateTime`, `shortDateTime`, `daysAgo`) are built here from a
 * world instant, so an expectation follows the anchor rather than a day written in the spec.
 */
const BENCH_ROOT = path.resolve(__dirname, "../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

export type YearInfo = { fiscal_year: string; label: string; start_date: string; end_date: string; shift_days: number };
export type Calendar = {
	mode: "legacy" | "anchored";
	story_as_at: string;
	anchor: string;
	execution_shift_days: number;
	history_shift_days: number;
	year2_journey_shift_days: number;
	closed_year_extra_shift_days: number;
	closed_year_slot_days?: number[];
	fiscal_years_from_authored: number;
	years: Record<"year0" | "year1" | "year2", YearInfo>;
	boundaries: { baseline_end: string; history_end: string; execution_start: string };
};

let cached: Calendar | null = null;

export function calendar(): Calendar {
	if (!cached) {
		const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_core.seeds.calendar.describe`, { stdio: "pipe", timeout: 120_000, encoding: "utf-8" });
		cached = JSON.parse(output.trim().split("\n").filter((line) => line.startsWith("{")).pop() || "{}") as Calendar;
	}
	return cached;
}

/** Tests of this helper only: use a known calendar instead of reading the site's. */
export function useCalendar(value: Calendar | null): void {
	cached = value;
}

const DAY = 86_400_000;

/** "2027-06-18 10:00:00" or "2027-06-18" as a UTC-based Date (the wall-clock fields are read back with the same convention). */
export function parse(value: string): { moment: Date; dateOnly: boolean } {
	const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value);
	const text = dateOnly ? `${value}T00:00:00Z` : `${value.replace(" ", "T")}Z`;
	return { moment: new Date(text), dateOnly };
}

export function format(moment: Date, dateOnly: boolean): string {
	const iso = moment.toISOString();
	return dateOnly ? iso.slice(0, 10) : `${iso.slice(0, 10)} ${iso.slice(11, 19)}`;
}

function shifted(value: string, days: number): string {
	if (!value || !days) return value;
	const { moment, dateOnly } = parse(value);
	return format(new Date(moment.getTime() + days * DAY), dateOnly);
}

function shiftedYears(value: string, years: number): string {
	if (!value || !years) return value;
	const { moment, dateOnly } = parse(value);
	const moved = new Date(moment.getTime());
	moved.setUTCFullYear(moved.getUTCFullYear() + years);
	return format(moved, dateOnly);
}

/** A story instant moved into the world (`calendar.world`). */
export function world(value: string): string {
	const c = calendar();
	if (c.mode !== "anchored" || !value) return value;
	const { moment } = parse(value);
	const at = (text: string) => parse(text).moment.getTime();
	if (moment.getTime() < at(c.boundaries.baseline_end)) return value;
	if (moment.getTime() < at(c.boundaries.history_end)) return shifted(value, c.history_shift_days);
	if (moment.getTime() < at(c.boundaries.execution_start)) return shifted(value, c.year2_journey_shift_days);
	let days = c.execution_shift_days;
	if (moment.getTime() > at(c.story_as_at)) days += 7; // a live deadline: a week beyond the world's lag behind the run's start
	return shifted(value, days);
}

/** An execution instant of the closed year (`calendar.world0`); `slot` is the Tender chain (0, 1 or 2) it belongs to. */
export function world0(value: string, slot = 0): string {
	const c = calendar();
	if (c.mode !== "anchored" || !value) return value;
	const spread = (c.closed_year_slot_days || [0, 0, 0])[Math.min(Math.max(slot, 0), 2)] || 0;
	return shifted(world(value), c.closed_year_extra_shift_days + spread);
}

/** A fiscal-calendar date moved by whole years (`calendar.fiscal`). */
export function fiscal(value: string): string {
	const c = calendar();
	return c.mode !== "anchored" ? value : shiftedYears(value, c.fiscal_years_from_authored);
}

/** The world's reference instant (the anchor; the story's own in a legacy world). */
export const asAt = (): string => calendar().anchor;

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const pad = (n: number) => String(n).padStart(2, "0");

/** "18 June 2027" */
export function longDate(value: string): string {
	const { moment } = parse(value);
	return `${moment.getUTCDate()} ${MONTHS[moment.getUTCMonth()]} ${moment.getUTCFullYear()}`;
}

/** "18 June 2027, 10:00 EAT" */
export function longDateTime(value: string): string {
	const { moment } = parse(value);
	return `${longDate(value)}, ${pad(moment.getUTCHours())}:${pad(moment.getUTCMinutes())} EAT`;
}

/** "18 June, 10:00" (a Home row's date inside the current year) */
export function dayMonthTime(value: string): string {
	const { moment } = parse(value);
	return `${moment.getUTCDate()} ${MONTHS[moment.getUTCMonth()]}, ${pad(moment.getUTCHours())}:${pad(moment.getUTCMinutes())}`;
}

/** "18 Jun 2027, 10:00 EAT" (a receipt or a Tender fact) */
export function shortDateTime(value: string, seconds = false): string {
	const { moment } = parse(value);
	const time = `${pad(moment.getUTCHours())}:${pad(moment.getUTCMinutes())}${seconds ? `:${pad(moment.getUTCSeconds())}` : ""}`;
	return `${moment.getUTCDate()} ${MONTHS[moment.getUTCMonth()].slice(0, 3)} ${moment.getUTCFullYear()}, ${time} EAT`;
}

/** Whole days from `from` to `to` (calendar days, the way Home counts "N days ago" and "In N days"). */
export function daysBetween(from: string, to: string): number {
	const a = parse(from).moment;
	const b = parse(to).moment;
	const day = (d: Date) => Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
	return Math.round((day(b) - day(a)) / DAY);
}

/**
 * The phrases Home prints (`kentender_core/services/home_time.py`), built the same way from a world instant and the read
 * instant (the anchor by default). Days are calendar days; the year is left out when it is the year of the read.
 */
export const home = {
	days(value: string, at: string = asAt()): number {
		const { moment } = parse(value);
		const read = parse(at).moment;
		const day = (d: Date) => Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
		return Math.round((day(moment) - day(read)) / DAY);
	},
	dayText(value: string, at: string = asAt()): string {
		const { moment } = parse(value);
		const sameYear = moment.getUTCFullYear() === parse(at).moment.getUTCFullYear();
		return `${moment.getUTCDate()} ${MONTHS[moment.getUTCMonth()]}${sameYear ? "" : ` ${moment.getUTCFullYear()}`}`;
	},
	/** "16 June, 11:00" for an instant, "16 June" for a plain date. */
	exact(value: string, at: string = asAt()): string {
		const { moment, dateOnly } = parse(value);
		const text = home.dayText(value, at);
		return dateOnly ? text : `${text}, ${pad(moment.getUTCHours())}:${pad(moment.getUTCMinutes())}`;
	},
	plural(count: number): string {
		return count === 1 ? `${count} day` : `${count} days`;
	},
	/** "Received 2 days ago (16 June, 11:00)" */
	entered(verb: string, value: string, at: string = asAt()): string {
		const ago = -home.days(value, at);
		const exact = home.exact(value, at);
		if (ago < 0) return `${verb} ${exact}`;
		if (ago === 0) return `${verb} today (${exact})`;
		if (ago === 1) return `${verb} yesterday (${exact})`;
		return `${verb} ${home.plural(ago)} ago (${exact})`;
	},
	/** "Waiting 2 days (since 16 June, 15:30)" */
	since(word: string, value: string, at: string = asAt()): string {
		const ago = -home.days(value, at);
		const exact = home.exact(value, at);
		if (ago < 0) return `${word} (since ${exact})`;
		if (ago === 0) return `${word} today (since ${exact})`;
		return `${word} ${home.plural(ago)} (since ${exact})`;
	},
	waiting: (value: string, at: string = asAt()) => home.since("Waiting", value, at),
	outstanding: (value: string, at: string = asAt()) => home.since("Outstanding", value, at),
	/** "Overdue since 15 June" */
	overdueSince: (deadline: string, at: string = asAt()) => `Overdue since ${home.dayText(deadline, at)}`,
	/** the badge and exact time of a Coming up row: ["In 7 days", "25 June, 11:00"] */
	comingUp(value: string, at: string = asAt()): [string, string] {
		const days = home.days(value, at);
		const badge = days <= 0 ? "Today" : days === 1 ? "Tomorrow" : `In ${days} days`;
		return [badge, home.exact(value, at)];
	},
};

/** The year `key` ("year0" | "year1" | "year2") of the world: its Fiscal Year name, label and dates. */
export const year = (key: "year0" | "year1" | "year2"): YearInfo => calendar().years[key];

/** "1 Jul 2027" (a date as the Needs and Planning screens print it). */
export function shortDate(value: string): string {
	const { moment } = parse(value);
	return `${moment.getUTCDate()} ${MONTHS[moment.getUTCMonth()].slice(0, 3)} ${moment.getUTCFullYear()}`;
}

/** The first day the seeded procurement rules are in force (`site_setup.PROFILE_EFFECTIVE`): the first seeded year's 1 January in an anchored world, 1 July of Year 1 before. */
export function ruleWindowStart(): string {
	const c = calendar();
	return c.mode === "anchored" ? `${c.years.year0.start_date.slice(0, 4)}-01-01` : c.years.year1.start_date;
}

/**
 * The mapping for a block of events whose story runs past the story's "now" (`calendar.block`): the execution shift and the
 * block's own whole weeks earlier, so its last instant is not later than the anchor; no live-deadline week is added.
 */
export function block(lastStoryInstant: string): (value: string) => string {
	return (value: string) => {
		const c = calendar();
		if (c.mode !== "anchored" || !value) return value;
		const over = parse(lastStoryInstant).moment.getTime() - parse(c.story_as_at).moment.getTime();
		const extra = over > 0 ? -7 * Math.ceil(over / (7 * DAY)) : 0;
		return shifted(value, c.execution_shift_days + extra);
	};
}

/** "2027-07-12T10:00" (a datetime-local input's value) from a world instant. */
export function inputDateTime(value: string): string {
	const { moment } = parse(value);
	return `${moment.toISOString().slice(0, 10)}T${pad(moment.getUTCHours())}:${pad(moment.getUTCMinutes())}`;
}

/** "July 2027" */
export function monthYear(value: string): string {
	const { moment } = parse(value);
	return `${MONTHS[moment.getUTCMonth()]} ${moment.getUTCFullYear()}`;
}

/**
 * The whole years a block of instants moves back so its last instant is not later than the anchor (`calendar.years_back`); 0 on a site whose world is not
 * anchored. Contract Management tells its story in calendar months and quarters, so its block moves by whole years.
 */
export function yearsBack(lastStoryInstant: string): number {
	const c = calendar();
	if (c.mode !== "anchored") return 0;
	const anchor = parse(c.anchor).moment.getTime();
	const last = parse(lastStoryInstant).moment;
	let years = 0;
	for (;;) {
		const moved = new Date(last.getTime());
		moved.setUTCFullYear(moved.getUTCFullYear() - years);
		if (moved.getTime() <= anchor) return years;
		years += 1;
	}
}

/** The synthetic Contract Management story moves back as one block of whole years (`kentender_contracts/simulation/timeline.py`); this is that move. */
export const cmWorld = (value: string): string => shiftedYears(value, -yearsBack("2028-07-28 11:00:00"));
