#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取同花顺全A(700001)历史行情数据 - 使用iFinDPy本地SDK
"""
import os
import sys
import pandas as pd

# 添加脚本路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifind_client import IFindClient

def main():
    print("=" * 60)
    print("获取同花顺全A(700001)历史行情数据 (iFinDPy SDK)")
    print("=" * 60)

    # 创建客户端并登录
    client = IFindClient()
    client.login()

    # 指数代码 - 同花顺全A (.TI表示指数)
    index_code = "700001.TI"

    # 指标 - 历史行情指标
    indicators = "pre_close;open;high;low;close;vwap;chg;pct_chg;volume;amt;turn"

    # 时间范围 - 根据回测时间调整
    start_date = "2010-03-01"
    end_date = "2026-03-17"

    print(f"\n查询: {index_code}")
    print(f"指标: {indicators}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print("\n正在查询...")

    try:
        # 使用THS_HD获取历史数据
        # 函数签名: THS_HD(codes, indicators, other_params, start_date, end_date)
        from iFinDPy import THS_HD

        result = THS_HD(
            index_code,      # 证券代码
            indicators,      # 指标
            '',              # 附加参数
            start_date,      # 开始日期
            end_date        # 结束日期
        )

        print(f"\n返回结果类型: {type(result)}")
        print(f"返回结果: {result}")

        if hasattr(result, 'data') and result.data is not None:
            data = result.data
            print(f"\n获取到数据: {len(data)} 行")
            print(f"列: {list(data.columns)}")

            # 保存数据
            output_file = "700001_history.csv"
            data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n数据已保存到: {output_file}")

            print("\n前5行:")
            print(data.head())
            print("\n后5行:")
            print(data.tail())
        else:
            error_code = getattr(result, 'errorcode', -1)
            error_msg = getattr(result, 'errormsg', 'Unknown error')
            print(f"\n获取数据失败: errorcode={error_code}, errormsg={error_msg}")

    except Exception as e:
        print(f"\n获取数据失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.logout()

if __name__ == "__main__":
    main()
