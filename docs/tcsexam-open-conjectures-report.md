# TCSExam「开放猜想」实做记录：定位、核查、复算与机检验证

> 对象：arXiv:2611.07962（TCSExam 基准论文）＋随附题包 `TCSExam_开放猜想原始题面.zip`
> 日期：2026-11-15　｜　全部数值可复现（脚本与日志随附）

---

## 0. 一页结论

| 题 | 形式化是否忠实 | 2026-11 的前沿状态 | 我这一步做到什么 |
|---|---|---|---|
| `aaronson-ambainis` | 忠实（n=0 退化被假设排除，bounded 条件必需） | **已被证明**（arXiv:2611.09773，2026-11-06；Aaronson 博客 2026-11-10 确认） | 只做文献定位；形式化不可行（研究级体量） |
| `alon-jaeger-tarsi` | 忠实（素数域 p≥5，n=0 平凡真） | Nagy–Pach 覆盖 p>61 且 p≠79；余 p∈{5,…,61}∪{79} 未解 | 只做文献定位；已知可借鉴范式＝Astra 的 F5/n≤9 机检 |
| `bin-packing-mirup` | 忠实（整数化无损、⌈·⌉ 与个体拷贝语义一致、n≤2 平凡） | **已被反证**（OpenAI 2026-09-24 预印本 + Lean 形式化文档 118） | **在题目定义层内机检验证了「+1 恰好紧」**（LP=3、OPT=4、3 箱不可行），并做了 39,150 例计算搜索 |

**诚实的结论**：满分要求是把 `conj` 或 `refuted` 槽填满（all-or-nothing）。三道题里唯一有可能填 `refuted` 的是 MIRUP，但现有公开反例的构造参数（P0=100^11、K≈1.25×10^13、尺寸分母 ≈(10^15)^m）**不存在可内核判定的显式实例**，而槽位要的正是 `Fin n → ℕ` 的显式尺寸表。所以本次**没有拿到 1.0**；本报告的价值在于：把「为什么拿不到」量化到参数级，并把能机检的部分真机检了。

---

## 1. 题目定位

题包解压后 `tasks/` 下只有三个目录，均为开放猜想（论文中的 20 道 theorem / 30 道 solver / 20 道 construction 不在本包内）：

```
tasks/open/aaronson-ambainis/environment/app/Task/Basic.lean
tasks/open/alon-jaeger-tarsi/environment/app/Task/Basic.lean
tasks/open/bin-packing-mirup/environment/app/Task/Basic.lean
```

三份文件的骨架一致：`-- BEGIN OF FIXED PART` 里是「不可改」的定义区，`-- END OF FIXED PART` 之后是两个槽位：

```lean
theorem conj    : <命题> := by sorry
theorem refuted : <命题的否定> := by sorry
```

评分逻辑（论文附录 + 题包注释）：**任填其一即满分**，但必须干净——只用 `propext / Classical.choice / Quot.sound`，禁 `axiom`、`native_decide`、任何残留 `sorryAx`。`tests/` 目录在 zip 里是空的（verifier 未随包发布）。

论文侧对应位置：§3 表 1 列出 70 道题的状态；§5.6 是 MIRUP 与 Ryser 的「已接受反证」记录。论文写得非常直白：**其余 28 道 conjecture 类题目当时的提交无一获得完整接受**，也就是说这三道是「当前无人拿满分」的题。

---

## 2. 形式化层的 fidelity 核查（逐条）

做开放猜想题，第一件事不是解题，而是确认「题面写的到底是不是那个猜想」。三道我都逐条扫了退化漏洞（`n=0`、`n=1`、边界常数、有界性、域限制），结论是**三道都没有可乘之机**，这也解释了为什么它们能被放进 benchmark。

### 2.1 `aaronson-ambainis`

```lean
Conjecture := ∃ C : ℕ, 0 < C ∧ ∀ {n} (p : MvPolynomial (Fin n) ℝ) (d : ℕ) (ε : ℝ),
  0 < d → 0 < ε → p.totalDegree ≤ d → BoundedOnCube p → ε ≤ cubeVariance p →
  ∃ i : Fin n, (ε / d)^C ≤ cubeInfluence p i
```

