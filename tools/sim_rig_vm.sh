#!/usr/bin/env bash
#
# VM half of the flight simulation rig. Runs inside the Parallels VM.
# Normally not run by hand: tools/sim_rig.sh on the Mac copies it to
# ~/uavrt-rig/bin/ in the VM and calls it over ssh.
#
#   sim_rig_vm.sh start [preset]   start PX4 SITL and the tag controller
#   sim_rig_vm.sh stop             stop both, and every process they spawned
#   sim_rig_vm.sh status           report what is actually running
#   sim_rig_vm.sh logs [px4|controller] [lines]
#
# The rig lives in ~/uavrt-rig:
#   repos/MavlinkTagController2  controller checkout the rig runs (built there)
#   repos/uavrt_detection        symlink to ~/repos/uavrt_detection
#   px4/                         PX4 working directory (parameters, .ulg logs)
#   logs/<start time>/           px4.log and controller.log for each start
#   Logs/                        the controller's own logs (it writes to $HOME/Logs)
#
# The controller is run with HOME=~/uavrt-rig. It builds every path it spawns
# from $HOME/repos/..., so this makes it use the rig's checkout, leaves
# ~/repos/MavlinkTagController2 untouched, and confines its log pruning to
# the rig's own Logs folder.

set -uo pipefail

RIG="$HOME/uavrt-rig"
MTC="$RIG/repos/MavlinkTagController2"
PX4_BUILD="$HOME/repos/PX4-Autopilot/build/px4_sitl_default"
PX4_DIR="$RIG/px4"
LOG_ROOT="$RIG/logs"

PX4_SESSION="rig-px4"
CTL_SESSION="rig-controller"

# Flagstaff, as in Michael's Gazebo runs.
HOME_LAT=35.178148
HOME_LON=-111.656720
HOME_ALT=2100

# numpy's OpenBLAS picks SME kernels on the M4, which fault inside the VM
# ("Illegal instruction"). Force the plain ARMv8 kernels.
export OPENBLAS_CORETYPE=ARMV8

# Signal levels the controller understands, then iq_simulator scenarios that
# only apply when no tag has been uploaded (TagTracker always uploads tags).
LEVEL_PRESETS="strong moderate marginal below-marginal silent competing power-line"
SCENARIO_PRESETS="weak noise-only two-tags distant dropout gap rate-switch"

die() { echo "error: $*" >&2; exit 1; }

has_session() { tmux has-session -t "=$1" 2>/dev/null; }

# The rig's px4: the one whose working directory is the rig's.
px4_pid() {
    local pid
    for pid in $(pgrep -x px4 2>/dev/null); do
        [ "$(readlink "/proc/$pid/cwd" 2>/dev/null)" = "$PX4_DIR" ] && echo "$pid"
    done
}

# The rig's controller: the one running from the rig's checkout.
# (The kernel truncates process names to 15 characters.)
controller_pid() {
    local pid
    for pid in $(pgrep '^MavlinkTagContr' 2>/dev/null); do
        grep -a -q "$MTC/" "/proc/$pid/cmdline" 2>/dev/null && echo "$pid"
    done
}

# Every live process belonging to the rig: px4, the controller, and whatever
# the controller spawned (simulator, decimator, detectors), which all run from
# the rig's checkout. tmux itself is excluded: its server keeps the command
# line of the new-session that started it, and killing it would take every
# other tmux session on the VM with it.
rig_pids() {
    px4_pid
    local pid
    for pid in $(pgrep -f "$MTC/|$RIG/repos/uavrt_detection/" 2>/dev/null); do
        [ "$pid" = "$$" ] && continue
        case "$(cat "/proc/$pid/comm" 2>/dev/null)" in tmux*) continue ;; esac
        echo "$pid"
    done
}

# PX4 or controller processes that are not the rig's. They would be holding
# the MAVLink ports the rig needs.
foreign_pids() {
    local pid
    for pid in $(pgrep -x px4 2>/dev/null); do
        [ "$(readlink "/proc/$pid/cwd" 2>/dev/null)" = "$PX4_DIR" ] || echo "$pid"
    done
    for pid in $(pgrep '^MavlinkTagContr' 2>/dev/null); do
        grep -a -q "$MTC/" "/proc/$pid/cmdline" 2>/dev/null || echo "$pid"
    done
}

