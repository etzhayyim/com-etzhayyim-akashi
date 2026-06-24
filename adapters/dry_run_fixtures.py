"""Dry-run CLI for akashi fixture parsing.

Reads local fixtures, validates emitted records against akashi lexicons, and
prints a summary or the fixture records. It never performs network access.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lexicon_shape_validator import validate_record, validate_records
from regulator_bulk_fixture_parser import parse_regulator_bulk_fixture

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
LEX = REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "akashi"
REGULATOR_FIXTURE = ROOT / "fixtures" / "regulator_bulk" / "sample.json"
REGULATOR_MISSING_OPTIONAL_FIXTURE = (
    ROOT / "fixtures" / "regulator_bulk" / "missing_optional_fields.json"
)
CLOSURE_FIXTURE = ROOT / "fixtures" / "closure" / "sample.json"

ATTESTING_DID = "did:web:akashi.etzhayyim.com"
SOURCE_POLICY_CID = "cid:akashi:source-policy:dry-run"
METHOD_NOTE_CID = "cid:akashi:method-note:dry-run"


def load_dry_run_records() -> dict[str, Any]:
    """Load, parse, and validate all local akashi fixture records."""
    regulator_payload = _load(REGULATOR_FIXTURE)
    parsed = parse_regulator_bulk_fixture(
        regulator_payload,
        attesting_did=ATTESTING_DID,
        source_policy_cid=SOURCE_POLICY_CID,
        method_note_cid=METHOD_NOTE_CID,
    )
    missing_optional_payload = _load(REGULATOR_MISSING_OPTIONAL_FIXTURE)
    missing_optional = parse_regulator_bulk_fixture(
        missing_optional_payload,
        attesting_did=ATTESTING_DID,
        source_policy_cid=SOURCE_POLICY_CID,
        method_note_cid=METHOD_NOTE_CID,
    )

    closure = _load(CLOSURE_FIXTURE)["records"]
    output = _merge_outputs(parsed, missing_optional, closure)
    _validate_output(output)
    return output


def summarize(records: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic dry-run counts without exposing payload detail."""
    counts = {
        name: len(value) if isinstance(value, list) else 1
        for name, value in sorted(records.items())
    }
    return {
        "actor": "akashi",
        "mode": "fixture-dry-run",
        "networkAccess": False,
        "writes": False,
        "lexiconNamespaces": sorted(counts),
        "recordCounts": counts,
        "totalRecords": sum(counts.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="akashi-dry-run-fixtures",
        description="Parse and validate local akashi fixtures without network access.",
    )
    parser.add_argument(
        "--emit-records",
        action="store_true",
        help="print validated fixture records instead of summary counts",
    )
    args = parser.parse_args(argv)

    records = load_dry_run_records()
    payload = records if args.emit_records else summarize(records)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _merge_outputs(*outputs: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for output in outputs:
        for name, value in output.items():
            if isinstance(value, list):
                merged.setdefault(name, []).extend(value)
            else:
                merged.setdefault(name, value)
    return merged


def _validate_output(output: dict[str, Any]) -> None:
    for name, value in output.items():
        lexicon = _load(LEX / f"{name}.json")
        if isinstance(value, list):
            validate_records(value, lexicon)
        else:
            validate_record(value, lexicon)


if __name__ == "__main__":
    raise SystemExit(main())
