"""Public task scenarios, input generation and weighted assertions. No private grader."""
import hashlib
import os
from pathlib import Path
import pwd
import shlex
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request

TASKS = {
    "Q1": ("找到开发目录", [("路径定位", 4), ("隐藏文件", 3), ("文本读取", 3)]),
    "Q2": ("建立工作区", [("目录结构", 4), ("空文件", 2), ("启动脚本", 2), ("配置文本", 2)]),
    "Q3": ("整理与权限", [("复制和备份", 3), ("移动归档", 2), ("删除临时目录", 1), ("精确权限", 2), ("执行脚本", 2)]),
    "Q4": ("日志分析", [("合并", 2), ("错误提取", 4), ("告警提取", 3), ("末尾日志", 2), ("首条错误", 2), ("错误计数", 2)]),
    "Q5": ("配置修复", [("原始备份", 3), ("端口", 3), ("日志等级", 3), ("保留其他内容", 3), ("输出分流", 3)]),
    "Q6": ("安装开发工具", [("真实安装状态", 6), ("运行安装产物", 4)]),
    "Q7": ("SSH 与 SCP", [("客户端配置", 3), ("远程命令", 3), ("远程日志传输", 4)]),
    "Q8": ("进程与服务排障", [("进程识别", 3), ("正常停止", 3), ("保留其他进程", 2), ("采集日志", 2), ("修复配置", 3), ("HTTP 恢复", 4), ("服务清理", 3)]),
    "B": ("tmux 会话", [("分离的会话", 4), ("日志持续增长", 4), ("停止与清理", 2)]),
}
HELLO = '#!/bin/bash\necho "Hello, AIM Linux!"\n'
CONFIG = "robot=sentry\nmode=training\nlog_level=INFO\n"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def text(path):
    require(path.is_file() and not path.is_symlink(), f"缺少普通文件：{path.name}")
    require(not any(parent.is_symlink() for parent in path.parents), "产物父目录不能是符号链接")
    require(path.stat().st_size <= 1_000_000, "文本产物超过 1 MB")
    return path.read_text(encoding="utf-8")


def equal(path, expected):
    actual = text(path)
    require(actual == expected, f"{path.name} 内容不符：期望 {expected[:180]!r}，得到 {actual[:180]!r}")


def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            result[relative] = ("link", os.readlink(path))
        elif path.is_dir():
            result[relative] = ("dir", path.stat().st_mode & 0o777)
        else:
            result[relative] = ("file", path.stat().st_mode & 0o777, path.read_bytes())
    return result


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(predicate, message, seconds=4):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError(message)


def env_file(path, values):
    path.write_text("".join(f"{key}={shlex.quote(str(value))}\n" for key, value in values.items()))


def pid_running(pid):
    try:
        state = Path(f"/proc/{pid}/stat").read_text().split(")", 1)[1].split()[0]
        return state != "Z"
    except FileNotFoundError:
        return False


class Case:
    def __init__(self, runtime, question, name):
        self.runtime = runtime
        self.question = question
        self.name = name
        self.root = runtime.base / f"{question} {name}"
        self.input = self.root / "input materials"
        self.output = self.root / "output results"
        self.state = self.root / "runtime"
        for folder in (self.root, self.input, self.output, self.state):
            folder.mkdir()
            folder.chmod(0o755)
        for folder in (self.output, self.state):
            os.chown(folder, runtime.uid, runtime.gid)
        self.error = None
        self.pending = False
        self.observations = {}
        self.processes = []

    def write(self, relative, content):
        path = self.input / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o644)
        return path

    def execute(self, action=None):
        script = "bonus.sh" if self.question == "B" else f"{self.question.lower()}.sh"
        args = ["bash", str(self.runtime.submission / script), str(self.input), str(self.output)]
        if action is not None:
            args.append(action)
        before = snapshot(self.input)
        result = self.runtime.student(args, cwd=self.output, timeout=15)
        self.runtime.record(self, action or "run", result)
        if result.returncode == 77:
            self.pending = True
            return
        require(result.returncode == 0, f"脚本退出 {result.returncode}：{result.stderr[-600:]}")
        require(snapshot(self.input) == before, "输入素材被修改")

    def twice(self):
        self.execute()
        if self.pending:
            return
        before = snapshot(self.output)
        if self.question == "Q6":
            before = {k: v for k, v in before.items() if not k.startswith("sysroot/var/lib/dpkg/")}
        self.execute()
        after = snapshot(self.output)
        if self.question == "Q6":
            after = {k: v for k, v in after.items() if not k.startswith("sysroot/var/lib/dpkg/")}
        require(after == before, "第二次运行改变了产物内容、结构或权限")

    def launch(self, args, log_name):
        log = open(self.state / log_name, "w")
        proc = self.runtime.spawn_student(args, cwd=self.state, stdout=log, stderr=log)
        log.close()
        self.processes.append(proc)
        return proc

    def close(self):
        for proc in self.processes:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=2)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    if proc.poll() is None:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()


