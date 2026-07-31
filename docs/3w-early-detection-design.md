# Silver & Gold design for early detection of undesirable events (3W v2.0.0)

**Status:** proposal · **Target:** PR #24 (`feat/glue-3w-transform-job`) and the follow-on Gold job
**Scope:** what Silver must clean and flag, what Gold must contain, and how the experiment must be split and evaluated so the results mean something.

All statistics below were measured directly on the local copy of the dataset (`3w-dataset/2.0.0`, 2,228 Parquet files, 76,587,318 observations, 1.8 GB Brotli-compressed), not taken from the literature.

---

## 1. Summary

The current `silver-transform` job is a *conforming* step: it stages the archive, casts sensors, derives `instance_id` / `well_id` / `source_type` from the filename, and passes labels through untouched. That is the right shape and the filename-derived metadata is exactly the right instinct. But between the Silver output as it stands today and a defensible early-detection model there are five properties of this dataset that will silently produce excellent, meaningless results.

The recommendation in one line: **Silver becomes lossless-but-annotated (clean values, keep an audit trail, never delete a row), Gold becomes a windowed early-detection table with a per-class prediction horizon and a pre-baked, well-disjoint split assignment.**

The single most important design decision in this document is §3.4 — the split — because it is the one that cannot be fixed after the fact by retraining.

---

## 2. Measured dataset profile

| Property | Value |
|---|---|
| Files / observations | 2,228 / 76,587,318 |
| Sources | real 1,119 files (32.9M obs) · simulated 1,089 (40.7M) · hand-drawn 20 (3.0M) |
| Distinct real wells | 40 (`WELL-00001`–`WELL-00042`, no 17/18) |
| Sampling | exactly 1 Hz — **0 gaps, 0 duplicate timestamps across all 2,228 files** |
| Time span | 2011-08-30 → 2023-09-26 |
| Columns | 27 sensors + `class` + `state` + `timestamp` index |
| Rows per file | median 26,999 · min 5,215 · max 768,314 |
| Unlabelled observations | 4,028,400 (5.26%), `class` is NULL — in **every one** of the 1,119 real files, and in no simulated or hand-drawn file |

**Observation-level label distribution**

| Steady label | Obs | % | | Transient | Obs | % |
|---|---|---|---|---|---|---|
| 0 Normal | 17,305,269 | 22.60 | | 101 | 5,265,821 | 6.88 |
| 1 Abrupt increase of BSW | 2,909,887 | 3.80 | | 102 | 146,691 | 0.19 |
| 2 Spurious closure of DHSV | 366,858 | 0.48 | | 105 | 2,423,367 | 3.16 |
| 3 Severe slugging | 4,834,079 | 6.31 | | 106 | 1,558,565 | 2.04 |
| 4 Flow instability | 2,454,883 | 3.21 | | 107 | 8,714,480 | 11.38 |
| 5 Rapid productivity loss | 10,553,279 | 13.78 | | 108 | 5,093,397 | 6.65 |
| 6 Quick restriction in PCK | 3,879,083 | 5.07 | | 109 | 2,967,445 | 3.88 |
| 7 Scaling in PCK | 138,148 | 0.18 | | NULL | 4,028,400 | 5.26 |
| 8 Hydrate in production line | 744,061 | 0.97 | | | | |
| 9 Hydrate in service line | 3,203,605 | 4.18 | | | | |

Note there are no transient labels `103` or `104` anywhere in the dataset — consistent with §3.1.

`state` is the well operating condition (valve configuration; NaN = Unknown, per the 3W 2.0.0 data article). In this snapshot it is non-constant in **only 12 of 2,228 files** — 11 in class 8 plus one class 0 instance. Treat it as a niche annotation, not a general feature; do not build it into the Gold feature set.

---

## 3. Five findings that constrain the design

### 3.1 Classes 3 and 4 have no "before" — they are outside the early-detection problem

| | files | obs | instances with a normal period | instances with a transient label |
|---|---|---|---|---|
| Class 3 (severe slugging) | 106 | 4,949,279 | **0 / 106** | **0 / 106** |
| Class 4 (flow instability) | 343 | 3,689,683 | **0 / 343** | **0 / 343** |

Every observation in all 449 of these files is already labelled as the fault. There is no onset to anticipate and no transient annotation to learn from. Class 4 alone is 343 files — 31% of all real instances — so this is not a rounding error.

