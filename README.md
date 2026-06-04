# pym — Python Process Manager

Like PM2, but for Python scripts. Run and manage multiple Python processes on Ubuntu Server.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Kubostrel/pym/main/install.sh | bash
```

Or with wget:

```bash
wget -qO- https://raw.githubusercontent.com/Kubostrel/pym/main/install.sh | bash
```

## Commands

```bash
pym add <name>       # Create & start a new Python process
pym edit <name>      # Edit script in $EDITOR, then restart
pym stop <name>      # Stop a running process
pym stop all         # Stop every process
pym delete <name>    # Stop + remove script, logs, config entry
pym status           # List all processes with live status
pym logs <name>      # Tail live logs (Ctrl+C to quit)
```

## Quick start

```bash
pym add mybot        # opens nano — write your code, save, done
pym status           # NAME   STATUS     PID    UPTIME   RESTARTS
pym logs mybot       # live output stream
pym stop mybot       # pause
pym edit mybot       # change code → auto-restart
pym delete mybot     # remove completely
```

## Features

- **Auto-restart on crash** — like PM2, processes come back automatically
- Scripts stored in `~/.pym/scripts/<name>.py`
- Logs stored in `~/.pym/logs/<name>.log`
- Set `$EDITOR` to use vim, micro, etc. (default: nano)
- Set `$PYM_HOME` to change the data directory

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/Kubostrel/pym/main/uninstall.sh | bash
```

## Requirements

- Ubuntu Server (18.04+)
- Python 3.6+
- bash
