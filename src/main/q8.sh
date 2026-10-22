#!/bin/bash
# Q8：repair 时识别并停止采集器、修复 HTTP 服务；cleanup 时停止修复后的服务。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"
action="${3:-repair}"

source "${input}/process.env"

if [ "${action}" = "repair" ]; then
    # 1. process.txt
    ps -o pid=,user=,state=,command= -p "${TARGET_PID}" > "${output}/process.txt"

    # 2. collector‑sample.log，至少两条TICK
    tail -n 10 "${WORKER_LOG}" | grep TICK > "${output}/collector-sample.log"

    # 3. terminate target pid
    kill "${TARGET_PID}"
    wait "${TARGET_PID}" 2>/dev/null

    # stop old service
    kill "${SERVICE_PID}"
    wait "${SERVICE_PID}" 2>/dev/null

    # write new server.conf
    cat > "${output}/server.conf" <<EOF
bind=127.0.0.1
port=${TARGET_PORT}
route=/status
EOF

    # start tool
    bash "${START_TOOL}" "${output}/server.conf" "${output}/service"

    # bounded retry curl
    status=""
    body=""
    for _ in {1..8}; do
        status=$(curl -s -o "${output}/_body.tmp" -w "%{http_code}" "http://127.0.0.1:${TARGET_PORT}/status" || true)
        body=$(cat "${output}/_body.tmp")
        if [ "${status}" = "200" ]; then
            break
        fi
        sleep 0.25
    done
    echo "${status}" > "${output}/http-status.txt"
    echo "${body}" > "${output}/httpbody.txt"
    rm -f "${output}/_body.tmp"

elif [ "${action}" = "cleanup" ]; then
    # read pid from service dir created by start‑tool
    serv_pid=$(cat "${output}/service/pid")
    kill "${serv_pid}"
    wait "${serv_pid}" 2>/dev/null
fi

exit 0
