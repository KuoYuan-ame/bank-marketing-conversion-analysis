"""Bank marketing: descriptive segment uncertainty and strategy validation.

Input: outputs/top_segment_candidates.csv generated from SQL customer segments.
Outputs: outputs/segment_uncertainty.csv, outputs/segment_wilson_intervals.png,
         outputs/strategy_validation_report.md

This script does not estimate causal effects or expected future returns.
"""

from pathlib import Path
from statistics import NormalDist
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
SOURCE = OUTPUT / "top_segment_candidates.csv"
TOTAL_RECORDS = 45_211
TOTAL_CONVERSIONS = 5_289
MIN_RECORDS_FOR_VISUAL = 500
Z = NormalDist().inv_cdf(0.975)


def wilson_interval(k: int, n: int) -> tuple[float, float]:
    """Wilson score interval for a binomial success rate; returns proportions."""
    p = k / n
    z2 = Z * Z
    denominator = 1 + z2 / n
    midpoint = (p + z2 / (2 * n)) / denominator
    halfwidth = Z / denominator * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return midpoint - halfwidth, midpoint + halfwidth


def load_and_validate() -> pd.DataFrame:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing {SOURCE}. Run 07_customer_priority_analysis.py first.")
    df = pd.read_csv(SOURCE)
    required = {"job", "housing", "loan", "records", "conversions"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
    if df[list(required)].isna().any().any():
        raise ValueError("Missing values in required columns")
    if df.duplicated(["job", "housing", "loan"]).any():
        raise ValueError("Repeated job/housing/loan segment")
    for c in ("records", "conversions"):
        df[c] = pd.to_numeric(df[c], errors="raise")
        if (df[c] % 1 != 0).any():
            raise ValueError(f"Non-integer values in {c}")
        df[c] = df[c].astype(int)
    if (df.records <= 0).any() or (df.conversions < 0).any() or (df.conversions > df.records).any():
        raise ValueError("Invalid group counts")
    if df.records.sum() > TOTAL_RECORDS or df.conversions.sum() > TOTAL_CONVERSIONS:
        raise ValueError("Group totals exceed full sample totals")
    if "conversion_rate_pct" in df:
        observed = df.conversions / df.records * 100
        if not np.allclose(df.conversion_rate_pct, observed, atol=0.011):
            raise ValueError("Inconsistent conversion rates")
    return df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["job", "housing", "loan", "records", "conversions"]].copy()
    out["observed_rate_pct"] = 100 * out.conversions / out.records
    intervals = [wilson_interval(k, n) for k, n in zip(out.conversions, out.records)]
    out["wilson_low_pct"] = [100 * lower for lower, _ in intervals]
    out["wilson_high_pct"] = [100 * upper for _, upper in intervals]
    out["historical_lift"] = (out.conversions / out.records) / (TOTAL_CONVERSIONS / TOTAL_RECORDS)
    out["share_of_all_records_pct"] = 100 * out.records / TOTAL_RECORDS
    out["share_of_all_conversions_pct"] = 100 * out.conversions / TOTAL_CONVERSIONS
    out = out.sort_values("observed_rate_pct", ascending=False).reset_index(drop=True)
    out["observed_rank"] = np.arange(1, len(out) + 1)
    out["wilson_lower_rank"] = out.wilson_low_pct.rank(method="min", ascending=False).astype(int)
    return out


