#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同指数代码格式
"""
import requests

ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
url = "https://quantapi.10jqka.com.cn/api/v1/real_time_quotation"
headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}

# 尝试不同代码
codes_to_test = [
    '700001',
    '700001.SH',
    '700001.SH:CN',
    '000852',
    '000852.SH',
    '000852.SH:CN',
]

for code in codes_to_test:
    params = {'codes': code, 'indicators': 'latest'}
    try:
        resp = requests.post(url, json=params, headers=headers, timeout=30, verify=False)
        data = resp.json()
        print(f"{code}: errorcode={data.get('errorcode')}, tables={len(data.get('tables', []))}")
        if data.get('errorcode') == 0 and data.get('tables'):
            print(f"  Data: {data['tables']}")
    except Exception as e:
        print(f"{code}: Error - {e}")
