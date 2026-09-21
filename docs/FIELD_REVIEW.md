# Field Review — post-flight analysis on the Herelink

**Status:** Python prototype built and validated, 2026-09-04 (§6a). Open questions answered by the
PI 2026-09-12 (§9). Don Gagne asked and answered 2026-09-12: **branch, integrate, PR** — §8.
Rotation-file bearings are **deferred to phase 2** (§4a); phase 1 is the original scope plus the
signal-strength floor and sub-vertex peak refinement.

**Created:** 2026-09-02, from a working session with the PI.
**Spans:** `uavrt_postflight` (prototype) and `TagTracker` (delivery).

---

## Start here

If you are an agent picking this up:

1. Read this whole document. It is the specification.
2. Work in **`uavrt_postflight/python/`**. Read that repo's `CLAUDE.md` first — it has real hazards.
3. The first prototype is **already built** — `fieldreview.py`, primitives in `analysis.py`, results in §6a. Extend it; do not start over, and do not grow `pulseplotter.py`.
4. The current work is **phase 1**: the original scope plus the **signal-strength floor** (§3) and **sub-vertex peak refinement** (§3). §9a says what is still undecided about each.
5. **Rotation-file bearings are phase 2. Do not build them now.** §4a says why, and what has to happen first.
6. `TagTracker` integration is a **branch in a fork, then a PR** — Don has agreed to that shape. §7 for placement, §8 for order. Finish phase 1 in Python first.

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
- **A signal-strength floor the operator can drag** — added 2026-09-12
- Show the flight track, so "flew there, heard nothing" is distinguishable from "never flew there"
- Filter by tag

**Out — deliberately:**

| Excluded | Why |
|---|---|
| Divergence mode | Bench analysis, not a field decision |
| Multiple simultaneous bearings | One at a time is enough in the field |
| Grid spacing, smoothing window, confirmed/unconfirmed toggle | Behind a config menu — changeable, not front and centre |
| Operator's own position, walk-to heading and distance | **Handled by a separate app the PI is building (`~/Developer/tritrack`).** Do not duplicate it. |
| Sharing results to `tritrack` | Real, but not near term. §9 Q5. |
| Bearings from `Rotation-<N>.csv` | Wanted, and **deferred to phase 2** by the PI on 2026-09-12. §4a. |

KMZ export moved *in* on 2026-09-12: there is a macOS TagTracker build, and reviewing a flight and
exporting a KMZ back at a desk is a use the PI wants. §9 Q4 covers what "platform friction" meant
and what it costs.

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

**On interpolation and where the peak actually lands.** *Added 2026-09-12, answering the PI's
question.* He is right. `build_grid` interpolates linearly over a Delaunay triangulation, so the
surface is piecewise planar and its maximum is always **at a data vertex** — the reported position
can only ever be a pulse position. §6a records this as "the grid does not move the answer;
smoothing does". A fit with curvature puts the peak *between* samples, which is where it physically
belongs.

Scale it honestly before spending much on it. Measured error against truth is 22–41 m, dominated by
the downhill offset described below; median pulse spacing drives grids of 2.2–7.4 m, so vertex
quantisation is worth single-digit metres of that. Sub-vertex refinement buys a peak that does not
visibly jump between pulse positions as the selection changes, and an honest surface shape. It will
not find the tag.

The recommended shape, which is cheap and degrades gracefully:

- Keep **linear interpolation for the displayed raster**. It is bounded and cannot overshoot.
- Compute the **reported** peak by fitting a local quadratic in ENU to the pulses within a radius of
  the best vertex and taking the stationary point. Reject it and fall back to the vertex if the fit
  is not concave, or if the stationary point falls outside the neighbourhood it was fitted to.

Do **not** reach for a global smooth interpolant — thin-plate spline, biharmonic, RBF — for the
displayed surface. They ring and overshoot near data gaps, and §6a already found that the convex
hull stretches the surface over never-flown wedges wherever there is a transit leg. A smooth global
fit would invent a peak in a wedge nobody flew, which is the one failure this tool must not have.

