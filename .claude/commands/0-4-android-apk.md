---
description: "Task 0-4 — set up the Android toolchain on the Mac and build a signed TagTracker APK for the SIYI UniRC 7 Pro"
model: opus
effort: high
---

Read first: `docs/WRITING_RULES.md`, then `docs/TASK_COMMS.md` including "Decisions already made".

## What this task is

Michael has replaced his Herelink with a SIYI UniRC 7 Pro, which runs Android 13. The old
controller could never run this build: TagTracker now requires Android 9, API level 28, and the
Herelink is stuck on Android 7.1.2 because its hardware cannot take a newer version. The new
controller clears that, and this task produces the APK to put on it.

**The controller does not need to be plugged in.** Build and verify first. Install only if a
device happens to be connected, and otherwise leave Michael the path and the one command.

## What is already in place

- Qt 6.11.1 for `android_arm64_v8a`, and the macOS host Qt at `~/Qt/6.11.1/macos`.
- The signing keystore, committed at `custom/deploy/android/debug.keystore`.
- The macOS build works. Its recipe is in `docs/TASK_COMMS.md`, and the same Python, `uv` and
  Homebrew groundwork applies here.

## What is missing, and the versions are not negotiable

`.github/build-config.json` pins them, and a mismatched NDK configures happily and then fails
somewhere that does not name the cause:

```
Java             21
SDK platform     android-36
Build tools      36.0.0
NDK              27.2.12479018   (r27c)
Minimum SDK      28
Target SDK       36
ABI              arm64-v8a only
```

Install those, then confirm each one is the version you think it is before building. Read the
versions out of `.github/build-config.json` rather than copying them from this brief, and say in
your report if they have moved.

## Building

The CI workflow `.github/workflows/android.yml` is the reference. It uses the `Android` preset
with `QT_ANDROID_ABIS=arm64-v8a`, `QT_HOST_PATH` pointing at the macOS Qt, and
`QT_ANDROID_SIGN_APK=ON`, with the keystore supplied through `QT_ANDROID_KEYSTORE_PATH`,
`QT_ANDROID_KEYSTORE_ALIAS` (`androiddebugkey`) and the two password variables. The Android
preset also reads `ANDROID_NDK`, `ANDROID_MIN_SDK`, `QT_TARGET_ROOT_DIR` and `QT_HOST_PATH` from
the environment.

**The keystore password is not known to anyone here.** It is a GitHub secret in Don Gagne's CI.
Try `android`, which is the conventional Android debug password, and if the keystore refuses it,
stop and ask Michael rather than generating a new keystore or turning signing off. An unsigned
APK will not install, and a differently-signed one will not upgrade an existing install.

Build release, not debug. A debug Android build is large and slow, and the point here is
something that runs on the controller.

## Verify before you hand it over

An APK that builds is not an APK that installs. Check the artifact itself, with `aapt2` or
`apkanalyzer` from the build tools:

- minimum SDK is 28 and target SDK is 36
- it contains `arm64-v8a` native libraries and no others
- it is signed, and `apksigner verify` passes
- the package name is `com.thegagnes.tagtracker`

Report the APK's size. Michael is going to copy it to a controller, and the number matters.

## Then run it on an emulator

Android Studio is installed and this Mac is Apple Silicon, so an arm64 system image runs natively
and will accept this APK without translation. Use an API 28 or newer arm64 image; API 28 exactly
is the more useful choice, because it is the floor the APK claims to support and the place a
packaging mistake shows up.

Drive it from the command line rather than the Android Studio interface: `avdmanager` to create
the device if none exists, `emulator` to start it headless or not, `adb install -r`, `adb logcat`
to watch it start, and `adb exec-out screencap -p` to pull a screenshot you can look at.

What to establish, in order:

- It installs. A signing or minimum-SDK mistake fails here and nowhere earlier.
- It launches and reaches its main screen rather than dying on a missing library. Read `logcat`
  for the first fatal error if it does not.
- **It can create and write the per-connection log folders.** This is the part worth the effort.
  The log reorganization on branch `telemetry-pairing` has only ever run on a Mac filesystem, and
  Android's scoped storage rules are the most likely place for it to fail on a real controller.
  Find where TagTracker's log save path resolves to on Android, make it write something there,
  and confirm a folder with a pulse log and a sidecar appears. Use `adb shell` to look.
- Report the screenshot and what `logcat` said.

If the emulator cannot be made to work, say so and why, and do not spend the whole task on it.
The APK itself is the deliverable; this is verification.

## Installing on the real controller, only if it is there

If `adb devices` shows the controller, install with `adb install -r` and confirm the app launches.
If it does not, say so plainly and give Michael the APK path and the exact command. Do not ask him
to plug anything in mid-task.

The UniRC 7 Pro needs developer options and USB debugging enabled before `adb` will see it.
Sideloading the file with the controller's own file manager also works and needs neither.

## Leave a rebuild command

A script in `tools/`, in the same spirit as `sim_rig.sh`, that rebuilds the APK in one line with
the environment already set. Every future Android build should not require rediscovering six
environment variables.

## Rules

This task changes no TagTracker source. Scripts go in the hub repository under `tools/`.

Do not commit the keystore password anywhere, and do not print it.

Build from the branch Michael is on. If that is `telemetry-pairing`, say so in your report, since
the APK then contains the unmerged log work.

If a required piece cannot be installed, stop and report `Blocked` with what is needed rather
than substituting a different version.

## When you finish

Append an entry to the top of "Open" in `docs/TASK_COMMS.md` with your commit hashes, the APK
path, its verified minimum SDK and ABI, its size, what the emulator run showed, and whether it
was installed on the real controller. Then report to
Michael in chat ending with what he needs to do.