udp_bound() { ss -Hlun "sport = :$1" 2>/dev/null | grep -q .; }

current_log_dir() { readlink -f "$LOG_ROOT/latest" 2>/dev/null; }

# PX4 SITL writes roughly 700 MB of flight log per hour and the VM's disk is
# small. Keep the newest ten.
prune_px4_logs() {
    [ -d "$PX4_DIR/log" ] || return 0
    find "$PX4_DIR/log" -name '*.ulg' -printf '%T@ %p\n' | sort -rn | tail -n +11 | cut -d' ' -f2- \
        | while read -r f; do rm -f "$f"; done
    find "$PX4_DIR/log" -mindepth 1 -type d -empty -delete
}

check_prereqs() {
    command -v tmux >/dev/null || die "tmux is not installed (sudo apt install tmux)"
    [ -x "$PX4_BUILD/bin/px4" ] || die "PX4 SITL not built: $PX4_BUILD/bin/px4 missing"
    [ -x "$MTC/build/controller/MavlinkTagController2" ] || die "controller not built in $MTC (run: cd $MTC && make controller decimator)"
    [ -x "$MTC/build/decimator/airspyhf_decimator" ] || die "decimator not built in $MTC (run: cd $MTC && make decimator)"
    [ -x "$MTC/.venv/bin/python3" ] || die "no Python environment in $MTC (run: cd $MTC && ./setup_venv.sh)"
    "$MTC/.venv/bin/python3" -c 'import numpy, scipy, zmq' 2>/dev/null \
        || die "the rig's Python environment cannot import numpy, scipy and zmq"
}

cmd_start() {
    local preset="${1:-strong}"
    case " $LEVEL_PRESETS $SCENARIO_PRESETS " in
        *" $preset "*) ;;
        *) die "unknown preset '$preset'. Signal levels: $LEVEL_PRESETS. Scenarios (used only with no tags uploaded): $SCENARIO_PRESETS" ;;
    esac
    check_prereqs

    local foreign
    foreign=$(foreign_pids | sort -u | tr '\n' ' ')
    [ -z "$foreign" ] || die "another PX4 or controller is already running outside the rig (pids: $foreign). Stop it first; it holds the MAVLink ports."

    if has_session "$CTL_SESSION"; then
        local running
        running=$(cat "$RIG/preset" 2>/dev/null)
        if [ "$running" != "$preset" ]; then
            die "the rig is already running with preset '$running'. Stop it first to change preset."
        fi
    fi

    local logdir
    if has_session "$PX4_SESSION" || has_session "$CTL_SESSION"; then
        logdir=$(current_log_dir)
    fi
    if [ -z "${logdir:-}" ] || [ ! -d "$logdir" ]; then
        logdir="$LOG_ROOT/$(date -u +%Y-%m-%dT%H-%M-%SZ)"
        mkdir -p "$logdir"
        ln -sfn "$logdir" "$LOG_ROOT/latest"
    fi

    if has_session "$PX4_SESSION"; then
        echo "PX4 SITL already running (tmux session $PX4_SESSION)"
    else
        prune_px4_logs
        # -w keeps PX4's parameters and flight logs in the rig's own directory
        # rather than the build's rootfs, which Michael's Gazebo runs use.
        mkdir -p "$PX4_DIR"
        tmux new-session -d -s "$PX4_SESSION" -c "$PX4_DIR" \
            "env PX4_SIM_MODEL=sihsim_quadx PX4_SIMULATOR=sihsim \
                 PX4_HOME_LAT=$HOME_LAT PX4_HOME_LON=$HOME_LON PX4_HOME_ALT=$HOME_ALT \
                 $PX4_BUILD/bin/px4 -w $PX4_DIR $PX4_BUILD/etc 2>&1 | tee -a $logdir/px4.log"
        echo "PX4 SITL starting (tmux session $PX4_SESSION)"
    fi

    # The controller exits if it cannot bind, and waits forever for a
    # heartbeat that never comes if PX4 is not up, so wait for PX4's onboard port.
    local i
    for i in $(seq 1 60); do
        udp_bound 14580 && break
        has_session "$PX4_SESSION" || die "PX4 exited during startup. Last lines of $logdir/px4.log:
