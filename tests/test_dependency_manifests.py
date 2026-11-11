"""@brief Validate repository dependency manifest invariants.
@details Enforces alignment between uv.lock and packaging metadata plus req.sh invocation semantics for uv-based execution behavior. Includes package-data coverage validation for resource subdirectories.
@satisfies SRS-055
@satisfies SRS-056
@satisfies SRS-342
@satisfies SRS-264
@satisfies SRS-272
@satisfies SRS-273
@satisfies SRS-274
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"
UV_LOCK_PATH = REPO_ROOT / "uv.lock"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
REQ_SCRIPT_PATH = REPO_ROOT / "scripts" / "req.sh"
README_PATH = REPO_ROOT / "README.md"
RESOURCES_DIR = REPO_ROOT / "src" / "usereq" / "resources"
REQUIRED_OPERATIONAL_RESOURCE_SUBDIRS = {
    "prompts",
    "templates",
}


def _normalize_requirement_name(requirement: str) -> str:
    """@brief Extract canonical package name token from requirement entry.
    @details Uses a deterministic regex to capture the leading PEP 508 package token and normalizes underscores to hyphens.
    @param requirement {str} Raw requirement/specifier entry from pyproject lists or uv.lock package names.
    @return {str} Normalized package name in lowercase.
    @throws {ValueError} Raised when the entry cannot be parsed into a package token.
    """

    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    if match is None:
        raise ValueError(f"Cannot parse requirement entry: {requirement!r}")
    return match.group(1).replace("_", "-").lower()


def _read_uv_lock_packages() -> set[str]:
    """@brief Parse uv.lock into a normalized package-name set.
    @details Reads the lockfile TOML and collects every `[[package]].name` token
    after deterministic normalization for set-level checks against pyproject declarations.
    @return {set[str]} Distinct normalized package names declared in uv.lock.
    """

    lock_data = tomllib.loads(UV_LOCK_PATH.read_text(encoding="utf-8"))
    package_entries = lock_data.get("package", [])
    assert isinstance(package_entries, list), "uv.lock must define a [[package]] list"
    package_names = {
        _normalize_requirement_name(entry["name"])
        for entry in package_entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    assert package_names, "uv.lock must define at least one package name"
    return package_names


def test_repository_uses_uv_lock_and_omits_requirements_txt() -> None:
    """@brief Assert repository dependency-manifest policy uses uv.lock only.
    @details Ensures uv.lock exists as canonical lockfile and root requirements.txt
    is absent from tracked project files.
    @return {None} No return value.
    @satisfies SRS-055
    """

    assert UV_LOCK_PATH.exists(), "uv.lock must exist at repository root"
    assert not REQUIREMENTS_PATH.exists(), "requirements.txt must not exist at repository root"


def test_gitignore_unignores_uv_lock_and_not_requirements_txt() -> None:
    """@brief Assert .gitignore tracks uv.lock and no longer unignores requirements.txt.
    @details Validates root .gitignore contains `!uv.lock` and excludes obsolete
    `!requirements.txt` unignore rule to keep lockfile tracking policy deterministic.
    @return {None} No return value.
    @satisfies SRS-055
    """

    content = GITIGNORE_PATH.read_text(encoding="utf-8")
    assert "!uv.lock" in content, ".gitignore must include !uv.lock unignore rule"
    assert (
        "!requirements.txt" not in content
    ), ".gitignore must not include !requirements.txt unignore rule"


def test_pyproject_dependencies_are_present_in_uv_lock() -> None:
    """@brief Verify pyproject dependency declarations are present in uv.lock.
    @details Compares project.dependencies after normalization against uv.lock
    package names. Runtime declarations MUST be represented by locked packages.
    Build-system requirements are validated independently of lock membership.
    @return {None} No return value.
    @satisfies SRS-264
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project_dependencies = pyproject_data["project"]["dependencies"]
    pyproject_packages = {
        _normalize_requirement_name(entry)
        for entry in project_dependencies
    }
    uv_lock_packages = _read_uv_lock_packages()
    assert pyproject_packages <= uv_lock_packages, (
        f"pyproject.toml declares packages not represented in uv.lock: "
        f"{sorted(pyproject_packages - uv_lock_packages)}"
    )


