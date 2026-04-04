# OI 背离自动狙击管线

自动化做空目标发现管线。从合约涨幅榜自动发现异常拉升币种，经过 OI 预筛、控盘检测、深度背离分析、综合评分，输出带优先级的做空推荐列表。

## 前置条件

需要安装 [Antseer MCP 服务器](https://smithery.ai/server/@anthropic/antseer)。

## 安装

```bash
cd skills/oi-divergence-pipeline
./setup.sh
```

setup.sh 会自动检测你的 Antseer MCP UUID 并配置 SKILL.md。

## 使用

```
/oi-divergence-pipeline          # 默认阈值（4H>8%, 24H>15%）
/oi-divergence-pipeline 10%      # 自定义 4H 阈值
/oi-divergence-pipeline low      # 熊市模式（4H>5%, 24H>10%）
/oi-divergence-pipeline high     # 牛市模式（4H>12%, 24H>25%）
```

## 管线流程

```
Phase 1: 涨幅榜筛选 (100+ 币种 → ~10 候选)
Phase 2: OI 快速预筛 (排除正常多头加仓)
Phase 3: 控盘检测精简版 (Holder 集中度 + 鲸鱼仓位)
Phase 4: 深度 OI 背离分析 (价格/OI/资金费率/爆仓 四维)
Phase 5: 综合评分排名 → Top 5 做空推荐
```

## 评分公式

| 维度 | 权重 | 说明 |
|------|------|------|
| OI 背离强度 | 40% | 连续 K 线数 + OI 降幅 |
| 控盘程度 | 25% | Top Holder 集中度 |
| 资金费率 | 15% | 多头拥挤程度 |
| 涨幅异常度 | 10% | 24H 涨幅 |
| 流动性 | 10% | 低流动性 = 高操纵风险 |

## 定时运行

搭配 Claude Code scheduled tasks 使用，建议每 4 小时巡检一次：

```
请帮我设置一个 scheduled task，每 4 小时自动运行 /oi-divergence-pipeline
```

## 相关 Skill

- `/oi-divergence {COIN}` — 单币 OI 背离分析
- `/whale-control {TOKEN} {CHAIN}` — 完整庄家控盘检测（地址聚类版）

对管线输出的高评分币种，建议用 `/whale-control` 做深入分析。

## 免责声明

仅供学习参考，不构成投资建议。OI 背离和控盘检测均基于链上数据推断，存在假阳性风险。
