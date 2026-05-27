# iFind 指标代码参考

## 股票行情指标

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 收盘价 | `ths_close_price_stock` | 日收盘价 |
| 开盘价 | `ths_open_price_stock` | 日开盘价 |
| 最高价 | `ths_high_price_stock` | 日最高价 |
| 最低价 | `ths_low_price_stock` | 日最低价 |
| 成交量 | `ths_vol_stock` | 成交量（股） |
| 成交额 | `ths_amt_stock` | 成交额（元） |
| 涨跌幅 | `ths_chg_ratio_stock` | 涨跌幅（%） |
| 换手率 | `ths_turnover_ratio_stock` | 换手率（%） |

## 股票估值指标

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 市盈率 | `ths_pe_stock` | PE（静态） |
| 市盈率TTM | `ths_pe_ttm_stock` | PE（滚动） |
| 市净率 | `ths_pb_stock` | PB |
| 市销率 | `ths_ps_stock` | PS |
| 总市值 | `ths_market_value_stock` | 总市值（元） |
| 流通市值 | `ths_float_mv_stock` | 流通市值（元） |
| 股息率 | `ths_dividend_yield_stock` | 股息率（%） |

## 股票财务指标

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 营业收入 | `ths_or_stock` | 营业收入（元） |
| 净利润 | `ths_np_stock` | 净利润（元） |
| ROE | `ths_roe_stock` | 净资产收益率（%） |
| ROA | `ths_roa_stock` | 总资产收益率（%） |
| EPS | `ths_eps_stock` | 每股收益（元） |
| BPS | `ths_bps_stock` | 每股净资产（元） |
| 毛利率 | `ths_gross_profit_margin_stock` | 毛利率（%） |
| 净利率 | `ths_net_profit_margin_stock` | 净利率（%） |

## 股票基础信息

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 股票简称 | `ths_stock_short_name_stock` | 股票名称 |
| 所属行业 | `ths_the_sw_industry_stock` | 申万行业 |
| 上市日期 | `ths_ipo_date_stock` | IPO 日期 |

## 基金指标

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 单位净值 | `ths_unit_nav_fund` | 单位净值 |
| 累计净值 | `ths_acc_nav_fund` | 累计净值 |
| 复权净值 | `ths_unit_nav_adj_fund` | 复权单位净值 |
| 日收益率 | `ths_return_1d_fund` | 日收益率（%） |
| 周收益率 | `ths_return_1w_fund` | 周收益率（%） |
| 月收益率 | `ths_return_1m_fund` | 月收益率（%） |
| 年收益率 | `ths_return_1y_fund` | 年收益率（%） |
| 今年以来 | `ths_return_ytd_fund` | 今年以来收益率 |
| 基金规模 | `ths_total_asset_fund` | 基金规模（元） |
| 波动率 | `ths_volatility_fund` | 年化波动率（%） |
| 最大回撤 | `ths_max_drawdown_fund` | 最大回撤（%） |
| 夏普比率 | `ths_sharpe_fund` | 夏普比率 |

## 指数指标

| 简称 | 指标代码 | 说明 |
|------|----------|------|
| 收盘价 | `ths_close_index` | 收盘点位 |
| 开盘价 | `ths_open_index` | 开盘点位 |
| 最高价 | `ths_high_index` | 最高点位 |
| 最低价 | `ths_low_index` | 最低点位 |
| 成交量 | `ths_vol_index` | 成交量 |
| 成交额 | `ths_amt_index` | 成交额 |
| 涨跌幅 | `ths_chg_ratio_index` | 涨跌幅（%） |
| 市盈率 | `ths_pe_index` | 指数PE |
| 市净率 | `ths_pb_index` | 指数PB |

## 实时行情指标

用于 `get_realtime_quotes()` 方法：

| 指标 | 说明 |
|------|------|
| `latest` | 最新价 |
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `preClose` | 前收盘价 |
| `volume` | 成交量 |
| `amount` | 成交额 |
| `change` | 涨跌额 |
| `changeRatio` | 涨跌幅 |
| `turnoverRatio` | 换手率 |
| `pe` | 市盈率 |
| `pb` | 市净率 |
| `totalValue` | 总市值 |
| `flowValue` | 流通市值 |
| `bid1` - `bid5` | 买一至买五价 |
| `bidVol1` - `bidVol5` | 买一至买五量 |
| `ask1` - `ask5` | 卖一至卖五价 |
| `askVol1` - `askVol5` | 卖一至卖五量 |

## 参数格式说明

### 复权参数

用于行情数据的第三个参数：

- `100` - 不复权
- `101` - 前复权
- `102` - 后复权

示例：`'2024-01-15,100'` 表示 2024-01-15 的不复权收盘价

### 日期格式

- 基础数据：`YYYY-MM-DD` 或 `YYYYMMDD`
- 高频数据：`YYYY-MM-DD HH:MM:SS`
