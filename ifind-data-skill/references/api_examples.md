# iFind API 调用示例

## 股票数据查询

### 获取单只股票收盘价

```python
from scripts.ifind_client import IFindClient

client = IFindClient()
client.login()

# 获取平安银行 2024-01-15 的收盘价（不复权）
data = client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,100')
print(data)
```

### 获取多只股票多个指标

```python
# 获取多只股票的收盘价和市盈率
data = client.get_basic_data(
    ['000001.SZ', '600000.SH', '600519.SH'],
    'ths_close_price_stock,ths_pe_stock,ths_pb_stock',
    '2024-01-15,100'
)
```

### 获取历史价格序列

```python
# 获取2024年1月的历史收盘价
data = client.get_date_serial(
    '000001.SZ',
    'ths_close_price_stock',
    'Fill:Blank',
    '2024-01-01',
    '2024-01-31'
)
```

### 获取前复权价格

```python
# 101 表示前复权
data = client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,101')
```

## 实时行情查询

### 获取最新价

```python
data = client.get_realtime_quotes('000001.SZ', 'latest,changeRatio')
print(f"最新价: {data.iloc[0]['latest']}")
print(f"涨跌幅: {data.iloc[0]['changeRatio']}%")
```

### 获取完整行情快照

```python
indicators = 'latest,open,high,low,preClose,volume,amount,change,changeRatio,turnoverRatio,pe,pb'
data = client.get_realtime_quotes(['000001.SZ', '600000.SH'], indicators)
```

### 获取 Level2 盘口数据

```python
indicators = 'latest,bid1,bid2,bid3,bid4,bid5,bidVol1,bidVol2,bidVol3,bidVol4,bidVol5,ask1,ask2,ask3,ask4,ask5,askVol1,askVol2,askVol3,askVol4,askVol5'
data = client.get_realtime_quotes('000001.SZ', indicators)
```

## 问财自然语言查询

### 条件选股

```python
# 低估值选股
data = client.wencai_query('市盈率小于20且市净率小于2且ROE大于15%的股票', 'stock')

# 高股息选股
data = client.wencai_query('股息率大于3%的股票', 'stock')

# 大市值选股
data = client.wencai_query('市值大于1000亿的股票', 'stock')
```

### 行情相关查询

```python
# 涨停股
data = client.wencai_query('今日涨停的股票', 'stock')

# 跌停股
data = client.wencai_query('今日跌停的股票', 'stock')

# 创新高
data = client.wencai_query('创60日新高的股票', 'stock')
```

### 资金流向

```python
# 主力资金流入
data = client.wencai_query('主力资金流入的股票', 'stock')

# 北向资金
data = client.wencai_query('北向资金流入的股票', 'stock')
```

### 行业和概念

```python
# 行业龙头
data = client.wencai_query('半导体行业市值前10的股票', 'stock')

# 概念股
data = client.wencai_query('人工智能概念的股票', 'stock')
```

## 指数和板块

### 获取指数成分股

```python
# 获取沪深300成分股
data = client.get_data_pool(
    'p03291',
    'date=20240115;blockname=001005261;iv_type=allcontract',
    'p03291_f001:Y,p03291_f002:Y,p03291_f003:Y,p03291_f004:Y'
)
```

### 获取指数行情

```python
# 主要指数实时行情
indices = ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH', '000905.SH']
data = client.get_realtime_quotes(indices)
```

### 获取指数估值

```python
data = client.get_basic_data(
    ['000300.SH', '000905.SH', '000852.SH'],
    'ths_pe_index,ths_pb_index',
    '2024-01-15'
)
```

## 基金数据

### 获取基金净值

```python
# 单位净值
data = client.get_basic_data('000001.OF', 'ths_unit_nav_fund', '2024-01-15')

# 累计净值
data = client.get_basic_data('000001.OF', 'ths_acc_nav_fund', '2024-01-15')
```

### 获取基金业绩

```python
indicators = 'ths_return_1w_fund,ths_return_1m_fund,ths_return_3m_fund,ths_return_1y_fund'
data = client.get_basic_data('000001.OF', indicators, '2024-01-15')
```

### 搜索基金

```python
# 医药主题基金
data = client.wencai_query('医药主题基金', 'fund')

# 高收益基金
data = client.wencai_query('近一年收益超过20%的基金', 'fund')
```

## 高频数据

### 获取分钟K线

```python
# 获取1分钟K线
data = client.get_high_frequency(
    '000001.SZ',
    'open,high,low,close,volume,amount',
    '2024-01-15 09:30:00',
    '2024-01-15 15:00:00',
    '1min'
)

# 获取5分钟K线
data = client.get_high_frequency(
    '000001.SZ',
    'open,high,low,close,volume,amount',
    '2024-01-15 09:30:00',
    '2024-01-15 15:00:00',
    '5min'
)
```

## 使用上下文管理器

```python
# 推荐方式：自动登录/登出
with IFindClient() as client:
    data = client.get_basic_data('000001.SZ', 'ths_close_price_stock', '2024-01-15,100')
    print(data)
# 退出时自动登出
```

## HTTP 客户端用法

无需安装本地 SDK：

```python
from scripts.http_client import IFindHTTPClient

client = IFindHTTPClient()  # 需配置 IFIND_REFRESH_TOKEN

# 获取实时行情
data = client.get_realtime_quotes(['000001.SZ', '600000.SH'])

# 获取高频数据
data = client.get_high_frequency(
    '000001.SZ',
    'open,high,low,close,volume,amount',
    '2024-01-15 09:30:00',
    '2024-01-15 15:00:00'
)
```
