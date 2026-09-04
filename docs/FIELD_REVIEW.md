# Field Review — post-flight analysis on the Herelink

**Status:** design settled, not yet built. Prototype next.
**Created:** 2026-09-02, from a working session with the PI.
**Spans:** `uavrt_postflight` (prototype) and `TagTracker` (delivery).

---

## Start here

If you are an agent picking this up:

1. Read this whole document. It is the specification.
2. Work in **`uavrt_postflight/python/`**. Read that repo's `CLAUDE.md` first — it has real hazards.
3. Build the prototype as a **new entry point**, not by growing `pulseplotter.py`. Shared primitives go in `analysis.py`.
4. Do **not** touch `TagTracker` yet. Section 7 says why.

Everything here came from the PI's field experience and from Mohammadi/Shafer/Flikkema 2026. Where a number or a claim is uncertain, it says so.

---

## 1. The problem

After a flight the operator needs one thing: **where do I walk next?**

Today that means: land, pull the pulse CSV off the Herelink or the aircraft onto a USB stick or SD card, carry it to a laptop, open MATLAB, eyeball the strongest signal on the plot, then read coordinates off the screen while cross-referencing Google Maps on a phone to figure out where that actually is.

In the PI's words: *"It is a real pain."*

This happens **between flights, standing in the field**. The New Zealand case studies in the 2026 paper are exactly this loop — Case 1 took four flights converging on one kiwi, Case 2 took three. Each flight's result decides where the next one goes. The laptop round trip is in the middle of that loop.

The data is already on the Herelink: `TagTracker`'s `CSVLogManager` writes `Pulse-<timestamp>.csv` and `Rotation-<N>.csv` there. Nothing needs to move. That single fact is what makes on-device analysis worth building.

## 2. Scope

**In — the core loop:**

- Recall a previous flight's pulse log for review
- Select a portion of it (time, altitude, and ideally a spatial box)
- See the interpolated signal raster and contours over the map
- **Identify the strongest-signal position and get its coordinates** — this is the headline feature
- Compute a bearing from the selected portion
- Show the flight track, so "flew there, heard nothing" is distinguishable from "never flew there"
- Filter by tag

**Out — deliberately:**

| Excluded | Why |
|---|---|
| Divergence mode | Bench analysis, not a field decision |
| Multiple simultaneous bearings | One at a time is enough in the field |
| Grid spacing, smoothing window, confirmed/unconfirmed toggle | Behind a config menu — changeable, not front and centre |
| Operator's own position, walk-to heading and distance | **Handled by a separate app the PI is building (`~/Developer/tritrack`).** Do not duplicate it. |
| KMZ export | Nice to have. Include if cheap, drop if it fights the platform. |

**Defaults:** confirmed pulses only. Everything else stays on the analysis screen.

## 3. Feature detail

### Tag selection — required
Logs are multi-tag; Cumbria carried four. Without a tag filter the raster blends transmitters and the bearing is meaningless. This is the first control, not an option.

### Flight track — required
The raster only exists where pulses were *received*. Without the track underneath you cannot tell "flew there, heard nothing" from "never flew there", and those imply opposite next moves. In Case 1 the strongest detections came immediately after takeoff, which only means something if you can see where the rest of the flight went.

### Selection: time, altitude, spatial
Time is the primary control. **Altitude matters specifically when the flight path passes back over the takeoff location** — near-field pulses from directly overhead contaminate the surface. A spatial box drawn on the map is the most natural gesture on a touchscreen and would also handle excluding an outbound transit leg; treat it as desirable, not required for a first pass.

### Strongest-signal position — the headline
Report the peak of the interpolated surface with its latitude and longitude, in a form that can be read aloud or typed into another app. This is what replaces the eyeball-and-Google-Maps step, and it is the single feature that justifies the whole thing.

