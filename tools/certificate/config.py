from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CertificateConfig:
    """Shared configuration knobs for the certificate toolchain."""

    modulus_power: int = 18
    max_window_length: int = 10
    max_valuation: int = 8
    delta_k: int = 3
    funnel_depth: int = 16
    artifacts_dir: Path = Path("artifacts")

    @property
    def modulus(self) -> int:
        return 1 << self.modulus_power

    @property
    def windows_csv(self) -> Path:
        return self.artifacts_dir / "windows.csv"

    @property
    def funnels_csv(self) -> Path:
        return self.artifacts_dir / "funnels.csv"

    def replace_paths(self, artifacts_dir: Path | None = None) -> "CertificateConfig":
        """Return a copy with optional path overrides."""
        if artifacts_dir is None:
            return self
        return CertificateConfig(
            modulus_power=self.modulus_power,
            max_window_length=self.max_window_length,
            max_valuation=self.max_valuation,
            delta_k=self.delta_k,
            funnel_depth=self.funnel_depth,
            artifacts_dir=artifacts_dir,
        )

