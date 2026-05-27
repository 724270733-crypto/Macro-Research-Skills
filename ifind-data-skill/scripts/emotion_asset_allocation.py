"""
情绪驱动下的股债配置策略
基于中泰金工研报复现

参考来源: 中泰证券 - 情绪驱动下的股债配置策略——中泰时钟多资产联动维度之一
数据来源: Tushare
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置参数
# ============================================================

class Config:
    """策略配置参数"""
    # 数据参数
    START_DATE = "2014-01-01"
    END_DATE = "2025-12-31"
    ROLLING_WINDOW = 20  # 计算RORO的滚动窗口

    # 仓位参数
    EQUITY_WEIGHT_BASE = 0.50  # 基准权益仓位
    SIGNAL_ADJUST = 0.30        # 每个信号调整幅度
    WEIGHT_MAX = 1.00           # 最大权益仓位
    WEIGHT_MIN = 0.30           # 最小权益仓位

    # Tushare Token
    TUSHARE_TOKEN = "4eecb207f9b1151ea8aaa0a976023145380216147b446f37544c7863"


# ============================================================
# 第一部分：数据获取
# ============================================================

def set_tushare_token(token: str):
    """设置Tushare Token"""
    import tushare as ts
    ts.set_token(token)
    return ts.pro_api()


def fetch_equity_data(pro, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取权益类资产数据

    资产:
    - 沪深300 (000300.SH)
    - 万得全A (用中证全指000852.SH代替)
    - 恒生指数 (HSI.HK - 港股)
    - 标普500 (SPX - 美股)
    - 纳斯达克100 (NDX - 美股)

    Returns:
        DataFrame: 日期 + 各资产收益率
    """
    equity_data = {}

    # 1. 沪深300
    print("获取沪深300数据...")
    df_hs300 = pro.index_daily(ts_code='000300.SH', start_date=start_date, end_date=end_date)
    df_hs300 = df_hs300.sort_values('trade_date')
    df_hs300['return'] = df_hs300['close'].pct_change()
    equity_data['沪深300'] = df_hs300[['trade_date', 'return']].rename(columns={'return': 'hs300'})

    # 2. 万得全A (用中证全指000852代替)
    print("获取中证全指数据...")
    try:
        df_winda = pro.index_daily(ts_code='000852.SH', start_date=start_date, end_date=end_date)
        df_winda = df_winda.sort_values('trade_date')
        df_winda['return'] = df_winda['close'].pct_change()
        equity_data['万得全A'] = df_winda[['trade_date', 'return']].rename(columns={'return': 'winda'})
    except Exception as e:
        print(f"万得全A获取失败: {e}")

    # 3. 港股恒生指数 - 需要港股权限，这里用沪深300代替
    print("注意: 港股和美股数据需要额外权限，使用沪深300代替")

    # 合并权益数据
    if '沪深300' in equity_data:
        result = equity_data['沪深300']
        if '万得全A' in equity_data:
            result = result.merge(equity_data['万得全A'], on='trade_date', how='outer')

        # 计算等权平均收益率
        return_cols = [c for c in result.columns if c != 'trade_date']
        result['equity_return'] = result[return_cols].mean(axis=1)

    return result


