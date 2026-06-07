# DataPilot Agent 数据分析初步报告

> 本报告由规则驱动的 DataPilot Agent Workflow 基于 `data/sample_orders.csv` 自动生成，结论需结合业务口径复核。

## 1. 数据概览

- 数据行数：30
- 数据列数：9
- 重复行数：1

数据包含订单、用户、下单时间、商品品类、数量、价格、支付状态、城市和配送时长字段。

## 2. 字段信息

| 字段 | 类型 | 缺失数 | 缺失率 |
|---|---|---:|---:|
| order_id | object | 0 | 0.00% |
| user_id | object | 0 | 0.00% |
| order_time | object | 0 | 0.00% |
| product_category | object | 0 | 0.00% |
| quantity | float64 | 1 | 3.33% |
| price | float64 | 1 | 3.33% |
| payment_status | object | 1 | 3.33% |
| city | object | 1 | 3.33% |
| delivery_minutes | float64 | 1 | 3.33% |

## 3. 数据质量检查

- 检测到 1 行完全重复记录；
- `quantity`、`price`、`payment_status`、`city` 和 `delivery_minutes` 存在少量缺失；
- `quantity`、`price` 和 `delivery_minutes` 存在 IQR 潜在异常值；
- `order_time` 当前为文本类型，建议转换为 datetime；
- 支付状态和城市等类别字段需要检查取值一致性。

潜在异常值是统计规则识别出的候选值，不代表一定是错误数据。例如高价商品和较长配送时间可能是真实业务事件。

## 4. 业务场景推断

- 推断场景：**订单/交易数据**
- 判断依据：字段中包含 `order`、`user`、`price`、`payment`、`product` 等交易关键词。

可进一步关注的业务问题：

- 用户消费金额分布如何？
- 哪些商品或客户贡献更高？
- 订单支付成功情况如何？

## 5. 清洗建议

1. 将 `order_time` 转换为 datetime，并记录解析失败的值。
2. 结合订单主键检查重复记录，确认后再去重。
3. 对少量缺失值按字段含义分别处理，不对 ID 字段做均值填补。
4. 统一支付状态、城市和商品品类的空格、大小写及同义值。
5. 对数量、价格和配送时长异常值进行业务复核，可先标记而不是直接删除。
6. 保留原始数据和清洗日志，便于追踪处理前后的数据变化。

## 6. 后续分析建议

1. 按日或按周分析订单量、成交金额和客单价趋势。
2. 按用户累计消费金额进行分层，识别高价值用户。
3. 按商品品类统计销量与销售额排行。
4. 分析不同支付状态的占比和支付成功率。
5. 按城市对比订单规模和平均配送时长。
6. 分析配送时长的 P50、P90 及超时订单。

## 7. SQL 分析模板

### 查看总行数

```sql
SELECT COUNT(*) AS total_rows
FROM your_table;
```

### 按日期聚合

```sql
SELECT DATE(`order_time`) AS stat_date,
       COUNT(*) AS record_count
FROM your_table
GROUP BY DATE(`order_time`)
ORDER BY stat_date;
```

### 按商品品类统计

```sql
SELECT `product_category`,
       COUNT(*) AS order_count,
       SUM(`quantity`) AS total_quantity,
       SUM(`price`) AS total_price
FROM your_table
GROUP BY `product_category`
ORDER BY total_price DESC;
```

### 用户维度统计

```sql
SELECT `user_id`,
       COUNT(*) AS order_count,
       SUM(`price`) AS total_price
FROM your_table
GROUP BY `user_id`
ORDER BY total_price DESC;
```

## 8. 总结

当前数据被初步识别为订单/交易数据。建议先处理时间类型、少量缺失值和重复记录，并对高价、批量购买和超长配送样本进行业务复核，再开展订单趋势、用户分层、品类贡献和履约效率分析。
