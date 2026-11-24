#!/usr/bin/env bash
# Compila dist/Sanitizador3MF.exe (Windows x64) desde Linux. Requiere Go.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
if ! command -v go >/dev/null && [ -x "$HOME/.local/go/bin/go" ]; then
    PATH="$HOME/.local/go/bin:$PATH"
fi

VERSION=1.0.0
OUT=../dist/Sanitizador3MF.exe

go test ./...
[ -f winres/icon.png ] || python3 winres/make_icon.py
mkdir -p "$(dirname "$OUT")"
go run github.com/tc-hib/go-winres@v0.3.3 simply \
    --arch amd64 \
    --out rsrc \
    --manifest gui \
    --icon winres/icon.png \
    --product-name "Sanitizador 3MF" \
    --file-description "Sanitizador 3MF" \
    --original-filename Sanitizador3MF.exe \
    --product-version "$VERSION" \
    --file-version "$VERSION"
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -H=windowsgui -X main.appVersion=$VERSION" -o "$OUT" .
rm -f rsrc_windows_*.syso
echo "Creado: $(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
