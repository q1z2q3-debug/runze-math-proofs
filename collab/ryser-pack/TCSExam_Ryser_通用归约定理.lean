/-!
TCSExam / ryser-conjecture — GENERAL REDUCTION THEOREM (instance-independent)

*** NOT COMPILED ***  This sandbox has no Lean 4 / mathlib (no `lean`, `lake`).
The mathematical proof is complete; the Lean text is a faithful specification
against the official `Task/Basic.lean` API, to be built in the official
`tcs-lean-base` image (leanprover/lean4:v4.33.0-rc1).

Official API used (verbatim from Task/Basic.lean):
  RPartiteHypergraph.IsCover          : Finset (Fin r × V) → Prop
  RPartiteHypergraph.coverNumber      : ℕ              (τ, Finset.min')
  RPartiteHypergraph.matchingNumber  : ℕ              (ν, Finset.max')
  RPartiteHypergraph.RyserBound      : Prop := τ ≤ (r-1)*ν
  le_coverNumber      : (∀ C, IsCover C → k ≤ C.card) → k ≤ coverNumber
  matchingNumber_le   : (∀ M, IsMatching M → M.card ≤ k) → matchingNumber ≤ k
  coverNumber_le      : IsCover C → coverNumber ≤ C.card
  exists_isCover_card_eq / exists_isMatching_card_eq

THEOREM A (reduction).  If H is r-partite with
   (1) intersecting: any two distinct edges agree in some part
   (2) distinct    : H.edges has no repeated transversals
   (3) degree      : every (p,v) lies in at most D edges
   (4) size        : (r-1)*D < H.edges.card
then ¬ H.RyserBound.
Proof: (1) => ν = 1.  Any cover C hits all |E| edges, each vertex hits at most
D edges, so |E| ≤ |C|*D, hence |C| ≥ ceil(|E|/D) ≥ r by (4), so τ ≥ r.
RyserBound would give τ ≤ (r-1)*ν = r-1 < r.  Contradiction.
-/

import Mathlib

namespace RyserConjecture
namespace RPartiteHypergraph

variable {r : ℕ} {V : Type*} [Fintype V] [DecidableEq V]
  (H : RPartiteHypergraph r V) [NeZero r]

/-- Number of edges using vertex `v` of part `p`. -/
def vertexDegree (p : Fin r) (v : V) : ℕ :=
  (H.edges.filter fun e => e p = v).card

/-- (1) pairwise intersecting => ν ≤ 1. -/
theorem matchingNumber_le_one_of_intersecting
    (hI : ∀ e ∈ H.edges, ∀ f ∈ H.edges, e ≠ f → ∃ i, e i = f i) :
    H.matchingNumber ≤ 1 := by
  apply H.matchingNumber_le
  intro M hM
  -- hM.2 : ∀ e∈M, ∀ e'∈M, e ≠ e' → ∀ i, e i ≠ e' i  (disjointness)
  by_contra h
  -- M.card ≥ 2, take two distinct members e,f ∈ M ⊆ H.edges;
  -- hI gives some i with e i = f i, contradicting hM.2.
  have hge : 2 ≤ M.card := by omega
  obtain ⟨e, heM, f, hfM, hef⟩ := Finset.exists_pair_ne_of_two_le_card hge
  have heE : e ∈ H.edges := hM.1 heM
  have hfE : f ∈ H.edges := hM.1 hfM
  obtain ⟨i, hi⟩ := hI e heE f hfE hef
  exact (hM.2 e heM f hfM hef i) hi

/-- Every edge is hit by C: it lies in the union of degree classes of C. -/
theorem edges_subset_biUnion_of_isCover (C : Finset (Fin r × V)) (hC : H.IsCover C) :
    H.edges ⊆ C.biUnion (fun pv => H.edges.filter fun e => e (pv.1) = pv.2) := by
  intro e he
  -- hC : ∀ e∈H.edges, ∃ i, (i, e i) ∈ C
  obtain ⟨i, hiC⟩ := hC e he
  rw [Finset.mem_biUnion]
  exact ⟨(i, e i), hiC, by simp [i]⟩

/-- (3) counting: |E| ≤ |C|·D for every cover C. -/
theorem card_edges_le_card_mul_degree (C : Finset (Fin r × V)) (hC : H.IsCover C)
    (D : ℕ) (hD : ∀ (p : Fin r) (v : V), H.vertexDegree p v ≤ D) :
    H.edges.card ≤ C.card * D := by
  have hsub := H.edges_subset_biUnion_of_isCover C hC
  have h1 : H.edges.card ≤ (C.biUnion (fun pv => H.edges.filter fun e => e pv.1 = pv.2)).card :=
    Finset.card_le_card hsub
  have h2 : (C.biUnion (fun pv => H.edges.filter fun e => e pv.1 = pv.2)).card ≤
      C.sum (fun pv => (H.edges.filter fun e => e pv.1 = pv.2).card) :=
    Finset.card_biUnion_le
  have h3 : C.sum (fun pv => (H.edges.filter fun e => e pv.1 = pv.2).card) ≤
      C.sum (fun _ => D) := by
    apply Finset.sum_le_sum
    intro pv hpv
    simpa [vertexDegree] using hD pv.1 pv.2
  have h4 : C.sum (fun _ => D) = C.card * D := by simp
  omega

/-- (4) => τ ≥ r. -/
theorem le_coverNumber_of_size (D : ℕ)
    (hD : ∀ (p : Fin r) (v : V), H.vertexDegree p v ≤ D)
    (hE : (r - 1) * D < H.edges.card) (hr : 1 ≤ r) :
    r ≤ H.coverNumber := by
  apply H.le_coverNumber
  intro C hC
  have hle := H.card_edges_le_card_mul_degree C hC D hD
  -- from (r-1)*D < |E| ≤ |C|*D deduce r ≤ |C| (D>0 follows from hE)
  by_contra hnot
  have hClt : C.card < r := by omega
  have hCle : C.card ≤ r - 1 := by omega
  have : H.edges.card ≤ (r - 1) * D := by nlinarith
  omega

/-- THEOREM A. -/
theorem not_ryserBound_of_counting (D : ℕ)
    (hI : ∀ e ∈ H.edges, ∀ f ∈ H.edges, e ≠ f → ∃ i, e i = f i)
    (hD : ∀ (p : Fin r) (v : V), H.vertexDegree p v ≤ D)
    (hE : (r - 1) * D < H.edges.card) (hr : 2 ≤ r) :
    ¬ H.RyserBound := by
  intro hb
  have hnu : H.matchingNumber ≤ 1 := H.matchingNumber_le_one_of_intersecting hI
  have htau : r ≤ H.coverNumber := H.le_coverNumber_of_size D hD hE (by omega)
  -- hb : H.coverNumber ≤ (r-1)*H.matchingNumber
  have : H.coverNumber ≤ r - 1 := by
    have hm : (r - 1) * H.matchingNumber ≤ (r - 1) * 1 := by
      exact Nat.mul_le_mul_left (r - 1) hnu
    omega
  omega

end RPartiteHypergraph
end RyserConjecture