**Implication:** the Gold early-detection table must exclude classes 3 and 4 (`8,638,962` observations, 20% of the corpus). They remain perfectly valid for a *state-recognition* task ("is this well slugging right now?"), which is a different Gold view with a different schema. Silver keeps them; Gold's early-detection view filters them out and records why.

One tempting alternative is worth ruling out explicitly, because a reviewer will raise it: flow instability (4) is documented as a precursor that may escalate into severe slugging (3), which sounds like a natural early-detection target. It cannot be built from this data — each file carries exactly one class label, so no instance records a 4 → 3 transition. Say so rather than leaving it unaddressed.

### 3.2 Simulated instances leak the label through elapsed time

The onset timing in simulated instances is not merely regular — it is very nearly constant:

| Class | Simulated files | Distinct normal-prefix durations | Distinct warning-window durations |
|---|---|---|---|
| 1 | 114 | **1** | 4 |
| 2 | 16 | **1** | **1** |
| 5 | 439 | **1** | 10 |
| 6 | 215 | 2 | 4 |
| 8 | 81 | **1** | 13 |
| 9 | 150 | 3 | 6 |

All 439 simulated class-5 instances begin their transient at exactly t = 500 s. All 114 simulated class-1 instances at t = 6,000 s. All 16 simulated class-2 instances at t = 3,600 s. Class 6 is 211 instances at 1,800 s and 4 at 1,799 s; class 9 is 146 at 6,000 s and 4 others.

**Implication:** any feature that encodes position within the instance — a row index, `timestamp - min(timestamp)`, a cumulative counter, even an unshuffled window ordinal — achieves near-perfect accuracy on simulated data while learning nothing about well physics. This must be an explicit, documented prohibition in the Gold feature contract, not an assumption. It is also the reason simulated instances cannot be scored in the same fold as real ones and have the result reported as one number.

### 3.3 Real and simulated warning windows disagree by an order of magnitude, in both directions

Warning window = seconds from first transient observation to first steady-fault observation. This is precisely the quantity an early-detection model is asked to predict, so a shift here is a shift in the *target*, not just the features.

| Class | Real: n / median | Simulated: n / median | Ratio |
|---|---|---|---|
| 1 | 4 / 9,818 s | 114 / 50,400 s | sim **5.1×** longer |
| 2 | 11 / 5,149 s | 16 / 3,600 s | real 1.4× longer |
| 5 | 7 / 9,180 s | 439 / 4,800 s | real 1.9× longer |
| 6 | 6 / **736 s** | 215 / **7,200 s** | sim **9.8×** longer |
| 8 | 12 / 174,148 s | 61 / 13,250 s | real **13.1×** longer |
| 9 | 3 / 6,201 s | 150 / 18,360 s | sim 3.0× longer |

Class 6 (quick restriction in the production choke) is the sharpest case: real wells give a median of **12 minutes** of warning; the simulator gives **two hours**. A horizon tuned on simulated class 6 is off by an order of magnitude in the direction that matters.

**Implication:** simulated data is usable for pre-training, augmentation and sanity checks, but the horizon (§4.2) and every headline metric must be derived from and reported on **real instances only**. Report simulated results separately and never pooled.

### 3.4 The real early-detection corpus is 48 instances, and well identity nearly determines the class

Instances that contain *both* a transient and a subsequent steady fault — the only ones that can teach or test lead time:

| Class | 1 | 2 | 5 | 6 | 7 | 8 | 9 | **Total** |
|---|---|---|---|---|---|---|---|---|
| Real | 4 | 11 | 7 | 6 | 5 | 12 | 3 | **48** |
| Hand-drawn | 6 | – | – | – | 4 | – | – | 10 |

Forty-eight. That is the whole real corpus, and it governs everything: 76.6M observations is a storage problem, not a statistical one. The effective sample size is closer to 48 than to 76 million, and any evaluation that reports per-observation accuracy over millions of rows is reporting the size of the files, not the strength of the evidence.

Worse, the class is nearly readable from the well ID:

- Class 7 real: `WELL-00021` (2), `00022` (8), `00023` (4), `00024` (19), plus `00001` (1), `00006` (2)
- Class 8 real: `WELL-00019` (4), `00026` (3), and `00025`/`00027`/`00028`/`00029`/`00030`/`00031`/`00032` (exactly one instance each)
- Class 9 real: `WELL-00033`–`00042`, plus `00010`, `00014`, `00015`, `00016`, `00020`
- Class 0 normal: dominated by `WELL-00001`, `00002`, `00005`, `00006`, `00008`

