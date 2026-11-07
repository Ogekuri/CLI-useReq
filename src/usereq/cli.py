"""!
@file cli.py
@brief CLI entry point implementing the useReq initialization flow.
@details Handles argument parsing, configuration management, and execution of useReq commands.
@author GitHub Copilot
@version 0.0.70
"""

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

REPO_ROOT = Path(__file__).resolve().parents[2]
"""! @brief The absolute path to the repository root."""

RESOURCE_ROOT = Path(__file__).resolve().parent / "resources"
"""! @brief The absolute path to the resources directory."""

VERBOSE = False
"""! @brief Whether verbose output is enabled."""

DEBUG = False
"""! @brief Whether debug output is enabled."""

REQUIREMENTS_TEMPLATE_NAME = "Requirements_Template.md"
"""! @brief Name of the packaged requirements template file."""

PERSISTED_CONFIG_KEYS = (
    "docs-dir",
    "tests-dir",
    "src-dir",
    "providers",
    "static-check",
    "auto-install",
)
"""! @brief Canonical keys persisted in the user-global configuration file (SRS-288)."""

AUTO_INSTALL_CONFIG_KEY = "auto-install"
"""! @brief Configuration key storing the auto-install enabled flag (SRS-420)."""

DEFAULT_AUTO_INSTALL = True
"""! @brief Default auto-install state when the configuration stores no entry (SRS-420)."""

DEFAULT_DOCS_DIR = "usereq"
"""! @brief Default docs-dir value stored when the configuration has no docs-dir (SRS-359)."""

DEFAULT_TESTS_DIR = "tests"
"""! @brief Default tests-dir value stored when the configuration has no tests-dir (SRS-361)."""

DEFAULT_SRC_DIRS = ("src",)
"""! @brief Default src-dir list stored when the configuration has no src-dir (SRS-362)."""

DEFAULT_STATIC_CHECK: dict = {
    "C": [
        {
            "module": "Command",
            "cmd": "cppcheck",
            "params": [
                "--error-exitcode=1",
                "--enable=warning,style,performance,portability",
                "--std=c11",
            ],
        },
        {"module": "Command", "cmd": "clang-format", "params": ["--dry-run", "--Werror"]},
    ],
    "C++": [
        {
            "module": "Command",
            "cmd": "cppcheck",
            "params": [
                "--error-exitcode=1",
                "--enable=warning,style,performance,portability",
                "--std=c++20",
            ],
        },
        {"module": "Command", "cmd": "clang-format", "params": ["--dry-run", "--Werror"]},
    ],
    "JavaScript": [{"module": "Command", "cmd": "node", "params": ["--check"]}],
    "Python": [{"module": "Pylance"}, {"module": "Ruff"}],
    "TypeScript": [{"module": "Command", "cmd": "eslint"}],
}
"""! @brief Default static-check configuration applied when the configuration stores no
`"static-check"` entry; a present entry, including an empty object, suppresses these
defaults (SRS-424, SRS-425, SRS-426). The `pyright` and `ruff` checkers from the external
configuration trace map to the native `Pylance` and `Ruff` modules (SRS-338, SRS-339)."""

GUIDELINES_DIR_RELATIVE_TO_HOME = (
    Path(".pi")
    / "agent"
    / "npm"
    / "node_modules"
    / "pi-usereq"
    / "src"
    / "resources"
    / "guidelines"
)
"""! @brief Home-relative, non-configurable installation path of GUIDELINES_DIR (SRS-360)."""

VALID_PROVIDERS = frozenset(
    {"antigravity", "claude", "codex", "opencode", "pi"}
)
"""! @brief Valid provider names accepted by ``--enable`` SPECs (SRS-275, SRS-364)."""

VALID_ARTIFACTS = frozenset({"prompts", "agents", "skills"})
"""! @brief Valid artifact type tokens accepted in ``--enable`` SPECs (SRS-275, SRS-364)."""

VALID_PROVIDER_OPTIONS = frozenset({"prompts-use-agents"})
"""! @brief Valid provider-scoped option tokens accepted in ``PROVIDER_OPTIONS`` (SRS-365)."""

PROVIDER_OPTION_APPLICABILITY: dict[str, frozenset[str]] = {
    "prompts-use-agents": frozenset({"prompts"}),
}
"""! @brief Artifact applicability map for provider-scoped options during installation-table rendering."""

GLOBAL_CONFIG_DIRNAME = ".config"
"""! @brief Root configuration directory name located under the user HOME (SRS-387)."""

GLOBAL_CONFIG_APP_DIRNAME = "usereq"
"""! @brief Application subdirectory name under ``~/.config`` (SRS-387)."""

GLOBAL_CONFIG_FILENAME = "config.json"
"""! @brief Canonical user-global configuration JSON filename (SRS-387)."""


def home_dir() -> Path:
    """!
    @brief Resolve the user HOME directory used for user-level CLI configuration.
    @details Single indirection point over ``Path.home()`` so tests and embedders can
    redirect all user-level provider and configuration paths deterministically.
    @return {Path} Absolute user HOME directory path.
    @satisfies SRS-381
    """
    return Path.home()


def get_global_config_path() -> Path:
    """!
    @brief Resolve the single user-global configuration file path.
    @details Builds ``~/.config/usereq/config.json`` from the effective home directory
    returned by :func:`home_dir`.
    @return {Path} Absolute path of the user-global configuration file.
    @satisfies SRS-387
    """
    return (
        home_dir()
        / GLOBAL_CONFIG_DIRNAME
        / GLOBAL_CONFIG_APP_DIRNAME
        / GLOBAL_CONFIG_FILENAME
    )


def guidelines_dir() -> Path:
    """!
    @brief Resolve the fixed installation-owned guidelines directory.
    @details Composes the effective user HOME returned by :func:`home_dir` with the
    non-configurable :data:`GUIDELINES_DIR_RELATIVE_TO_HOME` suffix.
    @return {Path} Absolute path of the installed guidelines directory.
    @satisfies SRS-360
    """
    return home_dir() / GUIDELINES_DIR_RELATIVE_TO_HOME


def format_home_relative_path(path: Path) -> str:
    """!
    @brief Render an absolute path in ``~/`` home-relative form.
    @details Returns ``~`` for the HOME directory, ``~/<rel>`` with POSIX separators for any
    path under HOME, and the absolute string for paths outside HOME.
    @param path {Path} Absolute path to render.
    @return {str} Home-relative rendering when the path is under HOME, otherwise absolute.
    @satisfies SRS-402, SRS-403
    """
    resolved_home = home_dir().resolve(strict=False)
    resolved_path = Path(path).resolve(strict=False)
    if resolved_path == resolved_home:
        return "~"
    try:
        relative = resolved_path.relative_to(resolved_home).as_posix()
    except ValueError:
        return str(resolved_path)
    return f"~/{relative}"


def provider_artifact_root(provider: str, artifact: str) -> Path:
    """!
    @brief Resolve the user-level installation root for one provider artifact.
    @details Maps ``provider`` and ``artifact`` selectors to user-level CLI configuration
    directories under the user HOME (claude -> ``~/.claude``, codex -> ``~/.codex``,
    antigravity -> ``~/.antigravity``, opencode -> ``~/.config/opencode``,
    pi -> ``~/.pi/agent``). Paths are computed lazily from :func:`home_dir` so HOME
    redirection stays consistent across a single process run.
    @param provider {str} Provider selector from ``{antigravity, claude, codex, opencode, pi}``.
    @param artifact {str} Artifact selector from ``{prompts, agents, skills}``.
    @return {Path} Absolute user-level target directory for the artifact.
    @throws {ReqError} Raised when the provider/artifact pair has no user-level target.
    @satisfies SRS-381, SRS-382, SRS-383, SRS-384, SRS-385, SRS-386
    """
    home = home_dir()
    roots: dict[str, dict[str, Path]] = {
        "antigravity": {
            "prompts": home / ".antigravity" / "commands" / "req",
            "skills": home / ".antigravity" / "skills",
        },
        "claude": {
            "prompts": home / ".claude" / "commands" / "req",
            "agents": home / ".claude" / "agents",
            "skills": home / ".claude" / "skills",
        },
        "codex": {
            "prompts": home / ".codex" / "prompts",
            "skills": home / ".codex" / "skills",
        },
        "opencode": {
            "prompts": home / ".config" / "opencode" / "command",
            "agents": home / ".config" / "opencode" / "agent",
            "skills": home / ".config" / "opencode" / "skill",
        },
        "pi": {
            "prompts": home / ".pi" / "agent" / "prompts",
            "skills": home / ".pi" / "agent" / "skills",
        },
    }
    provider_roots = roots.get(provider)
    if not provider_roots:
        raise ReqError(
            f"Error: provider '{provider}' does not define a user-level artifact root",
            1,
        )
    root = provider_roots.get(artifact)
    if root is None:
        raise ReqError(
            f"Error: artifact '{artifact}' is not supported for provider '{provider}'",
            1,
        )
    return root

INVALID_WT_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]')
"""! @brief Regex matching characters invalid in both Linux and Windows directory names."""


def _parse_provider_artifact_item(spec: str, artifact_item: str) -> tuple[str, list[str]]:
    """!
    @brief Parse one artifact item from an ``--enable`` SPEC.
    @details Splits `ARTIFACT_ITEM` on `+`, validates the artifact token and artifact-local option tokens, preserves first-seen option order, rejects provider-scoped option placement inside the artifact item, and raises deterministic `ReqError` payloads for all invalid tokens. Complexity: O(N) in artifact-item token count. No side effects.
    @param spec {str} Full raw ``--enable`` SPEC used for diagnostics.
    @param artifact_item {str} One comma-delimited `ARTIFACT_ITEM` fragment from `SPEC`.
    @return {tuple[str, list[str]]} Tuple `(artifact_name, ordered_artifact_options)`.
    @throws {ReqError} Raised when the artifact token is missing, unknown, or contains invalid option placement.
    @satisfies SRS-275, SRS-278, SRS-364, SRS-365
    """
    artifact = artifact_item.strip().lower()
    if not artifact:
        raise ReqError(
            f"Error: invalid artifact item '{artifact_item}' in --provider spec '{spec}'",
            1,
        )
    if artifact not in VALID_ARTIFACTS:
        raise ReqError(
            f"Error: unknown artifact '{artifact}' in --provider spec '{spec}'; "
            f"valid artifacts: {', '.join(sorted(VALID_ARTIFACTS))}",
            1,
        )
    return artifact, []


def _parse_provider_options(spec: str, raw_options: str) -> list[str]:
    """!
    @brief Parse provider-scoped options from an ``--enable`` SPEC.
    @details Splits `PROVIDER_OPTIONS` on commas, preserves first-seen option order, and accepts only the provider-scoped `prompts-use-agents` token (SRS-365). Complexity: O(N) in provider-option token count. No side effects.
    @param spec {str} Full raw ``--enable`` SPEC used for diagnostics.
    @param raw_options {str} Raw provider-options field from `SPEC` without leading separators.
    @return {list[str]} Ordered provider-scoped option tokens.
    @throws {ReqError} Raised when an option token is unknown or positioned in the wrong field.
    @satisfies SRS-275, SRS-278, SRS-365
    """
    ordered_options: list[str] = []
    for option in [token.strip().lower() for token in raw_options.split(",") if token.strip()]:
        if option not in VALID_PROVIDER_OPTIONS:
            raise ReqError(
                f"Error: unknown option '{option}' in --provider spec '{spec}'; "
                f"valid options: {', '.join(sorted(VALID_PROVIDER_OPTIONS))}",
                1,
            )
        if option not in ordered_options:
            ordered_options.append(option)
    return ordered_options


def parse_provider_spec(spec: str) -> tuple[str, list[tuple[str, list[str]]], list[str]]:
    """!
    @brief Parse a single ``--enable`` SPEC into ordered provider, artifact-item, and provider-option components.
    @details Splits `SPEC` on `:`, validates provider token membership, parses each comma-delimited bare `ARTIFACT` item (SRS-364), parses optional provider-scoped options, preserves first-seen artifact order and option order, and rejects unknown tokens. Complexity: O(A + O) where A is artifact-item token count and O is provider-option token count. No side effects.
    @param spec {str} Raw ``--enable`` SPEC in format `PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]`.
    @return {tuple[str, list[tuple[str, list[str]]], list[str]]} Tuple `(provider_name, ordered_artifact_items, ordered_provider_options)`.
    @throws {ReqError} Raised when provider, artifact, option, or option placement validation fails.
    @satisfies SRS-275, SRS-276, SRS-278, SRS-364, SRS-365
    @see resolve_provider_configs
    """
    parts = spec.split(":")
    if len(parts) < 2 or len(parts) > 3:
        raise ReqError(
            f"Error: invalid --provider spec '{spec}': expected PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]",
            1,
        )
    provider = parts[0].strip().lower()
    if provider not in VALID_PROVIDERS:
        raise ReqError(
            f"Error: unknown provider '{provider}' in --provider spec '{spec}'; "
            f"valid providers: {', '.join(sorted(VALID_PROVIDERS))}",
            1,
        )
    raw_artifact_items = [token.strip() for token in parts[1].split(",") if token.strip()]
    if not raw_artifact_items:
        raise ReqError(
            f"Error: --provider spec '{spec}' must list at least one artifact item",
            1,
        )
    ordered_artifact_items: list[tuple[str, list[str]]] = []
    for raw_artifact_item in raw_artifact_items:
        ordered_artifact_items.append(
            _parse_provider_artifact_item(spec, raw_artifact_item)
        )
    provider_options: list[str] = []
    if len(parts) == 3:
        provider_options = _parse_provider_options(spec, parts[2])
    return provider, ordered_artifact_items, provider_options


def resolve_provider_configs(
    provider_specs: list[str],
) -> dict[str, dict[str, Any]]:
    """!
    @brief Resolve per-provider configurations from ``--enable`` SPEC strings only.
    @details Initializes every provider as disabled, then merges parsed `ARTIFACT_ITEM` and `PROVIDER_OPTIONS` data across all raw specs for that provider. Artifact enablement is tracked in top-level `prompts`/`agents`/`skills` booleans. Provider-scoped `prompts-use-agents` remains a top-level boolean. Complexity: O(P * (A + O)) where P is spec count. No external side effects.
    @param provider_specs {list[str]} Raw ``--enable`` SPEC strings.
    @return {dict[str, dict[str, Any]]} Mapping provider -> configuration dict with keys `enabled`, `prompts`, `agents`, `skills`, and `prompts-use-agents`.
    @satisfies SRS-275, SRS-276, SRS-364, SRS-365
    @see parse_provider_spec
    """
    configs: dict[str, dict[str, Any]] = {}
    for prov in sorted(VALID_PROVIDERS):
        configs[prov] = {
            "enabled": False,
            "prompts": False,
            "agents": False,
            "skills": False,
            "prompts-use-agents": False,
        }

    for spec_str in provider_specs:
        provider, artifact_items, provider_options = parse_provider_spec(spec_str)
        cfg = configs[provider]
        cfg["enabled"] = True
        for artifact_name, _artifact_options in artifact_items:
            cfg[artifact_name] = True
        for option_name in provider_options:
            cfg[option_name] = True

    return configs


ANSI_BRIGHT_RED = "\033[91m"
"""! @brief ANSI escape prefix for bright red terminal output."""

ANSI_BRIGHT_GREEN = "\033[92m"
"""! @brief ANSI escape prefix for bright green terminal output."""

ANSI_RESET = "\033[0m"
"""! @brief ANSI escape sequence that resets terminal style."""

RELEASE_CHECK_TIMEOUT_SECONDS = 2.0
"""! @brief Hardcoded default timeout for startup release-check HTTP calls."""

RELEASE_CHECK_IDLE_DELAY_SECONDS = 3600
"""! @brief Hardcoded startup release-check idle-delay in seconds."""

RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS = 86400
"""! @brief Hardcoded startup release-check idle-delay in seconds for API rate limiting."""

TOOL_PROGRAM_NAME = "cli-usereq"
"""! @brief Hardcoded uv tool requirement name matching the PyPI distribution name of this package (SRS-435).
@details Used as the target of `uv tool install`/`uv tool uninstall` commands; it matches the
`[project].name` distribution name registered in the PyPI trusted publisher for repository
`Ogekuri/CLI-useReq` (SRS-343, SRS-344, SRS-433, SRS-435)."""

RELEASE_CHECK_PROGRAM_NAME = "usereq"
"""! @brief Program identifier used in release-check idle-state cache directory.
@details Fixes the idle-state cache path to `~/.cache/usereq/check_version_idle-time.json`
independently of the PyPI distribution name `cli-usereq` (SRS-345, SRS-346)."""

GITHUB_REPOSITORY_OWNER = "Ogekuri"
"""! @brief Hardcoded GitHub owner used by upgrade and release-check endpoints."""

GITHUB_REPOSITORY_NAME = "CLI-useReq"
"""! @brief Hardcoded GitHub repository used by upgrade and release-check endpoints."""

RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME = ".cache"
"""! @brief Root cache directory name located under `$HOME`."""

RELEASE_CHECK_IDLE_FILENAME = "check_version_idle-time.json"
"""! @brief Canonical release-check idle-state JSON filename."""

GITHUB_RELEASES_LATEST_URL = (
    f"https://api.github.com/repos/{GITHUB_REPOSITORY_OWNER}/"
    f"{GITHUB_REPOSITORY_NAME}/releases/latest"
)
"""! @brief Hardcoded GitHub API endpoint queried by `--ver`/`--version` and `--upgrade --develop` (SRS-442, SRS-451).
@details Intermediate and test releases are published on GitHub; this endpoint resolves the
latest tagged release independently of the branch holding the tag. The default `--upgrade`
path never queries it and installs from the PyPI index (SRS-343, SRS-440)."""

GITHUB_UPGRADE_SOURCE = (
    f"git+https://github.com/{GITHUB_REPOSITORY_OWNER}/{GITHUB_REPOSITORY_NAME}.git"
)
"""! @brief Hardcoded git source base used only by `--upgrade --develop` (alias `--dev`) installs (SRS-440, SRS-445).
@details The uv `--from` reference appends `@<TAG>` with the raw SRS-451 release tag so the
install pins the latest tagged release regardless of the branch holding the tag (SRS-452)."""

PYPI_PROJECT_JSON_URL = "https://pypi.org/pypi/cli-usereq/json"
"""! @brief Hardcoded PyPI JSON API endpoint for latest-version resolution (SRS-430).
@details The startup release-check and `--ver`/`--version` read `info.version` from this
endpoint; PyPI is the sole source for version verification and default self-upgrade
(SRS-343, SRS-441, SRS-442)."""

UNKNOWN_VERSION_LABEL = "unknown"
"""! @brief Label printed by `--ver`/`--version` when a remote latest version cannot be fetched (SRS-442)."""

FORCE_ONLINE_RELEASE_CHECK = False
"""! @brief Startup-scoped override that bypasses release-check idle-state gating when enabled."""


class ReqError(Exception):
    """! @brief Dedicated exception for expected CLI errors.
    @details This exception is used to bubble up known error conditions that should be reported to the user without a stack trace.
    """

    def __init__(self, message: str, code: int = 1) -> None:
        """!
        @brief Initialize an expected CLI failure payload.
                @param message Human-readable error message.
                @param code Process exit code bound to the failure category.
        @details Implements the __init__ function behavior with deterministic control flow.
        @return {None} Function return value.
        """
        super().__init__(message)
        self.message = message
        self.code = code


def log(msg: str) -> None:
    """!
    @brief Prints an informational message.
        @param msg The message string to print.
    @details Implements the log function behavior with deterministic control flow.
    @return {None} Function return value.
    """
    print(msg)


def dlog(msg: str) -> None:
    """!
    @brief Prints a debug message if debugging is active.
        @param msg The debug message string to print.
    @details Implements the dlog function behavior with deterministic control flow.
    @return {None} Function return value.
    """
    if DEBUG:
        print("DEBUG:", msg)


def vlog(msg: str) -> None:
    """!
    @brief Prints a verbose message if verbose mode is active.
        @param msg The verbose message string to print.
    @details Implements the vlog function behavior with deterministic control flow.
    @return {None} Function return value.
    """
    if VERBOSE:
        print(msg)


