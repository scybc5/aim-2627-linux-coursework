#!/bin/bash
# Q7：读取 input/remote.env，生成 ssh_config，用 SSH 和 SCP 获取远程数据。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"

source "${input}/remote.env"

sshconf="${output}/ssh_config"
mkdir -p "${output}/received"

cat > "${sshconf}" <<EOF
Host aim-sentry
  HostName ${HOST}
  Port ${PORT}
  User ${REMOTE_USER}
  IdentityFile "${KEY_PATH}"
  UserKnownHostsFile "${KNOWN_HOSTS}"
  IdentitiesOnly yes
  StrictHostKeyChecking yes
  BatchMode yes
EOF
chmod 600 "${sshconf}"

ssh -F "${sshconf}" aim-sentry whoami > "${output}/remote-user.txt"
scp -F "${sshconf}" aim-sentry:"${REMOTE_LOG}" "${output}/received/errors.log"

exit 0
