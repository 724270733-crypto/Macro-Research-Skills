#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺全A(700001)历史行情数据
"""
import requests
import json
import pandas as pd
import time

# 设置显示选项
pd.set_option('float_format', lambda x: '%.2f' % x)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 500)

# Token获取
getAccessTokenUrl = 'https://quantapi.51ifind.com/api/v1/get_access_token'
# 您的refresh_token
refreshtoken = 'eyJzaWduX3RpbWUiOiIyMDI2LTAzLTE3IDEyOjA2OjIwIn0=.eyJ1aWQiOiI3OTUzODEwNzIiLCJ1c2VyIjp7ImFjY291bnQiOiJxaHJzbDAwMSIsImF1dGhVc2VySW5mbyI6eyJjc2kiOmZhbHNlfSwiY29kZUNTSSI6W10sImNvZGVaekF1dGgiOlsiMTEiLCIyMiIsIjI1IiwiMjYiLCIxNyIsIjE4IiwiMTkiLCIxIiwiMiIsIjQiLCI1IiwiNyIsIjEwIl0sImhhc0FJUHJlZGljdCI6ZmFsc2UsImhhc0FJVGFsayI6ZmFsc2UsImhhc0NJQ0MiOmZhbHNlLCJoYXNDU0kiOmZhbHNlLCJoYXNFdmVudERyaXZlIjpmYWxzZSwiaGFzRlRTRSI6ZmFsc2UsImhhc0Zhc3QiOmZhbHNlLCJoYXNGdW5kVmFsdWF0aW9uIjpmYWxzZSwiaGFzSEsiOnRydWUsImhhc0xNRSI6ZmFsc2UsImhhc0xldmVsMiI6ZmFsc2UsImhhc1JlYWxDTUUiOmZhbHNlLCJoYXNUcmFuc2ZlciI6ZmFsc2UsImhhc1VTIjpmYWxzZSwiaGFzVVNBSW5kZXgiOmZhbHNlLCJoYXNVU0RFQlQiOmZhbHNlLCJtYXJrZXRBdXRoIjp7IkRDRSI6ZmFsc2V9LCJtYXJrZXRDb2RlIjoiMTY7MzI7MTQ0OzE3NjsxMTI7ODg7NDg7MTI4OzE2OC0xOzE4NDsyMDA7MjE2OzEwNDsxMjA7MTM2OzIzMjs1NjsxNjA7NjQ7IiwibWF4T25MaW5lIjoxLCJub0Rpc2siOmZhbHNlLCJwcm9kdWN0VHlwZSI6IlNVUEVSQ09NTUFORFBST0RVQ1QiLCJyZWZyZXNoVG9rZW5FeHBpcmVkVGltZSI6IjIwMjYtMDQtMTEgMDk6MDY6NTEiLCJzZXNzc2lvbiI6IjI5NzlkZGMyZTUyNzcwMDcwNjExNTA5MmJiYTRhZWNiIiwic2lkSW5mbyI6ezY0OiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDE6IjEwMSIsMjoiMSIsNjc6IjEwMTExMTExMTExMTExMTExMTExMTExMSIsMzoiMSIsNjk6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDU6IjEiLDY6IjEiLDcxOiIxMTExMTExMTExMTExMTExMTExMTExMDAiLDc6IjExMTExMTExMTExIiw4OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDEiLDEzODoiMTExMTExMTExMTExMTExMTExMTExMTExMTExIiwxMzk6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MDoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsMTQxOiIxMTExMTExMTExMTExMTExMTExMTExMTExIiwxNDI6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MzoiMTEiLDgwOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgxOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgyOiIxMTExMTExMTExMTExMTExMTExMTE1MTAiLDgzOiIxMTExMTExMTExMTExMTExMTExMDAwMDAiLDg1OiIwMTExMTExMTExMTExMTExMTExMTExMTEiLDg3OiIxMTExMTExMTAwMTExMTEwMTExMTExMTEiLDg5OiIxMTExMTExMTAxMTAxMDAwMDAwMDExMTEiLDkwOiIxMTExMTAxMTExMTExMTExMTAwMDExMTExMCIsOTM6IjExMTExMTExMTExMTExMTExMTExMDAwMDExMTEiLDk0OiIxMTExMTExMTExMTExMTExMTExMTExMTExIiw5NjoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsOTk6IjEwMCIsMTAwOiIxMTExMDExMTExMTExMTExMTEwIiwxMDI6IjEiLDQ0OiIxMSIsMTA5OiIxIiw1MzoiMTExMTExMTExMTExMTExMTExMTExMTExIiw1NDoiMTEwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAiLDU3OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDEwMDAwMDAwMCIsNjI6IjExMTExMTExMTExMTExMTExMTExMTExMSIsNjM6IjExMTExMTExMTExMTExMTExMTExMTExMSJ9LCJ0aW1lc3RhbXAiOiIxNzczNzIwMzgwNTI3IiwidHJhbnNBdXRoIjpmYWxzZSwidHRsVmFsdWUiOjAsInVpZCI6Ijc5NTM4MTA3MiIsInVzZXJUeXBlIjoiRlJFRUlBTCIsIndpZmluZExpbWl0TWFwIjp7fX19.4986E382D870BEB4853E532ADAE6FE3D03F6B4DDCBAC2ABFC5DE2995896C6D3B'

# 直接使用已获取的Access Token
accessToken = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
print("Using Access Token:", accessToken)

thsHeaders = {"Content-Type": "application/json", "access_token": accessToken}


def history_quotes():
    """获取历史日频行情数据"""
    thsUrl = 'https://quantapi.51ifind.com/api/v1/cmd_history_quotation'

    # 同花顺全A指数 - 使用.TI后缀表示指数
    # 指标: pre_close(前收盘价), open(开盘价), high(最高价), low(最低价), close(收盘价),
    #       vwap(均价), chg(涨跌), pct_chg(涨跌幅), volume(成交量), amt(成交额), turn(换手率)
    # 注意：指标之间用逗号分隔，不是分号！
    thsPara = {
        "codes": "700001.TI",
        "indicators": "pre_close,open,high,low,close,vwap,chg,pct_chg,volume,amt,turn",
        "startdate": "2010-03-01",
        "enddate": "2026-03-17",
        "functionpara": {"Fill": "Blank"}
    }

    print("\nRequesting history quotes...")
    print(f"URL: {thsUrl}")
    print(f"Params: {thsPara}")

    thsResponse = requests.post(url=thsUrl, json=thsPara, headers=thsHeaders, timeout=120, verify=False)
    print(f"Response Status: {thsResponse.status_code}")
    print(f"Response: {thsResponse.content[:2000]}")

    # 解析响应
    data = json.loads(thsResponse.content)

    if data.get('errorcode') == 0:
        tables = data.get('tables', [])
        print(f"\nGot {len(tables)} tables")

        if tables:
            # 解析数据
            all_records = []
            for table in tables:
                thscode = table.get('thscode', '')
                time_list = table.get('time', [])
                table_data = table.get('table', {})

                for i, t in enumerate(time_list):
                    record = {'thscode': thscode, 'trade_date': t}
                    for indicator, values in table_data.items():
                        if values and i < len(values):
                            record[indicator] = values[i]
                    all_records.append(record)

            df = pd.DataFrame(all_records)

            # 重命名列
            column_names = {
                'pre_close': 'pre_close',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vwap': 'vwap',
                'chg': 'chg',
                'pct_chg': 'pct_chg',
                'volume': 'volume',
                'amt': 'amt',
                'turn': 'turn'
            }
            df = df.rename(columns=column_names)

            # 保存到CSV
            output_file = "700001_history.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\nData saved to: {output_file}")
            print(f"Total records: {len(df)}")
            print("\nFirst 5 rows:")
            print(df.head())
            print("\nLast 5 rows:")
            print(df.tail())
    else:
        print(f"API Error: {data.get('errmsg')}")


if __name__ == '__main__':
    history_quotes()
