#!/usr/bin/env bash
#
# bootstrap.sh — clone every UAV-RT component into this directory.
#
#   ./bootstrap.sh              clone/update at the branch tips in versions.yaml
#   ./bootstrap.sh --pinned     check out the `verified` commits instead
#   ./bootstrap.sh --check      report status only; change nothing
#
# Components are gitignored by this repository: it is a hub holding docs,
# tooling and the manifest, not a superproject. Each component keeps its own
# history and is pushed to its own remote.
#
# Safe to re-run. It never discards local work: a component with uncommitted
# changes or on an unexpected branch is reported and skipped, not reset.

set -uo pipefail

HUB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HUB/versions.yaml"
MODE=branch
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --pinned) MODE=pinned ;;
    --check)  CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

[ -f "$MANIFEST" ] || { echo "error: $MANIFEST not found" >&2; exit 1; }
command -v git >/dev/null || { echo "error: git not found" >&2; exit 1; }

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
amber() { printf '\033[33m%s\033[0m\n' "$*"; }

# Minimal YAML reader: pulls name/url/branch/verified out of the components
# block. Deliberately not a general parser — keep versions.yaml in this shape.
parse_manifest() {
  awk '
    /^components:/ { inblock=1; next }
    inblock && /^  [a-zA-Z0-9_-]+:$/ {
      if (name != "") print name "|" url "|" branch "|" verified
      name=$1; sub(/:$/,"",name); url=""; branch=""; verified=""; next
    }
    inblock && /^    url:/      { url=$2 }
    inblock && /^    branch:/   { branch=$2 }
    inblock && /^    verified:/ { verified=$2 }
    END { if (name != "") print name "|" url "|" branch "|" verified }
  ' "$MANIFEST"
}

FAILED=0; SKIPPED=0; OK=0

while IFS='|' read -r name url branch verified; do
  [ -n "$name" ] || continue
  target="$HUB/$name"
  printf '%-26s ' "$name"

  if [ ! -d "$target/.git" ]; then
    if [ "$CHECK_ONLY" = 1 ]; then amber "absent"; SKIPPED=$((SKIPPED+1)); continue; fi
    if git clone --quiet --recurse-submodules "$url" "$target" 2>/dev/null; then
      green "cloned"
    else
      red "CLONE FAILED — $url"; FAILED=$((FAILED+1)); continue
    fi
  fi

  # Never touch a component with local work in progress.
  dirty="$(git -C "$target" status --porcelain --untracked-files=no 2>/dev/null)"
  if [ -n "$dirty" ]; then
    amber "skipped — uncommitted changes ($(echo "$dirty" | wc -l | tr -d ' ') files)"
    SKIPPED=$((SKIPPED+1)); continue
  fi

  if [ "$CHECK_ONLY" = 1 ]; then
    echo "$(git -C "$target" rev-parse --abbrev-ref HEAD) @ $(git -C "$target" rev-parse --short HEAD)"
    OK=$((OK+1)); continue
  fi

  git -C "$target" fetch --quiet origin 2>/dev/null || amber "  (fetch failed — offline?)"
  ref="$branch"; [ "$MODE" = pinned ] && ref="$verified"
  if git -C "$target" checkout --quiet "$ref" 2>/dev/null; then
    [ "$MODE" = branch ] && git -C "$target" merge --quiet --ff-only "origin/$branch" 2>/dev/null
    git -C "$target" submodule update --init --recursive --quiet 2>/dev/null
    green "$ref @ $(git -C "$target" rev-parse --short HEAD)"
    OK=$((OK+1))
  else
    red "CHECKOUT FAILED — $ref"; FAILED=$((FAILED+1))
  fi
done < <(parse_manifest)

echo
echo "ok: $OK   skipped: $SKIPPED   failed: $FAILED"

# --- Advisory checks; never fatal ------------------------------------------
echo
echo "environment:"
for cmd in cmake pkg-config python3; do
  if command -v "$cmd" >/dev/null; then printf '  %-12s %s\n' "$cmd" "$(command -v "$cmd")"
  else printf '  %-12s ' "$cmd"; amber "not found"; fi
done
if ls -d /Applications/MATLAB_R*.app >/dev/null 2>&1; then
  printf '  %-12s %s\n' matlab "$(ls -d /Applications/MATLAB_R*.app | tail -1)"
elif command -v matlab >/dev/null; then
  printf '  %-12s %s\n' matlab "$(command -v matlab)"
else
  printf '  %-12s ' matlab; amber "not found — needed only to regenerate codegen"
fi

# Committed generated code can silently stop matching its source. This has
# happened: uavrt_bearing's codegen was committed 2023-11-07 and its sources
# changed 2023-12-20, undetected for two years.
#
# Compare COMMIT DATES, not file mtimes: git does not preserve mtimes, so after
# a fresh clone every file looks equally old and an mtime check reports nothing.
echo
echo "codegen freshness (last commit touching sources vs codegen/):"
for repo in uavrt_detection uavrt_bearing uavrt_localize airspy_channelize airspy_decimate; do
  d="$HUB/$repo"
  [ -d "$d/.git" ] && [ -d "$d/codegen" ] || continue
  gen_date=$(git -C "$d" log -1 --format=%ct -- codegen 2>/dev/null)
  src_date=$(git -C "$d" log -1 --format=%ct -- '*.m' 2>/dev/null)
  printf '  %-24s ' "$repo"
  if [ -z "$gen_date" ] || [ -z "$src_date" ]; then
    amber "unknown"
  elif [ "$src_date" -gt "$gen_date" ]; then
    amber "STALE — sources committed $(git -C "$d" log -1 --format=%cs -- '*.m'), codegen $(git -C "$d" log -1 --format=%cs -- codegen)"
  else
    green "ok ($(git -C "$d" log -1 --format=%cs -- codegen))"
  fi
done

[ "$FAILED" -gt 0 ] && exit 1
exit 0
