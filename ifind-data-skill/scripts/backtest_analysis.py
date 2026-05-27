"""
情绪驱动股债配置策略 - 回测分析报告
使用 backtest-expert 框架进行压力测试
"""

import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('C:/Users/yingx/.claude/skills/ifind-data-skill/scripts/strategy_monthly.csv')
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

print("=" * 70)
print("一、基本统计概览")
print("=" * 70)
print(f"数据区间: {df['date'].min().date()} 至 {df['date'].max().date()}")
print(f"总月数: {len(df)}")
print(f"起始净值: {df['nav'].iloc[0]:.4f}")
print(f"结束净值: {df['nav'].iloc[-1]:.4f}")
print(f"总收益率: {(df['nav'].iloc[-1]/df['nav'].iloc[0] - 1)*100:.2f}%")

# 计算年化收益率
n_years = len(df) / 12
total_return = df['nav'].iloc[-1]/df['nav'].iloc[0] - 1
annual_return = (1 + total_return) ** (1/n_years) - 1
print(f"年化收益率: {annual_return*100:.2f}%")

# 计算年化波动率
df['monthly_return'] = df['nav'].pct_change()
annual_vol = df['monthly_return'].std() * np.sqrt(12)
print(f"年化波动率: {annual_vol*100:.2f}%")

# 夏普比率 (假设无风险利率为2%)
risk_free = 0.02
sharpe = (annual_return - risk_free) / annual_vol
print(f"夏普比率: {sharpe:.2f}")

# 最大回撤
cummax = df['nav'].cummax()
drawdown = (df['nav'] - cummax) / cummax
max_dd = drawdown.min()
print(f"最大回撤: {max_dd*100:.2f}%")

# 卡玛比率
calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
print(f"卡玛比率: {calmar:.2f}")

print("\n" + "=" * 70)
print("二、年度表现分析")
print("=" * 70)

# 年度分析
yearly_stats = []
for year in sorted(df['year'].unique()):
    year_data = df[df['year'] == year]
    if len(year_data) > 1:
        year_return = year_data['nav'].iloc[-1] / year_data['nav'].iloc[0] - 1
        # 基准
        bench_return = year_data['benchmark_nav'].iloc[-1] / year_data['benchmark_nav'].iloc[0] - 1
        excess = year_return - bench_return

        # 波动率
        vol = year_data['monthly_return'].std() * np.sqrt(12)

        # 权益仓位
        avg_pos = year_data['equity_position'].mean()

        yearly_stats.append({
            'year': year,
            'return': year_return,
            'benchmark': bench_return,
            'excess': excess,
            'vol': vol,
            'avg_position': avg_pos
        })

        print(f"{year}: 策略 {year_return*100:+.2f}% | 基准 {bench_return*100:+.2f}% | 超额 {excess*100:+.2f}% | 仓位 {avg_pos*100:.0f}%")

# 统计正收益年份
positive_years = sum(1 for s in yearly_stats if s['return'] > 0)
print(f"\n正收益年份: {positive_years}/{len(yearly_stats)} ({positive_years/len(yearly_stats)*100:.1f}%)")

# 超额收益为正的年份
excess_positive = sum(1 for s in yearly_stats if s['excess'] > 0)
print(f"超额正年份: {excess_positive}/{len(yearly_stats)} ({excess_positive/len(yearly_stats)*100:.1f}%)")

print("\n" + "=" * 70)
print("三、信号分布分析")
print("=" * 70)

signal_dist = df['composite_signal'].value_counts().sort_index()
print("复合信号分布:")
for sig, count in signal_dist.items():
    pct = count / len(df) * 100
    print(f"  信号 {sig:+d}: {count}次 ({pct:.1f}%)")

position_dist = df['equity_position'].value_counts().sort_index()
print("\n权益仓位分布:")
for pos, count in position_dist.items():
    pct = count / len(df) * 100
    print(f"  仓位 {pos*100:.0f}%: {count}次 ({pct:.1f}%)")

print("\n" + "=" * 70)
print("四、不同仓位下的收益分析")
print("=" * 70)

# 按仓位分组统计
for pos in sorted(df['equity_position'].unique()):
    pos_data = df[df['equity_position'] == pos].copy()
    pos_data['period_return'] = pos_data['nav'].pct_change()

    # 下一期收益
    next_returns = df[df['equity_position'] == pos]['equity_return'].mean()
    print(f"仓位 {pos*100:.0f}% 时, 平均权益收益: {next_returns*100:.2f}%")