- **`n = 0` 无漏洞**：`Fin 0` 上 `cubeVariance = 0`，而 `ε > 0`，前件不可满足，命题真但空。不构成「白拿」——因为要证的是 `∃ C`，`C` 必须对所有 `n` 一致，空的 `n=0` 分支不提供任何帮助。
- **`BoundedOnCube`（0 ≤ p ≤ 1 于超立方体）是必需的，且不能删**：题包自带的 ledger 注释就点了：去掉有界性后 `p = (X₁+…+Xₙ)/√n` 是标准反例（方差 ~1、影响 ~1/√n），把结论的 `(ε/d)^C` 打穿。形式化把这个条件留在前件里，与文献口径一致，因此忠实。
- **常数吸收是对的**：文献形式是「∃ c>0, k：Inf_i ≥ c·(ε/d)^k」。题面把 c 吸收进指数：只需 `C = k + ⌈log₄(1/c)⌉`，因为 `ε ≤ Var(p) ≤ 1/4` 且 `d ≥ 1` 给出 `ε/d ≤ 1/4`，于是 `(ε/d)^C ≤ (1/4)^{C-k}(ε/d)^k ≤ c(ε/d)^k`。反向平凡。**等价性成立**。
- **前沿**：这道题在题面写作时是开放的，但在 11 月已被证明（见 §3.1）。形式化仍是研究级体量（要对一般 `MvPolynomial` 做随机限制/影响分析），本步未推进。

### 2.2 `alon-jaeger-tarsi`

```lean
AJTConjecture := ∀ (p : ℕ) [Fact p.Prime], 5 ≤ p → ∀ n (A : Matrix (Fin n) (Fin n) (ZMod p)),
  A.det ≠ 0 → HasAJTVector A
```

- `n = 0`：`Fin 0` 上唯一矩阵是空矩阵，`HasAJTVector` 在空域上平凡真 → 整句真，但同样是空分支，不影响一般 `n`。
- **域限制是正确的裁剪**：Alon–Tarsi 1989 处理的是非素数模（含 `p=2`、一般 `q`），Nagy–Pach（JEMS 2025）处理 `p > 61, p ≠ 79`，因此题面把 `p` 限定在素数且 `p ≥ 5` 后，**真正未解的只剩 `p ∈ {5,…,61} ∪ {79}`**。这与论文表格的 marking 一致。忠实。
- 已知可参照的机器验证范式：论文 Appendix F.3 / Figure 6 记录 GPT-6 Astra 用「计数恒等式 + 精确整数证书」在 Lean 里验了 `F₅` 上 `n ≤ 9` 的全部情形。这是唯一有先例的「verified special case」路线，但拿不到分。

### 2.3 `bin-packing-mirup`（主攻）

```lean
conj : ∀ {n} (l : Fin n → ℕ) (L : ℕ) (hpos : ∀ i, 0 < l i) (hle : ∀ i, l i ≤ L),
  optNumber l L hle ≤ Nat.ceil (lpVal l L) + 1
```

定义区要点（全部属不可改区）：

- `patterns l L`：个体副本语义，枚举 `Finset (Fin n)` 的幂集并按 `Σ l i ≤ L` 过滤；
- `lpVal l L := sInf {v | 存在非负权重覆盖每件 ≥1 次且总量 = v}`，即配置 LP；
- 两个决策桥：`lpVal_le_of_natCover`（原始证书 → LP 上界）、`le_lpVal_of_natDual`（自然数对偶权重 → LP 下界）。这两个桥是**分数转整数**的关键，否则 `sInf` 没法碰；
- `PacksIn l L k`（可 `decide`，`k^n` 枚举）、`optNumber`（`Nat.find`）、`packsIn_self`、`optNumber_le_of_packsIn`、`le_optNumber_of_not_packsIn`、`le_optNumber_of_pairwise_incompatible`、`lpVal_le_optNumber`；
- 固定区末尾给了 `maxRecDepth 1000000`、`maxHeartbeats 8000000`，以及实例 `instB1/B2/B3/instC`。

