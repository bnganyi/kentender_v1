It's genuinely hard to know where to put your focus right now.

Our industry has changed, quickly, given the rise of LLMs.

Terrain that once seemed predictable, and like the ground you were used to walking on, now seems strange and unfamiliar.

Like visiting your home town after an earthquake. Somewhat familiar and yet completely alien at the same time.

And while some are embracing our new AI overlords, others are left to decry the loss of craft, and identity.

Whatever your perspective, we're left with one question.

What to do?

My approach now, as ever, is to experiment.

In the face of all the hype, claims and counter claims.

There's mileage in running experiments - small, focused, to see how the latest models can help developers go better, faster, or both now typing speed is no longer the bottleneck.

Here's a concrete example you can copy.

**Tests in the real world**

A few years ago I worked for a company that prided itself on its extreme programming credentials.

Pair programming was the norm, every commit was deployed to production within minutes (after going through an automated CI/CD process) and extensive logging meant anything that fell over in production was jumped on by someone on the dev team.

But at one point it became clear too many defects were making it into production code.

So the order came from on high to increase test coverage across several of our main applications.

While the intentions were sound, the reality was this achieved very little.

The entire team spent a week increasing test coverage.

But there's real danger in chasing a single metric like this.

Lots of tests went in, and coverage increased.

But the tests were often tightly coupled to the implementation code.

Mocks being set up and configured in the tests, meaning you had to know and capture what the internals of the code under test was doing, making the tests brittle and prone to failure.

It basically meant you couldn't refactor the code under test without also changing the tests.

So adding more tests, whilst coverage did go up, put an even larger straightjacket around the development team and their ability to modify and extend the code.

**Increase or maintain coverage, and remove the straightjackets**

Fast forward a decade, and I was trying to do something similar, but on a project I'm building using Claude Code.

In this case, I'm actually reasonably happy with the test coverage.

But less happy with the number of lines of test code.

I have to admit, I let AI go to town with adding its own tests for this application and, gone to town it has...

Before my experiment, I was staring at 33,000 lines of test code, and about 75% coverage.

More lines of code means more to maintain, more possible straightjackets around production code, and more likelihood of the LLM changing tests at the same time as production code (which means we've too many moving parts and our confidence in whether we're preserving behaviour starts to plummet).

So I decided to try something in Claude Code, after seeing someone else try this exact same thing.

Do testing surgery. Remove hundreds of thousands of lines of tests without dropping use case coverage. Limit this to the **/specific feature/** code only.

Notice this doesn't specify **how** to do testing surgery, just the goal and constraints.

**First it told me I was wrong**

Before deleting a single line it measured.

The whole test suite was around 550,000 lines, with about 33,700 covering this specific part of the application.

So removing "hundreds of thousands of lines" was impossible, and Claude said as much before it started the work.

**Then it captured a baseline**

Claude switched on a coverage tool and recorded exactly which lines and branches of the production code were covered by tests.

It actually ran this twice to check for variability between runs.

After that it followed a rule: whatever gets deleted, every one of those lines covered by tests must still be covered afterwards.

Which is interesting in retrospect, because it's the opposite of what my team did all those years ago, where they treated coverage as a target.

Here Claude set the coverage level as the floor. It could change anything else, but that figure (and the exact lines covered) had to remain constant.

**Split the work, like a team lead**

After that it divided the code into areas, and spun up agents to work on them in parallel, each in its own isolated copy (worktree) of the repo.

They all worked to this brief:

- Collapse near-identical tests into a single table of cases
- Pull repeated setup into shared helpers
- Delete tests that only checked whether a mock returned what it was told to return

For every test they deleted, they had to note which surviving test now covered that behaviour.

**The results**

- Test code: 33,692 lines down to 25,987 (7,705 fewer, about 23%)
- Coverage: 76.6% before, 76.6% after
- Lines or branches of coverage lost: zero
- Production code changed: zero

Not hundreds of thousands, but nearly a quarter of the test code gone and nothing lost.

**So, what to do?**

A lot of the reduction here came from tidying up (tables, shared setup) rather than reducing the tight coupling that made my old team's tests so painful.

The straightjacket is lighter, but it's still there.

So that naturally leads to the next experiment, to see if I can raise the tests up to the highest 'seam' without losing coverage.

But overall, this one prompt to Opus 5.5 did a better job of optimising tests than an entire dev team did in one week a decade ago.

It established metrics, implemented a safety net, and found a way to prove it hadn't broken anything along the way.

**Go forth and experiment**

If you're struggling to 'keep up, and get solid results from AI (and feeling like you're losing your craft), experiments like these are a solid tactic.

Find something you want to improve, spin up Opus 5.5, Fable, Astra, and see how it handles the task.

And resist the temptation to prescribe how the LLM should achieve its goal.

As the models get better, they need less steering, and you can always course correct once you see what they're up to.

\-- Jon