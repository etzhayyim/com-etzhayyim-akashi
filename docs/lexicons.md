# com.etzhayyim.akashi.* — Public Ad-Disclosure Lexicons

**ADR**: ADR-2606022300 (R0 scaffold)
**Owner actor**: akashi (証) — `did:web:akashi.etzhayyim.com`
**Status**: R0 schema skeletons. R1 hardening closes objects with
`additionalProperties:false`, adds adapter-specific validators, and pins
source-policy freshness gates.

## Purpose

These Lexicons are written by akashi cells that mirror already-public platform
ad disclosures into kotoba EAVT. They preserve source-limited facts instead of
pretending all platforms expose the same fields.

## Lexicons

| # | Lexicon | Purpose |
|---|---|---|
| L1 | `sourcePolicySnapshot` | Source access policy, terms/robots/API posture and cadence |
| L2 | `adDisclosureSnapshot` | Raw source payload CID/hash with source record lineage |
| L3 | `advertiserIdentity` | Advertiser/page/account identity as disclosed by the source |
| L4 | `creativeDisclosure` | Text/media/category/lang/landing refs |
| L5 | `deliveryDisclosure` | Active dates, region, spend/impression ranges, targeting summaries |
| L6 | `landingEvidence` | Landing URL/domain/redirect/content-hash evidence |
| L7 | `adDisclosureLink` | Non-adjudicating factual cross-platform link |
| L8 | `methodNote` | Open parser/normalizer/linker method note |
| L9 | `adTransparencyReport` | Aggregate transparency report |
| L10 | `malakEvidenceCandidate` | Reviewed evidence candidate for malak handoff |

## Constitutional Anchors

- `nonAdjudicatingNotice` is `const: true` on links, reports, and malak
  candidates.
- No schema has a field for voter/person profiling or persuasion scoring.
- Source lineage (`sourcePolicyCid`, `sourceSnapshotCid`, payload CID/hash,
  method note) is required at every derived layer.
- Malak handoff is candidate evidence only; accusation/case creation is
  structurally out of scope.