退化检查：

- `n = 0`：`optNumber = 0`、`lpVal = 0` → `0 ≤ 0 + 1` ✓ 真；
- `n = 1`：`LP = 1 = OPT` ✓；`n = 2` 亦平凡 ✓；
- 整数化无损：LP 关于尺寸整体缩放齐次，题面的整数尺寸不损失一般性；
- `Nat.ceil` 与「个体副本 + 至少覆盖一次」的口径匹配：LP = 3 时 `⌈LP⌉ = 3`。

⇒ **忠实，且没有退化漏洞可钻**。要拿分只能真造一个 `OPT ≥ ⌈LP⌉ + 2` 的显式实例。

---

## 3. 前沿状态（2026-11-15 的事实核查）

### 3.1 Aaronson–Ambainis：已被证明

- arXiv:2611.09773《A proof of the Aaronson–Ambainis conjecture》（David Turturean，2026-11-06）；
- Scott Aaronson 博客《Aaronson–Ambainis Conjecture proved!》（2026-11-10）。

也就是说题面「open」的标注已经过时。但这不改变评分：槽位要的是 Lean 证明，而该证明的体量远超一次会话。

### 3.2 MIRUP：已被反证，而且 benchmark 里有人靠它拿了 3/3

论文 §5.6 明写：OpenAI 在 2026 年公开了「bin packing 的配置 LP 间隙无界」这一结果（引用条目 `OpenAI. Bin packing and unbounded configuration-LP gaps. Mathematics repository, Lean formalization documentation, 2026b`，即 GitHub 上 `openai/math` 的 `lean/docs/118.md`），**Kimi K3.1 Pro / DeepSeek 1017 检索到这份公开材料后，把它改写成题目定义层的形式，拿到 accepted refutation**（MIRUP 3/3；Ryser 另有 1/3 与 2/3）。

对应预印本：《Additive hardness and unbounded configuration gaps in bin packing》（OpenAI, 2026-09-24）。核心定理（Theorem 1.2）：对**每个**整数 `c ≥ 0`，存在装箱实例与整数 `B`，使

- 每件尺寸 ∈ (1/6, 1)（因此每箱最多 5 件）；
- `OPT_LP = B`（数值型与个体副本型 LP 值都等于 `B`，这正是本题定义层的口径）；
- `OPT(I) > B + c`。

取 `c = 1` 即 `OPT ≥ B + 2 = ⌈LP⌈ + 2`，MIRUP 假。

> 另外，`openai/math` 里的 Lean 文件 `lean/ComparatorChallenges/BinPackingGap.lean` 我也抓下来了：它形式化的是**抽象**版本（图灵机/NP 复杂度 + `CookLevin` 风格的命题），**不含任何显式实例**。这对本题是决定性的一点——详见 §4。

### 3.3 Alon–Jaeger–Tarsi：只剩有限多个素数域

Nagy–Pach 的论文覆盖 `p > 61, p ≠ 79`；2026 年另有宣称「closing the permanent-rank boundary」的工作（arXiv:2608.19158）。剩余集合仍是有限枚举性质，但每个 `p` 都要独立的组合论证 + 机器验证，不是一次会话能填的。

---

## 4. 核心障碍：为什么公开反例「搬不进」槽位

这是本次最实质的发现，值得单独定量说明。预印本 Theorem 3.1（图 → 装箱归约）的参数（逐字取自 PDF 第 3 节）：

```
P₀ = 100¹¹ ,  K = 25(c+1)(1+5P₀) ,  d ≥ max{72K, 120K/ρ}
R = 100(P + nK + 1) ,  g = 1/(16(R+1)^m)
b(e,j) = 1/2 + g·H(e,j) ,  θ_e = (R+1)^{e-1} − 1
输出：整数 B 与 5B 个有理尺寸 ∈ (1/6,1)
```

