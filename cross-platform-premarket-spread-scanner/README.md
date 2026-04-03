# cross-platform-premarket-spread-scanner

跨平台盘前价差套利扫描 — 用多平台盘前报价数据，找出同一代币在 ASP、Binance、Polymarket 之间的价差套利机会

---

## 这个工具做什么？

你在某个代币 TGE（首次上所）的前几天，发现它同时在多个平台报价，但各平台价格差距很大。这个工具帮你：

1. **自动抓取多平台价格** — 从 ASP（Aspecta AI 盘前市场）、Binance 盘前、Polymarket 预测市场拿到当前报价
2. **计算实际可套利价差** — 名义价差减去双腿手续费和滑点，告诉你到底还剩多少利润空间
3. **评估做空风险** — 分析社区 FOMO 程度（市场情绪过热时做空容易被轧），给出是否适合执行的建议
4. **计算空投对冲仓位** — 如果你手里有待发空投（隐式多头），告诉你开多少空单才能对冲得当，不超对冲也不欠对冲
5. **给出套利评级** — 综合以上输出 A/B/C/D 评级，以及具体执行计划（在哪个平台开空、在哪个平台开多、建议仓位、止损价位）

---

## 怎么用？

### 基础用法

```
/cross-platform-premarket-spread-scanner EDGEX
```

### 完整参数

```
/cross-platform-premarket-spread-scanner EDGEX \
  --platforms ASP,Binance,Polymarket \
  --min_spread_pct 15 \
  --reference_token OPN \
  --airdrop_amount_est 200000 \
  --time_range 24h \
  --fdv_breakeven 350000000
```

### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| symbol | 是 | 目标代币符号 | — |
| platforms | 否 | 要扫描的盘前平台列表，逗号分隔 | ASP,Binance,Polymarket |
| min_spread_pct | 否 | 触发报警的最小价差百分比（相对低价平台） | 15 |
| reference_token | 否 | 历史类比参考代币，用于走势对比（如 OPN） | — |
| airdrop_amount_est | 否 | 你预估持有的空投代币数量，用于计算对冲仓位 | 0（跳过仓位计算） |
| time_range | 否 | 监控时间窗口 | 24h |
| fdv_breakeven | 否 | 盈亏平衡 FDV 估算（美元），用于评估价格合理性 | — |

---

## 会输出什么？

下面是一个基于 $EDGEX 真实案例的模拟输出：

```
=== 跨平台盘前价差套利扫描报告 ===
代币: $EDGEX | 扫描时间: 2026-03-20 09:30 UTC

【触发信号】
  TGE 日期: 2026-03-25
  时效窗口: 是（5 天内）

【价格矩阵】
  ASP (Aspecta AI):       $0.78
  Binance Pre-market:     $0.45
  Polymarket (隐含):      $0.52

【最优价差对】
  做空: ASP @ $0.78
  做多: Binance Pre-market @ $0.45
  名义价差: $0.33（73.3%）
  预估双腿手续费+滑点: $0.03
  实际可套利价差: $0.30/枚 ✅

【FOMO 校验】
  情绪分: 68/100（Medium）
  FOMO 风险等级: Medium ⚠️
  建议止损（做空腿）: $1.01（当前价 +30%）

【解锁与仓位】
  TGE 交割日期: 2026-03-25
  空投预估量: 200,000 EDGEX
  空投隐式多头价值: ~$156,000（@ ASP 价）
  推荐对冲比例: 0.6（不建议全对冲，保留部分上行空间）
  最大安全仓位: $60,000 USDT 双腿各

【历史类比】
  参考代币 $OPN: 走势相似度 High
  当前 EDGEX 定价对应 OPN 盘前第 2 天低位

【综合评级】: B（条件执行）
  原因：FOMO 中等偏高，建议缩减至 60% 仓位 + 设置 ASP 空仓止损

【执行建议】
  做空腿: ASP 开空 EDGEX，60,000 USDT 等值
  做多腿: Binance Pre-market 做多 EDGEX，60,000 USDT 等值
  止损 (ASP 空仓): $1.01
  预期收益: $0.30/枚 × 建议仓位

【风险提示】
  1. ASP 流动性薄，大单执行滑点可能超出预期，建议分批入场（单笔 ≤5,000 USDT）
  2. Binance 盘前存在最大订单量限制，注意平台规则
  3. cc 风险（代币 listing 取消/推迟）可能打破盘前转现货预期，需人工评估
  4. 本报告仅供参考，不构成投资建议，套利交易存在市场风险
```

---

## 什么时候用？什么时候不适合？

### 适合使用的场景

- 代币 TGE 在未来 7 天内，同时出现在 ASP、Binance 盘前、Polymarket 等多个市场
- 你已经拥有或预期获得该代币的空投，想通过盘前做空来对冲价格下行风险
- 你是职业套利交易员，想在代币正式上线前锁定跨平台价差收益
- 空投查询界面刚上线，盘前价格出现剧烈分化

### 不适合使用的场景

- 代币已经完成 TGE 并在现货市场上线（盘前窗口关闭，本工具失效）
- 你完全没有做空意愿，只想了解代币基本面（请使用其他研究工具）
- 盘前市场只有一个平台在报价（没有价差就没有套利机会）
- 平台流动性极差（< 1,000 USDT 深度），滑点会吞掉全部利润

---

## 前置依赖

### 为什么需要装 MCP？

这个工具需要实时的代币情绪和解锁计划数据才能完整运行。MCP（Model Context Protocol，模型上下文协议）服务器是数据来源 — 把它理解成"给 Claude 接上数据管道"。

没有 MCP 时，工具仍可运行，但会跳过以下步骤：
- TGE 时间节点确认（Step 1）
- 代币情绪 FOMO 校验（Step 4）
- 空投解锁批次详情（Step 6）

盘前价格数据（ASP/Binance/Polymarket）通过 WebFetch 直接获取，无需 MCP。

### Antseer MCP 服务安装

**Claude Code (CLI)**
```bash
claude mcp add --transport http --scope user antseer https://mcp.antseer.io/mcp
```

**OpenClaw / Claw**

在设置页面添加 MCP 服务器，填写：
- 名称：`antseer`
- URL：`https://mcp.antseer.io/mcp`
- 传输类型：`http`

**OpenCode**

在配置文件 `opencode.json` 中添加：
```json
{
  "mcpServers": {
    "antseer": {
      "type": "http",
      "url": "https://mcp.antseer.io/mcp"
    }
  }
}
```

**通用 MCP 客户端**

任何支持 MCP 协议的客户端均可接入，核心参数：
- MCP 端点：`https://mcp.antseer.io/mcp`
- 传输类型（Transport）：`http`
- 作用域（Scope）：`user`（推荐，跨项目共享）

安装完成后，**重启你的 Agent 客户端**以激活 MCP 服务。

---

## 免责声明

- 本 Skill 分析方法论归属原作者 @BTC_Alert_，基于其公开推文内容（2026-03-20 分析 $EDGEX 盘前套利）自动提炼生成。
- 所有分析基于历史数据和当前快照，不能预测未来价格走势。
- 盘前套利存在流动性风险、平台风险（cc 风险）、极端情绪风险，过去的套利成功案例不代表未来一定可复制。
- 本 Skill 不执行任何交易，所有建议仅供参考，不构成投资建议。最终决策由用户自行承担。
