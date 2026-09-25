#!/usr/bin/env bash
#
# Signed TagTracker APK for the SIYI UniRC 7 Pro (Android 13, arm64), built on the Mac.
#
#   tools/android_apk.sh build      configure and build the release APK, then verify it
#   tools/android_apk.sh verify     check the last APK: SDK levels, ABI, signature, package
#   tools/android_apk.sh install    adb install -r onto whatever single device adb sees
#   tools/android_apk.sh path       print the APK's path
#
# Builds whatever branch TagTracker is checked out on; the build prints which.
# The APK lands at TagTracker/build/Android/android-build/TagTracker.apk (the name
# comes from Qt's androiddeployqt; `path` finds it whatever it is called).
#
# Versions come from TagTracker/.github/build-config.json, the same file CI reads,
# and the script refuses to build if an installed piece does not match it. A wrong
# NDK configures happily and then fails somewhere that does not name the cause.
# Set up on 2026-09-24:
#   Java 21          Android Studio's bundled runtime (jbr), used as JAVA_HOME
#   SDK              ~/Library/Android/sdk: platforms;android-36, build-tools;36.0.0,
#                    ndk;27.2.12479018, installed with cmdline-tools/latest/bin/sdkmanager
#   Qt 6.11.1        ~/Qt/6.11.1/android_arm64_v8a (target) and ~/Qt/6.11.1/macos (host)
# If build-config.json moves a version, install the new one with
#   JAVA_HOME=<jbr> ~/Library/Android/sdk/cmdline-tools/latest/bin/sdkmanager "ndk;<ver>"
# and rerun; nothing in this script names a version.
#
# Signing uses the committed keystore custom/deploy/android/debug.keystore, alias
# androiddebugkey. The password is never written in this file. It is taken from
# $TAGTRACKER_KEYSTORE_PASS if set, otherwise from the macOS login keychain item
# "uavrt-tagtracker-keystore", otherwise asked for. To store it once:
#   security add-generic-password -a "$USER" -s uavrt-tagtracker-keystore -w
# (with no value after -w, security prompts for it and it stays out of shell history).
# That keychain item was created on this Mac on 2026-09-24, so the build needs no prompt.
# Do not make a new keystore: an APK signed with a different key will not install
# over one signed with this key.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
TT="${TAGTRACKER_DIR:-$HERE/../TagTracker}"
TT="$(cd "$TT" && pwd)"
CONFIG="$TT/.github/build-config.json"
BUILD_DIR="$TT/build/Android"

usage() { sed -n '4,7p' "$0"; exit 2; }

die() { echo "error: $*" >&2; exit 1; }

cfg() {  # cfg android.ndk_full_version
    python3 -c 'import json,sys
d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."): d=d[k]
print(d)' "$CONFIG" "$1"
}

