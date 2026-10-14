#!/bin/bash
# Chrome 自动化实例守护：退出即拉起，保持 CDP 9222 常驻
# CHROME：浏览器路径；CHROME_PROFILE：专用 profile 目录（登录态/cookie 持久化于此）
CHROME="${CHROME_BIN:-/c/Program Files/Google/Chrome/Application/chrome.exe}"
PROFILE="${CHROME_PROFILE:-C:\\Users\\USER\\.workbuddy-ai\\chrome-automation}"
ARGS="--remote-debugging-port=9222 --user-data-dir=$PROFILE --no-first-run --no-default-browser-check --hide-crash-restore-bubble"
while true; do
  echo "[$(date +%H:%M:%S)] launching chrome"
  "$CHROME" $ARGS
  echo "[$(date +%H:%M:%S)] chrome exited code=$?, relaunch in 5s"
  sleep 5
done
