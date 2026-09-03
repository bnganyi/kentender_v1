KenTender Industry Design Refinement

Read your KenTender file for context — this makes sense for where the design work is now.

The greyness isn't really a lightness problem, it's a structural one: right now your surface (#e2e4e6) is _darker_ than your ground (#f2f2f3), so every card, input, and dialog is a grey block sitting on grey. No amount of tuning either value fixes that — the whole page averages out to concrete. The move that changes the feel in one stroke is to **invert the relationship: white surfaces on a light ground.**

\--color-bg: #f4f5f7; /\* ground stays a quiet cool paper \*/

\--color-surface: #ffffff; /\* cards, dialogs, inputs become white \*/

\--color-surface-2: #eef0f3; /\* wells: table header rows, seg-control track, code \*/

\--color-text: #16181a; /\* a touch darker now that the ground is brighter \*/

Why this works better than just whitening the bg:

**Cards become paper, not slabs.** With --color-surface: #ffffff, every filled object — cards, the dialog, text inputs — reads as a clean sheet pinned to the board. The hairline border + corner marks do the "blueprint" work; the fill no longer has to. This is also truer to the metaphor: a drawing board with white sheets on it, rather than grey sheets on grey board.

**You keep the separation you fought for.** bg → surface still has a real step (~#f4f5f7 → #ffffff), just running lighter-upward instead of darker-downward. Elevation now reinforces it naturally: higher surfaces are whiter, which matches how --shadow-sm/md/lg already imply depth.

**Two refinements that kill the remaining "depressing" quality:**

1. **Give the neutrals a whisper of the steel hue.** Dead-chroma greys are what read as dreary. Regenerate the neutral ramp in OKLCH with ~0.006–0.010 chroma at the accent's hue angle (~250°). It's imperceptible as "blue" but the whole page stops feeling like wet cement and starts feeling like cool paper — consistent with the blueprint identity rather than fighting it.
2. **Lighten the top of the neutral ramp to match.** neutral-100/200 need to land between the new bg and white so tinted fills and hovers don't jump back to the old grey. Your solid-grey secondary text (neutral-700/800) survives unchanged — it actually gains contrast on white surfaces.

Knock-on effects to patch in the same pass, or they'll bite:

- **Borders need one step more weight.** Hairlines that were visible on #e2e4e6 can wash out on white. If card borders are neutral-300 now, check them at neutral-300/350 on white; the wireframe must stay _drawn_, not implied.
- **Inputs:** white fill + hairline border is the clean look, but then the :hover/:focus tint needs to be the thing that distinguishes an editable field from a card. A very light accent-100 wash on focus does it.
- **Disabled at 45% opacity** may go near-invisible on white. Swap to solid tokens (neutral-400 text, neutral-100 fill).
- **.kt-status chips** will look better automatically — 10% tints on white are cleaner than on grey — but re-check the is-pending neutral chip specifically; it was defined against the darker surface.
- **Duotone images:** raise the light end of the map toward white so photographs brighten with the page instead of staying muddy anchors.
- **The dialog backdrop scrim** can lighten slightly (or stay) — but verify the dialog still separates, since it's now white-on-scrim instead of grey-on-scrim.

One thing I'd _not_ do: pure white ground (--color-bg: #ffffff). You lose the board-vs-sheet layering entirely, cards only exist via borders, and a legally dense screen becomes a wall of white with hairlines — harder to scan, not easier. The light-grey ground is doing real work as the "drawing board"; it just shouldn't be the color of the objects sitting on it too.

If you paste or upload styles.css I can write the actual patch — the ramp regeneration in OKLCH plus the border/disabled/duotone follow-ups — and update theme.json and the readme so they don't drift.