#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
spec_path="$repo_root/scripts/packaging/horticalc.spec"

cd "$repo_root"
export HORTICALC_PROJECT_ROOT="$repo_root"

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

cp "$repo_root/scripts/packaging/README.txt" "$app_root/README.txt"
cp "$repo_root/LICENSE" "$app_root/LICENSE"

binary_path="$app_root/horticalc"
if [[ ! -x "$binary_path" ]]; then
  echo "Expected packaged binary not found or not executable: $binary_path" >&2
  exit 1
fi

for dir in frontend data recipes; do
  if [[ ! -d "$app_root/$dir" ]]; then
    echo "Expected packaged asset directory not found: $app_root/$dir" >&2
    exit 1
  fi
done

if [[ ! -f "$app_root/README.txt" ]]; then
  echo "Expected packaged README not found: $app_root/README.txt" >&2
  exit 1
fi

if [[ ! -f "$app_root/LICENSE" ]]; then
  echo "Expected packaged license not found: $app_root/LICENSE" >&2
  exit 1
fi

python "$repo_root/scripts/packaging/verify_linux_bundle.py" "$app_root"
