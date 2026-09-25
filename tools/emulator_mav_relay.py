#!/usr/bin/env python3
"""Connect TagTracker in an Android emulator to the simulated aircraft (tools/sim_rig.sh).

The rig's PX4 broadcasts MAVLink to port 14550 on the LAN, which the Mac hears but
the emulator does not: the emulator sits behind its own NAT, and on current system
images `adb emu redir` does not reach the app either. So the app sends out to the
Mac instead, which the emulator's NAT carries both ways, and this relay passes
packets between the two.

    tools/sim_rig.sh start
    tools/emulator_mav_relay.py          # leave running; Ctrl-C to stop

In TagTracker on the emulator, add a UDP comm link with local port 14570 and one
target host, 10.0.2.2 port 14551 (10.0.2.2 is the Mac as seen from the emulator),
set to connect automatically. TagTracker on the Mac must not be running, since
both want port 14550.

Written for task 0-4 on 2026-09-24, which used it to run a detection flight on
API 28 and API 33 emulators.
"""
import select
import socket
import time

px4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
px4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
px4.bind(("0.0.0.0", 14550))
emu = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
emu.bind(("0.0.0.0", 14551))

px4_addr = emu_addr = None
up = down = 0
last = time.time()
while True:
    for s in select.select([px4, emu], [], [], 1.0)[0]:
        data, addr = s.recvfrom(65535)
        if s is px4:
            px4_addr = addr
            if emu_addr:
                emu.sendto(data, emu_addr)
                down += 1
        else:
            emu_addr = addr
            if px4_addr:
                px4.sendto(data, px4_addr)
                up += 1
    if time.time() - last > 10:
        print(f"rig->emulator {down}  emulator->rig {up}  rig {px4_addr}  emulator {emu_addr}", flush=True)
        last = time.time()
