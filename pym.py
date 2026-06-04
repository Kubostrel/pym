#!/usr/bin/env python3
"""
pym — Python Process Manager
Like PM2, but for Python scripts on Ubuntu Server.
"""

import os, sys, json, signal, subprocess, time, datetime, textwrap
from pathlib import Path

# ── ANSI colors ───────────────────────────────────────────────────────────────
RESET  = "\033[0m";  BOLD   = "\033[1m"
GREEN  = "\033[92m"; RED    = "\033[91m"
YELLOW = "\033[93m"; CYAN   = "\033[96m"; GREY = "\033[90m"

def green(s):  return f"{GREEN}{s}{RESET}"
def red(s):    return f"{RED}{s}{RESET}"
def yellow(s): return f"{YELLOW}{s}{RESET}"
def cyan(s):   return f"{CYAN}{s}{RESET}"
def grey(s):   return f"{GREY}{s}{RESET}"
def bold(s):   return f"{BOLD}{s}{RESET}"

# ── Directory layout ──────────────────────────────────────────────────────────
PYM_DIR     = Path(os.environ.get("PYM_HOME", Path.home() / ".pym"))
SCRIPTS_DIR = PYM_DIR / "scripts"
LOGS_DIR    = PYM_DIR / "logs"
PIDS_DIR    = PYM_DIR / "pids"
CONFIG_FILE = PYM_DIR / "config.json"

def ensure_dirs():
    for d in (PYM_DIR, SCRIPTS_DIR, LOGS_DIR, PIDS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        _write_config({})

def _read_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}

def _write_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, default=str))

# ── Path helpers ──────────────────────────────────────────────────────────────
def _pid_file(name):     return PIDS_DIR  / f"{name}.pid"
def _log_file(name):     return LOGS_DIR  / f"{name}.log"
def _script_file(name):  return SCRIPTS_DIR / f"{name}.py"
def _wrapper_file(name): return PIDS_DIR  / f"_{name}_wrapper.sh"

def _get_pid(name) -> "int | None":
    try:
        return int(_pid_file(name).read_text().strip())
    except Exception:
        return None

def _is_alive(pid) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def _uptime(iso: str) -> str:
    try:
        delta = datetime.datetime.now() - datetime.datetime.fromisoformat(iso)
        s = int(delta.total_seconds())
        if s < 60:    return f"{s}s"
        if s < 3600:  return f"{s//60}m {s%60}s"
        if s < 86400: return f"{s//3600}h {(s%3600)//60}m"
        return f"{s//86400}d {(s%86400)//3600}h"
    except Exception:
        return "?"

# ── Bash wrapper template (auto-restart on crash) ─────────────────────────────
_WRAPPER = """\
#!/usr/bin/env bash
# pym auto-restart wrapper for: {name}
SCRIPT="{script}"
LOG="{log}"

log() {{ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }}

log "=== process started (PID $$) ==="

RESTARTS=0
while true; do
    python3 -u "$SCRIPT" >> "$LOG" 2>&1
    EC=$?
    RESTARTS=$((RESTARTS + 1))
    log "=== exited (code $EC, restart #$RESTARTS) — waiting 3s... ==="
    sleep 3
done
"""

