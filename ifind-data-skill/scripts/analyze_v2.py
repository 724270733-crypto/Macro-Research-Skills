import pandas as pd
import numpy as np

df = pd.read_csv('strategy_monthly.csv')
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

print('=' * 60)
print('Basic Statistics Overview')
print('=' * 60)
print(f'Data Range: {df["date"].min().date()} to {df["date"].max().date()}')
print(f'Total Months: {len(df)}')
print(f'Starting NAV: {df["nav"].iloc[0]:.4f}')
print(f'Ending NAV: {df["nav"].iloc[-1]:.4f}')
print(f'Total Return: {(df["nav"].iloc[-1]/df["nav"].iloc[0] - 1)*100:.2f}%')

n_years = len(df) / 12
total_return = df['nav'].iloc[-1]/df['nav'].iloc[0] - 1
annual_return = (1 + total_return) ** (1/n_years) - 1
print(f'Annual Return: {annual_return*100:.2f}%')

df['monthly_return'] = df['nav'].pct_change()
annual_vol = df['monthly_return'].std() * np.sqrt(12)
print(f'Annual Volatility: {annual_vol*100:.2f}%')

sharpe = (annual_return - 0.02) / annual_vol
print(f'Sharpe Ratio: {sharpe:.2f}')

cummax = df['nav'].cummax()
drawdown = (df['nav'] - cummax) / cummax
max_dd = drawdown.min()
print(f'Max Drawdown: {max_dd*100:.2f}%')

if max_dd != 0:
    calmar = annual_return / abs(max_dd)
else:
    calmar = 0
print(f'Calmar Ratio: {calmar:.2f}')

print()
print('=' * 60)
print('Yearly Performance Analysis')
print('=' * 60)

positive_years = 0
excess_positive = 0

for year in sorted(df['year'].unique()):
    year_data = df[df['year'] == year]
    if len(year_data) > 1:
        year_return = year_data['nav'].iloc[-1] / year_data['nav'].iloc[0] - 1
        bench_return = year_data['benchmark_nav'].iloc[-1] / year_data['benchmark_nav'].iloc[0] - 1
        excess = year_return - bench_return
        avg_pos = year_data['equity_position'].mean()
        print(f'{year}: Strategy {year_return*100:+.2f}% | Benchmark {bench_return*100:+.2f}% | Excess {excess*100:+.2f}% | Pos {avg_pos*100:.0f}%')

        if year_return > 0:
            positive_years += 1
        if excess > 0:
            excess_positive += 1

print(f'\nPositive Years: {positive_years}/12 ({positive_years/12*100:.1f}%)')
print(f'Excess Positive: {excess_positive}/12 ({excess_positive/12*100:.1f}%)')

print()
print('=' * 60)
print('Signal Distribution')
print('=' * 60)

signal_dist = df['composite_signal'].value_counts().sort_index()
print('Composite Signal Distribution:')
for sig, count in signal_dist.items():
    pct = count / len(df) * 100
    print(f'  Signal {sig:+d}: {count} times ({pct:.1f}%)')

position_dist = df['equity_position'].value_counts().sort_index()
print('\nEquity Position Distribution:')
for pos, count in position_dist.items():
    pct = count / len(df) * 100
    print(f'  Position {pos*100:.0f}%: {count} times ({pct:.1f}%)')

print()
print('=' * 60)
print('Position vs Next Month Return')
print('=' * 60)

for pos in sorted(df['equity_position'].unique()):
    pos_data = df[df['equity_position'] == pos]
    next_returns = pos_data['equity_return'].mean()
    print(f'Position {pos*100:.0f}%: Avg Equity Return {next_returns*100:.2f}%')

print()
print('=' * 60)
print('Stress Test - Slippage')
print('=' * 60)

slippage_rates = [0.0, 0.001, 0.002, 0.003, 0.005]
for slip in slippage_rates:
    df_test = df.copy()
    cost_per_trade = slip
    n_trades = (df_test['equity_position'].shift(1) != df_test['equity_position']).sum()
    total_cost = n_trades * cost_per_trade
    adjusted_return = total_return - total_cost
    ann_ret = (1 + adjusted_return) ** (1/n_years) - 1
    print(f'Slippage {slip*100:.1f}%: Total {adjusted_return*100:.2f}%, Annual {ann_ret*100:.2f}%')

print()
print('=' * 60)
print('Parameter Sensitivity')
print('=' * 60)

base_positions = [0.3, 0.4, 0.5, 0.6, 0.7]
signal_adjusts = [0.2, 0.25, 0.3, 0.35, 0.4]

print('Annual Return with different parameters:')
for base in base_positions:
    for adj in signal_adjusts:
        test_pos = base + df['composite_signal'] * adj
        test_pos = test_pos.clip(0.3, 1.0)
        df_temp = df.copy()
        df_temp['test_position'] = test_pos
        df_temp['test_return'] = df_temp['test_position'].shift(1) * df_temp['equity_return'] + \
                                   (1 - df_temp['test_position'].shift(1)) * df_temp['bond_return']
        df_temp = df_temp.dropna(subset=['test_return'])
        df_temp['test_nav'] = (1 + df_temp['test_return']).cumprod()
        test_total = df_temp['test_nav'].iloc[-1] - 1
        test_ann = (1 + test_total) ** (1/n_years) - 1
        print(f'  Base{base*100:.0f}% + Adj{adj*100:.0f}%: {test_ann*100:.2f}%')

print()
print('=' * 60)
print('Conclusion')
print('=' * 60)

bench_total = df['benchmark_nav'].iloc[-1] / df['benchmark_nav'].iloc[0] - 1
bench_ann = (1 + bench_total) ** (1/n_years) - 1

print(f'Strategy Annual: {annual_return*100:.2f}%')
print(f'Benchmark Annual: {bench_ann*100:.2f}%')
print(f'Excess Annual: {(annual_return - bench_ann)*100:.2f}%')
