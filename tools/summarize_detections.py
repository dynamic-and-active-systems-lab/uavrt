#!/usr/bin/env python3
"""
summarize_detections.py - Extract the run-invariant detection results from a
uavrt_detection diary log, so two runs can be compared meaningfully.

WHY THIS EXISTS
---------------
A raw diff of two diary logs is always dirty: the log carries wall-clock times,
per-stage elapsed seconds, and absolute POSIX interpulse times, all of which
change every run regardless of code. What must NOT change across a refactor is
the detection content: which pulses were found, at what frequency, at what SNR.

This tool pulls out only those invariants and prints a stable summary. Run it on
the before and after logs and diff the summaries.

USAGE
    python3 summarize_detections.py baseline_before.txt
    python3 summarize_detections.py before.txt after.txt      # compare two runs
"""

import argparse
import re
import sys

RE_PULSE = re.compile(r'Pulse at\s+([\d.]+)\s+Hz detected\.\s+SNR:\s+([\d.eE+-]+)')
RE_TRANSMITTED = re.compile(r'Transmitted\s+(\d+)\s+pulse\(s\)')
RE_SEGMENT = re.compile(r'BUFFER FULL, PROCESSING SEGMENT')
RE_PEAK = re.compile(r'Selected peak at frequency\s+([-\d.]+)\s+Hz')
RE_PARAMS = re.compile(r'Current interpulse params \|\| N:\s*(\d+), M:\s*(\d+), J:\s*(\d+)')
RE_STALE = re.compile(r'STALE DATA FLAG')
RE_WEIRD = re.compile(r'SOMETHING WEIRD HAPPENED')
RE_MISSING = re.compile(r'Missing samples detected')
RE_CACHE_HIT = re.compile(r'threshold values were pulled from cache')
RE_BUILDING = re.compile(r'Building thresholds')


def summarize(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    pulses = [(float(f), float(s)) for f, s in RE_PULSE.findall(txt)]
    return {
        'path': path,
        'pulses': pulses,
        'n_pulses': len(pulses),
        'n_transmitted': sum(int(n) for n in RE_TRANSMITTED.findall(txt)),
        'n_segments': len(RE_SEGMENT.findall(txt)),
        'peaks': [float(p) for p in RE_PEAK.findall(txt)],
        'params': sorted(set(RE_PARAMS.findall(txt))),
        'n_stale': len(RE_STALE.findall(txt)),
        'n_weird': len(RE_WEIRD.findall(txt)),
        'n_missing': len(RE_MISSING.findall(txt)),
        'n_cache_hits': len(RE_CACHE_HIT.findall(txt)),
        'n_threshold_builds': len(RE_BUILDING.findall(txt)) - len(RE_CACHE_HIT.findall(txt)),
    }


def render(d):
    out = []
    out.append(f"segments processed   : {d['n_segments']}")
    out.append(f"pulses detected      : {d['n_pulses']}")
    out.append(f"pulses transmitted   : {d['n_transmitted']}")
    out.append(f"threshold cache hits : {d['n_cache_hits']}")
    out.append(f"thresholds GENERATED : {d['n_threshold_builds']}"
               + ("   <-- NONDETERMINISTIC, see plan" if d['n_threshold_builds'] > 0 else ""))
    out.append(f"stale-data flushes   : {d['n_stale']}")
    out.append(f"missing-sample fills : {d['n_missing']}")
    out.append(f"peel-loop anomalies  : {d['n_weird']}"
               + ("   <-- the guarded condition FIRED" if d['n_weird'] > 0 else ""))
    out.append(f"interpulse params    : {', '.join('N=%s M=%s J=%s' % p for p in d['params']) or 'none'}")
    out.append('')
    out.append('detections (freq MHz, SNR):')
    for i, (f, s) in enumerate(d['pulses'], 1):
        out.append(f'  {i:3d}  {f:.6f}  {s:9.6f}')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('logs', nargs='+', help='one log to summarize, or two to compare')
    args = ap.parse_args()

    if len(args.logs) == 1:
        d = summarize(args.logs[0])
        print(f'=== {d["path"]} ===')
        print(render(d))
        return 0

    if len(args.logs) != 2:
        sys.exit('error: pass one log to summarize, or exactly two to compare')

    a, b = summarize(args.logs[0]), summarize(args.logs[1])
    print(f'A: {a["path"]}\nB: {b["path"]}\n')

    same = True
    for key, label in [('n_segments', 'segments'), ('n_pulses', 'pulses detected'),
                       ('n_transmitted', 'pulses transmitted'), ('n_weird', 'peel anomalies')]:
        flag = '' if a[key] == b[key] else '   *** DIFFERS ***'
        if a[key] != b[key]:
            same = False
        print(f'{label:22s} A={a[key]:<6} B={b[key]:<6}{flag}')

    if a['pulses'] == b['pulses']:
        print('\ndetection list         IDENTICAL')
    else:
        same = False
        print('\ndetection list         *** DIFFERS ***')
        for i in range(max(len(a['pulses']), len(b['pulses']))):
            pa = a['pulses'][i] if i < len(a['pulses']) else None
            pb = b['pulses'][i] if i < len(b['pulses']) else None
            if pa != pb:
                print(f'  #{i+1}: A={pa}  B={pb}')

    if a['n_threshold_builds'] or b['n_threshold_builds']:
        print('\nWARNING: at least one run generated thresholds from random trials.')
        print('         That run is not deterministic; re-run with a warm cache.')

    print('\nRESULT:', 'MATCH' if same else 'MISMATCH')
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
