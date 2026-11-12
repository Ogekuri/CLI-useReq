"""@file test_pre_release_check.py
@brief Verify pre-release cleanup and stale-venv repair without external services.
@details Level 1: script orchestration -> EXIT cleanup -> Git/filesystem boundaries,
plus dependency-sync entry-point guarding for the unit-tests stage. Uses temporary
repositories and a fake uv executable; no network or user paths. Covers successful
termination, stage failure, tracked-target preservation, and repair or rejection of
stale virtual-environment pytest entry points.
@satisfies SRS-475, SRS-479, SRS-480, SRS-481, SRS-483, SRS-484, SRS-556, SRS-558, SRS-574, SRS-575, SRS-576
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


def test_pre_release_cleanup_preserves_tracked_dist_entries(tmp_path: Path) -> None:
    """@brief Preserve git-tracked dist/ entries and remove untracked artifacts on exit.
    @details Arrange an isolated repository whose dist/ holds one staged release artifact, run
    the copied script with a fake uv that writes untracked sdist and wheel fixtures, and assert
    that only untracked entries are removed while the tracked entry keeps its content and the
    dist/ directory survives. O(n) work over fixture files; all writes remain under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Tracked dist entry is removed or untracked artifacts survive.
    @satisfies SRS-556, SRS-558, SRS-483
    """
    # @brief Arrange repository, staged tracked dist artifact, and deterministic uv stub.
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/pre-release-check.sh",
        scripts / "pre-release-check.sh",
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
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "add", "--", "dist/tracked-release.whl"],
        check=True, capture_output=True,
    )
    # @brief Fake uv creates untracked build artifacts and reports success for every stage.
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate uv stage outcomes without network access.\n"
        "# @details Build writes two untracked fixture files; every other stage succeeds.\n"
        "# @return Exit status 0.\n"
        'case "$*" in\n'
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
    })

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(scripts / "pre-release-check.sh"), "--allow-dirty"], cwd=tmp_path,
        env=environment, capture_output=True, text=True, check=False,
    )

    # @brief Assert tracked preservation, untracked removal, and the cleanup warning.
    assert result.returncode == 0, result.stdout + result.stderr
    assert tracked_artifact.read_text(encoding="utf-8") == "release payload"
    assert not (dist / "package.tar.gz").exists()
    assert not (dist / "package.whl").exists()
    assert dist.is_dir()
    assert "WARNING: cleanup skipped for 'dist/tracked-release.whl'" in result.stderr


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
    # @brief Arrange repository paths and a deterministic foreign interpreter stub.
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
        "# @details Capture the --project path; rewrite .venv/bin/pytest only when\n"
        "# --reinstall-package is present and FAKE_HEAL_ENTRY_POINT is enabled.\n"
        "# @return Exit status of the emulated uv operation.\n"
        "project=\"\"\n"
        "heal=0\n"
        "prev=\"\"\n"
        "for arg in \"$@\"; do\n"
        "  [ \"$prev\" = \"--project\" ] && project=\"$arg\"\n"
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
        "    mkdir -p \"$project/dist\"\n"
        "    touch \"$project/dist/package.tar.gz\" \"$project/dist/package.whl\"\n"
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
    # @brief Isolate subprocess HOME, Git configuration, and executable lookup.
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
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


def _create_preexisting_dist_repository(
    tmp_path: Path, build_script_body: str,
) -> Path:
    """@brief Create an isolated repository with a pre-release script and a build stub.
    @details Copies `scripts/pre-release-check.sh` into a fresh Git repository, seeds a `dist/`
    directory holding one git-tracked release artifact plus two untracked artifacts of previous
    versions, installs the supplied `scripts/build.sh` stub, and creates the `src`, `tests`, and
    `.venv` scaffold expected by the pipeline. O(1) filesystem writes plus one `git init`.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param build_script_body {str} Shell body installed as `scripts/build.sh`.
    @return {Path} Absolute path of the isolated repository root.
    @throws {subprocess.CalledProcessError} Raised when `git init` or `git add` fails.
    @satisfies SRS-471, SRS-574
    """
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(
        Path(__file__).resolve().parents[1] / "scripts/pre-release-check.sh",
        scripts / "pre-release-check.sh",
    )
    build_script = scripts / "build.sh"
    build_script.write_text(build_script_body, encoding="utf-8")
    build_script.chmod(0o755)
    for directory in ("src", "tests", ".venv"):
        (repository / directory).mkdir()
    dist = repository / "dist"
    dist.mkdir()
    (dist / "tracked-release.whl").write_text("release payload", encoding="utf-8")
    (dist / "cli_usereq-0.74.9.tar.gz").write_text("stale payload", encoding="utf-8")
    (dist / "cli_usereq-0.75.2-py3-none-any.whl").write_text(
        "stale payload", encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "add", "--", "dist/tracked-release.whl"],
        check=True, capture_output=True,
    )
    return repository


def _create_success_uv(binary_dir: Path) -> None:
    """@brief Create a fake uv executable reporting success for every pipeline stage.
    @details The stub exits 0 for sync, static-check, and pytest invocations, so only the
    dist/ preparation and verification stages can influence the pipeline outcome.
    @param binary_dir {Path} Directory receiving the fake `uv` executable.
    @return {None} Function return value.
    @satisfies SRS-574, SRS-575
    """
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate every uv pipeline invocation without network access.\n"
        "# @return Exit status 0.\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)


def _create_noop_rm(binary_dir: Path) -> None:
    """@brief Create a fake rm executable reporting success without deleting anything.
    @details Simulates a silent removal failure so the SRS-575 verification stage observes a
    surviving non-git-tracked `dist/` entry.
    @param binary_dir {Path} Directory receiving the fake `rm` executable.
    @return {None} Function return value.
    @satisfies SRS-575
    """
    rm = binary_dir / "rm"
    rm.write_text(
        "#!/bin/sh\n"
        "# @brief Report removal success without touching the filesystem.\n"
        "# @return Exit status 0.\n"
        "exit 0\n",
        encoding="utf-8",
    )
    rm.chmod(0o755)


def _pipeline_environment(tmp_path: Path, binary_dir: Path) -> dict[str, str]:
    """@brief Build an isolated subprocess environment for pre-release pipeline execution.
    @details Redirects HOME to tmp_path, disables shell startup files and Git global
    configuration, and prepends the fake binary directory to PATH.
    @param tmp_path {Path} Pytest-owned disposable filesystem root used as HOME.
    @param binary_dir {Path} Directory containing the fake executables.
    @return {dict[str, str]} Environment mapping for subprocess.run.
    """
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": str(binary_dir) + os.pathsep + os.defpath,
    })
    return environment


def test_pre_release_removes_preexisting_dist_artifacts_before_build(
    tmp_path: Path,
) -> None:
    """@brief Previous release versions are removed from dist/ before the build stage starts.
    @details Level 1: pre-release orchestration -> dist-preparation stage -> build stage
    handoff. Arrange a `dist/` holding one git-tracked artifact and two untracked artifacts of
    previous versions, plus a build stub that snapshots the `dist/` listing it observes. Act by
    running the copied script from a foreign directory. Assert exit status 0, that every
    untracked version is gone, that the tracked payload survives with an English warning, that
    the build stage observed only the tracked payload, and that both new stages run before
    `build`. Complexity O(1) plus one pipeline subprocess; all writes stay under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} A stale version survives into the build stage or the tracked
        payload is deleted.
    @satisfies SRS-574, SRS-575, SRS-576
    """
    # @brief Arrange the repository, the stale artifacts, and the observing build stub.
    snapshot = tmp_path / "dist-snapshot.txt"
    repository = _create_preexisting_dist_repository(
        tmp_path,
        "#!/bin/sh\n"
        "# @brief Snapshot the observed dist/ listing, then materialize build artifacts.\n"
        'for entry in dist/*; do printf \'%s\\n\' "${entry##*/}"; done > "$DIST_SNAPSHOT"\n'
        "mkdir -p dist\n"
        "touch dist/package.tar.gz dist/package.whl\n",
    )
    dist = repository / "dist"
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    _create_success_uv(binary_dir)
    environment = _pipeline_environment(tmp_path, binary_dir)
    environment.update({"DIST_SNAPSHOT": str(snapshot)})

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(repository / "scripts" / "pre-release-check.sh"), "--allow-dirty"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert removal, tracked preservation, build-stage observation, and stage order.
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot.read_text(encoding="utf-8").split() == ["tracked-release.whl"]
    assert not (dist / "cli_usereq-0.74.9.tar.gz").exists()
    assert not (dist / "cli_usereq-0.75.2-py3-none-any.whl").exists()
    assert (dist / "tracked-release.whl").read_text(encoding="utf-8") == "release payload"
    assert (
        "WARNING: cleanup skipped for 'dist/tracked-release.whl'"
        " because it contains git-tracked files"
    ) in result.stderr
    stage_lines = [
        line for line in result.stdout.splitlines() if line.startswith("[pre-release-check] stage ")
    ]
    preparation_index = stage_lines.index("[pre-release-check] stage dist-preparation")
    verification_index = stage_lines.index("[pre-release-check] stage dist-verification")
    build_index = stage_lines.index("[pre-release-check] stage build")
    assert preparation_index < verification_index < build_index
    assert "Pre-release check passed." in result.stdout


def test_pre_release_fails_when_preexisting_artifact_survives(tmp_path: Path) -> None:
    """@brief A surviving non-git-tracked dist/ entry aborts the pipeline at dist-verification.
    @details Level 1 regression: dist-preparation stage -> silent removal failure ->
    dist-verification stage. Arrange the standard stale artifacts and a fake rm that reports
    success without deleting, so only the SRS-575 verification can detect the residue. Act by
    running the copied script from a foreign directory. Assert exit status 1, the canonical
    stage-failure diagnostic naming the verification stage, the residual-path diagnostic, and
    that the build stage never starts. Complexity O(1) plus one pipeline subprocess.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} The surviving artifact is not reported or the build stage runs.
    @satisfies SRS-574, SRS-575, SRS-576
    """
    # @brief Arrange the repository and a removal stub that silently keeps every entry.
    repository = _create_preexisting_dist_repository(tmp_path, "#!/bin/sh\nexit 0\n")
    stale_artifact = repository / "dist" / "cli_usereq-0.74.9.tar.gz"
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    _create_success_uv(binary_dir)
    _create_noop_rm(binary_dir)

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(repository / "scripts" / "pre-release-check.sh"), "--allow-dirty"],
        cwd=tmp_path,
        env=_pipeline_environment(tmp_path, binary_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert verification gating, diagnostics, and absent build stage.
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Pre-release check failed at stage dist-verification." in result.stderr
    assert "pre-existing release artifact 'dist/cli_usereq-0.74.9.tar.gz'" in result.stderr
    assert "was not removed from dist/" in result.stderr
    assert stale_artifact.exists()
    assert "[pre-release-check] stage build" not in result.stdout
    assert "Pre-release check passed." not in result.stdout
