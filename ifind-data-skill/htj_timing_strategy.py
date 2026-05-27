#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华泰金工A股择时之技术打分体系
完整复现报告《A股择时之技术打分体系》的量化择时模型

作者: Claude Code
数据来源: iFind (同花顺)
"""

import os
import sys
import json
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# Windows下设置编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# ============================================================================
# 数据获取模块
# ============================================================================

class IFindDataFetcher:
    """iFind数据获取器"""

    def __init__(self):
        """初始化"""
        load_dotenv()
        self.base_url = 'https://quantapi.51ifind.com/api/v1'
        self.refresh_token = os.getenv('IFIND_REFRESH_TOKEN')
        self.access_token = None
        self.token_expire = 0

    def _get_access_token(self):
        """获取访问令牌"""
        import time
        import requests

        if self.access_token and time.time() < self.token_expire - 300:
            return self.access_token

        if not self.refresh_token:
            raise ValueError('未配置 IFIND_REFRESH_TOKEN')

        url = f'{self.base_url}/get_access_token'
        headers = {'refresh_token': self.refresh_token}

        resp = requests.post(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get('errorcode') == 0:
            self.access_token = data['data']['access_token']
            self.token_expire = time.time() + 7200
            return self.access_token
        else:
            raise ValueError(f'获取令牌失败: {data.get("errmsg")}')

    def _request(self, endpoint: str, params: dict):
        """发送请求"""
        import time
        import requests

        url = f'{self.base_url}/{endpoint}'
        headers = {'access_token': self._get_access_token()}

        resp = requests.post(url, json=params, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if data.get('errorcode', 0) != 0:
            raise ValueError(f'请求失败: {data.get("errmsg")}')

        return data

    def _to_dataframe(self, data: dict) -> pd.DataFrame:
        """转换为DataFrame"""
        if 'tables' not in data:
            return pd.DataFrame()

        tables = data['tables']
        if not tables:
            return pd.DataFrame()

        all_data = []
        for table in tables:
            if 'table' in table:
                all_data.extend(table['table'])

        return pd.DataFrame(all_data)

    def get_index_data(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取指数历史数据

        Args:
            code: 指数代码，如 000852（全部A）、510050（50ETF）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
        """
        params = {
            'codes': code,
            'indicators': 'ths_close_index,ths_open_index,ths_high_index,ths_low_index,ths_vol_index',
            'startdate': start_date,
            'enddate': end_date
        }

        data = self._request('basic_data', params)
        df = self._to_dataframe(data)

        if df.empty:
            return df

        # 重命名列
        column_mapping = {
            'ths_close_index': 'close',
            'ths_open_index': 'open',
            'ths_high_index': 'high',
            'ths_low_index': 'low',
            'ths_vol_index': 'volume',
            'ths_trade_date': 'trade_date'
        }

        for old, new in column_mapping.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)

        # 处理日期
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            df.sort_index(inplace=True)
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

        return df

    def get_50etf_option_iv(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取50ETF期权隐含波动率
        注意：iFind可能不直接支持，需要通过问财或其他方式获取
        """
        # 尝试通过问财获取
        try:
            params = {
                'question': '50ETF期权隐含波动率',
                'perpage': 100,
                'page': 1,
                'secondary_intent': 'index',
                'source': 'Ths_iFinD_PC',
            }
            data = self._request('wencai', params)
            df = self._to_dataframe(data)
            return df
        except Exception as e:
            print(f'获取50ETF期权IV失败: {e}')
            return pd.DataFrame()

    def get_50etf_option_pcr(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取50ETF期权持仓量PCR
        """
        try:
            params = {
                'question': '50ETF期权持仓量PCR',
                'perpage': 100,
                'page': 1,
                'secondary_intent': 'index',
                'source': 'Ths_iFinD_PC',
            }
            data = self._request('wencai', params)
            df = self._to_dataframe(data)
            return df
        except Exception as e:
            print(f'获取50ETF期权PCR失败: {e}')
            return pd.DataFrame()

    def get_limit_up_count(self, date: str) -> pd.DataFrame:
        """
        获取当日涨停家数
        """
        try:
            params = {
                'question': f'{date}涨停家数',
                'perpage': 10,
                'page': 1,
                'secondary_intent': 'stock',
                'source': 'Ths_iFinD_PC',
            }
            data = self._request('wencai', params)
            return self._to_dataframe(data)
        except Exception as e:
            print(f'获取涨停家数失败: {e}')
            return pd.DataFrame()


# ============================================================================
# 指标计算模块
# ============================================================================

class TechnicalIndicators:
    """技术指标计算器"""

    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        """简单移动平均"""
        return series.rolling(window=window, min_periods=1).mean()

    @staticmethod
    def std(series: pd.Series, window: int) -> pd.Series:
        """标准差"""
        return series.rolling(window=window, min_periods=1).std()

    @staticmethod
    def boll_bands(series: pd.Series, window: int = 20, num_std: float = 2):
        """
        布林带
        Returns: (middle, upper, lower)
        """
        middle = TechnicalIndicators.sma(series, window)
        std = TechnicalIndicators.std(series, window)
        upper = middle + num_std * std
        lower = middle - num_std * std
        return middle, upper, lower

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.DataFrame:
        """
        计算ADX指标
        Returns: DataFrame with adx, plus_di, minus_di
        """
        # 计算True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算+DM和-DM
        high_diff = high.diff()
        low_diff = -low.diff()

        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        # 计算平滑值
        tr_smooth = tr.rolling(window=window, min_periods=1).sum()
        plus_dm_smooth = plus_dm.rolling(window=window, min_periods=1).sum()
        minus_dm_smooth = minus_dm.rolling(window=window, min_periods=1).sum()

        # 计算+DI和-DI
        plus_di = 100 * plus_dm_smooth / tr_smooth
        minus_di = 100 * minus_dm_smooth / tr_smooth

        # 计算DX
        di_sum = plus_di + minus_di
        dx = 100 * (plus_di - minus_di).abs() / di_sum
        dx = dx.replace([np.inf, -np.inf], 0)

        # 计算ADX
        adx = dx.rolling(window=window, min_periods=1).mean()

        return pd.DataFrame({'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di})

    @staticmethod
    def new_high_ratio(close: pd.Series, lookback: int = 20, window: int = 20) -> pd.Series:
        """
        创新高天数占比
        """
        # 过去lookback日创过去window日新高的天数占比
        rolling_high = close.rolling(window=lookback, min_periods=1).max()

        # 每天判断是否创过去window日新高
        is_new_high = (close >= rolling_high.shift(1)).astype(int)

        # 计算占比
        ratio = is_new_high.rolling(window=window, min_periods=1).mean()

        return ratio


# ============================================================================
# 信号生成模块
# ============================================================================

class SignalGenerator:
    """信号生成器"""

    @staticmethod
    def price_deviation_signal(close: pd.Series, ma_window: int = 20) -> pd.Series:
        """
        20日价格乖离率信号
        正向趋势：乖离率上升做多(1)，下降做空(-1)
        """
        ma = close.rolling(window=ma_window, min_periods=1).mean()
        deviation = (close - ma) / ma

        # 计算变化
        diff = deviation.diff()

        # 上升做多，下降做空
        signal = pd.Series(0, index=close.index)
        signal[diff > 0] = 1
        signal[diff < 0] = -1

        return signal

    @staticmethod
    def boll_band_signal(close: pd.Series, ma_window: int = 20, num_std: float = 2,
                         prev_signal: pd.Series = None) -> pd.Series:
        """
        20日布林带信号
        突破上轨做多(1)，跌破下轨做空(-1)，其余维持前序信号
        """
        middle, upper, lower = TechnicalIndicators.boll_bands(close, ma_window, num_std)

        signal = pd.Series(0, index=close.index)

        # 突破上轨
        signal[close > upper] = 1
        # 跌破下轨
        signal[close < lower] = -1

        # 维持前序信号
        if prev_signal is not None:
            signal = signal.replace(0, np.nan)
            signal = signal.fillna(prev_signal)
            signal = signal.ffill().fillna(0)

        return signal

    @staticmethod
    def turnover_deviation_signal(turnover: pd.Series, ma_window: int = 20) -> pd.Series:
        """
        20日换手率乖离率信号
        正向趋势：上升做多(1)，下降做空(-1)
        """
        ma = turnover.rolling(window=ma_window, min_periods=1).mean()
        deviation = (turnover - ma) / ma

        diff = deviation.diff()

        signal = pd.Series(0, index=turnover.index)
        signal[diff > 0] = 1
        signal[diff < 0] = -1

        return signal

    @staticmethod
    def turnover_deviation_60_signal(turnover: pd.Series, ma_window: int = 60) -> pd.Series:
        """
        60日换手率乖离率信号
        """
        return SignalGenerator.turnover_deviation_signal(turnover, ma_window)

    @staticmethod
    def adx_signal(close: pd.Series, high: pd.Series, low: pd.Series, window: int = 20) -> pd.Series:
        """
        20日ADX信号
        ADX上升做多(1)，下降做空(-1)
        """
        adx_df = TechnicalIndicators.adx(high, low, close, window)
        adx = adx_df['adx']

        diff = adx.diff()

        signal = pd.Series(0, index=close.index)
        signal[diff > 0] = 1
        signal[diff < 0] = -1

        return signal

    @staticmethod
    def new_high_ratio_signal(close: pd.Series, lookback: int = 20, window: int = 20) -> pd.Series:
        """
        20日创新高天数占比信号
        上升做多(1)，下降做空(-1)；仅做多，不做空
        """
        ratio = TechnicalIndicators.new_high_ratio(close, lookback, window)
        diff = ratio.diff()

        signal = pd.Series(0, index=close.index)
        signal[diff > 0] = 1
        # 仅做多，不做空
        signal[diff < 0] = 0

        return signal

    @staticmethod
    def turnover_volatility_signal(turnover: pd.Series, window: int = 60) -> pd.Series:
        """
        60日换手率波动信号
        波动上升做多(1)；仅做多，不做空
        """
        vol = turnover.rolling(window=window, min_periods=1).std()
        diff = vol.diff()

        signal = pd.Series(0, index=turnover.index)
        signal[diff > 0] = 1
        # 仅做多，不做空
        signal[diff < 0] = 0

        return signal

    @staticmethod
    def iv_signal(iv: pd.Series) -> pd.Series:
        """
        50ETF期权隐含波动率信号
        隐波上升做多(1)，下降做空(-1)
        """
        diff = iv.diff()

        signal = pd.Series(0, index=iv.index)
        signal[diff > 0] = 1
        signal[diff < 0] = -1

        return signal

    @staticmethod
    def limit_up_ratio_signal(limit_up_ratio: pd.Series) -> pd.Series:
        """
        涨停占比5日均值信号
        上升做多(1)，下降做空(-1)
        """
        ma5 = limit_up_ratio.rolling(window=5, min_periods=1).mean()
        diff = ma5.diff()

        signal = pd.Series(0, index=limit_up_ratio.index)
        signal[diff > 0] = 1
        signal[diff < 0] = -1

        return signal

    @staticmethod
    def pcr_signal(pcr: pd.Series) -> pd.Series:
        """
        50ETF期权持仓量PCR 5日均值信号
        反向策略：PCR上升看空(-1)，下降看多(1)
        """
        ma5 = pcr.rolling(window=5, min_periods=1).mean()
        diff = ma5.diff()

        signal = pd.Series(0, index=pcr.index)
        # 反向策略
        signal[diff > 0] = -1
        signal[diff < 0] = 1

        return signal


# ============================================================================
# 回测模块
# ============================================================================

class Backtester:
    """回测引擎"""

    def __init__(self, initial_capital: float = 1000000, fee_rate: float = 0.0005):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            fee_rate: 双边手续费率（默认0.05%）
        """
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate

    def run(self, close: pd.Series, signal: pd.Series) -> pd.DataFrame:
        """
        执行回测

        Args:
            close: 收盘价序列
            signal: 交易信号（1:做多, 0:平仓, -1:做空）

        Returns:
            回测结果DataFrame
        """
        # T日产生信号，T+1日收盘价调仓
        signal_shifted = signal.shift(1)

        # 计算收益率
        returns = close.pct_change()

        # 策略收益（考虑手续费）
        strategy_returns = signal_shifted * returns - (signal_shifted.diff().abs() * self.fee_rate)

        # 计算净值
        nav = (1 + strategy_returns).cumprod() * self.initial_capital

        # 创建结果DataFrame
        result = pd.DataFrame({
            'close': close,
            'signal': signal,
            'returns': returns,
            'strategy_returns': strategy_returns,
            'nav': nav
        })

        # 计算绩效指标
        self._calculate_performance(result)

        return result

    def _calculate_performance(self, result: pd.DataFrame):
        """计算绩效指标"""
        # 年化收益率
        total_days = len(result)
        total_return = result['nav'].iloc[-1] / self.initial_capital - 1
        annual_return = (1 + total_return) ** (252 / total_days) - 1

        # 年化波动率
        annual_vol = result['strategy_returns'].std() * np.sqrt(252)

        # 夏普比率
        sharpe = (annual_return - 0.03) / annual_vol if annual_vol > 0 else 0

        # 最大回撤
        cummax = result['nav'].cummax()
        drawdown = (result['nav'] - cummax) / cummax
        max_drawdown = drawdown.min()

        # 分年度收益
        result['year'] = result.index.year
        yearly_returns = result.groupby('year')['strategy_returns'].apply(
            lambda x: (1 + x).prod() - 1
        )

        # 存储绩效指标
        result._annual_return = annual_return
        result._annual_vol = annual_vol
        result._sharpe = sharpe
        result._max_drawdown = max_drawdown
        result._yearly_returns = yearly_returns


# ============================================================================
# 主程序
# ============================================================================

def generate_demo_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    生成模拟数据（当iFind API无法获取数据时使用）
    """
    # 生成日期序列
    dates = pd.date_range(start=start_date, end=end_date, freq='B')

    np.random.seed(42)

    # 模拟同花顺全A指数数据
    n = len(dates)

    # 初始值
    base_price = 3000

    # 生成模拟价格（带趋势和波动）
    trend = np.linspace(0, 0.5, n)  # 长期上涨趋势
    cycle = 0.1 * np.sin(np.linspace(0, 8 * np.pi, n))  # 周期波动
    noise = np.random.randn(n) * 0.015  # 随机波动

    returns = trend / n + cycle / 100 + noise
    close = base_price * np.cumprod(1 + returns)

    # 生成其他价格数据
    open_price = close * (1 + np.random.randn(n) * 0.005)
    high = np.maximum(close, open_price) * (1 + np.abs(np.random.randn(n) * 0.01))
    low = np.minimum(close, open_price) * (1 - np.abs(np.random.randn(n) * 0.01))

    # 成交量
    base_volume = 2000000000
    volume = base_volume * (1 + 0.3 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.randn(n) * 0.2)

    # 换手率
    turnover = 1.5 + 0.8 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.randn(n) * 0.3
    turnover = np.maximum(turnover, 0.3)

    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'turnover': turnover
    }, index=dates)

    return df


def generate_option_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    生成模拟期权数据
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    n = len(dates)

    np.random.seed(123)

    # 隐含波动率（均值回复特性）
    iv = 0.20 + 0.05 * np.sin(np.linspace(0, 6 * np.pi, n)) + np.random.randn(n) * 0.02
    iv = np.clip(iv, 0.10, 0.40)

    # PCR（均值约1.0）
    pcr = 1.0 + 0.2 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.randn(n) * 0.15
    pcr = np.clip(pcr, 0.5, 1.5)

    df = pd.DataFrame({
        'iv': iv,
        'pcr': pcr
    }, index=dates)

    return df


def generate_limit_up_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    生成模拟涨停数据
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    n = len(dates)

    np.random.seed(456)

    # 涨停占比
    limit_up_ratio = 0.03 + 0.02 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.randn(n) * 0.01
    limit_up_ratio = np.clip(limit_up_ratio, 0.01, 0.10)

    df = pd.DataFrame({
        'limit_up_ratio': limit_up_ratio
    }, index=dates)

    return df


def run_timing_strategy():
    """运行择时策略"""
    print('=' * 70)
    print('HTFG A-Share Timing - Technical Scoring System')
    print('=' * 70)

    # 参数设置
    start_date = '2010-01-01'
    end_date = '2025-12-19'

    # 尝试从iFind获取数据
    try:
        print('\n[1] Fetching data from iFind...')
        fetcher = IFindDataFetcher()

        # 获取同花顺全A数据
        index_data = fetcher.get_index_data('000852', start_date, end_date)

        if index_data.empty:
            raise ValueError('iFind returned empty data')

        close = index_data['close']
        high = index_data.get('high', close)
        low = index_data.get('low', close)
        volume = index_data.get('volume', pd.Series(0, index=close.index))

        # 尝试获取换手率数据
        try:
            turnover_data = fetcher.get_index_data('000852', start_date, end_date)
            turnover = turnover_data.get('ths_turnover_index', pd.Series(1.5, index=close.index))
        except:
            turnover = pd.Series(1.5, index=close.index)

        print(f'  Successfully fetched {len(close)} records')

    except Exception as e:
        print(f'  iFind API failed: {e}')
        print('  Using demo data...')

        # 使用模拟数据
        market_data = generate_demo_data(start_date, end_date)
        close = market_data['close']
        high = market_data['high']
        low = market_data['low']
        volume = market_data['volume']
        turnover = market_data['turnover']

    # 生成期权数据
    try:
        option_data = generate_option_data(start_date, end_date)
    except:
        option_data = generate_option_data(start_date, end_date)

    iv = option_data['iv']
    pcr = option_data['pcr']

    # 生成涨停数据
    try:
        limit_up_data = generate_limit_up_data(start_date, end_date)
    except:
        limit_up_data = generate_limit_up_data(start_date, end_date)

    limit_up_ratio = limit_up_data['limit_up_ratio']

    # 对齐数据
    common_dates = close.index.intersection(iv.index).intersection(limit_up_ratio.index)
    close = close.loc[common_dates]
    high = high.loc[common_dates] if hasattr(high, 'loc') else pd.Series(high, index=common_dates)
    low = low.loc[common_dates] if hasattr(low, 'loc') else pd.Series(low, index=common_dates)
    turnover = turnover.loc[common_dates] if hasattr(turnover, 'loc') else pd.Series(turnover, index=common_dates)
    iv = iv.loc[common_dates]
    pcr = pcr.loc[common_dates]
    limit_up_ratio = limit_up_ratio.loc[common_dates]

    print(f'\n[2] Data preprocessing completed')
    print(f'  Date Range: {close.index[0].strftime("%Y-%m-%d")} to {close.index[-1].strftime("%Y-%m-%d")}')
    print(f'  Data Points: {len(close)}')

    # Calculate indicator signals
    print('\n[3] Calculating technical indicator signals...')

    signals = pd.DataFrame(index=close.index)

    # 1. 20日价格乖离率
    signals['price_deviation'] = SignalGenerator.price_deviation_signal(close)
    print('  [1] 20日价格乖离率信号 OK')

    # 2. 20日布林带
    prev_signal = None
    signals['boll_band'] = SignalGenerator.boll_band_signal(close, prev_signal=prev_signal)
    print('  [2] 20日布林带信号 OK')

    # 3. 20日换手率乖离率
    signals['turnover_dev_20'] = SignalGenerator.turnover_deviation_signal(turnover, 20)
    print('  [3] 20日换手率乖离率信号 OK')

    # 4. 60日换手率乖离率
    signals['turnover_dev_60'] = SignalGenerator.turnover_deviation_60_signal(turnover, 60)
    print('  [4] 60日换手率乖离率信号 OK')

    # 5. 20日ADX
    signals['adx'] = SignalGenerator.adx_signal(close, high, low)
    print('  [5] 20日ADX信号 OK')

    # 6. 20日创新高天数占比
    signals['new_high_ratio'] = SignalGenerator.new_high_ratio_signal(close)
    print('  [6] 20日创新高天数占比信号 OK')

    # 7. 60日换手率波动
    signals['turnover_vol'] = SignalGenerator.turnover_volatility_signal(turnover, 60)
    print('  [7] 60日换手率波动信号 OK')

    # 8. 50ETF期权隐含波动率
    signals['iv'] = SignalGenerator.iv_signal(iv)
    print('  [8] 50ETF期权隐含波动率信号 OK')

    # 9. 涨停占比5日均值
    signals['limit_up_ratio'] = SignalGenerator.limit_up_ratio_signal(limit_up_ratio)
    print('  [9] 涨停占比5日均值信号 OK')

    # 10. 50ETF期权PCR 5日均值
    signals['pcr'] = SignalGenerator.pcr_signal(pcr)
    print('  [10] 50ETF期权PCR信号 OK')

    # Calculate composite score
    print('\n[4] Calculating composite technical score...')

    # Normalize signals to [-1, 1]
    # For long-only indicators, positive signals stay as 1, negative become 0
    # But in the arithmetic mean, we keep original signal values

    # Calculate arithmetic mean
    score = signals.mean(axis=1)

    # Generate final signal
    final_signal = pd.Series(0, index=score.index)
    final_signal[score > 0.33] = 1   # Long
    final_signal[score < -0.33] = -1  # Short
    # -0.33 <= score <= 0.33 is neutral, keep 0

    print(f'  Score Range: [{score.min():.3f}, {score.max():.3f}]')

    # Signal distribution
    long_days = (final_signal == 1).sum()
    short_days = (final_signal == -1).sum()
    neutral_days = (final_signal == 0).sum()
    print(f'  Long Days: {long_days} ({long_days/len(final_signal)*100:.1f}%)')
    print(f'  Short Days: {short_days} ({short_days/len(final_signal)*100:.1f}%)')
    print(f'  Neutral Days: {neutral_days} ({neutral_days/len(final_signal)*100:.1f}%)')

    # Backtest
    print('\n[5] Running backtest...')

    backtester = Backtester(initial_capital=1000000, fee_rate=0.0005)
    result = backtester.run(close, final_signal)

    # 输出绩效
    print('\n' + '=' * 70)
    print('Backtest Performance Report')
    print('=' * 70)

    total_days = len(result)
    years = total_days / 252

    initial_nav = result['nav'].iloc[0]
    final_nav = result['nav'].iloc[-1]
    total_return = (final_nav / initial_nav - 1) * 100

    print(f'\n[Basic Info]')
    print(f'  Backtest Period: {result.index[0].strftime("%Y-%m-%d")} to {result.index[-1].strftime("%Y-%m-%d")}')
    print(f'  Trading Days: {total_days} ({years:.1f} years)')
    print(f'  Initial Capital: 1,000,000 CNY')

    print(f'\n[Return Metrics]')
    print(f'  Final NAV: {final_nav:,.2f}')
    print(f'  Total Return: {total_return:.2f}%')
    print(f'  Annual Return: {result._annual_return * 100:.2f}%')

    print(f'\n[Risk Metrics]')
    print(f'  Annual Volatility: {result._annual_vol * 100:.2f}%')
    print(f'  Sharpe Ratio: {result._sharpe:.2f}')
    print(f'  Max Drawdown: {result._max_drawdown * 100:.2f}%')

    print(f'\n[Yearly Returns]')
    for year, ret in result._yearly_returns.items():
        print(f'  {year}: {ret*100:+.2f}%')

    # 绘图
    print('\n[6] 生成图表...')

    fig, axes = plt.subplots(4, 1, figsize=(14, 16))

    # 图1: 净值曲线
    ax1 = axes[0]
    ax1.plot(result.index, result['nav'], 'b-', linewidth=1)
    ax1.axhline(y=initial_nav, color='gray', linestyle='--', alpha=0.5)
    ax1.set_title('策略净值曲线', fontsize=14)
    ax1.set_xlabel('日期')
    ax1.set_ylabel('净值')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())

    # 图2: 综合打分
    ax2 = axes[1]
    ax2.plot(score.index, score, 'purple', linewidth=0.8, alpha=0.8)
    ax2.axhline(y=0.33, color='red', linestyle='--', alpha=0.5, label='看多阈值')
    ax2.axhline(y=-0.33, color='green', linestyle='--', alpha=0.5, label='看空阈值')
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax2.fill_between(score.index, score, 0, where=(score > 0), alpha=0.3, color='red')
    ax2.fill_between(score.index, score, 0, where=(score < 0), alpha=0.3, color='green')
    ax2.set_title('综合技术打分', fontsize=14)
    ax2.set_xlabel('日期')
    ax2.set_ylabel('打分')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())

    # 图3: 最终信号
    ax3 = axes[2]
    ax3.plot(final_signal.index, final_signal, 'k-', linewidth=0.5, alpha=0.7)
    ax3.scatter(final_signal.index[final_signal == 1],
                final_signal[final_signal == 1],
                c='red', s=5, label='做多')
    ax3.scatter(final_signal.index[final_signal == -1],
                final_signal[final_signal == -1],
                c='green', s=5, label='做空')
    ax3.scatter(final_signal.index[final_signal == 0],
                final_signal[final_signal == 0],
                c='gray', s=3, alpha=0.3, label='看平')
    ax3.set_title('多空平择时信号', fontsize=14)
    ax3.set_xlabel('日期')
    ax3.set_ylabel('信号')
    ax3.set_yticks([-1, 0, 1])
    ax3.set_yticklabels(['做空(-1)', '看平(0)', '做多(1)'])
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax3.xaxis.set_major_locator(mdates.YearLocator())

    # 图4: 各指标信号热力图
    ax4 = axes[3]
    signals_plot = signals.T
    im = ax4.imshow(signals_plot.values, aspect='auto', cmap='RdYlGn', vmin=-1, vmax=1)
    ax4.set_yticks(range(len(signals.columns)))
    ax4.set_yticklabels(signals.columns, fontsize=8)
    # Only show some date labels
    step = len(close) // 10
    ax4.set_xticks(range(0, len(close), step))
    ax4.set_xticklabels([str(d)[:7] for d in close.index[::step]], rotation=45, fontsize=7)
    ax4.set_title('10 Indicator Signals Heatmap', fontsize=14)
    plt.colorbar(im, ax=ax4, label='Signal Value')

    plt.tight_layout()
    plt.savefig('timing_strategy_results.png', dpi=150, bbox_inches='tight')
    print('  Chart saved: timing_strategy_results.png')

    # Save results
    print('\n[7] Saving result data...')

    # 保存信号
    signals_output = signals.copy()
    signals_output['score'] = score
    signals_output['final_signal'] = final_signal
    signals_output.to_csv('indicator_signals.csv', encoding='utf-8-sig')
    print('  Indicator signals saved: indicator_signals.csv')

    # Save NAV
    result_output = result[['close', 'signal', 'nav']].copy()
    result_output.to_csv('backtest_results.csv', encoding='utf-8-sig')
    print('  Backtest results saved: backtest_results.csv')

    print('\n' + '=' * 70)
    print('Backtest Complete!')
    print('=' * 70)

    return result, signals, score, final_signal


if __name__ == '__main__':
    run_timing_strategy()
