#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺全A(000852)历史行情数据
"""
import os
import pandas as pd

from http_client import IFindHTTPClient

def main():
    print("=" * 60)
    print("获取同花顺全A(000852)历史行情数据")
    print("=" * 60)

    # 创建HTTP客户端
    client = IFindHTTPClient()

    # 指数代码 - 同花顺全A
    index_code = "000852.SH"

    # 指标 - 使用指数指标
    indicators = "ths_close_index,ths_open_index,ths_high_index,ths_low_index,ths_vol_index,ths_amt_index"

    start_date = "20100101"
    end_date = "20251219"

    print(f"\n查询: {index_code}")
    print(f"指标: {indicators}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print("\n正在查询...")

    try:
        # 获取基础数据（带日期范围）
        data = client.get_basic_data(
            index_code,
            indicators,
            start_date=start_date,
            end_date=end_date
        )

        print(f"\n获取到数据: {len(data)} 行")
        print(f"列: {list(data.columns)}")
        print("\n前5行:")
        print(data.head())
        print("\n后5行:")
        print(data.tail())

        # 保存数据
        output_file = "000852_history.csv"
        data.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: {output_file}")

    except Exception as e:
        print(f"\n获取数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
