"""@file test_build_script.py
@brief Verify scripts/build.sh performs pre-build cleanup, post-build cleanup, and stage gating.
@details Level 1: script orchestration -> stage execution -> Git/filesystem boundaries.
Uses a temporary Git repository holding a copy of scripts/build.sh and the project .gitignore,
a fake uv executable that materializes build artifacts and intermediates, and a fake rm
executable for injected removal failures; no network or user paths are touched.
@satisfies SRS-546, SRS-548, SRS-549, SRS-550, SRS-551, SRS-565, SRS-566, SRS-567, SRS-568, SRS-569, SRS-570
"""

import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _create_repository(tmp_path: Path) -> Path:
    """@brief Create an isolated Git repository containing build.sh and the project ignore policy.
    @details Copies scripts/build.sh and the project .gitignore into a fresh Git repository so
    `git ls-files` classifies tracked content exactly as in the real project. O(1) filesystem
    writes plus one `git init`; all writes remain under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {Path} Absolute path of the isolated repository root.
    @throws {subprocess.CalledProcessError} Raised when `git init` fails.
    @satisfies SRS-546
    """
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "build.sh"
    shutil.copyfile(REPOSITORY_ROOT / "scripts" / "build.sh", script)
    script.chmod(0o755)
    shutil.copyfile(REPOSITORY_ROOT / ".gitignore", repository / ".gitignore")
    (repository / "src").mkdir()
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True, capture_output=True,
    )
    return repository


def _create_fake_uv(binary_dir: Path) -> None:
    """@brief Create the deterministic fake uv executable emulating the build stage.
    @details The fake writes one sdist, one wheel, one build/ intermediate directory, and one
    src/*.egg-info metadata directory for the `-m build` invocation and exits 0 otherwise, so
    the post-build cleanup and artifact-verification stages observe real filesystem entries.
    O(1) filesystem writes.
    @param binary_dir {Path} Directory receiving the fake `uv` executable.
    @return {None} Function return value.
    @satisfies SRS-549, SRS-569
    """
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate the uv build invocation without network access.\n"
        "# @details Build writes one sdist, one wheel, a build/ directory, and an egg-info\n"
        "# directory into the repository tree.\n"
        "# @return Exit status 0.\n"
        'case "$*" in\n'
        '  *" -m build "*)\n'
        "    mkdir -p dist build/lib src/cli_usereq.egg-info\n"
        "    touch dist/package.tar.gz dist/package.whl\n"
        "    touch build/lib/package.py src/cli_usereq.egg-info/PKG-INFO\n"
        "    ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)


def _create_fake_rm(tmp_path: Path, binary_dir: Path, inject_rm_failure: bool) -> None:
    """@brief Create the deterministic fake rm executable with optional one-shot failure.
    @details When `inject_rm_failure` is true the first invocation exits 1 without removing
    anything, then every later invocation delegates to the real rm. This isolates a removal
    failure independent of directory listing order. O(1) filesystem writes.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param binary_dir {Path} Directory receiving the fake `rm` executable.
    @param inject_rm_failure {bool} Inject one transient removal failure when true.
    @return {None} Function return value.
    @throws {AssertionError} Raised when the real rm executable cannot be located.
    @satisfies SRS-548
    """
    real_rm = shutil.which("rm")
    assert real_rm is not None, "rm executable must be available for the fixture"
    consumed_flag = tmp_path / "rm-failure-consumed"
    failure_clause = ""
    if inject_rm_failure:
        failure_clause = (
            f"if [ ! -e {shlex.quote(str(consumed_flag))} ]; then\n"
            f"  touch {shlex.quote(str(consumed_flag))}\n"
            "  exit 1\n"
            "fi\n"
        )
    rm = binary_dir / "rm"
    rm.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate one transient removal failure for the dist-preparation stage.\n"
        "# @details First invocation exits 1 when injection is enabled; later calls delegate.\n"
        "# @return Exit status 1 once when injected, otherwise the real rm status.\n"
        + failure_clause
        + f"exec {shlex.quote(real_rm)} \"$@\"\n",
        encoding="utf-8",
    )
    rm.chmod(0o755)


