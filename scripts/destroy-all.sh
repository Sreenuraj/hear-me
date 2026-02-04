#!/bin/bash
# hear-me Destroy-All Reset Script
# Removes all hear-me artifacts and stops running processes.

set -e

YES=0
for arg in "$@"; do
  case "$arg" in
    --yes) YES=1 ;;
  esac
done

if [ "$YES" -ne 1 ]; then
  echo "WARNING: This will remove all hear-me data, venvs, engines, and cached models."
  echo "It will also stop any running hear-me/Dia2 processes."
  read -r -p "Type 'destroy' to continue: " CONFIRM
  if [ "$CONFIRM" != "destroy" ]; then
    echo "Aborted."
    exit 1
  fi
fi

echo "Stopping hear-me/Dia2 processes..."
pkill -f "python.*-m hearme" >/dev/null 2>&1 || true
pkill -f "uv run -m dia2.cli" >/dev/null 2>&1 || true

HEARME_DIR="${HOME}/.hear-me"
HF_HOME_DIR="${HF_HOME:-$HOME/.cache/huggingface}"

echo "Removing hear-me installation directory: ${HEARME_DIR}"
rm -rf "${HEARME_DIR}"

echo "Removing Dia2 model cache..."
rm -rf "${HF_HOME_DIR}/hub/models--nari-labs--Dia2-2B"

echo "Removing Kokoro model cache..."
rm -rf "${HF_HOME_DIR}/hub/models--hexgrad--Kokoro-82M"

echo "Removing Piper voice cache (best-effort)..."
rm -rf "${HOME}/.local/share/piper"
rm -rf "${HOME}/.cache/piper"

echo "Done. Your system should be reset to pre-install state."
