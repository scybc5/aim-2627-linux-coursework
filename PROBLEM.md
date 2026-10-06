# AIM 2627 Linux Coursework

> 哨兵开发机交接：从文件整理到远程连接，再到进程与服务排障。
>
> 本文是任务、接口和评分的唯一规格来源。本文先生成独立 LaTeX 源码 `Problem.tex`，再由 XeLaTeX 编译生成学生仓库的 `题面.pdf`；学生文本版 `PROBLEM.md` 与本文同步。环境与测试命令见学生仓库 `README.md`。

## 0. 开始前

你接手了一台哨兵开发机。上一位队友留下了目录、配置、日志和一句“昨天还能跑”。你的任务是把交接过程写成可复现的 Linux 命令，让换了路径、端口和数据之后也能重新完成。

本作业不要求机器人硬件、ROS 或 Python 编程。你只填写 Bash 脚本，教师已提供训练程序、临时 SSH 服务和全部公开测试。**GitHub Actions 是唯一正式评估通道。** 不交截图，不交人工操作记录，没有人工分、答辩分或独立 grader。

| 题号 | 题目 | 对应内容 | 分值 |
|---|---|---|---:|
| Q1 | 找到开发目录 | 路径、隐藏文件、文本读取 | 10 |
| Q2 | 建立哨兵工作区 | 目录、空文件、多行文本 | 10 |
| Q3 | 整理配置与权限 | 复制、移动、删除、权限、执行 | 10 |
| Q4 | 从日志中找到故障 | grep、管道、首尾查看、计数 | 15 |
| Q5 | 修复启动配置 | 精确替换、备份、输出通道 | 15 |
| Q6 | 安装交接工具 | 本地 Debian 包、安装数据库 | 10 |
| Q7 | 远程连接与日志回收 | SSH、公钥认证、SCP | 10 |
| Q8 | 昨天还能运行 | 进程、信号、端口、HTTP | 20 |
| Bonus | 保留调试会话 | tmux、后台运行与清理 | +10 |

建议按 Q1→Q8 的顺序完成，但各题独立评分，不依赖其他题的产物。预计 5–8 小时，不含虚拟机安装和首次下载依赖。正式截止时间另行公布。

### 0.1 统一接口

每题分别对应 `src/main/qN.sh`，接受两个参数：

```bash
bash src/main/qN.sh INPUT_DIRECTORY OUTPUT_DIRECTORY
```

两者都是绝对路径，可能包含空格。输入目录已经准备好，输出目录已经存在；Q3 的输出中还预置了待删除缓存。评测器从任意当前工作目录调用脚本。使用骨架里的 `input`、`output`，不要写死路径。只有 Q8 与 Bonus 额外接收动作参数。

输入素材不可修改，只在本题输出目录创建和修改产物。Q8／Bonus 还允许管理题面指定的训练进程和会话。各个脚本必须保留、使用 Bash 编写，不调用 Python、其他编程语言或预存答案替代命令；可以调用题目指定的教师工具。

非空文本使用 UTF-8、LF 换行，末尾保留一个换行；空结果为 0 字节。不在文本中添加进度提示、行号或其他说明。Q1–Q6 将连续执行两次，第二次应保持产物内容和权限稳定；Q6 的 dpkg 内部锁、备份数据库等维护状态不做逐字比较，安装状态与实际工具会重新检查。

未实现的骨架退出状态为 77，记 0 分。实现时删除提示和 `exit 77`；正常完成退出 0，意外错误返回非零。单次脚本调用限制为 15 秒，因此不能留下等待输入的命令、无限 `tail -f` 或持续前台服务。

### 0.2 环境变量文件

Q5、Q7、Q8 和 Bonus 会在输入目录放置 `.env` 文件。它们由教师生成，使用可被 Bash 读取的引用格式。可以这样读取：

```bash
source "$input/remote.env"
```

这只是读取本题参数，不是读取个人配置。临时用户名、路径、PID、端口和会话标识均以这些文件为准。

## Q1 找到开发目录 · 10 分

> 队友说配置就在交接包里，却没有告诉你那是一个隐藏文件。先确认自己在哪，再确认文件在哪。

**答题文件：** `src/main/q1.sh`。

输入结构：

```text
INPUT/
├── handover/
│   ├── .robot-id
│   └── README.txt
└── notes/
    └── welcome.txt
```

要求：

