#!/bin/bash
# Q5：运行 launch.env 给定的启动前检查，保存 stdout/stderr、真实退出码和诊断报告。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
# TODO：删除下方提示和 exit 77，再填写你的命令。
input="$1"
output="$2"

source "${input}/launch.env"

bash "${LAUNCH_TOOL}" "${MODEL_PATH}" "${CAMERA_PATH}" > "${output}/stdout.log" 2> "${output}/stderr.log"
ret=$?

echo "${ret}" > "${output}/exit-code.txt"

if [ "${ret}" -eq 0 ]; then
    res="SUCCESS"
    reason="NONE"
elif [ "${ret}" -eq 10 ]; then
    res="FAILED"
    reason="MODEL_MISSING"
elif [ "${ret}" -eq 20 ]; then
    res="FAILED"
    reason="CAMERA_DENIED"
else
    res="FAILED"
    reason="NONE"
fi

cat > "${output}/report.txt" <<EOF
result=${res}
exit_code=${ret}
reason=${reason}
EOF

exit 0
