# oi-divergence-monitor

OI 背离信号监测 -- 用合约数据检测主力高位平多的做空信号

## 这个工具做什么？

你在盯盘时发现币价在涨，但不确定这轮上涨是真的有资金在推，还是只是虚涨——主力可能已经在悄悄撤了。这个工具帮你回答这个问题。

它的工作流程很简单：

1. **查价格**：先看目标代币（比如 BTC）最近涨了多少
2. **查 OI**：再看永续合约的未平仓量（Open Interest，就是市场上还没平掉的合约总量）是涨是跌
3. **交叉验证**：如果价格在涨、OI 在跌，说明多头在高位平仓跑路，上涨缺乏杠杆资金支撑。然后再用资金费率（做多的人付给做空的人的利息）、爆仓数据（谁被强制平仓了）、多空比这三个维度来确认信号是否可靠
4. **出报告**：给你一个信号强度评分（0-100）和操作建议

这套方法论来自 @EmberCN，是衍生品市场分析中经典的"价格-OI 背离"检测框架。

## 怎么用？

```
/oi-divergence-monitor BTC
```

**参数说明：**

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| symbol | 是 | 代币符号，如 BTC、ETH | — |
| time_range | 否 | 观察窗口 | 24h |
| oi_change_threshold | 否 | OI 下降多少算"显著"(%) | -3.0 |
| funding_rate_threshold | 否 | 资金费率低于多少算"偏低"(%) | 0.02 |
| liquidation_window | 否 | 爆仓数据看多久 | 4h |
| price_change_threshold | 否 | 价格涨多少算"显著"(%) | 1.0 |

**更多示例：**

```
/oi-divergence-monitor ETH
/oi-divergence-monitor BTC --oi_change_threshold=-5.0
```

## 会输出什么？

完整的结构化分析报告。下面是一个模拟输出（基于 @EmberCN 原始案例数据）：

```
# BTC OI 背离信号监测报告

## 信号概要
- 信号等级：strong
- 背离评分：82/100
- 分析时间：2026-03-28T12:00:00Z

## 价格与 OI 数据
| 指标 | 数值 | 判定 |
|------|------|------|
| 当前价格 | $97,500 | — |
| 价格涨幅 | +2.3% | 上涨 |
| 当前 OI | $18,200,000,000 | — |
| OI 变化 | -5.1% | 下降 |

## 验证维度
| 维度 | 数据 | 判定 |
|------|------|------|
| 资金费率 | 0.01% | 偏低(看空增强) |
| 多单爆仓 | $45,000,000 | 多头被清洗(看空增强) |
| 空单爆仓 | $12,000,000 | — |
| 多空比 | 0.95 | 下降趋势 |

## 建议
强背离信号: 现货价格创新高(+2.3%)但OI大幅下降(-5.1%)，
资金费率偏低(0.01%)，多单爆仓$45M远超空单$12M。
三重验证均通过，短期回调概率较高。建议减仓或建立对冲头寸。

## 免责声明
本分析基于 @EmberCN 的衍生品市场微观结构方法论，不构成投资建议。
信号基于历史统计规律，不能保证未来表现。
```

## 什么时候用？什么时候不适合？

**适合的场景：**
- 币价快速拉升后，想判断上涨是否有杠杆资金支撑
- 每 4-8 小时做一次市场健康度巡检
- 已有仓位，想评估是否需要减仓或加对冲
- 做量化策略回测前，想人工验证信号逻辑

**不适合的场景：**
- 想知道"BTC 明天能涨到多少" — 本工具不预测价格目标
- 需要自动下单执行交易 — 本工具只做信号检测，不连接交易所
- 分析山寨币 / 流动性极低的代币 — OI 数据可能不够准确
- 重大宏观事件期间（如 ETF 审批、监管政策发布） — 技术信号可能失效，需结合基本面判断

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上/市场数据才能工作。MCP（Model Context Protocol）服务器是数据来源 -- 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

### MCP 服务安装

本 Skill 依赖以下 Antseer MCP 服务：

#### antseer-spot（现货市场数据）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-spot https://mcp.antseer.com/spot
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer-spot`
- URL：`https://mcp.antseer.com/spot`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-spot": {
      "type": "http",
      "url": "https://mcp.antseer.com/spot"
    }
  }
}
```

#### antseer-futures（合约市场数据）

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer-futures https://mcp.antseer.com/futures
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer-futures`
- URL：`https://mcp.antseer.com/futures`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer-futures": {
      "type": "http",
      "url": "https://mcp.antseer.com/futures"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- 现货端点：`https://mcp.antseer.com/spot`
- 合约端点：`https://mcp.antseer.com/futures`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 免责声明

- 本 Skill 基于 @EmberCN 公开推文中的分析方法论构建，方法论归属原作者
- 分析结果基于历史数据和统计规律，不能预测未来市场走势
- 不构成任何投资建议，具体交易决策需结合个人风险偏好和基本面判断
- OI 等衍生品数据存在交易所上报延迟和统计口径差异，请勿将信号作为唯一决策依据
