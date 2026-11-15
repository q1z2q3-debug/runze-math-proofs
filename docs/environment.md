# Environment log — what actually works

Recorded while trying to build the TCSExam `bin-packing-mirup` task (a Lean 4 file whose
fixed part is `import Mathlib`, pinned to `leanprover/lean4:v4.33.0-rc1`).

## 1. Installing the toolchain

`elan toolchain install leanprover/lean4:v4.33.0-rc1` failed repeatedly (partial download
files, release-metadata parse errors). Manual route that works:

```bash
curl -sSL -o lean.tar.zst \
  https://github.com/leanprover/lean4/releases/download/v4.33.0-rc1/lean-4.33.0-rc1-linux.tar.zst
python3 -c "import zstandard,tarfile; d=zstandard.ZstdDecompressor(); \
  f=open('lean.tar.zst','rb'); r=d.stream_reader(f); \
  tarfile.open(fileobj=r,mode='r|').extractall('/tmp/x',filter='data')"
mv /tmp/x/lean-4.33.0-rc1-linux ~/.elan/toolchains/leanprover--lean4---v4.33.0-rc1
```

There is no system `zstd` and no apt package for it; `pip install zstandard` suffices.

## 2. Disk: `/opt` is a 9.8 GB root partition

A 7 GB mathlib cache under `/opt` fills it. The failure then *looks* like a corrupt
extraction — `lib/lean/libInit_shared.so` missing, `lake: error while loading shared
libraries: libInit_shared.so` — because `tarfile.extractall` dies with
`OSError: [Errno 28] No space left on device` halfway through. Keep Lean libraries on
`/home/user` (10 TB volume).

## 3. The version trap: do **not** mix mathlib master with a 4.33-era manifest

First attempt: mathlib `master` (toolchain `v4.36.0-rc2`) + the task's own
`lake-manifest.json` (batteries rev `d60e6444…`). Result — the build dies inside Batteries:

```
error: Batteries/Data/UInt.lean:35:8: `UInt8.max_def` has already been declared
error: Batteries/Data/UInt.lean:40:6: Unknown identifier `max_def`
error: Batteries/Data/BitVec/Lemmas.lean:19:8: `BitVec.toNat_pow` has already been declared
warning: Batteries/Data/Fin/Fold.lean:79:20: `dif_pos` has been deprecated
```

Diagnosis: those are *toolchain/dependency* mismatches (Batteries compiled against a different
core), not problems with the task file. Two consistent configurations exist:

| config | toolchain | mathlib | dependency revs | cache |
|---|---|---|---|---|
| A (as shipped) | `v4.33.0-rc1` | tag `v4.33.0-rc1` | task's `lake-manifest.json` | **unavailable here** (see §4) |
| B (used for the kernel run) | `v4.36.0-rc2` | `master` | regenerate — delete `lake-manifest.json` and let Lake resolve from mathlib's own manifest | works |

Config B is semantically equivalent for this file (nothing here depends on lemma names that
changed), and it is the only one whose cache could be fetched in this sandbox.

## 4. Why the 4.33 cache never downloads

`mathlib v4.33.0-rc1`'s `Cache/` code requires `leantar` (bundled from
nightly-2026-03-09 onward) and, for download, a *container* base URL per repository
(`https://cache.mathlib.org/mathlib4-<branch>`, files at `<base>/f/<prefix><name>`),
driven through generated `curl` configs. In this sandbox:

* a direct run of the cache binary aborts with
  `leantar not found in Lean sysroot. This toolchain may predate nightly-2026-03-09`
  unless `LEAN_SYSROOT` is exported by the caller;
* under `lake exe cache get` the process sits at ~1 % CPU with no output and no bytes
  written (`/proc/<pid>/io` flat, `~/.cache/mathlib` never created) — it never reaches
  the download stage.

`Mathlib` alone cannot be built from source on 2 cores in reasonable time, and
`import Mathlib` is in the fixed part, so a reduced-import build is not an option
without deviating from the shipped file.

## 5. What this means for reproducibility

Config B is what `lean/` documents. Anyone with network access and a normal mathlib
install should prefer config A (the shipped pin). The arithmetic in `InstC` does not
depend on which config is used — both keep `lift_trace`-free kernel reduction
(`decide`) over `Fin 10` and `Fin 4`, which is core Lean plus `Finset`/`ℝ` from mathlib.
</content>
