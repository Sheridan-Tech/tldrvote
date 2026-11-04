# TLDR Vote — Standardized Platform v1

**Status (2026-11-03): tested staging foundation, NOT a fully verified or authoritative election guide.**

This work separates the Clark County reference layout from election-specific data. Both Clark (45 topics) and Multnomah (66 topics) now normalize to the same versioned JSON schema. A common JavaScript renderer handles both. The Multnomah staging page has the same core sections as Clark, while preserving its original research material under an expandable area.

## Common content contract

**Candidate race:** What this office actually controls; Candidates' stated priorities; Side-by-side comparison of the same main issues for everyone; Where they differ; Original evidence and uncertainties; Correction and missing-source report.

**Ballot measure:** The big picture; What Yes/No would change; Why supporters advocate and critics object (attributed); Who is affected; Money and timelines; Other possible effects; One thing to remember; Remaining unknowns; Original sources and correction reporting.

A keyword detected in a pamphlet is NOT a policy position. A candidate biography is NOT a verified credential. Empty comparable-position cells remain UNKNOWN. No voting recommendations, candidate scoring, or inferred private motivations.

## Repeatable flow

Election authority calendar -> New jurisdiction intake -> Official source snapshot and SHA256 -> Layout-aware extraction -> Candidate/office/measure reconciliation -> Canonical schema -> Source-backed research jobs -> Cross-check and counterevidence -> Human editor review -> Preview QA -> Approved deployment -> Source change monitoring and corrections -> Dated archive.

The system never approves political claims merely because a parser, language model, or page test succeeded.

## Working components

- platform/schema.json: canonical v1 election, jurisdiction, race, measure, candidate, issue row, claim, citation and editorial status contract.
- platform/build_editions.py: deterministic adapters from the current two county datasets. Does not generate inferred positions.
- platform/validate_release.py: validates schema, links, same-issue candidate comparison, source references, claim states and release blockers; an authoritative release fails closed.
- platform/research_jobs.py: produces an explicit pending research queue. This is not live AI research and does not publish drafts.
- platform/standard_sections.js and .css: reusable, source-aware sections for both counties, with source links and disclosed research gaps.
- platform/stage_multnomah_common.py: adds new sections first; keeps the former Multnomah detail view below in expandable original material. Externalizes the common renderer and data.
- platform/test_pipeline.py and test_standardized_ui.py: provenance/schema/failure-unit tests and browser tests across 66 Multnomah topics and 45 Clark normalized topic renders.
- platform/elections.json and election_tracker.py: official-date registry, clear upcoming, voting-open, polls-closed and certification-unverified phases. Never assume certification based only on a deadline.
- platform/watch_sources.py: allowlisted official PDF/HTML source hash monitoring. A source change triggers a review, never automatic publication.
- platform/new_jurisdiction.py: creates a new county/district intake manifest with all review gates unset.
- .github/ISSUE_TEMPLATE/correction.yml: structured public correction report, to be made available through GitHub after merge. Private email remains an alternative.
- .github/workflows/tldrvote-quality.yml: proposed pull-request CI; deployment credentials and public promotion are NOT in this workflow.

## Rebuild and test

From the repository root:

    python -m pip install -r platform/requirements.txt
    python -m playwright install chromium
    python platform/pipeline.py --preview --test-browser
    python platform/election_tracker.py --asof 2026-11-03T21:08:00-08:00
    python platform/watch_sources.py --edition multnomah
    python platform/validate_release.py --authoritative

The last command MUST exit code 2 while editorial review is incomplete. A structural PASS is NOT a completed fact-check. On Windows, tzdata is required for IANA time zone support.

Build output: assets/standard_sections.js and .css, data/clark_2026_canonical.json, data/multnomah_2026_canonical.json, multnomah/index.html, and platform/output/quality_report.json and research_jobs.json.

## New jurisdiction onboarding

Example (replace example URLs with REAL election-office sources before use):

    python platform/new_jurisdiction.py --state OR --county "Example County" --date 2027-05-18 --kind special --authority-url https://official.example.gov/elections --ballot-lookup-url https://official.example.gov/ballot

This creates a blocked intake manifest. It does NOT create election candidates or dates beyond the supplied values, fetch unauthorised websites, or make an unverified county page live. A new adapter must fetch authoritative source snapshots, validate official contest counts and district boundaries, resolve names using more than loose string matching, and produce the same canonical v1 schema.

Prefer official structured election feeds (e.g. Voting Information Project VIP v6) where available; otherwise use a source-specific PDF/HTML parser with page/column provenance. Reference: https://www.votinginfoproject.org/spec

## Source and claim verification

Original ballot records establish candidate spellings, legal ballot choices and jurisdiction. Candidate statements establish what a candidate *said*, not whether the statement is true. Journalistic reports document an attributed report or public event, not every claimed result. An LLM draft is always DRAFT.

For each material assertion: preserve exact words, page/passage, official URL, publication/inspection dates, original source digest, qualifications and exceptions, contradictory evidence, and an independent reviewer. Verify financial years, denominators, forecast assumptions, legal effective dates, bond principal versus repayment, and what happens if another ballot measure fails. Record UNKNOWN where a meaningful question cannot be resolved; never turn missing information into a negative candidate finding.

An independently named human editorial reviewer must sign off consequential claims, especially legal/fiscal interpretations, disputed allegations and campaign comparisons. No automated test can replace substantive editorial review.

## Elections

Election tracker phases are UPCOMING, VOTING_PERIOD, POLLS_CLOSED_CERTIFICATION_NOT_VERIFIED, PAST_CERTIFICATION_DEADLINE_NOT_VERIFIED, and CERTIFIED_ARCHIVE. The last phase requires original official confirmation. Election Day 2026-11-03 is recorded for Clark WA and Multnomah OR; Oregon's final certification schedule is a due date, not evidence of completed certification.

Official calendars:
- https://www.sos.wa.gov/elections/elections-calendar/dates-and-deadlines
- https://multco.us/info/november-3-2026-general-election

## Feedback and correction workflow

A public GitHub Issue Form requests topic URL, exact disputed claim, category, a primary-source link, and optional suggested correction. GitHub sign-in is required. The source-linked page also offers an email alternative for confidential reports. No private voter choices, home addresses or registration details should be collected.

Target editorial process: RECEIVED -> TRIAGE -> SOURCE_RESEARCH -> EDITORIAL_REVIEW -> CORRECTED or DECLINED_WITH_REASON -> DATED_PUBLIC_CHANGELOG -> CLOSED. Do not publish a submitted allegation as truth before verification. Preserve a private audit trail and a rollback version.

**Still missing:** anonymous public form backend, automatic email-to-ticket ingestion, Jira synchronization, staffed response SLA and managed moderation/anti-spam. Jira TLDRVOT-20 tracks these.

## Release risks and status

Current normalized data still has the Clark 55 unanswered policy-position cells and Multnomah 25 unmatched profiles, 2026 E-019 official report count discrepancy, and many unreviewed issue cells. The 21 ballot measures lack comprehensive independent legal/fiscal review. The model is structurally valid but the authoritative release gate is BLOCKED.

Tests support a *source-linked research preview*, not claims of comprehensive independent verification. GitHub changes should go through a reviewed PR and staging preview before any public publication. Never let GitHub Actions automatically publish unreviewed election research.

Jira work: TLDRVOT-5 through 25 already track official data integrity, research, editorial governance, accessibility, intake, deployment, monitoring and architecture. This PR is the first implementation foundation, not closure of those issues.
