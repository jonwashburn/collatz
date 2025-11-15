from __future__ import annotations

import argparse
import csv
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence
logger = logging.getLogger(__name__)


try:
    from .config import CertificateConfig  # type: ignore
except ImportError:  # pragma: no cover
    from config import CertificateConfig  # type: ignore


def read_window_residues(windows_csv: Path, modulus: int) -> set[int]:
    residues: set[int] = set()
    with windows_csv.open(newline="") as handle:
        reader = csv.DictReader(handle)
        residue_field = f"target_residue_mod_{modulus}"
        for row in reader:
            residues.add(int(row[residue_field]))
    return residues


def accelerated_step(residue: int, modulus: int) -> int:
    value = 3 * residue + 1
    shift = (value & -value).bit_length() - 1
    value >>= shift
    return value % modulus


def funnel_lengths(
    config: CertificateConfig, window_residues: set[int]
) -> tuple[list[tuple[int, int]], Counter[int]]:
    modulus = config.modulus
    funnels: list[tuple[int, int]] = []
    histogram: Counter[int] = Counter()
    for idx, residue in enumerate(range(1, modulus, 2), start=1):
        current = residue
        length = None
        for depth in range(config.funnel_depth + 1):
            if current in window_residues:
                length = depth
                break
            current = accelerated_step(current, modulus)
        if length is None:
            raise RuntimeError(
                f"Residue {residue} failed to reach window set within {config.funnel_depth} steps"
            )
        funnels.append((residue, length))
        histogram[length] += 1
        if idx % 5000 == 0:
            logger.info("Processed %s residues (latest length=%s)", idx, length)
    return funnels, histogram


def write_funnels(records: list[tuple[int, int]], output_path: Path, modulus: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [f"odd_residue_mod_{modulus}", "min_funnel_length"]
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for residue, length in records:
            writer.writerow({fieldnames[0]: str(residue), fieldnames[1]: str(length)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate funnel lengths for the Collatz certificate.")
    parser.add_argument("--modulus-power", type=int, default=18)
    parser.add_argument("--funnel-depth", type=int, default=16)
    parser.add_argument("--windows-csv", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    config = CertificateConfig(
        modulus_power=args.modulus_power,
        max_window_length=10,
        max_valuation=8,
        delta_k=3,
        funnel_depth=args.funnel_depth,
        artifacts_dir=args.artifacts_dir,
    )
    windows_csv = args.windows_csv or config.windows_csv
    if not windows_csv.exists():
        raise FileNotFoundError(f"window catalog not found: {windows_csv}")
    window_residues = read_window_residues(windows_csv, config.modulus)
    records, histogram = funnel_lengths(config, window_residues)
    output_path = args.output or config.funnels_csv
    write_funnels(records, output_path, config.modulus)
    histogram_path = output_path.with_suffix(".hist.json")
    with histogram_path.open("w") as handle:
        json.dump(dict(sorted(histogram.items())), handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()

