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

# cli.py | Python | 4711L | 173 symbols | 36 imports | 228 comments
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
import tomllib
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
from .static_check import (
from .static_check import run_static_check
import traceback
```

## Definitions

- var `REPO_ROOT = Path(__file__).resolve().parents[2]` (L42)
- var `RESOURCE_ROOT = Path(os.path.abspath(__file__)).parent / "resources"` (L45)
- @brief The absolute path to the repository root."""
- var `VERBOSE = False` (L48)
- @brief The absolute lexical path of the packaged resources directory; never resolves symbolic links (SRS-505)."""
- var `DEBUG = False` (L51)
- @brief Whether verbose output is enabled."""
- var `REQUIREMENTS_TEMPLATE_NAME = "Requirements_Template.md"` (L54)
- @brief Whether debug output is enabled."""
- var `PERSISTED_CONFIG_KEYS = (` (L57)
- @brief Name of the packaged requirements template file."""
- var `AUTO_INSTALL_CONFIG_KEY = "auto-install"` (L67)
- @brief Canonical keys persisted in the user-global configuration file (SRS-288)."""
- var `VALID_PROVIDERS = frozenset(VALID_PROVIDER_NAMES)` (L70)
- @brief Configuration key storing the auto-install enabled flag (SRS-420)."""
- var `GLOBAL_CONFIG_DIRNAME = ".config"` (L73)
- @brief Valid provider names accepted by ``--enable PROVIDER`` and ``--disable PROVIDER`` (SRS-275, SRS-364)."""
- var `GLOBAL_CONFIG_APP_DIRNAME = "usereq"` (L76)
- @brief Root configuration directory name located under the user HOME (SRS-387)."""
- var `GLOBAL_CONFIG_FILENAME = "config.json"` (L79)
- @brief Application subdirectory name under ``~/.config`` (SRS-387)."""
### fn `def home_dir() -> Path` (L83-93)
- @brief Canonical user-global configuration JSON filename (SRS-387)."""
- @brief Resolve the user HOME directory used for user-level CLI configuration.
- @details Single indirection point over ``Path.home()`` so tests and embedders can redirect all user-level provider and configuration paths deterministically.
- @return {Path} Absolute user HOME directory path.
- @satisfies SRS-381

### fn `def get_global_config_path() -> Path` (L94-109)
- @brief Resolve the single user-global configuration file path.
- @details Builds ``~/.config/usereq/config.json`` from the effective home directory returned by :func:`home_dir`.
- @return {Path} Absolute path of the user-global configuration file.
- @satisfies SRS-387

### fn `def guidelines_dir() -> Path` (L110-122)
- @brief Resolve the packaged guidelines directory of the running installation.
- @details Composes the packaged resources root of the running installation with the non-configurable ``guidelines`` suffix so installed skills reference the resources shipped with this installation instead of any external copy (SRS-360, SRS-497); composition is lexical and never resolves symbolic links (SRS-505).
- @return {Path} Absolute path of the packaged guidelines directory.
- @satisfies SRS-360, SRS-497, SRS-505

### fn `def templates_dir() -> Path` (L123-135)
- @brief Resolve the packaged document-template directory of the running installation.
- @details Composes the packaged resources root of the running installation with the non-configurable ``templates`` suffix feeding the ``%%TEMPLATE_PATH%%`` substitution so installed skills reference the templates shipped with this installation (SRS-498); composition is lexical and never resolves symbolic links (SRS-505).
- @return {Path} Absolute path of the packaged templates directory.
- @satisfies SRS-495, SRS-498, SRS-505

### fn `def format_home_relative_path(path: Path) -> str` (L136-159)
- @brief Render an absolute path in ``~/`` home-relative form.
- @details Returns ``~`` for the HOME directory, ``~/<rel>`` with POSIX separators for any path under HOME, and the absolute string for paths outside HOME. Normalization is strictly lexical via ``os.path.abspath``: symbolic links are never resolved, so a symlinked ``~/.config`` still renders as ``~/.config/...`` and the hardcoded provider skills roots of SRS-382..SRS-386, SRS-486, and SRS-493 render verbatim (SRS-385, SRS-463). No filesystem access occurs beyond path composition. Complexity: O(1).
- @param path {Path} Absolute path to render.
- @return {str} Home-relative rendering when the path is under HOME, otherwise absolute.
- @satisfies SRS-385, SRS-402, SRS-403, SRS-463

### fn `def provider_skills_root(provider: str) -> Path` (L160-193)
- @brief Resolve the user-level skills installation root for one provider.
- @details Maps ``provider`` to its hardcoded user-level skills directory under the user HOME (antigravity -> ``~/.gemini/config/skills``, claude -> ``~/.claude/skills``, codex -> ``~/.codex/skills``, copilot -> ``~/.copilot/skills``, openclaw -> ``~/.openclaw/workspace/skills``, opencode -> ``~/.config/opencode/skills``, pi -> ``~/.pi/agent/skills``). Paths are computed lazily from :func:`home_dir` so HOME redirection stays consistent across a single process run. Skills are the only supported artifact type (SRS-381).
- @param provider {str} Provider selector from ``{antigravity, claude, codex, copilot, openclaw, opencode, pi}``.
- @return {Path} Absolute user-level skills target directory for the provider.
- @throws {ReqError} Raised when the provider defines no user-level skills root.
- @satisfies SRS-381, SRS-382, SRS-383, SRS-384, SRS-385, SRS-386, SRS-486, SRS-493

### fn `def provider_skills_path(provider: str) -> str` (L194-207)
- @brief Render the home-relative hardcoded skills root shown in the `show` Providers table.
- @details Joins the effective user HOME with the hardcoded provider skills root from :func:`provider_skills_root` (SRS-382..SRS-386, SRS-486, SRS-493) and renders the result through :func:`format_home_relative_path` as a `~/`-prefixed POSIX path. Complexity: O(1). No side effects.
- @param provider {str} Provider selector from ``{antigravity, claude, codex, copilot, openclaw, opencode, pi}``.
- @return {str} Home-relative skills installation root such as ``~/.pi/agent/skills``.
- @satisfies SRS-462, SRS-463, SRS-485

- var `INVALID_WT_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]')` (L208)
### fn `def validate_provider_name(name: str) -> str` (L212-234)
- @brief Regex matching characters invalid in both Linux and Windows directory names."""
- @brief Validate one provider name token supplied via ``--enable`` or ``--disable``.
- @details Normalizes the token to lowercase and validates membership in :data:`VALID_PROVIDERS`; unknown tokens raise a deterministic English `ReqError` payload identifying the invalid token (SRS-278, SRS-422). Complexity: O(1). No side effects.
- @param name {str} Raw provider name token as supplied on the command line or read from the persisted `"providers"` array.
- @return {str} Normalized lowercase provider name.
- @throws {ReqError} Raised with exit code 1 when the token is not a valid provider.
- @satisfies SRS-275, SRS-278, SRS-364, SRS-422

### fn `def resolve_provider_configs(` (L235-236)

- var `ANSI_BRIGHT_RED = "\033[91m"` (L259)
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
- var `ANSI_BRIGHT_GREEN = "\033[92m"` (L262)
- @brief ANSI escape prefix for bright red terminal output."""
- var `ANSI_RESET = "\033[0m"` (L265)
- @brief ANSI escape prefix for bright green terminal output."""
- var `RELEASE_CHECK_TIMEOUT_SECONDS = 2.0` (L268)
- @brief ANSI escape sequence that resets terminal style."""
- var `RELEASE_CHECK_IDLE_DELAY_SECONDS = 3600` (L271)
- @brief Hardcoded default timeout for startup release-check HTTP calls."""
- var `RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS = 86400` (L274)
- @brief Hardcoded startup release-check idle-delay in seconds."""
- var `TOOL_PROGRAM_NAME = "cli-usereq"` (L277)
- @brief Hardcoded startup release-check idle-delay in seconds for API rate limiting."""
- var `TOOL_RECEIPT_FILENAME = "uv-receipt.toml"` (L283)
- @brief Hardcoded uv tool requirement name matching the PyPI distribution name of this package (SRS-435).
- @details Used as the target of `uv tool install`/`uv tool uninstall` commands; it matches the
`[project].name` distribution name registered in the PyPI trusted publisher for repository
`Ogekuri/CLI-useReq` (SRS-343, SRS-344, SRS-433, SRS-435)."""
- var `NON_REGISTRY_REQUIREMENT_KEYS = ("git", "url", "path", "editable", "rev", "tag", "branch")` (L286)
- @brief Canonical uv tool receipt filename recording the installed requirement source (SRS-343, SRS-440)."""
- var `RELEASE_CHECK_PROGRAM_NAME = "usereq"` (L292)
- @brief Receipt requirement keys marking a uv tool source other than the PyPI index (SRS-440).
- @details `uv` records the resolved source of every installed tool requirement in its receipt;
any of these keys means the requirement does not resolve from the PyPI index, so the plain
`--upgrade` form cannot replace the installed distribution (SRS-343, SRS-440)."""
- var `GITHUB_REPOSITORY_OWNER = "Ogekuri"` (L297)
- @brief Program identifier used in release-check idle-state cache directory.
- @details Fixes the idle-state cache path to `~/.cache/usereq/check_version_idle-time.json`
independently of the PyPI distribution name `cli-usereq` (SRS-345, SRS-346)."""
- var `GITHUB_REPOSITORY_NAME = "CLI-useReq"` (L300)
- @brief Hardcoded GitHub owner used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME = ".cache"` (L303)
- @brief Hardcoded GitHub repository used by upgrade and release-check endpoints."""
- var `RELEASE_CHECK_IDLE_FILENAME = "check_version_idle-time.json"` (L306)
- @brief Root cache directory name located under `$HOME`."""
- var `GITHUB_RELEASES_LATEST_URL = (` (L309)
- @brief Canonical release-check idle-state JSON filename."""
- var `GITHUB_UPGRADE_SOURCE = (` (L318)
- @brief Hardcoded GitHub API endpoint queried by `--ver`/`--version` and `--upgrade --develop` (SRS-442, SRS-451).
- @details Intermediate and test releases are published on GitHub; this endpoint resolves the
latest tagged release independently of the branch holding the tag. The default `--upgrade`
path never queries it and installs from the PyPI index (SRS-343, SRS-440)."""
- var `PYPI_PROJECT_JSON_URL = "https://pypi.org/pypi/cli-usereq/json"` (L325)
- @brief Hardcoded git source base used only by `--upgrade --develop` (alias `--dev`) installs (SRS-440, SRS-445).
- @details The uv `--from` reference appends `@<TAG>` with the raw SRS-451 release tag so the
install pins the latest tagged release regardless of the branch holding the tag (SRS-452)."""
- var `UNKNOWN_VERSION_LABEL = "unknown"` (L331)
- @brief Hardcoded PyPI JSON API endpoint for latest-version resolution (SRS-430).
- @details The startup release-check and `--ver`/`--version` read `info.version` from this
endpoint; PyPI is the sole source for version verification and default self-upgrade
(SRS-343, SRS-441, SRS-442)."""
- var `VERSION_REPORT_LABEL_WIDTH = 18` (L334)
- @brief Label printed by `--ver`/`--version` when a remote latest version cannot be fetched (SRS-442)."""
- var `FORCE_ONLINE_RELEASE_CHECK = False` (L337)
- @brief Left-justified label-field width aligning the `: <version>` column of every `--ver`/`--version` line (SRS-518)."""
### class `class ReqError(Exception)` : Exception (L341-358)
- @brief Startup-scoped override that bypasses release-check idle-state gating when enabled."""
- @brief Dedicated exception for expected CLI errors.
- @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
- fn `def __init__(self, message: str, code: int = 1) -> None` `priv` (L346-358)
  - @brief Dedicated exception for expected CLI errors.
  - @brief Initialize an expected CLI failure payload.
  - @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
  - @details Implements the __init__ function behavior with deterministic control flow.
  - @param message Human-readable error message.
  - @param code Process exit code bound to the failure category.
  - @return {None} Function return value.

### fn `def log(msg: str) -> None` (L359-368)
- @brief Prints an informational message.
- @details Implements the log function behavior with deterministic control flow.
- @param msg The message string to print.
- @return {None} Function return value.

### fn `def dlog(msg: str) -> None` (L369-379)
- @brief Prints a debug message if debugging is active.
- @details Implements the dlog function behavior with deterministic control flow.
- @param msg The debug message string to print.
- @return {None} Function return value.

### fn `def vlog(msg: str) -> None` (L380-390)
- @brief Prints a verbose message if verbose mode is active.
- @details Implements the vlog function behavior with deterministic control flow.
- @param msg The verbose message string to print.
- @return {None} Function return value.

### fn `def build_parser() -> argparse.ArgumentParser` (L391-590)
- @brief Builds the CLI argument parser.
- @details Defines all supported CLI arguments, flags, and help texts. Provider enablement is configured exclusively via the repeatable ``--enable PROVIDER`` argument, which accepts only the provider CLI name exactly like ``--disable PROVIDER`` (SRS-275, SRS-034); skills are the only supported artifact type. Every SRS-408 analysis subcommand accepts the global base arguments ``--prj-base`` and ``--git-base`` both before and after the subcommand token; ``--prj-base`` is mandatory only for the SRS-396 project-scan subcommands (enforced by ``_require_prj_base``) and ``--git-base`` is never mandatory for any SRS-408 subcommand (SRS-392, SRS-393, SRS-396, SRS-397, SRS-410). The ``--force`` auxiliary argument is accepted by ``--upgrade`` (with or without ``--develop``/``--dev``) and forces full package download and complete reinstallation (SRS-508, SRS-511).
- @return Configured ArgumentParser instance.

### fn `def parse_args(argv: Optional[list[str]] = None) -> Namespace` (L886-895)
- @brief Parses command-line arguments into a namespace.
- @details Implements the parse_args function behavior with deterministic control flow.
- @param argv List of arguments (defaults to sys.argv).
- @return Namespace containing parsed arguments.

### fn `def load_package_version() -> str` (L896-910)
- @brief Reads the package version from __init__.py.
- @details Implements the load_package_version function behavior with deterministic control flow.
- @return Version string extracted from the package.
- @throws ReqError If version cannot be determined.

### fn `def maybe_print_version(argv: list[str], pypi_latest: Optional[str] = None) -> bool` (L911-959)
- @brief Handles --ver/--version by printing installed, PyPI latest, and GitHub latest versions in aligned columns.
- @details When `--ver`/`--version` is present, prints exactly three stdout lines in order: installed version, PyPI latest version, GitHub latest version. Each line renders `<LABEL>` left-justified in :data:`VERSION_REPORT_LABEL_WIDTH` characters followed by `: <version>` so the version numbers align in one column (SRS-441, SRS-518); the labels are `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub`; fetch failures degrade to the `unknown` label without raising (SRS-442).
- @param argv Command line arguments to check.
- @param pypi_latest {Optional[str]} PyPI latest version already fetched by the startup release-check; when None, a direct PyPI JSON API fetch is attempted (SRS-441, SRS-442).
- @return {bool} True if version output was printed, False otherwise.
- @satisfies SRS-441, SRS-442, SRS-518

### fn `def _resolve_github_upgrade_tag() -> str` `priv` (L960-990)
- @brief Resolve the raw latest GitHub release tag for `--upgrade --develop` installations.
- @details Queries `GITHUB_RELEASES_LATEST_URL` through `fetch_github_latest_version(raw_tag=True)` and returns the raw `tag_name` value with the optional `v` prefix preserved so the uv `--from` reference targets an existing git tag regardless of the branch holding it (SRS-451). Maps fetch exceptions and empty payloads to one English `ReqError` so no uv process is spawned (SRS-453). Complexity: O(1). Side effects: one HTTP request.
- @return {str} Raw latest release tag, e.g. `v0.0.76`.
- @throws {ReqError} Raised with exit code 1 when the GitHub query fails or returns no tag (SRS-453).
- @satisfies SRS-451, SRS-453

### fn `def _installed_tool_uses_registry_source() -> bool` `priv` (L991-1044)
- @brief Detect whether the installed `cli-usereq` uv tool requirement resolves from the PyPI index.
- @details Resolves the effective uv tool root through `uv tool dir` and reads the canonical `TOOL_RECEIPT_FILENAME` requirement record of `TOOL_PROGRAM_NAME`. A record declaring any `NON_REGISTRY_REQUIREMENT_KEYS` entry (`git`, `url`, `path`, `editable`, `rev`, `tag`, `branch`) reports a non-registry source: `uv tool install <name> --upgrade` then re-resolves that non-registry source instead of the PyPI index, so a `--develop` installation would never return to the production channel (SRS-440). Missing `uv`, a failing `uv tool dir`, an absent receipt, an unparsable receipt, and non-mapping payloads all report the registry assumption so the documented SRS-343 command stays byte-identical when the source cannot be proven non-registry. Complexity: O(1) plus one `uv tool dir` subprocess. Side effects: one read-only subprocess and one read-only file read.
- @return {bool} True when the installed requirement is registry-sourced or undeterminable; False when the receipt records a non-PyPI source.
- @note Command construction only: this helper never mutates the tool environment.
- @see run_upgrade
- @satisfies SRS-343, SRS-440

### fn `def run_upgrade(use_github: bool = False, force: bool = False) -> None` (L1045-1115)
- @brief Executes the upgrade using uv from the PyPI index or the latest GitHub release tag.
- @details Builds the standard `uv tool install cli-usereq` command against the PyPI index by default (SRS-343); without `force` no forcing option is passed so the standard install/update process runs unchanged, and `--upgrade` is appended so uv resolves and installs the latest PyPI version instead of reusing the already-installed tool version. When the installed tool requirement does not resolve from the PyPI index (for example an installation produced by `--upgrade --develop`), `--upgrade` alone re-resolves that non-registry source and never installs the production release, so `_installed_tool_uses_registry_source()` decides whether the single uv option `--force` must be appended: forcing makes uv discard the recorded git/URL/path requirement and install the PyPI distribution, which restores the production channel and downgrades when the production version is older (SRS-440). On a registry-sourced installation the command stays byte-identical to the SRS-343 form. When `force` is True the command becomes the forced reinstallation form `uv tool install cli-usereq --force --reinstall --refresh` (SRS-509). When `use_github` is True, resolves the latest GitHub release tag through `_resolve_github_upgrade_tag()` (SRS-451) and appends `--from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` regardless of the branch holding that tag (SRS-440, SRS-452, SRS-510); the git source spec re-resolves the requested tag on every invocation, so no additional upgrade option is needed. Executes the command only on Linux; on non-Linux platforms prints the manual command and skips uv execution.
- @param use_github {bool} When True, install the latest tagged GitHub release instead of the PyPI index (`--upgrade --develop` or equivalent alias `--dev`, SRS-440, SRS-445).
- @param force {bool} When True, append `--force --reinstall --refresh` so uv re-downloads the package and fully reinstalls it (`--upgrade --force`, SRS-508, SRS-509, SRS-510).
- @return {None} Function return value.
- @throws {ReqError} When the SRS-451 GitHub tag resolution fails (exit code 1, SRS-453) or when the uv process fails.
- @note Tag resolution and the installed-source probe precede the platform gate so the non-Linux manual command embeds the resolved tag and the effective source switch (SRS-452).
- @note The `--develop`/`--dev` argv alias mapping to `use_github=True` and the `--force` argv token mapping to `force=True` are resolved by `main(...)` before calling this function.
- @satisfies SRS-343, SRS-440, SRS-445, SRS-451, SRS-452, SRS-453, SRS-508, SRS-509, SRS-510

### fn `def run_uninstall() -> None` (L1116-1148)
- @brief Executes the uninstallation using uv.
- @details Implements the run_uninstall function behavior with deterministic control flow.
- @return {None} Function return value.
- @throws ReqError If uninstall fails.
- @satisfies SRS-344, SRS-346

### fn `def normalize_release_tag(tag: str) -> str` (L1149-1161)
- @brief Normalizes the release tag by removing a 'v' prefix if present.
- @details Implements the normalize_release_tag function behavior with deterministic control flow.
- @param tag The raw tag string.
- @return The normalized version string.

### fn `def parse_version_tuple(version: str) -> tuple[int, ...] | None` (L1162-1186)
- @brief Converts a version into a numeric tuple for comparison.
- @details Accepts versions in 'X.Y.Z' format (ignoring any non-numeric suffixes).
- @param version The version string to parse.
- @return Tuple of integers or None if parsing fails.

### fn `def is_newer_version(current: str, latest: str) -> bool` (L1187-1205)
- @brief Returns True if latest is greater than current.
- @details Implements the is_newer_version function behavior with deterministic control flow.
- @param current The current installed version string.
- @param latest The latest available version string.
- @return True if update is available, False otherwise.

### fn `def parse_github_owner_repository(remote_url: str) -> tuple[str, str] | None` (L1206-1232)
- @brief Extract GitHub owner/repository from a git remote URL.
- @details Supports SSH (`git@github.com:owner/repo.git`), HTTPS (`https://github.com/owner/repo.git`), and SSH-scheme (`ssh://git@github.com/owner/repo.git`) forms. Removes optional `.git` suffix.
- @param remote_url Remote URL string from `git remote -v`.
- @return Tuple `(owner, repository)` when URL targets github.com; otherwise None.

### fn `def read_git_remote_verbose(cwd: str | None = None) -> str` (L1233-1252)
- @brief Read git remote definitions using `git remote -v`.
- @details Executes `git remote -v` with deterministic stderr capture and text decoding. When `cwd` is omitted, the current process working directory is used.
- @param cwd Optional working directory override for git execution context.
- @return Raw stdout output generated by `git remote -v`.
- @throws subprocess.CalledProcessError If git returns a non-zero status.

### fn `def resolve_github_owner_repository_from_active_remotes() -> tuple[str, str]` (L1253-1313)
- @brief Resolve GitHub owner/repository from active repository remotes.
- @details Reads `git remote -v`, prioritizes `origin` fetch URL, then other fetch remotes, then non-fetch entries, and returns the first parseable github.com owner/repository pair. If the first inspection fails outside the repository root context, retries once from `REPO_ROOT`.
- @return Tuple `(owner, repository)` resolved from active remotes.
- @throws ValueError If no github.com remote URL can be parsed from `git remote -v`.
- @throws ReqError If git remote inspection cannot execute successfully.

### fn `def resolve_pypi_latest_version_url() -> str` (L1314-1323)
- @brief Resolve the PyPI JSON API URL for latest-version resolution.
- @details Returns the static endpoint derived from the PyPI project `cli-usereq`.
- @return {str} Fully-qualified URL `https://pypi.org/pypi/cli-usereq/json`.
- @satisfies SRS-430

### fn `def fetch_pypi_latest_version(` (L1324-1325)

### fn `def fetch_github_latest_version(` (L1361-1364)
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

### fn `def format_unix_timestamp_utc(timestamp_seconds: int) -> str` (L1403-1415)
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

### fn `def get_release_check_idle_file_path(` (L1416-1417)

### fn `def cleanup_release_check_idle_state_cache(` (L1434-1435)
- @brief Resolve idle-state file path for startup release-check throttling.
- @details Builds the path using the effective home directory returned by `Path.home()`.
- @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
- @return Absolute path `$HOME/.cache/<program_name>/check_version_idle-time.json`.
- @satisfies SRS-345

### fn `def read_release_check_idle_state(file_path: Path) -> dict[str, int | str] | None` (L1458-1522)
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

### fn `def should_execute_release_check(` (L1523-1525)

### fn `def parse_retry_after_seconds(` (L1544-1546)
- @brief Decide whether startup release-check should execute in current invocation.
- @details Executes release-check when state is missing and skips only while the persisted `idle_until_timestamp` is greater than the current timestamp.
- @param idle_state Parsed idle-state payload or None when unavailable.
- @param now_timestamp Current Unix timestamp in seconds.
- @return True when release-check must execute; False when still in idle window.
- @satisfies SRS-348

### fn `def write_release_check_idle_state_payload(` (L1576-1579)
- @brief Parse an HTTP `Retry-After` header value into non-negative seconds.
- @details Supports integer-second values and HTTP-date values; HTTP-date values are converted to a delta from `now_timestamp`.
- @param retry_after_header Raw `Retry-After` header value.
- @param now_timestamp Current Unix timestamp in seconds.
- @return Retry delay in seconds when parsing succeeds; otherwise None.

### fn `def write_release_check_idle_state(` (L1606-1609)
- @brief Persist canonical release-check idle-state payload to disk.
- @details Serializes both numeric and UTC human-readable timestamps for the success instant and the idle-until instant.
- @param file_path Absolute idle-state JSON path.
- @param last_success_timestamp Unix timestamp of the last successful release-check.
- @param idle_until_timestamp Unix timestamp until startup release-check remains disabled.
- @throws OSError If file write fails.

### fn `def write_failed_release_check_idle_state(` (L1628-1632)
- @brief Persist release-check idle-state after a successful remote check.
- @details Computes `idle_until_timestamp = now_timestamp + idle_delay_seconds` and persists canonical idle-state keys.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Successful check timestamp in seconds.
- @param idle_delay_seconds Fixed idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-349

### fn `def persist_failed_release_check_idle_state(` (L1660-1664)
- @brief Persist idle-state after a startup release-check failure.
- @details Computes `idle_until_timestamp = now + idle_delay_seconds`, rewrites the canonical idle-state payload on every failure, and preserves the previous successful timestamp when available.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @throws OSError If file write fails.
- @satisfies SRS-350, SRS-351

### fn `def maybe_notify_newer_version(` (L1690-1691)
- @brief Persist failure idle-state and report write failures.
- @details Delegates failure idle-state persistence to `write_failed_release_check_idle_state(...)`; converts `OSError` into the standard bright-red stderr diagnostic without swallowing the original release-check failure.
- @param file_path Absolute idle-state JSON path.
- @param now_timestamp Current Unix timestamp in seconds.
- @param idle_state Existing parsed idle-state payload or None.
- @param idle_delay_seconds Fixed failure idle-delay length in seconds.
- @return {None} Function return value.
- @satisfies SRS-350, SRS-351

### fn `def ensure_doc_directory(` (L1820-1821)
- @brief Executes idle-gated online PyPI version check and prints bright colored status messages.
- @details Reads idle-state from `$HOME/.cache/usereq/check_version_idle-time.json`, skips remote requests when idle window is active unless startup context enables `FORCE_ONLINE_RELEASE_CHECK`, fetches the latest version from the PyPI JSON API (SRS-430) when due, compares versions, prints a bright-green update message only for newer versions, persists a 3600-second idle-delay after successful HTTP/JSON validation, prints bright-red diagnostics on every failure, rewrites idle-state JSON on every failure, uses an 86400-second idle-delay for `HTTPError`, `URLError`, and `TimeoutError`, and uses the default 3600-second idle-delay for other release-check failures.
- @param timeout_seconds Time to wait for the version check response.
- @return {Optional[str]} The fetched PyPI latest version on successful validation; None when the check is idle-gated or fails.
- @satisfies SRS-345, SRS-348, SRS-349, SRS-350, SRS-351, SRS-430

### fn `def ensure_test_directory(` (L1850-1851)
- @brief Resolve and validate docs directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate docs directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-359, SRS-363

### fn `def ensure_src_directory(` (L1880-1881)
- @brief Resolve and validate tests directory path under project base.
- @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
- @param path {str} Candidate tests directory path.
- @param project_base {Path} Absolute project base path.
- @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
- @return {None} Function return value.
- @throws {ReqError} Raised when path escapes project base or resolves to a file.
- @satisfies SRS-361, SRS-363

### fn `def make_relative_if_contains_project(path_value: str, project_base: Path) -> str` (L1910-1951)
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

### fn `def resolve_absolute(normalized: str, project_base: Path) -> Optional[Path]` (L1952-1967)
- @brief Resolves the absolute path starting from a normalized value.
- @details Implements the resolve_absolute function behavior with deterministic control flow.
- @param normalized The normalized relative path string.
- @param project_base The project root path.
- @return Absolute Path object or None if normalized is empty.

### fn `def resolve_git_root(target_path: Path) -> Path` (L1968-1995)
- @brief Resolve the git repository root for a given path.
- @param target_path Absolute path that must be inside a git repository.
- @return Absolute path to the git repository root.
- @throws ReqError If the path is not inside a git repository.
- @satisfies SRS-305, SRS-306

### fn `def sanitize_branch_name(branch: str) -> str` (L1996-2005)
- @brief Replace characters incompatible with Linux or Windows paths in a branch name.
- @param branch Raw git branch name.
- @return Sanitized string with incompatible characters replaced by `-`.
- @satisfies SRS-319

### fn `def validate_wt_name(wt_name: str) -> bool` (L2006-2017)
- @brief Validate that a worktree/branch name contains only valid directory characters.
- @param wt_name Candidate worktree name.
- @return True if valid, False if invalid characters are present.
- @satisfies SRS-321

### fn `def load_full_config() -> dict` (L2018-2038)
- @brief Load ALL parameters from the user-global configuration file as a raw dictionary.
- @return Full dictionary of all config key-value pairs.
- @throws ReqError If the global config file is missing or invalid JSON.
- @satisfies SRS-310, SRS-387

### fn `def save_config(` (L2039-2044)

### fn `def update_directory_config(` (L2074-2077)
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

### fn `def load_config() -> dict[str, str | list[str]]` (L2115-2165)
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

### fn `def load_static_check_from_config() -> dict` (L2166-2204)
- @brief Load the `"static-check"` section from the user-global configuration file without validation errors.
- @details Reads `~/.config/usereq/config.json` silently. When the payload stores no `"static-check"` entry (including a missing or unreadable file), returns a deep copy of `DEFAULT_STATIC_CHECK` (SRS-424); a present entry, including an empty or invalid object, suppresses the defaults and is normalized like before: per-language entries that are not non-empty arrays of objects are dropped. Does NOT raise `ReqError`; caller decides whether absence is an error.
- @return Dict of static-check config (canonical-lang -> list[config-dict]).
- @see SRS-252, SRS-253, SRS-256, SRS-424, SRS-425, SRS-426
- @satisfies SRS-424, SRS-425, SRS-426

### fn `def _static_check_entry_identity(` `priv` (L2205-2206)

### fn `def load_persisted_providers() -> list[str]` (L2229-2270)
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

### fn `def _read_config_payload() -> dict` `priv` (L2271-2291)
- @brief Read the raw user-global configuration payload without key filtering.
- @details Single read path for configuration commands performing read-modify-write updates (SRS-279, SRS-288, SRS-387, SRS-413, SRS-414, SRS-420).
- @return {dict} Raw JSON dictionary; empty dict when the file is absent.
- @throws {ReqError} Raised when the file exists but holds invalid JSON (exit code 11).
- @satisfies SRS-288, SRS-387

### fn `def _write_config_payload(payload: dict) -> None` `priv` (L2292-2310)
- @brief Write the user-global configuration payload filtered to canonical keys.
- @details Creates missing parent directories on first write (SRS-387) and never writes `--prj-base`/`--git-base` (SRS-394).
- @param payload {dict} Full payload; only `PERSISTED_CONFIG_KEYS` entries are written.
- @return {None} Function return value.
- @satisfies SRS-288, SRS-387, SRS-394

### fn `def load_auto_install_enabled() -> bool` (L2311-2325)
- @brief Resolve the persisted auto-install flag with enabled default.
- @details `auto-install` defaults to enabled; unreadable configuration falls back to the default (SRS-420, SRS-421).
- @return {bool} True unless the configuration stores exactly `false`.
- @satisfies SRS-420, SRS-421

### fn `def apply_enabled_providers(names: list[str]) -> None` (L2326-2355)
- @brief Persist ``--enable PROVIDER`` names replacing the named providers' entries.
- @details Validates every token through `validate_provider_name` (SRS-275, SRS-278), removes all previously persisted entries of the named providers, appends the new names deduplicated in CLI order, and preserves every other provider (SRS-279). No artifact is installed (SRS-276).
- @param names {list[str]} Raw provider name tokens in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid provider tokens with exit code 1 (SRS-278).
- @satisfies SRS-275, SRS-276, SRS-278, SRS-279

### fn `def apply_disabled_providers(names: list[str]) -> None` (L2356-2384)
- @brief Remove the named providers from the persisted `"providers"` array.
- @details Removes every persisted entry of each named provider; absent entries leave the configuration unchanged; the `"providers"` key is removed when no entries remain (SRS-413).
- @param names {list[str]} Provider names supplied via `--disable`.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown provider tokens with exit code 1 (SRS-422).
- @satisfies SRS-413, SRS-422

### fn `def apply_enable_static_check_specs(specs: list[str]) -> None` (L2385-2432)
- @brief Persist `--enable-static-check` entries merged into the existing configuration.
- @details Parses each SPEC (SRS-260), deduplicates within the invocation (SRS-251), validates Command executables (SRS-250), merges into the persisted `"static-check"` object by exact `(language, module, cmd, params)` identity (SRS-301), and requires no `--prj-base` (SRS-415).
- @param specs {list[str]} Raw SPEC strings in CLI order.
- @return {None} Function return value.
- @throws {ReqError} Raised on invalid language/module tokens or non-executable Command `cmd` values with exit code 1.
- @satisfies SRS-248, SRS-250, SRS-251, SRS-301, SRS-415

### fn `def apply_disable_static_check_specs(specs: list[str]) -> None` (L2433-2481)
- @brief Remove static-check entries selected by `--disable-static-check` SPECs.
- @details Empty language arrays are removed from the `"static-check"` object and the `"static-check"` key is persisted even when empty so explicit configuration suppresses the SRS-424 defaults; requires no `--prj-base` (SRS-414, SRS-415).
- @param specs {list[str]} SPEC strings; `LANG=MODULE[,CMD[,PARAM...]]` removes exact identity matches, bare `LANG` removes the whole canonical language key.
- @return {None} Function return value.
- @throws {ReqError} Raised on unknown language or module tokens with exit code 1 (SRS-422).
- @satisfies SRS-414, SRS-415, SRS-422, SRS-424

### fn `def apply_auto_install_config(enabled: bool) -> None` (L2482-2494)
- @brief Persist the auto-install enabled flag.
- @details Read-modify-write preserving all unrelated canonical keys (SRS-420).
- @param enabled {bool} Value persisted under `"auto-install"`.
- @return {None} Function return value.
- @satisfies SRS-420

### fn `def _is_provider_config_command(args: Namespace) -> bool` `priv` (L2495-2512)
- @brief Check if args request a provider/static-check/auto-install configuration command.
- @details Configuration commands only update `~/.config/usereq/config.json` and never install artifacts (SRS-276, SRS-413, SRS-414, SRS-415, SRS-420).
- @param args Parsed CLI namespace.
- @return True when any configuration flag is present.

### fn `def run_config_commands(args: Namespace) -> None` (L2513-2541)
- @brief Apply every provider/static-check/auto-install configuration command.
- @details Application order: `--enable`, `--disable`, `--enable-static-check`, `--disable-static-check`, `--enable-auto-install`, `--disable-auto-install`; each step persists immediately (SRS-275, SRS-413, SRS-414, SRS-420).
- @param args Parsed CLI namespace carrying the configuration flag values.
- @return {None} Function return value.
- @satisfies SRS-275, SRS-276, SRS-413, SRS-414, SRS-415, SRS-420

### fn `def _non_symlink_regular_files(directory: Path) -> list[Path]` `priv` (L2542-2565)
- @brief List non-hidden regular files in one directory without following symbolic links.
- @details Scans ``directory`` with ``os.scandir`` and ``follow_symlinks=False`` so symbolic-link entries are never followed or resolved: symlinked files, symlinked subdirectories, and broken links are excluded, and only entries whose own inode is a regular file are kept (SRS-504). Hidden names starting with ``.`` are excluded. When ``directory`` is itself a symbolic link or is absent, returns an empty list so callers apply their absent-directory fallback instead of reading through the link.
- @param directory {Path} Absolute directory to enumerate.
- @return {list[Path]} Sorted paths of non-symlink regular files.
- @satisfies SRS-504

### fn `def generate_guidelines_file_list() -> str` (L2566-2586)
- @brief Build the `%%GUIDELINES_FILES%%` substitution payload from GUIDELINES_DIR.
- @details Enumerates non-hidden non-symlink regular files in :func:`guidelines_dir` (packaged `resources/guidelines` of the running installation, SRS-360) in deterministic sorted order without following symbolic links (SRS-504) and renders each as a backticked home-relative path (SRS-402). When the directory is absent, symlinked, or empty, renders the home-relative directory itself with a trailing slash.
- @return {str} Comma-separated backticked home-relative paths, or the directory fallback.
- @satisfies SRS-403, SRS-504

### fn `def generate_guidelines_file_names() -> list[str]` (L2587-2601)
- @brief List the bare guideline file names reported after installation.
- @details Returns one bare file name per non-hidden non-symlink regular file in :func:`guidelines_dir` (packaged `resources/guidelines` of the running installation) without following symbolic links (SRS-504, SRS-516); names carry no directory components, and an absent, symlinked, or empty directory yields an empty list.
- @return {list[str]} Bare guideline file names in deterministic sorted order.
- @satisfies SRS-360, SRS-513, SRS-516

### fn `def generate_templates_file_names() -> list[str]` (L2602-2616)
- @brief List the bare template file names reported after installation.
- @details Returns one bare file name per non-hidden non-symlink regular file in :func:`templates_dir` (packaged `resources/templates` of the running installation) without following symbolic links (SRS-516); names carry no directory components, and an absent, symlinked, or empty directory yields an empty list.
- @return {list[str]} Bare template file names in deterministic sorted order.
- @satisfies SRS-498, SRS-514, SRS-516

### fn `def _print_resource_report() -> None` `priv` (L2617-2638)
- @brief Print the compact post-installation packaged-resource report.
- @details Prints the home-relative lexical guidelines directory path ending with `/`, then one comma-separated line of bare guideline file names (SRS-513), then the home-relative lexical templates directory path ending with `/`, then one comma-separated line of bare template file names (SRS-514). Every printed path is composed lexically without resolving symbolic links (SRS-515); an empty enumeration emits no file-name line (SRS-516).
- @return {None} Function return value.
- @satisfies SRS-513, SRS-514, SRS-515, SRS-516

### fn `def ensure_relative(value: str, name: str, code: int) -> None` (L2639-2654)
- @brief Validates that the path is not absolute and raises an error otherwise.
- @details Implements the ensure_relative function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @param name Input parameter `name`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def apply_replacements(text: str, replacements: Mapping[str, str]) -> str` (L2655-2667)
- @brief Returns text with token replacements applied.
- @details Implements the apply_replacements function behavior with deterministic control flow.
- @param text Input parameter `text`.
- @param replacements Input parameter `replacements`.
- @return {str} Function return value.

### fn `def write_text_file(dst: Path, text: str) -> None` (L2668-2679)
- @brief Writes text to disk, ensuring the destination folder exists.
- @details Implements the write_text_file function behavior with deterministic control flow.
- @param dst Input parameter `dst`.
- @param text Input parameter `text`.
- @return {None} Function return value.

### fn `def copy_with_replacements(` (L2680-2681)

### fn `def extract_frontmatter(content: str) -> tuple[str, str]` (L2696-2709)
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

### fn `def extract_purpose_first_bullet(body: str) -> str` (L2710-2734)
- @brief Returns the first bullet of the Purpose section.
- @details Implements the extract_purpose_first_bullet function behavior with deterministic control flow.
- @param body Input parameter `body`.
- @return {str} Function return value.

### fn `def _extract_section_text(body: str, section_name: str) -> str` `priv` (L2735-2762)
- @brief Extracts and collapses the text content of a named ## section.
- @details Scans `body` line by line for a heading matching `## <section_name>` (case-insensitive). Collects all subsequent non-empty lines until the next `##`-level heading (or end of string). Strips each line, joins with a single space, and returns the collapsed single-line result.
- @param[in] body str -- Full prompt body text (after front matter removal).
- @param[in] section_name str -- Target section name without `##` prefix (case-insensitive match).
- @return str -- Single-line collapsed text of the section; empty string if section absent or empty.

### fn `def extract_skill_description(frontmatter: str) -> str` (L2763-2781)
- @brief Extracts the usage field from YAML front matter as a single YAML-safe line.
- @details Parses the YAML front matter and returns the `usage` field value with all whitespace normalized to a single line. Returns an empty string if the field is absent.
- @param[in] frontmatter str -- YAML front matter text (without the leading/trailing `---` delimiters).
- @return str -- Single-line text of the usage field; empty string if absent.

### fn `def yaml_double_quote_escape(value: str) -> str` (L2782-2791)
- @brief Minimal escape for a double-quoted string in YAML.
- @details Implements the yaml_double_quote_escape function behavior with deterministic control flow.
- @param value Input parameter `value`.
- @return {str} Function return value.

### fn `def list_docs_templates() -> list[Path]` (L2792-2812)
- @brief Returns non-hidden files available in resources/templates.
- @details Implements the list_docs_templates function behavior with deterministic control flow.
- @return Sorted list of file paths under resources/templates.
- @throws ReqError If resources/templates does not exist or has no non-hidden files.
- @satisfies SRS-495

### fn `def find_requirements_template(docs_templates: list[Path]) -> Path` (L2813-2830)
- @brief Returns the packaged Requirements template file.
- @details Implements the find_requirements_template function behavior with deterministic control flow.
- @param docs_templates Runtime template file list from resources/templates.
- @return Path to `Requirements_Template.md`.
- @throws ReqError If `Requirements_Template.md` is not present.
- @satisfies SRS-495

### fn `def ensure_wrapped(target: Path, project_base: Path, code: int) -> None` (L2831-2846)
- @brief Verifies that the path is under the project root.
- @details Implements the ensure_wrapped function behavior with deterministic control flow.
- @param target Input parameter `target`.
- @param project_base Input parameter `project_base`.
- @param code Input parameter `code`.
- @return {None} Function return value.

### fn `def prune_empty_dirs(root: Path) -> None` (L2847-2863)
- @brief Removes empty directories under the specified root.
- @details Implements the prune_empty_dirs function behavior with deterministic control flow.
- @param root Input parameter `root`.
- @return {None} Function return value.

### fn `def remove_generated_resources() -> None` (L2864-2895)
- @brief Removes `req-*` skill artifacts generated by the tool from user-level provider directories.
- @details Loads the persisted `providers` array from the user-global configuration file, resolves each enabled provider skills root via :func:`provider_skills_root`, and deletes only `req-*` skill directories and files. Empty user-level skills roots are pruned afterwards; unrelated user content is never touched.
- @return {None} Function return value.
- @satisfies SRS-419

### fn `def _render_simple_table(headers: list[str], rows: list[list[str]]) -> str` `priv` (L2896-2926)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _line(cells: list[str]) -> str` `priv` (L2909-2917)
- @brief Render one Unicode box-drawing table from headers and rows.
- @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
- @param headers {list[str]} Column header labels.
- @param rows {list[list[str]]} Cell values per row; every row matches the header count.
- @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.

### fn `def _border(left: str, middle: str, right: str) -> str` `priv` (L2918-2920)

### fn `def _provider_skill_installed(provider: str, skill_name: str) -> bool` `priv` (L2927-2944)
- @brief Detect whether one named skill artifact exists for a provider.
- @details Per-skill installation-status detection for the `show` `Installation Status` table (SRS-417, SRS-490); unknown providers and absent roots report `False`. Complexity: O(1). Side effects: none (read-only filesystem probe).
- @param provider {str} Provider selector from `{antigravity, claude, codex, copilot, openclaw, opencode, pi}`.
- @param skill_name {str} Skill directory name such as `req-<prompt_name>`.
- @return {bool} True when the skill path exists under the provider skills root.
- @satisfies SRS-417, SRS-490

### fn `def _packaged_prompt_names() -> list[str]` `priv` (L2945-2959)
- @brief List the packaged prompt stem names defining installable skills.
- @details Enumeration source for the `show` `Installation Status` rows (SRS-489); returns an empty list when the packaged prompts directory is absent. Complexity: O(P log P) over P packaged prompts. Side effects: none (read-only).
- @return {list[str]} Sorted prompt file stems under the packaged `resources/prompts` directory.
- @satisfies SRS-489

### fn `def run_install(args: Namespace) -> None` (L2960-2975)
- @brief Execute install: install or update the persisted providers globally.
- @details Delegates to the config-driven installation flow (SRS-035, SRS-064, SRS-418) which requires at least one enabled provider and prints the installation summary report (SRS-049). Install performs no project-side operations and does not consume `--prj-base` (SRS-447, SRS-448); scaffolding and directory persistence are removed legacy behaviors (SRS-363, SRS-407, SRS-449).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If no provider is enabled.
- @satisfies SRS-035, SRS-064, SRS-418, SRS-447, SRS-448

### fn `def run_uninstall_providers(args: Namespace) -> None` (L2976-2993)
- @brief Execute uninstall: remove skill artifacts of the configured providers.
- @details Requires the user-global configuration file and removes `req-*` skill artifacts of the providers persisted under `"providers"` (SRS-419).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If the global configuration file is missing.
- @satisfies SRS-419

### fn `def run_show(args: Namespace) -> None` (L2994-3101)
- @brief Execute show: print the active configuration as tables.
- @details Prints the effective configuration table (`docs-dir`, `tests-dir`, `src-dir`, `auto-install`), the Providers table listing every configurable provider with the `CLI`, `Enabled`, and `Skills Path` columns in alphabetical order (SRS-462, SRS-463, SRS-485, SRS-488), exactly one `Installation Status` table with `Type`, `Name`, `CLI`, `Enabled`, and `Installed` columns reporting one row per packaged prompt and enabled provider pair ordered by prompt name then provider name (SRS-417, SRS-489, SRS-490, SRS-491), and the enabled static-check entries (SRS-416).
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If persisted provider names are invalid.
- @satisfies SRS-416, SRS-417, SRS-462, SRS-463, SRS-485, SRS-488, SRS-489, SRS-490, SRS-491

### fn `def _maybe_auto_install_after_upgrade(argv_list: list[str]) -> None` `priv` (L3102-3126)
- @brief Run the provider installation flow after a successful `--upgrade`.
- @details Executes the `install` flow with persisted providers when `auto-install` is enabled (SRS-420, SRS-421) regardless of `--prj-base` presence; prints an English stderr warning and skips when no provider is enabled (SRS-450).
- @param argv_list {list[str]} Raw CLI argument vector of the `--upgrade` invocation.
- @return {None} Function return value.
- @satisfies SRS-420, SRS-421, SRS-450

### fn `def run_set_directories(args: Namespace) -> None` (L3127-3190)
- @brief Persist `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` values.
- @details Requires `--prj-base` (SRS-396), normalizes each supplied path against the project base, rejects absolute or escaping paths, and writes only the supplied keys to `~/.config/usereq/config.json` while preserving unrelated keys (SRS-398, SRS-399, SRS-400, SRS-401). No project directory is created and no provider artifact is generated.
- @param args Parsed CLI namespace carrying the `set_docs_dir`, `set_src_dir`, and `set_tests_dir` values.
- @return {None} Function return value.
- @throws ReqError If `--prj-base` is absent or a supplied path escapes the project base.
- @satisfies SRS-396, SRS-398, SRS-399, SRS-400, SRS-401

### fn `def _validate_enable_static_check_command_executables(` `priv` (L3191-3194)

### fn `def run(args: Namespace) -> None` (L3223-3422)
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

- var `VERBOSE = getattr(args, "verbose", False)` (L3243)
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
- var `DEBUG = getattr(args, "debug", False)` (L3244)
### fn `def _format_install_table(` `priv` (L3363-3364)

### fn `def _wrap_cell(value: str, width: int, allow_wrap: bool) -> list[str]` `priv` (L3396-3418)
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

### fn `def _render_row(provider: str, skills: str) -> list[str]` `priv` (L3419-3440)
- @brief Render one logical table row into one or more physical lines.
- @details Applies per-cell wrapping and left alignment, then expands the row height to the maximum wrapped cell line count.
- @param provider {str} Provider cell text.
- @param skills {str} Skills Installed cell text.
- @return {list[str]} Physical row lines encoded with box-drawing separators.

### fn `def _colorize_table_border(line: str) -> str` `priv` (L3457-3469)
- @brief Colorize box-drawing border glyphs with bright-red ANSI style.
- @details Applies color to border characters while preserving cell payload text color.
- @param line {str} One already-rendered table line.
- @return {str} Line with border glyphs wrapped in ANSI bright-red and reset sequences.

- var `SUPPORTED_EXTENSIONS = frozenset(` (L3482)
### fn `def _collect_source_files(src_dirs: list[str], project_base: Path) -> list[str]` `priv` (L3524-3581)
- @brief Collect source files from git-indexed project paths.
- @details Uses `git ls-files --cached --others --exclude-standard` in project root, filters by src-dir prefixes, applies EXCLUDED_DIRS filtering, and keeps only SUPPORTED_EXTENSIONS files.
- @param src_dirs Input parameter `src_dirs`.
- @param project_base Input parameter `project_base`.
- @return {list[str]} Function return value.

### fn `def _build_ascii_tree(paths: list[str]) -> str` `priv` (L3582-3627)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _emit(` `priv` (L3606-3608)
- @brief Build a deterministic tree string from project-relative paths.
- @details Implements the _build_ascii_tree function behavior with deterministic control flow.
- @param paths Project-relative file paths.
- @return Rendered tree rooted at '.'.

### fn `def _format_files_structure_markdown(files: list[str], project_base: Path) -> str` `priv` (L3628-3642)
- @brief Format markdown section containing the scanned files tree.
- @details Implements the _format_files_structure_markdown function behavior with deterministic control flow.
- @param files Absolute file paths selected for references processing.
- @param project_base Project root used to normalize relative paths.
- @return Markdown section with heading and fenced tree.

### fn `def _is_standalone_command(args: Namespace) -> bool` `priv` (L3643-3654)
- @brief Check if the parsed args contain a standalone file command.
- @details The standalone group now contains only `--test-static-check` (SRS-240); the former `--files-*` and project-scan analysis flags were converted to bare subcommands (SRS-408) whose base requirements follow SRS-396 and SRS-410.
- @param args Parsed CLI namespace.
- @return True when the standalone `--test-static-check` flag is present.

### fn `def _is_project_scan_command(args: Namespace) -> bool` `priv` (L3655-3672)
- @brief Check if the parsed args contain a project-scan command.
- @details Project-scan commands: `--git-check`, `--docs-check`, `--git-wt-name`, `--git-wt-create`, and `--git-wt-delete`. The analysis commands were converted to bare subcommands (SRS-408) and `--git-path` was removed (SRS-333, SRS-334).
- @param args Parsed CLI namespace.
- @return True when any project-scan flag is present.

### fn `def _is_directory_config_command(args: Namespace) -> bool` `priv` (L3673-3688)
- @brief Check if args request a directory configuration command.
- @details Configuration commands persist project-relative directories and therefore require `--prj-base` without activating the installation flow (SRS-396, SRS-398, SRS-399, SRS-400).
- @param args Parsed CLI namespace.
- @return True when any `--set-*-dir` flag is present.

### fn `def _require_prj_base(args: Namespace) -> Path` `priv` (L3689-3707)
- @brief Return the mandatory absolute project base for the current command.
- @details `--prj-base` is command-line only and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI namespace.
- @return {Path} Absolute project base path.
- @throws ReqError If `--prj-base` is absent or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _require_git_base_value(args: Namespace) -> Path` `priv` (L3708-3727)
- @brief Validate and return the `--git-base` argument value without repository resolution.
- @details Performs presence and existence validation only (SRS-395); git-integration commands reach this level through `_require_git_base` because they are the only commands that execute git operations through `--git-base` (SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute `--git-base` path.
- @throws ReqError If `--git-base` is absent or does not exist.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def _require_git_base(args: Namespace) -> Path` `priv` (L3728-3740)
- @brief Return the mandatory absolute git repository base for the current command.
- @details `--git-base` is command-line only and is never loaded from configuration; the returned path is the repository root reported by `git rev-parse --show-toplevel` executed in `--git-base` (SRS-393, SRS-394, SRS-395, SRS-397).
- @param args Parsed CLI namespace.
- @return {Path} Absolute git repository root resolved from `--git-base`.
- @throws ReqError If `--git-base` is absent, does not exist, or is not inside a git work tree.
- @satisfies SRS-393, SRS-394, SRS-395, SRS-397

### fn `def run_git_check(args: Namespace) -> None` (L3741-3768)
- @brief Execute --git-check: verify clean git status and valid HEAD.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On git status unclear or when `--git-base` is outside a git repository.
- @satisfies SRS-311, SRS-312, SRS-391, SRS-397

### fn `def run_docs_check(args: Namespace) -> None` (L3769-3798)
- @brief Execute --docs-check: verify existence of REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError If any required doc file is missing.
- @satisfies SRS-313, SRS-314, SRS-315, SRS-316, SRS-317, SRS-396

### fn `def run_git_wt_name(args: Namespace) -> None` (L3799-3823)
- @brief Execute --git-wt-name: print standardized worktree name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @satisfies SRS-318, SRS-319, SRS-391, SRS-397

### fn `def _worktree_path_exists_exact(git_path: Path, target_path: Path) -> bool` `priv` (L3824-3853)
- @brief Check whether a git worktree exists at the exact target path.
- @details Parses `git worktree list --porcelain` output by `worktree <path>` records and performs exact path comparison to prevent partial-name or substring matches.
- @param git_path Absolute git root path used as command cwd.
- @param target_path Absolute worktree path expected for WT_NAME.
- @return {bool} True only when target_path is listed as an exact worktree path.
- @throws ReqError On git command execution errors.

### fn `def _rollback_worktree_create(git_path: Path, wt_path: Path, wt_name: str) -> None` `priv` (L3854-3890)
- @brief Roll back worktree and branch created by --git-wt-create on post-create failure.
- @details Uses `git worktree remove <path> --force` and `git branch -D <name>` to restore a clean git state when post-create copy/chdir operations fail.
- @param git_path Absolute git root path used as command cwd.
- @param wt_path Absolute worktree path to remove.
- @param wt_name Exact branch name to delete.
- @return {None} Function return value.
- @throws ReqError If rollback cannot remove the exact target worktree and branch.

### fn `def run_git_wt_create(args: Namespace) -> None` (L3891-3946)
- @brief Execute --git-wt-create: create a git worktree, branch, and .venv seeding from --prj-base.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name, missing or invalid `--prj-base` (SRS-395), git command failure, or when CWD is outside a git repository.
- @satisfies SRS-320, SRS-321, SRS-322, SRS-331, SRS-335, SRS-391, SRS-395, SRS-397, SRS-460

### fn `def run_git_wt_delete(args: Namespace) -> None` (L3947-4015)
- @brief Execute --git-wt-delete: remove a git worktree and branch by name.
- @param args Parsed CLI namespace.
- @return {None} Function return value.
- @throws ReqError On invalid name or git removal failure.
- @satisfies SRS-326, SRS-327, SRS-328, SRS-332, SRS-391, SRS-397

### fn `def run_files_tokens(files: list[str]) -> None` (L4016-4039)
- @brief Execute files-tokens: count tokens for arbitrary files.
- @details Implements the run_files_tokens function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_references(files: list[str]) -> None` (L4040-4057)
- @brief Execute files-references: generate markdown for arbitrary files.
- @details Implements the run_files_references function behavior with deterministic control flow.
- @param files Input parameter `files`.
- @return {None} Function return value.
- @satisfies SRS-234, SRS-408

### fn `def run_files_compress(files: list[str], enable_line_numbers: bool = False) -> None` (L4058-4077)
- @brief Execute files-compress: compress arbitrary files.
- @details Renders output header paths relative to current working directory.
- @param files List of source file paths to compress.
- @param enable_line_numbers If True, emits <n>: prefixes in compressed entries.
- @return {None} Function return value.
- @satisfies SRS-408

### fn `def run_files_find(args_list: list[str], enable_line_numbers: bool = False) -> None` (L4078-4107)
- @brief Execute files-find: find constructs in arbitrary files.
- @details Implements the run_files_find function behavior with deterministic control flow.
- @param args_list Combined list: [TAG, PATTERN, FILE1, FILE2, ...].
- @param enable_line_numbers If True, emits <n>: prefixes in output.
- @return {None} Function return value.
- @satisfies SRS-236, SRS-408

### fn `def run_references(args: Namespace) -> None` (L4108-4133)
- @brief Execute references: generate markdown for project source files.
- @details Resolves the mandatory ``--prj-base`` project base and the configured ``src-dir`` entries, selects supported source files from the git index, and prints the files-structure section followed by generated references markdown. When the selection is empty, prints the canonical :data:`EMPTY_REFERENCES_DIRECTIVE` payload instead and returns successfully so documentation-only repositories produce a deterministic empty-references marker (SRS-581, SRS-582). Complexity: O(F) file analysis over F selected files. Side effects: stdout writes.
- @param args {Namespace} Parsed CLI namespace carrying the mandatory ``--prj-base`` value.
- @return {None} Function return value.
- @throws {ReqError} Raised when ``--prj-base`` is absent or a configured directory value is invalid.
- @satisfies SRS-177, SRS-180, SRS-181, SRS-235, SRS-396, SRS-408, SRS-581, SRS-582

### fn `def run_compress_cmd(args: Namespace) -> None` (L4134-4156)
- @brief Execute compress: compress project source files.
- @details Implements the run_compress_cmd function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @satisfies SRS-179, SRS-180, SRS-181, SRS-396, SRS-408

### fn `def run_find(args: Namespace) -> None` (L4157-4187)
- @brief Execute find: find constructs in project source files.
- @details Implements the run_find function behavior with deterministic control flow.
- @param args Parsed CLI arguments namespace.
- @return {None} Function return value.
- @throws ReqError If no source files found or no constructs match criteria with available TAGs listing.
- @satisfies SRS-180, SRS-237, SRS-396, SRS-408

### fn `def run_tokens(args: Namespace) -> None` (L4188-4217)
- @brief Execute tokens on the canonical documentation files in --docs-dir.
- @details Uses the mandatory `--prj-base` project base joined with the docs-dir value from ~/.config/usereq/config.json, selects only REQUIREMENTS.md/WORKFLOW.md/REFERENCES.md as direct regular files in fixed order, and delegates summary rendering to run_files_tokens.
- @param args Parsed CLI arguments namespace.
- @return None.
- @exception ReqError Raised when no canonical documentation file exists in configured docs-dir.
- @satisfies SRS-387, SRS-392, SRS-396, SRS-408

### fn `def run_files_static_check_cmd(files: list[str], args: Namespace) -> int` (L4218-4285)
- @brief Execute `files-static-check`: run static analysis on an explicit file list.
- @details Static-check configuration is loaded from `~/.config/usereq/config.json`. When the global configuration file cannot be located, emits a warning to stderr and continues with the SRS-424 default static-check configuration (SRS-254). Project base for dispatch context is the mandatory `--prj-base` value (SRS-253). For each file: - Resolves absolute path; skips with warning if not a regular file. - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on the lowercase extension. - Looks up language in the `"static-check"` config section; skips silently if absent. - Executes each configured language entry sequentially via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`. - For `Command` module entries, execution order is `<cmd> [params...] <filename>`. Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-253). The command ignores `"scan-by-dir"` and always dispatches per explicit input file (SRS-591). Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-253, SRS-255)
- @param files List of raw file paths supplied by the user.
- @param args Parsed CLI namespace; the mandatory `--prj-base` resolves the dispatch context.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @see SRS-253, SRS-254, SRS-255, SRS-341, SRS-396, SRS-408, SRS-591

