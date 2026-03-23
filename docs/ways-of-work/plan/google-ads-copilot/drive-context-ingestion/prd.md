# 1. Feature Name

Drive Context Ingestion

## 2. Epic

- Parent epic: [Google Ads Copilot for Business Owners](../epic.md)

## 3. Goal

### Problem

Business owners already have campaign information, but it is scattered across files and folders that are not directly usable by Google Ads. Without normalization, the AI may create weak or misleading campaign drafts.

### Solution

Allow the user to select a Google Drive folder, ingest supported files, classify them into useful campaign inputs, and generate a structured campaign brief plus a readiness score before any draft generation happens.

### Impact

This feature transforms unstructured marketing material into a reliable source of truth for campaign creation. It improves draft quality and prevents the system from operating on incomplete context.

## 4. User Personas

- Business owner who stores campaign materials in Google Drive.
- Business owner who wants the system to understand the business without manual rewriting.

## 5. User Stories

- As a business owner, I want to choose the Drive folder for a campaign so that the system uses the right source materials.
- As a business owner, I want the system to summarize what it understood so that I can confirm the context before creating a campaign.
- As a business owner, I want to know what is missing so that I can improve the folder before publishing anything.

## 6. Requirements

### Functional Requirements

- The product must allow selecting a Google Drive folder after Drive connection is complete.
- The product must read supported source materials from that folder.
- The product must classify content into categories such as briefing, offer, landing page, creatives, brand rules, and restrictions.
- The product must generate a structured campaign brief from the ingested content.
- The product must calculate and display a campaign readiness score.
- The product must surface missing or weak inputs before draft generation.
- The product must allow the user to confirm the brief as the basis for draft generation.

### Non-Functional Requirements

- The ingestion process must handle retryable external API failures.
- The system must avoid exposing full private document contents unnecessarily in the UI.
- The system must record ingestion status and processing errors for debugging.
- The first full ingestion for a normal folder should complete within the MVP performance target.

## 7. Acceptance Criteria

- A connected user can select a Drive folder successfully.
- The system ingests at least the supported file types defined for MVP.
- The system produces a structured brief from ingested files.
- The system displays a readiness score and explicit missing-input warnings.
- The user can review the generated brief before proceeding.
- If critical inputs are missing, the system blocks draft generation and explains why.

## 8. Out of Scope

- OCR-heavy ingestion pipelines for scanned documents in MVP.
- Advanced brand asset management.
- Multi-folder orchestration for one campaign in MVP.
- Automatic correction of low-quality source documents.
