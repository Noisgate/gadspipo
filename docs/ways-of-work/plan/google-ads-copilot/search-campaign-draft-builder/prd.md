# 1. Feature Name

Search Campaign Draft Builder

## 2. Epic

- Parent epic: [Google Ads Copilot for Business Owners](../epic.md)

## 3. Goal

### Problem

Even with a good brief, business owners still need a campaign structure that is coherent, reviewable, and aligned with the selected objective. Without a draft builder, the product cannot convert context into action.

### Solution

Generate a Google Ads Search campaign draft from the approved campaign brief and the objective selected by the user. The draft should include the initial structure needed for review, plus clear explanations for why the AI made each recommendation.

### Impact

This feature produces the first tangible output users care about: a campaign they can inspect and approve. It is the core bridge between strategy extraction and real ad execution.

## 4. User Personas

- Business owner who wants campaigns generated from existing business materials.
- Business owner who needs understandable recommendations, not black-box output.

## 5. User Stories

- As a business owner, I want to choose a campaign goal so that the draft is aligned with the result I care about.
- As a business owner, I want the system to generate a Search campaign draft so that I do not have to build everything manually.
- As a business owner, I want explanations for the generated draft so that I can approve it confidently.

## 6. Requirements

### Functional Requirements

- The product must let the user select a primary campaign objective.
- The product must generate Search campaign drafts only in MVP.
- The draft must include at least campaign name, objective, ad groups, keywords, negative keywords, ads, and extensions.
- The product must map draft components back to the approved campaign brief.
- The product must provide rationale for each major recommendation.
- The product must support saving drafts before publication.
- The product must allow regenerating a draft when inputs or objective change.

### Non-Functional Requirements

- The draft generation output must be auditable and reproducible enough for debugging.
- The system must avoid producing unsupported campaign types in MVP.
- The generated content must respect policy and brand restrictions when those are present in the brief.
- The feature must remain PT-BR first, while keeping future localization possible.

## 7. Acceptance Criteria

- A user can choose an objective such as leads, sales, appointments, or another supported KPI.
- The system generates a complete Search campaign draft from an approved brief.
- The draft includes explanations for campaign structure and recommendations.
- The user can save the draft without publishing it.
- If the source brief lacks required information, the system refuses generation and points to the missing items.

## 8. Out of Scope

- Performance Max, Display, Video, Shopping, or Demand Gen drafts in MVP.
- Fully autonomous publication.
- Creative image generation.
- Advanced bid strategy optimization beyond MVP defaults.
