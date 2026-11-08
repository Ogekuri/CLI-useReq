# Files Structure
```
.
└── src
    └── usereq
        ├── __init__.py
        ├── __main__.py
        ├── cli.py
        ├── compress_files.py
        ├── compress.py
        ├── doxygen_parser.py
        ├── find_constructs.py
        ├── generate_markdown.py
        ├── source_analyzer.py
        ├── static_check.py
        └── token_counter.py
```

# __init__.py | Python | 62L | 2 symbols | 10 imports | 5 comments
> Path: `src/usereq/__init__.py`
- @brief Initialization module for the `usereq` package.
- @details Exposes package metadata and lazily-resolved CLI entrypoints while avoiding eager
import of `usereq.cli` during package initialization.
@author GitHub Copilot
@version 0.0.70

## Imports
```
from __future__ import annotations
import importlib
from . import compress  # usereq.compress submodule
from . import compress_files  # usereq.compress_files submodule
from . import find_constructs  # usereq.find_constructs submodule
from . import generate_markdown  # usereq.generate_markdown submodule
from . import source_analyzer  # usereq.source_analyzer submodule
from . import token_counter  # usereq.token_counter submodule
from typing import Any
from .cli import main as cli_main
```

## Definitions

### fn `def main(argv: list[str] | None = None) -> int` (L25-40)
- @brief Semantic version string of the package."""
- @brief Execute the package CLI entrypoint without eager module import side effects.
- @details Lazily imports `usereq.cli.main` on call to avoid pre-loading `usereq.cli` during package initialization, preventing runpy module-execution RuntimeWarning for `python -m usereq.cli`.
- @param argv {list[str] | None} Optional CLI arguments list forwarded to `usereq.cli.main`.
- @return {int} CLI process exit code produced by `usereq.cli.main`.
- @satisfies SRS-056

### fn `def __getattr__(name: str) -> Any` `priv` (L41-56)
- @brief Lazily resolve deferred public package attributes.
- @details Resolves `cli` on first access to preserve backward-compatible attribute access (`usereq.cli`) while keeping package initialization free from eager CLI import.
- @param name {str} Requested attribute name.
- @return {Any} Resolved attribute object.
- @throws {AttributeError} Raised when the attribute is not a supported deferred symbol.
- @satisfies SRS-056

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`main`|fn|pub|25-40|def main(argv: list[str] | None = None) -> int|
|`__getattr__`|fn|priv|41-56|def __getattr__(name: str) -> Any|


---

# __main__.py | Python | 17L | 0 symbols | 2 imports | 2 comments
> Path: `src/usereq/__main__.py`
- @brief Package entry point for execution as a module.
- @details Enables running the package via `python -m usereq`. Delegates execution to the CLI main function.
@author GitHub Copilot
@version 0.0.70

## Imports
```
from .cli import main
import sys
```


---

# cli.py | Python | 4284L | 167 symbols | 33 imports | 213 comments
> Path: `src/usereq/cli.py`
- @brief CLI entry point implementing the useReq initialization flow.
- @details Handles argument parsing, configuration management, and execution of useReq commands.
@author GitHub Copilot
@version 0.0.70

## Imports
```
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import os
import platform
import re
import shutil
import sys
import subprocess
import textwrap
import time
import urllib.error
import urllib.request
import copy
import yaml
from argparse import Namespace
from pathlib import Path
from typing import Any, Mapping, Optional
from .static_check import parse_enable_static_check as _parse_sc
from .static_check import (
from .token_counter import count_files_metrics, format_pack_summary
from .generate_markdown import generate_markdown
from .compress_files import compress_files
from .find_constructs import find_constructs_in_files
from .generate_markdown import generate_markdown
from .compress_files import compress_files
from .find_constructs import find_constructs_in_files
from .static_check import STATIC_CHECK_EXT_TO_LANG, dispatch_static_check_for_file
from .static_check import STATIC_CHECK_EXT_TO_LANG, dispatch_static_check_for_file
from .static_check import run_static_check
import traceback
```

## Definitions

- var `REPO_ROOT = Path(__file__).resolve().parents[2]` (L31)
- var `RESOURCE_ROOT = Path(__file__).resolve().parent / "resources"` (L34)
- @brief The absolute path to the repository root."""
- var `VERBOSE = False` (L37)
- @brief The absolute path to the resources directory."""
- var `DEBUG = False` (L40)
- @brief Whether verbose output is enabled."""
- var `REQUIREMENTS_TEMPLATE_NAME = "Requirements_Template.md"` (L43)
- @brief Whether debug output is enabled."""
- var `PERSISTED_CONFIG_KEYS = (` (L46)
- @brief Name of the packaged requirements template file."""
- var `AUTO_INSTALL_CONFIG_KEY = "auto-install"` (L56)
- @brief Canonical keys persisted in the user-global configuration file (SRS-288)."""
- var `DEFAULT_AUTO_INSTALL = True` (L59)
- @brief Configuration key storing the auto-install enabled flag (SRS-420)."""
- var `DEFAULT_DOCS_DIR = "usereq"` (L62)
- @brief Default auto-install state when the configuration stores no entry (SRS-420)."""
- var `DEFAULT_TESTS_DIR = "tests"` (L65)
- @brief Default docs-dir value stored when the configuration has no docs-dir (SRS-359)."""
- var `DEFAULT_SRC_DIRS = ("src",)` (L68)
- @brief Default tests-dir value stored when the configuration has no tests-dir (SRS-361)."""
- var `GUIDELINES_DIR_RELATIVE_TO_HOME = (` (L105)
- @brief Default static-check configuration applied when the configuration stores no
`"static-check"` entry; a present entry, including an empty object, suppresses these
defaults (SRS-424, SRS-425, SRS-426). The `pyright` and `ruff` checkers from the external
configuration trace map to the native `Pylance` and `Ruff` modules (SRS-338, SRS-339)."""
- var `VALID_PROVIDERS = frozenset(` (L117)
- @brief Home-relative, non-configurable installation path of GUIDELINES_DIR (SRS-360)."""
- var `GLOBAL_CONFIG_DIRNAME = ".config"` (L122)
- @brief Valid provider names accepted by ``--enable PROVIDER`` and ``--disable PROVIDER`` (SRS-275, SRS-364)."""
- var `GLOBAL_CONFIG_APP_DIRNAME = "usereq"` (L125)
- @brief Root configuration directory name located under the user HOME (SRS-387)."""
- var `GLOBAL_CONFIG_FILENAME = "config.json"` (L128)
- @brief Application subdirectory name under ``~/.config`` (SRS-387)."""
### fn `def home_dir() -> Path` (L132-142)
- @brief Canonical user-global configuration JSON filename (SRS-387)."""
- @brief Resolve the user HOME directory used for user-level CLI configuration.
- @details Single indirection point over ``Path.home()`` so tests and embedders can redirect all user-level provider and configuration paths deterministically.
- @return {Path} Absolute user HOME directory path.
- @satisfies SRS-381

### fn `def get_global_config_path() -> Path` (L143-158)
- @brief Resolve the single user-global configuration file path.
- @details Builds ``~/.config/usereq/config.json`` from the effective home directory returned by :func:`home_dir`.
- @return {Path} Absolute path of the user-global configuration file.
- @satisfies SRS-387

### fn `def guidelines_dir() -> Path` (L159-169)
- @brief Resolve the fixed installation-owned guidelines directory.
- @details Composes the effective user HOME returned by :func:`home_dir` with the non-configurable :data:`GUIDELINES_DIR_RELATIVE_TO_HOME` suffix.
- @return {Path} Absolute path of the installed guidelines directory.
- @satisfies SRS-360

### fn `def format_home_relative_path(path: Path) -> str` (L170-189)
- @brief Render an absolute path in ``~/`` home-relative form.
- @details Returns ``~`` for the HOME directory, ``~/<rel>`` with POSIX separators for any path under HOME, and the absolute string for paths outside HOME.
- @param path {Path} Absolute path to render.
- @return {str} Home-relative rendering when the path is under HOME, otherwise absolute.
- @satisfies SRS-402, SRS-403

### fn `def provider_skills_root(provider: str) -> Path` (L190-221)
- @brief Resolve the user-level skills installation root for one provider.
- @details Maps ``provider`` to its hardcoded user-level skills directory under the user HOME (antigravity -> ``~/.gemini/config/skills``, claude -> ``~/.claude/skills``, codex -> ``~/.agents/skills``, openclaw -> ``~/.openclaw/workspace/skills``, opencode -> ``~/.config/opencode/skills``, pi -> ``~/.pi/agent/skills``). Paths are computed lazily from :func:`home_dir` so HOME redirection stays consistent across a single process run. Skills are the only supported artifact type (SRS-381).
- @param provider {str} Provider selector from ``{antigravity, claude, codex, openclaw, opencode, pi}``.
- @return {Path} Absolute user-level skills target directory for the provider.
- @throws {ReqError} Raised when the provider defines no user-level skills root.
- @satisfies SRS-381, SRS-382, SRS-383, SRS-384, SRS-385, SRS-386, SRS-486

### fn `def provider_skills_path(provider: str) -> str` (L222-235)
- @brief Render the home-relative hardcoded skills root shown in the `show` Providers table.
- @details Joins the effective user HOME with the hardcoded provider skills root from :func:`provider_skills_root` (SRS-382..SRS-386, SRS-486) and renders the result through :func:`format_home_relative_path` as a `~/`-prefixed POSIX path. Complexity: O(1). No side effects.
- @param provider {str} Provider selector from ``{antigravity, claude, codex, openclaw, opencode, pi}``.
- @return {str} Home-relative skills installation root such as ``~/.pi/agent/skills``.
- @satisfies SRS-462, SRS-463, SRS-485

- var `INVALID_WT_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]')` (L236)
### fn `def validate_provider_name(name: str) -> str` (L240-262)
- @brief Regex matching characters invalid in both Linux and Windows directory names."""
- @brief Validate one provider name token supplied via ``--enable`` or ``--disable``.
- @details Normalizes the token to lowercase and validates membership in :data:`VALID_PROVIDERS`; unknown tokens raise a deterministic English `ReqError` payload identifying the invalid token (SRS-278, SRS-422). Complexity: O(1). No side effects.
- @param name {str} Raw provider name token as supplied on the command line or read from the persisted `"providers"` array.
- @return {str} Normalized lowercase provider name.
- @throws {ReqError} Raised with exit code 1 when the token is not a valid provider.
- @satisfies SRS-275, SRS-278, SRS-364, SRS-422

### fn `def resolve_provider_configs(` (L263-264)

