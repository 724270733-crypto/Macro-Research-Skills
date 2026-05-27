"""
情绪驱动下的股债配置策略 - 完全复现版
基于中泰金工研报 (完全按研报逻辑)

数据来源:
- A股: Tushare
- 港股: yfinance
- 美股: yfinance
- 债券: 用十年期国债收益率模拟 (无真实数据)

完全按照研报逻辑:
1. 月度调仓
2. RORO信号: RORO > 均值 → +1, RORO < 均值 → -1
3. 情绪可解释收益率信号: 上升 → +1, 下降 → -1
4. 复合信号 = RORO信号 + 情绪可解释收益率信号
5. 仓位 = 50% + 信号 * 30%, 范围[30%, 100%]
"""

import akshare as ak
import tushare as ts
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================

class Config:
    START_DATE = "2014-01-01"
    END_DATE = "2025-12-31"
    ROLLING_WINDOW = 20  # RORO计算滚动窗口

    # 仓位
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
    print("获取全球多资产数据")
    print("=" * 60)

    ts.set_token(Config.TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 1. A股数据
    print("\n[1] 获取A股数据...")
    hs300 = pro.index_daily(ts_code='000300.SH',
                             start_date='20140101',
                             end_date='20251231')
    # 数据是倒序的，需要反转
    hs300 = hs300.sort_values('trade_date', ascending=True)
    hs300['date'] = pd.to_datetime(hs300['trade_date'])
    hs300['hs300'] = hs300['close']
    hs300['hs300_return'] = hs300['close'].pct_change()

    winda = pro.index_daily(ts_code='000852.SH',
                            start_date='20140101',
                            end_date='20251231')
    winda = winda.sort_values('trade_date', ascending=True)
    winda['date'] = pd.to_datetime(winda['trade_date'])
    winda['winda'] = winda['close']
    winda['winda_return'] = winda['close'].pct_change()

    print(f"  沪深300: {len(hs300)}条")
    print(f"  中证全指: {len(winda)}条")

    # 2. 港股
    print("\n[2] 获取港股数据...")
    hsi = yf.download("^HSI", start="2014-01-01", end="2026-01-01", progress=False)
    hsi = hsi.reset_index()
    if isinstance(hsi.columns, pd.MultiIndex):
        hsi.columns = [c[0] for c in hsi.columns]
    hsi['date'] = pd.to_datetime(hsi['Date'])
    hsi['hsi'] = hsi['Close']
    hsi['hsi_return'] = hsi['Close'].pct_change()
    print(f"  恒生指数: {len(hsi)}条")

    # 3. 美股
    print("\n[3] 获取美股数据...")
    sp500 = yf.download("^GSPC", start="2014-01-01", end="2026-01-01", progress=False)
    sp500 = sp500.reset_index()
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = [c[0] for c in sp500.columns]
    sp500['date'] = pd.to_datetime(sp500['Date'])
    sp500['sp500'] = sp500['Close']
    sp500['sp500_return'] = sp500['Close'].pct_change()

    nasdaq = yf.download("^IXIC", start="2014-01-01", end="2026-01-01", progress=False)
    nasdaq = nasdaq.reset_index()
    if isinstance(nasdaq.columns, pd.MultiIndex):
        nasdaq.columns = [c[0] for c in nasdaq.columns]
    nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
    nasdaq['nasdaq'] = nasdaq['Close']
    nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()
    print(f"  标普500: {len(sp500)}条, 纳斯达克: {len(nasdaq)}条")

    # 4. 合并数据
    print("\n[4] 合并数据...")
    df = hs300[['date', 'hs300', 'hs300_return']].merge(
        winda[['date', 'winda', 'winda_return']], on='date', how='outer'
    )
    df = df.merge(hsi[['date', 'hsi', 'hsi_return']], on='date', how='outer')
    df = df.merge(sp500[['date', 'sp500', 'sp500_return']], on='date', how='outer')
    df = df.merge(nasdaq[['date', 'nasdaq', 'nasdaq_return']], on='date', how='outer')

    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'])

    # 5. 计算全球权益平均收益 (按研报: A股+港股+美股的平均)
    equity_cols = ['hs300_return', 'winda_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
    df['equity_return'] = df[equity_cols].mean(axis=1, skipna=True)

    # 6. 筛选日期
    df = df[(df['date'] >= Config.START_DATE) & (df['date'] <= Config.END_DATE)]
    df = df.reset_index(drop=True)

    print(f"\n数据范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"数据天数: {len(df)}")

    # 4. 债券数据 - 使用美国国债ETF (IEF 7-10年)
    print("\n[4.5] 获取美国债券ETF...")
    ief = yf.download("IEF", start="2014-01-01", end="2026-01-01", progress=False)
    ief = ief.reset_index()
    if isinstance(ief.columns, pd.MultiIndex):
        ief.columns = [c[0] for c in ief.columns]
    ief['date'] = pd.to_datetime(ief['Date'])
    ief['bond_ief'] = ief['Close']
    ief['bond_return'] = ief['Close'].pct_change()
    print(f"  IEF美国国债ETF: {len(ief)}条")

    # 合并债券数据
    df = df.merge(ief[['date', 'bond_return']], on='date', how='left')

    # 如果没有债券数据，用货币基金模拟
    if df['bond_return'].isna().all():
        print("[注意] IEF数据获取失败，使用货币基金模拟")
        np.random.seed(42)
        df['bond_return'] = np.random.normal(0.0001, 0.001, len(df))

    return df


# ============================================================
# RORO计算 (按研报)
# ============================================================

def calculate_roro(df, window=20):
    """
    计算RORO指数 (按研报公式)
    RORO = E1 / ΣEi (第一主成分解释方差占比)
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    print("\n[5] 计算RORO指数...")

    # 使用权益和债券收益率
    return_cols = ['equity_return', 'bond_return']

    roro_values = []
    roro_ma_values = []

    for i in range(len(df)):
        if i < window:
            roro_values.append(np.nan)
            roro_ma_values.append(np.nan)
        else:
            window_data = df[return_cols].iloc[i-window:i].fillna(0)

            if window_data.shape[1] < 2 or window_data.std().sum() == 0:
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

    # 计算RORO均值 (20日移动平均)
    df['roro_ma'] = df['roro'].rolling(window=20).mean()

    return df


# ============================================================
# 信号生成 (完全按研报)
# ============================================================

def generate_signals(df):
    """
    按研报生成信号:
    1. RORO信号: RORO > 均值 → +1, RORO < 均值 → -1
    2. 情绪可解释收益率信号: 上升 → +1, 下降 → -1
    3. 复合信号 = 两者相加
    """
    print("\n[6] 生成交易信号...")

    df = df.copy()

    # RORO信号: 与均值比较
    df['roro_signal'] = 0
    df.loc[df['roro'] > df['roro_ma'], 'roro_signal'] = 1
    df.loc[df['roro'] < df['roro_ma'], 'roro_signal'] = -1

    # 情绪可解释收益率 = RORO * 权益收益率 (滞后一期)
    df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']

    # 情绪可解释收益率信号: 变化方向
    df['sentiment_change'] = df['sentiment_return'].diff()
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1   # 上升 → 看多
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1  # 下降 → 看空

    # 复合信号
    df['composite_signal'] = df['roro_signal'] + df['sentiment_signal']

    return df


# ============================================================
# 月度调仓 (按研报)
# ============================================================

def resample_to_monthly(df):
    """月度调仓: 每月第一个交易日生成信号"""
    print("\n[7] 月度调仓处理...")

    df = df.copy()
    df['year_month'] = df['date'].dt.to_period('M')

    # 每月取第一个交易日
    monthly = df.groupby('year_month').first().reset_index()

    # 前向填充信号
    monthly['roro_signal'] = monthly['roro_signal'].fillna(method='ffill')
    monthly['sentiment_signal'] = monthly['sentiment_signal'].fillna(method='ffill')
    monthly['composite_signal'] = monthly['composite_signal'].fillna(method='ffill')

    print(f"月度数据: {len(monthly)}个月")

    return monthly


# ============================================================
# 仓位计算 (按研报)
# ============================================================

def calculate_position(df):
    """
    仓位计算 (按研报):
    - 基准: 50%权益 + 50%债券
    - 每个信号 ±30%
    - 范围: [30%, 100%]
    """
    df = df.copy()

    df['equity_position'] = Config.EQUITY_BASE + df['composite_signal'] * Config.SIGNAL_ADJUST
    df['equity_position'] = df['equity_position'].clip(Config.MIN_POSITION, Config.MAX_POSITION)
    df['bond_position'] = 1 - df['equity_position']

    return df


# ============================================================
# 回测 (月度)
# ============================================================

def backtest_monthly(df):
    """月度回测"""
    print("\n[8] 执行月度回测...")

    df = df.copy()

    # 使用日频计算收益，信号来自月频
    # 需要将月度信号广播到每日
    df['year_month'] = df['date'].dt.to_period('M')

    # 获取月度信号
    monthly_signals = df.groupby('year_month').agg({
        'composite_signal': 'first',
        'equity_return': 'first',
        'bond_return': 'first'
    }).reset_index()

    # 将月度信号应用到当月所有交易日
    df_monthly = df.copy()
    signal_map = dict(zip(monthly_signals['year_month'], monthly_signals['composite_signal']))
    df_monthly['monthly_signal'] = df_monthly['year_month'].map(signal_map)

    # 计算仓位 (使用月度信号)
    df_monthly['equity_position'] = Config.EQUITY_BASE + df_monthly['monthly_signal'] * Config.SIGNAL_ADJUST
    df_monthly['equity_position'] = df_monthly['equity_position'].clip(Config.MIN_POSITION, Config.MAX_POSITION)
    df_monthly['bond_position'] = 1 - df_monthly['equity_position']

    # 组合收益 (信号滞后一期应用)
    df_monthly['portfolio_return'] = df_monthly['equity_position'].shift(1) * df_monthly['equity_return'] + \
                                    df_monthly['bond_position'].shift(1) * df_monthly['bond_return']

    df_monthly = df_monthly.dropna(subset=['portfolio_return'])

    # 净值
    df_monthly['nav'] = (1 + df_monthly['portfolio_return']).cumprod()

    # 基准: 50-50
    df_monthly['benchmark_return'] = 0.5 * df_monthly['equity_return'] + 0.5 * df_monthly['bond_return']
    df_monthly['benchmark_nav'] = (1 + df_monthly['benchmark_return']).cumprod()

    # 指标
    total_return = df_monthly['nav'].iloc[-1] - 1
    n_years = len(df_monthly) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    annual_vol = df_monthly['portfolio_return'].std() * np.sqrt(252)
    sharpe = annual_return / annual_vol if annual_vol > 0 else 0

    cummax = df_monthly['nav'].cummax()
    drawdown = (df_monthly['nav'] - cummax) / cummax
    max_dd = drawdown.min()
    calmar = annual_return / abs(max_dd) if max_dd != 0 else 0

    avg_pos = df_monthly['equity_position'].mean()

    bench_total = df_monthly['benchmark_nav'].iloc[-1] - 1
    excess = total_return - bench_total

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'calmar': calmar,
        'avg_position': avg_pos,
        'bench_return': bench_total,
        'excess': excess
    }, df_monthly


# ============================================================
# 主程序
# ============================================================

def main():
    print("=" * 60)
    print("情绪驱动股债配置策略 - 完全复现研报版")
    print("=" * 60)

    # 1. 获取数据
    df = fetch_all_data()

    # 2. RORO
    df = calculate_roro(df, Config.ROLLING_WINDOW)

    # 3. 信号
    df = generate_signals(df)

    # 4. 月度调仓
    df_monthly = resample_to_monthly(df)

    # 5. 仓位
    df_monthly = calculate_position(df_monthly)

    # 6. 回测
    results, df_result = backtest_monthly(df_monthly)

    # 7. 输出
    print("\n" + "=" * 60)
    print("回测结果 (月度调仓)")
    print("=" * 60)
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"年化收益率: {results['annual_return']:.2%}")
    print(f"年化波动率: {results['annual_vol']:.2%}")
    print(f"夏普比率: {results['sharpe']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2%}")
    print(f"卡玛比率: {results['calmar']:.2f}")
    print(f"平均权益仓位: {results['avg_position']:.2%}")
    print(f"基准收益: {results['bench_return']:.2%}")
    print(f"超额收益: {results['excess']:.2%}")

    # 保存
    output_cols = ['date', 'equity_return', 'bond_return', 'roro', 'roro_ma',
                   'sentiment_return', 'composite_signal', 'equity_position', 'nav', 'benchmark_nav']
    df_result[output_cols].to_csv('strategy_monthly.csv', index=False, encoding='utf-8-sig')
    print("\n结果已保存到 strategy_monthly.csv")

    return df_result, results


if __name__ == "__main__":
    df, results = main()
