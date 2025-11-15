## Collatz Window/Funnel Certificate Specification

This document summarizes the requirements that the CSV artifacts must satisfy in
order for the finite-certificate proof route to succeed. It mirrors the
definitions in `collatz-conjecture.tex` but is phrased operationally for the
generation/validation tooling housed under `tools/certificate/`.

### Fixed parameters

- Modulus: \(M = 18\) so residue computations occur modulo \(2^{18} = 262144\).
- Window search limits: \(j \le 10\), step valuations \(1 \le s_i \le 8\),
  and total valuation \(K\) inside the band
  \(\lceil j \log_2 3 \rceil \le K \le \lceil j \log_2 3 \rceil + 3\).
- Funnel depth target: \(L \le 16\). All odd residues must reach the window
  set within this bound or trigger a search-extension alert.

### Window conditions (W1–W4)

For every row of `windows.csv` with fields
\((R, j, K, s, A, B, N_0)\):

1. **(W1)** With \(K_0 = 0\), \(c_0 = 0\) and the recursions
   \(K_{t+1} = K_t + s_t\), \(c_{t+1} = 3c_t + 2^{K_t}\),
   the congruences
   \(3^{t+1} R + 3c_t + 2^{K_t} \equiv 2^{K_{t+1}} \pmod{2^{K_{t+1}+1}}\)
   hold for all \(t < j\).
2. **(W2)** \(A = 3^j / 2^K < 1\) and \(B = c_j / 2^K\).
3. **(W3)** \(N_0 = B / (1-A)\).
4. **(W4)** \(R\) is an odd residue class modulo \(2^{18}\).

Each row corresponds to an anchor residue obtained by projecting the exact class
determined mod \(2^{K+1}\) down to \(2^{18}\).

### Funnel conditions (F1–F3)

For `funnels.csv`, each row stores an odd residue \(R\bmod 2^{18}\) and a
minimal funnel length \(d_R \in \{0,\dots,L\}\):

1. **(F1)** \(d_R = 0\) iff \(R\) appears in `windows.csv`.
2. **(F2)** For \(d_R > 0\), iterating the accelerated residue map
   \(\widetilde{T}(R) = \frac{3R+1}{2^{\nu_2(3R+1)}} \bmod 2^{18}\)
   exactly \(d_R\) times lands in the window set, with no earlier hit.
3. **(F3)** The maximum \(d_R\) over all residues does not exceed \(L\).

### Derived global constants

Given validated CSVs:

- \(j_{\max} = \max j\) across windows.
- \(L = \max d_R\) across funnels.
- \(J^\* = j_{\max} + L\).
- \(N_0^\* = \left\lceil 2^L \max N_0 \right\rceil\).

These values feed the log-height descent argument. The validator must compute
them directly from the CSVs and record them (along with SHA-256 hashes of the
files) in `artifacts/summary.json`.

### Artifact expectations

| File                     | Description                                                |
|--------------------------|------------------------------------------------------------|
| `artifacts/windows.csv`  | Window catalog satisfying (W1–W4).                         |
| `artifacts/funnels.csv`  | Funnel lengths satisfying (F1–F3).                         |
| `artifacts/summary.json` | `j_max`, `L`, `J_star`, `N0_star`, file hashes, counts.     |
| `artifacts/finite-check.log` | Evidence that every \(n \le N_0^\*\) reaches \(1\).   |

Generation scripts are responsible for producing the CSVs; the validator
recomputes all properties from scratch and emits the summary. The finite-check
step either references an external verified bound or performs an explicit
simulation when \(N_0^\*\) sits below an available computational certificate.

