/-
Core-only kernel check for the `instC` instance of the TCSExam `bin-packing-mirup` task.

`Task/Basic.lean` cannot be elaborated here (it needs the whole `Mathlib` olean cache, see
`docs/environment.md`), but the *combinatorial content* of the `InstC` certificates uses only
`ℕ` arithmetic, so it can be replayed in pure Lean core with the same conventions:

* a pattern is a bitmask `m < 2^10` whose item sizes sum to at most `L = 81` (empty mask
  included, exactly as `Finset.univ.powerset.filter (IsPattern l L)`);
* `PacksIn 3` means an assignment `Fin 10 → Fin 3` with every bin load ≤ 81.

Everything below is decided by the kernel (`decide`), no `native_decide`, no `sorry`,
no axioms. Compile with: `lean InstC_core.lean`
-/

set_option maxRecDepth 1000000
set_option maxHeartbeats 8000000

namespace InstC

/-- Item sizes of `instC`, in the order of `Fin 10`. -/
def sizes : List Nat := [4, 6, 6, 9, 16, 29, 32, 37, 40, 62]

/-- Bin capacity. -/
def L : Nat := 81

def sizeAt (i : Nat) : Nat := sizes.getD i 0

/-- `i`-th bit of the bitmask `m`, as `0`/`1` (`Nat.testBit`, kept as arithmetic). -/
def bit (m i : Nat) : Nat := (m / 2 ^ i) % 2

/-- Total size of the items selected by mask `m`. -/
def loadMask (m : Nat) : Nat := (List.range 10).foldl (fun a i => a + bit m i * sizeAt i) 0

/-- Is `m` a pattern (fits into one bin)? -/
def isPat (m : Nat) : Bool := loadMask m ≤ L

/-- All patterns, as bitmasks: `2^10` masks filtered by the capacity constraint. -/
def pats : List Nat := (List.range 1024).filter isPat

/-- Primal certificate weights `X`, indexed by bitmask (patterns only). -/
def X (m : Nat) : Nat :=
  if m = 113 then 1      -- {0,4,5,6}   4+16+29+32 = 81
  else if m = 172 then 1 -- {2,3,5,7}   6+9+29+37  = 81
  else if m = 198 then 1 -- {1,2,6,7}   6+6+32+37  = 81
  else if m = 294 then 1 -- {1,2,5,8}   6+6+29+40  = 81
  else if m = 328 then 1 -- {3,6,8}     9+32+40    = 81
  else if m = 385 then 1 -- {0,7,8}     4+37+40    = 81
  else if m = 523 then 1 -- {0,1,3,9}   4+6+9+62   = 81
  else if m = 528 then 2 -- {4,9}       16+62      = 78
  else 0

/-- How many times item `i` is covered by `X` (counted with weights). -/
def coverSum (i : Nat) : Nat := (pats.map (fun m => bit m i * X m)).sum

/-- Total primal weight. -/
def primalTotal : Nat := (pats.map X).sum

/-- Dual item weights `W`. -/
def W (i : Nat) : Nat := [1, 2, 2, 3, 6, 10, 11, 13, 14, 22].getD i 0

/-- Dual weight carried by pattern `m`. -/
def dualLoad (m : Nat) : Nat := (List.range 10).foldl (fun a i => a + bit m i * W i) 0

/-- Total dual weight. -/
def dualTotal : Nat := (List.range 10).foldl (fun a i => a + W i) 0

/-- Explicit 4-bin assignment of the ten items. -/
def pack4 : List Nat := [0, 0, 0, 1, 3, 0, 0, 1, 2, 3]

/-- Load of bin `b` under `pack4`. -/
def binLoad (b : Nat) : Nat :=
  (List.range 10).foldl (fun a i => a + if pack4.getD i 0 = b then sizeAt i else 0) 0

-- ---------------------------------------------------------------- primal side

/-- Every pattern of `pats` really fits into the bin. -/
theorem pats_fit : (pats.all isPat) = true := by decide

/-- Every item is covered at least `3` times. -/
theorem cover_ok : (List.range 10).all (fun i => decide (3 ≤ coverSum i)) = true := by
  decide

/-- The primal certificate has total weight `9 = 3 · 3`. -/
theorem primal_total_ok : primalTotal = 9 := by decide

-- ------------------------------------------------------------------ dual side

/-- No pattern carries more than `28` of dual weight (checked over all `2^10` masks;
`pats` are exactly those with a capacity-legal load). -/
theorem dual_ok : (pats.all (fun m => decide (dualLoad m ≤ 28))) = true := by decide

/-- The dual certificate has total weight `84 = 3 · 28`. -/
theorem dual_total_ok : dualTotal = 84 := by decide

-- --------------------------------------------------------------- packing side

/-- `instC` packs into four bins (loads 77, 46, 40, 78 ≤ 81). -/
theorem pack4_ok : (List.range 4).all (fun b => decide (binLoad b ≤ L)) = true := by decide

/-- The single combined statement that the kernel establishes:
primal cover `3 ≤ coverSum i` for every item, total `9 = 3·3`; dual `dualLoad m ≤ 28`
for every pattern, total `84 = 3·28`; and an explicit 4-bin packing.

Consequently (with the bridge lemmas in `Task/Basic.lean`) `lpVal instC 81 = 3 = ⌈LP⌉`
and `optNumber instC 81 ≤ 4`. The matching lower bound `optNumber ≥ 4` — i.e. that no
3-bin packing exists — is *not* a `3^10` enumeration here: this sandbox has 3 GB of RAM and
the kernel overflows on it (`maximum recursion depth` / OOM). It is proved instead by the
count argument recorded in `docs/tcsexam-open-conjectures-report.md` §5.3 and confirmed
by exact MILP (`scripts/bpp.py`: OPT = 4).
-/
theorem lp_side :
    ((List.range 10).all (fun i => decide (3 ≤ coverSum i)) = true)
      ∧ (primalTotal = 9) ∧ ((pats.all (fun m => decide (dualLoad m ≤ 28))) = true)
      ∧ (dualTotal = 84) ∧ ((List.range 4).all (fun b => decide (binLoad b ≤ L)) = true) :=
  ⟨cover_ok, primal_total_ok, dual_ok, dual_total_ok, pack4_ok⟩

end InstC
