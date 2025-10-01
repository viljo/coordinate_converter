"""Tests for runtime artifact management."""

from __future__ import annotations

import hashlib
import io
import os
import tarfile
from pathlib import Path
from unittest import mock

import pytest

from core import artifacts


@pytest.fixture()
def temp_artifact_dir(tmp_path: Path):
    cache_dir = tmp_path / "artifacts"
    cache_dir.mkdir()
    with mock.patch.dict(
        os.environ,
        {
            "COORDINATE_ARTIFACTS_DIR": str(cache_dir),
        },
    ):
        yield cache_dir


def test_ensure_artifact_from_local_archive(monkeypatch, temp_artifact_dir: Path, tmp_path: Path):
    name = "SWEN17_RH2000.gtx"
    content = b"grid-data"

    archive_path = tmp_path / "demo.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))

    checksum = hashlib.sha256(content).hexdigest()
    spec = artifacts.ArtifactSpec(
        name=name,
        checksum=checksum,
        url=archive_path.as_uri(),
        archive_member=name,
    )

    monkeypatch.setitem(artifacts.ARTIFACTS, name, spec)

    with mock.patch.dict(os.environ, {"COORDINATE_ARTIFACTS_OFFLINE": "0"}):
        path = artifacts.ensure_artifact(name)
    assert path.exists()
    assert path.read_bytes() == content

    path.write_bytes(b"corrupt")
    with mock.patch.dict(os.environ, {"COORDINATE_ARTIFACTS_OFFLINE": "0"}):
        path = artifacts.ensure_artifact(name)
    assert path.read_bytes() == content


def test_ensure_artifact_offline_mode(monkeypatch, temp_artifact_dir: Path):
    name = "SWEN17_RH2000.gtx"
    spec = artifacts.ArtifactSpec(
        name=name,
        checksum="0" * 64,
        url="file:///missing.tar.gz",
        archive_member=name,
    )

    monkeypatch.setitem(artifacts.ARTIFACTS, name, spec)

    with mock.patch.dict(os.environ, {"COORDINATE_ARTIFACTS_OFFLINE": "1"}):
        with pytest.raises(artifacts.ArtifactDownloadError):
            artifacts.ensure_artifact(name)

