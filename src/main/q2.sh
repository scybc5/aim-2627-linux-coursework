#!/bin/bash
# Q2：创建 sentry_ws 四个子目录、两个空文件以及指定脚本和配置。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
input="$1"
output="$2"

ws="${output}/sentry_ws"
mkdir -p "${ws}/scripts" "${ws}/config" "${ws}/logs" "${ws}/tmp"

# hello.sh
cat > "${ws}/scripts/hello.sh" <<'EOF'
#!/bin/bash
echo "Hello, AIM Linux!"
EOF

# robot.conf
cat > "${ws}/config/robot.conf" <<'EOF'
robot=sentry
mode=training
log_level=INFO
EOF
# TODO：删除下方提示和 exit 77，再填写你的命令。
touch "${ws}/logs/.keep"
touch "${ws}/tmp/scratch.txt"

exit 0
