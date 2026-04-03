# prediction-market-ev-trading

预测市场 +EV 量化交易分析 -- 用多数据源交叉验证发现预测市场的正期望值交易机会

## 这个工具做什么？

你在 Polymarket 这类预测市场上看到一堆合约（比如"明天纽约最高温超过 75 华氏度"），每个合约都有一个市场价格代表大家认为的概率。但市场价格不一定准。

这个工具帮你做三件事：

1. **多源交叉验证** -- 同时查多个独立数据源（比如三个不同的气象模型），算出你自己的概率估计，比只看一个来源靠谱得多
2. **找正期望值机会** -- 把你的概率和市场价格对比，算出哪些合约"定价偏了"，也就是 +EV（正期望值）交易机会
3. **科学算仓位** -- 用 Kelly 公式（一种数学上最优的下注比例公式）告诉你每笔该投多少，不会一把梭也不会太保守

另外还有一个自校准机制：每积累 30 次预测结果后，自动回头看看模型准不准，哪个数据源靠谱就给它更高权重。策略会越用越准。

方法论来源：@NFTCPS，原始策略在 Polymarket 天气市场上实现了持续盈利。本 Skill 将其通用化，理论上适用于天气、体育、政治、经济、crypto 等各类预测市场。

## 怎么用？

基本调用格式：

```
/prediction-market-ev-trading {market_category} --data_sources={source1},{source2}
```

### 参数说明

| 参数 | 含义 | 必填 | 默认值 |
|------|------|------|--------|
| market_category | 品类：weather / sports / politics / economics / crypto | 是 | - |
| market_id | 具体市场链接或 ID | 否 | 扫描全部活跃市场 |
| data_sources | 数据源列表，至少 2 个 | 是 | - |
| target_cities | 目标城市/事件 | 否 | 全部可用 |
| kelly_fraction | Kelly 缩放系数（0.5=半Kelly，更保守） | 否 | 0.5 |
| ev_threshold | EV 下限，低于此不交易 | 否 | 0.05 (5%) |
| calibration_window | 多少次预测后触发自校准 | 否 | 30 |
| max_position_size | 单笔最大占比 | 否 | 0.1 (10%) |
| backtest_mode | 用模拟资金回测 | 否 | true |
| time_range | 分析时间范围 | 否 | 7d |

### 调用示例

天气市场分析（最典型用法）：
```
/prediction-market-ev-trading weather --data_sources=ECMWF,HRRR,METAR --target_cities=NYC,London,Tokyo
```

Crypto 预测市场：
```
/prediction-market-ev-trading crypto --data_sources=spot_price,technical_indicators,sentiment --market_id=BTC_100k_March
```

回测模式：
```
/prediction-market-ev-trading weather --backtest_mode=true --time_range=30d
```

## 会输出什么？

完整的模拟输出示例：

```
=== 预测市场 +EV 交易机会扫描报告 ===
品类: 天气市场 | 平台: Polymarket | 扫描时间: 2026-04-03

策略概况:
- 覆盖城市: 20 个（4 大洲）
- 数据源: ECMWF, HRRR, METAR（三源交叉验证）
- 校准状态: 15/20 城市已完成首轮校准（>= 30 次预测）

当日最佳交易机会:
| 市场              | 市场价格 | 模型概率 | EV    | 置信度 | Kelly 仓位 | 建议金额 |
|-------------------|----------|----------|-------|--------|------------|----------|
| NYC 高温>75 F     | 0.42     | 0.58     | +0.38 | High   | 4.2%       | $420     |
| London 降水>5mm   | 0.65     | 0.78     | +0.20 | Medium | 2.1%       | $210     |
| Tokyo 风速>30km/h | 0.30     | 0.39     | +0.30 | Medium | 1.8%       | $180     |
| Sydney 最低温<10C | 0.55     | 0.41     | -0.25 | High   | 跳过       | -        |
| Berlin 晴天       | 0.48     | 0.52     | +0.08 | Low    | 0.9%       | $90      |

说明: Sydney 市场模型概率低于市场价格，EV 为负，不建议买入 YES 方向。
Berlin 市场虽有正 EV 但置信度低（数据源分歧大），建议小仓位或观望。

校准统计（最近 30 次预测）:
- NYC: 准确率 72%, Brier Score 0.18 -- 校准良好
- London: 准确率 65%, Brier Score 0.22 -- 可接受，持续监控
- Tokyo: 准确率 68%, Brier Score 0.20 -- 校准良好

数据源权重（经校准调整）:
- ECMWF: 40% (短期预测优势)
- HRRR: 35% (美国城市高分辨率)
- METAR: 25% (实测数据有滞后)

策略健康度: 良好
- 整体 ROI: +12.3%（模拟资金 $1000 -> $1123）
- 平均 Brier Score: 0.20
- 建议: 策略有效，继续运行。London 市场需关注校准趋势。
```

