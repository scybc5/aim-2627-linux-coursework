#!/bin/bash
# Q1：定位 handover，读取隐藏编号和欢迎文本。输出 location.txt、robot-id.txt、welcome.txt。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
input="$1"
output="$2"

handover_dir="${input}/handover"
real_handover=$(realpath "${handover_dir}")
echo "${real_handover}">"${output}/location.txt"

# TODO：删除下方提示和 exit 77，再填写你的命令。
cat "${handover_dir}/robot-id.txt" > "${output}/robot-id.txt"
cat "${handover_dir}/notes/welcome.txt" > "${output}/welcome.txt"

exit 0  




