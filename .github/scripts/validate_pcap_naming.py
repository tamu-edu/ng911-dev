"""
Validates PCAP filename convention.

Standard:
  TC_<ZONE>_<NUM>_var_<N>_<pass|fail>_<VAR_NAME>.pcap
  e.g. TC_CHFE_001_var_1_pass_HELD_location_dereferencing.pcap

Called by pre-commit with only the changed .pcap files as argv.
"""

from __future__ import annotations

import re
import sys

PCAP_NAME_RE = re.compile(
    r"^TC_(?P<zone>[A-Z0-9]+(?:_[A-Z0-9]+)*)_(?P<num>\d{3})"
    r"_var_(?P<var>\d+)_(?P<status>pass|fail)_(?P<desc>[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*)\.pcap$"
)


def main(argv: list[str]) -> int:
    errors = 0
    for path in argv:
        name = path.rsplit("/", 1)[-1]
        if not PCAP_NAME_RE.match(name):
            print(
                f"[ERROR] {path}: filename doesn't match "
                f"TC_<ZONE>_<NUM>_var_<N>_<pass|fail>_<VAR_NAME>.pcap"
            )
            errors += 1
    if errors:
        print(f"\n{errors} pcap filename violation(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
