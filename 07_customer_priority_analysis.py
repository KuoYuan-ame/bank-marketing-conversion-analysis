"""Summarize descriptive Bank Marketing customer segments and create project charts.

Inputs (in outputs/): previous_outcome.csv, housing_previous_segments.csv,
candidate_segments.csv. Outputs (in outputs/): strategy_findings.md,
top_segment_candidates.csv, previous_outcome_rates.png, candidate_segments_rate.png.

This is descriptive, in-sample prioritization; it does not estimate causal uplift
or justify excluding customers from financial services.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
EXPECTED_N, EXPECTED_Y = 45_211, 5_289
BASELINE = EXPECTED_Y / EXPECTED_N


def load(name, cols):
    path = OUT / name
    if not path.exists():
        raise FileNotFoundError(f'Missing: {path}')
    data = pd.read_csv(path)
    absent = set(cols) - set(data.columns)
    if absent:
        raise ValueError(f'{name}: missing columns {sorted(absent)}')
    for col in ('records', 'conversions', 'conversion_rate_pct'):
        data[col] = pd.to_numeric(data[col], errors='raise')
    if (data['records'] <= 0).any() or (data['conversions'] < 0).any():
        raise ValueError(f'{name}: invalid counts')
    if (data['conversions'] > data['records']).any():
        raise ValueError(f'{name}: conversions exceed records')
    computed = 100 * data['conversions'] / data['records']
    if (computed - data['conversion_rate_pct']).abs().max() > 0.011:
        raise ValueError(f'{name}: inconsistent conversion rate')
    return data


def check_total(data, name):
    totals = (int(data['records'].sum()), int(data['conversions'].sum()))
    if totals != (EXPECTED_N, EXPECTED_Y):
        raise ValueError(f'{name}: totals are {totals}, expected {(EXPECTED_N, EXPECTED_Y)}')


def main():
    OUT.mkdir(exist_ok=True)
    prior = load('previous_outcome.csv', ['poutcome', 'records', 'conversions', 'conversion_rate_pct'])
    cross = load('housing_previous_segments.csv', ['housing','poutcome','records','conversions', 'conversion_rate_pct'])
    seg = load('candidate_segments.csv', ['job','housing','loan','records','conversions','conversion_rate_pct','lift_vs_overall'])
    check_total(prior, 'Q6')
    check_total(cross, 'Q7')
    if seg.duplicated(['job','housing','loan']).any():
        raise ValueError('Q8: duplicate segment keys')
    if (seg['records'] < 200).any() or seg['records'].sum() > EXPECTED_N:
        raise ValueError('Q8: invalid threshold or coverage')
    # Q7 must aggregate exactly to Q6 for every previous-outcome category.
    reconciled = cross.groupby('poutcome')[['records', 'conversions']].sum().sort_index()
    reference = prior.set_index('poutcome')[['records', 'conversions']].sort_index()
    if not reconciled.equals(reference):
        raise ValueError('Q7 does not reconcile with Q6 by previous outcome')
    seg = seg.copy()
    seg['rate'] = seg['conversions'] / seg['records']
    seg['segment'] = seg['job'] + ' | housing=' + seg['housing'] + ' | loan=' + seg['loan']
    seg['lift_check'] = seg['rate'] / BASELINE
    if (seg['lift_check'] - pd.to_numeric(seg['lift_vs_overall'])).abs().max() > 0.011:
        raise ValueError('Q8: lift not consistent with overall baseline')
    # A minimum 500 observed records is used only for displaying a preliminary shortlist.
    shortlist = seg.loc[seg.records >= 500].copy()
    shortlist = shortlist.sort_values(['rate', 'records'], ascending=[False, False])
    shortlist[['job','housing','loan','records','conversions','conversion_rate_pct','lift_vs_overall']].head(10).to_csv(
        OUT / 'top_segment_candidates.csv', index=False, encoding='utf-8-sig'
    )

    # Chart 1: historical previous-outcome rates (different group sizes).
    tmp = prior.sort_values('conversion_rate_pct', ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.barh(tmp['poutcome'], tmp['conversion_rate_pct'])
    for bar, row in zip(bars, tmp.itertuples()):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height()/2,
                f'{row.conversion_rate_pct:.2f}% (n={row.records:,})', va='center', fontsize=9)
    ax.set_xlim(0, max(tmp['conversion_rate_pct'])*1.38)
    ax.set_xlabel('Observed subscription rate (%)')
    ax.set_title('Prior campaign outcome and current subscription')
    ax.axvline(BASELINE*100, linestyle='--', linewidth=1, label=f'Overall {BASELINE:.2%}')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(OUT / 'previous_outcome_rates.png', dpi=170)
    plt.close(fig)

    # Chart 2: top candidate groups ranked by historical rate, with n noted.
    display = shortlist.head(8).sort_values('rate', ascending=True)
    labels = [f'{r.job} | H:{r.housing} L:{r.loan}' for r in display.itertuples()]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    bars = ax.barh(labels, display['conversion_rate_pct'])
    for bar, row in zip(bars, display.itertuples()):
        ax.text(bar.get_width()+0.6, bar.get_y()+bar.get_height()/2,
                f'{row.conversion_rate_pct:.2f}% (n={row.records:,})', va='center', fontsize=9)
    ax.set_xlim(0, max(display['conversion_rate_pct'])*1.28)
    ax.axvline(BASELINE*100, linestyle='--', linewidth=1, label=f'Overall {BASELINE:.2%}')
    ax.set_xlabel('Observed subscription rate (%)')
    ax.set_title('Pre-contact segments: historical rate, minimum 500 records')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(OUT / 'candidate_segments_rate.png', dpi=170)
    plt.close(fig)

    top_rate = seg.sort_values(['rate','records'], ascending=[False,False]).iloc[0]
    top_volume = seg.sort_values(['conversions','records'], ascending=[False,False]).iloc[0]
    top_four = seg.sort_values(['rate','records'], ascending=[False,False]).head(4)
    success = prior.set_index('poutcome').loc['success']
    unknown = prior.set_index('poutcome').loc['unknown']
    housed = cross.groupby('housing')[['records','conversions']].sum()
    text = f'''# Bank Marketing: Customer Segmentation Findings

## Data and scope
- Source: UCI Bank Marketing (legacy bank-full.csv), record-level results.
- Total historical records: {EXPECTED_N:,}; subscriptions: {EXPECTED_Y:,}; observed rate: {BASELINE:.2%}.
- Q6 and Q7 reconcile to full dataset. Q8 retains {len(seg)} segments with at least 200 observations, covering {seg.records.sum():,} records ({seg.records.sum()/EXPECTED_N:.2%}) and {seg.conversions.sum():,} subscriptions ({seg.conversions.sum()/EXPECTED_Y:.2%}). Excluded smaller groups: {EXPECTED_N-seg.records.sum():,} records.

## Previous campaign outcome (Q6)
- `success`: {int(success.records):,} records, {int(success.conversions):,} subscriptions, {success.conversion_rate_pct:.2f}% observed rate.
- `unknown`: {int(unknown.records):,} records ({unknown.records/EXPECTED_N:.2%} of all observations), {unknown.conversion_rate_pct:.2f}% observed rate. `unknown` must not automatically be equated with never contacted.
- These rates are associations; they do not measure the increment caused by contacting again.

## Housing loan and previous outcome (Q7)
- `housing=no` and `poutcome=success`: {cross[(cross.housing=='no')&(cross.poutcome=='success')]['conversion_rate_pct'].iloc[0]:.2f}% (n={int(cross[(cross.housing=='no')&(cross.poutcome=='success')]['records'].iloc[0]):,}).
- `housing=yes` and `poutcome=success`: {cross[(cross.housing=='yes')&(cross.poutcome=='success')]['conversion_rate_pct'].iloc[0]:.2f}% (n={int(cross[(cross.housing=='yes')&(cross.poutcome=='success')]['records'].iloc[0]):,}).
- Group totals: housing=no {int(housed.loc['no','records']):,} records and {int(housed.loc['no','conversions']):,} subscriptions; housing=yes {int(housed.loc['yes','records']):,} records and {int(housed.loc['yes','conversions']):,} subscriptions.

## Pre-contact candidate segments (Q8)
- Highest observed rate in screened groups: **{top_rate.segment}**, {top_rate.conversion_rate_pct:.2f}% ({int(top_rate.conversions):,}/{int(top_rate.records):,}), lift {top_rate.lift_vs_overall:.2f}x relative to total historical average.
- Largest number of observed subscriptions: **{top_volume.segment}**, {int(top_volume.conversions):,} subscriptions from {int(top_volume.records):,} records; historical rate {top_volume.conversion_rate_pct:.2f}%.
- Top four groups **by observed rate** account for {int(top_four.records.sum()):,} records ({top_four.records.sum()/EXPECTED_N:.2%}) and {int(top_four.conversions.sum()):,} subscriptions ({top_four.conversions.sum()/EXPECTED_Y:.2%}); this is an in-sample description, not a forecast of future lift.
- Historical subscription rate alone is insufficient to select outreach targets. Consider segment size, costs, consent, channel capacity, uncertainty, and fair treatment.

## Important limitations
- Rows are marketing observations, not deduplicated customers. No unique customer ID is available.
- Historical data do not establish causal effects or incremental response to future calls; segment ranking is in-sample and may be optimistic.
- Thresholds of 200 (SQL) and 500 (visual shortlist) are presentation choices, not statistical guarantees.
- Prior-campaign outcomes are eligible pre-contact features only if actually available at the time of the intended decision.
- No per-contact cost, product margin, or control group is provided. No profit or causal uplift estimates are claimed.
'''
    (OUT / 'strategy_findings.md').write_text(text, encoding='utf-8')
    print('Q6/Q7 validated:', EXPECTED_N, 'records;', EXPECTED_Y, 'subscriptions')
    print(f'Q8: {len(seg)} segments; {int(seg.records.sum()):,} records ({seg.records.sum()/EXPECTED_N:.2%} coverage)')
    print('Top rate:',top_rate.segment, f'{top_rate.conversion_rate_pct:.2f}%', f'n={int(top_rate.records):,}')
    print('Top volume:',top_volume.segment, f'{int(top_volume.conversions):,} subscriptions')
    print('Saved to:', OUT)


if __name__ == '__main__':
    main()
