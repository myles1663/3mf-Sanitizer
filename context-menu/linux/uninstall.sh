#!/usr/bin/env bash
set -euo pipefail

data="${XDG_DATA_HOME:-$HOME/.local/share}"
rm -fv "$HOME/.local/bin/sanitize-3mf" \
    "$data/nautilus/scripts/Sanitizar 3MF" \
    "$data/nautilus-python/extensions/sanitize_3mf_extension.py"
echo "Restart Nautilus with: nautilus -q"
