#!/usr/bin/env python3
"""Fail-fast connectivity validator.

The LLM-backed features (``kb.py add --topic/--stem``) are
useless without a reachable API, and a half-written question bank is worse than
no run at all — so they probe first and abort on failure. The exam app needs no
network and doesn't call this.

Exit codes
----------
0  reachable
1  no connectivity

Usage
-----
    python scripts/check_network.py            # probe, print, exit
    python scripts/check_network.py --quiet    # exit code only
"""

from __future__ import annotations

import argparse
import socket
import sys
from typing import List, Tuple

ABORT_MESSAGE = (
    "[ERROR] Internet connection required for LLM/Claude Code features. Aborting."
)

#: Probed in order; the first success wins. TCP-only — no payload, no auth, and
#: no dependency on ``requests`` being installed yet.
PROBE_HOSTS: List[Tuple[str, int]] = [
    ("api.anthropic.com", 443),
    ("cloud.google.com", 443),
    ("1.1.1.1", 443),
]

DEFAULT_TIMEOUT = 4.0


def is_online(timeout: float = DEFAULT_TIMEOUT, hosts: List[Tuple[str, int]] | None = None) -> bool:
    """True if any probe host completes a TCP handshake within ``timeout``."""
    for host, port in hosts or PROBE_HOSTS:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def require_network(timeout: float = DEFAULT_TIMEOUT, quiet: bool = False) -> None:
    """Abort the process with status 1 unless the network is reachable.

    Call this at the top of anything that will talk to an LLM.
    """
    if is_online(timeout=timeout):
        return
    if not quiet:
        print(ABORT_MESSAGE, file=sys.stderr)
    sys.exit(1)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check connectivity for LLM-backed features.")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help=f"per-host TCP timeout in seconds (default {DEFAULT_TIMEOUT})")
    ap.add_argument("--quiet", action="store_true", help="suppress output; exit code only")
    args = ap.parse_args()

    if is_online(timeout=args.timeout):
        if not args.quiet:
            print("[OK] Network reachable — LLM/Claude Code features available.")
        return 0

    if not args.quiet:
        print(ABORT_MESSAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
