#!/bin/bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd -P)"
HOME_DIR="$HOME"
APP_PARENT="$HOME_DIR/Applications"
SUPPORT_PARENT="$HOME_DIR/Library/Application Support"
APP_TARGET="$APP_PARENT/Cortex Status.app"
SUPPORT_TARGET="$SUPPORT_PARENT/Cortex Status Board"
DESKTOP_LINK="$HOME_DIR/Desktop/Cortex Status.app"

for target in "$APP_TARGET" "$SUPPORT_TARGET" "$DESKTOP_LINK"; do
  if [[ -e "$target" || -L "$target" ]]; then
    printf 'Refusing to replace existing target: %s\n' "$target" >&2
    exit 73
  fi
done

NODE_PATH="$(command -v node || true)"
if [[ -z "$NODE_PATH" || "$NODE_PATH" != /* || ! -x "$NODE_PATH" ]]; then
  printf 'Could not discover an absolute executable Node.js path.\n' >&2
  exit 69
fi
NODE_VERSION="$("$NODE_PATH" --version)"
NODE_MAJOR="$(printf '%s' "$NODE_VERSION" | cut -d. -f1 | tr -d 'v')"
if [[ ! "$NODE_MAJOR" =~ ^[0-9]+$ ]] || [[ "$NODE_MAJOR" -lt 20 ]]; then
  printf 'Node.js 20 or later is required; found %s.\n' "$NODE_VERSION" >&2
  exit 69
fi

mkdir -p "$APP_PARENT" "$SUPPORT_PARENT"
STAGE_ROOT="$(mktemp -d /private/tmp/cortex-status-install.XXXXXX)"
APP_STAGE=""
SUPPORT_STAGE=""
cleanup() {
  rm -rf -- "$STAGE_ROOT"
  if [[ -n "$APP_STAGE" && -d "$APP_STAGE" ]]; then rm -rf -- "$APP_STAGE"; fi
  if [[ -n "$SUPPORT_STAGE" && -d "$SUPPORT_STAGE" ]]; then rm -rf -- "$SUPPORT_STAGE"; fi
}
trap cleanup EXIT
APP_STAGE="$(mktemp -d "$APP_PARENT/.CortexStatus-app-stage.XXXXXX")"
SUPPORT_STAGE="$(mktemp -d "$SUPPORT_PARENT/.CortexStatus-support-stage.XXXXXX")"

mkdir -p "$SUPPORT_STAGE/public" "$APP_STAGE/Contents/MacOS" "$APP_STAGE/Contents/Resources"
mkdir "$STAGE_ROOT/clang-cache"
cp "$SOURCE_DIR/server.mjs" "$SOURCE_DIR/package.json" "$SUPPORT_STAGE/"
cp "$SOURCE_DIR/public/"* "$SUPPORT_STAGE/public/"
/usr/bin/openssl rand -hex 32 > "$SUPPORT_STAGE/server.identity"
chmod 600 "$SUPPORT_STAGE/server.identity"

swiftc -module-cache-path "$STAGE_ROOT/clang-cache" -O -framework AppKit -framework Foundation \
  -o "$STAGE_ROOT/IconGenerator" "$SOURCE_DIR/macos/IconGenerator.swift"
"$STAGE_ROOT/IconGenerator" "$STAGE_ROOT/icon.png"
ICONSET="$APP_STAGE/Contents/Resources/CortexStatus.iconset"
mkdir "$ICONSET"
make_icon() {
  sips -z "$2" "$2" "$STAGE_ROOT/icon.png" --out "$ICONSET/icon_$1.png" >/dev/null
}
make_icon 16x16 16
make_icon 16x16@2x 32
make_icon 32x32 32
make_icon 32x32@2x 64
make_icon 128x128 128
make_icon 128x128@2x 256
make_icon 256x256 256
make_icon 256x256@2x 512
make_icon 512x512 512
make_icon 512x512@2x 1024
iconutil -c icns -o "$APP_STAGE/Contents/Resources/CortexStatus.icns" "$ICONSET"
rm -rf -- "$ICONSET"

swiftc -module-cache-path "$STAGE_ROOT/clang-cache" -parse-as-library -O -framework AppKit -framework Foundation \
  -o "$APP_STAGE/Contents/MacOS/CortexStatusApp" "$SOURCE_DIR/macos/CortexStatusApp.swift"
PLIST="$APP_STAGE/Contents/Info.plist"
cat > "$PLIST" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict></dict></plist>
PLIST
/usr/libexec/PlistBuddy -c 'Add :CFBundleExecutable string CortexStatusApp' "$PLIST"
/usr/libexec/PlistBuddy -c 'Add :CFBundleIdentifier string ai.cortex.statusboard.c004' "$PLIST"
/usr/libexec/PlistBuddy -c 'Add :CFBundleName string Cortex Status' "$PLIST"
/usr/libexec/PlistBuddy -c 'Add :CFBundleDisplayName string Cortex Status' "$PLIST"
/usr/libexec/PlistBuddy -c 'Add :CFBundlePackageType string APPL' "$PLIST"
/usr/libexec/PlistBuddy -c 'Add :CFBundleIconFile string CortexStatus.icns' "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CortexNodePath string $NODE_PATH" "$PLIST"
chmod 755 "$APP_STAGE/Contents/MacOS/CortexStatusApp"
/usr/bin/codesign --force --deep --sign - "$APP_STAGE"
/usr/bin/codesign --verify --deep --strict "$APP_STAGE"

for target in "$APP_TARGET" "$SUPPORT_TARGET" "$DESKTOP_LINK"; do
  if [[ -e "$target" || -L "$target" ]]; then
    printf 'Refusing to replace existing target: %s\n' "$target" >&2
    exit 73
  fi
done

mv -n "$APP_STAGE" "$APP_TARGET"
if [[ -e "$APP_STAGE" || ! -d "$APP_TARGET" ]]; then
  printf 'Could not install app bundle without replacing an existing path.\n' >&2
  exit 73
fi
APP_STAGE=""
mv -n "$SUPPORT_STAGE" "$SUPPORT_TARGET"
if [[ -e "$SUPPORT_STAGE" || ! -d "$SUPPORT_TARGET" ]]; then
  printf 'Could not install support files without replacing an existing path.\n' >&2
  exit 73
fi
SUPPORT_STAGE=""
ln -s "$APP_TARGET" "$DESKTOP_LINK"

printf 'Installed: %s\n' "$APP_TARGET"
printf 'Desktop shortcut: %s -> %s\n' "$DESKTOP_LINK" "$APP_TARGET"
printf 'Durable board files: %s\n' "$SUPPORT_TARGET"
printf 'Node.js: %s (%s)\n' "$NODE_PATH" "$NODE_VERSION"
