#!/bin/bash
# setup_reminder.sh - 设置每日健身提醒（macOS launchd）
# 每天早上 7:30 自动弹出系统通知提醒今日训练计划
#
# 使用方法：
#   bash setup_reminder.sh          安装/更新提醒
#   bash setup_reminder.sh remove   卸载提醒

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/fitness.py"
PLIST_LABEL="com.fitness.daily-reminder"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
LOG_FILE="$HOME/Library/Logs/fitness-reminder.log"
HOUR=7
MINUTE=30

# ─── 卸载 ─────────────────────────────────────────────────────────────────────
if [ "$1" = "remove" ]; then
    launchctl unload "$PLIST_FILE" 2>/dev/null
    rm -f "$PLIST_FILE"
    echo "✅ 已卸载每日健身提醒"
    exit 0
fi

# ─── 检查 Python ──────────────────────────────────────────────────────────────
PYTHON_BIN=$(which python3 2>/dev/null)
if [ -z "$PYTHON_BIN" ]; then
    echo "❌ 未找到 python3，请先安装 Python 3"
    exit 1
fi

echo "📍 脚本路径：$SCRIPT_PATH"
echo "🐍 Python：$PYTHON_BIN"
echo "⏰ 提醒时间：每天 ${HOUR}:$(printf "%02d" $MINUTE)"

# ─── 创建 launchd plist ───────────────────────────────────────────────────────
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HOME/Library/Logs"

BRIEF_PATH="$SCRIPT_DIR/daily_brief.py"

# 生成一个启动脚本，Terminal.app 打开后运行简报
LAUNCHER="$SCRIPT_DIR/data/.launcher.sh"
cat > "$LAUNCHER" <<LAUNCHER_EOF
#!/bin/bash
clear
${PYTHON_BIN} "${BRIEF_PATH}"
echo ""
read -r -p "按 Enter 关闭..." _
LAUNCHER_EOF
chmod +x "$LAUNCHER"

cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/osascript</string>
        <string>-e</string>
        <string>tell application "Terminal" to do script "${LAUNCHER}"</string>
        <string>-e</string>
        <string>tell application "Terminal" to activate</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>${MINUTE}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>${LOG_FILE}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_FILE}</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

# ─── 加载 ─────────────────────────────────────────────────────────────────────
# 先卸载旧的（如有），再重新加载
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

if launchctl list | grep -q "$PLIST_LABEL"; then
    echo ""
    echo "✅ 每日健身提醒已设置！"
    echo "   每天 ${HOUR}:$(printf "%02d" $MINUTE) 会弹出系统通知告诉你今天练什么"
    echo ""
    echo "   立即测试简报：python3 \"$BRIEF_PATH\""
    echo "   卸载提醒：    bash \"$SCRIPT_DIR/setup_reminder.sh\" remove"
else
    echo "⚠️  加载失败，请检查系统设置 > 隐私与安全 > 通知是否已授权终端"
fi
