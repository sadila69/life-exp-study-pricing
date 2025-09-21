import pandas as pd
import numpy as np

def expand_exposure_years(policies: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in policies.iterrows():
        term = int(r['term_length'])
        exit_dur = r['exit_duration']
        for d in range(1, term+1):
            attained_age = int(r['issue_age']) + d - 1
            event = None
            if pd.notna(exit_dur) and int(exit_dur) == d:
                event = 'death' if r['status']=='claimed' else ('lapse' if r['status']=='lapsed' else None)
            exposure = 1.0 if event is None else 0.5
            rows.append({
                'policy_id': r['policy_id'],
                'issue_year': r['issue_year'],
                'issue_age': r['issue_age'],
                'gender': r['gender'],
                'smoker': r['smoker'],
                'duration': d,
                'attained_age': attained_age,
                'exposure': exposure,
                'event': event,
                'status': r['status']
            })
            if event is not None:
                break
    return pd.DataFrame(rows)

def actual_expected(exposure_df: pd.DataFrame, mort_table: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    if group_cols is None:
        group_cols = ['attained_age']
    mort = mort_table.rename(columns={'age':'attained_age'})
    df = exposure_df.merge(mort, on='attained_age', how='left')
    df['actual_deaths'] = (df['event']=='death').astype(int)
    df['expected_deaths'] = df['exposure'] * df['qx']
    grouped = df.groupby(group_cols, dropna=False).agg(
        exposure=('exposure','sum'),
        actual=('actual_deaths','sum'),
        expected=('expected_deaths','sum')
    ).reset_index()
    grouped['AE'] = grouped['actual'] / grouped['expected'].replace(0, np.nan)
    return grouped