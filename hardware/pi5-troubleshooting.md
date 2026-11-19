# Drone Pi 5 troubleshooting notes (Oct–Nov 2026)

Findings from debugging MavlinkTagController2 (Raspberry Pi 5 on the drone) and TagTracker (UniRC Pro 7), Oct 30 – Nov 2, 2026. There were three separate problems.

## Applicability: versions in use when these notes were written

These findings apply to the versions below. Before relying on a fix, check whether it is still needed. For example, problem 3 may be fixed upstream; check the MavlinkTagController2 issues and `setup/full_setup.sh` for `uart0_console`.

| Component | Version / commit | Date |
| --- | --- | --- |
| MavlinkTagController2 (`main`) | `584b42eb427f` "Heartbeat reports CPU thermal throttling and under-voltage (tunnel protocol v9)" | 2026-10-24 |
| TagTracker (`main`, GitHub HEAD) | `9eada79beff2` "add simple auto rotation screen". The UniRC build may be slightly older but is at least tunnel protocol v9 (Oct 24). | 2026-10-28 |
| TagTrackerTunnelProtocol (pinned by both) | `bbc0f0e3cece`, protocol **v9** | 2026-10-24 |
| mavlink-router (pinned by full_setup.sh) | `2362c620f483` (v4-16-g2362c62) | — |
| raspi-config (`trixie` branch, checked for problem 3) | `472d90964a8a` | checked 2026-11-02 |
| Raspberry Pi OS | 64-bit with desktop, Debian 13 (trixie), systemd 257.9, kernel 6.12.62+rpt-rpi-2712 | flashed 2026-11-02 |
| Raspberry Pi Imager | 2.0.12 | — |
| Pi 5 bootloader EEPROM | 2025-05-08 (1746713597); 2025-12-08 available but not applied | — |
| Hardware | Raspberry Pi 5 (8 GB), Pixhawk on TELEM2 at 921600, SIYI UniRC Pro 7 | — |

The repo commits are GitHub HEAD as of Nov 2, 2026, and are believed to match what was installed. To confirm on the Pi:

```bash
git -C ~/repos/MavlinkTagController2 log -1 --oneline
```

## 1. Red bar after updating MavlinkTagController2 (one-time transition)

**Symptom:** After `git pull --recurse-submodules`, `make`, `./setup_venv.sh` and `make test` (all passing), TagTracker showed a red controller bar.

**Cause:** Commit `b69e0a3` (Oct 15, 2026) moved auto-start from an `@reboot` crontab entry to the `mavlink-tag-controller` systemd service and deleted the old script. Building alone doesn't change how the controller starts, so cron kept calling a missing script.

**Fix:** After updates, rerun `bash ~/repos/MavlinkTagController2/setup/install.sh` and reboot.

## 2. Slow boots, black screen, emergency mode (failing microSD card)

**Symptoms:**
- Boots of 1.5–4.5 minutes, varying from boot to boot.
- Black screen with a blinking cursor, or a desktop with only a mouse pointer.
- Occasional emergency mode after a battery pull.
- Heartbeats still reached TagTracker, so the Pi wasn't actually hung.
- Last field season showed the same pattern, getting worse over the deployment until the card was replaced.

**Cause:** The Samsung microSD card (`manfid 0x1b`, `ED2S5`, 128 GB) stalled for about 30 s at a time. The kernel logged `mmc0: Card stuck being busy! __mmc_poll_for_busy`, and boots showed repeated ~33-second gaps in the journal. Disabling SD command queueing (`dtparam=sd_cqe=off`) and running `fstrim` did **not** help; those were dead ends.

**Fix:** Fresh install on a SanDisk Extreme PLUS 128 GB card. Five consecutive boots, including one battery pull, each took about 12.5 s, with no long gaps. (One of the two new cards was dead on arrival. It reported 32.1 MB in `diskutil list` and gave I/O errors on write.)

**How to check boot health:** Logging must be persistent; see Diagnostics below.

```bash
for b in -4 -3 -2 -1 0; do
  echo -n "boot $b: "
  journalctl -b $b --no-pager | grep -m1 "(kernel)" | sed 's/.*= //'
  journalctl -b $b --no-pager -o short-monotonic | awk -F'[][]' '{t=$2+0; if (p && t-p>25) n++; p=t} END {print "   long gaps:", n+0}'
done
journalctl -k --no-pager | grep -i stuck
```

## 3. Red bar on a fresh Pi 5 install (serial0 points at the wrong UART)

**Symptom:** After a fresh install, both services were running, but the controller log stopped at `Waiting for autopilot heartbeat...`. Pixhawk settings were correct (`MAV_1_CONFIG` TELEM2, `SER_TEL2_BAUD` 921600).

**Cause:** On a Pi 5, `/dev/serial0` pointed to `ttyAMA10`, the debug connector, instead of `ttyAMA0`, UART0 on GPIO 14/15 wired to TELEM2. raspi-config's serial steps used by `full_setup.sh` only add `dtparam=uart0=on`, not `dtparam=uart0_console`, which is what moves `serial0` to UART0. The old card had the line, apparently added by hand. Reported as [MavlinkTagController2 issue #187](https://github.com/DonLakeFlyer/MavlinkTagController2/issues/187).

**Fix:**

