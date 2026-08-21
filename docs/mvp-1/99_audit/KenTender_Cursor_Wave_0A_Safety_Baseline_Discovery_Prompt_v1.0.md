# KenTender Cursor Wave 0A — Safety Baseline Discovery Prompt

**Document ID:** KENTENDER-CURSOR-W0A-1.0  
**Version:** 1.0  
**Date:** 11 August 2026  
**Status:** Approved recovery activity when run exactly as bounded below  
**Mode:** Read-only discovery plus analysis-document creation  
**Parent authority:** KenTender MVP Correction Control and Backlog v1.0, approved 11 August 2026

## 1. Objective

Prepare a safe, reviewable proposal for the KenTender recovery baseline before any application correction begins.

This Wave 0A pass shall determine:

- the correct repository and application boundaries;
- the exact files that should be version controlled;
- the files and directories that must be excluded;
- potential secret or environment-data risks without exposing secret values;
- the database and application-file backup procedure;
- the restore-verification procedure; and
- the current test commands that should be captured in Wave 0B.

Wave 0A must stop for product-owner review. It does not create the repository baseline, backup the database, run migrations or execute application tests.

## 2. Controlling documents

Read these first:

1. `KenTender_MVP_Cross_Module_Operating_Model_v1.0.md` — approved;
2. `KenTender_MVP_Correction_Control_and_Backlog_v1.0.md` — approved;
3. `KenTender_MVP_Semantic_and_Workflow_Assurance_Audit_v1.1.md` — correction analysis;
4. the read-only audit outputs `00`–`09` under `docs/mvp-1/99_audit/`.

Do not use older module requirements, Stitch packs, Cursor packs or tracker `Done` statuses as authority for Wave 0A scope.

## 3. Absolute restrictions

Do not:

- run `git add`, `git commit`, `git init`, `git clean`, `git reset`, `git checkout`, `git restore` or any command that changes Git state;
- create a branch or tag;
- modify `.gitignore`, `.gitattributes` or any repository file;
- delete, move, rename or reformat files;
- run a database backup yet;
- run `bench migrate`, seed commands, patches, fixtures, schema changes or database writes;
- run application tests in this discovery pass;
- run build, install, update, cache-clearing or asset-generation commands;
- access or print secret values;
- copy site configuration, credentials, private keys or database dumps into the proposed repository;
- archive the entire bench, home directory or sites directory;
- follow symlinks into duplicate application trees without reporting them; or
- silently decide the tracked-file set.

The only permitted writes are the Wave 0A analysis outputs named in section 10.

## 4. Privacy and secret-handling rule

Search for secret risk by filename, configuration structure and recognised credential patterns, but never print a secret value.

For each risk, report only:

- relative path;
- risk category, such as database password, API key, private key, session secret or environment file;
- whether it is currently tracked, untracked or outside the proposed scope; and
- recommended exclusion or sanitisation action.

Redact all matched values as `[REDACTED]`. Do not include even partial tokens, hashes of secrets or connection strings in reports.

## 5. Repository-boundary discovery

Starting from the current KenTender bench and `apps/kentender_v1`, determine:

1. every Git worktree or repository boundary;
2. whether `apps/kentender_v1` is itself a repository;
3. whether the bench root is the intended repository or only a runtime container;
4. the relationship between `apps/kentender_v1` and the `apps/kentender_*` symlinks;
5. whether following those links would duplicate files;
6. the current branch, commit state and status of each discovered repository;
7. nested repositories or submodules;
8. generated/runtime directories within the intended source tree; and
9. large files that would make the initial baseline unsuitable.

Prefer the smallest source-controlled boundary that contains the KenTender application code, requirements, migrations, seeds and tests without including the Frappe bench runtime or site data.

Do not assume the bench root is correct merely because it contains `.git`.

## 6. Proposed tracked-file manifest

Produce a complete relative-path manifest of files proposed for the initial baseline.

Include source-controlled material such as:

- KenTender application Python, JavaScript, JSON, HTML, CSS and configuration source;
- DocType definitions;
- patches and migration source;
- tests and test fixtures that belong to the source tree;
- seed source and validators;
- requirements and approved control documents;
- Makefiles and project-level test configuration;
- package metadata required to install or run the KenTender apps; and
- deliberate static assets that are source, not generated build output.

Do not include a path merely because it is under the application directory. Classify each category.

For each manifest category, report:

- file count;
- total size;
- representative paths;
- rationale for tracking; and
- duplication or symlink risk.

## 7. Proposed exclusion manifest

Identify files and directories that should not enter the baseline, including as applicable:

