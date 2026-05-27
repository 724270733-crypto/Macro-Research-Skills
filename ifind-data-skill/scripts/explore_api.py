#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索正确的API端点
"""
import requests
import json

ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
BASE_URL = "https://quantapi.10jqka.com.cn/api/v1"

# 测试更多端点
endpoints_to_test = [
    # 基本数据
    ("basic_data", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    ("basic", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    # 历史数据
    ("date_serial", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "params": "Fill:Blank", "startdate": "20240101", "enddate": "20240110"}),
    ("history", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    ("his", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    # 序列数据
    ("serial", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    # 指数专用
    ("index_daily", {"codes": "000852.SH", "indicators": "ths_close_index", "startdate": "20240101", "enddate": "20240110"}),
    # 日线
    ("daily", {"codes": "000001.SZ", "start_date": "20240101", "end_date": "20240110"}),
    # K线
    ("kline", {"codes": "000001.SZ", "ktype": "D", "startdate": "20240101", "enddate": "20240110"}),
]

headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}

for endpoint, params in endpoints_to_test:
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.post(url, json=params, headers=headers, timeout=15)
        print(f"\n{endpoint}: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('errorcode') == 0:
                print(f"  Success! tables: {len(data.get('tables', []))}")
            else:
                print(f"  Error: {data.get('errmsg', 'unknown')}")
        else:
            print(f"  Response: {resp.text[:100]}")
    except requests.exceptions.SSLError:
        print(f"\n{endpoint}: SSL Error")
    except Exception as e:
        print(f"\n{endpoint}: {e}")
