# akashi adapters

R1 adapter work starts with fixture-only parsers. No file in this directory may
perform live network collection unless a `sourcePolicySnapshot` has
`collectionStatus=allowed` and ADR-2606022300 R1 activation is attested.

Current parser:

- `regulator_bulk_fixture_parser.py` maps a local regulator-style bulk fixture
  into akashi lexicon-shaped records.
- `lexicon_shape_validator.py` validates fixture parser output against the
  akashi lexicon subset used by these records.
- `dry_run_fixtures.py` parses and validates local fixtures, then prints counts
  or records. It has no network mode.
