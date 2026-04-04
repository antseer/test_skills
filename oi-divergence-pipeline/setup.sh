#!/bin/bash
# oi-divergence-pipeline skill 安装配置脚本
# 自动检测 Antseer MCP 服务器 UUID 并写入 SKILL.md

set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_FILE="$SKILL_DIR/SKILL.md"

echo ""
echo "=== oi-divergence-pipeline skill 配置 ==="
echo ""

# 检查 SKILL.md 是否已经配置过
if ! grep -q "ANTSEER_MCP_ID" "$SKILL_FILE"; then
  echo "✅ 已检测到 SKILL.md 中不含占位符，可能已配置完成。"
  echo "   如需重新配置，请手动将 SKILL.md 中的 UUID 替换为 ANTSEER_MCP_ID 后再运行此脚本。"
  exit 0
fi

echo "🔍 尝试从 Claude Code session 缓存中自动检测 Antseer MCP UUID..."

MCP_ID=$(grep -r "ant_futures_market_structure" ~/.claude/sessions/*.json 2>/dev/null | \
  grep -o 'mcp__[a-z0-9-]*__ant_futures_market_structure' | head -1 | \
  sed 's/mcp__//;s/__ant_futures_market_structure//' 2>/dev/null || true)

if [ -n "$MCP_ID" ]; then
  echo "✅ 自动检测到 MCP ID: $MCP_ID"
else
  echo "⚠️  无法自动检测 Antseer MCP UUID。"
  echo ""
  echo "   请按以下步骤手动获取："
  echo "   1. 在 Claude Code 中输入 /tools 或查看工具列表"
  echo "   2. 找到工具名格式为: mcp__<UUID>__ant_futures_market_structure"
  echo "   3. 复制其中的 <UUID> 部分（中间那段，如 3211031c-c61f-4f99-8441-0878d032a450）"
  echo ""
  read -p "   请粘贴你的 Antseer MCP UUID: " MCP_ID
fi

if [ -z "$MCP_ID" ]; then
  echo "❌ 未输入 UUID，退出。请确保 Antseer MCP 服务器已正确安装后重试。"
  exit 1
fi

echo ""
echo "📝 正在更新 SKILL.md (替换 ANTSEER_MCP_ID → $MCP_ID)..."

sed -i '' "s/ANTSEER_MCP_ID/$MCP_ID/g" "$SKILL_FILE"

echo ""
echo "✅ 配置完成！"
echo ""
echo "   现在可以在 Claude Code 中运行:"
echo "   /oi-divergence-pipeline"
echo ""
echo "   如需重置，请将 SKILL.md 中的 UUID 替换回 ANTSEER_MCP_ID 再次运行此脚本。"
