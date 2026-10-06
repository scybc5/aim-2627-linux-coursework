# AIM 2627 Linux Coursework - 哨兵开发机交接

> 全部任务、接口、评分与提交要求见 [题面.pdf](题面.pdf) 或其同内容文本版 [PROBLEM.md](PROBLEM.md)。本 README 说明如何开始和运行测试。
>
> **GitHub Actions 是唯一正式评估通道。全部测试公开，没有独立 grader、隐藏测试、操作截图分或人工答辩分。**

## 1. 环境

- 学生环境：课程要求的 Ubuntu 24.04 LTS 虚拟机，amd64／arm64 均可；答题文件使用 Bash、UTF-8、LF 换行。
- 正式 CI：GitHub hosted `ubuntu-24.04` runner，直接执行测试；无需 Docker。
- Windows／macOS 可以编辑文件并推送自测；需要本地完整测试时，请进入 Ubuntu 虚拟机。
- 不需要安装 ROS、连接机器人或编写 Python 程序。`tools/`、`tests/` 中的 Python 是教师提供的基础设施。

## 2. 快速开始

1. 在模板仓库的 GitHub 页面点击 **Use this template → Create a new repository**，创建自己的仓库。
2. 克隆你的仓库，在 main 分支完成作业：

   ```bash
   git clone https://github.com/<你的用户名>/<你的仓库>.git
   cd <你的仓库>
   ```

3. 阅读题面，依次填写 `src/main/q1.sh` 至 `q8.sh`。选做题填写 `bonus.sh`。
4. 每个骨架末尾有 `exit 77`，表示“未实现”。开始实现时删除该行和对应提示。只删除提示却不实现任务不能得分。
5. 提交并推送，查看 **Actions → Linux Coursework CI → 最新运行 → Summary**。

   ```bash
   git add src/main
   git commit -m "Complete Q1 path navigation"
   git push origin main
   ```

CI 会显示每题、小项、必做总分、Bonus 和通过结论。原始骨架可初始化成功，但成绩是 0 分、结论是“未开始”；开始答题后，未达到通过条件的完整 CI 会失败。

## 3. 本地自测

只在自己的 Ubuntu 训练虚拟机中执行。先安装教师测试依赖：

```bash
sudo apt-get update
sudo apt-get install -y python3 openssh-client openssh-server tmux procps curl dpkg
```

运行全部测试，或只测试一题：

```bash
bash tools/test.sh
bash tools/test.sh --question Q4
bash tools/test.sh --question Q7 --question Q8
bash tools/test.sh --question B
```

测试器需要 sudo 来创建临时测试账户与 SSH 服务，**学生脚本以临时普通用户执行，不具备 sudo 权限**。临时账户、进程和目录在测试后清理。测试仅连接本机回环地址，不改你的个人 SSH 配置、不使用你的密钥、不重启系统 SSH 服务。首次 apt 安装依赖需要网络，正式题目用例不依赖公网。

结果写入 `generated/`：

| 文件 | 内容 |
|---|---|
| `summary.md` | 和 Actions Summary 相同的得分与反馈 |
| `score.json` | 分题、小项、总分和通过状态 |
| `runs.json` | 各次脚本的退出状态、标准输出和标准错误 |
| `artifacts/` | 指定文本产物，便于对照题面 |

单题自测只帮助调试，不是正式总成绩。正式成绩取指定 main commit 对应的完整 CI。`generated/` 不提交。

## 4. 仓库结构与修改范围

| 路径 | 用途 | 可否修改 |
|---|---|---|
| `src/main/q1.sh`–`q8.sh` | 必做题答题脚本 | 可以 |
| `src/main/bonus.sh` | 选做题答题脚本 | 可以 |
| `.agent-sessions/` | 可选 AI 会话归档 | 可以 |
| `PROBLEM.md`、`题面.pdf`、`README.md` | 规格和使用说明 | 不可 |
| `tests/`、`tools/`、`fixtures/` | 全部公开测试、训练程序和素材 | 不可 |
| `.github/`、`.vscode/` 与其余配置 | CI 和基础设施 | 不可 |

请保留所有 9 个答题文件，未做的题继续保留骨架。不得删除、改名或换成符号链接；无需赋予答题文件执行权限，评测器通过 Bash 调用。

学生仓库的 CI 以仓库初始模板提交为基准检查累计修改，并从该提交取出测试运行。因此修改测试、评分权重、题面或 CI 不属于合法提交。不要用 `git init` 重建历史或合并不相关仓库。

## 5. AI 使用与归档

允许查阅课程、命令手册、同伴解释和 AI 辅助。提交的脚本需要遵守公开规格，用真实命令完成任务；测试会更换路径、内容、版本和端口。

与 Python 模板保持一致，提供可选 AgentLedger 会话归档配置：

```bash
python3 -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit
```

归档不参与评分，未使用 AI 无需安装。若启用归档，先确认会话没有密码、令牌或个人密钥；归档是普通 Git 内容，可能随公开仓库推送。

## 6. 常见问题

- **`grep` 没找到匹配后脚本提前退出？** 无匹配通常返回 1；Q4 中没有错误是正常输入，需处理这个状态。
- **本地能跑、CI 路径不对？** 使用传入的输入／输出目录，引用含空格路径；不要写死用户名、仓库位置、PID、端口或包版本。
- **Q6 提示不是 root？** 本题安装到指定 sysroot；按题面使用 dpkg 的非 root 选项，不使用 sudo。
- **Q7 找不到自己的 SSH 密钥？** 不使用个人密钥。读取测试器提供的 `remote.env` 和临时密钥路径。
- **Q8 修好后立刻停止服务了？** `repair` 返回时必须保持服务运行，教师会独立发送 HTTP 请求；收到 `cleanup` 才停止它。
- **Actions 没有运行？** 确认推送到 main、仓库允许 Actions；也可用 workflow_dispatch 手动触发。
- **CI 显示红色，但有分数？** 仍可在 Summary 查看小项得分。基础设施检查失败时则没有有效成绩。

正式提交方式见题面末尾；收集入口和截止时间由培训负责人另行公布。
