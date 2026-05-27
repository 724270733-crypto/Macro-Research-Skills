#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug: 尝试不同的指标格式
"""
import requests
import json

accessToken = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
thsHeaders = {"Content-Type": "application/json", "access_token": accessToken}

# 尝试不同的指标格式
indicators_list = [
    "pre_close,open,high,low,close,vwap,chg,pct_chg,volume,amt,turn",  # 逗号分隔
    "pre_close;open;high;low;close;vwap;chg;pct_chg;volume;amt;turn",  # 分号分隔
    "close",  # 单个指标
]

for ind in indicators_list:
    print(f"\n{'='*50}")
    print(f"Testing indicators: {ind}")
    print('='*50)

    thsUrl = 'https://quantapi.51ifind.com/api/v1/cmd_history_quotation'
    thsPara = {
        "codes": "700001.TI",
        "indicators": ind,
        "startdate": "2021-03-17",
        "enddate": "2021-03-22",
        "functionpara": {"Fill": "Blank"}
    }

    thsResponse = requests.post(url=thsUrl, json=thsPara, headers=thsHeaders, timeout=60, verify=False)
    data = json.loads(thsResponse.content)

    tables = data.get('tables', [])
    if tables:
        table = tables[0].get('table', {})
        print(f"table keys: {list(table.keys())}")
        print(f"table content: {table}")
    else:
        print("No tables in response")