def test_pyproject_dependencies_include_ruff_and_pyright() -> None:
    """@brief Verify pyproject.toml project.dependencies includes ruff and pyright.
    @details Ensures static-analysis tools are declared as runtime dependencies
    so they are installed with the package, enabling internal module-based invocation
    via sys.executable without requiring external PATH availability.
    @return {None} No return value.
    @satisfies SRS-338, SRS-340
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project_dependencies = pyproject_data["project"]["dependencies"]
    normalized_deps = {
        _normalize_requirement_name(entry)
        for entry in project_dependencies
    }
    required_static_tools = {"ruff", "pyright"}
    missing = required_static_tools - normalized_deps
    assert not missing, (
        f"pyproject.toml [project].dependencies missing static-analysis tools: "
        f"{sorted(missing)}. Required: {sorted(required_static_tools)}"
    )


def test_req_sh_executes_cli_with_uv_run() -> None:
    """@brief Validate req.sh executes CLI through uv-managed runtime without virtualenv bootstrap.
    @details Confirms req.sh forwards CLI arguments unchanged through `uv run`,
    executes `python -m usereq.cli`, and does not create or activate `.venv` manually.
    @return {None} No return value.
    """

    content = REQ_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "exec uv run" in content
    assert "python -m usereq.cli" in content
    assert '"$@"' in content
    assert "virtualenv" not in content
    assert "pip install -r" not in content
    assert "/bin/activate" not in content
    assert "${VENVDIR}/bin/python3" not in content
    assert "REQ_HASH_FILE=" not in content
    assert "sha256sum" not in content


def test_req_sh_forwards_git_base_argument(tmp_path: Path) -> None:
    """@brief Verify req.sh forwards the mandatory --git-base argument unchanged.
    @details Executes req.sh from an isolated non-git directory and calls
    `--git-check --git-base <target>`; expected behavior is failure with the git
    resolution diagnostic because the forwarded base is not inside a git repository.
    @param tmp_path {Path} Pytest-provided isolated temporary directory.
    @return {None} No return value.
    @satisfies SRS-056
    @satisfies SRS-311, SRS-391, SRS-397
    """

    target_cwd = tmp_path / "external-project"
    target_cwd.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(REQ_SCRIPT_PATH), "--git-check", "--git-base", str(target_cwd)],
        cwd=target_cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "is not inside a git repository" in result.stderr


def test_python_module_cli_entrypoint_emits_no_runpy_runtimewarning() -> None:
    """@brief Verify module-mode CLI execution does not emit runpy pre-import warning.
    @details Executes `python -m usereq.cli --ver` under repository PYTHONPATH and
    asserts stderr does not contain the known runpy RuntimeWarning emitted when
    `usereq.cli` is imported by package initialization before module execution.
    @return {None} No return value.
    @satisfies SRS-056
    """

    existing_pythonpath = os.environ.get("PYTHONPATH")
    composed_pythonpath = str(REPO_ROOT / "src")
    if existing_pythonpath:
        composed_pythonpath = f"{composed_pythonpath}:{existing_pythonpath}"
    env = {**os.environ, "PYTHONPATH": composed_pythonpath}
    result = subprocess.run(
        [sys.executable, "-m", "usereq.cli", "--ver"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "RuntimeWarning" not in result.stderr, result.stderr
    assert "usereq.cli" not in result.stderr, result.stderr


def test_python_module_cli_executes_main_for_ver_flag() -> None:
    """@brief Verify `python -m usereq.cli` executes CLI main for version requests.
    @details Executes module mode with `--ver` and asserts version text is printed
    on stdout, proving module execution invokes `main()` rather than importing only.
    @return {None} No return value.
    @satisfies SRS-056
    """

    existing_pythonpath = os.environ.get("PYTHONPATH")
    composed_pythonpath = str(REPO_ROOT / "src")
    if existing_pythonpath:
        composed_pythonpath = f"{composed_pythonpath}:{existing_pythonpath}"
    env = {**os.environ, "PYTHONPATH": composed_pythonpath}
    result = subprocess.run(
        [sys.executable, "-m", "usereq.cli", "--ver"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), "Expected version output on stdout for --ver"


def test_readme_includes_requirements_section_with_uv_tool() -> None:
    """@brief Validate README declares Astral uv tool requirement in a dedicated Requirements section.
    @details Confirms README includes the `## Requirements` heading and explicitly states Astral `uv` tool is required.
    @return {None} No return value.
    @satisfies SRS-342
    """

    content = README_PATH.read_text(encoding="utf-8")
    assert "## Requirements" in content
    assert "Astral `uv` tool is required" in content


def _get_package_data_patterns() -> list[str]:
    """@brief Extract package-data glob patterns from pyproject.toml for usereq.
    @details Reads [tool.setuptools.package-data].usereq and returns the declared patterns list.
    @return {list[str]} List of glob pattern strings declared as package data.
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    return pyproject_data["tool"]["setuptools"]["package-data"]["usereq"]