**Label it "strongest signal", never "tag position".** Mohammadi 2026 documents received strength peaking when the aircraft is slightly *downhill* of the tag — the monopole's toroidal pattern combined with terrain-dependent propagation — and attributes the 20–30 m residual in both kiwi localisations to exactly this. The PI's position: the peak is *"the indication of the closest spot and the user's human intelligence takes over after that."* The UI should support that judgement, not pre-empt it. A biologist in Cumbria with this tool will not know the offset exists unless the screen says so.

### Signal-strength floor — required
*Added 2026-09-12.* The operator must be able to suppress weak returns so the strong area stands out
on its own. This is the answer to "do contours read at 7 inches in sunlight" — the PI's judgement is
that contours are *likely not needed* if a floor does the decluttering instead.

Express the floor as **decibels below the peak of the current selection**, not as an absolute SNR.
Absolute SNR is not comparable between flights, tags or SDR chains; "within N dB of the strongest"
is self-scaling and means the same thing everywhere. Everything below the floor renders as
background, not as a low-signal colour. Default 10 dB, which is the same window §6a's second-lobe
test already uses, so the floor and the lobe report agree by construction.

The floor is a *display and reporting* control, not a filter on the fit: it must not silently change
the interpolated surface underneath, or the peak would move as the operator drags the slider.

### Bearing
A single bearing computed from the current selection, with a confidence indication. Advanced position estimation can come later.

**Rotation files — phase 2, not now.** `Rotation-<N>.csv` postdates `pulseplotter2.m`, which is why
nothing reads it yet. Showing a bearing per rotation is wanted, but the PI deferred it on 2026-09-12
until the original scope is integrated. §4a has the format, the blocker, and what has to happen
first. Do not build it into phase 1, and do not design phase 1 around it beyond what §4a notes.

### Contours
Contour lines over the raster. Verify they read on a 7-inch screen in sunlight before committing to them.

## 4. Data

Input is the pulse CSV `TagTracker` already writes. `uavrt_postflight/python/readpulsetable.py` parses all four historical header variants positionally and rejects the interleaved 4-field rotation records — reuse it, do not re-derive it.

Columns available: `command_id, tag_id, frequency_hz, start_time_seconds, predict_next_start_seconds, snr, stft_score, group_seq_counter, group_ind, group_snr, noise_psd, detection_status, confirmed_status, lat, lon, alt_rel`.

Filters therefore map directly: tag → `tag_id`, confirmed-only → `confirmed_status`, time → `start_time_seconds`, altitude → `alt_rel`.

### 4a. Rotation logs — phase 2

**Deferred by the PI, 2026-09-12:** *"We'll hold off on the update on the rotation files for now and
plan to incorporate that once the basic fieldreview integration is complete for the original
scope."* Nothing here is phase 1 work. It is recorded now because it was established now, and
because one line of it constrains phase 1 — see the end of this section.

*Established 2026-09-12 by reading `TagTracker/custom/src/CSVLogManager.cc` and `CustomPlugin.cc`.*

**`Rotation-<N>.csv` is the same format as the pulse log.** `csvStartRotationPulseLog()` writes the
identical two-line header via `_csvWritePulseHeader()` and the identical rows via `_csvLogPulse()`.
It is not a different schema; it is the pulse log restricted to the pulses of one rotation. So
`readpulsetable.py` reads it unchanged, and a per-rotation bearing is `estimate_bearing` over the
whole file with no time selection needed.

**It does not contain a bearing.** The on-board answer from `BearingCalculator` arrives as a
`BEARING_RESULT` tunnel message and `CustomPlugin::_handleBearingResult` puts it on a `RotationInfo`
object in memory and into the debug log. It is never written to any CSV. `bearing_deg`, `r_squared`,
`n_valid_slices`, `best_snr` and `confirmed` are all lost when the app closes. A bearing shown from a
rotation file is therefore one the field view **recomputed**, not the one the aircraft reported — and
the two cannot be compared after the fact until Don logs the result.

**Blocker: the rotation files are deleted on every app start.** `CustomPlugin::init()` calls
`_csvLogManager.csvClearPrevRotationLogs()`, which removes every `Rotation-*.csv` in the log
directory. They are also numbered from zero per session rather than timestamped, so they would
collide across flights even if they survived. **As the code stands, post-flight review of rotation
bearings is impossible beyond the current app session.** The whole-flight `Pulse-<timestamp>.csv` is
unaffected — it is timestamped and never cleared — so everything else in §3 works today.

