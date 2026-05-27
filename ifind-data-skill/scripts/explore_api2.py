#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索正确的API端点 - 尝试ftwc.51ifind.com
"""
import requests

ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"

# 尝试 ftwc 域名
BASE_URLS = [
    "https://quantapi.10jqka.com.cn/api/v1",
    "https://ftwc.51ifind.com/api/v1",
]

# 已知的端点
known_endpoints = [
    "real_time_quotation",  # 这个已经确认可用
]

# 尝试更多端点
test_endpoints = [
    # 实时
    ("realtime", {"codes": "000001.SZ"}),
    ("quote", {"codes": "000001.SZ"}),
    # 基础数据
    ("basic", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    ("basic_data", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    # 历史
    ("history", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    ("history_quotes", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    ("his", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    # 日期序列
    ("date_serial", {"codes": "000001.SZ", "indicators": "ths_close_price_stock"}),
    ("date_serial_v2", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    # 日线
    ("daily", {"codes": "000001.SZ"}),
    ("daily_line", {"codes": "000001.SZ"}),
    # K线
    ("kline", {"codes": "000001.SZ", "ktype": "D"}),
    ("minline", {"codes": "000001.SZ", "ktype": "1"}),
    # 问财
    ("wencai", {"question": "000001.SZ 今日收盘价"}),
    ("wc", {"question": "000001.SZ 收盘价"}),
]

headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}

for base_url in BASE_URLS:
    print(f"\n{'='*60}")
    print(f"Testing: {base_url}")
    print('='*60)

    for endpoint, params in test_endpoints:
        url = f"{base_url}/{endpoint}"
        try:
            resp = requests.post(url, json=params, headers=headers, timeout=15, verify=False)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                if data.get('errorcode') == 0:
                    print(f"  {endpoint}: SUCCESS! (tables: {len(data.get('tables', []))})")
                else:
                    print(f"  {endpoint}: API Error - {data.get('errmsg', 'unknown')}")
            elif status == 404:
                print(f"  {endpoint}: 404 Not Found")
            else:
                print(f"  {endpoint}: {status}")
        except requests.exceptions.SSLError:
            print(f"  {endpoint}: SSL Error")
        except Exception as e:
            print(f"  {endpoint}: {e}")
