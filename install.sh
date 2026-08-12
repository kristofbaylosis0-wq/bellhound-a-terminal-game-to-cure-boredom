#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/kristofbaylosis0-wq/idk.git"
INSTALL_ROOT="${HOME}/.local/share/text-rpg-chatgpt"
BIN_DIR="${HOME}/.local/bin"
RPG_COMMAND="${BIN_DIR}/RPG"

export PIP_DISABLE_PIP_VERSION_CHECK=1
export GIT_TERMINAL_PROMPT=0

step() { printf '  • %s\n' "$1"; }
done_step() { printf '  ✓ %s\n' "$1"; }
fail() {
  printf '\n  ✗ Installation failed.\n' >&2
  printf '    %s\n' "$1" >&2
  exit 1
}

printf '\n'
printf '  ╭──────────────────────────────────────────────╮\n'
printf '  │       A TEXT RPG GAME MADE BY CHATGPT       │\n'
printf '  ╰──────────────────────────────────────────────╯\n\n'
printf '  Installing RPG...\n\n'

step "Checking Python"
command -v python3 >/dev/null 2>&1 || fail "Python 3.10+ is required."
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || fail "Python 3.10+ is required."
done_step "Python 3.10+ found"

step "Preparing installation directory"
mkdir -p "${HOME}/.local/share" "${BIN_DIR}"
done_step "Installation directory ready"

if [[ -d "${INSTALL_ROOT}/.git" ]]; then
  step "Updating RPG"
  git -C "${INSTALL_ROOT}" fetch --depth 1 origin main >/dev/null 2>&1 || fail "Could not fetch the latest RPG version."
  git -C "${INSTALL_ROOT}" reset --hard origin/main >/dev/null 2>&1 || fail "Could not update the RPG installation."
  done_step "RPG updated"
else
  step "Downloading RPG"
  rm -rf "${INSTALL_ROOT}"
  git clone --depth 1 --quiet "${REPO_URL}" "${INSTALL_ROOT}" || fail "Could not download the RPG repository."
  done_step "RPG downloaded"
fi

cd "${INSTALL_ROOT}"

step "Creating Python environment"
python3 -m venv .venv >/dev/null 2>&1 || fail "Could not create the Python environment."
done_step "Python environment ready"

step "Installing RPG components"
".venv/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || fail "Could not update pip."
".venv/bin/python" -m pip install -e ".[dev]" >/dev/null 2>&1 || fail "Could not install RPG components."
done_step "RPG components installed"

step "Installing RPG command"
cat > "${RPG_COMMAND}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${INSTALL_ROOT}/.venv/bin/python" -m game "\$@"
EOF
chmod +x "${RPG_COMMAND}"
done_step "RPG command installed"

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *)
    printf '\n  Note: %s is not currently in PATH.\n' "${BIN_DIR}"
    printf '  Add it with: export PATH="\$HOME/.local/bin:\$PATH"\n'
    ;;
esac

printf '\n  ✓ Installation complete.\n'
printf '  → Launching RPG...\n\n'
sleep 0.3

# When this script is launched through `curl ... | bash`, stdin belongs to curl.
# Give the interactive game the terminal instead so input() can read normally.
if [[ -r /dev/tty ]]; then
  exec "${RPG_COMMAND}" game </dev/tty
else
  exec "${RPG_COMMAND}" game
fi
