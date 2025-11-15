from __future__ import annotations

import argparse
import csv
import json
import logging
import math
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence
logger = logging.getLogger(__name__)


try:
    from .config import CertificateConfig  # type: ignore
except ImportError:  # pragma: no cover
    from config import CertificateConfig  # type: ignore


@dataclass
class WindowRecord:
    residue: int
    exact_residue: int
    j: int
    K: int
    pattern: Sequence[int]
    A: Fraction
    B: Fraction
    N0: Fraction

    def to_row(self, modulus: int) -> dict[str, str]:
        return {
            f"target_residue_mod_{modulus}": str(self.residue),
            "exact_residue_modulus": str(1 << (self.K + 1)),
            "exact_residue": str(self.exact_residue),
            "j": str(self.j),
            "K": str(self.K),
            "s_vec": json.dumps(list(self.pattern)),
            "A": format_fraction(self.A),
            "B": format_fraction(self.B),
            "N0": format_fraction(self.N0),
        }


def format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def enumerate_patterns(length: int, total: int, max_part: int) -> Iterable[List[int]]:
    """Yield all compositions of `total` into `length` parts bounded by max_part."""
    if length == 1:
        if 1 <= total <= max_part:
            yield [total]
        return

    def backtrack(prefix: List[int], remaining: int, slots: int) -> Iterator[List[int]]:
        if slots == 1:
            if 1 <= remaining <= max_part:
                yield prefix + [remaining]
            return
        min_part = max(1, remaining - max_part * (slots - 1))
        max_part_allowed = min(max_part, remaining - (slots - 1))
        for part in range(min_part, max_part_allowed + 1):
            yield from backtrack(prefix + [part], remaining - part, slots - 1)

    yield from backtrack([], total, length)


def solve_residue(pattern: Sequence[int]) -> tuple[int, int]:
    """Return (r mod 2^{K+1}, K) satisfying the congruences for the pattern."""
    K_t = 0
    c_t = 0
    r_mod = 0
    for idx, s_val in enumerate(pattern):
        K_next = K_t + s_val
        modulus = 1 << (K_next + 1)
        rhs = (- (3 * c_t + (1 << K_t)) + (1 << K_next)) % modulus
        inv = pow(3, -(idx + 1), modulus)
        r_mod = (inv * rhs) % modulus
        c_t = 3 * c_t + (1 << K_t)
        K_t = K_next
    return r_mod, K_t


def record_from_pattern(pattern: Sequence[int]) -> WindowRecord | None:
    r_mod, K = solve_residue(pattern)
    j = len(pattern)
    three_pow = pow(3, j)
    two_pow = 1 << K
    if three_pow >= two_pow:
        return None
    c_j = 0
    K_t = 0
    for s_val in pattern:
        c_j = 3 * c_j + (1 << K_t)
        K_t += s_val
    A = Fraction(three_pow, two_pow)
    B = Fraction(c_j, two_pow)
    N0 = Fraction(B, 1 - A)
    residue = r_mod
    return WindowRecord(
        residue=residue,
        exact_residue=r_mod,
        j=j,
        K=K,
        pattern=list(pattern),
        A=A,
        B=B,
        N0=N0,
    )


def project_residues(record: WindowRecord, modulus_power: int) -> list[WindowRecord]:
    """Project the exact residue to modulus 2^M, duplicating entries as needed."""
    modulus = 1 << modulus_power
    window_modulus = 1 << (record.K + 1)
    if window_modulus >= modulus:
        residue = record.residue % modulus
        return [
            WindowRecord(
                residue=residue,
                exact_residue=record.exact_residue,
                j=record.j,
                K=record.K,
                pattern=record.pattern,
                A=record.A,
                B=record.B,
                N0=record.N0,
            )
        ]

    stride = window_modulus
    copies = 1 << (modulus_power - (record.K + 1))
    projected = []
    for offset in range(copies):
        candidate = record.residue + offset * stride
        if candidate % 2 == 1:
            projected.append(
                WindowRecord(
                    residue=candidate % modulus,
                    exact_residue=record.exact_residue,
                    j=record.j,
                    K=record.K,
                    pattern=record.pattern,
                    A=record.A,
                    B=record.B,
                    N0=record.N0,
                )
            )
    return projected


def generate_windows(config: CertificateConfig, output_path: Path) -> list[WindowRecord]:
    records: list[WindowRecord] = []
    coverage: set[int] = set()
    counts_by_j: Counter[int] = Counter()
    counts_by_K: Counter[int] = Counter()
    for j in range(1, config.max_window_length + 1):
        k_min = math.ceil(j * math.log2(3))
        logger.info("Enumerating windows for j=%s (K in [%s, %s])", j, k_min, k_min + config.delta_k)
        for K in range(k_min, k_min + config.delta_k + 1):
            for pattern in enumerate_patterns(j, K, config.max_valuation):
                base_record = record_from_pattern(pattern)
                if base_record is None:
                    continue
                projected = project_residues(base_record, config.modulus_power)
                records.extend(projected)
                coverage.update(rec.residue for rec in projected)
                counts_by_j[j] += len(projected)
                counts_by_K[K] += len(projected)
        logger.info("j=%s produced %s projected windows so far", j, counts_by_j[j])
    records.sort(key=lambda rec: rec.residue)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                f"target_residue_mod_{config.modulus}",
                "exact_residue_modulus",
                "exact_residue",
                "j",
                "K",
                "s_vec",
                "A",
                "B",
                "N0",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_row(config.modulus))
    coverage_ratio = len(coverage) / (config.modulus // 2)
    stats_path = output_path.with_suffix(".stats.json")
    stats_payload = {
        "modulus": config.modulus,
        "odd_residue_count": config.modulus // 2,
        "covered_residue_count": len(coverage),
        "coverage_fraction": coverage_ratio,
        "window_rows": len(records),
        "counts_by_j": dict(sorted(counts_by_j.items())),
        "counts_by_K": dict(sorted(counts_by_K.items())),
    }
    with stats_path.open("w") as handle:
        json.dump(stats_payload, handle, indent=2, sort_keys=True)
    logger.info(
        "Generated %s windows covering %.2f%% of odd residues",
        len(records),
        coverage_ratio * 100,
    )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate window certificates for Collatz.")
    parser.add_argument("--modulus-power", type=int, default=18)
    parser.add_argument("--max-j", type=int, default=10)
    parser.add_argument("--s-max", type=int, default=8)
    parser.add_argument("--delta-k", type=int, default=3)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    config = CertificateConfig(
        modulus_power=args.modulus_power,
        max_window_length=args.max_j,
        max_valuation=args.s_max,
        delta_k=args.delta_k,
        funnel_depth=16,
        artifacts_dir=args.artifacts_dir,
    )
    output_path = args.output or config.windows_csv
    generate_windows(config, output_path)


if __name__ == "__main__":
    main()