### fn `def run_project_static_check_cmd(args: Namespace) -> int` (L4286-4454)
- @brief Execute `static-check`: run static analysis on project source and test files.
- @details Collects files from configured `src-dir` directories and the `tests-dir` directory (SRS-256, SRS-336), applies `EXCLUDED_DIRS` filtering and `SUPPORTED_EXTENSIONS` matching. If `tests-dir` is missing or invalid in the global configuration file, test directory inclusion is skipped silently without error (SRS-336). Files under `<tests-dir>/fixtures/` are excluded from static-check selection because they are fixture corpus inputs for parser/static-check tests and can intentionally contain diagnostics unrelated to project code quality gates. For each collected file: - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on lowercase extension. - Groups files under ordered, deduplicated scan roots: the configured `src-dir` entries followed by `tests-dir` (SRS-588). Per scan root and language: - Looks up language in the `"static-check"` section of `~/.config/usereq/config.json`. - Skips silently when no tool is configured for the file's language. - Resolves each configured entry's directory-scan mode through `entry_scan_by_dir` (SRS-584, SRS-585). - Dispatches `"scan-by-dir"`-false entries per selected file via `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)` (SRS-587); for `Command` entries, execution order is `<cmd> [params...] <filename>`. - Dispatches `"scan-by-dir"`-true entries as exactly one recursive `dispatch_static_check_for_directory(root, lang_config, fail_only=True, project_base=...)` invocation per root containing selected files of the entry's language (SRS-588, SRS-589); for `Command` entries, execution order is `<cmd> [params...] <root>`. - Excludes existing fixture-corpus directories from directory invocations through module-native exclusion flags (SRS-590). Dispatch context provides project root for checker runtime execution. All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-256). Overall exit code: max of all dispatch codes (0=all pass, 1=any fail). (SRS-256, SRS-257)
- @param args Parsed CLI namespace; requires the mandatory `--prj-base` argument.
- @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
- @throws ReqError If no source files are found.
- @see SRS-256, SRS-257, SRS-336, SRS-341, SRS-396, SRS-408, SRS-584, SRS-585, SRS-587, SRS-588, SRS-589, SRS-590, SRS-592

