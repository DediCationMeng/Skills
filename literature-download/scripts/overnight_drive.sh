#!/bin/bash
# 通宵自动下载驱动：生成批次 -> 下载 -> 核验导入 -> 清理，循环至队列清空
# 遇到付费墙/交互自动搁置继续；遇限流/质询自动冷却重试；CDP 掉线自动等守护拉起
# 路径约定：WORKDIR=工作目录（默认脚本上一级）；DL_DIR=下载目录；IMPORT_TOOL=项目归档工具（默认 elm_import_pdfs.py）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
export NO_PROXY="localhost,127.0.0.1,::1"
export BU_CDP_URL="http://127.0.0.1:9222"
BU="${BU_BIN:-/c/Users/USER/.workbuddy-ai/binaries/python/envs/default/Scripts/browser-use.exe}"
PY="${PY_BIN:-/c/Users/USER/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe}"
PYQ="${PYQ_BIN:-/c/Users/USER/.workbuddy-ai/binaries/python/versions/3.13.12/python.exe}"
LOG=night_run.log
BASE="${WORKDIR:-$(dirname "$SCRIPT_DIR")}"
DL_DIR="${DL_DIR:-$HOME/Downloads}"
IMPORT_TOOL="${IMPORT_TOOL:-elm_import_pdfs.py}"

blocked_streak=0

for round in $(seq 1 80); do
  echo "===== ROUND $round $(date +%H:%M:%S) =====" | tee -a $LOG

  # --- CDP 存活检查（守护脚本应在 5s 内拉起） ---
  for chk in 1 2 3; do
    if curl -s --max-time 5 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
      break
    fi
    echo "CDP down (try $chk), wait for guard" | tee -a $LOG
    if [ "$chk" = 1 ]; then
      nohup bash chrome_guard.sh >/dev/null 2>&1 &
    fi
    sleep 20
  done
  if ! curl -s --max-time 5 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
    echo "CDP still down, sleep 120" | tee -a $LOG
    sleep 120
    continue
  fi

  # --- 生成批次 ---
  GEN=$("$PYQ" gen_batch_next.py 2>&1)
  echo "$GEN" | tee -a $LOG
  PHASE=$(echo "$GEN" | grep -o "PHASE=[a-z_]*" | cut -d= -f2)
  if [ "$PHASE" = "none" ]; then
    echo "ALL_DONE: queue empty" | tee -a $LOG
    break
  fi

  # --- 下载 ---
  "$BU" < batch_download.py > batch_out.txt 2>&1
  grep -E "^(OK|SKIP|FAILED|CARRYOVER|=== )" batch_out.txt | tee -a $LOG

  # --- 状态判定 + 搁置 ---
  ST=$("$PYQ" night_state.py batch_out.txt "$PHASE" 2>&1)
  echo "$ST" | tee -a $LOG

  # --- 导入核验（项目归档工具；--apply 写库前驱动即本脚本，故导入在下载间隙执行即安全） ---
  "$PY" "$IMPORT_TOOL" --downloads "$DL_DIR" --since "${IMPORT_SINCE:-2026-10-10}" \
    --dir "$BASE" --apply 2>&1 | tail -3 | tee -a $LOG

  # --- 清理（每轮两小批，≤20 个） ---
  "$PYQ" cleanup_once.py | tee -a $LOG
  "$PYQ" cleanup_once.py | tee -a $LOG

  # --- 阻塞冷却 ---
  if echo "$ST" | grep -q "verdict=BLOCKED"; then
    blocked_streak=$((blocked_streak+1))
    if [ $blocked_streak -ge 3 ]; then
      echo "blocked 3 rounds in a row, long cooldown 1800s" | tee -a $LOG
      sleep 1800
      blocked_streak=0
    else
      echo "blocked, cooldown 600s" | tee -a $LOG
      sleep 600
    fi
  else
    blocked_streak=0
    sleep 25
  fi
done
echo "DRIVER EXIT $(date +%H:%M:%S)" | tee -a $LOG
