"""Runtime management for external geodetic grid artifacts."""

from __future__ import annotations

import hashlib
import os
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

__all__ = [
    "ArtifactDownloadError",
    "ArtifactSpec",
    "ensure_artifact",
    "ensure_runtime_artifacts",
    "get_artifact_path",
    "register_with_pyproj",
]


class ArtifactDownloadError(RuntimeError):
    """Raised when an artifact could not be downloaded or verified."""


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    checksum: str
    url: str
    archive_member: str | None = None


DEFAULT_CACHE_ROOT = Path.home() / ".coordinate_converter" / "artifacts"

ARTIFACTS: Dict[str, ArtifactSpec] = {
    "SWEN17_RH2000.gtx": ArtifactSpec(
        name="SWEN17_RH2000.gtx",
        checksum="86ea0ff37304358e184375e8c820799a5586f3a9e5c3142742b57c755c6de370",
        url="https://download.osgeo.org/proj/proj-datumgrid-europe-1.5.tar.gz",
        archive_member="SWEN17_RH2000.gtx",
    ),
}


def _is_offline() -> bool:
    return os.getenv("COORDINATE_ARTIFACTS_OFFLINE", "0") == "1"


def _cache_dir() -> Path:
    override = os.getenv("COORDINATE_ARTIFACTS_DIR")
    path = Path(override) if override else DEFAULT_CACHE_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def _download_to_tempfile(url: str) -> Path:
    try:
        with urllib.request.urlopen(url) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    if not chunk:
                        break
                    tmp.write(chunk)
                return Path(tmp.name)
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise ArtifactDownloadError(f"Failed to download {url}: {exc.reason}") from exc


def _verify_checksum(path: Path, checksum: str) -> bool:
    if not path.exists():
        return False
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest() == checksum


def _extract_member(archive_path: Path, member: str, target: Path) -> None:
    try:
        with tarfile.open(archive_path, mode="r:gz") as tar:
            info = tar.getmember(member)
            extracted = tar.extractfile(info)
            if extracted is None:
                raise ArtifactDownloadError(
                    f"Member {member!r} not found in archive {archive_path.name}"
                )
            with target.open("wb") as dest:
                for chunk in iter(lambda: extracted.read(1024 * 1024), b""):
                    if not chunk:
                        break
                    dest.write(chunk)
    except (KeyError, tarfile.TarError) as exc:
        raise ArtifactDownloadError(
            f"Failed to extract {member!r} from {archive_path.name}: {exc}"
        ) from exc


def ensure_artifact(name: str) -> Path:
    if name not in ARTIFACTS:
        raise KeyError(f"Unknown artifact {name!r}")

    spec = ARTIFACTS[name]
    cache_dir = _cache_dir()
    target = cache_dir / spec.name

    if target.exists() and _verify_checksum(target, spec.checksum):
        return target

    if _is_offline():
        raise ArtifactDownloadError(
            f"Artifact {name} is missing and downloads are disabled (COORDINATE_ARTIFACTS_OFFLINE=1)."
        )

    temp_file: Path | None = None
    try:
        if spec.archive_member:
            temp_file = _download_to_tempfile(spec.url)
            _extract_member(temp_file, spec.archive_member, target)
        else:
            temp_file = _download_to_tempfile(spec.url)
            temp_file.replace(target)
    finally:
        if temp_file and temp_file.exists():
            temp_file.unlink()

    if not _verify_checksum(target, spec.checksum):
        target.unlink(missing_ok=True)
        raise ArtifactDownloadError(
            f"Checksum verification failed for {name}. Expected {spec.checksum}."
        )

    return target


def get_artifact_path(name: str) -> Path:
    path = _cache_dir() / name
    if not path.exists():
        raise FileNotFoundError(f"Artifact {name} is not present in cache {path.parent}")
    return path


def register_with_pyproj(paths: Iterable[Path]) -> None:
    try:
        from pyproj import datadir  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - optional dependency scenario
        return

    for path in paths:
        datadir.append_data_dir(str(path))



