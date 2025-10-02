# Coordinate Converter – Specification

## Purpose
The Coordinate Converter application provides accurate transformations between Swedish and global coordinate systems. It offers a graphical interface (Flet), a map preview, and a command-line batch mode for CSV files.

---

## Functional Requirements
- Accept coordinates in multiple input formats: decimal degrees (DD), degrees-minutes-seconds (DMS), degrees-decimal minutes (DDM), MGRS, RT90, etc.
- Output coordinates in supported systems: WGS84, SWEREF99, RT90, geocentric XYZ, RR92.
- Support height systems: ellipsoidal height, RH2000 (geoid), RFN (when parameters are available).
- Parse free text input robustly, with clear error feedback on invalid entries.
- Support batch CSV conversion via CLI.
- Provide a responsive map preview that visualizes input/output coordinates.

---

## User Interface Specification

### General Layout
- **Input Panel**: A single field where users can paste or type coordinates in any supported format.  
- **Output Grid**: Each coordinate system is displayed in a **Card**, arranged in a responsive grid.  
- **Map Preview**: Displays the location of the input coordinate, resizes proportionally, padded by 16px on all sides.

### Cards
- All coordinate systems (WGS84, SWEREF99, RT90, XYZ, RR92) are displayed in **visually consistent cards**.
- Each card includes:
  - Title (system name).
  - Latitude / Longitude or equivalent fields.
  - Height values (Ellipsoidal, RH2000, RFN if available).
- **Uniform height and width**: cards in the same row expand to match the tallest card.
- Cards styled with:
  - Rounded corners (12px).
  - Light background color.
  - Soft drop shadow.
  - Padding: 16px internal.

### Labels & Units
- Every numeric field displays units explicitly:  
  - Latitude/Longitude: `°`  
  - Height: `m`  
  - Gon for RT90: `gon`
- Labels written in sentence case: `Latitude (°)`, not `LATITUDE`.
- Units rendered in smaller font size (12px) but aligned with the value field.

### Coordinate Field Consistency
- Angular coordinate fields (Latitude/Longitude in any representation) use the **same width** as the input panel field to ensure perfect alignment between input and output.
- Linear coordinates (northing/easting, geocentric X/Y/Z, heights) share a fixed width distinct from angular fields.
- Grid-based outputs (MGRS, RT90 string formats) are constrained to a shared width matching their corresponding outputs.
- **All coordinate inputs and outputs are instantiated from the same field configuration** so formatting, widths, labels, and tab order remain in sync across the UI.

### Error States
- Invalid input triggers:
  - Red border around the field.
  - Inline error message in red text (smaller font, below the field).
- Errors never fail silently.

### Spacing & Grid
- Use an 8px baseline grid for spacing and padding.  
- Consistent vertical spacing between fields (min 8px, max 16px).  
- Equal margins around cards, map, and panels.

### Responsiveness
- Wide windows: cards arranged in rows of 2–3.  
- Narrow windows: cards stack vertically with 16px spacing.  
- Map preview resizes proportionally and never touches the window edge.  

### Typography
- Font family: sans-serif (default system sans).  
- **Titles**: 18px, bold.  
- **Labels**: 14px, medium weight.  
- **Values**: 16px, regular.  
- **Units**: 12px, light weight.  
- Typography consistent across all cards.

### Buttons & Actions
- Primary actions (e.g. "Copy", "Convert") styled in **accent color** (blue tone, `#1976d2`).  
- Buttons have consistent corner radius (8px) and padding.  
- Hover/focus states use a lighter accent shade.

### Tab Navigation
- All interactive fields must support **keyboard navigation** with **Tab**.  
- Traversal order is strictly **left-to-right, top-to-bottom**, independent of responsive layout.  
- Tab order is **auto-assigned sequentially** at runtime (no manual tab indices).  
- Guarantee: sequential, unique indices `[1,2,3,…]` across all fields.  
- Invalid fields remain focusable in their correct position.  
- Non-input widgets (e.g. map) excluded unless explicitly interactive.

---

## Non-Functional Requirements
- Must run offline after initial geoid grid download.  
- UI responsiveness: updates fields and map marker as user types.  
- Performance: handle batch conversion of 100k+ rows in CSV CLI.  
- Accessibility: ensure color contrasts meet WCAG AA.

---