1. 进入输入目录的 `handover/`，把该目录的绝对路径保存为输出目录中的 `location.txt`。
2. 将隐藏文件 `.robot-id` 的完整内容保存为 `robot-id.txt`。
3. 将 `notes/welcome.txt` 的完整内容保存为 `welcome.txt`。

编号和欢迎文本会变化，根路径包含空格，调用时的当前目录不保证是仓库。`location.txt` 是本次真实绝对路径，而不是示例路径。

**评分：** 路径 4 分，隐藏编号 3 分，欢迎文本 3 分。

**相关命令：** `pwd`、`cd`、`ls`、`cat`、重定向。可以用 `man` 或 `--help` 查用法，不考 Linux 历史背诵。

## Q2 建立哨兵工作区 · 10 分

> 在讨论算法前，先让下一位队友能找到脚本、配置和日志。

**答题文件：** `src/main/q2.sh`。输入目录没有内容依赖。

在输出目录建立：

```text
OUTPUT/
└── sentry_ws/
    ├── scripts/
    │   └── hello.sh
    ├── config/
    │   └── robot.conf
    ├── logs/
    │   └── .keep
    └── tmp/
        └── scratch.txt
```

`.keep`、`scratch.txt` 均为空文件。`hello.sh` 完整内容为：

```text
#!/bin/bash
echo "Hello, AIM Linux!"
```

`robot.conf` 完整内容为：

```text
robot=sentry
mode=training
log_level=INFO
```

所有文件必须为普通文件，不能用符号链接代替。脚本此时不要求有执行权限。再次运行不能把文本重复追加。

**评分：** 四个子目录 4 分，两个空文件 2 分，脚本内容 2 分，配置内容 2 分。

**相关命令：** `mkdir`、`touch`、`cat` 和多行重定向。区分 `>` 与 `>>`。

## Q3 整理配置与权限 · 10 分

> 正式配置、草稿和缓存混在一起。你要整理文件，并让启动脚本能直接执行。

**答题文件：** `src/main/q3.sh`。

输入目录提供 `hello.sh`、`robot.conf`、`draft.conf` 和含 `cache.txt` 的 `tmp/`。脚本内容与 Q2 相同，初始没有执行权限。两份配置内容随测试变化。首次调用时，输出目录已经有 `sentry_ws/tmp/cache.txt`，模拟上次运行留下的缓存；必须实际删除它。

要求：

1. 在输出目录整理 `sentry_ws/`，把脚本复制到 `scripts/`，两份配置复制到 `config/`；可以复制输入的临时素材练习整理，但最终不保留 tmp。
2. 保留正式配置 `config/robot.conf`，另在 `backup/robot.conf` 保存完整副本。
3. 把 `config/draft.conf` 移动并改名为 `archive/draft.conf.old`，原位置不再保留。
4. 删除输出工作区的整个 `tmp/`，保留其他文件。
5. 将 `scripts/hello.sh` 权限设为 `750`，`config/robot.conf` 权限设为 `640`。
6. **直接执行**工作区中的 `hello.sh`，将标准输出保存为输出根目录的 `hello-output.txt`，完整内容为一行 `Hello, AIM Linux!`。

源素材不能改变；第二次运行同样应成功。无需修改文件所有者或使用 sudo。

**评分：** 复制及备份 3 分，移动 2 分，删除 1 分，两个权限共 2 分，执行与输出 2 分。

**相关命令：** `cp`、`mv`、`rm`、`chmod`。数字权限与“所有者／组／其他人”三类权限对应；不是所有权限问题都需要 root。

## Q4 从日志中找到故障 · 15 分

> 消息里提到 ERROR，不代表这一行的级别就是 ERROR。日志筛选要依据结构，而不是关键词猜测。

**答题文件：** `src/main/q4.sh`。

输入为 `boot.log`、`run.log`。非空行格式固定：

```text
级别 时间 模块 消息
```

前三个字段之间各一个空格；级别只有大写 `INFO`、`WARN`、`ERROR`，消息可以包含空格。输入没有空白行，但整个文件可以为空。两份日志各自已按时间排序，boot 整体早于 run。

示例：

```text
ERROR 09:00:02 camera device unavailable
INFO 09:00:03 launcher previous ERROR has been handled
```

第一行是错误，第二行不是。

输出要求：

