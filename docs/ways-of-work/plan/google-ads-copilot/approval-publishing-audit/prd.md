# 1. Feature Name

Approval, Publishing, and Audit

## 2. Epic

- Parent epic: [Google Ads Copilot for Business Owners](../epic.md)

## 3. Goal

### Problem

Drafts do not create business value unless they can be safely reviewed and published. The product promise depends on human approval before any campaign goes live, and without auditability the user cannot trust the system.

### Solution

Provide a review and approval workflow that lets the user inspect a campaign draft, approve or reject it, publish only approved changes to Google Ads, and track all actions through a clear audit trail.

### Impact

This feature turns the platform into a trustworthy operator instead of a recommendation-only tool. It also creates the control layer required for future optimization automation with approval gates.

## 4. User Personas

- Business owner who wants complete control over what gets published.
- Business owner who wants proof of what changed and when.

## 5. User Stories

- As a business owner, I want to review a draft before it goes live so that I stay in control.
- As a business owner, I want to approve or reject publication so that nothing is published without my permission.
- As a business owner, I want a history of approvals and publications so that I can audit past actions.

## 6. Requirements

### Functional Requirements

- The product must present a review screen for campaign drafts.
- The product must let the user approve, reject, or send a draft back for adjustment.
- The product must publish only after explicit approval.
- The product must write publication results back to the workspace status.
- The product must record all approval and publishing events in an audit trail.
- The product must surface publishing errors and partial failures clearly.
- The product must respect configured guardrails such as budget caps and restricted geographies.

### Non-Functional Requirements

- Audit records must be immutable enough for operational trust.
- Publishing failures must be recoverable and traceable.
- Logs must exclude sensitive credential material.
- The approval flow must remain simple enough for a non-technical business owner.

## 7. Acceptance Criteria

- A saved draft can be opened in a review flow.
- A user can explicitly approve or reject the draft.
- Publication to Google Ads only happens after approval.
- The system records who approved, what changed, and when publication happened.
- If publication fails, the user sees the failure state and a human-readable explanation.
- The workspace shows whether a campaign is draft, approved, published, or failed.

## 8. Out of Scope

- Bulk approval of multiple campaigns in MVP.
- Advanced multi-step approval chains.
- Agency-level compliance workflows.
- Automatic rollback beyond explicit retry or manual correction.
