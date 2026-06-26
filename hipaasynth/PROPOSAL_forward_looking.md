# PROPOSAL — forward-looking validation additions

**Status: proposal, nothing implemented.** Written during assembly verification (2026-04-18 / 2026-04-23). Your call on each.

This doc has three parts:
- Part A: the reducer replacement (resolving the session-notes flagged gap)
- Part B: three novel validation concepts that extend RIV beyond current state of the art
- Part C: a sequencing suggestion tied to SBIR / Dakota Conference / Dawn Berg proposal timing

---

## Part A — Reducer replacement

### Empirical finding from smoke test

The reducer's described behavior is "floors at 10." The code reads:

```python
while len(current) > 10:
    half = current[:len(current) // 2]
    if self._still_fails(half):
        current = half
    else:
        current = current[len(current) // 2:]
return current
```

Smoke-test verification showed the **actual** output range is roughly **6–10 items**, not exactly 10. The loop exits as soon as `len(current) ≤ 10`, and because the last halving step can shrink an 11-item set into a 5-item or 6-item subset, you land wherever that halving puts you. The "floor" is not 10 — it's data-dependent and effectively somewhere around 5–10.

This matters because the reducer output is intended to become a **regulatory-filing primitive** (see Part B) — and an unprincipled stopping criterion undermines that.

### Three replacement options, tradeoffs explicit

#### Option A-1 — Statistical-power floor (recommended for RIV-Cert)

Compute the minimum subset size that can still **statistically distinguish** model failure from sampling noise, given the evaluator's configured pass threshold.

For a binomial-power calculation against a pass-threshold `p_fail_required` (e.g., "model must fail on < 5% of cohort"):

```
n_min = ceil( (z_{α/2} * sqrt(p*(1-p)) / margin)^2 )
```

where `p` is the observed failure rate, `margin` is the acceptable confidence-interval half-width (e.g., 0.02), and `α` is the significance level (typically 0.05).

**Typical n_min values:**
- Pass threshold 5%, margin 2%, α = 0.05 → n_min ≈ 457
- Pass threshold 5%, margin 5%, α = 0.05 → n_min ≈ 73
- Pass threshold 5%, margin 10%, α = 0.05 → n_min ≈ 19

**Pro:** the shrunk failure set has statistical authority — defensible in regulatory review.
**Con:** floors are higher than 10 for tight margins; the reducer will return larger minimum cohorts.
**Fit:** best for RIV-Cert deliverables where the shrunk set is evidence in a filing.

#### Option A-2 — Exhaustive leave-one-out below threshold

Keep binary-search halving until `len(current) ≤ 20`, then switch to exhaustive leave-one-out: remove each patient in turn, check if the remainder still fails; drop them if yes, keep them if no. Terminates when no single removal leaves a still-failing subset — that's the **true minimum failing set.**

**Pro:** produces the provably minimal failure cohort, which is the strongest possible artifact ("these exact N patients are sufficient to break the model"). Computationally cheap once you're under 20 items — that's at most 190 additional evaluator calls per leave-one-out sweep.
**Con:** slower than pure binary search. Requires confidence that the evaluator is deterministic under re-evaluation (it should be — anchor-rooted generation guarantees this).
**Fit:** best for RIV-Core custom evaluation reports — the deliverable is "this specific 7-patient subset breaks the model."

#### Option A-3 — Hybrid

Binary-search halving down to max(Option A-1, 20), then leave-one-out. Combines statistical validity with genuine minimum. Slightly more complex to explain to auditors than A-1 alone.

### Recommendation

**A-2 as the default**, with an explicit `--statistical-floor` flag that switches to A-1 for cert filings where statistical power is the required property rather than minimality. This gives you both tiers: "minimum failing subset" for Core reports and "statistically-powered failure subset" for Cert filings.

### Deployment note

When replacing the reducer, add a unit test asserting the NEW stopping criterion explicitly. The existing smoke test's reducer check (in `smoke_test.py`) will need its assertions updated to match the new behavior — currently it asserts `len(out) ≤ 10`, which will be wrong after the replacement.

---

## Part B — Novel validation axes

Three extensions to the current 4-axis adversarial framework (missingness / noise / temporal drift / population shift). Each is **new territory** — no existing framework does these. Each could be productized as a distinct RIV tier or as a premium add-on to existing tiers.

### B-1: Axis interaction — combined perturbations

**Problem the current framework has:** each of the 4 adversarial axes runs independently. A model that survives 20% missingness alone and survives σ=0.1 Gaussian noise alone may fail catastrophically when both are applied simultaneously. Clinical production environments **always** combine these — a real EHR has missing labs AND instrument noise AND drift over time AND a shifting patient population.

**What the extension does:** systematic pairwise and triple combinations of the 4 axes, measured at a grid of intensities. For each combination, report the **interaction effect** — the gap between the observed failure rate and the additive prediction from the independent-axis rates.

```
for (axis_i, intensity_i) × (axis_j, intensity_j) in grid:
    observed = failure_rate_on_combined_perturbation
    predicted_additive = 1 - (1 - fr_i) * (1 - fr_j)
    interaction = observed - predicted_additive
```

**Why it sells:** no other validator has this. The number is headline-grade — "Model X degrades 14% more under combined missingness + noise than the additive prediction would suggest." That's the kind of finding that goes into FDA pre-submissions and lands on an institutional review slide.

**Product tier fit:** RIV-Cert premium add-on. $750–$1,250 uplift per cohort tested.

