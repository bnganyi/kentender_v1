User Interface Design vs Implementation Issues

# Issues

Looking back across everything found in this session, the same few mechanisms explain nearly all of it:

**The rule was written down, but nothing checked the code against it.** The clearest case is the last one: the file's own header comment says "waiting work is status on its own document, never a duplicate disabled task row," and the code nine lines below it does exactly that. The rule wasn't missing or unclear. Nobody re-read the comment against what the code actually did before calling it finished.

**A fix gets added to the command someone happened to be working on, not to every place the same fact needs to hold.** The "accepted Need never shows up in an already-open plan" bug is a good example: the sync step existed in two of the three places that needed it (opening a plan, submitting it) but never made it into the third (just viewing one). Each command was built and tested in isolation; nobody asked "where else does this same truth need to stay current."

**Verification covers the one path someone clicked through, not the others a real user takes.** "Start departmental plan does nothing" only happened if you landed on the create screen any way other than clicking the one button that had been tested. The department-picker bug was the same shape: worked when you clicked through, broke on a refresh or a direct link. This codebase has a standing rule to test direct load, refresh, and back/forward specifically because it keeps failing quietly otherwise, and it kept failing quietly here too.

**Copied boilerplate carries its mistakes forward.** Eleven dialogs closed on an outside click while forty-five others didn't, because dialogs get built by copying an existing one, and one bad copy got reused as the template for the next ten. There's no single shared dialog component here to fix once, so an error made once in the wrong file becomes the pattern everyone after it copies.

**Cases the spec calls out as the normal case get handled ad hoc, or not at all, per screen.** The spec deliberately tests a person holding two roles in two departments, that's not an edge case in this domain, it's a named regression fixture. But the workspace's own "spotlight" section just grabbed "the first department" with no thought for a second one, and the "ready for review" card didn't check whether there was anything to review, only which role the viewer held. Each screen re-decided how to handle that situation on its own instead of there being one place that gets it right and everything else uses.

**Green tests get read as "matches the design," when the tests check something narrower.** Every one of these shipped behind a passing suite. That's possible because the tests assert the shape of a response, not the specific sentence in the spec that got violated. A test can confirm a field exists without confirming it says the right thing, or that two different screens agree with each other about it.

The throughline: this is a lot of small services and screens that each implement one rule correctly in isolation, without anything cross-checking that the same rule holds everywhere it's supposed to, or that the finished screen was actually read against the paragraph in the spec that describes it. Passing the automated suite has been treated as the finish line, when the suite doesn't ask the same question the spec does.

# Suggested Remedy

A remedy for each mechanism, in the same order:

**Check the code against the written rule before calling it done, not just against the test result.** Every one of these bugs sat within a few lines of the sentence it violated, in the spec, the artboard, or the file's own comment. The fix isn't a new tool, it's actually doing the comparison: after building a screen, reopen the spec paragraph it's meant to satisfy and the artboard image, and read them against the code line by line. "Tests pass" answers a narrower question than "matches the design," and this session kept treating the two as the same thing.

**Find every caller before calling a fix complete.** The Need-sync bug existed because the same fix landed in two of three places that needed it. When a rule like "this must stay in sync" gets added, the right question is "who else reads this same data," not just "does my command work now." One test that asserts the invariant across every entry point catches this; three separate tests that each check their own command doesn't.

**Test direct load, refresh, and back-forward as a standing requirement, not a reminder that gets skipped.** This codebase already has that rule written down, and it still kept failing because it's easy to stop at "the button works." Making this a required part of finishing a screen, not an optional extra check, is the actual fix, since the rule already exists and isn't being followed.

**Build one shared dialog component instead of copying files.** Eleven broken dialogs trace to zero shared code. A single component that every dialog wraps means the backdrop-click behavior gets fixed once and stays fixed, instead of re-drifting the next time someone copies a file to start a new one.

**Route every "what can this actor do here" question through one function, not a fresh guess per screen.** The codebase already has the right idea in places, a shared resolver that answers "is this person the author, the head of department, both, or neither" for a given unit. Screens that reimplemented that logic themselves are exactly the ones that got the two-role and two-department cases wrong. Where the spec genuinely doesn't say what a multi-department view should look like, that should stop and get resolved as a real decision, not get silently defaulted to "just use the first one."

**Write tests that name the sentence they're proving.** A test that checks a field exists doesn't catch two screens disagreeing about what that field should say. Tying each acceptance test to the specific spec line it verifies means a reviewer can tell whether the test actually protects the rule, not just the shape of the response.

If I had to pick the one with the most leverage: the first. Almost everything else here would have been caught by someone actually reading the artboard and the spec paragraph next to the finished screen before moving on, since the answer was usually already sitting in writing a few lines away from the mistake.
# What was actually done about it (24 September 2026)

The remedy above put the most leverage on the first mechanism: *"the fix isn't a new tool, it's actually doing the comparison — reopen the spec paragraph and the artboard image, and read them against the code line by line."*

That was tried and it did not hold. Between it and this note there were five reconciliation passes across Procurement Planning and Departmental Needs, and two mechanical gates. The owner still found deviations on the first screen he looked at, every time he looked.

The reason is narrower than "people forgot". The gate that existed **did** compare against the artboard, but it compared the artboard's ordered landmark **text** — the words in headings, labels, table headers and buttons. Three things are invisible to that, by construction:

- **A container.** A wrapper has no text of its own, so dropping the `.kt-group` around Plan checks changed no landmark.
- **An element demoted to another element.** "Approval" as a `.kt-label` where the board titles a region with `h2` is the same string in the same position.
- **Anything without text.** A disclosure chevron is an SVG. Eight disclosure heads had lost both their title row and their chevron.

That is the whole of the "green tests get read as matches-the-design" mechanism, made specific. The defects were not subtle and nobody was careless; the instrument could not see them.

So the remedy changed from a discipline to a check. `tests/ui/fidelity/skeleton.js` reduces both the board and the built screen to their landmark skeletons and compares them as a contract — every container the board draws, in order, under the same chain of landmark ancestors — with non-landmark elements transparent, so an implementation-only wrapper stays legal. Structure the board does not draw is recorded in `tests/ui/fidelity/departures/<module>.js` with a reason and an authority, and a stale entry fails, because the previous register of departures had already rotted unnoticed: `PLN-CHG-001_FOLLOW_UPS.md` still names four landmark exemptions that no longer exist in any spec file.

One more mechanism worth naming, because it is the same shape as the original list and was not on it: **claims of enforcement outran the enforcement.** The geometry probes are described as enforced in `AGENTS.md` and in the `Makefile` and have no call sites at all. `expectLayoutSanity` is required by the rules on every editor journey and was wired into one. A rule that describes a check nobody runs is not neutral — it is read as assurance. The rule added alongside this work is that a rule and the thing that fails when it is broken land in the same change.