def build_parser() -> argparse.ArgumentParser:
    """! @brief Builds the CLI argument parser.
    @return Configured ArgumentParser instance.
    @details Defines all supported CLI arguments, flags, and help texts. Provider enablement,
    artifact selection, and per-provider options are configured exclusively via the repeatable
    ``--enable SPEC`` argument (SRS-275, SRS-034).
    """
    usage = (
        "req [-h] [--upgrade] [--develop] [--dev] [--uninstall] [--prj-base PRJ_BASE] [--git-base GIT_BASE] "
        "[--set-docs-dir DOCS_DIR] [--set-src-dir SRC_DIR] [--set-tests-dir TESTS_DIR] [--verbose] [--debug] "
        "[--enable SPEC] [--disable PROVIDER] [--enable-auto-install] [--disable-auto-install] "
        "[--enable-line-numbers] "
        "[--enable-static-check SPEC] [--disable-static-check SPEC] "
        "[--test-static-check {dummy,pylance,ruff,command} [FILES...]] "
        "[--git-check] [--docs-check] [--git-wt-name] [--git-wt-create WT_NAME] [--git-wt-delete WT_NAME] "
        "{files-tokens,files-references,files-compress,files-find,tokens,references,compress,find,files-static-check,static-check,install,uninstall,show} ..."
    )
    parser = argparse.ArgumentParser(
        description="Initialize a project with useReq resources.",
        prog="req",
        usage=usage,
    )
    parser.add_argument(
        "--prj-base",
        type=Path,
        default=None,
        dest="prj_base",
        help=(
            "Absolute project base directory containing the configured docs-dir, "
            "src-dir, and tests-dir. Required for --docs-check, --set-*-dir, and "
            "the project-scan analysis subcommands (tokens, references, compress, "
            "find, static-check, files-static-check); optional for install."
        ),
    )
    parser.add_argument(
        "--git-base",
        type=Path,
        default=None,
        dest="git_base",
        help=(
            "Absolute git repository base directory used as working directory "
            "for every git operation. Required by --git-check, --git-wt-name, "
            "--git-wt-create, and --git-wt-delete."
        ),
    )
    parser.add_argument(
        "--set-docs-dir",
        metavar="DOCS_DIR",
        default=None,
        dest="set_docs_dir",
        help=(
            "Configure DOCS_DIR as the project-relative documentation "
            "directory. Requires --prj-base."
        ),
    )
    parser.add_argument(
        "--set-src-dir",
        action="append",
        metavar="SRC_DIR",
        default=None,
        dest="set_src_dir",
        help=(
            "Configure SRC_DIR as a project-relative source directory "
            "(repeatable). Requires --prj-base."
        ),
    )
    parser.add_argument(
        "--set-tests-dir",
        metavar="TESTS_DIR",
        default=None,
        dest="set_tests_dir",
        help=(
            "Configure TESTS_DIR as the project-relative test directory. "
            "Requires --prj-base."
        ),
    )
    parser.add_argument(
        "--upgrade", action="store_true", help="Upgrade the tool with uv from PyPI."
    )
    parser.add_argument(
        "--develop",
        "--dev",
        action="store_true",
        help=(
            "With --upgrade: install the latest tagged GitHub release "
            "(git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>, resolved via the "
            "GitHub releases API regardless of branch) instead of PyPI. "
            "--dev is an equivalent alias of --develop."
        ),
    )
    parser.add_argument(
        "--uninstall", action="store_true", help="Uninstall the tool with uv."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show verbose progress messages."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show debug logs for diagnostics."
    )
    parser.add_argument(
        "--enable",
        action="append",
        metavar="SPEC",
        dest="enable_provider",
        help=(
            "Configure provider enablement without installing (repeatable); "
            "run the 'install' subcommand to install. "
            "Format: PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]. "
            "PROVIDER: antigravity|claude|codex|opencode|pi. "
            "ARTIFACT_ITEM: one of prompts|agents|skills. "
            "PROVIDER_OPTIONS: comma-separated from {prompts-use-agents}."
        ),
    )
    parser.add_argument(
        "--disable",
        action="append",
        metavar="PROVIDER",
        dest="disable_provider",
        help=(
            "Disable a provider (repeatable); one of "
            "antigravity|claude|codex|opencode|pi."
        ),
    )
    parser.add_argument(
        "--enable-auto-install",
        action="store_true",
        dest="enable_auto_install",
        help=(
            "Reinstall the configured providers automatically after a "
            "successful --upgrade."
        ),
    )
    parser.add_argument(
        "--disable-auto-install",
        action="store_true",
        dest="disable_auto_install",
        help="Skip automatic provider reinstallation after a successful --upgrade.",
    )
    parser.add_argument(
        "--enable-line-numbers",
        action="store_true",
        default=False,
        help="Enable line number prefixes (<n>:) in output for files-compress, compress, files-find, and find subcommands (disabled by default).",
    )
    parser.add_argument(
        "--test-static-check",
        nargs=argparse.REMAINDER,
        metavar="ARG",
        dest="test_static_check",
        help=(
            "Run static analysis: --test-static-check <subcommand> [FILES...]. "
            "Subcommands: dummy, pylance, ruff, command <cmd>. "
            "[FILES] may be files, directories, or glob patterns including ** (standalone, no --prj-base required)."
        ),
    )
    parser.add_argument(
        "--enable-static-check",
        action="append",
        metavar="SPEC",
        dest="enable_static_check",
        default=None,
        help=(
            "Configure a static-check tool for a language without requiring "
            "--prj-base. "
            "SPEC format: LANG=MODULE[,CMD[,PARAM...]]. "
            "MODULE: Dummy, Pylance, Ruff, Command (case-insensitive). "
            "LANG: Python, C, C++, C#, Rust, JavaScript, TypeScript, Java, Go, Ruby, "
            "PHP, Swift, Kotlin, Scala, Lua, Shell, Perl, Haskell, Zig, Elixir (case-insensitive). "
            "For Command, CMD is the binary and subsequent tokens are params; "
            "tokens containing commas must be wrapped in double quotes. "
            "Repeatable: multiple flags per language append multiple entries. "
            "Example: --enable-static-check Python=Pylance "
            "--enable-static-check C=Command,/usr/bin/cppcheck,--check-library"
        ),
    )
    parser.add_argument(
        "--disable-static-check",
        action="append",
        metavar="SPEC",
        dest="disable_static_check",
        help=(
            "Remove configured static-check entries. "
            "SPEC format: LANG=MODULE[,CMD[,PARAM...]] removes the exact matching "
            "entry; bare LANG removes the whole language key."
        ),
    )
    parser.add_argument(
        "--git-check",
        action="store_true",
        default=False,
        dest="git_check",
        help=(
            "Check git repository status: clean work tree and valid HEAD "
            "(requires --git-base)."
        ),
    )
    parser.add_argument(
        "--docs-check",
        action="store_true",
        default=False,
        dest="docs_check",
        help=(
            "Check existence of REQUIREMENTS.md, WORKFLOW.md, and REFERENCES.md in docs-dir "
            "(requires --prj-base)."
        ),
    )
    parser.add_argument(
        "--git-wt-name",
        action="store_true",
        default=False,
        dest="git_wt_name",
        help=(
            "Print a standardized worktree name: useReq-<PROJECT>-<BRANCH>-<TIMESTAMP> "
            "(requires --git-base)."
        ),
    )
    parser.add_argument(
        "--git-wt-create",
        metavar="WT_NAME",
        default=None,
        dest="git_wt_create",
        help=(
            "Create a git worktree and branch with the given name, copying .venv when present "
            "(requires --git-base)."
        ),
    )
    parser.add_argument(
        "--git-wt-delete",
        metavar="WT_NAME",
        default=None,
        dest="git_wt_delete",
        help=(
            "Remove a git worktree and branch by name "
            "(requires --git-base)."
        ),
    )
    # Bare analysis subcommands (SRS-408). Legacy --prefixed forms are not parsed
    # (SRS-409); --prj-base is mandatory exactly per SRS-396/SRS-410.
    # SUPPRESS defaults prevent subparser defaults from clobbering values parsed
    # by the main parser before the subcommand token.
    base_options = argparse.ArgumentParser(add_help=False)
    base_options.add_argument(
        "--prj-base",
        type=Path,
        default=argparse.SUPPRESS,
        dest="prj_base",
        help="Absolute project base directory; required by project-scan analysis subcommands.",
    )
    line_number_options = argparse.ArgumentParser(add_help=False)
    line_number_options.add_argument(
        "--enable-line-numbers",
        action="store_true",
        default=argparse.SUPPRESS,
        dest="enable_line_numbers",
        help="Enable line number prefixes (<n>:) in output (disabled by default).",
    )
    install_options = argparse.ArgumentParser(add_help=False)
    install_options.add_argument(
        "--prj-base",
        type=Path,
        default=argparse.SUPPRESS,
        dest="prj_base",
        help=(
            "Absolute project base directory; optional: when provided, installation "
            "also creates the project directories and persists the directory "
            "configuration."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="subcommands",
        description=(
            "Project-scan analysis subcommands (tokens, references, compress, "
            "find, static-check, files-static-check) require --prj-base. "
            "Legacy --prefixed forms are not accepted."
        ),
        metavar=(
            "{files-tokens,files-references,files-compress,files-find,tokens,"
            "references,compress,find,files-static-check,static-check,"
            "install,uninstall,show}"
        ),
    )

    sub = subparsers.add_parser(
        "files-tokens",
        usage="req files-tokens FILE [FILE ...]",
        help="Count tokens and chars for the given files.",
    )
    sub.add_argument("files_tokens", nargs="+", metavar="FILE")

    sub = subparsers.add_parser(
        "files-references",
        usage="req files-references FILE [FILE ...]",
        help="Generate LLM reference markdown for the given files.",
    )
    sub.add_argument("files_references", nargs="+", metavar="FILE")

    sub = subparsers.add_parser(
        "files-compress",
        parents=[line_number_options],
        usage="req files-compress [--enable-line-numbers] FILE [FILE ...]",
        help="Generate compressed output for the given files.",
    )
    sub.add_argument("files_compress", nargs="+", metavar="FILE")

    sub = subparsers.add_parser(
        "files-find",
        parents=[line_number_options],
        usage="req files-find [--enable-line-numbers] TAG PATTERN FILE [FILE ...]",
        help=(
            "Find and extract specific constructs: files-find TAG PATTERN FILE ... "
            "TAG accepts pipe-separated tags; the per-language tag catalog is "
            "printed on invalid TAG or non-matching filter errors."
        ),
    )
    sub.add_argument("files_find", nargs="+", metavar="ARG")

    sub = subparsers.add_parser(
        "tokens",
        parents=[base_options],
        usage="req tokens --prj-base PRJ_BASE",
        help=(
            "Count tokens/chars for REQUIREMENTS.md, WORKFLOW.md, and REFERENCES.md "
            "in the configured docs-dir."
        ),
    )

    sub = subparsers.add_parser(
        "references",
        parents=[base_options],
        usage="req references --prj-base PRJ_BASE",
        help=(
            "Generate LLM reference markdown for all source files in the configured "
            "src-dir directories."
        ),
    )

    sub = subparsers.add_parser(
        "compress",
        parents=[base_options, line_number_options],
        usage="req compress --prj-base PRJ_BASE [--enable-line-numbers]",
        help=(
            "Generate compressed output for all source files in the configured "
            "src-dir directories."
        ),
    )

    sub = subparsers.add_parser(
        "find",
        parents=[base_options, line_number_options],
        usage=(
            "req find --prj-base PRJ_BASE "
            "[--enable-line-numbers] TAG PATTERN"
        ),
        help=(
            "Find and extract specific constructs from the configured src-dir: "
            "find TAG PATTERN. TAG accepts pipe-separated tags; the per-language "
            "tag catalog is printed on invalid TAG or non-matching filter errors."
        ),
    )
    sub.add_argument("find", nargs=2, metavar=("TAG", "PATTERN"))

    sub = subparsers.add_parser(
        "files-static-check",
        parents=[base_options],
        usage="req files-static-check --prj-base PRJ_BASE FILE [FILE ...]",
        help=(
            "Run static analysis on explicit files using the configured tools. "
            "Detects language from file extension; skips files with no configured "
            "tool. Requires --prj-base as the checker dispatch context."
        ),
    )
    sub.add_argument("files_static_check", nargs="+", metavar="FILE")

    sub = subparsers.add_parser(
        "static-check",
        parents=[base_options],
        usage="req static-check --prj-base PRJ_BASE",
        help=(
            "Run static analysis on source and test files selected from the "
            "configured src-dir and tests-dir directories."
        ),
    )

    sub = subparsers.add_parser(
        "install",
        parents=[install_options],
        usage="req install [--prj-base PRJ_BASE]",
        help=(
            "Install or update the configured providers into user-level "
            "directories and print the installation report."
        ),
    )

    sub = subparsers.add_parser(
        "uninstall",
        usage="req uninstall",
        help=(
            "Remove req-* artifacts of the configured providers."
        ),
    )

    sub = subparsers.add_parser(
        "show",
        usage="req show",
        help=(
            "Print the active configuration, enabled providers with component "
            "installation status, and enabled static-check entries as tables."
        ),
    )
    return parser


def parse_args(argv: Optional[list[str]] = None) -> Namespace:
    """!
    @brief Parses command-line arguments into a namespace.
        @param argv List of arguments (defaults to sys.argv).
        @return Namespace containing parsed arguments.
    @details Implements the parse_args function behavior with deterministic control flow.
    """
    return build_parser().parse_args(argv)


def load_package_version() -> str:
    """!
    @brief Reads the package version from __init__.py.
        @return Version string extracted from the package.
        @throws ReqError If version cannot be determined.
    @details Implements the load_package_version function behavior with deterministic control flow.
    """
    init_path = Path(__file__).resolve().parent / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"\s*$', text, re.M)
    if not match:
        raise ReqError("Error: unable to determine package version", 6)
    return match.group(1)


def maybe_print_version(argv: list[str], pypi_latest: Optional[str] = None) -> bool:
    """!
    @brief Handles --ver/--version by printing installed, PyPI latest, and GitHub latest versions.
        @param argv Command line arguments to check.
        @param pypi_latest {Optional[str]} PyPI latest version already fetched by the startup
        release-check; when None, a direct PyPI JSON API fetch is attempted (SRS-441, SRS-442).
    @details When `--ver`/`--version` is present, prints the installed package version as the
    first stdout line, then queries (or reuses) the PyPI JSON API `info.version` and the GitHub
    latest-release `tag_name`, printing `PyPI latest: <version>` and `GitHub latest: <version>`
    lines; fetch failures degrade to the `unknown` label without raising (SRS-441, SRS-442).
    @return {bool} True if version output was printed, False otherwise.
    @satisfies SRS-441, SRS-442
    """
    if "--ver" in argv or "--version" in argv:
        print(load_package_version())
        if pypi_latest is None:
            try:
                pypi_latest = fetch_pypi_latest_version(RELEASE_CHECK_TIMEOUT_SECONDS)
            except (
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
                json.JSONDecodeError,
                ValueError,
            ):
                pypi_latest = None
        try:
            github_latest: Optional[str] = fetch_github_latest_version(
                RELEASE_CHECK_TIMEOUT_SECONDS
            )
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
        ):
            github_latest = None
        print(f"PyPI latest: {pypi_latest if pypi_latest else UNKNOWN_VERSION_LABEL}")
        print(
            f"GitHub latest: {github_latest if github_latest else UNKNOWN_VERSION_LABEL}"
        )
        return True
    return False


def _resolve_github_upgrade_tag() -> str:
    """!
    @brief Resolve the raw latest GitHub release tag for `--upgrade --develop` installations.
    @details Queries `GITHUB_RELEASES_LATEST_URL` through
    `fetch_github_latest_version(raw_tag=True)` and returns the raw `tag_name` value with the
    optional `v` prefix preserved so the uv `--from` reference targets an existing git tag
    regardless of the branch holding it (SRS-451). Maps fetch exceptions and empty payloads to
    one English `ReqError` so no uv process is spawned (SRS-453). Complexity: O(1).
    Side effects: one HTTP request.
    @return {str} Raw latest release tag, e.g. `v0.0.76`.
    @throws {ReqError} Raised with exit code 1 when the GitHub query fails or returns no tag (SRS-453).
    @satisfies SRS-451, SRS-453
    """
    failure_message = (
        "Error: unable to resolve the latest GitHub release tag for "
        f"--upgrade --develop from {GITHUB_RELEASES_LATEST_URL}"
    )
    try:
        resolved_tag = fetch_github_latest_version(raw_tag=True)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        ValueError,
    ) as exc:
        raise ReqError(f"{failure_message} ({exc})", 1) from exc
    if not resolved_tag:
        raise ReqError(failure_message, 1)
    return resolved_tag


def run_upgrade(use_github: bool = False) -> None:
    """!
    @brief Executes the upgrade using uv from the PyPI index or the latest GitHub release tag.
        @param use_github {bool} When True, install the latest tagged GitHub release instead of
        the PyPI index (`--upgrade --develop` or equivalent alias `--dev`, SRS-440, SRS-445).
    @details Builds `uv tool install cli-usereq --force` against the PyPI index by default
    (SRS-343). When `use_github` is True, resolves the latest GitHub release tag through
    `_resolve_github_upgrade_tag()` (SRS-451) and appends
    `--from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` regardless of the branch
    holding that tag (SRS-440, SRS-452). Executes the command only on Linux; on non-Linux
    platforms prints the manual command and skips uv execution.
    @throws {ReqError} When the SRS-451 GitHub tag resolution fails (exit code 1, SRS-453) or
    when the uv process fails.
    @return {None} Function return value.
    @note Tag resolution precedes the platform gate so the non-Linux manual command embeds the
    resolved tag (SRS-452).
    @note The `--develop`/`--dev` argv alias mapping to `use_github=True` is resolved by
    `main(...)` before calling this function.
    @satisfies SRS-343, SRS-440, SRS-445, SRS-451, SRS-452, SRS-453
    """
    command = [
        "uv",
        "tool",
        "install",
        TOOL_PROGRAM_NAME,
        "--force",
    ]
    if use_github:
        resolved_tag = _resolve_github_upgrade_tag()
        command += ["--from", f"{GITHUB_UPGRADE_SOURCE}@{resolved_tag}"]
    detected_system = platform.system() or "Unknown"
    if detected_system != "Linux":
        print(
            "Warning: --upgrade automatic execution is supported only on Linux "
            f"(detected: {detected_system}). Run manually: {' '.join(command)}"
        )
        return
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        raise ReqError("Error: 'uv' command not found in PATH", 12) from exc
    if result.returncode != 0:
        raise ReqError(
            f"Error: auto-upgrade failed (code {result.returncode})",
            result.returncode,
        )


def run_uninstall() -> None:
    """!
    @brief Executes the uninstallation using uv.
        @throws ReqError If uninstall fails.
    @details Implements the run_uninstall function behavior with deterministic control flow.
    @return {None} Function return value.
    @satisfies SRS-344, SRS-346
    """
    command = [
        "uv",
        "tool",
        "uninstall",
        TOOL_PROGRAM_NAME,
    ]
    detected_system = platform.system() or "Unknown"
    if detected_system != "Linux":
        print(
            "Warning: --uninstall automatic execution is supported only on Linux "
            f"(detected: {detected_system}). Run manually: {' '.join(command)}"
        )
        return
    try:
        result = subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        raise ReqError("Error: 'uv' command not found in PATH", 12) from exc
    if result.returncode != 0:
        raise ReqError(
            f"Error: uninstall failed (code {result.returncode})",
            result.returncode,
        )
    cleanup_release_check_idle_state_cache()


def normalize_release_tag(tag: str) -> str:
    """!
    @brief Normalizes the release tag by removing a 'v' prefix if present.
        @param tag The raw tag string.
        @return The normalized version string.
    @details Implements the normalize_release_tag function behavior with deterministic control flow.
    """
    value = (tag or "").strip()
    if value.lower().startswith("v") and len(value) > 1:
        value = value[1:]
    return value.strip()


def parse_version_tuple(version: str) -> tuple[int, ...] | None:
    """! @brief Converts a version into a numeric tuple for comparison.
    @param version The version string to parse.
    @return Tuple of integers or None if parsing fails.
    @details Accepts versions in 'X.Y.Z' format (ignoring any non-numeric suffixes).
    """

    cleaned = (version or "").strip()
    if not cleaned:
        return None

    parts = cleaned.split(".")
    numbers: list[int] = []
    for part in parts:
        match = re.match(r"^(\d+)", part)
        if not match:
            break
        try:
            numbers.append(int(match.group(1)))
        except ValueError:
            return None

    return tuple(numbers) if numbers else None


def is_newer_version(current: str, latest: str) -> bool:
    """!
    @brief Returns True if latest is greater than current.
        @param current The current installed version string.
        @param latest The latest available version string.
        @return True if update is available, False otherwise.
    @details Implements the is_newer_version function behavior with deterministic control flow.
    """
    current_tuple = parse_version_tuple(current)
    latest_tuple = parse_version_tuple(latest)
    if not current_tuple or not latest_tuple:
        return False

    max_len = max(len(current_tuple), len(latest_tuple))
    current_norm = current_tuple + (0,) * (max_len - len(current_tuple))
    latest_norm = latest_tuple + (0,) * (max_len - len(latest_tuple))
    return latest_norm > current_norm


def parse_github_owner_repository(remote_url: str) -> tuple[str, str] | None:
    """!
    @brief Extract GitHub owner/repository from a git remote URL.
        @param remote_url Remote URL string from `git remote -v`.
        @return Tuple `(owner, repository)` when URL targets github.com; otherwise None.
    @details Supports SSH (`git@github.com:owner/repo.git`), HTTPS (`https://github.com/owner/repo.git`), and SSH-scheme (`ssh://git@github.com/owner/repo.git`) forms. Removes optional `.git` suffix.
    """
    value = (remote_url or "").strip()
    if not value:
        return None

    patterns = (
        r"^git@github\.com:(?P<owner>[^/\s]+)/(?P<repository>[^/\s]+?)(?:\.git)?$",
        r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repository>[^/\s]+?)(?:\.git)?/?$",
        r"^ssh://git@github\.com/(?P<owner>[^/\s]+)/(?P<repository>[^/\s]+?)(?:\.git)?/?$",
    )
    for pattern in patterns:
        match = re.match(pattern, value)
        if not match:
            continue
        owner = match.group("owner").strip()
        repository = match.group("repository").strip()
        if owner and repository:
            return owner, repository
    return None


def read_git_remote_verbose(cwd: str | None = None) -> str:
    """!
    @brief Read git remote definitions using `git remote -v`.
        @param cwd Optional working directory override for git execution context.
        @return Raw stdout output generated by `git remote -v`.
        @throws subprocess.CalledProcessError If git returns a non-zero status.
    @details Executes `git remote -v` with deterministic stderr capture and text decoding. When `cwd` is omitted, the current process working directory is used.
    """
    command_kwargs: dict[str, Any] = {
        "stderr": subprocess.PIPE,
        "text": True,
    }
    if cwd is not None:
        command_kwargs["cwd"] = cwd
    return subprocess.check_output(
        ["git", "remote", "-v"],
        **command_kwargs,
    )


def resolve_github_owner_repository_from_active_remotes() -> tuple[str, str]:
    """!
    @brief Resolve GitHub owner/repository from active repository remotes.
        @return Tuple `(owner, repository)` resolved from active remotes.
        @throws ValueError If no github.com remote URL can be parsed from `git remote -v`.
        @throws ReqError If git remote inspection cannot execute successfully.
    @details Reads `git remote -v`, prioritizes `origin` fetch URL, then other fetch remotes, then non-fetch entries, and returns the first parseable github.com owner/repository pair. If the first inspection fails outside the repository root context, retries once from `REPO_ROOT`.
    """
    try:
        output = read_git_remote_verbose()
    except subprocess.CalledProcessError as exc:
        try:
            current_directory = Path.cwd().resolve()
            repo_root_directory = REPO_ROOT.resolve()
        except OSError:
            current_directory = Path.cwd()
            repo_root_directory = REPO_ROOT
        if current_directory != repo_root_directory:
            try:
                output = read_git_remote_verbose(cwd=str(REPO_ROOT))
            except subprocess.CalledProcessError as repo_exc:
                raise ReqError(
                    "Error: unable to inspect git remotes for GitHub owner/repository",
                    1,
                ) from repo_exc
        else:
            raise ReqError(
                "Error: unable to inspect git remotes for GitHub owner/repository",
                1,
            ) from exc
    except FileNotFoundError as exc:
        raise ReqError(
            "Error: unable to inspect git remotes for GitHub owner/repository",
            1,
        ) from exc

    ranked_remotes: list[tuple[int, str]] = []
    fallback_remotes: list[str] = []
    for raw_line in output.splitlines():
        parts = raw_line.strip().split()
        if len(parts) < 3:
            continue
        remote_name, remote_url, remote_kind = parts[0], parts[1], parts[2]
        if remote_kind == "(fetch)":
            rank = 0 if remote_name == "origin" else 1
            ranked_remotes.append((rank, remote_url))
        else:
            fallback_remotes.append(remote_url)

    ranked_remotes.sort(key=lambda item: item[0])
    candidate_urls = [url for _, url in ranked_remotes] + fallback_remotes
    for candidate_url in candidate_urls:
        parsed = parse_github_owner_repository(candidate_url)
        if parsed:
            return parsed

    raise ValueError(
        "unable to resolve GitHub owner/repository from active git remotes"
    )


