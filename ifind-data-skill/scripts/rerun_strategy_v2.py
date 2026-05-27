"""
情绪驱动股债配置策略 - 修正版
使用20日窗口，修正数据格式
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
class Config:
    START_DATE = "2014-01-01"
    END_DATE = "2025-12-19"
    ROLLING_WINDOW = 20  # 用户指定：20个交易日

    # 仓位
    EQUITY_BASE = 0.50
    SIGNAL_ADJUST = 0.30
    MAX_POSITION = 1.00
    MIN_POSITION = 0.30

    # 研报参数 - 信号阈值
    HIGH_THRESHOLD = 0.38   # 高位阈值
    LOW_THRESHOLD = 0.28     # 低位阈值

    # 成本
    COMMISSION_RATE = 0.001
    SLIPPAGE_RATE = 0.001


# ============================================================
# 数据获取
# ============================================================
print("加载本地数据文件...")

# AGG - 需要转换为收益率
agg = pd.read_csv('C:/Users/yingx/AGG.csv')
agg['date'] = pd.to_datetime(agg['date'])
agg = agg.sort_values('date')
agg['agg'] = pd.to_numeric(agg['AGG'], errors='coerce')
agg['agg_return'] = agg['agg'].pct_change()
print(f"AGG: {len(agg)}条, 日期范围: {agg['date'].min()} ~ {agg['date'].max()}")

# WTI - 需要转换为收益率，注意数据有空格
wti = pd.read_csv('C:/Users/yingx/WTI.csv')
wti['date'] = pd.to_datetime(wti['date'])
wti = wti.sort_values('date')
wti['wti'] = pd.to_numeric(wti['WTI'].astype(str).str.strip(), errors='coerce')
wti['wti_return'] = wti['wti'].pct_change()
print(f"WTI: {len(wti)}条, 日期范围: {wti['date'].min()} ~ {wti['date'].max()}")

# 读取已计算好的其他收益率数据
df = pd.read_csv('C:/Users/yingx/strategy_final_monthly.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
print(f"主数据: {len(df)}条, 日期范围: {df['date'].min()} ~ {df['date'].max()}")

# 替换agg和wti的收益率为本地计算的值
# 先按月对齐
df['year_month'] = df['date'].dt.to_period('M')
agg['year_month'] = agg['date'].dt.to_period('M')
wti['year_month'] = wti['date'].dt.to_period('M')

# 计算月度收益率
agg_monthly = agg.groupby('year_month').last().reset_index()
agg_monthly['agg_return_local'] = agg_monthly['agg_return']

wti_monthly = wti.groupby('year_month').last().reset_index()
wti_monthly['wti_return_local'] = wti_monthly['wti_return']

# 替换
df = df.merge(agg_monthly[['year_month', 'agg_return_local']], on='year_month', how='left')
df = df.merge(wti_monthly[['year_month', 'wti_return_local']], on='year_month', how='left')

# 使用本地计算的收益率（如果缺失则用原来的）
df['agg_return'] = df['agg_return_local'].fillna(df['agg_return'])
df['oil_return'] = df['wti_return_local'].fillna(df['oil_return'])

print(f"\n数据更新完成")


# ============================================================
# 重新计算RORO - 使用20日窗口
# ============================================================
print("\n" + "="*60)
print("使用20日窗口重新计算RORO...")
print("="*60)

# 获取日度数据来计算RORO
# 需要重新获取日度数据
import tushare as ts
import yfinance as yf
import akshare as ak

ts.set_token('4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863')
pro = ts.pro_api()

# 获取日度数据
hs300 = pro.index_daily(ts_code='000300.SH', start_date='20140101', end_date='20251219')
hs300['date'] = pd.to_datetime(hs300['trade_date'])
hs300 = hs300.sort_values('date')
hs300['hs300_return'] = hs300['close'].pct_change()

guozheng = pro.index_daily(ts_code='399317.SZ', start_date='20140101', end_date='20251219')
guozheng['date'] = pd.to_datetime(guozheng['trade_date'])
guozheng = guozheng.sort_values('date')
guozheng['guozheng_return'] = guozheng['close'].pct_change()

hsi = yf.download('^HSI', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
hsi.columns = [c[0] if isinstance(c, tuple) else c for c in hsi.columns]
hsi['date'] = pd.to_datetime(hsi['Date'])
hsi = hsi.sort_values('date')
hsi['hsi_return'] = hsi['Close'].pct_change()

sp500 = yf.download('^GSPC', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
sp500.columns = [c[0] if isinstance(c, tuple) else c for c in sp500.columns]
sp500['date'] = pd.to_datetime(sp500['Date'])
sp500 = sp500.sort_values('date')
sp500['sp500_return'] = sp500['Close'].pct_change()

nasdaq = yf.download('^NDX', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
nasdaq.columns = [c[0] if isinstance(c, tuple) else c for c in nasdaq.columns]
nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
nasdaq = nasdaq.sort_values('date')
nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()

cbond = ak.bond_new_composite_index_cbond()
cbond['date'] = pd.to_datetime(cbond['date'])
cbond = cbond.sort_values('date')
cbond['cbond_return'] = cbond['value'].pct_change()

# 合并日度数据
daily_df = hs300[['date', 'hs300_return']].merge(
    guozheng[['date', 'guozheng_return']], on='date', how='outer')
daily_df = daily_df.merge(hsi[['date', 'hsi_return']], on='date', how='outer')
daily_df = daily_df.merge(sp500[['date', 'sp500_return']], on='date', how='outer')
daily_df = daily_df.merge(nasdaq[['date', 'nasdaq_return']], on='date', how='outer')
daily_df = daily_df.merge(cbond[['date', 'cbond_return']], on='date', how='outer')
daily_df = daily_df.merge(agg[['date', 'agg_return']], on='date', how='outer')
daily_df = daily_df.merge(wti[['date', 'wti_return']], on='date', how='outer')
daily_df = daily_df.sort_values('date').reset_index(drop=True)

# 填充缺失值
for col in daily_df.columns:
    if col != 'date':
        daily_df[col] = daily_df[col].fillna(method='ffill').fillna(0)

# 添加黄金数据
daily_df['gold_return'] = 0  # 简化处理

# 计算RORO - 使用20日窗口
window = 20
asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return',
              'nasdaq_return', 'cbond_return', 'agg_return', 'wti_return', 'gold_return']

roro_values = []
scaler = StandardScaler()

for i in range(len(daily_df)):
    if i < window:
        roro_values.append(np.nan)
    else:
        window_data = daily_df[asset_cols].iloc[i-window:i].fillna(0)
        try:
            scaled = scaler.fit_transform(window_data)
            pca = PCA()
            pca.fit(scaled)
            eigenvalues = pca.explained_variance_
            roro = eigenvalues[0] / eigenvalues.sum()
            roro_values.append(roro)
        except:
            roro_values.append(np.nan)

daily_df['roro'] = roro_values
daily_df['roro'] = daily_df['roro'].fillna(method='bfill').fillna(method='ffill')

print(f"RORO计算完成: 范围 {daily_df['roro'].min():.4f} ~ {daily_df['roro'].max():.4f}")

# 转为月度
daily_df['year_month'] = daily_df['date'].dt.to_period('M')
monthly_roro = daily_df.groupby('year_month').last()[['roro']].reset_index()
monthly_roro['year_month'] = monthly_roro['year_month'].astype(str)

# 合并到主数据
df['year_month'] = df['year_month'].astype(str)
df = df.merge(monthly_roro, on='year_month', how='left')
if 'roro_y' in df.columns:
    df['roro'] = df['roro_y'].fillna(df['roro_x'])
    df = df.drop(['roro_x', 'roro_y'], axis=1)
elif 'roro' in df.columns and 'roro' in monthly_roro.columns:
    # 如果已有roro列，用新的覆盖
    pass


# ============================================================
# 信号生成 - 修正"快速回落"逻辑
# ============================================================
print("\n生成信号...")

HIGH_THRESHOLD = 0.38
LOW_THRESHOLD = 0.28

# RORO变化
df['roro_change'] = df['roro'].diff()

# 记录最近高点日期
df['recent_high_date'] = pd.NaT
in_high_region = False
high_start_date = None

for i in range(len(df)):
    if df.iloc[i]['roro'] >= HIGH_THRESHOLD:
        if not in_high_region:
            in_high_region = True
            high_start_date = df.iloc[i]['date']
        df.iloc[i, df.columns.get_loc('recent_high_date')] = high_start_date
    else:
        if in_high_region:
            in_high_region = False

# 计算距最近高点月数
df['months_since_high'] = (df['date'] - df['recent_high_date']).dt.days / 30

# RORO信号
# 低位上升：上期<0.28，本期>上期 → +1
df['roro_signal'] = 0
df.loc[(df['roro'].shift(1) < LOW_THRESHOLD) & (df['roro_change'] > 0), 'roro_signal'] = 1

# 快速回落：前期>0.38，本期<上期，且距高点≤3个月 → -1
df.loc[(df['roro'].shift(1) > HIGH_THRESHOLD) &
       (df['roro_change'] < 0) &
       (df['months_since_high'] <= 3), 'roro_signal'] = -1

# 情绪信号
df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']
df['sentiment_change'] = df['sentiment_return'].diff()

df['sentiment_signal'] = 0
df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1
df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1

# 复合信号
df['composite_signal'] = 0
df.loc[(df['roro_signal'] == 1) & (df['sentiment_signal'] == 1), 'composite_signal'] = 2
df.loc[(df['roro_signal'] == -1) & (df['sentiment_signal'] == -1), 'composite_signal'] = -2

print(f"RORO信号分布: {df['roro_signal'].value_counts().to_dict()}")
print(f"情绪信号分布: {df['sentiment_signal'].value_counts().to_dict()}")
print(f"复合信号分布: {df['composite_signal'].value_counts().to_dict()}")


# ============================================================
# 回测
# ============================================================
print("\n" + "="*60)
print("回测...")
print("="*60)

# 测试1: 原始参数
position1 = 0.5 + df['composite_signal'] * 0.3
position1 = position1.clip(0.3, 1.0)

df['pos_change1'] = (position1.shift(1) - position1.shift(2)).abs().fillna(0)
df['cost1'] = df['pos_change1'] * (Config.COMMISSION_RATE + Config.SLIPPAGE_RATE)

ret1 = position1.shift(1) * df['equity_return'] + (1 - position1.shift(1)) * df['bond_return'] - df['cost1']
ret1 = ret1.dropna()

bench_ret = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
bench_ret = bench_ret.dropna()

# 指标计算
def calc_metrics(ret, bench_ret):
    nav = (1 + ret).cumprod()
    n_years = len(ret) / 12
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
        'annual_return': ann,
        'bench_annual': bench_ann,
        'excess': ann - bench_ann,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'nav': nav,
        'bench_nav': bench_nav,
        'drawdown': drawdown
    }

metrics1 = calc_metrics(ret1, bench_ret)

print(f"\n测试1: 原始参数 (复合信号, 50%+30%)")
print(f"年化收益率: {metrics1['annual_return']*100:.2f}%")
print(f"基准年化: {metrics1['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics1['excess']*100:.2f}%")
print(f"夏普比率: {metrics1['sharpe']:.2f}")
print(f"最大回撤: {metrics1['max_drawdown']*100:.2f}%")

# 测试2: RORO信号
position2 = 0.5 + df['roro_signal'] * 0.3
position2 = position2.clip(0.0, 1.0)

df['pos_change2'] = (position2.shift(1) - position2.shift(2)).abs().fillna(0)
df['cost2'] = df['pos_change2'] * (Config.COMMISSION_RATE + Config.SLIPPAGE_RATE)

ret2 = position2.shift(1) * df['equity_return'] + (1 - position2.shift(1)) * df['bond_return'] - df['cost2']
ret2 = ret2.dropna()

metrics2 = calc_metrics(ret2, bench_ret)

print(f"\n测试2: RORO信号 (50%+30%)")
print(f"年化收益率: {metrics2['annual_return']*100:.2f}%")
print(f"基准年化: {metrics2['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics2['excess']*100:.2f}%")
print(f"夏普比率: {metrics2['sharpe']:.2f}")
print(f"最大回撤: {metrics2['max_drawdown']*100:.2f}%")

# 测试3: 情绪信号绝对值
position3 = 0.8 + df['sentiment_signal'].abs() * 0.9
position3 = position3.clip(0.0, 1.0)

df['pos_change3'] = (position3.shift(1) - position3.shift(2)).abs().fillna(0)
df['cost3'] = df['pos_change3'] * (Config.COMMISSION_RATE + Config.SLIPPAGE_RATE)

ret3 = position3.shift(1) * df['equity_return'] + (1 - position3.shift(1)) * df['bond_return'] - df['cost3']
ret3 = ret3.dropna()

metrics3 = calc_metrics(ret3, bench_ret)

print(f"\n测试3: 情绪绝对值 (80%+90%)")
print(f"年化收益率: {metrics3['annual_return']*100:.2f}%")
print(f"基准年化: {metrics3['bench_annual']*100:.2f}%")
print(f"超额年化: {metrics3['excess']*100:.2f}%")
print(f"夏普比率: {metrics3['sharpe']:.2f}")
print(f"最大回撤: {metrics3['max_drawdown']*100:.2f}%")

# 对比表
print("\n" + "="*60)
print("结果对比")
print("="*60)
print(f"{'测试':<20} {'年化收益':>12} {'基准':>12} {'超额':>12} {'夏普':>10} {'最大回撤':>12}")
print("-"*70)
print(f"{'测试1-原始参数':<20} {metrics1['annual_return']*100:>+11.2f}% {metrics1['bench_annual']*100:>+11.2f}% {metrics1['excess']*100:>+11.2f}% {metrics1['sharpe']:>9.2f} {metrics1['max_drawdown']*100:>11.2f}%")
print(f"{'测试2-RORO信号':<20} {metrics2['annual_return']*100:>+11.2f}% {metrics2['bench_annual']*100:>+11.2f}% {metrics2['excess']*100:>+11.2f}% {metrics2['sharpe']:>9.2f} {metrics2['max_drawdown']*100:>11.2f}%")
print(f"{'测试3-情绪绝对值':<20} {metrics3['annual_return']*100:>+11.2f}% {metrics3['bench_annual']*100:>+11.2f}% {metrics3['excess']*100:>+11.2f}% {metrics3['sharpe']:>9.2f} {metrics3['max_drawdown']*100:>11.2f}%")
print("-"*70)
print(f"{'研报目标':<20} {'+11.40%':>12} {'+6.50%':>12} {'+4.90%':>12} {'-':>10} {'-':>12}")


# ============================================================
# 保存结果
# ============================================================
# 保存更新的数据
output_cols = ['date', 'year_month', 'hs300_return', 'guozheng_return', 'hsi_return',
                'sp500_return', 'nasdaq_return', 'cbond_return', 'agg_return',
                'gold_return', 'oil_return', 'equity_return', 'bond_return',
                'roro', 'roro_signal', 'sentiment_signal', 'composite_signal',
                'months_since_high']

df_output = df[output_cols].copy()
df_output.to_csv('C:/Users/yingx/strategy_final_monthly_v2.csv', index=False)
print("\n数据已保存到: strategy_final_monthly_v2.csv")

print("\n完成!")