`WELL-00025` through `WELL-00032` contribute exactly one file each and appear in no other class. Under a random or per-file split, windows from the same well land on both sides of the split, so a model can reach a high score by recognising a well's baseline pressure offset rather than any fault dynamics. This is the standard identity-leakage failure and it is not hypothetical here — the well ID is close to a sufficient statistic for the label. (Quantify it before you rely on the argument: train a classifier on `well_id` alone and report its accuracy. That number belongs in the thesis.)

The official 3W folds (`folds_clf_*.csv`) are, by the project's own description, *random but fixed for reproducibility*. Fixed is not the same as leakage-free. Reproducing them is the right way to compare against published numbers; it is not a substitute for a well-disjoint split.

**Implication — the split protocol.** Use **two** reported settings, always both:

- **Setting A — official folds.** Reproduce the 3W fold files exactly. This is your comparability baseline against the literature. Label it as such and expect it to be optimistic.
- **Setting B — leave-one-well-out (primary).** Group by `well_id`; no well appears in both train and test. This is the number that estimates performance on the next well. Expect it to be substantially worse, and say so.

Setting B has a real cost that must be stated rather than engineered around: for classes 7, 8 and 9 there is almost no well that contributes both normal and faulted data, so a well-disjoint fold gives the model no in-well normal baseline. That is not a flaw in the protocol — it is the honest difficulty of the problem, and it is the most interesting thing you can write about in the thesis. Handle it by normalising each instance against **its own leading normal window** rather than against global per-well statistics, so the model sees deviation-from-baseline instead of absolute level.

**Assign the split in Gold, materialise it as a column, and never compute it in a notebook.** A `split_setting` / `fold_id` pair written by the Gold job is the only way to guarantee that every experiment, every author and every re-run uses the same partition.

### 3.5 Corrupt sentinels, frozen sensors, and missing-by-design channels

**Corrupt values.** `P-PDG` reaches **−1.18 × 10⁴²** and `T-PDG` reaches **−1.71 × 10³⁸**. These are instrument error sentinels, not measurements. `P-TPT` reaches 2.94 × 10⁹ Pa (≈ 2,942 MPa; subsea wellhead pressures are tens of MPa). `ABER-CKP` — a percentage opening — ranges −99.99 to 100.4.

Out-of-physical-range observations, real instances only, using bounds of `[0, 6×10⁷]` Pa for pressures, `[0, 200]` °C for temperatures and `[0, 100]` % for valve openings:

| Variable | Out of range | % of real obs | Files |
|---|---|---|---|
| T-PDG | 2,445,048 | 7.44 | 36 |
| T-TPT | 1,533,353 | 4.67 | 8 |
| P-JUS-CKGL | 1,299,132 | 3.95 | 85 |
| P-PDG | 1,200,682 | 3.65 | 33 |
| P-TPT | 1,152,036 | 3.51 | 11 |
| P-ANULAR | 387,650 | 1.18 | 3 |
| ABER-CKP | 161,872 | 0.49 | 2 |

Those bounds are a starting proposal, not physics — the temperature floor in particular is a judgement call (`T-TPT` reaches −33.75 °C, implausible for produced fluid but not absurd as a sensor drifting cold). Pin the final bounds in config, log the rejection count per variable per run, and treat a sudden change in that count as a data-quality alarm.

> **Concrete bug in the current handler.** `transform()` casts every sensor with `F.col(sensor).cast("float")` — Spark `float` is float32, max ≈ 3.40 × 10³⁸. The `P-PDG` sentinel of −1.18 × 10⁴² **overflows and becomes `-Infinity`**: 305,679 observations across 3 files. Downstream, any mean, standard deviation or scaler touching those partitions returns `NaN`/`Inf` and poisons every window in the file. Float32 itself is fine — round-trip error on a 1.01 × 10⁷ Pa `P-TPT` sample is 0.000 Pa — so the fix is to clip sentinels to NULL *before* the cast, not to abandon float32.

**Frozen sensors.** Median fraction of consecutive-identical readings, real instances: `P-PDG` 100%, `T-PDG` 100%, `QGL` 100%, `ABER-CKP` 59%, `P-ANULAR` 44%, `P-JUS-CKGL` 39%. Longest single frozen run: **768,314 s (8.9 days)**. Rolling-variance features on these channels are identically zero, and a "sensor stopped updating" event is itself diagnostic — it should become a feature, not be silently averaged away.