- `sites/` and site-private files;
- database dumps and backups;
- logs;
- caches and bytecode;
- virtual environments;
- node modules;
- generated/built assets where reproducible;
- temporary files;
- screenshots or test reports not deliberately retained as fixtures;
- credentials and environment files;
- uploaded documents or user data;
- socket, PID and lock files;
- large binary artifacts with no source-control justification; and
- duplicate content reachable through application symlinks.

Compare the proposed exclusions with all relevant existing ignore files. Report missing or dangerously broad ignore rules, but do not edit them.

## 8. Backup and restore proposal

Design, but do not execute, a Wave 0B backup procedure for:

### 8.1 Database

Identify:

- the target site;
- the database engine detected;
- the appropriate non-destructive Frappe/bench backup mechanism;
- whether private/public files should be included;
- expected destination outside the proposed source repository;
- encryption/access-control considerations;
- expected size if safely measurable without dumping data; and
- a verification method that does not expose data.

### 8.2 Application source

Propose a snapshot of the intended KenTender source boundary before the initial commit. The snapshot must:

- exclude secrets, site data, caches, generated runtime files and existing backups;
- preserve permissions and symlink information where required;
- use an explicit destination that is not inside the source tree; and
- include a checksum or equivalent integrity record.

### 8.3 Restore verification

State exactly how Wave 0B will prove that:

- the database backup exists and is readable;
- the source snapshot is complete for its declared scope;
- checksums match;
- the restore commands are known; and
- no restore is performed over the live environment during verification.

Do not claim a backup is valid merely because a command returned exit code zero.

## 9. Baseline-test discovery

Inventory the existing commands for:

- unit tests;
- integration tests;
- Frappe tests;
- Playwright/UI tests;
- seed validation;
- permission and scope tests; and
- module Makefile gates.

For each command, report:

- what it covers;
- whether it writes to a database or test site;
- whether it seeds, migrates, builds assets or clears caches;
- required services and environment assumptions;
- estimated duration if documented or observable without running it;
- whether it is safe for Wave 0B; and
- the output/report path to retain outside generated source files.

Do not run the commands during Wave 0A.

The baseline plan must preserve currently failing tests as evidence. Do not change tests or expected results to make the baseline green.

## 10. Required outputs

Create these analysis files under a dedicated Wave 0A audit directory, preferably `docs/mvp-1/99_audit/wave_0a/` if that directory is within the intended source boundary:

### 10.1 `00_Wave_0A_Executive_Summary.md`

Include:

- recommended repository boundary;
- current Git safety assessment;
- proposed tracked/excluded totals;
- secret-risk count by category without values;
- recommended backup approach;
- recommended baseline-test set; and
- explicit blockers requiring product-owner action.

### 10.2 `01_Repository_Boundary_and_Symlink_Map.md`

Show all discovered Git boundaries and relevant application symlinks. Identify the one proposed source-of-truth path.

### 10.3 `02_Proposed_Tracked_Files.txt`

One exact relative path per line, sorted deterministically. Do not include secret values or file contents.

### 10.4 `03_Proposed_Exclusions.md`

List exclusion patterns, matched categories, counts, sizes and rationale. Include required ignore-rule changes as a proposal only.

### 10.5 `04_Secret_Risk_Report.md`

Report path and category only, with every value redacted. Include false-positive notes where applicable.

### 10.6 `05_Backup_and_Restore_Plan.md`

Provide exact proposed commands with placeholders where a command would otherwise reveal a secret. Commands are for later approval and must not be executed in Wave 0A.

### 10.7 `06_Baseline_Test_Plan.md`

List the ordered test commands, mutation characteristics, dependencies, expected outputs and stop conditions for Wave 0B.

### 10.8 `07_Wave_0B_Approval_Checklist.md`

Provide a concise checklist for the product owner to approve:

- repository boundary;
- proposed tracked-file manifest;
- proposed exclusions and ignore changes;
- backup destinations and procedure;
- restore verification;
- baseline-test commands; and
- whether Wave 0B may create the initial branch and commit.

## 11. Evidence standard

Every conclusion must cite an exact path or non-mutating command result.

Report totals deterministically. If a symlink, permission restriction or very large directory prevents complete enumeration, identify the exact limitation rather than guessing.

Do not use `find` or archive commands that traverse the whole home directory, root filesystem or unrelated application trees. Keep discovery bounded to the bench metadata and proposed KenTender source paths.

## 12. Completion and stop condition

Wave 0A is complete only when:

- the proposed source-of-truth repository boundary is explicit;
- the tracked-file manifest is complete and reviewable;
- exclusions and secret risks are documented without disclosing values;
- backup and restore procedures are proposed but not executed;
- the baseline-test plan is proposed but not executed;
- no Git state, database, application, seed, test or configuration file has changed; and
- the product owner has a single approval checklist for Wave 0B.

Stop after producing the eight outputs. Do not begin Wave 0B and do not propose Wave 1 implementation code.
