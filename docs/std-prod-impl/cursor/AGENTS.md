# KenTender Agent Instructions

This repository implements the KenTender Standard Tender Document Engine and related procurement workflows.

## Core execution rule

Work as a bounded task executor. Do not act as an unconstrained architect unless explicitly asked to produce architecture documentation.

Before editing files for a task:

1. Read the task and listed context files.
2. Identify the exact files expected to change.
3. Identify tests to add or update.
4. Identify risks, blockers, or ambiguities.
5. Confirm that the task does not violate STD lifecycle, immutability, source-traceability, or governance rules.
6. Wait for explicit approval before modifying files when the prompt asks for a plan first.

## Project principles

- The STD Engine is the legal/source-of-truth configuration layer.
- Tender Management consumes generated STD outputs; it must not recreate STD legal rules independently.
- Official Standard Tender Documents are master templates.
- Actual tenders are tender-specific instances or calibration fixtures, not master STD templates.
- Active STD versions are immutable.
- Published tender bundles are immutable.
- Post-publication changes require addendum/supersession handling.
- Locked ITT and GCC clauses must not be edited through tender configuration.
- TDS, SCC, requirements, forms, schedules, and appendices are controlled configuration surfaces.
- Do not hard-code the IT STD into the generic STD Engine.
- Do not bypass approval workflows or state-transition guards.

## Completion standard

A task is not complete unless:

- The requested behavior is implemented.
- Tests are added or updated.
- Relevant checks have been run where available.
- `docs/MODULE_STATUS.md` is updated when the task changes module status.
- Any follow-up work is documented explicitly.
