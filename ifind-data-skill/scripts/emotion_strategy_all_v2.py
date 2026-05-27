"""
情绪驱动下的股债配置策略 - 完整版
按研报规范实现三种策略和多种配置
"""
import akshare as ak
import tushare as ts
import yfinance as yf
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
    ROLLING_WINDOW = 60

    # 仓位配置
    EQUITY_BASE = 0.50
    SIGNAL_ADJUST = 0.30
    MAX_POSITION = 1.00
    MIN_POSITION = 0.30

    TUSHARE_TOKEN = "4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863"


# ============================================================
# 数据获取
# ============================================================
def fetch_all_data():
    """获取所有资产数据"""
    print("=" * 60)
    print("获取数据...")
    print("=" * 60)

    ts.set_token(Config.TUSHARE_TOKEN)
    pro = ts.pro_api()

    # A股 - 沪深300
    hs300 = pro.index_daily(ts_code='000300.SH', start_date='20140101', end_date='20251219')
    hs300 = hs300.sort_values('trade_date', ascending=True)
    hs300['date'] = pd.to_datetime(hs300['trade_date'])
    hs300['hs300'] = hs300['close']
    hs300['hs300_return'] = hs300['close'].pct_change()
    print(f"沪深300: {len(hs300)}条")

    # A股 - 国证A指 (替换万得全A)
    guozheng = pro.index_daily(ts_code='399317.SZ', start_date='20140101', end_date='20251219')
    guozheng = guozheng.sort_values('trade_date', ascending=True)
    guozheng['date'] = pd.to_datetime(guozheng['trade_date'])
    guozheng['guozheng'] = guozheng['close']
    guozheng['guozheng_return'] = guozheng['close'].pct_change()
    print(f"国证A指: {len(guozheng)}条")

    # 港股
    hsi = yf.download("^HSI", start="2014-01-01", end="2026-01-01", progress=False)
    hsi = hsi.reset_index()
    if isinstance(hsi.columns, pd.MultiIndex):
        hsi.columns = [c[0] for c in hsi.columns]
    hsi['date'] = pd.to_datetime(hsi['Date'])
    hsi['hsi'] = hsi['Close']
    hsi['hsi_return'] = hsi['Close'].pct_change()
    print(f"恒生指数: {len(hsi)}条")

    # 美股
    sp500 = yf.download("^GSPC", start="2014-01-01", end="2026-01-01", progress=False)
    sp500 = sp500.reset_index()
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = [c[0] for c in sp500.columns]
    sp500['date'] = pd.to_datetime(sp500['Date'])
    sp500['sp500'] = sp500['Close']
    sp500['sp500_return'] = sp500['Close'].pct_change()

    nasdaq = yf.download("^NDX", start="2014-01-01", end="2026-01-01", progress=False)
    nasdaq = nasdaq.reset_index()
    if isinstance(nasdaq.columns, pd.MultiIndex):
        nasdaq.columns = [c[0] for c in nasdaq.columns]
    nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
    nasdaq['nasdaq'] = nasdaq['Close']
    nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()
    print(f"标普500: {len(sp500)}条, 纳斯达克100: {len(nasdaq)}条")

    # 中债
    cbond = ak.bond_new_composite_index_cbond()
    cbond['date'] = pd.to_datetime(cbond['date'])
    cbond['cbond'] = cbond['value']
    cbond['cbond_return'] = cbond['value'].pct_change()
    print(f"中债新综合指数: {len(cbond)}条")

    # 美债
    agg = yf.download("AGG", start="2014-01-01", end="2026-01-01", progress=False)
    agg = agg.reset_index()
    if isinstance(agg.columns, pd.MultiIndex):
        agg.columns = [c[0] for c in agg.columns]
    agg['date'] = pd.to_datetime(agg['Date'])
    agg['agg'] = agg['Close']
    agg['agg_return'] = agg['Close'].pct_change()
    print(f"AGG美债ETF: {len(agg)}条")

    # 黄金
    gold = pd.read_excel('C:/Users/yingx/gold.xlsx')
    gold['date'] = pd.to_datetime(gold['date'])
    gold['gold'] = gold['gold']
    gold['gold_return'] = gold['gold'].pct_change()
    print(f"伦敦金: {len(gold)}条")

    # 原油
    oil = yf.download("CL=F", start="2014-01-01", end="2026-01-01", progress=False)
    oil = oil.reset_index()
    if isinstance(oil.columns, pd.MultiIndex):
        oil.columns = [c[0] for c in oil.columns]
    oil['date'] = pd.to_datetime(oil['Date'])
    oil['oil'] = oil['Close']
    oil['oil_return'] = oil['Close'].pct_change()
    print(f"WTI原油: {len(oil)}条")

    # 中国十年期国债收益率
    try:
        bond_10y = pro.bond_yield_curve(start_date='20140101', end_date='20251219')
        bond_10y = bond_10y[bond_10y['curve'] == '中债国债收益率曲线']
        bond_10y['date'] = pd.to_datetime(bond_10y['date'])
        bond_10y = bond_10y.sort_values('date')
        bond_10y['bond_10y_return'] = bond_10y['close'].pct_change()
        print(f"十年期国债: {len(bond_10y)}条")
    except:
        bond_10y = None
        print("十年期国债获取失败")

    # 合并数据
    df = hs300[['date', 'hs300', 'hs300_return']].copy()
    df = df.merge(guozheng[['date', 'guozheng', 'guozheng_return']], on='date', how='left')
    df = df.merge(hsi[['date', 'hsi', 'hsi_return']], on='date', how='left')
    df = df.merge(sp500[['date', 'sp500', 'sp500_return']], on='date', how='left')
    df = df.merge(nasdaq[['date', 'nasdaq', 'nasdaq_return']], on='date', how='left')
    df = df.merge(cbond[['date', 'cbond', 'cbond_return']], on='date', how='left')
    df = df.merge(agg[['date', 'agg', 'agg_return']], on='date', how='left')
    df = df.merge(gold[['date', 'gold', 'gold_return']], on='date', how='left')
    df = df.merge(oil[['date', 'oil', 'oil_return']], on='date', how='left')
    if bond_10y is not None:
        df = df.merge(bond_10y[['date', 'bond_10y_return']], on='date', how='left')

    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'])

    # 计算全球权益平均收益
    df['equity_return'] = df[['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']].mean(axis=1, skipna=True)

    # 计算全球债券平均收益
    df['bond_return'] = df[['cbond_return', 'agg_return']].mean(axis=1, skipna=True)

    # 筛选日期
    df = df[(df['date'] >= Config.START_DATE) & (df['date'] <= Config.END_DATE)]

    print(f"\n数据范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"数据天数: {len(df)}")

    return df


def calculate_roro(df, window=60):
    """计算RORO指数"""
    asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return',
                 'nasdaq_return', 'cbond_return', 'agg_return', 'gold_return', 'oil_return']

    roro_values = []
    for i in range(len(df)):
        if i < window:
            roro_values.append(np.nan)
        else:
            window_data = df[asset_cols].iloc[i-window:i].fillna(0)
            if window_data.shape[1] < 2:
                roro_values.append(np.nan)
                continue
            try:
                scaler = StandardScaler()
                scaled = scaler.fit_transform(window_data)
                pca = PCA()
                pca.fit(scaled)
                eigenvalues = pca.explained_variance_
                roro = eigenvalues[0] / eigenvalues.sum()
                roro_values.append(roro)
            except:
                roro_values.append(np.nan)

    df = df.copy()
    df['roro'] = roro_values
    df['roro'] = df['roro'].fillna(method='bfill').fillna(method='ffill')
    df['roro_ma'] = df['roro'].rolling(window=20).mean()

    return df


