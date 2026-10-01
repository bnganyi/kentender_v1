# AWD-CHG-001 v0.4 — artboard inventory

Extracted by script from the inline `BOARDS` array of `../design/Award Artboards.dc.html` (tracker AWD4-001). 47 boards: 9 main, 27 variants, 11 dialogs. Every board sits in exactly one slice (plan Phases 3–9). Journey codes: D Done, C Current, B Blocked, N Not started, one letter per stage (Opinion, Decision, Notices, Acceptance and wait, Send to Contracting).

The board literals (TND-MOH-2027-033/036/037, AWD-MOH-2027-033, instants) are fixture data (plan C2). The canonical tender is TND-MOH-2027-002; the synthetic fixtures reproduce 033, 036 and 037 for the fidelity capture.

| # | Board | Name | Group | Actor / context | Journey | Viewport | Spec | Slice |
|---|---|---|---|---|---|---|---|---|
| 1 | D01 | Workspace | Main boards | Charles Mutiso, Head of Procurement · 17 Jun 2027, 08:55 EAT | — | Desktop | §10.2 D01 | 3 Opinion |
| 2 | D01e | Workspace — empty | Main boards | Charles Mutiso · empty variant | — | Desktop | §10.2 D01 empty variant | 3 Opinion |
| 3 | D02 | Opinion | Main boards | Charles Mutiso · 17 Jun 2027, 09:00 EAT | CNNNN | Desktop | §10.2 D02 | 3 Opinion |
| 4 | D03 | Decision | Main boards | Amina Hassan, Accounting Officer · 17 Jun 2027, 10:00 EAT | DCNNN | Desktop | §10.2 D03 | 4 Decision |
| 5 | D04 | Supplier notice | Main boards | Mary Wanjiku, Authorised Signatory · 17 Jun 2027, 10:10 EAT | — | Desktop and 390 px (supplier) | §10.2 D04 | 6 Supplier |
| 6 | D05 | Wait | Main boards | Charles Mutiso · 18 Jun 2027, 09:05 EAT | DDDCN | Desktop | §10.2 D05 | 7 Wait and deliver |
| 7 | D06 | Delivered | Main boards | Charles Mutiso · 2 Jul 2027, 09:00 EAT | DDDDD | Desktop | §10.2 D06 | 7 Wait and deliver |
| 8 | D07 | Explanation | Main boards | Charles Mutiso · isolated branch · 18 Jun 2027, 10:00 EAT | DDDCN | Desktop | §10.2 D07 | 8 Debrief and holds |
| 9 | D07c | Explanation — closed | Main boards | Charles Mutiso · closed variant | DDDCN | Desktop | §10.2 D07 closed variant | 8 Debrief and holds |
| 10 | V01 | Returned | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | CNNNN | Desktop | §10.3 V01 | 3 Opinion |
| 11 | V02 | Source problem | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | BNNNN | Desktop | §10.3 V02 | 3 Opinion |
| 12 | V03 | Expired report | Variants | Charles Mutiso · 11 Oct 2027, 09:00 EAT | CNNNN | Desktop | §10.3 V03 | 3 Opinion |
| 13 | V04 | No award | Variants | Charles Mutiso · 11 Oct 2027, 09:00 EAT | DDNNN | Desktop | §10.3 V04 | 4 Decision |
| 14 | V05 | Delivery failure | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | DDBNN | Desktop | §10.3 V05 | 5 Notices |
| 15 | V06 | Supplier declined | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | DDDBN | Desktop | §10.3 V06 | 7 Wait and deliver |
| 16 | V07 | No response | Variants | Charles Mutiso · 24 Jun 2027, 17:01 EAT | DDDBN | Desktop | §10.3 V07 | 7 Wait and deliver |
| 17 | V08 | Review hold | Variants | Charles Mutiso · 20 Jun 2027, 11:00 EAT | DDDBN | Desktop | §10.3 V08 | 8 Debrief and holds |
| 18 | V09 | Post-decision correction | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | DDDBN | Desktop | §10.3 V09 | 9 Corrections |
| 19 | V10 | Receiver failure | Variants | Charles Mutiso · 2 Jul 2027, 09:01 EAT | DDDDB | Desktop | §10.3 V10 | 7 Wait and deliver |
| 20 | V11 | Cancelled | Variants | Charles Mutiso · 17 Jun 2027, 09:30 EAT | DBNNN | Desktop | §10.3 V11 | 8 Debrief and holds |
| 21 | V12 | Signing unavailable | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | BNNNN | Desktop | §10.3 V12 | 3 Opinion |
| 22 | V13 | Supplier representative | Variants | David Ouma, Supplier Representative · 17 Jun 2027, 10:10 EAT | — | Desktop and 390 px (supplier) | §10.3 V13 | 6 Supplier |
| 23 | V14 | Unsuccessful bidder | Variants | Mary Wanjiku · isolated two-bid fixture | — | Desktop and 390 px (supplier) | §10.3 V14 | 6 Supplier |
| 24 | V15 | Rules unavailable | Variants | Charles Mutiso · 18 Jun 2027, 10:00 EAT | BNNNN | Desktop | §10.3 V15 | 5 Notices |
| 25 | V15s | Status service unavailable | Variants | Charles Mutiso · status-service alternative | BNNNN | Desktop | §10.3 V15 status-service alternative | 5 Notices |
| 26 | V16 | Technical incident | Variants | Daniel Otieno, Technical operator · technical work view | — | Desktop | §10.3 V16 | 5 Notices |
| 27 | V17 | Correction decision | Variants | Amina Hassan · 18 Jun 2027, 10:00 EAT | DDDBN | Desktop | §10.3 V17 | 9 Corrections |
| 28 | V18 | No single recommendation | Variants | Charles Mutiso · tender 036 fixture | CNNNN | Desktop | §10.3 V18 | 3 Opinion |
| 29 | V19 | Correction authorised | Variants | Charles Mutiso · 18 Jun 2027, 10:05 EAT | BNNNN | Desktop | §10.3 V19 | 9 Corrections |
| 30 | V20 | Corrected report received | Variants | Charles Mutiso · 19 Jun 2027, 09:05 EAT | CNNNN | Desktop | §10.3 V20 | 9 Corrections |
| 31 | V21 | Correction after No award | Variants | Charles Mutiso · 11 Oct 2027, 10:00 EAT | DDNNN | Desktop | §10.3 V21 | 9 Corrections |
| 32 | V22 | Late response | Variants | Mary Wanjiku · isolated branch | — | Desktop and 390 px (supplier) | §10.3 V22 | 6 Supplier |
| 33 | V23 | Corrected opinion decision | Variants | Amina Hassan · 19 Jun 2027, 09:15 EAT | DCNNN | Desktop | §10.3 V23 | 9 Corrections |
| 34 | V23p | Corrected opinion — positive | Variants | Amina Hassan · separate synthetic branch · 19 Jun 2027, 09:15 EAT | DCNNN | Desktop | §10.3 V23 positive alternative | 9 Corrections |
| 35 | V24 | Revised notices held | Variants | Charles Mutiso · isolated branch · 19 Jun 2027, 10:00 EAT | DDBNN | Desktop | §10.3 V24 | 9 Corrections |
| 36 | V25 | Revised notices ready | Variants | Amina Hassan · isolated branch · 19 Jun 2027, 10:00 EAT | DDCNN | Desktop | §10.3 V25 | 9 Corrections |
| 37 | X01 | Accept award | Dialogs | From D04 · Mary Wanjiku | — | Desktop and 390 px (supplier) | §10.3 dialog text | 6 Supplier |
| 38 | X02 | Decline award | Dialogs | From D04 · Mary Wanjiku | — | Desktop and 390 px (supplier) | §10.3 dialog text | 6 Supplier |
| 39 | X03 | Record restriction | Dialogs | From Outstanding issues · Charles Mutiso | — | Desktop | §10.3 dialog text | 8 Debrief and holds |
| 40 | X04 | Record outcome — order | Dialogs | From V08 · Charles Mutiso | — | Desktop | §10.3 dialog text | 8 Debrief and holds |
| 41 | X05 | Record outcome — reported challenge | Dialogs | Reported-challenge variant · Charles Mutiso | — | Desktop | §10.3 dialog text | 8 Debrief and holds |
| 42 | X06 | Review correction | Dialogs | From V09 and V21 · Charles Mutiso | — | Desktop | §10.3 dialog text | 9 Corrections |
| 43 | X07 | Return report | Dialogs | From D02 · Charles Mutiso | — | Desktop | §10.3 dialog text | 3 Opinion |
| 44 | X08 | Return for correction | Dialogs | From D03 · Amina Hassan | — | Desktop | §10.3 dialog text | 4 Decision |
| 45 | X09 | Record no award | Dialogs | From D03 · Amina Hassan | — | Desktop | §10.3 dialog text | 4 Decision |
| 46 | X10 | Record next action | Dialogs | From V06 and V07 · Charles Mutiso | — | Desktop | §10.3 dialog text | 7 Wait and deliver |
| 47 | X11 | Request explanation | Dialogs | From D04 · supplier user | — | Desktop and 390 px (supplier) | §10.3 dialog text | 6 Supplier |
