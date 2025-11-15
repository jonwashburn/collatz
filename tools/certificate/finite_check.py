from __future__ import annotations

import argparse
import json
from pathlib import Path


def collatz_reaches_one(n: int, max_steps: int = 1_000_000) -> int:
    """Return steps needed for n to reach 1 under the original Collatz map."""
    steps = 0
    value = n
    while value != 1:
        if steps > max_steps:
            raise RuntimeError(f"Exceeded max steps for n={n}")
        if value % 2 == 0:
            value //= 2
        else:
            value = 3 * value + 1
        steps += 1
    return steps


def simulate_range(limit: int) -> tuple[int, int]:
    """Simulate Collatz for all n <= limit, returning (max_steps, argmax)."""
    max_steps = 0
    argmax = 1
    for n in range(1, limit + 1):
        steps = collatz_reaches_one(n)
        if steps > max_steps:
            max_steps = steps
            argmax = n
    return max_steps, argmax


def main() -> None:
    parser = argparse.ArgumentParser(description="Finite verification for n ≤ N0*.")
    parser.add_argument("--summary", type=Path, default=Path("artifacts/summary.json"))
    parser.add_argument("--verified-bound", type=int, default=None)
    parser.add_argument("--log", type=Path, default=Path("artifacts/finite-check.log"))
    args = parser.parse_args()

    if not args.summary.exists():
        raise FileNotFoundError(f"Summary file not found: {args.summary}")
    data = json.loads(args.summary.read_text())
    N0_star = int(data["N0_star"])
    log_lines: list[str] = []

    if args.verified_bound is not None and args.verified_bound >= N0_star:
        log_lines.append(
            f"Verified bound shortcut: known computations cover all n ≤ {args.verified_bound}, "
            f"and N0*={N0_star} lies below this threshold."
        )
        log_lines.append("No additional simulation was required.")
    else:
        log_lines.append(f"Simulating Collatz for all n ≤ {N0_star} ...")
        max_steps, argmax = simulate_range(N0_star)
        log_lines.append(
            f"Simulation complete. Max steps {max_steps} attained at n={argmax}."
        )

    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text("\n".join(log_lines) + "\n")


if __name__ == "__main__":
    main()