**Label it "strongest signal", never "tag position".** Mohammadi 2026 documents received strength peaking when the aircraft is slightly *downhill* of the tag — the monopole's toroidal pattern combined with terrain-dependent propagation — and attributes the 20–30 m residual in both kiwi localisations to exactly this. The PI's position: the peak is *"the indication of the closest spot and the user's human intelligence takes over after that."* The UI should support that judgement, not pre-empt it. A biologist in Cumbria with this tool will not know the offset exists unless the screen says so.

### Bearing
A single bearing computed from the current selection, with a confidence indication. Advanced position estimation can come later.

### Contours
Contour lines over the raster. Verify they read on a 7-inch screen in sunlight before committing to them.

## 4. Data

Input is the pulse CSV `TagTracker` already writes. `uavrt_postflight/python/readpulsetable.py` parses all four historical header variants positionally and rejects the interleaved 4-field rotation records — reuse it, do not re-derive it.

Columns available: `command_id, tag_id, frequency_hz, start_time_seconds, predict_next_start_seconds, snr, stft_score, group_seq_counter, group_ind, group_snr, noise_psd, detection_status, confirmed_status, lat, lon, alt_rel`.

Filters therefore map directly: tag → `tag_id`, confirmed-only → `confirmed_status`, time → `start_time_seconds`, altitude → `alt_rel`.

## 5. What already exists

In `uavrt_postflight/python/`:

| Module | Provides | Reusable as-is? |
|---|---|---|
| `readpulsetable.py` | Log parsing, all four variants, rotation-record rejection | Yes |
| `analysis.py` | `build_grid` (linear interpolation, NaN outside the convex hull), `movmean`, `estimate_bearing` (magnitude-weighted circular mean of gradient directions, returns bearing/confidence/spread), `color_bins` | Yes |
| `geodesy.py` | `geo2enu` / `enu2geo`, flat-earth WGS84, agrees with a rigorous ECEF transform to under 5 cm over 1 km | Yes |
| `kmzwrite.py` | KMZ with styles declared once, packaged icon, GroundOverlay raster, contour folder | If KMZ stays in scope |

**Missing, and the actual work:**

- Peak finding on the interpolated grid, returning lat/lon
- Contour extraction as polylines (for later handoff to a map renderer, not a matplotlib figure)
- The filter set: tag, confirmed, time, altitude, spatial box
- Grid spacing **derived from the flown extent** rather than a fixed metre value — a 200 m rotation and a 2 km lawnmower need different grids, and a hardcoded number will look broken on one of them

## 6. Prototype first, in Python

Build it in `uavrt_postflight/python/` as a separate entry point. Do not grow `pulseplotter.py`: that is the desktop bench, and this is a different product with a deliberately smaller control set. Shared primitives belong in `analysis.py` so both use one implementation.

**The deliverable of the prototype is settled behaviour, not a UI.** Specifically, answers to:

- What grid spacing rule works across both a tight rotation and a wide lawnmower?
- Do contours read usefully at small scale, or is the raster enough?
- What does the peak finder do when the surface has two lobes?
- On flights where the tag position is known — Cumbria Tag 42, and the NZ cases — how far is the reported peak from truth, and does it sit downhill as the paper predicts?

Test data is outside the repo, under `…/OneDrive-…/FLIGHT_TESTING_DATA/`. Known-good cases from `uavrt_postflight/CLAUDE.md`: `2025-11-21-Cumbria-Day5-Fri` (4 tags, known tag position), `2023-08-18-NAVHDA Site` (headerless, plus rotation rows), `2025-01-13-Raymond Park Scan Flights`.

**Constraint:** MATLAB cannot be assumed. Verify numerics by transliteration and by running against real logs, and say which method was used. Never claim MATLAB code has been tested.

## 7. Delivering it in TagTracker

**Do not start this until the prototype settles and Don Gagne has been asked.** See §8.

### Where it goes

`TagTracker` is a QGroundControl custom build, and QGC is explicitly designed for this. Three extension points already in use, in increasing order of invasiveness:

