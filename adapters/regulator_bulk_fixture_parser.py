"""Fixture-only parser for regulator-style public ad-disclosure bulk exports.

This module intentionally performs no live fetching. It accepts an already
loaded fixture payload and maps source-disclosed fields into akashi record
shapes while preserving source-limited gaps.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlparse

PARSER_VERSION = "regulator-bulk-fixture-r1.0"
SOURCE_CODE_CID = "cid:akashi:regulator-bulk-fixture-parser:r1"


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _cid(prefix: str, value: Any) -> str:
    return f"cid:akashi:{prefix}:{_sha256_json(value)[:32]}"


def _domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def _range(source_range: dict[str, Any] | None) -> dict[str, Any] | None:
    if source_range is None:
        return None
    mapped = {
        "min": source_range.get("min", source_range.get("lower")),
        "max": source_range.get("max", source_range.get("upper")),
        "currency": source_range.get("currency"),
        "sourceLabel": source_range.get("sourceLabel"),
    }
    return {k: v for k, v in mapped.items() if v is not None}


def parse_regulator_bulk_fixture(
    payload: dict[str, Any],
    *,
    attesting_did: str,
    source_policy_cid: str,
    method_note_cid: str,
) -> dict[str, Any]:
    """Map a local fixture payload into akashi lexicon-shaped records."""
    source = payload["source"]
    records = payload["records"]
    captured_at = payload["capturedAt"]

    method_note = {
        "createdAt": captured_at,
        "methodId": "akashi.regulator-bulk-fixture-parser",
        "methodFamily": "snapshot-parser",
        "version": PARSER_VERSION,
        "sourceCodeCid": SOURCE_CODE_CID,
        "limits": [
            "fixture-only parser; does not fetch remote sources",
            "preserves only source-disclosed fields",
            "does not infer private-person or targeting profiles",
        ],
        "falsePositiveNotes": [
            "same advertiser display name can represent unrelated entities",
            "source issue labels are mirrored, not adjudicated",
        ],
        "attestingDid": attesting_did,
    }

    source_policy = {
        "createdAt": captured_at,
        "platform": source["platform"],
        "sourceFamily": "regulator-repository",
        "sourceUrl": source["sourceUrl"],
        "jurisdiction": source["jurisdiction"],
        "accessMode": "public-bulk-export",
        "collectionStatus": "manual-review",
        "methodNoteCid": method_note_cid,
        "attestingDid": attesting_did,
    }

    snapshots: list[dict[str, Any]] = []
    advertisers: list[dict[str, Any]] = []
    landing: list[dict[str, Any]] = []
    creative: list[dict[str, Any]] = []
    delivery: list[dict[str, Any]] = []

    for source_record in records:
        snapshot_payload_cid = _cid("payload", source_record)
        snapshot = {
            "fetchedAt": captured_at,
            "platform": source["platform"],
            "sourcePolicyCid": source_policy_cid,
            "sourceRecordId": source_record["sourceRecordId"],
            "sourceUrl": source_record["sourceUrl"],
            "payloadCid": snapshot_payload_cid,
            "payloadSha256": _sha256_json(source_record),
            "parserVersion": PARSER_VERSION,
            "sourceLimited": True,
            "attestingDid": attesting_did,
        }
        snapshot_cid = _cid("snapshot", snapshot)
        snapshots.append(snapshot)

        advertiser = {
            "createdAt": captured_at,
            "platform": source["platform"],
            "sourceSnapshotCid": snapshot_cid,
            "displayName": source_record["advertiser"]["displayName"],
            "platformAdvertiserId": source_record["advertiser"].get(
                "platformAdvertiserId"
            ),
            "websiteDomain": source_record["advertiser"].get("websiteDomain"),
            "jurisdiction": source_record["advertiser"].get("jurisdiction"),
            "verifiedStatus": source_record["advertiser"].get(
                "verifiedStatus", "not-disclosed"
            ),
            "nonInferred": True,
            "attestingDid": attesting_did,
        }
        advertiser = {k: v for k, v in advertiser.items() if v is not None}
        advertiser_cid = _cid("advertiser", advertiser)
        advertisers.append(advertiser)

        landing_record = {
            "fetchedAt": captured_at,
            "sourceSnapshotCid": snapshot_cid,
            "url": source_record["landingUrl"],
            "domain": _domain(source_record["landingUrl"]),
            "fetchMode": "manual-review-only",
            "methodNoteCid": method_note_cid,
            "attestingDid": attesting_did,
        }
        landing_cid = _cid("landing", landing_record)
        landing.append(landing_record)

        creative_record = {
            "createdAt": captured_at,
            "sourceSnapshotCid": snapshot_cid,
            "advertiserIdentityCid": advertiser_cid,
            "creativeTextCid": _cid("creative-text", source_record["creativeText"]),
            "creativeTextSha256": hashlib.sha256(
                source_record["creativeText"].encode()
            ).hexdigest(),
            "language": source_record.get("language"),
            "disclosedCategory": source_record.get("disclosedCategory"),
            "sourceIssuePoliticalFlag": source_record.get(
                "sourceIssuePoliticalFlag", "not-applicable"
            ),
            "landingEvidenceCid": landing_cid,
            "methodNoteCid": method_note_cid,
            "attestingDid": attesting_did,
        }
        creative_record = {
            k: v for k, v in creative_record.items() if v is not None
        }
        creative_cid = _cid("creative", creative_record)
        creative.append(creative_record)

        delivery_record = {
            "createdAt": captured_at,
            "sourceSnapshotCid": snapshot_cid,
            "creativeDisclosureCid": creative_cid,
            "startedAt": source_record.get("startedAt"),
            "endedAt": source_record.get("endedAt"),
            "status": source_record.get("status", "unknown"),
            "spendRange": _range(source_record.get("spendRange")),
            "impressionRange": _range(source_record.get("impressionRange")),
            "regionSummary": source_record.get("regionSummary"),
            "sourceLimited": True,
            "attestingDid": attesting_did,
        }
        delivery_record = {
            k: v for k, v in delivery_record.items() if v is not None
        }
        delivery.append(delivery_record)

    return {
        "methodNote": method_note,
        "sourcePolicySnapshot": source_policy,
        "adDisclosureSnapshot": snapshots,
        "advertiserIdentity": advertisers,
        "landingEvidence": landing,
        "creativeDisclosure": creative,
        "deliveryDisclosure": delivery,
    }


__all__ = ["PARSER_VERSION", "parse_regulator_bulk_fixture"]
