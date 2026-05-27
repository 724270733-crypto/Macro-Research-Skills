#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试获取更早的历史数据 - 测试不同指数代码
"""
import requests
import json

accessToken = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
thsHeaders = {"Content-Type": "application/json", "access_token": accessToken}

# 测试不同的指数代码
index_codes = [
    "700001.TI",   # 同花顺全A
    "000852.SH",   # 中证1000
    "000001.SH",   # 上证指数
    "399106.SZ",   # 深证1000
    "000300.SH",   # 沪深300
]

indicators = "close,open,high,low,volume"

for code in index_codes:
    print(f"\n{'='*50}")
    print(f"Testing: {code}")
    print('='*50)

    thsUrl = 'https://quantapi.51ifind.com/api/v1/cmd_history_quotation'
    thsPara = {
        "codes": code,
        "indicators": indicators,
        "startdate": "2010-01-01",
        "enddate": "2010-01-10",
        "functionpara": {"Fill": "Blank"}
    }

    try:
        thsResponse = requests.post(url=thsUrl, json=thsPara, headers=thsHeaders, timeout=30, verify=False)
        data = json.loads(thsResponse.content)

        if data.get('errorcode') == 0:
            tables = data.get('tables', [])
            if tables:
                times = tables[0].get('time', [])
                table_data = tables[0].get('table', {})
                print(f"  Success! Records: {len(times)}")
                print(f"  Date range: {times[0] if times else 'N/A'} to {times[-1] if times else 'N/A'}")
                print(f"  Data keys: {list(table_data.keys())}")
            else:
                print(f"  No data tables")
        else:
            print(f"  Error: {data.get('errmsg')}")
    except Exception as e:
        print(f"  Exception: {e}")
