## Collatz Certificate Workspace

This directory bundles every artifact related to the finite window–funnel
certificate and manuscript so it can be downloaded or shared independently of
the main `reality` repository.

### Layout

| Path | Contents |
| --- | --- |
| `collatz-conjecture.tex` | LaTeX manuscript describing the conditional theorem and certificate protocol. |
| `docs/certificate-spec.md` | Operational spec for window/funnel CSVs (W1–W4, F1–F3, global bounds). |
| `tools/certificate/` | Generator, funnel builder, validator, and finite check scripts (Python). |
| `artifacts/` | Generated CSVs, stats, `summary.json`, `finite-check.log`, and `certificate_bundle.tgz`. |
| `formal/` | Lean and Isabelle stubs for importing/verifying the CSVs. |
| `Makefile` | Targets (`make cert-all`, etc.) to regenerate and validate the certificate. |

### Usage

1. Install Python 3.10+ and run `make cert-all` to regenerate all artifacts.
2. Inspect `artifacts/summary.json` for the derived constants (`J*`, `N0*`) and
   SHA-256 hashes.
3. The tarball `artifacts/certificate_bundle.tgz` packages the CSVs + logs for
   easy distribution.
4. Use the files under `formal/` as starting points when importing the data into
   Lean or Isabelle.