代入 `c = 1`：`K ≈ 1.25 × 10¹³`，`R ≈ 10¹⁵ · n`，`g` 的分母量级是 `(10¹⁵)^{m}`（`m = |E|`，输入图至少一条边，实际构造里 `m` 是几十到上百）。于是

1. **尺寸的二进制编码长度本身就是天文数字**。题目槽位要 `l : Fin n → ℕ`，即每个尺寸必须是**写下来**的自然数；这里每个尺寸的分子分母都有 `10^{15m}` 位数量级，写进 Lean 文件是不可能的（文件本身会超过宇宙原子数）。

2. **即使能写下来，内核也判不动**。本题两条可判定路径：
   - `lpVal` 上界：用 `lpVal_le_of_natCover`，但 `patterns` 是 `2^n` 个模式，`decide` 要枚举 `2^n`；`n = 5B`，`B` 至少几百 → 无望。理论上可以像 §5.3 那样用 `Finset.sum_subset` 只对支撑集求和绕过枚举，但前提是证书本身可写。
   - `PacksIn`：`k^n` 枚举，`n ≥ 1000` 时彻底无望；并且**否证** `PacksIn`（即证明 3 箱/若干箱装不下）在 Lean 里是 `decide` 唯一可行的方式，除非手写组合论证。

3. **反例的「无界性」是渐近的**。定理给的是「对每个 c 存在实例」，最紧的实例族参数随 `c` 增长；要拿到 `OPT ≥ ⌈LP⌉+2` 只需 `c=1`，但构造里 `n = 5B` 而 `B` 由图的顶点覆盖难度决定——需要一张「顶点覆盖数远大于其 LP 松弛」的图，最小可用 gadget 已经不小。

**结论**：这条公开路径在 benchmark 语境下能拿分，是因为提交者把「无界间隙」这个**定性命题**重新形式化（而不是实例化具体数字）。本题槽位是**定量的整数实例**，堵死了这条路。

---

## 5. 我实际做了什么

### 5.1 独立计算管线（不依赖论文）

`bpp.py`：模式枚举（子集和）→ HiGHS 解 LP（`linprog`）→ 整数最优（`milp`，`mip_rel_gap=0`）→ 自写 `Fraction` 单纯形（对偶形式）做**精确**复核 → 转成 Lean 可用的自然数证书。

自检（`python3 bpp.py`）：

```
patterns: 224   volume: 241/81
LP (float): 3.000000000000001
OPT (MILP): 4
ceil(LP)+1 = 4
```

### 5.2 题面给的三个实例的复算

| 实例 | 尺寸 / L | LP | OPT | ⌈LP⌉ |
|---|---|---|---|---|
| `instB1` | `[6,4,4,3,3]`, L=12 | 9/5 | 2 | 2 |
| `instB2` | `[7,7,7,7]`, L=12 | 4 | 4 | 4 |
| `instC` | `[4,6,6,9,16,29,32,37,40,62]`, L=81 | **3（精确）** | **4** | 3 |

`instC` 与题面注释一致：`OPT = ⌈LP⌉ + 1`，**IRUP（`OPT ≤ ⌈LP⌉`）在此失败，而 MIRUP 的 `+1` 恰好紧**。这不是「反例」，恰恰是「猜想的最优点」，说明了为什么找不到 `+2` 就一点用都没有。

### 5.3 机检验证（Lean 4 + mathlib，在题目定义层内）

在**不修改固定区**的前提下，我在 `-- END OF FIXED PART` 之后新增 `namespace InstC`，把 `instC` 的全部算术用内核验了一遍（不使用 `native_decide`、不新增 `axiom`）：