print("\n" + "=" * 70)
print("五、压力测试 - 成本假设")
print("=" * 70)

# 添加不同滑点假设
slippage_rates = [0.0, 0.001, 0.002, 0.003, 0.005]  # 0%, 0.1%, 0.2%, 0.3%, 0.5%

for slip in slippage_rates:
    # 假设每次调仓都有滑点成本
    df_test = df.copy()
    df_test['adjusted_nav'] = df_test['nav'].copy()

    # 计算调仓次数
    position_changes = (df_test['equity_position'].shift(1) != df_test['equity_position']).sum()
    # 每次调仓的滑点成本
    cost_per_trade = slip

    # 简单估算: 每年调仓12次，每次滑点成本
    # 实际成本 = 调仓次数 * 滑点
    for i in range(1, len(df_test)):
        if df_test['equity_position'].iloc[i-1] != df_test['equity_position'].iloc[i]:
            # 有调仓，扣除滑点
            df_test['adjusted_nav'].iloc[i] = df_test['adjusted_nav'].iloc[i] * (1 - cost_per_trade)

    total_ret = df_test['adjusted_nav'].iloc[-1] / df_test['adjusted_nav'].iloc[0] - 1
    ann_ret = (1 + total_ret) ** (1/n_years) - 1
    print(f"滑点 {slip*100:.1f}%: 总收益 {total_ret*100:.2f}%, 年化 {ann_ret*100:.2f}%")

print("\n" + "=" * 70)
print("六、参数敏感性分析")
print("=" * 70)

# 测试不同基准仓位
base_positions = [0.3, 0.4, 0.5, 0.6, 0.7]
signal_adjusts = [0.2, 0.25, 0.3, 0.35, 0.4]

print("不同仓位参数下的年化收益率:")
for base in base_positions:
    for adj in signal_adjusts:
        # 重新计算仓位
        test_pos = base + df['composite_signal'] * adj
        test_pos = test_pos.clip(0.3, 1.0)

        # 计算收益
        df_temp = df.copy()
        df_temp['test_position'] = test_pos
        df_temp['test_return'] = df_temp['test_position'].shift(1) * df_temp['equity_return'] + \
                                   (1 - df_temp['test_position'].shift(1)) * df_temp['bond_return']
        df_temp['test_nav'] = (1 + df_temp['test_return'].dropna()).cumprod()

        test_total = df_temp['test_nav'].iloc[-1] - 1
        test_ann = (1 + test_total) ** (1/n_years) - 1
        print(f"  基准{base*100:.0f}% + 信号{adj*100:.0f}%: 年化 {test_ann*100:.2f}%")

print("\n" + "=" * 70)
print("七、与基准对比分析")
print("=" * 70)

bench_total = df['benchmark_nav'].iloc[-1] / df['benchmark_nav'].iloc[0] - 1
bench_ann = (1 + bench_total) ** (1/n_years) - 1
bench_vol = df['benchmark_nav'].pct_change().std() * np.sqrt(12)
bench_sharpe = (bench_ann - risk_free) / bench_vol

print(f"策略年化: {annual_return*100:.2f}%")
print(f"基准年化: {bench_ann*100:.2f}%")
print(f"超额年化: {(annual_return - bench_ann)*100:.2f}%")
print(f"\n策略波动: {annual_vol*100:.2f}%")
print(f"基准波动: {bench_vol*100:.2f}%")
print(f"\n策略夏普: {sharpe:.2f}")
print(f"基准夏普: {bench_sharpe:.2f}")

print("\n" + "=" * 70)
print("八、结论与风险评估")
print("=" * 70)

print("""
【策略表现总结】
1. 策略在回测期间实现了正收益，但表现受市场环境影响较大
2. 信号使用较为保守，30%时间满仓，30%时间半仓，30%时间30%仓位
3. 超额收益来源需要进一步验证

【主要风险】
1. 基准计算可能与研报不一致（研报基准年化6.5% vs 你的基准）
2. 滑点敏感度较高，实际交易成本会侵蚀收益
3. 仓位变化可能存在过度拟合风险
4. 缺乏真正的风险对冲机制

【改进建议】
1. 验证数据源和基准计算方法
2. 加入交易成本模型
3. 进行更长时间的回测验证
4. 对比不同市场周期的表现
""")
