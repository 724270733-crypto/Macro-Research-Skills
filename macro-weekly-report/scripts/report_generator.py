"""
宏观策略周报/日报生成器
生成Markdown格式的宏观策略与配置观点报告
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


def get_date_range(report_type: str) -> tuple:
    """获取报告日期范围"""
    today = datetime.now()
    today_str = today.strftime("%Y.%m.%d")

    if report_type == "日报":
        # 日报：前一天
        target_date = today - timedelta(days=1)
        start_date = target_date.strftime("%Y.%m.%d")
        end_date = start_date
    else:
        # 周报：过去一周（周一到周五）
        weekday = today.weekday()
        # 计算上周五
        days_since_friday = (weekday + 2) % 7
        last_friday = today - timedelta(days=days_since_friday)

        # 找到上周一
        start_date = (last_friday - timedelta(days=4)).strftime("%Y.%m.%d")
        end_date = last_friday.strftime("%Y.%m.%d")

    return start_date, end_date, today_str


def generate_report_header(date_range: tuple, report_type: str) -> str:
    """生成报告头部"""
    start_date, end_date, today = date_range
    header = f"""# 宏观策略与配置观点（{end_date}）

> 生成时间：{today} | 报告类型：{report_type} | 数据期间：{start_date} - {end_date}

---
"""
    return header


def generate_abstract(macro_data: Dict) -> str:
    """生成摘要部分"""
    abstract = """## 摘要

**国内宏观：** [在此处填写宏观摘要，包括GDP预测、PPI走势、CPI变化等]

"""
    return abstract


def generate_global_overview(global_data: Dict) -> str:
    """生成全球概览部分"""
    overview = """## 全球概览

### 美国市场
- **FOMC政策：** [FOMC利率决策及声明要点]
- **美债收益率：** [10年期美债收益率变化]
- **美元指数：** [美元指数走势]

### 欧洲市场
- **欧央行政策：** [欧央行利率决策]
- **德国DAX：** [DAX指数表现]

### 全球宏观事件
- [重要全球财经事件简述]

"""
    return overview


def generate_market_review(market_data: Dict) -> str:
    """生成市场回顾部分"""
    review = """## 市场回顾

### A股/权益市场
**主要指数表现：**
| 指数 | 涨跌幅 | 最新点位 |
|------|--------|----------|
| 沪深300 | [±X.XX%] | XXXX |
| 创业板指 | [±X.XX%] | XXXX |
| 上证指数 | [±X.XX%] | XXXX |

**行业表现：** [表现最好/最差的行业]

### 债券市场
- **DR007：** [X.XX%]（[±Xbp]）
- **10年期国债：** [X.XX%]（[±Xbp]）
- **30年期国债：** [X.XX%]（[±Xbp]）

### 商品市场
- **原油（NYMEX）：** [XX.XX] 美元/桶（[±X.XX%]）
- **铜（LME）：** [XXXX] 美元/吨（[±X.XX%]）
- **黄金（COMEX）：** [XXXX] 美元/盎司（[±X.XX%]）

"""
    return review


def generate_allocation_views(allocation_data: Dict) -> str:
    """生成配置观点部分"""
    views = """## 配置观点

### 债券
- **信用债：** [配置建议]
- **利率债：** [交易机会]

### A股/港股
- **行业配置：** [推荐行业]
- **风格判断：** [价值/成长]
- **港股观点：** [港股配置建议]

### 商品
- **原油：** [配置建议]
- **铜：** [配置建议]
- **黄金：** [配置建议]

"""
    return views


def generate_weekly_events(events: List) -> str:
    """生成一周重大事件部分"""
    events_str = """## 一周重大事件

"""
    for i, event in enumerate(events, 1):
        events_str += f"{i}. {event}\n"

    return events_str


def generate_footer() -> str:
    """生成报告尾部"""
    footer = """
---
*报告说明：*

1. 数据来源：iFind
2. 报告内容仅供参考，不构成投资建议

"""
    return footer


def generate_macro_report(report_type: str = "周报", market_data: Optional[Dict] = None) -> str:
    """
    生成完整的宏观策略报告

    Args:
        report_type: 报告类型，"周报" 或 "日报"
        market_data: 市场数据字典（可选）

    Returns:
        Markdown格式的报告字符串
    """
    # 获取日期范围
    date_range = get_date_range(report_type)

    # 生成报告各部分
    report = generate_report_header(date_range, report_type)
    report += generate_abstract({})
    report += generate_global_overview({})
    report += generate_market_review({})
    report += generate_allocation_views({})
    report += generate_weekly_events([
        "[重大事件1]",
        "[重大事件2]",
        "[重大事件3]"
    ])
    report += generate_footer()

    return report


def save_report(report_content: str, filepath: str = None) -> str:
    """保存报告到文件"""
    if filepath is None:
        today = datetime.now().strftime("%Y%m%d")
        filepath = f"macro_report_{today}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

    return filepath


def main():
    """测试报告生成"""
    print("生成测试报告...")
    print("-" * 50)

    # 生成周报
    report = generate_macro_report("周报")
    print(report)

    # 保存到文件
    filepath = save_report(report)
    print(f"\n报告已保存到: {filepath}")


if __name__ == "__main__":
    main()
