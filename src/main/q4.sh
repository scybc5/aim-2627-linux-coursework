#!/bin/bash
# Q4：合并日志，按级别提取，保存首尾片段并统计错误行数。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"

cat "${input}/boot.log" "${input}/run.log" > "${output}/all.log"

cat "${output}/all.log" | grep "^ERROR" > "${output}/errors.log" || true
cat "${output}/all.log" | grep -E "^WARN|^ERROR" > "${output}/attention.log" || true

tail -n5 "${output}/all.log" > "${output}/recent.log"
head -n3 "${output}/errors.log" > "${output}/first-errors.log"

wc -l < "${output}/errors.log" > "${output}/error-count.txt"

exit 0
