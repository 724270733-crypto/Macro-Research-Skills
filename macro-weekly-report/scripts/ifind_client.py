"""
iFind API 数据获取脚本
用于宏观策略周报/日报生成
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# iFind API 配置
API_TOKEN = "eyJzaWduX3RpbWUiOiIyMDI2LTAzLTE3IDEyOjA2OjIwIn0=.eyJ1aWQiOiI3OTUzODEwNzIiLCJ1c2VyIjp7ImFjY291bnQiOiJxaHJzbDAwMSIsImF1dGhVc2VySW5mbyI6eyJjc2kiOmZhbHNlfSwiY29kZUNTSSI6W10sImNvZGVaekF1dGgiOlsiMTEiLCIyMiIsIjI1IiwiMjYiLCIxNyIsIjE4IiwiMTkiLCIxIiwiMiIsIjQiLCI1IiwiNyIsIjEwIl0sImhhc0FJUHJlZGljdCI6ZmFsc2UsImhhc0FJVGFsayI6ZmFsc2UsImhhc0NJQ0MiOmZhbHNlLCJoYXNDU0kiOmZhbHNlLCJoYXNFdmVudERyaXZlIjpmYWxzZSwiaGFzRlRTRSI6ZmFsc2UsImhhc0Zhc3QiOmZhbHNlLCJoYXNGdW5kVmFsdWF0aW9uIjpmYWxzZSwiaGFzSEsiOnRydWUsImhhc0xNRSI6ZmFsc2UsImhhc0xldmVsMiI6ZmFsc2UsImhhc1JlYWxDTUUiOmZhbHNlLCJoYXNUcmFuc2ZlciI6ZmFsc2UsImhhc1VTIjpmYWxzZSwiaGFzVVNBSW5kZXgiOmZhbHNlLCJoYXNVU0RFQlQiOmZhbHNlLCJtYXJrZXRBdXRoIjp7IkRDRSI6ZmFsc2V9LCJtYXJrZXRDb2RlIjoiMTY7MzI7MTQ0OzE3NjsxMTI7ODg7NDg7MTI4OzE2OC0xOzE4NDsyMDA7MjE2OzEwNDsxMjA7MTM2OzIzMjs1Njs5NjsxNjA7NjQ7IiwibWF4T25MaW5lIjoxLCJub0Rpc2MiOmZhbHNlLCJwcm9kdWN0VHlwZSI6IlNVUEVSQ09NTUFORFBST0RVQ1QiLCJyZWZyZXNoVG9rZW5FeHBpcmVkVGltZSI6IjIwMjYtMDQtMTEgMDk6MDY6NTEiLCJzZXNzc2lvbiI6IjI5NzlkZGMyZTUyNzcwMDcwNjExNTA5MmJiYTRhZWNiIiwic2lkSW5mbyI6ezY0OiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDE6IjEwMSIsMjoiMSIsNjc6IjEwMTExMTExMTExMTExMTExMTExMTExMSIsMzoiMSIsNjk6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDU6IjEiLDY6IjEiLDcxOiIxMTExMTExMTExMTExMTExMTExMTExMDAiLDc6IjExMTExMTExMTExIiw4OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDEiLDEzODoiMTExMTExMTExMTExMTExMTExMTExMTExMTEiLDEzOToiMTExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MDoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsMTQxOiIxMTExMTExMTExMTExMTExMTExMTExMTExIiwxNDI6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MzoiMTEiLDgwOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgxOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgyOiIxMTExMTExMTExMTExMTExMTExMTAxMTAiLDgzOiIxMTExMTExMTExMTExMTExMTExMDAwMDAwIiw4NToiMDExMTExMTExMTExMTExMTExMTExMTExMSIsODc6IjExMTExMTExMTAwMTExMTEwMTExMTExMTEiLDg5OiIxMTExMTExMTAxMTAxMDAwMDAwMDExMTEiLDkwOiIxMTExMTAxMTExMTExMTExMTAwMDExMTExMCIsOTM6IjExMTExMTExMTExMTExMTExMDAwMDExMTEiLDk0OiIxMTExMTExMTExMTExMTExMTExMTExMTExIiw5NjoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsOTk6IjEwMCIsMTAwOiIxMTExMDExMTExMTExMTExMTEwIiwxMDI6IjEiLDQ0OiIxMSIsMTA5OiIxIiw1MzoiMTExMTExMTExMTExMTExMTExMTExMTExIiw1NDoiMTEwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAiLDU3OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMDAwMDAwMCIsNjI6IjExMTExMTExMTExMTExMTExMTExMTExMSIsNjM6IjExMTExMTExMTExMTExMTExMTExMTExMSJ9LCJ0aW1lc3RhbXAiOiIxNzczNzIwMzgwNTI3IiwidHJhbnNBdXRoIjpmYWxzZSwidHRsVmFsdWUiOjAsInVpZCI6Ijc5NTM4MTA3MiIsInVzZXJUeXBlIjoiRlJFRUlBTCIsIndpZmluZExpbWl0TWFwIjp7fX19.4986E382D870BEB4853E532ADAE6FE3D03F6B4DDCBAC2ABFC5DE2995896C6D3B"
BASE_URL = "https://iwinvip.ifind.com.hk/ifind-data-api/api/v1"


class IFindClient:
    """iFind API 客户端"""

    def __init__(self, token: str = API_TOKEN):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def get_market_data(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """获取市场数据"""
        endpoint = f"{BASE_URL}/market_data"
        params = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()

    def get_macro_data(self, indicator: str, period: str = "monthly") -> Dict:
        """获取宏观经济数据"""
        endpoint = f"{BASE_URL}/macro_data"
        params = {
            "indicator": indicator,
            "period": period
        }
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()

    def get_index_constituent(self, index_code: str) -> Dict:
        """获取指数成分股"""
        endpoint = f"{BASE_URL}/index_constituent"
        params = {"index_code": index_code}
        response = requests.get(endpoint, headers=self.headers, params=params)
        return response.json()


def get_trading_dates(start_date: str, end_date: str) -> List[str]:
    """获取交易日列表（排除周末）"""
    dates = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        if current.weekday() < 5:  # 0-4 表示周一到周五
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def format_change(old_value: float, new_value: float) -> tuple:
    """计算变化值和变化率"""
    change = new_value - old_value
    change_pct = (change / old_value) * 100 if old_value != 0 else 0
    return change, change_pct


def main():
    """测试数据获取"""
    client = IFindClient()

    # 测试获取上证指数数据
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"测试获取数据: {week_ago} 到 {today}")
    print("-" * 50)

    # 这里可以添加更多测试代码
    print("iFind API 客户端初始化成功")


if __name__ == "__main__":
    main()