def generate_signals(df):
    """生成信号"""
    df = df.copy()

    # RORO变化
    df['roro_change'] = df['roro'].diff()

    # RORO信号 (研报: 高位回落=看跌, 低位上升=看涨)
    df['roro_signal'] = 0
    # 看涨: RORO > 20日均线 且 上升
    df.loc[(df['roro'] > df['roro_ma']) & (df['roro_change'] > 0), 'roro_signal'] = 1
    # 看跌: RORO < 20日均线 且 下降
    df.loc[(df['roro'] < df['roro_ma']) & (df['roro_change'] < 0), 'roro_signal'] = -1

    # 情绪可解释收益率 = RORO(滞后1期) × 权益收益率
    df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']
    df['sentiment_change'] = df['sentiment_return'].diff()

    # 情绪信号
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1

    # 复合信号 (研报逻辑)
    # RORO看多 + 情绪看多 = +2
    # RORO看跌 + 情绪看跌 = -2
    # 其他 = 0
    df['composite_signal'] = 0
    df.loc[(df['roro_signal'] == 1) & (df['sentiment_signal'] == 1), 'composite_signal'] = 2
    df.loc[(df['roro_signal'] == -1) & (df['sentiment_signal'] == -1), 'composite_signal'] = -2

    return df


def calculate_position(signal):
    """计算仓位"""
    position = Config.EQUITY_BASE + signal * Config.SIGNAL_ADJUST
    position = position.clip(Config.MIN_POSITION, Config.MAX_POSITION)
    return position


