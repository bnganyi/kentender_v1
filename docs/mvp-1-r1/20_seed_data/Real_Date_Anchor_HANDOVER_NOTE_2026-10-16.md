# Real-date anchor: hand-over note to the module sessions (16 October 2026)

Written for: engineers and module sessions that seed, test or demonstrate the canonical world. Plain language; the rules are in SEED-002 v0.9 (proposed) and KT-STD-001 v1.30 (approved).

## What changed

1. **The canonical world is read as at an anchor, not at 18 June 2027.** `make seed-canonical ANCHOR=real` stores an anchor (the latest Friday 10:00 not later than the run's start) on the site (site default `kt_seed_world_state`) and builds three financial years around it: Year 0 closed, Year 1 carried out, Year 2 prepared. No seeded instant is later than the real clock. `ANCHOR=story` builds the v0.7 world. `ANCHOR=real` is the Makefile default since the development site was reseeded (17 October 2026).
2. **The prepared year goes as far as the anchor allows.** At an October anchor that is Departmental Needs: the Year 2 Annual Plan does not exist. A test or spec that reads the Year 2 plan must build its own, or skip when the Year 2 Annual Plan has no active version.
3. **Both sites are on the anchor of Friday 16 October 2026 10:00** (test site repaired and the development site migrated and reseeded on 17 October; both validate; the test clock is pinned on the test site only). Rebuild: `make seed-canonical SITE=<site> REBUILD=True FORCE=True` (6 to 25 minutes, longer when anything else runs on the site; after a failed rebuild a plain run finishes it).
4. **A command never runs at an instant later than the real clock** (`kentender_core.seeds.clock.at`, in an anchored world).
5. **Clock policy** (`kt_test_clock_policy`): `off` on the development site; the test site stays `free` (not `never_ahead`) because the Python suite has not been re-run under `never_ahead`.
7. **A second permanent Budget Approver** (Hellen Mutua, `hellen.mutua@moh.example.test`, site-wide) is in the canonical world on both sites since 17 October (KT-STD-001 v1.31, proposed): the one Approver could not approve what she had confirmed. A fixture or script that adds its own second Approver does not need to.
6. **Anchor-dependent text:** an anchor of 16 October (not 9 October) is what the sites hold now; tests and specs read it at run time (`calendar.describe()`), so none names the day.

## How a test or spec names a seeded date

| You have | Use |
|---|---|
| An instant of the story ("17 June 2027 10:00") | `W(...)` = `kentender_core.seeds.calendar.world` |
| A fiscal-calendar date (a Required by, a year's end, a rule's start) | `F(...)` = `calendar.fiscal` |
| A value the system derives from an earlier act (a reply deadline seven days after a notice) | `shift(W(base), 7)` — never `W(base + 7)`: `W` adds a week to an instant after the story's "now" |
| A story that runs past the story's "now" and keeps its own spacing (the Award tests) | `calendar.block(last)`; Award tests import `W` from `award/test_services/timeline.py` |
| A story told in months and quarters (Contract Management) | `calendar.years_block(last)`; `kentender_contracts.simulation.timeline.D` |
| Text a screen prints for such a date | `kentender_core.tests.anchor_display` (`dt_eat`, `d_short`, `home_dt`, …; `Display(mapper)` for a block) |
| The same in a browser spec | `tests/ui/helpers/anchor.ts` (`world`, `fiscal`, `shortDateTime`, `home.*`, `cmWorld`, `awardWorldInstant`) |

## Traps found on the way

- Wrapping a test that only parses or formats a date breaks it; leave pure tests alone.
- Home reads the real site time. A test that needs "within thirty days of the action" freezes the clock at an instant after the action (`clock.at`); an instant later than the real clock cannot be frozen in an anchored world.
- A design-fidelity spec that finds an element on the board by its text must keep the board's own literal text.
- Month names: "May" is both short and long; check which form a screen prints before converting.
- Tests do not roll back on this bench. Budget tests leave `bud.*@test.local` users, extra budgets, reservations, commitments and `KT Budget Test …` organisation units; ERPNext's test loader leaves `_Test Fiscal Year …` rows that make the Strategy tests fail. Rebuild the world after a run, and delete those rows.
- A world older than 60 days fails validation on a `never_ahead` site.
- Two sessions running tests on the one site at once make both slow and corrupt each other's worlds; take `/tmp/kt-test-site.lock` per module and say so on the site's channel.
