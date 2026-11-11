"""@file test_clean_script.py
@brief Verify scripts/clean.sh removes build.sh artifacts and preserves git-tracked content.
@details Level 1: script orchestration -> stage execution -> Git/filesystem boundaries.
Uses a temporary Git repository holding a copy of scripts/clean.sh and the project
.gitignore; no network or user paths are touched. Covers untracked artifact removal,
git-tracked preservation with warnings, empty-dist directory removal, idempotent no-op
execution, and foreign working-directory execution.
@satisfies SRS-559, SRS-561, SRS-562, SRS-563, SRS-564, SRS-565
"""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _create_repository(tmp_path: Path) -> Path:
    """@brief Create an isolated Git repository containing clean.sh and the project ignore policy.
    @details Copies scripts/clean.sh and the project .gitignore into a fresh Git repository so
    `git ls-files` classifies tracked content exactly as in the real project. O(1) filesystem
    writes plus one `git init`; all writes remain under tmp_path.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {Path} Absolute path of the isolated repository root.
    @throws {subprocess.CalledProcessError} Raised when `git init` fails.
    @satisfies SRS-559
    """
    repository = tmp_path / "repository with spaces"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "clean.sh"
    shutil.copyfile(REPOSITORY_ROOT / "scripts" / "clean.sh", script)
    script.chmod(0o755)
    shutil.copyfile(REPOSITORY_ROOT / ".gitignore", repository / ".gitignore")
    (repository / "src").mkdir()
    subprocess.run(
        ["git", "init", "--quiet", str(repository)], check=True, capture_output=True,
    )
    return repository


def _create_build_artifacts(repository: Path) -> dict[str, Path]:
    """@brief Materialize the artifact set produced by scripts/build.sh inside a fixture repository.
    @details Creates two untracked release artifacts under dist/, the setuptools build/
    intermediate directory, and one src/*.egg-info metadata directory with one payload file
    each. O(1) filesystem writes; all writes remain under the fixture repository.
    @param repository {Path} Fixture repository root created by `_create_repository`.
    @return {dict[str, Path]} Mapping of artifact labels to their absolute paths.
    """
    dist = repository / "dist"
    dist.mkdir()
    build = repository / "build"
    build.mkdir()
    egg_info = repository / "src" / "cli_usereq.egg-info"
    egg_info.mkdir()
    artifacts = {
        "sdist": dist / "package.tar.gz",
        "wheel": dist / "package.whl",
        "build_payload": build / "intermediate.o",
        "egg_info_payload": egg_info / "PKG-INFO",
    }
    for payload in artifacts.values():
        payload.write_text("build artifact", encoding="utf-8")
    return artifacts


def _environment(tmp_path: Path) -> dict[str, str]:
    """@brief Build an isolated subprocess environment for clean.sh execution.
    @details Redirects HOME to tmp_path, disables shell startup files and Git global
    configuration, and keeps the standard binary lookup path so real git/find/rm run.
    @param tmp_path {Path} Pytest-owned disposable filesystem root used as HOME.
    @return {dict[str, str]} Environment mapping for subprocess.run.
    """
    environment = dict(os.environ)
    environment.update({
        "HOME": str(tmp_path),
        "BASH_ENV": os.devnull,
        "ENV": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": os.defpath,
    })
    return environment


