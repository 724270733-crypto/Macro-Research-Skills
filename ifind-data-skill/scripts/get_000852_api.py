#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺全A(000852)历史行情数据 - 使用正确的API
"""
import requests
import pandas as pd

# Access Token from user
ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"

BASE_URL = "https://quantapi.10jqka.com.cn/api/v1"

def get_realtime_quotes(codes, indicators="latest,open,high,low,preClose,volume,amount,changeRatio"):
    """获取实时行情"""
    url = f"{BASE_URL}/real_time_quotation"
    headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}
    params = {"codes": codes, "indicators": indicators}

    resp = requests.post(url, json=params, headers=headers, timeout=30)
    data = resp.json()

    if data.get('errorcode') != 0:
        print(f"Error: {data}")
        return None

    # 解析数据
    tables = data.get('tables', [])
    if not tables:
        return None

    records = []
    for table in tables:
        thscode = table.get('thscode', '')
        table_data = table.get('table', {})
        time = table.get('time', [''])[0]

        record = {'thscode': thscode, 'time': time}
        for key, values in table_data.items():
            if values and len(values) > 0:
                record[key] = values[0]
        records.append(record)

    return pd.DataFrame(records)

def get_index_historical():
    """尝试获取指数历史数据"""
    # 尝试不同的API端点
    endpoints = [
        ("date_serial", {"codes": "000852.SH", "indicators": "ths_close_index,ths_open_index,ths_high_index,ths_low_index", "startdate": "20240101", "enddate": "20241231"}),
        ("history_quotes", {"codes": "000852.SH", "indicators": "ths_close_index,ths_open_index", "startdate": "20240101", "enddate": "20241231"}),
    ]

    for endpoint, params in endpoints:
        url = f"{BASE_URL}/{endpoint}"
        headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}

        print(f"\nTrying endpoint: {endpoint}")
        print(f"Params: {params}")

        try:
            resp = requests.post(url, json=params, headers=headers, timeout=30)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:500]}")

            if resp.status_code == 200:
                data = resp.json()
                if data.get('errorcode') == 0:
                    print(f"Success! Got {len(data.get('tables', []))} tables")
                    return data
        except Exception as e:
            print(f"Error: {e}")

    return None

def main():
    print("=" * 60)
    print("获取同花顺全A(000852)数据")
    print("=" * 60)

    # 测试1: 获取实时行情
    print("\n1. 测试实时行情 (000001.SZ):")
    df = get_realtime_quotes("000001.SZ")
    if df is not None:
        print(df)

    # 测试2: 获取指数实时行情
    print("\n2. 测试指数实时行情 (000852.SH):")
    df = get_realtime_quotes("000852.SH", "latest,open,high,low,preClose")
    if df is not None:
        print(df)

    # 测试3: 尝试获取历史数据
    print("\n3. 尝试获取历史数据:")
    data = get_index_historical()

if __name__ == "__main__":
    main()
