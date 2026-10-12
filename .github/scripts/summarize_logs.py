import os
import re
import sys

LOG_DIR = "testing_tools/logs"

with open(f"{LOG_DIR}/general.log") as f:
    text = f.read()
    lines = text.splitlines()

try:
    with open(f"{LOG_DIR}/summary.log") as f:
        summary_text = f.read() or "summary.log is empty"
except FileNotFoundError:
    summary_text = "summary.log not found"

with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
    f.write("## Test run summary\n\n```\n" + summary_text + "\n```\n")

id_line_re = re.compile(r"^\[\d\d:\d\d:\d\d\]\s+(\S+)$")
test_config_re = re.compile(r"^\[\d\d:\d\d:\d\d\]\s+test config:\s+(found|NOT FOUND)$")
pcap_re = re.compile(r"^\[\d\d:\d\d:\d\d\]\s+pcap:\s+(found|NOT FOUND)")
outcome_re = re.compile(
    r"^\[\d\d:\d\d:\d\d\]\s+(\S+)\s+-\s+"
    r"(finished|aborted|missing_lab_config|missing_test_config|missing_pcap)(?:\(([^)]*)\))?"
)

runnable = {}
outcome = (
    {}
)  # test_id -> "PASSED" | "FAILED" | "ABORTED" | "MISSING_LAB_CONFIG" | "MISSING_TEST_CONFIG" | "MISSING_PCAP" | ...
current_id = None
has_test_config = False

for line in lines:
    m = id_line_re.match(line)
    if m:
        current_id = m.group(1)
        has_test_config = False
        continue
    tc = test_config_re.match(line)
    if tc and current_id:
        has_test_config = tc.group(1) == "found"
        continue
    pc = pcap_re.match(line)
    if pc and current_id:
        runnable[current_id] = has_test_config and pc.group(1) == "found"
        continue
    om = outcome_re.match(line)
    if om:
        test_id, status, paren = om.groups()
        if status == "finished":
            outcome[test_id] = paren or "UNKNOWN"
        elif status == "aborted":
            outcome[test_id] = "ABORTED"
        elif status == "missing_pcap":
            outcome[test_id] = "MISSING_PCAP"
        elif status == "missing_lab_config":
            outcome[test_id] = "MISSING_LAB_CONFIG"
        else:
            outcome[test_id] = "MISSING_TEST_CONFIG"

should_have_run = [t for t, ok in runnable.items() if ok]
not_passed = [t for t in should_have_run if outcome.get(t) != "PASSED"]

gate_failed = bool(not_passed)
if not_passed:
    for test_id in not_passed:
        print(
            f"::error title={test_id}::has test_config + pcap but did not pass "
            f"(status: {outcome.get(test_id, 'no outcome logged')})"
        )
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(
            "\n**Gate FAILED** — "
            f"{len(not_passed)}/{len(should_have_run)} test(s) with test_config + pcap "
            f"did not pass: {', '.join(not_passed)}\n"
        )
else:
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(
            f"\n**Gate passed** — all {len(should_have_run)} test(s) with test_config + pcap passed.\n"
        )

# Annotate genuine code-level crashes (traceback_errors.log) so they're
# visible individually even though they're already covered by the gate above.
try:
    with open(f"{LOG_DIR}/traceback_errors.log") as f:
        tb = f.read()
    crash_tests = re.findall(r"^\[\d\d:\d\d:\d\d\] (\S+)$", tb, re.MULTILINE)
    for test_id in crash_tests:
        print(
            f"::error title={test_id}::genuine code exception, see traceback_errors.log artifact"
        )
except FileNotFoundError:
    pass

if gate_failed:
    sys.exit(1)
