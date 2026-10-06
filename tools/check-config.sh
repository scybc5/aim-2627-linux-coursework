#!/bin/bash
# 教师提供的 Q5 检查工具。stderr 的 NOTICE 不是失败。
set -eu
config=${1:?需要配置文件路径}
if ! grep -qx 'port=8080' "$config" || ! grep -qx 'log_level=INFO' "$config"; then
    printf '%s\n' 'CONFIG INVALID' >&2
    exit 1
fi
printf '%s\n' 'CONFIG OK'
printf '%s\n' 'NOTICE: training check only' >&2