## 什么时候用？什么时候不适合？

### 适合的场景

- 你在 Polymarket 上看到一个合约，想知道市场定价是否合理
- 你有多个数据源（比如多个气象模型），想系统性地交叉验证
- 你想从"拍脑袋下注"转向数据驱动的量化下注
- 你想评估自己过去的预测准不准（Brier Score 校准）
- 你想了解 Kelly 公式在预测市场中的实际应用

### 不适合的场景

- 想自动执行交易（本工具只出建议，不连接交易接口）
- 分析流动性极低的长尾市场（定价噪音太大，模型无效）
- 不愿意自己找数据源（核心数据源需要用户提供或配置外部 API）
- 追求短期暴利（+EV 策略需要足够样本量才能体现统计优势）
- 评估 Polymarket 平台本身的风险（智能合约风险、监管风险等不在分析范围内）

## 前置依赖

### 为什么需要装 MCP？

当你分析 crypto 品类的预测市场（比如"BTC 月底是否突破 $100k"）时，这个工具需要实时的链上/市场数据来构建概率模型。MCP（Model Context Protocol）服务器是数据来源 -- 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到 crypto 数据，只能用你手动提供的数据做分析。

对于天气、体育等非 crypto 品类，MCP 不是必须的，但仍需要你提供外部数据源的数据（如气象 API 返回结果）。

### MCP 服务安装

#### Antseer MCP（crypto 数据）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer https://mcp.antseer.com/http
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer`
- URL：`https://mcp.antseer.com/http`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer": {
      "type": "http",
      "url": "https://mcp.antseer.com/http"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://mcp.antseer.com/http`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

### 外部数据源（非 MCP）

本 Skill 的核心数据需求需要外部 API，以下是主要数据源:

| 数据源 | 用途 | API 获取方式 |
|--------|------|-------------|
| Polymarket CLOB API | 市场合约、赔率、流动性 | `https://clob.polymarket.com`（免费） |
| ECMWF | 欧洲中期天气预报 | `https://api.ecmwf.int`（需注册） |
| NOAA HRRR | 美国高分辨率天气模型 | NOAA 公开数据（免费） |
| METAR | 机场实测气象数据 | aviationweather.gov（免费） |

用户可以手动将外部 API 返回的数据粘贴给 Claude 进行分析，或者自行配置对应的 MCP 服务器。

## 免责声明

- 本工具基于历史数据和统计模型进行分析，**不能预测未来**。正期望值策略在统计上有优势，但短期内仍可能亏损。
- 分析方法论归属原作者 **@NFTCPS**，本工具是对其公开分享策略的结构化实现。
- 本工具的输出**不构成投资建议**。预测市场交易存在本金损失风险，请根据自身风险承受能力做出决策。
- Polymarket 在部分司法管辖区可能存在合规限制，使用前请自行评估法律风险。
- 模型质量完全依赖外部数据源的准确性和可用性，数据源故障或延迟可能影响分析结果。
