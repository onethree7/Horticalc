#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
spec_path="$repo_root/scripts/packaging/horticalc.spec"

python -m PyInstaller --noconfirm --clean "$spec_path"

dist_root="$repo_root/dist"
app_root="$dist_root/horticalc"

if [[ ! -d "$app_root" ]]; then
  echo "Expected PyInstaller output folder not found: $app_root" >&2
  exit 1
fi

for dir in frontend data recipes; do
  src="$repo_root/$dir"
  dest="$app_root/$dir"
  rm -rf "$dest"
  cp -a "$src" "$dest"
done
