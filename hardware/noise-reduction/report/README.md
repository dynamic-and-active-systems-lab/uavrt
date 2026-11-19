# Noise-reduction report

Draft 0.1, 2026-11-19. Two versions of the same report:

| File | What it is |
|---|---|
| `noise_report.pdf` | The PDF, built from `noise_report.tex` with `latexmk -pdf noise_report.tex`. |
| `uavrt-noise-reduction.html` | The interactive version: flight and spectrum explorers, the calibration at each tone level, and a noise-budget calculator. Self-contained; open it in any browser. |
| `uavrt-noise-reduction.artifact.html` | The same page without its `<head>`, for publishing as a claude.ai artifact (the host supplies the head). |
| `figures/` | The PDF's figures, made by `make_figures.py` from `../data/`. |
| `page_template.html`, `page_script.js` | Sources of the interactive page. The page is the template with `__DATA__` replaced by the data JSON and `__SCRIPT__` by the script. |

## Rebuilding after a new test

1. Add the test's notes under `../tests/<date>-<name>/`.
2. Extend `tools/noise_report_data.py` if the test is a new kind, then run it:
   `python3 tools/noise_report_data.py <folder holding the FLIGHT_TESTING_DATA test folders> <hub>`.
3. `python3 make_figures.py ../data figures`, then `latexmk -pdf noise_report.tex`.
4. `python3 build_page.py` rebuilds both HTML files. It escapes every non-ASCII character, so the page reads correctly even where a browser guesses the wrong text encoding (Safari did, opening the file from disk). Republish the `.artifact.html` file to the same artifact.
