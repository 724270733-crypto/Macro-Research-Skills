"""
完整的回测分析脚本 - 基于研报规范
"""
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_excel('strategy_reproduction.xlsx', sheet_name='月度数据')
df['date'] = pd.to_datetime(df['date'])

# 计算仓位
df['equity_position'] = 0.5 + df['composite_signal'] * 0.3
df['equity_position'] = df['equity_position'].clip(0.3, 1.0)

# 重新计算净值
df['portfolio_return'] = df['equity_position'].shift(1) * df['equity_return'] + \
                        (1 - df['equity_position'].shift(1)) * df['bond_return']
df = df.dropna(subset=['portfolio_return'])
df['nav'] = (1 + df['portfolio_return']).cumprod()
df['benchmark_return'] = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
df['benchmark_nav'] = (1 + df['benchmark_return']).cumprod()

# 基本统计
n_years = len(df) / 12
total_return = df['nav'].iloc[-1] / df['nav'].iloc[0] - 1
annual_return = (1 + total_return) ** (1/n_years) - 1
annual_vol = df['portfolio_return'].std() * np.sqrt(12)
sharpe = (annual_return - 0.02) / annual_vol if annual_vol > 0 else 0
cummax = df['nav'].cummax()
drawdown = (df['nav'] - cummax) / cummax
max_dd = drawdown.min()
bench_total = df['benchmark_nav'].iloc[-1] / df['benchmark_nav'].iloc[0] - 1
bench_ann = (1 + bench_total) ** (1/n_years) - 1

print("=" * 70)
print("一、基本统计概览")
print("=" * 70)
print(f"数据区间: {df['date'].min().date()} 至 {df['date'].max().date()}")
print(f"总月数: {len(df)}")
print(f"起始净值: {df['nav'].iloc[0]:.4f}")
print(f"结束净值: {df['nav'].iloc[-1]:.4f}")
print(f"总收益率: {total_return*100:.2f}%")
print(f"年化收益率: {annual_return*100:.2f}%")
print(f"年化波动率: {annual_vol*100:.2f}%")
print(f"夏普比率: {sharpe:.2f}")
print(f"最大回撤: {max_dd*100:.2f}%")
print(f"基准年化: {bench_ann*100:.2f}%")
print(f"超额年化: {(annual_return - bench_ann)*100:.2f}%")

# 年度分析
print("\n" + "=" * 70)
print("二、年度表现分析")
print("=" * 70)
df['year'] = df['date'].dt.year

positive_years = 0
excess_positive = 0
for year in sorted(df['year'].unique()):
    year_data = df[df['year'] == year]
    if len(year_data) > 1:
        yr_ret = year_data['nav'].iloc[-1] / year_data['nav'].iloc[0] - 1
        bench_ret = year_data['benchmark_nav'].iloc[-1] / year_data['benchmark_nav'].iloc[0] - 1
        excess = yr_ret - bench_ret
        avg_pos = year_data['equity_position'].mean()
        print(f"{year}: 策略 {yr_ret*100:+6.2f}% | 基准 {bench_ret*100:+6.2f}% | 超额 {excess*100:+6.2f}% | 仓位 {avg_pos*100:4.0f}%")
        if yr_ret > 0:
            positive_years += 1
        if excess > 0:
            excess_positive += 1

print(f"\n正收益年份: {positive_years}/{len(df['year'].unique())}")
print(f"超额正年份: {excess_positive}/{len(df['year'].unique())}")

# 信号分布
print("\n" + "=" * 70)
print("三、信号分布分析")
print("=" * 70)
signal_dist = df['composite_signal'].value_counts().sort_index()
for sig, count in signal_dist.items():
    pct = count / len(df) * 100
    print(f"信号 {sig:+d}: {count}次 ({pct:.1f}%)")

print("\n仓位分布:")
position_dist = df['equity_position'].value_counts().sort_index()
for pos, count in position_dist.items():
    pct = count / len(df) * 100
    print(f"仓位 {pos*100:.0f}%: {count}次 ({pct:.1f}%)")

# 滑点测试
print("\n" + "=" * 70)
print("四、滑点敏感性测试")
print("=" * 70)

n_trades = (df['equity_position'].shift(1) != df['equity_position']).sum()
print(f"总调仓次数: {n_trades}")

for slip in [0.0, 0.001, 0.002, 0.003, 0.005]:
    cost = n_trades * slip
    adj_return = total_return - cost
    adj_ann = (1 + adj_return) ** (1/n_years) - 1
    print(f"滑点 {slip*100:.1f}%: 总收益 {adj_return*100:.2f}% | 年化 {adj_ann*100:.2f}%")

# 参数敏感性
print("\n" + "=" * 70)
print("五、参数敏感性分析")
print("=" * 70)

for base in [0.4, 0.5, 0.6]:
    for adj in [0.2, 0.3, 0.4]:
        test_pos = base + df['composite_signal'] * adj
        test_pos = test_pos.clip(0.3, 1.0)
        test_ret = (test_pos.shift(1) * df['equity_return'] +
                   (1 - test_pos.shift(1)) * df['bond_return']).dropna()
        test_nav = (1 + test_ret).cumprod()
        test_total = test_nav.iloc[-1] - 1
        test_ann = (1 + test_total) ** (1/n_years) - 1
        print(f"基准{base*100:.0f}%+调整{adj*100:.0f}%: 年化 {test_ann*100:.2f}%")

# 与研报对比
print("\n" + "=" * 70)
print("六、与原研报对比")
print("=" * 70)
print(f"               复现结果    研报结果    差异")
print(f"年化收益率:    {annual_return*100:+6.2f}%    +11.40%    {annual_return*100 - 11.4:+6.2f}%")
print(f"基准收益率:    {bench_ann*100:+6.2f}%     +6.50%    {bench_ann*100 - 6.5:+6.2f}%")
print(f"超额收益率:    {(annual_return-bench_ann)*100:+6.2f}%     +4.90%    {(annual_return-bench_ann)*100 - 4.9:+6.2f}%")

# 保存
df.to_excel('strategy_reproduction.xlsx', sheet_name='月度数据', index=False)
print("\n已保存更新数据到 Excel")
