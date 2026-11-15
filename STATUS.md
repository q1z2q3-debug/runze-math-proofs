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
* **Kernel run (core layer)**: `lean/core-check/InstC_core.lean` compiles with pure Lean core
  (`rc=0`, no `sorry`, no warnings). It kernel-decides: all 1024 masks classified by capacity,
  every item covered `≥ 3` times, primal total `9 = 3·3`, every pattern's dual load `≤ 28`,
  dual total `84 = 3·28`, and the explicit 4-bin packing. Log: `data/core_check.log`.

## Blocked

* `lake build Task` in this sandbox. `import Mathlib` (inside the fixed part) requires a
  ~7 GB olean cache; the cache tool of the shipped toolchain (`v4.33.0-rc1`) hangs with zero
  output and zero network traffic here, and mathlib cannot be built from source on 2 cores.
  Details and both attempted configurations: `docs/environment.md`.

  Consequence: the `InstC` block in `Task/Basic.lean` is **written but not elaborated here**;
  only its `ℝ`/`ℚ` bridge steps remain unchecked. The arithmetic itself is already
  kernel-verified in `lean/core-check/` and independently by exact LP/ILP.

## Not attempted

* The `conj` / `refuted` slots (the graded deliverables). Both still hold `sorry`.
  No integer instance with `OPT ≥ ⌈LP⌉ + 2` is known anywhere, and the published
  constructions have denominators of size `(10^15)^m`, which cannot be turned into
  `l : Fin n → ℕ`. Routes judged viable are in `docs/tcsexam-open-conjectures-report.md` §6.
</content>
