"""
情绪驱动下的股债配置策略 - 完全复现研报版
基于中泰金工研报

数据来源:
- A股: Tushare (沪深300, 中证全指)
- 港股: yfinance (恒生指数)
- 美股: yfinance (标普500, 纳斯达克)
- 债券: AKShare (中债综合指数) + yfinance (美国债券ETF)
- 黄金: yfinance (伦敦金期货)
- 原油: AKShare (WTI原油)
"""

import akshare as ak
import tushare as ts
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================

class Config:
    START_DATE = "2014-01-01"
    END_DATE = "2025-12-19"
    ROLLING_WINDOW = 60  # RORO计算滚动窗口 (按研报)

    # 仓位
    EQUITY_BASE = 0.50
    SIGNAL_ADJUST = 0.30
    MAX_POSITION = 1.00
    MIN_POSITION = 0.30

    TUSHARE_TOKEN = "4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863"


# ============================================================
# 数据获取
# ============================================================

def clean_data(df, price_cols):
    """
    数据清洗流程
    1. 删除重复值
    2. 处理逻辑错误值（负值、零值）
    3. 处理异常值（3σ原则）
    4. 处理空值（前向填充）
    """
    df = df.copy()

    # 1. 删除重复值
    df = df[~df.index.duplicated(keep='first')]

    # 2. 处理逻辑错误值
    for col in price_cols:
        if col in df.columns:
            # 价格不能为0或负数
            df[col] = df[col].apply(lambda x: np.nan if (pd.isna(x) or x <= 0) else x)

    # 3. 处理异常值（3σ原则）
    for col in price_cols:
        if col in df.columns and df[col].notna().sum() > 0:
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                lower = mean - 3 * std
                upper = mean + 3 * std
                df[col] = df[col].where((df[col] >= lower) & (df[col] <= upper), np.nan)

    # 4. 处理空值（前向填充）
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].fillna(method='ffill').fillna(method='bfill')

    return df


