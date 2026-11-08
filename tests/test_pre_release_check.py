"""@file test_pre_release_check.py
@brief Verify pre-release cleanup without invoking external build services.
@details Level 1: script orchestration -> EXIT cleanup -> Git/filesystem boundaries.
Uses temporary repositories and a fake uv executable; no network or user paths.
Covers successful termination, stage failure, and tracked-target preservation.
@satisfies SRS-480, SRS-481, SRS-483, SRS-484
"""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize(
    ("fail_sync", "tracked_cache"),
    [(False, False), (True, False), (False, True)],
    ids=["success", "sync-failure", "tracked-cache"],
)
def test_pre_release_cleanup_preserves_only_tracked_cache(
    tmp_path: Path, fail_sync: bool, tracked_cache: bool,
) -> None:
    """@brief Remove disposable Ruff cache and preserve tracked cache on exit.
    @details Arrange an isolated repository and deterministic uv stub; execute
    the copied script from outside its root; assert exit status, cache lifetime,
    tracked-file content, and virtual-environment preservation. O(n) filesystem
    work for n fixture files; all writes remain under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param fail_sync {bool} Inject dependency-sync exit status 7 when true.
    @param tracked_cache {bool} Add the cache sentinel to the temporary Git index.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Exit status or cleanup violates its contract.
    @satisfies SRS-471, SRS-475, SRS-480, SRS-481, SRS-483, SRS-484
    """
    # @brief Arrange repository paths and sentinel payloads.
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "pre-release-check.sh"
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/pre-release-check.sh",
        script,
    )
    for directory in ("src", "tests", ".venv", ".ruff_cache"):
        (repository / directory).mkdir()
    cache_file = repository / ".ruff_cache" / "sentinel"
    cache_file.write_text("cache payload", encoding="utf-8")
    venv_file = repository / ".venv" / "sentinel"
    venv_file.write_text("environment payload", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True,
        capture_output=True,
    )
    if tracked_cache:
        subprocess.run(
            ["git", "-C", str(repository), "add", "--", ".ruff_cache"],
            check=True, capture_output=True,
        )
    # @brief Fake uv creates build artifacts or returns a deterministic sync error.
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate uv stage outcomes without network access.\n"
        "# @details Build writes two fixture files; sync uses injected status.\n"
        "# @return Exit status 7 for injected sync failure; otherwise 0.\n"
        'case "$*" in\n'
        '  sync*) exit "$FAKE_SYNC_STATUS" ;;\n'
        '  *" -m build "*) mkdir -p dist; '
        'touch dist/package.tar.gz dist/package.whl ;;\n'
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    # @brief Isolate subprocess HOME, Git configuration, and executable lookup.
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": str(binary_dir) + os.pathsep + os.defpath,
        "FAKE_SYNC_STATUS": "7" if fail_sync else "0",
    })
    expected_output = 1 if fail_sync else 0

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(script), "--allow-dirty"], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )

    # @brief Assert cleanup, failure propagation, and protected payload integrity.
    assert result.returncode == expected_output, result.stdout + result.stderr
    assert cache_file.exists() is tracked_cache
    assert venv_file.read_text(encoding="utf-8") == "environment payload"
    assert not (repository / "dist").exists()
    if tracked_cache:
        assert cache_file.read_text(encoding="utf-8") == "cache payload"
        assert "WARNING: cleanup skipped for '.ruff_cache'" in result.stderr
    if fail_sync:
        assert "Pre-release check failed at stage dependency-sync." in result.stderr
        assert "stage build" not in result.stdout
        assert "Pre-release check passed." not in result.stdout
    else:
        assert "Pre-release check passed." in result.stdout
