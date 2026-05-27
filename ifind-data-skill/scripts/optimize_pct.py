"""
分位数阈值优化
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import akshare as ak
import tushare as ts
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

print('重新计算RORO...')

ts.set_token('4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863')
pro = ts.pro_api()

# 数据
hs300 = pro.index_daily(ts_code='000300.SH', start_date='20140101', end_date='20251219')
hs300['date'] = pd.to_datetime(hs300['trade_date'])
hs300['hs300_return'] = hs300['close'].pct_change()

guozheng = pro.index_daily(ts_code='399317.SZ', start_date='20140101', end_date='20251219')
guozheng['date'] = pd.to_datetime(guozheng['trade_date'])
guozheng['guozheng_return'] = guozheng['close'].pct_change()

hsi = yf.download('^HSI', start='2014-01-01', end='2026-01-01', progress=False)
hsi = hsi.reset_index()
if isinstance(hsi.columns, pd.MultiIndex):
    hsi.columns = [c[0] for c in hsi.columns]
hsi['date'] = pd.to_datetime(hsi['Date'])
hsi['hsi_return'] = hsi['Close'].pct_change()

sp500 = yf.download('^GSPC', start='2014-01-01', end='2026-01-01', progress=False)
sp500 = sp500.reset_index()
if isinstance(sp500.columns, pd.MultiIndex):
    sp500.columns = [c[0] for c in sp500.columns]
sp500['date'] = pd.to_datetime(sp500['Date'])
sp500['sp500_return'] = sp500['Close'].pct_change()

nasdaq = yf.download('^NDX', start='2014-01-01', end='2026-01-01', progress=False)
nasdaq = nasdaq.reset_index()
if isinstance(nasdaq.columns, pd.MultiIndex):
    nasdaq.columns = [c[0] for c in nasdaq.columns]
nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()

cbond = ak.bond_new_composite_index_cbond()
cbond['date'] = pd.to_datetime(cbond['date'])
cbond['cbond_return'] = cbond['value'].pct_change()

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
df = hs300[['date', 'hs300_return']].merge(guozheng[['date', 'guozheng_return']], on='date', how='outer')
df = df.merge(hsi[['date', 'hsi_return']], on='date', how='outer')
df = df.merge(sp500[['date', 'sp500_return']], on='date', how='outer')
df = df.merge(nasdaq[['date', 'nasdaq_return']], on='date', how='outer')
df = df.merge(cbond[['date', 'cbond_return']], on='date', how='outer')
df = df.merge(agg[['date', 'agg_return']], on='date', how='outer')
df = df.merge(gold[['date', 'gold_return']], on='date', how='outer')
df = df.merge(oil[['date', 'oil_return']], on='date', how='outer')
df = df.sort_values('date').reset_index(drop=True)

# 填充
for col in df.columns:
    if col != 'date':
        df[col] = df[col].fillna(method='ffill').fillna(0)

df['equity_return'] = df[['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']].mean(axis=1, skipna=True)
df['bond_return'] = df[['cbond_return', 'agg_return']].mean(axis=1, skipna=True)

# 计算RORO
window = 60
asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return', 'cbond_return', 'agg_return', 'gold_return', 'oil_return']

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
print(f'RORO分位数: 5%={df["roro"].quantile(0.05):.4f}, 25%={df["roro"].quantile(0.25):.4f}')
print(f'           50%={df["roro"].quantile(0.50):.4f}, 75%={df["roro"].quantile(0.75):.4f}, 95%={df["roro"].quantile(0.95):.4f}')

# 月度化
df['year_month'] = df['date'].dt.to_period('M')
monthly = df.groupby('year_month').first().reset_index()

print()
print('='*70)
print('使用分位数阈值的回测结果')
print('='*70)

high_pcts = [0.70, 0.75, 0.80, 0.85, 0.90]
low_pcts = [0.10, 0.15, 0.20, 0.25, 0.30]

best_excess = -999
best_params = None

for high_pct in high_pcts:
    for low_pct in low_pcts:
        if low_pct >= high_pct:
            continue

        high = df['roro'].quantile(high_pct)
        low = df['roro'].quantile(low_pct)

        roro_change = monthly['roro'].diff()
        signal = np.where((monthly['roro'].shift(1) < low) & (roro_change > 0), 1, 0)
        signal = np.where((monthly['roro'].shift(1) > high) & (roro_change < 0), -1, signal)

        sentiment_ret = monthly['roro'].shift(1) * monthly['equity_return']
        sentiment_change = sentiment_ret.diff()
        sentiment_signal = np.where(sentiment_change > 0, 1, np.where(sentiment_change < 0, -1, 0))

        composite = np.where((signal == 1) & (sentiment_signal == 1), 2,
                           np.where((signal == -1) & (sentiment_signal == -1), -2, 0))

        position = 0.5 + composite * 0.3
        position = position.clip(0.3, 1.0)

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
            best_params = (high_pct, low_pct, high, low, ann, bench_ann)

        if excess > 0.02:
            print(f'高位{int(high_pct*100)}%/低{int(low_pct*100)}% (阈值{high:.3f}/{low:.3f}): 年化{ann*100:.2f}%, 基准{bench_ann*100:.2f}%, 超额{excess*100:.2f}%')

print()
print(f'最佳: 高{int(best_params[0]*100)}%/低{int(best_params[1]*100)}% (阈值{best_params[2]:.3f}/{best_params[3]:.3f})')
print(f'结果: 年化{best_params[4]*100:.2f}%, 基准{best_params[5]*100:.2f}%, 超额{best_excess*100:.2f}%')
print()
print('研报目标: 年化=11.40%, 基准=6.50%, 超额=4.90%')
