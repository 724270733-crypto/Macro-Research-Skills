---
name: macro-weekly-report
description: |
  宏观策略周报/日报生成技能 - 当用户说"生成周报"、"生成日报"、"宏观策略报告"、"宏观周报"、"分析报告"、"帮我写周报"、"生成宏观分析报告"时使用此技能。

  此技能帮助用户自动生成宏观策略与配置观点周报或日报，数据来源为iFind金融终端API。报告涵盖全球经济形势、A股市场、债券市场、商品市场分析，以及配置建议。

  使用场景：
  - 用户需要每周或每天生成类似的宏观策略周报/日报
  - 用户想要自动获取最新市场数据并生成分析报告
  - 用户说"帮我生成上周的宏观周报"、"生成今天的日报"等
---

# 宏观策略周报/日报生成技能

## 技能概述

本技能帮助用户自动生成宏观策略与配置观点周报或日报。报告基于iFind金融数据API获取的最新市场数据，生成结构化的Markdown格式报告。

## iFind API配置

iFind API认证信息：
- API Token: `eyJzaWduX3RpbWUiOiIyMDI2LTAzLTE3IDEyOjA2OjIwIn0=.eyJ1aWQiOiI3OTUzODEwNzIiLCJ1c2VyIjp7ImFjY291bnQiOiJxaHJzbDAwMSIsImF1dGhVc2VySW5mbyI6eyJjc2kiOmZhbHNlfSwiY29kZUNTSSI6W10sImNvZGVaekF1dGgiOlsiMTEiLCIyMiIsIjI1IiwiMjYiLCIxNyIsIjE4IiwiMTkiLCIxIiwiMiIsIjQiLCI1IiwiNyIsIjEwIl0sImhhc0FJUHJlZGljdCI6ZmFsc2UsImhhc0FJVGFsayI6ZmFsc2UsImhhc0NJQ0MiOmZhbHNlLCJoYXNDU0kiOmZhbHNlLCJoYXNFdmVudERyaXZlIjpmYWxzZSwiaGFzRlRTRSI6ZmFsc2UsImhhc0Zhc3QiOmZhbHNlLCJoYXNGdW5kVmFsdWF0aW9uIjpmYWxzZSwiaGFzSEsiOnRydWUsImhhc0xNRSI6ZmFsc2UsImhhc0xldmVsMiI6ZmFsc2UsImhhc1JlYWxDTUUiOmZhbHNlLCJoYXNUcmFuc2ZlciI6ZmFsc2UsImhhc1VTIjpmYWxzZSwiaGFzVVNBSW5kZXgiOmZhbHNlLCJoYXNVU0RFQlQiOmZhbHNlLCJtYXJrZXRBdXRoIjp7IkRDRSI6ZmFsc2V9LCJtYXJrZXRDb2RlIjoiMTY7MzI7MTQ0OzE3NjsxMTI7ODg7NDg7MTI4OzE2OC0xOzE4NDsyMDA7MjE2OzEwNDsxMjA7MTM2OzIzMjs1Njs5NjsxNjA7NjQ7IiwibWF4T25MaW5lIjoxLCJub0Rpc2MiOmZhbHNlLCJwcm9kdWN0VHlwZSI6IlNVUEVSQ09NTUFORFBST0RVQ1QiLCJyZWZyZXNoVG9rZW5FeHBpcmVkVGltZSI6IjIwMjYtMDQtMTEgMDk6MDY6NTEiLCJzZXNzc2lvbiI6IjI5NzlkZGMyZTUyNzcwMDcwNjExNTA5MmJiYTRhZWNiIiwic2lkSW5mbyI6ezY0OiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDE6IjEwMSIsMjoiMSIsNjc6IjEwMTExMTExMTExMTExMTExMTExMTExMSIsMzoiMSIsNjk6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDU6IjEiLDY6IjEiLDcxOiIxMTExMTExMTExMTExMTExMTExMTExMDAiLDc6IjExMTExMTExMTExIiw4OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDEiLDEzODoiMTExMTExMTExMTExMTExMTExMTExMTExMTEiLDEzOToiMTExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MDoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsMTQxOiIxMTExMTExMTExMTExMTExMTExMTExMTExIiwxNDI6IjExMTExMTExMTExMTExMTExMTExMTExMTEiLDE0MzoiMTEiLDgwOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgxOiIxMTExMTExMTExMTExMTExMTExMTExMTEiLDgyOiIxMTExMTExMTExMTExMTExMTExMTAxMTAiLDgzOiIxMTExMTExMTExMTExMTExMTExMDAwMDAwIiw4NToiMDExMTExMTExMTExMTExMTExMTExMTExMSIsODc6IjExMTExMTExMTAwMTExMTEwMTExMTExMTEiLDg5OiIxMTExMTExMTAxMTAxMDAwMDAwMDExMTEiLDkwOiIxMTExMTAxMTExMTExMTExMTAwMDExMTExMCIsOTM6IjExMTExMTExMTExMTExMTExMDAwMDExMTEiLDk0OiIxMTExMTExMTExMTExMTExMTExMTExMTExIiw5NjoiMTExMTExMTExMTExMTExMTExMTExMTExMSIsOTk6IjEwMCIsMTAwOiIxMTExMDExMTExMTExMTExMTEwIiwxMDI6IjEiLDQ0OiIxMSIsMTA5OiIxIiw1MzoiMTExMTExMTExMTExMTExMTExMTExMTExIiw1NDoiMTEwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAiLDU3OiIwMDAwMDAwMDAwMDAwMDAwMDAwMDAxMDAwMDAwMDAwMCIsNjI6IjExMTExMTExMTExMTExMTExMTExMTExMSIsNjM6IjExMTExMTExMTExMTExMTExMTExMTExMSJ9LCJ0aW1lc3RhbXAiOiIxNzczNzIwMzgwNTI3IiwidHJhbnNBdXRoIjpmYWxzZSwidHRsVmFsdWUiOjAsInVpZCI6Ijc5NTM4MTA3MiIsInVzZXJUeXBlIjoiRlJFRUlBTCIsIndpZmluZExpbWl0TWFwIjp7fX19.4986E382D870BEB4853E532ADAE6FE3D03F6B4DDCBAC2ABFC5DE2995896C6D3B`
- API Base URL: `https://iwinvip.ifind.com.hk/ifind-data-api/api/v1`