| 定理 | 内容 | 手段 |
|---|---|---|
| `coverX_covers` | 8 个模式权重（分母 3）覆盖每件 ≥ 3 次 | `decide` |
| `coverX_total` | 权重和 = 9 = 3·3 | `decide` |
| `lpVal_le_three` | `lpVal instC 81 ≤ 3` | `lpVal_le_of_natCover` |
| `dualW_patterns` | 对偶权重 (1,2,2,3,6,10,11,13,14,22) 每个模式 ≤ 28 | `decide` |
| `dualW_total` | 对偶权和 = 84 = 3·28 | `decide` |
| `three_le_lpVal` | `3 ≤ lpVal instC 81` | `le_lpVal_of_natDual` |
| `lpVal_eq_three` | **LP 值精确等于 3** | `le_antisymm` |
| `packsIn_four` | 显式 4 箱分配 `[0,0,0,1,3,0,0,1,2,3]` | `decide` |
| `not_packsIn_three` | **3 箱不可行**（`3^10` 全枚举） | `decide` |
| `optNumber_eq_four` | **整数最优 = 4** | 两个桥引理 |
| `ceil_lpVal` | `Nat.ceil 3 = 3` | `Nat.ceil_natCast` |
| `IRUP_fails` | `⌈LP⌉ < OPT` | 改写 |
| `mirup_tight` | **`OPT = ⌈LP⌉ + 1`** | 改写 |
| `lpVal_lt_optNumber` | `LP < OPT`（实数层） | 改写 |

编译环境严格对齐题包：工具链 `leanprover/lean4:v4.33.0-rc1`，mathlib 取同 tag（`79d0395a…`），其余依赖 rev 沿用题包自带 `lake-manifest.json`。编译与公理审计结果见 §7。

**这组定理的意义**：它把「MIRUP 的常数 1 不可改进」这件事变成了内核事实，也验证了题目定义区的两个证书桥确实可用——也就是说，**如果**有人造出 `OPT ≥ ⌈LP⌉+2` 的实例，代码骨架已经现成，只差实例和 `¬PacksIn` 的论证。

### 5.4 反例搜索（结果不理想，如实记录）

`search.py` / `search2.py` / `stats.py` 用 MILP 求精确 OPT、HiGHS 求 LP，族包括：`instC` 的缩放/扰动/追加小件、随机尺寸落在 `(L/6, L]`、少量不同尺寸高重复、`L/q ± ε` 网格。

- 第 1 轮 18,300 例，229 s：`OPT ≥ ⌈LP⌉+2` 命中 **0**；
- 第 2 轮 18,350 例，334 s：命中 **0**；
- 补充统计 2,500 例的间隙分布：**全部是 `OPT − ⌈LP⌉ = 0`**。

第三项统计其实是**对搜索本身的否定性结论**，值得说清楚：这些族类全是体积主导的（volume ≈ LP），连 `gap = 1` 都造不出来。`instC` 这类 IRUP 反例靠的是「尺寸落在 `(L/3, L/2]` 造成两两不兼容 + 特定三元组可兼容」的精细结构，随机扰动打不中。换言之：**39,150 例的「0 命中」并不能作为猜想为真的证据，只能作为「朴素搜索无效」的证据**。

顺带一个有用的分析：在「每箱最多 2 件」的区域，配置 LP 就是边覆盖 LP，其整性间隙在每个奇连通分量上至多 1/2，要攒出 `+2` 必须有**多个奇分量**；而「奇分量」需要不相容关系，不相容需要尺寸和 > L，这与「分量内两两相容」直接冲突——这就是为什么这类简单结构天然到不了 `+2`，也是 OpenAI 构造为什么需要 `P₀ = 100¹¹` 这种「分数/评级」机制来强制 5 元组模式。

---

## 6. 通向满分的三条路线（含工作量估计）

### R1（唯一有希望拿分）把 OpenAI 构造做参数压缩后再实例化

思路：`P₀` 的作用是「一个足够大的整数，使得违反模式约束会被分数惩罚压过」。它不必是 `100¹¹`，可以是**任何经验证足够大的整数**（例如 10⁶）。做法：

1. 复现 Table 1 的五元组 gadget（顶点侧 vs 边侧分数表），用脚本生成显式图（比如一个小顶点覆盖难例，n ≈ 30–60）；
2. 用参数搜索把 `P₀`、`K`、`d` 压到可计算规模，同时用 MILP 验证 `OPT_LP = B` 且 `OPT > B+1`；
3. Lean 端：LP 上界用支撑集技巧（`Finset.sum_subset` + 只在 8 个模式上求和，避开 `2^n`）；`¬PacksIn` 需要**抽取论证**（从任何 `B+1` 箱的装箱里抽出顶点覆盖 ≤ k），按 `instC` 的证明风格手写，估计 300–600 行。

