import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.discrete.discrete_model import Probit
PRICES = [0, 1, 2, 5, 10, 20]
K = 20

def fit_probit(prices, p_a_list, n_samples=20):
    y, X = [], []
    for p, pr in zip(prices, p_a_list):
        n_a = int(round(pr * n_samples))
        n_b = n_samples - n_a
        y.extend([1]*n_a + [0]*n_b)
        X.extend([p]*n_samples)
    y = np.array(y)
    X = np.column_stack([np.ones(len(X)), np.array(X)])
    model = Probit(y, X)
    result = model.fit(disp=0)
    beta0, beta1 = result.params
    p_star = -beta0 / beta1 if abs(beta1) > 1e-6 else float('inf')
    price_grid = np.linspace(0, max(prices)*1.5, 200)
    fitted = result.model.cdf(beta0 + beta1 * price_grid)
    return {'beta0': beta0, 'beta1': beta1, 'p_star': p_star,
            'price_grid': price_grid, 'fitted_probs': fitted,
            'prices': prices, 'observed': p_a_list}

def plot_sweep(fit, title, save_path=None):
    fig, ax = plt.subplots(figsize=(6,4))
    ax.scatter(fit['prices'], fit['observed'], s=80, color='black', zorder=3)
    ax.plot(fit['price_grid'], fit['fitted_probs'], 'r-', linewidth=2)
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    ps = fit['p_star']
    if -5 <= ps <= max(fit['prices'])*1.5:
        ax.axvline(ps, color='green', linestyle='--', alpha=0.5)
        ax.text(ps, 0.55, f'p*={ps:.1f}', color='green', fontsize=9)
    ax.set_xlabel('Price'); ax.set_ylabel('P(choose A)')
    ax.set_title(title); ax.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    if save_path: plt.savefig(save_path, dpi=150)
    plt.show()

native_p = [0.85, 0.72, 0.58, 0.40, 0.22, 0.10]
native_fit = fit_probit(PRICES, native_p)
plot_sweep(native_fit, 'Native — Mock', 'sprint/figures/native_mock.png')
print(f"Native p* = {native_fit['p_star']:.2f}")

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

trials = load_jsonl('sprint/data/mock_data.jsonl')
df = pd.DataFrame(trials)
print(df[['condition', 'price', 'p_a']])
print(f"\nLoaded {len(trials)} trials")


for condition, group in df.groupby('condition'):
    prices = group['price'].tolist()
    p_as = group['p_a'].tolist()
    fit = fit_probit(prices, p_as)
    print(f"{condition}: p* = {fit['p_star']:.2f}")
    plot_sweep(fit, f'{condition} — from JSONL', f'sprint/figures/{condition}_jsonl.png')