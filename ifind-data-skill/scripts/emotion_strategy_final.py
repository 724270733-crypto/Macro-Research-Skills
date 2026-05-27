"""
情绪驱动股债配置策略 - 最终版
按研报规范实现（修正信号逻辑 + 十年期国债）
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
    ROLLING_WINDOW = 20  # 用户指定：20个交易日

    # 仓位
    EQUITY_BASE = 0.50
    SIGNAL_ADJUST = 0.30
    MAX_POSITION = 1.00
    MIN_POSITION = 0.30

    # 研报参数 - 信号阈值
    HIGH_THRESHOLD = 0.38   # 高位阈值
    LOW_THRESHOLD = 0.28     # 低位阈值

    # 研报参数 - 滑点和手续费
    COMMISSION_RATE = 0.001   # 手续费率 0.1%
    SLIPPAGE_RATE = 0.001     # 滑点 0.1%

    TUSHARE_TOKEN = "4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863"


# ============================================================
# 数据获取
# ============================================================
def fetch_all_data():
    """获取所有数据"""
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

    # A股 - 国证A指
    try:
        guozheng = pro.index_daily(ts_code='399317.SZ', start_date='20140101', end_date='20251219')
        if guozheng is not None and len(guozheng) > 0:
            guozheng = guozheng.sort_values('trade_date', ascending=True)
            guozheng['date'] = pd.to_datetime(guozheng['trade_date'])
            guozheng['guozheng'] = guozheng['close']
            guozheng['guozheng_return'] = guozheng['close'].pct_change()
        else:
            guozheng = pd.DataFrame()
    except Exception as e:
        print(f"国证A指获取失败: {e}")
        guozheng = pd.DataFrame()
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

    # 中债新综合指数
    cbond = ak.bond_new_composite_index_cbond()
    cbond['date'] = pd.to_datetime(cbond['date'])
    cbond['cbond'] = cbond['value']
    cbond['cbond_return'] = cbond['value'].pct_change()
    print(f"中债新综合指数: {len(cbond)}条")

    # 美债 - 使用本地数据
    agg_local = pd.read_csv('C:/Users/yingx/.claude/skills/ifind-data-skill/scripts/AGG.csv')
    agg_local['date'] = pd.to_datetime(agg_local['date'])
    agg_local = agg_local.sort_values('date')
    agg_local['agg'] = agg_local['AGG']
    agg_local['agg_return'] = agg_local['agg'].pct_change()
    print(f"AGG美债ETF(本地): {len(agg_local)}条")

    # 黄金
    gold = pd.read_excel('C:/Users/yingx/gold.xlsx')
    gold['date'] = pd.to_datetime(gold['date'])
    gold['gold'] = gold['gold']
    gold['gold_return'] = gold['gold'].pct_change()
    print(f"伦敦金: {len(gold)}条")

    # 原油 - 使用本地数据
    oil_local = pd.read_csv('C:/Users/yingx/.claude/skills/ifind-data-skill/scripts/WTI.csv')
    oil_local['date'] = pd.to_datetime(oil_local['date'])
    oil_local = oil_local.sort_values('date')
    oil_local['oil'] = oil_local['WTI']
    oil_local['oil_return'] = oil_local['oil'].pct_change()
    print(f"WTI原油(本地): {len(oil_local)}条")

    # 十年期国债收益率 (使用AKShare)
    try:
        bond_10y = ak.bond_zh_us_rate()
        # 找到十年期国债列
        col_10y = None
        for c in bond_10y.columns:
            if '10年' in c:
                col_10y = c
                break
        if col_10y:
            bond_10y = bond_10y[['日期', col_10y]].copy()
            bond_10y.columns = ['date', 'bond_10y']
            bond_10y['date'] = pd.to_datetime(bond_10y['date'])
            bond_10y = bond_10y.sort_values('date')
            bond_10y['bond_10y_return'] = bond_10y['bond_10y'].pct_change() / 100  # 收益率转换
            bond_10y = bond_10y[['date', 'bond_10y_return']]
            print(f"十年期国债: {len(bond_10y)}条")
    except Exception as e:
        print(f"十年期国债获取失败: {e}")
        bond_10y = None

    # 合并
    df = hs300[['date', 'hs300', 'hs300_return']].copy()
    df = df.merge(guozheng[['date', 'guozheng', 'guozheng_return']], on='date', how='left')
    df = df.merge(hsi[['date', 'hsi', 'hsi_return']], on='date', how='left')
    df = df.merge(sp500[['date', 'sp500', 'sp500_return']], on='date', how='left')
    df = df.merge(nasdaq[['date', 'nasdaq', 'nasdaq_return']], on='date', how='left')
    df = df.merge(cbond[['date', 'cbond', 'cbond_return']], on='date', how='left')
    df = df.merge(agg_local[['date', 'agg', 'agg_return']], on='date', how='left')
    df = df.merge(gold[['date', 'gold', 'gold_return']], on='date', how='left')
    df = df.merge(oil_local[['date', 'oil', 'oil_return']], on='date', how='left')
    if bond_10y is not None:
        df = df.merge(bond_10y, on='date', how='left')

    df = df.sort_values('date').reset_index(drop=True)
    df = df.drop_duplicates(subset=['date'])

    # 缺失数据用前值补全
    return_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return',
                   'nasdaq_return', 'cbond_return', 'agg_return', 'gold_return', 'oil_return']
    for col in return_cols:
        if col in df.columns:
            df[col] = df[col].fillna(method='ffill')
    # 收益率列用0填充第一个NA
    for col in return_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 权益收益 (5宫格平均)
    equity_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
    df['equity_return'] = df[equity_cols].mean(axis=1, skipna=True)

    # 债券收益 (2宫格平均)
    bond_cols = ['cbond_return', 'agg_return']
    df['bond_return'] = df[bond_cols].mean(axis=1, skipna=True)

    # 筛选日期
    df = df[(df['date'] >= Config.START_DATE) & (df['date'] <= Config.END_DATE)]

    print(f"\n数据范围: {df['date'].min()} 至 {df['date'].max()}")
    print(f"数据天数: {len(df)}")

    return df


# ============================================================
# RORO计算 (研报公式)
# ============================================================
def calc_roro(df, window=60):
    """按研报公式计算RORO"""
    asset_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return',
                 'nasdaq_return', 'cbond_return', 'agg_return', 'gold_return', 'oil_return']

    roro_values = []
    scaler = StandardScaler()

    for i in range(len(df)):
        if i < window:
            roro_values.append(np.nan)
        else:
            window_data = df[asset_cols].iloc[i-window:i].fillna(0)
            if window_data.shape[1] < 2:
                roro_values.append(np.nan)
                continue
            try:
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


# ============================================================
# 信号生成 (研报逻辑 - 最终版)
# ============================================================
def generate_signals(df):
    """按研报规范生成信号"""
    df = df.copy()

    # 参数设置
    HIGH_THRESHOLD = 0.38  # 高位阈值
    LOW_THRESHOLD = 0.28   # 低位阈值
    WINDOW = 20            # 滚动窗口

    # 更新RORO均值窗口
    df['roro_ma'] = df['roro'].rolling(window=WINDOW).mean()

    # RORO变化
    df['roro_change'] = df['roro'].diff()

    # 记录最近高点日期（用于判断是否在3个月内）
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

    # RORO信号 - 研报定义
    # 低位上升：上期<0.28，本期>上期 → +1
    df['roro_signal'] = 0
    df.loc[(df['roro'].shift(1) < LOW_THRESHOLD) & (df['roro_change'] > 0), 'roro_signal'] = 1

    # 快速回落：前期>0.38，本期<上期，且距高点≤3个月 → -1
    df.loc[(df['roro'].shift(1) > HIGH_THRESHOLD) &
           (df['roro_change'] < 0) &
           (df['months_since_high'] <= 3), 'roro_signal'] = -1

    # 情绪可解释收益率 = RORO(滞后) × 权益收益率
    df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']
    df['sentiment_change'] = df['sentiment_return'].diff()

    # 情绪信号
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1

    # 复合信号 - 研报定义
    df['composite_signal'] = 0
    df.loc[(df['roro_signal'] == 1) & (df['sentiment_signal'] == 1), 'composite_signal'] = 2
    df.loc[(df['roro_signal'] == -1) & (df['sentiment_signal'] == -1), 'composite_signal'] = -2

    return df


# ============================================================
# 回测
# ============================================================
def backtest_strategy(df, equity_col, bond_col, signal_col, name):
    """回测 - 按研报规范，包含滑点和手续费"""
    df = df.copy()

    # 仓位
    df['position'] = Config.EQUITY_BASE + df[signal_col] * Config.SIGNAL_ADJUST
    df['position'] = df['position'].clip(Config.MIN_POSITION, Config.MAX_POSITION)

    # 计算调仓（仓位变化）
    df['position_change'] = (df['position'].shift(1) - df['position'].shift(2)).abs()
    df['position_change'] = df['position_change'].fillna(0)

    # 收益（含滑点和手续费）
    # 滑点成本 = 调仓幅度 * 滑点率
    df['slippage_cost'] = df['position_change'] * Config.SLIPPAGE_RATE
    # 手续费 = 调仓幅度 * 手续费率
    df['commission_cost'] = df['position_change'] * Config.COMMISSION_RATE
    # 总成本
    df['total_cost'] = df['slippage_cost'] + df['commission_cost']

    # 组合收益（扣除成本）
    df['portfolio_return'] = df['position'].shift(1) * df[equity_col] + \
                            (1 - df['position'].shift(1)) * df[bond_col] - \
                            df['total_cost']
    df = df.dropna(subset=['portfolio_return'])

    # 净值
    df['nav'] = (1 + df['portfolio_return']).cumprod()
    df['benchmark_return'] = 0.5 * df[equity_col] + 0.5 * df[bond_col]
    df['benchmark_nav'] = (1 + df['benchmark_return']).cumprod()

    # 统计总成本
    total_cost = df['total_cost'].sum()
    n_trades = (df['position_change'] > 0).sum()

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
    print(f"平均权益仓位: {df['position'].mean()*100:.1f}%")
    print(f"调仓次数: {n_trades}")
    print(f"总成本: {total_cost*100:.2f}%")

    return {
        'name': name,
        'annual_return': annual_return,
        'bench_annual': bench_ann,
        'excess': annual_return - bench_ann,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'avg_position': df['position'].mean(),
        'n_trades': n_trades,
        'total_cost': total_cost
    }


# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 60)
    print("情绪驱动股债配置策略 - 最终版")
    print("=" * 60)

    # 1. 获取数据
    df = fetch_all_data()

    # 2. 计算RORO
    print("\n计算RORO...")
    df = calc_roro(df, Config.ROLLING_WINDOW)
    print(f"RORO范围: {df['roro'].min():.4f} ~ {df['roro'].max():.4f}")

    # 3. 生成信号
    print("\n生成信号...")
    df = generate_signals(df)
    print(f"RORO信号: {df['roro_signal'].value_counts().to_dict()}")
    print(f"情绪信号: {df['sentiment_signal'].value_counts().to_dict()}")
    print(f"复合信号: {df['composite_signal'].value_counts().to_dict()}")

    # 4. 月度化 - 修复：计算正确的月度收益率
    df['year_month'] = df['date'].dt.to_period('M')

    # 资产价格列
    price_cols = ['hs300', 'guozheng', 'hsi', 'sp500', 'nasdaq', 'cbond', 'agg', 'gold', 'oil']

    # 按月计算月度收益率 =月末价格/月初价格-1
    monthly_data = {}
    for col in price_cols:
        if col in df.columns and df[col].notna().sum() > 0:
            monthly_grouped = df.groupby('year_month')[col]
            first_prices = monthly_grouped.first()
            last_prices = monthly_grouped.last()
            monthly_data[col + '_return'] = (last_prices / first_prices - 1).values

    # 获取月末日期和月份
    month_info = df.groupby('year_month')['date'].last()
    monthly_data['date'] = month_info.values
    monthly_data['year_month'] = month_info.index

    # 创建月度DataFrame
    monthly = pd.DataFrame(monthly_data)

    # 权益和债券收益（多资产平均）
    equity_cols = ['hs300_return', 'guozheng_return', 'hsi_return', 'sp500_return', 'nasdaq_return']
    bond_cols = ['cbond_return', 'agg_return']
    monthly['equity_return'] = monthly[equity_cols].mean(axis=1, skipna=True)
    monthly['bond_return'] = monthly[bond_cols].mean(axis=1, skipna=True)

    # 获取信号（取每月最后一天的信号）
    signal_df = df.groupby('year_month').agg({
        'roro_signal': 'last',
        'sentiment_signal': 'last',
        'composite_signal': 'last'
    }).reset_index()
    monthly = monthly.merge(signal_df, on='year_month', how='left')
    for col in ['roro_signal', 'sentiment_signal', 'composite_signal']:
        monthly[col] = monthly[col].fillna(method='ffill').fillna(0)

    results = {}

    # 策略1: 复合信号-全球配置
    print("\n" + "="*60)
    print("策略1: 复合信号 - 全球股债配置")
    print("="*60)
    results['composite_global'] = backtest_strategy(
        monthly, 'equity_return', 'bond_return', 'composite_signal',
        '复合信号-全球配置'
    )

    # 策略2: 复合信号-沪深300+国债
    bond_col = 'bond_10y_return' if 'bond_10y_return' in monthly.columns else 'bond_return'
    print("\n" + "="*60)
    print("策略2: 复合信号 - 沪深300 + 国债")
    print("="*60)
    results['composite_hs300'] = backtest_strategy(
        monthly, 'hs300_return', bond_col, 'composite_signal',
        '复合信号-沪深300+国债'
    )

    # 策略3: 复合信号-国证A指+国债
    print("\n" + "="*60)
    print("策略3: 复合信号 - 国证A指 + 国债")
    print("="*60)
    results['composite_guozheng'] = backtest_strategy(
        monthly, 'guozheng_return', bond_col, 'composite_signal',
        '复合信号-国证A指+国债'
    )

    # 输出汇总
    print("\n" + "="*70)
    print("结果汇总 (与研报对比)")
    print("="*70)
    print(f"{'策略':<35} {'年化收益':>10} {'基准':>10} {'超额':>10} {'夏普':>8}")
    print("-"*70)

    # 研报数据
    report = {
        'composite_global': (0.114, 0.065, 0.049),
        'composite_hs300': (0.118, 0.061, 0.056),
        'composite_guozheng': (0.148, 0.077, 0.072)
    }

    for key, res in results.items():
        r_ann = res['annual_return']
        r_bench = res['bench_annual']
        r_excess = res['excess']
        r_sharpe = res['sharpe']

        rep_ann, rep_bench, rep_excess = report.get(key, (0,0,0))

        print(f"{res['name']:<35} {r_ann*100:>+8.2f}% {r_bench*100:>+8.2f}% {r_excess*100:>+8.2f}% {r_sharpe:>7.2f}")
        print(f"  研报参考:                               {rep_ann*100:>+8.2f}% {rep_bench*100:>+8.2f}% {rep_excess*100:>+8.2f}%")

    # 保存
    monthly.to_csv('strategy_final_monthly.csv', index=False, encoding='utf-8-sig')
    print("\n已保存到 strategy_final_monthly.csv")

    return results


if __name__ == "__main__":
    results = main()