setup_env() {
    [[ -f "$CONFIG" ]] || die "no $CONFIG; is TAGTRACKER_DIR right?"

    QT_VERSION="$(cfg qt.version)"
    JAVA_WANT="$(cfg android.java_version)"
    PLATFORM="$(cfg android.platform)"
    BUILD_TOOLS="$(cfg android.build_tools)"
    NDK_VERSION="$(cfg android.ndk_full_version)"
    MIN_SDK="$(cfg android.min_sdk)"

    export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
    export ANDROID_HOME="$ANDROID_SDK_ROOT"
    export ANDROID_NDK="$ANDROID_SDK_ROOT/ndk/$NDK_VERSION"
    export ANDROID_NDK_ROOT="$ANDROID_NDK" ANDROID_NDK_HOME="$ANDROID_NDK"
    export ANDROID_MIN_SDK="$MIN_SDK"
    export QT_TARGET_ROOT_DIR="$HOME/Qt/$QT_VERSION/android_arm64_v8a"
    export QT_HOST_PATH="$HOME/Qt/$QT_VERSION/macos"
    export JAVA_HOME="${JAVA_HOME_OVERRIDE:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
    export PATH="$JAVA_HOME/bin:$ANDROID_SDK_ROOT/platform-tools:$PATH"
    BT="$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS"

    local missing=()
    [[ -x "$JAVA_HOME/bin/java" ]] || missing+=("Java at $JAVA_HOME")
    [[ -d "$ANDROID_SDK_ROOT/platforms/android-$PLATFORM" ]] || missing+=("SDK platform android-$PLATFORM")
    [[ -x "$BT/aapt2" ]] || missing+=("build-tools $BUILD_TOOLS")
    [[ -d "$ANDROID_NDK" ]] || missing+=("NDK $NDK_VERSION")
    [[ -f "$QT_TARGET_ROOT_DIR/lib/cmake/Qt6/qt.toolchain.cmake" ]] || missing+=("Qt $QT_VERSION android_arm64_v8a")
    [[ -x "$QT_HOST_PATH/bin/qmake" || -x "$QT_HOST_PATH/bin/qtpaths" ]] || missing+=("Qt $QT_VERSION macos (host)")
    ((${#missing[@]} == 0)) || die "missing: ${missing[*]}"

    local java_major
    java_major="$("$JAVA_HOME/bin/java" -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1)"
    [[ "$java_major" == "$JAVA_WANT" ]] || die "Java $java_major at $JAVA_HOME, build-config wants $JAVA_WANT"
    local ndk_rev
    ndk_rev="$(sed -n 's/^Pkg.Revision *= *//p' "$ANDROID_NDK/source.properties")"
    [[ "$ndk_rev" == "$NDK_VERSION" ]] || die "NDK directory $ANDROID_NDK reports $ndk_rev"
}

keystore_env() {
    local pass="${TAGTRACKER_KEYSTORE_PASS:-}"
    [[ -n "$pass" ]] || pass="$(security find-generic-password -a "$USER" -s uavrt-tagtracker-keystore -w 2>/dev/null || true)"
    if [[ -z "$pass" ]]; then
        read -r -s -p "Keystore password: " pass; echo
    fi
    local ks="$TT/custom/deploy/android/debug.keystore"
    "$JAVA_HOME/bin/keytool" -list -keystore "$ks" -storepass "$pass" -alias androiddebugkey >/dev/null 2>&1 \
        || die "the keystore refused that password"
    export QT_ANDROID_KEYSTORE_PATH="$ks"
    export QT_ANDROID_KEYSTORE_ALIAS=androiddebugkey
    export QT_ANDROID_KEYSTORE_STORE_PASS="$pass" QT_ANDROID_KEYSTORE_KEY_PASS="$pass"
}

apk_path() {
    local apk
    apk="$(ls -t "$BUILD_DIR"/android-build/*.apk 2>/dev/null | head -1 || true)"
    [[ -n "$apk" ]] || die "no APK under $BUILD_DIR/android-build; run build first"
    echo "$apk"
}

verify() {
    local apk badging ok=1
    apk="$(apk_path)"
    badging="$("$BT/aapt2" dump badging "$apk")"
    local pkg min target abis
    pkg="$(sed -n "s/^package: name='\([^']*\)'.*/\1/p" <<<"$badging")"
    min="$(sed -nE "s/^(min)?[sS]dkVersion:'([0-9]*)'/\2/p" <<<"$badging")"
    target="$(sed -n "s/^targetSdkVersion:'\([0-9]*\)'/\1/p" <<<"$badging")"
    abis="$(unzip -Z1 "$apk" 'lib/*' 2>/dev/null | cut -d/ -f2 | sort -u | tr '\n' ' ')"

    check() { if [[ "$2" == "$3" ]]; then echo "  ok    $1: $2"; else echo "  FAIL  $1: $2 (want $3)"; ok=0; fi; }
    echo "$apk"
    check "package" "$pkg" "com.thegagnes.tagtracker"
    check "minimum SDK" "$min" "$MIN_SDK"
    check "target SDK" "$target" "$PLATFORM"
    check "native ABIs" "${abis% }" "arm64-v8a"
    if "$BT/apksigner" verify "$apk" >/dev/null 2>&1; then
        echo "  ok    apksigner verify: $("$BT/apksigner" verify --print-certs "$apk" | sed -n 's/^Signer #1 certificate DN: //p')"
    else
        echo "  FAIL  apksigner verify"; ok=0
    fi
    echo "  size  $(du -h "$apk" | cut -f1 | tr -d ' ') ($(stat -f %z "$apk") bytes)"
    ((ok)) || die "APK failed verification"
}

cmd="${1:-}"
case "$cmd" in
    build)
        setup_env
        keystore_env
        echo "TagTracker branch $(git -C "$TT" branch --show-current) at $(git -C "$TT" rev-parse --short HEAD)"
        cd "$TT"
        cmake --preset Android \
            -DQT_ANDROID_ABIS=arm64-v8a \
            -DQT_ANDROID_SIGN_APK=ON \
            -DCMAKE_WARN_DEPRECATED=FALSE
        cmake --build --preset Android
        verify
        ;;
    verify) setup_env; verify ;;
    install)
        setup_env
        n="$(adb devices | awk 'NR>1 && $2=="device"' | wc -l | tr -d ' ')"
        [[ "$n" == 1 || -n "${ANDROID_SERIAL:-}" ]] || die "adb sees $n devices; want exactly one (adb devices lists them; pick with ANDROID_SERIAL=...)"
        adb install -r "$(apk_path)"
        adb shell monkey -p com.thegagnes.tagtracker -c android.intent.category.LAUNCHER 1 >/dev/null
        echo "installed and launched"
        ;;
    path) apk_path ;;
    *) usage ;;
esac
