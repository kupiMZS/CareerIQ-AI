# Phase 3 — ATS Assessment Contract

## Objective

Create a separate, explainable resume assessment based on
observable information and Phase 2 structured intelligence.

## Legacy compatibility

The existing `/analyze` endpoint and its `ats_score` remain
unchanged. The legacy score is a prototype heuristic.

The new report is internal until implementation and integration
have been independently tested.

## Finding states

- `satisfied`: the defined check has observable support.
- `needs_attention`: the check identifies a potential issue.
- `not_assessed`: sufficient assessment input is unavailable.

Each finding contains a code, status, explanation, optional
supporting text, and optional recommendation.

## Scoring

The report score defaults to `None`.

Weighted scoring must not be introduced without documented
criteria, explainability, and synthetic validation.

A score must not be represented as an employer ATS score,
hiring probability, or guaranteed parser compatibility.

## Planned assessment areas

- Contact information completeness
- Recognizable resume sections
- Skills and supporting textual evidence
- Education and experience information
- Observable measurable achievements
- Job-description alignment, when supplied
- Format or parsing risks only when the necessary document
  information is actually available

Missing job descriptions and unavailable document-layout
information must be identified as assessment limitations.

## Safety and compatibility

Do not infer experience, proficiency, or employment claims.

Do not mutate Phase 2 intelligence, legacy analysis responses,
saved Laravel analyses, or frozen evaluation contracts.

Use synthetic resume data for implementation tests.

No Phase 3 API endpoint or scoring implementation is claimed
by this initial contract milestone.
