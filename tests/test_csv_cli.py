import csv
from pathlib import Path

from cli import csv_convert
from core.transform import HeightSystem


def test_cli_converts_basic(tmp_path):
    input_path = tmp_path / "input.csv"
    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["latitude", "longitude"])
        writer.writeheader()
        writer.writerow({"latitude": "59.3293", "longitude": "18.0686"})

    output_path = tmp_path / "output.csv"
    exit_code = csv_convert.run_cli(
        [
            "--in",
            str(input_path),
            "--out",
            str(output_path),
            "--from",
            "SWEREF99_GEO",
            "--to",
            "WGS84_GEO,MGRS",
            "--height",
            HeightSystem.ELLIPSOIDAL,
        ]
    )
    assert exit_code == 0

    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    row = rows[0]
    assert row["WGS84_GEO_LAT"]
    assert row["WGS84_GEO_LON"]
    assert row["MGRS"]
    assert "ERROR" in row