def fetch_bond_data(pro, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取债券类资产数据

    资产:
    - 中债新综合财富指数
    - 美国国债ETF (需要美股权限)

    Returns:
        DataFrame: 日期 + 债券收益率
    """
    print("获取中债综合财富指数...")

    # 尝试获取中债指数
    # 中债新综合财富指数代码: CBA001/CBA003等
    try:
        # 使用国债指数代替
        df_bond = pro.index_daily(ts_code='000932.SH', start_date=start_date, end_date=end_date)
        df_bond = df_bond.sort_values('trade_date')
        df_bond['return'] = df_bond['close'].pct_change()
        return df_bond[['trade_date', 'return']].rename(columns={'return': 'bond_return'})
    except Exception as e:
        print(f"债券数据获取失败: {e}")
        # 如果获取失败，生成模拟数据
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        df = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'bond_return': np.random.normal(0.0002, 0.001, len(dates))
        })
        return df


def fetch_gold_data(pro, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取黄金数据
    """
    print("获取黄金数据...")
    # Tushare没有黄金期货历史数据接口
    # 需要使用其他数据源或模拟
    print("注意: 黄金数据需要额外数据源")
    return None


# ============================================================
# 第二部分：RORO指数计算
# ============================================================

def calculate_roro(returns_df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    计算RORO指数 (Risk-On Risk-Off Index)

    公式: RORO = E1 / ΣEi
    其中E1是第一主成分的特征值，Ei是所有主成分的特征值

    Args:
        returns_df: 收益率DataFrame，列为各资产收益率
        window: 滚动窗口大小

    Returns:
        DataFrame: trade_date, roro
    """
    from sklearn.decomposition import PCA

    # 填充缺失值
    returns_matrix = returns_df.fillna(0)

    roro_values = []
    dates = []

    for i in range(window, len(returns_matrix)):
        window_data = returns_matrix.iloc[i-window:i].values

        # 标准化
        window_data = (window_data - window_data.mean(axis=0)) / (window_data.std(axis=0) + 1e-8)

        # PCA
        pca = PCA()
        pca.fit(window_data)

        # 计算RORO
        eigenvalues = pca.explained_variance_
        roro = eigenvalues[0] / eigenvalues.sum()
        roro_values.append(roro)
        dates.append(returns_matrix.index[i])

    result = pd.DataFrame({
        'trade_date': returns_matrix.index[window:],
        'roro': roro_values
    })

    return result


def calculate_sentiment_return(roro: pd.Series, equity_return: pd.Series) -> pd.Series:
    """
    计算情绪可解释收益率

    公式: 情绪可解释收益率 = RORO * 权益资产收益率

    Args:
        roro: RORO指数序列
        equity_return: 权益资产收益率序列

    Returns:
        Series: 情绪可解释收益率
    """
    return roro * equity_return


# ============================================================
# 第三部分：信号生成
# ============================================================

def generate_signals(df: pd.DataFrame, roro_col: 'roro', sentiment_col: 'sentiment_return') -> pd.DataFrame:
    """
    生成交易信号

    规则:
    1. 情绪驱动力信号: RORO上穿均值 → +1, 下穿均值 → -1
    2. 情绪可解释收益率信号: 上升 → +1, 下降 → -1

    Args:
        df: 包含roro和sentiment_return的DataFrame
        roro_col: RORO列名
        sentiment_col: 情绪可解释收益率列名

    Returns:
        DataFrame: 添加信号列
    """
    df = df.copy()

    # 计算RORO均值
    df['roro_ma'] = df[roro_col].rolling(window=20).mean()

    # RORO信号
    df['roro_signal'] = 0
    df.loc[df[roro_col] > df['roro_ma'], 'roro_signal'] = 1
    df.loc[df[roro_col] < df['roro_ma'], 'roro_signal'] = -1

    # RORO变化信号
    df['roro_change'] = df[roro_col].diff()
    df['roro_signal'] = 0
    df.loc[df['roro_change'] > 0, 'roro_signal'] = 1   # RORO上升 → 情绪驱动增强
    df.loc[df['roro_change'] < 0, 'roro_signal'] = -1  # RORO下降 → 情绪驱动减弱

    # 情绪可解释收益率信号
    df['sentiment_change'] = df[sentiment_col].diff()
    df['sentiment_signal'] = 0
    df.loc[df['sentiment_change'] > 0, 'sentiment_signal'] = 1   # 情绪收益上升 → 增持
    df.loc[df['sentiment_change'] < 0, 'sentiment_signal'] = -1  # 情绪收益下降 → 减持

    # 复合信号
    df['composite_signal'] = df['roro_signal'] + df['sentiment_signal']

    return df


# ============================================================
# 第四部分：仓位计算
# ============================================================

def calculate_position(signals: pd.DataFrame, signal_col: str = 'composite_signal') -> pd.DataFrame:
    """
    根据信号计算权益仓位

    规则:
    - 基准仓位: 50%
    - 每个信号: ±30%
    - 范围: 30% - 100%

    Args:
        signals: 信号DataFrame
        signal_col: 信号列名

    Returns:
        DataFrame: 添加position列
    """
    df = signals.copy()

    # 计算仓位
    df['equity_position'] = Config.EQUITY_WEIGHT_BASE + df[signal_col] * Config.SIGNAL_ADJUST

    # 限制范围
    df['equity_position'] = df['equity_position'].clip(Config.WEIGHT_MIN, Config.WEIGHT_MAX)

    # 债券仓位
    df['bond_position'] = 1 - df['equity_position']

    return df


# ============================================================
# 第五部分：回测
# ============================================================

def backtest(positions: pd.DataFrame,
             equity_return_col: str = 'equity_return',
             bond_return_col: str = 'bond_return',
             position_col: str = 'equity_position') -> dict:
    """
    回测函数

    Args:
        positions: 仓位DataFrame
        equity_return_col: 权益收益率列名
        bond_return_col: 债券收益率列名
        position_col: 权益仓位列名

    Returns:
        dict: 回测结果
    """
    df = positions.copy()

    # 计算组合收益
    df['portfolio_return'] = df[position_col] * df[equity_return_col] + \
                            (1 - df[position_col]) * df[bond_return_col]

    # 计算净值
    df['nav'] = (1 + df['portfolio_return']).cumprod()
    df['benchmark_nav'] = (1 - df[position_col].iloc[0]) * (1 + df[equity_return_col]).cumprod() + \
                          df[position_col].iloc[0] * (1 + df[bond_return_col]).cumprod()

    # 计算指标
    total_return = df['nav'].iloc[-1] - 1
    n_years = len(df) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    annual_volatility = df['portfolio_return'].std() * np.sqrt(252)
    sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0

    # 最大回撤
    df['cummax'] = df['nav'].cummax()
    df['drawdown'] = (df['nav'] - df['cummax']) / df['cummax']
    max_drawdown = df['drawdown'].min()

    # 卡玛比率
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # 平均仓位
    avg_equity_position = df[position_col].mean()

    results = {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar_ratio,
        'avg_equity_position': avg_equity_position,
        'nav_series': df['nav'],
        'position_series': df[position_col]
    }

    return results


def calculate_metrics(returns: pd.Series) -> dict:
    """
    计算回测指标

    Args:
        returns: 收益率序列

    Returns:
        dict: 指标字典
    """
    total_return = (1 + returns).prod() - 1
    n_years = len(returns) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    annual_volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0

    cumret = (1 + returns).cumprod()
    cummax = cumret.cummax()
    drawdown = (cumret - cummax) / cummax
    max_dd = drawdown.min()

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': annual_volatility,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'calmar': annual_return / abs(max_dd) if max_dd != 0 else 0
    }


# ============================================================
# 第六部分：主程序
# ============================================================

def main():
    """主函数"""
    print("=" * 60)
    print("情绪驱动下的股债配置策略")
    print("=" * 60)

    # 1. 初始化Tushare
    print("\n[1] 初始化Tushare...")
    pro = set_tushare_token(Config.TUSHARE_TOKEN)

    # 2. 获取数据
    print("\n[2] 获取数据...")
    start = Config.START_DATE.replace('-', '')
    end = Config.END_DATE.replace('-', '')

    # 获取权益数据
    equity_df = fetch_equity_data(pro, start, end)

    # 获取债券数据
    bond_df = fetch_bond_data(pro, start, end)

    # 合并数据
    print("\n[3] 合并数据...")
    df = equity_df.merge(bond_df, on='trade_date', how='inner')
    df = df.sort_values('trade_date').reset_index(drop=True)
    df.set_index('trade_date', inplace=True)

    # 填充缺失值
    df = df.fillna(0)

    print(f"数据范围: {df.index[0]} 至 {df.index[-1]}")
    print(f"数据天数: {len(df)}")

    # 3. 计算RORO
    print("\n[4] 计算RORO指数...")
    # 使用多资产数据（如果有）
    return_cols = [c for c in df.columns if 'return' in c]
    returns_for_pca = df[return_cols].fillna(0)

    # 简化的RORO计算：使用权益和债券收益率的相关系数
    # 实际研报使用PCA，这里用相关性简化
    df['correlation'] = df['equity_return'].rolling(20).corr(df['bond_return'])
    df['roro'] = df['correlation'].abs()  # RORO = 相关性的绝对值

    # 4. 计算情绪可解释收益率
    print("\n[5] 计算情绪可解释收益率...")
    df['sentiment_return'] = df['roro'].shift(1) * df['equity_return']

    # 5. 生成信号
    print("\n[6] 生成信号...")
    df = generate_signals(df, 'roro', 'sentiment_return')

    # 6. 计算仓位
    print("\n[7] 计算仓位...")
    df = calculate_position(df, 'composite_signal')

    # 7. 回测
    print("\n[8] 回测...")
    results = backtest(df)

    # 8. 输出结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"年化收益率: {results['annual_return']:.2%}")
    print(f"年化波动率: {results['annual_volatility']:.2%}")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2%}")
    print(f"卡玛比率: {results['calmar_ratio']:.2f}")
    print(f"平均权益仓位: {results['avg_equity_position']:.2%}")

    print("\n[9] 保存数据...")
    # 保存结果
    output_df = df[['equity_return', 'bond_return', 'roro', 'sentiment_return',
                    'composite_signal', 'equity_position']].copy()
    output_df.to_csv('strategy_results.csv', encoding='utf-8-sig')
    print("结果已保存到 strategy_results.csv")

    return df, results


if __name__ == "__main__":
    df, results = main()