- var `ANSI_BRIGHT_RED = "\033[91m"` (L287)
- @brief Resolve per-provider enablement from ``--enable PROVIDER`` names only.
- @details Initializes every provider as disabled, validates each supplied name
through :func:`validate_provider_name`, and marks validated providers as enabled;
enabling a provider implicitly enables its skills, the only supported artifact
(SRS-035, SRS-464). Complexity: O(N) in provider-name token count. No external
side effects.
- @param provider_names {list[str]} Raw provider name strings from ``--enable`` or the
persisted `"providers"` array.
- @return {dict[str, bool]} Mapping provider -> enabled flag covering every valid provider.
- @throws {ReqError} Raised when a provider name is unknown (SRS-278).
- @see validate_provider_name
- @satisfies SRS-275, SRS-279, SRS-364
- var `ANSI_BRIGHT_GREEN = "\033[92m"` (L290)
- @brief ANSI escape prefix for bright red terminal output."""
- var `ANSI_RESET = "\033[0m"` (L293)
- @brief ANSI escape prefix for bright green terminal output."""
- var `RELEASE_CHECK_TIMEOUT_SECONDS = 2.0` (L296)
- @brief ANSI escape sequence that resets terminal style."""
- var `RELEASE_CHECK_IDLE_DELAY_SECONDS = 3600` (L299)
- @brief Hardcoded default timeout for startup release-check HTTP calls."""
- var `RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS = 86400` (L302)
- @brief Hardcoded startup release-check idle-delay in seconds."""
- var `TOOL_PROGRAM_NAME = "cli-usereq"` (L305)
- @brief Hardcoded startup release-check idle-delay in seconds for API rate limiting."""
- var `RELEASE_CHECK_PROGRAM_NAME = "usereq"` (L311)
- @brief Hardcoded uv tool requirement name matching the PyPI distribution name of this package (SRS-435).
- @details Used as the target of `uv tool install`/`uv tool uninstall` commands; it matches the
`[project].name` distribution name registered in the PyPI trusted publisher for repository
`Ogekuri/CLI-useReq` (SRS-343, SRS-344, SRS-433, SRS-435)."""
- var `GITHUB_REPOSITORY_OWNER = "Ogekuri"` (L316)
- @brief Program identifier used in release-check idle-state cache directory.
- @details Fixes the idle-state cache path to `~/.cache/usereq/check_version_idle-time.json`
independently of the PyPI distribution name `cli-usereq` (SRS-345, SRS-346)."""
- var `GITHUB_REPOSITORY_NAME = "CLI-useReq"` (L319)
- @brief Hardcoded GitHub owner used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME = ".cache"` (L322)
- @brief Hardcoded GitHub repository used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_FILENAME = "check_version_idle-time.json"` (L325)
- @brief Root cache directory name located under `$HOME`."""
- var `GITHUB_RELEASES_LATEST_URL = (` (L328)
- @brief Canonical release-check idle-state JSON filename."""
- var `GITHUB_UPGRADE_SOURCE = (` (L337)
- @brief Hardcoded GitHub API endpoint queried by `--ver`/`--version` and `--upgrade --develop` (SRS-442, SRS-451).
- @details Intermediate and test releases are published on GitHub; this endpoint resolves the
latest tagged release independently of the branch holding the tag. The default `--upgrade`
path never queries it and installs from the PyPI index (SRS-343, SRS-440)."""
- var `PYPI_PROJECT_JSON_URL = "https://pypi.org/pypi/cli-usereq/json"` (L344)
- @brief Hardcoded git source base used only by `--upgrade --develop` (alias `--dev`) installs (SRS-440, SRS-445).
- @details The uv `--from` reference appends `@<TAG>` with the raw SRS-451 release tag so the
install pins the latest tagged release regardless of the branch holding the tag (SRS-452)."""
- var `UNKNOWN_VERSION_LABEL = "unknown"` (L350)
- @brief Hardcoded PyPI JSON API endpoint for latest-version resolution (SRS-430).
- @details The startup release-check and `--ver`/`--version` read `info.version` from this
endpoint; PyPI is the sole source for version verification and default self-upgrade
(SRS-343, SRS-441, SRS-442)."""
- var `FORCE_ONLINE_RELEASE_CHECK = False` (L353)
- @brief Label printed by `--ver`/`--version` when a remote latest version cannot be fetched (SRS-442)."""
### class `class ReqError(Exception)` : Exception (L357-374)
- @brief Startup-scoped override that bypasses release-check idle-state gating when enabled."""
- @brief Dedicated exception for expected CLI errors.
- @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
- fn `def __init__(self, message: str, code: int = 1) -> None` `priv` (L362-374)
  - @brief Dedicated exception for expected CLI errors.
  - @brief Initialize an expected CLI failure payload.
  - @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
  - @details Implements the __init__ function behavior with deterministic control flow.
  - @param message Human-readable error message.
  - @param code Process exit code bound to the failure category.
  - @return {None} Function return value.

### fn `def log(msg: str) -> None` (L375-384)
- @brief Prints an informational message.
- @details Implements the log function behavior with deterministic control flow.
- @param msg The message string to print.
- @return {None} Function return value.

### fn `def dlog(msg: str) -> None` (L385-395)
- @brief Prints a debug message if debugging is active.
- @details Implements the dlog function behavior with deterministic control flow.
- @param msg The debug message string to print.
- @return {None} Function return value.

### fn `def vlog(msg: str) -> None` (L396-406)
- @brief Prints a verbose message if verbose mode is active.
- @details Implements the vlog function behavior with deterministic control flow.
- @param msg The verbose message string to print.
- @return {None} Function return value.

### fn `def build_parser() -> argparse.ArgumentParser` (L407-606)
- @brief Builds the CLI argument parser.
- @details Defines all supported CLI arguments, flags, and help texts. Provider enablement is configured exclusively via the repeatable ``--enable PROVIDER`` argument, which accepts only the provider CLI name exactly like ``--disable PROVIDER`` (SRS-275, SRS-034); skills are the only supported artifact type. Every SRS-408 analysis subcommand accepts the global base arguments ``--prj-base`` and ``--git-base`` both before and after the subcommand token; ``--prj-base`` is mandatory only for the SRS-396 project-scan subcommands (enforced by ``_require_prj_base``) and ``--git-base`` is never mandatory for any SRS-408 subcommand (SRS-392, SRS-393, SRS-396, SRS-397, SRS-410).
- @return Configured ArgumentParser instance.

### fn `def parse_args(argv: Optional[list[str]] = None) -> Namespace` (L825-834)
- @brief Parses command-line arguments into a namespace.
- @details Implements the parse_args function behavior with deterministic control flow.
- @param argv List of arguments (defaults to sys.argv).
- @return Namespace containing parsed arguments.

### fn `def load_package_version() -> str` (L835-849)
- @brief Reads the package version from __init__.py.
- @details Implements the load_package_version function behavior with deterministic control flow.
- @return Version string extracted from the package.
- @throws ReqError If version cannot be determined.

### fn `def maybe_print_version(argv: list[str], pypi_latest: Optional[str] = None) -> bool` (L850-895)
- @brief Handles --ver/--version by printing installed, PyPI latest, and GitHub latest versions.
- @details When `--ver`/`--version` is present, prints the installed package version as the first stdout line, then queries (or reuses) the PyPI JSON API `info.version` and the GitHub latest-release `tag_name`, printing `PyPI latest: <version>` and `GitHub latest: <version>` lines; fetch failures degrade to the `unknown` label without raising (SRS-441, SRS-442).
- @param argv Command line arguments to check.
- @param pypi_latest {Optional[str]} PyPI latest version already fetched by the startup release-check; when None, a direct PyPI JSON API fetch is attempted (SRS-441, SRS-442).
- @return {bool} True if version output was printed, False otherwise.
- @satisfies SRS-441, SRS-442

### fn `def _resolve_github_upgrade_tag() -> str` `priv` (L896-926)
- @brief Resolve the raw latest GitHub release tag for `--upgrade --develop` installations.
- @details Queries `GITHUB_RELEASES_LATEST_URL` through `fetch_github_latest_version(raw_tag=True)` and returns the raw `tag_name` value with the optional `v` prefix preserved so the uv `--from` reference targets an existing git tag regardless of the branch holding it (SRS-451). Maps fetch exceptions and empty payloads to one English `ReqError` so no uv process is spawned (SRS-453). Complexity: O(1). Side effects: one HTTP request.
- @return {str} Raw latest release tag, e.g. `v0.0.76`.
- @throws {ReqError} Raised with exit code 1 when the GitHub query fails or returns no tag (SRS-453).
- @satisfies SRS-451, SRS-453

### fn `def run_upgrade(use_github: bool = False) -> None` (L927-974)
- @brief Executes the upgrade using uv from the PyPI index or the latest GitHub release tag.
- @details Builds `uv tool install cli-usereq --force` against the PyPI index by default (SRS-343). When `use_github` is True, resolves the latest GitHub release tag through `_resolve_github_upgrade_tag()` (SRS-451) and appends `--from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` regardless of the branch holding that tag (SRS-440, SRS-452). Executes the command only on Linux; on non-Linux platforms prints the manual command and skips uv execution.
- @param use_github {bool} When True, install the latest tagged GitHub release instead of the PyPI index (`--upgrade --develop` or equivalent alias `--dev`, SRS-440, SRS-445).
- @return {None} Function return value.
- @throws {ReqError} When the SRS-451 GitHub tag resolution fails (exit code 1, SRS-453) or when the uv process fails.
- @note Tag resolution precedes the platform gate so the non-Linux manual command embeds the resolved tag (SRS-452).
- @note The `--develop`/`--dev` argv alias mapping to `use_github=True` is resolved by `main(...)` before calling this function.
- @satisfies SRS-343, SRS-440, SRS-445, SRS-451, SRS-452, SRS-453

### fn `def run_uninstall() -> None` (L975-1007)
- @brief Executes the uninstallation using uv.
- @details Implements the run_uninstall function behavior with deterministic control flow.
- @return {None} Function return value.
- @throws ReqError If uninstall fails.
- @satisfies SRS-344, SRS-346

### fn `def normalize_release_tag(tag: str) -> str` (L1008-1020)
- @brief Normalizes the release tag by removing a 'v' prefix if present.
- @details Implements the normalize_release_tag function behavior with deterministic control flow.
- @param tag The raw tag string.
- @return The normalized version string.

### fn `def parse_version_tuple(version: str) -> tuple[int, ...] | None` (L1021-1045)
- @brief Converts a version into a numeric tuple for comparison.
- @details Accepts versions in 'X.Y.Z' format (ignoring any non-numeric suffixes).
- @param version The version string to parse.
- @return Tuple of integers or None if parsing fails.

### fn `def is_newer_version(current: str, latest: str) -> bool` (L1046-1064)
- @brief Returns True if latest is greater than current.
- @details Implements the is_newer_version function behavior with deterministic control flow.
- @param current The current installed version string.
- @param latest The latest available version string.
- @return True if update is available, False otherwise.

### fn `def parse_github_owner_repository(remote_url: str) -> tuple[str, str] | None` (L1065-1091)
- @brief Extract GitHub owner/repository from a git remote URL.
- @details Supports SSH (`git@github.com:owner/repo.git`), HTTPS (`https://github.com/owner/repo.git`), and SSH-scheme (`ssh://git@github.com/owner/repo.git`) forms. Removes optional `.git` suffix.
- @param remote_url Remote URL string from `git remote -v`.
- @return Tuple `(owner, repository)` when URL targets github.com; otherwise None.

### fn `def read_git_remote_verbose(cwd: str | None = None) -> str` (L1092-1111)
- @brief Read git remote definitions using `git remote -v`.
- @details Executes `git remote -v` with deterministic stderr capture and text decoding. When `cwd` is omitted, the current process working directory is used.
- @param cwd Optional working directory override for git execution context.
- @return Raw stdout output generated by `git remote -v`.
- @throws subprocess.CalledProcessError If git returns a non-zero status.

### fn `def resolve_github_owner_repository_from_active_remotes() -> tuple[str, str]` (L1112-1172)
- @brief Resolve GitHub owner/repository from active repository remotes.
- @details Reads `git remote -v`, prioritizes `origin` fetch URL, then other fetch remotes, then non-fetch entries, and returns the first parseable github.com owner/repository pair. If the first inspection fails outside the repository root context, retries once from `REPO_ROOT`.
- @return Tuple `(owner, repository)` resolved from active remotes.
- @throws ValueError If no github.com remote URL can be parsed from `git remote -v`.
- @throws ReqError If git remote inspection cannot execute successfully.

### fn `def resolve_pypi_latest_version_url() -> str` (L1173-1182)
- @brief Resolve the PyPI JSON API URL for latest-version resolution.
- @details Returns the static endpoint derived from the PyPI project `cli-usereq`.
- @return {str} Fully-qualified URL `https://pypi.org/pypi/cli-usereq/json`.
- @satisfies SRS-430

### fn `def fetch_pypi_latest_version(` (L1183-1184)

### fn `def fetch_github_latest_version(` (L1220-1223)
- @brief Fetch the latest published version of `cli-usereq` from the PyPI JSON API.
- @details Issues `GET https://pypi.org/pypi/cli-usereq/json` with JSON `Accept` headers,
parses `info.version`, and normalizes the value through `normalize_release_tag`.
Complexity: O(1). Side effects: one HTTP request.
- @param timeout_seconds {float} Timeout for the HTTP GET request.
- @return {Optional[str]} Normalized latest version string; None when `info.version` is
absent or not a non-empty string.
- @throws {urllib.error.HTTPError} When the endpoint answers with an HTTP error status.
- @throws {urllib.error.URLError} On network-level failures.
- @throws {TimeoutError} When the request exceeds `timeout_seconds`.
- @throws {json.JSONDecodeError} When the response body is not valid JSON.
- @satisfies SRS-430, SRS-442

### fn `def format_unix_timestamp_utc(timestamp_seconds: int) -> str` (L1262-1274)
- @brief Fetch the latest GitHub release version from the GitHub latest-release API.
- @brief Convert a Unix timestamp into a UTC human-readable string.
- @details Issues `GET https://api.github.com/repos/Ogekuri/CLI-useReq/releases/latest` with
GitHub JSON `Accept` headers and parses `tag_name`. The endpoint answers with the latest
tagged release independently of the branch holding the tag. Normalized output feeds the
`--ver`/`--version` display (SRS-441, SRS-442); raw output feeds the `--upgrade --develop`
tag resolution (SRS-451). The startup release-check never calls this function (SRS-430).
Complexity: O(1). Side effects: one HTTP request.
- @details Implements deterministic UTC conversion for release-check idle-state persistence.
- @param timeout_seconds {float} Timeout for the HTTP GET request.
- @param raw_tag {bool} When True, return the raw `tag_name` value with its optional
`v` prefix preserved; when False, normalize through `normalize_release_tag`.
- @param timestamp_seconds Unix timestamp in seconds.
- @return {Optional[str]} Latest GitHub release tag: raw whitespace-stripped `tag_name` when
`raw_tag` is True, `v`-prefix-stripped otherwise; None when `tag_name` is absent or not a
non-empty string.
- @return UTC datetime string in ISO-like `YYYY-MM-DDTHH:MM:SSZ` format.
- @throws {urllib.error.HTTPError} When the endpoint answers with an HTTP error status.
- @throws {urllib.error.URLError} On network-level failures.
- @throws {TimeoutError} When the request exceeds `timeout_seconds`.
- @throws {json.JSONDecodeError} When the response body is not valid JSON.
- @satisfies SRS-442, SRS-451

### fn `def get_release_check_idle_file_path(` (L1275-1276)

### fn `def cleanup_release_check_idle_state_cache(` (L1293-1294)
- @brief Resolve idle-state file path for startup release-check throttling.
- @details Builds the path using the effective home directory returned by `Path.home()`.
- @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
- @return Absolute path `$HOME/.cache/<program_name>/check_version_idle-time.json`.
- @satisfies SRS-345

### fn `def read_release_check_idle_state(file_path: Path) -> dict[str, int | str] | None` (L1317-1381)
- @brief Delete release-check idle-state file and remove empty cache directory.
- @brief Read and validate release-check idle-state JSON.
- @details Deletes `$HOME/.cache/<program_name>/check_version_idle-time.json` when present; removes `$HOME/.cache/<program_name>` only when it exists and has no remaining entries.
- @details Validates required keys `last_success_timestamp`, `last_success_human_readable_timestamp`, `idle_until_timestamp`, and `idle_until_human_readable_timestamp`; timestamps are normalized to integers.
- @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
- @param file_path Absolute idle-state JSON path under `$HOME`.
- @return Normalized idle-state dictionary or None when file does not exist.
- @throws OSError If filesystem operations fail.
- @throws OSError If file read fails.
- @throws json.JSONDecodeError If file content is not valid JSON.
- @throws ValueError If required keys are missing or value types are invalid.
- @satisfies SRS-346

### fn `def should_execute_release_check(` (L1382-1384)

### fn `def parse_retry_after_seconds(` (L1403-1405)
- @brief Decide whether startup release-check should execute in current invocation.
- @details Executes release-check when state is missing and skips only while the persisted `idle_until_timestamp` is greater than the current timestamp.
- @param idle_state Parsed idle-state payload or None when unavailable.
- @param now_timestamp Current Unix timestamp in seconds.
- @return True when release-check must execute; False when still in idle window.
- @satisfies SRS-348

### fn `def write_release_check_idle_state_payload(` (L1435-1438)
- @brief Parse an HTTP `Retry-After` header value into non-negative seconds.
- @details Supports integer-second values and HTTP-date values; HTTP-date values are converted to a delta from `now_timestamp`.
- @param retry_after_header Raw `Retry-After` header value.
- @param now_timestamp Current Unix timestamp in seconds.
- @return Retry delay in seconds when parsing succeeds; otherwise None.

### fn `def write_release_check_idle_state(` (L1465-1468)
- @brief Persist canonical release-check idle-state payload to disk.
- @details Serializes both numeric and UTC human-readable timestamps for the success instant and the idle-until instant.
- @param file_path Absolute idle-state JSON path.
- @param last_success_timestamp Unix timestamp of the last successful release-check.
- @param idle_until_timestamp Unix timestamp until startup release-check remains disabled.
- @throws OSError If file write fails.

### fn `def write_failed_release_check_idle_state(` (L1487-1491)
- @brief Persist release-check idle-state after a successful remote check.
- @details Computes `idle_until_timestamp = now_timestamp + idle_delay_seconds` and persists canonical idle-state keys.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Successful check timestamp in seconds.
- @param idle_delay_seconds Fixed idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-349

### fn `def persist_failed_release_check_idle_state(` (L1519-1523)
- @brief Persist idle-state after a startup release-check failure.
- @details Computes `idle_until_timestamp = now + idle_delay_seconds`, rewrites the canonical idle-state payload on every failure, and preserves the previous successful timestamp when available.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-350, SRS-351

### fn `def maybe_notify_newer_version(` (L1549-1550)
- @brief Persist failure idle-state and report write failures.
- @details Delegates failure idle-state persistence to `write_failed_release_check_idle_state(...)`; converts `OSError` into the standard bright-red stderr diagnostic without swallowing the original release-check failure.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @return {None} Function return value.
- @satisfies SRS-350, SRS-351

### fn `def ensure_doc_directory(` (L1679-1680)
- @brief Executes idle-gated online PyPI version check and prints bright colored status messages.
- @details Reads idle-state from `$HOME/.cache/usereq/check_version_idle-time.json`, skips remote requests when idle window is active unless startup context enables `FORCE_ONLINE_RELEASE_CHECK`, fetches the latest version from the PyPI JSON API (SRS-430) when due, compares versions, prints a bright-green update message only for newer versions, persists a 3600-second idle-delay after successful HTTP/JSON validation, prints bright-red diagnostics on every failure, rewrites idle-state JSON on every failure, uses an 86400-second idle-delay for `HTTPError`, `URLError`, and `TimeoutError`, and uses the default 3600-second idle-delay for other release-check failures.
- @param timeout_seconds Time to wait for the version check response.
- @return {Optional[str]} The fetched PyPI latest version on successful validation; None when the check is idle-gated or fails.
- @satisfies SRS-345, SRS-348, SRS-349, SRS-350, SRS-351, SRS-430

### fn `def ensure_test_directory(` (L1709-1710)
- @brief Resolve and validate docs directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate docs directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-359, SRS-363

### fn `def ensure_src_directory(` (L1739-1740)
- @brief Resolve and validate tests directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate tests directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-361, SRS-363

### fn `def make_relative_if_contains_project(path_value: str, project_base: Path) -> str` (L1769-1810)
- @brief Resolve and validate source directory path under project base.
- @brief Normalizes the path relative to the project root when possible.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @details Handles cases where the path includes the project directory name redundantly.
- @param path {str} Candidate source directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @param path_value The input path string.
- @param project_base The base path of the project.
- @return {None} Function return value.
- @return The normalized relative path string.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-362, SRS-363

### fn `def resolve_absolute(normalized: str, project_base: Path) -> Optional[Path]` (L1811-1826)
- @brief Resolves the absolute path starting from a normalized value.
- @details Implements the resolve_absolute function behavior with deterministic control flow.
- @param normalized The normalized relative path string.
- @param project_base The project root path.
- @return Absolute Path object or None if normalized is empty.

### fn `def resolve_git_root(target_path: Path) -> Path` (L1827-1854)
- @brief Resolve the git repository root for a given path.
- @param target_path Absolute path that must be inside a git repository.
- @return Absolute path to the git repository root.
- @throws ReqError If the path is not inside a git repository.
- @satisfies SRS-305, SRS-306

### fn `def sanitize_branch_name(branch: str) -> str` (L1855-1864)
- @brief Replace characters incompatible with Linux or Windows paths in a branch name.
- @param branch Raw git branch name.
- @return Sanitized string with incompatible characters replaced by `-`.
- @satisfies SRS-319

### fn `def validate_wt_name(wt_name: str) -> bool` (L1865-1876)
- @brief Validate that a worktree/branch name contains only valid directory characters.
- @param wt_name Candidate worktree name.
- @return True if valid, False if invalid characters are present.
- @satisfies SRS-321

### fn `def load_full_config() -> dict` (L1877-1897)
- @brief Load ALL parameters from the user-global configuration file as a raw dictionary.
- @return Full dictionary of all config key-value pairs.
- @throws ReqError If the global config file is missing or invalid JSON.
- @satisfies SRS-310, SRS-387

### fn `def save_config(` (L1898-1903)

### fn `def update_directory_config(` (L1933-1936)
- @brief Saves normalized directory parameters to the user-global configuration file.
- @details Writes the configuration payload to `~/.config/usereq/config.json`, creating
missing parent directories on first write, via read-modify-write so unspecified
canonical keys (including `"auto-install"`) are preserved. Only canonical keys from
`PERSISTED_CONFIG_KEYS` are written; `--prj-base` and `--git-base` are never written
(SRS-288, SRS-387, SRS-394, SRS-407, SRS-420).
- @param doc_dir_value Project-relative docs directory value.
- @param test_dir_value Project-relative tests directory value.
- @param src_dir_values Ordered project-relative source directory values.
- @param static_check_config Optional dict of static-check config to persist under key
`"static-check"`; preserved unchanged when None.
- @param providers Optional list of provider names to persist under the `"providers"`
key (SRS-279).
- @return {None} Function return value.
- @satisfies SRS-279, SRS-288, SRS-387, SRS-394, SRS-407, SRS-420

### fn `def load_config() -> dict[str, str | list[str]]` (L1974-2024)
- @brief Persist one or more directory configuration keys while preserving unrelated keys.
- @brief Loads directory parameters from the user-global configuration file.
- @details Loads the existing raw configuration payload when present, replaces only the
supplied directory keys, and rewrites `~/.config/usereq/config.json` with parent
directories created on demand. `--prj-base` and `--git-base` are never persisted
(SRS-394, SRS-398, SRS-399, SRS-400, SRS-401).
- @details Reads `~/.config/usereq/config.json`; when the file is absent every key falls back to its default (`usereq`, `tests`, `src`). Present but invalid values raise `ReqError`; `--prj-base` and `--git-base` are never read from the file (SRS-359, SRS-361, SRS-362, SRS-394, SRS-407).
- @param docs_dir_value Project-relative docs directory value, or None to keep current.
- @param tests_dir_value Project-relative tests directory value, or None to keep current.
- @param src_dir_values Ordered project-relative source directory values, or None to keep current.
- @return {None} Function return value.
- @return Dictionary containing `docs-dir`, `tests-dir`, and `src-dir` values.
- @throws ReqError If the existing configuration file contains invalid JSON.
- @throws ReqError If the global config file is invalid or holds invalid directory values.
- @satisfies SRS-394, SRS-398, SRS-399, SRS-400, SRS-401
- @satisfies SRS-359, SRS-361, SRS-362, SRS-394, SRS-407

### fn `def load_static_check_from_config() -> dict` (L2025-2063)
- @brief Load the `"static-check"` section from the user-global configuration file without validation errors.
- @details Reads `~/.config/usereq/config.json` silently. When the payload stores no `"static-check"` entry (including a missing or unreadable file), returns a deep copy of `DEFAULT_STATIC_CHECK` (SRS-424); a present entry, including an empty or invalid object, suppresses the defaults and is normalized like before: per-language entries that are not non-empty arrays of objects are dropped. Does NOT raise `ReqError`; caller decides whether absence is an error.
- @return Dict of static-check config (canonical-lang -> list[config-dict]).
- @see SRS-252, SRS-253, SRS-256, SRS-424, SRS-425, SRS-426
- @satisfies SRS-424, SRS-425, SRS-426

### fn `def _static_check_entry_identity(` `priv` (L2064-2065)

### fn `def load_persisted_providers() -> list[str]` (L2088-2110)
- @brief Build the canonical identity tuple for one static-check entry.
- @brief Load persisted provider names from the user-global configuration file.
- @details Identity is defined strictly by language, module, cmd, and params.
Unknown/additional keys in ``entry`` are ignored; ``params`` is normalized
to a tuple preserving order, and non-list params are treated as empty.
- @details Reads the ``"providers"`` key from `~/.config/usereq/config.json` (SRS-064, SRS-279). All providers are disabled by default because the key defaults to an empty list. Returns ``[]`` on any read or parse error rather than raising.
- @param canonical_lang Canonical language key that owns the entry.
- @param entry Static-check entry mapping loaded from config or parsed from CLI.
- @return Tuple ``(canonical_lang, module, cmd, params_tuple)``.
- @return List of provider names; empty list if key is missing or config is unreadable.
- @see SRS-279, SRS-064
- @satisfies SRS-301
- @satisfies SRS-064, SRS-279

### fn `def _read_config_payload() -> dict` `priv` (L2111-2131)
- @brief Read the raw user-global configuration payload without key filtering.
- @details Single read path for configuration commands performing read-modify-write updates (SRS-279, SRS-288, SRS-387, SRS-413, SRS-414, SRS-420).
- @return {dict} Raw JSON dictionary; empty dict when the file is absent.
- @throws {ReqError} Raised when the file exists but holds invalid JSON (exit code 11).
- @satisfies SRS-288, SRS-387

### fn `def _write_config_payload(payload: dict) -> None` `priv` (L2132-2150)
- @brief Write the user-global configuration payload filtered to canonical keys.
- @details Creates missing parent directories on first write (SRS-387) and never writes `--prj-base`/`--git-base` (SRS-394).
- @param payload {dict} Full payload; only `PERSISTED_CONFIG_KEYS` entries are written.
- @return {None} Function return value.
- @satisfies SRS-288, SRS-387, SRS-394

### fn `def load_auto_install_enabled() -> bool` (L2151-2165)
- @brief Resolve the persisted auto-install flag with enabled default.
- @details `auto-install` defaults to enabled; unreadable configuration falls back to the default (SRS-420, SRS-421).
- @return {bool} True unless the configuration stores exactly `false`.
- @satisfies SRS-420, SRS-421

### fn `def apply_enabled_providers(names: list[str]) -> None` (L2166-2195)
- @brief Persist ``--enable PROVIDER`` names replacing the named providers' entries.
- @details Validates every token through `validate_provider_name` (SRS-275, SRS-278), removes all previously persisted entries of the named providers, appends the new names deduplicated in CLI order, and preserves every other provider (SRS-279). No artifact is installed (SRS-276).
- @param names {list[str]} Raw provider name tokens in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid provider tokens with exit code 1 (SRS-278).
- @satisfies SRS-275, SRS-276, SRS-278, SRS-279

### fn `def apply_disabled_providers(names: list[str]) -> None` (L2196-2224)
- @brief Remove the named providers from the persisted `"providers"` array.
- @details Removes every persisted entry of each named provider; absent entries leave the configuration unchanged; the `"providers"` key is removed when no entries remain (SRS-413).
- @param names {list[str]} Provider names supplied via `--disable`.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown provider tokens with exit code 1 (SRS-422).
- @satisfies SRS-413, SRS-422

### fn `def apply_enable_static_check_specs(specs: list[str]) -> None` (L2225-2272)
- @brief Persist `--enable-static-check` entries merged into the existing configuration.
- @details Parses each SPEC (SRS-260), deduplicates within the invocation (SRS-251), validates Command executables (SRS-250), merges into the persisted `"static-check"` object by exact `(language, module, cmd, params)` identity (SRS-301), and requires no `--prj-base` (SRS-415).
- @param specs {list[str]} Raw SPEC strings in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid language/module tokens or non-executable Command `cmd` values with exit code 1.
- @satisfies SRS-248, SRS-250, SRS-251, SRS-301, SRS-415

### fn `def apply_disable_static_check_specs(specs: list[str]) -> None` (L2273-2321)
- @brief Remove static-check entries selected by `--disable-static-check` SPECs.
- @details Empty language arrays are removed from the `"static-check"` object and the `"static-check"` key is persisted even when empty so explicit configuration suppresses the SRS-424 defaults; requires no `--prj-base` (SRS-414, SRS-415).
- @param specs {list[str]} SPEC strings; `LANG=MODULE[,CMD[,PARAM...]]` removes exact identity matches, bare `LANG` removes the whole canonical language key.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown language or module tokens with exit code 1 (SRS-422).
- @satisfies SRS-414, SRS-415, SRS-422, SRS-424

### fn `def apply_auto_install_config(enabled: bool) -> None` (L2322-2334)
- @brief Persist the auto-install enabled flag.
- @details Read-modify-write preserving all unrelated canonical keys (SRS-420).
- @param enabled {bool} Value persisted under `"auto-install"`.
- @return {None} Function return value.
- @satisfies SRS-420

### fn `def _is_provider_config_command(args: Namespace) -> bool` `priv` (L2335-2352)
- @brief Check if args request a provider/static-check/auto-install configuration command.
- @details Configuration commands only update `~/.config/usereq/config.json` and never install artifacts (SRS-276, SRS-413, SRS-414, SRS-415, SRS-420).
- @param args Parsed CLI namespace.
- @return True when any configuration flag is present.

### fn `def run_config_commands(args: Namespace) -> None` (L2353-2381)
- @brief Apply every provider/static-check/auto-install configuration command.
- @details Application order: `--enable`, `--disable`, `--enable-static-check`, `--disable-static-check`, `--enable-auto-install`, `--disable-auto-install`; each step persists immediately (SRS-275, SRS-413, SRS-414, SRS-420).
- @param args Parsed CLI namespace carrying the configuration flag values.
- @return {None} Function return value.
- @satisfies SRS-275, SRS-276, SRS-413, SRS-414, SRS-415, SRS-420

### fn `def generate_guidelines_file_list() -> str` (L2382-2405)
- @brief Build the `%%GUIDELINES_FILES%%` substitution payload from GUIDELINES_DIR.
- @details Enumerates non-hidden regular files in :func:`guidelines_dir` in deterministic sorted order and renders each as a backticked home-relative path (SRS-402). When the directory is absent or empty, renders the home-relative directory itself with a trailing slash.
- @return {str} Comma-separated backticked home-relative paths, or the directory fallback.
- @satisfies SRS-403

### fn `def generate_guidelines_file_items() -> list[str]` (L2406-2428)
- @brief List the home-relative guideline entries reported after installation.
- @details Returns one home-relative path per non-hidden regular file in :func:`guidelines_dir`; when the directory is absent or empty, returns the home-relative directory itself with a trailing slash.
- @return {list[str]} Ordered home-relative guideline paths.
- @satisfies SRS-360, SRS-403

### fn `def ensure_relative(value: str, name: str, code: int) -> None` (L2429-2444)
- @brief Validates that the path is not absolute and raises an error otherwise.
- @details Implements the ensure_relative function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @param name Input parameter `name`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def apply_replacements(text: str, replacements: Mapping[str, str]) -> str` (L2445-2457)
- @brief Returns text with token replacements applied.
- @details Implements the apply_replacements function behavior with deterministic control flow.
- @param text Input parameter `text`.
- @param replacements Input parameter `replacements`.
- @return {str} Function return value.

### fn `def write_text_file(dst: Path, text: str) -> None` (L2458-2469)
- @brief Writes text to disk, ensuring the destination folder exists.
- @details Implements the write_text_file function behavior with deterministic control flow.
- @param dst Input parameter `dst`.
- @param text Input parameter `text`.
- @return {None} Function return value.

### fn `def copy_with_replacements(` (L2470-2471)

### fn `def extract_frontmatter(content: str) -> tuple[str, str]` (L2486-2499)
- @brief Copies a file substituting the indicated tokens with their values.
- @brief Extracts front matter and body from Markdown.
- @details Implements the copy_with_replacements function behavior with deterministic control flow.
- @details Implements the extract_frontmatter function behavior with deterministic control flow.
- @param src Input parameter `src`.
- @param dst Input parameter `dst`.
- @param replacements Input parameter `replacements`.
- @param content Input parameter `content`.
- @return {None} Function return value.
- @return {tuple[str, str]} Function return value.

### fn `def extract_purpose_first_bullet(body: str) -> str` (L2500-2524)
- @brief Returns the first bullet of the Purpose section.
- @details Implements the extract_purpose_first_bullet function behavior with deterministic control flow.
- @param body Input parameter `body`.
- @return {str} Function return value.

### fn `def _extract_section_text(body: str, section_name: str) -> str` `priv` (L2525-2552)
- @brief Extracts and collapses the text content of a named ## section.
- @details Scans `body` line by line for a heading matching `## <section_name>` (case-insensitive). Collects all subsequent non-empty lines until the next `##`-level heading (or end of string). Strips each line, joins with a single space, and returns the collapsed single-line result.
- @param[in] body str -- Full prompt body text (after front matter removal).
- @param[in] section_name str -- Target section name without `##` prefix (case-insensitive match).
- @return str -- Single-line collapsed text of the section; empty string if section absent or empty.

### fn `def extract_skill_description(frontmatter: str) -> str` (L2553-2571)
- @brief Extracts the usage field from YAML front matter as a single YAML-safe line.
- @details Parses the YAML front matter and returns the `usage` field value with all whitespace normalized to a single line. Returns an empty string if the field is absent.
- @param[in] frontmatter str -- YAML front matter text (without the leading/trailing `---` delimiters).
- @return str -- Single-line text of the usage field; empty string if absent.

### fn `def yaml_double_quote_escape(value: str) -> str` (L2572-2581)
- @brief Minimal escape for a double-quoted string in YAML.
- @details Implements the yaml_double_quote_escape function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @return {str} Function return value.

### fn `def list_docs_templates() -> list[Path]` (L2582-2601)
- @brief Returns non-hidden files available in resources/docs.
- @details Implements the list_docs_templates function behavior with deterministic control flow.
- @return Sorted list of file paths under resources/docs.
- @throws ReqError If resources/docs does not exist or has no non-hidden files.

### fn `def find_requirements_template(docs_templates: list[Path]) -> Path` (L2602-2618)
- @brief Returns the packaged Requirements template file.
- @details Implements the find_requirements_template function behavior with deterministic control flow.
- @param docs_templates Runtime docs template file list from resources/docs.
- @return Path to `Requirements_Template.md`.
- @throws ReqError If `Requirements_Template.md` is not present.

### fn `def ensure_wrapped(target: Path, project_base: Path, code: int) -> None` (L2619-2634)
- @brief Verifies that the path is under the project root.
- @details Implements the ensure_wrapped function behavior with deterministic control flow.
- @param target Input parameter `target`.
- @param project_base Input parameter `project_base`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def prune_empty_dirs(root: Path) -> None` (L2635-2651)
- @brief Removes empty directories under the specified root.
- @details Implements the prune_empty_dirs function behavior with deterministic control flow.
- @param root Input parameter `root`.
- @return {None} Function return value.

### fn `def remove_generated_resources() -> None` (L2652-2683)
- @brief Removes `req-*` skill artifacts generated by the tool from user-level provider directories.
- @details Loads the persisted `providers` array from the user-global configuration file, resolves each enabled provider skills root via :func:`provider_skills_root`, and deletes only `req-*` skill directories and files. Empty user-level skills roots are pruned afterwards; unrelated user content is never touched.
- @return {None} Function return value.
- @satisfies SRS-419

### fn `def _render_simple_table(headers: list[str], rows: list[list[str]]) -> str` `priv` (L2684-2714)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _line(cells: list[str]) -> str` `priv` (L2697-2705)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _border(left: str, middle: str, right: str) -> str` `priv` (L2706-2708)

### fn `def _provider_skills_installed(provider: str) -> bool` `priv` (L2715-2732)
- @brief Detect whether at least one `req-*` skill artifact exists for a provider.
- @details Installation status detection for the `show` subcommand (SRS-417); unknown providers and absent roots report `False`.
- @param provider {str} Provider selector from `{antigravity, claude, codex, openclaw, opencode, pi}`.
- @return {bool} True when the provider skills root contains a `req-*` entry.
- @satisfies SRS-417

### fn `def run_install(args: Namespace) -> None` (L2733-2748)
- @brief Execute install: install or update the persisted providers globally.
- @details Delegates to the config-driven installation flow (SRS-035, SRS-064, SRS-418) which requires at least one enabled provider and prints the installation summary report (SRS-049). Install performs no project-side operations and does not consume `--prj-base` (SRS-447, SRS-448); scaffolding and directory persistence are removed legacy behaviors (SRS-363, SRS-407, SRS-449).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If no provider is enabled.
- @satisfies SRS-035, SRS-064, SRS-418, SRS-447, SRS-448

### fn `def run_uninstall_providers(args: Namespace) -> None` (L2749-2766)
- @brief Execute uninstall: remove skill artifacts of the configured providers.
- @details Requires the user-global configuration file and removes `req-*` skill artifacts of the providers persisted under `"providers"` (SRS-419).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If the global configuration file is missing.
- @satisfies SRS-419

### fn `def run_show(args: Namespace) -> None` (L2767-2863)
- @brief Execute show: print the active configuration as tables.
- @details Prints the effective configuration table (`docs-dir`, `tests-dir`, `src-dir`, `auto-install`), the Providers table with `Provider` and `Skills Path` columns rendering the home-relative hardcoded skills root of every enabled provider in alphabetical order (SRS-462, SRS-463, SRS-485), one dedicated skills installation-status table per enabled provider in alphabetical order (SRS-417, SRS-485), and the enabled static-check entries (SRS-416).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If persisted provider names are invalid.
- @satisfies SRS-416, SRS-417, SRS-462, SRS-463, SRS-485

### fn `def _maybe_auto_install_after_upgrade(argv_list: list[str]) -> None` `priv` (L2864-2888)
- @brief Run the provider installation flow after a successful `--upgrade`.
- @details Executes the `install` flow with persisted providers when `auto-install` is enabled (SRS-420, SRS-421) regardless of `--prj-base` presence; prints an English stderr warning and skips when no provider is enabled (SRS-450).
- @param argv_list {list[str]} Raw CLI argument vector of the `--upgrade` invocation.
- @return {None} Function return value.
- @satisfies SRS-420, SRS-421, SRS-450

### fn `def run_set_directories(args: Namespace) -> None` (L2889-2952)
- @brief Persist `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` values.
- @details Requires `--prj-base` (SRS-396), normalizes each supplied path against the project base, rejects absolute or escaping paths, and writes only the supplied keys to `~/.config/usereq/config.json` while preserving unrelated keys (SRS-398, SRS-399, SRS-400, SRS-401). No project directory is created and no provider artifact is generated.
- @param args Parsed CLI namespace carrying the `set_docs_dir`, `set_src_dir`, and `set_tests_dir` values.
- @return {None} Function return value.
- @throws ReqError If `--prj-base` is absent or a supplied path escapes the project base.
- @satisfies SRS-396, SRS-398, SRS-399, SRS-400, SRS-401

### fn `def _validate_enable_static_check_command_executables(` `priv` (L2953-2956)

### fn `def run(args: Namespace) -> None` (L2985-3184)
- @brief Validate Command-module executables in `--enable-static-check` parsed entries.
- @brief Handles the main installation flow installing skills for persisted providers.
- @details Validation scope is limited to Command entries coming from CLI specs.
Each Command `cmd` is resolved with `shutil.which`; on miss, raises `ReqError(code=1)`
before any configuration persistence.
- @details Loads the persisted `"providers"` names from `~/.config/usereq/config.json` (SRS-064, SRS-279) and requires at least one enabled provider (SRS-035), installs `req-<prompt_name>/SKILL.md` skill artifacts into the user-level hardcoded skills roots (SRS-381..SRS-386, SRS-464, SRS-486) with home-relative GUIDELINES_DIR token substitution (SRS-402, SRS-403), and never rewrites the user-global configuration file (SRS-448). Install does not consume `--prj-base` (SRS-447); project scaffolding, containment validation, and directory persistence are removed legacy behaviors (SRS-363, SRS-407, SRS-449).
- @param static_check_config Parsed static-check entries grouped by canonical language.
- @param enforce When false, skip validation and return immediately.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @return {None} Function return value.
- @throws ReqError If a Command entry references a non-executable `cmd` on this system.
- @throws ReqError If no provider is enabled.
- @see SRS-250
- @satisfies SRS-035, SRS-064, SRS-279, SRS-381, SRS-387, SRS-388, SRS-402, SRS-403, SRS-418, SRS-447, SRS-448

- var `VERBOSE = getattr(args, "verbose", False)` (L3002)
- @brief Handles the main installation flow installing skills for persisted providers.
- @details Loads the persisted `"providers"` names from `~/.config/usereq/config.json`
(SRS-064, SRS-279) and requires at least one enabled provider (SRS-035), installs
`req-<prompt_name>/SKILL.md` skill artifacts into the user-level hardcoded skills
roots (SRS-381..SRS-386, SRS-464, SRS-486) with home-relative GUIDELINES_DIR token
substitution (SRS-402, SRS-403), and never rewrites the user-global configuration
file (SRS-448). Install does not consume `--prj-base` (SRS-447); project scaffolding,
containment validation, and directory persistence are removed legacy behaviors
(SRS-363, SRS-407, SRS-449).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If no provider is enabled.
- @satisfies SRS-035, SRS-064, SRS-279, SRS-381, SRS-387, SRS-388, SRS-402, SRS-403, SRS-418, SRS-447, SRS-448
- var `DEBUG = getattr(args, "debug", False)` (L3003)
### fn `def _format_install_table(` `priv` (L3113-3114)

### fn `def _wrap_cell(value: str, width: int, allow_wrap: bool) -> list[str]` `priv` (L3146-3168)
- @brief Format the Unicode installation summary table.
- @brief Normalize one table cell to printable lines.
- @details Builds a deterministic box-drawing table with exactly the `Provider`
and `Skills Installed` columns (SRS-291). Rows are rendered only for providers
whose skills were installed during the current invocation (SRS-036), in
alphabetical order. `Skills Installed` wraps overflowing content onto
subsequent lines at a maximum width of 50 characters (SRS-290). Borders are
emitted with Unicode line-drawing characters and bright-red ANSI styling
(SRS-049).
- @details Preserves explicit newline-separated segments. When wrapping is enabled, wraps each segment to the target width; otherwise keeps each segment as-is.
- @param skills_map {dict[str, set[str]]} Mapping: provider name -> installed skill identifiers.
- @param value {str} Cell text payload.
- @param width {int} Maximum cell width.
- @param allow_wrap {bool} Whether to apply line wrapping.
- @return {list[str]} Fully formatted table lines (including separators) ready for printing.
- @return {list[str]} Normalized printable lines for the cell.
- @note Complexity: O(C * (S log S)) where C is provider count and S is installed skills per provider.
- @note Side effects: None (pure formatting).
- @satisfies SRS-036, SRS-049, SRS-290, SRS-291

### fn `def _render_row(provider: str, skills: str) -> list[str]` `priv` (L3169-3190)
- @brief Render one logical table row into one or more physical lines.
- @details Applies per-cell wrapping and left alignment, then expands the row height to the maximum wrapped cell line count.
- @param provider {str} Provider cell text.
- @param skills {str} Skills Installed cell text.
- @return {list[str]} Physical row lines encoded with box-drawing separators.

### fn `def _colorize_table_border(line: str) -> str` `priv` (L3207-3219)
- @brief Colorize box-drawing border glyphs with bright-red ANSI style.
- @details Applies color to border characters while preserving cell payload text color.
- @param line {str} One already-rendered table line.
- @return {str} Line with border glyphs wrapped in ANSI bright-red and reset sequences.

- var `SUPPORTED_EXTENSIONS = frozenset(` (L3232)
### fn `def _collect_source_files(src_dirs: list[str], project_base: Path) -> list[str]` `priv` (L3260-3317)
- @brief Collect source files from git-indexed project paths.
- @details Uses `git ls-files --cached --others --exclude-standard` in project root, filters by src-dir prefixes, applies EXCLUDED_DIRS filtering, and keeps only SUPPORTED_EXTENSIONS files.
- @param src_dirs Input parameter `src_dirs`.
- @param project_base Input parameter `project_base`.
- @return {list[str]} Function return value.

### fn `def _build_ascii_tree(paths: list[str]) -> str` `priv` (L3318-3363)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _emit(` `priv` (L3342-3344)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _format_files_structure_markdown(files: list[str], project_base: Path) -> str` `priv` (L3364-3378)
- @brief Format markdown section containing the scanned files tree.
- @details Implements the _format_files_structure_markdown function behavior with deterministic control flow.
- @param files Absolute file paths selected for references processing.
- @param project_base Project root used to normalize relative paths.
- @return Markdown section with heading and fenced tree.

### fn `def _is_standalone_command(args: Namespace) -> bool` `priv` (L3379-3390)
- @brief Check if the parsed args contain a standalone file command.
- @details The standalone group now contains only `--test-static-check` (SRS-240); the former `--files-*` and project-scan analysis flags were converted to bare subcommands (SRS-408) whose base requirements follow SRS-396 and SRS-410.
- @param args Parsed CLI namespace.
- @return True when the standalone `--test-static-check` flag is present.

### fn `def _is_project_scan_command(args: Namespace) -> bool` `priv` (L3391-3408)
- @brief Check if the parsed args contain a project-scan command.
- @details Project-scan commands: `--git-check`, `--docs-check`, `--git-wt-name`, `--git-wt-create`, and `--git-wt-delete`. The analysis commands were converted to bare subcommands (SRS-408) and `--git-path` was removed (SRS-333, SRS-334).
- @param args Parsed CLI namespace.
- @return True when any project-scan flag is present.

### fn `def _is_directory_config_command(args: Namespace) -> bool` `priv` (L3409-3424)
- @brief Check if args request a directory configuration command.
- @details Configuration commands persist project-relative directories and therefore require `--prj-base` without activating the installation flow (SRS-396, SRS-398, SRS-399, SRS-400).
- @param args Parsed CLI namespace.
- @return True when any `--set-*-dir` flag is present.

### fn `def _require_prj_base(args: Namespace) -> Path` `priv` (L3425-3443)
- @brief Return the mandatory absolute project base for the current command.
- @details `--prj-base` is command-line only and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI namespace.
- @return {Path} Absolute project base path.
- @throws ReqError If `--prj-base` is absent or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _require_git_base_value(args: Namespace) -> Path` `priv` (L3444-3463)
- @brief Validate and return the `--git-base` argument value without repository resolution.
- @details Performs presence and existence validation only (SRS-395); git-integration commands reach this level through `_require_git_base` because they are the only commands that execute git operations through `--git-base` (SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute `--git-base` path.
- @throws ReqError If `--git-base` is absent or does not exist.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def _require_git_base(args: Namespace) -> Path` `priv` (L3464-3476)
- @brief Return the mandatory absolute git repository base for the current command.
- @details `--git-base` is command-line only and is never loaded from configuration; the returned path is the repository root reported by `git rev-parse --show-toplevel` executed in `--git-base` (SRS-393, SRS-394, SRS-395, SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute git repository root resolved from `--git-base`.
- @throws ReqError If `--git-base` is absent, does not exist, or is not inside a git work tree.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def run_git_check(args: Namespace) -> None` (L3477-3504)
- @brief Execute --git-check: verify clean git status and valid HEAD.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On git status unclear or when `--git-base` is outside a git repository.
- @satisfies SRS-311, SRS-312, SRS-391, SRS-397

### fn `def run_docs_check(args: Namespace) -> None` (L3505-3534)
- @brief Execute --docs-check: verify existence of REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If any required doc file is missing.
- @satisfies SRS-313, SRS-314, SRS-315, SRS-316, SRS-317, SRS-396

### fn `def run_git_wt_name(args: Namespace) -> None` (L3535-3559)
- @brief Execute --git-wt-name: print standardized worktree name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @satisfies SRS-318, SRS-319, SRS-391, SRS-397

### fn `def _worktree_path_exists_exact(git_path: Path, target_path: Path) -> bool` `priv` (L3560-3589)
- @brief Check whether a git worktree exists at the exact target path.
- @details Parses `git worktree list --porcelain` output by `worktree <path>` records and performs exact path comparison to prevent partial-name or substring matches.
- @param git_path Absolute git root path used as command cwd.
- @param target_path Absolute worktree path expected for WT_NAME.
- @return {bool} True only when target_path is listed as an exact worktree path.
- @throws ReqError On git command execution errors.

### fn `def _rollback_worktree_create(git_path: Path, wt_path: Path, wt_name: str) -> None` `priv` (L3590-3626)
- @brief Roll back worktree and branch created by --git-wt-create on post-create failure.
- @details Uses `git worktree remove <path> --force` and `git branch -D <name>` to restore a clean git state when post-create copy/chdir operations fail.
- @param git_path Absolute git root path used as command cwd.
- @param wt_path Absolute worktree path to remove.
- @param wt_name Exact branch name to delete.
- @return {None} Function return value.
- @throws ReqError If rollback cannot remove the exact target worktree and branch.

### fn `def run_git_wt_create(args: Namespace) -> None` (L3627-3682)
- @brief Execute --git-wt-create: create a git worktree, branch, and .venv seeding from --prj-base.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name, missing or invalid `--prj-base` (SRS-395), git command failure, or when CWD is outside a git repository.
- @satisfies SRS-320, SRS-321, SRS-322, SRS-331, SRS-335, SRS-391, SRS-395, SRS-397, SRS-460

### fn `def run_git_wt_delete(args: Namespace) -> None` (L3683-3751)
- @brief Execute --git-wt-delete: remove a git worktree and branch by name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name or git removal failure.
- @satisfies SRS-326, SRS-327, SRS-328, SRS-332, SRS-391, SRS-397

### fn `def run_files_tokens(files: list[str]) -> None` (L3752-3775)
- @brief Execute files-tokens: count tokens for arbitrary files.
- @details Implements the run_files_tokens function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_references(files: list[str]) -> None` (L3776-3793)
- @brief Execute files-references: generate markdown for arbitrary files.
- @details Implements the run_files_references function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-234, SRS-408

### fn `def run_files_compress(files: list[str], enable_line_numbers: bool = False) -> None` (L3794-3813)
- @brief Execute files-compress: compress arbitrary files.
- @details Renders output header paths relative to current working directory.
- @param files List of source file paths to compress.
- @param enable_line_numbers If True, emits <n>: prefixes in compressed entries.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_find(args_list: list[str], enable_line_numbers: bool = False) -> None` (L3814-3843)
- @brief Execute files-find: find constructs in arbitrary files.
- @details Implements the run_files_find function behavior with deterministic control flow.
- @param args_list Combined list: [TAG, PATTERN, FILE1, FILE2, ...].
- @param enable_line_numbers If True, emits <n>: prefixes in output.
- @return {None} Function return value.
- @satisfies SRS-236, SRS-408

### fn `def run_references(args: Namespace) -> None` (L3844-3862)
- @brief Execute references: generate markdown for project source files.
- @details Implements the run_references function behavior with deterministic control flow.
- @param args Input parameter `args`.
- @return {None} Function return value.
- @satisfies SRS-177, SRS-180, SRS-181, SRS-235, SRS-396, SRS-408

### fn `def run_compress_cmd(args: Namespace) -> None` (L3863-3885)
- @brief Execute compress: compress project source files.
- @details Implements the run_compress_cmd function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @satisfies SRS-179, SRS-180, SRS-181, SRS-396, SRS-408

### fn `def run_find(args: Namespace) -> None` (L3886-3916)
- @brief Execute find: find constructs in project source files.
- @details Implements the run_find function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @throws ReqError If no source files found or no constructs match criteria with available TAGs listing.
- @satisfies SRS-180, SRS-237, SRS-396, SRS-408

### fn `def run_tokens(args: Namespace) -> None` (L3917-3946)
- @brief Execute tokens on the canonical documentation files in --docs-dir.
- @details Uses the mandatory `--prj-base` project base joined with the docs-dir value from ~/.config/usereq/config.json, selects only REQUIREMENTS.md/WORKFLOW.md/REFERENCES.md as direct regular files in fixed order, and delegates summary rendering to run_files_tokens.
- @param args Parsed CLI arguments namespace.
- @return None.
- @exception ReqError Raised when no canonical documentation file exists in configured docs-dir.
- @satisfies SRS-387, SRS-392, SRS-396, SRS-408

### fn `def run_files_static_check_cmd(files: list[str], args: Namespace) -> int` (L3947-4013)
- @brief Execute `files-static-check`: run static analysis on an explicit file list.
- @details Static-check configuration is loaded from `~/.config/usereq/config.json`. When the global configuration file cannot be located, emits a warning to stderr and continues with the SRS-424 default static-check configuration (SRS-254). Project base for dispatch context is the mandatory `--prj-base` value (SRS-253). For each file: - Resolves absolute path; skips with warning if not a regular file. - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on the lowercase extension. - Looks up language in the `"static-check"` config section; skips silently if absent. - Executes each configured language entry sequentially via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`. - For `Command` module entries, execution order is `<cmd> [params...] <filename>`. Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-253). Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-253, SRS-255)
- @param files List of raw file paths supplied by the user.
- @param args Parsed CLI namespace; the mandatory `--prj-base` resolves the dispatch context.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @see SRS-253, SRS-254, SRS-255, SRS-341, SRS-396, SRS-408

### fn `def run_project_static_check_cmd(args: Namespace) -> int` (L4014-4113)
- @brief Execute `static-check`: run static analysis on project source and test files.
- @details Collects files from configured `src-dir` directories and the `tests-dir` directory (SRS-256, SRS-336), applies `EXCLUDED_DIRS` filtering and `SUPPORTED_EXTENSIONS` matching. If `tests-dir` is missing or invalid in the global configuration file, test directory inclusion is skipped silently without error (SRS-336). Files under `<tests-dir>/fixtures/` are excluded from static-check selection because they are fixture corpus inputs for parser/static-check tests and can intentionally contain diagnostics unrelated to project code quality gates. For each collected file: - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on lowercase extension. - Looks up language in the `"static-check"` section of `~/.config/usereq/config.json`. - Skips silently when no tool is configured for the file's language. - Executes each configured language entry sequentially via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`. - For `Command` module entries, execution order is `<cmd> [params...] <filename>`. Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-256). Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-256, SRS-257)
- @param args Parsed CLI namespace; requires the mandatory `--prj-base` argument.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @throws ReqError If no source files are found.
- @see SRS-256, SRS-257, SRS-336, SRS-341, SRS-396, SRS-408

### fn `def _resolve_project_base(args: Namespace) -> Path` `priv` (L4114-4126)
- @brief Resolve the mandatory project base path for project-level commands.
- @details The project base is never derived from the current working directory and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI arguments namespace.
- @return Absolute path of the project base supplied by `--prj-base`.
- @throws ReqError If `--prj-base` is missing or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _resolve_project_src_dirs(args: Namespace) -> tuple[Path, list[str]]` `priv` (L4127-4157)
- @brief Resolve project base and src-dirs for project source commands.
- @details Loads the `src-dir` list from the user-global configuration file (`~/.config/usereq/config.json`) and resolves it against the mandatory `--prj-base` project base (SRS-392, SRS-396).
- @param args Input parameter `args`.
- @return {tuple[Path, list[str]]} Tuple `(project_base, src_dirs)`.
- @throws ReqError If `--prj-base` is missing or `src-dir` is invalid.
- @satisfies SRS-392, SRS-396

### fn `def main(argv: Optional[list[str]] = None) -> int` (L4158-4282)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.

- var `FORCE_ONLINE_RELEASE_CHECK = force_online_release_check` (L4172)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.
- var `FORCE_ONLINE_RELEASE_CHECK = previous_force_online_release_check` (L4179)
- var `VERBOSE = getattr(args, "verbose", False)` (L4193)
- var `DEBUG = getattr(args, "debug", False)` (L4194)
## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`REPO_ROOT`|var|pub|31||
|`RESOURCE_ROOT`|var|pub|34||
|`VERBOSE`|var|pub|37||
|`DEBUG`|var|pub|40||
|`REQUIREMENTS_TEMPLATE_NAME`|var|pub|43||
|`PERSISTED_CONFIG_KEYS`|var|pub|46||
|`AUTO_INSTALL_CONFIG_KEY`|var|pub|56||
|`DEFAULT_AUTO_INSTALL`|var|pub|59||
|`DEFAULT_DOCS_DIR`|var|pub|62||
|`DEFAULT_TESTS_DIR`|var|pub|65||
|`DEFAULT_SRC_DIRS`|var|pub|68||
|`GUIDELINES_DIR_RELATIVE_TO_HOME`|var|pub|105||
|`VALID_PROVIDERS`|var|pub|117||
|`GLOBAL_CONFIG_DIRNAME`|var|pub|122||
|`GLOBAL_CONFIG_APP_DIRNAME`|var|pub|125||
|`GLOBAL_CONFIG_FILENAME`|var|pub|128||
|`home_dir`|fn|pub|132-142|def home_dir() -> Path|
|`get_global_config_path`|fn|pub|143-158|def get_global_config_path() -> Path|
|`guidelines_dir`|fn|pub|159-169|def guidelines_dir() -> Path|
|`format_home_relative_path`|fn|pub|170-189|def format_home_relative_path(path: Path) -> str|
|`provider_skills_root`|fn|pub|190-221|def provider_skills_root(provider: str) -> Path|
|`provider_skills_path`|fn|pub|222-235|def provider_skills_path(provider: str) -> str|
|`INVALID_WT_NAME_RE`|var|pub|236||
|`validate_provider_name`|fn|pub|240-262|def validate_provider_name(name: str) -> str|
|`resolve_provider_configs`|fn|pub|263-264|def resolve_provider_configs(|
|`ANSI_BRIGHT_RED`|var|pub|287||
|`ANSI_BRIGHT_GREEN`|var|pub|290||
|`ANSI_RESET`|var|pub|293||
|`RELEASE_CHECK_TIMEOUT_SECONDS`|var|pub|296||
|`RELEASE_CHECK_IDLE_DELAY_SECONDS`|var|pub|299||
|`RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS`|var|pub|302||
|`TOOL_PROGRAM_NAME`|var|pub|305||
|`RELEASE_CHECK_PROGRAM_NAME`|var|pub|311||
|`GITHUB_REPOSITORY_OWNER`|var|pub|316||
|`GITHUB_REPOSITORY_NAME`|var|pub|319||
|`RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME`|var|pub|322||
|`RELEASE_CHECK_IDLE_FILENAME`|var|pub|325||
|`GITHUB_RELEASES_LATEST_URL`|var|pub|328||
|`GITHUB_UPGRADE_SOURCE`|var|pub|337||
|`PYPI_PROJECT_JSON_URL`|var|pub|344||
|`UNKNOWN_VERSION_LABEL`|var|pub|350||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|353||
|`ReqError`|class|pub|357-374|class ReqError(Exception)|
|`ReqError.__init__`|fn|priv|362-374|def __init__(self, message: str, code: int = 1) -> None|
|`log`|fn|pub|375-384|def log(msg: str) -> None|
|`dlog`|fn|pub|385-395|def dlog(msg: str) -> None|
|`vlog`|fn|pub|396-406|def vlog(msg: str) -> None|
|`build_parser`|fn|pub|407-606|def build_parser() -> argparse.ArgumentParser|
|`parse_args`|fn|pub|825-834|def parse_args(argv: Optional[list[str]] = None) -> Names...|
|`load_package_version`|fn|pub|835-849|def load_package_version() -> str|
|`maybe_print_version`|fn|pub|850-895|def maybe_print_version(argv: list[str], pypi_latest: Opt...|
|`_resolve_github_upgrade_tag`|fn|priv|896-926|def _resolve_github_upgrade_tag() -> str|
|`run_upgrade`|fn|pub|927-974|def run_upgrade(use_github: bool = False) -> None|
|`run_uninstall`|fn|pub|975-1007|def run_uninstall() -> None|
|`normalize_release_tag`|fn|pub|1008-1020|def normalize_release_tag(tag: str) -> str|
|`parse_version_tuple`|fn|pub|1021-1045|def parse_version_tuple(version: str) -> tuple[int, ...] ...|
|`is_newer_version`|fn|pub|1046-1064|def is_newer_version(current: str, latest: str) -> bool|
|`parse_github_owner_repository`|fn|pub|1065-1091|def parse_github_owner_repository(remote_url: str) -> tup...|
|`read_git_remote_verbose`|fn|pub|1092-1111|def read_git_remote_verbose(cwd: str | None = None) -> str|
|`resolve_github_owner_repository_from_active_remotes`|fn|pub|1112-1172|def resolve_github_owner_repository_from_active_remotes()...|
|`resolve_pypi_latest_version_url`|fn|pub|1173-1182|def resolve_pypi_latest_version_url() -> str|
|`fetch_pypi_latest_version`|fn|pub|1183-1184|def fetch_pypi_latest_version(|
|`fetch_github_latest_version`|fn|pub|1220-1223|def fetch_github_latest_version(|
|`format_unix_timestamp_utc`|fn|pub|1262-1274|def format_unix_timestamp_utc(timestamp_seconds: int) -> str|
|`get_release_check_idle_file_path`|fn|pub|1275-1276|def get_release_check_idle_file_path(|
|`cleanup_release_check_idle_state_cache`|fn|pub|1293-1294|def cleanup_release_check_idle_state_cache(|
|`read_release_check_idle_state`|fn|pub|1317-1381|def read_release_check_idle_state(file_path: Path) -> dic...|
|`should_execute_release_check`|fn|pub|1382-1384|def should_execute_release_check(|
|`parse_retry_after_seconds`|fn|pub|1403-1405|def parse_retry_after_seconds(|
|`write_release_check_idle_state_payload`|fn|pub|1435-1438|def write_release_check_idle_state_payload(|
|`write_release_check_idle_state`|fn|pub|1465-1468|def write_release_check_idle_state(|
|`write_failed_release_check_idle_state`|fn|pub|1487-1491|def write_failed_release_check_idle_state(|
|`persist_failed_release_check_idle_state`|fn|pub|1519-1523|def persist_failed_release_check_idle_state(|
|`maybe_notify_newer_version`|fn|pub|1549-1550|def maybe_notify_newer_version(|
|`ensure_doc_directory`|fn|pub|1679-1680|def ensure_doc_directory(|
|`ensure_test_directory`|fn|pub|1709-1710|def ensure_test_directory(|
|`ensure_src_directory`|fn|pub|1739-1740|def ensure_src_directory(|
|`make_relative_if_contains_project`|fn|pub|1769-1810|def make_relative_if_contains_project(path_value: str, pr...|
|`resolve_absolute`|fn|pub|1811-1826|def resolve_absolute(normalized: str, project_base: Path)...|
|`resolve_git_root`|fn|pub|1827-1854|def resolve_git_root(target_path: Path) -> Path|
|`sanitize_branch_name`|fn|pub|1855-1864|def sanitize_branch_name(branch: str) -> str|
|`validate_wt_name`|fn|pub|1865-1876|def validate_wt_name(wt_name: str) -> bool|
|`load_full_config`|fn|pub|1877-1897|def load_full_config() -> dict|
|`save_config`|fn|pub|1898-1903|def save_config(|
|`update_directory_config`|fn|pub|1933-1936|def update_directory_config(|
|`load_config`|fn|pub|1974-2024|def load_config() -> dict[str, str | list[str]]|
|`load_static_check_from_config`|fn|pub|2025-2063|def load_static_check_from_config() -> dict|
|`_static_check_entry_identity`|fn|priv|2064-2065|def _static_check_entry_identity(|
|`load_persisted_providers`|fn|pub|2088-2110|def load_persisted_providers() -> list[str]|
|`_read_config_payload`|fn|priv|2111-2131|def _read_config_payload() -> dict|
|`_write_config_payload`|fn|priv|2132-2150|def _write_config_payload(payload: dict) -> None|
|`load_auto_install_enabled`|fn|pub|2151-2165|def load_auto_install_enabled() -> bool|
|`apply_enabled_providers`|fn|pub|2166-2195|def apply_enabled_providers(names: list[str]) -> None|
|`apply_disabled_providers`|fn|pub|2196-2224|def apply_disabled_providers(names: list[str]) -> None|
|`apply_enable_static_check_specs`|fn|pub|2225-2272|def apply_enable_static_check_specs(specs: list[str]) -> ...|
|`apply_disable_static_check_specs`|fn|pub|2273-2321|def apply_disable_static_check_specs(specs: list[str]) ->...|
|`apply_auto_install_config`|fn|pub|2322-2334|def apply_auto_install_config(enabled: bool) -> None|
|`_is_provider_config_command`|fn|priv|2335-2352|def _is_provider_config_command(args: Namespace) -> bool|
|`run_config_commands`|fn|pub|2353-2381|def run_config_commands(args: Namespace) -> None|
|`generate_guidelines_file_list`|fn|pub|2382-2405|def generate_guidelines_file_list() -> str|
|`generate_guidelines_file_items`|fn|pub|2406-2428|def generate_guidelines_file_items() -> list[str]|
|`ensure_relative`|fn|pub|2429-2444|def ensure_relative(value: str, name: str, code: int) -> ...|
|`apply_replacements`|fn|pub|2445-2457|def apply_replacements(text: str, replacements: Mapping[s...|
|`write_text_file`|fn|pub|2458-2469|def write_text_file(dst: Path, text: str) -> None|
|`copy_with_replacements`|fn|pub|2470-2471|def copy_with_replacements(|
|`extract_frontmatter`|fn|pub|2486-2499|def extract_frontmatter(content: str) -> tuple[str, str]|
|`extract_purpose_first_bullet`|fn|pub|2500-2524|def extract_purpose_first_bullet(body: str) -> str|
|`_extract_section_text`|fn|priv|2525-2552|def _extract_section_text(body: str, section_name: str) -...|
|`extract_skill_description`|fn|pub|2553-2571|def extract_skill_description(frontmatter: str) -> str|
|`yaml_double_quote_escape`|fn|pub|2572-2581|def yaml_double_quote_escape(value: str) -> str|
|`list_docs_templates`|fn|pub|2582-2601|def list_docs_templates() -> list[Path]|
|`find_requirements_template`|fn|pub|2602-2618|def find_requirements_template(docs_templates: list[Path]...|
|`ensure_wrapped`|fn|pub|2619-2634|def ensure_wrapped(target: Path, project_base: Path, code...|
|`prune_empty_dirs`|fn|pub|2635-2651|def prune_empty_dirs(root: Path) -> None|
|`remove_generated_resources`|fn|pub|2652-2683|def remove_generated_resources() -> None|
|`_render_simple_table`|fn|priv|2684-2714|def _render_simple_table(headers: list[str], rows: list[l...|
|`_line`|fn|priv|2697-2705|def _line(cells: list[str]) -> str|
|`_border`|fn|priv|2706-2708|def _border(left: str, middle: str, right: str) -> str|
|`_provider_skills_installed`|fn|priv|2715-2732|def _provider_skills_installed(provider: str) -> bool|
|`run_install`|fn|pub|2733-2748|def run_install(args: Namespace) -> None|
|`run_uninstall_providers`|fn|pub|2749-2766|def run_uninstall_providers(args: Namespace) -> None|
|`run_show`|fn|pub|2767-2863|def run_show(args: Namespace) -> None|
|`_maybe_auto_install_after_upgrade`|fn|priv|2864-2888|def _maybe_auto_install_after_upgrade(argv_list: list[str...|
|`run_set_directories`|fn|pub|2889-2952|def run_set_directories(args: Namespace) -> None|
|`_validate_enable_static_check_command_executables`|fn|priv|2953-2956|def _validate_enable_static_check_command_executables(|
|`run`|fn|pub|2985-3184|def run(args: Namespace) -> None|
|`VERBOSE`|var|pub|3002||
|`DEBUG`|var|pub|3003||
|`_format_install_table`|fn|priv|3113-3114|def _format_install_table(|
|`_wrap_cell`|fn|priv|3146-3168|def _wrap_cell(value: str, width: int, allow_wrap: bool) ...|
|`_render_row`|fn|priv|3169-3190|def _render_row(provider: str, skills: str) -> list[str]|
|`_colorize_table_border`|fn|priv|3207-3219|def _colorize_table_border(line: str) -> str|
|`SUPPORTED_EXTENSIONS`|var|pub|3232||
|`_collect_source_files`|fn|priv|3260-3317|def _collect_source_files(src_dirs: list[str], project_ba...|
|`_build_ascii_tree`|fn|priv|3318-3363|def _build_ascii_tree(paths: list[str]) -> str|
|`_emit`|fn|priv|3342-3344|def _emit(|
|`_format_files_structure_markdown`|fn|priv|3364-3378|def _format_files_structure_markdown(files: list[str], pr...|
|`_is_standalone_command`|fn|priv|3379-3390|def _is_standalone_command(args: Namespace) -> bool|
|`_is_project_scan_command`|fn|priv|3391-3408|def _is_project_scan_command(args: Namespace) -> bool|
|`_is_directory_config_command`|fn|priv|3409-3424|def _is_directory_config_command(args: Namespace) -> bool|
|`_require_prj_base`|fn|priv|3425-3443|def _require_prj_base(args: Namespace) -> Path|
|`_require_git_base_value`|fn|priv|3444-3463|def _require_git_base_value(args: Namespace) -> Path|
|`_require_git_base`|fn|priv|3464-3476|def _require_git_base(args: Namespace) -> Path|
|`run_git_check`|fn|pub|3477-3504|def run_git_check(args: Namespace) -> None|
|`run_docs_check`|fn|pub|3505-3534|def run_docs_check(args: Namespace) -> None|
|`run_git_wt_name`|fn|pub|3535-3559|def run_git_wt_name(args: Namespace) -> None|
|`_worktree_path_exists_exact`|fn|priv|3560-3589|def _worktree_path_exists_exact(git_path: Path, target_pa...|
|`_rollback_worktree_create`|fn|priv|3590-3626|def _rollback_worktree_create(git_path: Path, wt_path: Pa...|
|`run_git_wt_create`|fn|pub|3627-3682|def run_git_wt_create(args: Namespace) -> None|
|`run_git_wt_delete`|fn|pub|3683-3751|def run_git_wt_delete(args: Namespace) -> None|
|`run_files_tokens`|fn|pub|3752-3775|def run_files_tokens(files: list[str]) -> None|
|`run_files_references`|fn|pub|3776-3793|def run_files_references(files: list[str]) -> None|
|`run_files_compress`|fn|pub|3794-3813|def run_files_compress(files: list[str], enable_line_numb...|
|`run_files_find`|fn|pub|3814-3843|def run_files_find(args_list: list[str], enable_line_numb...|
|`run_references`|fn|pub|3844-3862|def run_references(args: Namespace) -> None|
|`run_compress_cmd`|fn|pub|3863-3885|def run_compress_cmd(args: Namespace) -> None|
|`run_find`|fn|pub|3886-3916|def run_find(args: Namespace) -> None|
|`run_tokens`|fn|pub|3917-3946|def run_tokens(args: Namespace) -> None|
|`run_files_static_check_cmd`|fn|pub|3947-4013|def run_files_static_check_cmd(files: list[str], args: Na...|
|`run_project_static_check_cmd`|fn|pub|4014-4113|def run_project_static_check_cmd(args: Namespace) -> int|
|`_resolve_project_base`|fn|priv|4114-4126|def _resolve_project_base(args: Namespace) -> Path|
|`_resolve_project_src_dirs`|fn|priv|4127-4157|def _resolve_project_src_dirs(args: Namespace) -> tuple[P...|
|`main`|fn|pub|4158-4282|def main(argv: Optional[list[str]] = None) -> int|
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4172||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4179||
|`VERBOSE`|var|pub|4193||
|`DEBUG`|var|pub|4194||


---

# compress.py | Python | 393L | 11 symbols | 4 imports | 41 comments
> Path: `src/usereq/compress.py`
- @brief Source code compressor for LLM context optimization.
- @details Parses a source file and removes all comments (inline, single-line, multi-line), blank lines, trailing whitespace, and redundant spacing while preserving language semantics (e.g. Python indentation). Leverages LanguageSpec from source_analyzer to correctly identify comment syntax for each supported language.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import os
import sys
from .source_analyzer import build_language_specs
import argparse
```

## Definitions

- var `EXT_LANG_MAP = {` (L16)
- var `INDENT_SIGNIFICANT = {"python", "haskell", "elixir"}` (L28)
### fn `def _get_specs()` `priv` (L35-45)
- @brief Cached language specification dictionary initialized lazily."""
- @brief Return cached language specifications, initializing once.
- @details If cache is empty, calls `build_language_specs()` to populate it.
- @return Dictionary mapping normalized language keys to language specs.