def _create_binary_dir(tmp_path: Path, inject_rm_failure: bool = False) -> Path:
    """@brief Create the isolated binary directory with the fake uv and rm executables.
    @details Delegates to `_create_fake_uv` and `_create_fake_rm`.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param inject_rm_failure {bool} Inject one transient rm failure when true.
    @return {Path} Binary directory to prepend to PATH.
    @satisfies SRS-549
    """
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    _create_fake_uv(binary_dir)
    _create_fake_rm(tmp_path, binary_dir, inject_rm_failure)
    return binary_dir


def _environment(tmp_path: Path, path_value: str) -> dict[str, str]:
    """@brief Build an isolated subprocess environment for build.sh execution.
    @details Redirects HOME to tmp_path, disables shell startup files and Git global
    configuration, and pins PATH to the supplied value.
    @param tmp_path {Path} Pytest-owned disposable filesystem root used as HOME.
    @param path_value {str} PATH value for the child process.
    @return {dict[str, str]} Environment mapping for subprocess.run.
    """
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": path_value,
    })
    return environment


def _run_build(repository: Path, tmp_path: Path, binary_dir: Path) -> subprocess.CompletedProcess[str]:
    """@brief Execute the fixture build.sh from a foreign working directory.
    @details Invokes the script through bash with cwd set outside the repository so the
    SRS-546 root-resolution contract is exercised on every test.
    @param repository {Path} Fixture repository root holding scripts/build.sh.
    @param tmp_path {Path} Foreign working directory for the invocation.
    @param binary_dir {Path} Directory containing fake uv and rm executables.
    @return {subprocess.CompletedProcess[str]} Captured process result.
    @satisfies SRS-546
    """
    return subprocess.run(
        ["bash", str(repository / "scripts" / "build.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path, str(binary_dir) + os.pathsep + os.defpath),
        capture_output=True,
        text=True,
        check=False,
    )


def test_build_removes_all_untracked_dist_versions(tmp_path: Path) -> None:
    """@brief Pre-build cleanup removes stale artifacts of every previously built version.
    @details Arrange several untracked artifacts with distinct version numbers plus the
    build/ and egg-info intermediates. Act by executing build.sh to completion. Assert exit
    status 0, every stale version is gone, the current artifacts remain in dist/, the build
    intermediates are removed after the build, and the cleanup summary reports the removals.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} A stale version survives or an intermediate artifact remains.
    @satisfies SRS-548, SRS-567, SRS-569, SRS-570
    """
    # @brief Arrange stale artifacts for multiple versions plus build intermediates.
    repository = _create_repository(tmp_path)
    dist = repository / "dist"
    dist.mkdir()
    stale = [
        dist / "cli_usereq-0.0.1.tar.gz",
        dist / "cli_usereq-0.0.1-py3-none-any.whl",
        dist / "cli_usereq-0.74.9.tar.gz",
        dist / "cli_usereq-0.75.2-py3-none-any.whl",
    ]
    for entry in stale:
        entry.write_text("stale artifact", encoding="utf-8")
    (repository / "build").mkdir()
    (repository / "build" / "stale.o").write_text("stale", encoding="utf-8")
    egg_info = repository / "src" / "cli_usereq.egg-info"
    egg_info.mkdir()
    (egg_info / "PKG-INFO").write_text("stale metadata", encoding="utf-8")
    binary_dir = _create_binary_dir(tmp_path)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_build(repository, tmp_path, binary_dir)

    # @brief Assert stale removal, artifact retention, intermediate cleanup, and summary.
    assert result.returncode == 0, result.stdout + result.stderr
    for entry in stale:
        assert not entry.exists()
    assert (dist / "package.tar.gz").exists()
    assert (dist / "package.whl").exists()
    assert not (repository / "build").exists()
    assert not egg_info.exists()
    assert "[build] stage dist-preparation" in result.stdout
    assert "[build] stage intermediate-preparation" in result.stdout
    assert "[build] stage intermediate-cleanup" in result.stdout
    assert "[build] artifacts in dist/:" in result.stdout
    assert "  package.tar.gz" in result.stdout
    assert "  package.whl" in result.stdout
    assert "[build] removed 8 path(s):" in result.stdout
    assert "  dist/cli_usereq-0.0.1.tar.gz" in result.stdout
    assert "  src/cli_usereq.egg-info" in result.stdout
    assert "[build] skipped 0 git-tracked path(s):" in result.stdout


def test_build_preserves_git_tracked_dist_entry(tmp_path: Path) -> None:
    """@brief Pre-build cleanup preserves git-tracked dist/ entries with an English warning.
    @details Arrange a force-added release artifact under dist/ and an untracked stale entry.
    Act by executing build.sh. Assert exit status 0, the tracked payload survives, the untracked
    sibling is removed, the warning identifies the skipped path, and the summary reports it.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Tracked content is deleted or the warning is missing.
    @satisfies SRS-548, SRS-568, SRS-570
    """
    # @brief Arrange a tracked release artifact and an untracked stale sibling.
    repository = _create_repository(tmp_path)
    dist = repository / "dist"
    dist.mkdir()
    tracked_artifact = dist / "tracked-release-0.75.0.whl"
    tracked_artifact.write_text("release payload", encoding="utf-8")
    stale_artifact = dist / "stale-release-0.1.0.tar.gz"
    stale_artifact.write_text("stale payload", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repository), "add", "-f", "--", "dist/tracked-release-0.75.0.whl"],
        check=True, capture_output=True,
    )
    binary_dir = _create_binary_dir(tmp_path)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_build(repository, tmp_path, binary_dir)

    # @brief Assert tracked preservation, untracked removal, and skip reporting.
    assert result.returncode == 0, result.stdout + result.stderr
    assert tracked_artifact.read_text(encoding="utf-8") == "release payload"
    assert not stale_artifact.exists()
    assert (
        "WARNING: cleanup skipped for 'dist/tracked-release-0.75.0.whl'"
        " because it contains git-tracked files"
    ) in result.stderr
    assert "[build] skipped 1 git-tracked path(s):" in result.stdout
    assert "  dist/tracked-release-0.75.0.whl" in result.stdout
    assert (repository / "dist" / "package.tar.gz").exists()


