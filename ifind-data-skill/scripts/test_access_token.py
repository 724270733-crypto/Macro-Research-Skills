#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test iFind API with Access Token
"""
import requests

# Access Token from user
ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"

# Test API endpoint with access token
url = "https://quantapi.10jqka.com.cn/api/v1/basic_data"

# Test different endpoints
endpoints_to_test = [
    ("basic_data", {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}),
    ("real_time_quotation", {"codes": "000001.SZ", "indicators": "latest,open,high,low"}),
]

import json

for endpoint, params in endpoints_to_test:
    print(f"\n{'='*60}")
    print(f"Testing endpoint: {endpoint}")
    print(f"Params: {params}")
    print('='*60)

    try:
        full_url = f"https://quantapi.10jqka.com.cn/api/v1/{endpoint}"
        headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}
        resp = requests.post(full_url, json=params, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:1000]}")
    except Exception as e:
        print(f"Error: {e}")

# Also try ftwc.51ifind.com
print(f"\n\n{'='*60}")
print("Testing with ftwc.51ifind.com")
print('='*60)

try:
    full_url = "https://ftwc.51ifind.com/api/v1/basic_data"
    headers = {'access_token': ACCESS_TOKEN, 'Content-Type': 'application/json'}
    params = {"codes": "000001.SZ", "indicators": "ths_close_price_stock", "startdate": "20240101", "enddate": "20240110"}
    resp = requests.post(full_url, json=params, headers=headers, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