$(tail -15 "$logdir/px4.log")"
        sleep 0.5
    done
    udp_bound 14580 || die "PX4 did not open its onboard MAVLink port 14580 within 30 s. See $logdir/px4.log"

    if has_session "$CTL_SESSION"; then
        echo "Controller already running (tmux session $CTL_SESSION, preset $preset)"
    else
        echo "$preset" > "$RIG/preset"
        tmux new-session -d -s "$CTL_SESSION" -c "$MTC" \
            "env HOME=$RIG OPENBLAS_CORETYPE=ARMV8 \
                 $MTC/build/controller/MavlinkTagController2 --simulator $preset udp://127.0.0.1:14540 \
                 2>&1 | tee -a $logdir/controller.log"
        echo "Controller starting (tmux session $CTL_SESSION, preset $preset)"
    fi

    for i in $(seq 1 20); do
        grep -q 'Found autopilot' "$logdir/controller.log" 2>/dev/null && break
        has_session "$CTL_SESSION" || die "the controller exited during startup. Last lines of $logdir/controller.log:
$(tail -15 "$logdir/controller.log")"
        sleep 0.5
    done
    echo
    cmd_status
}

# Ask a process to stop, then insist after the given number of seconds.
stop_session() {
    local session="$1" graceful_keys="$2" wait_s="$3"
    has_session "$session" || return 0
    # "=name:" is the exact-match form send-keys accepts; bare "=name" is not.
    tmux send-keys -t "=$session:" $graceful_keys 2>/dev/null
    local i
    for i in $(seq 1 $((wait_s * 2))); do
        has_session "$session" || return 0
        sleep 0.5
    done
    echo "$session did not exit within $wait_s s; killing it" >&2
    tmux kill-session -t "=$session" 2>/dev/null
}