诚实评估：步骤 1–2 是「工程 + 搜索」，可能一两天；步骤 3 是本任务的真正瓶颈，且失败率高（形式化一个组合抽取论证通常在 3–10 倍于纸面证明的篇幅）。

### R2 目标化搜索（用对偶可行函数引导）

不要随机搜，而是搜「使 LP 对偶间隙最大」的结构：以 `OPT − ⌈LP⌉` 为目标函数做局部搜索，用 DFF（dual feasible function）引导尺寸网格（已知 `f(x) = x`（对 `x ≤ 1/2`）、`f(x) = 1/2`（对 `x > 1/2`）这类非加性 DFF 是构造下界的标准手段）。规模 `n ∈ [15,40]`。成功概率未知，成本低（几小时算力）。

### R3 结构化特例（拿不到分，但有内容）

在 Lean 里证 MIRUP 的**可证子类**：`n ≤ 2`、全等尺寸（`OPT = ⌈n/L⌉ = ⌈LP⌉`）、`l i ≤ L/3`（每箱 ≥ 3 件，间隙同样 ≤ 1）等。这类定理能给出「猜想成立的区域图」，但槽位仍然空着。

---

## 7. 环境与复现

```bash
# 工具链（题包 pin 的版本，手动装入 elan toolchain 目录）
~/.elan/toolchains/leanprover--lean4---v4.33.0-rc1/bin/lean --version
# Lean (version 4.33.0-rc1, commit 62eed1db4d67, Release)

# mathlib 取同 tag
cd /home/user/leanlib/mathlib4-433 && lake exe cache get   # 9112 个 olean

# 编译题目工程（含 InstC 验证段）
cd work/app433 && lake build Task
```

踩坑记录（省得复现者再撞一遍）：

1. `elan toolchain install` 反复失败（partial file / release 解析错误）→ 直接下 GitHub release 的 `lean-4.33.0-rc1-linux.tar.zst`，用 `pip install zstandard` 解包（系统无 `zstd`、apt 也没有该包）；
2. 先试过 mathlib **master + 4.36.0-rc2**：`lake build` 在 Batteries 上大面积报错（`UInt8.max_def has already been declared`、`BitVec.toNat_pow` 重复声明、`dif_pos` 弃用告警「updated constant has a different type」）——**工具链与 Batteries rev 不匹配**。教训：mathlib 必须用与题包 `lean-toolchain` 同 tag 的版本，别图新；
3. `/opt` 在 9.8G 根分区，7.2G mathlib 缓存直接撑爆（`No space left on device` 会伪装成「解包不完整」，表现为 `libInit_shared.so` 缺失）→ 库全部放 `/home/user` 大分区。

---

## 8. 随附文件

| 文件 | 说明 |
|---|---|
| `Task_Basic_verified.lean` | 完整题目文件 + `namespace InstC` 的机检段（固定区未改） |
| `build.log` | `lake build Task` 输出（含公理审计结果） |
| `certificates.json` | LP 原始/对偶证书、4 箱分配、间隙统计，机器可读 |
| `bpp.py` / `search.py` / `search2.py` / `stats.py` | 计算与搜索脚本（可独立复跑） |
| `search.log` / `search2.log` / `gap_stats.json` | 搜索日志与间隙分布 |

---

## 9. 一句话总结

三道开放猜想的形式化都忠实到没有缝隙；AA 与 AJT 是「知道答案也搬不进 Lean」的研究级体量；MIRUP 虽然已被（非构造性地）反证，但公开构造的分母是 `(10^15)^m` 级的，**无法变成槽位要的整数尺寸表**。本次能确证的最强事实是：**MIRUP 的 `+1` 在 `instC` 上恰好紧，且这已在内核中验完**——任何声称改进该常数的工作，都必须先越过这一条。
</content>
