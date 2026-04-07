# whale-position-contrarian-signal

交易所巨鲸仓位反向信号 -- 用交易所仓位极端变化检测反向操作机会

## 这个工具做什么？

你可能听过"跟着巨鲸买"的说法，但数据告诉我们一个反直觉的结论：**当巨鲸仓位出现极端变化时，反着操作反而更赚钱。**

这个工具帮你做三件事：

1. **监控仓位变化** -- 自动拉取交易所的 OI（未平仓合约量，即市场上所有未结算的合约总额）或多空比数据，计算 30 天内的变化幅度
2. **检测极端信号** -- 当仓位 30 天涨幅超过 15% 或跌幅超过 10% 时，触发信号告警
3. **回测验证** -- 统计历史上同类极端事件后的价格表现，给你一个"这个信号历史上靠不靠谱"的胜率数字

核心逻辑来自 @leifuchen 对 Bitfinex 保证金多头仓位的 1838 天量化回测：巨鲸大幅加仓（涨>15%）后 30 天做空胜率 69%，巨鲸大幅减仓（跌>10%）后 14 天做多胜率 62%。

## 怎么用？

**基础用法：**
```
/whale-position-contrarian-signal BTC
```

**带参数：**
```
/whale-position-contrarian-signal BTC --exchange binance --position_type long_short_ratio --lookback_days 365
```

**参数说明：**

| 参数 | 含义 | 默认值 |
|------|------|--------|
| symbol | 代币名称，如 BTC、ETH | 必填 |
| exchange | 交易所 | binance |
| position_type | 仓位数据类型：futures_oi 或 long_short_ratio | futures_oi |
| lookback_days | 回看多少天的历史数据 | 180 |
| rolling_window | 计算变化率的窗口天数 | 30 |
| increase_threshold | 仓位大涨阈值（%） | 15.0 |
| decrease_threshold | 仓位大跌阈值（%） | 10.0 |

## 会输出什么？

下面是一个模拟输出示例：

```
=== 交易所巨鲸仓位反向信号分析 ===
代币: BTC | 数据源: Binance futures_oi | 分析日期: 2026-04-07

-- 当前信号 --
  30天仓位变化率: +18.7%
  信号状态: WHALE_ACCUMULATION（巨鲸大幅加仓）
  建议方向: SHORT（考虑做空）
  信号强度: HIGH

-- 历史回测 --
  | 信号类型 | 窗口 | 次数 | 胜率 | 平均收益 |
  |---------|------|------|------|---------|
  | ACCUMULATION->做空 | 30天 | 23 | 69% | -4.2% |
  | DISTRIBUTION->做多 | 14天 | 18 | 62% | +3.1% |

-- 辅助验证 --
  资金费率: +0.012%（偏多，支持反向做空逻辑）
  近24h爆仓: 多头爆仓 $4.2M > 空头 $1.8M
  交易所储备变化: +1,200 BTC（7日净流入）

-- 风险提示 --
  本信号为统计概率判断，非确定性预测。
  建议结合其他指标综合判断，不构成投资建议。
  方法论来源: @leifuchen
```

## 什么时候用？什么时候不适合？

**适合的场景：**
- 每日/每周定期巡检，看看有没有极端仓位信号出现
- BTC/ETH 等主流币的合约仓位异常时，快速判断是否存在反向操作机会
- 量化研究中需要验证"巨鲸信号"是否真的有效
- 想要一个基于数据的"贪婪/恐惧"指标来辅助决策

**不适合的场景：**
- 想找精确的入场价位、止损位 -- 这个工具只判断方向，不给具体价格
- 小币种分析 -- OI 和多空比数据主要覆盖主流币种，小币种数据稀疏
- 短线炒单（分钟/小时级） -- 信号基于 30 天窗口，适合日线以上的中长周期
- 希望自动下单 -- 工具只给信号，不执行交易

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的链上/市场数据才能工作。MCP（Model Context Protocol）服务器是数据来源 -- 把它理解成"给 Claude 接上数据管道"。不装的话，Claude 拿不到数据，分析就跑不起来。

### MCP 服务安装

#### ant-on-chain-mcp

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user ant-on-chain-mcp https://ant-on-chain-mcp.antseer.ai/mcp
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`ant-on-chain-mcp`
- URL：`https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "ant-on-chain-mcp": {
      "type": "http",
      "url": "https://ant-on-chain-mcp.antseer.ai/mcp"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://ant-on-chain-mcp.antseer.ai/mcp`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

## 免责声明

- 本工具基于历史数据进行统计分析，历史表现不代表未来收益，不能预测未来价格走势
- 分析方法论归属原作者 @leifuchen，本工具为自动化实现，非原创研究
- 所有输出仅供参考，不构成任何投资建议。交易决策应由用户自行判断并承担风险
- 默认使用 OI/多空比作为替代指标，与原始 Bitfinex Margin Longs 数据的行为特征可能存在差异
