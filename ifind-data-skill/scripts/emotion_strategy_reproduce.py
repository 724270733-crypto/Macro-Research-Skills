"""
情绪驱动下的股债配置策略 - 研报复现版
基于中泰金工研报完全复刻
"""

import akshare as ak
import tushare as ts
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================

class Config:
    START_DATE = "2014-01-01"
    END_DATE = "2025-12-19"
    ROLLING_WINDOW = 60  # 研报中未明确，按实际需要

    # 仓位配置
    EQUITY_BASE = 0.50
    SIGNAL_ADJUST = 0.30
    MAX_POSITION = 1.00
    MIN_POSITION = 0.30

    TUSHARE_TOKEN = "4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863"


# ============================================================
# 数据获取
# ============================================================

def fetch_china_equity():
    """获取A股数据"""
    print("[1] 获取A股数据...")

    ts.set_token(Config.TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 沪深300
    hs300 = pro.index_daily(ts_code='000300.SH',
                            start_date='20140101',
                            end_date='20251219')
    hs300 = hs300.sort_values('trade_date', ascending=True)
    hs300['date'] = pd.to_datetime(hs300['trade_date'])
    hs300['hs300'] = hs300['close']
    hs300['hs300_return'] = hs300['close'].pct_change()

    # 万得全A
    winda = pro.index_daily(ts_code='000852.SH',
                            start_date='20140101',
                            end_date='20251219')
    winda = winda.sort_values('trade_date', ascending=True)
    winda['date'] = pd.to_datetime(winda['trade_date'])
    winda['winda'] = winda['close']
    winda['winda_return'] = winda['close'].pct_change()

    print(f"  沪深300: {len(hs300)}条, 万得全A: {len(winda)}条")

    return hs300[['date', 'hs300', 'hs300_return']], winda[['date', 'winda', 'winda_return']]


def fetch_hk_equity():
    """获取港股数据"""
    print("[2] 获取港股数据...")

    hsi = yf.download("^HSI", start="2014-01-01", end="2026-01-01", progress=False)
    hsi = hsi.reset_index()
    if isinstance(hsi.columns, pd.MultiIndex):
        hsi.columns = [c[0] for c in hsi.columns]
    hsi['date'] = pd.to_datetime(hsi['Date'])
    hsi['hsi'] = hsi['Close']
    hsi['hsi_return'] = hsi['Close'].pct_change()

    print(f"  恒生指数: {len(hsi)}条")
    return hsi[['date', 'hsi', 'hsi_return']]


def fetch_us_equity():
    """获取美股数据"""
    print("[3] 获取美股数据...")

    # 标普500
    sp500 = yf.download("^GSPC", start="2014-01-01", end="2026-01-01", progress=False)
    sp500 = sp500.reset_index()
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = [c[0] for c in sp500.columns]
    sp500['date'] = pd.to_datetime(sp500['Date'])
    sp500['sp500'] = sp500['Close']
    sp500['sp500_return'] = sp500['Close'].pct_change()

    # 纳斯达克100
    nasdaq = yf.download("^NDX", start="2014-01-01", end="2026-01-01", progress=False)
    nasdaq = nasdaq.reset_index()
    if isinstance(nasdaq.columns, pd.MultiIndex):
        nasdaq.columns = [c[0] for c in nasdaq.columns]
    nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
    nasdaq['nasdaq'] = nasdaq['Close']
    nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()

    print(f"  标普500: {len(sp500)}条, 纳斯达克100: {len(nasdaq)}条")

    return sp500[['date', 'sp500', 'sp500_return']], nasdaq[['date', 'nasdaq', 'nasdaq_return']]


def fetch_china_bond():
    """获取中债数据"""
    print("[4] 获取中债数据...")

    try:
        df = ak.bond_new_composite_index_cbond()
        print(f"  中债新综合指数: {len(df)}条")
        print(f"  列名: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"  获取失败: {e}")
        return None


def fetch_us_bond():
    """获取美债数据"""
    print("[5] 获取美债数据...")

    agg = yf.download("AGG", start="2014-01-01", end="2026-01-01", progress=False)
    agg = agg.reset_index()
    if isinstance(agg.columns, pd.MultiIndex):
        agg.columns = [c[0] for c in agg.columns]
    agg['date'] = pd.to_datetime(agg['Date'])
    agg['agg'] = agg['Close']
    agg['agg_return'] = agg['Close'].pct_change()

    print(f"  AGG: {len(agg)}条")
    return agg[['date', 'agg', 'agg_return']]


def fetch_gold():
    """获取伦敦金数据"""
    print("[6] 获取黄金数据...")

    try:
        gold_df = pd.read_excel('C:/Users/yingx/gold.xlsx')
        gold_df['date'] = pd.to_datetime(gold_df['date'])
        # 列名是 'gold' 不是 'close'
        gold_df['gold_return'] = gold_df['gold'].pct_change()
        print(f"  伦敦金: {len(gold_df)}条")
        return gold_df[['date', 'gold', 'gold_return']]
    except Exception as e:
        print(f"  获取失败: {e}")
        return None


def fetch_oil():
    """获取原油数据"""
    print("[7] 获取原油数据...")

    oil = yf.download("CL=F", start="2014-01-01", end="2026-01-01", progress=False)
    oil = oil.reset_index()
    if isinstance(oil.columns, pd.MultiIndex):
        oil.columns = [c[0] for c in oil.columns]
    oil['date'] = pd.to_datetime(oil['Date'])
    oil['oil'] = oil['Close']
    oil['oil_return'] = oil['Close'].pct_change()

    print(f"  WTI原油: {len(oil)}条")
    return oil[['date', 'oil', 'oil_return']]


def merge_all_data():
    """合并所有数据"""
    print("\n========== 合并所有数据 ==========")

    # 获取各资产数据
    hs300, winda = fetch_china_equity()
    hsi = fetch_hk_equity()
    sp500, nasdaq = fetch_us_equity()
    cbond = fetch_china_bond()
    agg = fetch_us_bond()
    gold = fetch_gold()
    oil = fetch_oil()

    # 以A股为基础合并
    df = hs300.copy()

    # 合并其他权益数据
    df = df.merge(winda[['date', 'winda', 'winda_return']], on='date', how='left')
    df = df.merge(hsi[['date', 'hsi', 'hsi_return']], on='date', how='left')
    df = df.merge(sp500[['date', 'sp500', 'sp500_return']], on='date', how='left')
    df = df.merge(nasdaq[['date', 'nasdaq', 'nasdaq_return']], on='date', how='left')

    # 合并债券数据
    if cbond is not None and len(cbond) > 0:
        # 处理中债数据
        if 'date' in cbond.columns:
            cbond['date'] = pd.to_datetime(cbond['date'])
        elif '日期' in cbond.columns:
            cbond = cbond.rename(columns={'日期': 'date'})
            cbond['date'] = pd.to_datetime(cbond['date'])

        # 找到收益率列 - 中债返回的是指数值，不是收益率
        if 'value' in cbond.columns:
            cbond['cbond'] = cbond['value']
            cbond['cbond_return'] = cbond['cbond'].pct_change()
            cbond = cbond[['date', 'cbond', 'cbond_return']]
        else:
            # 尝试直接使用
            cbond_cols = [c for c in cbond.columns if c != 'date']
            if cbond_cols:
                cbond['cbond'] = cbond[cbond_cols[0]]
                cbond['cbond_return'] = cbond['cbond'].pct_change()
                cbond = cbond[['date', 'cbond', 'cbond_return']]

        df = df.merge(cbond, on='date', how='left')

    df = df.merge(agg[['date', 'agg_return']], on='date', how='left')

    # 合并商品数据
    if gold is not None:
        df = df.merge(gold[['date', 'gold_return']], on='date', how='left')
    if oil is not None:
        df = df.merge(oil[['date', 'oil_return']], on='date', how='left')

    # 排序去重
    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'])

    # 计算全球权益平均收益
    equity_cols = ['hs300_return', 'winda_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
    df['equity_return'] = df[equity_cols].mean(axis=1, skipna=True)

    # 债券平均收益
    bond_cols = ['cbond_return', 'agg_return']
    df['bond_return'] = df[bond_cols].mean(axis=1, skipna=True)

    # 筛选日期
    df = df[(df['date'] >= Config.START_DATE) & (df['date'] <= Config.END_DATE)]

    print(f"\n数据范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"数据天数: {len(df)}")
    print(f"权益收益列: {equity_cols}")
    print(f"债券收益列: {bond_cols}")

    return df


# ============================================================
# RORO计算
# ============================================================

def calculate_roro(df, window=60):
    """
    计算RORO指数（研报复现版）
    RORO = 第一主成分解释方差占比
    """
    print(f"\n========== 计算RORO (窗口={window}) ==========")

    # 使用全部7个资产
    asset_cols = ['hs300_return', 'winda_return', 'hsi_return', 'sp500_return',
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
            except Exception as e:
                roro_values.append(np.nan)

    df = df.copy()
    df['roro'] = roro_values
    df['roro'] = df['roro'].fillna(method='bfill').fillna(method='ffill')

    # RORO移动平均
    df['roro_ma'] = df['roro'].rolling(window=20).mean()

    print(f"RORO范围: {df['roro'].min():.4f} ~ {df['roro'].max():.4f}")
    print(f"RORO均值: {df['roro'].mean():.4f}")

    return df


# ============================================================
# 信号生成（研报规范）
# ============================================================

def generate_signals(df):
    """
    按研报规范生成信号:

    1. RORO信号:
       - 看多: RORO低位上升（当前RORO > 20日均线，且RORO上升）
       - 看跌: RORO高位快速回落（当前RORO < 20日均线，且RORO下降）
       - 无信号: 其他情况

    2. 情绪可解释收益率信号:
       - 情绪可解释收益率 = RORO(滞后1期) × 权益收益率
       - 上升: +1
       - 下降: -1

    3. 复合信号:
       - RORO看多 + 情绪看多 = +2
       - RORO看跌 + 情绪看跌 = -2
       - 其他 = 0
    """
    print("\n========== 生成信号 ==========")

    df = df.copy()

    # RORO变化
    df['roro_change'] = df['roro'].diff()

    # RORO信号
    df['roro_signal'] = 0
    # 看多: RORO > 均值 且 RORO上升
    df.loc[(df['roro'] > df['roro_ma']) & (df['roro_change'] > 0), 'roro_signal'] = 1
    # 看跌: RORO < 均值 且 RORO下降
    df.loc[(df['roro'] < df['roro_ma']) & (df['roro_change'] < 0), 'roro_signal'] = -1

    # 情绪可解释收益率 = RORO(滞后1期) × 权益收益率
    df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']
    df['sentiment_change'] = df['sentiment_return'].diff()

    # 情绪信号
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1

    # 复合信号
    df['composite_signal'] = 0
    # 两者同向: +2 或 -2
    df.loc[(df['roro_signal'] == 1) & (df['sentiment_signal'] == 1), 'composite_signal'] = 2
    df.loc[(df['roro_signal'] == -1) & (df['sentiment_signal'] == -1), 'composite_signal'] = -2

    # RORO信号分布
    print(f"RORO信号分布: {df['roro_signal'].value_counts().to_dict()}")
    print(f"情绪信号分布: {df['sentiment_signal'].value_counts().to_dict()}")
    print(f"复合信号分布: {df['composite_signal'].value_counts().to_dict()}")

    return df


# ============================================================
# 月度调仓
# ============================================================

def resample_to_monthly(df):
    """月度调仓"""
    print("\n========== 月度调仓 ==========")

    df = df.copy()
    df['year_month'] = df['date'].dt.to_period('M')

    # 每月第一个交易日
    monthly = df.groupby('year_month').first().reset_index()

    # 前向填充信号
    for col in ['roro_signal', 'sentiment_signal', 'composite_signal']:
        monthly[col] = monthly[col].fillna(method='ffill')

    print(f"月度数据: {len(monthly)}个月")

    return monthly


# ============================================================
# 仓位计算
# ============================================================

def calculate_position(df):
    """
    仓位 = 50% + 信号 × 30%
    范围: [30%, 100%]
    """
    df = df.copy()

    df['equity_position'] = Config.EQUITY_BASE + df['composite_signal'] * Config.SIGNAL_ADJUST
    df['equity_position'] = df['equity_position'].clip(Config.MIN_POSITION, Config.MAX_POSITION)
    df['bond_position'] = 1 - df['equity_position']

    print(f"仓位分布: {df['equity_position'].value_counts().to_dict()}")

    return df


# ============================================================
# 回测
# ============================================================

def backtest(df):
    """月度回测"""
    print("\n========== 回测 ==========")

    df = df.copy()

    # 使用滞后一期仓位
    df['portfolio_return'] = df['equity_position'].shift(1) * df['equity_return'] + \
                            df['bond_position'].shift(1) * df['bond_return']

    df = df.dropna(subset=['portfolio_return'])

    # 净值
    df['nav'] = (1 + df['portfolio_return']).cumprod()

    # 基准 (50-50)
    df['benchmark_return'] = 0.5 * df['equity_return'] + 0.5 * df['bond_return']
    df['benchmark_nav'] = (1 + df['benchmark_return']).cumprod()

    # 指标计算
    n_years = len(df) / 12

    total_return = df['nav'].iloc[-1] / df['nav'].iloc[0] - 1
    annual_return = (1 + total_return) ** (1 / n_years) - 1

    annual_vol = df['portfolio_return'].std() * np.sqrt(12)
    sharpe = (annual_return - 0.02) / annual_vol if annual_vol > 0 else 0

    cummax = df['nav'].cummax()
    drawdown = (df['nav'] - cummax) / cummax
    max_dd = drawdown.min()

    bench_total = df['benchmark_nav'].iloc[-1] / df['benchmark_nav'].iloc[0] - 1
    bench_ann = (1 + bench_total) ** (1 / n_years) - 1

    print("\n" + "=" * 50)
    print("回测结果")
    print("=" * 50)
    print(f"数据区间: {df['date'].min().date()} 至 {df['date'].max().date()}")
    print(f"总月数: {len(df)}")
    print(f"总收益率: {total_return*100:.2f}%")
    print(f"年化收益率: {annual_return*100:.2f}%")
    print(f"年化波动率: {annual_vol*100:.2f}%")
    print(f"夏普比率: {sharpe:.2f}")
    print(f"最大回撤: {max_dd*100:.2f}%")
    print(f"基准年化: {bench_ann*100:.2f}%")
    print(f"超额年化: {(annual_return - bench_ann)*100:.2f}%")

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_vol': annual_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'bench_annual': bench_ann,
        'excess': annual_return - bench_ann
    }, df


# ============================================================
# 输出Excel
# ============================================================

def output_to_excel(df_daily, df_monthly, results):
    """输出所有数据到Excel"""
    print("\n========== 输出Excel ==========")

    # 确保df_monthly有year列
    if 'year' not in df_monthly.columns:
        df_monthly['year'] = df_monthly['date'].dt.year

    with pd.ExcelWriter('strategy_reproduction.xlsx', engine='openpyxl') as writer:
        # 日度数据
        daily_cols = ['date', 'hs300', 'winda', 'hsi', 'sp500', 'nasdaq',
                      'equity_return', 'bond_return', 'roro', 'roro_ma',
                      'roro_signal', 'sentiment_return', 'sentiment_signal', 'composite_signal']
        daily_cols = [c for c in daily_cols if c in df_daily.columns]
        df_daily[daily_cols].to_excel(writer, sheet_name='日度数据', index=False)

        # 月度数据
        monthly_cols = ['date', 'year', 'equity_return', 'bond_return', 'roro', 'roro_ma',
                       'composite_signal', 'equity_position', 'nav', 'benchmark_nav']
        monthly_cols = [c for c in monthly_cols if c in df_monthly.columns]
        df_monthly[monthly_cols].to_excel(writer, sheet_name='月度数据', index=False)

        # 回测结果
        results_df = pd.DataFrame([results])
        results_df.to_excel(writer, sheet_name='回测结果', index=False)

        # 年度表现
        yearly = []
        for year in df_monthly['year'].unique():
            year_data = df_monthly[df_monthly['year'] == year]
            if len(year_data) > 1 and 'nav' in year_data.columns:
                yr_ret = year_data['nav'].iloc[-1] / year_data['nav'].iloc[0] - 1
                bench_ret = year_data['benchmark_nav'].iloc[-1] / year_data['benchmark_nav'].iloc[0] - 1
                yearly.append({
                    'year': year,
                    'strategy_return': yr_ret,
                    'benchmark_return': bench_ret,
                    'excess': yr_ret - bench_ret
                })
        pd.DataFrame(yearly).to_excel(writer, sheet_name='年度表现', index=False)

    print("已保存到 strategy_reproduction.xlsx")


# ============================================================
# 主程序
# ============================================================

def main():
    print("=" * 60)
    print("情绪驱动股债配置策略 - 研报复现版")
    print("=" * 60)

    # 1. 获取数据
    df = merge_all_data()

    # 2. 计算RORO
    df = calculate_roro(df, Config.ROLLING_WINDOW)

    # 3. 生成信号
    df = generate_signals(df)

    # 4. 月度调仓
    df_monthly = resample_to_monthly(df)

    # 5. 计算仓位
    df_monthly = calculate_position(df_monthly)

    # 6. 回测
    results, df_result = backtest(df_monthly)

    # 7. 输出Excel
    output_to_excel(df, df_monthly, results)

    return df, df_monthly, results


if __name__ == "__main__":
    df_daily, df_monthly, results = main()