def _get_existing_resource_subdirs() -> set[str]:
    """@brief Enumerate actual resource subdirectories under src/usereq/resources/.
    @details Scans the filesystem for immediate child directories, excluding hidden directories (starting with dot).
    @return {set[str]} Set of subdirectory names present under resources/.
    """

    return {
        entry.name
        for entry in RESOURCES_DIR.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    }


def test_package_data_covers_required_operational_resource_subdirectories() -> None:
    """@brief Assert package-data patterns reference required operational resource subdirectories.
    @details Extracts directory prefixes from package-data glob patterns and verifies coverage of the fixed
    operational subdirectory set required for runtime behavior and packaging.
    @return {None} No return value.
    @satisfies SRS-272, SRS-274
    """

    patterns = _get_package_data_patterns()
    covered_dirs: set[str] = set()
    for pattern in patterns:
        parts = pattern.split("/")
        if len(parts) >= 2 and parts[0] == "resources":
            covered_dirs.add(parts[1])

    missing = REQUIRED_OPERATIONAL_RESOURCE_SUBDIRS - covered_dirs
    assert not missing, (
        "Required operational resource subdirectories not covered by package-data: "
        f"{sorted(missing)}. Required: {sorted(REQUIRED_OPERATIONAL_RESOURCE_SUBDIRS)}, "
        f"Covered: {sorted(covered_dirs)}"
    )


def test_package_data_patterns_reference_existing_directories() -> None:
    """@brief Assert package-data patterns do not reference non-existent resource directories.
    @details Validates that every directory prefix extracted from package-data glob patterns corresponds
    to an actual directory under src/usereq/resources/. Prevents build warnings from stale patterns.
    @return {None} No return value.
    @satisfies SRS-273
    """

    patterns = _get_package_data_patterns()
    existing_dirs = _get_existing_resource_subdirs()
    referenced_dirs: set[str] = set()
    for pattern in patterns:
        parts = pattern.split("/")
        if len(parts) >= 3 and parts[0] == "resources":
            # resources/<dir>/<glob>: the second segment is a directory prefix.
            referenced_dirs.add(parts[1])
        elif (
            len(parts) == 2
            and parts[0] == "resources"
            and any(ch in parts[1] for ch in "*?[")
        ):
            # resources/<glob-at-root>: the segment itself is a glob, not a directory.
            continue

    nonexistent = referenced_dirs - existing_dirs
    assert not nonexistent, (
        f"Package-data references non-existent resource directories: {sorted(nonexistent)}. "
        f"Existing: {sorted(existing_dirs)}"
    )


def test_package_data_matches_actual_resource_files() -> None:
    """@brief Assert every non-hidden file under resources/ is matched by at least one package-data pattern.
    @details Iterates all regular files under src/usereq/resources/ (excluding hidden files) and verifies
    each file's relative path matches at least one declared pattern in package-data. Ensures no operational
    resource file is silently excluded from the distribution.
    @return {None} No return value.
    @satisfies SRS-274
    """

    patterns = _get_package_data_patterns()
    all_resource_files: list[Path] = []
    for child in RESOURCES_DIR.rglob("*"):
        if child.is_file() and not any(
            p.startswith(".") for p in child.relative_to(RESOURCES_DIR).parts
        ):
            all_resource_files.append(child)

    assert all_resource_files, "No resource files found under src/usereq/resources/"

    unmatched: list[str] = []
    for resource_file in all_resource_files:
        rel_path = str(resource_file.relative_to(RESOURCES_DIR.parent))
        matched = any(fnmatch.fnmatch(rel_path, pat) for pat in patterns)
        if not matched:
            unmatched.append(rel_path)

    assert not unmatched, (
        f"Resource files not matched by any package-data pattern: {sorted(unmatched)}"
    )