def resolve_pypi_latest_version_url() -> str:
    """!
    @brief Resolve the PyPI JSON API URL for latest-version resolution.
    @details Returns the static endpoint derived from the PyPI project `cli-usereq`.
    @return {str} Fully-qualified URL `https://pypi.org/pypi/cli-usereq/json`.
    @satisfies SRS-430
    """
    return PYPI_PROJECT_JSON_URL


def fetch_pypi_latest_version(
    timeout_seconds: float = RELEASE_CHECK_TIMEOUT_SECONDS,
) -> Optional[str]:
    """!
    @brief Fetch the latest published version of `cli-usereq` from the PyPI JSON API.
        @param timeout_seconds {float} Timeout for the HTTP GET request.
    @details Issues `GET https://pypi.org/pypi/cli-usereq/json` with JSON `Accept` headers,
    parses `info.version`, and normalizes the value through `normalize_release_tag`.
    Complexity: O(1). Side effects: one HTTP request.
    @return {Optional[str]} Normalized latest version string; None when `info.version` is
    absent or not a non-empty string.
    @throws {urllib.error.HTTPError} When the endpoint answers with an HTTP error status.
    @throws {urllib.error.URLError} On network-level failures.
    @throws {TimeoutError} When the request exceeds `timeout_seconds`.
    @throws {json.JSONDecodeError} When the response body is not valid JSON.
    @satisfies SRS-430, SRS-442
    """
    request = urllib.request.Request(
        resolve_pypi_latest_version_url(),
        headers={
            "Accept": "application/json",
            "User-Agent": f"usereq/{load_package_version()}",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8", errors="replace")
    payload = json.loads(body)
    info = payload.get("info")
    if not isinstance(info, dict):
        return None
    version = info.get("version")
    if not isinstance(version, str) or not version.strip():
        return None
    return normalize_release_tag(version)


def fetch_github_latest_version(
    timeout_seconds: float = RELEASE_CHECK_TIMEOUT_SECONDS,
    *,
    raw_tag: bool = False,
) -> Optional[str]:
    """!
    @brief Fetch the latest GitHub release version from the GitHub latest-release API.
        @param timeout_seconds {float} Timeout for the HTTP GET request.
        @param raw_tag {bool} When True, return the raw `tag_name` value with its optional
        `v` prefix preserved; when False, normalize through `normalize_release_tag`.
    @details Issues `GET https://api.github.com/repos/Ogekuri/CLI-useReq/releases/latest` with
    GitHub JSON `Accept` headers and parses `tag_name`. The endpoint answers with the latest
    tagged release independently of the branch holding the tag. Normalized output feeds the
    `--ver`/`--version` display (SRS-441, SRS-442); raw output feeds the `--upgrade --develop`
    tag resolution (SRS-451). The startup release-check never calls this function (SRS-430).
    Complexity: O(1). Side effects: one HTTP request.
    @return {Optional[str]} Latest GitHub release tag: raw whitespace-stripped `tag_name` when
    `raw_tag` is True, `v`-prefix-stripped otherwise; None when `tag_name` is absent or not a
    non-empty string.
    @throws {urllib.error.HTTPError} When the endpoint answers with an HTTP error status.
    @throws {urllib.error.URLError} On network-level failures.
    @throws {TimeoutError} When the request exceeds `timeout_seconds`.
    @throws {json.JSONDecodeError} When the response body is not valid JSON.
    @satisfies SRS-442, SRS-451
    """
    request = urllib.request.Request(
        GITHUB_RELEASES_LATEST_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"usereq/{load_package_version()}",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8", errors="replace")
    payload = json.loads(body)
    tag = payload.get("tag_name")
    if not isinstance(tag, str) or not tag.strip():
        return None
    return tag.strip() if raw_tag else normalize_release_tag(tag)


def format_unix_timestamp_utc(timestamp_seconds: int) -> str:
    """!
    @brief Convert a Unix timestamp into a UTC human-readable string.
        @param timestamp_seconds Unix timestamp in seconds.
        @return UTC datetime string in ISO-like `YYYY-MM-DDTHH:MM:SSZ` format.
    @details Implements deterministic UTC conversion for release-check idle-state persistence.
    """
    return datetime.fromtimestamp(
        timestamp_seconds,
        tz=timezone.utc,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_release_check_idle_file_path(
    program_name: str = RELEASE_CHECK_PROGRAM_NAME,
) -> Path:
    """!
    @brief Resolve idle-state file path for startup release-check throttling.
        @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
        @return Absolute path `$HOME/.cache/<program_name>/check_version_idle-time.json`.
    @details Builds the path using the effective home directory returned by `Path.home()`.
    @satisfies SRS-345
    """
    return (
        Path.home()
        / RELEASE_CHECK_IDLE_CACHE_ROOT_DIRNAME
        / program_name
        / RELEASE_CHECK_IDLE_FILENAME
    )


def cleanup_release_check_idle_state_cache(
    program_name: str = RELEASE_CHECK_PROGRAM_NAME,
) -> None:
    """!
    @brief Delete release-check idle-state file and remove empty cache directory.
        @param program_name Program identifier used as cache subdirectory under `$HOME/.cache`.
        @throws OSError If filesystem operations fail.
    @details Deletes `$HOME/.cache/<program_name>/check_version_idle-time.json` when present; removes `$HOME/.cache/<program_name>` only when it exists and has no remaining entries.
    @satisfies SRS-346
    """
    idle_state_file_path = get_release_check_idle_file_path(program_name=program_name)
    idle_state_cache_dir = idle_state_file_path.parent

    if idle_state_file_path.exists():
        idle_state_file_path.unlink()

    if (
        idle_state_cache_dir.exists()
        and idle_state_cache_dir.is_dir()
        and not any(idle_state_cache_dir.iterdir())
    ):
        idle_state_cache_dir.rmdir()


def read_release_check_idle_state(file_path: Path) -> dict[str, int | str] | None:
    """!
    @brief Read and validate release-check idle-state JSON.
        @param file_path Absolute idle-state JSON path under `$HOME`.
        @return Normalized idle-state dictionary or None when file does not exist.
        @throws OSError If file read fails.
        @throws json.JSONDecodeError If file content is not valid JSON.
        @throws ValueError If required keys are missing or value types are invalid.
    @details Validates required keys `last_success_timestamp`, `last_success_human_readable_timestamp`, `idle_until_timestamp`, and `idle_until_human_readable_timestamp`; timestamps are normalized to integers.
    """
    if not file_path.exists():
        return None

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("idle-state JSON root must be an object")

    required_keys = (
        "last_success_timestamp",
        "last_success_human_readable_timestamp",
        "idle_until_timestamp",
        "idle_until_human_readable_timestamp",
    )
    for key in required_keys:
        if key not in payload:
            raise ValueError(f"idle-state JSON missing key '{key}'")

    last_success_timestamp = payload["last_success_timestamp"]
    idle_until_timestamp = payload["idle_until_timestamp"]
    last_success_human_readable_timestamp = payload[
        "last_success_human_readable_timestamp"
    ]
    idle_until_human_readable_timestamp = payload["idle_until_human_readable_timestamp"]

    if not isinstance(last_success_timestamp, (int, float)):
        raise ValueError("idle-state key 'last_success_timestamp' must be numeric")
    if not isinstance(idle_until_timestamp, (int, float)):
        raise ValueError("idle-state key 'idle_until_timestamp' must be numeric")
    if (
        not isinstance(last_success_human_readable_timestamp, str)
        or not last_success_human_readable_timestamp.strip()
    ):
        raise ValueError(
            "idle-state key 'last_success_human_readable_timestamp' must be a non-empty string"
        )
    if (
        not isinstance(idle_until_human_readable_timestamp, str)
        or not idle_until_human_readable_timestamp.strip()
    ):
        raise ValueError(
            "idle-state key 'idle_until_human_readable_timestamp' must be a non-empty string"
        )

    return {
        "last_success_timestamp": int(last_success_timestamp),
        "last_success_human_readable_timestamp": (
            last_success_human_readable_timestamp.strip()
        ),
        "idle_until_timestamp": int(idle_until_timestamp),
        "idle_until_human_readable_timestamp": (
            idle_until_human_readable_timestamp.strip()
        ),
    }


def should_execute_release_check(
    idle_state: Mapping[str, Any] | None,
    now_timestamp: int,
) -> bool:
    """!
    @brief Decide whether startup release-check should execute in current invocation.
        @param idle_state Parsed idle-state payload or None when unavailable.
        @param now_timestamp Current Unix timestamp in seconds.
        @return True when release-check must execute; False when still in idle window.
    @details Executes release-check when state is missing and skips only while the persisted `idle_until_timestamp` is greater than the current timestamp.
    @satisfies SRS-348
    """
    if idle_state is None:
        return True

    idle_until_timestamp = idle_state.get("idle_until_timestamp")
    if not isinstance(idle_until_timestamp, (int, float)):
        return True
    return now_timestamp >= int(idle_until_timestamp)


def parse_retry_after_seconds(
    retry_after_header: str | None,
    now_timestamp: int,
) -> int | None:
    """!
    @brief Parse an HTTP `Retry-After` header value into non-negative seconds.
        @param retry_after_header Raw `Retry-After` header value.
        @param now_timestamp Current Unix timestamp in seconds.
        @return Retry delay in seconds when parsing succeeds; otherwise None.
    @details Supports integer-second values and HTTP-date values; HTTP-date values are converted to a delta from `now_timestamp`.
    """
    if retry_after_header is None:
        return None

    raw_value = retry_after_header.strip()
    if not raw_value:
        return None

    if re.fullmatch(r"[0-9]+", raw_value):
        return max(0, int(raw_value))

    try:
        parsed_datetime = parsedate_to_datetime(raw_value)
    except (TypeError, ValueError):
        return None
    if parsed_datetime is None:
        return None
    if parsed_datetime.tzinfo is None:
        parsed_datetime = parsed_datetime.replace(tzinfo=timezone.utc)
    return max(0, int(parsed_datetime.timestamp()) - now_timestamp)


def write_release_check_idle_state_payload(
    file_path: Path,
    last_success_timestamp: int,
    idle_until_timestamp: int,
) -> None:
    """!
    @brief Persist canonical release-check idle-state payload to disk.
        @param file_path Absolute idle-state JSON path.
        @param last_success_timestamp Unix timestamp of the last successful release-check.
        @param idle_until_timestamp Unix timestamp until startup release-check remains disabled.
        @throws OSError If file write fails.
    @details Serializes both numeric and UTC human-readable timestamps for the success instant and the idle-until instant.
    """
    payload = {
        "last_success_timestamp": last_success_timestamp,
        "last_success_human_readable_timestamp": format_unix_timestamp_utc(
            last_success_timestamp
        ),
        "idle_until_timestamp": idle_until_timestamp,
        "idle_until_human_readable_timestamp": format_unix_timestamp_utc(
            idle_until_timestamp
        ),
    }
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )


def write_release_check_idle_state(
    file_path: Path,
    now_timestamp: int,
    idle_delay_seconds: int = RELEASE_CHECK_IDLE_DELAY_SECONDS,
) -> None:
    """!
    @brief Persist release-check idle-state after a successful remote check.
        @param file_path Absolute idle-state JSON path.
        @param now_timestamp Successful check timestamp in seconds.
        @param idle_delay_seconds Fixed idle-delay length in seconds.
        @throws OSError If file write fails.
    @details Computes `idle_until_timestamp = now_timestamp + idle_delay_seconds` and persists canonical idle-state keys.
    @satisfies SRS-349
    """
    idle_until_timestamp = now_timestamp + int(idle_delay_seconds)
    write_release_check_idle_state_payload(
        file_path=file_path,
        last_success_timestamp=now_timestamp,
        idle_until_timestamp=idle_until_timestamp,
    )


def write_failed_release_check_idle_state(
    file_path: Path,
    now_timestamp: int,
    idle_state: Mapping[str, Any] | None,
    idle_delay_seconds: int = RELEASE_CHECK_IDLE_DELAY_SECONDS,
) -> None:
    """!
    @brief Persist idle-state after a startup release-check failure.
        @param file_path Absolute idle-state JSON path.
        @param now_timestamp Current Unix timestamp in seconds.
        @param idle_state Existing parsed idle-state payload or None.
        @param idle_delay_seconds Fixed failure idle-delay length in seconds.
        @throws OSError If file write fails.
    @details Computes `idle_until_timestamp = now + idle_delay_seconds`, rewrites the canonical idle-state payload on every failure, and preserves the previous successful timestamp when available.
    @satisfies SRS-350, SRS-351
    """
    effective_idle_delay = max(0, int(idle_delay_seconds))
    idle_until_timestamp = now_timestamp + effective_idle_delay

    last_success_timestamp = now_timestamp
    if isinstance(idle_state, Mapping):
        current_last_success = idle_state.get("last_success_timestamp")
        if isinstance(current_last_success, (int, float)):
            last_success_timestamp = int(current_last_success)

    write_release_check_idle_state_payload(
        file_path=file_path,
        last_success_timestamp=last_success_timestamp,
        idle_until_timestamp=idle_until_timestamp,
    )


def persist_failed_release_check_idle_state(
    file_path: Path,
    now_timestamp: int,
    idle_state: Mapping[str, Any] | None,
    idle_delay_seconds: int = RELEASE_CHECK_IDLE_DELAY_SECONDS,
) -> None:
    """!
    @brief Persist failure idle-state and report write failures.
        @param file_path Absolute idle-state JSON path.
        @param now_timestamp Current Unix timestamp in seconds.
        @param idle_state Existing parsed idle-state payload or None.
        @param idle_delay_seconds Fixed failure idle-delay length in seconds.
        @return {None} Function return value.
    @details Delegates failure idle-state persistence to `write_failed_release_check_idle_state(...)`; converts `OSError` into the standard bright-red stderr diagnostic without swallowing the original release-check failure.
    @satisfies SRS-350, SRS-351
    """
    try:
        write_failed_release_check_idle_state(
            file_path=file_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
            idle_delay_seconds=idle_delay_seconds,
        )
    except OSError as idle_state_error:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: idle-state write failure ({idle_state_error}){ANSI_RESET}",
            file=sys.stderr,
        )


def maybe_notify_newer_version(
    timeout_seconds: float = RELEASE_CHECK_TIMEOUT_SECONDS,
) -> Optional[str]:
    """!
    @brief Executes idle-gated online PyPI version check and prints bright colored status messages.
        @param timeout_seconds Time to wait for the version check response.
        @details Reads idle-state from `$HOME/.cache/usereq/check_version_idle-time.json`, skips remote requests when idle window is active unless startup context enables `FORCE_ONLINE_RELEASE_CHECK`, fetches the latest version from the PyPI JSON API (SRS-430) when due, compares versions, prints a bright-green update message only for newer versions, persists a 3600-second idle-delay after successful HTTP/JSON validation, prints bright-red diagnostics on every failure, rewrites idle-state JSON on every failure, uses an 86400-second idle-delay for `HTTPError`, `URLError`, and `TimeoutError`, and uses the default 3600-second idle-delay for other release-check failures.
    @return {Optional[str]} The fetched PyPI latest version on successful validation; None when the check is idle-gated or fails.
    @satisfies SRS-345, SRS-348, SRS-349, SRS-350, SRS-351, SRS-430
    """

    current_version = load_package_version()
    idle_state_path = get_release_check_idle_file_path()
    now_timestamp = int(time.time())

    idle_state: Mapping[str, Any] | None = None
    try:
        idle_state = read_release_check_idle_state(idle_state_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: invalid idle-state ({exc}){ANSI_RESET}",
            file=sys.stderr,
        )
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
        )
    if not FORCE_ONLINE_RELEASE_CHECK and not should_execute_release_check(
        idle_state,
        now_timestamp,
    ):
        return None

    try:
        latest_version = fetch_pypi_latest_version(timeout_seconds)
    except urllib.error.HTTPError as exc:
        error_details = f"HTTP {exc.code}"
        raw_error_payload = exc.read().decode("utf-8", errors="replace")
        payload: Any = None
        try:
            payload = json.loads(raw_error_payload) if raw_error_payload else None
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                error_details = f"{error_details}: {message.strip()}"
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
            idle_delay_seconds=RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: {error_details}{ANSI_RESET}",
            file=sys.stderr,
        )
        return None
    except urllib.error.URLError as exc:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: network failure ({exc.reason}){ANSI_RESET}",
            file=sys.stderr,
        )
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
            idle_delay_seconds=RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )
        return None
    except TimeoutError:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: timeout exceeded{ANSI_RESET}",
            file=sys.stderr,
        )
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
            idle_delay_seconds=RELEASE_CHECK_RATE_LIMIT_IDLE_DELAY_SECONDS,
        )
        return None
    except (json.JSONDecodeError, ValueError) as exc:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: invalid release payload ({exc}){ANSI_RESET}",
            file=sys.stderr,
        )
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
        )
        return None

    if latest_version is None:
        print(
            (
                f"{ANSI_BRIGHT_RED}Release-check error: invalid response payload "
                "(missing 'info.version')."
                f"{ANSI_RESET}"
            ),
            file=sys.stderr,
        )
        persist_failed_release_check_idle_state(
            file_path=idle_state_path,
            now_timestamp=now_timestamp,
            idle_state=idle_state,
        )
        return None

    if is_newer_version(current_version, latest_version):
        print(
            (
                f"{ANSI_BRIGHT_GREEN}New version available: "
                f"installed {current_version}, latest {latest_version}."
                f"{ANSI_RESET}"
            ),
            file=sys.stderr,
        )
    try:
        write_release_check_idle_state(idle_state_path, now_timestamp)
    except OSError as exc:
        print(
            f"{ANSI_BRIGHT_RED}Release-check error: idle-state write failure ({exc}){ANSI_RESET}",
            file=sys.stderr,
        )
    return latest_version


def ensure_doc_directory(
    path: str, project_base: Path, *, create_missing: bool = False
) -> None:
    """!
    @brief Resolve and validate docs directory path under project base.
    @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
    @param path {str} Candidate docs directory path.
    @param project_base {Path} Absolute project base path.
    @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
    @return {None} Function return value.
    @throws {ReqError} Raised when path escapes project base or resolves to a file.
    @satisfies SRS-359, SRS-363
    """
    normalized = make_relative_if_contains_project(path, project_base)
    doc_path = project_base / normalized
    resolved = doc_path.resolve(strict=False)
    if not resolved.is_relative_to(project_base):
        raise ReqError("Error: --docs-dir must be under the project base", 5)
    if doc_path.exists() and not doc_path.is_dir():
        raise ReqError("Error: --docs-dir must specify a directory, not a file", 5)
    if not doc_path.exists():
        if create_missing:
            doc_path.mkdir(parents=True, exist_ok=True)
        else:
            raise ReqError(
                f"Error: the --docs-dir directory '{normalized}' does not exist under {project_base}",
                5,
            )


def ensure_test_directory(
    path: str, project_base: Path, *, create_missing: bool = False
) -> None:
    """!
    @brief Resolve and validate tests directory path under project base.
    @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
    @param path {str} Candidate tests directory path.
    @param project_base {Path} Absolute project base path.
    @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
    @return {None} Function return value.
    @throws {ReqError} Raised when path escapes project base or resolves to a file.
    @satisfies SRS-361, SRS-363
    """
    normalized = make_relative_if_contains_project(path, project_base)
    test_path = project_base / normalized
    resolved = test_path.resolve(strict=False)
    if not resolved.is_relative_to(project_base):
        raise ReqError("Error: --tests-dir must be under the project base", 5)
    if test_path.exists() and not test_path.is_dir():
        raise ReqError("Error: --tests-dir must specify a directory, not a file", 5)
    if not test_path.exists():
        if create_missing:
            test_path.mkdir(parents=True, exist_ok=True)
        else:
            raise ReqError(
                f"Error: the --tests-dir directory '{normalized}' does not exist under {project_base}",
                5,
            )


def ensure_src_directory(
    path: str, project_base: Path, *, create_missing: bool = False
) -> None:
    """!
    @brief Resolve and validate source directory path under project base.
    @details Normalizes input path against project base, enforces in-repository containment, and validates directory shape. When `create_missing` is true, creates missing directory and all missing parent directories.
    @param path {str} Candidate source directory path.
    @param project_base {Path} Absolute project base path.
    @param create_missing {bool} Installation-mode flag enabling recursive directory creation.
    @return {None} Function return value.
    @throws {ReqError} Raised when path escapes project base or resolves to a file.
    @satisfies SRS-362, SRS-363
    """
    normalized = make_relative_if_contains_project(path, project_base)
    src_path = project_base / normalized
    resolved = src_path.resolve(strict=False)
    if not resolved.is_relative_to(project_base):
        raise ReqError("Error: --src-dir must be under the project base", 5)
    if src_path.exists() and not src_path.is_dir():
        raise ReqError("Error: --src-dir must specify a directory, not a file", 5)
    if not src_path.exists():
        if create_missing:
            src_path.mkdir(parents=True, exist_ok=True)
        else:
            raise ReqError(
                f"Error: the --src-dir directory '{normalized}' does not exist under {project_base}",
                5,
            )


