#!/usr/bin/env bash
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
bin="$HOME/.local/bin/sanitize-3mf"
script="$data/nautilus/scripts/Sanitizar 3MF"
extension="$data/nautilus-python/extensions/sanitize_3mf_extension.py"

install -Dm755 "$src/sanitize_3mf.py" "$bin"
install -Dm644 "$src/sanitize_3mf_extension.py" "$extension"

if dpkg-query -W -f='${Status}' python3-nautilus 2>/dev/null | grep -q "install ok installed"; then
    rm -f "$script"
    echo "Installed direct Nautilus menu. Restart Nautilus with: nautilus -q"
else
    mkdir -p "$(dirname "$script")"
    printf '#!/usr/bin/env bash\nexec "%s" --notify -- "$@"\n' "$bin" > "$script"
    chmod 755 "$script"
    echo "Installed Nautilus menu under Scripts > Sanitizar 3MF."
    echo "Install python3-nautilus and rerun this script for the direct menu."
fi