def make_chart(df: pd.DataFrame) -> None:
    top = df.head(10).iloc[::-1]
    labels = [f"{r.job} | H:{r.housing} L:{r.loan}" for r in top.itertuples()]
    fig, ax = plt.subplots(figsize=(11, 6.4))
    y = np.arange(len(top))
    rate = top.observed_rate_pct.to_numpy()
    lower = rate - top.wilson_low_pct.to_numpy()
    upper = top.wilson_high_pct.to_numpy() - rate
    ax.errorbar(rate, y, xerr=[lower, upper], fmt="o", capsize=3, markersize=6)
    ax.axvline(100 * TOTAL_CONVERSIONS / TOTAL_RECORDS, linestyle="--", linewidth=1.3,
               label="Overall historical rate (11.70%)")
    ax.set_yticks(y, labels)
    ax.set_xlabel("Observed subscription rate and 95% Wilson interval (%)")
    ax.set_title("Candidate segments: in-sample rate uncertainty")
    ax.grid(axis="x", alpha=0.15)
    ax.legend(loc="lower right")
    max_x = max(top.wilson_high_pct.max(), 15)
    ax.set_xlim(0, max_x + 7)
    for yi, r in enumerate(top.itertuples()):
        ax.text(r.wilson_high_pct + 0.5, yi, f"n={r.records:,}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT / "segment_wilson_intervals.png", dpi=170)
    plt.close(fig)


def make_report(df: pd.DataFrame) -> None:
    top4 = df.head(4)
    top_rate = df.iloc[0]
    most_conversions = df.loc[df.conversions.idxmax()]
    source_count = df.records.sum()
    subs_count = df.conversions.sum()
    report = f"""# Bank Marketing: Segment Stability and Strategy Validation

## 1. Data scope

- Source: UCI Bank Marketing, legacy `bank-full.csv`.
- Full historical dataset: {TOTAL_RECORDS:,} marketing records, {TOTAL_CONVERSIONS:,} subscriptions; observed rate {100*TOTAL_CONVERSIONS/TOTAL_RECORDS:.2f}%.
- Current input: {len(df)} shortlisted segment rows totaling {source_count:,} historical records ({100*source_count/TOTAL_RECORDS:.2f}% of all records) and {subs_count:,} subscriptions ({100*subs_count/TOTAL_CONVERSIONS:.2f}% of all subscriptions).
- These are observation-level summaries, not deduplicated customers. Segments are selected using the same history being summarized.

## 2. Descriptive findings

- Highest observed rate among the **provided shortlist**: `{top_rate.job} / housing={top_rate.housing} / loan={top_rate.loan}`, {top_rate.observed_rate_pct:.2f}% ({top_rate.conversions:,}/{top_rate.records:,}), 95% Wilson interval [{top_rate.wilson_low_pct:.2f}%, {top_rate.wilson_high_pct:.2f}%].
- Largest absolute subscription count among the shortlist: `{most_conversions.job} / housing={most_conversions.housing} / loan={most_conversions.loan}`, {most_conversions.conversions:,} successes from {most_conversions.records:,} records; observed rate {most_conversions.observed_rate_pct:.2f}%.
- Top four **by in-sample observed rate**: {top4.records.sum():,} records ({100*top4.records.sum()/TOTAL_RECORDS:.2f}% of the dataset), {top4.conversions.sum():,} subscriptions ({100*top4.conversions.sum()/TOTAL_CONVERSIONS:.2f}% of all observed subscriptions).
- `historical_lift` means segment observed rate divided by overall historical rate; it is **not** incremental uplift.

## 3. Statistical stability

- `segment_uncertainty.csv` includes the observed rate, Wilson 95% interval, and rank by point estimate / interval lower bound.
- Wilson intervals provide an indication of sampling uncertainty **under an independent Bernoulli approximation**. They do not correct for selection, multiple comparisons, repeated contacts from the same customer, or possible confounding.
- The shortlist originates from historical rates; ranking by these same data tends to overstate the expected advantage of the top-ranked segments.
- The prior SQL minimum 200 records and plot minimum 500 records are filtering choices, **not guarantees** of statistical reliability.

## 4. Proposed operational validation (not measured in this dataset)

1. Define the eligible customer population and obtain a persistent customer-level ID. Apply consent, suitability, compliance, and fair-treatment checks before outreach.
2. Freeze the segment-selection policy before testing. Randomly assign eligible customers to policy vs existing outreach strategy; use intention-to-treat analysis.
3. Primary outcome: subscriptions per eligible customer within a prespecified window. Guardrails: contacts per customer, opt-outs, complaints, customer experience and compliance.
4. Prespecify experiment duration, alpha, power/MDE, tracking quality checks, and stopping rules. Add cost per contact / product margin to evaluate net business value.
5. Compare **incremental** performance between randomized arms, not subgroup historical rates alone.

## 5. Interpretation limitations

- This historical dataset has no unique customer ID, per-contact cost, product margin, or randomized policy-control comparison.
- `duration` and final `campaign` are not suitable pre-contact targeting features; `poutcome` may be used only if known at the relevant decision time.
- No claims are made about causal effects, future conversion probabilities, revenue lift, campaign savings, or suitability of any occupation group.
"""
    (OUTPUT / "strategy_validation_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    data = load_and_validate()
    summary = build_summary(data)
    summary.to_csv(OUTPUT / "segment_uncertainty.csv", index=False, encoding="utf-8-sig", float_format="%.4f")
    make_chart(summary)
    make_report(summary)
    cols = ["job", "housing", "loan", "records", "conversions", "observed_rate_pct", "wilson_low_pct", "wilson_high_pct", "wilson_lower_rank"]
    print("\n========== Segment uncertainty review ==========")
    print(summary[cols].round(2).to_string(index=False))
    print(f"\nShortlist records: {summary.records.sum():,}; subscriptions: {summary.conversions.sum():,}")
    print("Outputs generated in:", OUTPUT)
    print("Notes: historical, selected-group descriptive analysis only; not causal uplift.")


if __name__ == "__main__":
    main()
