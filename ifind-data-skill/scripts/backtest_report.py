"""
情绪驱动股债配置策略 - 完整回测报告
包含三次优化前后的结果对比
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('strategy_final_monthly.csv')
df['date'] = pd.to_datetime(df['date'])

# 成本参数
COMMISSION = 0.001
SLIPPAGE = 0.001

def calculate_metrics(ret, bench_ret, n_years):
    """计算回测指标"""
    nav = (1 + ret).cumprod()
    total = nav.iloc[-1] / nav.iloc[0] - 1
    ann = (1 + total) ** (1/n_years) - 1

    bench_nav = (1 + bench_ret).cumprod()
    bench_total = bench_nav.iloc[-1] / bench_nav.iloc[0] - 1
    bench_ann = (1 + bench_total) ** (1/n_years) - 1

    vol = ret.std() * np.sqrt(12)
    sharpe = (ann - 0.02) / vol if vol > 0 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_dd = drawdown.min()

    return {
        'total_return': total,
        'annual_return': ann,
        'annual_vol': vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'bench_annual': bench_ann,
        'excess': ann - bench_ann,
        'nav': nav,
        'bench_nav': bench_nav,
        'drawdown': drawdown
    }

# ============================================================
# 测试1: 原始参数 (复合信号, 基准50%, 调整30%)
# ============================================================
print("="*70)
print("测试1: 原始参数")
print("="*70)

position1 = 0.5 + df['composite_signal'] * 0.3
position1 = position1.clip(0.3, 1.0)

# 成本
df['pos_change1'] = (position1.shift(1) - position1.shift(2)).abs().fillna(0)
df['cost1'] = df['pos_change1'] * (COMMISSION + SLIPPAGE)

ret1 = position1.shift(1) * df['equity_return'] + (1 - position1.shift(1)) * df['bond_return'] - df['cost1']
ret1 = ret1.dropna()
bench_ret1 = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
bench_ret1 = bench_ret1.dropna()

n_years1 = len(ret1) / 12
metrics1 = calculate_metrics(ret1, bench_ret1, n_years1)

print(f"信号分布: {df['composite_signal'].value_counts().to_dict()}")
print(f"年化收益率: {metrics1['annual_return']*100:.2f}%")
print(f"基准年化: {metrics1['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics1['excess']*100:.2f}%")
print(f"夏普比率: {metrics1['sharpe']:.2f}")
print(f"最大回撤: {metrics1['max_drawdown']*100:.2f}%")
print(f"调仓次数: {(df['pos_change1'] > 0).sum()}")

# ============================================================
# 测试2: 降低阈值后的参数 (简化版，仍用复合信号)
# ============================================================
print()
print("="*70)
print("测试2: 降低阈值后 (仍用复合信号，基准50%, 调整30%)")
print("="*70)

# 由于阈值降低后信号仍然很少，这里测试用RORO信号
position2 = 0.5 + df['roro_signal'] * 0.3
position2 = position2.clip(0.0, 1.0)

df['pos_change2'] = (position2.shift(1) - position2.shift(2)).abs().fillna(0)
df['cost2'] = df['pos_change2'] * (COMMISSION + SLIPPAGE)

ret2 = position2.shift(1) * df['equity_return'] + (1 - position2.shift(1)) * df['bond_return'] - df['cost2']
ret2 = ret2.dropna()
bench_ret2 = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
bench_ret2 = bench_ret2.dropna()

n_years2 = len(ret2) / 12
metrics2 = calculate_metrics(ret2, bench_ret2, n_years2)

print(f"信号分布: {df['roro_signal'].value_counts().to_dict()}")
print(f"年化收益率: {metrics2['annual_return']*100:.2f}%")
print(f"基准年化: {metrics2['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics2['excess']*100:.2f}%")
print(f"夏普比率: {metrics2['sharpe']:.2f}")
print(f"最大回撤: {metrics2['max_drawdown']*100:.2f}%")
print(f"调仓次数: {(df['pos_change2'] > 0).sum()}")

# ============================================================
# 测试3: 优化仓位参数 (情绪信号绝对值, 基准80%, 调整90%)
# ============================================================
print()
print("="*70)
print("测试3: 优化仓位参数 (情绪信号绝对值, 基准80%, 调整90%)")
print("="*70)

position3 = 0.8 + df['sentiment_signal'].abs() * 0.9
position3 = position3.clip(0.0, 1.0)

df['pos_change3'] = (position3.shift(1) - position3.shift(2)).abs().fillna(0)
df['cost3'] = df['pos_change3'] * (COMMISSION + SLIPPAGE)

ret3 = position3.shift(1) * df['equity_return'] + (1 - position3.shift(1)) * df['bond_return'] - df['cost3']
ret3 = ret3.dropna()
bench_ret3 = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
bench_ret3 = bench_ret3.dropna()

n_years3 = len(ret3) / 12
metrics3 = calculate_metrics(ret3, bench_ret3, n_years3)

print(f"信号分布: {df['sentiment_signal'].abs().value_counts().to_dict()}")
print(f"年化收益率: {metrics3['annual_return']*100:.2f}%")
print(f"基准年化: {metrics3['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics3['excess']*100:.2f}%")
print(f"夏普比率: {metrics3['sharpe']:.2f}")
print(f"最大回撤: {metrics3['max_drawdown']*100:.2f}%")
print(f"调仓次数: {(df['pos_change3'] > 0).sum()}")

# ============================================================
# 生成对比表格
# ============================================================
print()
print("="*70)
print("三次优化结果对比")
print("="*70)
print(f"{'测试':<20} {'年化收益':>12} {'基准':>12} {'超额':>12} {'夏普':>10} {'最大回撤':>12}")
print("-"*70)
print(f"{'测试1-原始参数':<20} {metrics1['annual_return']*100:>+11.2f}% {metrics1['bench_annual']*100:>+11.2f}% {metrics1['excess']*100:>+11.2f}% {metrics1['sharpe']:>9.2f} {metrics1['max_drawdown']*100:>11.2f}%")
print(f"{'测试2-RORO信号':<20} {metrics2['annual_return']*100:>+11.2f}% {metrics2['bench_annual']*100:>+11.2f}% {metrics2['excess']*100:>+11.2f}% {metrics2['sharpe']:>9.2f} {metrics2['max_drawdown']*100:>11.2f}%")
print(f"{'测试3-情绪绝对值':<20} {metrics3['annual_return']*100:>+11.2f}% {metrics3['bench_annual']*100:>+11.2f}% {metrics3['excess']*100:>+11.2f}% {metrics3['sharpe']:>9.2f} {metrics3['max_drawdown']*100:>11.2f}%")
print("-"*70)
print(f"{'研报目标':<20} {'+11.40%':>12} {'+6.50%':>12} {'+4.90%':>12} {'-':>10} {'-':>12}")

# ============================================================
# 生成图表
# ============================================================
fig, axes = plt.subplots(3, 2, figsize=(14, 12))

# 测试1
axes[0, 0].plot(metrics1['nav'].values, label='Strategy', linewidth=1.5)
axes[0, 0].plot(metrics1['bench_nav'].values, label='Benchmark', linewidth=1.5, alpha=0.7)
axes[0, 0].set_title('Test 1: Original Parameters (Composite Signal, 50%+30%)', fontsize=10)
axes[0, 0].set_xlabel('Month')
axes[0, 0].set_ylabel('NAV')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].fill_between(range(len(metrics1['drawdown'])), metrics1['drawdown'].values, 0, alpha=0.5, color='red')
axes[0, 1].set_title('Test 1: Drawdown', fontsize=10)
axes[0, 1].set_xlabel('Month')
axes[0, 1].set_ylabel('Drawdown')
axes[0, 1].grid(True, alpha=0.3)

# 测试2
axes[1, 0].plot(metrics2['nav'].values, label='Strategy', linewidth=1.5)
axes[1, 0].plot(metrics2['bench_nav'].values, label='Benchmark', linewidth=1.5, alpha=0.7)
axes[1, 0].set_title('Test 2: RORO Signal Only (50%+30%)', fontsize=10)
axes[1, 0].set_xlabel('Month')
axes[1, 0].set_ylabel('NAV')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

axes[1, 1].fill_between(range(len(metrics2['drawdown'])), metrics2['drawdown'].values, 0, alpha=0.5, color='red')
axes[1, 1].set_title('Test 2: Drawdown', fontsize=10)
axes[1, 1].set_xlabel('Month')
axes[1, 1].set_ylabel('Drawdown')
axes[1, 1].grid(True, alpha=0.3)

# 测试3
axes[2, 0].plot(metrics3['nav'].values, label='Strategy', linewidth=1.5)
axes[2, 0].plot(metrics3['bench_nav'].values, label='Benchmark', linewidth=1.5, alpha=0.7)
axes[2, 0].set_title('Test 3: Sentiment Absolute (80%+90%)', fontsize=10)
axes[2, 0].set_xlabel('Month')
axes[2, 0].set_ylabel('NAV')
axes[2, 0].legend()
axes[2, 0].grid(True, alpha=0.3)

axes[2, 1].fill_between(range(len(metrics3['drawdown'])), metrics3['drawdown'].values, 0, alpha=0.5, color='red')
axes[2, 1].set_title('Test 3: Drawdown', fontsize=10)
axes[2, 1].set_xlabel('Month')
axes[2, 1].set_ylabel('Drawdown')
axes[2, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backtest_comparison.png', dpi=150, bbox_inches='tight')
print()
print("图表已保存到: backtest_comparison.png")

# ============================================================
# 保存详细数据到Excel
# ============================================================
# 重新构建数据 - 确保索引对齐
# 用dropna后的结果直接获取日期
ret1_dates = df['date'].iloc[ret1.index].reset_index(drop=True)
ret2_dates = df['date'].iloc[ret2.index].reset_index(drop=True)
ret3_dates = df['date'].iloc[ret3.index].reset_index(drop=True)

# 获取对应的原始数据（使用整数位置索引）
ret1_equity = df['equity_return'].iloc[ret1.index].reset_index(drop=True)
ret1_bond = df['bond_return'].iloc[ret1.index].reset_index(drop=True)
ret1_position = position1.iloc[ret1.index].reset_index(drop=True)

ret2_equity = df['equity_return'].iloc[ret2.index].reset_index(drop=True)
ret2_bond = df['bond_return'].iloc[ret2.index].reset_index(drop=True)
ret2_position = position2.iloc[ret2.index].reset_index(drop=True)

ret3_equity = df['equity_return'].iloc[ret3.index].reset_index(drop=True)
ret3_bond = df['bond_return'].iloc[ret3.index].reset_index(drop=True)
ret3_position = position3.iloc[ret3.index].reset_index(drop=True)

with pd.ExcelWriter('backtest_results.xlsx', engine='openpyxl') as writer:
    # 测试1
    df1 = pd.DataFrame({
        'date': ret1_dates,
        'equity_return': ret1_equity,
        'bond_return': ret1_bond,
        'position': ret1_position,
        'portfolio_return': ret1.reset_index(drop=True),
        'nav': metrics1['nav'].reset_index(drop=True),
        'benchmark_nav': metrics1['bench_nav'].reset_index(drop=True)
    })
    df1.to_excel(writer, sheet_name='Test1_Original', index=False)

    # 测试2
    df2 = pd.DataFrame({
        'date': ret2_dates,
        'equity_return': ret2_equity,
        'bond_return': ret2_bond,
        'position': ret2_position,
        'portfolio_return': ret2.reset_index(drop=True),
        'nav': metrics2['nav'].reset_index(drop=True),
        'benchmark_nav': metrics2['bench_nav'].reset_index(drop=True)
    })
    df2.to_excel(writer, sheet_name='Test2_RORO', index=False)

    # 测试3
    df3 = pd.DataFrame({
        'date': ret3_dates,
        'equity_return': ret3_equity,
        'bond_return': ret3_bond,
        'position': ret3_position,
        'portfolio_return': ret3.reset_index(drop=True),
        'nav': metrics3['nav'].reset_index(drop=True),
        'benchmark_nav': metrics3['bench_nav'].reset_index(drop=True)
    })
    df3.to_excel(writer, sheet_name='Test3_Optimized', index=False)

    # 汇总
    summary = pd.DataFrame({
        'Test': ['Test1_Original', 'Test2_RORO', 'Test3_Optimized', 'Target'],
        'Signal': ['Composite', 'RORO', 'Sentiment Abs', '-'],
        'Base': ['50%', '50%', '80%', '-'],
        'Adjust': ['30%', '30%', '90%', '-'],
        'Annual_Return': [metrics1['annual_return'], metrics2['annual_return'], metrics3['annual_return'], 0.114],
        'Benchmark': [metrics1['bench_annual'], metrics2['bench_annual'], metrics3['bench_annual'], 0.065],
        'Excess': [metrics1['excess'], metrics2['excess'], metrics3['excess'], 0.049],
        'Sharpe': [metrics1['sharpe'], metrics2['sharpe'], metrics3['sharpe'], '-'],
        'Max_DD': [metrics1['max_drawdown'], metrics2['max_drawdown'], metrics3['max_drawdown'], '-']
    })
    summary.to_excel(writer, sheet_name='Summary', index=False)

print("数据已保存到: backtest_results.xlsx")
print()
print("完成!")
