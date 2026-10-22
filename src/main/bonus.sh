#!/bin/bash
# Bonus：start 时创建分离的 tmux 会话和采集器；stop 时正常停止采集器并结束会话。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"
action="${3:-start}"

source "${input}/bonus.env"

if [ "${action}" = "start" ]; then
    tmux -L "${TMUX_SOCKET}" new-session -d -s "${SESSION}" "python3 \"${WORKER_TOOL}\" --token \"${TOKEN}\" --log \"${output}/bonus.log\""
elif [ "${action}" = "stop" ]; then
    tmux -L "${TMUX_SOCKET}" send-keys -t "${SESSION}" C-c
    sleep 0.3
    tmux -L "${TMUX_SOCKET}" kill-session -t "${SESSION}"
fi

exit 0
