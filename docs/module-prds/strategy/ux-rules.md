\# Strategy Module UX Rules (Non-negotiable)



These rules define how the Strategy module MUST behave.

If any rule is violated, the UX is incorrect.



\---



\## 1. No Long Forms



\- The Strategy module MUST NOT use long scrolling forms

\- Users must never scroll through large sections to complete data

\- Form-based ERP-style UI is NOT allowed



\---



\## 2. Step-Based Builder (Mandatory)



Opening a Strategic Plan MUST show a step-based builder:



Steps:



1\. Plan Info

2\. Programs

3\. Sub-programs

4\. Indicators

5\. Targets

6\. Review



Rules:



\- Only ONE step visible at a time

\- Clear navigation using Next / Back

\- No mixing of steps in a single page



\---



\## 3. Visible Progress Indicator



\- A progress bar (stepper) MUST always be visible

\- It must show:

&#x20; - current step

&#x20; - completed steps

&#x20; - remaining steps



User must always know where they are.



\---



\## 4. Table-Based Interaction



All structured data MUST be handled in tables:



\- Programs → table

\- Sub-programs → table

\- Indicators → table

\- Targets → table



Rules:



\- No inline form clutter

\- No multi-section input forms

\- Data must be easy to scan



\---



\## 5. Modal / Panel Data Entry



Adding or editing records MUST:



\- use modal dialogs or side panels

\- NOT expand inline forms

\- NOT navigate away from the builder



\---



\## 6. Parent-Child Visibility



At all times, the UI must show relationships:



\- Sub-program shows its Program

\- Indicator shows its Sub-program

\- Target shows its Indicator



User must never guess hierarchy.



\---



\## 7. Guided Flow



User must always understand:



\- what to do next

\- what is missing

\- what is required



Rules:



\- no hidden required steps

\- no implicit dependencies

\- no surprise validation at the end



\---



\## 8. Review Step (Mandatory)



The Review step MUST:



\- show counts:

&#x20; - Programs

&#x20; - Sub-programs

&#x20; - Indicators

&#x20; - Targets



\- show validation issues clearly

\- block submission if incomplete



\---



\## 9. Validation Visibility



Validation must be:



\- immediate where possible

\- clear and specific

\- shown near the problem



Rules:



\- no generic errors

\- no silent failures

\- no “something went wrong”



\---



\## 10. Workflow Visibility



Plan status MUST always be visible:



\- Draft

\- Submitted

\- Approved

\- Active

\- Archived



User must not guess current state.



\---



\## 11. Read-Only Behavior After Submission



After submission:



\- all fields become read-only

\- no inline edits allowed

\- no hidden edit paths



Active plan = locked for normal users.



\---



\## 12. Navigation Rules



\- Strategy must be accessible via workspace/menu

\- No dependency on search (CTRL+K)

\- No hidden screens



\---



\## 13. Consistency Rules



\- same interaction pattern across all steps

\- same modal behavior

\- same table structure style

\- predictable navigation



\---



\## 14. Forbidden UX Patterns



The following are NOT allowed:



\- long scrolling forms

\- mixed-step screens

\- hidden required fields

\- inline multi-section forms

\- unclear parent relationships

\- navigation via search only

\- form-first ERP UI patterns



\---



\## 15. Enforcement Rule



If any implementation:



\- introduces long forms

\- breaks step-based builder

\- hides workflow or hierarchy

\- confuses user navigation



→ It must be rejected and corrected.