@pytest.mark.parametrize(
    "tracked_egg_info",
    [False, True],
    ids=["untracked-egg-info", "tracked-egg-info"],
)
def test_build_prunes_only_untracked_egg_info(
    tmp_path: Path, tracked_egg_info: bool,
) -> None:
    """@brief Build removes only untracked generated egg-info directories.
    @details Arrange an egg-info directory under src/, optionally added to the Git index with
    `git add -f`. Act by running build.sh to completion. Assert exit status 0, that the release
    artifacts remain in dist/, the artifact summary is printed, and the egg-info directory exists
    exactly when it is git-tracked.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param tracked_egg_info {bool} True when the egg-info directory is present in the Git index.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Untracked egg-info survives or tracked egg-info is removed.
    @satisfies SRS-548, SRS-549, SRS-550, SRS-551, SRS-568, SRS-569
    """
    # @brief Arrange isolated repository and egg-info directory with the requested tracking state.
    repository = _create_repository(tmp_path)
    egg_info = repository / "src" / "cli_usereq.egg-info"
    egg_info.mkdir()
    (egg_info / "PKG-INFO").write_text("stale metadata", encoding="utf-8")
    if tracked_egg_info:
        subprocess.run(
            ["git", "-C", str(repository), "add", "-f", "--", "src/cli_usereq.egg-info"],
            check=True, capture_output=True,
        )
    binary_dir = _create_binary_dir(tmp_path)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_build(repository, tmp_path, binary_dir)

    # @brief Assert success, artifact retention, summary output, and egg-info policy.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Release build failed" not in result.stderr
    assert (repository / "dist" / "package.tar.gz").exists()
    assert (repository / "dist" / "package.whl").exists()
    assert "[build] artifacts in dist/:" in result.stdout
    assert egg_info.exists() is tracked_egg_info
    if tracked_egg_info:
        assert "WARNING: cleanup skipped for 'src/cli_usereq.egg-info'" in result.stderr


