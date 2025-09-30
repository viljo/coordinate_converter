# Architecture Overview

## Component Map

```
┌──────────────────────┐
│ Flet UI (app/main.py)│
│  • source selectors   │
│  • dynamic inputs     │
│  • map bridge         │
│  • status + logging   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐        ┌─────────────────────┐
│ core.parser          │◄──────►│ core.crs_registry   │
│  • free-text parsing │        │  • CRS metadata      │
│  • format normaliser │        │  • transformer cache │
└──────────┬───────────┘        └──────────┬──────────┘
           │                                │
           ▼                                ▼
┌──────────────────────┐        ┌─────────────────────┐
│ core.transform       │        │ core.helmert_rr92   │
│  • canonical routing │        │  • 7-param Helmert  │
│  • height dispatch   │        │  • trig helpers     │
└──────────┬───────────┘        └──────────┬──────────┘
           │                                │
           ▼                                ▼
┌──────────────────────┐        ┌─────────────────────┐
│ height_swen17        │        │ height_rfn          │
│  • PROJ grid wrapper │        │  • placeholder API  │
└──────────────────────┘        └─────────────────────┘
```

The CLI (`cli/csv_convert.py`) reuses `core.parser` and `core.transform` for each row.

## Data Flow
1. **Input**: The UI builds coordinate strings from the selected source/height controls
   (e.g., WGS84 lat/lon boxes, RT90 northing/easting, MGRS text) while the CLI accepts
   raw CSV tokens. `core.parser` tokenises and infers CRS/format, returning a structured
   `ParsedCoordinate` dataclass with numeric values, CRS code, and warnings.
2. **Canonical conversion**: `core.transform` converts parsed values into both
   geocentric (EPSG:4978) and geographic (EPSG:4326) canonical caches. All downstream
   conversions start from these caches to minimise precision loss and reduce the
   number of transformer instantiations.
3. **RR92 handling**: If either source or target is RR92, the module uses
   `helmert_rr92` to convert between RR92 XYZ and SWEREF99/WGS84 XYZ before/after
   calling PyProj transformers.
4. **Heights**: Orthometric conversions call height modules. `height_swen17` looks up
   the SWEN17 geoid; `height_rfn` currently exposes the interface but returns
   informative errors until constants are added.
5. **Output**: Target-specific formatters re-encode values (e.g., DMS string) and
   return structured objects. The UI displays them, while the CLI writes them into
   CSV columns.

## Key Dataclasses
- `ParsedCoordinate`: holds CRS code, values, format hints, height, and warnings.
- `CRSInfo`: metadata (EPSG code, axis order, dimension) for each supported CRS.
- `CanonicalCoordinate`: geocentric/geographic caches produced by the transform layer.
- `CoordinateOption` (UI): describes selectable coordinate groups and their field layout.

## Threading Considerations
Flet runs in a single-threaded event loop. Potentially slow operations (file IO,
transform initialisation) are executed via background threads using
`asyncio.to_thread`. Transformer caches are thread-safe thanks to module-level
`functools.lru_cache` functions.

## Map Integration
`app/map_view/leaflet.html` contains a Leaflet scene with a central crosshair. The
Flet app injects coordinates using the webview's `evaluate_js` method. Tile URL is
configurable through the `OSM_TILE_URL` env var; default is OpenStreetMap standard
tiles with attribution shown in the footer.

## Error Handling Strategy
- Parser attaches warnings for ambiguous inputs and raises `ParseError` only for
  unrecoverable strings (empty input, too few numeric tokens).
- Transform layer wraps `pyproj` exceptions and surfaces user-friendly messages while
  logging the original exception.
- CLI collects row-level errors and writes a JSON summary to stderr before exiting with
  a non-zero status when failures occur.

## Testing Strategy
- Parser tests cover all supported formats and ambiguous cases.
- Helmert tests validate forward/inverse RR92 transformations and matrix symmetry.
- Height RFN tests validate scaffolding behaviour (xfail for future constants).
- CSV CLI tests use temporary files to exercise detection, conversion, and error
  reporting.
