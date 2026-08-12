#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/kristofbaylosis0-wq/idk.git"
INSTALL_ROOT="${HOME}/.local/share/text-rpg-chatgpt"
BIN_DIR="${HOME}/.local/bin"
RPG_COMMAND="${BIN_DIR}/RPG"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.10+ and run this again."
  exit 1
fi

mkdir -p "${HOME}/.local/share" "${BIN_DIR}"

if [[ -d "${INSTALL_ROOT}/.git" ]]; then
  echo "Updating existing RPG installation..."
  git -C "${INSTALL_ROOT}" pull --ff-only
else
  echo "Installing the RPG..."
  rm -rf "${INSTALL_ROOT}"
  git clone --depth 1 "${REPO_URL}" "${INSTALL_ROOT}"
fi

cd "${INSTALL_ROOT}"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

cat > "${RPG_COMMAND}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${INSTALL_ROOT}/.venv/bin/python" -m game "\$@"
EOF
chmod +x "${RPG_COMMAND}"

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *)
    echo ""
    echo "RPG was installed to ${RPG_COMMAND}."
    echo "Add ${BIN_DIR} to PATH if 'RPG' is not found in new shells."
    ;;
esac

echo ""
echo "Installation complete."
echo "Starting RPG..."
echo ""
exec "${RPG_COMMAND}" game