def test_pyproject_project_name_matches_pypi_trusted_publisher() -> None:
    """@brief Verify pyproject.toml declares the PyPI trusted-publisher distribution name.
    @details The OIDC trusted publisher for repository Ogekuri/CLI-useReq and workflow
    release-pypi.yml is registered for PyPI project cli-usereq; the built distribution
    name must match it for authenticated uploads.
    @return {None} No return value.
    @satisfies SRS-435, SRS-439
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project_name = pyproject_data["project"]["name"]
    assert project_name == "cli-usereq", (
        f"pyproject.toml [project].name must be cli-usereq to match the registered "
        f"PyPI trusted publisher, found: {project_name!r}"
    )


def test_pyproject_declares_ogekuri_author_and_repository_urls() -> None:
    """@brief Verify pyproject.toml author and project URLs reference the real repository.
    @details Author metadata must declare Ogekuri and Homepage/Repository URLs must
    point to https://github.com/Ogekuri/CLI-useReq for compliant PyPI metadata.
    @return {None} No return value.
    @satisfies SRS-436, SRS-437, SRS-439
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    authors = pyproject_data["project"]["authors"]
    author_names = {author.get("name") for author in authors}
    assert "Ogekuri" in author_names, (
        f"pyproject.toml [project].authors must declare Ogekuri, found: {sorted(author_names)}"
    )

    project_urls = pyproject_data["project"]["urls"]
    expected_url = "https://github.com/Ogekuri/CLI-useReq"
    assert project_urls.get("Homepage") == expected_url, (
        f"[project.urls] Homepage must be {expected_url}, found: {project_urls.get('Homepage')!r}"
    )
    assert project_urls.get("Repository") == expected_url, (
        f"[project.urls] Repository must be {expected_url}, found: {project_urls.get('Repository')!r}"
    )


def test_pyproject_does_not_define_unsupported_uv_forms_section() -> None:
    """@brief Ensure pyproject.toml does not declare unsupported uv settings keys.
    @details Guards req.sh uv-managed execution from settings-discovery warnings by
    forbidding the deprecated `[tool.uv.forms.*]` subtree in pyproject metadata.
    @return {None} No return value.
    @satisfies SRS-056
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    uv_settings = pyproject_data.get("tool", {}).get("uv", {})
    assert "forms" not in uv_settings, (
        "pyproject.toml MUST NOT define [tool.uv.forms.*] because current uv "
        "settings schema rejects `forms` and emits runtime warnings."
    )


def test_pyproject_license_uses_spdx_expression_with_license_file() -> None:
    """@brief Verify pyproject.toml declares the license as SPDX expression plus license file.
    @details Enforces PEP 639 metadata so built distributions carry `License-Expression` and
    `License-File` headers instead of embedding the full license text in the `License` field.
    @return {None} No return value.
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project = pyproject_data["project"]
    assert project.get("license") == "GPL-3.0-only", (
        f"pyproject.toml [project].license must be the SPDX string GPL-3.0-only, found: {project.get('license')!r}"
    )
    assert project.get("license-files") == ["LICENSE"], (
        f"pyproject.toml [project].license-files must be ['LICENSE'], found: {project.get('license-files')!r}"
    )
    assert (REPO_ROOT / "LICENSE").is_file(), "LICENSE file must exist at repository root"


