#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iFind HTTP API 客户端

通过 HTTP API 进行数据查询，无需安装本地 SDK。

Usage:
    from http_client import IFindHTTPClient
    
    client = IFindHTTPClient()
    data = client.get_realtime_quotes('000001.SZ')
"""

import os
import time
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from dotenv import load_dotenv


class IFindHTTPError(Exception):
    """HTTP API 异常"""

    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(f'[{code}] {message}')


class IFindHTTPClient:
    """iFind HTTP API 客户端"""

    BASE_URL = 'https://quantapi.51ifind.com/api/v1'

    def __init__(self, refresh_token: str = None, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            refresh_token: 刷新令牌，默认从环境变量 IFIND_REFRESH_TOKEN 读取
            timeout: 请求超时时间（秒）
        """
        load_dotenv()
        self.refresh_token = refresh_token or os.getenv('IFIND_REFRESH_TOKEN')
        self.timeout = timeout
        self._access_token = None
        self._token_expire = 0

    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self._access_token and time.time() < self._token_expire - 300:
            return self._access_token

        if not self.refresh_token:
            raise IFindHTTPError('未配置 refresh_token', -100)

        url = f'{self.BASE_URL}/get_access_token'
        headers = {'refresh_token': self.refresh_token}

        try:
            resp = requests.post(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if data.get('errorcode') == 0:
                self._access_token = data['data']['access_token']
                self._token_expire = time.time() + 7200
                return self._access_token
            else:
                raise IFindHTTPError(data.get('errmsg', '获取令牌失败'), -100)

        except requests.exceptions.RequestException as e:
            raise IFindHTTPError(f'网络请求失败: {e}', -101)

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """发送请求"""
        url = f'{self.BASE_URL}/{endpoint}'
        headers = {'access_token': self._get_access_token()}

        try:
            resp = requests.post(url, json=params, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if data.get('errorcode', 0) != 0:
                raise IFindHTTPError(data.get('errmsg', '请求失败'), data.get('errorcode', -1))

            return data

        except requests.exceptions.RequestException as e:
            raise IFindHTTPError(f'网络请求失败: {e}', -101)

    def _to_dataframe(self, data: Dict, tables_key: str = 'tables') -> pd.DataFrame:
        """转换为 DataFrame"""
        if tables_key not in data:
            return pd.DataFrame()

        tables = data[tables_key]
        if not tables:
            return pd.DataFrame()

        all_data = []
        for table in tables:
            if 'table' in table:
                all_data.extend(table['table'])

        return pd.DataFrame(all_data)

    def get_basic_data(
        self,
        codes: Union[str, List[str]],
        indicators: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取基础数据
        
        Args:
            codes: 证券代码
            indicators: 指标代码
            start_date: 开始日期
            end_date: 结束日期
        """
        if isinstance(codes, list):
            codes = ','.join(codes)

        params = {'codes': codes, 'indicators': indicators}
        if start_date:
            params['startdate'] = start_date
        if end_date:
            params['enddate'] = end_date

        data = self._request('basic_data', params)
        return self._to_dataframe(data)

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
        """
        if isinstance(codes, list):
            codes = ','.join(codes)

        params = {'codes': codes, 'indicators': indicators}
        data = self._request('real_time_quotation', params)
        return self._to_dataframe(data)

    def get_high_frequency(
        self,
        codes: Union[str, List[str]],
        indicators: str,
        start_time: str,
        end_time: str,
    ) -> pd.DataFrame:
        """
        获取高频数据
        
        Args:
            codes: 证券代码
            indicators: 指标代码
            start_time: 开始时间 YYYY-MM-DD HH:MM:SS
            end_time: 结束时间
        """
        if isinstance(codes, list):
            codes = ','.join(codes)

        params = {
            'codes': codes,
            'indicators': indicators,
            'starttime': start_time,
            'endtime': end_time,
        }
        data = self._request('high_frequency', params)
        return self._to_dataframe(data)

    def get_data_pool(
        self,
        pool_id: str,
        params: str,
        fields: str,
    ) -> pd.DataFrame:
        """
        获取数据池数据
        
        Args:
            pool_id: 数据池 ID
            params: 查询参数
            fields: 返回字段
        """
        request_params = {
            'reportname': pool_id,
            'functionpara': params,
            'outputpara': fields,
        }
        data = self._request('data_pool', request_params)
        return self._to_dataframe(data)

    def wencai_query(
        self,
        query: str,
        query_type: str = 'stock',
    ) -> pd.DataFrame:
        """
        问财查询
        
        Args:
            query: 查询语句
            query_type: 查询类型
        """
        params = {
            'question': query,
            'perpage': 100,
            'page': 1,
            'secondary_intent': query_type,
            'source': 'Ths_iFinD_PC',
        }
        data = self._request('wencai', params)
        return self._to_dataframe(data)


def main():
    """示例用法"""
    print('iFind HTTP Client 示例')
    print('=' * 50)

    client = IFindHTTPClient()

    # 获取实时行情
    print('\n1. 获取实时行情:')
    data = client.get_realtime_quotes(['000001.SZ', '600000.SH'])
    print(data)


if __name__ == '__main__':
    main()