**What phase 2 needs first.** Three small changes, all in Don's code: timestamp the rotation files
or put each flight's in its own folder, stop clearing them at init, and append the `BEARING_RESULT`
fields so the on-board estimate is recoverable. A handful of lines. Raise them once the phase 1 PR
is in flight and there is a working feature to motivate them — they are far easier to ask for as
"this is what the next version needs" than as a speculative request attached to nothing.

**The one thing phase 1 must not do:** hard-wire the reader to a single whole-flight log. Rotation
files are the same format (above), so keeping the log loader indifferent to *which* file it was
handed — rather than assuming one timestamped `Pulse-*.csv` per session — costs nothing in phase 1
and is the whole of what phase 2 needs from it. Do not build a rotation UI; just do not preclude one.

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

### 6a. Prototype results, 2026-09-04

Built: `uavrt_postflight/python/fieldreview.py` (entry point), primitives in `analysis.py`,
`dem.py` and `validate_fieldreview.py` for validation, `test_fieldreview.py`. Full report
with the methods and their maths: `uavrt_postflight/DOCS/fieldreview-prototype.pdf`.
MATLAB never ran; everything is Python against real logs and synthetic surfaces.

Answers to the four questions above:

1. **Grid spacing:** half the median pulse spacing, held between 60 and 300 cells across the
   longer side, floor 1 m. Chose 2.2–7.4 m on every survey on disk. The reported position does
   not depend on it: a linear interpolant's maximum is at a vertex, so the strongest signal is
   always a (smoothed) pulse position. Smoothing moves it; the grid does not.
2. **Contours:** the raster alone finds the peak; contours add shape at no cost. Keep, switchable.
3. **Two lobes:** local maxima ranked by height, kept when within 10 dB of the strongest and
   with topographic prominence ≥ 2 dB, at most three. At the 3 dB window first proposed no real
   flight ever reported a second lobe. Also flagged: a *weak* surface (peak < 10 dB above the
   surface median) and a peak on the *edge* of the flown area.
4. **Against truth:** Cumbria tag 42, three surveys: 30, 22, 41 m, all NE, all 3–7 m lower than
   the tag. Ponui case 2, three flights: 119 → 36 → 22 m, final peak 2.5 m lower. Ponui case 1,
   four flights: 195 → 158 → 42 → 23 m, final peak 11 m lower. Downhill as the paper predicts,
   on every well-sampled flight with the tag inside the survey.

Two findings for the TagTracker side: the convex hull stretches the surface over never-flown
wedges wherever there is a transit leg, so the spatial box matters more than it looked; and the
bearing's confidence collapses on a bullseye, which is fine, it means the peak is the answer.

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

## 8. Sequencing

1. This document. Done.
2. Python prototype against real logs. Done, 2026-09-04 — §6a.
3. PI review of the open questions. Done, 2026-09-12 — §9.
4. Ask Don how he wants the TagTracker side handled. Done, 2026-09-12 — see below.
5. **Phase 1, Python:** signal-strength floor and sub-vertex peak refinement, on top of the existing
   prototype. **Next.**
6. **Phase 1, TagTracker:** branch in a fork, integrate against `analyzePages` (§7), PR to Don.
7. **Phase 2:** rotation-file bearings, and the three log changes they depend on. §4a.

**Don's answer, 2026-09-12.** Asked whether he wanted this upstream or carried on a fork, he said to
**make a branch, do the integration, and then open a PR.** That is the first of the three outcomes
this section used to hedge against, and it is the good one: the feature is wanted upstream, and the
placement question is settled by working in `custom/` the way §7 describes.

Two things follow from having an invitation rather than a maybe.

*The PR is still his to review, and its size is still the risk.* An invited PR that arrives as one
large drop is easier to decline than one that arrives as a reviewable branch. Keep the analysis core
— peak finding, floor, contours, bearing — free of QGC and Qt types so it reads as a self-contained
unit, and keep the UI wiring separate from it in the history. That also keeps rebases cheap against
an upstream that moves.

