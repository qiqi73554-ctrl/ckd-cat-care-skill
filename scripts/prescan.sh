#!/usr/bin/env bash
# 提交/推送前敏感信息扫描。用法：bash scripts/prescan.sh
# 退出码 0 = 干净，1 = 发现可疑项
set -u
cd "$(dirname "$0")/.." || exit 1

# 把关键词放进环境变量，避免脚本自身被扫描命中
COMPANY="${QA_COMPANY_PATTERN:-}"
NAME="${QA_NAME_PATTERN:-}"

EXCLUDE='\.git/|node_modules/|__pycache__|\.venv/|translations/|\.lock$|scripts/prescan\.sh'

hits=""

echo "=== 1/4 公司名 ==="
if [ -n "$COMPANY" ]; then
  r=$(grep -rInE "$COMPANY" . 2>/dev/null | grep -vE "$EXCLUDE")
  [ -n "$r" ] && { echo "$r"; hits="$hits company"; }
else
  echo "(未设置 QA_COMPANY_PATTERN，跳过)"
fi

echo "=== 2/4 真实姓名 ==="
if [ -n "$NAME" ]; then
  r=$(grep -rInE "$NAME" . 2>/dev/null | grep -vE "$EXCLUDE")
  [ -n "$r" ] && { echo "$r"; hits="$hits name"; }
else
  echo "(未设置 QA_NAME_PATTERN，跳过)"
fi

echo "=== 3/4 硬编码密码 / 内网 IP ==="
r2=$(grep -rInE '(password|passwd|pwd|secret|apikey|api_key)[[:space:]]*[=:][[:space:]]*['"'"'"][^'"'"'"]{6,}' \
  --include='*.py' --include='*.js' --include='*.json' --include='*.yaml' --include='*.md' . 2>/dev/null \
  | grep -vE "$EXCLUDE|process\.env|os\.environ|getenv|placeholder|example|your|dummy|测试|示例")
[ -n "$r2" ] && { echo "$r2"; hits="$hits cred"; }

r3=$(grep -rInE '\b(10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9]{1,3}\.[0-9]{1,3}\b' \
  --include='*.py' --include='*.js' --include='*.json' --include='*.md' --include='*.yaml' . 2>/dev/null \
  | grep -vE "$EXCLUDE")
[ -n "$r3" ] && { echo "$r3"; hits="$hits ip"; }

echo "=== 4/4 Git 提交历史 ==="
r4=""
if [ -n "$COMPANY$NAME" ]; then
  pat="${COMPANY}${NAME:+|$NAME}"
  r4=$(git grep -IlE "$pat" $(git rev-list --all) 2>/dev/null)
  [ -n "$r4" ] && { echo "$r4" | head -20; hits="$hits history"; }
fi

echo
if [ -n "$hits" ]; then
  echo "❌ 发现可疑项：$hits —— 清理后再提交/推送"
  exit 1
else
  echo "✅ 未发现敏感信息"
  exit 0
fi