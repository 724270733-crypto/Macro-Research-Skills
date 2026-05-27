#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iFind 本地 SDK 客户端

基于 iFinDPy SDK 提供金融数据查询功能。
需要先从 https://quantapi.10jqka.com.cn 下载安装 SDK。

Usage:
    from ifind_client import IFindClient
    
    client = IFindClient()
    client.login()
    data = client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,100')
"""

import os
from typing import List, Optional, Union

import pandas as pd
from dotenv import load_dotenv


class IFindError(Exception):
    """iFind API 异常"""

    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(f'[{code}] {message}')


class IFindClient:
    """iFind 本地 SDK 客户端"""

    def __init__(self, username: str = None, password: str = None):
        """
        初始化客户端
        
        Args:
            username: iFind 账号，默认从环境变量 IFIND_USERNAME 读取
            password: iFind 密码，默认从环境变量 IFIND_PASSWORD 读取
        """
        load_dotenv()
        self.username = username or os.getenv('IFIND_USERNAME')
        self.password = password or os.getenv('IFIND_PASSWORD')
        self._logged_in = False
        self._ths = None

    def _ensure_sdk(self):
        """确保 SDK 已导入"""
        if self._ths is not None:
            return

        try:
            from iFinDPy import (
                THS_BasicData, THS_BD, THS_DataPool, THS_DateOffset,
                THS_DateSerial, THS_DP, THS_DR, THS_DS, THS_HF,
                THS_iFinDLogin, THS_iFinDLogout,
                THS_RealtimeQuotes, THS_RQ, THS_WC,
            )
            self._ths = {
                'login': THS_iFinDLogin,
                'logout': THS_iFinDLogout,
                'bd': THS_BD,
                'ds': THS_DS,
                'dr': THS_DR,
                'rq': THS_RQ,
                'hf': THS_HF,
                'wc': THS_WC,
                'date_offset': THS_DateOffset,
            }
        except ImportError as e:
            raise IFindError(
                '未安装 iFinDPy SDK，请从 https://quantapi.10jqka.com.cn 下载安装',
                -101
            ) from e

    def login(self) -> bool:
        """
        登录 iFind 服务
        
        Returns:
            登录是否成功
        """
        if self._logged_in:
            return True

        self._ensure_sdk()

        if not self.username or not self.password:
            raise IFindError('未配置用户名或密码', -100)

        result = self._ths['login'](self.username, self.password)

        if result in {0, -201}:
            self._logged_in = True
            return True
        else:
            raise IFindError(f'登录失败，错误码: {result}', result)

    def logout(self) -> bool:
        """登出 iFind 服务"""
        if not self._logged_in:
            return True

        self._ensure_sdk()
        result = self._ths['logout']()
        if result == 0:
            self._logged_in = False
        return result == 0

    def _ensure_login(self):
        """确保已登录"""
        if not self._logged_in:
            self.login()

    def get_basic_data(
        self,
        codes: Union[str, List[str]],
        indicators: str,
        params: str = '',
    ) -> pd.DataFrame:
        """
        获取基础数据
        
        Args:
            codes: 证券代码，如 '000001.SZ' 或 ['000001.SZ', '600000.SH']
            indicators: 指标代码，如 'ths_close_price_stock'
            params: 指标参数，如 '2024-01-15,100'
            
        Returns:
            数据 DataFrame
            
        Example:
            >>> client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,100')
        """
        self._ensure_login()

        if isinstance(codes, list):
            codes = ','.join(codes)

        result = self._ths['bd'](codes, indicators, params)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'获取数据失败', code)

    def get_date_serial(
        self,
        codes: Union[str, List[str]],
        indicators: str,
        params: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        获取日期序列数据
        
        Args:
            codes: 证券代码
            indicators: 指标代码
            params: 指标参数，通常为 'Fill:Blank'
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            数据 DataFrame
            
        Example:
            >>> client.get_date_serial('000001.SZ', 'ths_close_price_stock', 
            ...                        'Fill:Blank', '2024-01-01', '2024-01-15')
        """
        self._ensure_login()

        if isinstance(codes, list):
            codes = ','.join(codes)

        result = self._ths['ds'](codes, indicators, params, 'Fill:Blank', start_date, end_date)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'获取数据失败', code)

    def get_data_pool(
        self,
        pool_id: str,
        params: str,
        fields: str,
    ) -> pd.DataFrame:
        """
        获取数据池数据（板块成分等）
        
        Args:
            pool_id: 数据池 ID，如 'p03291'
            params: 查询参数，如 'date=20240115;blockname=001005261'
            fields: 返回字段，如 'p03291_f001:Y,p03291_f002:Y'
            
        Returns:
            数据 DataFrame
            
        Example:
            >>> client.get_data_pool('p03291', 
            ...     'date=20240115;blockname=001005261',
            ...     'p03291_f001:Y,p03291_f002:Y')
        """
        self._ensure_login()

        result = self._ths['dr'](pool_id, params, fields)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'获取数据失败', code)

    def get_realtime_quotes(
        self,
        codes: Union[str, List[str]],
        indicators: str = 'latest,open,high,low,preClose,volume,amount,changeRatio',
    ) -> pd.DataFrame:
        """
        获取实时行情
        
        Args:
            codes: 证券代码
            indicators: 行情指标
            
        Returns:
            实时行情 DataFrame
            
        Example:
            >>> client.get_realtime_quotes(['000001.SZ', '600000.SH'])
        """
        self._ensure_login()

        if isinstance(codes, list):
            codes = ','.join(codes)

        result = self._ths['rq'](codes, indicators)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'获取实时行情失败', code)

    def get_high_frequency(
        self,
        codes: Union[str, List[str]],
        indicators: str,
        start_time: str,
        end_time: str,
        period: str = '1min',
    ) -> pd.DataFrame:
        """
        获取高频数据（分钟级）
        
        Args:
            codes: 证券代码
            indicators: 指标代码
            start_time: 开始时间 YYYY-MM-DD HH:MM:SS
            end_time: 结束时间
            period: 周期 1min/5min/15min/30min/60min
            
        Returns:
            高频数据 DataFrame
        """
        self._ensure_login()

        if isinstance(codes, list):
            codes = ','.join(codes)

        result = self._ths['hf'](codes, indicators, '', start_time, end_time, period)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'获取高频数据失败', code)

    def wencai_query(
        self,
        query: str,
        query_type: str = 'stock',
    ) -> pd.DataFrame:
        """
        问财自然语言查询
        
        Args:
            query: 查询语句，如 '市值大于1000亿的股票'
            query_type: 查询类型 stock/fund/bond/index
            
        Returns:
            查询结果 DataFrame
            
        Example:
            >>> client.wencai_query('市盈率小于20且ROE大于15%的股票', 'stock')
            >>> client.wencai_query('今日涨停的股票', 'stock')
        """
        self._ensure_login()

        result = self._ths['wc'](query, query_type)

        if hasattr(result, 'data') and result.data is not None:
            return result.data
        else:
            code = getattr(result, 'errorcode', -1)
            raise IFindError(f'问财查询失败', code)

    def get_date_offset(
        self,
        start_date: str,
        offset: int,
        date_type: str = 'TD',
    ) -> str:
        """
        日期偏移计算
        
        Args:
            start_date: 起始日期 YYYY-MM-DD
            offset: 偏移天数（正数向后，负数向前）
            date_type: TD 交易日 / ND 自然日
            
        Returns:
            偏移后的日期
        """
        self._ensure_login()
        return self._ths['date_offset'](start_date, offset, date_type)

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()


def main():
    """示例用法"""
    print('iFind Client 示例')
    print('=' * 50)

    # 使用上下文管理器
    with IFindClient() as client:
        # 获取股票数据
        print('\n1. 获取股票收盘价:')
        data = client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,100')
        print(data)

        # 获取实时行情
        print('\n2. 获取实时行情:')
        data = client.get_realtime_quotes(['000001.SZ', '600000.SH'])
        print(data)

        # 问财查询
        print('\n3. 问财查询:')
        data = client.wencai_query('市值大于1000亿的股票', 'stock')
        print(data.head(10))


if __name__ == '__main__':
    main()
