from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Iterable

try:
    from .config import CertificateConfig  # type: ignore
except ImportError:  # pragma: no cover
    from config import CertificateConfig  # type: ignore


def parse_fraction(value: str) -> Fraction:
    if "/" in value:
        num, denom = value.split("/", 1)
        return Fraction(int(num), int(denom))
    return Fraction(int(value), 1)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_windows(windows_csv: Path, modulus_power: int) -> tuple[
    list[Fraction], set[int], int, int
]:
    modulus_field = f"target_residue_mod_{1 << modulus_power}"
    window_residues: set[int] = set()
    max_j = 0
    max_K = 0
    thresholds: list[Fraction] = []
    with windows_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader, start=1):
            residue = int(row[modulus_field])
            if residue % 2 == 0:
                raise ValueError(f"Row {idx}: residue {residue} must be odd")
            j = int(row["j"])
            K = int(row["K"])
            pattern = json.loads(row["s_vec"])
            exact_modulus = int(row["exact_residue_modulus"])
            exact_residue = int(row["exact_residue"])
            if exact_modulus != (1 << (K + 1)):
                raise ValueError(
                    f"Row {idx}: exact modulus mismatch ({exact_modulus} vs {1 << (K + 1)})"
                )
            if len(pattern) != j:
                raise ValueError(f"Row {idx}: length mismatch between j={j} and pattern={pattern}")
            K_t = 0
            c_t = 0
            reduced_residue = exact_residue
            for t, s_val in enumerate(pattern):
                K_next = K_t + s_val
                modulus = 1 << (K_next + 1)
                lhs = (
                    (pow(3, t + 1, modulus) * (reduced_residue % modulus) + 3 * c_t + (1 << K_t))
                    % modulus
                )
                expected = 1 << K_next
                if lhs != expected:
                    raise ValueError(
                        f"Row {idx}: congruence failed at step {t} "
                        f"(lhs={lhs}, expected={expected}, modulus={modulus})"
                    )
                c_t = 3 * c_t + (1 << K_t)
                K_t = K_next
            if K_t != K:
                raise ValueError(f"Row {idx}: cumulative K mismatch (computed {K_t}, expected {K})")
            three_pow = pow(3, j)
            two_pow = 1 << K
            recorded_A = parse_fraction(row["A"])
            recorded_B = parse_fraction(row["B"])
            recorded_N0 = parse_fraction(row["N0"])
            expected_A = Fraction(three_pow, two_pow)
            expected_B = Fraction(c_t, two_pow)
            if expected_A >= 1:
                raise ValueError(f"Row {idx}: expected A >= 1, invalid window")
            if recorded_A != expected_A or recorded_B != expected_B:
                raise ValueError(
                    f"Row {idx}: affine parameters mismatch "
                    f"(A={recorded_A} vs {expected_A}, B={recorded_B} vs {expected_B})"
                )
            expected_N0 = Fraction(expected_B, 1 - expected_A)
            if recorded_N0 != expected_N0:
                raise ValueError(f"Row {idx}: N0 mismatch ({recorded_N0} vs {expected_N0})")
            window_residues.add(residue)
            thresholds.append(expected_N0)
            max_j = max(max_j, j)
            max_K = max(max_K, K)
    return thresholds, window_residues, max_j, max_K


def accelerated_step(value: int, modulus: int) -> int:
    tmp = 3 * value + 1
    shift = (tmp & -tmp).bit_length() - 1
    tmp >>= shift
    return tmp % modulus


def validate_funnels(
    funnels_csv: Path, window_residues: set[int], modulus: int
) -> tuple[int, list[tuple[int, int]]]:
    field = f"odd_residue_mod_{modulus}"
    records: list[tuple[int, int]] = []
    max_depth = 0
    with funnels_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader, start=1):
            residue = int(row[field])
            length = int(row["min_funnel_length"])
            if length == 0 and residue not in window_residues:
                raise ValueError(f"Row {idx}: residue {residue} claims length 0 but is not a window")
            current = residue
            for depth in range(length):
                if current in window_residues:
                    raise ValueError(
                        f"Row {idx}: residue {residue} hits window after {depth} < {length} steps"
                    )
                current = accelerated_step(current, modulus)
            if current not in window_residues:
                raise ValueError(
                    f"Row {idx}: residue {residue} fails to hit window after {length} steps"
                )
            records.append((residue, length))
            max_depth = max(max_depth, length)
    return max_depth, records


def csv_row_count(path: Path) -> int:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        # subtract header
        return max(sum(1 for _ in reader) - 1, 0)


def summarize(
    windows_csv: Path,
    funnels_csv: Path,
    thresholds: Iterable[Fraction],
    j_max: int,
    L: int,
    modulus: int,
) -> dict:
    max_threshold = max(thresholds)
    N0_star = math.ceil((1 << L) * max_threshold)
    summary = {
        "windows_csv": str(windows_csv),
        "funnels_csv": str(funnels_csv),
        "windows_sha256": file_sha256(windows_csv),
        "funnels_sha256": file_sha256(funnels_csv),
        "window_rows": csv_row_count(windows_csv),
        "funnel_rows": csv_row_count(funnels_csv),
        "j_max": j_max,
        "L": L,
        "J_star": j_max + L,
        "max_window_threshold": str(max_threshold),
        "N0_star": int(N0_star),
        "modulus": modulus,
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Collatz window/funnel certificates.")
    parser.add_argument("--modulus-power", type=int, default=18)
    parser.add_argument("--windows-csv", type=Path, default=None)
    parser.add_argument("--funnels-csv", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = CertificateConfig(
        modulus_power=args.modulus_power,
        max_window_length=10,
        max_valuation=8,
        delta_k=3,
        funnel_depth=16,
        artifacts_dir=args.artifacts_dir,
    )
    windows_csv = args.windows_csv or config.windows_csv
    funnels_csv = args.funnels_csv or config.funnels_csv
    thresholds, window_residues, j_max, _ = validate_windows(windows_csv, config.modulus_power)
    L, _ = validate_funnels(funnels_csv, window_residues, config.modulus)
    summary = summarize(windows_csv, funnels_csv, thresholds, j_max, L, config.modulus)
    summary_path = args.summary or (config.artifacts_dir / "summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