def fetch_china_equity():
    """获取A股数据"""
    print("[1] 获取A股数据...")

    ts.set_token(Config.TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 沪深300
    hs300 = pro.index_daily(ts_code='000300.SH',
                             start_date='20140101',
                             end_date='20251231')
    hs300 = hs300.sort_values('trade_date', ascending=True)
    hs300['date'] = pd.to_datetime(hs300['trade_date'])
    hs300['hs300_close'] = hs300['close']

    # 中证全指 (万得全A)
    winda = pro.index_daily(ts_code='000852.SH',
                            start_date='20140101',
                            end_date='20251231')
    winda = winda.sort_values('trade_date', ascending=True)
    winda['date'] = pd.to_datetime(winda['trade_date'])
    winda['winda_close'] = winda['close']

    # 合并
    df = hs300[['date', 'hs300_close']].merge(
        winda[['date', 'winda_close']], on='date', how='outer'
    )
    df = df.sort_values('date').reset_index(drop=True)
    df = df.set_index('date')

    # 数据清洗
    df = clean_data(df, ['hs300_close', 'winda_close'])

    # 计算收益率
    df['hs300_return'] = df['hs300_close'].pct_change()
    df['winda_return'] = df['winda_close'].pct_change()
    df['equity_return'] = df[['hs300_return', 'winda_return']].mean(axis=1)

    df = df.reset_index()
    print(f"  沪深300: {len(hs300)}条, 中证全指: {len(winda)}条")
    return df


def fetch_hk_equity():
    """获取港股数据"""
    print("[2] 获取港股数据...")

    hsi = yf.download("^HSI", start="2014-01-01", end="2026-01-01", progress=False)
    hsi = hsi.reset_index()
    if isinstance(hsi.columns, pd.MultiIndex):
        hsi.columns = [c[0] for c in hsi.columns]
    hsi['date'] = pd.to_datetime(hsi['Date'])
    hsi['hsi_close'] = hsi['Close']
    hsi['hsi_return'] = hsi['Close'].pct_change()

    print(f"  恒生指数: {len(hsi)}条")
    return hsi[['date', 'hsi_close', 'hsi_return']]


def fetch_us_equity():
    """获取美股数据"""
    print("[3] 获取美股数据...")

    # 标普500
    sp500 = yf.download("^GSPC", start="2014-01-01", end="2026-01-01", progress=False)
    sp500 = sp500.reset_index()
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = [c[0] for c in sp500.columns]
    sp500['date'] = pd.to_datetime(sp500['Date'])
    sp500['sp500_close'] = sp500['Close']
    sp500['sp500_return'] = sp500['Close'].pct_change()

    # 纳斯达克100
    nasdaq = yf.download("^NDX", start="2014-01-01", end="2026-01-01", progress=False)
    nasdaq = nasdaq.reset_index()
    if isinstance(nasdaq.columns, pd.MultiIndex):
        nasdaq.columns = [c[0] for c in nasdaq.columns]
    nasdaq['date'] = pd.to_datetime(nasdaq['Date'])
    nasdaq['nasdaq_close'] = nasdaq['Close']
    nasdaq['nasdaq_return'] = nasdaq['Close'].pct_change()

    # 合并美股
    us_df = sp500[['date', 'sp500_close', 'sp500_return']].merge(
        nasdaq[['date', 'nasdaq_close', 'nasdaq_return']], on='date', how='outer'
    )
    us_df = us_df.sort_values('date').reset_index(drop=True)
    us_df['us_return'] = us_df[['sp500_return', 'nasdaq_return']].mean(axis=1)

    print(f"  标普500: {len(sp500)}条, 纳斯达克: {len(nasdaq)}条")
    return us_df


def fetch_china_bond():
    """获取中债新综合财富指数"""
    print("[4] 获取中债新综合财富指数...")

    # 中债新综合指数
    cbond = ak.bond_new_composite_index_cbond()
    cbond['date'] = pd.to_datetime(cbond['date'])
    cbond = cbond.sort_values('date').reset_index(drop=True)
    cbond['cbond_close'] = cbond['value']
    cbond['cbond_return'] = cbond['value'].pct_change()

    print(f"  中债新综合指数: {len(cbond)}条")
    return cbond[['date', 'cbond_close', 'cbond_return']]


def fetch_us_bond():
    """获取美国债券ETF"""
    print("[5] 获取美国债券ETF...")

    # iShares核心美国总债券ETF (AGG)
    agg = yf.download("AGG", start="2014-01-01", end="2026-01-01", progress=False)
    agg = agg.reset_index()
    if isinstance(agg.columns, pd.MultiIndex):
        agg.columns = [c[0] for c in agg.columns]
    agg['date'] = pd.to_datetime(agg['Date'])
    agg['agg_close'] = agg['Close']
    agg['agg_return'] = agg['Close'].pct_change()

    print(f"  AGG: {len(agg)}条")
    return agg[['date', 'agg_close', 'agg_return']]


def fetch_gold():
    """获取伦敦金现货 (从用户上传的Excel文件)"""
    print("[6] 获取伦敦金现货...")

    # 从用户上传的Excel读取伦敦金数据
    gold = pd.read_excel(r'C:\Users\yingx\gold.xlsx')
    gold['date'] = pd.to_datetime(gold['date'])
    gold = gold.sort_values('date').reset_index(drop=True)
    gold['gold_return'] = gold['gold'].pct_change()

    print(f"  伦敦金现货: {len(gold)}条")
    return gold[['date', 'gold_return']]


def fetch_oil():
    """获取WTI原油 (日度数据)"""
    print("[7] 获取WTI原油...")

    # 用yfinance获取WTI原油期货日度数据
    oil = yf.download('CL=F', start="2014-01-01", end="2026-01-01", progress=False)
    oil = oil.reset_index()
    if isinstance(oil.columns, pd.MultiIndex):
        oil.columns = [c[0] for c in oil.columns]
    oil['date'] = pd.to_datetime(oil['Date'])
    oil = oil.sort_values('date').reset_index(drop=True)
    oil['oil_return'] = oil['Close'].pct_change()

    print(f"  WTI原油: {len(oil)}条")
    return oil[['date', 'oil_return']].copy()


def merge_all_data():
    """合并所有数据"""
    print("\n========== 获取所有数据 ==========")

    # 获取各类数据
    china_eq = fetch_china_equity()
    hk_eq = fetch_hk_equity()
    us_eq = fetch_us_equity()
    cn_bond = fetch_china_bond()
    us_bond = fetch_us_bond()
    gold = fetch_gold()
    oil = fetch_oil()

    # 合并数据 - 使用left join，以A股交易日为基础
    print("\n========== 合并数据 (对齐) ==========")
    df = china_eq[['date', 'equity_return']].copy()

    # 合并其他数据（前向填充空值）
    df = df.merge(hk_eq[['date', 'hsi_return']], on='date', how='left')
    df = df.merge(us_eq[['date', 'us_return']], on='date', how='left')
    df = df.merge(cn_bond[['date', 'cbond_return']], on='date', how='left')
    df = df.merge(us_bond[['date', 'agg_return']], on='date', how='left')
    df = df.merge(gold[['date', 'gold_return']], on='date', how='left')
    df = df.merge(oil[['date', 'oil_return']], on='date', how='left')

    # 排序和去重
    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'])

    # 计算全球权益平均收益 (按研报: A股+港股+美股)
    equity_cols = ['equity_return', 'hsi_return', 'us_return']
    df['global_equity_return'] = df[equity_cols].mean(axis=1, skipna=True)

    # 计算全球债券平均收益
    bond_cols = ['cbond_return', 'agg_return']
    df['global_bond_return'] = df[bond_cols].mean(axis=1, skipna=True)

    # 筛选日期
    df = df[(df['date'] >= Config.START_DATE) & (df['date'] <= Config.END_DATE)]
    df = df.reset_index(drop=True)

    print(f"合并后数据天数: {len(df)}")
    print(f"空值情况: equity={df['equity_return'].isna().sum()}, bond={df['global_bond_return'].isna().sum()}, gold={df['gold_return'].isna().sum()}, oil={df['oil_return'].isna().sum()}")

    return df

    print(f"\n数据范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"数据天数: {len(df)}")

    return df


# ============================================================
# RORO计算 (按研报)
# ============================================================

def calculate_roro(df, window=60):
    """
    计算RORO指数 (按研报公式)
    RORO = 第一主成分解释方差占比 = explained_variance_ratio_[0]
    使用所有7个资产的原始收益率
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    print(f"\n[8] 计算RORO指数 (窗口={window})...")

    # 使用所有7个资产的原始收益率（按研报）
    return_cols = ['equity_return', 'hsi_return', 'us_return',
                    'cbond_return', 'agg_return', 'gold_return', 'oil_return']

    roro_values = []
    scaler = StandardScaler()

    for i in range(len(df)):
        if i < window - 1:
            roro_values.append(np.nan)
        else:
            # 取滚动窗口数据
            window_data = df[return_cols].iloc[i-window+1:i+1].dropna(axis=1)

            if len(window_data.columns) < 2:
                roro_values.append(np.nan)
                continue

            try:
                # 标准化
                scaled_data = scaler.fit_transform(window_data)
                # PCA
                pca = PCA(n_components=len(window_data.columns))
                pca.fit(scaled_data)
                # RORO = 第一主成分解释方差占比
                roro = pca.explained_variance_ratio_[0]
                roro_values.append(roro)
            except:
                roro_values.append(np.nan)

    df = df.copy()
    df['roro'] = roro_values
    df['roro'] = df['roro'].fillna(method='bfill').fillna(method='ffill')

    # 计算RORO均值 (20日移动平均，按研报)
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
    print("\n[9] 生成交易信号...")

    df = df.copy()

    # RORO信号: 与均值比较
    df['roro_signal'] = 0
    df.loc[df['roro'] > df['roro_ma'], 'roro_signal'] = 1
    df.loc[df['roro'] < df['roro_ma'], 'roro_signal'] = -1

    # 情绪可解释收益率 = RORO * 权益收益率 (滞后一期)
    df['sentiment_return'] = df['roro'].shift(1) * df['global_equity_return']

    # 情绪可解释收益率信号: 变化方向
    df['sentiment_change'] = df['sentiment_return'].diff()
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1   # 上升 → 看多
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1  # 下降 → 看空

    # 复合信号
    df['composite_signal'] = df['roro_signal'] + df['sentiment_signal']

    return df


# ============================================================
# 月度调仓
# ============================================================

def resample_to_monthly(df):
    """月度调仓: 每月第一个交易日生成信号"""
    print("\n[10] 月度调仓处理...")

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
    print("\n[11] 执行月度回测...")

    df = df.copy()

    # 使用日频计算收益，信号来自月频
    df['year_month'] = df['date'].dt.to_period('M')

    # 获取月度信号
    monthly_signals = df.groupby('year_month').agg({
        'composite_signal': 'first',
        'global_equity_return': 'first',
        'global_bond_return': 'first'
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
    df_monthly['portfolio_return'] = df_monthly['equity_position'].shift(1) * df_monthly['global_equity_return'] + \
                                    df_monthly['bond_position'].shift(1) * df_monthly['global_bond_return']

    df_monthly = df_monthly.dropna(subset=['portfolio_return'])

    # 净值
    df_monthly['nav'] = (1 + df_monthly['portfolio_return']).cumprod()

    # 基准: 50-50
    df_monthly['benchmark_return'] = 0.5 * df_monthly['global_equity_return'] + 0.5 * df_monthly['global_bond_return']
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
    df = merge_all_data()

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

    # 保存 - 包含RORO详细数据
    output_cols = ['date', 'equity_return', 'hsi_return', 'us_return',
                   'cbond_return', 'agg_return', 'gold_return', 'oil_return',
                   'global_equity_return', 'global_bond_return',
                   'roro', 'roro_ma', 'roro_signal',
                   'sentiment_return', 'sentiment_signal', 'composite_signal',
                   'equity_position', 'nav', 'benchmark_nav']
    df_result[output_cols].to_csv('strategy_monthly.csv', index=False, encoding='utf-8-sig')
    print("\n结果已保存到 strategy_monthly.csv")

    # 输出RORO统计信息
    print("\n========== RORO统计 ==========")
    print(f"RORO均值: {df_result['roro'].mean():.4f}")
    print(f"RORO标准差: {df_result['roro'].std():.4f}")
    print(f"RORO最小值: {df_result['roro'].min():.4f}")
    print(f"RORO最大值: {df_result['roro'].max():.4f}")

    return df_result, results


if __name__ == "__main__":
    df, results = main()