1. **Model append** — `AnalyzeView.qml` builds its page list from `QGroundControl.corePlugin.analyzePages`, supplied by `CustomPlugin` / `CustomOptions` in `custom/`. **This is the right home.** QGC's own log-download and MAVLink-inspector pages live there, so post-flight review belongs beside them. Adding a page is a few lines in files the custom build already owns, plus new QML that is entirely yours.
2. **Whole-file override** — `custom/src/ResourceOverrides/FlightDisplay/` already replaces `FlyViewToolStrip.qml`, `FlyViewCustomLayer.qml` and others by matching qrc path.
3. **Full model replacement** — `custom/src/SettingsPagesModel.qml` replaces QGC's settings list outright.

None requires editing upstream QGC.

**Structure it so it survives:** analysis logic as plain C++ in `custom/src/` with no QGC dependencies — unit-testable, and unaffected by rebases if this ends up living on a long-lived fork. The QML page stays thin.

**What you get for free by being inside TagTracker:** the map, the tag database, CSV parsing in `CSVLogManager`, the SNR colour gradient, `PulseMapItem`. A standalone app rebuilds all of it, and would realistically be written in the same Qt stack by the same person — so separation would be organisational, not technical, and would cost more.

### Building for the Herelink

`.github/workflows/herelink-linux.yml` is a working recipe:

| | |
|---|---|
| Qt | **6.6.3** |
| ABI | **arm64-v8a** only (`QT_ANDROID_BUILD_ALL_ABIS=OFF`) |
| Min SDK | **25** |
| Target SDK | 35 |
| Signing | `custom/android/debug.keystore` |

```bash
$QT_ROOT/bin/qt-cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DQT_ANDROID_ABIS=arm64-v8a \
  -DQT_ANDROID_BUILD_ALL_ABIS=OFF \
  -DQT_HOST_PATH=$QT_ROOT/../macos
cmake --build build --target all
# APK in build/android-build/ ; adb install -r
```

> **The Qt 6.6.3 pin is load-bearing.** `cmake/CustomOptions.cmake` sets min SDK 25 only while Qt < 6.7; at 6.7+ it becomes 28, which may drop Herelink support entirely. Do not casually upgrade Qt.

macOS is a supported Qt host for Android builds but less trodden than the CI's Linux. If the toolchain fights, running that same workflow via `workflow_dispatch` on a fork is the known-good fallback.

## 8. Sequencing, and one process point

1. This document. Done.
2. Python prototype against real logs. **Next.**
3. **Ask Don before building the TagTracker side.**
4. Fork branch → PR, or long-lived fork, depending on 3.

**On step 3.** A large unsolicited PR to an unpaid volunteer's repository is the worst outcome: declined or stalled, leaving a stranded implementation in a codebase the PI does not control. Three possible answers, each implying different work:

- *Wants it upstream* → fork branch, PR when ready.
- *Would rather not own it* → long-lived fork branch. Workable — `custom/` is designed for it — but push harder on keeping the analysis core dependency-free so rebases stay cheap.
- *Has opinions about placement* → far cheaper to hear before building against `analyzePages`.

A short note describing the field problem, what the prototype does, and "would you want this in TagTracker or should I carry it on a fork?" costs nothing and de-risks everything after it.

## 9. Open questions

- Does the Herelink have enough compute for interpolation and gradient at a useful grid size? Almost certainly yes, but unmeasured.
- Do contours read at 7 inches in sunlight, or is the raster alone better?
- Should the field view read `Rotation-<N>.csv` as well as `Pulse-*.csv`, or only whole-flight logs?
- Is KMZ export worth the platform friction on Android, given the PI called it nice-to-have?
- How does this relate to `tritrack`, the PI's separate app handling operator position and walk-to bearing? Boundary is clear today; worth revisiting so the two do not converge on the same job.