def make_relative_if_contains_project(path_value: str, project_base: Path) -> str:
    """! @brief Normalizes the path relative to the project root when possible.
    @param path_value The input path string.
    @param project_base The base path of the project.
    @return The normalized relative path string.
    @details Handles cases where the path includes the project directory name redundantly.
    """
    if not path_value:
        return ""
    candidate = Path(path_value)
    if not candidate.is_absolute():
        parts = candidate.parts
        if parts and parts[0] == project_base.name and len(parts) > 1:
            candidate = Path(*parts[1:])
        elif project_base.name in parts:
            project_name_index = max(
                idx for idx, part in enumerate(parts) if part == project_base.name
            )
            if project_name_index + 1 < len(parts):
                suffix_candidate = Path(*parts[project_name_index + 1 :])
                suffix_resolved = (project_base / suffix_candidate).resolve(
                    strict=False
                )
                if suffix_resolved.exists():
                    candidate = suffix_candidate
    if candidate.is_absolute():
        try:
            return str(candidate.relative_to(project_base))
        except ValueError:
            return str(candidate)
    resolved = (project_base / candidate).resolve(strict=False)
    try:
        return str(resolved.relative_to(project_base))
    except ValueError:
        pass
    base_str = str(project_base)
    if path_value.startswith(base_str):
        trimmed = path_value[len(base_str) :].lstrip("/\\")
        return trimmed
    return path_value


def resolve_absolute(normalized: str, project_base: Path) -> Optional[Path]:
    """!
    @brief Resolves the absolute path starting from a normalized value.
        @param normalized The normalized relative path string.
        @param project_base The project root path.
        @return Absolute Path object or None if normalized is empty.
    @details Implements the resolve_absolute function behavior with deterministic control flow.
    """
    if not normalized:
        return None
    candidate = Path(normalized)
    if candidate.is_absolute():
        return candidate
    return (project_base / candidate).resolve(strict=False)


def resolve_git_root(target_path: Path) -> Path:
    """!
    @brief Resolve the git repository root for a given path.
    @param target_path Absolute path that must be inside a git repository.
    @return Absolute path to the git repository root.
    @throws ReqError If the path is not inside a git repository.
    @satisfies SRS-305, SRS-306
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=str(target_path),
            timeout=10,
        )
        if result.returncode != 0:
            raise ReqError(
                f"Error: '{target_path}' is not inside a git repository.",
                3,
            )
        return Path(result.stdout.strip()).resolve()
    except FileNotFoundError:
        raise ReqError("Error: git is not available on PATH.", 3)
    except subprocess.TimeoutExpired:
        raise ReqError("Error: git command timed out.", 3)


def sanitize_branch_name(branch: str) -> str:
    """!
    @brief Replace characters incompatible with Linux or Windows paths in a branch name.
    @param branch Raw git branch name.
    @return Sanitized string with incompatible characters replaced by `-`.
    @satisfies SRS-319
    """
    return re.sub(r'[<>:"/\\|?*\x00-\x1f\s~^{}\[\]]', "-", branch)


def validate_wt_name(wt_name: str) -> bool:
    """!
    @brief Validate that a worktree/branch name contains only valid directory characters.
    @param wt_name Candidate worktree name.
    @return True if valid, False if invalid characters are present.
    @satisfies SRS-321
    """
    if not wt_name or wt_name in (".", ".."):
        return False
    return INVALID_WT_NAME_RE.search(wt_name) is None


def load_full_config() -> dict:
    """!
    @brief Load ALL parameters from the user-global configuration file as a raw dictionary.
    @return Full dictionary of all config key-value pairs.
    @throws ReqError If the global config file is missing or invalid JSON.
    @satisfies SRS-310, SRS-387
    """
    config_path = get_global_config_path()
    if not config_path.is_file():
        raise ReqError(
            f"Error: global configuration file not found at {config_path}",
            11,
        )
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReqError(
            f"Error: global configuration file {config_path} is not valid", 11
        ) from exc


def save_config(
    doc_dir_value: str,
    test_dir_value: str,
    src_dir_values: list[str],
    static_check_config: Optional[dict] = None,
    provider_specs: Optional[list[str]] = None,
) -> None:
    """!
    @brief Saves normalized directory parameters to the user-global configuration file.
    @param doc_dir_value Project-relative docs directory value.
    @param test_dir_value Project-relative tests directory value.
    @param src_dir_values Ordered project-relative source directory values.
    @param static_check_config Optional dict of static-check config to persist under key
      `"static-check"`; preserved unchanged when None.
    @param provider_specs Optional list of raw ``--enable`` SPEC strings to
      persist under the `"providers"` key (SRS-279).
    @details Writes the configuration payload to `~/.config/usereq/config.json`, creating
    missing parent directories on first write, via read-modify-write so unspecified
    canonical keys (including `"auto-install"`) are preserved. Only canonical keys from
    `PERSISTED_CONFIG_KEYS` are written; `--prj-base` and `--git-base` are never written
    (SRS-288, SRS-387, SRS-394, SRS-407, SRS-420).
    @return {None} Function return value.
    @satisfies SRS-279, SRS-288, SRS-387, SRS-394, SRS-407, SRS-420
    """
    payload = _read_config_payload()
    payload["docs-dir"] = doc_dir_value
    payload["tests-dir"] = test_dir_value
    payload["src-dir"] = src_dir_values
    if static_check_config:
        payload["static-check"] = static_check_config
    if provider_specs:
        payload["providers"] = provider_specs
    _write_config_payload(payload)


def update_directory_config(
    docs_dir_value: Optional[str] = None,
    tests_dir_value: Optional[str] = None,
    src_dir_values: Optional[list[str]] = None,
) -> None:
    """!
    @brief Persist one or more directory configuration keys while preserving unrelated keys.
    @details Loads the existing raw configuration payload when present, replaces only the
    supplied directory keys, and rewrites `~/.config/usereq/config.json` with parent
    directories created on demand. `--prj-base` and `--git-base` are never persisted
    (SRS-394, SRS-398, SRS-399, SRS-400, SRS-401).
    @param docs_dir_value Project-relative docs directory value, or None to keep current.
    @param tests_dir_value Project-relative tests directory value, or None to keep current.
    @param src_dir_values Ordered project-relative source directory values, or None to keep current.
    @return {None} Function return value.
    @throws ReqError If the existing configuration file contains invalid JSON.
    @satisfies SRS-394, SRS-398, SRS-399, SRS-400, SRS-401
    """
    config_path = get_global_config_path()
    payload: dict = {}
    if config_path.is_file():
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReqError(
                f"Error: global configuration file {config_path} is not valid", 11
            ) from exc
        if isinstance(loaded, dict):
            payload = loaded
    if docs_dir_value is not None:
        payload["docs-dir"] = docs_dir_value
    if tests_dir_value is not None:
        payload["tests-dir"] = tests_dir_value
    if src_dir_values is not None:
        payload["src-dir"] = list(src_dir_values)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_config() -> dict[str, str | list[str]]:
    """!
    @brief Loads directory parameters from the user-global configuration file.
    @return Dictionary containing `docs-dir`, `tests-dir`, and `src-dir` values.
    @details Reads `~/.config/usereq/config.json`; when the file is absent every key falls
    back to its default (`usereq`, `tests`, `src`). Present but invalid values raise
    `ReqError`; `--prj-base` and `--git-base` are never read from the file
    (SRS-359, SRS-361, SRS-362, SRS-394, SRS-407).
    @throws ReqError If the global config file is invalid or holds invalid directory values.
    @satisfies SRS-359, SRS-361, SRS-362, SRS-394, SRS-407
    """
    config_path = get_global_config_path()
    payload: dict = {}
    if config_path.is_file():
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReqError(
                f"Error: global configuration file {config_path} is not valid", 11
            ) from exc
        if isinstance(loaded, dict):
            payload = loaded
    doc_dir_value = payload.get("docs-dir", DEFAULT_DOCS_DIR)
    test_dir_value = payload.get("tests-dir", DEFAULT_TESTS_DIR)
    src_dir_value = payload.get("src-dir", list(DEFAULT_SRC_DIRS))
    if not isinstance(doc_dir_value, str) or not doc_dir_value.strip():
        raise ReqError(
            "Error: missing or invalid 'docs-dir' field in the global configuration file",
            11,
        )
    if not isinstance(test_dir_value, str) or not test_dir_value.strip():
        raise ReqError(
            "Error: missing or invalid 'tests-dir' field in the global configuration file",
            11,
        )
    if (
        not isinstance(src_dir_value, list)
        or not src_dir_value
        or not all(isinstance(item, str) and item.strip() for item in src_dir_value)
    ):
        raise ReqError(
            "Error: missing or invalid 'src-dir' field in the global configuration file",
            11,
        )
    return {
        "docs-dir": doc_dir_value,
        "tests-dir": test_dir_value,
        "src-dir": src_dir_value,
    }


def load_static_check_from_config() -> dict:
    """!
    @brief Load the `"static-check"` section from the user-global configuration file without validation errors.
    @return Dict of static-check config (canonical-lang -> list[config-dict]).
    @details Reads `~/.config/usereq/config.json` silently. When the payload stores no
    `"static-check"` entry (including a missing or unreadable file), returns a deep copy of
    `DEFAULT_STATIC_CHECK` (SRS-424); a present entry, including an empty or invalid object,
    suppresses the defaults and is normalized like before: per-language entries that are
    not non-empty arrays of objects are dropped. Does NOT raise `ReqError`; caller decides
    whether absence is an error.
    @see SRS-252, SRS-253, SRS-256, SRS-424, SRS-425, SRS-426
    @satisfies SRS-424, SRS-425, SRS-426
    """
    config_path = get_global_config_path()
    payload: dict = {}
    if config_path.is_file():
        try:
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            loaded = {}
        if isinstance(loaded, dict):
            payload = loaded
    if "static-check" not in payload:
        return copy.deepcopy(DEFAULT_STATIC_CHECK)
    sc = payload.get("static-check")
    if not isinstance(sc, dict):
        return {}
    normalized: dict = {}
    for lang, entries in sc.items():
        if (
            isinstance(lang, str)
            and isinstance(entries, list)
            and entries
            and all(isinstance(item, dict) for item in entries)
        ):
            normalized[lang] = entries
    return normalized


def _static_check_entry_identity(
    canonical_lang: str, entry: Mapping[str, Any]
) -> tuple[str, str, Optional[str], tuple[str, ...]]:
    """!
    @brief Build the canonical identity tuple for one static-check entry.
    @param canonical_lang Canonical language key that owns the entry.
    @param entry Static-check entry mapping loaded from config or parsed from CLI.
    @return Tuple ``(canonical_lang, module, cmd, params_tuple)``.
    @details Identity is defined strictly by language, module, cmd, and params.
      Unknown/additional keys in ``entry`` are ignored; ``params`` is normalized
      to a tuple preserving order, and non-list params are treated as empty.
    @satisfies SRS-301
    """
    module_raw = entry.get("module")
    cmd_raw = entry.get("cmd")
    params_raw = entry.get("params")
    module = module_raw if isinstance(module_raw, str) else ""
    cmd = cmd_raw if isinstance(cmd_raw, str) else None
    params: tuple[str, ...] = ()
    if isinstance(params_raw, list):
        params = tuple(item for item in params_raw if isinstance(item, str))
    return (canonical_lang, module, cmd, params)


def load_persisted_provider_specs() -> list[str]:
    """!
    @brief Load persisted ``--enable`` SPEC strings from the user-global configuration file.
    @return List of raw SPEC strings; empty list if key is missing or config is unreadable.
    @details Reads the ``"providers"`` key from `~/.config/usereq/config.json` (SRS-064,
    SRS-279). All providers are disabled by default because the key defaults to an empty
    list. Returns ``[]`` on any read or parse error rather than raising.
    @see SRS-279, SRS-064
    @satisfies SRS-064, SRS-279
    """
    config_path = get_global_config_path()
    if not config_path.is_file():
        return []
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    specs = payload.get("providers", [])
    if isinstance(specs, list) and all(isinstance(s, str) for s in specs):
        return specs
    return []


def _read_config_payload() -> dict:
    """!
    @brief Read the raw user-global configuration payload without key filtering.
    @return {dict} Raw JSON dictionary; empty dict when the file is absent.
    @throws {ReqError} Raised when the file exists but holds invalid JSON (exit code 11).
    @details Single read path for configuration commands performing read-modify-write
    updates (SRS-279, SRS-288, SRS-387, SRS-413, SRS-414, SRS-420).
    @satisfies SRS-288, SRS-387
    """
    config_path = get_global_config_path()
    if not config_path.is_file():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReqError(
            f"Error: global configuration file {config_path} is not valid", 11
        ) from exc
    return payload if isinstance(payload, dict) else {}


def _write_config_payload(payload: dict) -> None:
    """!
    @brief Write the user-global configuration payload filtered to canonical keys.
    @param payload {dict} Full payload; only `PERSISTED_CONFIG_KEYS` entries are written.
    @return {None} Function return value.
    @details Creates missing parent directories on first write (SRS-387) and never
    writes `--prj-base`/`--git-base` (SRS-394).
    @satisfies SRS-288, SRS-387, SRS-394
    """
    config_path = get_global_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    filtered = {
        key: value for key, value in payload.items() if key in PERSISTED_CONFIG_KEYS
    }
    config_path.write_text(
        json.dumps(filtered, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_auto_install_enabled() -> bool:
    """!
    @brief Resolve the persisted auto-install flag with enabled default.
    @return {bool} True unless the configuration stores exactly `false`.
    @details `auto-install` defaults to enabled; unreadable configuration falls back to
    the default (SRS-420, SRS-421).
    @satisfies SRS-420, SRS-421
    """
    try:
        payload = _read_config_payload()
    except ReqError:
        return DEFAULT_AUTO_INSTALL
    return payload.get(AUTO_INSTALL_CONFIG_KEY, DEFAULT_AUTO_INSTALL) is not False


def _persisted_provider_spec_provider(spec: str) -> Optional[str]:
    """!
    @brief Resolve the provider token of one persisted SPEC string.
    @param spec {str} Raw persisted SPEC string.
    @return {Optional[str]} Provider name, or None when the SPEC is invalid.
    @details Invalid persisted SPECs are treated as unmatched and dropped by callers.
    """
    try:
        return parse_provider_spec(spec)[0]
    except ReqError:
        return None


def apply_enable_provider_specs(specs: list[str]) -> None:
    """!
    @brief Persist `--enable` specs replacing the named providers' entries.
    @param specs {list[str]} Raw SPEC strings in CLI order.
    @return {None} Function return value.
    @details Validates every SPEC through `parse_provider_spec` (SRS-275, SRS-278),
    removes all previously persisted specs of the named providers, appends the new
    specs in CLI order, and preserves every other provider (SRS-279). No artifact is
    installed (SRS-276).
    @throws {ReqError} Raised on invalid SPEC tokens with exit code 1 (SRS-278).
    @satisfies SRS-275, SRS-276, SRS-278, SRS-279
    """
    validated: list[str] = []
    named_providers: list[str] = []
    for spec in specs:
        provider_name = parse_provider_spec(spec)[0]
        validated.append(spec)
        if provider_name not in named_providers:
            named_providers.append(provider_name)
    payload = _read_config_payload()
    persisted = payload.get("providers", [])
    persisted_specs = (
        persisted
        if isinstance(persisted, list) and all(isinstance(s, str) for s in persisted)
        else []
    )
    kept = [
        spec
        for spec in persisted_specs
        if _persisted_provider_spec_provider(spec) not in named_providers
    ]
    payload["providers"] = kept + validated
    _write_config_payload(payload)


def apply_disable_provider_specs(names: list[str]) -> None:
    """!
    @brief Remove all persisted specs of the named providers.
    @param names {list[str]} Provider names supplied via `--disable`.
    @return {None} Function return value.
    @details Removes every persisted SPEC of each named provider; absent specs leave the
    configuration unchanged; the `"providers"` key is removed when no specs remain
    (SRS-413).
    @throws {ReqError} Raised on unknown provider tokens with exit code 1 (SRS-422).
    @satisfies SRS-413, SRS-422
    """
    for name in names:
        if name not in VALID_PROVIDERS:
            raise ReqError(f"Error: unknown provider '{name}'.", 1)
    payload = _read_config_payload()
    persisted = payload.get("providers", [])
    persisted_specs = (
        persisted
        if isinstance(persisted, list) and all(isinstance(s, str) for s in persisted)
        else []
    )
    disabled = set(names)
    remaining = [
        spec
        for spec in persisted_specs
        if _persisted_provider_spec_provider(spec) not in disabled
    ]
    if remaining:
        payload["providers"] = remaining
    else:
        payload.pop("providers", None)
    _write_config_payload(payload)


def apply_enable_static_check_specs(specs: list[str]) -> None:
    """!
    @brief Persist `--enable-static-check` entries merged into the existing configuration.
    @param specs {list[str]} Raw SPEC strings in CLI order.
    @return {None} Function return value.
    @details Parses each SPEC (SRS-260), deduplicates within the invocation (SRS-251),
    validates Command executables (SRS-250), merges into the persisted `"static-check"`
    object by exact `(language, module, cmd, params)` identity (SRS-301), and requires no
    `--prj-base` (SRS-415).
    @throws {ReqError} Raised on invalid language/module tokens or non-executable Command
    `cmd` values with exit code 1.
    @satisfies SRS-248, SRS-250, SRS-251, SRS-301, SRS-415
    """
    from .static_check import parse_enable_static_check as _parse_sc

    new_entries: dict = {}
    for spec in specs:
        canonical_lang, lang_cfg = _parse_sc(spec)
        identity = _static_check_entry_identity(canonical_lang, lang_cfg)
        existing = new_entries.get(canonical_lang, [])
        if not any(
            _static_check_entry_identity(canonical_lang, entry) == identity
            for entry in existing
        ):
            new_entries.setdefault(canonical_lang, []).append(lang_cfg)
    _validate_enable_static_check_command_executables(new_entries, enforce=True)
    payload = _read_config_payload()
    existing_sc = payload.get("static-check", {})
    merged = (
        {lang: list(entries) for lang, entries in existing_sc.items()}
        if isinstance(existing_sc, dict)
        else {}
    )
    for lang, entries in new_entries.items():
        identities = {
            _static_check_entry_identity(lang, entry)
            for entry in merged.get(lang, [])
            if isinstance(entry, dict)
        }
        for entry in entries:
            identity = _static_check_entry_identity(lang, entry)
            if identity not in identities:
                merged.setdefault(lang, []).append(entry)
                identities.add(identity)
    payload["static-check"] = merged
    _write_config_payload(payload)


def apply_disable_static_check_specs(specs: list[str]) -> None:
    """!
    @brief Remove static-check entries selected by `--disable-static-check` SPECs.
    @param specs {list[str]} SPEC strings; `LANG=MODULE[,CMD[,PARAM...]]` removes exact
    identity matches, bare `LANG` removes the whole canonical language key.
    @return {None} Function return value.
    @details Empty language arrays are removed from the `"static-check"` object and the
    `"static-check"` key is persisted even when empty so explicit configuration suppresses
    the SRS-424 defaults; requires no `--prj-base` (SRS-414, SRS-415).
    @throws {ReqError} Raised on unknown language or module tokens with exit code 1 (SRS-422).
    @satisfies SRS-414, SRS-415, SRS-422, SRS-424
    """
    from .static_check import (
        STATIC_CHECK_LANG_CANONICAL,
        parse_enable_static_check as _parse_sc,
    )

    payload = _read_config_payload()
    existing_sc = payload.get("static-check", {})
    merged = (
        {lang: list(entries) for lang, entries in existing_sc.items()}
        if isinstance(existing_sc, dict)
        else {}
    )
    for spec in specs:
        if "=" in spec:
            canonical_lang, lang_cfg = _parse_sc(spec)
            identity = _static_check_entry_identity(canonical_lang, lang_cfg)
            merged[canonical_lang] = [
                entry
                for entry in merged.get(canonical_lang, [])
                if not (
                    isinstance(entry, dict)
                    and _static_check_entry_identity(canonical_lang, entry) == identity
                )
            ]
        else:
            canonical_lang = STATIC_CHECK_LANG_CANONICAL.get(spec.strip().lower())
            if canonical_lang is None:
                raise ReqError(
                    f"Error: unknown static-check language '{spec}'.", 1
                )
            merged.pop(canonical_lang, None)
    for lang in [key for key, entries in merged.items() if not entries]:
        del merged[lang]
    payload["static-check"] = merged
    _write_config_payload(payload)


def apply_auto_install_config(enabled: bool) -> None:
    """!
    @brief Persist the auto-install enabled flag.
    @param enabled {bool} Value persisted under `"auto-install"`.
    @return {None} Function return value.
    @details Read-modify-write preserving all unrelated canonical keys (SRS-420).
    @satisfies SRS-420
    """
    payload = _read_config_payload()
    payload[AUTO_INSTALL_CONFIG_KEY] = enabled
    _write_config_payload(payload)


def _is_provider_config_command(args: Namespace) -> bool:
    """!
    @brief Check if args request a provider/static-check/auto-install configuration command.
    @param args Parsed CLI namespace.
    @return True when any configuration flag is present.
    @details Configuration commands only update `~/.config/usereq/config.json` and never
    install artifacts (SRS-276, SRS-413, SRS-414, SRS-415, SRS-420).
    """
    return bool(
        getattr(args, "enable_provider", None)
        or getattr(args, "disable_provider", None)
        or getattr(args, "enable_static_check", None)
        or getattr(args, "disable_static_check", None)
        or getattr(args, "enable_auto_install", False)
        or getattr(args, "disable_auto_install", False)
    )


def run_config_commands(args: Namespace) -> None:
    """!
    @brief Apply every provider/static-check/auto-install configuration command.
    @param args Parsed CLI namespace carrying the configuration flag values.
    @return {None} Function return value.
    @details Application order: `--enable`, `--disable`,
    `--enable-static-check`, `--disable-static-check`, `--enable-auto-install`,
    `--disable-auto-install`; each step persists immediately (SRS-275, SRS-413, SRS-414,
    SRS-420).
    @satisfies SRS-275, SRS-276, SRS-413, SRS-414, SRS-415, SRS-420
    """
    enable_provider = getattr(args, "enable_provider", None) or []
    if enable_provider:
        apply_enable_provider_specs(enable_provider)
    disable_provider = getattr(args, "disable_provider", None) or []
    if disable_provider:
        apply_disable_provider_specs(disable_provider)
    enable_sc = getattr(args, "enable_static_check", None) or []
    if enable_sc:
        apply_enable_static_check_specs(enable_sc)
    disable_sc = getattr(args, "disable_static_check", None) or []
    if disable_sc:
        apply_disable_static_check_specs(disable_sc)
    if getattr(args, "enable_auto_install", False):
        apply_auto_install_config(True)
    if getattr(args, "disable_auto_install", False):
        apply_auto_install_config(False)


def generate_guidelines_file_list() -> str:
    """!
    @brief Build the `%%GUIDELINES_FILES%%` substitution payload from GUIDELINES_DIR.
    @details Enumerates non-hidden regular files in :func:`guidelines_dir` in deterministic
    sorted order and renders each as a backticked home-relative path (SRS-402). When the
    directory is absent or empty, renders the home-relative directory itself with a trailing
    slash.
    @return {str} Comma-separated backticked home-relative paths, or the directory fallback.
    @satisfies SRS-403
    """
    source_dir = guidelines_dir()
    if not source_dir.is_dir():
        return f"`{format_home_relative_path(source_dir)}/`"

    files = [
        f"`{format_home_relative_path(file_path)}`"
        for file_path in sorted(source_dir.iterdir())
        if file_path.is_file() and not file_path.name.startswith(".")
    ]
    if not files:
        return f"`{format_home_relative_path(source_dir)}/`"
    return ", ".join(files)


def generate_guidelines_file_items() -> list[str]:
    """!
    @brief List the home-relative guideline entries reported after installation.
    @details Returns one home-relative path per non-hidden regular file in
    :func:`guidelines_dir`; when the directory is absent or empty, returns the home-relative
    directory itself with a trailing slash.
    @return {list[str]} Ordered home-relative guideline paths.
    @satisfies SRS-360, SRS-403
    """
    source_dir = guidelines_dir()
    if not source_dir.is_dir():
        return [f"{format_home_relative_path(source_dir)}/"]

    items = [
        format_home_relative_path(file_path)
        for file_path in sorted(source_dir.iterdir())
        if file_path.is_file() and not file_path.name.startswith(".")
    ]
    if not items:
        return [f"{format_home_relative_path(source_dir)}/"]
    return items


def ensure_relative(value: str, name: str, code: int) -> None:
    """!
    @brief Validates that the path is not absolute and raises an error otherwise.
    @details Implements the ensure_relative function behavior with deterministic control flow.
    @param value Input parameter `value`.
    @param name Input parameter `name`.
    @param code Input parameter `code`.
    @return {None} Function return value.
    """
    if Path(value).is_absolute():
        raise ReqError(
            f"Error: {name} must be a relative path under PROJECT_BASE",
            code,
        )


def apply_replacements(text: str, replacements: Mapping[str, str]) -> str:
    """!
    @brief Returns text with token replacements applied.
    @details Implements the apply_replacements function behavior with deterministic control flow.
    @param text Input parameter `text`.
    @param replacements Input parameter `replacements`.
    @return {str} Function return value.
    """
    for token, replacement in replacements.items():
        text = text.replace(token, replacement)
    return text


def write_text_file(dst: Path, text: str) -> None:
    """!
    @brief Writes text to disk, ensuring the destination folder exists.
    @details Implements the write_text_file function behavior with deterministic control flow.
    @param dst Input parameter `dst`.
    @param text Input parameter `text`.
    @return {None} Function return value.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def copy_with_replacements(
    src: Path, dst: Path, replacements: Mapping[str, str]
) -> None:
    """!
    @brief Copies a file substituting the indicated tokens with their values.
    @details Implements the copy_with_replacements function behavior with deterministic control flow.
    @param src Input parameter `src`.
    @param dst Input parameter `dst`.
    @param replacements Input parameter `replacements`.
    @return {None} Function return value.
    """
    text = src.read_text(encoding="utf-8")
    updated = apply_replacements(text, replacements)
    write_text_file(dst, updated)