cmd_stop() {
    local had=0
    has_session "$CTL_SESSION" && had=1
    has_session "$PX4_SESSION" && had=1

    stop_session "$CTL_SESSION" C-c 5
    # PX4 logs everything from boot, a few hundred MB an hour, and flushes
    # it on shutdown; killing it early would truncate the flight log.
    stop_session "$PX4_SESSION" "shutdown Enter" 20

    # Anything the controller spawned that outlived it.
    local pids i
    for i in 1 2 3; do
        pids=$(rig_pids | sort -u | tr '\n' ' ')
        [ -z "$pids" ] && break
        if [ "$i" -lt 3 ]; then kill $pids 2>/dev/null; else kill -9 $pids 2>/dev/null; fi
        sleep 1
    done
    pids=$(rig_pids | sort -u | tr '\n' ' ')
    rm -f "$RIG/preset"

    if [ -n "$pids" ]; then
        echo "error: these rig processes survived kill -9: $pids" >&2
        ps -o pid,args -p ${pids// /,} >&2
        exit 1
    fi
    if [ "$had" = 1 ]; then
        echo "Rig stopped. Nothing left running."
    else
        echo "Rig was not running. Nothing left running."
    fi
    local logdir
    logdir=$(current_log_dir)
    [ -n "$logdir" ] && echo "Logs from the last run: $logdir"
}

cmd_status() {
    local logdir pid
    logdir=$(current_log_dir)

    echo "PX4 SITL:"
    if has_session "$PX4_SESSION"; then
        pid=$(px4_pid | head -1)
        if [ -n "$pid" ]; then
            echo "  running, pid $pid, tmux session $PX4_SESSION"
        else
            echo "  tmux session $PX4_SESSION exists but no px4 process is running in it"
        fi
    else
        echo "  not running"
    fi
    local port
    for port in 18570 14580; do
        if udp_bound "$port"; then
            echo "  UDP $port bound$([ $port = 18570 ] && echo ' (GCS link; broadcasts to port 14550 on the LAN until a ground station answers)' || echo ' (onboard link, the controller talks to it from 14540)')"
        else
            echo "  UDP $port NOT bound"
        fi
    done

    if [ -n "$(px4_pid)" ]; then
        # PX4's client commands print into its own shell, not back to the
        # caller, so ask in the shell and read the pane. "GCS heartbeat valid"
        # only appears while a ground station's heartbeats are current.
        tmux send-keys -t "=$PX4_SESSION:" "mavlink status" Enter 2>/dev/null
        sleep 1
        local link
        link=$(tmux capture-pane -p -J -t "=$PX4_SESSION:" -S -300 2>/dev/null \
            | awk '/^instance #0/{b=""; f=1} /^instance #1/{f=0} f{b=b $0 "\n"} END{printf "%s", b}')
        if echo "$link" | grep -q 'GCS heartbeat valid'; then
            echo "  a ground station is connected now, at $(echo "$link" | awk '/partner IP/{print $3}')"
        else
            echo "  no ground station on the GCS link right now"
        fi
    fi

    echo "Tag controller:"
    if has_session "$CTL_SESSION"; then
        pid=$(controller_pid | head -1)
        if [ -n "$pid" ]; then
            echo "  running, pid $pid, tmux session $CTL_SESSION, preset $(cat "$RIG/preset" 2>/dev/null)"
            echo "  commit $(git -C "$MTC" log -1 --format='%h %cs %s' 2>/dev/null)"
            local log="$logdir/controller.log"
            if grep -q 'Found autopilot' "$log" 2>/dev/null; then
                echo "  has heard the autopilot"
            else
                echo "  has NOT heard the autopilot yet"
            fi
            # Heartbeats to the ground station start once the controller has
            # seen a GCS, so this is the line that means TagTracker is on the link.
            if grep -q 'Found gcs' "$log" 2>/dev/null; then
                echo "  has seen a ground station since it started, and sends it tag controller heartbeats"
            else
                echo "  has not seen a ground station since it started"
            fi
        else
            echo "  tmux session $CTL_SESSION exists but the controller process is not running"
        fi
    else
        echo "  not running"
    fi

    echo "Detection pipeline (runs only between start and stop detection):"
    local found=0 p
    for p in $(rig_pids); do
        case "$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)" in
            *iq_simulator.py*)     echo "  IQ simulator, pid $p"; found=1 ;;
            *airspyhf_decimator*)  echo "  decimator, pid $p"; found=1 ;;
            *pulse_detector.py*)   echo "  Python detector, pid $p"; found=1 ;;
            *uavrt_detection/uavrt_detection*) echo "  uavrt_detection (C++ detector), pid $p"; found=1 ;;
        esac
    done
    [ "$found" = 1 ] || echo "  idle"

    local stray
    stray=$(foreign_pids | sort -u | tr '\n' ' ')
    [ -z "$stray" ] || echo "Warning: PX4 or controller processes outside the rig: $stray"

    [ -n "$logdir" ] && echo "Logs: $logdir (controller's own logs under $RIG/Logs)"
    echo "VM disk: $(df -h --output=avail "$HOME" | tail -1 | tr -d ' ') free; PX4 flight logs use $(du -sh "$PX4_DIR/log" 2>/dev/null | cut -f1)"
    return 0
}

cmd_logs() {
    local which="${1:-controller}" lines="${2:-40}" logdir
    logdir=$(current_log_dir)
    [ -n "$logdir" ] || die "no rig logs yet"
    case "$which" in
        px4|controller) tail -n "$lines" "$logdir/$which.log" ;;
        *) die "logs takes px4 or controller" ;;
    esac
}

case "${1:-}" in
    start)  shift; cmd_start "$@" ;;
    stop)   cmd_stop ;;
    status) cmd_status ;;
    logs)   shift; cmd_logs "$@" ;;
    *)      sed -n '3,12p' "$0"; exit 2 ;;
esac