| 文件 | 内容 |
|---|---|
| `all.log` | 按 boot、run 顺序完整拼接 |
| `errors.log` | 级别字段等于 ERROR 的完整行 |
| `attention.log` | 级别字段等于 WARN 或 ERROR 的完整行 |
| `recent.log` | all 最后 5 行，不足则全部 |
| `first-errors.log` | errors 最前 3 行，不足则全部 |
| `error-count.txt` | 错误行数，只有整数与换行 |

保持原行内容、顺序和重复行；不要排序或去重。没有匹配时提取文件为空，计数为 `0`，脚本仍正常结束。公开测试包含常规、无错误、全空和不足指定行数的日志。

**评分：** 合并 2 分，错误 4 分，告警 3 分，末尾 2 分，首条错误 2 分，计数 2 分。

**相关命令：** `cat`、`grep`、`head`、`tail`、`wc`、管道。普通正则和扩展正则的语法不同；`grep` 无匹配返回 1，不应当作本题致命错误。

## Q5 修复启动配置 · 15 分

> 改配置时最怕“全局替换一下”把注释、备用端口和有效配置一起改掉。

**答题文件：** `src/main/q5.sh`。

输入有 `robot.conf` 和 `tools.env`。配置中的有效 `port`、`log_level` 各出现一次；键和值之间无空格，旧值会变化。注释、空行和相似键不是修改对象，例如：

```text
# port=9000

port=9000
backup_port=9000
# log_level=DEBUG
log_level=DEBUG
```

要求：

1. 完整备份为 `robot.conf.bak`。
2. 生成输出 `robot.conf`，仅把有效 `port` 值改为 `8080`、有效 `log_level` 值改为 `INFO`。其他行、顺序、注释和空行保持不变。
3. 读取 `tools.env` 中的 `CHECK_TOOL`。调用接口为 `bash "$CHECK_TOOL" CONFIG_FILE`，检查修复后的文件。
4. 工具标准输出保存为 `check.out`，标准错误保存为 `check.err`，不要混合或追加上次内容。

工具成功时退出 0，stdout 为一行 `CONFIG OK`，stderr 为一行 `NOTICE: training check only`；该提示不表示失败。配置不合格时退出非零，工具不修改文件、不连接网络。

**评分：** 备份、端口、日志等级、其他内容保留、通道分流各 3 分。

**相关命令：** `cp`、`sed`、`>`、`2>`，以及退出状态。输入遵守上述格式，不考重复键、缺失键或任意配置语法解析。

## Q6 安装交接工具 · 10 分

> 赛场网络不一定可靠。队友给你一个本地 Debian 包，你要确认它真的安装了，而且能运行。

**答题文件：** `src/main/q6.sh`。

输入提供 `aim-sentry-tools.deb`，包名为 `aim-sentry-tools`，架构为 all，版本随测试变化；没有依赖和安装维护脚本，包内有 `/usr/bin/aim-sentry-info`。

要求：

1. 使用 dpkg 把包安装到输出目录的 `sysroot/`，不能安装到真实系统根目录。
2. 安装数据库位于 `sysroot/var/lib/dpkg/`，必须记录正确版本的 `install ok installed` 状态。
3. 运行安装后的 `sysroot/usr/bin/aim-sentry-info`，stdout 保存为 `tool-output.txt`。工具输出 `SENTRY TOOL 版本号`，版本须来自实际包。

教师用普通账户执行本题。dpkg 支持 `--root=目录` 指定安装根、`--force-not-root` 允许非 root 安装；日志可以用 `--log=/dev/null` 关闭。这些选项用于本题的无维护脚本训练包。不要使用 sudo，不联网安装或刷新源。只解压 `.deb`、手写数据库或直接写报告都不能代替安装。

允许再次安装相同版本；dpkg 的内部数据库备份不是作业产物规格。测试器独立查询数据库并运行真实安装文件。

**评分：** 正确安装状态与版本 6 分，真实工具运行及记录 4 分。

**相关命令：** `dpkg`、`dpkg-query`。课程中的 apt 在有软件源时负责依赖解析和下载；本题刻意使用本地无依赖包，以免外部镜像站决定成绩。

## Q7 远程连接与日志回收 · 10 分

> 机器人上的日志不能靠在自己的电脑里复制一份来冒充。先登录另一名用户，再从远端回收文件。

**答题文件：** `src/main/q7.sh`。

教师启动只监听回环地址的临时 SSH 服务，使用独立远端账户。输入目录 `remote.env` 提供：