def normalize_description(value: str) -> str:
    """!
    @brief Normalizes a description by removing superfluous quotes and escapes.
    @details Implements the normalize_description function behavior with deterministic control flow.
    @param value Input parameter `value`.
    @return {str} Function return value.
    """
    trimmed = value.strip()
    if len(trimmed) >= 2 and trimmed.startswith('"') and trimmed.endswith('"'):
        trimmed = trimmed[1:-1]
    if len(trimmed) >= 4 and trimmed.startswith('\\"') and trimmed.endswith('\\"'):
        trimmed = trimmed[2:-2]
    return trimmed.replace('\\"', '"')


def md_to_toml(md_path: Path, toml_path: Path, force: bool) -> None:
    """!
    @brief Converts a Markdown prompt to TOML for Gemini.
    @details Implements the md_to_toml function behavior with deterministic control flow.
    @param md_path Input parameter `md_path`.
    @param toml_path Input parameter `toml_path`.
    @param force Input parameter `force`.
    @return {None} Function return value.
    """
    if toml_path.exists() and not force:
        raise ReqError(
            f"Destination TOML already exists (use --force to overwrite): {toml_path}",
            3,
        )
    content = md_path.read_text(encoding="utf-8")
    match = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", content, re.S)
    if not match:
        raise ReqError("No leading '---' block found at start of Markdown file.", 4)
    frontmatter, rest = match.groups()
    desc = extract_description(frontmatter)
    desc_escaped = desc.replace("\\", "\\\\").replace('"', '\\"')
    rest_text = rest if rest.endswith("\n") else rest + "\n"
    toml_body = [
        f'description = "{desc_escaped}"',
        "",
        'prompt = """',
        rest_text,
        '"""',
        "",
    ]
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    toml_path.write_text("\n".join(toml_body), encoding="utf-8")
    dlog(f"Wrote TOML to: {toml_path}")


def extract_frontmatter(content: str) -> tuple[str, str]:
    """!
    @brief Extracts front matter and body from Markdown.
    @details Implements the extract_frontmatter function behavior with deterministic control flow.
    @param content Input parameter `content`.
    @return {tuple[str, str]} Function return value.
    """
    match = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", content, re.S)
    if not match:
        raise ReqError("No leading '---' block found at start of Markdown file.", 4)
    # Explicitly return two strings to satisfy type annotation.
    return match.group(1), match.group(2)


def extract_description(frontmatter: str) -> str:
    """!
    @brief Extracts the description from front matter.
    @details Implements the extract_description function behavior with deterministic control flow.
    @param frontmatter Input parameter `frontmatter`.
    @return {str} Function return value.
    """
    desc_match = re.search(r"^description:\s*(.*)$", frontmatter, re.M)
    if not desc_match:
        raise ReqError("No 'description:' field found inside the leading block.", 5)
    return normalize_description(desc_match.group(1).strip())


def extract_argument_hint(frontmatter: str) -> str:
    """!
    @brief Extracts the argument-hint from front matter, if present.
    @details Implements the extract_argument_hint function behavior with deterministic control flow.
    @param frontmatter Input parameter `frontmatter`.
    @return {str} Function return value.
    """
    match = re.search(r"^argument-hint:\s*(.*)$", frontmatter, re.M)
    if not match:
        return ""
    return normalize_description(match.group(1).strip())