### fn `def detect_language(filepath: str) -> str | None` (L46-55)
- @brief Detect language key from file extension.
- @details Uses `EXT_LANG_MAP` for lookup. Case-insensitive extension matching.
- @param filepath Source file path.
- @return Normalized language key, or None when extension is unsupported.

### fn `def _is_in_string(line: str, pos: int, string_delimiters: tuple) -> bool` `priv` (L56-97)
- @brief Check if position `pos` in `line` is inside a string literal.
- @details iterates through the line handling escaped delimiters.
- @param line The code line string.
- @param pos The character index to check.
- @param string_delimiters Tuple of string delimiter characters/sequences.
- @return True if `pos` is inside a string, False otherwise.

### fn `def _remove_inline_comment(line: str, single_comment: str,` `priv` (L98-141)
- @brief Remove trailing single-line comment from a code line.
- @details Respects string literals; does not remove comments inside strings.
- @param line The code line string.
- @param single_comment The single-line comment marker (e.g., "//", "#").
- @param string_delimiters Tuple of string delimiters to respect.
- @return The line content before the comment starts.

### fn `def _is_python_docstring_line(line: str) -> bool` `priv` (L142-155)
- @brief Check if a line is a standalone Python docstring (triple-quote only).
- @details Implements the _is_python_docstring_line function behavior with deterministic control flow.
- @param line The code line string.
- @return True if the line appears to be a standalone triple-quoted string.