def simple_case(runtime, q, variant):
    case = Case(runtime, q, variant)
    if q == "Q1":
        case.write("handover/.robot-id", f"SENTRY-{variant.upper()}\n")
        case.write("handover/README.txt", "AIM developer handover\n")
        case.write("notes/welcome.txt", "Welcome to AIM.\nRead before changing files.\n" if variant == "normal" else "Welcome, rookie!\nDifferent input.\n")
    elif q == "Q3":
        case.write("hello.sh", HELLO)
        case.write("robot.conf", CONFIG + f"revision={variant}\n")
        case.write("draft.conf", f"mode=draft\nowner={variant}\n")
        case.write("tmp/cache.txt", "temporary\n")
        # Pre-existing output cache makes skipping the deletion observably wrong.
        cache = case.output / "sentry_ws/tmp/cache.txt"
        cache.parent.mkdir(parents=True)
        cache.write_text("previous run cache\n")
        for path in [case.output / "sentry_ws", *list((case.output / "sentry_ws").rglob("*"))]:
            os.chown(path, runtime.uid, runtime.gid)
    elif q == "Q4":
        datasets = {
            "normal": (
                "INFO 09:00:00 launcher startup complete\nWARN 09:00:01 camera frame delayed\nERROR 09:00:02 camera device unavailable\n",
                "INFO 09:00:03 launcher previous ERROR has been handled\nERROR 09:00:04 nav lost position\nWARN 09:00:05 nav retry\nERROR 09:00:06 nav timeout\nERROR 09:00:06 nav timeout\nERROR 09:00:07 launcher exit\n"),
            "no-errors": ("INFO 10:00:00 launcher ERROR is only a message\n", "WARN 10:00:01 camera delayed\n"),
            "empty": ("", ""),
            "short": ("ERROR 11:00:00 camera ERROR repeated in message\n", "ERROR 11:00:01 nav stopped\n"),
        }
        boot, run = datasets[variant]
        case.write("boot.log", boot)
        case.write("run.log", run)
    elif q == "Q5":
        old_port, level = (9000, "DEBUG") if variant == "normal" else (12001, "WARN")
        case.write("robot.conf", f"# AIM handover\n# port={old_port}\n\nrobot=sentry\nport={old_port}\nbackup_port={old_port}\n# log_level={level}\nlog_level={level}\nowner={variant}\n")
        case.write("tools.env", f"CHECK_TOOL={shlex.quote(str(runtime.tools / 'check-config.sh'))}\n")
    elif q == "Q6":
        version = "1.0.0" if variant == "normal" else "1.1.0"
        stage = case.root / "package staging"
        (stage / "DEBIAN").mkdir(parents=True)
        (stage / "usr/bin").mkdir(parents=True)
        (stage / "DEBIAN/control").write_text(f"Package: aim-sentry-tools\nVersion: {version}\nArchitecture: all\nMaintainer: AIM <training@example.invalid>\nDescription: Offline Linux training utility\n")
        binary = stage / "usr/bin/aim-sentry-info"
        binary.write_text(f"#!/bin/bash\nprintf '%s\\n' 'SENTRY TOOL {version}'\n")
        binary.chmod(0o755)
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(stage), str(case.input / "aim-sentry-tools.deb")], check=True, capture_output=True)
        case.observations["version"] = version
    try:
        case.twice()
    except Exception as exc:
        case.error = str(exc)
    return case


