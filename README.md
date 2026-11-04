# TLDR Vote

Independent, source-linked voter research prototype by Sheridan Technologies. Not affiliated with an election authority, candidate or party. **The 2026 content is an election research snapshot, not a personalized ballot or a completed independent fact-check.** Always confirm official election details with the relevant election office.

Website: https://tldrvote.sheridansystems.tech/

## Current regions

- Clark County, Washington: 45 topic screens, 51 candidate listings, 15 ballot measures.
- Multnomah County, Oregon: 66 topic screens, 155 candidate listings, six local measures; incomplete verification and official report-count questions are disclosed.

Both are being migrated to a shared, versioned research data contract and common presentation. Candidate-submitted material, topic keyword matches, and independent evidence are explicitly separated.

## Developer guide

See [platform/README.md](platform/README.md) for the canonical schema, research workflow, source provenance, election tracking, corrections, QA gates, jurisdiction onboarding, and approved release process.

Quick start:

    python -m pip install -r platform/requirements.txt
    python -m playwright install chromium
    python platform/pipeline.py --preview --test-browser

An authoritative release is blocked until independent source verification and named editorial review are complete. GitHub Actions checks preview integrity, **not substantive political correctness**. A PR passing CI must not automatically publish this election content.

## Corrections

Report an issue using the public [correction form](https://github.com/Sheridan-Tech/tldrvote/issues/new?template=correction.yml) (GitHub account required), or use the private email address listed on the [transparency page](https://tldrvote.sheridansystems.tech/transparency.html). Include the specific item, the exact problem, and a primary source. Do not post private voter records or your voting choices.
