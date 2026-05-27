"""
参数优化脚本 - 寻找最佳阈值组合
"""
import pandas as pd
import numpy as np
import akshare as ak
import tushare as ts
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print('重新获取数据并计算RORO...')

ts.set_token('4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863')
pro = ts.pro_api()

# 快速获取数据
hs300 = pro.index_daily(ts_code='000300.SH', start_date='20140101', end_date='20251219')
hs300['date'] = pd.to_datetime(hs300['trade_date'])
hs300['hs300_return'] = hs300['close'].pct_change()

guozheng = pro.index_daily(ts_code='399317.SZ', start_date='20140101', end_date='20251219')
guozheng['date'] = pd.to_datetime(guozheng['trade_date'])
guozheng['guozheng_return'] = guozheng['close'].pct_change()

import yfinance as yf
hsi = yf.download('^HSI', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
hsi['date'] = pd.to_datetime(hsi['Date'])
hsi['hsi_return'] = hsi['Close'].pct_change()

sp500 = yf.download('^GSPC', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
sp500['date'] = pd.to_datetime(sp500['Date'])
sp500['sp500_return'] = sp500['Close'].pct_change()

nasdaq = yf.download('^NDX', start='2014-01-01', end='2026-01-01', progress=False).reset_index()
nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()

cbond = ak.bond_new_composite_index_cbond()
cbond['date'] = pd.to_datetime(cbond['date'])
cbond['cbond_return'] = cbond['value'].pct_change()

# 本地数据
agg = pd.read_csv('C:/Users/yingx/.claude/skills/ifind-data-skill/scripts/AGG.csv')
agg['date'] = pd.to_datetime(agg['date'])
agg['agg_return'] = agg['AGG'].pct_change()

gold = pd.read_excel('C:/Users/yingx/gold.xlsx')
gold['date'] = pd.to_datetime(gold['date'])
gold['gold_return'] = gold['gold'].pct_change()

oil = pd.read_csv('C:/Users/yingx/.claude/skills/ifind-data-skill/scripts/WTI.csv')
oil['date'] = pd.to_datetime(oil['date'])
oil['oil_return'] = oil['WTI'].pct_change()

# 合并
df = hs300[['date', 'hs300_return']].copy()
df = df.merge(guozheng[['date', 'guozheng_return']], on='date', how='left')
df = df.merge(hsi[['date', 'hsi_return']], on='date', how='left')
df = df.merge(sp500[['date', 'sp500_return']], on='date', how='left')
df = df.merge(nasdaq[['date', 'nasdaq_return']], on='date', how='left')
df = df.merge(cbond[['date', 'cbond_return']], on='date', how='left')
df = df.merge(agg[['date', 'agg_return']], on='date', how='left')
df = df.merge(gold[['date', 'gold_return']], on='date', how='left')
df = df.merge(oil[['date', 'oil_return']], on='date', how='left')
df = df.sort_values('date').reset_index(drop=True)

# 填充缺失值
for col in df.columns:
    if col != 'date':
        df[col] = df[col].fillna(method='ffill').fillna(0)

# 权益收益
equity_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
bond_cols = ['cbond_return', 'agg_return']
df['equity_return'] = df[equity_cols].mean(axis=1, skipna=True)
df['bond_return'] = df[bond_cols].mean(axis=1, skipna=True)

print('计算RORO...')
# 计算RORO - 60天滚动窗口
window = 60
asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return',
             'nasdaq_return', 'cbond_return', 'agg_return', 'gold_return', 'oil_return']

roro_values = []
scaler = StandardScaler()

for i in range(len(df)):
    if i < window:
        roro_values.append(np.nan)
    else:
        window_data = df[asset_cols].iloc[i-window:i].fillna(0)
        try:
            scaled = scaler.fit_transform(window_data)
            pca = PCA()
            pca.fit(scaled)
            eigenvalues = pca.explained_variance_
            roro = eigenvalues[0] / eigenvalues.sum()
            roro_values.append(roro)
        except:
            roro_values.append(np.nan)

df['roro'] = roro_values
df['roro'] = df['roro'].fillna(method='bfill').fillna(method='ffill')
print(f'RORO范围: {df["roro"].min():.4f} ~ {df["roro"].max():.4f}')

# 月度化
df['year_month'] = df['date'].dt.to_period('M')
monthly = df.groupby('year_month').first().reset_index()

# 测试不同阈值
print()
print('='*70)
print('不同阈值组合的回测结果')
print('='*70)
print(f'{"高位阈值":>8} {"低位阈值":>8} {"年化收益":>10} {"基准":>10} {"超额":>10}')
print('-'*70)

high_thresholds = [0.25, 0.28, 0.30, 0.32, 0.35, 0.38, 0.40]
low_thresholds = [0.15, 0.18, 0.20, 0.22, 0.25]

best_excess = -999
best_params = (None, None)

for high in high_thresholds:
    for low in low_thresholds:
        if low >= high:
            continue

        # 计算信号
        roro_change = monthly['roro'].diff()

        # 低位上升: 上期<low, 本期上升
        signal = np.where((monthly['roro'].shift(1) < low) & (roro_change > 0), 1, 0)

        # 高位回落: 上期>high, 本期下降
        signal = np.where((monthly['roro'].shift(1) > high) & (roro_change < 0), -1, signal)

        monthly['signal'] = signal

        # 情绪信号
        sentiment_ret = monthly['roro'].shift(1) * monthly['equity_return']
        sentiment_change = sentiment_ret.diff()
        sentiment_signal = np.where(sentiment_change > 0, 1, np.where(sentiment_change < 0, -1, 0))

        # 复合信号
        composite = np.where((signal == 1) & (sentiment_signal == 1), 2,
                           np.where((signal == -1) & (sentiment_signal == -1), -2, 0))

        # 仓位
        position = 0.5 + composite * 0.3
        position = position.clip(0.3, 1.0)

        # 回测
        ret = position.shift(1) * monthly['equity_return'] + (1 - position.shift(1)) * monthly['bond_return']
        ret = ret.dropna()

        if len(ret) == 0:
            continue

        nav = (1 + ret).cumprod()
        n_years = len(ret) / 12
        total = nav.iloc[-1] / nav.iloc[0] - 1
        ann = (1 + total) ** (1/n_years) - 1

        bench_ret = 0.5 * monthly['equity_return'] + 0.5 * monthly['bond_return']
        bench_ret = bench_ret.dropna()
        bench_nav = (1 + bench_ret).cumprod()
        bench_total = bench_nav.iloc[-1] / bench_nav.iloc[0] - 1
        bench_ann = (1 + bench_total) ** (1/n_years) - 1

        excess = ann - bench_ann

        if excess > best_excess:
            best_excess = excess
            best_params = (high, low, ann, bench_ann)

        if excess > 0.01:
            print(f'{high:>8.2f} {low:>8.2f} {ann*100:>10.2f}% {bench_ann*100:>10.2f}% {excess*100:>10.2f}%')

print()
print(f'最佳组合: 高位={best_params[0]}, 低位={best_params[1]}')
print(f'最佳结果: 年化={best_params[2]*100:.2f}%, 基准={best_params[3]*100:.2f}%, 超额={best_excess*100:.2f}%')