### fn `def _resolve_project_base(args: Namespace) -> Path` `priv` (L4455-4467)
- @brief Resolve the mandatory project base path for project-level commands.
- @details The project base is never derived from the current working directory and is never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
- @param args Parsed CLI arguments namespace.
- @return Absolute path of the project base supplied by `--prj-base`.
- @throws ReqError If `--prj-base` is missing or the resolved path does not exist.
- @satisfies SRS-392, SRS-394, SRS-395, SRS-396

### fn `def _resolve_project_src_dirs(args: Namespace) -> tuple[Path, list[str]]` `priv` (L4468-4498)
- @brief Resolve project base and src-dirs for project source commands.
- @details Loads the `src-dir` list from the user-global configuration file (`~/.config/usereq/config.json`) and resolves it against the mandatory `--prj-base` project base (SRS-392, SRS-396).
- @param args Input parameter `args`.
- @return {tuple[Path, list[str]]} Tuple `(project_base, src_dirs)`.
- @throws ReqError If `--prj-base` is missing or `src-dir` is invalid.
- @satisfies SRS-392, SRS-396

### fn `def _is_config_schema_command(args: Namespace) -> bool` `priv` (L4499-4516)
- @brief Detect the canonical configuration CLI command path.
- @details Configuration schema commands are `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` (SRS-519); they never trigger provider installation.
- @param args {Namespace} Parsed CLI namespace.
- @return {bool} True when any configuration schema command flag is present.

