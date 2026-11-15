# STATUS — what is done, what is blocked

Snapshot: 2026-11-15.

## Done

* Locate the three open-conjecture tasks in the TCSExam zip (arXiv:2611.07962), read every
  definition in the fixed parts, and record the fidelity check per task
  (degenerate cases, boundedness requirement, prime-field restriction, integer scaling).
* Literature frontier for all three (AA proved 2026-11; MIRUP refuted 2026-09 by the
  OpenAI preprint; AJT remaining primes).
* Independent exact recomputation pipeline: `scripts/bpp.py` (pattern enumeration → HiGHS LP
  → MILP optimum → exact `Fraction` simplex cross-check → natural-number certificates).
  Self-check: `instC` gives LP = 3 exactly, OPT = 4.
* Printed certificates for `instC` (primal cover with D = 3, dual with D = 28, explicit 4-bin
  packing, `data/certificates.json`).
* Counterexample search, 39,150 instances in four families, 0 hits; gap distribution
  computed (`data/gap_stats.json`) and the negative result interpreted honestly.
* `InstC` Lean certificates written against the task's own definitions
  (`lean/Task/Basic.lean`, appended namespace, fixed part untouched).

## Blocked

* `lake build Task` in this sandbox. `import Mathlib` (inside the fixed part) requires a
  ~7 GB olean cache; the cache tool of the shipped toolchain (`v4.33.0-rc1`) hangs with zero
  output and zero network traffic here, and mathlib cannot be built from source on 2 cores.
  Details and both attempted configurations: `docs/environment.md`.

  Consequence: the `InstC` block is **written and arithmetically cross-checked by an
  independent exact solver, but not yet kernel-checked**. Do not read it as a verified build
  until a machine with the mathlib cache runs `lake build Task`.

## Not attempted

* The `conj` / `refuted` slots (the graded deliverables). Both still hold `sorry`.
  No integer instance with `OPT ≥ ⌈LP⌉ + 2` is known anywhere, and the published
  constructions have denominators of size `(10^15)^m`, which cannot be turned into
  `l : Fin n → ℕ`. Routes judged viable are in `docs/tcsexam-open-conjectures-report.md` §6.
</content>
