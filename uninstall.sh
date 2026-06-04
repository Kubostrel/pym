#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  pym uninstaller
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DEST="/usr/local/bin/pym"
PYM_DIR="${PYM_HOME:-$HOME/.pym}"

echo ""
echo "  pym — Uninstaller"
echo ""

# Stop all running processes first
if command -v pym &>/dev/null && [[ -f "$PYM_DIR/config.json" ]]; then
    echo "  Stopping all pym processes…"
    pym stop all 2>/dev/null || true
fi

# Remove the binary
if [[ -f "$DEST" ]]; then
    if [[ $EUID -eq 0 ]]; then
        rm -f "$DEST"
    else
        sudo rm -f "$DEST"
    fi
    echo "  ✓ Removed $DEST"
else
    echo "  ○ $DEST not found (already removed?)"
fi

# Optionally remove data directory
echo ""
read -rp "  Remove data directory $PYM_DIR ? [y/N] " choice
if [[ "${choice,,}" == "y" ]]; then
    rm -rf "$PYM_DIR"
    echo "  ✓ Removed $PYM_DIR"
else
    echo "  ○ Kept $PYM_DIR"
fi

echo ""
echo "  pym uninstalled."
echo ""