**Missing by design — and the NULL pattern leaks the class.** Four columns are 100% NULL across all 2,228 files: `P-JUS-BS`, `P-MON-SDV-P`, `PT-P`, `QBS`. `P-MON-CKGL` appears only in class-8 real instances. Real instances carry 17–22 channels; simulated instances carry 5–7, and **the set differs by class**:

| Group | Channels | Set |
|---|---|---|
| Simulated 1, 2, 3, 8 · all hand-drawn | 5 | `P-MON-CKP`, `P-PDG`, `P-TPT`, `T-JUS-CKP`, `T-TPT` |
| Simulated 5 | 7 | above + `P-JUS-CKP`, `T-MON-CKP` |
| Simulated 6 | 6 | `P-JUS-CKP`, `P-MON-CKP`, `P-PDG`, `P-TPT`, `T-JUS-CKP`, `T-MON-CKP` — **no `T-TPT`** |
| Simulated 9 | 7 | `P-JUS-CKGL`, `P-MON-CKP`, `P-PDG`, `P-TPT`, `QGL`, `T-JUS-CKP`, `T-TPT` |

Only **four** channels are common to every simulated class: `P-MON-CKP`, `P-PDG`, `P-TPT`, `T-JUS-CKP`. Simulated class 6 is the only group in the entire dataset with no `T-TPT`; simulated class 9 is the only simulated group with `QGL` and `P-JUS-CKGL`. So among simulated instances, **a NULL-indicator mask alone identifies classes 6 and 9 perfectly** — no sensor values required. This is a second, independent leakage channel on top of §3.2, and it also caps the honest feature set for any real+simulated joint model at those four channels.

---

## 4. Proposed design

### 4.1 Silver — clean, flag, never drop

Silver stays one row per observation, one-to-one with Bronze. Nothing is filtered. Three column families:

**(a) Conformed values** — the 23 sensors that are not all-NULL, cast to float32 **after** sentinel handling, plus `class`, `state`, `timestamp`.

**(b) Identity and provenance** — `instance_id`, `well_id`, `source_type`, `folder_class` (keep the existing derivation; it is correct), plus `bronze_key` and `silver_run_id` so any row can be traced to the archive and job run that produced it.

**(c) QC flags** — one `qc_<sensor>` byte per sensor, bit-packed or as a small struct, recording *why* a value was changed:

| Rule | Action | Flag bit |
|---|---|---|
| `abs(v) > 1e10` (instrument sentinel) | → NULL | `SENTINEL` |
| Pressure outside `[0, 6e7]` Pa | → NULL | `OUT_OF_RANGE` |
| Temperature outside `[0, 200]` °C | → NULL | `OUT_OF_RANGE` |
| Opening (`ABER-*`) outside `[0, 100]` % | clamp | `CLAMPED` |
| Value identical to previous ≥ 300 s | keep value | `FROZEN` |
| Column all-NULL for this `source_type` | — | `ABSENT_BY_DESIGN` |

Rationale for NULL rather than impute: imputation is a modelling decision and belongs in Gold, where it is part of an experiment that can be ablated. Silver's job is to make it impossible to *accidentally* consume a sentinel. The flags mean nothing is lost — a reviewer can reconstruct the raw distribution by reading Bronze, and can reconstruct *what changed* without leaving Silver.

Add two instance-level derived columns while the data is already in memory, because both are expensive to recompute later and both are needed by every downstream consumer:

- `obs_index` — 0-based position within the instance. **Stored deliberately so it can be audited and excluded**, never as a model input (§3.2). Name it something a reviewer will notice, e.g. `obs_index__do_not_use_as_feature`.
- `seconds_to_fault` — signed seconds until the first steady-fault observation of the instance, NULL for class 0 and for classes 3/4. This is the raw material for the Gold horizon.

**Partitioning.** Current: `partitionBy("folder_class")` alone → 10 partitions, badly skewed (class 5 = 402 MB, class 2 = 18 MB). Change to `partitionBy("source_type", "folder_class")`. This makes "real only" a partition prune rather than a full scan, which matters because §3.3 means you will read real-only far more often than you read everything.

### 4.2 Gold — windowed early detection with a per-class horizon

**Problem statement.** For a sliding window ending at time *t*, predict whether a steady fault of class *c* will begin within horizon *H(c)*. Positive = the window ends inside the transient; negative = the window ends during confirmed normal operation. Windows overlapping a labelling gap (`class` NULL) are excluded and counted.

