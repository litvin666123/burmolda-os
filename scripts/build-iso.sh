#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "Burmolda OS currently builds only on x86_64." >&2
  exit 1
fi
if (( EUID == 0 )) && [[ "${BURMOLDA_CI_ROOT_BUILD:-0}" != "1" ]]; then
  echo "Run locally as a regular user; root builds are enabled only in isolated CI." >&2
  exit 1
fi
command -v mkarchiso >/dev/null 2>&1 || { echo "Install archiso first." >&2; exit 1; }
[[ -d /usr/share/archiso/configs/releng ]] || { echo "Archiso releng profile not found." >&2; exit 1; }

PROFILE="$ROOT/.build/profile"
rm -rf -- "$PROFILE"
mkdir -p -- "$ROOT/.build" "$ROOT/work" "$ROOT/out"
cp -a /usr/share/archiso/configs/releng "$PROFILE"

python3 "$ROOT/scripts/generate-assets.py" --overlay "$ROOT/profile-overlay/airootfs"
python3 "$ROOT/scripts/prepare-profile.py" \
  --profile "$PROFILE" \
  --overlay "$ROOT/profile-overlay/airootfs" \
  --grub-dir "$ROOT/profile-overlay/grub" \
  --version "$(cat "$ROOT/VERSION")" \
  --wallpapers "$ROOT/assets/community-wallpapers" \
  --sounds "$ROOT/assets/community-sounds"

mkarchiso -v -w "$ROOT/work" -o "$ROOT/out" "$PROFILE"
while IFS= read -r -d '' iso; do
  sha256sum "$iso" > "$iso.sha256"
done < <(find "$ROOT/out" -maxdepth 1 -type f -name '*.iso' -print0)
echo "Burmolda OS ISO build completed. Files in: $ROOT/out"
