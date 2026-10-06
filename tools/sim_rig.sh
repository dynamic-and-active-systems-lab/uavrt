#!/usr/bin/env bash
#
# Flight simulation rig, driven from the Mac.
#
#   tools/sim_rig.sh start [preset]   start PX4 SITL and the tag controller in the VM
#   tools/sim_rig.sh stop             stop both, leaving nothing running
#   tools/sim_rig.sh status           what is running in the VM, and whether the Mac hears it
#   tools/sim_rig.sh logs [px4|controller] [lines]
#
# The aircraft side (PX4 SITL, MavlinkTagController2 --simulator and everything it
# spawns) runs in the Parallels VM under tmux, so it outlives this command.
# TagTracker runs on the Mac and finds the vehicle by its usual UDP auto-connect
# on port 14550: PX4's ground station link broadcasts there across the LAN.
#
# Presets. Signal levels, applied to the tags TagTracker uploads:
#   strong (default), moderate, marginal, below-marginal, silent, competing, power-line
# Simulator scenarios, used only if no tags are uploaded:
#   weak, noise-only, two-tags, distant, dropout, gap, rate-switch
#
# The VM is reached with `ssh $UAVRT_VM` (default parallels@10.211.55.3), which
# must work without a password prompt; see the "uavrt-vm" entry in ~/.ssh/config.
# The key is ECDSA P-256 because this Mac's managed ssh policy
# (/etc/ssh/crypto.conf) accepts no other key type; an ed25519 key is silently
# never offered.
# To watch a process live: ssh -t parallels@10.211.55.3 tmux attach -t rig-controller
# (or rig-px4 for the PX4 shell); detach with Ctrl-b d.
#
# One-time VM setup, done 2026-09-23 (start says which piece is missing):
#   sudo apt install tmux
#   sudo ufw allow from 10.211.55.0/24 to any port 22 proto tcp
#   git clone https://github.com/DonLakeFlyer/MavlinkTagController2 ~/uavrt-rig/repos/MavlinkTagController2
#   cd ~/uavrt-rig/repos/MavlinkTagController2 && make controller decimator && ./setup_venv.sh
#   ln -s ~/repos/uavrt_detection ~/uavrt-rig/repos/uavrt_detection
# PX4 SITL is the existing build in ~/repos/PX4-Autopilot. To move the rig to newer
# controller code, git pull in its checkout and make again, keeping the tunnel protocol
# commit (TunnelProtocol GIT_TAG in its CMakeLists.txt) equal to TagTracker's
# (custom/CMakeLists.txt), or the two will misread each other's messages.

set -uo pipefail

VM="${UAVRT_VM:-parallels@10.211.55.3}"
HERE="$(cd "$(dirname "$0")" && pwd)"
VM_SCRIPT="$HERE/sim_rig_vm.sh"
REMOTE_SCRIPT='uavrt-rig/bin/sim_rig_vm.sh'   # relative to the VM user's home

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=5 "$VM")

usage() { sed -n '3,8p' "$0"; exit 2; }

case "${1:-}" in
    start|stop|status|logs) ;;
    *) usage ;;
esac

if ! "${SSH[@]}" true 2>/dev/null; then
    cat >&2 <<EOF
error: cannot ssh to $VM without a password.
  Check the VM is running and at that address (prlctl list -a shows its state).
  If the key is not installed yet, run once, entering the VM password:
    ssh-copy-id -o BatchMode=no -i ~/.ssh/id_ecdsa_uavrt_vm.pub $VM
EOF
    exit 1
fi

# Install the current VM half, then run it. One ssh call: cat reads this
# script from stdin, then the installed copy runs with the arguments.
args=""
for a in "$@"; do args+=" $(printf '%q' "$a")"; done
"${SSH[@]}" "mkdir -p ~/uavrt-rig/bin && cat > ~/$REMOTE_SCRIPT && chmod +x ~/$REMOTE_SCRIPT && ~/$REMOTE_SCRIPT$args" < "$VM_SCRIPT"
rc=$?

# From the Mac's side: is PX4's broadcast arriving where TagTracker listens?
# Only checked with TagTracker closed. Once TagTracker is connected, PX4 sends
# to it directly instead of broadcasting, and macOS delivers those packets to
# TagTracker's socket alone, so a listener here would hear nothing and report
# a working link as dead. With TagTracker open, PX4's own view (above) is the check.
if [ "$1" = status ] || { [ "$1" = start ] && [ $rc -eq 0 ]; }; then
    echo "On the Mac:"
    if pgrep -x TagTracker >/dev/null; then
        echo "  TagTracker is running (while PX4 is up, its ground station line above says whether TagTracker is connected)"
        exit $rc
    fi
    echo "  TagTracker is not running"
    python3 - "${VM#*@}" <<'EOF'
import socket, sys, time
vm = sys.argv[1]
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if hasattr(socket, "SO_REUSEPORT"):
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
try:
    s.bind(("0.0.0.0", 14550))
except OSError as e:
    print(f"  could not listen on UDP 14550 to check ({e.strerror}); TagTracker may hold it exclusively")
    sys.exit(0)
s.settimeout(0.5)
n, end = 0, time.time() + 2
while time.time() < end:
    try:
        _, (host, _) = s.recvfrom(4096)
        n += host == vm
    except socket.timeout:
        pass
if n:
    print(f"  MAVLink from the VM is arriving on UDP 14550 ({n} packets in 2 s)")
else:
    print("  nothing from the VM on UDP 14550 in 2 s: TagTracker will not see the vehicle")
EOF
fi
exit $rc