def extract_purpose_first_bullet(body: str) -> str:
    """!
    @brief Returns the first bullet of the Purpose section.
    @details Implements the extract_purpose_first_bullet function behavior with deterministic control flow.
    @param body Input parameter `body`.
    @return {str} Function return value.
    """
    lines = body.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == "## purpose":
            start_idx = idx + 1
            break
    if start_idx is None:
        raise ReqError("Error: missing '## Purpose' section in prompt.", 7)
    for line in lines[start_idx:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        match = re.match(r"^\s*-\s+(.*)$", line)
        if match:
            return match.group(1).strip()
    raise ReqError("Error: no bullet found under the '## Purpose' section.", 7)


def _extract_section_text(body: str, section_name: str) -> str:
    """! @brief Extracts and collapses the text content of a named ## section.
    @details Scans `body` line by line for a heading matching `## <section_name>`
    (case-insensitive). Collects all subsequent non-empty lines until the next
    `##`-level heading (or end of string). Strips each line, joins with a single
    space, and returns the collapsed single-line result.
    @param[in] body str -- Full prompt body text (after front matter removal).
    @param[in] section_name str -- Target section name without `##` prefix (case-insensitive match).
    @return str -- Single-line collapsed text of the section; empty string if section absent or empty.
    """
    lines = body.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == f"## {section_name.lower()}":
            start_idx = idx + 1
            break
    if start_idx is None:
        return ""
    parts: list[str] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        if stripped:
            parts.append(" ".join(stripped.split()))
    return " ".join(parts)


def extract_skill_description(frontmatter: str) -> str:
    """! @brief Extracts the usage field from YAML front matter as a single YAML-safe line.
    @details Parses the YAML front matter and returns the `usage` field value with all
    whitespace normalized to a single line. Returns an empty string if the field is absent.
    @param[in] frontmatter str -- YAML front matter text (without the leading/trailing `---` delimiters).
    @return str -- Single-line text of the usage field; empty string if absent.
    """
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError:
        return ""
    if not isinstance(data, dict):
        return ""
    usage = data.get("usage", "")
    if not usage:
        return ""
    return " ".join(str(usage).split())


def replace_tokens(path: Path, replacements: Mapping[str, str]) -> None:
    """!
    @brief Replaces tokens in the specified file.
    @details Implements the replace_tokens function behavior with deterministic control flow.
    @param path Input parameter `path`.
    @param replacements Input parameter `replacements`.
    @return {None} Function return value.
    """
    text = path.read_text(encoding="utf-8")
    for token, replacement in replacements.items():
        text = text.replace(token, replacement)
    path.write_text(text, encoding="utf-8")


def yaml_double_quote_escape(value: str) -> str:
    """!
    @brief Minimal escape for a double-quoted string in YAML.
    @details Implements the yaml_double_quote_escape function behavior with deterministic control flow.
    @param value Input parameter `value`.
    @return {str} Function return value.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


def list_docs_templates() -> list[Path]:
    """!
    @brief Returns non-hidden files available in resources/docs.
        @return Sorted list of file paths under resources/docs.
        @throws ReqError If resources/docs does not exist or has no non-hidden files.
    @details Implements the list_docs_templates function behavior with deterministic control flow.
    """
    candidate = RESOURCE_ROOT / "docs"
    if not candidate.is_dir():
        raise ReqError("Error: no docs templates directory found in resources", 9)
    templates = sorted(
        path
        for path in candidate.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )
    if not templates:
        raise ReqError("Error: no docs templates found in resources/docs", 9)
    return templates


def find_requirements_template(docs_templates: list[Path]) -> Path:
    """!
    @brief Returns the packaged Requirements template file.
        @param docs_templates Runtime docs template file list from resources/docs.
        @return Path to `Requirements_Template.md`.
        @throws ReqError If `Requirements_Template.md` is not present.
    @details Implements the find_requirements_template function behavior with deterministic control flow.
    """
    for template_path in docs_templates:
        if template_path.name == REQUIREMENTS_TEMPLATE_NAME:
            return template_path
    raise ReqError(
        f"Error: no {REQUIREMENTS_TEMPLATE_NAME} template found in docs",
        9,
    )


def ensure_wrapped(target: Path, project_base: Path, code: int) -> None:
    """!
    @brief Verifies that the path is under the project root.
    @details Implements the ensure_wrapped function behavior with deterministic control flow.
    @param target Input parameter `target`.
    @param project_base Input parameter `project_base`.
    @param code Input parameter `code`.
    @return {None} Function return value.
    """
    if not target.resolve().is_relative_to(project_base):
        raise ReqError(
            f"Error: safe removal of {target} refused (not under PROJECT_BASE)",
            code,
        )


def prune_empty_dirs(root: Path) -> None:
    """!
    @brief Removes empty directories under the specified root.
    @details Implements the prune_empty_dirs function behavior with deterministic control flow.
    @param root Input parameter `root`.
    @return {None} Function return value.
    """
    if not root.is_dir():
        return
    for current, _dirs, _files in os.walk(root, topdown=False):
        current_path = Path(current)
        try:
            if not any(current_path.iterdir()):
                current_path.rmdir()
        except OSError:
            continue

def remove_generated_resources() -> None:
    """!
    @brief Removes `req-*` artifacts generated by the tool from user-level provider directories.
    @details Loads the persisted `providers` array from the user-global configuration file,
    resolves each enabled provider/artifact user-level root via :func:`provider_artifact_root`,
    and deletes only `req-*` files and `req-*` skill directories. Empty user-level provider
    subdirectories are pruned afterwards; unrelated user content is never touched.
    @return {None} Function return value.
    @satisfies SRS-390
    """
    specs = load_persisted_provider_specs()
    configs = resolve_provider_configs(specs)
    for provider, cfg in configs.items():
        if not cfg.get("enabled"):
            continue
        for artifact in sorted(VALID_ARTIFACTS):
            if not cfg.get(artifact):
                continue
            root = provider_artifact_root(provider, artifact)
            if not root.is_dir():
                continue
            if root.name == "req":
                # usereq-owned namespace directory (e.g. ~/.claude/commands/req):
                # all content inside is generated by this tool, so remove it entirely.
                for path in sorted(root.iterdir()):
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.is_file():
                        path.unlink()
                continue
            for path in sorted(root.iterdir()):
                if not path.name.startswith("req-"):
                    continue
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
    for provider in sorted(VALID_PROVIDERS):
        cfg = configs[provider]
        if not cfg.get("enabled"):
            continue
        for artifact in sorted(VALID_ARTIFACTS):
            if not cfg.get(artifact):
                continue
            root = provider_artifact_root(provider, artifact)
            if root.is_dir():
                prune_empty_dirs(root)

def _render_simple_table(headers: list[str], rows: list[list[str]]) -> str:
    """!
    @brief Render one Unicode box-drawing table from headers and rows.
    @param headers {list[str]} Column header labels.
    @param rows {list[list[str]]} Cell values per row; every row matches the header count.
    @return {str} Multi-line table with `│` separators and `─` borders, no ANSI styling.
    @details Pure deterministic formatting used by the `show` subcommand (SRS-416, SRS-417).
    """
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _line(cells: list[str]) -> str:
        return (
            "│ "
            + " │ ".join(
                cell.ljust(widths[index]) for index, cell in enumerate(cells)
            )
            + " │"
        )

    def _border(left: str, middle: str, right: str) -> str:
        return left + middle.join("─" * (width + 2) for width in widths) + right

    lines = [_border("┌", "┬", "┐"), _line(headers), _border("├", "┼", "┤")]
    lines.extend(_line(row) for row in rows)
    lines.append(_border("└", "┴", "┘"))
    return "\n".join(lines)


def _provider_artifact_installed(provider: str, artifact: str) -> bool:
    """!
    @brief Detect whether at least one `req-*` artifact exists for a provider component.
    @param provider {str} Provider selector from `{antigravity, claude, codex, opencode, pi}`.
    @param artifact {str} Artifact selector from `{prompts, agents, skills}`.
    @return {bool} True when the provider/artifact user-level root contains a `req-*` entry.
    @details Installation status detection for the `show` subcommand (SRS-417); unsupported
    provider/artifact pairs and absent roots report `False`.
    @satisfies SRS-417
    """
    try:
        root = provider_artifact_root(provider, artifact)
    except ReqError:
        return False
    if not root.is_dir():
        return False
    return any(entry.name.startswith("req-") for entry in root.iterdir())


def run_install(args: Namespace) -> None:
    """!
    @brief Execute install: install or update the persisted providers globally.
    @param args Parsed CLI namespace; `--prj-base` is optional (SRS-447).
    @return {None} Function return value.
    @details Delegates to the config-driven installation flow (SRS-035, SRS-064, SRS-418)
    which requires at least one enabled provider and prints the installation summary
    report (SRS-049). When `--prj-base` is absent, project-side scaffold, validation,
    and persistence are skipped (SRS-448); when provided, the combined flow executes
    (SRS-449).
    @throws ReqError If no provider is enabled.
    @satisfies SRS-035, SRS-064, SRS-418, SRS-447, SRS-448, SRS-449
    """
    run(args)


def run_uninstall_providers(args: Namespace) -> None:
    """!
    @brief Execute uninstall: remove artifacts of the configured providers.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @details Requires the user-global configuration file and removes `req-*` artifacts of
    the providers persisted under `"providers"` (SRS-390, SRS-419).
    @throws ReqError If the global configuration file is missing.
    @satisfies SRS-419
    """
    if not get_global_config_path().is_file():
        raise ReqError(
            f"Error: global configuration file not found at {get_global_config_path()}",
            11,
        )
    remove_generated_resources()


def run_show(args: Namespace) -> None:
    """!
    @brief Execute show: print the active configuration as tables.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @details Prints the effective configuration table (`docs-dir`, `tests-dir`, `src-dir`,
    `auto-install`), the provider enablement table, one dedicated component
    installation-status table per enabled provider (SRS-417), and the enabled
    static-check entries (SRS-416).
    @throws ReqError If persisted provider SPECs are invalid.
    @satisfies SRS-416, SRS-417, SRS-420
    """
    config = load_config()
    doc_dir_value = str(config["docs-dir"])
    test_dir_value = str(config["tests-dir"])
    src_dir_value = ", ".join(str(item) for item in config["src-dir"])
    auto_install_state = (
        "enabled" if load_auto_install_enabled() else "disabled"
    )
    print("Active Configuration")
    print(
        _render_simple_table(
            ["Setting", "Value"],
            [
                ["docs-dir", doc_dir_value],
                ["tests-dir", test_dir_value],
                ["src-dir", src_dir_value],
                ["auto-install", auto_install_state],
            ],
        )
    )

    persisted_specs = load_persisted_provider_specs()
    provider_configs = resolve_provider_configs(persisted_specs)
    print()
    print("Providers")
    print(
        _render_simple_table(
            ["Provider", "Status"],
            [
                [
                    name,
                    "enabled" if provider_configs[name]["enabled"] else "disabled",
                ]
                for name in sorted(VALID_PROVIDERS)
            ],
        )
    )
    for name in sorted(VALID_PROVIDERS):
        provider_cfg = provider_configs[name]
        if not provider_cfg["enabled"]:
            continue
        print()
        print(f"Provider {name}")
        component_rows = [
            [
                artifact,
                "yes" if provider_cfg[artifact] else "no",
                (
                    "installed"
                    if _provider_artifact_installed(name, artifact)
                    else "not installed"
                ),
            ]
            for artifact in sorted(VALID_ARTIFACTS)
        ]
        print(
            _render_simple_table(
                ["Component", "Configured", "Status"], component_rows
            )
        )

    sc_config = load_static_check_from_config()
    sc_rows = [
        [
            lang,
            str(entry.get("module", "")),
            str(entry.get("cmd", "")),
            " ".join(str(param) for param in entry.get("params", [])),
        ]
        for lang in sorted(sc_config)
        for entry in sc_config.get(lang, [])
        if isinstance(entry, dict)
    ]
    print()
    print("Static Checks")
    if sc_rows:
        print(
            _render_simple_table(
                ["Language", "Module", "Cmd", "Params"], sc_rows
            )
        )
    else:
        print("(none)")


def _maybe_auto_install_after_upgrade(argv_list: list[str]) -> None:
    """!
    @brief Run the provider installation flow after a successful `--upgrade`.
    @param argv_list {list[str]} Raw CLI argument vector of the `--upgrade` invocation.
    @return {None} Function return value.
    @details Executes the `install` flow with persisted providers when `auto-install` is
    enabled (SRS-420, SRS-421) regardless of `--prj-base` presence; prints an English
    stderr warning and skips when no provider is enabled (SRS-450).
    @satisfies SRS-420, SRS-421, SRS-450
    """
    if not load_auto_install_enabled():
        return
    if not load_persisted_provider_specs():
        print(
            "Warning: no enabled providers in ~/.config/usereq/config.json; skipping auto-install after upgrade.",
            file=sys.stderr,
        )
        return
    try:
        args = parse_args(argv_list)
    except SystemExit:
        return
    run_install(args)


def run_set_directories(args: Namespace) -> None:
    """!
    @brief Persist `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` values.
    @details Requires `--prj-base` (SRS-396), normalizes each supplied path against the
    project base, rejects absolute or escaping paths, and writes only the supplied keys to
    `~/.config/usereq/config.json` while preserving unrelated keys (SRS-398, SRS-399,
    SRS-400, SRS-401). No project directory is created and no provider artifact is generated.
    @param args Parsed CLI namespace carrying the `set_docs_dir`, `set_src_dir`, and
      `set_tests_dir` values.
    @return {None} Function return value.
    @throws ReqError If `--prj-base` is absent or a supplied path escapes the project base.
    @satisfies SRS-396, SRS-398, SRS-399, SRS-400, SRS-401
    """
    project_base = _require_prj_base(args)

    docs_value = getattr(args, "set_docs_dir", None)
    tests_value = getattr(args, "set_tests_dir", None)
    src_values = getattr(args, "set_src_dir", None)

    normalized_docs: Optional[str] = None
    if docs_value is not None:
        normalized_docs = make_relative_if_contains_project(
            docs_value, project_base
        ).rstrip("/\\")
        ensure_relative(normalized_docs, "DOCS_DIR", 4)
        abs_docs = resolve_absolute(normalized_docs, project_base)
        if abs_docs and not abs_docs.resolve().is_relative_to(project_base):
            raise ReqError("Error: docs-dir must be under the project base", 4)

    normalized_tests: Optional[str] = None
    if tests_value is not None:
        normalized_tests = make_relative_if_contains_project(
            tests_value, project_base
        ).rstrip("/\\")
        ensure_relative(normalized_tests, "TESTS_DIR", 4)
        abs_tests = resolve_absolute(normalized_tests, project_base)
        if abs_tests and not abs_tests.resolve().is_relative_to(project_base):
            raise ReqError("Error: tests-dir must be under the project base", 4)

    normalized_srcs: Optional[list[str]] = None
    if src_values:
        normalized_srcs = []
        for src_value in src_values:
            normalized_src = make_relative_if_contains_project(
                src_value, project_base
            ).rstrip("/\\")
            ensure_relative(normalized_src, "SRC_DIR", 4)
            abs_src = resolve_absolute(normalized_src, project_base)
            if abs_src and not abs_src.resolve().is_relative_to(project_base):
                raise ReqError("Error: src-dir must be under the project base", 4)
            normalized_srcs.append(normalized_src)

    update_directory_config(
        docs_dir_value=normalized_docs,
        tests_dir_value=normalized_tests,
        src_dir_values=normalized_srcs,
    )
    if docs_value is not None:
        log(f"OK: docs-dir set to {normalized_docs}")
    if tests_value is not None:
        log(f"OK: tests-dir set to {normalized_tests}")
    if normalized_srcs is not None:
        log(f"OK: src-dir set to {', '.join(normalized_srcs)}")

def _validate_enable_static_check_command_executables(
    static_check_config: Mapping[str, list[dict[str, Any]]],
    *,
    enforce: bool,
) -> None:
    """!
        @brief Validate Command-module executables in `--enable-static-check` parsed entries.
        @param static_check_config Parsed static-check entries grouped by canonical language.
        @param enforce When false, skip validation and return immediately.
        @throws ReqError If a Command entry references a non-executable `cmd` on this system.
        @details
          Validation scope is limited to Command entries coming from CLI specs.
          Each Command `cmd` is resolved with `shutil.which`; on miss, raises `ReqError(code=1)`
          before any configuration persistence.
        @see SRS-250
    @return {None} Function return value.
    """
    if not enforce:
        return
    for entries in static_check_config.values():
        for entry in entries:
            if entry.get("module") != "Command":
                continue
            cmd_raw = entry.get("cmd")
            cmd = cmd_raw.strip() if isinstance(cmd_raw, str) else ""
            if not cmd or shutil.which(cmd) is None:
                raise ReqError(
                    f"Error: --enable-static-check Command cmd '{cmd or '<missing>'}' is not an executable program on this system.",
                    1,
                )


def run(args: Namespace) -> None:
    """!
    @brief Handles the main installation/update flow for persisted providers.
    @details Treats `--prj-base` as optional (SRS-447, SRS-418): loads the persisted
    `"providers"` specs from `~/.config/usereq/config.json` (SRS-064, SRS-279) and
    requires at least one enabled provider (SRS-035), orchestrates user-level provider
    artifact generation with home-relative GUIDELINES_DIR token substitution
    (SRS-402, SRS-403), and preserves the persisted static-check and auto-install
    configuration (SRS-288, SRS-301, SRS-420). When `--prj-base` is provided, it
    additionally loads the `docs-dir`, `tests-dir`, and `src-dir` values from the
    user-global configuration with defaults `usereq`, `tests`, and `src` (SRS-359,
    SRS-361, SRS-362), creates missing directories during installation (SRS-363),
    validates containment under the project base, persists the effective directory
    values, and rewrites the global configuration (SRS-288, SRS-301, SRS-420, SRS-407);
    when `--prj-base` is absent, all project-side operations are skipped (SRS-448).
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @throws ReqError If no provider is enabled or configured paths are invalid.
    @satisfies SRS-035, SRS-064, SRS-251, SRS-279, SRS-288, SRS-301, SRS-359, SRS-361, SRS-362, SRS-363, SRS-381, SRS-387, SRS-388, SRS-396, SRS-402, SRS-403, SRS-407, SRS-418, SRS-447, SRS-448, SRS-449
    """
    global VERBOSE, DEBUG
    VERBOSE = getattr(args, "verbose", False)
    DEBUG = getattr(args, "debug", False)

    # Main flow: validates input, calculates paths, generates user-level resources.
    # `--prj-base` is optional for install (SRS-447): when absent, project-side
    # scaffold, containment validation, and directory persistence are skipped (SRS-448).
    project_base: Optional[Path] = None
    normalized_doc = ""
    normalized_test = ""
    normalized_src_dirs: list[str] = []
    if getattr(args, "prj_base", None) is not None:
        project_base = _resolve_project_base(args)

        config = load_config()
        doc_dir_value = config["docs-dir"]
        test_dir_value = config["tests-dir"]
        src_dir_values = config["src-dir"]

        if not isinstance(doc_dir_value, str):
            raise ReqError("Error: invalid docs configuration values", 11)
        if not isinstance(test_dir_value, str):
            raise ReqError("Error: invalid tests configuration value", 11)
        if (
            not isinstance(src_dir_values, list)
            or not src_dir_values
            or not all(isinstance(value, str) for value in src_dir_values)
        ):
            raise ReqError("Error: invalid src configuration values", 11)

        create_missing_dirs = True
        ensure_doc_directory(
            doc_dir_value, project_base, create_missing=create_missing_dirs
        )
        ensure_test_directory(
            test_dir_value, project_base, create_missing=create_missing_dirs
        )
        for src_dir_value in src_dir_values:
            ensure_src_directory(
                src_dir_value, project_base, create_missing=create_missing_dirs
            )

        normalized_doc = make_relative_if_contains_project(
            doc_dir_value, project_base
        ).rstrip("/\\")
        normalized_test = make_relative_if_contains_project(
            test_dir_value, project_base
        ).rstrip("/\\")
        for src_dir_value in src_dir_values:
            normalized_src = make_relative_if_contains_project(
                src_dir_value, project_base
            )
            normalized_src_dirs.append(normalized_src.rstrip("/\\"))

        ensure_relative(normalized_doc, "DOCS_DIR", 4)
        ensure_relative(normalized_test, "TESTS_DIR", 4)
        for normalized_src in normalized_src_dirs:
            ensure_relative(normalized_src, "SRC_DIR", 4)

        abs_doc = resolve_absolute(normalized_doc, project_base)
        abs_test = resolve_absolute(normalized_test, project_base)
        abs_src_dirs = [
            resolve_absolute(normalized_src, project_base)
            for normalized_src in normalized_src_dirs
        ]
        if abs_doc and not abs_doc.resolve().is_relative_to(project_base):
            raise ReqError("Error: docs-dir must be under the project base", 5)
        if abs_test and not abs_test.resolve().is_relative_to(project_base):
            raise ReqError("Error: tests-dir must be under the project base", 5)
        for abs_src in abs_src_dirs:
            if abs_src and not abs_src.resolve().is_relative_to(project_base):
                raise ReqError("Error: src-dir must be under the project base", 5)

    # Resolve persisted provider specs (SRS-064, SRS-279); installation is config-driven.
    effective_provider_specs = load_persisted_provider_specs()
    # Validate all specs (will raise ReqError on invalid tokens, SRS-278).
    for spec_str in effective_provider_specs:
        parse_provider_spec(spec_str)
    # Resolve per-provider configs (spec-driven only, SRS-275).
    provider_configs = resolve_provider_configs(effective_provider_specs)

    # Derive flat enable_* variables from per-provider configs (spec-driven only).
    enable_antigravity = provider_configs["antigravity"]["enabled"]
    enable_claude = provider_configs["claude"]["enabled"]
    enable_codex = provider_configs["codex"]["enabled"]
    enable_opencode = provider_configs["opencode"]["enabled"]
    enable_pi = provider_configs["pi"]["enabled"]

    # A provider's artifacts are enabled only via the per-provider spec.
    enable_prompts = any(pc["prompts"] for pc in provider_configs.values())
    enable_agents = any(pc["agents"] for pc in provider_configs.values())
    enable_skills = any(pc["skills"] for pc in provider_configs.values())

    if not any(
        (
            enable_antigravity,
            enable_claude,
            enable_codex,
            enable_opencode,
            enable_pi,
        )
    ):
        parser = build_parser()
        parser.print_help()
        raise ReqError(
            "Error: at least one enabled provider is required in ~/.config/usereq/config.json (configure it with --enable SPEC)",
            4,
        )
    if not any((enable_prompts, enable_agents, enable_skills)):
        parser = build_parser()
        parser.print_help()
        raise ReqError(
            "Error: at least one enabled provider with artifact types is required in ~/.config/usereq/config.json",
            4,
        )

    # Preserve the persisted static-check configuration unchanged; an absent key stays
    # absent so the SRS-424 defaults keep tracking tool upgrades (SRS-301, SRS-415, SRS-424).
    try:
        raw_payload = _read_config_payload()
    except ReqError:
        raw_payload = {}
    persisted_sc = raw_payload.get("static-check")
    merged_static_check = persisted_sc if isinstance(persisted_sc, dict) else None

    if project_base is not None:
        # Persist the single user-global configuration file (SRS-279, SRS-288, SRS-407).
        save_config(
            normalized_doc,
            normalized_test,
            normalized_src_dirs,
            static_check_config=merged_static_check if merged_static_check else None,
            provider_specs=effective_provider_specs
            if effective_provider_specs
            else None,
        )

    # Resolve the installation-owned guidelines substitution values (SRS-360, SRS-402, SRS-403).
    guidelines_file_list = generate_guidelines_file_list()
    guidelines_path_value = f"{format_home_relative_path(guidelines_dir())}/"

    dlog(f"project_base={project_base}")
    dlog(f"DOCS_DIR={normalized_doc}")
    dlog(f"GUIDELINES_DIR={guidelines_path_value}")
    dlog(f"TESTS_DIR={normalized_test}")
    dlog(f"SRC_DIRS={normalized_src_dirs}")
    dlog(f"GUIDELINES_FILE_LIST={guidelines_file_list}")

    # Resolve user-level provider artifact roots under the user HOME (SRS-381..SRS-386).
    skills_roots: dict[str, Path] = {}
    target_folders: list[Path] = []
    for provider_name, provider_cfg in provider_configs.items():
        if not provider_cfg["enabled"]:
            continue
        for artifact_name in sorted(VALID_ARTIFACTS):
            if not provider_cfg[artifact_name]:
                continue
            try:
                root = provider_artifact_root(provider_name, artifact_name)
            except ReqError:
                continue
            if artifact_name == "skills":
                skills_roots[provider_name] = root
            else:
                target_folders.append(root)
    for folder in target_folders:
        folder.mkdir(parents=True, exist_ok=True)
    for skills_root in skills_roots.values():
        skills_root.mkdir(parents=True, exist_ok=True)
    if VERBOSE:
        log(
            "OK: ensured user-level provider folders for the requested target CLIs under "
            f"{home_dir()}"
        )

    prompts_dir = RESOURCE_ROOT / "prompts"
    if not prompts_dir.is_dir():
        raise ReqError(
            f"Error: prompts directory not found at {prompts_dir} (RESOURCE_ROOT/prompts required)",
            9,
        )
    prompts_installed: dict[str, set[str]] = {
        "antigravity": set(),
        "claude": set(),
        "codex": set(),
        "opencode": set(),
        "pi": set(),
    }
    modules_installed: dict[str, set[str]] = {
        key: set() for key in prompts_installed.keys()
    }
    prompt_sources: list[tuple[str, Path]] = [
        *[("prompts", path) for path in sorted(prompts_dir.glob("*.md"))],
    ]
    for source_kind, prompt_path in prompt_sources:
        is_prompt_source = source_kind == "prompts"
        PROMPT = prompt_path.stem
        content = prompt_path.read_text(encoding="utf-8")
        frontmatter, prompt_body = extract_frontmatter(content)
        description = extract_description(frontmatter)
        argument_hint = extract_argument_hint(frontmatter)
        prompt_body = prompt_body if prompt_body.endswith("\n") else prompt_body + "\n"

        base_replacements = {
            "%%GUIDELINES_FILES%%": guidelines_file_list,
            "%%GUIDELINES_PATH%%": guidelines_path_value,
        }
        prompt_replacements = {
            **base_replacements,
            "%%ARGS%%": "$ARGUMENTS",
        }
        prompt_with_replacements = apply_replacements(content, prompt_replacements)
        prompt_body_replaced = apply_replacements(prompt_body, prompt_replacements)

        # Precompute description metadata so provider blocks can reuse them safely.
        desc_yaml = yaml_double_quote_escape(description)
        skill_desc_yaml = yaml_double_quote_escape(
            extract_skill_description(frontmatter)
        )

        pc_antigravity = provider_configs["antigravity"]
        pc_claude = provider_configs["claude"]
        pc_codex = provider_configs["codex"]
        pc_opencode = provider_configs["opencode"]
        pc_pi = provider_configs["pi"]

        if is_prompt_source and pc_codex["enabled"] and pc_codex["prompts"]:
            # ~/.codex/prompts
            dst_codex_prompt = provider_artifact_root("codex", "prompts") / f"req-{PROMPT}.md"
            existed = dst_codex_prompt.exists()
            write_text_file(dst_codex_prompt, prompt_with_replacements)
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_codex_prompt}")
            prompts_installed["codex"].add(PROMPT)
            modules_installed["codex"].add("prompts")

        if pc_codex["enabled"] and pc_codex["skills"]:
            # ~/.codex/skills/req-<prompt>/SKILL.md
            codex_skill_dir = skills_roots["codex"] / f"req-{PROMPT}"
            codex_skill_dir.mkdir(parents=True, exist_ok=True)
            codex_skill_text = (
                "---\n"
                f"name: req-{PROMPT}\n"
                f'description: "{skill_desc_yaml}"\n'
                "---\n\n" + prompt_body_replaced
            )
            if not codex_skill_text.endswith("\n"):
                codex_skill_text += "\n"
            write_text_file(codex_skill_dir / "SKILL.md", codex_skill_text)
            prompts_installed["codex"].add(PROMPT)
            modules_installed["codex"].add("skills")

        if is_prompt_source and pc_antigravity["enabled"] and pc_antigravity["prompts"]:
            # ~/.antigravity/commands/req/<PROMPT>.toml (Antigravity TOML command)
            dst_toml = (
                provider_artifact_root("antigravity", "prompts") / f"{PROMPT}.toml"
            )
            existed = dst_toml.exists()
            md_to_toml(prompt_path, dst_toml, force=existed)
            toml_replacements = {
                "%%GUIDELINES_FILES%%": guidelines_file_list,
                "%%GUIDELINES_PATH%%": guidelines_path_value,
                "%%ARGS%%": "{{args}}",
            }
            replace_tokens(dst_toml, toml_replacements)
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_toml}")
            prompts_installed["antigravity"].add(PROMPT)
            modules_installed["antigravity"].add("commands")

        if is_prompt_source and pc_claude["enabled"] and pc_claude["agents"]:
            # ~/.claude/agents
            dst_claude_agent = provider_artifact_root("claude", "agents") / f"req-{PROMPT}.md"
            existed = dst_claude_agent.exists()
            claude_header_lines = [
                "---",
                f"name: req-{PROMPT}",
                f'description: "{desc_yaml}"',
            ]
            claude_text = (
                "\n".join(claude_header_lines) + "\n---\n\n" + prompt_body_replaced
            )
            dst_claude_agent.parent.mkdir(parents=True, exist_ok=True)
            if not claude_text.endswith("\n"):
                claude_text += "\n"
            dst_claude_agent.write_text(claude_text, encoding="utf-8")
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_claude_agent}")
            prompts_installed["claude"].add(PROMPT)
            modules_installed["claude"].add("agents")

        if is_prompt_source and pc_pi["enabled"] and pc_pi["prompts"]:
            # ~/.pi/agent/prompts/req-<PROMPT>.prompt.md
            dst_pi_prompt = (
                provider_artifact_root("pi", "prompts") / f"req-{PROMPT}.prompt.md"
            )
            existed = dst_pi_prompt.exists()
            if pc_pi["prompts-use-agents"]:
                pi_prompt_text = f"---\nagent: req-{PROMPT}\n---\n"
            else:
                pi_header_lines = [
                    "---",
                    f"description: {frontmatter.splitlines()[0].split(':', 1)[1].strip() if 'description:' in frontmatter else description}",
                ]
                if argument_hint:
                    pi_header_lines.append(f"argument-hint: {argument_hint}")
                pi_header = "\n".join(pi_header_lines) + "\n---\n\n"
                pi_prompt_text = pi_header + prompt_body_replaced
            dst_pi_prompt.parent.mkdir(parents=True, exist_ok=True)
            dst_pi_prompt.write_text(pi_prompt_text, encoding="utf-8")
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_pi_prompt}")
            prompts_installed["pi"].add(PROMPT)
            modules_installed["pi"].add("prompts")

        if is_prompt_source and pc_opencode["enabled"] and pc_opencode["agents"]:
            # ~/.config/opencode/agent
            dst_opencode_agent = (
                provider_artifact_root("opencode", "agents") / f"req-{PROMPT}.md"
            )
            existed = dst_opencode_agent.exists()
            opencode_header_lines = ["---", f'description: "{desc_yaml}"', "mode: all"]
            opencode_text = (
                "\n".join(opencode_header_lines) + "\n---\n\n" + prompt_body_replaced
            )
            dst_opencode_agent.parent.mkdir(parents=True, exist_ok=True)
            if not opencode_text.endswith("\n"):
                opencode_text += "\n"
            dst_opencode_agent.write_text(opencode_text, encoding="utf-8")
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_opencode_agent}")
            prompts_installed["opencode"].add(PROMPT)
            modules_installed["opencode"].add("agent")

        if is_prompt_source and pc_opencode["enabled"] and pc_opencode["prompts"]:
            # ~/.config/opencode/command
            dst_opencode_command = (
                provider_artifact_root("opencode", "prompts") / f"req-{PROMPT}.md"
            )
            existed = dst_opencode_command.exists()
            if pc_opencode["prompts-use-agents"]:
                command_text = f"---\nagent: req-{PROMPT}\n---\n"
            else:
                command_header_lines = [
                    "---",
                    f'description: "{desc_yaml}"',
                ]
                if argument_hint:
                    command_header_lines.append(
                        f'argument-hint: "{yaml_double_quote_escape(argument_hint)}"'
                    )
                command_text = (
                    "\n".join(command_header_lines) + "\n---\n\n" + prompt_body_replaced
                )
            dst_opencode_command.parent.mkdir(parents=True, exist_ok=True)
            if not command_text.endswith("\n"):
                command_text += "\n"
            dst_opencode_command.write_text(command_text, encoding="utf-8")
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_opencode_command}")
            prompts_installed["opencode"].add(PROMPT)
            modules_installed["opencode"].add("command")

        if is_prompt_source and pc_claude["enabled"] and pc_claude["prompts"]:
            # ~/.claude/commands/req
            dst_claude_command = (
                provider_artifact_root("claude", "prompts") / f"{PROMPT}.md"
            )
            existed = dst_claude_command.exists()
            if pc_claude["prompts-use-agents"]:
                command_header_lines = ["---", f"agent: req-{PROMPT}"]
                claude_command_text = "\n".join(command_header_lines) + "\n---\n"
            else:
                command_header_lines = ["---"]
                if description:
                    command_header_lines.append(f'description: "{desc_yaml}"')
                if argument_hint:
                    command_header_lines.append(
                        f'argument-hint: "{yaml_double_quote_escape(argument_hint)}"'
                    )
                claude_command_text = (
                    "\n".join(command_header_lines) + "\n---\n\n" + prompt_body_replaced
                )
            dst_claude_command.parent.mkdir(parents=True, exist_ok=True)
            if not claude_command_text.endswith("\n"):
                claude_command_text += "\n"
            dst_claude_command.write_text(claude_command_text, encoding="utf-8")
            if VERBOSE:
                log(f"{'OVERWROTE' if existed else 'COPIED'}: {dst_claude_command}")
            prompts_installed["claude"].add(PROMPT)
            modules_installed["claude"].add("commands")

        if pc_claude["enabled"] and pc_claude["skills"]:
            # ~/.claude/skills/req-<prompt>/SKILL.md
            claude_skill_dir = skills_roots["claude"] / f"req-{PROMPT}"
            claude_skill_dir.mkdir(parents=True, exist_ok=True)
            claude_skill_text = (
                "---\n"
                f"name: req-{PROMPT}\n"
                f'description: "{skill_desc_yaml}"\n'
                "---\n\n" + prompt_body_replaced
            )
            if not claude_skill_text.endswith("\n"):
                claude_skill_text += "\n"
            write_text_file(claude_skill_dir / "SKILL.md", claude_skill_text)
            prompts_installed["claude"].add(PROMPT)
            modules_installed["claude"].add("skills")

        if pc_antigravity["enabled"] and pc_antigravity["skills"]:
            # ~/.antigravity/skills/req-<prompt>/SKILL.md
            antigravity_skill_dir = skills_roots["antigravity"] / f"req-{PROMPT}"
            antigravity_skill_dir.mkdir(parents=True, exist_ok=True)
            antigravity_skill_text = (
                "---\n"
                f"name: req-{PROMPT}\n"
                f'description: "{skill_desc_yaml}"\n'
                "---\n\n" + prompt_body_replaced
            )
            if not antigravity_skill_text.endswith("\n"):
                antigravity_skill_text += "\n"
            write_text_file(
                antigravity_skill_dir / "SKILL.md", antigravity_skill_text
            )
            prompts_installed["antigravity"].add(PROMPT)
            modules_installed["antigravity"].add("skills")

        if pc_pi["enabled"] and pc_pi["skills"]:
            # ~/.pi/agent/skills/req-<prompt>/SKILL.md
            pi_skill_dir = skills_roots["pi"] / f"req-{PROMPT}"
            pi_skill_dir.mkdir(parents=True, exist_ok=True)
            pi_skill_text = (
                "---\n"
                f"name: req-{PROMPT}\n"
                f'description: "{skill_desc_yaml}"\n'
                "---\n\n" + prompt_body_replaced
            )
            if not pi_skill_text.endswith("\n"):
                pi_skill_text += "\n"
            write_text_file(pi_skill_dir / "SKILL.md", pi_skill_text)
            prompts_installed["pi"].add(PROMPT)
            modules_installed["pi"].add("skills")

        if pc_opencode["enabled"] and pc_opencode["skills"]:
            # ~/.config/opencode/skill/req-<prompt>/SKILL.md
            opencode_skill_dir = skills_roots["opencode"] / f"req-{PROMPT}"
            opencode_skill_dir.mkdir(parents=True, exist_ok=True)
            opencode_skill_text = (
                "---\n"
                f"name: req-{PROMPT}\n"
                f'description: "{skill_desc_yaml}"\n'
                "---\n\n" + prompt_body_replaced
            )
            if not opencode_skill_text.endswith("\n"):
                opencode_skill_text += "\n"
            write_text_file(opencode_skill_dir / "SKILL.md", opencode_skill_text)
            prompts_installed["opencode"].add(PROMPT)
            modules_installed["opencode"].add("skills")

    # Final success notification: printed only when the command completed all
    # intended filesystem modifications without raising an exception.
    try:
        resolved_home = str(home_dir().resolve())
    except Exception:
        resolved_home = str(home_dir())
    print(f"Installation completed successfully in {resolved_home}")

    # Print the discovered directories used for token substitutions
    # as required by REQ-078: one item per line prefixed with '- '.
    guidelines_items = generate_guidelines_file_items()

    if guidelines_items:
        for entry in guidelines_items:
            print(f"- {entry}")
    else:
        print("The folder %%GUIDELINES_FILES%% does not contain any files")


    # Build and print installation report table with provider artifact/options details.
    def _format_install_table(
        modules_map: dict[str, list[str]],
        prompts_map: dict[str, set[str]],
    ) -> list[str]:
        """!
        @brief Format the Unicode installation summary table.
        @details Builds a deterministic box-drawing table with columns: Provider, Prompts Installed, Modules Installed.
        Prompts Installed is wrapped to a maximum width of 50 characters. Modules Installed renders one non-wrapped
        line per active artifact item as `artifact` when no artifact-local or applicable provider-scoped options are active, or `artifact:options` when one or more such options are active.
        Borders are emitted with Unicode line-drawing characters and bright-red ANSI styling.
        @note Complexity: O(C * (P log P + M)) where C is provider count, P is prompts per provider, M is module-entry lines per provider.
        @note Side effects: None (pure formatting).
        @param modules_map {dict[str, list[str]]} Mapping: provider name -> module-entry lines in `artifact` or `artifact:options` format.
        @param prompts_map {dict[str, set[str]]} Mapping: provider name -> installed prompt identifiers (union across artifact types).
        @return {list[str]} Fully formatted table lines (including separators) ready for printing.
        """
        columns = ("Provider", "Prompts Installed", "Modules Installed")
        rows: list[tuple[str, str, str]] = []
        for provider_name in sorted(prompts_map.keys()):
            prompts = sorted(prompts_map.get(provider_name, ()))
            if not prompts:
                continue
            prompts_text = ", ".join(prompts) if prompts else "-"
            module_lines = modules_map.get(provider_name, [])
            modules_text = "\n".join(module_lines) if module_lines else "-"
            rows.append((provider_name, prompts_text, modules_text))

        if not rows:
            rows = [("-", "-", "-")]

        provider_width = max(len(columns[0]), max(len(row[0]) for row in rows))
        prompt_cells = [columns[1], *[row[1] for row in rows]]
        prompt_width = min(50, max(len(cell) for cell in prompt_cells))
        modules_width = len(columns[2])
        for row in rows:
            modules_width = max(
                modules_width, max(len(line) for line in row[2].splitlines() or [""])
            )

        def _wrap_cell(value: str, width: int, allow_wrap: bool) -> list[str]:
            """! @brief Normalize one table cell to printable lines.
            @details Preserves explicit newline-separated segments. When wrapping is enabled, wraps each segment to the target width; otherwise keeps each segment as-is.
            @param value {str} Cell text payload.
            @param width {int} Maximum cell width.
            @param allow_wrap {bool} Whether to apply line wrapping.
            @return {list[str]} Normalized printable lines for the cell.
            """
            raw_lines = value.splitlines() or [""]
            lines: list[str] = []
            for raw_line in raw_lines:
                if allow_wrap:
                    wrapped = textwrap.wrap(
                        raw_line,
                        width=width,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                    lines.extend(wrapped if wrapped else [""])
                else:
                    lines.append(raw_line)
            return lines if lines else [""]

        def _render_row(provider: str, prompts: str, modules: str) -> list[str]:
            """!
            @brief Render one logical table row into one or more physical lines.
            @details Applies per-cell wrapping and left alignment, then expands the row height to the maximum wrapped cell line count.
            @param provider {str} Provider cell text.
            @param prompts {str} Prompts Installed cell text.
            @param modules {str} Modules Installed cell text.
            @return {list[str]} Physical row lines encoded with box-drawing separators.
            """
            provider_lines = _wrap_cell(provider, provider_width, allow_wrap=False)
            prompt_lines = _wrap_cell(prompts, prompt_width, allow_wrap=True)
            module_lines = _wrap_cell(modules, modules_width, allow_wrap=False)
            row_height = max(len(provider_lines), len(prompt_lines), len(module_lines))
            lines: list[str] = []
            for idx in range(row_height):
                provider_part = (
                    provider_lines[idx] if idx < len(provider_lines) else ""
                ).ljust(provider_width)
                prompt_part = (
                    prompt_lines[idx] if idx < len(prompt_lines) else ""
                ).ljust(prompt_width)
                module_part = (
                    module_lines[idx] if idx < len(module_lines) else ""
                ).ljust(modules_width)
                lines.append(f"│ {provider_part} │ {prompt_part} │ {module_part} │")
            return lines

        top = f"┌{'─' * (provider_width + 2)}┬{'─' * (prompt_width + 2)}┬{'─' * (modules_width + 2)}┐"
        middle = f"├{'─' * (provider_width + 2)}┼{'─' * (prompt_width + 2)}┼{'─' * (modules_width + 2)}┤"
        bottom = f"└{'─' * (provider_width + 2)}┴{'─' * (prompt_width + 2)}┴{'─' * (modules_width + 2)}┘"

        lines: list[str] = [top]
        lines.extend(_render_row(*columns))
        lines.append(middle)
        for index, row in enumerate(rows):
            lines.extend(_render_row(*row))
            if index != len(rows) - 1:
                lines.append(middle)
        lines.append(bottom)
        return lines

    def _build_provider_modules_map(provider_specs: list[str]) -> dict[str, list[str]]:
        """!
        @brief Build provider-to-module-entry mapping for installation table rendering.
        @details Parses validated raw `--provider` specifications, preserves first-seen artifact-item order and artifact-local option order, appends applicable provider-scoped options in first-seen order, and emits one module-entry line per active artifact item as `artifact` or `artifact:options`. Complexity: O(P * (A + O)) where P is spec count. No side effects.
        @param provider_specs {list[str]} Raw `--provider` SPEC values after update-merging logic.
        @return {dict[str, list[str]]} Mapping from provider to ordered module-entry lines.
        @satisfies SRS-291, SRS-294, SRS-297
        """
        artifacts_ordered: dict[str, list[str]] = {
            provider_name: [] for provider_name in sorted(VALID_PROVIDERS)
        }
        artifact_options_ordered: dict[str, dict[str, list[str]]] = {
            provider_name: {
                artifact_name: [] for artifact_name in sorted(VALID_ARTIFACTS)
            }
            for provider_name in sorted(VALID_PROVIDERS)
        }
        provider_options_ordered: dict[str, list[str]] = {
            provider_name: [] for provider_name in sorted(VALID_PROVIDERS)
        }
        for raw_spec in provider_specs:
            provider_name, artifact_items, provider_options = parse_provider_spec(raw_spec)
            for artifact_name, artifact_options in artifact_items:
                if artifact_name not in artifacts_ordered[provider_name]:
                    artifacts_ordered[provider_name].append(artifact_name)
                ordered_artifact_options = artifact_options_ordered[provider_name][
                    artifact_name
                ]
                for option_name in artifact_options:
                    if option_name not in ordered_artifact_options:
                        ordered_artifact_options.append(option_name)
            for option_name in provider_options:
                if option_name not in provider_options_ordered[provider_name]:
                    provider_options_ordered[provider_name].append(option_name)
        modules_map: dict[str, list[str]] = {}
        for provider_name in sorted(VALID_PROVIDERS):
            provider_lines: list[str] = []
            for artifact_name in artifacts_ordered[provider_name]:
                ordered_options = list(
                    artifact_options_ordered[provider_name][artifact_name]
                )
                for option_name in provider_options_ordered[provider_name]:
                    applicable_artifacts = PROVIDER_OPTION_APPLICABILITY.get(
                        option_name, frozenset()
                    )
                    if (
                        artifact_name in applicable_artifacts
                        and option_name not in ordered_options
                    ):
                        ordered_options.append(option_name)
                if ordered_options:
                    provider_lines.append(
                        f"{artifact_name}:{','.join(ordered_options)}"
                    )
                else:
                    provider_lines.append(artifact_name)
            modules_map[provider_name] = provider_lines
        return modules_map

    def _colorize_table_border(line: str) -> str:
        """!
        @brief Colorize box-drawing border glyphs with bright-red ANSI style.
        @details Applies color to border characters while preserving cell payload text color.
        @param line {str} One already-rendered table line.
        @return {str} Line with border glyphs wrapped in ANSI bright-red and reset sequences.
        """
        border_chars = frozenset("┌┬┐├┼┤└┴┘─│")
        return "".join(
            f"{ANSI_BRIGHT_RED}{char}{ANSI_RESET}" if char in border_chars else char
            for char in line
        )

    table_lines = _format_install_table(
        _build_provider_modules_map(effective_provider_specs), prompts_installed
    )
    for table_line in table_lines:
        print(_colorize_table_border(table_line))


# ── Excluded directories for project-scan file selection ──────────────────

EXCLUDED_DIRS: frozenset[str] = frozenset()
"""Directories additionally excluded from project scan after `.gitignore` filtering."""

# ── Supported source file extensions ──────────────────────────────────────

SUPPORTED_EXTENSIONS = frozenset(
    {
        ".c",
        ".cpp",
        ".cs",
        ".ex",
        ".go",
        ".hs",
        ".java",
        ".js",
        ".mjs",
        ".kt",
        ".lua",
        ".pl",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".swift",
        ".ts",
        ".zig",
    }
)
"""File extensions considered during source directory scanning."""


def _collect_source_files(src_dirs: list[str], project_base: Path) -> list[str]:
    """!
    @brief Collect source files from git-indexed project paths.
        @details Uses `git ls-files --cached --others --exclude-standard` in project root, filters by src-dir prefixes, applies EXCLUDED_DIRS filtering, and keeps only SUPPORTED_EXTENSIONS files.
    @param src_dirs Input parameter `src_dirs`.
    @param project_base Input parameter `project_base`.
    @return {list[str]} Function return value.
    """
    cmd = [
        "git",
        "-C",
        str(project_base),
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
    ]
    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError:
        raise ReqError(
            "Error: failed to collect source files with `git ls-files` in project root.",
            1,
        )

    normalized_src_dirs: list[str] = []
    for src_dir in src_dirs:
        normalized = make_relative_if_contains_project(src_dir, project_base)
        normalized = Path(normalized).as_posix().strip("/")
        normalized_src_dirs.append(normalized)

    collected: set[str] = set()
    for rel_path in output.splitlines():
        rel_posix = Path(rel_path.strip()).as_posix()
        if rel_posix.startswith("./"):
            rel_posix = rel_posix[2:]
        if not rel_posix:
            continue
        if not any(
            src_dir in {"", "."}
            or rel_posix == src_dir
            or rel_posix.startswith(f"{src_dir}/")
            for src_dir in normalized_src_dirs
        ):
            continue
        rel_obj = Path(rel_posix)
        if any(part in EXCLUDED_DIRS for part in rel_obj.parts[:-1]):
            continue
        if rel_obj.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        collected.add(str((project_base / rel_obj).resolve()))
    return sorted(collected)


def _build_ascii_tree(paths: list[str]) -> str:
    """!
    @brief Build a deterministic tree string from project-relative paths.
        @param paths Project-relative file paths.
        @return Rendered tree rooted at '.'.
    @details Implements the _build_ascii_tree function behavior with deterministic control flow.
    """
    tree: dict[str, dict[str, Any] | None] = {}
    for rel_path in sorted(paths):
        node = tree
        parts = Path(rel_path).parts
        for index, part in enumerate(parts):
            is_leaf = index == len(parts) - 1
            if is_leaf:
                node.setdefault(part, None)
            else:
                child = node.setdefault(part, {})
                if child is None:
                    child = {}
                    node[part] = child
                node = child

    lines = ["."]

    def _emit(
        branch: dict[str, dict[str, Any] | None],
        prefix: str = "",
    ) -> None:
        """! @brief Emit one subtree in deterministic ASCII-tree order.
        @details Traverses child entries sorted lexicographically, appends connector glyphs (`├──`, `└──`) to `lines`, and recursively emits nested directories while preserving tree indentation state in `prefix`.
        @param branch {dict[str, dict[str, Any] | None]} Current subtree mapping where `None` denotes file leaf and `dict` denotes directory node.
        @param prefix {str} Prefix containing indentation and vertical-branch markers for current depth.
        @return {None} This helper mutates closure variable `lines` with formatted rows.
        """
        entries = sorted(branch.items(), key=lambda item: item[0])
        for idx, (name, child) in enumerate(entries):
            last = idx == len(entries) - 1
            connector = "└── " if last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if isinstance(child, dict) and child:
                _emit(child, prefix + ("    " if last else "│   "))

    _emit(tree)
    return "\n".join(lines)


def _format_files_structure_markdown(files: list[str], project_base: Path) -> str:
    """!
    @brief Format markdown section containing the scanned files tree.
        @param files Absolute file paths selected for references processing.
        @param project_base Project root used to normalize relative paths.
        @return Markdown section with heading and fenced tree.
    @details Implements the _format_files_structure_markdown function behavior with deterministic control flow.
    """
    rel_paths = [
        Path(path).resolve().relative_to(project_base).as_posix() for path in files
    ]
    tree = _build_ascii_tree(rel_paths)
    return f"# Files Structure\n```\n{tree}\n```"


def _is_standalone_command(args: Namespace) -> bool:
    """!
    @brief Check if the parsed args contain a standalone file command.
    @param args Parsed CLI namespace.
    @return True when the standalone `--test-static-check` flag is present.
    @details The standalone group now contains only `--test-static-check` (SRS-240); the
      former `--files-*` and project-scan analysis flags were converted to bare
      subcommands (SRS-408) whose base requirements follow SRS-396 and SRS-410.
    """
    return getattr(args, "test_static_check", None) is not None


def _is_project_scan_command(args: Namespace) -> bool:
    """!
    @brief Check if the parsed args contain a project-scan command.
    @param args Parsed CLI namespace.
    @return True when any project-scan flag is present.
    @details Project-scan commands: `--git-check`, `--docs-check`, `--git-wt-name`,
      `--git-wt-create`, and `--git-wt-delete`. The analysis commands were converted
      to bare subcommands (SRS-408) and `--git-path` was removed (SRS-333, SRS-334).
    """
    return bool(
        getattr(args, "git_check", False)
        or getattr(args, "docs_check", False)
        or getattr(args, "git_wt_name", False)
        or getattr(args, "git_wt_create", None)
        or getattr(args, "git_wt_delete", None)
    )


def _is_directory_config_command(args: Namespace) -> bool:
    """!
    @brief Check if args request a directory configuration command.
    @param args Parsed CLI namespace.
    @return True when any `--set-*-dir` flag is present.
    @details Configuration commands persist project-relative directories and therefore
      require `--prj-base` without activating the installation flow (SRS-396, SRS-398,
      SRS-399, SRS-400).
    """
    return bool(
        getattr(args, "set_docs_dir", None) is not None
        or getattr(args, "set_src_dir", None)
        or getattr(args, "set_tests_dir", None) is not None
    )


def _require_prj_base(args: Namespace) -> Path:
    """!
    @brief Return the mandatory absolute project base for the current command.
    @param args Parsed CLI namespace.
    @return {Path} Absolute project base path.
    @throws ReqError If `--prj-base` is absent or the resolved path does not exist.
    @details `--prj-base` is command-line only and is never loaded from configuration
      (SRS-392, SRS-394, SRS-395, SRS-396).
    @satisfies SRS-392, SRS-394, SRS-395, SRS-396
    """
    prj_base = getattr(args, "prj_base", None)
    if prj_base is None:
        raise ReqError("Error: --prj-base is required for this command.", 1)
    project_base = Path(prj_base).resolve()
    if not project_base.exists():
        raise ReqError(f"Error: --prj-base '{project_base}' does not exist", 2)
    return project_base


def _require_git_base_value(args: Namespace) -> Path:
    """!
    @brief Validate and return the `--git-base` argument value without repository resolution.
    @param args Parsed CLI namespace.
    @return {Path} Absolute `--git-base` path.
    @throws ReqError If `--git-base` is absent or does not exist.
    @details Performs presence and existence validation only (SRS-395); git-integration
      commands reach this level through `_require_git_base` because they are the only
      commands that execute git operations through `--git-base` (SRS-397).
    @satisfies SRS-393, SRS-394, SRS-395, SRS-397
    """
    git_base = getattr(args, "git_base", None)
    if git_base is None:
        raise ReqError("Error: --git-base is required for this command.", 1)
    git_path = Path(git_base).resolve()
    if not git_path.exists():
        raise ReqError(f"Error: --git-base '{git_path}' does not exist", 2)
    return git_path


def _require_git_base(args: Namespace) -> Path:
    """!
    @brief Return the mandatory absolute git repository base for the current command.
    @param args Parsed CLI namespace.
    @return {Path} Absolute git repository root resolved from `--git-base`.
    @throws ReqError If `--git-base` is absent, does not exist, or is not inside a git work tree.
    @details `--git-base` is command-line only and is never loaded from configuration; the
      returned path is the repository root reported by `git rev-parse --show-toplevel`
      executed in `--git-base` (SRS-393, SRS-394, SRS-395, SRS-397).
    @satisfies SRS-393, SRS-394, SRS-395, SRS-397
    """
    return resolve_git_root(_require_git_base_value(args))

def run_git_check(args: Namespace) -> None:
    """!
    @brief Execute --git-check: verify clean git status and valid HEAD.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @throws ReqError On git status unclear or when `--git-base` is outside a git repository.
    @satisfies SRS-311, SRS-312, SRS-391, SRS-397
    """
    git_path = _require_git_base(args)
    cmd = (
        "git rev-parse --is-inside-work-tree "
        "&& ! git status --porcelain | grep -q . "
        "&& { git symbolic-ref -q HEAD || git rev-parse --verify HEAD ; }"
    )
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        raise ReqError("ERROR: Git status unclear!", 1)
    if result.returncode != 0:
        raise ReqError("ERROR: Git status unclear!", 1)


def run_docs_check(args: Namespace) -> None:
    """!
    @brief Execute --docs-check: verify existence of REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @throws ReqError If any required doc file is missing.
    @satisfies SRS-313, SRS-314, SRS-315, SRS-316, SRS-317, SRS-396
    """
    project_base = _require_prj_base(args)
    full_cfg = load_full_config()
    base_path = project_base
    docs_dir = full_cfg.get("docs-dir", DEFAULT_DOCS_DIR)
    if isinstance(docs_dir, str):
        docs_dir = docs_dir.rstrip("/\\")
    doc_path = Path(base_path) / docs_dir
    for filename, prompt_cmd in [
        ("REQUIREMENTS.md", "/req-write"),
        ("WORKFLOW.md", "/req-workflow"),
        ("REFERENCES.md", "/req-references"),
    ]:
        full_path = doc_path / filename
        if not full_path.is_file():
            msg = (
                f"ERROR: File {doc_path}/{filename} does not exist, "
                f"generate it with the {prompt_cmd} prompt!"
            )
            print(msg)
            raise ReqError(msg, 1)


def run_git_wt_name(args: Namespace) -> None:
    """!
    @brief Execute --git-wt-name: print standardized worktree name.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @satisfies SRS-318, SRS-319, SRS-391, SRS-397
    """
    git_path = _require_git_base(args)
    project_name = git_path.name
    try:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=10,
        )
        branch = branch_result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        branch = "unknown"
    sanitized_branch = sanitize_branch_name(branch)
    execution_id = datetime.now().strftime("%Y%m%d%H%M%S")
    print(f"useReq-{project_name}-{sanitized_branch}-{execution_id}")


def _worktree_path_exists_exact(git_path: Path, target_path: Path) -> bool:
    """!
    @brief Check whether a git worktree exists at the exact target path.
    @param git_path Absolute git root path used as command cwd.
    @param target_path Absolute worktree path expected for WT_NAME.
    @return {bool} True only when target_path is listed as an exact worktree path.
    @throws ReqError On git command execution errors.
    @details Parses `git worktree list --porcelain` output by `worktree <path>` records and performs exact path comparison to prevent partial-name or substring matches.
    """
    try:
        wt_list = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        raise ReqError("Error: unable to query git worktree list.", 3)
    if wt_list.returncode != 0:
        raise ReqError("Error: unable to query git worktree list.", 3)
    target_norm = str(target_path.resolve())
    for line in wt_list.stdout.splitlines():
        if line.startswith("worktree "):
            listed_path = line[len("worktree ") :].strip()
            if Path(listed_path).resolve() == Path(target_norm):
                return True
    return False


def _rollback_worktree_create(git_path: Path, wt_path: Path, wt_name: str) -> None:
    """!
    @brief Roll back worktree and branch created by --git-wt-create on post-create failure.
    @param git_path Absolute git root path used as command cwd.
    @param wt_path Absolute worktree path to remove.
    @param wt_name Exact branch name to delete.
    @return {None} Function return value.
    @throws ReqError If rollback cannot remove the exact target worktree and branch.
    @details Uses `git worktree remove <path> --force` and `git branch -D <name>` to restore a clean git state when post-create copy/chdir operations fail.
    """
    try:
        remove_result = subprocess.run(
            ["git", "worktree", "remove", str(wt_path), "--force"],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=30,
        )
        branch_result = subprocess.run(
            ["git", "branch", "-D", wt_name],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        raise ReqError(
            f"ERROR: Rollback failed for worktree or branch {wt_name}.",
            1,
        )
    if remove_result.returncode != 0 or branch_result.returncode != 0:
        raise ReqError(
            f"ERROR: Rollback failed for worktree or branch {wt_name}.",
            1,
        )


def run_git_wt_create(args: Namespace) -> None:
    """!
    @brief Execute --git-wt-create: create a git worktree, branch, and optional .venv copy.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @throws ReqError On invalid name, git command failure, or when CWD is outside a git repository.
    @satisfies SRS-320, SRS-321, SRS-322, SRS-331, SRS-335, SRS-391, SRS-397
    """
    wt_name: str = args.git_wt_create
    if not validate_wt_name(wt_name):
        msg = f"ERROR: Invalid worktree/branch name: {wt_name}."
        print(msg)
        raise ReqError(msg, 1)
    git_path = _require_git_base(args)
    prj_base_arg = getattr(args, "prj_base", None)
    base_path = Path(prj_base_arg).resolve() if prj_base_arg else git_path
    parent_path = git_path.parent
    # SRS-322: create worktree + branch.
    wt_dest = parent_path / wt_name
    try:
        result = subprocess.run(
            ["git", "worktree", "add", str(wt_dest), "-b", wt_name],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=30,
        )
        if result.returncode != 0:
            raise ReqError(
                f"Error: git worktree add failed: {result.stderr.strip()}", 1
            )
    except FileNotFoundError:
        raise ReqError("Error: git is not available on PATH.", 3)
    except subprocess.TimeoutExpired:
        raise ReqError("Error: git worktree add timed out.", 3)
    try:
        # SRS-335: copy .venv from --prj-base first when provided, else --git-base.
        src_venv: Optional[Path] = None
        base_venv = base_path / ".venv"
        git_venv = git_path / ".venv"
        rel_venv = Path(".venv")
        if base_venv.is_dir():
            src_venv = base_venv
            try:
                rel_venv = base_path.relative_to(git_path) / ".venv"
            except ValueError:
                rel_venv = Path(".venv")
        elif git_venv.is_dir():
            src_venv = git_venv
            rel_venv = Path(".venv")
        if src_venv is not None:
            dst_venv = wt_dest / rel_venv
            if not dst_venv.is_dir():
                dst_venv.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(str(src_venv), str(dst_venv))
    except (OSError, ReqError):
        _rollback_worktree_create(git_path, wt_dest, wt_name)
        raise ReqError(
            f"ERROR: Unable to finalize worktree creation for {wt_name}.",
            1,
        )


def run_git_wt_delete(args: Namespace) -> None:
    """!
    @brief Execute --git-wt-delete: remove a git worktree and branch by name.
    @param args Parsed CLI namespace.
    @return {None} Function return value.
    @throws ReqError On invalid name or git removal failure.
    @satisfies SRS-326, SRS-327, SRS-328, SRS-332, SRS-391, SRS-397
    """
    wt_name: str = args.git_wt_delete
    git_path = _require_git_base(args)
    base_path = git_path
    parent_path = git_path.parent
    # SRS-327: validate branch or worktree exists.
    branch_exists = False
    try:
        br = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{wt_name}"],
            capture_output=True,
            text=True,
            cwd=str(git_path),
            timeout=10,
        )
        if br.returncode == 0:
            branch_exists = True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    wt_path = parent_path / wt_name
    try:
        wt_exists = _worktree_path_exists_exact(git_path, wt_path)
    except ReqError:
        wt_exists = False
    if not branch_exists and not wt_exists:
        msg = f"ERROR: Invalid worktree or branch name: {wt_name}."
        print(msg)
        raise ReqError(msg, 1)
    # SRS-328: remove worktree and branch.
    error_occurred = False
    if wt_exists:
        try:
            r1 = subprocess.run(
                ["git", "worktree", "remove", str(wt_path), "--force"],
                capture_output=True,
                text=True,
                cwd=str(base_path),
                timeout=30,
            )
            if r1.returncode != 0:
                error_occurred = True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            error_occurred = True
    if branch_exists:
        try:
            r2 = subprocess.run(
                ["git", "branch", "-D", wt_name],
                capture_output=True,
                text=True,
                cwd=str(base_path),
                timeout=10,
            )
            if r2.returncode != 0:
                error_occurred = True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            error_occurred = True
    if error_occurred:
        msg = f"ERROR: Unable to remove worktree or branch {wt_name}."
        print(msg)
        raise ReqError(msg, 1)


def run_files_tokens(files: list[str]) -> None:
    """!
    @brief Execute files-tokens: count tokens for arbitrary files.
    @details Implements the run_files_tokens function behavior with deterministic control flow.
    @param files Input parameter `files`.
    @return {None} Function return value.
    @satisfies SRS-408
    """
    from .token_counter import count_files_metrics, format_pack_summary

    valid_files = []
    for f in files:
        if not os.path.isfile(f):
            print(f"  Warning: skipping (not found): {f}", file=sys.stderr)
        else:
            valid_files.append(f)

    if not valid_files:
        raise ReqError("Error: no valid files provided.", 1)

    results = count_files_metrics(valid_files)
    print(format_pack_summary(results))


def run_files_references(files: list[str]) -> None:
    """!
    @brief Execute files-references: generate markdown for arbitrary files.
    @details Implements the run_files_references function behavior with deterministic control flow.
    @param files Input parameter `files`.
    @return {None} Function return value.
    @satisfies SRS-234, SRS-408
    """
    from .generate_markdown import generate_markdown

    md = generate_markdown(
        files,
        verbose=VERBOSE,
        output_base=Path.cwd().resolve(),
    )
    print(md)


def run_files_compress(files: list[str], enable_line_numbers: bool = False) -> None:
    """!
    @brief Execute files-compress: compress arbitrary files.
        @param files List of source file paths to compress.
        @param enable_line_numbers If True, emits <n>: prefixes in compressed entries.
        @details Renders output header paths relative to current working directory.
    @return {None} Function return value.
    @satisfies SRS-408
    """
    from .compress_files import compress_files

    output = compress_files(
        files,
        include_line_numbers=enable_line_numbers,
        verbose=VERBOSE,
        output_base=Path.cwd().resolve(),
    )
    print(output)


def run_files_find(args_list: list[str], enable_line_numbers: bool = False) -> None:
    """!
    @brief Execute files-find: find constructs in arbitrary files.
        @param args_list Combined list: [TAG, PATTERN, FILE1, FILE2, ...].
        @param enable_line_numbers If True, emits <n>: prefixes in output.
    @details Implements the run_files_find function behavior with deterministic control flow.
    @return {None} Function return value.
    @satisfies SRS-236, SRS-408
    """
    from .find_constructs import find_constructs_in_files

    if len(args_list) < 3:
        raise ReqError(
            "Error: files-find requires at least TAG, PATTERN, and one FILE.", 1
        )

    tag_filter = args_list[0]
    pattern = args_list[1]
    files = args_list[2:]

    output = find_constructs_in_files(
        files,
        tag_filter,
        pattern,
        include_line_numbers=enable_line_numbers,
        verbose=VERBOSE,
    )
    print(output)


def run_references(args: Namespace) -> None:
    """!
    @brief Execute references: generate markdown for project source files.
    @details Implements the run_references function behavior with deterministic control flow.
    @param args Input parameter `args`.
    @return {None} Function return value.
    @satisfies SRS-177, SRS-180, SRS-181, SRS-235, SRS-396, SRS-408
    """
    from .generate_markdown import generate_markdown

    project_base, src_dirs = _resolve_project_src_dirs(args)
    files = _collect_source_files(src_dirs, project_base)
    if not files:
        raise ReqError("Error: no source files found in configured directories.", 1)
    md = generate_markdown(files, verbose=VERBOSE, output_base=project_base)
    files_structure = _format_files_structure_markdown(files, project_base)
    print(f"{files_structure}\n\n{md}")


def run_compress_cmd(args: Namespace) -> None:
    """!
    @brief Execute compress: compress project source files.
        @param args Parsed CLI arguments namespace.
    @details Implements the run_compress_cmd function behavior with deterministic control flow.
    @return {None} Function return value.
    @satisfies SRS-179, SRS-180, SRS-181, SRS-396, SRS-408
    """
    from .compress_files import compress_files

    project_base, src_dirs = _resolve_project_src_dirs(args)
    files = _collect_source_files(src_dirs, project_base)
    if not files:
        raise ReqError("Error: no source files found in configured directories.", 1)
    output = compress_files(
        files,
        include_line_numbers=getattr(args, "enable_line_numbers", False),
        verbose=VERBOSE,
        output_base=project_base,
    )
    print(output)


def run_find(args: Namespace) -> None:
    """!
    @brief Execute find: find constructs in project source files.
        @param args Parsed CLI arguments namespace.
        @throws ReqError If no source files found or no constructs match criteria with available TAGs listing.
    @details Implements the run_find function behavior with deterministic control flow.
    @return {None} Function return value.
    @satisfies SRS-180, SRS-237, SRS-396, SRS-408
    """
    from .find_constructs import find_constructs_in_files

    project_base, src_dirs = _resolve_project_src_dirs(args)
    files = _collect_source_files(src_dirs, project_base)
    if not files:
        raise ReqError("Error: no source files found in configured directories.", 1)

    # args.find is a list [TAG, PATTERN]
    tag_filter, pattern = args.find
    try:
        output = find_constructs_in_files(
            files,
            tag_filter,
            pattern,
            include_line_numbers=getattr(args, "enable_line_numbers", False),
            verbose=VERBOSE,
        )
        print(output)
    except ValueError as e:
        raise ReqError(str(e), 1)


def run_tokens(args: Namespace) -> None:
    """! @brief Execute tokens on the canonical documentation files in --docs-dir.
    @param args Parsed CLI arguments namespace.
    @return None.
    @exception ReqError Raised when no canonical documentation file exists in configured docs-dir.
    @details Uses the mandatory `--prj-base` project base joined with the docs-dir value
      from ~/.config/usereq/config.json, selects only REQUIREMENTS.md/WORKFLOW.md/REFERENCES.md
      as direct regular files in fixed order, and delegates summary rendering to
      run_files_tokens.
    @satisfies SRS-387, SRS-392, SRS-396, SRS-408
    """
    project_base = _resolve_project_base(args)
    config = load_config()
    docs_dir_value = config["docs-dir"]
    ensure_doc_directory(str(docs_dir_value), project_base)
    normalized_docs_dir = make_relative_if_contains_project(
        str(docs_dir_value), project_base
    )
    docs_dir = project_base / normalized_docs_dir
    canonical_names = ("REQUIREMENTS.md", "WORKFLOW.md", "REFERENCES.md")
    files = [
        str(candidate_path)
        for candidate_path in (docs_dir / name for name in canonical_names)
        if candidate_path.is_file()
    ]
    if not files:
        raise ReqError("Error: no canonical docs files found in --docs-dir.", 1)
    run_files_tokens(files)


def run_files_static_check_cmd(files: list[str], args: Namespace) -> int:
    """!
    @brief Execute `files-static-check`: run static analysis on an explicit file list.
    @param files List of raw file paths supplied by the user.
    @param args Parsed CLI namespace; the mandatory `--prj-base` resolves the dispatch context.
    @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
    @details
      Static-check configuration is loaded from `~/.config/usereq/config.json`.
      When the global configuration file cannot be located, emits a warning to stderr and
      continues with the SRS-424 default static-check configuration (SRS-254).
      Project base for dispatch context is the mandatory `--prj-base` value (SRS-253).
      For each file:
      - Resolves absolute path; skips with warning if not a regular file.
      - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on the lowercase extension.
      - Looks up language in the `"static-check"` config section; skips silently if absent.
      - Executes each configured language entry sequentially via
        `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`.
      - For `Command` module entries, execution order is `<cmd> [params...] <filename>`.
      Dispatch context provides project root for checker runtime execution.
      All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-253).
      Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-253, SRS-255)
    @see SRS-253, SRS-254, SRS-255, SRS-341, SRS-396, SRS-408
    """
    from .static_check import STATIC_CHECK_EXT_TO_LANG, dispatch_static_check_for_file

    # Resolve the mandatory project base for dispatch context (SRS-253, SRS-396).
    project_base = _require_prj_base(args)

    # SRS-254: warn on a missing configuration file, then continue with the SRS-424 defaults.
    if not get_global_config_path().is_file():
        print(
            "  Warning: global configuration file not found; using the default static-check configuration.",
            file=sys.stderr,
        )
    sc_config = load_static_check_from_config()

    overall = 0
    for raw_path in files:
        p = Path(raw_path)
        if not p.is_file():
            print(
                f"  Warning: skipping (not found or not a file): {raw_path}",
                file=sys.stderr,
            )
            continue
        filepath = str(p.resolve())
        ext = p.suffix.lower()
        lang = STATIC_CHECK_EXT_TO_LANG.get(ext)
        if not lang:
            vlog(f"Skipping {raw_path}: no language mapping for extension '{ext}'")
            continue
        lang_configs = sc_config.get(lang)
        if not lang_configs:
            vlog(f"Skipping {raw_path}: no static-check config for language '{lang}'")
            continue
        for lang_config in lang_configs:
            rc = dispatch_static_check_for_file(
                filepath,
                lang_config,
                fail_only=True,
                project_base=project_base,
            )
            if rc != 0:
                overall = 1
    return overall


def run_project_static_check_cmd(args: Namespace) -> int:
    """!
    @brief Execute `static-check`: run static analysis on project source and test files.
    @param args Parsed CLI namespace; requires the mandatory `--prj-base` argument.
    @return Exit code: 0 if all checked files pass (or none are checked), 1 if any fail.
    @details
      Collects files from configured `src-dir` directories and the `tests-dir` directory
      (SRS-256, SRS-336), applies `EXCLUDED_DIRS` filtering and `SUPPORTED_EXTENSIONS` matching.
      If `tests-dir` is missing or invalid in the global configuration file, test directory
      inclusion is skipped silently without error (SRS-336).
      Files under `<tests-dir>/fixtures/` are excluded from static-check selection because they
      are fixture corpus inputs for parser/static-check tests and can intentionally contain
      diagnostics unrelated to project code quality gates.
      For each collected file:
      - Detects language via `STATIC_CHECK_EXT_TO_LANG` keyed on lowercase extension.
      - Looks up language in the `"static-check"` section of `~/.config/usereq/config.json`.
      - Skips silently when no tool is configured for the file's language.
      - Executes each configured language entry sequentially via
        `dispatch_static_check_for_file(filepath, lang_config, fail_only=True, project_base=...)`.
      - For `Command` module entries, execution order is `<cmd> [params...] <filename>`.
      Dispatch context provides project root for checker runtime execution.
      All checks execute with `fail_only=True`: passing checks produce no stdout output (SRS-256).
      Overall exit code: max of all per-file codes (0=all pass, 1=any fail). (SRS-256, SRS-257)
    @throws ReqError If no source files are found.
    @see SRS-256, SRS-257, SRS-336, SRS-341, SRS-396, SRS-408
    """
    from .static_check import STATIC_CHECK_EXT_TO_LANG, dispatch_static_check_for_file

    project_base, src_dirs = _resolve_project_src_dirs(args)
    sc_config = load_static_check_from_config()
    selection_dirs = list(src_dirs)
    tests_dir_rel: Optional[str] = None

    # SRS-336: append tests-dir to file selection; skip silently if missing/invalid
    try:
        full_cfg = load_full_config()
        tests_dir_val = full_cfg.get("tests-dir")
        if isinstance(tests_dir_val, str) and tests_dir_val.strip():
            selection_dirs.append(tests_dir_val)
            tests_dir_rel = (
                Path(make_relative_if_contains_project(tests_dir_val, project_base))
                .as_posix()
                .strip("/")
            )
    except ReqError:
        pass

    files = _collect_source_files(selection_dirs, project_base)
    fixture_roots: list[str] = ["tests/fixtures"]
    if tests_dir_rel is not None:
        configured_root = (
            "fixtures" if tests_dir_rel in {"", "."} else f"{tests_dir_rel}/fixtures"
        )
        if configured_root not in fixture_roots:
            fixture_roots.append(configured_root)
    filtered_files: list[str] = []
    for filepath in files:
        try:
            rel_posix = (
                Path(filepath).resolve().relative_to(project_base.resolve()).as_posix()
            )
        except ValueError:
            filtered_files.append(filepath)
            continue
        should_skip = False
        for fixture_root in fixture_roots:
            fixture_prefix = f"{fixture_root}/"
            if rel_posix == fixture_root or rel_posix.startswith(fixture_prefix):
                should_skip = True
                break
        if should_skip:
            continue
        filtered_files.append(filepath)
    files = filtered_files
    if not files:
        raise ReqError("Error: no source files found in configured directories.", 1)

    overall = 0
    for filepath in files:
        ext = Path(filepath).suffix.lower()
        lang = STATIC_CHECK_EXT_TO_LANG.get(ext)
        if not lang:
            vlog(f"Skipping {filepath}: no language mapping for extension '{ext}'")
            continue
        lang_configs = sc_config.get(lang)
        if not lang_configs:
            vlog(f"Skipping {filepath}: no static-check config for language '{lang}'")
            continue
        for lang_config in lang_configs:
            rc = dispatch_static_check_for_file(
                filepath,
                lang_config,
                fail_only=True,
                project_base=project_base,
            )
            if rc != 0:
                overall = 1
    return overall


def _resolve_project_base(args: Namespace) -> Path:
    """!
    @brief Resolve the mandatory project base path for project-level commands.
    @param args Parsed CLI arguments namespace.
    @return Absolute path of the project base supplied by `--prj-base`.
    @throws ReqError If `--prj-base` is missing or the resolved path does not exist.
    @details The project base is never derived from the current working directory and is
      never loaded from configuration (SRS-392, SRS-394, SRS-395, SRS-396).
    @satisfies SRS-392, SRS-394, SRS-395, SRS-396
    """
    return _require_prj_base(args)


def _resolve_project_src_dirs(args: Namespace) -> tuple[Path, list[str]]:
    """!
    @brief Resolve project base and src-dirs for project source commands.
    @details Loads the `src-dir` list from the user-global configuration file
    (`~/.config/usereq/config.json`) and resolves it against the mandatory `--prj-base`
    project base (SRS-392, SRS-396).
    @param args Input parameter `args`.
    @return {tuple[Path, list[str]]} Tuple `(project_base, src_dirs)`.
    @throws ReqError If `--prj-base` is missing or `src-dir` is invalid.
    @satisfies SRS-392, SRS-396
    """
    project_base = _resolve_project_base(args)

    src_dirs: list[str]
    config = load_config()
    raw_src_dirs = config.get("src-dir", [])
    if not isinstance(raw_src_dirs, list) or not all(
        isinstance(item, str) for item in raw_src_dirs
    ):
        raise ReqError(
            "Error: missing or invalid 'src-dir' field in the global configuration file",
            11,
        )
    src_dirs = raw_src_dirs

    if not src_dirs:
        raise ReqError("Error: no source directories configured.", 1)

    return project_base, src_dirs


def main(argv: Optional[list[str]] = None) -> int:
    """!
    @brief CLI entry point for console_scripts and `-m` execution.
        @details Returns an exit code (0 success, non-zero on error).
    @param argv Input parameter `argv`.
    @return {int} Function return value.
    """
    try:
        global VERBOSE, DEBUG
        argv_list = sys.argv[1:] if argv is None else argv
        force_online_release_check = "--ver" in argv_list or "--version" in argv_list
        # Run release-check at startup before argument parsing/validation.
        global FORCE_ONLINE_RELEASE_CHECK
        previous_force_online_release_check = FORCE_ONLINE_RELEASE_CHECK
        FORCE_ONLINE_RELEASE_CHECK = force_online_release_check
        pypi_latest_from_check: Optional[str] = None
        try:
            pypi_latest_from_check = maybe_notify_newer_version(
                timeout_seconds=RELEASE_CHECK_TIMEOUT_SECONDS
            )
        finally:
            FORCE_ONLINE_RELEASE_CHECK = previous_force_online_release_check
        if not argv_list:
            build_parser().print_help()
            return 0
        if "--uninstall" in argv_list:
            run_uninstall()
            return 0
        if "--upgrade" in argv_list:
            run_upgrade(use_github=("--develop" in argv_list or "--dev" in argv_list))
            _maybe_auto_install_after_upgrade(argv_list)
            return 0
        if maybe_print_version(argv_list, pypi_latest=pypi_latest_from_check):
            return 0
        args = parse_args(argv_list)
        VERBOSE = getattr(args, "verbose", False)
        DEBUG = getattr(args, "debug", False)
        # Directory configuration commands require --prj-base only (SRS-396, SRS-398..SRS-401).
        if _is_directory_config_command(args):
            run_set_directories(args)
            return 0
        # Provider/static-check/auto-install configuration commands persist to
        # ~/.config/usereq/config.json and never install by themselves (SRS-276, SRS-413,
        # SRS-414, SRS-415, SRS-420); when combined with the install subcommand they are
        # applied first and installation proceeds afterwards.
        if _is_provider_config_command(args):
            run_config_commands(args)
            if getattr(args, "command", None) is None:
                return 0
        # Bare subcommands (SRS-408, SRS-280).
        command = getattr(args, "command", None)
        if command == "install":
            run_install(args)
            return 0
        if command == "uninstall":
            run_uninstall_providers(args)
            return 0
        if command == "show":
            run_show(args)
            return 0
        # Bare analysis subcommands (SRS-408); --prj-base is enforced by the handlers
        # that consume it (SRS-396, SRS-410) and no subcommand requires --git-base.
        if command is not None:
            if command == "files-tokens":
                run_files_tokens(args.files_tokens)
            elif command == "files-references":
                run_files_references(args.files_references)
            elif command == "files-compress":
                run_files_compress(
                    args.files_compress,
                    enable_line_numbers=getattr(args, "enable_line_numbers", False),
                )
            elif command == "files-find":
                run_files_find(
                    args.files_find,
                    enable_line_numbers=getattr(args, "enable_line_numbers", False),
                )
            elif command == "files-static-check":
                return run_files_static_check_cmd(args.files_static_check, args)
            elif command == "references":
                run_references(args)
            elif command == "compress":
                run_compress_cmd(args)
            elif command == "tokens":
                run_tokens(args)
            elif command == "find":
                run_find(args)
            elif command == "static-check":
                return run_project_static_check_cmd(args)
            return 0
        # Standalone static-check testbed command (SRS-240)
        if _is_standalone_command(args):
            from .static_check import run_static_check

            rc = run_static_check(args.test_static_check)
            return rc
        # Project scan commands (git and docs)
        if _is_project_scan_command(args):
            if getattr(args, "git_check", False):
                run_git_check(args)
            elif getattr(args, "docs_check", False):
                run_docs_check(args)
            elif getattr(args, "git_wt_name", False):
                run_git_wt_name(args)
            elif getattr(args, "git_wt_create", None):
                run_git_wt_create(args)
            elif getattr(args, "git_wt_delete", None):
                run_git_wt_delete(args)
            return 0
        # Install flow: --prj-base optional (SRS-447); a provided base adds the
        # project-side scaffold, validation, and persistence flow (SRS-449).
        run(args)
    except ReqError as e:
        print(e.message, file=sys.stderr)
        return e.code
    except Exception as e:  # Unexpected error
        print(f"Unexpected error: {e}", file=sys.stderr)
        if DEBUG:
            import traceback

            traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
