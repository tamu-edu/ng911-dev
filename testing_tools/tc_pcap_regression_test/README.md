# tc_pcap_regression_test

Runs conformance tests from pre-recorded pcap files instead of live packet
capture — a regression pass over test cases whose expected traffic is
already captured, so you don't need a live lab to check that `test_suite`
still assesses them correctly.

## Running

```
(.venv) sudo python -m main test_ag_pcap [--tests BCF_001 BCF_003 ...] [--report_file out.json]
```

No `--tests` runs every test_id known to the RQ schema. `--report_file`
additionally dumps the results as JSON.

## What a test needs to be picked up

Test discovery is driven by `REQUIREMENTS_SCHEMA`.
For each discovered test_id to actually run, `test_suite/pcaps/<test_id>/`
needs:

- a `*lab_config*.yaml` file
- a matching `test_configs/test_config_<test_id lowercased>.yaml`
- at least one `.pcap` file whose name contains a pass marker (`..._pass_...`
  or `..._pass.pcap`) — anything without one is treated as not usable, not
  silently included

pcap files are matched to test_config variations positionally, by the
`var_N_pass_...` numbering in the filename (`var_1_pass_...` → the test
config's first variation, and so on).

Missing lab_config / test_config / pcap each get their own status
(`MISSING_LAB_CONFIG` / `MISSING_TEST_CONFIG` / `MISSING_PCAP`)
## Error categories

An aborted test (`RunStatus.ABORTED`) gets classified into one of four
categories by `record_exception` in `logger.py`, counted in `summary.log`'s
`Errors:` block:

- `pcap_parsing` — tshark/pyshark blew up reading the pcap itself.
  → `pcap_errors.log`
- `config_parsing` — lab_config/test_config is invalid (bad YAML, failed
  schema validation). → `config_errors.log`
- `test_prep` — config is valid, but the run couldn't actually be assembled
  from it: no pcap matched a variation, or a required filtering param
  (e.g. src/dst IP) is missing. → `config_errors.log`
- `test_run` — anything unexpected raised during `TestOracle`'s actual
  assessment. → `traceback_errors.log`

`pcap_parsing`/`config_parsing`/`test_prep` all originate from the same two
exception types (`WrongConfigurationError`, `FileNotFoundError`) — which
bucket they land in depends on the exception message, matched against
`_TEST_PREP_MESSAGE_PATTERNS` / `_CONFIG_PARSING_TRACE_PATTERNS` at the top
of `logger.py`.

## Layout

- `pcap_run_config_manager.py` — loads/validates lab_config, matches pcaps
  to variations, builds the `RunConfig` handed to `TestOracle`
- `test_discovery_service.py` — RQ-schema-based test_id discovery +
  per-test file lookup
- `logger.py` — `PipelineLogWriter`, the five logs above
- `types/test_run_result.py` — `TCPRResult` / `RunStatus`
