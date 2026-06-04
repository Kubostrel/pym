#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  pym installer
#  GitHub: https://github.com/Kubostrel/pym
#
#  Local:   bash install.sh
#  Remote:  curl -fsSL https://raw.githubusercontent.com/Kubostrel/pym/main/install.sh | bash
#           wget -qO- https://raw.githubusercontent.com/Kubostrel/pym/main/install.sh | bash
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

GITHUB_USER="Kubostrel"
GITHUB_REPO="pym"
GITHUB_BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"

DEST="/usr/local/bin/pym"
TMP_PY="/tmp/pym_$$.py"

echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  pym — Python Process Manager   │"
echo "  │         Installer v1.0          │"
echo "  │   github.com/Kubostrel/pym      │"
echo "  └─────────────────────────────────┘"
echo ""

# ── Check python3 ─────────────────────────────────────────────────────────────
PY=$(command -v python3 2>/dev/null || true)
if [[ -z "$PY" ]]; then
    echo "  ✗ python3 not found. Install it first:"
    echo "      sudo apt install python3"
    exit 1
fi

# ── Get pym.py: use local file if present, otherwise download ─────────────────
LOCAL_PY="$(cd "$(dirname "${BASH_SOURCE[0]:-/}")" 2>/dev/null && pwd)/pym.py"

if [[ -f "$LOCAL_PY" ]]; then
    echo "  ○ Using local file: $LOCAL_PY"
    SRC="$LOCAL_PY"
else
    echo "  ↓ Downloading pym.py from GitHub..."
    if command -v curl &>/dev/null; then
        curl -fsSL "${RAW_BASE}/pym.py" -o "$TMP_PY"
    elif command -v wget &>/dev/null; then
        wget -qO "$TMP_PY" "${RAW_BASE}/pym.py"
    else
        echo "  ✗ curl or wget is required"
        exit 1
    fi
    SRC="$TMP_PY"
    echo "  ✓ Downloaded"
fi

echo "  Python : $($PY --version)"
echo "  Target : $DEST"
echo ""

# ── Install ───────────────────────────────────────────────────────────────────
_do_install() {
    cp "$1" "$2"
    chmod +x "$2"
}

if [[ $EUID -eq 0 ]]; then
    _do_install "$SRC" "$DEST"
else
    echo "  → Needs sudo to write to $DEST"
    sudo bash -c "_do_install() { cp \"\$1\" \"\$2\"; chmod +x \"\$2\"; }; _do_install '$SRC' '$DEST'"
fi

[[ -f "$TMP_PY" ]] && rm -f "$TMP_PY"

# ── Verify ────────────────────────────────────────────────────────────────────
if command -v pym &>/dev/null; then
    echo "  ✓ pym installed successfully!"
    echo ""
    echo "  Get started:"
    echo "    pym add mybot      # create & start your first process"
    echo "    pym status         # view all running processes"
    echo "    pym logs mybot     # tail live output"
    echo ""
else
    echo "  ✓ File copied — but $DEST is not in your \$PATH."
    echo "    Add this to ~/.bashrc:"
    echo "      export PATH=\"/usr/local/bin:\$PATH\""
    echo "    Then run: source ~/.bashrc"
    echo ""
fi