def test_pyproject_pytest_is_declared_only_as_development_dependency() -> None:
    """@brief Verify pytest is a development-only dependency while ruff and pyright stay at runtime.
    @details Runtime `[project].dependencies` MUST keep ruff and pyright and MUST NOT declare the
    test-only pytest package. The `dev` dependency group MUST declare pytest so `uv sync` and
    `uv run pytest` keep the unit-test suite runnable.
    @return {None} No return value.
    @satisfies SRS-264, SRS-338
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    runtime_packages = {
        _normalize_requirement_name(entry)
        for entry in pyproject_data["project"]["dependencies"]
    }
    dev_entries = pyproject_data.get("dependency-groups", {}).get("dev", [])
    dev_packages = {
        _normalize_requirement_name(entry)
        for entry in dev_entries
        if isinstance(entry, str)
    }
    assert "pytest" not in runtime_packages, (
        "pytest must not be a runtime dependency in [project].dependencies"
    )
    assert {"ruff", "pyright"} <= runtime_packages, (
        f"ruff and pyright must remain runtime dependencies, found: {sorted(runtime_packages)}"
    )
    assert "pytest" in dev_packages, (
        f"[dependency-groups].dev must declare pytest, found: {sorted(dev_packages)}"
    )


def test_pyproject_build_system_requires_pep639_capable_setuptools() -> None:
    """@brief Verify the build backend floor supports PEP 639 license fields.
    @details Setuptools releases before 77.0.0 reject the SPDX `license` string and the
    `license-files` key. The build-system requirement MUST pin a `setuptools>=77` floor.
    @return {None} No return value.
    """

    pyproject_data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    requires = pyproject_data["build-system"]["requires"]
    floors = [
        int(match.group(1))
        for match in (re.match(r"^setuptools\s*>=\s*([0-9]+)", entry) for entry in requires)
        if match is not None
    ]
    assert floors and max(floors) >= 77, (
        f"[build-system].requires must pin setuptools>=77, found: {requires!r}"
    )


def test_manifest_prunes_generated_egg_info_from_sdist() -> None:
    """@brief Verify MANIFEST.in excludes the generated setuptools egg-info from sdists.
    @details The `src/*.egg-info` directory is a generated build intermediate written by
    setuptools during sdist creation. MANIFEST.in MUST carry the exact `prune src/*.egg-info`
    directive so the sdist ships no generated metadata.
    @return {None} No return value.
    """

    manifest_path = REPO_ROOT / "MANIFEST.in"
    assert manifest_path.is_file(), "MANIFEST.in must exist at repository root"
    manifest_lines = [
        line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines()
    ]
    assert "prune src/*.egg-info" in manifest_lines, (
        f"MANIFEST.in must prune src/*.egg-info, found lines: {manifest_lines!r}"
    )
    gitignore_lines = [
        line.strip() for line in GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
    ]
    assert "!MANIFEST.in" in gitignore_lines, (
        ".gitignore must re-include MANIFEST.in so the tracked manifest is versionable"
    )


def _gitignore_lines() -> list[str]:
    """@brief Read every .gitignore line stripped of surrounding whitespace in file order.
    @details Single read of GITIGNORE_PATH; O(n) over lines; no side effects beyond the read.
    @return {list[str]} Stripped lines including comments and blank entries.
    """
    return [line.strip() for line in GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()]


def test_gitignore_default_exclusion_precedes_reinclusion_rules() -> None:
    """@brief Verify the default `/*` exclusion precedes every `!` re-inclusion rule.
    @details Validates the SRS-552 inverse exclusion strategy; gitignore uses the last matching
    pattern, so the default exclusion MUST appear before the first negated rule.
    @return {None} No return value.
    @satisfies SRS-552
    """
    rules = [line for line in _gitignore_lines() if line and not line.startswith("#")]
    first_reinclusion = next(index for index, rule in enumerate(rules) if rule.startswith("!"))
    assert "/*" in rules[:first_reinclusion], (
        ".gitignore must exclude everything by default before any !-re-inclusion rule"
    )


def test_gitignore_reincludes_dist_directory_and_contents() -> None:
    """@brief Verify `!dist/` and `!dist/**/*` reside in the Include section.
    @details Validates SRS-553 and SRS-557; the include section spans the lines between its
    header and the Exclude-section header.
    @return {None} No return value.
    @satisfies SRS-553, SRS-557
    """
    lines = _gitignore_lines()
    include_index = next(
        index for index, line in enumerate(lines)
        if "Include specific files and directories" in line
    )
    exclude_index = next(
        index for index, line in enumerate(lines)
        if "Exlucde specific files and directories" in line
    )
    include_section = lines[include_index:exclude_index]
    assert "!dist/" in include_section, ".gitignore include section must contain !dist/"
    assert "!dist/**/*" in include_section, (
        ".gitignore include section must contain !dist/**/*"
    )


def test_gitignore_contains_no_dist_exclusion_rule() -> None:
    """@brief Verify no non-negated .gitignore rule targets dist/ or its entries.
    @details Validates SRS-555; a non-negated pattern is offending when its leading `/` removed
    form starts with `dist`. O(n) over rule lines.
    @return {None} No return value.
    @satisfies SRS-555
    """
    offending = [
        line for line in _gitignore_lines()
        if line and not line.startswith(("#", "!")) and line.lstrip("/").startswith("dist")
    ]
    assert offending == [], f".gitignore must not exclude dist/, found rules: {offending!r}"


def test_gitignore_leaves_dist_artifacts_unignored_by_git() -> None:
    """@brief Verify git classifies sample dist/ artifacts as not ignored.
    @details Runs `git check-ignore --no-index` on sample sdist, wheel, and nested paths beneath
    dist/ inside REPO_ROOT; exit status 1 means not ignored, 0 means ignored. Skips when the
    repository root carries no .git entry (for example, an unpacked source distribution).
    @return {None} No return value.
    @throws {AssertionError} Raised when any sample artifact path is ignored.
    @satisfies SRS-554, SRS-555, SRS-557
    """
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("repository root carries no .git entry")
    sample_paths = [
        "dist/package-1.0.tar.gz",
        "dist/package-1.0-py3-none-any.whl",
        "dist/nested/tracked.whl",
    ]
    for sample_path in sample_paths:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", "--no-index", "-q", "--", sample_path],
            capture_output=True, check=False,
        )
        assert result.returncode == 1, f"git must not ignore {sample_path}"