*Phase 1 only.* The rotation-log changes in §4a are his code, not this feature's, and they are
deferred. Do not put them in this PR or this branch.

## 9. Open questions

**Answered by the PI, 2026-09-12.** Kept in full — the answers changed the scope above, and a later
reader needs to see what was asked as well as what came back.

**1. Does the Herelink have enough compute?** *"I think so yes but we'll need to test."* Unchanged
as a risk, and it stays unmeasured until something runs on the device. The prototype's grid rule
(§6a: 60–300 cells across the longer side) bounds the work, so the honest statement is that the
sizing is known and the hardware is not. Measure it on the first Herelink build rather than
designing around a guess.

**2. Do contours read at 7 inches in sunlight?** *"Likely not needed"* — but a way to exclude weak
signal and focus on the strongest area is wanted instead, and *"user should easily be able to see
the strongest signal area."* This became the signal-strength floor in §3. Contours stay in the build
(§6a: they cost nothing) but demote to a config-menu toggle, defaulting off on the field screen.
The same answer raised the interpolation question, addressed in §3 under the headline feature.

**3. Should the field view read `Rotation-<N>.csv`?** Yes. *"The rotation csv files are new since I
built the original pulse plotter and we'll want to be able to read and display bearings measured
from the rotation csv as well."* Wanted, and **deferred to phase 2** in the same conversation:
build it once the original scope is integrated. §4a has the format, the blocker, and the one
constraint it puts on phase 1.

**4. "What platform friction?"** A fair challenge — the original line was vague. Concretely: writing
a KMZ is trivial anywhere, it is a zip of XML. The friction is Android-specific and has two parts.
*Scoped storage:* the Herelink build targets SDK 35 (§7), so the app cannot write a file to a path
the user names — it needs the Storage Access Framework or a share intent, which is a different code
path from the desktop's "write to this path". *Nothing to open it with:* a Herelink has no Play
Services and so no Google Earth, so a KMZ written on the controller has nowhere to go except a USB
stick — the exact trip this feature exists to avoid.

The PI's answer resolves it: *"there is a mac version of tagtracker and when the user gets back to a
desk they might review the flight and export the kmz."* That is a use with no friction at all.
So: KMZ export is **in**, `kmzwrite.py` already covers the core, expose it unconditionally on the
desktop builds, and on Android emit through a share intent rather than a path write. Its value on
the controller itself stays low, and that is fine — the desktop is where it earns its place.

**5. How does this relate to `tritrack`?** The boundary is by platform and by role, and it is
clean: *"tritrack is for manual localization on the ground. tagtracker is for the drone."* Sharing
positions, rasters or bearings between them is real but *"not near term"*, and `tritrack` could in
principle run on the Android side, so the two could eventually meet on one device. The PI's read is
that this is *"easy to build later"*.

The design consequence is small and worth taking now: keep the field view's outputs — peak lat/lon,
bearing, contour polylines — as plain serialisable values behind the UI, not as objects tangled into
the screen that renders them. That costs nothing today and is the whole of what a future handoff
needs. Do not build the handoff.

### 9a. New questions, raised by those answers

- **What does the local quadratic fit use as its neighbourhood radius,** and does it behave on a
  bullseye — the case §6a found where the bearing's confidence collapses because the aircraft
  circled the tag? A fit centred on a vertex with data all around it is the well-posed case; a fit
  centred on a vertex at the edge of the flown area is not, and §6a's edge-of-survey flag should
  probably suppress refinement entirely rather than report a refined peak.
- **Does the dB-below-peak floor interact badly with the second-lobe report?** At a 10 dB floor and
  a 10 dB lobe window they are the same threshold, so a reported second lobe sits exactly at the
  edge of visibility. That may be the right coupling or it may mean a lobe the operator is told
  about but cannot see. Decide deliberately.
- **Will Don take the rotation-log changes (§4a)?** Still unknown, and now a phase 2 question rather
  than a blocker on anything being built. If he declines, phase 2 shrinks to reading rotation files
  within the current app session only — materially smaller, and worth scoping as such rather than
  building and then discovering.