### fn `def _format_result(entries: list[tuple[int, str]],` `priv` (L156-169)
- @brief Format compressed entries, optionally prefixing original line numbers.
- @details Implements the _format_result function behavior with deterministic control flow.
- @param entries List of tuples (line_number, text).
- @param include_line_numbers Boolean flag to enable line prefixes.
- @return Formatted string.

### fn `def compress_source(source: str, language: str,` (L170-337)
- @brief Compress source code by removing comments, blank lines, and extra whitespace.
- @details Preserves indentation for indent-significant languages (Python, Haskell, Elixir).
- @param source The source code string.
- @param language Language identifier (e.g. "python", "javascript").
- @param include_line_numbers If True (default), prefix each line with <n>: format.
- @return Compressed source code string.
- @throws ValueError If language is unsupported.

### fn `def compress_file(filepath: str, language: str | None = None,` (L338-361)
- @brief Compress a source file by removing comments and extra whitespace.
- @details Implements the compress_file function behavior with deterministic control flow.
- @param filepath Path to the source file.
- @param language Optional language override. Auto-detected if None.
- @param include_line_numbers If True (default), prefix each line with <n>: format.
- @return Compressed source code string.
- @throws ValueError If language cannot be detected.

### fn `def main()` (L362-391)
- @brief Execute the standalone compression CLI.
- @details Parses command-line arguments and invokes `compress_file`, printing the result to stdout or errors to stderr.
- @return {None} Function return value.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`EXT_LANG_MAP`|var|pub|16||
|`INDENT_SIGNIFICANT`|var|pub|28||
|`_get_specs`|fn|priv|35-45|def _get_specs()|
|`detect_language`|fn|pub|46-55|def detect_language(filepath: str) -> str | None|
|`_is_in_string`|fn|priv|56-97|def _is_in_string(line: str, pos: int, string_delimiters:...|
|`_remove_inline_comment`|fn|priv|98-141|def _remove_inline_comment(line: str, single_comment: str,|
|`_is_python_docstring_line`|fn|priv|142-155|def _is_python_docstring_line(line: str) -> bool|
|`_format_result`|fn|priv|156-169|def _format_result(entries: list[tuple[int, str]],|
|`compress_source`|fn|pub|170-337|def compress_source(source: str, language: str,|
|`compress_file`|fn|pub|338-361|def compress_file(filepath: str, language: str | None = N...|
|`main`|fn|pub|362-391|def main()|


---

# compress_files.py | Python | 134L | 4 symbols | 5 imports | 6 comments
> Path: `src/usereq/compress_files.py`
- @brief Compress and concatenate multiple source files.
- @details Uses the compress module to strip comments and whitespace from each input file, then concatenates results with a compact header per file for unique identification by an LLM agent.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import os
import sys
from pathlib import Path
from .compress import compress_file, detect_language
import argparse
```

## Definitions

### fn `def _extract_line_range(compressed_with_line_numbers: str) -> tuple[int, int]` `priv` (L17-34)
- @brief Extract source line interval from compressed output with <n>: prefixes.
- @details Parses the first token of each line as an integer line number.
- @param compressed_with_line_numbers Compressed payload generated with include_line_numbers=True.
- @return Tuple (line_start, line_end) derived from preserved <n>: prefixes; returns (0, 0) when no prefixed lines exist.

### fn `def _format_output_path(filepath: str, output_base: Path | None) -> str` `priv` (L35-48)
- @brief Build the header-visible path for one compressed source file.
- @details Implements the _format_output_path function behavior with deterministic control flow.
- @param filepath Absolute or relative source file path.
- @param output_base Project-home base used to relativize output paths.
- @return Original filepath when output_base is None; otherwise POSIX relative path from output_base.

### fn `def compress_files(filepaths: list[str],` (L49-109)

### fn `def main()` (L110-132)
- @brief Execute the multi-file compression CLI command.
- @details Parses command-line arguments, calls `compress_files`, and prints output or errors.
- @return {None} Function return value.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`_extract_line_range`|fn|priv|17-34|def _extract_line_range(compressed_with_line_numbers: str...|
|`_format_output_path`|fn|priv|35-48|def _format_output_path(filepath: str, output_base: Path ...|
|`compress_files`|fn|pub|49-109|def compress_files(filepaths: list[str],|
|`main`|fn|pub|110-132|def main()|


---

# doxygen_parser.py | Python | 172L | 6 symbols | 2 imports | 19 comments
> Path: `src/usereq/doxygen_parser.py`
- @brief Doxygen comment parser for extracting structured documentation fields.
- @brief ,
- @details Parses Doxygen-formatted documentation comments and extracts recognized tags (
- @param ,
- @return , etc.) into structured dictionaries for downstream LLM-optimized markdown rendering.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import re
from typing import Dict, List
```

## Definitions

- var `DOXYGEN_TAGS = [` (L15)
- var `DOXYGEN_TAG_PATTERN = re.compile(` (L44)
- @brief Regex alternation for non-param tags ordered by descending length."""
### fn `def parse_doxygen_comment(comment_text: str) -> Dict[str, List[str]]` (L51-99)
- @brief Compiled regex that matches supported @tag / \\tag tokens."""
- @brief Extract Doxygen fields from a documentation comment block.
- @details Parses both @tag and \\tag syntax. Each tag's content extends until the next tag or end of comment. Multiple occurrences of the same tag accumulate in the returned list. Whitespace is normalized.
- @param comment_text Raw comment string potentially containing Doxygen tags.
- @return Dictionary mapping normalized tag names to lists of extracted content strings.
- @note Returns empty dict if no Doxygen tags are found.
- @see DOXYGEN_TAGS for recognized tag list.

### fn `def _strip_comment_delimiters(text: str) -> str` `priv` (L100-128)
- @brief Remove common comment delimiters from text block.
- @details Strips leading/trailing /**, */, //, #, triple quotes, and intermediate * column markers. Preserves content while removing comment syntax artifacts.
- @param text Raw comment block possibly containing comment delimiters.
- @return Cleaned text with delimiters removed.

### fn `def _normalize_whitespace(text: str) -> str` `priv` (L129-154)
- @brief Normalize internal whitespace in extracted tag content.
- @details Collapses multiple spaces to single space, preserves single newlines, removes redundant blank lines.
- @param text Tag content with potentially irregular whitespace.
- @return Whitespace-normalized content.

### fn `def format_doxygen_fields_as_markdown(doxygen_fields: Dict[str, List[str]]) -> List[str]` (L155-173)
- @brief Format extracted Doxygen fields as Markdown bulleted list.
- @details Emits fields in fixed order (DOXYGEN_TAGS) preserving original Doxygen tag tokens with `@` prefix and no `:` suffix. Skips tags not present in input. Each extracted field occurrence is emitted as an independent markdown bullet.
- @param doxygen_fields Dictionary of tag -> content list from parse_doxygen_comment().
- @return List of Markdown lines (each starting with '- ').
- @note Output order matches DOXYGEN_TAGS sequence.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`DOXYGEN_TAGS`|var|pub|15||
|`DOXYGEN_TAG_PATTERN`|var|pub|44||
|`parse_doxygen_comment`|fn|pub|51-99|def parse_doxygen_comment(comment_text: str) -> Dict[str,...|
|`_strip_comment_delimiters`|fn|priv|100-128|def _strip_comment_delimiters(text: str) -> str|
|`_normalize_whitespace`|fn|priv|129-154|def _normalize_whitespace(text: str) -> str|
|`format_doxygen_fields_as_markdown`|fn|pub|155-173|def format_doxygen_fields_as_markdown(doxygen_fields: Dic...|


---

# find_constructs.py | Python | 394L | 12 symbols | 7 imports | 19 comments
> Path: `src/usereq/find_constructs.py`
- @brief Find and extract specific constructs from source files.
- @details Filters source code constructs (CLASS, FUNCTION, etc.) by type tag and name regex pattern, generating markdown output with complete code extracts.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import os
import re
import sys
from .doxygen_parser import format_doxygen_fields_as_markdown, parse_doxygen_comment
from .source_analyzer import SourceAnalyzer
from .compress import compress_source, detect_language
import argparse
```

## Definitions

- var `LANGUAGE_TAGS = {` (L20)
### fn `def format_available_tags() -> str` (L44-57)
- @brief Generate formatted list of available TAGs per language.
- @details Iterates LANGUAGE_TAGS dictionary, formats each entry as "- Language: TAG1, TAG2, ..." with language capitalized and tags alphabetically sorted and comma-separated.
- @return Multi-line string listing each language with its supported TAGs.

### fn `def parse_tag_filter(tag_string: str) -> set[str]` (L58-66)
- @brief Parse pipe-separated tag filter into a normalized set.
- @details Splits the input string by pipe character `|` and strips whitespace from each component.
- @param tag_string Raw tag filter string (e.g., "CLASS|FUNCTION").
- @return Set of uppercase tag identifiers.

### fn `def language_supports_tags(lang: str, tag_set: set[str]) -> bool` (L67-77)
- @brief Check if the language supports at least one of the requested tags.
- @details Lookups the language in `LANGUAGE_TAGS` and checks if any of `tag_set` exists in the supported tags.
- @param lang Normalized language identifier.
- @param tag_set Set of requested TAG identifiers.
- @return True if intersection is non-empty, False otherwise.

### fn `def construct_matches(element, tag_set: set[str], pattern: str) -> bool` (L78-95)
- @brief Check if a source element matches tag filter and regex pattern.
- @details Validates the element type and then applies the regex search on the element name.
- @param element SourceElement instance from analyzer.
- @param tag_set Set of requested TAG identifiers.
- @param pattern Regex pattern string to test against element name.
- @return True if element type is in tag_set and name matches pattern.

### fn `def _merge_doxygen_fields(` `priv` (L96-98)

### fn `def _extract_construct_doxygen_fields(element) -> dict[str, list[str]]` `priv` (L113-136)
- @brief Merge Doxygen fields preserving per-tag content order.
- @brief Build aggregate Doxygen fields for one construct.
- @details Appends extra field values to base field lists for matching tags and initializes missing tags. Mutates and returns base_fields.
- @details Uses canonical `element.doxygen_fields` from `SourceAnalyzer.enrich()` and merges only body comments located at construct start (first 3 lines) to retain docstring-style Doxygen blocks while preventing internal-body duplication.
- @param base_fields Canonical field dictionary to update.
- @param extra_fields Additional parsed fields to append.
- @param element SourceElement instance potentially enriched with doxygen_fields and body_comments.
- @return Updated base_fields dictionary.
- @return Dictionary tag->list preserving tag content insertion order.

### fn `def _extract_file_level_doxygen_fields(elements: list) -> dict[str, list[str]]` `priv` (L137-161)
- @brief Extract file-level Doxygen fields from the first comment containing `@file`.
- @details Scans non-inline comment elements in source order and parses the first block containing `@file` or `\\file` markers.
- @param elements SourceAnalyzer output for one source file.
- @return Parsed Doxygen fields from the file-level comment; empty dictionary if absent.

### fn `def _strip_construct_comments(` `priv` (L162-166)

### fn `def format_construct(` (L202-206)
- @brief Remove comments from extracted construct code while preserving source line mapping.
- @details Delegates comment stripping to `compress_source()` to remove inline, single-line, and multi-line comments while preserving string literals. When line numbers are enabled, remaps local compressed line indices back to absolute file line numbers using `line_start`.
- @param code_lines Raw construct code lines sliced by SourceElement line range.
- @param language Normalized language key used by the compression parser.
- @param line_start Absolute start line number of the construct in the original file.
- @param include_line_numbers If True, emit `<n>:` prefixes with absolute source line numbers.
- @return Comment-stripped construct code string.

### fn `def find_constructs_in_files(` (L244-249)
- @brief Format a single matched construct for markdown output with complete code extraction.
- @details Extracts construct code directly from source_lines using element.line_start and element.line_end indices, removes inline/single-line/multi-line comments from the extracted block, and inserts Doxygen metadata before the code fence when available.
- @param element SourceElement instance containing line range indices.
- @param source_lines Complete source file content as list of lines.
- @param include_line_numbers If True, prefix code lines with <n>: format.
- @param language Normalized source language key used for comment stripping.
- @return Formatted markdown block for the construct with complete code from line_start to line_end.

### fn `def main()` (L355-392)
- @brief Find and extract constructs matching tag filter and regex pattern from multiple files.
- @brief Execute the construct finding CLI command.
- @details Analyzes each file with SourceAnalyzer, filters elements by tag and name pattern, formats results as markdown with file headers.
- @details Parses arguments and calls find_constructs_in_files. Handles exceptions by printing errors to stderr.
- @param filepaths List of source file paths.
- @param tag_filter Pipe-separated TAG identifiers (e.g., "CLASS|FUNCTION").
- @param pattern Regex pattern for construct name matching.
- @param include_line_numbers If True (default), prefix code lines with <n>: format.
- @param verbose If True, emits progress status messages on stderr.
- @return Concatenated markdown output string.
- @return {None} Function return value.
- @throws ValueError If no files could be processed or no constructs found.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`LANGUAGE_TAGS`|var|pub|20||
|`format_available_tags`|fn|pub|44-57|def format_available_tags() -> str|
|`parse_tag_filter`|fn|pub|58-66|def parse_tag_filter(tag_string: str) -> set[str]|
|`language_supports_tags`|fn|pub|67-77|def language_supports_tags(lang: str, tag_set: set[str]) ...|
|`construct_matches`|fn|pub|78-95|def construct_matches(element, tag_set: set[str], pattern...|
|`_merge_doxygen_fields`|fn|priv|96-98|def _merge_doxygen_fields(|
|`_extract_construct_doxygen_fields`|fn|priv|113-136|def _extract_construct_doxygen_fields(element) -> dict[st...|
|`_extract_file_level_doxygen_fields`|fn|priv|137-161|def _extract_file_level_doxygen_fields(elements: list) ->...|
|`_strip_construct_comments`|fn|priv|162-166|def _strip_construct_comments(|
|`format_construct`|fn|pub|202-206|def format_construct(|
|`find_constructs_in_files`|fn|pub|244-249|def find_constructs_in_files(|
|`main`|fn|pub|355-392|def main()|


---

# generate_markdown.py | Python | 158L | 5 symbols | 4 imports | 8 comments
> Path: `src/usereq/generate_markdown.py`
- @brief Generate concatenated markdown from arbitrary source files.
- @details Analyzes each input file with source_analyzer and produces a single markdown output concatenating all results. Prints pack summary to stderr.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import os
import sys
from pathlib import Path
from .source_analyzer import SourceAnalyzer, format_markdown
```

## Definitions

- var `EXT_LANG_MAP = {` (L17)
### fn `def detect_language(filepath: str) -> str | None` (L45-54)
- @brief Extension-to-language normalization map for markdown generation."""
- @brief Detect language from file extension.
- @details Uses EXT_LANG_MAP for extension lookup (case-insensitive).
- @param filepath Path to the source file.
- @return Language identifier string or None if unknown.

### fn `def _format_output_path(filepath: str, output_base: Path | None) -> str` `priv` (L55-68)
- @brief Build the markdown-visible path for one source file.
- @details Implements the _format_output_path function behavior with deterministic control flow.
- @param filepath Absolute or relative source file path.
- @param output_base Project-home base used to relativize output paths.
- @return Original filepath when output_base is None; otherwise POSIX relative path from output_base.

### fn `def generate_markdown(` (L69-72)

### fn `def main()` (L138-156)
- @brief Analyze source files and return concatenated markdown.
- @brief Execute the standalone markdown generation CLI command.
- @details Iterates through files, detecting language, analyzing constructs, and formatting output. Disables legacy comment/exit annotation traces in rendered markdown, emitting only construct references plus Doxygen field bullets when available.
- @details Expects file paths as command-line arguments. Prints generated markdown to stdout.
- @param filepaths List of source file paths to analyze.
- @param verbose If True, emits progress status messages on stderr.
- @param output_base Project-home base used to render file paths in markdown as relative paths.
- @return Concatenated markdown string with all file analyses.
- @return {None} Function return value.
- @throws ValueError If no valid source files are found.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`EXT_LANG_MAP`|var|pub|17||
|`detect_language`|fn|pub|45-54|def detect_language(filepath: str) -> str | None|
|`_format_output_path`|fn|priv|55-68|def _format_output_path(filepath: str, output_base: Path ...|
|`generate_markdown`|fn|pub|69-72|def generate_markdown(|
|`main`|fn|pub|138-156|def main()|


---

# source_analyzer.py | Python | 2280L | 62 symbols | 11 imports | 135 comments
> Path: `src/usereq/source_analyzer.py`
- @brief Multi-language source code analyzer.
- @details Inspired by tree-sitter, this module analyzes source files across multiple programming languages, extracting: - Definitions of functions, methods, classes, structs, enums, traits, interfaces, modules, components and other constructs - Comments (single-line and multi-line) in language-specific syntax - A structured listing of the entire file with line number prefixes
@author GitHub Copilot
@version 0.0.70

## Imports
```
import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from .doxygen_parser import parse_doxygen_comment
from usereq.doxygen_parser import parse_doxygen_comment
from .doxygen_parser import format_doxygen_fields_as_markdown
from usereq.doxygen_parser import format_doxygen_fields_as_markdown
```

## Definitions

### class `class ElementType(Enum)` : Enum (L24-54)
- @brief Element types recognized in source code.
- @details Enumeration of all supported syntactic constructs across languages.
- var `FUNCTION = auto()` (L28)
  - @brief Element types recognized in source code.
  - @details Enumeration of all supported syntactic constructs across languages.
- var `METHOD = auto()` (L29)
- var `CLASS = auto()` (L30)
- var `STRUCT = auto()` (L31)
- var `ENUM = auto()` (L32)
- var `TRAIT = auto()` (L33)
- var `INTERFACE = auto()` (L34)
- var `MODULE = auto()` (L35)
- var `IMPL = auto()` (L36)
- var `MACRO = auto()` (L37)
- var `CONSTANT = auto()` (L38)
- var `VARIABLE = auto()` (L39)
- var `TYPE_ALIAS = auto()` (L40)
- var `IMPORT = auto()` (L41)
- var `DECORATOR = auto()` (L42)
- var `COMMENT_SINGLE = auto()` (L43)
- var `COMMENT_MULTI = auto()` (L44)
- var `COMPONENT = auto()` (L45)
- var `PROTOCOL = auto()` (L46)
- var `EXTENSION = auto()` (L47)
- var `UNION = auto()` (L48)
- var `NAMESPACE = auto()` (L49)
- var `PROPERTY = auto()` (L50)
- var `SIGNAL = auto()` (L51)
- var `TYPEDEF = auto()` (L52)

### class `class SourceElement` `@dataclass` (L56-116)
- @brief Element found in source file.
- @details Data class representing a single extracted code construct with its metadata.
- fn `def type_label(self) -> str` (L82-116)
  - @brief Return the normalized printable label for element_type.
  - @details Maps internal ElementType enum to a string representation for reporting.
  - @return Stable uppercase label used in markdown rendering output.

### class `class LanguageSpec` `@dataclass` (L118-129)
- @brief Language recognition pattern specification.
- @details Holds regex patterns and configuration for parsing a specific programming language.

### fn `def build_language_specs() -> dict` (L130-329)
- @brief Build specifications for all supported languages.
- @details Implements the build_language_specs function behavior with deterministic control flow.
- @return {dict} Function return value.

### class `class SourceAnalyzer` (L686-885)
- @brief Multi-language source file analyzer.
- @details Analyzes a source file identifying definitions, comments and constructs for the specified language. Produces structured output with line numbers, inspired by tree-sitter tags functionality.
- fn `def __init__(self)` `priv` (L691-698)
  - @brief Multi-language source file analyzer.
  - @brief Initialize analyzer state with language specifications.
  - @details Analyzes a source file identifying definitions, comments and constructs for the specified language. Produces structured output with line numbers, inspired by tree-sitter tags functionality.
  - @details Implements the __init__ function behavior with deterministic control flow.
  - @return {None} Function return value.
- fn `def get_supported_languages(self) -> list` (L699-712)
  - @brief Return list of supported languages (without aliases).
  - @details Implements the get_supported_languages function behavior with deterministic control flow.
  - @return Sorted list of unique language identifiers.
- fn `def analyze(self, filepath: str, language: str) -> list` (L713-868)
  - @brief Analyze a source file and return the list of SourceElement found.
  - @details Reads file content, detects single/multi-line comments, and matches regex patterns for definitions.
  - @param filepath Path to the source file.
  - @param language Language identifier.
  - @return List of SourceElement instances.
  - @throws ValueError If language is not supported.

### fn `def _in_string_context(self, line: str, pos: int, spec: LanguageSpec) -> bool` `priv` (L869-904)
- @brief Check if position pos is inside a string literal.
- @details Implements the _in_string_context function behavior with deterministic control flow.
- @param line The line of code.
- @param pos The column index.
- @param spec The LanguageSpec instance.
- @return True if pos is within a string.

### fn `def _find_comment(self, line: str, spec: LanguageSpec) -> Optional[int]` `priv` (L905-944)
- @brief Find position of single-line comment, ignoring strings.
- @details Implements the _find_comment function behavior with deterministic control flow.
- @param line The line of code.
- @param spec The LanguageSpec instance.
- @return Column index of comment start, or None.

### fn `def _find_block_end(self, lines: list, start_idx: int,` `priv` (L945-1023)
- @brief Find the end of a block (function, class, struct, etc.).
- @details Returns the index (1-based) of the final line of the block. Limits search for performance.
- @param lines List of all file lines.
- @param start_idx Index of the start line.
- @param language Language identifier.
- @param first_line Content of the start line.
- @return 1-based index of the end line.

### fn `def enrich(self, elements: list, language: str,` (L1026-1046)
- @brief Enrich elements with signatures, hierarchy, visibility, inheritance.
- @details Call after analyze() to add metadata for LLM-optimized markdown output. Modifies elements in-place and returns them. If filepath is provided, also extracts body comments and exit points.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @param filepath Input parameter `filepath`.
- @return {list} Function return value.

### fn `def _clean_names(self, elements: list, language: str)` `priv` (L1047-1075)
- @brief Extract clean identifiers from name fields.
- @details Due to regex group nesting, name may contain the full match expression (e.g. 'class MyClass:' instead of 'MyClass'). This method extracts the actual identifier.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @return {None} Function return value.

### fn `def _extract_signatures(self, elements: list, language: str)` `priv` (L1076-1096)
- @brief Extract clean signatures from element extracts.
- @details Implements the _extract_signatures function behavior with deterministic control flow.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @return {None} Function return value.

### fn `def _detect_hierarchy(self, elements: list)` `priv` (L1097-1133)
- @brief Detect parent-child relationships between elements.
- @details Containers (class, struct, module, etc.) remain at depth=0. Non-container elements inside containers get depth=1 and parent_name set.
- @param elements Input parameter `elements`.
- @return {None} Function return value.

### fn `def _extract_visibility(self, elements: list, language: str)` `priv` (L1134-1151)
- @brief Extract visibility/access modifiers from elements.
- @details Implements the _extract_visibility function behavior with deterministic control flow.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @return {None} Function return value.

### fn `def _parse_visibility(self, sig: str, name: Optional[str],` `priv` (L1152-1203)
- @brief Parse visibility modifier from a signature line.
- @details Implements the _parse_visibility function behavior with deterministic control flow.
- @param sig Input parameter `sig`.
- @param name Input parameter `name`.
- @param language Input parameter `language`.
- @return {Optional[str]} Function return value.

### fn `def _extract_inheritance(self, elements: list, language: str)` `priv` (L1204-1220)
- @brief Extract inheritance/implementation info from class-like elements.
- @details Implements the _extract_inheritance function behavior with deterministic control flow.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @return {None} Function return value.

### fn `def _parse_inheritance(self, first_line: str,` `priv` (L1221-1255)
- @brief Parse inheritance info from a class/struct declaration line.
- @details Implements the _parse_inheritance function behavior with deterministic control flow.
- @param first_line Input parameter `first_line`.
- @param language Input parameter `language`.
- @return {Optional[str]} Function return value.

### fn `def _extract_body_annotations(self, elements: list,` `priv` (L1263-1391)
- @brief Extract comments and exit points from within function/class bodies.
- @details Reads the source file and scans each definition's line range for: - Single-line comments (# or // etc.) - Multi-line comments (docstrings, /* */ blocks) - Exit points (return, yield, raise, throw, panic!, sys.exit) Populates body_comments and exit_points on each element.
- @param elements Input parameter `elements`.
- @param language Input parameter `language`.
- @param filepath Input parameter `filepath`.
- @return {None} Function return value.

### fn `def _extract_doxygen_fields(self, elements: list)` `priv` (L1392-1540)
- @brief Extract Doxygen tag fields from associated documentation comments.
- @details For each non-comment element, resolves the nearest associated documentation comment using language-agnostic adjacency rules: same-line postfix comment (`//!<`, `#!<`, `/**<`), nearest preceding standalone comment block within two lines, or nearest following postfix standalone comment within two lines. When the nearest preceding match is a standalone comment, contiguous preceding standalone comments are merged into one logical block before parsing so multi-line tag sets split across `#`/`//` lines are preserved. Parsed fields are stored in element.doxygen_fields.
- @param elements Input parameter `elements`.
- @return {None} Function return value.

### fn `def _is_file_level_comment(comment) -> bool` `priv` (L1413-1423)
- @brief Extract Doxygen tag fields from associated documentation comments.
- @brief Detect whether a comment block is file-scoped Doxygen metadata.
- @details For each non-comment element, resolves the nearest associated documentation comment using language-agnostic adjacency rules: same-line postfix comment (`//!<`, `#!<`, `/**<`), nearest preceding standalone comment block within two lines, or nearest following postfix standalone comment within two lines. When the nearest preceding match is a standalone comment, contiguous preceding standalone comments are merged into one logical block before parsing so multi-line tag sets split across `#`/`//` lines are preserved. Parsed fields are stored in element.doxygen_fields.
- @details Resolves canonical text from `comment_source` or fallback `extract` and checks for a standalone `@file` or `\\file` tag token; empty comment payloads are treated as non file-level.
- @param elements Input parameter `elements`.
- @param comment {SourceElement} Candidate comment element.
- @return {None} Function return value.
- @return {bool} True when the comment declares file-level metadata and must not be bound to a symbol.

### fn `def _has_blocking_element(comment) -> bool` `priv` (L1447-1468)
- @brief Validate that no non-comment construct exists between comment and target symbol.
- @details Evaluates direct-span and overlap-span blockers in `non_comment_elements`; returns True when any unrelated construct occupies the interval between `comment.line_end` and `elem.line_start`.
- @param comment {SourceElement} Candidate preceding comment element.
- @return {bool} True when association must be rejected due to an intervening non-comment element.

### fn `def _is_postfix_doxygen_comment(comment_text: str) -> bool` `priv` `@staticmethod` (L1542-1551)
- @brief Detect whether a comment uses postfix Doxygen association markers.
- @details Returns True for comment prefixes that explicitly bind documentation to a preceding construct, including variants like `#!<`, `//!<`, `///<`, `/*!<`, and `/**<`.
- @param comment_text Raw extracted comment text.
- @return True when the comment text starts with a supported postfix marker; otherwise False.

### fn `def _clean_comment_line(text: str, spec) -> str` `priv` `@staticmethod` (L1553-1569)
- @brief Strip comment markers from a single line of comment text.
- @details Implements the _clean_comment_line function behavior with deterministic control flow.
- @param text Input parameter `text`.
- @param spec Input parameter `spec`.
- @return {str} Function return value.

### fn `def _md_loc(elem) -> str` `priv` (L1570-1581)
- @brief Format element location compactly for markdown.
- @details Implements the _md_loc function behavior with deterministic control flow.
- @param elem Input parameter `elem`.
- @return {str} Function return value.

### fn `def _md_kind(elem) -> str` `priv` (L1582-1613)
- @brief Short kind label for markdown output.
- @details Implements the _md_kind function behavior with deterministic control flow.
- @param elem Input parameter `elem`.
- @return {str} Function return value.

### fn `def _extract_comment_text(comment_elem, max_length: int = 0) -> str` `priv` (L1614-1640)
- @brief Extract clean text content from a comment element.
- @details Args: comment_elem: SourceElement with comment content max_length: if >0, truncate to this length. 0 = no truncation.
- @param comment_elem Input parameter `comment_elem`.
- @param max_length Input parameter `max_length`.
- @return {str} Function return value.

### fn `def _extract_comment_lines(comment_elem) -> list` `priv` (L1641-1661)
- @brief Extract clean text lines from a multi-line comment (preserving structure).
- @details Implements the _extract_comment_lines function behavior with deterministic control flow.
- @param comment_elem Input parameter `comment_elem`.
- @return {list} Function return value.

### fn `def _build_comment_maps(elements: list) -> tuple` `priv` (L1662-1725)
- @brief Build maps that associate comments with their adjacent definitions.
- @details Returns: - doc_for_def: dict mapping def line_start -> list of comment texts (comments immediately preceding a definition) - standalone_comments: list of comment elements not attached to defs - file_description: text from the first comment block (file-level docs)
- @param elements Input parameter `elements`.
- @return {tuple} Function return value.

### fn `def _render_body_annotations(out: list, elem, indent: str = "",` `priv` (L1726-1783)
- @brief Render body comments and exit points for a definition element.
- @details Merges body_comments and exit_points in line-number order, outputting each as L<N>> text. When both a comment and exit point exist on the same line, merges them as: L<N>> `return` — comment text. Skips annotations within exclude_ranges.
- @param out Input parameter `out`.
- @param elem Input parameter `elem`.
- @param indent Input parameter `indent`.
- @param exclude_ranges Input parameter `exclude_ranges`.
- @return {None} Function return value.

### fn `def _merge_doxygen_fields(` `priv` (L1784-1786)

### fn `def _collect_element_doxygen_fields(elem) -> dict[str, list[str]]` `priv` (L1802-1825)
- @brief Merge Doxygen field dictionaries preserving per-tag value order.
- @brief Aggregate construct Doxygen fields from associated and body comments.
- @details Implements the _merge_doxygen_fields function behavior with deterministic control flow.
- @details Uses canonical `elem.doxygen_fields` from `SourceAnalyzer.enrich()` and merges only body comments located at construct start (first 3 lines) to retain docstring-style Doxygen blocks while avoiding internal-body duplication.
- @param base_fields Destination dictionary mutated in place.
- @param extra_fields Source dictionary containing additional tag values.
- @param elem SourceElement containing optional `doxygen_fields` and `body_comments`.
- @return Updated destination dictionary.
- @return Dictionary of normalized Doxygen tags to ordered value lists.

### fn `def _collect_file_level_doxygen_fields(elements: list) -> dict[str, list[str]]` `priv` (L1826-1850)
- @brief Extract file-level Doxygen fields from the first `@file` documentation block.
- @details Scans non-inline comment elements in source order and selects the first comment containing `@file` or `\\file`, then parses the full comment text through `parse_doxygen_comment()`.
- @param elements Parsed SourceElement list for one source file.
- @return Parsed Doxygen fields from the file-level documentation block; empty dictionary if not found.

### fn `def format_markdown(` (L1851-1857)

### fn `def main()` (L2151-2278)
- @brief Execute the standalone source analyzer CLI command.
- @details Implements the main function behavior with deterministic control flow.
- @return {None} Function return value.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`ElementType`|class|pub|24-54|class ElementType(Enum)|
|`ElementType.FUNCTION`|var|pub|28||
|`ElementType.METHOD`|var|pub|29||
|`ElementType.CLASS`|var|pub|30||
|`ElementType.STRUCT`|var|pub|31||
|`ElementType.ENUM`|var|pub|32||
|`ElementType.TRAIT`|var|pub|33||
|`ElementType.INTERFACE`|var|pub|34||
|`ElementType.MODULE`|var|pub|35||
|`ElementType.IMPL`|var|pub|36||
|`ElementType.MACRO`|var|pub|37||
|`ElementType.CONSTANT`|var|pub|38||
|`ElementType.VARIABLE`|var|pub|39||
|`ElementType.TYPE_ALIAS`|var|pub|40||
|`ElementType.IMPORT`|var|pub|41||
|`ElementType.DECORATOR`|var|pub|42||
|`ElementType.COMMENT_SINGLE`|var|pub|43||
|`ElementType.COMMENT_MULTI`|var|pub|44||
|`ElementType.COMPONENT`|var|pub|45||
|`ElementType.PROTOCOL`|var|pub|46||
|`ElementType.EXTENSION`|var|pub|47||
|`ElementType.UNION`|var|pub|48||
|`ElementType.NAMESPACE`|var|pub|49||
|`ElementType.PROPERTY`|var|pub|50||
|`ElementType.SIGNAL`|var|pub|51||
|`ElementType.TYPEDEF`|var|pub|52||
|`SourceElement`|class|pub|56-116|class SourceElement|
|`SourceElement.type_label`|fn|pub|82-116|def type_label(self) -> str|
|`LanguageSpec`|class|pub|118-129|class LanguageSpec|
|`build_language_specs`|fn|pub|130-329|def build_language_specs() -> dict|
|`SourceAnalyzer`|class|pub|686-885|class SourceAnalyzer|
|`SourceAnalyzer.__init__`|fn|priv|691-698|def __init__(self)|
|`SourceAnalyzer.get_supported_languages`|fn|pub|699-712|def get_supported_languages(self) -> list|
|`SourceAnalyzer.analyze`|fn|pub|713-868|def analyze(self, filepath: str, language: str) -> list|
|`_in_string_context`|fn|priv|869-904|def _in_string_context(self, line: str, pos: int, spec: L...|
|`_find_comment`|fn|priv|905-944|def _find_comment(self, line: str, spec: LanguageSpec) ->...|
|`_find_block_end`|fn|priv|945-1023|def _find_block_end(self, lines: list, start_idx: int,|
|`enrich`|fn|pub|1026-1046|def enrich(self, elements: list, language: str,|
|`_clean_names`|fn|priv|1047-1075|def _clean_names(self, elements: list, language: str)|
|`_extract_signatures`|fn|priv|1076-1096|def _extract_signatures(self, elements: list, language: str)|
|`_detect_hierarchy`|fn|priv|1097-1133|def _detect_hierarchy(self, elements: list)|
|`_extract_visibility`|fn|priv|1134-1151|def _extract_visibility(self, elements: list, language: str)|
|`_parse_visibility`|fn|priv|1152-1203|def _parse_visibility(self, sig: str, name: Optional[str],|
|`_extract_inheritance`|fn|priv|1204-1220|def _extract_inheritance(self, elements: list, language: ...|
|`_parse_inheritance`|fn|priv|1221-1255|def _parse_inheritance(self, first_line: str,|
|`_extract_body_annotations`|fn|priv|1263-1391|def _extract_body_annotations(self, elements: list,|
|`_extract_doxygen_fields`|fn|priv|1392-1540|def _extract_doxygen_fields(self, elements: list)|
|`_is_file_level_comment`|fn|priv|1413-1423|def _is_file_level_comment(comment) -> bool|
|`_has_blocking_element`|fn|priv|1447-1468|def _has_blocking_element(comment) -> bool|
|`_is_postfix_doxygen_comment`|fn|priv|1542-1551|def _is_postfix_doxygen_comment(comment_text: str) -> bool|
|`_clean_comment_line`|fn|priv|1553-1569|def _clean_comment_line(text: str, spec) -> str|
|`_md_loc`|fn|priv|1570-1581|def _md_loc(elem) -> str|
|`_md_kind`|fn|priv|1582-1613|def _md_kind(elem) -> str|
|`_extract_comment_text`|fn|priv|1614-1640|def _extract_comment_text(comment_elem, max_length: int =...|
|`_extract_comment_lines`|fn|priv|1641-1661|def _extract_comment_lines(comment_elem) -> list|
|`_build_comment_maps`|fn|priv|1662-1725|def _build_comment_maps(elements: list) -> tuple|
|`_render_body_annotations`|fn|priv|1726-1783|def _render_body_annotations(out: list, elem, indent: str...|
|`_merge_doxygen_fields`|fn|priv|1784-1786|def _merge_doxygen_fields(|
|`_collect_element_doxygen_fields`|fn|priv|1802-1825|def _collect_element_doxygen_fields(elem) -> dict[str, li...|
|`_collect_file_level_doxygen_fields`|fn|priv|1826-1850|def _collect_file_level_doxygen_fields(elements: list) ->...|
|`format_markdown`|fn|pub|1851-1857|def format_markdown(|
|`main`|fn|pub|2151-2278|def main()|


---

# static_check.py | Python | 812L | 25 symbols | 9 imports | 63 comments
> Path: `src/usereq/static_check.py`
- @brief Static code analysis dispatch module implementing Dummy/Pylance/Ruff/Command check classes.
- @details Provides a class hierarchy for running static analysis tools against resolved file lists.
Exposes `run_static_check(argv)` as the primary entry point for `--test-static-check` called
from cli.py. Also exposes `parse_enable_static_check`, `dispatch_static_check_for_file`,
`STATIC_CHECK_LANG_CANONICAL`, and `STATIC_CHECK_EXT_TO_LANG` for `--enable-static-check`,
`files-static-check` and `static-check` subcommand support.
Class hierarchy: StaticCheckBase (Dummy) -> StaticCheckPylance, StaticCheckRuff, StaticCheckCommand.
File resolution supports: explicit file paths, glob patterns (with full `**` recursive expansion),
and direct-children-only directory traversal. No custom `--recursive` flag; recursive traversal
is expressed via `**` glob syntax (e.g., `src/**/*.py`).
@author useReq
@version 0.0.72

## Imports
```
from __future__ import annotations
import glob
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence
from .cli import ReqError
```

## Definitions

### fn `def _split_csv_like_tokens(spec_rhs: str) -> list[str]` `priv` (L113-147)
- @brief Split a comma-separated SPEC right-hand side with quote-aware token boundaries.
- @details - Supported quote delimiters: single quote `'` and double quote `"`. - Commas split tokens only when parser is outside a quoted segment. - Quote delimiters are not included in output tokens. - Leading and trailing whitespace for each token is stripped.
- @param spec_rhs Text after `LANG=` in `--enable-static-check`.
- @return Token list where commas inside `'...'` or `"..."` do not split tokens.
- @see SRS-260, SRS-250

### fn `def parse_enable_static_check(spec: str) -> tuple[str, dict]` (L148-224)
- @brief Parse a single `--enable-static-check` SPEC string into a (lang, config_dict) pair.
- @details Parse steps: 1. Split on the first `=`; left side is LANG token, right side is `MODULE[,...]`. 2. Normalize LANG via `STATIC_CHECK_LANG_CANONICAL` (case-insensitive). 3. Parse right side as comma-separated tokens; first token is MODULE (case-insensitive, validated against `_CANONICAL_MODULES`). 4. For Command: next token is `cmd` (mandatory); all subsequent tokens are `params`. 5. For all other modules: all tokens after MODULE are `params`. 6. `params` key is omitted when the list is empty. 7. `cmd` key is omitted for non-Command modules. 8. Surrounding quote delimiters (`'` or `"`) are stripped from parsed tokens. Note: PARAM values containing `,` must be wrapped with `'` or `"` in SPEC.
- @param spec Raw SPEC string in the format `LANG=MODULE[,CMD[,PARAM...]]`.
- @return Tuple `(canonical_lang, config_dict)` where `config_dict` contains `"module"` and optionally `"cmd"` (Command only) and `"params"` (non-empty list only).
- @throws ReqError If `=` separator is absent, language is unknown, or module is unknown.
- @see SRS-260, SRS-248, SRS-249, SRS-250

### fn `def dispatch_static_check_for_file(` (L229-234)

### fn `def _resolve_files(inputs: Sequence[str]) -> List[str]` `priv` (L293-335)
- @brief Resolve a mixed list of paths, glob patterns, and directories into regular files.
- @details Resolution order per element: 1. If the element contains a glob wildcard character (`*`, `?`, `[`) expand via `glob.glob(entry, recursive=True)`, enabling full `**` recursive expansion (e.g., `src/**/*.py` matches all `.py` files under `src/` at any depth). 2. If the element is an existing directory, iterate direct children only (flat traversal). 3. Otherwise treat as a literal file path; include if it is a regular file. Symlinks to regular files are included. Non-existent paths that do not match a glob produce a warning on stderr and are skipped.
- @param inputs Sequence of raw path strings (file, directory, or glob pattern).
- @return Sorted deduplicated list of resolved absolute file paths (regular files only).

### class `class StaticCheckBase` (L340-469)
- @brief Dummy static-check class; base of the static analysis class hierarchy.
- @details Iterates over resolved input files and emits a per-file header line plus `Result: OK`. Subclasses override `_check_file` to provide tool-specific logic. File resolution is delegated to `_resolve_files`. When `fail_only` is True, passing files produce no output (SRS-241, SRS-253, SRS-256).
- fn `def __init__(` `priv` (L352-357)
  - @brief Dummy static-check class; base of the static analysis class hierarchy.
  - @details Iterates over resolved input files and emits a per-file header line plus `Result: OK`.
Subclasses override `_check_file` to provide tool-specific logic.
File resolution is delegated to `_resolve_files`.
When `fail_only` is True, passing files produce no output (SRS-241, SRS-253, SRS-256).
- fn `def is_available(self) -> tuple[bool, str]` (L377-386)
  - @brief Probe checker availability before execution.
  - @details Base implementation (Dummy): always available. Subclasses override to verify tool module or binary availability (SRS-427).
  - @return {tuple[bool, str]} Tuple `(available, reason)`; `(True, "")` when available.
  - @satisfies SRS-427
- fn `def run(self) -> int` (L387-429)
  - @brief Execute the static check for all resolved files.
  - @details If the resolved file list is empty a warning is printed to stderr and 0 is returned. Before any file is checked the SRS-427 pre-flight availability probe runs; when the checker is unavailable every file emits header, `Result: FAIL`, English evidence identifying the missing checker or binary, and one trailing blank line in both `fail_only` modes, the overall exit code is 1, and no exception is raised (SRS-428). For each file `_check_file` is called; the overall return code is the maximum of all per-file return codes (0 = all OK, 1 = at least one FAIL). When `fail_only` is True, trailing blank separator lines are emitted only for failing files.
  - @return Exit code: 0 if all files pass (or file list is empty), 1 if any file fails.
  - @satisfies SRS-427, SRS-428
- fn `def _header_line(self, filepath: str) -> str` `priv` (L434-444)
  - @brief Build the per-file header line for output.
  - @details Format: `# Static-Check(<LABEL>): <filepath> [<extra_args>]`. When `extra_args` is empty the bracket section is omitted.
  - @param filepath Absolute path of the file being checked.
  - @return Formatted header string including label, filename, and extra args.
- fn `def _check_file(self, filepath: str) -> int` `priv` (L445-459)
  - @brief Perform the static analysis for a single file.
  - @details Base implementation (Dummy): always passes. When `fail_only` is False, prints the header and `Result: OK`. When `fail_only` is True, produces no output (SRS-241). Subclasses override this method to invoke external tools.
  - @param filepath Absolute path of the file to check.
  - @return 0 on pass, non-zero on failure.
- fn `def _emit_line(self, line: str) -> None` `priv` (L460-469)
  - @brief Emit one markdown output line.
  - @details Emits `line` followed by a newline.
  - @param line Line content to emit on stdout.
  - @return {None} Function return value.

### class `class StaticCheckPylance(StaticCheckBase)` : StaticCheckBase (L474-576)
- @brief Pylance static-check class; runs pyright on each resolved file via `sys.executable -m pyright`.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `pyright` via `[sys.executable, '-m', 'pyright']` subprocess using the active runtime interpreter, without requiring external PATH availability, and parse its exit code. Header label: `Pylance`. Evidence block is emitted on failure by concatenating stdout and stderr from pyright.
- @see StaticCheckBase
- @satisfies SRS-242, SRS-339, SRS-341
- var `LABEL = "Pylance"` (L486)
  - @brief Pylance static-check class; runs pyright on each resolved file via `sys.executable -m pyright`.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `pyright`
via `[sys.executable, '-m', 'pyright']` subprocess using the active runtime interpreter,
without requiring external PATH availability, and parse its exit code.
Header label: `Pylance`.
Evidence block is emitted on failure by concatenating stdout and stderr from pyright.
  - @see StaticCheckBase
  - @satisfies SRS-242, SRS-339, SRS-341
- fn `def is_available(self) -> tuple[bool, str]` (L488-503)
  - @brief Probe pyright module availability in the active interpreter.
  - @details Availability matches the `[sys.executable, '-m', 'pyright']` dispatch exactly: the module must be importable by the running interpreter (SRS-427).
  - @return {tuple[bool, str]} `(False, reason)` when `importlib.util.find_spec('pyright')` is `None`; `(True, "")` otherwise.
  - @satisfies SRS-427
- fn `def __init__(` `priv` (L504-510)
- fn `def _check_file(self, filepath: str) -> int` `priv` (L525-576)
  - @brief Initialize Pylance checker with runtime context.
  - @brief Run pyright on `filepath` via `sys.executable -m pyright` and emit OK or FAIL with evidence.
  - @details Stores runtime context for uv-first pyright invocation. No `.venv` probing is used.
  - @details Invokes `[sys.executable, '-m', 'pyright', '--pythonpath', sys.executable, <filepath>, <extra_args>...]` to use the active runtime interpreter without requiring external PATH availability or project `.venv` detection. No `--extra-path` argument is passed. Captures combined stdout+stderr. When `fail_only` is False: prints header, then `Result: OK` or `Result: FAIL` with evidence. When `fail_only` is True: on pass produces no output; on fail emits header, FAIL, evidence (SRS-242).
  - @param inputs Raw path/pattern/directory entries from CLI.
  - @param extra_args Additional CLI arguments forwarded to pyright.
  - @param fail_only When True, suppress all stdout output for passing checks.
  - @param project_base Absolute project root available as runtime context.
  - @param filepath Absolute path of the file to analyse with pyright.
  - @return {None} Function return value.
  - @return 0 when pyright exits 0, 1 otherwise.
  - @exception ReqError Not raised; subprocess errors are surfaced as FAIL evidence.
  - @satisfies SRS-242, SRS-339, SRS-341
  - @satisfies SRS-242, SRS-339, SRS-341

### class `class StaticCheckRuff(StaticCheckBase)` : StaticCheckBase (L581-652)
- @brief Ruff static-check class; runs `ruff check` on each resolved file via `sys.executable -m ruff`.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `ruff check` via `[sys.executable, '-m', 'ruff', 'check']` subprocess using the package-installed ruff module, without requiring external PATH availability, and parse its exit code. Header label: `Ruff`. Evidence block is emitted on failure by concatenating stdout and stderr from ruff.
- @see StaticCheckBase
- @satisfies SRS-243, SRS-339
- var `LABEL = "Ruff"` (L593)
  - @brief Ruff static-check class; runs `ruff check` on each resolved file via `sys.executable -m ruff`.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `ruff check`
via `[sys.executable, '-m', 'ruff', 'check']` subprocess using the package-installed ruff module,
without requiring external PATH availability, and parse its exit code.
Header label: `Ruff`.
Evidence block is emitted on failure by concatenating stdout and stderr from ruff.
  - @see StaticCheckBase
  - @satisfies SRS-243, SRS-339
- fn `def is_available(self) -> tuple[bool, str]` (L595-610)
  - @brief Probe ruff module availability in the active interpreter.
  - @details Availability matches the `[sys.executable, '-m', 'ruff']` dispatch exactly: the module must be importable by the running interpreter (SRS-427).
  - @return {tuple[bool, str]} `(False, reason)` when `importlib.util.find_spec('ruff')` is `None`; `(True, "")` otherwise.
  - @satisfies SRS-427
- fn `def _check_file(self, filepath: str) -> int` `priv` (L611-652)
  - @brief Run `ruff check` on `filepath` via `sys.executable -m ruff` and emit OK or FAIL with evidence.
  - @details Invokes `[sys.executable, '-m', 'ruff', 'check', <filepath>, <extra_args>...]` to use the package-installed ruff module without requiring external PATH availability. Captures combined stdout+stderr. When `fail_only` is False: prints header, then `Result: OK` or `Result: FAIL` with evidence. When `fail_only` is True: on pass produces no output; on fail emits header, FAIL, evidence (SRS-243).
  - @param filepath Absolute path of the file to analyse with ruff.
  - @return 0 when ruff exits 0, 1 otherwise.
  - @exception ReqError Not raised; subprocess errors are surfaced as FAIL evidence.
  - @satisfies SRS-243, SRS-339

### class `class StaticCheckCommand(StaticCheckBase)` : StaticCheckBase (L657-743)
- @brief Command static-check class; runs an arbitrary external command on each resolved file.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke the user-supplied `cmd` as a subprocess. Header label: `Command[<cmd>]`. `cmd` availability is resolved at execution time by the SRS-427 pre-flight via `shutil.which`; an unavailable `cmd` yields a per-file `Result: FAIL` outcome with English evidence and execution continues (SRS-428); the constructor does not raise.
- @see StaticCheckBase
- @satisfies SRS-427, SRS-428
- fn `def __init__(` `priv` (L670-676)
  - @brief Command static-check class; runs an arbitrary external command on each resolved file.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke the user-supplied
`cmd` as a subprocess.
Header label: `Command[<cmd>]`.
`cmd` availability is resolved at execution time by the SRS-427 pre-flight via
`shutil.which`; an unavailable `cmd` yields a per-file `Result: FAIL` outcome with
English evidence and execution continues (SRS-428); the constructor does not raise.
  - @see StaticCheckBase
  - @satisfies SRS-427, SRS-428
- fn `def is_available(self) -> tuple[bool, str]` (L691-703)
  - @brief Initialize the command checker.
  - @brief Probe the external command binary on PATH.
  - @details Stores `cmd` and sets `LABEL` dynamically to `Command[<cmd>]`.
  - @details Availability of the checker binary is required before any subprocess dispatch (SRS-427); unavailability is reported as FAIL evidence without raising (SRS-428).
  - @param cmd External command name (availability resolved by the SRS-427 pre-flight).
  - @param inputs Raw path/pattern/directory entries from CLI.
  - @param extra_args Additional CLI arguments forwarded to the external command.
  - @param fail_only When True, suppress all stdout output for passing checks (SRS-244).
  - @return {None} Function return value.
  - @return {tuple[bool, str]} `(False, reason)` when `shutil.which(self._cmd)` is `None`; `(True, "")` otherwise.
  - @satisfies SRS-427, SRS-428
- fn `def _check_file(self, filepath: str) -> int` `priv` (L704-743)
  - @brief Run the external command on `filepath` and emit OK or FAIL with evidence.
  - @details Invokes `<cmd> [extra_args...] <filepath>`. Captures combined stdout+stderr. When `fail_only` is False: prints header, then `Result: OK` or `Result: FAIL` with evidence. When `fail_only` is True: on pass produces no output; on fail emits header, FAIL, evidence (SRS-244).
  - @param filepath Absolute path of the file to analyse.
  - @return 0 when the command exits 0, 1 otherwise.
  - @satisfies SRS-244, SRS-253, SRS-256

### fn `def run_static_check(argv: Sequence[str]) -> int` (L748-813)
- @brief Parse `--test-static-check` sub-argv and dispatch to the appropriate checker class.
- @details Expected argument format: - `dummy [FILES...]` - `pylance [FILES...]` - `ruff [FILES...]` - `command <cmd> [FILES...]` No custom `--recursive` flag is parsed; recursive traversal is expressed via `**` glob patterns in `[FILES]` (e.g., `src/**/*.py`). For `command`, the first token after `command` is treated as `<cmd>`. All remaining tokens (after subcommand and optional cmd) are treated as FILES. Dispatches to: - `dummy` -> `StaticCheckBase` - `pylance` -> `StaticCheckPylance` - `ruff` -> `StaticCheckRuff` - `command` -> `StaticCheckCommand`
- @param argv Remaining argument tokens after `--test-static-check` (i.e. [subcommand, ...]).
- @return Process exit code from the selected checker's `run()` method.
- @throws ReqError If subcommand is missing, unknown, or `command` subcommand is missing `cmd`.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`_split_csv_like_tokens`|fn|priv|113-147|def _split_csv_like_tokens(spec_rhs: str) -> list[str]|
|`parse_enable_static_check`|fn|pub|148-224|def parse_enable_static_check(spec: str) -> tuple[str, dict]|
|`dispatch_static_check_for_file`|fn|pub|229-234|def dispatch_static_check_for_file(|
|`_resolve_files`|fn|priv|293-335|def _resolve_files(inputs: Sequence[str]) -> List[str]|
|`StaticCheckBase`|class|pub|340-469|class StaticCheckBase|
|`StaticCheckBase.__init__`|fn|priv|352-357|def __init__(|
|`StaticCheckBase.is_available`|fn|pub|377-386|def is_available(self) -> tuple[bool, str]|
|`StaticCheckBase.run`|fn|pub|387-429|def run(self) -> int|
|`StaticCheckBase._header_line`|fn|priv|434-444|def _header_line(self, filepath: str) -> str|
|`StaticCheckBase._check_file`|fn|priv|445-459|def _check_file(self, filepath: str) -> int|
|`StaticCheckBase._emit_line`|fn|priv|460-469|def _emit_line(self, line: str) -> None|
|`StaticCheckPylance`|class|pub|474-576|class StaticCheckPylance(StaticCheckBase)|
|`StaticCheckPylance.LABEL`|var|pub|486||
|`StaticCheckPylance.is_available`|fn|pub|488-503|def is_available(self) -> tuple[bool, str]|
|`StaticCheckPylance.__init__`|fn|priv|504-510|def __init__(|
|`StaticCheckPylance._check_file`|fn|priv|525-576|def _check_file(self, filepath: str) -> int|
|`StaticCheckRuff`|class|pub|581-652|class StaticCheckRuff(StaticCheckBase)|
|`StaticCheckRuff.LABEL`|var|pub|593||
|`StaticCheckRuff.is_available`|fn|pub|595-610|def is_available(self) -> tuple[bool, str]|
|`StaticCheckRuff._check_file`|fn|priv|611-652|def _check_file(self, filepath: str) -> int|
|`StaticCheckCommand`|class|pub|657-743|class StaticCheckCommand(StaticCheckBase)|
|`StaticCheckCommand.__init__`|fn|priv|670-676|def __init__(|
|`StaticCheckCommand.is_available`|fn|pub|691-703|def is_available(self) -> tuple[bool, str]|
|`StaticCheckCommand._check_file`|fn|priv|704-743|def _check_file(self, filepath: str) -> int|
|`run_static_check`|fn|pub|748-813|def run_static_check(argv: Sequence[str]) -> int|


---

# token_counter.py | Python | 123L | 7 symbols | 2 imports | 8 comments
> Path: `src/usereq/token_counter.py`
- @brief Token and character counting for generated output.
- @details Uses tiktoken for accurate token counting compatible with OpenAI/Claude models.
@author GitHub Copilot
@version 0.0.70

## Imports
```
import os
import tiktoken  # pyright: ignore[reportMissingImports]
```

## Definitions

### class `class TokenCounter` (L14-49)
- @brief Count tokens using tiktoken encoding (cl100k_base by default).
- @details Wrapper around tiktoken encoding to simplify token counting operations.
- fn `def __init__(self, encoding_name: str = "cl100k_base")` `priv` (L19-27)
  - @brief Count tokens using tiktoken encoding (cl100k_base by default).
  - @brief Initialize token counter with a specific tiktoken encoding.
  - @details Wrapper around tiktoken encoding to simplify token counting operations.
  - @details Implements the __init__ function behavior with deterministic control flow.
  - @param encoding_name Name of tiktoken encoding used for tokenization.
  - @return {None} Function return value.
- fn `def count_tokens(self, content: str) -> int` (L28-38)
  - @brief Count tokens in content string.
  - @details Uses `disallowed_special=()` to allow special tokens in input without raising errors. Returns 0 on failure.
  - @param content The text content to tokenize.
  - @return Integer count of tokens.
- fn `def count_chars(content: str) -> int` (L40-49)
  - @brief Count characters in content string.
  - @details Implements the count_chars function behavior with deterministic control flow.
  - @param content The text string.
  - @return Integer count of characters.

### fn `def count_file_metrics(content: str,` (L50-65)
- @brief Count tokens and chars for a content string.
- @details Implements the count_file_metrics function behavior with deterministic control flow.
- @param content The text content to measure.
- @param encoding_name The tiktoken encoding name (default: "cl100k_base").
- @return Dictionary with keys 'tokens' (int) and 'chars' (int).

### fn `def count_files_metrics(file_paths: list,` (L66-94)
- @brief Count tokens and chars for a list of files.
- @details Iterates through files, reading content and counting metrics. Gracefully handles read errors.
- @param file_paths List of file paths to process.
- @param encoding_name The tiktoken encoding name.
- @return List of dictionaries, each containing 'file', 'tokens', 'chars', and optionally 'error'.

### fn `def format_pack_summary(results: list) -> str` (L95-124)
- @brief Format a pack summary string from a list of file metrics.
- @details Generates a human-readable report including icons, per-file stats, and aggregate totals.
- @param results List of metrics dictionaries from count_files_metrics().
- @return Formatted summary string with per-file details and totals.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`TokenCounter`|class|pub|14-49|class TokenCounter|
|`TokenCounter.__init__`|fn|priv|19-27|def __init__(self, encoding_name: str = "cl100k_base")|
|`TokenCounter.count_tokens`|fn|pub|28-38|def count_tokens(self, content: str) -> int|
|`TokenCounter.count_chars`|fn|pub|40-49|def count_chars(content: str) -> int|
|`count_file_metrics`|fn|pub|50-65|def count_file_metrics(content: str,|
|`count_files_metrics`|fn|pub|66-94|def count_files_metrics(file_paths: list,|
|`format_pack_summary`|fn|pub|95-124|def format_pack_summary(results: list) -> str|

