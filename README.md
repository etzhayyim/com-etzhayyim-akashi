# akashi (証) — Public Ad-Disclosure Transparency Actor

**DID**: `did:web:akashi.etzhayyim.com`
**Namespace**: `com.etzhayyim.akashi.*`
**ADR**: ADR-2606022300 (R0 scaffold)
**Status**: R0 design scaffold (2026-06-02)

akashi is a kotoba-native actor for ingesting already-public advertising
transparency disclosures from platform ad libraries into a source-cited EAVT
graph.

It is the advertising-disclosure sibling of `danjo`: passive public records in,
non-adjudicating transparency records out.

## Scope

akashi stores public ad disclosure evidence as kotoba datoms:

- platform source policy snapshots
- advertiser identities as disclosed by source platforms
- creative text/media hashes
- delivery period, region, spend range and impression range where disclosed
- disclosed targeting summaries
- landing URL/domain/redirect/content hash evidence
- cross-platform factual links by source ID, advertiser, landing domain or
  creative hash

## Malak Boundary

akashi is not part of `malak`. malak is confidential CTI and agency-referral
infrastructure. akashi is public transparency infrastructure.

The only allowed bridge is `malakEvidenceCandidate`: a reviewed, source-cited,
non-adjudicating evidence package when a public ad disclosure intersects already
known phishing, malware, brand-abuse or fraud indicators.

## R0 Cells

These cells are present as gated scaffolds under
`kotoba-lang/kotodama-cells/akashi_*`. Each one raises at import until
ADR-2606022300 R1 activation and source-policy review gates are attested.

| Cell | Phase | Output |
|---|---|---|
| `akashi_source_registry` | periodic | `sourcePolicySnapshot` |
| `akashi_disclosure_fetch` | periodic | `adDisclosureSnapshot` |
| `akashi_normalize_creative` | continuous | advertiser / creative / delivery datoms |
| `akashi_landing_evidence` | rate-limited | `landingEvidence` |
| `akashi_cross_platform_link` | continuous | `adDisclosureLink` |
| `akashi_transparency_report` | periodic | `adTransparencyReport` |
| `akashi_malak_evidence_bridge` | event-gated | `malakEvidenceCandidate` |

## Migration Boundary

`kotoba-lang/kotodama-cells/akashi_*` is legacy source
during migration. New akashi cell orchestration belongs in
`src/akashi/murakumo.cljc` as pure `.cljc` actor plans. The plans preserve the
R0 gate behavior by emitting no write effects until Council/source-policy/R1
attestations are supplied. Host placement remains in `kotoba-lang/murakumo`;
AT Protocol/PDS surfaces remain in `gftdcojp/app-aozora`.

## R0 Coverage

R0 coverage is schema and planning coverage only. There are no live adapters,
fixtures, or collection jobs yet. See:

- `COVERAGE.md` — source / field coverage matrix
- `MATURITY.md` — maturity scorecard and R1 work list
- `registry/source-catalog.seed.json` — planning seed for Meta, X, LINE,
  Google/YouTube, TikTok, and regulator repositories
- `registry/source-policy-reviews.seed.json` — data-driven review state; all
  live collection remains disabled in R0
- `registry/source-policy-approval.schema.json` — future approval transaction
  shape with rollback-to-disabled requirement
- `adapters/regulator_bulk_fixture_parser.py` and `fixtures/regulator_bulk/`
  — local fixture parser only; no live collection
- `fixtures/closure/` — non-adjudicating link/report/malak-candidate closure
  fixtures
- `adapters/dry_run_fixtures.py` — local fixture dry-run CLI; no network access
  and no writes
- `fixtures/dry_run/summary.golden.json` — dry-run summary regression fixture
- `/00-contracts/lexicons/com/etzhayyim/akashi/` — 10 lexicon skeletons

## Immutable Gates

- passive public-source only
- source provenance mandatory
- non-adjudicating
- no political profiling
- no target lists
- open method notes
- ToS / robots / API policy snapshot required
- no ad SDK or tracking pixels
- no commercial ad-intel product
- no private-person inference
- Murakumo-only inference
- transparent publication only
- malak bridge requires review

## Related

- `/90-docs/adr/2606022300-akashi-public-ad-disclosure-kotoba-actor-r0.md`
- `/20-actors/danjo/README.md`
- `/60-apps/etzhayyim-project-malak/CLAUDE.md`