| 变量 | 意义 |
|---|---|
| `HOST`、`PORT` | 目标地址与动态端口 |
| `REMOTE_USER` | 远端临时用户名 |
| `KEY_PATH` | 教师提供的客户端私钥路径 |
| `KNOWN_HOSTS` | 已核对的目标主机公钥记录 |
| `REMOTE_LOG` | 远端日志的绝对路径 |

要求：

1. 在输出目录创建权限为 `600` 的 `ssh_config`，定义别名 `aim-sentry`；地址、端口、用户、密钥、已知主机文件均读取给定参数。
2. 配置 `IdentitiesOnly yes` 和 `StrictHostKeyChecking yes`。不得关闭主机密钥检查，也不要依赖个人 SSH 配置或 agent；用 `BatchMode yes` 或命令行等价选项避免等待密码输入。
3. 使用该配置和别名通过 SSH 执行远端 `whoami`，将返回的用户名保存为 `remote-user.txt`。
4. 使用 SCP 将 `REMOTE_LOG` 下载为输出目录的 `received/errors.log`。

客户端脚本没有本地读取该远端私有日志的权限。远端服务只接受公钥认证；教师会用输出配置重新连接，并比较真实远端文件与下载内容，同时核对服务端连接与文件传输会话。

密钥、用户名、端口和日志内容都会变化。路径可能包含空格，SSH 配置中的路径也要正确引用。不要复制或提交临时私钥。

**评分：** 配置 3 分，远端命令与复连 3 分，SCP 文件传输 4 分。

**相关命令：** `ssh -F`、`scp -F`、公钥认证、known_hosts。OpenSSH 新版 SCP 默认使用 SFTP 子系统，这是正常行为。

## Q8 昨天还能运行 · 20 分

> 后台跑着两个采集器，一个 HTTP 服务监听错了位置。别急着结束所有 Python 进程，也别把防火墙整个关掉。

**答题文件：** `src/main/q8.sh`。

本题调用两次：

```bash
bash src/main/q8.sh INPUT OUTPUT repair
bash src/main/q8.sh INPUT OUTPUT cleanup
```

省略动作时默认为 repair。repair 返回后，服务必须保持运行，供教师独立请求；cleanup 返回后服务必须停止。

教师预先启动目标日志采集器、另一个不能停止的采集器、一个错误 HTTP 服务。输入有 `server.conf` 和 `process.env`：

| 变量 | 意义 |
|---|---|
| `TARGET_PID`、`TARGET_TOKEN` | 目标采集器 PID 和实例标识 |
| `WORKER_LOG` | 目标采集器不断增长的日志 |
| `SERVICE_PID` | 原错误 HTTP 服务 PID |
| `TARGET_PORT` | 修复后应使用的动态端口 |
| `START_TOOL` | 教师服务启动工具路径 |

### A. 定位与停止采集器 · 10 分

repair 阶段要求：

1. 用进程查询命令查看目标 PID，保存输出根目录的 `process.txt`，每行一个键：

   ```text
   pid=实际PID
   user=实际所有者
   state=实际进程状态
   command=完整命令行
   ```

   state 接受实际 ps 状态字符串，如 `S` 或 `Ss`；进程应处于 R／S 状态。命令行应包含教师给定实例标识，不能写死用户名和 PID。
2. 保存至少两条目标采集器的 TICK 日志为 `collector-sample.log`，允许包含 START 行。
3. 向目标 PID 发送普通终止信号，等待它正常退出。教师程序正常退出时会写出 `STOP 实例标识`。
4. 另一个采集器必须继续运行，不能用 killall 或宽泛的 pkill 代替 PID 定位。

**评分：** 识别记录 3 分，正常停止 3 分，保留另一个进程 2 分，日志记录 2 分。教师检查真实进程和停止记录，不仅检查学生写的文本。

### B. 恢复 HTTP 服务 · 10 分

两个公开场景分别是端口错误和路由错误，教师会逐个验证。输入 `server.conf` 固定包含三行：

```text
bind=127.0.0.1
port=原端口
route=原路径
```

repair 阶段要求：

1. 正常停止 `SERVICE_PID` 指定的原服务，等待退出。
2. 生成输出 `server.conf`，完整内容是 `bind=127.0.0.1`、`port=TARGET_PORT 实际数值`、`route=/status` 三行，保持这一顺序。
3. 使用教师启动工具运行修复后的服务：

   ```bash
   bash "$START_TOOL" "$output/server.conf" "$output/service"
   ```

   工具启动后台进程后返回，写入 `service/pid` 和 `service/service.log`。工具只启动，不替你等待服务就绪或验证 HTTP。
