## Formal proof assistant stubs

The certificate tooling emits machine-checkable CSV files inside `artifacts/`.
This directory sketches how to import those datasets into proof assistants.

### Lean 4 outline

`formal/lean_import.lean` demonstrates:

1. Hash-checking the CSVs against the values recorded in `artifacts/summary.json`.
2. Parsing the window catalog to reconstruct the congruence witnesses.
3. Exposing a structure `WindowWitness` that mirrors the definitions in
   `collatz-conjecture.tex`.
4. Stating the conditional theorem: if every residue satisfies the funnel/window
   conditions, then Collatz holds.

The file intentionally stops after setting up the datatypes and IO helpers; use
it as a starting scaffold for a full Lean formalization.

### Isabelle outline

`formal/isabelle_import.thy` shows the analogous setup for Isabelle/HOL:

1. Register the CSV paths as constants.
2. Define record types for windows and funnels.
3. Sketch how to interpret the CSV contents as lists of records checked inside
   the logic.

Both stubs assume the CSVs already exist (run `make cert-all` first). Each proof
assistant will need bespoke verification scripts, but these files document the
entry points and keep the narrative aligned with the Markdown specification at
`docs/certificate-spec.md`.