**Per-class horizon.** A single global horizon is wrong by an order of magnitude in both directions (§3.3). Derive `H(c)` from the **real** warning-window distribution, rounded *down* to an operationally meaningful unit — a horizon that most real instances can actually support beats one tuned to the median, because a horizon longer than the median means the majority of positives have no observable precursor at all:

| Class | Real median warning | Suggested `H(c)` | Operational reading |
|---|---|---|---|
| 2 spurious DHSV closure | 5,149 s | 1 h | fast, valve-driven |
| 6 quick restriction in PCK | 736 s | **10 min** | the hard one — very little warning |
| 5 rapid productivity loss | 9,180 s | 2 h | |
| 9 hydrate in service line | 6,201 s | 1 h | only 3 real instances |
| 1 abrupt BSW increase | 9,818 s | 2 h | only 4 real instances |
| 7 scaling in PCK | 43,224 s | 6 h | slow, gradual |
| 8 hydrate in production line | 174,148 s | 24 h | slow; 12 real instances |

Publish `H(c)` in config, not in code. It is an experimental parameter and reviewers will ask you to vary it.

**Windowing.** 1 Hz native. Suggested starting point: 60-observation windows, stride 10 for positives and stride 60 for negatives — a wider negative stride rebalances the classes while preserving temporal coverage, which post-hoc random downsampling does not. Windows must not cross an `instance_id` boundary. Measure the resulting positive/negative ratio per class and record it in the run log; with only 48 real instances it will vary a lot between classes.

**Feature families.** Per sensor, per window: last value, mean, std, min, max, linear slope, first-vs-last delta, count of QC-flagged observations, fraction frozen. Plus cross-sensor ratios that carry physics — e.g. `P-TPT − P-MON-CKP` (drawdown across the choke) and `T-TPT − T-JUS-CKP` — because those survive the per-well offset that a leave-one-well-out split punishes.

**Baseline normalisation (important, see §3.4).** Normalise each window against the instance's own leading normal segment (mean and std of the first *N* confirmed-normal seconds) rather than against global or per-well statistics. This is what makes a model transfer to a well it has never seen, and it is computable causally, so the same code works in a streaming scorer later.

**Prohibited features — write this into the Gold job as an assertion, not a comment:** `obs_index`, absolute `timestamp`, anything derived from `seconds_to_fault` other than the label itself, `folder_class`, `instance_id`, `well_id`, and **any NULL-indicator / missingness mask**, since per §3.5 that mask alone identifies simulated classes 6 and 9. If a joint real+simulated model is trained at all, restrict it to the four channels common to every simulated class (`P-MON-CKP`, `P-PDG`, `P-TPT`, `T-JUS-CKP`).

**Gold schema (one row per window)**

```
window_id, instance_id, well_id, source_type, folder_class,
window_start_ts, window_end_ts,
<feature columns>,
label,                  -- 1 if a steady fault begins within H(class)
seconds_to_fault,       -- NULL for negatives; for analysis, not a feature
horizon_s,              -- H(c) used, so the table is self-describing
split_setting,          -- 'official_folds' | 'leave_one_well_out'
fold_id,
qc_window_flags         -- counts of sentinel/frozen/imputed obs in window
```

Partition by `split_setting`, `source_type`, `folder_class`.

---

## 5. Evaluation protocol

Per-observation accuracy is the wrong metric and will read as naïve. With 48 real instances, report:

1. **Instance-level detection rate** — fraction of faulted instances detected at all before onset. Denominator 48, stated explicitly.
2. **Detection delay / lead time** — distribution of (fault onset − first alarm), per class, as a distribution and not a mean. This is the number an operations engineer cares about.
3. **False alarms per well-day** on class 0 instances. Not "false positive rate": an operator experiences alarms per unit time, and 594 normal instances give a usable denominator.
4. **Both split settings, side by side**, with the gap between them discussed rather than hidden.
5. **Real and simulated reported separately**, never pooled (§3.2, §3.3).

Require an alarm to persist for *k* consecutive windows before it counts. Single-window spikes on 1 Hz data are noise, and this one change usually moves false-alarms-per-day by an order of magnitude.

**Two adversarial probes to run first, before any modelling.** Both should be in the test suite, not the notebook:

1. Train on `obs_index` alone. On simulated data it should score near-perfectly (§3.2); on real leave-one-well-out it should be near chance.
2. Train on the NULL-indicator mask alone. On simulated data it should separate classes 6 and 9 perfectly (§3.5).

Both probes are *supposed* to succeed on simulated data — that is the proof the leak exists. The test is that neither succeeds on the real leave-one-well-out fold. If either does, the leakage controls are not working and nothing downstream is trustworthy.