4. 等待就绪，用 curl 请求 `http://127.0.0.1:TARGET_PORT/status`。保存 `http-status.txt` 为一行 `200`，`http-body.txt` 为一行 `SENTRY READY`。使用有界重试和超时，不能无限等待。
5. 返回时保留服务运行。教师独立发出请求，不信任学生报告中的 200。

cleanup 阶段要求：根据本题服务状态目录定位修复后的服务，正常停止它并等待端口释放；保留已生成的报告，不操作其他进程。

**评分：** 原服务停止与新配置 3 分，真实 HTTP 响应和报告 4 分，cleanup 释放端口 3 分。

**相关命令：** `ps`、`kill`、`cat`／`tail`、`ss`、`curl`。ping 成功只说明部分网络可达，不证明 HTTP 程序正确。不要修改系统路由、防火墙或真实 SSH 服务。

## Bonus 保留调试会话 · +10 分

> SSH 断开后仍希望调试程序继续运行。先学会管理一个分离的 tmux 会话。

**答题文件：** `src/main/bonus.sh`，额外接收 start／stop 动作，默认 start。

输入 `bonus.env` 提供 `TMUX_SOCKET`、`SESSION`、`TOKEN`、`WORKER_TOOL`。所有 tmux 命令使用 `-L "$TMUX_SOCKET"`，只管理指定会话。

start 阶段：

1. 创建指定名称的分离会话，运行教师采集器，接口为 `python3 "$WORKER_TOOL" --token "$TOKEN" --log "$output/bonus.log"`。
2. 脚本返回后会话无附着客户端，采集器继续运行，日志继续增长；全程只启动一个实例。

stop 阶段：正常停止会话内采集器，再结束指定会话；不结束其他会话。

**评分：** 分离会话 4 分，返回后日志继续增长 4 分，停止和清理 2 分。本题用真实 tmux 会话验证持久运行，不要求模拟公网断线。

## 9. 评分与提交

### 9.1 唯一评分通道

全部权重、生成数据和检查代码公开在 `tests/coursework.py`。每个小项需要通过该题所有公开场景才得到该小项分数，部分小项失败不取消其他小项分数。

必做总分 100，Bonus 单独最多 10。通过条件是**必做至少 60 分，且 Q7、Q8 的全部检查通过**。Bonus 不抵消这两项关键能力。满分条件是必做全部小项通过，不要求 Bonus。

没有隐藏测试、单独 grader、人工评阅或现场答辩。CI 只验证提交脚本的行为，不能证明作者独立理解全部命令；允许 AI 辅助，不设置无法自动判断的主观分。

原始模板的脚本全部未实现，初始化可成功，但 `assessment_passed` 为 false、得分为 0。开始答题后，未达到通过条件，完整 CI 退出失败；Summary 仍展示分数。单题本地测试不产生正式通过结论。

### 9.2 合法修改与提交

只允许修改 `src/main/q1.sh`–`q8.sh`、`bonus.sh`，以及可选 `.agent-sessions/` 归档。其余文件不可修改；所有答题文件必须保留为普通文件。不要提交 generated、个人 SSH 密钥或密码。

使用模板创建个人仓库，在 main 开发；每完成一段任务可以提交并推送。CI 会直接在 Ubuntu runner 上运行，无需 Docker。累计修改以初始模板提交为基准检查，测试从该基准取出；不要重建 Git 历史。

正式提交内容：个人仓库地址、指定 main commit 链接、与该 commit 对应的完整 Actions run 链接。不要只提交单题自测结果或旧 commit 的成功截图。提交入口和截止日期由培训负责人公布。

### 9.3 学习参考

- 2526 Linux 作业：<https://github.com/unnc-aim/aim-2526-linux-coursework>
- 2627 Linux 课程：<https://github.com/unnc-aim/aim-2627-rookie-courses/tree/main/Computing/02-Linux>
- Linux2：路径与目录；Linux3／4：文件与权限；Linux5：包管理。
- Linux6：SSH；Linux7：文本处理；Linux8：进程与 tmux；Linux9：网络与服务。
- 不熟悉的命令先查 `man 命令` 或 `命令 --help`。先用小样例理解输出，再组合命令。