def _run_clean(repository: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """@brief Execute the fixture clean.sh from a foreign working directory.
    @details Invokes the script through bash with cwd set outside the repository so the
    SRS-559 root-resolution contract is exercised on every test.
    @param repository {Path} Fixture repository root holding scripts/clean.sh.
    @param tmp_path {Path} Foreign working directory for the invocation.
    @return {subprocess.CompletedProcess[str]} Captured process result.
    """
    return subprocess.run(
        ["bash", str(repository / "scripts" / "clean.sh")],
        cwd=tmp_path,
        env=_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_removes_untracked_build_artifacts(tmp_path: Path) -> None:
    """@brief Clean removes every untracked build.sh artifact and the emptied dist/ directory.
    @details Arrange the full untracked artifact set (sdist, wheel, build/, egg-info). Act by
    executing clean.sh from a foreign directory. Assert exit status 0, removal of every
    artifact, removal of the emptied dist/ directory, stage progress lines, and the summary
    reporting four removed and zero skipped paths.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} An untracked artifact survives or the summary is incorrect.
    @satisfies SRS-559, SRS-561, SRS-562, SRS-564
    """
    # @brief Arrange isolated repository with the full untracked build artifact set.
    repository = _create_repository(tmp_path)
    _create_build_artifacts(repository)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_clean(repository, tmp_path)

    # @brief Assert exit status, artifact removal, and summary content.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Repository clean failed" not in result.stderr
    assert not (repository / "dist").exists()
    assert not (repository / "build").exists()
    assert not (repository / "src" / "cli_usereq.egg-info").exists()
    assert "[clean] stage dist-cleanup" in result.stdout
    assert "[clean] stage intermediate-cleanup" in result.stdout
    assert "[clean] removed 4 path(s):" in result.stdout
    assert "  dist/package.tar.gz" in result.stdout
    assert "  dist/package.whl" in result.stdout
    assert "  build" in result.stdout
    assert "  src/cli_usereq.egg-info" in result.stdout
    assert "[clean] skipped 0 git-tracked path(s):" in result.stdout


@pytest.mark.parametrize(
    ("tracked_path", "kept_path", "sibling_path"),
    [
        ("dist/package.whl", "dist/package.whl", "dist/package.tar.gz"),
        ("build", "build/intermediate.o", "dist/package.tar.gz"),
        (
            "src/cli_usereq.egg-info",
            "src/cli_usereq.egg-info/PKG-INFO",
            "dist/package.tar.gz",
        ),
    ],
    ids=["tracked-dist-entry", "tracked-build-dir", "tracked-egg-info"],
)
def test_clean_preserves_git_tracked_targets(
    tmp_path: Path, tracked_path: str, kept_path: str, sibling_path: str,
) -> None:
    """@brief Clean preserves any removal target containing git-tracked files with a warning.
    @details Arrange the full artifact set and force-add one target to the Git index. Act by
    executing clean.sh. Assert exit status 0, the tracked target payload survives, the English
    warning identifies the repository-relative skipped path, untracked sibling artifacts are
    removed, and the summary reports the skip.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param tracked_path {str} Repository-relative path force-added to the Git index.
    @param kept_path {str} Repository-relative payload expected to survive.
    @param sibling_path {str} Repository-relative untracked artifact expected to be removed.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} Tracked content is deleted or an untracked sibling survives.
    @satisfies SRS-561, SRS-562, SRS-563, SRS-564
    """
    # @brief Arrange isolated repository, artifacts, and one git-tracked removal target.
    repository = _create_repository(tmp_path)
    _create_build_artifacts(repository)
    subprocess.run(
        ["git", "-C", str(repository), "add", "-f", "--", tracked_path],
        check=True, capture_output=True,
    )

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_clean(repository, tmp_path)

    # @brief Assert tracked preservation, warning emission, and untracked sibling removal.
    assert result.returncode == 0, result.stdout + result.stderr
    assert (repository / kept_path).exists()
    assert (repository / kept_path).read_text(encoding="utf-8") == "build artifact"
    assert not (repository / sibling_path).exists()
    assert (
        f"WARNING: cleanup skipped for '{tracked_path}'"
        " because it contains git-tracked files"
    ) in result.stderr
    assert "[clean] skipped 1 git-tracked path(s):" in result.stdout
    assert f"  {tracked_path}" in result.stdout
    if tracked_path.startswith("dist/"):
        assert (repository / "dist").exists()


def test_clean_without_artifacts_is_noop(tmp_path: Path) -> None:
    """@brief Clean exits 0 with empty removed/skipped summaries when no artifact exists.
    @details Arrange a repository without dist/, build/, or egg-info content. Act by executing
    clean.sh. Assert exit status 0 and zero-count summary lines, proving idempotent no-op
    behavior on a fresh checkout.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @return {None} Assertions complete on matching observable behavior.
    @throws {AssertionError} The no-op execution fails or reports phantom removals.
    @satisfies SRS-561, SRS-562, SRS-564
    """
    # @brief Arrange isolated repository without any build artifact.
    repository = _create_repository(tmp_path)

    # @brief Act through the public shell interface from a foreign directory.
    result = _run_clean(repository, tmp_path)

    # @brief Assert success and empty summaries.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Repository clean failed" not in result.stderr
    assert "[clean] removed 0 path(s):" in result.stdout
    assert "[clean] skipped 0 git-tracked path(s):" in result.stdout
