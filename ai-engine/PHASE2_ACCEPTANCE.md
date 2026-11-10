# Phase 2 — Resume Intelligence Acceptance Record

## 1. Scope

Phase 2 establishes a structured and factual representation
of information extracted from candidate resumes.

The `ResumeIntelligence` schema supports:

- Candidate information
- Professional summary
- Skills
- Education
- Work experience
- Projects
- Certifications
- Publications
- Languages
- Achievements
- Career Profile

The AI orchestration and deterministic enrichment pipeline
support structured extraction, normalization, and reconciliation.

Advanced ATS analysis, semantic job matching, skill-gap
analysis, and career roadmaps belong to later phases.

## 2. Evidence infrastructure

The internal `EvidenceRecord` schema supports:

- Field paths
- Extracted values
- Supporting text excerpts
- Evidence provenance
- Optional confidence metadata

Evidence verification distinguishes:

- `excerpt_not_found`
- `claim_not_found`
- `explicitly_unsupported`
- `lexically_supported`

The existing opt-in evidence workflow focuses on skill names.

Skill evidence coverage distinguishes:

- `no_literal_evidence`
- `literal_mention_only`
- `explicit_rejection_only`
- `mixed_mentions`

Review flags identify selected aspirational, requirement,
and contrast-related wording.

These classifications describe textual evidence only.

A literal mention does not establish proficiency, semantic
truth, or the accuracy of a candidate's real-world claims.

Confidence fields are validated when supplied, but no
calibrated probability interpretation is claimed.

## 3. API integration

FastAPI provides:

`POST /analyze/evidence`

Laravel provides:

`POST /api/v1/resumes/{resume}/analysis/evidence`

The Laravel endpoint requires authentication and ownership
of the requested resume.

Evidence reporting is opt-in.

The existing analysis response is kept separate from
the evidence response.

The opt-in workflow must not overwrite previously saved
analysis data.

## 4. Verified results

Verification date: 28 October 2026.

Previously confirmed validation results:

- Ruff formatting: 98 Python files correctly formatted
- Ruff lint: all checks passed
- Focused Phase 2 regression: 294 passed
- Full Python regression: 693 passed
- Laravel regression: 32 passed, 109 assertions
- PHP runtime: 8.3.35
- PHPUnit: 12.5.35
- Warning-free PHPUnit execution confirmed
- Laravel testing database: SQLite in-memory
- Laravel test container networking: disabled

Existing frozen Phase 2 baseline tests passed as part
of the Python regression suite.

No frozen evaluation datasets were modified.

## 5. Verification boundaries

Regression tests verify their covered behaviors.
They do not establish universal extraction accuracy.

The Laravel evidence integration tests use mocked
AI-engine responses.

A live Laravel-to-FastAPI end-to-end test is not claimed.

No new human-labeled extraction accuracy study,
provider benchmark, or confidence calibration study
was performed during this acceptance review.

The current evidence-reporting contract focuses on
skills rather than all structured resume fields.

Evidence metadata does not establish factual truth
outside the provided resume text.

## 6. Phase boundaries

Phase 3 will address serious ATS analysis.

Phase 4 will expand model and provider evaluation.

Later phases will introduce skill ontology, embeddings,
job matching, skill-gap analysis, and career roadmaps.

Phase 2 acceptance applies to the currently defined,
implemented, and regression-tested Resume Intelligence
scope, subject to the limitations documented above.