# ── Start / stop ──────────────────────────────────────────────────────────────
def _start(name: str, cfg: dict) -> bool:
    script = _script_file(name)
    if not script.exists():
        print(red(f"  ✗ script not found: {script}"))
        return False

    log     = _log_file(name)
    wrapper = _wrapper_file(name)

    # Write the auto-restart shell wrapper
    wrapper.write_text(_WRAPPER.format(name=name, script=script, log=log))
    wrapper.chmod(0o755)

    # Append separator to log
    with log.open("a") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'━'*52}\n[{ts}] pym start\n{'━'*52}\n")

    proc = subprocess.Popen(
        ["/bin/bash", str(wrapper)],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _pid_file(name).write_text(str(proc.pid))

    cfg[name] = {
        "name":       name,
        "started_at": datetime.datetime.now().isoformat(),
        "restarts":   cfg.get(name, {}).get("restarts", 0),
    }
    _write_config(cfg)
    print(green(f"  ✓ [{name}]") + f" started  " + grey(f"(pid {proc.pid})"))
    return True


def _stop(name: str):
    pid = _get_pid(name)

    if pid and _is_alive(pid):
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            for _ in range(8):          # wait up to ~2.4s
                if not _is_alive(pid):
                    break
                time.sleep(0.3)
            if _is_alive(pid):
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except OSError:
            pass
        print(yellow(f"  ⏹  [{name}]") + " stopped")
    else:
        print(grey(f"  ○  [{name}] was not running"))

    for f in (_pid_file(name), _wrapper_file(name)):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


# ── Commands ──────────────────────────────────────────────────────────────────
_STARTER_TEMPLATE = """\
# {name}.py  ── managed by pym
# Edit this file and save.  pym will start/restart the process automatically.

import time

def main():
    print("Hello from {name}!")
    # Your code here
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
"""

def do_add(name: str):
    if not all(c.isalnum() or c in "-_" for c in name) or not name:
        print(red("  ✗ Name may only contain letters, digits, hyphens and underscores."))
        sys.exit(1)

    cfg = _read_config()
    if name in cfg:
        print(yellow(f"  ! '{name}' already exists.") +
              f"  Use {cyan('pym edit ' + name)} to edit it.")
        return

    script = _script_file(name)
    script.write_text(_STARTER_TEMPLATE.format(name=name))

    editor = os.environ.get("EDITOR", "nano")
    print(grey(f"  ↗  Opening {editor} — save & exit to start '{name}'."))
    subprocess.run([editor, str(script)])

    print(f"\n  Starting {bold(name)} …")
    _start(name, cfg)


def do_edit(name: str):
    cfg = _read_config()
    if name not in cfg:
        print(red(f"  ✗ '{name}' not found.") +
              f"  Use {cyan('pym add ' + name)} to create it.")
        return

    editor = os.environ.get("EDITOR", "nano")
    print(grey(f"  ↗  Opening {editor} — save & exit to restart '{name}'."))
    subprocess.run([editor, str(_script_file(name))])

    pid = _get_pid(name)
    if pid and _is_alive(pid):
        print(f"\n  Restarting {bold(name)} …")
        _stop(name)
    else:
        print(f"\n  Starting {bold(name)} …")

    cfg[name]["restarts"] = cfg[name].get("restarts", 0) + 1
    _start(name, cfg)


def do_stop(target: str):
    cfg = _read_config()
    if not cfg:
        print(grey("  No processes registered."))
        return
    if target == "all":
        print("  Stopping all processes…")
        for name in list(cfg):
            _stop(name)
    elif target in cfg:
        _stop(target)
    else:
        print(red(f"  ✗ '{target}' not found."))


def do_delete(name: str):
    cfg = _read_config()
    if name not in cfg:
        print(red(f"  ✗ '{name}' not found."))
        return

    _stop(name)

    for path in (_script_file(name), _log_file(name)):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    del cfg[name]
    _write_config(cfg)
    print(red(f"  ✗ [{name}]") + " deleted")


def do_status():
    cfg = _read_config()

    print(f"\n  {bold('PYM')} {grey('─')} Python Process Manager\n")

    if not cfg:
        print(grey("  No processes yet. Run:  pym add <name>\n"))
        return

    W = [24, 12, 8, 12, 10]   # column widths (visible chars)
    headers = ["NAME", "STATUS", "PID", "UPTIME", "RESTARTS"]
    sep = "  " + grey("─" * (sum(W) + len(W) * 2))

    header_row = "  " + "  ".join(bold(h.ljust(w)) for h, w in zip(headers, W))
    print(header_row)
    print(sep)

    for name, info in cfg.items():
        pid   = _get_pid(name)
        alive = _is_alive(pid)

        # Build visible-width strings; colour codes don't count
        name_s    = name[:W[0]].ljust(W[0])
        if alive:
            status_v  = "● online"
            status_s  = green(status_v).ljust(W[1] + len(green("")) - len(status_v) + W[1])
        else:
            status_v  = "○ stopped"
            status_s  = red(status_v).ljust(W[1] + len(red("")) - len(status_v) + W[1])

        pid_s     = (str(pid) if alive else grey("—")).ljust(W[2])
        uptime_s  = (_uptime(info.get("started_at","")) if alive else grey("—")).ljust(W[3])
        restart_s = str(info.get("restarts", 0)).ljust(W[4])

        print(f"  {name_s}  {status_s}  {pid_s}  {uptime_s}  {restart_s}")

    print()


def do_logs(name: str):
    cfg = _read_config()
    if name not in cfg:
        print(red(f"  ✗ '{name}' not found."))
        return
    log = _log_file(name)
    if not log.exists():
        print(grey(f"  No logs yet for '{name}'"))
        return
    print(grey(f"  Logs for [{name}]  (Ctrl+C to exit)\n"))
    try:
        subprocess.run(["tail", "-n", "100", "-f", str(log)])
    except KeyboardInterrupt:
        print(grey("\n  ← exited log view"))


def do_help():
    print(f"""
  {bold('PYM')} — Python Process Manager  {grey('v1.0')}

  {bold('USAGE')}
    pym {cyan('add')} <name>        Create & start a new Python process
    pym {cyan('edit')} <name>       Edit script in $EDITOR, then restart
    pym {cyan('stop')} <name>       Stop a running process
    pym {cyan('stop')} all          Stop every process
    pym {cyan('delete')} <name>     Stop, remove script + logs + config entry
    pym {cyan('status')}            List all processes with live status
    pym {cyan('logs')} <name>       Tail live logs  (Ctrl+C to quit)

  {bold('FEATURES')}
    {green('●')} Processes {bold('auto-restart')} on crash (like PM2)
    {green('●')} Scripts are stored in   {grey('~/.pym/scripts/<name>.py')}
    {green('●')} Logs are stored in      {grey('~/.pym/logs/<name>.log')}
    {green('●')} Set $EDITOR env var to use vim / micro / etc.
    {green('●')} Set $PYM_HOME to change the data directory

  {bold('QUICK START')}
    pym add mybot          # create, edit and launch mybot
    pym status             # see all processes
    pym logs mybot         # watch live output
    pym stop mybot         # pause it
    pym edit mybot         # change code and hot-restart
    pym delete mybot       # remove completely
""")


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    ensure_dirs()
    argv = sys.argv[1:]

    NEEDS_ARG = {"add", "edit", "stop", "delete", "logs"}
    NO_ARG    = {"status"}

    if not argv or argv[0] not in (NEEDS_ARG | NO_ARG):
        do_help()
        return

    cmd = argv[0]

    if cmd in NEEDS_ARG:
        if len(argv) < 2:
            print(red(f"  ✗ '{cmd}' requires a name argument."))
            return
        arg = argv[1]
        {"add": do_add, "edit": do_edit, "stop": do_stop,
         "delete": do_delete, "logs": do_logs}[cmd](arg)
    else:
        do_status()


if __name__ == "__main__":
    main()
