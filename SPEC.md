# Coordinate Converter Specification

## Product Overview
Coordinate Converter is a macOS desktop utility for surveyors, GIS professionals, and
geodesists who routinely work with Swedish reference systems as well as
international frames. The application offers:

- A responsive desktop UI built with [Flet](https://flet.dev/) for coordinate
  conversion, datum/height handling, and visual verification on a live OpenStreetMap
  preview.
- Robust free-text parsing of the most common geographic, projected, grid, and
  geocentric formats used in Sweden.
- Deterministic and traceable transformation pipelines powered by PyProj with a
  bespoke 7-parameter Helmert model for the RR92 (RFN) datum.
- A batch-friendly CSV CLI for large scale conversions.

The target audience expects millimetre-level accuracy, friendly error handling, and
transparent documentation of coordinate reference systems (CRS) and height systems.

## Supported Reference Frames & Formats

| CRS | Code | Input Formats | Output Formats |
| --- | --- | --- | --- |
| WGS 84 geographic | `WGS84_GEO` | DD, DMS, DDM | DD, DMS, DDM |
| SWEREF 99 geographic | `SWEREF99_GEO` | DD, DMS, DDM | DD, DMS, DDM |
| RT90 2.5 gon V | `RT90_3021` | northing/easting metres | northing/easting metres |
| WGS 84 geocentric | `WGS84_XYZ` | cartesian XYZ | cartesian XYZ |
| RR92 (RFN) geocentric | `RR92_XYZ` | cartesian XYZ | cartesian XYZ |
| MGRS | `MGRS` | 100 km grid designators | 100 km grid designators |

All conversions are routed through canonical caches in EPSG:4978 (geocentric) and
EPSG:4326 (geographic) to minimise repeated Transformer instantiation.

## Height Handling
- Ellipsoidal heights align with GRS80/WGS84 and are treated interchangeably in the UI.
- RH2000 orthometric heights use the SWEN17_RH2000 geoid (GTX grid). When the grid is
  unavailable a warning is surfaced and the conversion gracefully degrades.
- RFN height support is scaffolded pending official parameters. The interface exists
  and tests mark numerical checks as xfail until reference data is supplied.

## User Experience Requirements
1. Desktop UI: left-hand coordinate source and height source selectors dynamically
   create the relevant input boxes (e.g., lat/lon, RT90, XYZ, MGRS) while the right-hand
   pane hosts the Leaflet 1.x WebView map preview.
2. Geographic inputs accept DD, DDM, or DMS text per axis; MGRS, RT90, and XYZ fields
   match their domain structures. Output coordinate selectors mirror the same options
   and display the requested format only.
3. Precision controls per axis with keyboard adjustments (↑/↓ ±1, Shift for ×10). All
   conversions happen non-blocking; warnings do not crash the UI.
4. Status bar summarises datum/CRS, height system, and last warning.
5. Map view centres on committed coordinates, uses configurable tile URL via
   `OSM_TILE_URL` environment variable, and shows attribution.

## Map Implementation Requirements ⚠️ CRITICAL - DO NOT MODIFY
**This section documents the WORKING map configuration. Changes to this will break the map display.**

### WebView Configuration (TESTED & WORKING)
- **MUST use `ft.WebView`** (NOT `flet_webview.WebView` or any other variant)
- **MUST use base64-encoded data URI** to load HTML content:
  ```python
  import base64
  map_html_content = (Path(__file__).resolve().parent / "map_view" / "leaflet.html").read_text()
  map_html_b64 = base64.b64encode(map_html_content.encode('utf-8')).decode('ascii')
  map_url = f"data:text/html;base64,{map_html_b64}"
  ```
- **DO NOT use `file://` URIs** - they cause CORS issues that prevent tile loading
- **DO NOT use `flet_webview.WebView`** - it fails to render tiles properly despite being the "official" package

### Leaflet HTML Structure (TESTED & WORKING)
- **MUST use Leaflet 1.9.4** from unpkg CDN:
  - CSS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
  - JS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
- **MUST have minimal HTML structure** (see `src/app/map_view/leaflet.html`):
  - Simple `<!DOCTYPE html>` with UTF-8 charset
  - No complex styling, crosshairs, or overlays (they can interfere with rendering)
  - Direct map div: `<div id="map"></div>`
  - Full viewport sizing: `#map { height: 100vh; width: 100vw; }`

### Map Type Switching (TESTED & WORKING)
- **MUST define mapTypes object** with configurations for:
  - `osm`: OpenStreetMap (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`)
  - `satellite`: ArcGIS World Imagery
  - `terrain`: OpenTopoMap
  - `lantmateriet`: Swedish Lantmäteriet tiles
- **MUST use `changeMapType(type)` function** that:
  - Removes current layer before adding new one
  - Uses `L.tileLayer()` with proper attribution and maxZoom
  - Defaults to 'osm' if invalid type provided
- **MUST initialize with OSM**: `changeMapType('osm');`
- **MUST set `window.mapReady = true;`** at end of script

### Map Update Mechanism (TESTED & WORKING)
- **MUST use `updateMapCenter(lat, lon)` function** exposed on window
- **MUST call via `run_javascript`**: `self.map_view.run_javascript(f"updateMapCenter({lat}, {lon});")`
- **MUST check `self.map_ready` flag** before calling JavaScript functions
- **MUST set `self.map_ready = True`** in `on_page_ended` handler

### Map Type Selector UI (TESTED & WORKING)
- **MUST have dropdown** with options: OSM, Satellite, Terrain, Lantmäteriet
- **MUST call `changeMapType()`** via `run_javascript` on change
- **Example**: `self.map_view.run_javascript(f"changeMapType('{map_type}');")`

### What NOT to Do
❌ Do not use `flet_webview.WebView` - causes tile rendering issues  
❌ Do not use `file://` URLs - causes CORS blocking of tiles  
❌ Do not add complex overlays/crosshairs in HTML - can break rendering  
❌ Do not change Leaflet version without testing  
❌ Do not modify the base64 encoding approach  
❌ Do not add WebView configuration options beyond the minimal working set

## CLI Requirements
- Command: `python -m cli.csv_convert --in in.csv --out out.csv --from <CRS_CODE> --to <CRS_CODES> [--height <HEIGHT_SYSTEM>]`.
- Supports multiple target CRS (`--to WGS84_GEO,SWEREF99_GEO,RT90_3021,MGRS,XYZ,RR92_XYZ`).
- Column detection heuristics support decimal/DMS/DDM pairs, RT90 metrics, MGRS strings,
  and XYZ triplets. Non-coordinate columns are copied through unchanged.
- Per-row errors are collected; summary appended to stderr.

## Non-Functional Requirements
- Python 3.11+, macOS focus but cross-platform friendly.
- Logging uses Python's standard logging with human-readable messages.
- Tests via pytest, coverage emphasising parser, RR92 Helmert, and CLI.
- Repository includes SPEC, architecture, README, and MIT license.
- Continuous integration readiness: lint (`ruff` via make lint), formatting (`black`),
  install/test targets in Makefile.

## External Dependencies
- `flet` for GUI shell.
- `pyproj` for CRS definitions and transformations.
- Pure-Python trig (standard library) for Helmert matrix operations (no NumPy runtime dependency).
- `mgrs` to decode/encode Military Grid Reference System positions.
- `pytest` for testing; `pytest-cov` optional but recommended.

## Future Enhancements (Not In Scope)
- RFN orthometric height constants (pending official release).
- Additional CRS (e.g., SWEREF99 TM, other RT90 variants).
- Offline tile caching and multi-map layers.
- Packaging as a signed `.app` bundle.