---

## 6. Implications for PR #24 as it stands

The architecture is sound — Bronze/Silver/Gold on S3, Glue for the heavy pass, SSM for config, filename-derived metadata. These are specific, mostly small changes.

| # | Issue | Where | Fix |
|---|---|---|---|
| 1 | `cast("float")` turns the −1.18e42 `P-PDG` sentinel into `-Infinity` (305,679 obs, 3 files) | `threed_w_handler.transform()` | Null out `abs(v) > 1e10` before the cast |
| 2 | No QC or flag columns; Silver is not yet "cleaned and conformed" | `transform()` | §4.1 |
| 3 | Partitioning by `folder_class` alone — 10 skewed partitions, 402 MB vs 18 MB | `PARTITION_COLUMN` | `partitionBy("source_type", "folder_class")` |
| 4 | `_normalise_timestamp()` handles `LongType` epoch-millis, but `conform_parquet_bytes()` already coerces to `us`, so Spark always reads `TimestampType` and the branch is unreachable | `_normalise_timestamp()` | Delete the branch or assert the type; the docstring currently describes behaviour that cannot occur |
| 5 | `mergeSchema=true` reads all 2,228 footers on the driver | `_read_staged()` | You now control staging output; write a uniform schema and drop the option |
| 6 | Staging re-encodes 2,228 files single-threaded on the driver; Brotli→Snappy measured at **1.51× growth** on a 40-file sample, so the staging prefix costs ≈ **2.7 GB** against 1.8 GB of Bronze | `_stage_archive()` | Acceptable at this size, but it is the wall-clock bottleneck and every executor sits idle through it. Parallelise across a thread pool, or split it into its own job so a Spark-side failure does not re-run the unzip. Also consider `zstd` instead of Snappy — Spark-readable, and much closer to Brotli's ratio |
| 7 | `mode("overwrite")` with static partition overwrite wipes the whole output path | `_write()` | Set `spark.sql.sources.partitionOverwriteMode=dynamic` if re-runs should be incremental |
| 8 | `input_file_name()` is correct here but breaks if evaluated after a shuffle | `transform()` | Add a comment pinning it to the scan; a future refactor will otherwise silently blank `instance_id` |
| 9 | Four all-NULL columns carried through the whole pipeline | `EXPECTED_SENSORS` | Keep them in the expected list for version detection, exclude from the output projection |

`MIN_EXPECTED_SENSORS = 15` deserves a note: simulated files legitimately carry 5–7 sensors, so if staging is ever run on a simulated-only archive this warns on every file. Make the threshold depend on `source_type`.

---

## 7. Open decisions

1. **Hand-drawn instances (20 files, 3.0M obs).** They are neither real measurements nor physics simulation. Recommendation: exclude from training and test entirely, keep in Silver, state the exclusion. They inflate class 1 and 7 counts and cannot be defended in either direction.
2. **The 5.26% unlabelled observations.** Recommendation: exclude affected windows and *report the count* — a reviewer will ask, and "we dropped 5.26%" is a fine answer while silence is not.
3. **Classes 3 and 4.** Confirm they are out of the early-detection scope and become a separate state-recognition view, or are dropped from the project entirely.
4. **Class 9's 3 real usable instances.** Arguably below the threshold at which any per-class claim is meaningful. Consider folding hydrate classes 8 and 9 into one "hydrate formation" target (15 real instances), which is also how an operator would treat them.

---

## 8. Sources

- [3W Dataset 2.0.0: a realistic and public dataset with rare undesirable real events in oil wells](https://arxiv.org/abs/2507.01048) — Vargas et al., *Scientific Data* ([DOI](https://doi.org/10.1038/s41597-026-07225-z))
- [petrobras/3W repository](https://github.com/petrobras/3W) — toolkit, `problems/` benchmark definitions, fold configuration files
- [3W_DATASET_STRUCTURE.md](https://github.com/petrobras/3W/blob/main/3W_DATASET_STRUCTURE.md) — file layout, Parquet/Brotli conventions, `Int64` label storage
- [Binary Classifier of Spurious Closure of DHSV — baseline](https://github.com/petrobras/3W/blob/main/problems/01_binary_classifier_of_spurious_closure_of_dhsv/_baseline/main.ipynb) — official 5-fold protocol, fold −1 for simulated data
- All dataset statistics measured directly on `3w-dataset/2.0.0` (2,228 files, 76,587,318 observations)
