#!/bin/bash
# Q3：复制素材、备份配置、移动草稿、删除 tmp、设定权限并直接运行 hello.sh。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"

ws="${output}/sentry_ws"

# 复制素材
mkdir -p "${ws}/scripts" "${ws}/config"
cp "${input}/hello.sh" "${ws}/scripts/"
cp "${input}/robot.conf" "${ws}/config/"
cp "${input}/draft.conf" "${ws}/config/"

# backup
mkdir -p "${output}/backup"
cp "${ws}/config/robot.conf" "${output}/backup/robot.conf"

# move draft.conf → archive/draft.conf.old
mkdir -p "${output}/archive"
mv "${ws}/config/draft.conf" "${output}/archive/draft.conf.old"

# remove tmp entire
rm -rf "${ws}/tmp"

# permissions
chmod 750 "${ws}/scripts/hello.sh"
chmod 640 "${ws}/config/robot.conf"

# run and capture output
bash "${ws}/scripts/hello.sh" > "${output}/hello-output.txt"

exit 0