### fn `def run_config_schema_command(args: Namespace) -> int` (L4517-4577)
- @brief Execute one configuration schema command.
- @details Dispatches `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` against the user-global configuration file, writes payloads to stdout, and reports every diagnostic on stderr (SRS-519, SRS-532).
- @param args {Namespace} Parsed CLI namespace carrying the configuration flag values.
- @return {int} Process exit code: 0 on success, 1 on any configuration failure.
- @satisfies SRS-519, SRS-527, SRS-528, SRS-529, SRS-530, SRS-531, SRS-532

### fn `def main(argv: Optional[list[str]] = None) -> int` (L4578-4709)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.

- var `FORCE_ONLINE_RELEASE_CHECK = force_online_release_check` (L4592)
- @brief CLI entry point for console_scripts and `-m` execution.
- @details Returns an exit code (0 success, non-zero on error).
- @param argv Input parameter `argv`.
- @return {int} Function return value.
- var `FORCE_ONLINE_RELEASE_CHECK = previous_force_online_release_check` (L4599)
- var `VERBOSE = getattr(args, "verbose", False)` (L4616)
- var `DEBUG = getattr(args, "debug", False)` (L4617)
## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`REPO_ROOT`|var|pub|42||
|`RESOURCE_ROOT`|var|pub|45||
|`VERBOSE`|var|pub|48||
|`DEBUG`|var|pub|51||
|`REQUIREMENTS_TEMPLATE_NAME`|var|pub|54||
|`PERSISTED_CONFIG_KEYS`|var|pub|57||
|`AUTO_INSTALL_CONFIG_KEY`|var|pub|67||
|`VALID_PROVIDERS`|var|pub|70||
|`GLOBAL_CONFIG_DIRNAME`|var|pub|73||
|`GLOBAL_CONFIG_APP_DIRNAME`|var|pub|76||
|`GLOBAL_CONFIG_FILENAME`|var|pub|79||
|`home_dir`|fn|pub|83-93|def home_dir() -> Path|
|`get_global_config_path`|fn|pub|94-109|def get_global_config_path() -> Path|
|`guidelines_dir`|fn|pub|110-122|def guidelines_dir() -> Path|
|`templates_dir`|fn|pub|123-135|def templates_dir() -> Path|
|`format_home_relative_path`|fn|pub|136-159|def format_home_relative_path(path: Path) -> str|
|`provider_skills_root`|fn|pub|160-193|def provider_skills_root(provider: str) -> Path|
|`provider_skills_path`|fn|pub|194-207|def provider_skills_path(provider: str) -> str|
|`INVALID_WT_NAME_RE`|var|pub|208||
|`validate_provider_name`|fn|pub|212-234|def validate_provider_name(name: str) -> str|
|`resolve_provider_configs`|fn|pub|235-236|def resolve_provider_configs(|
|`ANSI_BRIGHT_RED`|var|pub|259||
|`ANSI_BRIGHT_GREEN`|var|pub|262||
|`ANSI_RESET`|var|pub|265||
|`RELEASE_CHECK_TIMEOUT_SECONDS`|var|pub|268||
|`RELEASE_CHECK_IDLE_DELAY_SECONDS`|var|pub|271||
|`RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS`|var|pub|274||
|`TOOL_PROGRAM_NAME`|var|pub|277||
|`TOOL_RECEIPT_FILENAME`|var|pub|283||
|`NON_REGISTRY_REQUIREMENT_KEYS`|var|pub|286||
|`RELEASE_CHECK_PROGRAM_NAME`|var|pub|292||
|`GITHUB_REPOSITORY_OWNER`|var|pub|297||
|`GITHUB_REPOSITORY_NAME`|var|pub|300||
|`RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME`|var|pub|303||
|`RELEASE_CHECK_IDLE_FILENAME`|var|pub|306||
|`GITHUB_RELEASES_LATEST_URL`|var|pub|309||
|`GITHUB_UPGRADE_SOURCE`|var|pub|318||
|`PYPI_PROJECT_JSON_URL`|var|pub|325||
|`UNKNOWN_VERSION_LABEL`|var|pub|331||
|`VERSION_REPORT_LABEL_WIDTH`|var|pub|334||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|337||
|`ReqError`|class|pub|341-358|class ReqError(Exception)|
|`ReqError.__init__`|fn|priv|346-358|def __init__(self, message: str, code: int = 1) -> None|
|`log`|fn|pub|359-368|def log(msg: str) -> None|
|`dlog`|fn|pub|369-379|def dlog(msg: str) -> None|
|`vlog`|fn|pub|380-390|def vlog(msg: str) -> None|
|`build_parser`|fn|pub|391-590|def build_parser() -> argparse.ArgumentParser|
|`parse_args`|fn|pub|886-895|def parse_args(argv: Optional[list[str]] = None) -> Names...|
|`load_package_version`|fn|pub|896-910|def load_package_version() -> str|
|`maybe_print_version`|fn|pub|911-959|def maybe_print_version(argv: list[str], pypi_latest: Opt...|
|`_resolve_github_upgrade_tag`|fn|priv|960-990|def _resolve_github_upgrade_tag() -> str|
|`_installed_tool_uses_registry_source`|fn|priv|991-1044|def _installed_tool_uses_registry_source() -> bool|
|`run_upgrade`|fn|pub|1045-1115|def run_upgrade(use_github: bool = False, force: bool = F...|
|`run_uninstall`|fn|pub|1116-1148|def run_uninstall() -> None|
|`normalize_release_tag`|fn|pub|1149-1161|def normalize_release_tag(tag: str) -> str|
|`parse_version_tuple`|fn|pub|1162-1186|def parse_version_tuple(version: str) -> tuple[int, ...] ...|
|`is_newer_version`|fn|pub|1187-1205|def is_newer_version(current: str, latest: str) -> bool|
|`parse_github_owner_repository`|fn|pub|1206-1232|def parse_github_owner_repository(remote_url: str) -> tup...|
|`read_git_remote_verbose`|fn|pub|1233-1252|def read_git_remote_verbose(cwd: str | None = None) -> str|
|`resolve_github_owner_repository_from_active_remotes`|fn|pub|1253-1313|def resolve_github_owner_repository_from_active_remotes()...|
|`resolve_pypi_latest_version_url`|fn|pub|1314-1323|def resolve_pypi_latest_version_url() -> str|
|`fetch_pypi_latest_version`|fn|pub|1324-1325|def fetch_pypi_latest_version(|
|`fetch_github_latest_version`|fn|pub|1361-1364|def fetch_github_latest_version(|
|`format_unix_timestamp_utc`|fn|pub|1403-1415|def format_unix_timestamp_utc(timestamp_seconds: int) -> str|
|`get_release_check_idle_file_path`|fn|pub|1416-1417|def get_release_check_idle_file_path(|
|`cleanup_release_check_idle_state_cache`|fn|pub|1434-1435|def cleanup_release_check_idle_state_cache(|
|`read_release_check_idle_state`|fn|pub|1458-1522|def read_release_check_idle_state(file_path: Path) -> dic...|
|`should_execute_release_check`|fn|pub|1523-1525|def should_execute_release_check(|
|`parse_retry_after_seconds`|fn|pub|1544-1546|def parse_retry_after_seconds(|
|`write_release_check_idle_state_payload`|fn|pub|1576-1579|def write_release_check_idle_state_payload(|
|`write_release_check_idle_state`|fn|pub|1606-1609|def write_release_check_idle_state(|
|`write_failed_release_check_idle_state`|fn|pub|1628-1632|def write_failed_release_check_idle_state(|
|`persist_failed_release_check_idle_state`|fn|pub|1660-1664|def persist_failed_release_check_idle_state(|
|`maybe_notify_newer_version`|fn|pub|1690-1691|def maybe_notify_newer_version(|
|`ensure_doc_directory`|fn|pub|1820-1821|def ensure_doc_directory(|
|`ensure_test_directory`|fn|pub|1850-1851|def ensure_test_directory(|
|`ensure_src_directory`|fn|pub|1880-1881|def ensure_src_directory(|
|`make_relative_if_contains_project`|fn|pub|1910-1951|def make_relative_if_contains_project(path_value: str, pr...|
|`resolve_absolute`|fn|pub|1952-1967|def resolve_absolute(normalized: str, project_base: Path)...|
|`resolve_git_root`|fn|pub|1968-1995|def resolve_git_root(target_path: Path) -> Path|
|`sanitize_branch_name`|fn|pub|1996-2005|def sanitize_branch_name(branch: str) -> str|
|`validate_wt_name`|fn|pub|2006-2017|def validate_wt_name(wt_name: str) -> bool|
|`load_full_config`|fn|pub|2018-2038|def load_full_config() -> dict|
|`save_config`|fn|pub|2039-2044|def save_config(|
|`update_directory_config`|fn|pub|2074-2077|def update_directory_config(|
|`load_config`|fn|pub|2115-2165|def load_config() -> dict[str, str | list[str]]|
|`load_static_check_from_config`|fn|pub|2166-2204|def load_static_check_from_config() -> dict|
|`_static_check_entry_identity`|fn|priv|2205-2206|def _static_check_entry_identity(|
|`load_persisted_providers`|fn|pub|2229-2270|def load_persisted_providers() -> list[str]|
|`_read_config_payload`|fn|priv|2271-2291|def _read_config_payload() -> dict|
|`_write_config_payload`|fn|priv|2292-2310|def _write_config_payload(payload: dict) -> None|
|`load_auto_install_enabled`|fn|pub|2311-2325|def load_auto_install_enabled() -> bool|
|`apply_enabled_providers`|fn|pub|2326-2355|def apply_enabled_providers(names: list[str]) -> None|
|`apply_disabled_providers`|fn|pub|2356-2384|def apply_disabled_providers(names: list[str]) -> None|
|`apply_enable_static_check_specs`|fn|pub|2385-2432|def apply_enable_static_check_specs(specs: list[str]) -> ...|
|`apply_disable_static_check_specs`|fn|pub|2433-2481|def apply_disable_static_check_specs(specs: list[str]) ->...|
|`apply_auto_install_config`|fn|pub|2482-2494|def apply_auto_install_config(enabled: bool) -> None|
|`_is_provider_config_command`|fn|priv|2495-2512|def _is_provider_config_command(args: Namespace) -> bool|
|`run_config_commands`|fn|pub|2513-2541|def run_config_commands(args: Namespace) -> None|
|`_non_symlink_regular_files`|fn|priv|2542-2565|def _non_symlink_regular_files(directory: Path) -> list[P...|
|`generate_guidelines_file_list`|fn|pub|2566-2586|def generate_guidelines_file_list() -> str|
|`generate_guidelines_file_names`|fn|pub|2587-2601|def generate_guidelines_file_names() -> list[str]|
|`generate_templates_file_names`|fn|pub|2602-2616|def generate_templates_file_names() -> list[str]|
|`_print_resource_report`|fn|priv|2617-2638|def _print_resource_report() -> None|
|`ensure_relative`|fn|pub|2639-2654|def ensure_relative(value: str, name: str, code: int) -> ...|
|`apply_replacements`|fn|pub|2655-2667|def apply_replacements(text: str, replacements: Mapping[s...|
|`write_text_file`|fn|pub|2668-2679|def write_text_file(dst: Path, text: str) -> None|
|`copy_with_replacements`|fn|pub|2680-2681|def copy_with_replacements(|
|`extract_frontmatter`|fn|pub|2696-2709|def extract_frontmatter(content: str) -> tuple[str, str]|
|`extract_purpose_first_bullet`|fn|pub|2710-2734|def extract_purpose_first_bullet(body: str) -> str|
|`_extract_section_text`|fn|priv|2735-2762|def _extract_section_text(body: str, section_name: str) -...|
|`extract_skill_description`|fn|pub|2763-2781|def extract_skill_description(frontmatter: str) -> str|
|`yaml_double_quote_escape`|fn|pub|2782-2791|def yaml_double_quote_escape(value: str) -> str|
|`list_docs_templates`|fn|pub|2792-2812|def list_docs_templates() -> list[Path]|
|`find_requirements_template`|fn|pub|2813-2830|def find_requirements_template(docs_templates: list[Path]...|
|`ensure_wrapped`|fn|pub|2831-2846|def ensure_wrapped(target: Path, project_base: Path, code...|
|`prune_empty_dirs`|fn|pub|2847-2863|def prune_empty_dirs(root: Path) -> None|
|`remove_generated_resources`|fn|pub|2864-2895|def remove_generated_resources() -> None|
|`_render_simple_table`|fn|priv|2896-2926|def _render_simple_table(headers: list[str], rows: list[l...|
|`_line`|fn|priv|2909-2917|def _line(cells: list[str]) -> str|
|`_border`|fn|priv|2918-2920|def _border(left: str, middle: str, right: str) -> str|
|`_provider_skill_installed`|fn|priv|2927-2944|def _provider_skill_installed(provider: str, skill_name: ...|
|`_packaged_prompt_names`|fn|priv|2945-2959|def _packaged_prompt_names() -> list[str]|
|`run_install`|fn|pub|2960-2975|def run_install(args: Namespace) -> None|
|`run_uninstall_providers`|fn|pub|2976-2993|def run_uninstall_providers(args: Namespace) -> None|
|`run_show`|fn|pub|2994-3101|def run_show(args: Namespace) -> None|
|`_maybe_auto_install_after_upgrade`|fn|priv|3102-3126|def _maybe_auto_install_after_upgrade(argv_list: list[str...|
|`run_set_directories`|fn|pub|3127-3190|def run_set_directories(args: Namespace) -> None|
|`_validate_enable_static_check_command_executables`|fn|priv|3191-3194|def _validate_enable_static_check_command_executables(|
|`run`|fn|pub|3223-3422|def run(args: Namespace) -> None|
|`VERBOSE`|var|pub|3243||
|`DEBUG`|var|pub|3244||
|`_format_install_table`|fn|priv|3363-3364|def _format_install_table(|
|`_wrap_cell`|fn|priv|3396-3418|def _wrap_cell(value: str, width: int, allow_wrap: bool) ...|
|`_render_row`|fn|priv|3419-3440|def _render_row(provider: str, skills: str) -> list[str]|
|`_colorize_table_border`|fn|priv|3457-3469|def _colorize_table_border(line: str) -> str|
|`SUPPORTED_EXTENSIONS`|var|pub|3482||
|`_collect_source_files`|fn|priv|3524-3581|def _collect_source_files(src_dirs: list[str], project_ba...|
|`_build_ascii_tree`|fn|priv|3582-3627|def _build_ascii_tree(paths: list[str]) -> str|
|`_emit`|fn|priv|3606-3608|def _emit(|
|`_format_files_structure_markdown`|fn|priv|3628-3642|def _format_files_structure_markdown(files: list[str], pr...|
|`_is_standalone_command`|fn|priv|3643-3654|def _is_standalone_command(args: Namespace) -> bool|
|`_is_project_scan_command`|fn|priv|3655-3672|def _is_project_scan_command(args: Namespace) -> bool|
|`_is_directory_config_command`|fn|priv|3673-3688|def _is_directory_config_command(args: Namespace) -> bool|
|`_require_prj_base`|fn|priv|3689-3707|def _require_prj_base(args: Namespace) -> Path|
|`_require_git_base_value`|fn|priv|3708-3727|def _require_git_base_value(args: Namespace) -> Path|
|`_require_git_base`|fn|priv|3728-3740|def _require_git_base(args: Namespace) -> Path|
|`run_git_check`|fn|pub|3741-3768|def run_git_check(args: Namespace) -> None|
|`run_docs_check`|fn|pub|3769-3798|def run_docs_check(args: Namespace) -> None|
|`run_git_wt_name`|fn|pub|3799-3823|def run_git_wt_name(args: Namespace) -> None|
|`_worktree_path_exists_exact`|fn|priv|3824-3853|def _worktree_path_exists_exact(git_path: Path, target_pa...|
|`_rollback_worktree_create`|fn|priv|3854-3890|def _rollback_worktree_create(git_path: Path, wt_path: Pa...|
|`run_git_wt_create`|fn|pub|3891-3946|def run_git_wt_create(args: Namespace) -> None|
|`run_git_wt_delete`|fn|pub|3947-4015|def run_git_wt_delete(args: Namespace) -> None|
|`run_files_tokens`|fn|pub|4016-4039|def run_files_tokens(files: list[str]) -> None|
|`run_files_references`|fn|pub|4040-4057|def run_files_references(files: list[str]) -> None|
|`run_files_compress`|fn|pub|4058-4077|def run_files_compress(files: list[str], enable_line_numb...|
|`run_files_find`|fn|pub|4078-4107|def run_files_find(args_list: list[str], enable_line_numb...|
|`run_references`|fn|pub|4108-4133|def run_references(args: Namespace) -> None|
|`run_compress_cmd`|fn|pub|4134-4156|def run_compress_cmd(args: Namespace) -> None|
|`run_find`|fn|pub|4157-4187|def run_find(args: Namespace) -> None|
|`run_tokens`|fn|pub|4188-4217|def run_tokens(args: Namespace) -> None|
|`run_files_static_check_cmd`|fn|pub|4218-4285|def run_files_static_check_cmd(files: list[str], args: Na...|
|`run_project_static_check_cmd`|fn|pub|4286-4454|def run_project_static_check_cmd(args: Namespace) -> int|
|`_resolve_project_base`|fn|priv|4455-4467|def _resolve_project_base(args: Namespace) -> Path|
|`_resolve_project_src_dirs`|fn|priv|4468-4498|def _resolve_project_src_dirs(args: Namespace) -> tuple[P...|
|`_is_config_schema_command`|fn|priv|4499-4516|def _is_config_schema_command(args: Namespace) -> bool|
|`run_config_schema_command`|fn|pub|4517-4577|def run_config_schema_command(args: Namespace) -> int|
|`main`|fn|pub|4578-4709|def main(argv: Optional[list[str]] = None) -> int|
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4592||
|`FORCE_ONLINE_RELEASE_CHECK`|var|pub|4599||
|`VERBOSE`|var|pub|4616||
|`DEBUG`|var|pub|4617||


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

# config_cli.py | Python | 1371L | 56 symbols | 12 imports | 59 comments
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

- var `BRANCH = "├── "` (L41)
- var `LAST = "└── "` (L44)
- @brief Structural marker for a configuration node with a later sibling (SRS-524)."""
- var `INDENT = "    "` (L47)
- @brief Structural marker for the final configuration sibling at its depth (SRS-524)."""
- var `CONTINUE = "│   "` (L50)
- @brief Exact four-ASCII-space ancestor prefix segment (SRS-524)."""
### class `class ConfigError(Exception)` : Exception (L57-74)
- @brief Sentinel marking an absent optional configuration value (SRS-527)."""
- @brief Expected configuration CLI failure with an English diagnostic.
- @details Carries the diagnostic text and the process exit code consumed by the CLI dispatcher so configuration failures never leak stack traces (SRS-532).
- fn `def __init__(self, message: str, code: int = 1) -> None` `priv` (L64-74)
  - @brief Expected configuration CLI failure with an English diagnostic.
  - @brief Initialize one configuration failure payload.
  - @details Carries the diagnostic text and the process exit code consumed by the CLI
dispatcher so configuration failures never leak stack traces (SRS-532).
  - @param message {str} English diagnostic text written to stderr.
  - @param code {int} Process exit code bound to the failure category.

### class `class RenderNode` `@dataclass` (L76-91)
- @brief One real configuration node of the rendered tree.
- @details Holds the canonical token, canonical path, node kind, the finalized heading line, attached detail blocks, and real child nodes. Tree topology derives exclusively from `children`; details never create structural depth (SRS-524, SRS-525).

### class `class Target` `@dataclass` (L93-107)
- @brief Resolved configuration path describing the operation target.
- @details `op` is one of `node`, `array_item`, `append`, `insert`, `dict_field`, or `map_key`. `container` is the mutable parent list/dictionary, `key` the list index or dictionary key, and `spec` the schema node governing the target value (SRS-533, SRS-534).

### fn `def default_config() -> dict[str, Any]` (L108-122)
- @brief Build the complete default configuration from the canonical schema.
- @details Defaults are deep-copied so callers never mutate the shared schema objects (SRS-521, SRS-529).
- @return {dict[str, Any]} Configuration payload holding every canonical key default.

### fn `def read_raw_payload(config_path: Path) -> dict[str, Any]` (L123-153)
- @brief Read the raw configuration JSON payload without applying defaults.
- @details Only the raw stored payload is returned; unknown keys are preserved here and dropped by the canonical writer (SRS-528, SRS-530).
- @param config_path {Path} Absolute global configuration file path.
- @return {dict[str, Any]} Parsed JSON object; empty dictionary when the file is absent.
- @throws {ConfigError} Raised when the file is unreadable, not JSON, or not a JSON object.

### fn `def _type_name(value: Any) -> str` `priv` (L154-172)
- @brief Return a stable English type name for one JSON value.
- @param value {Any} Parsed JSON value.
- @return {str} JSON type name used inside diagnostics.

### fn `def validate_node(node: SchemaNode, value: Any, path: str) -> None` (L173-275)
- @brief Validate one value against its schema node, including nested values.
- @details Covers primitives, enums, arrays, map keys, fixed-field dictionaries, required fields, the Command `cmd` cross-field constraint, and the `scan-by-dir` capability cross-field constraint (SRS-530, SRS-536, SRS-586).
- @param node {SchemaNode} Schema node governing the value.
- @param value {Any} Parsed JSON value to validate.
- @param path {str} Canonical path used inside diagnostics.
- @return {None} Function return value.
- @throws {ConfigError} Raised with an English diagnostic on any schema violation.

### fn `def normalize_config(payload: dict[str, Any]) -> dict[str, Any]` (L276-295)
- @brief Merge a raw payload over the schema defaults and validate stored values.
- @details Unknown top-level keys are outside the canonical schema and are therefore ignored here and dropped by `write_config` (SRS-288, SRS-530).
- @param payload {dict[str, Any]} Raw stored JSON payload.
- @return {dict[str, Any]} Effective configuration holding every canonical key.
- @throws {ConfigError} Raised when a stored canonical value violates the schema.

### fn `def load_effective_config(config_path: Path) -> dict[str, Any]` (L296-305)
- @brief Load and validate the effective configuration for one configuration command.
- @param config_path {Path} Absolute global configuration file path.
- @return {dict[str, Any]} Effective configuration with defaults applied.
- @throws {ConfigError} Raised when the file is unreadable or schema-invalid.

### fn `def write_config(config_path: Path, config: dict[str, Any]) -> None` (L306-351)
- @brief Atomically persist the canonical configuration payload.
- @details Creates missing parent directories, writes a same-directory temporary file, flushes and fsyncs it, preserves the existing file mode, atomically replaces the target, and fsyncs the parent directory (SRS-529, SRS-531).
- @param config_path {Path} Absolute global configuration file path.
- @param config {dict[str, Any]} Fully validated effective configuration.
- @return {None} Function return value.
- @throws {ConfigError} Raised when the write fails; the original file is preserved.

### fn `def ensure_config_file(config_path: Path) -> None` (L352-369)
- @brief Bootstrap the global configuration file from schema defaults when absent.
- @details Missing parent directories are created and the file is initialized from the canonical schema defaults; an existing file is never overwritten (SRS-529).
- @param config_path {Path} Absolute global configuration file path.
- @return {None} Function return value.
- @throws {ConfigError} Raised when the path is a directory or the bootstrap write fails.

### fn `def _parse_index(token: str, path: str) -> int` `priv` (L370-385)
- @brief Parse one non-negative decimal array index token.
- @param token {str} Raw path token.
- @param path {str} Canonical path used inside diagnostics.
- @return {int} Parsed zero-based index.
- @throws {ConfigError} Raised for negative, signed, or non-decimal tokens.

### fn `def _out_of_range(owner_path: str, index: int, length: int) -> ConfigError` `priv` (L386-400)
- @brief Build the out-of-range diagnostic for an array access.
- @param owner_path {str} Canonical path of the owning array parameter.
- @param index {int} Rejected index.
- @param length {int} Current array length.
- @return {ConfigError} English diagnostic describing the valid range and append option.

### fn `def _child_of_section(spec: SchemaNode, token: str, path: str) -> SchemaNode` `priv` (L401-417)
- @brief Resolve one section/dictionary field token or raise an unknown-token error.
- @param spec {SchemaNode} Section or dictionary node holding candidate fields.
- @param token {str} Exact canonical field token.
- @param path {str} Canonical path used inside diagnostics.
- @return {SchemaNode} Matching field node.
- @throws {ConfigError} Raised when the token is not a canonical schema token.

### fn `def resolve_target(config: dict[str, Any], path: str) -> Target` (L418-548)
- @brief Resolve a canonical colon-separated path against the configuration schema.
- @details Paths are resolved token by token against the schema, never against displayed strings; `append`, `+`, and `insert:<Idx>` are recognized only inside array paths (SRS-520, SRS-533, SRS-534).
- @param config {dict[str, Any]} Effective configuration used as the resolution root.
- @param path {str} Canonical colon-separated configuration path.
- @return {Target} Resolved operation target.
- @throws {ConfigError} Raised for empty tokens, unknown tokens, invalid indices, out-of-range indices, and missing dynamic map keys.

### fn `def parse_cli_value(` (L549-550)

### fn `def get_value(config: dict[str, Any], path: str) -> Any` (L597-618)
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

### fn `def apply_set(config: dict[str, Any], path: str, text: str) -> dict[str, Any]` (L619-660)
- @brief Apply one `--set` operation to a copy of the effective configuration.
- @details Supports primitives, whole branches, whole arrays/maps, single array items, append and insert operations, dictionary fields, and dynamic map keys (SRS-530, SRS-533, SRS-534, SRS-535).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @param text {str} Raw CLI value text.
- @return {dict[str, Any]} New validated configuration payload.
- @throws {ConfigError} Raised before mutation when the path or value is invalid.

### fn `def apply_unset(config: dict[str, Any], path: str) -> dict[str, Any]` (L661-704)
- @brief Apply one `--unset` operation to a copy of the effective configuration.
- @details Restores declared schema defaults, deletes optional fields and map keys, and removes array elements while keeping indices contiguous (SRS-530, SRS-533, SRS-536).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @return {dict[str, Any]} New validated configuration payload.
- @throws {ConfigError} Raised for write-only operations, absent keys, and required fields.

### fn `def _display_width(text: str) -> int` `priv` (L705-718)
- @brief Measure the terminal display width of one table cell.
- @param text {str} Sanitized cell text.
- @return {int} Display column count honoring wide and combining characters.

### fn `def _sanitize_cell(text: str) -> str` `priv` (L719-739)
- @brief Escape control characters so one cell stays on one physical line.
- @param text {str} Raw cell payload.
- @return {str} Printable single-line cell text.

### fn `def format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]` (L740-776)
- @brief Render one rectangular Unicode box-drawing table.
- @details Column widths derive from the maximum display width of the header and every formatted cell; all borders share the same column boundaries (SRS-539).
- @param headers {Sequence[str]} Column header labels.
- @param rows {Sequence[Sequence[str]]} Cell values matching the header count.
- @return {list[str]} Physical table lines without structural tree prefixes.

### fn `def border(left: str, middle: str, right: str) -> str` (L759-762)
- @brief Render one rectangular Unicode box-drawing table.
- @brief Build one horizontal table border line.
- @details Column widths derive from the maximum display width of the header and every
formatted cell; all borders share the same column boundaries (SRS-539).
- @param headers {Sequence[str]} Column header labels.
- @param rows {Sequence[Sequence[str]]} Cell values matching the header count.
- @return {list[str]} Physical table lines without structural tree prefixes.

### fn `def line(cells: Sequence[str]) -> str` (L763-770)
- @brief Build one padded table content line.

### fn `def render_tree(root: RenderNode) -> list[str]` (L777-792)
- @brief Render one configuration tree with the mandatory prefix algorithm.
- @details The display root has no structural marker and attached root details use a four-space indent; every real child is emitted by `_emit_node` (SRS-524, SRS-525).
- @param root {RenderNode} Display root of the requested tree.
- @return {list[str]} Complete physical output lines.

### fn `def _emit_node(` `priv` (L793-797)

### fn `def render_text(root: RenderNode) -> str` (L825-833)
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

### fn `def _json_value(value: Any) -> str` `priv` (L834-842)
- @brief Encode one value as JSON text for display.
- @param value {Any} JSON-serializable value.
- @return {str} JSON-encoded text with non-ASCII characters preserved.

### fn `def _shell(value: str) -> str` `priv` (L843-851)
- @brief Shell-quote one literal value for a copyable command example.
- @param value {str} Literal value.
- @return {str} POSIX shell-quoted value.

### fn `def _example_item(node: SchemaNode) -> str` `priv` (L852-862)
- @brief Choose a schema-valid example value for one collection item.
- @param node {SchemaNode} Item schema node.
- @return {str} Example value text.

### fn `def _example_key(map_node: SchemaNode) -> str` `priv` (L863-873)
- @brief Choose a schema-valid example key for one dynamic map.
- @param map_node {SchemaNode} Map schema node.
- @return {str} Example key text.

### fn `def _print_marker(spec: SchemaNode, value: Any) -> str` `priv` (L881-894)
- @brief Schema-valid alternative example values for string parameters (SRS-541)."""
- @brief Build the default/custom status marker of one primitive parameter.
- @param spec {SchemaNode} Parameter schema node.
- @param value {Any} Current typed value.
- @return {str} Empty text for nodes without defaults, otherwise the status marker.

### fn `def _collection_summary(spec: SchemaNode, value: Any, path: str) -> str` `priv` (L895-927)
- @brief Build the `--print` value summary of one collection parameter.
- @details Empty collections emit a complete-path action hint instead of an empty table (SRS-537, SRS-539).
- @param spec {SchemaNode} Collection schema node.
- @param value {Any} Current collection value.
- @param path {str} Canonical parameter path.
- @return {str} Collection summary text.

### fn `def _example_map_value(item: SchemaNode) -> str` `priv` (L928-942)
- @brief Build one schema-valid example JSON text for a map value.
- @param item {SchemaNode} Map value schema node.
- @return {str} JSON text accepted by the map value schema.

### fn `def _value_cell(spec: SchemaNode, value: Any) -> str` `priv` (L943-957)
- @brief Render one table cell value for a configuration value.
- @param spec {SchemaNode} Schema node of the value.
- @param value {Any} JSON-serializable value.
- @return {str} Single-line cell text.

### fn `def _print_parameter_details(` `priv` (L958-959)

### fn `def _dictionary_fields(spec: SchemaNode) -> tuple[SchemaNode, ...]` `priv` (L1003-1015)
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

### fn `def _item_schema_table(fields: Sequence[SchemaNode]) -> list[str]` `priv` (L1016-1045)
- @brief Render the `Item Schema` table of one fixed-field dictionary.
- @param fields {Sequence[SchemaNode]} Fixed field schema nodes.
- @return {list[str]} Table lines.

### fn `def _array_examples(spec: SchemaNode, path: str) -> list[list[str]]` `priv` (L1046-1082)
- @brief Build the attached `--info` command examples of one array parameter.
- @details Single-item operations receive exactly one JSON item; the whole-array overwrite receives a JSON array (SRS-535, SRS-541).
- @param spec {SchemaNode} Array schema node.
- @param path {str} Canonical array path.
- @return {list[list[str]]} Detail blocks with complete copyable commands.

### fn `def _info_parameter_details(spec: SchemaNode, path: str) -> list[list[str]]` `priv` (L1083-1161)
- @brief Build the attached `--info` details of one parameter node.
- @details Required dictionary fields without defaults never advertise a reset command (SRS-536, SRS-538, SRS-541).
- @param spec {SchemaNode} Parameter schema node.
- @param path {str} Canonical parameter path.
- @return {list[list[str]]} Attached detail blocks with defaults, commands, and tables.

### fn `def _print_parameter_heading(spec: SchemaNode, value: Any, token: str, path: str) -> str` `priv` (L1162-1178)
- @brief Build the `--print` heading of one parameter node.
- @param spec {SchemaNode} Parameter schema node.
- @param value {Any} Current typed value.
- @param token {str} Exact canonical node token.
- @param path {str} Canonical node path.
- @return {str} Heading text without structural prefix.

### fn `def _info_parameter_heading(spec: SchemaNode, token: str) -> str` `priv` (L1179-1191)
- @brief Build the `--info` heading of one parameter node.
- @param spec {SchemaNode} Parameter schema node.
- @param token {str} Exact canonical node token.
- @return {str} `Token - [Type: constraints] Description` heading text.

### fn `def _build_node(` `priv` (L1192-1197)

### fn `def _section_heading(path: str, info: bool) -> str` `priv` (L1244-1256)
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

### fn `def build_full_tree(config: dict[str, Any], info: bool) -> RenderNode` (L1257-1277)
- @brief Build the complete configuration tree for `--print` or `--info`.
- @param config {dict[str, Any]} Effective configuration.
- @param info {bool} True for `--info`; False for `--print`.
- @return {RenderNode} Virtual display root holding the `Configuration` section.

### fn `def build_subtree(config: dict[str, Any], path: str, info: bool) -> RenderNode` (L1278-1301)
- @brief Build the requested subtree or parameter display.
- @details No ancestors are invented; the requested node becomes the display root with four-space-indented details and normally rendered real children (SRS-526).
- @param config {dict[str, Any]} Effective configuration.
- @param path {str} Canonical colon-separated configuration path.
- @param info {bool} True for `--info`; False for `--print`.
- @return {RenderNode} Requested node as the unconnected display root.
- @throws {ConfigError} Raised for unknown paths and non-displayable collection elements.

### fn `def handle_get(config_path: Path, path: str) -> str` (L1302-1313)
- @brief Execute one `--get` read and return JSON text.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @return {str} JSON-encoded value text.
- @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.

### fn `def handle_set(config_path: Path, path: str, text: str) -> None` (L1314-1327)
- @brief Execute one `--set` write.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @param text {str} Raw CLI value text.
- @return {None} Function return value.
- @throws {ConfigError} Raised before mutation when the operation is invalid.

### fn `def handle_unset(config_path: Path, path: str) -> None` (L1328-1340)
- @brief Execute one `--unset` write.
- @param config_path {Path} Absolute global configuration file path.
- @param path {str} Canonical configuration path.
- @return {None} Function return value.
- @throws {ConfigError} Raised before mutation when the operation is invalid.

### fn `def handle_print_raw(config_path: Path) -> bytes` (L1341-1357)
- @brief Return the unmodified on-disk configuration file bytes.
- @details Never reformats, prepends a heading, or appends explanatory text (SRS-528).
- @param config_path {Path} Absolute global configuration file path.
- @return {bytes} Raw file bytes exactly as stored.
- @throws {ConfigError} Raised when the bootstrapped file cannot be read.

### fn `def handle_display(config_path: Path, path: Optional[str], info: bool) -> str` (L1358-1372)
- @brief Execute one `--print` or `--info` display request.
- @param config_path {Path} Absolute global configuration file path.
- @param path {Optional[str]} Requested canonical path; None renders the full tree.
- @param info {bool} True for `--info`; False for `--print`.
- @return {str} Rendered tree text without a trailing newline.
- @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`BRANCH`|var|pub|41||
|`LAST`|var|pub|44||
|`INDENT`|var|pub|47||
|`CONTINUE`|var|pub|50||
|`ConfigError`|class|pub|57-74|class ConfigError(Exception)|
|`ConfigError.__init__`|fn|priv|64-74|def __init__(self, message: str, code: int = 1) -> None|
|`RenderNode`|class|pub|76-91|class RenderNode|
|`Target`|class|pub|93-107|class Target|
|`default_config`|fn|pub|108-122|def default_config() -> dict[str, Any]|
|`read_raw_payload`|fn|pub|123-153|def read_raw_payload(config_path: Path) -> dict[str, Any]|
|`_type_name`|fn|priv|154-172|def _type_name(value: Any) -> str|
|`validate_node`|fn|pub|173-275|def validate_node(node: SchemaNode, value: Any, path: str...|
|`normalize_config`|fn|pub|276-295|def normalize_config(payload: dict[str, Any]) -> dict[str...|
|`load_effective_config`|fn|pub|296-305|def load_effective_config(config_path: Path) -> dict[str,...|
|`write_config`|fn|pub|306-351|def write_config(config_path: Path, config: dict[str, Any...|
|`ensure_config_file`|fn|pub|352-369|def ensure_config_file(config_path: Path) -> None|
|`_parse_index`|fn|priv|370-385|def _parse_index(token: str, path: str) -> int|
|`_out_of_range`|fn|priv|386-400|def _out_of_range(owner_path: str, index: int, length: in...|
|`_child_of_section`|fn|priv|401-417|def _child_of_section(spec: SchemaNode, token: str, path:...|
|`resolve_target`|fn|pub|418-548|def resolve_target(config: dict[str, Any], path: str) -> ...|
|`parse_cli_value`|fn|pub|549-550|def parse_cli_value(|
|`get_value`|fn|pub|597-618|def get_value(config: dict[str, Any], path: str) -> Any|
|`apply_set`|fn|pub|619-660|def apply_set(config: dict[str, Any], path: str, text: st...|
|`apply_unset`|fn|pub|661-704|def apply_unset(config: dict[str, Any], path: str) -> dic...|
|`_display_width`|fn|priv|705-718|def _display_width(text: str) -> int|
|`_sanitize_cell`|fn|priv|719-739|def _sanitize_cell(text: str) -> str|
|`format_table`|fn|pub|740-776|def format_table(headers: Sequence[str], rows: Sequence[S...|
|`border`|fn|pub|759-762|def border(left: str, middle: str, right: str) -> str|
|`line`|fn|pub|763-770|def line(cells: Sequence[str]) -> str|
|`render_tree`|fn|pub|777-792|def render_tree(root: RenderNode) -> list[str]|
|`_emit_node`|fn|priv|793-797|def _emit_node(|
|`render_text`|fn|pub|825-833|def render_text(root: RenderNode) -> str|
|`_json_value`|fn|priv|834-842|def _json_value(value: Any) -> str|
|`_shell`|fn|priv|843-851|def _shell(value: str) -> str|
|`_example_item`|fn|priv|852-862|def _example_item(node: SchemaNode) -> str|
|`_example_key`|fn|priv|863-873|def _example_key(map_node: SchemaNode) -> str|
|`_print_marker`|fn|priv|881-894|def _print_marker(spec: SchemaNode, value: Any) -> str|
|`_collection_summary`|fn|priv|895-927|def _collection_summary(spec: SchemaNode, value: Any, pat...|
|`_example_map_value`|fn|priv|928-942|def _example_map_value(item: SchemaNode) -> str|
|`_value_cell`|fn|priv|943-957|def _value_cell(spec: SchemaNode, value: Any) -> str|
|`_print_parameter_details`|fn|priv|958-959|def _print_parameter_details(|
|`_dictionary_fields`|fn|priv|1003-1015|def _dictionary_fields(spec: SchemaNode) -> tuple[SchemaN...|
|`_item_schema_table`|fn|priv|1016-1045|def _item_schema_table(fields: Sequence[SchemaNode]) -> l...|
|`_array_examples`|fn|priv|1046-1082|def _array_examples(spec: SchemaNode, path: str) -> list[...|
|`_info_parameter_details`|fn|priv|1083-1161|def _info_parameter_details(spec: SchemaNode, path: str) ...|
|`_print_parameter_heading`|fn|priv|1162-1178|def _print_parameter_heading(spec: SchemaNode, value: Any...|
|`_info_parameter_heading`|fn|priv|1179-1191|def _info_parameter_heading(spec: SchemaNode, token: str)...|
|`_build_node`|fn|priv|1192-1197|def _build_node(|
|`_section_heading`|fn|priv|1244-1256|def _section_heading(path: str, info: bool) -> str|
|`build_full_tree`|fn|pub|1257-1277|def build_full_tree(config: dict[str, Any], info: bool) -...|
|`build_subtree`|fn|pub|1278-1301|def build_subtree(config: dict[str, Any], path: str, info...|
|`handle_get`|fn|pub|1302-1313|def handle_get(config_path: Path, path: str) -> str|
|`handle_set`|fn|pub|1314-1327|def handle_set(config_path: Path, path: str, text: str) -...|
|`handle_unset`|fn|pub|1328-1340|def handle_unset(config_path: Path, path: str) -> None|
|`handle_print_raw`|fn|pub|1341-1357|def handle_print_raw(config_path: Path) -> bytes|
|`handle_display`|fn|pub|1358-1372|def handle_display(config_path: Path, path: Optional[str]...|


---

# config_schema.py | Python | 379L | 21 symbols | 3 imports | 30 comments
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
### fn `def static_check_dir_scan_default(module: Any, cmd: Any = None) -> bool` (L109-134)
- @brief Command `cmd` binaries supporting recursive directory-scan execution (SRS-584)."""
- @brief Resolve the default directory-scan mode of one static-check entry.
- @details Capability table: `Pylance` and `Ruff` are always capable, `Dummy` is never capable, and `Command` is capable exactly when `cmd` is `cppcheck`, `eslint`, `ruff`, or `pyright`. Non-string tokens are never capable. Complexity: O(1). No side effects.
- @param module {Any} Raw module token; matched case-insensitively against `STATIC_CHECK_MODULES`.
- @param cmd {Any} Raw Command `cmd` token; matched lowercased against `STATIC_CHECK_DIR_SCAN_COMMANDS`.
- @return {bool} True exactly for SRS-584 directory-scan-capable entries, False otherwise.
- @satisfies SRS-584, SRS-585

### class `class SchemaNode` `@dataclass(frozen=True)` (L170-201)
- @brief Typed schema node describing one configuration token or collection element.
- @details Nodes form an ordered tree rooted at `CONFIG_SECTION`. A node carries the exact canonical token, the node kind, a concise English description, the textual type label and constraints used by `--info`, the typed default (or `NO_DEFAULT`), enumeration metadata, and the child collection definitions used by validation and rendering (SRS-521, SRS-522, SRS-538).
- fn `def has_default(self) -> bool` (L197-201)
  - @brief Return True when the node declares a typed default value (SRS-536).

### fn `def _entry_fields() -> tuple[SchemaNode, ...]` `priv` (L202-251)
- @brief Build the fixed field set of one static-check dictionary entry (SRS-540).
- @return {tuple[SchemaNode, ...]} Ordered `module`, `cmd`, `params`, and `scan-by-dir` field nodes.

- var `CONFIG_SECTION = SchemaNode(` (L272)
- @brief Array of static-check entries stored under one canonical language key (SRS-540)."""
- var `ROOT_LABEL = "Application_Configuration"` (L349)
- @brief Root schema section holding every persisted configuration parameter (SRS-521)."""
### fn `def find_field(node: SchemaNode, token: str) -> Optional[SchemaNode]` (L356-370)
- @brief Canonical persisted configuration keys in schema order (SRS-288, SRS-521)."""
- @brief Look up one ordered child field of a section or dictionary node.
- @details Matching is case-sensitive and byte-exact so path resolution never depends on displayed labels or decorative text (SRS-520, SRS-522).
- @param node {SchemaNode} Section or dictionary node providing the candidate fields.
- @param token {str} Exact canonical field token to resolve.
- @return {Optional[SchemaNode]} Matching field node, or None when the token is unknown.

### fn `def canonical_path(tokens: tuple[str, ...]) -> str` (L371-380)
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
|`static_check_dir_scan_default`|fn|pub|109-134|def static_check_dir_scan_default(module: Any, cmd: Any =...|
|`SchemaNode`|class|pub|170-201|class SchemaNode|
|`SchemaNode.has_default`|fn|pub|197-201|def has_default(self) -> bool|
|`_entry_fields`|fn|priv|202-251|def _entry_fields() -> tuple[SchemaNode, ...]|
|`CONFIG_SECTION`|var|pub|272||
|`ROOT_LABEL`|var|pub|349||
|`find_field`|fn|pub|356-370|def find_field(node: SchemaNode, token: str) -> Optional[...|
|`canonical_path`|fn|pub|371-380|def canonical_path(tokens: tuple[str, ...]) -> str|


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

# static_check.py | Python | 1065L | 34 symbols | 10 imports | 73 comments
> Path: `src/usereq/static_check.py`
- @brief Static code analysis dispatch module implementing Dummy/Pylance/Ruff/Command check classes.
- @details Provides a class hierarchy for running static analysis tools against resolved file lists.
Exposes `run_static_check(argv)` as the primary entry point for `--test-static-check` called
from cli.py. Also exposes `parse_enable_static_check`, `dispatch_static_check_for_file`,
`dispatch_static_check_for_directory`, `entry_scan_by_dir`, `STATIC_CHECK_LANG_CANONICAL`,
and `STATIC_CHECK_EXT_TO_LANG` for `--enable-static-check`, `files-static-check`
and `static-check` subcommand support.
Class hierarchy: StaticCheckBase (Dummy) -> StaticCheckPylance, StaticCheckRuff, StaticCheckCommand.
File resolution supports: explicit file paths, glob patterns (with full `**` recursive expansion),
and direct-children-only directory traversal. No custom `--recursive` flag; recursive traversal
is expressed via `**` glob syntax (e.g., `src/**/*.py`).
Directory-scan execution (`scan-by-dir`) dispatches one recursive checker invocation per
configured root directory instead of one invocation per file (SRS-584..SRS-592).
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
from typing import List, Mapping, Optional, Sequence
from .cli import ReqError
from .config_schema import static_check_dir_scan_default
```

## Definitions

### fn `def entry_scan_by_dir(lang_config: Mapping[str, object]) -> bool` (L126-142)
- @brief Maps directory-scan-capable Command binaries to their exclusion flag tokens.
- @brief Resolve the effective directory-scan mode of one static-check entry.
- @details Drives the SRS-590 fixture-corpus exclusion arguments appended to directory-scan
invocations; capability membership mirrors `STATIC_CHECK_DIR_SCAN_COMMANDS`.
- @details Non-boolean stored values fall back to the capability default resolved through `static_check_dir_scan_default(module, cmd)`. Complexity: O(1). No side effects.
- @param lang_config {Mapping[str, object]} Entry mapping with optional boolean `"scan-by-dir"`.
- @return {bool} Stored boolean when present, otherwise the SRS-584 capability default.
- @see SRS-584, SRS-590
- @satisfies SRS-584, SRS-585

### fn `def _split_csv_like_tokens(spec_rhs: str) -> list[str]` `priv` (L147-181)
- @brief Split a comma-separated SPEC right-hand side with quote-aware token boundaries.
- @details - Supported quote delimiters: single quote `'` and double quote `"`. - Commas split tokens only when parser is outside a quoted segment. - Quote delimiters are not included in output tokens. - Leading and trailing whitespace for each token is stripped.
- @param spec_rhs Text after `LANG=` in `--enable-static-check`.
- @return Token list where commas inside `'...'` or `"..."` do not split tokens.
- @see SRS-260, SRS-250

### fn `def parse_enable_static_check(spec: str) -> tuple[str, dict]` (L182-258)
- @brief Parse a single `--enable-static-check` SPEC string into a (lang, config_dict) pair.
- @details Parse steps: 1. Split on the first `=`; left side is LANG token, right side is `MODULE[,...]`. 2. Normalize LANG via `STATIC_CHECK_LANG_CANONICAL` (case-insensitive). 3. Parse right side as comma-separated tokens; first token is MODULE (case-insensitive, validated against `_CANONICAL_MODULES`). 4. For Command: next token is `cmd` (mandatory); all subsequent tokens are `params`. 5. For all other modules: all tokens after MODULE are `params`. 6. `params` key is omitted when the list is empty. 7. `cmd` key is omitted for non-Command modules. 8. Surrounding quote delimiters (`'` or `"`) are stripped from parsed tokens. Note: PARAM values containing `,` must be wrapped with `'` or `"` in SPEC.
- @param spec Raw SPEC string in the format `LANG=MODULE[,CMD[,PARAM...]]`.
- @return Tuple `(canonical_lang, config_dict)` where `config_dict` contains `"module"` and optionally `"cmd"` (Command only) and `"params"` (non-empty list only).
- @throws ReqError If `=` separator is absent, language is unknown, or module is unknown.
- @see SRS-260, SRS-248, SRS-249, SRS-250

### fn `def dispatch_static_check_for_file(` (L263-268)

### fn `def dispatch_static_check_for_directory(` (L323-329)
- @brief Dispatch static-check for a single file based on a language config dict.
- @details Module dispatch table:
- `"Dummy"` (case-insensitive) -> `StaticCheckBase`
- `"Pylance"` -> `StaticCheckPylance`
- `"Ruff"` -> `StaticCheckRuff`
- `"Command"` -> `StaticCheckCommand` (requires `"cmd"` key)
Instantiates the checker with `inputs=[filepath]`, `extra_args=params`, and `fail_only`.
For Pylance, forwards `project_base` runtime context.
Delegates actual check to `checker.run()`.
- @param filepath Absolute path of the file to analyse.
- @param lang_config Dict with keys `"module"` (str), optional `"cmd"` (str, Command only),
optional `"params"` (list[str]).
- @param fail_only When True, suppress all stdout output for passing checks (SRS-253, SRS-256).
- @param project_base Absolute project root used for checker runtime context.
- @return Exit code: 0 on pass, 1 on fail.
- @throws ReqError If module is unknown, or Command module is missing `"cmd"`.
- @see SRS-261, SRS-253, SRS-256, SRS-341

### fn `def _resolve_files(inputs: Sequence[str]) -> List[str]` `priv` (L388-430)
- @brief Resolve a mixed list of paths, glob patterns, and directories into regular files.
- @details Resolution order per element: 1. If the element contains a glob wildcard character (`*`, `?`, `[`) expand via `glob.glob(entry, recursive=True)`, enabling full `**` recursive expansion (e.g., `src/**/*.py` matches all `.py` files under `src/` at any depth). 2. If the element is an existing directory, iterate direct children only (flat traversal). 3. Otherwise treat as a literal file path; include if it is a regular file. Symlinks to regular files are included. Non-existent paths that do not match a glob produce a warning on stderr and are skipped.
- @param inputs Sequence of raw path strings (file, directory, or glob pattern).
- @return Sorted deduplicated list of resolved absolute file paths (regular files only).

### class `class StaticCheckBase` (L435-634)
- @brief Dummy static-check class; base of the static analysis class hierarchy.
- @details Iterates over resolved input files and emits a per-file header line plus `Result: OK`. Subclasses override `_check_file` to provide tool-specific logic. File resolution is delegated to `_resolve_files`. When `fail_only` is True, passing files produce no output (SRS-241, SRS-253, SRS-256).
- fn `def __init__(` `priv` (L447-452)
  - @brief Dummy static-check class; base of the static analysis class hierarchy.
  - @details Iterates over resolved input files and emits a per-file header line plus `Result: OK`.
Subclasses override `_check_file` to provide tool-specific logic.
File resolution is delegated to `_resolve_files`.
When `fail_only` is True, passing files produce no output (SRS-241, SRS-253, SRS-256).
- fn `def is_available(self) -> tuple[bool, str]` (L472-481)
  - @brief Probe checker availability before execution.
  - @details Base implementation (Dummy): always available. Subclasses override to verify tool module or binary availability (SRS-427).
  - @return {tuple[bool, str]} Tuple `(available, reason)`; `(True, "")` when available.
  - @satisfies SRS-427
- fn `def run(self) -> int` (L482-524)
  - @brief Execute the static check for all resolved files.
  - @details If the resolved file list is empty a warning is printed to stderr and 0 is returned. Before any file is checked the SRS-427 pre-flight availability probe runs; when the checker is unavailable every file emits header, `Result: FAIL`, English evidence identifying the missing checker or binary, and one trailing blank line in both `fail_only` modes, the overall exit code is 1, and no exception is raised (SRS-428). For each file `_check_file` is called; the overall return code is the maximum of all per-file return codes (0 = all OK, 1 = at least one FAIL). When `fail_only` is True, trailing blank separator lines are emitted only for failing files.
  - @return Exit code: 0 if all files pass (or file list is empty), 1 if any file fails.
  - @satisfies SRS-427, SRS-428
- fn `def run_directory(self, target: str, exclude_dirs: Sequence[str] = ()) -> int` (L525-586)
  - @brief Execute one recursive directory-scan checker invocation.
  - @details Runs the SRS-427 availability pre-flight; an unavailable checker or an unsupported directory command emits header, `Result: FAIL`, English evidence, and one trailing blank line in both fail_only modes, returns 1, and never raises (SRS-428). Otherwise executes `_directory_command(...)` exactly once with the root directory as target, aggregates the subprocess exit code, and renders the SRS-241..SRS-244 block shape with the directory path in place of the filename (SRS-592); when `fail_only` is True a passing scan produces no output.
  - @param target {str} Absolute root directory path scanned recursively by the checker.
  - @param exclude_dirs {Sequence[str]} Absolute directory paths excluded through module-native flags (SRS-590).
  - @return {int} Exit code: 0 on pass, 1 on fail.
  - @satisfies SRS-427, SRS-428, SRS-588, SRS-589, SRS-592
- fn `def _directory_command(` `priv` (L587-588)
- fn `def _dir_exclude_tokens(self, exclude_dir: str) -> List[str]` `priv` (L600-608)
  - @brief Build the checker command for one recursive directory-scan invocation.
  - @brief Build the module-native exclusion tokens for one excluded directory.
  - @details Base implementation (Dummy): directory scanning is unsupported (SRS-584).
  - @details Built-in module checkers exclude through `--exclude` (SRS-590).
  - @param target {str} Absolute root directory path passed as the checker target.
  - @param exclude_args {Sequence[str]} SRS-590 exclusion argument tokens.
  - @param exclude_dir {str} Absolute directory path excluded from the recursive scan.
  - @return {Optional[List[str]]} Full subprocess argument vector; None when the module
does not support directory scanning.
  - @return {List[str]} Exclusion flag and path tokens appended before the target.
- fn `def _header_line(self, filepath: str) -> str` `priv` (L613-623)
  - @brief Build the per-file header line for output.
  - @details Format: `# Static-Check(<LABEL>): <filepath> [<extra_args>]`. When `extra_args` is empty the bracket section is omitted.
  - @param filepath Absolute path of the file being checked.
  - @return Formatted header string including label, filename, and extra args.

### fn `def _check_file(self, filepath: str) -> int` `priv` (L624-638)
- @brief Perform the static analysis for a single file.
- @details Base implementation (Dummy): always passes. When `fail_only` is False, prints the header and `Result: OK`. When `fail_only` is True, produces no output (SRS-241). Subclasses override this method to invoke external tools.
- @param filepath Absolute path of the file to check.
- @return 0 on pass, non-zero on failure.

### fn `def _emit_line(self, line: str) -> None` `priv` (L639-648)
- @brief Emit one markdown output line.
- @details Emits `line` followed by a newline.
- @param line Line content to emit on stdout.
- @return {None} Function return value.

### class `class StaticCheckPylance(StaticCheckBase)` : StaticCheckBase (L653-780)
- @brief Pylance static-check class; runs pyright on each resolved file via `sys.executable -m pyright`.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `pyright` via `[sys.executable, '-m', 'pyright']` subprocess using the active runtime interpreter, without requiring external PATH availability, and parse its exit code. Header label: `Pylance`. Evidence block is emitted on failure by concatenating stdout and stderr from pyright.
- @see StaticCheckBase
- @satisfies SRS-242, SRS-339, SRS-341
- var `LABEL = "Pylance"` (L665)
  - @brief Pylance static-check class; runs pyright on each resolved file via `sys.executable -m pyright`.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `pyright`
via `[sys.executable, '-m', 'pyright']` subprocess using the active runtime interpreter,
without requiring external PATH availability, and parse its exit code.
Header label: `Pylance`.
Evidence block is emitted on failure by concatenating stdout and stderr from pyright.
  - @see StaticCheckBase
  - @satisfies SRS-242, SRS-339, SRS-341
- fn `def is_available(self) -> tuple[bool, str]` (L667-682)
  - @brief Probe pyright module availability in the active interpreter.
  - @details Availability matches the `[sys.executable, '-m', 'pyright']` dispatch exactly: the module must be importable by the running interpreter (SRS-427).
  - @return {tuple[bool, str]} `(False, reason)` when `importlib.util.find_spec('pyright')` is `None`; `(True, "")` otherwise.
  - @satisfies SRS-427
- fn `def __init__(` `priv` (L683-689)
- fn `def _check_file(self, filepath: str) -> int` `priv` (L704-754)
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
- fn `def _directory_command(` `priv` (L755-756)

### class `class StaticCheckRuff(StaticCheckBase)` : StaticCheckBase (L785-880)
- @brief Ruff static-check class; runs `ruff check` on each resolved file via `sys.executable -m ruff`.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `ruff check` via `[sys.executable, '-m', 'ruff', 'check']` subprocess using the package-installed ruff module, without requiring external PATH availability, and parse its exit code. Header label: `Ruff`. Evidence block is emitted on failure by concatenating stdout and stderr from ruff.
- @see StaticCheckBase
- @satisfies SRS-243, SRS-339
- var `LABEL = "Ruff"` (L797)
  - @brief Ruff static-check class; runs `ruff check` on each resolved file via `sys.executable -m ruff`.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke `ruff check`
via `[sys.executable, '-m', 'ruff', 'check']` subprocess using the package-installed ruff module,
without requiring external PATH availability, and parse its exit code.
Header label: `Ruff`.
Evidence block is emitted on failure by concatenating stdout and stderr from ruff.
  - @see StaticCheckBase
  - @satisfies SRS-243, SRS-339
- fn `def is_available(self) -> tuple[bool, str]` (L799-814)
  - @brief Probe ruff module availability in the active interpreter.
  - @details Availability matches the `[sys.executable, '-m', 'ruff']` dispatch exactly: the module must be importable by the running interpreter (SRS-427).
  - @return {tuple[bool, str]} `(False, reason)` when `importlib.util.find_spec('ruff')` is `None`; `(True, "")` otherwise.
  - @satisfies SRS-427
- fn `def _check_file(self, filepath: str) -> int` `priv` (L815-855)
  - @brief Run `ruff check` on `filepath` via `sys.executable -m ruff` and emit OK or FAIL with evidence.
  - @details Invokes `[sys.executable, '-m', 'ruff', 'check', <filepath>, <extra_args>...]` to use the package-installed ruff module without requiring external PATH availability. Captures combined stdout+stderr. When `fail_only` is False: prints header, then `Result: OK` or `Result: FAIL` with evidence. When `fail_only` is True: on pass produces no output; on fail emits header, FAIL, evidence (SRS-243).
  - @param filepath Absolute path of the file to analyse with ruff.
  - @return 0 when ruff exits 0, 1 otherwise.
  - @exception ReqError Not raised; subprocess errors are surfaced as FAIL evidence.
  - @satisfies SRS-243, SRS-339
- fn `def _directory_command(` `priv` (L856-857)

### class `class StaticCheckCommand(StaticCheckBase)` : StaticCheckBase (L885-996)
- @brief Command static-check class; runs an arbitrary external command on each resolved file.
- @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke the user-supplied `cmd` as a subprocess. Header label: `Command[<cmd>]`. `cmd` availability is resolved at execution time by the SRS-427 pre-flight via `shutil.which`; an unavailable `cmd` yields a per-file `Result: FAIL` outcome with English evidence and execution continues (SRS-428); the constructor does not raise.
- @see StaticCheckBase
- @satisfies SRS-427, SRS-428
- fn `def __init__(` `priv` (L898-904)
  - @brief Command static-check class; runs an arbitrary external command on each resolved file.
  - @details Derived from `StaticCheckBase`; overrides `_check_file` to invoke the user-supplied
`cmd` as a subprocess.
Header label: `Command[<cmd>]`.
`cmd` availability is resolved at execution time by the SRS-427 pre-flight via
`shutil.which`; an unavailable `cmd` yields a per-file `Result: FAIL` outcome with
English evidence and execution continues (SRS-428); the constructor does not raise.
  - @see StaticCheckBase
  - @satisfies SRS-427, SRS-428
- fn `def is_available(self) -> tuple[bool, str]` (L919-931)
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
- fn `def _check_file(self, filepath: str) -> int` `priv` (L932-970)
  - @brief Run the external command on `filepath` and emit OK or FAIL with evidence.
  - @details Invokes `<cmd> [extra_args...] <filepath>`. Captures combined stdout+stderr. When `fail_only` is False: prints header, then `Result: OK` or `Result: FAIL` with evidence. When `fail_only` is True: on pass produces no output; on fail emits header, FAIL, evidence (SRS-244).
  - @param filepath Absolute path of the file to analyse.
  - @return 0 when the command exits 0, 1 otherwise.
  - @satisfies SRS-244, SRS-253, SRS-256
- fn `def _dir_exclude_tokens(self, exclude_dir: str) -> List[str]` `priv` (L971-981)
  - @brief Build the cmd-native exclusion tokens for one excluded directory.
  - @details Flags: `cppcheck` -> `-i`, `eslint` -> `--ignore-pattern`, `ruff`/`pyright` -> `--exclude` (SRS-590).
  - @param exclude_dir {str} Absolute directory path excluded from the recursive scan.
  - @return {List[str]} Exclusion flag and path tokens; empty for unknown `cmd` binaries.
- fn `def _directory_command(` `priv` (L982-983)

### fn `def run_static_check(argv: Sequence[str]) -> int` (L1001-1066)
- @brief Parse `--test-static-check` sub-argv and dispatch to the appropriate checker class.
- @details Expected argument format: - `dummy [FILES...]` - `pylance [FILES...]` - `ruff [FILES...]` - `command <cmd> [FILES...]` No custom `--recursive` flag is parsed; recursive traversal is expressed via `**` glob patterns in `[FILES]` (e.g., `src/**/*.py`). For `command`, the first token after `command` is treated as `<cmd>`. All remaining tokens (after subcommand and optional cmd) are treated as FILES. Dispatches to: - `dummy` -> `StaticCheckBase` - `pylance` -> `StaticCheckPylance` - `ruff` -> `StaticCheckRuff` - `command` -> `StaticCheckCommand`
- @param argv Remaining argument tokens after `--test-static-check` (i.e. [subcommand, ...]).
- @return Process exit code from the selected checker's `run()` method.
- @throws ReqError If subcommand is missing, unknown, or `command` subcommand is missing `cmd`.

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`entry_scan_by_dir`|fn|pub|126-142|def entry_scan_by_dir(lang_config: Mapping[str, object]) ...|
|`_split_csv_like_tokens`|fn|priv|147-181|def _split_csv_like_tokens(spec_rhs: str) -> list[str]|
|`parse_enable_static_check`|fn|pub|182-258|def parse_enable_static_check(spec: str) -> tuple[str, dict]|
|`dispatch_static_check_for_file`|fn|pub|263-268|def dispatch_static_check_for_file(|
|`dispatch_static_check_for_directory`|fn|pub|323-329|def dispatch_static_check_for_directory(|
|`_resolve_files`|fn|priv|388-430|def _resolve_files(inputs: Sequence[str]) -> List[str]|
|`StaticCheckBase`|class|pub|435-634|class StaticCheckBase|
|`StaticCheckBase.__init__`|fn|priv|447-452|def __init__(|
|`StaticCheckBase.is_available`|fn|pub|472-481|def is_available(self) -> tuple[bool, str]|
|`StaticCheckBase.run`|fn|pub|482-524|def run(self) -> int|
|`StaticCheckBase.run_directory`|fn|pub|525-586|def run_directory(self, target: str, exclude_dirs: Sequen...|
|`StaticCheckBase._directory_command`|fn|priv|587-588|def _directory_command(|
|`StaticCheckBase._dir_exclude_tokens`|fn|priv|600-608|def _dir_exclude_tokens(self, exclude_dir: str) -> List[str]|
|`StaticCheckBase._header_line`|fn|priv|613-623|def _header_line(self, filepath: str) -> str|
|`_check_file`|fn|priv|624-638|def _check_file(self, filepath: str) -> int|
|`_emit_line`|fn|priv|639-648|def _emit_line(self, line: str) -> None|
|`StaticCheckPylance`|class|pub|653-780|class StaticCheckPylance(StaticCheckBase)|
|`StaticCheckPylance.LABEL`|var|pub|665||
|`StaticCheckPylance.is_available`|fn|pub|667-682|def is_available(self) -> tuple[bool, str]|
|`StaticCheckPylance.__init__`|fn|priv|683-689|def __init__(|
|`StaticCheckPylance._check_file`|fn|priv|704-754|def _check_file(self, filepath: str) -> int|
|`StaticCheckPylance._directory_command`|fn|priv|755-756|def _directory_command(|
|`StaticCheckRuff`|class|pub|785-880|class StaticCheckRuff(StaticCheckBase)|
|`StaticCheckRuff.LABEL`|var|pub|797||
|`StaticCheckRuff.is_available`|fn|pub|799-814|def is_available(self) -> tuple[bool, str]|
|`StaticCheckRuff._check_file`|fn|priv|815-855|def _check_file(self, filepath: str) -> int|
|`StaticCheckRuff._directory_command`|fn|priv|856-857|def _directory_command(|
|`StaticCheckCommand`|class|pub|885-996|class StaticCheckCommand(StaticCheckBase)|
|`StaticCheckCommand.__init__`|fn|priv|898-904|def __init__(|
|`StaticCheckCommand.is_available`|fn|pub|919-931|def is_available(self) -> tuple[bool, str]|
|`StaticCheckCommand._check_file`|fn|priv|932-970|def _check_file(self, filepath: str) -> int|
|`StaticCheckCommand._dir_exclude_tokens`|fn|priv|971-981|def _dir_exclude_tokens(self, exclude_dir: str) -> List[str]|
|`StaticCheckCommand._directory_command`|fn|priv|982-983|def _directory_command(|
|`run_static_check`|fn|pub|1001-1066|def run_static_check(argv: Sequence[str]) -> int|


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

