"""@file test_build_script.py
@brief Verify scripts/build.sh propagates stage failures and prunes only disposable intermediates.
@details Level 1: script orchestration -> stage execution -> dist/ pruning and egg-info cleanup
boundaries. Uses a temporary Git repository holding a copy of scripts/build.sh and the project
.gitignore, a fake uv executable, and a fake rm executable; no network or user paths are touched.
@satisfies SRS-546, SRS-548, SRS-549, SRS-550, SRS-551
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
    `git check-ignore` classifies dist/ and egg-info entries exactly as in the real project.
    O(1) filesystem writes plus one `git init`; all writes remain under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {Path} Absolute path of the isolated repository root.
    @throws {subprocess.CalledProcessError} Raised when `git init` fails.
    @satisfies SRS-546, SRS-548
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


def _create_fake_tools(tmp_path: Path, inject_rm_failure: bool) -> Path:
    """@brief Create deterministic fake uv and rm executables in an isolated binary directory.
    @details The fake uv writes one sdist, one wheel, and an egg-info directory for the
    `-m build` invocation and exits 0 otherwise. The fake rm, when `inject_rm_failure` is true,
    exits 1 without removing anything on its first invocation only, then delegates every later
    invocation to the real rm. This isolates a non-final loop iteration failure independent of
    directory listing order. O(1) filesystem writes.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param inject_rm_failure {bool} Inject one transient removal failure when true.
    @return {Path} Binary directory to prepend to PATH.
    @throws {AssertionError} Raised when the real rm executable cannot be located.
    @satisfies SRS-548, SRS-549
    """
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    uv = binary_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "# @brief Emulate the uv build invocation without network access.\n"
        "# @details Build writes one sdist, one wheel, and an egg-info directory into the tree.\n"
        "# @return Exit status 0.\n"
        'case "$*" in\n'
        '  *" -m build "*)\n'
        "    mkdir -p dist src/cli_usereq.egg-info\n"
        "    touch dist/package.tar.gz dist/package.whl src/cli_usereq.egg-info/PKG-INFO\n"
        "    ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)

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
    return binary_dir


def _environment(tmp_path: Path, binary_dir: Path) -> dict[str, str]:
    """@brief Build an isolated subprocess environment for build.sh execution.
    @details Redirects HOME to tmp_path, disables shell startup files and Git global
    configuration, and prepends the fake binary directory to PATH.
    @param tmp_path {Path} Pytest-owned disposable filesystem root used as HOME.
    @param binary_dir {Path} Directory containing fake uv and rm executables.
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


def test_build_stage_failure_aborts_before_compile(tmp_path: Path) -> None:
    """@brief A failing removal inside dist-preparation aborts the build before compile runs.
    @details Arrange two gitignored stale entries under dist/ and a fake rm failing once.
    Act by executing build.sh from a foreign directory. Assert exit status 1, the canonical
    stage-failure diagnostic, the surviving stale entry, and that the compile stage never starts.
    Pre-fix behavior: the failing rm is masked inside `if ! "$@"` and the build reports success.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Stage failure is masked or compile runs after a failed prune.
    @satisfies SRS-548, SRS-551
    """
    # @brief Arrange isolated repository, stale gitignored artifacts, and fake tools.
    repository = _create_repository(tmp_path)
    dist = repository / "dist"
    dist.mkdir()
    (dist / "stale-one.tar.gz").write_text("stale", encoding="utf-8")
    (dist / "stale-two.whl").write_text("stale", encoding="utf-8")
    # @brief Re-ignore the stale entries so dist-preparation classifies them as gitignored.
    with (repository / ".gitignore").open("a", encoding="utf-8") as handle:
        handle.write("\ndist/stale-*\n")
    binary_dir = _create_fake_tools(tmp_path, inject_rm_failure=True)

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(repository / "scripts" / "build.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path, binary_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert failure propagation and stage ordering.
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Release build failed at stage dist-preparation." in result.stderr
    assert "[build] stage compile" not in result.stdout
    assert (dist / "stale-one.tar.gz").exists() or (dist / "stale-two.whl").exists()


@pytest.mark.parametrize(
    "tracked_egg_info",
    [False, True],
    ids=["untracked-egg-info", "tracked-egg-info"],
)
def test_build_success_prunes_only_untracked_egg_info(
    tmp_path: Path, tracked_egg_info: bool,
) -> None:
    """@brief Successful build removes only untracked generated egg-info directories.
    @details Arrange an egg-info directory under src/, optionally added to the Git index with
    `git add -f`. Act by running build.sh to completion. Assert exit status 0, that the release
    artifacts remain in dist/, the artifact summary is printed, and the egg-info directory exists
    exactly when it is git-tracked.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param tracked_egg_info {bool} True when the egg-info directory is present in the Git index.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Untracked egg-info survives or tracked egg-info is removed.
    @satisfies SRS-548, SRS-549, SRS-550, SRS-551
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
    binary_dir = _create_fake_tools(tmp_path, inject_rm_failure=False)

    # @brief Act through the public shell interface from a foreign directory.
    result = subprocess.run(
        ["bash", str(repository / "scripts" / "build.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path, binary_dir),
        capture_output=True,
        text=True,
        check=False,
    )

    # @brief Assert success, artifact retention, summary output, and egg-info policy.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Release build failed" not in result.stderr
    assert (repository / "dist" / "package.tar.gz").exists()
    assert (repository / "dist" / "package.whl").exists()
    assert "[build] artifacts in dist/:" in result.stdout
    assert egg_info.exists() is tracked_egg_info
