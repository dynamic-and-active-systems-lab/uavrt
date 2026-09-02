#!/usr/bin/env python3
"""
replay_iq_udp.py - Replay a recorded uavrt_detection IQ file over UDP.

Feeds a `data_record.*.bin` recording to a running detector so the detector can be
exercised on real recorded signal with no SDR, no Pi, and no channelizer.

WIRE FORMAT  (this is the part that is easy to get wrong)
---------------------------------------------------------
The detector reads fixed-size datagrams of `channelizerSampleFrameSize` = **1024
complex float32 samples**, but the first sample is NOT signal - it is a TIMESTAMP:

    uavrt_detection.m:
        timeStampRaw     = dataReceived(1);
        timeStampSec     = typecast(real(timeStampRaw), 'uint32');
        timeStampNanoSec = typecast(imag(timeStampRaw), 'uint32');
        iqData           = dataReceived(2:end);          % 1023 samples

`typecast` REINTERPRETS the four bytes of the float32 as a uint32 - it does not
convert numerically. So the timestamp sample is built by writing the raw bytes of
each uint32 into a float32 slot.

Each datagram is therefore:

    [ sec:uint32 | nsec:uint32 ]  followed by  1023 x (I:float32, Q:float32)
    = 8 bytes + 8184 bytes = 8192 bytes

The recording on disk contains ONLY the IQ payload - `asyncWriteBuff` is fed
`iqData`, i.e. post-timestamp-strip - so timestamps must be synthesised here.

Timestamps are generated from the CURRENT wall clock and advanced by 1023/Fs per
datagram. Replaying the original 2023 timestamps would trip the detector's
staleness check (uavrt_detection.m:252) and the buffer would be flushed forever.

USAGE
-----
Start the detector FIRST and wait for "Starting processing...", then:

    python3 replay_iq_udp.py data_record.2.5.bin --port 20000 --fs 3750

Match --port and --fs to the detector config (portData / Fs).
Mini path: port 20000, Fs 3750.   HF+ path: port 10000, Fs 3840.
"""

import argparse
import os
import socket
import struct
import sys
import time

BYTES_PER_COMPLEX = 8       # float32 I + float32 Q
FRAME_COMPLEX = 1024        # channelizerSampleFrameSize
PAYLOAD_COMPLEX = FRAME_COMPLEX - 1   # 1023, first slot is the timestamp


def timestamp_sample(t_posix):
    """Build the 8-byte leading sample: uint32 seconds and uint32 nanoseconds,
    written as raw bytes into the two float32 slots (MATLAB `typecast`)."""
    sec = int(t_posix)
    nsec = int(round((t_posix - sec) * 1e9))
    if nsec >= 1_000_000_000:          # rounding can carry
        sec += 1
        nsec -= 1_000_000_000
    return struct.pack('<II', sec & 0xFFFFFFFF, nsec)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('binfile', help='data_record.*.bin recording to replay')
    ap.add_argument('--ip', default='127.0.0.1', help='destination IP (default 127.0.0.1)')
    ap.add_argument('--port', type=int, default=20000,
                    help='destination UDP port; must match portData in the detector config')
    ap.add_argument('--fs', type=float, default=3750.0,
                    help='sample rate in Hz; must match Fs in the detector config')
    ap.add_argument('--repeat', type=int, default=1, help='replay the file N times (default 1)')
    ap.add_argument('--fast', action='store_true',
                    help='send as fast as possible; the detector WILL drop packets. Plumbing check only.')
    ap.add_argument('--start-delay', type=float, default=2.0,
                    help='seconds to wait before sending (default 2)')
    args = ap.parse_args()

    if not os.path.isfile(args.binfile):
        sys.exit(f'error: no such file: {args.binfile}')

    nbytes = os.path.getsize(args.binfile)
    if nbytes % BYTES_PER_COMPLEX:
        sys.exit(f'error: {nbytes} bytes is not a whole number of complex float32 samples')

    n_complex = nbytes // BYTES_PER_COMPLEX
    n_frames = n_complex // PAYLOAD_COMPLEX
    leftover = n_complex - n_frames * PAYLOAD_COMPLEX
    payload_bytes = PAYLOAD_COMPLEX * BYTES_PER_COMPLEX
    frame_period = PAYLOAD_COMPLEX / args.fs

    print(f'file        : {args.binfile}')
    print(f'size        : {nbytes} bytes = {n_complex} complex samples '
          f'({n_complex / args.fs:.2f} s at {args.fs:g} Hz)')
    print(f'datagrams   : {n_frames} x (1 timestamp + {PAYLOAD_COMPLEX} IQ) = 8192 bytes each', end='')
    print(f'  (+{leftover} trailing samples, not sent)' if leftover else '')
    print(f'destination : {args.ip}:{args.port}')
    print(f'pacing      : {"none (--fast)" if args.fast else f"{frame_period * 1000:.2f} ms per datagram"}')

    with open(args.binfile, 'rb') as fh:
        iq = fh.read(n_frames * payload_bytes)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if args.start_delay > 0:
        print(f'\nwaiting {args.start_delay:g}s...')
        time.sleep(args.start_delay)

    try:
        for pass_num in range(1, args.repeat + 1):
            if args.repeat > 1:
                print(f'\n--- pass {pass_num}/{args.repeat} ---')
            t_wall_start = time.time()
            t_perf_start = time.perf_counter()
            for i in range(n_frames):
                stamp = timestamp_sample(t_wall_start + i * frame_period)
                sock.sendto(stamp + iq[i * payload_bytes:(i + 1) * payload_bytes],
                            (args.ip, args.port))
                if not args.fast:
                    slack = t_perf_start + (i + 1) * frame_period - time.perf_counter()
                    if slack > 0:
                        time.sleep(slack)
                if (i + 1) % 25 == 0 or i + 1 == n_frames:
                    print(f'\r  sent {i + 1}/{n_frames} datagrams '
                          f'({(i + 1) * PAYLOAD_COMPLEX / args.fs:6.2f} s of signal)', end='', flush=True)
            print(f'\n  elapsed: {time.perf_counter() - t_perf_start:.2f} s')
    except KeyboardInterrupt:
        print('\ninterrupted', file=sys.stderr)
        return 1
    finally:
        sock.close()

    print('\ndone.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