def test_build_removal_failure_aborts_before_compile(tmp_path: Path) -> None:
    """@brief A failing removal inside dist-preparation aborts the build before compile runs.
    @details Arrange two untracked stale entries under dist/ and a fake rm failing once. Act by
    executing build.sh from a foreign directory. Assert exit status 1, the canonical
    stage-failure diagnostic, the surviving stale entry, and that the compile stage never starts.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Stage failure is masked or compile runs after a failed prune.
    @satisfies SRS-548, SRS-551
    """
    # @brief Arrange isolated repository, stale artifacts, and fake tools.
    repository = _create_repository(tmp_path)
    dist = repository / "dist"
    dist.mkdir()
    (dist / "stale-one.tar.gz").write_text("stale", encoding="utf-8")
    (dist / "stale-two.whl").write_text("stale", encoding="utf-8")
    binary_dir = _create_binary_dir(tmp_path, inject_rm_failure=True)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_build(repository, tmp_path, binary_dir)

    # @brief Assert failure propagation and stage ordering.
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Release build failed at stage dist-preparation." in result.stderr
    assert "[build] stage compile" not in result.stdout
    assert (dist / "stale-one.tar.gz").exists() or (dist / "stale-two.whl").exists()


def test_build_reports_post_build_intermediate_cleanup(tmp_path: Path) -> None:
    """@brief A fresh checkout build reports the post-build intermediate removals.
    @details Arrange a repository without dist/, build/, or egg-info content. Act by executing
    build.sh. Assert exit status 0, a summary reporting the two intermediates created and
    removed by the build, and zero skipped git-tracked paths.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} The cleanup summary is missing or incorrect.
    @satisfies SRS-548, SRS-569, SRS-570
    """
    # @brief Arrange an isolated repository without any build artifact.
    repository = _create_repository(tmp_path)
    binary_dir = _create_binary_dir(tmp_path)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_build(repository, tmp_path, binary_dir)

    # @brief Assert success and the post-build cleanup summary.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Release build failed" not in result.stderr
    assert "[build] removed 2 path(s):" in result.stdout
    assert "  build" in result.stdout
    assert "  src/cli_usereq.egg-info" in result.stdout
    assert "[build] skipped 0 git-tracked path(s):" in result.stdout


def test_build_requires_git_command(tmp_path: Path) -> None:
    """@brief Build aborts with an English error when git is not executable.
    @details Restrict PATH to a directory holding bash, readlink, dirname, and the fake uv
    executable while omitting git. Act by executing build.sh. Assert exit status 1 and the
    English git diagnostic.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} The missing git dependency is not reported.
    @satisfies SRS-566
    """
    # @brief Arrange a restricted binary directory without git.
    repository = _create_repository(tmp_path)
    binary_dir = tmp_path / "restricted-bin"
    binary_dir.mkdir()
    for tool in ("bash", "readlink", "dirname"):
        resolved = shutil.which(tool)
        assert resolved is not None, f"{tool} must be available for the fixture"
        (binary_dir / tool).symlink_to(resolved)
    _create_fake_uv(binary_dir)

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(repository / "scripts" / "build.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path, str(binary_dir)),
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert the missing git dependency aborts the build.
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ERROR: git command not found in PATH" in result.stderr
    assert "[build] stage compile" not in result.stdout