### B-2: Off-label cohort evaluation

**Problem:** clinical AI vendors routinely over-extend their validation claims. A model validated on adult sepsis gets deployed against pediatric patients; a CHF model is used for patients with concurrent COPD; a stroke-triage model runs on patients with undiagnosed comorbid AFib.

**What the extension does:** cross-module evaluation. Run a model whose intended use is X against the cohort for Y, where the cohorts share overlapping comorbidity profiles. Your existing modules already encode these profiles — e.g., stroke patients with CHF comorbidity, OUD patients with HFrEF, diabetes patients with CKD.

Define a set of "contamination pairs":
- stroke × CHF (high comorbidity in real cohorts)
- sepsis × OUD (real ICU population)
- CHF × COPD (real cardio-pulmonary population)
- diabetes × oncology (real chemo-patient population)

For each pair, run the model (intended for axis X) against the cohort generated for axis Y, and report failure rates vs. the on-label baseline.

**Why it sells:** this is the #1 unmodeled clinical-AI failure mode in production. Regulators (FDA SaMD, CE-MDR) are increasingly asking about "intended-use drift." A vendor who can demonstrate that their model degrades gracefully on off-label cohorts has a defensible position; a vendor who hasn't tested it has an unbounded liability.

**Product tier fit:** new tier — **RIV-Scope** ("scope-of-use certification"). Distinct from Cert (which tests intended use) because Scope tests **unintended** use. Pricing suggestion: $3,500–$5,000 per scope-boundary report; premium over Core because the combinatorial testing is more expensive.

### B-3: Calibration drift as a monitoring primitive

**Problem:** clinical AI models drift after deployment — the model's output distribution shifts as the operating-point population drifts from the training population. Current monitoring tools (like MLflow or Evidently) track drift on real production data, which means you detect drift after it's causing harm, using data you can't audit.

**What the extension does:** use the deterministic anchor chain to generate a **time series of synthetic cohorts** representing 1, 3, 6, 12, 18, 24 months post-deployment, each with a controlled drift profile (e.g., "Profile B rural critical-access demographics drifting toward Profile D aging-rural composite at 2%/year"). Re-evaluate the deployed model against each time-point cohort. Plot the output distribution over time.

Because the cohorts are anchor-rooted and deterministic, the auditor can **regenerate any time-point from the seed** and confirm the drift profile was exactly what was claimed. No real-patient data involved.

**Why it sells:** this is the **RIV-Monitor** product line. You already have the raw primitives — deterministic generation + temporal perturbation module. The gap is the synthesis into a monitoring deliverable: a dashboard showing model-output drift against controlled synthetic drift, updated monthly, audit-verifiable.

**Product tier fit:** RIV-Monitor annual subscription. $12,000–$24,000/year per model, 5–10× the per-shot Cert pricing because it's recurring. This is the tier that justifies the air-gapped flash-drive concept — the institution runs it locally, monthly, against their own model.

---

## Part C — Sequencing against your current timeline

Based on your top-of-mind items (Dawn Berg proposal, Phase 2A recovery, Dakota Conference June 3–4, I-Corps → SBIR pathway):

### Near-term (before Dawn Berg proposal)

1. **Decide on the determinism-break path** in `DRAFT_PATCH_determinism_fix.md`. Path A (fix + republish) is the defensible choice for someone building a cert product. If you go that way, disclosure to Debditya and Faiyyaz can piggyback on the v1.1 disclosure thread — same pattern, different fix.
2. **Pick reducer replacement option** (A-2 recommended). This is a ~1-day build given the reducer is ~30 lines. Ship it before Dawn sees anything; she'll ask about statistical power on the shrunk failure sets.
3. **Run the smoke test as part of your standard pre-demo checklist.** `python smoke_test.py --json` produces a machine-readable pass/fail log that's auditor-clean.

### Medium-term (Dakota Conference June 3–4)

4. **Implement B-1 (axis interaction)** as the flagship demo. Interaction effects are headline-grade and nobody else does them. Takes ~3 days on top of the existing adversarial framework.
5. **Draft B-2 (RIV-Scope) as a product concept** but don't build it yet — wait for signal from Dawn or I-Corps conversations. If one FQHC or state office bites on "off-label scope certification," build it against their specific use case as the pilot.

### Longer-term (SBIR Phase I)

6. **B-3 (RIV-Monitor)** is the SBIR Phase I pitch. Recurring revenue, federal-demand-aligned, uses the core IP (deterministic anchor chain) in a way no one can replicate without starting from scratch. The monitor product is also the easiest story to tell a non-technical federal reviewer: "we simulate the future of your deployed model so you don't find out about drift from a patient outcome."

---

## Financial framing

Rough per-engagement math at current Phase 2A pricing ($1,950 per population-test, $2,500 scope):

- **B-1 adds ~35%** to Cert engagement value (one combined-axis add-on per test).
- **B-2 creates a new tier** that maps to off-label evaluation — minimum $3,500 ticket, 2–4x per engagement.
- **B-3 creates recurring revenue** at ~$18K/year average per deployed model. Ten monitoring subscriptions = ~$180K ARR; comparable in annual value to ~90 one-shot Cert tests but at maybe 1/10th the per-revenue-dollar effort.

The pivot from one-shot Cert tests → monitoring subscriptions is also what makes this a venture story vs. a consulting story — and that matters for I-Corps → SBIR → any future non-dilutive capital.

---

Draft authored during assembly verification. No design decisions locked; proposal only.
