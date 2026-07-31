# Procurement Home — source query map

Read-only projection. No Home-persisted totals.

| Home value | Source model / API | Filter / rule | Permission | Deep link |
|---|---|---|---|---|
| PE choices | `pp_scope.get_user_allowed_entities` + Procuring Entity list | User PE + User Permission; break-glass = all | scope | — |
| FY choices | Budget.`fiscal_year` distinct | Budgets in selected PE (when field present) | Budget read | — |
| Action: demand approval | Demand | `Pending HoD Approval` / `Pending Finance Approval` + role queue | DIA roles | `/desk/demand-workbench/{name}` |
| Action: returned demand | Demand | `Draft` + `return_reason` + `requested_by=user` | owner | `/desk/demand-workbench/{name}` |
| Action: plan review / returned | Procurement Package | `In Review` / `Returned for Correction` | PP roles | `/desk/planning-hub` |
| Action: tender prep / publication | TM2 Tender | Returned / Ready for Publication Review / blockers | TM roles | `/desk/tender-management-v2` or publications |
| Pipeline 1 | Demand | Pending HoD \| Pending Finance | scope | `/desk/demand-hub` |
| Pipeline 2 | approved_demand_queue | Approved not fully planned | PP | `/desk/planning-hub` |
| Pipeline 3 | Procurement Package | Approved \| Ready for Release, not released/consumed | PP | `/desk/planning-hub` |
| Pipeline 4 | TM2 Tender | Not Published/Cancelled/Closed/Evaluation* | TM | `/desk/tender-management-v2` |
| Pipeline 5 | TM2 Tender + Timeline | Published + submission_deadline_at > now | TM | `/desk/publications` |
| Pipeline 6 | TM2 Tender | Closed / Opening Ready (pre-Evaluation) | TM | `/desk/tender-management-v2` |
| Deadline: bid submission | TM2 Tender Timeline.`submission_deadline_at` | Explicit only | TM | tender workbench |
| Deadline: clarification | TM2 Tender Timeline.`clarification_deadline_at` | Explicit only | TM | tender workbench |
| Portfolio budget / allocated / available | `get_budget_landing_data` budgets | Approved/Active PE+FY: approved = max(total, line allocated); available = line `amount_available`; allocated = approved − available | Budget | `/desk/budget-hub` |
| Unfunded approved demand | Demand Approved + budget shortfall sum | DIA budget control shortfall where available | Budget+DIA | `/desk/demand-hub` |
| Active / open tenders | TM2 Tender counts | Active = prep+pub+open+closed-awaiting; Open = published + deadline future | TM | `/desk/tender-management-v2` |

Bid confidentiality: payloads never include bidder names, bid counts, or submission contents.
