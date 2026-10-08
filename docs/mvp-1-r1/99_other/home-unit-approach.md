**The home-unit approach is sound, but the proposed appointment gate and reference handling need adjustment.**

| **Proposal**                                            | **My assessment**                                                                                                                                                                                                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **D1: One Home organisation unit per staff account**    | Accept. Link it to the canonical Organisation Unit register. State explicitly that it describes staff affiliation and grants no authority. Retire kt_primary_department.                                                                                     |
| **D2: Block appointment when the home unit is missing** | Revise. We have not established why missing department information makes a person ineligible. Flag missing staff data for correction, but do not introduce an appointment gate solely to populate a display column. Eligibility checks must remain separate. |
| **D3: Generate appointment references**                 | Accept. Generate them on the server when the appointment succeeds, including secretary appointments and replacements. Preserve existing references as history.                                                                                               |
| **D4: Align units and people in fixtures**              | Accept, subject to checking the intended organisational structure. Use one canonical spelling. Samuel's home unit and expired responsibility assignment should remain separate facts.                                                                        |

Two further corrections matter:

- **Do not constrain production numbering to preserve screenshot strings.** Seed setup should make numbering deterministic where necessary; tests and screenshots should be updated to the agreed numbering behaviour.
- **Snapshot the department on the appointment record.** Derive it from the person's home unit at appointment time. A later staff transfer must not silently rewrite the historical committee roster.

The form should therefore let the AO select **Person** and **Capacity**, show the derived department as text, and generate the reference after appointment. The server must perform the derivation and eligibility checks itself.

**The next step is one coordinated proposed requirements set:** AUTH defines the home-unit field; CFG defines its maintenance; EVL defines derivation, historical snapshots and generated references; the fixture register supplies consistent examples. Review those together, then update seeds, boards, code and tests.

Reconcile this with the existing proposed EVL v0.6 permissions.