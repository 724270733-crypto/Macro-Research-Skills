#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取50ETF期权隐含波动率/VIX数据
"""
import akshare as ak
import pandas as pd
import os

print("=" * 60)
print("获取50ETF期权隐含波动率(VIX)数据")
print("=" * 60)

# 设置显示选项
pd.set_option('float_format', lambda x: '%.4f' % x)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 500)

try:
    # 获取50ETF期权隐含波动率数据
    print("\n正在获取50ETF期权VIX数据...")
    df = ak.index_option_50etf_qvix()

    print(f"\n获取成功! 数据量: {len(df)} 行")
    print(f"列名: {list(df.columns)}")

    # 显示数据信息
    print("\n数据前10行:")
    print(df.head(10))

    print("\n数据后10行:")
    print(df.tail(10))

    # 检查日期范围
    print(f"\n日期范围:")
    print(f"  最早日期: {df.iloc[0]}")
    print(f"  最新日期: {df.iloc[-1]}")

    # 保存数据
    output_file = "50etf_vix.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n数据已保存到: {output_file}")

except Exception as e:
    print(f"获取数据失败: {e}")
    import traceback
    traceback.print_exc()
