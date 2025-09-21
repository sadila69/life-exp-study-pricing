import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def build_mortality_table():
    ages = np.arange(20, 101)
    qx = 0.0004 * np.exp(0.075 * (ages - 30))
    qx = np.clip(qx, 1e-6, 0.35)
    return pd.DataFrame({'age': ages, 'qx': qx})

def build_lapse_table(max_duration=30):
    dur = np.arange(1, max_duration+1)
    lapse = np.where(dur==1, 0.08, np.where(dur==2, 0.05, np.where(dur<=5, 0.03, 0.015)))
    return pd.DataFrame({'duration': dur, 'lapse_rate': lapse})

def generate_policies(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    policy_id = np.arange(1, n+1)
    issue_age = rng.integers(20, 61, size=n)
    gender = rng.choice(['M','F'], size=n, p=[0.5,0.5])
    smoker = rng.choice([0,1], size=n, p=[0.8,0.2])
    issue_year = rng.integers(2012, 2023, size=n)
    term_length = rng.choice([10,20,30], size=n, p=[0.5,0.35,0.15])
    product = np.where(term_length==10, 'Term10', np.where(term_length==20, 'Term20', 'Term30'))
    face = np.exp(rng.normal(11.2, 0.6, size=n))
    face = np.clip(face, 50000, 750000)
    base_pct = np.where(term_length==10, 0.0045, np.where(term_length==20, 0.0065, 0.0085))
    load = 1.0 + 0.35*smoker + 0.10*(gender=='M')
    annual_premium = (face * base_pct * load).round(2)
    df = pd.DataFrame({
        'policy_id': policy_id,
        'issue_age': issue_age,
        'gender': gender,
        'smoker': smoker,
        'issue_year': issue_year,
        'term_length': term_length,
        'product': product,
        'face_amount': face.round(2),
        'annual_premium': annual_premium
    })
    return df

def simulate_statuses(df, mort_table, lapse_table, seed=123):
    rng = np.random.default_rng(seed)
    statuses, exit_years, exit_duration = [], [], []
    for _, row in df.iterrows():
        age = int(row['issue_age'])
        term = int(row['term_length'])
        issue_yr = int(row['issue_year'])
        g = row['gender']
        smoker = int(row['smoker'])
        male_mult = 1.15 if g=='M' else 0.95
        smoke_mult = 1.5 if smoker==1 else 1.0
        status, ex_year, ex_dur = 'inforce', None, None
        for d in range(1, term+1):
            cur_age = age + d - 1
            qx = float(mort_table.loc[mort_table['age']==min(cur_age, mort_table['age'].max()), 'qx'].iloc[0])
            qx *= male_mult * smoke_mult
            lx = float(lapse_table.loc[lapse_table['duration']==min(d, lapse_table['duration'].max()), 'lapse_rate'].iloc[0])
            u = rng.random()
            if u < qx:
                status, ex_year, ex_dur = 'claimed', issue_yr + d - 1, d
                break
            elif u < qx + lx:
                status, ex_year, ex_dur = 'lapsed', issue_yr + d - 1, d
                break
        statuses.append(status)
        exit_years.append(ex_year)
        exit_duration.append(ex_dur)
    out = df.copy()
    out['status'] = statuses
    out['exit_year'] = exit_years
    out['exit_duration'] = exit_duration
    return out

def write_csvs(output_dir, policies, mort, lapse):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    policies.to_csv(output_dir / 'policies.csv', index=False)
    mort.to_csv(output_dir / 'mortality_table.csv', index=False)
    lapse.to_csv(output_dir / 'lapse_table.csv', index=False)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', type=str)
    parser.add_argument('--n', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.generate:
        mort = build_mortality_table()
        lapse = build_lapse_table()
        policies = generate_policies(n=args.n, seed=args.seed)
        policies = simulate_statuses(policies, mort, lapse, seed=args.seed+1)
        write_csvs(args.generate, policies, mort, lapse)
        print(f'Wrote: {args.generate}/policies.csv, mortality_table.csv, lapse_table.csv')

if __name__ == '__main__':
    main()