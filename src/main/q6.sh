#!/bin/bash
# Q6：将本地 Debian 包安装到 output/sysroot，运行安装后的工具。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"

debfile="${input}/aim-sentry-tools.deb"
sysroot="${output}/sysroot"

mkdir -p "${sysroot}"
dpkg -i --root="${sysroot}" --force-not-root --log=/dev/null "${debfile}"

bash "${sysroot}/usr/bin/aim-sentry-info" > "${output}/tool-output.txt"

exit 0
