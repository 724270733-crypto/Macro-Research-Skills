#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺全A(000852)完整历史行情数据
"""
import requests
import pandas as pd
import datetime
import time
import os

ACCESS_TOKEN = "0b6fa1f18e7f28f80339cba3a12dfc27186df292.signs_Nzk1MzgxMDcy"
BASE_URL = "https://quantapi.10jqka.com.cn/api/v1"

def get_trading_dates(start_date, end_date):
    """生成交易日列表"""
    dates = []
    current = datetime.datetime.strptime(start_date, "%Y%m%d")
    end = datetime.datetime.strptime(end_date, "%Y%m%d")

    while current <= end:
        # 跳过周末
        if current.weekday() < 5:
            dates.append(current.strftime("%Y%m%d"))
        current += datetime.timedelta(days=1)

    return dates

def get_index_data_batch(codes, dates, indicators):
    """批量获取指数数据"""
    headers = {
        'access_token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }

    # 将日期列表转为逗号分隔的字符串
    daylist = ",".join(dates)

    params = {
        "codes": codes,
        "indicators": indicators,
        "daylist": daylist
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/real_time_quotation",
            json=params,
            headers=headers,
            timeout=60,
            verify=False
        )
        data = resp.json()

        if data.get('errorcode') == 0:
            return data
        else:
            print(f"API Error: {data.get('errmsg')}")
            return None
    except Exception as e:
        print(f"Request Error: {e}")
        return None

def parse_response(data):
    """解析API响应"""
    if not data or 'tables' not in data:
        return []

    tables = data['tables']
    if not tables:
        return []

    # 解析数据
    records = []
    for table in tables:
        thscode = table.get('thscode', '')
        table_data = table.get('table', {})
        times = table.get('time', [])

        # 获取每个指标的数据
        for i, t in enumerate(times):
            record = {
                'thscode': thscode,
                'trade_date': t.split()[0] if t else '',
            }

            for indicator, values in table_data.items():
                if values and i < len(values):
                    record[indicator] = values[i]

            records.append(record)

    return records

def main():
    print("=" * 60)
    print("获取同花顺全A(000852)历史行情数据")
    print("=" * 60)

    # 指数代码 - 同花顺全A
    index_code = "000852.SH"

    # 指标
    indicators = "latest,open,high,low,preClose,volume"

    # 时间范围
    start_date = "20100101"
    end_date = "20251219"

    print(f"\n指数: {index_code}")
    print(f"指标: {indicators}")
    print(f"时间范围: {start_date} - {end_date}")

    # 获取所有交易日
    print("\n生成交易日列表...")
    all_dates = get_trading_dates(start_date, end_date)
    print(f"总交易日数: {len(all_dates)}")

    # 每次请求100个交易日
    batch_size = 100
    all_records = []

    print("\n开始获取数据...")
    for i in range(0, len(all_dates), batch_size):
        batch_dates = all_dates[i:i+batch_size]
        print(f"获取 {i+1}-{min(i+batch_size, len(all_dates))} / {len(all_dates)}...")

        data = get_index_data_batch(index_code, batch_dates, indicators)

        if data:
            records = parse_response(data)
            all_records.extend(records)
            print(f"  获取到 {len(records)} 条记录")
        else:
            print(f"  获取失败")

        # 避免请求过快
        time.sleep(0.5)

    print(f"\n总共获取 {len(all_records)} 条记录")

    # 创建DataFrame
    df = pd.DataFrame(all_records)

    if not df.empty:
        # 整理列顺序
        cols = ['thscode', 'trade_date', 'latest', 'open', 'high', 'low', 'preClose', 'volume']
        df = df[[c for c in cols if c in df.columns]]

        # 重命名列
        df.columns = ['thscode', 'trade_date', 'close', 'open', 'high', 'low', 'pre_close', 'volume']

        # 按日期排序
        df = df.sort_values('trade_date')

        # 保存到CSV
        output_file = "000852_history.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: {output_file}")

        print("\n前5行:")
        print(df.head())
        print("\n后5行:")
        print(df.tail())
    else:
        print("\n没有获取到数据")

if __name__ == "__main__":
    main()