def backtest_strategy(df, equity_col, bond_col, signal_col, name):
    """回测策略"""
    df = df.copy()

    # 计算仓位
    df['position'] = calculate_position(df[signal_col])

    # 计算收益 (信号滞后一期)
    df['portfolio_return'] = df['position'].shift(1) * df[equity_col] + \
                            (1 - df['position'].shift(1)) * df[bond_col]
    df = df.dropna(subset=['portfolio_return'])

    # 净值
    df['nav'] = (1 + df['portfolio_return']).cumprod()

    # 基准
    df['benchmark_return'] = 0.5 * df[equity_col] + 0.5 * df[bond_col]
    df['benchmark_nav'] = (1 + df['benchmark_return']).cumprod()

    # 指标
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

    # 年度表现
    df['year'] = df['date'].dt.year
    yearly = []
    for year in sorted(df['year'].unique()):
        year_data = df[df['year'] == year]
        if len(year_data) > 1:
            yr_ret = year_data['nav'].iloc[-1] / year_data['nav'].iloc[0] - 1
            bench_ret = year_data['benchmark_nav'].iloc[-1] / year_data['benchmark_nav'].iloc[0] - 1
            yearly.append({
                'year': year,
                'return': yr_ret,
                'benchmark': bench_ret,
                'excess': yr_ret - bench_ret
            })

    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"{'='*60}")
    print(f"数据区间: {df['date'].min().date()} 至 {df['date'].max().date()}")
    print(f"总月数: {len(df)}")
    print(f"总收益率: {total_return*100:.2f}%")
    print(f"年化收益率: {annual_return*100:.2f}%")
    print(f"年化波动率: {annual_vol*100:.2f}%")
    print(f"夏普比率: {sharpe:.2f}")
    print(f"最大回撤: {max_dd*100:.2f}%")
    print(f"基准年化: {bench_ann*100:.2f}%")
    print(f"超额年化: {(annual_return - bench_ann)*100:.2f}%")

    # 平均仓位
    avg_pos = df['position'].mean()
    print(f"平均权益仓位: {avg_pos*100:.1f}%")

    return {
        'name': name,
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'bench_annual': bench_ann,
        'excess': annual_return - bench_ann,
        'avg_position': avg_pos,
        'yearly': yearly
    }, df


