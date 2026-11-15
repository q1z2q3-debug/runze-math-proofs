# Lean 4 project — TCSExam `bin-packing-mirup`

The task file (`Task/Basic.lean`) is copied verbatim from the benchmark zip
(`tasks/open/bin-packing-mirup/environment/app`). Everything under the
`-- BEGIN OF FIXED PART … -- END OF FIXED PART` markers is untouched. The only
addition is `namespace InstC` at the end of the file: the machine-checked
certificates for the benchmark's own example `instC`.

The two slots (`conj`, `refuted`) still contain `sorry` — they are the graded
deliverable and are **not** modified here.

## Toolchain

`lean-toolchain` pins `leanprover/lean4:v4.33.0-rc1`, the exact version the task
ships. `lakefile.toml` points at a *local* mathlib checkout (path require), so
adjust the path if you clone elsewhere:

```toml
[[require]]
name = "mathlib"
path = "/home/user/leanlib/mathlib4-433"
```

`lake-manifest.json` pins the same transitive revisions as the task zip
(plausible, LeanSearchClient, importGraph, proofwidgets, aesop, Qq, batteries),
so the build is reproducible without network access once the cache is warm.

## Build

```bash
lake exe cache get        # downloads ~9,100 mathlib oleans (~7 GB)
lake build Task
```

Expected: `Task/Basic.lean` compiles with **no** `sorry` warning for the `InstC`
block and no error anywhere (the two slots emit the standard "declaration uses
`sorry`" warnings, which is the graded state).

## Pitfalls (learned the hard way)

1. **Do not use mathlib `master`.** With mathlib master + `lean4 v4.36.0-rc2`
   the build dies inside `Batteries`:

   ```
   Batteries/Data/UInt.lean:35:8: `UInt8.max_def` has already been declared
   Batteries/Data/UInt.lean:40:6: Unknown identifier `max_def`
   Batteries/Data/BitVec/Lemmas.lean:19:8: `BitVec.toNat_pow` has already been declared
   ```

   This is a toolchain/dependency mismatch (Batteries expects an older core),
   not a problem with the task file. Use the tag that matches `lean-toolchain`.

2. **`elan toolchain install` is unreliable here** (partial downloads / release
   metadata parse errors). Download the release tarball directly and unpack it
   into `~/.elan/toolchains/leanprover--lean4---v<ver>/`:

   ```bash
   curl -sSL -o lean.tar.zst \
     https://github.com/leanprover/lean4/releases/download/v4.33.0-rc1/lean-4.33.0-rc1-linux.tar.zst
   python3 -c "import zstandard,tarfile; d=zstandard.ZstdDecompressor(); \
     f=open('lean.tar.zst','rb'); r=d.stream_reader(f); \
     tarfile.open(fileobj=r,mode='r|').extractall('/tmp/x',filter='data')"
   ```

   (There is no system `zstd` and no apt package for it; `pip install zstandard`.)

3. **Watch the disk.** A 7 GB cache on a partition with < 8 GB free fails as
   `No space left on device`, which then *looks* like a corrupt extraction —
   the symptom is a missing `lib/lean/libInit_shared.so` and
   `lake: error while loading shared libraries`. Keep mathlib off small roots.

4. **`lake exe cache get` also materialises dependency sources.** The first
   build after a cache fetch still compiles `Batteries`, `aesop`, `Qq`, … from
   scratch (several minutes). It is not a hang.
</content>
