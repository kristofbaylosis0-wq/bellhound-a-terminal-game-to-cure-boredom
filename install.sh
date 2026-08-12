#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/kristofbaylosis0-wq/idk.git"
INSTALL_DIR="${RPG_INSTALL_DIR:-$HOME/.local/share/text-rpg}"
BIN_DIR="${RPG_BIN_DIR:-$HOME/.local/bin}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10+ is required. Install Python and run this again."
  exit 1
fi

if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  mkdir -p "$(dirname "$INSTALL_DIR")"
  if command -v git >/dev/null 2>&1; then
    git clone "$REPO_URL" "$INSTALL_DIR"
  else
    echo "Git is required for the installer."
    exit 1
  fi
else
  git -C "$INSTALL_DIR" pull --ff-only
fi

cd "$INSTALL_DIR"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/RPG" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/boot.sh" "\$@"
EOF
chmod +x "$BIN_DIR/RPG" "$INSTALL_DIR/boot.sh"

echo
echo "RPG installed to: $INSTALL_DIR"
echo "Command: RPG"

echo "Starting the game..."
exec "$BIN_DIR/RPG" game