def ssh_case(runtime, variant):
    case = Case(runtime, "Q7", variant)
    server = None
    try:
        port = free_port()
        hostkey, key = case.state / "host_key", case.input / "client_key"
        for path in (hostkey, key):
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path)], check=True)
        # Readable only to root and the student's private group; student cannot alter it.
        os.chown(key, 0, runtime.gid)
        key.chmod(0o440)
        case.state.chmod(0o755)
        os.chown(case.state, 0, 0)
        remote_ssh = Path(pwd.getpwnam(runtime.remote_user).pw_dir) / ".ssh"
        remote_ssh.mkdir(exist_ok=True)
        remote_ssh.chmod(0o700)
        os.chown(remote_ssh, runtime.remote_uid, runtime.remote_gid)
        authorized = remote_ssh / "authorized_keys"
        authorized.write_bytes(Path(str(key) + ".pub").read_bytes())
        authorized.chmod(0o600)
        os.chown(authorized, runtime.remote_uid, runtime.remote_gid)
        remote_log = case.state / "remote-private.log"
        remote_log.write_text(f"ERROR 12:00:00 nav remote-{variant}\nnonce={hashlib.sha256(str(case.root).encode()).hexdigest()[:20]}\n")
        os.chown(remote_log, runtime.remote_uid, runtime.remote_gid)
        remote_log.chmod(0o600)
        pub = Path(str(hostkey) + ".pub").read_text().split()
        known = case.write("known_hosts", f"[127.0.0.1]:{port} {pub[0]} {pub[1]}\n")
        env_file(case.input / "remote.env", {
            "HOST": "127.0.0.1", "PORT": port, "REMOTE_USER": runtime.remote_user,
            "KEY_PATH": key, "KNOWN_HOSTS": known, "REMOTE_LOG": remote_log,
        })
        config = case.state / "sshd_config"
        config.write_text(f'Port {port}\nListenAddress 127.0.0.1\nHostKey "{hostkey}"\nPidFile "{case.state / "sshd.pid"}"\nAuthorizedKeysFile "{authorized}"\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPubkeyAuthentication yes\nPermitRootLogin no\nUsePAM no\nStrictModes yes\nAllowUsers {runtime.remote_user}\nLogLevel VERBOSE\nSubsystem sftp internal-sftp\n')
        server = subprocess.Popen(["/usr/sbin/sshd", "-D", "-e", "-f", str(config)], stdout=open(case.state / "sshd.out", "w"), stderr=open(case.state / "sshd.log", "w"), start_new_session=True)
        case.processes.append(server)
        def listening():
            with socket.socket() as sock:
                sock.settimeout(0.1)
                return sock.connect_ex(("127.0.0.1", port)) == 0
        wait_for(listening, "教师 SSH 服务启动失败")
        case.execute()
        if not case.pending:
            cfg = case.output / "ssh_config"
            resolved = runtime.student(["ssh", "-G", "-F", str(cfg), "aim-sentry"])
            require(resolved.returncode == 0, "无法解析输出的 ssh_config")
            case.observations["ssh_config"] = resolved.stdout
            remote = runtime.student(["ssh", "-F", str(cfg), "-o", "BatchMode=yes", "-o", "ConnectTimeout=3", "aim-sentry", "whoami"], timeout=5)
            case.observations["connection"] = remote
            case.observations["auth_log"] = (case.state / "sshd.log").read_text()
            case.observations["expected_log"] = remote_log.read_text()
    except Exception as exc:
        case.error = str(exc)
    finally:
        case.close()
    return case


