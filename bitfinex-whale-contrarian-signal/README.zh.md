<div align="center">

# Bitfinex 巨鲸仓位反指信号

Bitfinex 巨鲸仓位反指信号 -- 用保证金多头仓位极端变动检测 BTC 反向交易机会

[![X](https://img.shields.io/badge/关注-%40Antseer__ai-black?logo=x&logoColor=white)](https://x.com/Antseer_ai) [![Telegram](https://img.shields.io/badge/Telegram-AntseerGroup-2CA5E0?logo=telegram&logoColor=white)](https://t.me/AntseerGroup) [![GitHub](https://img.shields.io/badge/GitHub-antseer--dev-181717?logo=github&logoColor=white)](https://github.com/antseer-dev/OpenWeb3Data_MCP) [![Medium](https://img.shields.io/badge/Medium-antseer-000000?logo=medium&logoColor=white)](https://medium.com/@antseer/)

[English](README.md) | 简体中文

</div>

## 这个工具做什么？

你可能听过一句话："当所有人都在抄底的时候，底还没到。" 这个工具就是帮你量化验证这句话的。

它监控的是 Bitfinex 交易所的保证金多头仓位（margin long position，简单说就是在 Bitfinex 上借钱买 BTC 的总量）。当这些"巨鲸"（大户）疯狂加仓抄底时，BTC 反而大概率要跌；当他们集体止盈减仓时，BTC 反而大概率要涨。

工作流程：

1. **拉数据** -- 从 Bitfinex 公开 API 获取保证金多头仓位的历史数据（免费、不需要 API Key）
2. **算变化率** -- 计算最近 30 天仓位变化了多少百分比
3. **识别极端信号** -- 涨幅超过 15%（巨鲸疯狂抄底）标记为做空信号；跌幅超过 10%（巨鲸集体止盈）标记为做多信号
4. **回测验证** -- 统计历史上每次信号触发后 BTC 在 7 天、14 天、30 天内的实际涨跌和胜率
5. **输出报告** -- 告诉你当前有没有信号、历史胜率多少、建议怎么操作

这套方法论来自 [@leifuchen](https://x.com/leifuchen/status/2041145516637966508)，他用 1838 天的数据（2021 年 3 月至 2026 年 4 月）做了系统性量化验证。核心发现：仓位暴涨超 15% 后，BTC 30 天内平均跌 5.4%，做空胜率 69%；仓位暴跌超 10% 后，BTC 14 天内平均涨 4.1%，做多胜率 62%。

## 怎么用？

```
/bitfinex-whale-contrarian-signal
```

或者带参数：

```
/bitfinex-whale-contrarian-signal BTC --lookback_days=30 --threshold_long=15 --threshold_short=10
```

**参数说明：**

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| symbol | 否 | 目标币种（目前仅支持 BTC） | BTC |
| lookback_days | 否 | 计算仓位变化率的天数 | 30 |
| threshold_long | 否 | 仓位涨多少算"极端"(%)，触发做空信号 | 15 |
| threshold_short | 否 | 仓位跌多少算"极端"(%)，触发做多信号 | 10 |
| forward_window | 否 | 信号触发后观察多久 | 7d,14d,30d |
| data_start_date | 否 | 分析数据起始日期 | 自动取最早可用 |

## 会输出什么？

一份结构化分析报告。下面是一个基于原文研究数据的模拟输出：

```
===== Bitfinex 巨鲸仓位反指信号 =====
分析时间: 2026-04-04
数据范围: 2021-03-24 ~ 2026-04-04（1838 天）

[当前状态]
  30 日仓位变化率: +18.3%
  信号状态: 触发 -- 抄底反指（做空信号）
  信号强度: Strong（超过阈值 3.3 个百分点）

[历史统计（仓位涨幅 >15% 后的 BTC 表现）]
  | 窗口 | 平均收益 | 胜率（做空） | 样本数 |
  |------|----------|-------------|--------|
  | 7 天 | -2.1%    | 58%         | 23     |
  | 14 天| -3.8%    | 65%         | 23     |
  | 30 天| -5.4%    | 69%         | 23     |

  样本外验证（2024-2026）:
  | 窗口 | 平均收益 | 胜率（做空） | 样本数 |
  |------|----------|-------------|--------|
  | 30 天| -3.8%    | 69%         | 11     |

[建议]
  巨鲸正在大幅加仓抄底，历史数据表明此时 BTC 后续偏空。
  考虑做空或减仓，30 天内做空历史胜率 69%。

[注意]
  - 该信号平均每年独立触发不到 5 次，适合作为辅助确认
  - 极端信号样本量有限（5 年共 23 次），统计置信度有限
  - 不构成投资建议，需结合其他指标综合判断
```

## 什么时候用？什么时候不适合？

**适合：**

- 你做 BTC 合约或现货交易，想在开仓前多一个确认信号
- 你想知道 Bitfinex 大户最近是在疯狂加仓还是在清仓跑路
- 你每天或每周做一次 BTC 市场结构巡检，想把巨鲸仓位变化作为其中一个观察维度
- 你是量化研究员，想验证 Bitfinex margin 数据的反向指标有效性

**不适合：**

- 你需要实时的、分钟级的交易信号 -- 这个工具分析的是 30 天滚动变化，不是日内短线指标
- 你做山寨币交易 -- 原始研究只覆盖 BTC，没有验证其他币种的有效性
- 你想拿它当主策略 -- 信号每年平均触发不到 5 次，只能当辅助确认用
- 你需要精确的入场和出场价位 -- 这个工具给的是方向性概率，不是具体点位

## 安装

### 1. 安装 Skill

把 `bitfinex-whale-contrarian-signal` 目录复制到你的 Claude Code skills 目录：

```bash
# macOS / Linux
cp -r bitfinex-whale-contrarian-signal ~/.claude/skills/

# 验证安装
ls ~/.claude/skills/bitfinex-whale-contrarian-signal/SKILL.md
```

### 2. MCP 依赖

这个 Skill 使用 Antseer MCP 获取 BTC 价格数据和辅助市场结构数据。在你的 Claude Code 配置中添加 MCP 服务器：

**Claude Desktop（`claude_desktop_config.json`）：**

```json
{
  "mcpServers": {
    "antseer-mcp": {
      "command": "npx",
      "args": ["-y", "@anthropic/antseer-mcp"],
      "env": {
        "ANTSEER_API_KEY": "your-api-key"
      }
    }
  }
}
```

**Claude Code（`.claude/settings.json`）：**

```json
{
  "mcpServers": {
    "antseer-mcp": {
      "command": "npx",
      "args": ["-y", "@anthropic/antseer-mcp"],
      "env": {
        "ANTSEER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 3. 外部数据源

核心数据（Bitfinex 保证金多头仓位）来自 Bitfinex 的免费公开 API，不需要 API Key：

```
GET https://api-pub.bitfinex.com/v2/stats1/pos.size:1m:tBTCUSD:long/hist
```

Skill 会自动调用这个接口，不需要额外配置。

## 免责声明

本工具仅用于信息参考和研究目的，不构成投资建议。

- 分析方法论归属 [@leifuchen](https://x.com/leifuchen/status/2041145516637966508)，所有智力成果归原作者所有。
- 历史胜率和平均收益基于过去的数据（2021-2026），不保证未来表现。
- 信号每年触发不到 5 次，总样本量约 23 次，统计置信度有限。
- 市场结构可能随时间变化（如 BTC ETF 获批、机构参与度提升），这些可能影响信号有效性。
- 请始终结合其他指标和自己的判断。永远不要投入超过你能承受损失的资金。

---

<div align="center">

Built by [AntSeer](https://antseer.ai) · Powered by AI Agents

</div>
