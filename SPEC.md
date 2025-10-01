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

## UI Field Layout and Behavior Requirements ⚠️ CRITICAL - DO NOT MODIFY
**This section documents the WORKING UI configuration. Changes to this will break the user experience.**

### Field Dimensions (TESTED & WORKING)
- **Coordinate fields (degrees/minutes/seconds)**: 159px width
  - Applies to: DD, DDM, DMS latitude/longitude fields
  - Applies to: RT90 easting/northing fields (same width as DD)
  - Field width MUST accommodate maximum coordinate value with required precision (see Accuracy Requirements)
- **Direction fields (N/S, E/W)**: 60px width
- **Height field**: 108px width
  - Height field MUST be present for ALL coordinate types EXCEPT geocentric (WGS84_XYZ, RR92_XYZ)

### Coordinate Accuracy Requirements (CRITICAL)
- **Maximum accuracy**: ±2.5cm (0.025m)
- **Round finer coordinates** to meet accuracy requirement
- **Decimal precision by format**:
  - **DD (Decimal Degrees)**: 7 decimal places (±1.1cm at equator)
    - Latitude: max "90.1234567" (10 chars)
    - Longitude: max "180.1234567" (11 chars)
  - **DDM (Degrees Decimal Minutes)**: 5 decimal places in minutes (±1.4cm at equator)
    - Degrees: max "90" or "180" (2-3 chars)
    - Minutes: max "59.12345" (8 chars)
  - **DMS (Degrees Minutes Seconds)**: 3 decimal places in seconds (±3.1cm at equator)
    - Degrees: max "90" or "180" (2-3 chars)
    - Minutes: max "59" (2 chars)
    - Seconds: max "59.123" (6 chars)
  - **RT90/Projected meters**: 2 decimal places (±2.5cm)
    - Max "7654321.12" (10 chars)
  - **Height (meters)**: 2 decimal places (±2.5cm)
    - Max "12345.12" (8 chars)
- **Field sizing**: Text field width MUST exactly fit maximum allowed coordinate with precision
- **Accuracy display (input only)**: Show current accuracy to the right of input coordinate display, outside the box
  - Format: "accuracy: <newline> X.Xm" (e.g., "accuracy: ↵ 0.4m")
  - Display dynamically based on actual input precision
  - MUST NOT be shown on output rows

### Field Order and Layout (TESTED & WORKING)
- **Direction fields MUST appear first** in each row:
  - DD format: `[N/S] [Lat Degrees]` then `[E/W] [Lon Degrees]`
  - DDM format: `[N/S] [Lat Degrees] [Lat Minutes]` then `[E/W] [Lon Degrees] [Lon Minutes]`
  - DMS format: `[N/S] [Lat Degrees] [Lat Minutes] [Lat Seconds]` then `[E/W] [Lon Degrees] [Lon Minutes] [Lon Seconds]`
- **Row labels MUST appear above fields**: "Latitude:" and "Longitude:" as separate text widgets above each row
- **Field labels MUST be on TextField borders**: Never use hint_text or placeholders inside boxes
- **Direction field labels**: MUST be exactly "N/S" or "E/W" (NOT "Lat N/S", "Lon N/S", "Lat E/W", "Lon E/W")
- **Coordinate field labels**: Should indicate component type and axis:
  - Latitude fields: "Lat Degrees", "Lat Minutes", "Lat Seconds"
  - Longitude fields: "Lon Degrees", "Lon Minutes", "Lon Seconds"
- **Boxes start empty**: Except direction fields which default to "N" and "E"

### Tab Order (TESTED & WORKING)
- **Tab and Enter keys** move to the next field in custom order (not default Flet order)
- **Order MUST be horizontal first, then vertical** (left-to-right, then top-to-bottom):
  - DD: `lat_dir → lat_deg → lon_dir → lon_deg → height (if present)`
  - DDM: `lat_dir → lat_deg → lat_min → lon_dir → lon_deg → lon_min → height (if present)`
  - DMS: `lat_dir → lat_deg → lat_min → lat_sec → lon_dir → lon_deg → lon_min → lon_sec → height (if present)`