def process_case(runtime, variant):
    case = Case(runtime, "Q8", variant)
    try:
        worker_log, decoy_log = case.state / "collector.log", case.state / "other.log"
        token = f"aim-{variant}-{case.root.name.replace(' ', '-')}"
        worker = case.launch(["python3", str(runtime.tools / "worker.py"), "--token", token, "--log", str(worker_log)], "collector.stdout")
        decoy = case.launch(["python3", str(runtime.tools / "worker.py"), "--token", token + "-other", "--log", str(decoy_log)], "other.stdout")
        wait_for(lambda: worker_log.exists() and worker_log.read_text().count("TICK") >= 2, "采集器未就绪")
        port, wrong = free_port(), free_port()
        while wrong == port:
            wrong = free_port()
        initial = f"bind=127.0.0.1\nport={wrong if variant == 'wrong-port' else port}\nroute={'/status' if variant == 'wrong-port' else '/old-status'}\n"
        config = case.write("server.conf", initial)
        old = case.launch(["python3", str(runtime.tools / "service.py"), str(config)], "old-service.log")
        wait_for(lambda: "LISTEN " in (case.state / "old-service.log").read_text(), "教师 HTTP 服务未就绪")
        env_file(case.input / "process.env", {
            "TARGET_PID": worker.pid, "TARGET_TOKEN": token, "WORKER_LOG": worker_log,
            "SERVICE_PID": old.pid, "TARGET_PORT": port, "START_TOOL": runtime.tools / "start-service.sh",
        })
        case.observations.update(pid=worker.pid, token=token, target_port=port)
        case.execute("repair")
        if case.pending:
            return case
        case.observations["stopped"] = not pid_running(worker.pid)
        case.observations["graceful"] = f"STOP {token}\n" in worker_log.read_text()
        case.observations["decoy_alive"] = pid_running(decoy.pid)
        case.observations["old_stopped"] = not pid_running(old.pid)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(f"http://127.0.0.1:{port}/status", timeout=2) as response:
                case.observations["http"] = (response.status, response.read().decode())
        except (OSError, urllib.error.URLError) as exc:
            case.observations["http"] = str(exc)
        try:
            case.execute("cleanup")
            wait_for(lambda: not tcp_open(port), "cleanup 后服务仍在监听")
            case.observations["cleanup"] = True
        except Exception as exc:
            case.observations["cleanup"] = str(exc)
    except Exception as exc:
        case.error = str(exc)
    finally:
        case.close()
    return case


