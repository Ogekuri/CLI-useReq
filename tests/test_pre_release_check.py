"""@file test_pre_release_check.py
@brief Verify pre-release temporary-build staging, dist/ independence, and stale-venv repair.
@details Level 1: script orchestration -> EXIT cleanup -> Git/filesystem boundaries,
plus dependency-sync entry-point guarding for the unit-tests stage. Uses temporary
repositories and a fake uv executable; no network or user paths. Covers successful
termination, stage failure, tracked-target preservation, temporary build-directory
lifecycle, dist/ independence, and repair or rejection of stale virtual-environment
pytest entry points.
@satisfies SRS-475, SRS-479, SRS-480, SRS-481, SRS-483, SRS-484, SRS-556, SRS-558
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
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/build.sh",
        scripts / "build.sh",
    )
    (scripts / "build.sh").chmod(0o755)
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
    # @brief Fake uv writes temporary artifacts into the requested outdir argument.
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate uv stage outcomes without network access.\n"
        "# @details Build writes two fixture files into --outdir; sync uses injected status.\n"
        "# @return Exit status 7 for injected sync failure; otherwise 0.\n"
        "outdir=\"\"\n"
        "prev=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  [ \"$prev\" = \"--outdir\" ] && outdir=\"$arg\"\n"
        "  prev=\"$arg\"\n"
        "done\n"
        'case "$*" in\n'
        '  sync*) exit "$FAKE_SYNC_STATUS" ;;\n'
        '  *" -m build "*)\n'
        '    [ -n "$outdir" ] || exit 1\n'
        '    mkdir -p "$outdir"\n'
        '    touch "$outdir/package.tar.gz" "$outdir/package.whl" ;;\n'
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    # @brief Isolate subprocess HOME, temporary build root, Git config, and PATH lookup.
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "TMPDIR": str(temp_root),
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

    # @brief Assert cleanup, failure propagation, temporary-dir removal, and payload integrity.
    assert result.returncode == expected_output, result.stdout + result.stderr
    assert cache_file.exists() is tracked_cache
    assert venv_file.read_text(encoding="utf-8") == "environment payload"
    assert not (repository / "dist").exists()
    assert not any(temp_root.iterdir())
    if tracked_cache:
        assert cache_file.read_text(encoding="utf-8") == "cache payload"
        assert "WARNING: cleanup skipped for '.ruff_cache'" in result.stderr
    if fail_sync:
        assert "Pre-release check failed at stage dependency-sync." in result.stderr
        assert "stage build" not in result.stdout
        assert "Pre-release check passed." not in result.stdout
    else:
        assert "Pre-release check passed." in result.stdout


def test_pre_release_check_leaves_dist_directory_untouched(tmp_path: Path) -> None:
    """@brief Leave every dist/ entry unchanged and build artifacts in a temporary directory.
    @details Level 1 regression for SRS-556: arrange an isolated repository whose dist/ holds
    one tracked and one untracked release artifact, run the copied script with a fake uv that
    writes sdist and wheel fixtures into the --outdir temporary directory, and assert that
    dist/ neither loses nor gains entries, emits no dist/ cleanup warning, and that the
    temporary build directory is removed on termination.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} dist/ is modified or the temporary build directory survives.
    @satisfies SRS-476, SRS-477, SRS-482, SRS-556, SRS-558
    """
    # @brief Arrange repository, tracked and untracked dist artifacts, and a uv stub.
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "pre-release-check.sh"
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/pre-release-check.sh",
        script,
    )
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/build.sh",
        scripts / "build.sh",
    )
    (scripts / "build.sh").chmod(0o755)
    for directory in ("src", "tests", ".venv"):
        (repository / directory).mkdir()
    dist = repository / "dist"
    dist.mkdir()
    tracked_artifact = dist / "tracked-release.whl"
    tracked_artifact.write_text("release payload", encoding="utf-8")
    untracked_artifact = dist / "previous-release.tar.gz"
    untracked_artifact.write_text("previous payload", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "add", "--", "dist/tracked-release.whl"],
        check=True, capture_output=True,
    )
    # @brief Fake uv writes artifacts into the requested outdir and succeeds everywhere.
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate uv stage outcomes without network access.\n"
        "# @details Build writes two fixture files into --outdir; every other stage succeeds.\n"
        "# @return Exit status 0.\n"
        "outdir=\"\"\n"
        "prev=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  [ \"$prev\" = \"--outdir\" ] && outdir=\"$arg\"\n"
        "  prev=\"$arg\"\n"
        "done\n"
        'case "$*" in\n'
        '  *" -m build "*)\n'
        '    [ -n "$outdir" ] || exit 1\n'
        '    mkdir -p "$outdir"\n'
        '    touch "$outdir/package.tar.gz" "$outdir/package.whl" ;;\n'
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    # @brief Isolate subprocess HOME, temporary build root, Git config, and PATH lookup.
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "TMPDIR": str(temp_root),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": str(binary_dir) + os.pathsep + os.defpath,
    })

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(script), "--allow-dirty"], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )

    # @brief Assert dist/ independence, temporary cleanup, and success reporting.
    assert result.returncode == 0, result.stdout + result.stderr
    assert tracked_artifact.read_text(encoding="utf-8") == "release payload"
    assert untracked_artifact.read_text(encoding="utf-8") == "previous payload"
    assert sorted(entry.name for entry in dist.iterdir()) == [
        "previous-release.tar.gz", "tracked-release.whl",
    ]
    assert not any(temp_root.iterdir())
    assert "dist/" not in result.stderr
    assert "Pre-release check passed." in result.stdout


@pytest.mark.parametrize(
    ("heal_succeeds",),
    [(True,), (False,)],
    ids=["healed", "unhealable"],
)
def test_pre_release_check_stale_venv_pytest_entry_point(
    tmp_path: Path, heal_succeeds: bool,
) -> None:
    """@brief Repair or reject a stale foreign pytest entry point before unit tests.
    @details Level 1 regression: dependency-sync stage -> venv entry-point guard ->
    unit-tests stage. A console script copied from a relocated virtual environment
    keeps a foreign shebang; `uv sync --frozen` reuses its dist-info without
    rewriting it, so `uv run pytest` executes under a foreign interpreter and the
    conftest import fails with `ModuleNotFoundError: No module named 'tiktoken'`.
    Arrange an isolated repository with a poisoned `.venv/bin/pytest` and a fake uv
    that heals it only on `--reinstall-package` sync calls; assert the pipeline
    passes after repair, or stops at `dependency-sync` with English guidance when
    repair cannot localize the interpreter. Complexity O(1) plus one subprocess
    pipeline execution; all writes stay under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param heal_succeeds {bool} Fake uv rewrites the entry point when true.
    @return {None} Completes when the observable pipeline outcome is asserted.
    @throws {AssertionError} When repair, stage gating, or exit status violates the
        documented pre-release behavior.
    @satisfies SRS-475, SRS-479, SRS-480
    """
    # @brief Arrange a deterministic foreign interpreter stub and an outdir-aware uv stub.
    repository = tmp_path / "repository"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "pre-release-check.sh"
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/pre-release-check.sh",
        script,
    )
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/build.sh",
        scripts / "build.sh",
    )
    (scripts / "build.sh").chmod(0o755)
    for directory in ("src", "tests", ".venv"):
        (repository / directory).mkdir()
    venv_bin = repository / ".venv" / "bin"
    venv_bin.mkdir()
    venv_python = venv_bin / "python3"
    venv_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    venv_python.chmod(0o755)
    foreign_bin = tmp_path / "foreign-venv" / "bin"
    foreign_bin.mkdir(parents=True)
    foreign_python = foreign_bin / "python3"
    foreign_python.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
    foreign_python.chmod(0o755)
    pytest_entry_point = venv_bin / "pytest"
    pytest_entry_point.write_text(
        f"#!{foreign_python}\nexit 9\n",
        encoding="utf-8",
    )
    pytest_entry_point.chmod(0o755)
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True,
        capture_output=True,
    )
    # @brief Fake uv heals the entry point only for --reinstall-package sync calls.
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate uv sync, build, run, and entry-point repair flows.\n"
        "# @details Capture --project and --outdir paths; rewrite .venv/bin/pytest only when\n"
        "# --reinstall-package is present and FAKE_HEAL_ENTRY_POINT is enabled.\n"
        "# @return Exit status of the emulated uv operation.\n"
        "project=\"\"\n"
        "outdir=\"\"\n"
        "heal=0\n"
        "prev=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  [ \"$prev\" = \"--project\" ] && project=\"$arg\"\n"
        "  [ \"$prev\" = \"--outdir\" ] && outdir=\"$arg\"\n"
        "  [ \"$arg\" = \"--reinstall-package\" ] && heal=1\n"
        "  prev=\"$arg\"\n"
        "done\n"
        'case "$*" in\n'
        "  sync*)\n"
        "    if [ \"$heal\" -eq 1 ] && [ \"$FAKE_HEAL_ENTRY_POINT\" = \"1\" ]; then\n"
        "      printf '#!%s/.venv/bin/python3\\nexit 0\\n' \"$project\""
        " > \"$project/.venv/bin/pytest\"\n"
        "      chmod 755 \"$project/.venv/bin/pytest\"\n"
        "    fi\n"
        "    exit 0\n"
        "    ;;\n"
        '  *" -m build "*)\n'
        "    [ -n \"$outdir\" ] || exit 1\n"
        "    mkdir -p \"$outdir\"\n"
        "    touch \"$outdir/package.tar.gz\" \"$outdir/package.whl\"\n"
        "    exit 0\n"
        "    ;;\n"
        "  run*\" pytest\")\n"
        "    exec \"$project/.venv/bin/pytest\"\n"
        "    ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    # @brief Isolate subprocess HOME, temporary build root, Git config, and PATH lookup.
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "TMPDIR": str(temp_root),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": str(binary_dir) + os.pathsep + os.defpath,
        "FAKE_HEAL_ENTRY_POINT": "1" if heal_succeeds else "0",
    })

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(script), "--allow-dirty"], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )

    # @brief Assert repair success or dependency-sync gating with English guidance.
    shebang = pytest_entry_point.read_text(encoding="utf-8").splitlines()[0]
    if heal_succeeds:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Pre-release check passed." in result.stdout
        assert shebang == f"#!{repository}/.venv/bin/python3"
        assert "stale virtual environment entry point" in result.stderr
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert (
            "Pre-release check failed at stage dependency-sync." in result.stderr
        )
        assert "still targets a foreign interpreter" in result.stderr
        assert "stage unit-tests" not in result.stdout
        assert shebang == f"#!{foreign_python}"
