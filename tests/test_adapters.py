#!/usr/bin/env python3
"""akashi — adapter tests (lexicon validator + regulator fixture parser +
dry-run pipeline). Pure stdlib; the actor had real parsing/validation code
with zero tests (coverage/maturity loop iteration 2).

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
"""
import copy
import pathlib
import sys

import pytest

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "adapters"))

from lexicon_shape_validator import validate_record, validate_records  # noqa: E402
from regulator_bulk_fixture_parser import (  # noqa: E402
    PARSER_VERSION,
    parse_regulator_bulk_fixture,
)

# ── lexicon_shape_validator ──────────────────────────────────────────────────

LEX = {
    "id": "com.etzhayyim.akashi.test",
    "defs": {
        "main": {
            "record": {
                "required": ["name", "kind"],
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 8},
                    "kind": {"type": "string", "knownValues": ["a", "b"]},
                    "count": {"type": "integer", "minimum": 0, "maximum": 10},
                    "flag": {"type": "boolean"},
                    "tags": {
                        "type": "array",
                        "minLength": 1,
                        "items": {"type": "string"},
                    },
                    "ref": {"type": "ref", "ref": "#sub"},
                },
            }
        },
        "sub": {
            "required": ["x"],
            "properties": {"x": {"type": "integer"}},
        },
    },
}

GOOD = {"name": "ok", "kind": "a", "count": 3, "flag": True,
        "tags": ["t"], "ref": {"x": 1}}


def test_validator_accepts_a_fully_populated_record():
    validate_record(GOOD, LEX)  # must not raise
    validate_records([GOOD, GOOD], LEX)


@pytest.mark.parametrize("mutate, match", [
    (lambda r: r.pop("name"), "missing required field name"),
    (lambda r: r.__setitem__("bogus", 1), "unknown field bogus"),
    (lambda r: r.__setitem__("kind", "z"), "unknown value 'z'"),
    (lambda r: r.__setitem__("name", "x"), "shorter than minLength"),
    (lambda r: r.__setitem__("name", "toolongname"), "longer than maxLength"),
    (lambda r: r.__setitem__("count", -1), "below minimum"),
    (lambda r: r.__setitem__("count", 11), "above maximum"),
    (lambda r: r.__setitem__("count", True), "expected integer"),
    (lambda r: r.__setitem__("flag", "yes"), "expected boolean"),
    (lambda r: r.__setitem__("tags", []), "shorter than minLength"),
    (lambda r: r.__setitem__("tags", [1]), "expected string"),
    (lambda r: r.__setitem__("ref", {"x": 1, "y": 2}), "unknown object field y"),
    (lambda r: r.__setitem__("ref", {}), "missing required object field x"),
    (lambda r: r.__setitem__("ref", "not-an-object"), "expected object"),
])
def test_validator_rejects_each_violation(mutate, match):
    record = copy.deepcopy(GOOD)
    mutate(record)
    with pytest.raises(ValueError, match=match):
        validate_record(record, LEX)


def test_validator_const_and_unsupported_type():
    lex = {"id": "t", "defs": {"main": {"record": {
        "required": [], "properties": {"v": {"type": "string", "const": "fixed"}}}}}}
    validate_record({"v": "fixed"}, lex)
    with pytest.raises(ValueError, match="expected const"):
        validate_record({"v": "other"}, lex)
    bad = {"id": "t", "defs": {"main": {"record": {
        "required": [], "properties": {"v": {"type": "cid-link"}}}}}}
    with pytest.raises(ValueError, match="unsupported schema type"):
        validate_record({"v": 1}, bad)


# ── regulator_bulk_fixture_parser ────────────────────────────────────────────

PAYLOAD = {
    "source": {
        "platform": "test-regulator",
        "sourceUrl": "https://regulator.example/bulk",
        "jurisdiction": "JP",
    },
    "capturedAt": "2026-06-11T00:00:00Z",
    "records": [
        {
            "sourceRecordId": "rec-1",
            "sourceUrl": "https://regulator.example/rec-1",
            "advertiser": {
                "displayName": "Example Corp",
                "platformAdvertiserId": "adv-9",
                "websiteDomain": "example.com",
                "verifiedStatus": "verified",
            },
            "landingUrl": "https://Landing.Example.com/page?q=1",
            "creativeText": "creative body",
            "language": "ja",
            "status": "active",
            "spendRange": {"lower": 100, "upper": 200, "currency": "JPY"},
        },
        {
            "sourceRecordId": "rec-2",
            "sourceUrl": "https://regulator.example/rec-2",
            "advertiser": {"displayName": "Minimal Inc"},
            "landingUrl": "https://min.example/",
            "creativeText": "minimal",
        },
    ],
}

KW = dict(
    attesting_did="did:web:akashi.etzhayyim.com",
    source_policy_cid="cid:akashi:source-policy:test",
    method_note_cid="cid:akashi:method-note:test",
)


def test_parser_maps_every_record_family():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert out["methodNote"]["version"] == PARSER_VERSION
    for family in ("adDisclosureSnapshot", "advertiserIdentity",
                   "landingEvidence", "creativeDisclosure", "deliveryDisclosure"):
        assert len(out[family]) == 2, family
    # provenance honesty markers survive the mapping
    assert all(s["sourceLimited"] for s in out["adDisclosureSnapshot"])
    assert all(a["nonInferred"] for a in out["advertiserIdentity"])


def test_parser_is_deterministic_and_content_addressed():
    a = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    b = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert a == b
    s = a["adDisclosureSnapshot"][0]
    assert s["payloadCid"].startswith("cid:akashi:payload:")
    assert len(s["payloadSha256"]) == 64
    # changing the source record must change its content address
    mutated = copy.deepcopy(PAYLOAD)
    mutated["records"][0]["creativeText"] = "different"
    c = parse_regulator_bulk_fixture(mutated, **KW)
    assert c["adDisclosureSnapshot"][0]["payloadCid"] != s["payloadCid"]


def test_parser_source_limited_gaps_are_preserved_not_invented():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    minimal = out["advertiserIdentity"][1]
    # undisclosed fields are ABSENT (None-stripped), never fabricated
    assert "platformAdvertiserId" not in minimal
    assert "websiteDomain" not in minimal
    assert minimal["verifiedStatus"] == "not-disclosed"
    delivery_min = out["deliveryDisclosure"][1]
    assert delivery_min["status"] == "unknown"
    assert "spendRange" not in delivery_min


def test_parser_normalizes_domain_and_range_aliases():
    out = parse_regulator_bulk_fixture(copy.deepcopy(PAYLOAD), **KW)
    assert out["landingEvidence"][0]["domain"] == "landing.example.com"
    spend = out["deliveryDisclosure"][0]["spendRange"]
    # lower/upper aliases map onto min/max
    assert spend["min"] == 100 and spend["max"] == 200
    assert spend["currency"] == "JPY"


# ── dry-run pipeline (fixtures → parse → lexicon-validate, end-to-end) ──────

def test_dry_run_fixtures_validate_against_real_lexicons():
    sys.path.insert(0, str(ACTOR_DIR / "adapters"))
    from dry_run_fixtures import load_dry_run_records  # noqa: E402
    output = load_dry_run_records()
    assert output, "dry-run pipeline returned no record families"
    total = sum(len(v) if isinstance(v, list) else 1 for v in output.values())
    assert total >= 5, f"expected a non-trivial fixture set, got {total} records"
