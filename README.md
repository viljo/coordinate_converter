# Coordinate Converter

A production-ready Python/Flet desktop application that converts coordinates between
Swedish and global reference systems, including a bespoke RR92 (RFN) Helmert
transformation, SWEN17_RH2000 height support, and a CSV batch CLI.

> **Status:** reference implementation targeting Python 3.11+ on macOS. Most features
> run cross-platform, but packaging/signing is not included.

## Features
- Flet desktop UI with coordinate source/height selectors, precision controls, and a
  live OpenStreetMap preview via Leaflet.
- Robust free-text parser for DD, DMS, DDM, RT90 2.5 gon V, MGRS, and geocentric XYZ
  (WGS84 + RR92).
- Canonical transformation engine using PyProj with cached Transformer pipelines and a
  custom exact-rotation 7-parameter Helmert implementation for RR92.
- Ellipsoidal vs orthometric height handling with SWEN17_RH2000 geoid support.
- CSV batch CLI supporting multiple target CRS outputs in a single run.

## Quick Start
```bash
./start_app.sh
```

The helper script creates (or reuses) a local `.venv`, installs dependencies via
[`uv`](https://docs.astral.sh/uv/), and launches the desktop UI. Pass additional
arguments to forward them to the application entry point.

The first run downloads the SWEN17 geoid grid if PROJ is configured to fetch remote
resources. If the grid is missing a warning banner is shown.

## Usage
### Desktop UI
```bash
make run
```

Choose the **Input coordinate source** and **Input height reference** selectors to
spawn the relevant fields (e.g., WGS84 lat/lon, RT90 northing/easting, XYZ, MGRS).
After entering values, click **Convert** or press Enter. The **Output coordinate** and
**Output height system** selectors mirror the same options and render the chosen
representation only. Geographic outputs can be displayed as DD, DDM, or DMS via the
format dropdown.

Keyboard shortcuts (numeric input fields):
- **↑/↓**: ±1 in the focused box
- **Shift + ↑/↓**: ±10 in the focused box
- **Enter / focus-out**: commit edits and refresh map

### CSV CLI
```bash
python -m cli.csv_convert --in samples/input.csv --out output.csv \
  --from SWEREF99_GEO --to WGS84_GEO,RR92_XYZ,RT90_3021 --height RH2000
```

- `--from` supplies the default CRS when a row cannot be inferred.
- `--to` may contain multiple comma-separated targets.
- Height selection currently accepts `ELLIPSOIDAL` and `RH2000`. RFN heights are
  stubbed until authoritative parameters are published.

Unknown columns are preserved, and row-level errors are appended to a summary written
to stderr.

## Coordinate Reference Systems
| Code | Description |
| ---- | ----------- |
| `WGS84_GEO` | EPSG:4326 latitude/longitude (degrees). |
| `SWEREF99_GEO` | EPSG:4619 latitude/longitude. |
| `RT90_3021` | EPSG:3021 RT90 2.5 gon V (northing/easting). |
| `WGS84_XYZ` | EPSG:4978 Earth-Centered Earth-Fixed cartesian. |
| `RR92_XYZ` | Rikets referenssystem 1992 geocentric cartesian. |
| `MGRS` | WGS84 Military Grid Reference System strings. |

## Height Systems
- **Ellipsoidal**: h above GRS80/WGS84 ellipsoid.
- **RH2000**: H = h − N using the SWEN17_RH2000 geoid grid.
- **RFN**: Placeholder module pending publication of official transformation
  parameters; see `core/height_rfn.py`.

## Development
```bash
make fmt   # black
make lint  # ruff
make test  # pytest
```

Project layout:
```
src/
  app/main.py              # Flet desktop app entry
  app/map_view/leaflet.html# Leaflet map scaffold
  core/                    # Parser, CRS registry, transforms, heights
  cli/csv_convert.py       # CSV batch tool
```

## Tests & Samples
- Parser: `tests/test_parser.py`
- Helmert: `tests/test_helmert_rr92.py`
- Height placeholder: `tests/test_height_rfn.py`
- CLI: `tests/test_csv_cli.py`

Sample CSVs live under `tests/data` (created during tests).

## Screenshots
_Add screenshots of the UI in `docs/` once the visual design is finalised._

## License
Released under the MIT License. See [LICENSE](LICENSE).