## 数据获取

### 使用ifind-data-skill获取数据

调用ifind-data-skill skill来获取以下数据：

1. **宏观经济数据**：
   - GDP同比/环比
   - PPI同比/环比
   - CPI同比/环比
   - 制造业PMI
   - 社会融资规模

2. **A股市场数据**：
   - 沪深300指数行情
   - 创业板指行情
   - 上证指数行情
   - 行业板块表现

3. **债券市场数据**：
   - DR007（银行间质押式回购利率）
   - 10年期国债收益率
   - 30年期国债收益率
   - 国债收益率曲线变化

4. **商品市场数据**：
   - 原油期货价格（NYMEX原油）
   - 铜期货价格（LME铜）
   - 黄金期货价格（COMEX黄金）

5. **全球宏观数据**：
   - FOMC利率决策
   - 欧央行利率决策
   - 美债收益率
   - 美元指数

### 调用方式

使用Skill工具调用ifind-data-skill，传入具体数据查询请求。

## 报告结构

生成的报告必须包含以下结构：

```markdown
# 宏观策略与配置观点（[日期]）

## 摘要
[宏观经济要点概述，包括GDP、PPI等关键指标预测]

## 全球概览
### 美国市场
[FOMC政策、 美债收益率、美元指数等]
### 欧洲市场
[欧央行政策、德国DAX指数等]
### 全球宏观事件
[重要财经事件简述]

## 市场回顾
### A股/权益市场
[主要指数表现、行业表现]
### 债券市场
[DR007、国债收益率曲线分析]
### 商品市场
[原油、铜、黄金价格走势]

## 配置观点
### 债券
[信用债配置建议]
### A股/港股
[行业配置建议]
### 商品
[原油、铜等配置建议]

## 一周重大事件
[按时间顺序排列的重要财经事件]
```

## 工作流程

1. **确定报告类型**：根据用户请求确定生成日报还是周报
   - 周报：覆盖过去一周（通常周一至周五）
   - 日报：覆盖前一天

2. **获取数据**：使用ifind-data-skill获取各类市场数据

3. **数据处理**：计算涨跌幅、环比、同比变化

4. **生成报告**：按照上述结构生成Markdown格式报告

5. **输出保存**：将报告保存到用户指定目录或当前目录

## 输出格式

- 优先输出Markdown格式
- 如需转换为docx，使用python-docx库
- 数据来源标注：每个数据图表注明"数据来源：iFind"

## 注意事项

- 日期格式：[年].[月].[日]，如2026.03.24
- 涨跌幅使用百分比，保留2位小数
- 利率使用百分比，保留2位小数
- 关键数据变化用箭头标注（↑上涨/下跌）
