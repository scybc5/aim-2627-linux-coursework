#!/bin/bash
# 在 Ubuntu 上使用和 GitHub Actions 相同的测试入口。
set -eu
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [ "$(uname -s)" != Linux ]; then
    printf '%s\n' '请在 Ubuntu 虚拟机中运行，或推送到 GitHub Actions 自测。无需 Docker。' >&2
    exit 2
fi
mkdir -p "$root/generated"
sudo python3 "$root/tools/run_tests.py" \
    --submission "$root/src/main" --results "$root/generated" "$@"