- **Shift+Tab** reverses the order
- **Read-only output fields** are completely skipped in tab order

### Output Field Styling (TESTED & WORKING)
- **All read-only output fields MUST be bold**: `text_style=ft.TextStyle(weight=ft.FontWeight.BOLD)`
- Same field order as input (direction first)
- Same labels on borders (never placeholders)

### Copy-to-Clipboard Controls (CRITICAL)
- **Per-row output copy**: A copy button MUST be placed to the left of each output coordinate row (Latitude and Longitude sections). Clicking copies that row’s coordinate in the currently selected output format with the specified precision and direction labels.
  - DD: "<lat>, <lon>" with 7 dp for DD output rows where applicable
  - DDM/DMS: component-formatted per format and direction letters
  - Projected (e.g., RT90): numeric with 2 dp and unit where applicable
  - MGRS: full grid string
- **Full output copy**: A copy button MUST be placed to the left of the bottommost combined output row (showing full coordinate and height). Clicking copies the entire assembled output string exactly as displayed.
- **Height-only copy**: A copy button MUST be placed to the left of the output height box to copy height value with unit and height system.
- **Clipboard content** MUST reflect rounding/precision rules in this spec and use the same labels/direction indicators as rendered.

### Clipboard Integration (Input) (CRITICAL)
- **Paste from clipboard**: A button labeled "Paste from clipboard" MUST be placed directly under the "Input" label, left-aligned.
  - On click: read clipboard text and perform a pre-parse (without changing any inputs).
  - If a coordinate is identified, switch input type to the Free-text parser, paste the clipboard content into the free-text field, and parse immediately.
  - If no coordinate is identified, DO NOT change input type or any current input values; show a non-blocking status message.


### Key Navigation Implementation
- Implemented in `_on_page_key()` method in `main.py`
- Uses `input_tab_order` list to track custom sequence
- Calls `field.focus()` programmatically to override default Flet behavior
- Handles both Tab/Enter (forward) and Shift+Tab (backward)

## Map Implementation Requirements ⚠️ CRITICAL - DO NOT MODIFY
**This section documents the WORKING map configuration. Changes to this will break the map display.**

### Map Type Configuration (TESTED & WORKING)
- **Default map type**: Terrain (OpenTopoMap)
- **Available map types**: OSM, Satellite, Terrain
- **Removed**: Lantmäteriet (removed from dropdown and HTML)
- **Map initializes with**: `changeMapType('terrain')` on page load

### Click-to-Select Coordinates (TESTED & WORKING)
- Clicking map emits console message: `{type: 'map_click', lat: X, lon: Y}`
- Console message handler in `main.py` parses lat/lon
- Automatically switches input to WGS84 DD format if not already DD
- Populates lat_deg, lon_deg, lat_dir, lon_dir fields
- Triggers conversion and map re-center

### Map Center Behavior (TESTED & WORKING)
- Map centers immediately when input coordinates change
- Map centers on click when user selects coordinate from map
- Uses `updateMapCenter(lat, lon)` JavaScript function via `run_javascript()`

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
  - `terrain`: OpenTopoMap (default)
- **MUST use `changeMapType(type)` function** that:
  - Removes current layer before adding new one
  - Uses `L.tileLayer()` with proper attribution and maxZoom
  - Defaults to 'terrain' if invalid type provided
- **MUST initialize with Terrain**: `changeMapType('terrain');`
- **MUST set `window.mapReady = true;`** at end of script
- **MUST emit click events**: `map.on('click', ...)` emits console messages for coordinate selection

### Map Interaction (CRITICAL)
- **Double-click selects coordinate**: Map selection MUST be triggered by double-click (`dblclick`), not single click. The emitted event should include lat/lon as before.
- **Selection MUST NOT change input type**: Selecting a coordinate via the map must update values in the current input format (if applicable) without switching the input coordinate type selector.
- **Crosshair cursor**: The map cursor MUST be a crosshair when hovering over the map to convey precision selection.

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