def main():
    print("=" * 60)
    print("情绪驱动股债配置策略 - 完整版")
    print("=" * 60)

    # 1. 获取数据
    df = fetch_all_data()

    # 2. 计算RORO
    print("\n计算RORO...")
    df = calculate_roro(df, Config.ROLLING_WINDOW)
    print(f"RORO范围: {df['roro'].min():.4f} ~ {df['roro'].max():.4f}")

    # 3. 生成信号
    print("\n生成信号...")
    df = generate_signals(df)
    print(f"RORO信号: {df['roro_signal'].value_counts().to_dict()}")
    print(f"情绪信号: {df['sentiment_signal'].value_counts().to_dict()}")
    print(f"复合信号: {df['composite_signal'].value_counts().to_dict()}")

    # 4. 月度化
    df['year_month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('year_month').first().reset_index()
    for col in ['roro_signal', 'sentiment_signal', 'composite_signal']:
        monthly[col] = monthly[col].fillna(method='ffill')

    results = {}

    # ============================================================
    # 策略1: 情绪驱动力(RORO)单信号策略 - 全球股债配置
    # ============================================================
    print("\n" + "="*60)
    print("策略1: 情绪驱动力(RORO)单信号策略 - 全球股债配置")
    print("="*60)
    roro_only, df_roro = backtest_strategy(
        monthly, 'equity_return', 'bond_return', 'roro_signal',
        'RORO单信号-全球配置'
    )
    results['roro_global'] = roro_only

    # ============================================================
    # 策略2: 情绪可解释收益率单信号策略 - 全球股债配置
    # ============================================================
    print("\n" + "="*60)
    print("策略2: 情绪可解释收益率单信号策略 - 全球股债配置")
    print("="*60)
    sentiment_only, df_sentiment = backtest_strategy(
        monthly, 'equity_return', 'bond_return', 'sentiment_signal',
        '情绪可解释收益率单信号-全球配置'
    )
    results['sentiment_global'] = sentiment_only

    # ============================================================
    # 策略3: 情绪复合信号策略 - 全球股债配置
    # ============================================================
    print("\n" + "="*60)
    print("策略3: 情绪复合信号策略 - 全球股债配置")
    print("="*60)
    composite_global, df_comp_global = backtest_strategy(
        monthly, 'equity_return', 'bond_return', 'composite_signal',
        '复合信号-全球配置'
    )
    results['composite_global'] = composite_global

    # ============================================================
    # 策略4: 复合信号 - 沪深300 + 国债
    # ============================================================
    print("\n" + "="*60)
    print("策略4: 复合信号 - 沪深300 + 国债")
    print("="*60)
    # 使用十年期国债，如果没有则用中债
    if 'bond_10y_return' in monthly.columns:
        bond_col = 'bond_10y_return'
    else:
        bond_col = 'cbond_return'

    composite_hs300, df_hs300 = backtest_strategy(
        monthly, 'hs300_return', bond_col, 'composite_signal',
        '复合信号-沪深300+国债'
    )
    results['composite_hs300'] = composite_hs300

    # ============================================================
    # 策略5: 复合信号 - 国证A指 + 国债
    # ============================================================
    print("\n" + "="*60)
    print("策略5: 复合信号 - 国证A指 + 国债")
    print("="*60)
    composite_guozheng, df_guozheng = backtest_strategy(
        monthly, 'guozheng_return', bond_col, 'composite_signal',
        '复合信号-国证A指+国债'
    )
    results['composite_guozheng'] = composite_guozheng

    # ============================================================
    # 输出汇总
    # ============================================================
    print("\n" + "="*70)
    print("结果汇总")
    print("="*70)
    print(f"{'策略':<40} {'年化收益':>10} {'基准':>10} {'超额':>10} {'夏普':>8}")
    print("-"*70)
    for key, res in results.items():
        print(f"{res['name']:<40} {res['annual_return']*100:>+9.2f}% {res['bench_annual']*100:>+9.2f}% {res['excess']*100:>+9.2f}% {res['sharpe']:>7.2f}")

    # 保存到Excel
    print("\n保存到Excel...")
    with pd.ExcelWriter('strategy_all_results.xlsx', engine='openpyxl') as writer:
        for key, res in results.items():
            df_res = res.get('yearly')
            if df_res is not None:
                pd.DataFrame(df_res).to_excel(writer, sheet_name=key[:30], index=False)

    print("已保存到 strategy_all_results.xlsx")

    return results


if __name__ == "__main__":
    results = main()