```bash
echo "dtparam=uart0_console" | sudo tee -a /boot/firmware/config.txt
sudo reboot
ls -l /dev/serial0                        # -> ttyAMA0
systemctl is-active serial-getty@ttyAMA0  # inactive (no login console)
```

**Caution:** Turning serial off in raspi-config on a Pi 5 deletes every `dtparam=uart0…` line, including this one.

## Fresh install checklist

1. In Raspberry Pi Imager, choose Raspberry Pi OS (64-bit, with desktop). Set username `pi`, hostname `raspberrypi`, Wi-Fi country US, and enable SSH. Let verification finish before ejecting.
2. On the Mac: `ssh-keygen -R raspberrypi.local`.
3. On the Pi:

   ```bash
   sudo apt update && sudo apt full-upgrade -y
   wget https://raw.githubusercontent.com/DonLakeFlyer/MavlinkTagController2/main/setup/install.sh
   bash install.sh
   ```

4. Add `dtparam=uart0_console` (see problem 3) and reboot.
5. Add field Wi-Fi networks:

   ```bash
   sudo nmcli connection add type wifi con-name "<name>" ssid "<SSID>" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "<password>"
   ```

6. Verify the controller has found the autopilot and TagTracker shows a green bar.
7. Check the fixed IP on the field router (see below).

### Fixed IP on the field TP-Link router (DHCP reservation)

The portable TP-Link field router (Wi-Fi `TP-Link_E417`) has a DHCP reservation that always gives the Pi the same address, so it is easy to find when headless. Reserved address: `192.168.0.100`.

The reservation is stored on the router and tied to the Pi 5's built-in Wi-Fi MAC address, not to the SD card. A fresh install or card swap on the same Pi keeps it. It only needs redoing if the router is reset or a different Pi is used.

To set it up again:

1. On the Pi, find the Wi-Fi MAC address and current IP: `ip link show wlan0` (the `link/ether` value) and `hostname -I`.
2. Log in to the router's admin page from a device on its network. The address is the gateway, usually `192.168.0.1` or `192.168.1.1`.
3. Find the reservation settings. They may be called DHCP Reservation, Address Reservation or Static Lease, usually under Advanced, Network or LAN settings.
4. Add a reservation pairing the Pi's Wi-Fi MAC with an address on the same subnet, preferably outside the router's dynamic DHCP range. Save.
5. Reconnect the Pi with `sudo nmcli connection up TP-Link_E417`, or reboot, then confirm with `hostname -I`.

Connect with `ssh pi@192.168.0.100`. After a fresh install, clear the old host key first with `ssh-keygen -R 192.168.0.100`.

## Diagnostics

- **Keep logs across reboots (temporary).** Raspberry Pi OS keeps the journal in RAM. To save it for debugging:

  ```bash
  sudo mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nStorage=persistent\n' | sudo tee /etc/systemd/journald.conf.d/99-persistent.conf
  ```

  Remove the file afterward to cut writes to the card.
- **Bar colors in TagTracker:**
  - Red: no heartbeats.
  - Orange: heartbeats arriving, but the Pi reports under-voltage or throttling (`vcgencmd get_throttled`).
  - A "protocol mismatch" popup means the controller and TagTracker builds are out of sync.
- **Timeline of a boot:** `journalctl -b -o short-monotonic` shows time since boot, which is unaffected by clock jumps when the controller sets the clock from GPS.
- **Card identity:** `cat /sys/block/mmcblk0/device/{manfid,oemid,name}`. `0x1b` is Samsung, `0x03` is SanDisk.

## Field practices

- Use `sudo poweroff` before pulling the battery when practical. Power cuts caused filesystem damage (emergency mode) on the old card.
- If boot times start creeping up during a deployment, run the boot-health check above before it gets bad.
- Keep a spare card cloned from a known-good install.
- Longer term, consider NVMe boot or a read-only OS (raspi-config overlay filesystem) for robustness against power cuts.

## Record of this session (Nov 2, 2026)

- **Old card:** Samsung 128 GB (`ED2S5`), retired as bad. Its `config.txt` had `dtparam=uart0=on`, `dtparam=uart0_console` and `dtparam=sd_cqe=off`; the last was added during debugging and isn't needed. Its Wi-Fi country was set to GB, which is wrong for the US; the new install uses US.
- **New card:** SanDisk Extreme PLUS 128 GB, fresh install as described above. Persistent journal turned back off after testing. Bootloader EEPROM left at 2025-05-08.
- **Second new card:** dead on arrival (reported 32.1 MB). Return it and get a replacement. Clone the working card onto the replacement once the drone has flown with it.
- **Saved Wi-Fi networks on the old card:** only `TP-Link_E417`. There was no `wpa_supplicant.conf`; networks are managed by NetworkManager.
- **Log archive from the old card (`~/Logs`, detector logs from Sep 30, 2026):** `OneDrive-NorthernArizonaUniversity/FLIGHT_TESTING_DATA/2026-11-02-Drone RPI Log Archive for Fresh SD Card/`
- **Issue filed** on MavlinkTagController2 for the Pi 5 `serial0` problem (problem 3): https://github.com/DonLakeFlyer/MavlinkTagController2/issues/187. Don was emailed a summary.

## Open items

- Test a battery pull on the full drone and confirm the green bar returns.
- Optional: apply the newer bootloader with `sudo rpi-eeprom-update -a` and reboot.
- Watch boot times during the next deployment.
