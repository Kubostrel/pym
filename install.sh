#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  pym installer — работает и локально, и через curl/wget
#
#  Локально:    bash install.sh
#  Удалённо:    curl -fsSL https://raw.githubusercontent.com/YOUR/pym/main/install.sh | bash
#               wget -qO- https://raw.githubusercontent.com/YOUR/pym/main/install.sh | bash
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Поменяй на свой репозиторий ───────────────────────────────────────────────
GITHUB_USER="YOUR_USERNAME"
GITHUB_REPO="pym"
GITHUB_BRANCH="main"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"
# ─────────────────────────────────────────────────────────────────────────────

DEST="/usr/local/bin/pym"
TMP_PY="/tmp/pym_$$.py"

echo ""
echo "  ┌─────────────────────────────────┐"
echo "  │  pym — Python Process Manager   │"
echo "  │         Installer v1.0          │"
echo "  └─────────────────────────────────┘"
echo ""

# ── Проверка python3 ──────────────────────────────────────────────────────────
PY=$(command -v python3 2>/dev/null || true)
if [[ -z "$PY" ]]; then
    echo "  ✗ python3 не найден. Установи:"
    echo "      sudo apt install python3"
    exit 1
fi

# ── Получаем pym.py: сначала ищем рядом, иначе скачиваем ─────────────────────
LOCAL_PY="$(cd "$(dirname "${BASH_SOURCE[0]:-/}")" 2>/dev/null && pwd)/pym.py"

if [[ -f "$LOCAL_PY" ]]; then
    echo "  ○ Использую локальный файл: $LOCAL_PY"
    SRC="$LOCAL_PY"
else
    echo "  ↓ Скачиваю pym.py с GitHub…"
    if command -v curl &>/dev/null; then
        curl -fsSL "${RAW_BASE}/pym.py" -o "$TMP_PY"
    elif command -v wget &>/dev/null; then
        wget -qO "$TMP_PY" "${RAW_BASE}/pym.py"
    else
        echo "  ✗ Нужен curl или wget"
        exit 1
    fi
    SRC="$TMP_PY"
    echo "  ✓ Скачано"
fi

echo "  Python : $($PY --version)"
echo "  Target : $DEST"
echo ""

# ── Установка ─────────────────────────────────────────────────────────────────
_install() {
    cp "$1" "$2"
    chmod +x "$2"
}

if [[ $EUID -eq 0 ]]; then
    _install "$SRC" "$DEST"
else
    echo "  → Нужен sudo для записи в $DEST"
    sudo bash -c "_install() { cp \"\$1\" \"\$2\"; chmod +x \"\$2\"; }; _install '$SRC' '$DEST'"
fi

# Удаляем временный файл если скачивали
[[ -f "$TMP_PY" ]] && rm -f "$TMP_PY"

# ── Проверка ──────────────────────────────────────────────────────────────────
if command -v pym &>/dev/null; then
    echo "  ✓ pym успешно установлен!"
    echo ""
    echo "  Начало работы:"
    echo "    pym add mybot      # создать и запустить процесс"
    echo "    pym status         # список всех процессов"
    echo "    pym logs mybot     # живые логи"
    echo ""
else
    echo "  ✓ Файл скопирован — но $DEST не в \$PATH."
    echo "    Добавь в ~/.bashrc:"
    echo "      export PATH=\"/usr/local/bin:\$PATH\""
    echo "    Затем: source ~/.bashrc"
    echo ""
fi
