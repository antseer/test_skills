# 六因子过滤框架参考文档

本文档解释 polymarket-quant-signal 六因子框架的数学原理和实现细节，供 Claude 在执行分析时按需参考。

---

## 因子 1：KL散度跨周期背离检测

**原理**：Kullback-Leibler 散度衡量两个概率分布之间的差异。当BTC的短周期（5min）价格变动分布与长周期（15min）价格变动分布显著脱钩时，说明短期市场存在局部过度运动，均值回归概率升高。

**公式**：
```
KL(P‖Q) = Σ P(x) · log(P(x)/Q(x))
```
其中 P = 短周期价格变动分布，Q = 长周期价格变动分布。

**实现注意事项**：
- 使用平滑项 ε=1e-10 防止零概率导致的对数无穷大
- 价格变动序列先离散化为直方图（20 bins），再转换为概率分布
- 阈值0.10是保守设置，高波动市场可上调至0.15-0.20

**方向判断逻辑**：
- 短周期均值收益率 > 长周期均值收益率 → 短期相对超涨 → BEARISH_REVERT（预计向下回归）
- 短周期均值收益率 < 长周期均值收益率 → 短期相对超跌 → BULLISH_REVERT（预计向上回归）

---

## 因子 2：资金费率Z-score（LMSR代理指标）

**原理**：永续合约资金费率（Funding Rate）反映市场多空情绪的偏斜程度。LMSR（Logarithmic Market Scoring Rule）是预测市场的自动做市商定价机制，两者本质相似——都是衡量市场情绪将价格推离真实概率的程度。

**公式**：
```
Z-score = (当前资金费率 - 历史均值μ) / 历史标准差σ
```

**历史统计窗口**：建议使用过去30天（约90个8小时结算周期数据点）

**方向逻辑**：
- Z > +2.0：市场过度偏多 → 做空有正期望值（预期资金费率回归）
- Z < -2.0：市场过度偏空 → 做多有正期望值
- |Z| ≤ 2.0：市场处于均衡状态，无强烈EV方向

**局限性**：资金费率与Polymarket隐含概率之间存在结构性差异（CeFi衍生品市场 ≠ 预测市场），两者方向可能背离，本因子是代理指标而非精确映射。

---

## 因子 3：贝叶斯信号聚合

**原理**：贝叶斯更新将多个独立信号（KL方向、资金费率方向、Taker流向、市场情绪）融合为统一的方向概率估计。

**公式**：
```
P(α|D) ∝ P(D|α) × P(α)

先验 P(α)：
  - KL和资金费率方向一致 → P_prior = 0.60
  - 方向相反 → P_prior = 0.50

似然信号：
  L1 = Taker净买入率 = (buy_vol - sell_vol) / total_vol ∈ [-1, 1]
  L2 = 成交量异常倍数 = 当前量 / 30日均量，截断至 [0.5, 3.0]
  L3 = 情绪归一化 = sentiment_score / 100 ∈ [0, 1]

likelihood_score = (1 + L1) × L2 × L3
P_posterior = normalize(likelihood_score × P_prior)
```

**触发条件**：P_posterior > 0.60，且与资金费率方向一致

---

## 因子 4：Polymarket EV缺口

**原理**：精确测量模型概率（p_bayes）与市场隐含概率（p_market = Polymarket YES代币价格）之间的差值。

**数据来源**：
```
GET https://gamma-api.polymarket.com/markets?slug={market_slug}
返回字段: outcomePrices[0] = YES代币当前价格（0-1范围）
```

**EV计算**：
```
EV缺口 = p_bayes - p_market
  > ev_min_edge（默认0.05）→ 模型认为YES被低估，买YES有正期望值
  < -ev_min_edge → 模型认为YES被高估，买NO有正期望值
```

**注意**：Polymarket价格数据有延迟，精确到秒级的套利需要更高频的数据访问。

---

## 因子 5：Kelly仓位计算

**原理**：Kelly准则最大化对数期望财富增长率，在给定概率优势时计算最优下注比例。

**公式（二元预测市场）**：
```
赔率 b = (1 - p_market) / p_market  （Polymarket标准赔率）
f* = (b × p_bayes - (1 - p_bayes)) / b
实际仓位 f_actual = f* × kelly_scale（默认0.25）
```

**为什么用四分之一Kelly**：全Kelly在实际应用中波动性过大，且对概率估计误差极度敏感。0.25 Kelly是保守实践，牺牲约6%的长期增长率换取显著降低的波动和破产概率。

**f* ≤ 0 时**：数学期望为负，不应下注，输出 NO_SIGNAL。

---

## 因子 6：Stoikov最优执行价格

**原理**：Stoikov做市商模型定义了做市商在持仓偏斜时愿意接受的最低/最高价格（保留价），避免在不利价格追高。

**简化公式**：
```
r = mid_price - q × γ × σ²

mid_price = 当前市场中间价
q = 目标仓位大小（f_actual）
γ = 风险厌恶系数（默认0.10）
σ = 布林带带宽/2（价格波动率代理，USDT）
```

**执行规则**：
- 做多方向：当前价格 ≤ r → price_in_range = true（等价格回落到保留价以下才买）
- 做空方向：当前价格 ≥ r → price_in_range = true（等价格反弹到保留价以上才卖）

---

## 综合信号逻辑

```
ALL_GREEN: 六因子全部通过
  → 可考虑执行，仓位 = f_actual × 账户净值

PARTIAL_5（EV因子BYPASSED）: 无market_slug时，5因子通过
  → 谨慎执行，需自行判断Polymarket对应市场的隐含概率

PARTIAL_N（N=3-4）: 部分因子通过
  → 观察等待，设置价格或数据提醒

NO_SIGNAL（N<3）: 少于3个因子通过
  → 当前无机会，不操作
```

---

## 数据源覆盖限制

| 因子 | MCP覆盖 | 备注 |
|------|---------|------|
| KL散度（Step 2） | 依赖Step 1数据 | 受BTC价格数据分辨率限制 |
| 资金费率Z-score（Step 3） | 完全覆盖 | ant_futures_market_structure |
| 贝叶斯聚合（Step 4） | 完全覆盖 | ant_market_indicators + ant_market_sentiment |
| EV缺口（Step 5） | 外部API | gamma-api.polymarket.com |
| Kelly（Step 6） | 纯计算 | 无MCP调用 |
| Stoikov（Step 7） | 依赖boll | ant_market_indicators |
