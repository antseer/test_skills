<div align="center">

# 比特币泡沫指数底部探测器

BTC 底部探测器 — 用链上 MVRV+NVT 数据识别比特币是否进入历史底部区域

[![X](https://img.shields.io/badge/关注-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

</div>

---

## 这个工具做什么？

你在 BTC 大幅下跌之后想知道"现在到底了吗？值不值得抄底？"——这个工具帮你用链上数据给出一个结构化的答案。

它的核心逻辑来自 @monkeyjiang 的观察：一个叫"比特币泡沫指数"的指标，每次跌到 10 附近，BTC 就进入底部区域，2022 年至今从未失效。这个工具用 **MVRV**（市值/已实现价值，反映整体盈亏状态）和 **NVT**（网络价值/链上交易量，反映估值相对活跃度）两个链上指标来近似还原这个信号。

三步工作流：
1. 从 Antseer MCP 拉取 BTC 价格、MVRV 和 NVT 历史数据
2. 对两个指标分别做区间归一化（0-100），加权合并成"泡沫代理指数"
3. 与底部阈值对比，扫描历史信号次数和涨幅统计，输出底部探测报告

数据来源：Antseer MCP（`ant_spot_market_structure`、`ant_token_analytics`）

---

## 怎么用？

```
/btc-bubble-index-bottom-detector [symbol] [--bottom_threshold=N] [--lookback_days=N] [--price_target=N] [--include_chart_context=true]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| symbol | 是 | BTC | 分析的资产（当前版本仅支持 BTC） |
| bottom_threshold | 否 | 12 | 底部区域上限阈值（0-100 指数） |
| lookback_days | 否 | 1460 | 历史回溯天数（用于归一化，默认 4 年） |
| price_target | 否 | 不填 | 设定目标价（USD），用于计算风险收益比 |
| include_chart_context | 否 | true | 是否输出指数趋势文字描述 |

**调用示例：**

```
/btc-bubble-index-bottom-detector BTC
/btc-bubble-index-bottom-detector BTC --bottom_threshold=10
/btc-bubble-index-bottom-detector BTC --price_target=200000
```

---

## 会输出什么？

```
=== 比特币泡沫代理指数 — 底部探测报告 ===

资产: BTC  |  分析日期: 2026-04-08
当前价格: $62,000
泡沫代理指数: 9.8 / 100  （底部阈值: 12）

信号: 强底部信号
信号强度: 82/100
指数趋势: confirmed（已在底部区域，近30天小幅回升）

--- 历史验证（4年回测）---
历史触发次数: 3 次
信号后 90 天平均涨幅: +47.3%
信号后 365 天平均涨幅: +198.6%
历史信号后最大回撤（中位数）: 18.2%

--- 各指标评分 ---
MVRV（权重 60%）: 8/100   [当前 MVRV: 0.91]
NVT （权重 40%）: 12/100  [当前 NVT:  28.4]

--- 风险收益比分析（目标价: $200,000）---
潜在涨幅: +222.6%
风险收益比: 12.2:1
历史平均最大回撤: 18.2%

注: 本指数为 MVRV+NVT 代理值，非 monkeyjiang 原版泡沫指数。
方法论归属 @monkeyjiang。仅供参考，不构成投资建议。
```

---

## 什么时候用？什么时候不适合？

**适合用：**
- BTC 价格大跌 20% 以上，想用链上数据确认是否形成底部
- 定期巡检 BTC 是否进入积累区间
- 中长线建仓前需要一个链上估值确认信号
- 设定了目标价（如 20 万美元）想看风险收益比是否合理

**不适合用：**
- 短线交易（日内或几天）——MVRV 和 NVT 是周/月级别的周期指标，不反映短期波动
- 山寨币分析——非 BTC 资产的 MVRV/NVT 数据质量较差
- 预测精确底部价格——本工具只能判断"区域"，不能给出精确价位
- 实时告警（毫秒级）——链上数据通常有 T+1 延迟

---

## 安装

### 安装 Skill

将此 Skill 目录复制到你的 Claude Code skills 文件夹：

```bash
cp -r btc-bubble-index-bottom-detector ~/.claude/skills/
```

### 安装 AntSeer MCP（必须）

本 Skill 依赖 Antseer OpenWeb3Data MCP 服务获取链上数据。

**Claude 桌面客户端（`claude_desktop_config.json`）：**

```json
{
  "mcpServers": {
    "antseer": {
      "command": "npx",
      "args": ["-y", "@antseer/openweb3data-mcp"]
    }
  }
}
```

**Claude Code（`settings.json`）：**

```json
{
  "mcpServers": {
    "antseer": {
      "command": "npx",
      "args": ["-y", "@antseer/openweb3data-mcp"]
    }
  }
}
```

其他支持 MCP 的客户端，请参考 [AntSeer MCP GitHub](https://github.com/antseer-dev/OpenWeb3Data_MCP) 的各平台安装说明。

---

## 免责声明

本工具仅供参考，不构成任何投资建议。分析基于 MVRV 和 NVT 链上指标作为代理，与 @monkeyjiang 原版"比特币泡沫指数"存在偏差。历史信号样本量仅 3-4 次（2021 年至今），统计显著性有限。历史表现不代表未来结果。分析框架与方法论归属 @monkeyjiang，AntSeer 不主张对原始概念的所有权。投资有风险，入市需谨慎，请在做出投资决策前进行充分的独立研究。

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
