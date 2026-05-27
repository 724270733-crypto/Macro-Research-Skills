"""
Weekly backtest with 1.5σ threshold
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# 计算阈值
df = pd.read_csv('C:/Users/yingx/strategy_final_monthly_v2.csv')
roro_mean = df['roro'].mean()
roro_std = df['roro'].std()

HIGH = roro_mean + 1.5 * roro_std
LOW = roro_mean - 1 * roro_std

print('RORO Mean: {:.4f}'.format(roro_mean))
print('RORO Std: {:.4f}'.format(roro_std))
print('High Threshold (mean+1.5σ): {:.4f}'.format(HIGH))
print('Low Threshold (mean-1σ): {:.4f}'.format(LOW))
print()

# 获取日度数据
print('Loading data...')
agg = pd.read_csv('C:/Users/yingx/AGG.csv')
agg['date'] = pd.to_datetime(agg['date'])
agg = agg.sort_values('date')
agg['price'] = pd.to_numeric(agg['AGG'], errors='coerce')
agg['agg_return'] = agg['price'].pct_change()

wti = pd.read_csv('C:/Users/yingx/WTI.csv')
wti['date'] = pd.to_datetime(wti['date'])
wti = wti.sort_values('date')
wti['price'] = pd.to_numeric(wti['WTI'].astype(str).str.strip(), errors='coerce')
wti['wti_return'] = wti['price'].pct_change()

print('Fetching daily data...')
import tushare as ts
import yfinance as yf
import akshare as ak

ts.set_token('4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863')
pro = ts.pro_api()

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

# 合并
daily_df = hs300[['date', 'hs300_return']].merge(guozheng[['date', 'guozheng_return']], on='date', how='outer')
daily_df = daily_df.merge(hsi[['date', 'hsi_return']], on='date', how='outer')
daily_df = daily_df.merge(sp500[['date', 'sp500_return']], on='date', how='outer')
daily_df = daily_df.merge(nasdaq[['date', 'nasdaq_return']], on='date', how='outer')
daily_df = daily_df.merge(cbond[['date', 'cbond_return']], on='date', how='outer')
daily_df = daily_df.merge(agg[['date', 'agg_return']], on='date', how='outer')
daily_df = daily_df.merge(wti[['date', 'wti_return']], on='date', how='outer')
daily_df = daily_df.sort_values('date').reset_index(drop=True)

for col in daily_df.columns:
    if col != 'date':
        daily_df[col] = daily_df[col].fillna(method='ffill').fillna(0)

daily_df['gold_return'] = 0

# 计算RORO - 20日窗口
window = 20
asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return', 'cbond_return', 'agg_return', 'wti_return', 'gold_return']

print('Calculating RORO...')
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

# 转为周度
daily_df['week'] = daily_df['date'].dt.to_period('W')
weekly = daily_df.groupby('week').last().reset_index()
weekly['date'] = weekly['week'].apply(lambda x: x.end_time.date())

print('Weekly data: {} weeks'.format(len(weekly)))

# 权益和债券收益
equity_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
bond_cols = ['cbond_return', 'agg_return']
weekly['equity_return'] = weekly[equity_cols].mean(axis=1, skipna=True)
weekly['bond_return'] = weekly[bond_cols].mean(axis=1, skipna=True)

# 信号
weekly['roro_change'] = weekly['roro'].diff()

# 最近高点
weekly['recent_high_date'] = pd.NaT
in_high_region = False
high_start_date = None

for i in range(len(weekly)):
    if weekly.iloc[i]['roro'] >= HIGH:
        if not in_high_region:
            in_high_region = True
            high_start_date = weekly.iloc[i]['date']
        weekly.iloc[i, weekly.columns.get_loc('recent_high_date')] = high_start_date
    else:
        if in_high_region:
            in_high_region = False

weekly['weeks_since_high'] = (pd.to_datetime(weekly['date']) - pd.to_datetime(weekly['recent_high_date'])).dt.days / 7

# RORO信号
weekly['roro_signal'] = 0
weekly.loc[(weekly['roro'].shift(1) < LOW) & (weekly['roro_change'] > 0), 'roro_signal'] = 1
weekly.loc[(weekly['roro'].shift(1) > HIGH) & (weekly['roro_change'] < 0) & (weekly['weeks_since_high'] <= 3), 'roro_signal'] = -1

# 情绪信号
weekly['sentiment_return'] = weekly['roro'].shift(1) * weekly['equity_return']
weekly['sentiment_change'] = weekly['sentiment_return'].diff()
weekly['sentiment_signal'] = 0
weekly.loc[weekly['sentiment_change'] > 0, 'sentiment_signal'] = 1
weekly.loc[weekly['sentiment_change'] < 0, 'sentiment_signal'] = -1

# 复合信号
weekly['composite_signal'] = 0
weekly.loc[(weekly['roro_signal'] == 1) & (weekly['sentiment_signal'] == 1), 'composite_signal'] = 2
weekly.loc[(weekly['roro_signal'] == -1) & (weekly['sentiment_signal'] == -1), 'composite_signal'] = -2

print()
print('Signal distribution:')
print('  RORO:', weekly['roro_signal'].value_counts().to_dict())
print('  Composite:', weekly['composite_signal'].value_counts().to_dict())

# 回测
COMMISSION = 0.001
SLIPPAGE = 0.001

def calc_metrics(ret, bench_ret):
    ret = ret.dropna()
    bench_ret = bench_ret.dropna()
    nav = (1 + ret).cumprod()
    n_years = len(ret) / 52
    total = nav.iloc[-1] / nav.iloc[0] - 1
    ann = (1 + total) ** (1/n_years) - 1
    bench_nav = (1 + bench_ret).cumprod()
    bench_total = bench_nav.iloc[-1] / bench_nav.iloc[0] - 1
    bench_ann = (1 + bench_total) ** (1/n_years) - 1
    vol = ret.std() * np.sqrt(52)
    sharpe = (ann - 0.02) / vol if vol > 0 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_dd = drawdown.min()
    return ann, bench_ann, ann - bench_ann, sharpe, max_dd, len(ret)

# 复合信号
position1 = 0.5 + weekly['composite_signal'] * 0.3
position1 = position1.clip(0.0, 1.0)
weekly['pos_change1'] = (position1.shift(1) - position1.shift(2)).abs().fillna(0)
weekly['cost1'] = weekly['pos_change1'] * (COMMISSION + SLIPPAGE)
weekly['ret1'] = position1.shift(1) * weekly['equity_return'] + (1 - position1.shift(1)) * weekly['bond_return'] - weekly['cost1']
weekly['bench_ret'] = 0.5 * weekly['equity_return'] + 0.5 * weekly['bond_return']

ann1, bench1, excess1, sharpe1, dd1, n_weeks = calc_metrics(weekly['ret1'], weekly['bench_ret'])

print()
print('='*70)
print('Weekly Backtest (HIGH=mean+1.5σ, LOW=mean-1σ)')
print('='*70)
print('Test 1: Composite Signal (50%+30%)')
print('  Annual: {:.2f}%, Benchmark: {:.2f}%, Excess: {:.2f}%'.format(ann1*100, bench1*100, excess1*100))
print('  Sharpe: {:.2f}, MaxDD: {:.2f}%, Rebalance: {}'.format(sharpe1, dd1*100, (weekly['pos_change1'] > 0).sum()))

# RORO信号
position2 = 0.5 + weekly['roro_signal'] * 0.3
position2 = position2.clip(0.0, 1.0)
weekly['pos_change2'] = (position2.shift(1) - position2.shift(2)).abs().fillna(0)
weekly['cost2'] = weekly['pos_change2'] * (COMMISSION + SLIPPAGE)
weekly['ret2'] = position2.shift(1) * weekly['equity_return'] + (1 - position2.shift(1)) * weekly['bond_return'] - weekly['cost2']

ann2, bench2, excess2, sharpe2, dd2, _ = calc_metrics(weekly['ret2'], weekly['bench_ret'])

print()
print('Test 2: RORO Signal (50%+30%)')
print('  Annual: {:.2f}%, Benchmark: {:.2f}%, Excess: {:.2f}%'.format(ann2*100, bench2*100, excess2*100))
print('  Sharpe: {:.2f}, MaxDD: {:.2f}%, Rebalance: {}'.format(sharpe2, dd2*100, (weekly['pos_change2'] > 0).sum()))

# 情绪绝对值
position3 = 0.8 + weekly['sentiment_signal'].abs() * 0.9
position3 = position3.clip(0.0, 1.0)
weekly['pos_change3'] = (position3.shift(1) - position3.shift(2)).abs().fillna(0)
weekly['cost3'] = weekly['pos_change3'] * (COMMISSION + SLIPPAGE)
weekly['ret3'] = position3.shift(1) * weekly['equity_return'] + (1 - position3.shift(1)) * weekly['bond_return'] - weekly['cost3']

ann3, bench3, excess3, sharpe3, dd3, _ = calc_metrics(weekly['ret3'], weekly['bench_ret'])

print()
print('Test 3: Sentiment Absolute (80%+90%)')
print('  Annual: {:.2f}%, Benchmark: {:.2f}%, Excess: {:.2f}%'.format(ann3*100, bench3*100, excess3*100))
print('  Sharpe: {:.2f}, MaxDD: {:.2f}%, Rebalance: {}'.format(sharpe3, dd3*100, (weekly['pos_change3'] > 0).sum()))

print()
print('Comparison:')
print('-'*70)
print('Test                       Annual    Benchmark   Excess     Sharpe   MaxDD')
print('-'*70)
print('Weekly-Composite           {:>+9.2f}% {:>+9.2f}% {:>+9.2f}% {:>7.2f} {:>9.2f}%'.format(ann1*100, bench1*100, excess1*100, sharpe1, dd1*100))
print('Weekly-RORO                {:>+9.2f}% {:>+9.2f}% {:>+9.2f}% {:>7.2f} {:>9.2f}%'.format(ann2*100, bench2*100, excess2*100, sharpe2, dd2*100))
print('Weekly-Sentiment           {:>+9.2f}% {:>+9.2f}% {:>+9.2f}% {:>7.2f} {:>9.2f}%'.format(ann3*100, bench3*100, excess3*100, sharpe3, dd3*100))
print('-'*70)
print('Research Target            +11.40%   +6.50%    +4.90%')
