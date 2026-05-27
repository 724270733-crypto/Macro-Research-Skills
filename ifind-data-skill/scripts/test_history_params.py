#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试用real_time_quotation端点获取历史数据
"""
import requests

ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
BASE_URL = "https://quantapi.10jqka.com.cn/api/v1"

headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}

# 尝试用不同的参数
tests = [
    # 测试1: 实时行情
    {"codes": "000852.SH", "indicators": "latest,open,high,low,preClose"},
    # 测试2: 带日期范围
    {"codes": "000852.SH", "indicators": "latest,open,high,low", "startdate": "20240101", "enddate": "20240110"},
    # 测试3: 多日行情
    {"codes": "000852.SH", "indicators": "latest", "daylist": "20240101,20240102,20240103,20240104,20240105"},
    # 测试4: 扩展参数
    {"codes": "000852.SH", "indicators": "latest,open,high,low,volume", "fields": "all"},
]

for i, params in enumerate(tests):
    print(f"\nTest {i+1}: {params}")
    try:
        resp = requests.post(f"{BASE_URL}/real_time_quotation", json=params, headers=headers, timeout=30)
        data = resp.json()
        if data.get('errorcode') == 0:
            print(f"  Success! Tables: {len(data.get('tables', []))}")
            print(f"  Data: {str(data)[:300]}")
        else:
            print(f"  Error: {data.get('errmsg')}")
    except Exception as e:
        print(f"  Exception: {e}")

# 尝试用多次请求模拟历史数据
print("\n\n尝试多次请求获取历史数据:")
import datetime

# 获取最近5个交易日
today = datetime.datetime.now()
dates = []
for i in range(20):
    d = today - datetime.timedelta(days=i)
    if d.weekday() < 5:  # 工作日
        dates.append(d.strftime("%Y%m%d"))
    if len(dates) >= 5:
        break

print(f"Dates: {dates}")

all_data = []
for date in dates:
    params = {"codes": "000852.SH", "indicators": "latest,open,high,low,preClose,volume", "daylist": date}
    try:
        resp = requests.post(f"{BASE_URL}/real_time_quotation", json=params, headers=headers, timeout=30)
        data = resp.json()
        if data.get('errorcode') == 0:
            tables = data.get('tables', [])
            if tables and 'table' in tables[0]:
                table_data = tables[0]['table']
                all_data.append(table_data)
                print(f"  {date}: Got data")
        else:
            print(f"  {date}: Error - {data.get('errmsg')}")
    except Exception as e:
        print(f"  {date}: Exception - {e}")

print(f"\nTotal records: {len(all_data)}")
