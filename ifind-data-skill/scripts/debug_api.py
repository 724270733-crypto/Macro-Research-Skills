#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug: 检查API返回的数据结构
"""
import requests
import json

accessToken = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
thsHeaders = {"Content-Type": "application/json", "access_token": accessToken}

thsUrl = 'https://quantapi.51ifind.com/api/v1/cmd_history_quotation'
thsPara = {
    "codes": "700001.TI",
    "indicators": "pre_close;open;high;low;close;vwap;chg;pct_chg;volume;amt;turn",
    "startdate": "2021-03-17",
    "enddate": "2021-03-22",
    "functionpara": {"Fill": "Blank"}
}

thsResponse = requests.post(url=thsUrl, json=thsPara, headers=thsHeaders, timeout=60, verify=False)
data = json.loads(thsResponse.content)

print("Full response:")
print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
