# MVP Feature Breakdown

## Objective

Break the epic into implementable MVP features that can be built in sequence without losing the product's main promise: transform Google Drive campaign materials into Google Ads Search campaigns and optimization recommendations, always with user approval.

## Feature Set

| ID | Feature | Primary Outcome | Priority | Depends On |
|---|---|---|---|---|
| MVP-01 | Workspace Onboarding | User can enter the product, connect accounts, and reach a usable workspace | P0 | None |
| MVP-02 | Drive Context Ingestion | User can select a Drive folder and get a structured campaign brief | P0 | MVP-01 |
| MVP-03 | Search Campaign Draft Builder | User can generate a Google Ads Search campaign draft from the brief | P0 | MVP-02 |
| MVP-04 | Approval, Publishing, and Audit | User can review, approve, publish, and audit changes safely | P0 | MVP-03 |
| MVP-05 | Optimization Recommendations Center | User can receive, approve, and apply ongoing improvements | P1 | MVP-04 |

## Implementation Order

1. Build the workspace shell and integrations first.
2. Add Drive ingestion and campaign readiness validation.
3. Add draft generation for Search campaigns only.
4. Add approval and publishing workflow with audit trail.
5. Add optimization recommendations and approval loop.

## MVP Boundaries

- Target market: Brazil, PT-BR.
- Primary user: business owner.
- Initial campaign type: Google Ads Search only.
- Publishing requires explicit approval.
- Optimization requires explicit approval.
- Multi-country support is deferred to a later phase.
- Other ad platforms are out of scope for MVP.

## Notes

- Feature PRDs are stored in subfolders under this epic directory.
- Technical implementation details remain flexible and should be finalized in the architecture step.
- Auth method, billing, and advanced team permissions remain TBD unless they become blockers for MVP delivery.