def tcp_open(port):
    with socket.socket() as sock:
        sock.settimeout(0.1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def bonus_case(runtime):
    case = Case(runtime, "B", "session")
    socket_name = f"aim-{os.getpid()}"
    name = "aim-debug"
    token = f"bonus-{os.getpid()}"
    try:
        env_file(case.input / "bonus.env", {"TMUX_SOCKET": socket_name, "SESSION": name, "TOKEN": token, "WORKER_TOOL": runtime.tools / "worker.py"})
        case.execute("start")
        if case.pending:
            return case
        listing = runtime.student(["tmux", "-L", socket_name, "display-message", "-p", "-t", name, "#{session_attached}"])
        case.observations["detached"] = listing.returncode == 0 and listing.stdout.strip() == "0"
        log = case.output / "bonus.log"
        wait_for(lambda: log.exists() and log.read_text().count("TICK") >= 2, "tmux 内采集器未产生日志")
        first = log.read_text()
        time.sleep(0.45)
        later = log.read_text()
        case.observations["growth"] = later.count("TICK") > first.count("TICK")
        starts = [line for line in later.splitlines() if line.startswith(f"START {token} pid=")]
        require(len(starts) == 1, "应仅有一个采集器实例")
        pid = int(starts[0].split("pid=")[1])
        case.execute("stop")
        wait_for(lambda: not pid_running(pid), "stop 后采集器仍在运行")
        exists = runtime.student(["tmux", "-L", socket_name, "has-session", "-t", name])
        case.observations["cleanup"] = exists.returncode != 0 and f"STOP {token}\n" in log.read_text()
    except Exception as exc:
        case.error = str(exc)
    finally:
        runtime.student(["tmux", "-L", socket_name, "kill-server"])
    return case


def assert_check(case, index):
    q, inp, out, obs = case.question, case.input, case.output, case.observations
    if q == "Q1":
        checks = [lambda: equal(out / "location.txt", str(inp / "handover") + "\n"), lambda: equal(out / "robot-id.txt", text(inp / "handover/.robot-id")), lambda: equal(out / "welcome.txt", text(inp / "notes/welcome.txt"))]
    elif q == "Q2":
        ws = out / "sentry_ws"
        checks = [lambda: require(all((ws / p).is_dir() and not (ws / p).is_symlink() for p in ("scripts", "config", "logs", "tmp")), "缺少目标目录"), lambda: (equal(ws / "logs/.keep", ""), equal(ws / "tmp/scratch.txt", "")), lambda: equal(ws / "scripts/hello.sh", HELLO), lambda: equal(ws / "config/robot.conf", CONFIG)]
    elif q == "Q3":
        ws = out / "sentry_ws"
        checks = [lambda: (equal(ws / "scripts/hello.sh", HELLO), equal(ws / "config/robot.conf", text(inp / "robot.conf")), equal(ws / "backup/robot.conf", text(inp / "robot.conf"))), lambda: (equal(ws / "archive/draft.conf.old", text(inp / "draft.conf")), require(not (ws / "config/draft.conf").exists(), "草稿源位置仍存在")), lambda: require(not (ws / "tmp").exists(), "tmp 未删除"), lambda: require((ws / "scripts/hello.sh").stat().st_mode & 0o777 == 0o750 and (ws / "config/robot.conf").stat().st_mode & 0o777 == 0o640, "权限不是 750/640"), lambda: (equal(out / "hello-output.txt", "Hello, AIM Linux!\n"), require(case.runtime.student([str(ws / "scripts/hello.sh")]).stdout == "Hello, AIM Linux!\n", "脚本不能直接执行"))]
    elif q == "Q4":
        all_lines = (text(inp / "boot.log") + text(inp / "run.log")).splitlines(keepends=True)
        errors = [line for line in all_lines if line.startswith("ERROR ")]
        attention = [line for line in all_lines if line.startswith(("WARN ", "ERROR "))]
        expected = [("all.log", "".join(all_lines)), ("errors.log", "".join(errors)), ("attention.log", "".join(attention)), ("recent.log", "".join(all_lines[-5:])), ("first-errors.log", "".join(errors[:3])), ("error-count.txt", f"{len(errors)}\n")]
        filename, content = expected[index]
        equal(out / filename, content)
        return
    elif q == "Q5":
        original = text(inp / "robot.conf")
        actual = lambda: text(out / "robot.conf")
        preserve = lambda data: "".join(line for line in data.splitlines(keepends=True) if not line.startswith(("port=", "log_level=")))
        checks = [lambda: equal(out / "robot.conf.bak", original), lambda: require([line for line in actual().splitlines() if line.startswith("port=")] == ["port=8080"], "有效端口未精确修改"), lambda: require([line for line in actual().splitlines() if line.startswith("log_level=")] == ["log_level=INFO"], "有效日志等级未修改"), lambda: require(preserve(actual()) == preserve(original), "其他配置、注释或空行改变"), lambda: (equal(out / "check.out", "CONFIG OK\n"), equal(out / "check.err", "NOTICE: training check only\n"))]
    elif q == "Q6":
        root = out / "sysroot"
        query = subprocess.run(["dpkg-query", f"--admindir={root / 'var/lib/dpkg'}", "-W", "-f=${Status}|${Version}\n", "aim-sentry-tools"], capture_output=True, text=True)
        expected = f"SENTRY TOOL {obs['version']}\n"
        checks = [lambda: require(query.returncode == 0 and query.stdout == f"install ok installed|{obs['version']}\n", "dpkg 数据库没有记录正确的已安装版本"), lambda: (require(case.runtime.student([str(root / "usr/bin/aim-sentry-info")]).stdout == expected, "安装产物无法运行"), equal(out / "tool-output.txt", expected))]
    elif q == "Q7":
        resolved = obs.get("ssh_config", "")
        config = text(out / "ssh_config")
        conn = obs.get("connection")
        checks = [lambda: require("host aim-sentry" in resolved and "stricthostkeychecking true" in resolved and "identitiesonly yes" in resolved and str(inp / "known_hosts") in resolved and str(inp / "client_key") in resolved and "Host aim-sentry" in config and (out / "ssh_config").stat().st_mode & 0o777 == 0o600, "别名、密钥、已知主机或权限配置不符"), lambda: (equal(out / "remote-user.txt", case.runtime.remote_user + "\n"), require(conn is not None and conn.returncode == 0 and conn.stdout == case.runtime.remote_user + "\n", "教师复连失败"), require("Accepted publickey" in obs.get("auth_log", ""), "未验证公钥认证")), lambda: (equal(out / "received/errors.log", obs["expected_log"]), require("subsystem 'sftp'" in obs.get("auth_log", "") or "command 'scp " in obs.get("auth_log", ""), "服务端没有文件传输会话"))]
    elif q == "Q8":
        def identification():
            data = text(out / "process.txt")
            values = dict(line.split("=", 1) for line in data.splitlines())
            require(values.get("pid") == str(obs["pid"]) and values.get("user") == case.runtime.user and values.get("state", "")[:1] in "RS" and obs["token"] in values.get("command", ""), "process.txt 中 PID、所有者、状态或命令行不符")
        checks = [identification, lambda: require(obs.get("stopped") and obs.get("graceful"), "采集器未正常终止，或没有 STOP 记录"), lambda: require(obs.get("decoy_alive"), "误杀了另一个采集器"), lambda: require(text(out / "collector-sample.log").count(f"TICK {obs['token']} ") >= 2, "至少保存两条目标采集器日志"), lambda: (equal(out / "server.conf", f"bind=127.0.0.1\nport={obs['target_port']}\nroute=/status\n"), require(obs.get("old_stopped"), "原错误服务没有停止")), lambda: (require(obs.get("http") == (200, "SENTRY READY\n"), f"教师实际请求失败：{obs.get('http')}"), equal(out / "http-status.txt", "200\n"), equal(out / "http-body.txt", "SENTRY READY\n")), lambda: require(obs.get("cleanup") is True and not tcp_open(obs["target_port"]), f"服务清理失败：{obs.get('cleanup')}")]
    else:
        checks = [lambda: require(obs.get("detached"), "指定 tmux 会话不存在或仍有客户端附着"), lambda: require(obs.get("growth"), "脚本返回后日志没有继续增长"), lambda: require(obs.get("cleanup"), "会话或采集器没有清理")]
    checks[index]()


def evaluate(runtime, selected):
    results = []
    for q in selected:
        title, criteria = TASKS[q]
        runtime.progress(f"{q} {title}")
        if q == "Q7":
            cases = [ssh_case(runtime, name) for name in ("normal", "changed")]
        elif q == "Q8":
            cases = [process_case(runtime, name) for name in ("wrong-port", "wrong-route")]
        elif q == "B":
            cases = [bonus_case(runtime)]
        else:
            variants = ("normal", "no-errors", "empty", "short") if q == "Q4" else ("normal", "changed")
            cases = [simple_case(runtime, q, name) for name in variants]
        checks = []
        for index, (label, weight) in enumerate(criteria):
            errors = []
            pending = any(case.pending for case in cases)
            for case in cases:
                if case.pending:
                    continue
                try:
                    require(case.error is None, case.error)
                    assert_check(case, index)
                except Exception as exc:
                    errors.append(f"{case.name}: {exc}")
            status = "failed" if errors else "pending" if pending else "passed"
            checks.append({"name": label, "max_points": weight, "points": weight if status == "passed" else 0, "status": status, "feedback": "\n".join(errors) if errors else "尚未实现" if pending else "全部公开场景通过"})
        result = {"question": q, "title": title, "points": sum(c["points"] for c in checks), "max_points": sum(c["max_points"] for c in checks), "status": "passed" if all(c["status"] == "passed" for c in checks) else "pending" if all(c["status"] == "pending" for c in checks) else "failed", "checks": checks}
        results.append(result)
        runtime.progress(f"  {result['status']}: {result['points']}/{result['max_points']}")
        for case in cases:
            runtime.archive(case)
            case.close()
    return results
