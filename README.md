# runze-math-proofs

Machine-checked mathematics and formal-verification experiments (Lean 4 + mathlib).

> 中文说明见下：本仓库收录「润泽数学证明」系列的可复现实验——题目定位、形式化忠实性核查、
> 精确计算复算，以及 Lean 4 内核验证。所有脚本、证书、日志均可独立复跑。

---

## What's inside

```
lean/       Lean 4 project (toolchain pinned to the exact version the task ships)
scripts/    exact bin-packing toolkit, counterexample search, certificate generator
data/       machine-readable certificates, search logs, gap statistics
docs/       research report (fidelity check, literature frontier, barrier analysis)
```

## Current experiment: TCSExam open conjectures (arXiv:2611.07962)

The benchmark ships three *open* conjecture tasks. We took them on:

| Task | Fidelity | Frontier status (2026-11) | Outcome |
|---|---|---|---|
| `aaronson-ambainis` | faithful (degenerate `n=0` excluded by hypotheses) | **proved** — arXiv:2611.09773 (2026-11-06), confirmed by S. Aaronson (2026-11-10) | literature only; formalisation out of scope |
| `alon-jaeger-tarsi` | faithful (`p` prime, `p ≥ 5`; `n=0` vacuous) | Nagy–Pach cover `p > 61, p ≠ 79`; `p ∈ {5,…,61} ∪ {79}` open | literature only |
| `bin-packing-mirup` | faithful (integer sizes lossless, `Nat.ceil` matches the copy semantics) | **refuted** — OpenAI preprint 2026-09-24 (`OPT > B + c` with `OPT_LP = B`) | **kernel-checked tightness of the `+1`** on `instC`; 39,150-instance search, 0 hits |

### The kernel certificate

**Status: the arithmetic is kernel-checked; the file is not built here.** `lean/core-check/`
replays the certificates in pure Lean core (no mathlib) and compiles cleanly
(`data/core_check.log`, `rc=0`), so the counting facts are kernel facts. What is missing is the
`ℝ`/`ℚ` bridge: `lean/Task/Basic.lean` starts with `import Mathlib`, and this sandbox cannot
fetch the ~7 GB olean cache (`docs/environment.md`), so the task file itself was not elaborated
here. The block uses no `axiom`, no `native_decide`, no `sorry`:

`lean/Task/Basic.lean` adds a `namespace InstC` block **after the fixed part** (the task file is
otherwise untouched) stating, inside the task's own definitions:

* `lpVal instC 81 = 3` — via a primal natural-number cover certificate (`D = 3`, 8 patterns,
  total weight 9) and a dual natural-number certificate (`D = 28`, weights
  `1,2,2,3,6,10,11,13,14,22`, total 84);
* `optNumber instC 81 = 4` — an explicit 4-bin packing plus a `decide` refutation of every
  3-bin packing (`3^10` assignments);
* therefore `optNumber = Nat.ceil (lpVal) + 1`: the `+1` of the Modified Integer Round-Up
  Property is **attained exactly** on `instC`, and IRUP (`OPT ≤ ⌈LP⌉`) fails there.

That is the honest ceiling of this run: the slot still needs an explicit instance with
`OPT ≥ ⌈LP⌉ + 2`, and every published construction has denominators of size `(10^15)^m`,
which cannot be written down as `l : Fin n → ℕ`. See `docs/` for the parameter-level barrier
analysis and the three routes we judge viable.

## Build

```bash
cd lean
lake exe cache get     # mathlib oleans, ~7 GB
lake build Task
```

Toolchain: `leanprover/lean4:v4.33.0-rc1` (the version the task file pins), mathlib at the
matching tag. `lean/README.md` documents the pitfalls (why 4.36-rc2 fails, why `elan` install
is unreliable, why the cache must not live on a small root partition).

## Reproduce the numbers

```bash
python3 scripts/bpp.py        # self-check: instC -> LP 3 (exact), OPT 4
python3 scripts/certgen.py    # regenerate data/certificates.json
python3 scripts/search.py     # counterexample search (MILP + HiGHS)
python3 scripts/stats.py      # gap distribution OPT - ceil(LP)
```

## Cite

```
Runze Math Proofs — TCSExam open conjectures experiment.
https://github.com/q1z2q3-debug/runze-math-proofs
```

## License

MIT — see `LICENSE`.
</content>
