\# KenTender Agent Rules



Before making changes, read:

\- docs/architecture/kentender-architecture-rules.md

\- docs/architecture/global-architecture-v2.md

**IMPORTANT: Rule Precedence Hierarchy**

All rules follow this priority (highest to lowest):
1. User's explicit instructions in current conversation
2. Execution discipline rules (06-execution-gatekeeper.md)
3. Framework generator rules (07-framework-generators-first.md)
4. Planning workflow guidance
5. General architecture rules

**Rule Conflict Detection**
Before any action, check for conflicts using 10-rule-conflict-detection.md

**User Override Mechanism**
Any instruction with "DO NOT" or "NEVER" automatically overrides all rules (11-user-override-mechanism.md)



\## Core Rules

1\. \*\*Respect app ownership and dependency direction.\*\*

2\. \*\*Do not create new apps.\*\*

3\. \*\*Keep business logic in services/\*\*, not DocType controllers.

4\. \*\*Keep APIs explicit and minimal.\*\*

5\. \*\*Do not invent hidden workflow states.\*\*

6\. \*\*Do not mix unrelated phases.\*\*

7\. \*\*Do not implement future phases.\*\*

8\. \*\*Stop exactly at the requested phase boundary.\*\*

9\. \*\*Use workspace-first UX\*\*, not raw DocType-first UX.

10\. \*\*If changing architecture-sensitive code\*\*, summarize impacted apps/files before editing.



\---



\## Required Output Before Coding

\* \*\*Summary\*\*: Brief overview of the task.

\* \*\*Impacted Apps\*\*: List of Frappe apps affected.

\* \*\*Impacted Files\*\*: Specific paths to files being modified.

\* \*\*Scope Boundaries\*\*: What is explicitly inside and outside this task.

\* \*\*Tests to Run\*\*: Which existing or new tests will validate the change.



\## Required Output After Coding

\* \*\*Files Changed\*\*: Final list of modified files.

\* \*\*What Changed\*\*: Summary of the logic implemented.

\* \*What Was Intentionally Not Changed\*\*: Constraints or future-phase items skipped.

\* \*\*Manual Checks\*\*: Specific UI or flow steps to verify.

\* \*\*Smoke Tests to Run\*\*: Quick validation commands or scripts.





\## Framework generator rules



For Frappe-managed artifacts:

\- Apps must be created with `bench new-app`

\- Sites must be created with `bench new-site`

\- DocType scaffolds must be generated through Frappe’s standard creation flow

\- Do not handwrite framework scaffolds from scratch



If command execution is slow or unavailable:

\- output the exact WSL command

\- stop after proposing the command

\- do not simulate the scaffold by creating files manually

