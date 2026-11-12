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
        ├── config_cli.py
        ├── config_schema.py
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

# cli.py | Python | 4546L | 170 symbols | 35 imports | 219 comments
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
from . import config_cli
from .config_schema import (
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

- var `REPO_ROOT = Path(__file__).resolve().parents[2]` (L41)
- var `RESOURCE_ROOT = Path(os.path.abspath(__file__)).parent / "resources"` (L44)
- @brief The absolute path to the repository root."""
- var `VERBOSE = False` (L47)
- @brief The absolute lexical path of the packaged resources directory; never resolves symbolic links (SRS-505)."""
- var `DEBUG = False` (L50)
- @brief Whether verbose output is enabled."""
- var `REQUIREMENTS_TEMPLATE_NAME = "Requirements_Template.md"` (L53)
- @brief Whether debug output is enabled."""
- var `PERSISTED_CONFIG_KEYS = (` (L56)
- @brief Name of the packaged requirements template file."""
- var `AUTO_INSTALL_CONFIG_KEY = "auto-install"` (L66)
- @brief Canonical keys persisted in the user-global configuration file (SRS-288)."""
- var `VALID_PROVIDERS = frozenset(VALID_PROVIDER_NAMES)` (L69)
- @brief Configuration key storing the auto-install enabled flag (SRS-420)."""
- var `GLOBAL_CONFIG_DIRNAME = ".config"` (L72)
- @brief Valid provider names accepted by ``--enable PROVIDER`` and ``--disable PROVIDER`` (SRS-275, SRS-364)."""
- var `GLOBAL_CONFIG_APP_DIRNAME = "usereq"` (L75)
- @brief Root configuration directory name located under the user HOME (SRS-387)."""
- var `GLOBAL_CONFIG_FILENAME = "config.json"` (L78)
- @brief Application subdirectory name under ``~/.config`` (SRS-387)."""
### fn `def home_dir() -> Path` (L82-92)
- @brief Canonical user-global configuration JSON filename (SRS-387)."""
- @brief Resolve the user HOME directory used for user-level CLI configuration.
- @details Single indirection point over ``Path.home()`` so tests and embedders can redirect all user-level provider and configuration paths deterministically.
- @return {Path} Absolute user HOME directory path.
- @satisfies SRS-381

### fn `def get_global_config_path() -> Path` (L93-108)
- @brief Resolve the single user-global configuration file path.
- @details Builds ``~/.config/usereq/config.json`` from the effective home directory returned by :func:`home_dir`.
- @return {Path} Absolute path of the user-global configuration file.
- @satisfies SRS-387

### fn `def guidelines_dir() -> Path` (L109-121)
- @brief Resolve the packaged guidelines directory of the running installation.
- @details Composes the packaged resources root of the running installation with the non-configurable ``guidelines`` suffix so installed skills reference the resources shipped with this installation instead of any external copy (SRS-360, SRS-497); composition is lexical and never resolves symbolic links (SRS-505).
- @return {Path} Absolute path of the packaged guidelines directory.
- @satisfies SRS-360, SRS-497, SRS-505

### fn `def templates_dir() -> Path` (L122-134)
- @brief Resolve the packaged document-template directory of the running installation.
- @details Composes the packaged resources root of the running installation with the non-configurable ``templates`` suffix feeding the ``%%TEMPLATE_PATH%%`` substitution so installed skills reference the templates shipped with this installation (SRS-498); composition is lexical and never resolves symbolic links (SRS-505).
- @return {Path} Absolute path of the packaged templates directory.
- @satisfies SRS-495, SRS-498, SRS-505

### fn `def format_home_relative_path(path: Path) -> str` (L135-158)
- @brief Render an absolute path in ``~/`` home-relative form.
- @details Returns ``~`` for the HOME directory, ``~/<rel>`` with POSIX separators for any path under HOME, and the absolute string for paths outside HOME. Normalization is strictly lexical via ``os.path.abspath``: symbolic links are never resolved, so a symlinked ``~/.config`` still renders as ``~/.config/...`` and the hardcoded provider skills roots of SRS-382..SRS-386, SRS-486, and SRS-493 render verbatim (SRS-385, SRS-463). No filesystem access occurs beyond path composition. Complexity: O(1).
- @param path {Path} Absolute path to render.
- @return {str} Home-relative rendering when the path is under HOME, otherwise absolute.
- @satisfies SRS-385, SRS-402, SRS-403, SRS-463

### fn `def provider_skills_root(provider: str) -> Path` (L159-192)
- @brief Resolve the user-level skills installation root for one provider.
- @details Maps ``provider`` to its hardcoded user-level skills directory under the user HOME (antigravity -> ``~/.gemini/config/skills``, claude -> ``~/.claude/skills``, codex -> ``~/.codex/skills``, copilot -> ``~/.copilot/skills``, openclaw -> ``~/.openclaw/workspace/skills``, opencode -> ``~/.config/opencode/skills``, pi -> ``~/.pi/agent/skills``). Paths are computed lazily from :func:`home_dir` so HOME redirection stays consistent across a single process run. Skills are the only supported artifact type (SRS-381).
- @param provider {str} Provider selector from ``{antigravity, claude, codex, copilot, openclaw, opencode, pi}``.
- @return {Path} Absolute user-level skills target directory for the provider.
- @throws {ReqError} Raised when the provider defines no user-level skills root.
- @satisfies SRS-381, SRS-382, SRS-383, SRS-384, SRS-385, SRS-386, SRS-486, SRS-493

### fn `def provider_skills_path(provider: str) -> str` (L193-206)
- @brief Render the home-relative hardcoded skills root shown in the `show` Providers table.
- @details Joins the effective user HOME with the hardcoded provider skills root from :func:`provider_skills_root` (SRS-382..SRS-386, SRS-486, SRS-493) and renders the result through :func:`format_home_relative_path` as a `~/`-prefixed POSIX path. Complexity: O(1). No side effects.
- @param provider {str} Provider selector from ``{antigravity, claude, codex, copilot, openclaw, opencode, pi}``.
- @return {str} Home-relative skills installation root such as ``~/.pi/agent/skills``.
- @satisfies SRS-462, SRS-463, SRS-485

- var `INVALID_WT_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]')` (L207)
### fn `def validate_provider_name(name: str) -> str` (L211-233)
- @brief Regex matching characters invalid in both Linux and Windows directory names."""
- @brief Validate one provider name token supplied via ``--enable`` or ``--disable``.
- @details Normalizes the token to lowercase and validates membership in :data:`VALID_PROVIDERS`; unknown tokens raise a deterministic English `ReqError` payload identifying the invalid token (SRS-278, SRS-422). Complexity: O(1). No side effects.
- @param name {str} Raw provider name token as supplied on the command line or read from the persisted `"providers"` array.
- @return {str} Normalized lowercase provider name.
- @throws {ReqError} Raised with exit code 1 when the token is not a valid provider.
- @satisfies SRS-275, SRS-278, SRS-364, SRS-422

### fn `def resolve_provider_configs(` (L234-235)

- var `ANSI_BRIGHT_RED = "\033[91m"` (L258)
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
- var `ANSI_BRIGHT_GREEN = "\033[92m"` (L261)
- @brief ANSI escape prefix for bright red terminal output."""
- var `ANSI_RESET = "\033[0m"` (L264)
- @brief ANSI escape prefix for bright green terminal output."""
- var `RELEASE_CHECK_TIMEOUT_SECONDS = 2.0` (L267)
- @brief ANSI escape sequence that resets terminal style."""
- var `RELEASE_CHECK_IDLE_DELAY_SECONDS = 3600` (L270)
- @brief Hardcoded default timeout for startup release-check HTTP calls."""
- var `RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS = 86400` (L273)
- @brief Hardcoded startup release-check idle-delay in seconds."""
- var `TOOL_PROGRAM_NAME = "cli-usereq"` (L276)
- @brief Hardcoded startup release-check idle-delay in seconds for API rate limiting."""
- var `RELEASE_CHECK_PROGRAM_NAME = "usereq"` (L282)
- @brief Hardcoded uv tool requirement name matching the PyPI distribution name of this package (SRS-435).
- @details Used as the target of `uv tool install`/`uv tool uninstall` commands; it matches the
`[project].name` distribution name registered in the PyPI trusted publisher for repository
`Ogekuri/CLI-useReq` (SRS-343, SRS-344, SRS-433, SRS-435)."""
- var `GITHUB_REPOSITORY_OWNER = "Ogekuri"` (L287)
- @brief Program identifier used in release-check idle-state cache directory.
- @details Fixes the idle-state cache path to `~/.cache/usereq/check_version_idle-time.json`
independently of the PyPI distribution name `cli-usereq` (SRS-345, SRS-346)."""
- var `GITHUB_REPOSITORY_NAME = "CLI-useReq"` (L290)
- @brief Hardcoded GitHub owner used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME = ".cache"` (L293)
- @brief Hardcoded GitHub repository used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_FILENAME = "check_version_idle-time.json"` (L296)
- @brief Root cache directory name located under `$HOME`."""
- var `GITHUB_RELEASES_LATEST_URL = (` (L299)
- @brief Canonical release-check idle-state JSON filename."""
- var `GITHUB_UPGRADE_SOURCE = (` (L308)
- @brief Hardcoded GitHub API endpoint queried by `--ver`/`--version` and `--upgrade --develop` (SRS-442, SRS-451).
- @details Intermediate and test releases are published on GitHub; this endpoint resolves the
latest tagged release independently of the branch holding the tag. The default `--upgrade`
path never queries it and installs from the PyPI index (SRS-343, SRS-440)."""
- var `PYPI_PROJECT_JSON_URL = "https://pypi.org/pypi/cli-usereq/json"` (L315)
- @brief Hardcoded git source base used only by `--upgrade --develop` (alias `--dev`) installs (SRS-440, SRS-445).
- @details The uv `--from` reference appends `@<TAG>` with the raw SRS-451 release tag so the
install pins the latest tagged release regardless of the branch holding the tag (SRS-452)."""
- var `UNKNOWN_VERSION_LABEL = "unknown"` (L321)
- @brief Hardcoded PyPI JSON API endpoint for latest-version resolution (SRS-430).
- @details The startup release-check and `--ver`/`--version` read `info.version` from this
endpoint; PyPI is the sole source for version verification and default self-upgrade
(SRS-343, SRS-441, SRS-442)."""
- var `VERSION_REPORT_LABEL_WIDTH = 18` (L324)
- @brief Label printed by `--ver`/`--version` when a remote latest version cannot be fetched (SRS-442)."""
- var `FORCE_ONLINE_RELEASE_CHECK = False` (L327)
- @brief Left-justified label-field width aligning the `: <version>` column of every `--ver`/`--version` line (SRS-518)."""
### class `class ReqError(Exception)` : Exception (L331-348)
- @brief Startup-scoped override that bypasses release-check idle-state gating when enabled."""
- @brief Dedicated exception for expected CLI errors.
- @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
- fn `def __init__(self, message: str, code: int = 1) -> None` `priv` (L336-348)
  - @brief Dedicated exception for expected CLI errors.
  - @brief Initialize an expected CLI failure payload.
  - @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
  - @details Implements the __init__ function behavior with deterministic control flow.
  - @param message Human-readable error message.
  - @param code Process exit code bound to the failure category.
  - @return {None} Function return value.

### fn `def log(msg: str) -> None` (L349-358)
- @brief Prints an informational message.
- @details Implements the log function behavior with deterministic control flow.
- @param msg The message string to print.
- @return {None} Function return value.

### fn `def dlog(msg: str) -> None` (L359-369)
- @brief Prints a debug message if debugging is active.
- @details Implements the dlog function behavior with deterministic control flow.
- @param msg The debug message string to print.
- @return {None} Function return value.

### fn `def vlog(msg: str) -> None` (L370-380)
- @brief Prints a verbose message if verbose mode is active.
- @details Implements the vlog function behavior with deterministic control flow.
- @param msg The verbose message string to print.
- @return {None} Function return value.

### fn `def build_parser() -> argparse.ArgumentParser` (L381-580)
- @brief Builds the CLI argument parser.
- @details Defines all supported CLI arguments, flags, and help texts. Provider enablement is configured exclusively via the repeatable ``--enable PROVIDER`` argument, which accepts only the provider CLI name exactly like ``--disable PROVIDER`` (SRS-275, SRS-034); skills are the only supported artifact type. Every SRS-408 analysis subcommand accepts the global base arguments ``--prj-base`` and ``--git-base`` both before and after the subcommand token; ``--prj-base`` is mandatory only for the SRS-396 project-scan subcommands (enforced by ``_require_prj_base``) and ``--git-base`` is never mandatory for any SRS-408 subcommand (SRS-392, SRS-393, SRS-396, SRS-397, SRS-410). The ``--force`` auxiliary argument is accepted by ``--upgrade`` (with or without ``--develop``/``--dev``) and forces full package download and complete reinstallation (SRS-508, SRS-511).
- @return Configured ArgumentParser instance.

### fn `def parse_args(argv: Optional[list[str]] = None) -> Namespace` (L876-885)
- @brief Parses command-line arguments into a namespace.
- @details Implements the parse_args function behavior with deterministic control flow.
- @param argv List of arguments (defaults to sys.argv).
- @return Namespace containing parsed arguments.

### fn `def load_package_version() -> str` (L886-900)
- @brief Reads the package version from __init__.py.
- @details Implements the load_package_version function behavior with deterministic control flow.
- @return Version string extracted from the package.
- @throws ReqError If version cannot be determined.

### fn `def maybe_print_version(argv: list[str], pypi_latest: Optional[str] = None) -> bool` (L901-949)
- @brief Handles --ver/--version by printing installed, PyPI latest, and GitHub latest versions in aligned columns.
- @details When `--ver`/`--version` is present, prints exactly three stdout lines in order: installed version, PyPI latest version, GitHub latest version. Each line renders `<LABEL>` left-justified in :data:`VERSION_REPORT_LABEL_WIDTH` characters followed by `: <version>` so the version numbers align in one column (SRS-441, SRS-518); the labels are `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub`; fetch failures degrade to the `unknown` label without raising (SRS-442).
- @param argv Command line arguments to check.
- @param pypi_latest {Optional[str]} PyPI latest version already fetched by the startup release-check; when None, a direct PyPI JSON API fetch is attempted (SRS-441, SRS-442).
- @return {bool} True if version output was printed, False otherwise.
- @satisfies SRS-441, SRS-442, SRS-518

### fn `def _resolve_github_upgrade_tag() -> str` `priv` (L950-980)
- @brief Resolve the raw latest GitHub release tag for `--upgrade --develop` installations.
- @details Queries `GITHUB_RELEASES_LATEST_URL` through `fetch_github_latest_version(raw_tag=True)` and returns the raw `tag_name` value with the optional `v` prefix preserved so the uv `--from` reference targets an existing git tag regardless of the branch holding it (SRS-451). Maps fetch exceptions and empty payloads to one English `ReqError` so no uv process is spawned (SRS-453). Complexity: O(1). Side effects: one HTTP request.
- @return {str} Raw latest release tag, e.g. `v0.0.76`.
- @throws {ReqError} Raised with exit code 1 when the GitHub query fails or returns no tag (SRS-453).
- @satisfies SRS-451, SRS-453

### fn `def run_upgrade(use_github: bool = False, force: bool = False) -> None` (L981-1041)
- @brief Executes the upgrade using uv from the PyPI index or the latest GitHub release tag.
- @details Builds the standard `uv tool install cli-usereq` command against the PyPI index by default (SRS-343); without `force` no forcing option is passed so the standard install/update process runs unchanged, and `--upgrade` is appended so uv resolves and installs the latest PyPI version instead of reusing the already-installed tool version. When `force` is True the command becomes the forced reinstallation form `uv tool install cli-usereq --force --reinstall --refresh` (SRS-509). When `use_github` is True, resolves the latest GitHub release tag through `_resolve_github_upgrade_tag()` (SRS-451) and appends `--from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` regardless of the branch holding that tag (SRS-440, SRS-452, SRS-510); the git source spec re-resolves the requested tag on every invocation, so no additional upgrade option is needed. Executes the command only on Linux; on non-Linux platforms prints the manual command and skips uv execution.
- @param use_github {bool} When True, install the latest tagged GitHub release instead of the PyPI index (`--upgrade --develop` or equivalent alias `--dev`, SRS-440, SRS-445).
- @param force {bool} When True, append `--force --reinstall --refresh` so uv re-downloads the package and fully reinstalls it (`--upgrade --force`, SRS-508, SRS-509, SRS-510).
- @return {None} Function return value.
- @throws {ReqError} When the SRS-451 GitHub tag resolution fails (exit code 1, SRS-453) or when the uv process fails.
- @note Tag resolution precedes the platform gate so the non-Linux manual command embeds the resolved tag (SRS-452).
- @note The `--develop`/`--dev` argv alias mapping to `use_github=True` and the `--force` argv token mapping to `force=True` are resolved by `main(...)` before calling this function.
- @satisfies SRS-343, SRS-440, SRS-445, SRS-451, SRS-452, SRS-453, SRS-508, SRS-509, SRS-510

### fn `def run_uninstall() -> None` (L1042-1074)
- @brief Executes the uninstallation using uv.
- @details Implements the run_uninstall function behavior with deterministic control flow.
- @return {None} Function return value.
- @throws ReqError If uninstall fails.
- @satisfies SRS-344, SRS-346

### fn `def normalize_release_tag(tag: str) -> str` (L1075-1087)
- @brief Normalizes the release tag by removing a 'v' prefix if present.
- @details Implements the normalize_release_tag function behavior with deterministic control flow.
- @param tag The raw tag string.
- @return The normalized version string.

### fn `def parse_version_tuple(version: str) -> tuple[int, ...] | None` (L1088-1112)
- @brief Converts a version into a numeric tuple for comparison.
- @details Accepts versions in 'X.Y.Z' format (ignoring any non-numeric suffixes).
- @param version The version string to parse.
- @return Tuple of integers or None if parsing fails.

### fn `def is_newer_version(current: str, latest: str) -> bool` (L1113-1131)
- @brief Returns True if latest is greater than current.
- @details Implements the is_newer_version function behavior with deterministic control flow.
- @param current The current installed version string.
- @param latest The latest available version string.
- @return True if update is available, False otherwise.

### fn `def parse_github_owner_repository(remote_url: str) -> tuple[str, str] | None` (L1132-1158)
- @brief Extract GitHub owner/repository from a git remote URL.
- @details Supports SSH (`git@github.com:owner/repo.git`), HTTPS (`https://github.com/owner/repo.git`), and SSH-scheme (`ssh://git@github.com/owner/repo.git`) forms. Removes optional `.git` suffix.
- @param remote_url Remote URL string from `git remote -v`.
- @return Tuple `(owner, repository)` when URL targets github.com; otherwise None.

### fn `def read_git_remote_verbose(cwd: str | None = None) -> str` (L1159-1178)
- @brief Read git remote definitions using `git remote -v`.
- @details Executes `git remote -v` with deterministic stderr capture and text decoding. When `cwd` is omitted, the current process working directory is used.
- @param cwd Optional working directory override for git execution context.
- @return Raw stdout output generated by `git remote -v`.
- @throws subprocess.CalledProcessError If git returns a non-zero status.

### fn `def resolve_github_owner_repository_from_active_remotes() -> tuple[str, str]` (L1179-1239)
- @brief Resolve GitHub owner/repository from active repository remotes.
- @details Reads `git remote -v`, prioritizes `origin` fetch URL, then other fetch remotes, then non-fetch entries, and returns the first parseable github.com owner/repository pair. If the first inspection fails outside the repository root context, retries once from `REPO_ROOT`.
- @return Tuple `(owner, repository)` resolved from active remotes.
- @throws ValueError If no github.com remote URL can be parsed from `git remote -v`.
- @throws ReqError If git remote inspection cannot execute successfully.

### fn `def resolve_pypi_latest_version_url() -> str` (L1240-1249)
- @brief Resolve the PyPI JSON API URL for latest-version resolution.
- @details Returns the static endpoint derived from the PyPI project `cli-usereq`.
- @return {str} Fully-qualified URL `https://pypi.org/pypi/cli-usereq/json`.
- @satisfies SRS-430

### fn `def fetch_pypi_latest_version(` (L1250-1251)

### fn `def fetch_github_latest_version(` (L1287-1290)
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

### fn `def format_unix_timestamp_utc(timestamp_seconds: int) -> str` (L1329-1341)
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

### fn `def get_release_check_idle_file_path(` (L1342-1343)

### fn `def cleanup_release_check_idle_state_cache(` (L1360-1361)
- @brief Resolve idle-state file path for startup release-check throttling.
- @details Builds the path using the effective home directory returned by `Path.home()`.
- @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
- @return Absolute path `$HOME/.cache/<program_name>/check_version_idle-time.json`.
- @satisfies SRS-345

### fn `def read_release_check_idle_state(file_path: Path) -> dict[str, int | str] | None` (L1384-1448)
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

### fn `def should_execute_release_check(` (L1449-1451)

### fn `def parse_retry_after_seconds(` (L1470-1472)
- @brief Decide whether startup release-check should execute in current invocation.
- @details Executes release-check when state is missing and skips only while the persisted `idle_until_timestamp` is greater than the current timestamp.
- @param idle_state Parsed idle-state payload or None when unavailable.
- @param now_timestamp Current Unix timestamp in seconds.
- @return True when release-check must execute; False when still in idle window.
- @satisfies SRS-348

### fn `def write_release_check_idle_state_payload(` (L1502-1505)
- @brief Parse an HTTP `Retry-After` header value into non-negative seconds.
- @details Supports integer-second values and HTTP-date values; HTTP-date values are converted to a delta from `now_timestamp`.
- @param retry_after_header Raw `Retry-After` header value.
- @param now_timestamp Current Unix timestamp in seconds.
- @return Retry delay in seconds when parsing succeeds; otherwise None.

### fn `def write_release_check_idle_state(` (L1532-1535)
- @brief Persist canonical release-check idle-state payload to disk.
- @details Serializes both numeric and UTC human-readable timestamps for the success instant and the idle-until instant.
- @param file_path Absolute idle-state JSON path.
- @param last_success_timestamp Unix timestamp of the last successful release-check.
- @param idle_until_timestamp Unix timestamp until startup release-check remains disabled.
- @throws OSError If file write fails.

### fn `def write_failed_release_check_idle_state(` (L1554-1558)
- @brief Persist release-check idle-state after a successful remote check.
- @details Computes `idle_until_timestamp = now_timestamp + idle_delay_seconds` and persists canonical idle-state keys.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Successful check timestamp in seconds.
- @param idle_delay_seconds Fixed idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-349

### fn `def persist_failed_release_check_idle_state(` (L1586-1590)
- @brief Persist idle-state after a startup release-check failure.
- @details Computes `idle_until_timestamp = now + idle_delay_seconds`, rewrites the canonical idle-state payload on every failure, and preserves the previous successful timestamp when available.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-350, SRS-351

### fn `def maybe_notify_newer_version(` (L1616-1617)
- @brief Persist failure idle-state and report write failures.
- @details Delegates failure idle-state persistence to `write_failed_release_check_idle_state(...)`; converts `OSError` into the standard bright-red stderr diagnostic without swallowing the original release-check failure.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @return {None} Function return value.
- @satisfies SRS-350, SRS-351

### fn `def ensure_doc_directory(` (L1746-1747)
- @brief Executes idle-gated online PyPI version check and prints bright colored status messages.
- @details Reads idle-state from `$HOME/.cache/usereq/check_version_idle-time.json`, skips remote requests when idle window is active unless startup context enables `FORCE_ONLINE_RELEASE_CHECK`, fetches the latest version from the PyPI JSON API (SRS-430) when due, compares versions, prints a bright-green update message only for newer versions, persists a 3600-second idle-delay after successful HTTP/JSON validation, prints bright-red diagnostics on every failure, rewrites idle-state JSON on every failure, uses an 86400-second idle-delay for `HTTPError`, `URLError`, and `TimeoutError`, and uses the default 3600-second idle-delay for other release-check failures.
- @param timeout_seconds Time to wait for the version check response.
- @return {Optional[str]} The fetched PyPI latest version on successful validation; None when the check is idle-gated or fails.
- @satisfies SRS-345, SRS-348, SRS-349, SRS-350, SRS-351, SRS-430

### fn `def ensure_test_directory(` (L1776-1777)
- @brief Resolve and validate docs directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate docs directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-359, SRS-363

### fn `def ensure_src_directory(` (L1806-1807)
- @brief Resolve and validate tests directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate tests directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-361, SRS-363

### fn `def make_relative_if_contains_project(path_value: str, project_base: Path) -> str` (L1836-1877)
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

### fn `def resolve_absolute(normalized: str, project_base: Path) -> Optional[Path]` (L1878-1893)
- @brief Resolves the absolute path starting from a normalized value.
- @details Implements the resolve_absolute function behavior with deterministic control flow.
- @param normalized The normalized relative path string.
- @param project_base The project root path.
- @return Absolute Path object or None if normalized is empty.

### fn `def resolve_git_root(target_path: Path) -> Path` (L1894-1921)
- @brief Resolve the git repository root for a given path.
- @param target_path Absolute path that must be inside a git repository.
- @return Absolute path to the git repository root.
- @throws ReqError If the path is not inside a git repository.
- @satisfies SRS-305, SRS-306

### fn `def sanitize_branch_name(branch: str) -> str` (L1922-1931)
- @brief Replace characters incompatible with Linux or Windows paths in a branch name.
- @param branch Raw git branch name.
- @return Sanitized string with incompatible characters replaced by `-`.
- @satisfies SRS-319

### fn `def validate_wt_name(wt_name: str) -> bool` (L1932-1943)
- @brief Validate that a worktree/branch name contains only valid directory characters.
- @param wt_name Candidate worktree name.
- @return True if valid, False if invalid characters are present.
- @satisfies SRS-321

### fn `def load_full_config() -> dict` (L1944-1964)
- @brief Load ALL parameters from the user-global configuration file as a raw dictionary.
- @return Full dictionary of all config key-value pairs.
- @throws ReqError If the global config file is missing or invalid JSON.
- @satisfies SRS-310, SRS-387

### fn `def save_config(` (L1965-1970)

### fn `def update_directory_config(` (L2000-2003)
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

### fn `def load_config() -> dict[str, str | list[str]]` (L2041-2091)
- @brief Persist one or more directory configuration keys while preserving unrelated keys.
- @brief Loads directory parameters from the user-global configuration file.
- @details Loads the existing raw configuration payload when present, replaces only the
supplied directory keys, and rewrites `~/.config/usereq/config.json` with parent
directories created on demand. `--prj-base` and `--git-base` are never persisted
(SRS-394, SRS-398, SRS-399, SRS-400, SRS-401).
- @details Reads `~/.config/usereq/config.json`; when the file is absent every key falls back to its default (`usereq/docs`, `tests`, `src`). Present but invalid values raise `ReqError`; `--prj-base` and `--git-base` are never read from the file (SRS-359, SRS-361, SRS-362, SRS-394, SRS-407).
- @param docs_dir_value Project-relative docs directory value, or None to keep current.
- @param tests_dir_value Project-relative tests directory value, or None to keep current.
- @param src_dir_values Ordered project-relative source directory values, or None to keep current.
- @return {None} Function return value.
- @return Dictionary containing `docs-dir`, `tests-dir`, and `src-dir` values.
- @throws ReqError If the existing configuration file contains invalid JSON.
- @throws ReqError If the global config file is invalid or holds invalid directory values.
- @satisfies SRS-394, SRS-398, SRS-399, SRS-400, SRS-401
- @satisfies SRS-359, SRS-361, SRS-362, SRS-394, SRS-407

### fn `def load_static_check_from_config() -> dict` (L2092-2130)
- @brief Load the `"static-check"` section from the user-global configuration file without validation errors.
- @details Reads `~/.config/usereq/config.json` silently. When the payload stores no `"static-check"` entry (including a missing or unreadable file), returns a deep copy of `DEFAULT_STATIC_CHECK` (SRS-424); a present entry, including an empty or invalid object, suppresses the defaults and is normalized like before: per-language entries that are not non-empty arrays of objects are dropped. Does NOT raise `ReqError`; caller decides whether absence is an error.
- @return Dict of static-check config (canonical-lang -> list[config-dict]).
- @see SRS-252, SRS-253, SRS-256, SRS-424, SRS-425, SRS-426
- @satisfies SRS-424, SRS-425, SRS-426

### fn `def _static_check_entry_identity(` `priv` (L2131-2132)

### fn `def load_persisted_providers() -> list[str]` (L2155-2196)
- @brief Build the canonical identity tuple for one static-check entry.
- @brief Load persisted provider names from the user-global configuration file.
- @details Identity is defined strictly by language, module, cmd, and params.
Unknown/additional keys in ``entry`` are ignored; ``params`` is normalized
to a tuple preserving order, and non-list params are treated as empty.
- @details Reads the ``"providers"`` key from `~/.config/usereq/config.json` (SRS-064, SRS-279). Foreign entries (non-string values or strings that are not valid provider names, e.g. legacy `PROVIDER:ARTIFACT` SPEC strings persisted by the pre-1.20 grammar) are dropped with one English stderr warning each; provider-reading commands (`show`, `install`, `uninstall`) therefore consider only providers that remain enabled, and the install flow raises the SRS-035 config-invalid error exactly when no valid provider remains (SRS-064). The configuration file is never rewritten by this read path. All providers are disabled by default because the key defaults to an empty list. Returns ``[]`` on any read or parse error rather than raising.
- @param canonical_lang Canonical language key that owns the entry.
- @param entry Static-check entry mapping loaded from config or parsed from CLI.
- @return Tuple ``(canonical_lang, module, cmd, params_tuple)``.
- @return List of valid provider names; empty list if key is missing, config is unreadable, or no persisted entry is a valid provider name.
- @see SRS-279, SRS-064, SRS-416, SRS-419
- @satisfies SRS-301
- @satisfies SRS-064, SRS-279

### fn `def _read_config_payload() -> dict` `priv` (L2197-2217)
- @brief Read the raw user-global configuration payload without key filtering.
- @details Single read path for configuration commands performing read-modify-write updates (SRS-279, SRS-288, SRS-387, SRS-413, SRS-414, SRS-420).
- @return {dict} Raw JSON dictionary; empty dict when the file is absent.
- @throws {ReqError} Raised when the file exists but holds invalid JSON (exit code 11).
- @satisfies SRS-288, SRS-387

### fn `def _write_config_payload(payload: dict) -> None` `priv` (L2218-2236)
- @brief Write the user-global configuration payload filtered to canonical keys.
- @details Creates missing parent directories on first write (SRS-387) and never writes `--prj-base`/`--git-base` (SRS-394).
- @param payload {dict} Full payload; only `PERSISTED_CONFIG_KEYS` entries are written.
- @return {None} Function return value.
- @satisfies SRS-288, SRS-387, SRS-394

### fn `def load_auto_install_enabled() -> bool` (L2237-2251)
- @brief Resolve the persisted auto-install flag with enabled default.
- @details `auto-install` defaults to enabled; unreadable configuration falls back to the default (SRS-420, SRS-421).
- @return {bool} True unless the configuration stores exactly `false`.
- @satisfies SRS-420, SRS-421

### fn `def apply_enabled_providers(names: list[str]) -> None` (L2252-2281)
- @brief Persist ``--enable PROVIDER`` names replacing the named providers' entries.
- @details Validates every token through `validate_provider_name` (SRS-275, SRS-278), removes all previously persisted entries of the named providers, appends the new names deduplicated in CLI order, and preserves every other provider (SRS-279). No artifact is installed (SRS-276).
- @param names {list[str]} Raw provider name tokens in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid provider tokens with exit code 1 (SRS-278).
- @satisfies SRS-275, SRS-276, SRS-278, SRS-279

### fn `def apply_disabled_providers(names: list[str]) -> None` (L2282-2310)
- @brief Remove the named providers from the persisted `"providers"` array.
- @details Removes every persisted entry of each named provider; absent entries leave the configuration unchanged; the `"providers"` key is removed when no entries remain (SRS-413).
- @param names {list[str]} Provider names supplied via `--disable`.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown provider tokens with exit code 1 (SRS-422).
- @satisfies SRS-413, SRS-422

### fn `def apply_enable_static_check_specs(specs: list[str]) -> None` (L2311-2358)
- @brief Persist `--enable-static-check` entries merged into the existing configuration.
- @details Parses each SPEC (SRS-260), deduplicates within the invocation (SRS-251), validates Command executables (SRS-250), merges into the persisted `"static-check"` object by exact `(language, module, cmd, params)` identity (SRS-301), and requires no `--prj-base` (SRS-415).
- @param specs {list[str]} Raw SPEC strings in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid language/module tokens or non-executable Command `cmd` values with exit code 1.
- @satisfies SRS-248, SRS-250, SRS-251, SRS-301, SRS-415

### fn `def apply_disable_static_check_specs(specs: list[str]) -> None` (L2359-2407)
- @brief Remove static-check entries selected by `--disable-static-check` SPECs.
- @details Empty language arrays are removed from the `"static-check"` object and the `"static-check"` key is persisted even when empty so explicit configuration suppresses the SRS-424 defaults; requires no `--prj-base` (SRS-414, SRS-415).
- @param specs {list[str]} SPEC strings; `LANG=MODULE[,CMD[,PARAM...]]` removes exact identity matches, bare `LANG` removes the whole canonical language key.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown language or module tokens with exit code 1 (SRS-422).
- @satisfies SRS-414, SRS-415, SRS-422, SRS-424

### fn `def apply_auto_install_config(enabled: bool) -> None` (L2408-2420)
- @brief Persist the auto-install enabled flag.
- @details Read-modify-write preserving all unrelated canonical keys (SRS-420).
- @param enabled {bool} Value persisted under `"auto-install"`.
- @return {None} Function return value.
- @satisfies SRS-420

### fn `def _is_provider_config_command(args: Namespace) -> bool` `priv` (L2421-2438)
- @brief Check if args request a provider/static-check/auto-install configuration command.
- @details Configuration commands only update `~/.config/usereq/config.json` and never install artifacts (SRS-276, SRS-413, SRS-414, SRS-415, SRS-420).
- @param args Parsed CLI namespace.
- @return True when any configuration flag is present.

### fn `def run_config_commands(args: Namespace) -> None` (L2439-2467)
- @brief Apply every provider/static-check/auto-install configuration command.
- @details Application order: `--enable`, `--disable`, `--enable-static-check`, `--disable-static-check`, `--enable-auto-install`, `--disable-auto-install`; each step persists immediately (SRS-275, SRS-413, SRS-414, SRS-420).
- @param args Parsed CLI namespace carrying the configuration flag values.
- @return {None} Function return value.
- @satisfies SRS-275, SRS-276, SRS-413, SRS-414, SRS-415, SRS-420

### fn `def _non_symlink_regular_files(directory: Path) -> list[Path]` `priv` (L2468-2491)
- @brief List non-hidden regular files in one directory without following symbolic links.
- @details Scans ``directory`` with ``os.scandir`` and ``follow_symlinks=False`` so symbolic-link entries are never followed or resolved: symlinked files, symlinked subdirectories, and broken links are excluded, and only entries whose own inode is a regular file are kept (SRS-504). Hidden names starting with ``.`` are excluded. When ``directory`` is itself a symbolic link or is absent, returns an empty list so callers apply their absent-directory fallback instead of reading through the link.
- @param directory {Path} Absolute directory to enumerate.
- @return {list[Path]} Sorted paths of non-symlink regular files.
- @satisfies SRS-504

### fn `def generate_guidelines_file_list() -> str` (L2492-2512)
- @brief Build the `%%GUIDELINES_FILES%%` substitution payload from GUIDELINES_DIR.
- @details Enumerates non-hidden non-symlink regular files in :func:`guidelines_dir` (packaged `resources/guidelines` of the running installation, SRS-360) in deterministic sorted order without following symbolic links (SRS-504) and renders each as a backticked home-relative path (SRS-402). When the directory is absent, symlinked, or empty, renders the home-relative directory itself with a trailing slash.
- @return {str} Comma-separated backticked home-relative paths, or the directory fallback.
- @satisfies SRS-403, SRS-504

### fn `def generate_guidelines_file_names() -> list[str]` (L2513-2527)
- @brief List the bare guideline file names reported after installation.
- @details Returns one bare file name per non-hidden non-symlink regular file in :func:`guidelines_dir` (packaged `resources/guidelines` of the running installation) without following symbolic links (SRS-504, SRS-516); names carry no directory components, and an absent, symlinked, or empty directory yields an empty list.
- @return {list[str]} Bare guideline file names in deterministic sorted order.
- @satisfies SRS-360, SRS-513, SRS-516

### fn `def generate_templates_file_names() -> list[str]` (L2528-2542)
- @brief List the bare template file names reported after installation.
- @details Returns one bare file name per non-hidden non-symlink regular file in :func:`templates_dir` (packaged `resources/templates` of the running installation) without following symbolic links (SRS-516); names carry no directory components, and an absent, symlinked, or empty directory yields an empty list.
- @return {list[str]} Bare template file names in deterministic sorted order.
- @satisfies SRS-498, SRS-514, SRS-516

### fn `def _print_resource_report() -> None` `priv` (L2543-2564)
- @brief Print the compact post-installation packaged-resource report.
- @details Prints the home-relative lexical guidelines directory path ending with `/`, then one comma-separated line of bare guideline file names (SRS-513), then the home-relative lexical templates directory path ending with `/`, then one comma-separated line of bare template file names (SRS-514). Every printed path is composed lexically without resolving symbolic links (SRS-515); an empty enumeration emits no file-name line (SRS-516).
- @return {None} Function return value.
- @satisfies SRS-513, SRS-514, SRS-515, SRS-516

### fn `def ensure_relative(value: str, name: str, code: int) -> None` (L2565-2580)
- @brief Validates that the path is not absolute and raises an error otherwise.
- @details Implements the ensure_relative function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @param name Input parameter `name`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def apply_replacements(text: str, replacements: Mapping[str, str]) -> str` (L2581-2593)
- @brief Returns text with token replacements applied.
- @details Implements the apply_replacements function behavior with deterministic control flow.
- @param text Input parameter `text`.
- @param replacements Input parameter `replacements`.
- @return {str} Function return value.

### fn `def write_text_file(dst: Path, text: str) -> None` (L2594-2605)
- @brief Writes text to disk, ensuring the destination folder exists.
- @details Implements the write_text_file function behavior with deterministic control flow.
- @param dst Input parameter `dst`.
- @param text Input parameter `text`.
- @return {None} Function return value.

### fn `def copy_with_replacements(` (L2606-2607)

### fn `def extract_frontmatter(content: str) -> tuple[str, str]` (L2622-2635)
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

### fn `def extract_purpose_first_bullet(body: str) -> str` (L2636-2660)
- @brief Returns the first bullet of the Purpose section.
- @details Implements the extract_purpose_first_bullet function behavior with deterministic control flow.
- @param body Input parameter `body`.
- @return {str} Function return value.

### fn `def _extract_section_text(body: str, section_name: str) -> str` `priv` (L2661-2688)
- @brief Extracts and collapses the text content of a named ## section.
- @details Scans `body` line by line for a heading matching `## <section_name>` (case-insensitive). Collects all subsequent non-empty lines until the next `##`-level heading (or end of string). Strips each line, joins with a single space, and returns the collapsed single-line result.
- @param[in] body str -- Full prompt body text (after front matter removal).
- @param[in] section_name str -- Target section name without `##` prefix (case-insensitive match).
- @return str -- Single-line collapsed text of the section; empty string if section absent or empty.

### fn `def extract_skill_description(frontmatter: str) -> str` (L2689-2707)
- @brief Extracts the usage field from YAML front matter as a single YAML-safe line.
- @details Parses the YAML front matter and returns the `usage` field value with all whitespace normalized to a single line. Returns an empty string if the field is absent.
- @param[in] frontmatter str -- YAML front matter text (without the leading/trailing `---` delimiters).
- @return str -- Single-line text of the usage field; empty string if absent.

### fn `def yaml_double_quote_escape(value: str) -> str` (L2708-2717)
- @brief Minimal escape for a double-quoted string in YAML.
- @details Implements the yaml_double_quote_escape function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @return {str} Function return value.

### fn `def list_docs_templates() -> list[Path]` (L2718-2738)
- @brief Returns non-hidden files available in resources/templates.
- @details Implements the list_docs_templates function behavior with deterministic control flow.
- @return Sorted list of file paths under resources/templates.
- @throws ReqError If resources/templates does not exist or has no non-hidden files.
- @satisfies SRS-495

### fn `def find_requirements_template(docs_templates: list[Path]) -> Path` (L2739-2756)
- @brief Returns the packaged Requirements template file.
- @details Implements the find_requirements_template function behavior with deterministic control flow.
- @param docs_templates Runtime template file list from resources/templates.
- @return Path to `Requirements_Template.md`.
- @throws ReqError If `Requirements_Template.md` is not present.
- @satisfies SRS-495

### fn `def ensure_wrapped(target: Path, project_base: Path, code: int) -> None` (L2757-2772)
- @brief Verifies that the path is under the project root.
- @details Implements the ensure_wrapped function behavior with deterministic control flow.
- @param target Input parameter `target`.
- @param project_base Input parameter `project_base`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def prune_empty_dirs(root: Path) -> None` (L2773-2789)
- @brief Removes empty directories under the specified root.
- @details Implements the prune_empty_dirs function behavior with deterministic control flow.
- @param root Input parameter `root`.
- @return {None} Function return value.

### fn `def remove_generated_resources() -> None` (L2790-2821)
- @brief Removes `req-*` skill artifacts generated by the tool from user-level provider directories.
- @details Loads the persisted `providers` array from the user-global configuration file, resolves each enabled provider skills root via :func:`provider_skills_root`, and deletes only `req-*` skill directories and files. Empty user-level skills roots are pruned afterwards; unrelated user content is never touched.
- @return {None} Function return value.
- @satisfies SRS-419

### fn `def _render_simple_table(headers: list[str], rows: list[list[str]]) -> str` `priv` (L2822-2852)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _line(cells: list[str]) -> str` `priv` (L2835-2843)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _border(left: str, middle: str, right: str) -> str` `priv` (L2844-2846)

### fn `def _provider_skill_installed(provider: str, skill_name: str) -> bool` `priv` (L2853-2870)
- @brief Detect whether one named skill artifact exists for a provider.
- @details Per-skill installation-status detection for the `show` `Installation Status` table (SRS-417, SRS-490); unknown providers and absent roots report `False`. Complexity: O(1). Side effects: none (read-only filesystem probe).
- @param provider {str} Provider selector from `{antigravity, claude, codex, copilot, openclaw, opencode, pi}`.
- @param skill_name {str} Skill directory name such as `req-<prompt_name>`.
- @return {bool} True when the skill path exists under the provider skills root.
- @satisfies SRS-417, SRS-490

### fn `def _packaged_prompt_names() -> list[str]` `priv` (L2871-2885)
- @brief List the packaged prompt stem names defining installable skills.
- @details Enumeration source for the `show` `Installation Status` rows (SRS-489); returns an empty list when the packaged prompts directory is absent. Complexity: O(P log P) over P packaged prompts. Side effects: none (read-only).
- @return {list[str]} Sorted prompt file stems under the packaged `resources/prompts` directory.
- @satisfies SRS-489

### fn `def run_install(args: Namespace) -> None` (L2886-2901)
- @brief Execute install: install or update the persisted providers globally.
- @details Delegates to the config-driven installation flow (SRS-035, SRS-064, SRS-418) which requires at least one enabled provider and prints the installation summary report (SRS-049). Install performs no project-side operations and does not consume `--prj-base` (SRS-447, SRS-448); scaffolding and directory persistence are removed legacy behaviors (SRS-363, SRS-407, SRS-449).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If no provider is enabled.
- @satisfies SRS-035, SRS-064, SRS-418, SRS-447, SRS-448

### fn `def run_uninstall_providers(args: Namespace) -> None` (L2902-2919)
- @brief Execute uninstall: remove skill artifacts of the configured providers.
- @details Requires the user-global configuration file and removes `req-*` skill artifacts of the providers persisted under `"providers"` (SRS-419).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If the global configuration file is missing.
- @satisfies SRS-419

### fn `def run_show(args: Namespace) -> None` (L2920-3027)
- @brief Execute show: print the active configuration as tables.
- @details Prints the effective configuration table (`docs-dir`, `tests-dir`, `src-dir`, `auto-install`), the Providers table listing every configurable provider with the `CLI`, `Enabled`, and `Skills Path` columns in alphabetical order (SRS-462, SRS-463, SRS-485, SRS-488), exactly one `Installation Status` table with `Type`, `Name`, `CLI`, `Enabled`, and `Installed` columns reporting one row per packaged prompt and enabled provider pair ordered by prompt name then provider name (SRS-417, SRS-489, SRS-490, SRS-491), and the enabled static-check entries (SRS-416).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If persisted provider names are invalid.
- @satisfies SRS-416, SRS-417, SRS-462, SRS-463, SRS-485, SRS-488, SRS-489, SRS-490, SRS-491

### fn `def _maybe_auto_install_after_upgrade(argv_list: list[str]) -> None` `priv` (L3028-3052)
- @brief Run the provider installation flow after a successful `--upgrade`.
- @details Executes the `install` flow with persisted providers when `auto-install` is enabled (SRS-420, SRS-421) regardless of `--prj-base` presence; prints an English stderr warning and skips when no provider is enabled (SRS-450).
- @param argv_list {list[str]} Raw CLI argument vector of the `--upgrade` invocation.
- @return {None} Function return value.
- @satisfies SRS-420, SRS-421, SRS-450

### fn `def run_set_directories(args: Namespace) -> None` (L3053-3116)
- @brief Persist `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` values.
- @details Requires `--prj-base` (SRS-396), normalizes each supplied path against the project base, rejects absolute or escaping paths, and writes only the supplied keys to `~/.config/usereq/config.json` while preserving unrelated keys (SRS-398, SRS-399, SRS-400, SRS-401). No project directory is created and no provider artifact is generated.
- @param args Parsed CLI namespace carrying the `set_docs_dir`, `set_src_dir`, and `set_tests_dir` values.
- @return {None} Function return value.
- @throws ReqError If `--prj-base` is absent or a supplied path escapes the project base.
- @satisfies SRS-396, SRS-398, SRS-399, SRS-400, SRS-401

### fn `def _validate_enable_static_check_command_executables(` `priv` (L3117-3120)

### fn `def run(args: Namespace) -> None` (L3149-3348)
- @brief Validate Command-module executables in `--enable-static-check` parsed entries.
- @brief Handles the main installation flow installing skills for persisted providers.
- @details Validation scope is limited to Command entries coming from CLI specs.
Each Command `cmd` is resolved with `shutil.which`; on miss, raises `ReqError(code=1)`
before any configuration persistence.
- @details Loads the persisted `"providers"` names from `~/.config/usereq/config.json` (SRS-064, SRS-279) and requires at least one enabled provider (SRS-035), installs `req-<prompt_name>/SKILL.md` skill artifacts into the user-level hardcoded skills roots (SRS-381..SRS-386, SRS-464, SRS-486) with home-relative packaged-resource token substitution for `%%GUIDELINES_FILES%%`, `%%GUIDELINES_PATH%%`, `%%TEMPLATE_PATH%%`, `%%DOC_PATH%%`, `%%SRC_PATHS%%`, and `%%TEST_PATH%%` (SRS-360, SRS-402, SRS-403, SRS-498, SRS-500, SRS-501, SRS-502), never following or resolving symbolic links in substitution sources (SRS-504, SRS-505, SRS-506), and never rewrites the user-global configuration file (SRS-448). Install does not consume `--prj-base` (SRS-447); project scaffolding, containment validation, and directory persistence are removed legacy behaviors (SRS-363, SRS-407, SRS-449).
- @param static_check_config Parsed static-check entries grouped by canonical language.
- @param enforce When false, skip validation and return immediately.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @return {None} Function return value.
- @throws ReqError If a Command entry references a non-executable `cmd` on this system.
- @throws ReqError If no provider is enabled.
- @see SRS-250
- @satisfies SRS-035, SRS-064, SRS-279, SRS-359, SRS-360, SRS-361, SRS-362, SRS-381, SRS-387, SRS-388, SRS-402, SRS-403, SRS-418, SRS-447, SRS-448, SRS-498, SRS-500, SRS-501, SRS-502, SRS-504, SRS-505, SRS-506

- var `VERBOSE = getattr(args, "verbose", False)` (L3169)
- @brief Handles the main installation flow installing skills for persisted providers.
- @details Loads the persisted `"providers"` names from `~/.config/usereq/config.json`
(SRS-064, SRS-279) and requires at least one enabled provider (SRS-035), installs
`req-<prompt_name>/SKILL.md` skill artifacts into the user-level hardcoded skills
roots (SRS-381..SRS-386, SRS-464, SRS-486) with home-relative packaged-resource token
substitution for `%%GUIDELINES_FILES%%`, `%%GUIDELINES_PATH%%`, `%%TEMPLATE_PATH%%`,
`%%DOC_PATH%%`, `%%SRC_PATHS%%`, and `%%TEST_PATH%%` (SRS-360, SRS-402, SRS-403,
SRS-498, SRS-500, SRS-501, SRS-502), never following or resolving symbolic links in
substitution sources (SRS-504, SRS-505, SRS-506), and never rewrites the user-global
configuration file (SRS-448). Install does not consume `--prj-base` (SRS-447); project
scaffolding, containment validation, and directory persistence are removed legacy
behaviors (SRS-363, SRS-407, SRS-449).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If no provider is enabled.
- @satisfies SRS-035, SRS-064, SRS-279, SRS-359, SRS-360, SRS-361, SRS-362, SRS-381, SRS-387, SRS-388, SRS-402, SRS-403, SRS-418, SRS-447, SRS-448, SRS-498, SRS-500, SRS-501, SRS-502, SRS-504, SRS-505, SRS-506
- var `DEBUG = getattr(args, "debug", False)` (L3170)
### fn `def _format_install_table(` `priv` (L3289-3290)

### fn `def _wrap_cell(value: str, width: int, allow_wrap: bool) -> list[str]` `priv` (L3322-3344)
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

### fn `def _render_row(provider: str, skills: str) -> list[str]` `priv` (L3345-3366)
- @brief Render one logical table row into one or more physical lines.
- @details Applies per-cell wrapping and left alignment, then expands the row height to the maximum wrapped cell line count.
- @param provider {str} Provider cell text.
- @param skills {str} Skills Installed cell text.
- @return {list[str]} Physical row lines encoded with box-drawing separators.

### fn `def _colorize_table_border(line: str) -> str` `priv` (L3383-3395)
- @brief Colorize box-drawing border glyphs with bright-red ANSI style.
- @details Applies color to border characters while preserving cell payload text color.
- @param line {str} One already-rendered table line.
- @return {str} Line with border glyphs wrapped in ANSI bright-red and reset sequences.

- var `SUPPORTED_EXTENSIONS = frozenset(` (L3408)
### fn `def _collect_source_files(src_dirs: list[str], project_base: Path) -> list[str]` `priv` (L3436-3493)
- @brief Collect source files from git-indexed project paths.
- @details Uses `git ls-files --cached --others --exclude-standard` in project root, filters by src-dir prefixes, applies EXCLUDED_DIRS filtering, and keeps only SUPPORTED_EXTENSIONS files.
- @param src_dirs Input parameter `src_dirs`.
- @param project_base Input parameter `project_base`.
- @return {list[str]} Function return value.

### fn `def _build_ascii_tree(paths: list[str]) -> str` `priv` (L3494-3539)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _emit(` `priv` (L3518-3520)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _format_files_structure_markdown(files: list[str], project_base: Path) -> str` `priv` (L3540-3554)
- @brief Format markdown section containing the scanned files tree.
- @details Implements the _format_files_structure_markdown function behavior with deterministic control flow.
- @param files Absolute file paths selected for references processing.
- @param project_base Project root used to normalize relative paths.
- @return Markdown section with heading and fenced tree.

### fn `def _is_standalone_command(args: Namespace) -> bool` `priv` (L3555-3566)
- @brief Check if the parsed args contain a standalone file command.
- @details The standalone group now contains only `--test-static-check` (SRS-240); the former `--files-*` and project-scan analysis flags were converted to bare subcommands (SRS-408) whose base requirements follow SRS-396 and SRS-410.
- @param args Parsed CLI namespace.
- @return True when the standalone `--test-static-check` flag is present.

### fn `def _is_project_scan_command(args: Namespace) -> bool` `priv` (L3567-3584)
- @brief Check if the parsed args contain a project-scan command.
- @details Project-scan commands: `--git-check`, `--docs-check`, `--git-wt-name`, `--git-wt-create`, and `--git-wt-delete`. The analysis commands were converted to bare subcommands (SRS-408) and `--git-path` was removed (SRS-333, SRS-334).
- @param args Parsed CLI namespace.
- @return True when any project-scan flag is present.

### fn `def _is_directory_config_command(args: Namespace) -> bool` `priv` (L3585-3600)
- @brief Check if args request a directory configuration command.
- @details Configuration commands persist project-relative directories and therefore require `--prj-base` without activating the installation flow (SRS-396, SRS-398, SRS-399, SRS-400).
- @param args Parsed CLI namespace.
- @return True when any `--set-*-dir` flag is present.

### fn `def _require_prj_base(args: Namespace) -> Path` `priv` (L3601-3619)
- @brief Return the mandatory absolute project base for the current command.
- @details `--prj-base` is command-line only and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI namespace.
- @return {Path} Absolute project base path.
- @throws ReqError If `--prj-base` is absent or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _require_git_base_value(args: Namespace) -> Path` `priv` (L3620-3639)
- @brief Validate and return the `--git-base` argument value without repository resolution.
- @details Performs presence and existence validation only (SRS-395); git-integration commands reach this level through `_require_git_base` because they are the only commands that execute git operations through `--git-base` (SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute `--git-base` path.
- @throws ReqError If `--git-base` is absent or does not exist.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def _require_git_base(args: Namespace) -> Path` `priv` (L3640-3652)
- @brief Return the mandatory absolute git repository base for the current command.
- @details `--git-base` is command-line only and is never loaded from configuration; the returned path is the repository root reported by `git rev-parse --show-toplevel` executed in `--git-base` (SRS-393, SRS-394, SRS-395, SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute git repository root resolved from `--git-base`.
- @throws ReqError If `--git-base` is absent, does not exist, or is not inside a git work tree.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def run_git_check(args: Namespace) -> None` (L3653-3680)
- @brief Execute --git-check: verify clean git status and valid HEAD.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On git status unclear or when `--git-base` is outside a git repository.
- @satisfies SRS-311, SRS-312, SRS-391, SRS-397

### fn `def run_docs_check(args: Namespace) -> None` (L3681-3710)
- @brief Execute --docs-check: verify existence of REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If any required doc file is missing.
- @satisfies SRS-313, SRS-314, SRS-315, SRS-316, SRS-317, SRS-396

### fn `def run_git_wt_name(args: Namespace) -> None` (L3711-3735)
- @brief Execute --git-wt-name: print standardized worktree name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @satisfies SRS-318, SRS-319, SRS-391, SRS-397

### fn `def _worktree_path_exists_exact(git_path: Path, target_path: Path) -> bool` `priv` (L3736-3765)
- @brief Check whether a git worktree exists at the exact target path.
- @details Parses `git worktree list --porcelain` output by `worktree <path>` records and performs exact path comparison to prevent partial-name or substring matches.
- @param git_path Absolute git root path used as command cwd.
- @param target_path Absolute worktree path expected for WT_NAME.
- @return {bool} True only when target_path is listed as an exact worktree path.
- @throws ReqError On git command execution errors.

### fn `def _rollback_worktree_create(git_path: Path, wt_path: Path, wt_name: str) -> None` `priv` (L3766-3802)
- @brief Roll back worktree and branch created by --git-wt-create on post-create failure.
- @details Uses `git worktree remove <path> --force` and `git branch -D <name>` to restore a clean git state when post-create copy/chdir operations fail.
- @param git_path Absolute git root path used as command cwd.
- @param wt_path Absolute worktree path to remove.
- @param wt_name Exact branch name to delete.
- @return {None} Function return value.
- @throws ReqError If rollback cannot remove the exact target worktree and branch.

### fn `def run_git_wt_create(args: Namespace) -> None` (L3803-3858)
- @brief Execute --git-wt-create: create a git worktree, branch, and .venv seeding from --prj-base.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name, missing or invalid `--prj-base` (SRS-395), git command failure, or when CWD is outside a git repository.
- @satisfies SRS-320, SRS-321, SRS-322, SRS-331, SRS-335, SRS-391, SRS-395, SRS-397, SRS-460

### fn `def run_git_wt_delete(args: Namespace) -> None` (L3859-3927)
- @brief Execute --git-wt-delete: remove a git worktree and branch by name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name or git removal failure.
- @satisfies SRS-326, SRS-327, SRS-328, SRS-332, SRS-391, SRS-397

### fn `def run_files_tokens(files: list[str]) -> None` (L3928-3951)
- @brief Execute files-tokens: count tokens for arbitrary files.
- @details Implements the run_files_tokens function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_references(files: list[str]) -> None` (L3952-3969)
- @brief Execute files-references: generate markdown for arbitrary files.
- @details Implements the run_files_references function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-234, SRS-408

### fn `def run_files_compress(files: list[str], enable_line_numbers: bool = False) -> None` (L3970-3989)
- @brief Execute files-compress: compress arbitrary files.
- @details Renders output header paths relative to current working directory.
- @param files List of source file paths to compress.
- @param enable_line_numbers If True, emits <n>: prefixes in compressed entries.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_find(args_list: list[str], enable_line_numbers: bool = False) -> None` (L3990-4019)
- @brief Execute files-find: find constructs in arbitrary files.
- @details Implements the run_files_find function behavior with deterministic control flow.
- @param args_list Combined list: [TAG, PATTERN, FILE1, FILE2, ...].
- @param enable_line_numbers If True, emits <n>: prefixes in output.
- @return {None} Function return value.
- @satisfies SRS-236, SRS-408

### fn `def run_references(args: Namespace) -> None` (L4020-4038)
- @brief Execute references: generate markdown for project source files.
- @details Implements the run_references function behavior with deterministic control flow.
- @param args Input parameter `args`.
- @return {None} Function return value.
- @satisfies SRS-177, SRS-180, SRS-181, SRS-235, SRS-396, SRS-408

### fn `def run_compress_cmd(args: Namespace) -> None` (L4039-4061)
- @brief Execute compress: compress project source files.
- @details Implements the run_compress_cmd function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @satisfies SRS-179, SRS-180, SRS-181, SRS-396, SRS-408

### fn `def run_find(args: Namespace) -> None` (L4062-4092)
- @brief Execute find: find constructs in project source files.
- @details Implements the run_find function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @throws ReqError If no source files found or no constructs match criteria with available TAGs listing.
- @satisfies SRS-180, SRS-237, SRS-396, SRS-408

### fn `def run_tokens(args: Namespace) -> None` (L4093-4122)
- @brief Execute tokens on the canonical documentation files in --docs-dir.
- @details Uses the mandatory `--prj-base` project base joined with the docs-dir value from ~/.config/usereq/config.json, selects only REQUIREMENTS.md/WORKFLOW.md/REFERENCES.md as direct regular files in fixed order, and delegates summary rendering to run_files_tokens.
- @param args Parsed CLI arguments namespace.
- @return None.
- @exception ReqError Raised when no canonical documentation file exists in configured docs-dir.
- @satisfies SRS-387, SRS-392, SRS-396, SRS-408

### fn `def run_files_static_check_cmd(files: list[str], args: Namespace) -> int` (L4123-4189)
- @brief Execute `files-static-check`: run static analysis on an explicit file list.
- @details Static-check configuration is loaded from `~/.config/usereq/config.json`. When the global configuration file cannot be located, emits a warning to stderr and continues with the SRS-424 default static-check configuration (SRS-254). Project base for dispatch context is the mandatory `--prj-base` value (SRS-253). For each file: - Resolves absolute path; skips with warning if not a regular file. - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on the lowercase extension. - Looks up language in the `"static-check"` config section; skips silently if absent. - Executes each configured language entry sequentially via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`. - For `Command` module entries, execution order is `<cmd> [params...] <filename>`. Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-253). Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-253, SRS-255)
- @param files List of raw file paths supplied by the user.
- @param args Parsed CLI namespace; the mandatory `--prj-base` resolves the dispatch context.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @see SRS-253, SRS-254, SRS-255, SRS-341, SRS-396, SRS-408

### fn `def run_project_static_check_cmd(args: Namespace) -> int` (L4190-4289)
- @brief Execute `static-check`: run static analysis on project source and test files.
- @details Collects files from configured `src-dir` directories and the `tests-dir` directory (SRS-256, SRS-336), applies `EXCLUDED_DIRS` filtering and `SUPPORTED_EXTENSIONS` matching. If `tests-dir` is missing or invalid in the global configuration file, test directory inclusion is skipped silently without error (SRS-336). Files under `<tests-dir>/fixtures/` are excluded from static-check selection because they are fixture corpus inputs for parser/static-check tests and can intentionally contain diagnostics unrelated to project code quality gates. For each collected file: - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on lowercase extension. - Looks up language in the `"static-check"` section of `~/.config/usereq/config.json`. - Skips silently when no tool is configured for the file's language. - Executes each configured language entry sequentially via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`. - For `Command` module entries, execution order is `<cmd> [params...] <filename>`. Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-256). Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-256, SRS-257)
- @param args Parsed CLI namespace; requires the mandatory `--prj-base` argument.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @throws ReqError If no source files are found.
- @see SRS-256, SRS-257, SRS-336, SRS-341, SRS-396, SRS-408

### fn `def _resolve_project_base(args: Namespace) -> Path` `priv` (L4290-4302)
- @brief Resolve the mandatory project base path for project-level commands.
- @details The project base is never derived from the current working directory and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI arguments namespace.
- @return Absolute path of the project base supplied by `--prj-base`.
- @throws ReqError If `--prj-base` is missing or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _resolve_project_src_dirs(args: Namespace) -> tuple[Path, list[str]]` `priv` (L4303-4333)
- @brief Resolve project base and src-dirs for project source commands.
- @details Loads the `src-dir` list from the user-global configuration file (`~/.config/usereq/config.json`) and resolves it against the mandatory `--prj-base` project base (SRS-392, SRS-396).
- @param args Input parameter `args`.
- @return {tuple[Path, list[str]]} Tuple `(project_base, src_dirs)`.
- @throws ReqError If `--prj-base` is missing or `src-dir` is invalid.
- @satisfies SRS-392, SRS-396

### fn `def _is_config_schema_command(args: Namespace) -> bool` `priv` (L4334-4351)
- @brief Detect the canonical configuration CLI command path.
- @details Configuration schema commands are `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` (SRS-519); they never trigger provider installation.
- @param args {Namespace} Parsed CLI namespace.
- @return {bool} True when any configuration schema command flag is present.

### fn `def run_config_schema_command(args: Namespace) -> int` (L4352-4412)
- @brief Execute one configuration schema command.
- @details Dispatches `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` against the user-global configuration file, writes payloads to stdout, and reports every diagnostic on stderr (SRS-519, SRS-532).
- @param args {Namespace} Parsed CLI namespace carrying the configuration flag values.
- @return {int} Process exit code: 0 on success, 1 on any configuration failure.
- @satisfies SRS-519, SRS-527, SRS-528, SRS-529, SRS-530, SRS-531, SRS-532

### fn `def main(argv: Optional[list[str]] = None) -> int` (L4413-4544)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.

- var `FORCE_ONLINE_RELEASE_CHECK = force_online_release_check` (L4427)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.
- var `FORCE_ONLINE_RELEASE_CHECK = previous_force_online_release_check` (L4434)
- var `VERBOSE = getattr(args, "verbose", False)` (L4451)
- var `DEBUG = getattr(args, "debug", False)` (L4452)
## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`REPO_ROOT`|var|pub|41||
|`RESOURCE_ROOT`|var|pub|44||
|`VERBOSE`|var|pub|47||
|`DEBUG`|var|pub|50||
|`REQUIREMENTS_TEMPLATE_NAME`|var|pub|53||
|`PERSISTED_CONFIG_KEYS`|var|pub|56||
|`AUTO_INSTALL_CONFIG_KEY`|var|pub|66||
|`VALID_PROVIDERS`|var|pub|69||
|`GLOBAL_CONFIG_DIRNAME`|var|pub|72||
|`GLOBAL_CONFIG_APP_DIRNAME`|var|pub|75||
|`GLOBAL_CONFIG_FILENAME`|var|pub|78||
|`home_dir`|fn|pub|82-92|def home_dir() -> Path|
|`get_global_config_path`|fn|pub|93-108|def get_global_config_path() -> Path|
|`guidelines_dir`|fn|pub|109-121|def guidelines_dir() -> Path|
|`templates_dir`|fn|pub|122-134|def templates_dir() -> Path|
|`format_home_relative_path`|fn|pub|135-158|def format_home_relative_path(path: Path) -> str|
|`provider_skills_root`|fn|pub|159-192|def provider_skills_root(provider: str) -> Path|
|`provider_skills_path`|fn|pub|193-206|def provider_skills_path(provider: str) -> str|
|`INVALID_WT_NAME_RE`|var|pub|207||
|`validate_provider_name`|fn|pub|211-233|def validate_provider_name(name: str) -> str|
|`resolve_provider_configs`|fn|pub|234-235|def resolve_provider_configs(|
|`ANSI_BRIGHT_RED`|var|pub|258||
|`ANSI_BRIGHT_GREEN`|var|pub|261||
|`ANSI_RESET`|var|pub|264||
|`RELEASE_CHECK_TIMEOUT_SECONDS`|var|pub|267||
|`RELEASE_CHECK_IDLE_DELAY_SECONDS`|var|pub|270||
|`RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS`|var|pub|273||
|`TOOL_PROGRAM_NAME`|var|pub|276||
|`RELEASE_CHECK_PROGRAM_NAME`|var|pub|282||
|`GITHUB_REPOSITORY_OWNER`|var|pub|287||
|`GITHUB_REPOSITORY_NAME`|var|pub|290||
|`RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME`|var|pub|293||
|`RELEASE_CHECK_IDLE_FILENAME`|var|pub|296||
|`GITHUB_RELEASES_LATEST_URL`|var|pub|299||
|`GITHUB_UPGRADE_SOURCE`|var|pub|308||
|`PYPI_PROJECT_JSON_URL`|var|pub|315||
|`UNKNOWN_VERSION_LABEL`|var|pub|321||
|`VERSION_REPORT_LABEL_WIDTH`|var|pub|324||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|327||
|`ReqError`|class|pub|331-348|class ReqError(Exception)|
|`ReqError.__init__`|fn|priv|336-348|def __init__(self, message: str, code: int = 1) -> None|
|`log`|fn|pub|349-358|def log(msg: str) -> None|
|`dlog`|fn|pub|359-369|def dlog(msg: str) -> None|
|`vlog`|fn|pub|370-380|def vlog(msg: str) -> None|
|`build_parser`|fn|pub|381-580|def build_parser() -> argparse.ArgumentParser|
|`parse_args`|fn|pub|876-885|def parse_args(argv: Optional[list[str]] = None) -> Names...|
|`load_package_version`|fn|pub|886-900|def load_package_version() -> str|
|`maybe_print_version`|fn|pub|901-949|def maybe_print_version(argv: list[str], pypi_latest: Opt...|
|`_resolve_github_upgrade_tag`|fn|priv|950-980|def _resolve_github_upgrade_tag() -> str|
|`run_upgrade`|fn|pub|981-1041|def run_upgrade(use_github: bool = False, force: bool = F...|
|`run_uninstall`|fn|pub|1042-1074|def run_uninstall() -> None|
|`normalize_release_tag`|fn|pub|1075-1087|def normalize_release_tag(tag: str) -> str|
|`parse_version_tuple`|fn|pub|1088-1112|def parse_version_tuple(version: str) -> tuple[int, ...] ...|
|`is_newer_version`|fn|pub|1113-1131|def is_newer_version(current: str, latest: str) -> bool|
|`parse_github_owner_repository`|fn|pub|1132-1158|def parse_github_owner_repository(remote_url: str) -> tup...|
|`read_git_remote_verbose`|fn|pub|1159-1178|def read_git_remote_verbose(cwd: str | None = None) -> str|
|`resolve_github_owner_repository_from_active_remotes`|fn|pub|1179-1239|def resolve_github_owner_repository_from_active_remotes()...|
|`resolve_pypi_latest_version_url`|fn|pub|1240-1249|def resolve_pypi_latest_version_url() -> str|
|`fetch_pypi_latest_version`|fn|pub|1250-1251|def fetch_pypi_latest_version(|
|`fetch_github_latest_version`|fn|pub|1287-1290|def fetch_github_latest_version(|
|`format_unix_timestamp_utc`|fn|pub|1329-1341|def format_unix_timestamp_utc(timestamp_seconds: int) -> str|
|`get_release_check_idle_file_path`|fn|pub|1342-1343|def get_release_check_idle_file_path(|
|`cleanup_release_check_idle_state_cache`|fn|pub|1360-1361|def cleanup_release_check_idle_state_cache(|
|`read_release_check_idle_state`|fn|pub|1384-1448|def read_release_check_idle_state(file_path: Path) -> dic...|
|`should_execute_release_check`|fn|pub|1449-1451|def should_execute_release_check(|
|`parse_retry_after_seconds`|fn|pub|1470-1472|def parse_retry_after_seconds(|
|`write_release_check_idle_state_payload`|fn|pub|1502-1505|def write_release_check_idle_state_payload(|
|`write_release_check_idle_state`|fn|pub|1532-1535|def write_release_check_idle_state(|
|`write_failed_release_check_idle_state`|fn|pub|1554-1558|def write_failed_release_check_idle_state(|
|`persist_failed_release_check_idle_state`|fn|pub|1586-1590|def persist_failed_release_check_idle_state(|
|`maybe_notify_newer_version`|fn|pub|1616-1617|def maybe_notify_newer_version(|
|`ensure_doc_directory`|fn|pub|1746-1747|def ensure_doc_directory(|
|`ensure_test_directory`|fn|pub|1776-1777|def ensure_test_directory(|
|`ensure_src_directory`|fn|pub|1806-1807|def ensure_src_directory(|
|`make_relative_if_contains_project`|fn|pub|1836-1877|def make_relative_if_contains_project(path_value: str, pr...|
|`resolve_absolute`|fn|pub|1878-1893|def resolve_absolute(normalized: str, project_base: Path)...|
|`resolve_git_root`|fn|pub|1894-1921|def resolve_git_root(target_path: Path) -> Path|
|`sanitize_branch_name`|fn|pub|1922-1931|def sanitize_branch_name(branch: str) -> str|
|`validate_wt_name`|fn|pub|1932-1943|def validate_wt_name(wt_name: str) -> bool|
|`load_full_config`|fn|pub|1944-1964|def load_full_config() -> dict|
|`save_config`|fn|pub|1965-1970|def save_config(|
|`update_directory_config`|fn|pub|2000-2003|def update_directory_config(|
|`load_config`|fn|pub|2041-2091|def load_config() -> dict[str, str | list[str]]|
|`load_static_check_from_config`|fn|pub|2092-2130|def load_static_check_from_config() -> dict|
|`_static_check_entry_identity`|fn|priv|2131-2132|def _static_check_entry_identity(|
|`load_persisted_providers`|fn|pub|2155-2196|def load_persisted_providers() -> list[str]|
|`_read_config_payload`|fn|priv|2197-2217|def _read_config_payload() -> dict|
|`_write_config_payload`|fn|priv|2218-2236|def _write_config_payload(payload: dict) -> None|
|`load_auto_install_enabled`|fn|pub|2237-2251|def load_auto_install_enabled() -> bool|
|`apply_enabled_providers`|fn|pub|2252-2281|def apply_enabled_providers(names: list[str]) -> None|
|`apply_disabled_providers`|fn|pub|2282-2310|def apply_disabled_providers(names: list[str]) -> None|
|`apply_enable_static_check_specs`|fn|pub|2311-2358|def apply_enable_static_check_specs(specs: list[str]) -> ...|
|`apply_disable_static_check_specs`|fn|pub|2359-2407|def apply_disable_static_check_specs(specs: list[str]) ->...|
|`apply_auto_install_config`|fn|pub|2408-2420|def apply_auto_install_config(enabled: bool) -> None|
|`_is_provider_config_command`|fn|priv|2421-2438|def _is_provider_config_command(args: Namespace) -> bool|
|`run_config_commands`|fn|pub|2439-2467|def run_config_commands(args: Namespace) -> None|
|`_non_symlink_regular_files`|fn|priv|2468-2491|def _non_symlink_regular_files(directory: Path) -> list[P...|
|`generate_guidelines_file_list`|fn|pub|2492-2512|def generate_guidelines_file_list() -> str|
|`generate_guidelines_file_names`|fn|pub|2513-2527|def generate_guidelines_file_names() -> list[str]|
|`generate_templates_file_names`|fn|pub|2528-2542|def generate_templates_file_names() -> list[str]|
|`_print_resource_report`|fn|priv|2543-2564|def _print_resource_report() -> None|
|`ensure_relative`|fn|pub|2565-2580|def ensure_relative(value: str, name: str, code: int) -> ...|
|`apply_replacements`|fn|pub|2581-2593|def apply_replacements(text: str, replacements: Mapping[s...|
|`write_text_file`|fn|pub|2594-2605|def write_text_file(dst: Path, text: str) -> None|
|`copy_with_replacements`|fn|pub|2606-2607|def copy_with_replacements(|
|`extract_frontmatter`|fn|pub|2622-2635|def extract_frontmatter(content: str) -> tuple[str, str]|
|`extract_purpose_first_bullet`|fn|pub|2636-2660|def extract_purpose_first_bullet(body: str) -> str|
|`_extract_section_text`|fn|priv|2661-2688|def _extract_section_text(body: str, section_name: str) -...|
|`extract_skill_description`|fn|pub|2689-2707|def extract_skill_description(frontmatter: str) -> str|
|`yaml_double_quote_escape`|fn|pub|2708-2717|def yaml_double_quote_escape(value: str) -> str|
|`list_docs_templates`|fn|pub|2718-2738|def list_docs_templates() -> list[Path]|
|`find_requirements_template`|fn|pub|2739-2756|def find_requirements_template(docs_templates: list[Path]...|
|`ensure_wrapped`|fn|pub|2757-2772|def ensure_wrapped(target: Path, project_base: Path, code...|
|`prune_empty_dirs`|fn|pub|2773-2789|def prune_empty_dirs(root: Path) -> None|
|`remove_generated_resources`|fn|pub|2790-2821|def remove_generated_resources() -> None|
|`_render_simple_table`|fn|priv|2822-2852|def _render_simple_table(headers: list[str], rows: list[l...|
|`_line`|fn|priv|2835-2843|def _line(cells: list[str]) -> str|
|`_border`|fn|priv|2844-2846|def _border(left: str, middle: str, right: str) -> str|
|`_provider_skill_installed`|fn|priv|2853-2870|def _provider_skill_installed(provider: str, skill_name: ...|
|`_packaged_prompt_names`|fn|priv|2871-2885|def _packaged_prompt_names() -> list[str]|
|`run_install`|fn|pub|2886-2901|def run_install(args: Namespace) -> None|
|`run_uninstall_providers`|fn|pub|2902-2919|def run_uninstall_providers(args: Namespace) -> None|
|`run_show`|fn|pub|2920-3027|def run_show(args: Namespace) -> None|
|`_maybe_auto_install_after_upgrade`|fn|priv|3028-3052|def _maybe_auto_install_after_upgrade(argv_list: list[str...|
|`run_set_directories`|fn|pub|3053-3116|def run_set_directories(args: Namespace) -> None|
|`_validate_enable_static_check_command_executables`|fn|priv|3117-3120|def _validate_enable_static_check_command_executables(|
|`run`|fn|pub|3149-3348|def run(args: Namespace) -> None|
|`VERBOSE`|var|pub|3169||
|`DEBUG`|var|pub|3170||
|`_format_install_table`|fn|priv|3289-3290|def _format_install_table(|
|`_wrap_cell`|fn|priv|3322-3344|def _wrap_cell(value: str, width: int, allow_wrap: bool) ...|
|`_render_row`|fn|priv|3345-3366|def _render_row(provider: str, skills: str) -> list[str]|
|`_colorize_table_border`|fn|priv|3383-3395|def _colorize_table_border(line: str) -> str|
|`SUPPORTED_EXTENSIONS`|var|pub|3408||
|`_collect_source_files`|fn|priv|3436-3493|def _collect_source_files(src_dirs: list[str], project_ba...|
|`_build_ascii_tree`|fn|priv|3494-3539|def _build_ascii_tree(paths: list[str]) -> str|
|`_emit`|fn|priv|3518-3520|def _emit(|
|`_format_files_structure_markdown`|fn|priv|3540-3554|def _format_files_structure_markdown(files: list[str], pr...|
|`_is_standalone_command`|fn|priv|3555-3566|def _is_standalone_command(args: Namespace) -> bool|
|`_is_project_scan_command`|fn|priv|3567-3584|def _is_project_scan_command(args: Namespace) -> bool|
|`_is_directory_config_command`|fn|priv|3585-3600|def _is_directory_config_command(args: Namespace) -> bool|
|`_require_prj_base`|fn|priv|3601-3619|def _require_prj_base(args: Namespace) -> Path|
|`_require_git_base_value`|fn|priv|3620-3639|def _require_git_base_value(args: Namespace) -> Path|
|`_require_git_base`|fn|priv|3640-3652|def _require_git_base(args: Namespace) -> Path|
|`run_git_check`|fn|pub|3653-3680|def run_git_check(args: Namespace) -> None|
|`run_docs_check`|fn|pub|3681-3710|def run_docs_check(args: Namespace) -> None|
|`run_git_wt_name`|fn|pub|3711-3735|def run_git_wt_name(args: Namespace) -> None|
|`_worktree_path_exists_exact`|fn|priv|3736-3765|def _worktree_path_exists_exact(git_path: Path, target_pa...|
|`_rollback_worktree_create`|fn|priv|3766-3802|def _rollback_worktree_create(git_path: Path, wt_path: Pa...|
|`run_git_wt_create`|fn|pub|3803-3858|def run_git_wt_create(args: Namespace) -> None|
|`run_git_wt_delete`|fn|pub|3859-3927|def run_git_wt_delete(args: Namespace) -> None|
|`run_files_tokens`|fn|pub|3928-3951|def run_files_tokens(files: list[str]) -> None|
|`run_files_references`|fn|pub|3952-3969|def run_files_references(files: list[str]) -> None|
|`run_files_compress`|fn|pub|3970-3989|def run_files_compress(files: list[str], enable_line_numb...|
|`run_files_find`|fn|pub|3990-4019|def run_files_find(args_list: list[str], enable_line_numb...|
|`run_references`|fn|pub|4020-4038|def run_references(args: Namespace) -> None|
|`run_compress_cmd`|fn|pub|4039-4061|def run_compress_cmd(args: Namespace) -> None|
|`run_find`|fn|pub|4062-4092|def run_find(args: Namespace) -> None|
|`run_tokens`|fn|pub|4093-4122|def run_tokens(args: Namespace) -> None|
|`run_files_static_check_cmd`|fn|pub|4123-4189|def run_files_static_check_cmd(files: list[str], args: Na...|
|`run_project_static_check_cmd`|fn|pub|4190-4289|def run_project_static_check_cmd(args: Namespace) -> int|
|`_resolve_project_base`|fn|priv|4290-4302|def _resolve_project_base(args: Namespace) -> Path|
|`_resolve_project_src_dirs`|fn|priv|4303-4333|def _resolve_project_src_dirs(args: Namespace) -> tuple[P...|
|`_is_config_schema_command`|fn|priv|4334-4351|def _is_config_schema_command(args: Namespace) -> bool|
|`run_config_schema_command`|fn|pub|4352-4412|def run_config_schema_command(args: Namespace) -> int|
|`main`|fn|pub|4413-4544|def main(argv: Optional[list[str]] = None) -> int|
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4427||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4434||
|`VERBOSE`|var|pub|4451||
|`DEBUG`|var|pub|4452||


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

# config_cli.py | Python | 1362L | 56 symbols | 12 imports | 59 comments
> Path: `src/usereq/config_cli.py`
- @brief Configuration CLI operations and deterministic tree rendering.
- @details Implements the canonical configuration interface of the useReq CLI:
typed path resolution, strict schema validation, atomic persistence, JSON reads, and the
single recursive tree renderer shared by `--print` and `--info` (SRS-519..SRS-545).
The module never imports `usereq.cli`; callers pass the resolved global configuration path
and translate `ConfigError` into the CLI error channel.
@author useReq
@version 0.75.3

## Imports
```
from __future__ import annotations
import copy
import json
import os
import shlex
import stat
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence
from .config_schema import (
```

## Definitions

- var `BRANCH = "├── "` (L40)
- var `LAST = "└── "` (L43)
- @brief Structural marker for a configuration node with a later sibling (SRS-524)."""
- var `INDENT = "    "` (L46)
- @brief Structural marker for the final configuration sibling at its depth (SRS-524)."""
- var `CONTINUE = "│   "` (L49)
- @brief Exact four-ASCII-space ancestor prefix segment (SRS-524)."""
### class `class ConfigError(Exception)` : Exception (L56-73)
- @brief Sentinel marking an absent optional configuration value (SRS-527)."""
- @brief Expected configuration CLI failure with an English diagnostic.
- @details Carries the diagnostic text and the process exit code consumed by the CLI dispatcher so configuration failures never leak stack traces (SRS-532).
- fn `def __init__(self, message: str, code: int = 1) -> None` `priv` (L63-73)
  - @brief Expected configuration CLI failure with an English diagnostic.
  - @brief Initialize one configuration failure payload.
  - @details Carries the diagnostic text and the process exit code consumed by the CLI
dispatcher so configuration failures never leak stack traces (SRS-532).
  - @param message {str} English diagnostic text written to stderr.
  - @param code {int} Process exit code bound to the failure category.

### class `class RenderNode` `@dataclass` (L75-90)
- @brief One real configuration node of the rendered tree.
- @details Holds the canonical token, canonical path, node kind, the finalized heading line, attached detail blocks, and real child nodes. Tree topology derives exclusively from `children`; details never create structural depth (SRS-524, SRS-525).

### class `class Target` `@dataclass` (L92-106)
- @brief Resolved configuration path describing the operation target.
- @details `op` is one of `node`, `array_item`, `append`, `insert`, `dict_field`, or `map_key`. `container` is the mutable parent list/dictionary, `key` the list index or dictionary key, and `spec` the schema node governing the target value (SRS-533, SRS-534).

### fn `def default_config() -> dict[str, Any]` (L107-121)
- @brief Build the complete default configuration from the canonical schema.
- @details Defaults are deep-copied so callers never mutate the shared schema objects (SRS-521, SRS-529).
- @return {dict[str, Any]} Configuration payload holding every canonical key default.

### fn `def read_raw_payload(config_path: Path) -> dict[str, Any]` (L122-152)
- @brief Read the raw configuration JSON payload without applying defaults.
- @details Only the raw stored payload is returned; unknown keys are preserved here and dropped by the canonical writer (SRS-528, SRS-530).
- @param config_path {Path} Absolute global configuration file path.
- @return {dict[str, Any]} Parsed JSON object; empty dictionary when the file is absent.
- @throws {ConfigError} Raised when the file is unreadable, not JSON, or not a JSON object.

### fn `def _type_name(value: Any) -> str` `priv` (L153-171)
- @brief Return a stable English type name for one JSON value.
- @param value {Any} Parsed JSON value.
- @return {str} JSON type name used inside diagnostics.

### fn `def validate_node(node: SchemaNode, value: Any, path: str) -> None` (L172-266)
- @brief Validate one value against its schema node, including nested values.
- @details Covers primitives, enums, arrays, map keys, fixed-field dictionaries, required fields, and the Command `cmd` cross-field constraint (SRS-530, SRS-536).
- @param node {SchemaNode} Schema node governing the value.
- @param value {Any} Parsed JSON value to validate.
- @param path {str} Canonical path used inside diagnostics.
- @return {None} Function return value.
- @throws {ConfigError} Raised with an English diagnostic on any schema violation.

### fn `def normalize_config(payload: dict[str, Any]) -> dict[str, Any]` (L267-286)
- @brief Merge a raw payload over the schema defaults and validate stored values.
- @details Unknown top-level keys are outside the canonical schema and are therefore ignored here and dropped by `write_config` (SRS-288, SRS-530).
- @param payload {dict[str, Any]} Raw stored JSON payload.
- @return {dict[str, Any]} Effective configuration holding every canonical key.
- @throws {ConfigError} Raised when a stored canonical value violates the schema.

### fn `def load_effective_config(config_path: Path) -> dict[str, Any]` (L287-296)
- @brief Load and validate the effective configuration for one configuration command.
- @param config_path {Path} Absolute global configuration file path.
- @return {dict[str, Any]} Effective configuration with defaults applied.
- @throws {ConfigError} Raised when the file is unreadable or schema-invalid.

### fn `def write_config(config_path: Path, config: dict[str, Any]) -> None` (L297-342)
- @brief Atomically persist the canonical configuration payload.
- @details Creates missing parent directories, writes a same-directory temporary file, flushes and fsyncs it, preserves the existing file mode, atomically replaces the target, and fsyncs the parent directory (SRS-529, SRS-531).
- @param config_path {Path} Absolute global configuration file path.
- @param config {dict[str, Any]} Fully validated effective configuration.
- @return {None} Function return value.
- @throws {ConfigError} Raised when the write fails; the original file is preserved.

### fn `def ensure_config_file(config_path: Path) -> None` (L343-360)
- @brief Bootstrap the global configuration file from schema defaults when absent.
- @details Missing parent directories are created and the file is initialized from the canonical schema defaults; an existing file is never overwritten (SRS-529).
- @param config_path {Path} Absolute global configuration file path.
- @return {None} Function return value.
- @throws {ConfigError} Raised when the path is a directory or the bootstrap write fails.

### fn `def _parse_index(token: str, path: str) -> int` `priv` (L361-376)
- @brief Parse one non-negative decimal array index token.
- @param token {str} Raw path token.
- @param path {str} Canonical path used inside diagnostics.
- @return {int} Parsed zero-based index.
- @throws {ConfigError} Raised for negative, signed, or non-decimal tokens.

### fn `def _out_of_range(owner_path: str, index: int, length: int) -> ConfigError` `priv` (L377-391)
- @brief Build the out-of-range diagnostic for an array access.
- @param owner_path {str} Canonical path of the owning array parameter.
- @param index {int} Rejected index.
- @param length {int} Current array length.
- @return {ConfigError} English diagnostic describing the valid range and append option.

### fn `def _child_of_section(spec: SchemaNode, token: str, path: str) -> SchemaNode` `priv` (L392-408)
- @brief Resolve one section/dictionary field token or raise an unknown-token error.
- @param spec {SchemaNode} Section or dictionary node holding candidate fields.
- @param token {str} Exact canonical field token.
- @param path {str} Canonical path used inside diagnostics.
- @return {SchemaNode} Matching field node.
- @throws {ConfigError} Raised when the token is not a canonical schema token.

### fn `def resolve_target(config: dict[str, Any], path: str) -> Target` (L409-539)
- @brief Resolve a canonical colon-separated path against the configuration schema.
- @details Paths are resolved token by token against the schema, never against displayed strings; `append`, `+`, and `insert:<Idx>` are recognized only inside array paths (SRS-520, SRS-533, SRS-534).
- @param config {dict[str, Any]} Effective configuration used as the resolution root.
- @param path {str} Canonical colon-separated configuration path.
- @return {Target} Resolved operation target.
- @throws {ConfigError} Raised for empty tokens, unknown tokens, invalid indices, out-of-range indices, and missing dynamic map keys.

### fn `def parse_cli_value(` (L540-541)

### fn `def get_value(config: dict[str, Any], path: str) -> Any` (L588-609)
- @brief Parse one CLI value into the schema type of the target node.
- @brief Read the effective value addressed by one canonical path.
- @details Plain strings are taken verbatim; booleans, arrays, maps, dictionaries, and
sections require JSON text so numbers and booleans stay typed (SRS-530, SRS-535).
- @param spec {SchemaNode} Schema node governing the target value.
- @param text {str} Raw CLI value text.
- @param path {str} Canonical path used inside diagnostics.
- @param reject_collections {bool} True for single-item array writes; rejects JSON arrays
and objects supplied where exactly one item is required.
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @return {Any} Parsed and validated typed value.
- @return {Any} JSON-serializable value addressed by the path.
- @throws {ConfigError} Raised for malformed JSON, invalid types, or schema violations.
- @throws {ConfigError} Raised for invalid paths, absent values, and write-only operations.

### fn `def apply_set(config: dict[str, Any], path: str, text: str) -> dict[str, Any]` (L610-651)
- @brief Apply one `--set` operation to a copy of the effective configuration.
- @details Supports primitives, whole branches, whole arrays/maps, single array items, append and insert operations, dictionary fields, and dynamic map keys (SRS-530, SRS-533, SRS-534, SRS-535).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @param text {str} Raw CLI value text.
- @return {dict[str, Any]} New validated configuration payload.
- @throws {ConfigError} Raised before mutation when the path or value is invalid.

### fn `def apply_unset(config: dict[str, Any], path: str) -> dict[str, Any]` (L652-695)
- @brief Apply one `--unset` operation to a copy of the effective configuration.
- @details Restores declared schema defaults, deletes optional fields and map keys, and removes array elements while keeping indices contiguous (SRS-530, SRS-533, SRS-536).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @return {dict[str, Any]} New validated configuration payload.
- @throws {ConfigError} Raised for write-only operations, absent keys, and required fields.

### fn `def _display_width(text: str) -> int` `priv` (L696-709)
- @brief Measure the terminal display width of one table cell.
- @param text {str} Sanitized cell text.
- @return {int} Display column count honoring wide and combining characters.

### fn `def _sanitize_cell(text: str) -> str` `priv` (L710-730)
- @brief Escape control characters so one cell stays on one physical line.
- @param text {str} Raw cell payload.
- @return {str} Printable single-line cell text.

### fn `def format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]` (L731-767)
- @brief Render one rectangular Unicode box-drawing table.
- @details Column widths derive from the maximum display width of the header and every formatted cell; all borders share the same column boundaries (SRS-539).
- @param headers {Sequence[str]} Column header labels.
- @param rows {Sequence[Sequence[str]]} Cell values matching the header count.
- @return {list[str]} Physical table lines without structural tree prefixes.

### fn `def border(left: str, middle: str, right: str) -> str` (L750-753)
- @brief Render one rectangular Unicode box-drawing table.
- @brief Build one horizontal table border line.
- @details Column widths derive from the maximum display width of the header and every
formatted cell; all borders share the same column boundaries (SRS-539).
- @param headers {Sequence[str]} Column header labels.
- @param rows {Sequence[Sequence[str]]} Cell values matching the header count.
- @return {list[str]} Physical table lines without structural tree prefixes.

### fn `def line(cells: Sequence[str]) -> str` (L754-761)
- @brief Build one padded table content line.

### fn `def render_tree(root: RenderNode) -> list[str]` (L768-783)
- @brief Render one configuration tree with the mandatory prefix algorithm.
- @details The display root has no structural marker and attached root details use a four-space indent; every real child is emitted by `_emit_node` (SRS-524, SRS-525).
- @param root {RenderNode} Display root of the requested tree.
- @return {list[str]} Complete physical output lines.

### fn `def _emit_node(` `priv` (L784-788)

### fn `def render_text(root: RenderNode) -> str` (L816-824)
- @brief Emit one real configuration node and its attached details recursively.
- @brief Render one configuration tree as newline-terminated text.
- @details Heading prefix and detail prefix derive only from real sibling topology;
details never receive a structural marker or additional depth (SRS-524, SRS-525).
- @param node {RenderNode} Node to emit.
- @param ancestor_has_next {list[bool]} Per-ancestor later-sibling flags.
- @param is_last {bool} True when the node is the final sibling at its depth.
- @param lines {list[str]} Accumulated output lines.
- @param root {RenderNode} Display root of the requested tree.
- @return {None} Function return value.
- @return {str} Complete output text without a trailing newline.

### fn `def _json_value(value: Any) -> str` `priv` (L825-833)
- @brief Encode one value as JSON text for display.
- @param value {Any} JSON-serializable value.
- @return {str} JSON-encoded text with non-ASCII characters preserved.

### fn `def _shell(value: str) -> str` `priv` (L834-842)
- @brief Shell-quote one literal value for a copyable command example.
- @param value {str} Literal value.
- @return {str} POSIX shell-quoted value.

### fn `def _example_item(node: SchemaNode) -> str` `priv` (L843-853)
- @brief Choose a schema-valid example value for one collection item.
- @param node {SchemaNode} Item schema node.
- @return {str} Example value text.

### fn `def _example_key(map_node: SchemaNode) -> str` `priv` (L854-864)
- @brief Choose a schema-valid example key for one dynamic map.
- @param map_node {SchemaNode} Map schema node.
- @return {str} Example key text.

### fn `def _print_marker(spec: SchemaNode, value: Any) -> str` `priv` (L872-885)
- @brief Schema-valid alternative example values for string parameters (SRS-541)."""
- @brief Build the default/custom status marker of one primitive parameter.
- @param spec {SchemaNode} Parameter schema node.
- @param value {Any} Current typed value.
- @return {str} Empty text for nodes without defaults, otherwise the status marker.

### fn `def _collection_summary(spec: SchemaNode, value: Any, path: str) -> str` `priv` (L886-918)
- @brief Build the `--print` value summary of one collection parameter.
- @details Empty collections emit a complete-path action hint instead of an empty table (SRS-537, SRS-539).
- @param spec {SchemaNode} Collection schema node.
- @param value {Any} Current collection value.
- @param path {str} Canonical parameter path.
- @return {str} Collection summary text.

### fn `def _example_map_value(item: SchemaNode) -> str` `priv` (L919-933)
- @brief Build one schema-valid example JSON text for a map value.
- @param item {SchemaNode} Map value schema node.
- @return {str} JSON text accepted by the map value schema.

### fn `def _value_cell(spec: SchemaNode, value: Any) -> str` `priv` (L934-948)
- @brief Render one table cell value for a configuration value.
- @param spec {SchemaNode} Schema node of the value.
- @param value {Any} JSON-serializable value.
- @return {str} Single-line cell text.

### fn `def _print_parameter_details(` `priv` (L949-950)

### fn `def _dictionary_fields(spec: SchemaNode) -> tuple[SchemaNode, ...]` `priv` (L994-1006)
- @brief Build the attached `--print` details of one parameter node.
- @brief Resolve the fixed field set documented by an `Item Schema` table.
- @details Non-empty collections attach measured rectangular tables; scalars attach no
details (SRS-537, SRS-539).
- @param spec {SchemaNode} Parameter schema node.
- @param value {Any} Current typed value.
- @param path {str} Canonical parameter path.
- @param spec {SchemaNode} Array or dictionary schema node.
- @return {list[list[str]]} Attached detail blocks rendered with the owner prefix.
- @return {tuple[SchemaNode, ...]} Fixed fields, or an empty tuple for primitives.

### fn `def _item_schema_table(fields: Sequence[SchemaNode]) -> list[str]` `priv` (L1007-1036)
- @brief Render the `Item Schema` table of one fixed-field dictionary.
- @param fields {Sequence[SchemaNode]} Fixed field schema nodes.
- @return {list[str]} Table lines.

### fn `def _array_examples(spec: SchemaNode, path: str) -> list[list[str]]` `priv` (L1037-1073)
- @brief Build the attached `--info` command examples of one array parameter.
- @details Single-item operations receive exactly one JSON item; the whole-array overwrite receives a JSON array (SRS-535, SRS-541).
- @param spec {SchemaNode} Array schema node.
- @param path {str} Canonical array path.
- @return {list[list[str]]} Detail blocks with complete copyable commands.

### fn `def _info_parameter_details(spec: SchemaNode, path: str) -> list[list[str]]` `priv` (L1074-1152)
- @brief Build the attached `--info` details of one parameter node.
- @details Required dictionary fields without defaults never advertise a reset command (SRS-536, SRS-538, SRS-541).
- @param spec {SchemaNode} Parameter schema node.
- @param path {str} Canonical parameter path.
- @return {list[list[str]]} Attached detail blocks with defaults, commands, and tables.

### fn `def _print_parameter_heading(spec: SchemaNode, value: Any, token: str, path: str) -> str` `priv` (L1153-1169)
- @brief Build the `--print` heading of one parameter node.
- @param spec {SchemaNode} Parameter schema node.
- @param value {Any} Current typed value.
- @param token {str} Exact canonical node token.
- @param path {str} Canonical node path.
- @return {str} Heading text without structural prefix.

### fn `def _info_parameter_heading(spec: SchemaNode, token: str) -> str` `priv` (L1170-1182)
- @brief Build the `--info` heading of one parameter node.
- @param spec {SchemaNode} Parameter schema node.
- @param token {str} Exact canonical node token.
- @return {str} `Token - [Type: constraints] Description` heading text.

### fn `def _build_node(` `priv` (L1183-1188)

### fn `def _section_heading(path: str, info: bool) -> str` `priv` (L1235-1247)
- @brief Build one real configuration node for the requested display mode.
- @brief Build the section heading carrying the canonical path badge.
- @details Only sections expose real child nodes; metadata and tables stay attached
details (SRS-522, SRS-525, SRS-540).
- @param spec {SchemaNode} Schema node of the configuration value.
- @param value {Any} Current effective value.
- @param token {str} Exact canonical node token.
- @param path {str} Canonical node path.
- @param info {bool} True for `--info`; False for `--print`.
- @param path {str} Canonical section path.
- @param info {bool} True for `--info`; False for `--print`.
- @return {RenderNode} Renderable node with attached details and real children.
- @return {str} `Token - [Path: <full canonical path>]` heading text.

### fn `def build_full_tree(config: dict[str, Any], info: bool) -> RenderNode` (L1248-1268)
- @brief Build the complete configuration tree for `--print` or `--info`.
- @param config {dict[str, Any]} Effective configuration.
- @param info {bool} True for `--info`; False for `--print`.
- @return {RenderNode} Virtual display root holding the `Configuration` section.

### fn `def build_subtree(config: dict[str, Any], path: str, info: bool) -> RenderNode` (L1269-1292)
- @brief Build the requested subtree or parameter display.
- @details No ancestors are invented; the requested node becomes the display root with four-space-indented details and normally rendered real children (SRS-526).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @param info {bool} True for `--info`; False for `--print`.
- @return {RenderNode} Requested node as the unconnected display root.
- @throws {ConfigError} Raised for unknown paths and non-displayable collection elements.

### fn `def handle_get(config_path: Path, path: str) -> str` (L1293-1304)
- @brief Execute one `--get` read and return JSON text.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @return {str} JSON-encoded value text.
- @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.

### fn `def handle_set(config_path: Path, path: str, text: str) -> None` (L1305-1318)
- @brief Execute one `--set` write.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @param text {str} Raw CLI value text.
- @return {None} Function return value.
- @throws {ConfigError} Raised before mutation when the operation is invalid.

### fn `def handle_unset(config_path: Path, path: str) -> None` (L1319-1331)
- @brief Execute one `--unset` write.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @return {None} Function return value.
- @throws {ConfigError} Raised before mutation when the operation is invalid.

### fn `def handle_print_raw(config_path: Path) -> bytes` (L1332-1348)
- @brief Return the unmodified on-disk configuration file bytes.
- @details Never reformats, prepends a heading, or appends explanatory text (SRS-528).
- @param config_path {Path} Absolute global configuration file path.
- @return {bytes} Raw file bytes exactly as stored.
- @throws {ConfigError} Raised when the bootstrapped file cannot be read.

### fn `def handle_display(config_path: Path, path: Optional[str], info: bool) -> str` (L1349-1363)
- @brief Execute one `--print` or `--info` display request.
- @param config_path {Path} Absolute global configuration file path.
- @param path {Optional[str]} Requested canonical path; None renders the full tree.
- @param info {bool} True for `--info`; False for `--print`.
- @return {str} Rendered tree text without a trailing newline.
- @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`BRANCH`|var|pub|40||
|`LAST`|var|pub|43||
|`INDENT`|var|pub|46||
|`CONTINUE`|var|pub|49||
|`ConfigError`|class|pub|56-73|class ConfigError(Exception)|
|`ConfigError.__init__`|fn|priv|63-73|def __init__(self, message: str, code: int = 1) -> None|
|`RenderNode`|class|pub|75-90|class RenderNode|
|`Target`|class|pub|92-106|class Target|
|`default_config`|fn|pub|107-121|def default_config() -> dict[str, Any]|
|`read_raw_payload`|fn|pub|122-152|def read_raw_payload(config_path: Path) -> dict[str, Any]|
|`_type_name`|fn|priv|153-171|def _type_name(value: Any) -> str|
|`validate_node`|fn|pub|172-266|def validate_node(node: SchemaNode, value: Any, path: str...|
|`normalize_config`|fn|pub|267-286|def normalize_config(payload: dict[str, Any]) -> dict[str...|
|`load_effective_config`|fn|pub|287-296|def load_effective_config(config_path: Path) -> dict[str,...|
|`write_config`|fn|pub|297-342|def write_config(config_path: Path, config: dict[str, Any...|
|`ensure_config_file`|fn|pub|343-360|def ensure_config_file(config_path: Path) -> None|
|`_parse_index`|fn|priv|361-376|def _parse_index(token: str, path: str) -> int|
|`_out_of_range`|fn|priv|377-391|def _out_of_range(owner_path: str, index: int, length: in...|
|`_child_of_section`|fn|priv|392-408|def _child_of_section(spec: SchemaNode, token: str, path:...|
|`resolve_target`|fn|pub|409-539|def resolve_target(config: dict[str, Any], path: str) -> ...|
|`parse_cli_value`|fn|pub|540-541|def parse_cli_value(|
|`get_value`|fn|pub|588-609|def get_value(config: dict[str, Any], path: str) -> Any|
|`apply_set`|fn|pub|610-651|def apply_set(config: dict[str, Any], path: str, text: st...|
|`apply_unset`|fn|pub|652-695|def apply_unset(config: dict[str, Any], path: str) -> dic...|
|`_display_width`|fn|priv|696-709|def _display_width(text: str) -> int|
|`_sanitize_cell`|fn|priv|710-730|def _sanitize_cell(text: str) -> str|
|`format_table`|fn|pub|731-767|def format_table(headers: Sequence[str], rows: Sequence[S...|
|`border`|fn|pub|750-753|def border(left: str, middle: str, right: str) -> str|
|`line`|fn|pub|754-761|def line(cells: Sequence[str]) -> str|
|`render_tree`|fn|pub|768-783|def render_tree(root: RenderNode) -> list[str]|
|`_emit_node`|fn|priv|784-788|def _emit_node(|
|`render_text`|fn|pub|816-824|def render_text(root: RenderNode) -> str|
|`_json_value`|fn|priv|825-833|def _json_value(value: Any) -> str|
|`_shell`|fn|priv|834-842|def _shell(value: str) -> str|
|`_example_item`|fn|priv|843-853|def _example_item(node: SchemaNode) -> str|
|`_example_key`|fn|priv|854-864|def _example_key(map_node: SchemaNode) -> str|
|`_print_marker`|fn|priv|872-885|def _print_marker(spec: SchemaNode, value: Any) -> str|
|`_collection_summary`|fn|priv|886-918|def _collection_summary(spec: SchemaNode, value: Any, pat...|
|`_example_map_value`|fn|priv|919-933|def _example_map_value(item: SchemaNode) -> str|
|`_value_cell`|fn|priv|934-948|def _value_cell(spec: SchemaNode, value: Any) -> str|
|`_print_parameter_details`|fn|priv|949-950|def _print_parameter_details(|
|`_dictionary_fields`|fn|priv|994-1006|def _dictionary_fields(spec: SchemaNode) -> tuple[SchemaN...|
|`_item_schema_table`|fn|priv|1007-1036|def _item_schema_table(fields: Sequence[SchemaNode]) -> l...|
|`_array_examples`|fn|priv|1037-1073|def _array_examples(spec: SchemaNode, path: str) -> list[...|
|`_info_parameter_details`|fn|priv|1074-1152|def _info_parameter_details(spec: SchemaNode, path: str) ...|
|`_print_parameter_heading`|fn|priv|1153-1169|def _print_parameter_heading(spec: SchemaNode, value: Any...|
|`_info_parameter_heading`|fn|priv|1170-1182|def _info_parameter_heading(spec: SchemaNode, token: str)...|
|`_build_node`|fn|priv|1183-1188|def _build_node(|
|`_section_heading`|fn|priv|1235-1247|def _section_heading(path: str, info: bool) -> str|
|`build_full_tree`|fn|pub|1248-1268|def build_full_tree(config: dict[str, Any], info: bool) -...|
|`build_subtree`|fn|pub|1269-1292|def build_subtree(config: dict[str, Any], path: str, info...|
|`handle_get`|fn|pub|1293-1304|def handle_get(config_path: Path, path: str) -> str|
|`handle_set`|fn|pub|1305-1318|def handle_set(config_path: Path, path: str, text: str) -...|
|`handle_unset`|fn|pub|1319-1331|def handle_unset(config_path: Path, path: str) -> None|
|`handle_print_raw`|fn|pub|1332-1348|def handle_print_raw(config_path: Path) -> bytes|
|`handle_display`|fn|pub|1349-1363|def handle_display(config_path: Path, path: Optional[str]...|


---

# config_schema.py | Python | 336L | 20 symbols | 3 imports | 27 comments
> Path: `src/usereq/config_schema.py`
- @brief Canonical configuration schema for the user-global useReq configuration file.
- @details Single source of truth for the persisted configuration parameter set: section and
parameter tokens, node kinds, defaults, constraints, and canonical paths. The path resolver,
typed value parser, tree renderer, and help generator of `usereq.config_cli` consume this
schema, so `--print`, `--info`, `--get`, `--set`, and `--unset` never maintain duplicated
parameter lists (SRS-521, SRS-542).
@author useReq
@version 0.75.3

## Imports
```
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
```

## Definitions

- var `KIND_SECTION = "section"` (L18)
- var `KIND_STRING = "string"` (L21)
- @brief Schema node kind for a named configuration section (SRS-523)."""
- var `KIND_BOOLEAN = "boolean"` (L24)
- @brief Schema node kind for a plain text value (SRS-521)."""
- var `KIND_ARRAY = "array"` (L27)
- @brief Schema node kind for a JSON boolean value (SRS-521)."""
- var `KIND_MAP = "map"` (L30)
- @brief Schema node kind for an ordered list value (SRS-533, SRS-534)."""
- var `KIND_DICTIONARY = "dictionary"` (L33)
- @brief Schema node kind for a dynamic string-keyed dictionary value (SRS-521)."""
- var `DEFAULT_DOCS_DIR = "usereq/docs"` (L39)
- @brief Sentinel marking a schema node without a declared default value (SRS-536)."""
- var `DEFAULT_TESTS_DIR = "tests"` (L42)
- @brief Default docs-dir value when the configuration stores no docs-dir entry (SRS-359)."""
- var `DEFAULT_SRC_DIRS = ("src",)` (L45)
- @brief Default tests-dir value when the configuration stores no tests-dir entry (SRS-361)."""
- var `DEFAULT_AUTO_INSTALL = True` (L48)
- @brief Default src-dir list when the configuration stores no src-dir entry (SRS-362)."""
- var `VALID_PROVIDER_NAMES = (` (L51)
- @brief Default auto-install state when the configuration stores no entry (SRS-420)."""
- var `STATIC_CHECK_LANGUAGES = (` (L73)
- @brief Short English meaning rendered by the providers `Allowed Values` table (SRS-538)."""
- var `STATIC_CHECK_MODULES = ("Dummy", "Pylance", "Ruff", "Command")` (L97)
- @brief Canonical static-check language keys usable as `static-check` map keys (SRS-249, SRS-540)."""
### class `class SchemaNode` `@dataclass(frozen=True)` (L135-166)
- @brief Typed schema node describing one configuration token or collection element.
- @details Nodes form an ordered tree rooted at `CONFIG_SECTION`. A node carries the exact canonical token, the node kind, a concise English description, the textual type label and constraints used by `--info`, the typed default (or `NO_DEFAULT`), enumeration metadata, and the child collection definitions used by validation and rendering (SRS-521, SRS-522, SRS-538).
- fn `def has_default(self) -> bool` (L162-166)
  - @brief Return True when the node declares a typed default value (SRS-536).

### fn `def _entry_fields() -> tuple[SchemaNode, ...]` `priv` (L167-208)
- @brief Build the fixed field set of one static-check dictionary entry (SRS-540).
- @return {tuple[SchemaNode, ...]} Ordered `module`, `cmd`, and `params` field nodes.

- var `CONFIG_SECTION = SchemaNode(` (L229)
- @brief Array of static-check entries stored under one canonical language key (SRS-540)."""
- var `ROOT_LABEL = "Application_Configuration"` (L306)
- @brief Root schema section holding every persisted configuration parameter (SRS-521)."""
### fn `def find_field(node: SchemaNode, token: str) -> Optional[SchemaNode]` (L313-327)
- @brief Canonical persisted configuration keys in schema order (SRS-288, SRS-521)."""
- @brief Look up one ordered child field of a section or dictionary node.
- @details Matching is case-sensitive and byte-exact so path resolution never depends on displayed labels or decorative text (SRS-520, SRS-522).
- @param node {SchemaNode} Section or dictionary node providing the candidate fields.
- @param token {str} Exact canonical field token to resolve.
- @return {Optional[SchemaNode]} Matching field node, or None when the token is unknown.

### fn `def canonical_path(tokens: tuple[str, ...]) -> str` (L328-337)
- @brief Join canonical path tokens with the colon separator.
- @details Empty tokens are rejected by the resolver, so joining never produces an ambiguous empty path segment (SRS-520).
- @param tokens {tuple[str, ...]} Ordered canonical path tokens without the virtual root.
- @return {str} Canonical colon-separated configuration path.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`KIND_SECTION`|var|pub|18||
|`KIND_STRING`|var|pub|21||
|`KIND_BOOLEAN`|var|pub|24||
|`KIND_ARRAY`|var|pub|27||
|`KIND_MAP`|var|pub|30||
|`KIND_DICTIONARY`|var|pub|33||
|`DEFAULT_DOCS_DIR`|var|pub|39||
|`DEFAULT_TESTS_DIR`|var|pub|42||
|`DEFAULT_SRC_DIRS`|var|pub|45||
|`DEFAULT_AUTO_INSTALL`|var|pub|48||
|`VALID_PROVIDER_NAMES`|var|pub|51||
|`STATIC_CHECK_LANGUAGES`|var|pub|73||
|`STATIC_CHECK_MODULES`|var|pub|97||
|`SchemaNode`|class|pub|135-166|class SchemaNode|
|`SchemaNode.has_default`|fn|pub|162-166|def has_default(self) -> bool|
|`_entry_fields`|fn|priv|167-208|def _entry_fields() -> tuple[SchemaNode, ...]|
|`CONFIG_SECTION`|var|pub|229||
|`ROOT_LABEL`|var|pub|306||
|`find_field`|fn|pub|313-327|def find_field(node: SchemaNode, token: str) -> Optional[...|
|`canonical_path`|fn|pub|328-337|def canonical_path(tokens: tuple[str, ...]) -> str|


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

