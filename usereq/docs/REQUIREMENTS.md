---
title: "useReq Requirements"
description: "Software Requirements Specification"
date: "2026-04-12"
version: 1.16
author: "Ogekuri"
scope:
  paths:
    - "**/*.py"
  excludes:
    - ".*/**"
visibility: "draft"
tags: ["markdown", "requirements", "srs"]
---

# useReq Requirements

## 1. Introduction
useReq is a text-based CLI that initializes and updates repository resources for multi-agent workflows and source-analysis commands.

### 1.1 Document Rules
- This document MUST be written and maintained in English.
- RFC 2119 keywords MUST be used exclusively: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY.
- Each requirement MUST be atomic, single-sentence, and testable; target <= 35 words per requirement; split compound behavior into separate requirement IDs.
- Requirement bullets in requirements sections MUST start with a unique, stable requirement ID and MUST preserve all pre-existing ID values.
- Pre-existing requirement IDs MUST NOT be renumbered, renamed, or reused; newly created requirement IDs MUST be appended beyond the current highest ID.
- This document MUST NOT introduce requirements about source-code comment authoring style beyond already preserved requirements.

### 1.2 Project Scope
- Primary interface: CLI (`req`, `use-req`, `usereq`).
- Functional domains: user-level CLI resource generation, global configuration persistence, source analysis, token counting, compression, construct extraction, Doxygen field extraction, and git worktree management.
- Out-of-scope for this SRS rewrite: source-code modification.

### 1.3 Components and Dependencies
- Runtime: Python 3.11+.
- Core libraries: `argparse`, `pathlib`, `json`, `re`, `os`, `shutil`, `subprocess`, `urllib`.
- Tokenization: `tiktoken` (`cl100k_base` default).
- Workflow automation: `.github/workflows/release-uvx.yml`.

### 1.4 Project Structure (evidence tree)
```text
.
├── docs/
│   ├── REQUIREMENTS.md
│   ├── REFERENCES.md
│   └── WORKFLOW.md
├── .github/workflows/
│   └── release-uvx.yml
├── src/usereq/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── source_analyzer.py
│   ├── generate_markdown.py
│   ├── compress.py
│   ├── compress_files.py
│   ├── find_constructs.py
│   ├── doxygen_parser.py
│   ├── token_counter.py
│   └── resources/
│       ├── docs/
│       └── prompts/
└── tests/
    ├── fixtures/
    └── test_*.py
```

### 1.5 User Interface and Behavioral Overview
- Implemented UI is CLI-only; no GUI behavior is implemented.
- Output channels: stdout for normal payloads and stderr for warnings/errors/verbose status.
- Configuration persistence: single user-global file `~/.config/usereq/config.json`.

### 1.6 Performance Evidence
No explicit performance optimizations identified.

## 2. Project Requirements

### 2.1 Project Functions

### 2.2 Project Constraints

## 3. Requirements

### 3.1 Design and Implementation Constraints

### 3.2 CLI Interface and Lifecycle
- **SRS-034**: MUST accept `--upgrade` and `--uninstall`; provider configuration MUST remain exclusive to repeatable `--enable SPEC`; removed legacy flags, including `--provider`, `--enable-provider`, `--disable-provider`, `--base`, `--here`, `--get-base-path`, `--docs-dir`, `--src-dir`, `--tests-dir`, `--guidelines-dir`, `--add-guidelines`, and `--upgrade-guidelines`, MUST NOT be parsed.
- **SRS-035**: MUST implement the following behavior: The `install` command MUST require at least one enabled provider persisted under `"providers"`; otherwise it MUST print an English error and exit code 4. Each spec implicitly enables the named provider and the listed artifact types.
- **SRS-036**: MUST implement the following behavior: The installation summary table MUST include rows only for providers whose prompts were installed during the current invocation.
- **SRS-049**: MUST implement the following behavior: Immediately after the file list, CLI MUST print a Unicode box-drawing installation summary table with bright-red border lines.
- **SRS-290**: MUST implement the following behavior: The `Prompts Installed` column MUST use a maximum display width of 50 characters and MUST wrap overflowing content onto subsequent lines.
- **SRS-291**: MUST implement the following behavior: The `Modules Installed` column MUST render one line per active `--enable` artifact item as `artifact` when no artifact-local or applicable provider-scoped options are active, or `artifact:options` when one or more such options are active.
- **SRS-296**: MUST implement the following behavior: The `Modules Installed` column width MUST fit the longest rendered module-entry line in active rows and MUST NOT wrap module-entry lines.
- **SRS-055**: MUST implement the following behavior: The repository MUST keep `uv.lock` as the canonical committed dependency lockfile for execution, build, development, testing, and static analysis environments, and MUST NOT keep a root `requirements.txt` manifest.
- **SRS-056**: MUST implement the following behavior: `scripts/req.sh` MUST execute the CLI via `uv run python -m usereq.cli` from repository root, MUST forward all user-provided CLI arguments unchanged, and MUST rely on uv-managed runtime environments.
- **SRS-342**: MUST implement the following behavior: `README.md` MUST include a `Requirements` section stating that Astral `uv` tool is required for `scripts/req.sh` and recommended project CLI execution workflows.
- **SRS-352**: MUST implement the following behavior: `README.md` MUST describe only currently supported CLI flags and provider-option syntax, and MUST NOT describe removed standalone flags superseded by `--enable SPEC` options.
- **SRS-264**: MUST implement the following behavior: Runtime dependency declarations in `pyproject.toml` `[project].dependencies` MUST be present in the locked package set defined by `uv.lock`; `[project].dependencies` MUST include `ruff` and `pyright`; `[build-system].requires` MAY be outside `uv.lock`.
- **SRS-064**: MUST load persisted `providers` from `~/.config/usereq/config.json` for the `install` command, `--update`, and the implicit installation flow; if no provider spec remains active, it MUST raise a config-invalid error.
- **SRS-275**: MUST implement the following behavior: The CLI MUST accept a repeatable `--enable SPEC` argument as the sole mechanism for provider enablement, artifact selection, and option configuration, where `SPEC` syntax is `PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]`.
- **SRS-364**: MUST implement the following behavior: `PROVIDER` MUST be one of `antigravity`, `claude`, `codex`, `opencode`, `pi`; each `ARTIFACT_ITEM` MUST be exactly one `ARTIFACT` from `{prompts, agents, skills}`.
- **SRS-365**: MUST implement the following behavior: `PROVIDER_OPTIONS`, when present, MUST be a comma-separated list containing only `prompts-use-agents`; any other token MUST be rejected as an invalid option.
- **SRS-276**: MUST implement the following behavior: `--enable` MUST only update `~/.config/usereq/config.json` and MUST NOT install provider artifacts; `prompts-use-agents` MUST remain provider-scoped and apply only to `prompts` artifacts.
- **SRS-278**: MUST implement the following behavior: If an `--enable` or `--disable` token is unknown, invalid, or misplaced, the CLI MUST print an English error message identifying the invalid token and exit with code 1.
- **SRS-279**: MUST implement the following behavior: The CLI MUST persist `--enable` specs as raw SPEC strings in the `"providers"` JSON array, replacing all previously persisted specs of the named providers while preserving other providers.
- **SRS-280**: MUST implement the following behavior: The bare `install`, `uninstall`, and `show` subcommands MUST be accepted without the `--` prefix and MUST NOT require `--git-base`.
- **SRS-281**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-282**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-343**: MUST implement the following behavior: `--upgrade` MUST execute `uv tool install usereq --force --from git+https://github.com/Ogekuri/useReq.git` only on Linux; on non-Linux, it MUST NOT execute `uv` and MUST print the manual command.
- **SRS-344**: MUST implement the following behavior: `--uninstall` on Linux MUST execute `uv tool uninstall usereq` and MUST run release-check cache cleanup per SRS-346; on non-Linux, it MUST NOT execute `uv` and MUST print the manual command.
- **SRS-345**: MUST persist startup release-check idle-state at `~/.cache/usereq/check_version_idle-time.json`; idle-state writes MUST create parent directories; `--ver`/`--version` MUST force the HTTP release-check and bypass idle gating.
- **SRS-346**: MUST implement the following behavior: On Linux, `--uninstall` MUST delete `~/.cache/usereq/check_version_idle-time.json` when present and MUST remove `~/.cache/usereq` only when the directory is empty.
- **SRS-348**: MUST execute the startup HTTP release-check only when the idle-state file is missing, the persisted `idle_until_timestamp` is expired, or `--ver`/`--version` is active; otherwise it MUST skip the request.
- **SRS-349**: MUST persist a 3600-second idle-delay after a successful startup HTTP release-check; when the fetched version is newer than the installed version, it MUST print a bright-green stderr message `New version available: installed <installed_version>, latest <latest_version>.`.
- **SRS-350**: MUST print a bright-red stderr diagnostic for every startup release-check failure and MUST rewrite `~/.cache/usereq/check_version_idle-time.json` with a newly calculated `idle_until_timestamp` on every failure.
- **SRS-351**: MUST use an 86400-second idle-delay for startup release-check API call failures (`HTTPError`, `URLError`, `TimeoutError`); all other startup release-check failures MUST use the default 3600-second idle-delay.
- **SRS-359**: MUST use `usereq` as the `docs-dir` default value when `~/.config/usereq/config.json` stores no `docs-dir` entry.
- **SRS-360**: MUST resolve `GUIDELINES_DIR` as the user-home-relative directory `~/.pi/agent/npm/node_modules/pi-usereq/src/resources/guidelines`, which MUST NOT be configurable.
- **SRS-361**: MUST use `tests` as the `tests-dir` default value when `~/.config/usereq/config.json` stores no `tests-dir` entry.
- **SRS-362**: MUST use `src` as the sole `src-dir` list entry when `~/.config/usereq/config.json` stores no `src-dir` entry.
- **SRS-363**: MUST create missing directories, including missing parents, for the configured `docs-dir`, `tests-dir`, and each `src-dir` entry under `--prj-base` during installation.
- **SRS-387**: MUST persist all configuration state in the single user-global file `~/.config/usereq/config.json` and MUST create missing parent directories on first write.
- **SRS-388**: MUST NOT create, read, or require the `.req` project directory or any per-project configuration file under the project base or git repository path.
- **SRS-398**: MUST support `--set-docs-dir PATH` to persist the project-relative `docs-dir` value in `~/.config/usereq/config.json`.
- **SRS-399**: MUST support repeatable `--set-src-dir PATH` to persist the ordered project-relative `src-dir` list in `~/.config/usereq/config.json`, replacing previous entries.
- **SRS-400**: MUST support `--set-tests-dir PATH` to persist the project-relative `tests-dir` value in `~/.config/usereq/config.json`.
- **SRS-401**: MUST preserve all unrelated configuration keys when `--set-docs-dir`, `--set-src-dir`, or `--set-tests-dir` writes `~/.config/usereq/config.json`.
- **SRS-407**: MUST persist the effective `docs-dir`, `tests-dir`, and `src-dir` values in `~/.config/usereq/config.json` during installation and update.
- **SRS-408**: MUST implement the following behavior: The CLI MUST accept exactly these ten analysis subcommand tokens without the `--` prefix: `files-tokens`, `files-references`, `files-compress`, `files-find`, `tokens`, `references`, `compress`, `find`, `files-static-check`, `static-check`.
- **SRS-409**: MUST NOT parse the legacy `--`-prefixed forms of the SRS-408 subcommands (`--files-tokens`, `--files-references`, `--files-compress`, `--files-find`, `--tokens`, `--references`, `--compress`, `--find`, `--files-static-check`, `--static-check`).
- **SRS-410**: MUST require both `--prj-base` and `--git-base` for every SRS-408 subcommand; absent arguments MUST trigger the SRS-395 error behavior.
- **SRS-411**: MUST implement the following behavior: The CLI help output MUST document every SRS-408 subcommand together with its mandatory `--prj-base` and `--git-base` arguments.
- **SRS-413**: MUST implement the following behavior: `--disable PROVIDER` MUST remove all persisted specs of `PROVIDER` from the `"providers"` array; absent specs MUST leave the configuration unchanged.
- **SRS-414**: MUST implement the following behavior: `--disable-static-check LANG=MODULE[,CMD[,PARAM...]]` MUST remove entries matching the SRS-301 identity tuple; `--disable-static-check LANG` MUST remove the whole canonical language key.
- **SRS-415**: MUST implement the following behavior: `--enable-static-check` and `--disable-static-check` MUST only update the `"static-check"` key in `~/.config/usereq/config.json` and MUST NOT require `--prj-base`.
- **SRS-416**: MUST implement the following behavior: The `show` subcommand MUST print the active configuration in tabular form, including `docs-dir`, `tests-dir`, `src-dir`, `auto-install`, enabled providers, and enabled static-check entries.
- **SRS-417**: MUST implement the following behavior: For every enabled provider, `show` MUST print a dedicated table reporting the installation status of the `prompts`, `agents`, and `skills` components detected from user-level directories.
- **SRS-418**: MUST implement the following behavior: The `install` subcommand MUST install or update the providers persisted under `"providers"`, MUST require `--prj-base`, and MUST print the installation summary report.
- **SRS-419**: MUST implement the following behavior: The `uninstall` subcommand MUST remove `req-*` artifacts of the providers persisted under `"providers"` per SRS-390 semantics.
- **SRS-420**: MUST implement the following behavior: `auto-install` MUST default to enabled; `--disable-auto-install` MUST persist `"auto-install": false` and `--enable-auto-install` MUST persist `"auto-install": true` in `~/.config/usereq/config.json`.
- **SRS-421**: MUST implement the following behavior: When `--upgrade` succeeds and `auto-install` is enabled, the CLI MUST execute the provider installation flow with persisted providers; when `--prj-base` is absent it MUST print an English stderr warning and skip.
- **SRS-422**: MUST implement the following behavior: `--disable-static-check` and `--disable` with unknown language or provider tokens MUST print an English error and exit with code 1.

### 3.3 Provider Resource Generation
- **SRS-381**: MUST install provider prompts, agents, and skills into user-level CLI configuration directories under the user HOME directory and MUST NOT write into project or git-repository directories.
- **SRS-382**: MUST install provider `claude` prompts to `~/.claude/commands/req`, agents to `~/.claude/agents`, and skills to `~/.claude/skills`.
- **SRS-383**: MUST install provider `codex` prompts to `~/.codex/prompts` and skills to `~/.codex/skills`.
- **SRS-384**: MUST install provider `antigravity` TOML prompt commands to `~/.antigravity/commands/req` and skills to `~/.antigravity/skills`.
- **SRS-385**: MUST install provider `opencode` prompts to `~/.config/opencode/command`, agents to `~/.config/opencode/agent`, and skills to `~/.config/opencode/skill`.
- **SRS-386**: MUST install provider `pi` prompts to `~/.pi/agent/prompts` and skills to `~/.pi/agent/skills`.
- **SRS-095**: MUST generate `SKILL.md` for each skill subdirectory of every enabled provider using prompt body substituted with only `%%GUIDELINES_FILES%%`, `%%GUIDELINES_PATH%%`, and `%%ARGS%%` tokens, and provider-resolved YAML front matter.
- **SRS-368**: MUST set `SKILL.md` YAML `name` to `req-<prompt_name>` and `description` to the YAML-escaped output of `extract_skill_description(prompt_frontmatter)`.
- **SRS-389**: MUST NOT emit `model`, `tools`, or `allowed-tools` fields in generated prompt, agent, command, or skill artifacts.
- **SRS-402**: MUST render the `%%GUIDELINES_PATH%%` substitution as the home-relative `~/`-prefixed GUIDELINES_DIR path ending with `/`.
- **SRS-403**: MUST render the `%%GUIDELINES_FILES%%` substitution as a comma-separated list of home-relative `~/`-prefixed guideline file paths.
- **SRS-404**: MUST NOT copy, create, update, or delete guideline files in project or user directories.
- **SRS-371**: MUST implement the following behavior: When `src/usereq/resources/prompts/flowchart.md` exists, provider resource generation MUST emit `req-flowchart` artifacts for every enabled provider/artifact combination supported by packaged prompt templates.

- **SRS-353**: MUST implement the following behavior: Provider `pi` prompt installation MUST write `req-<prompt_name>.prompt.md` files with `description` and optional `argument-hint` front matter under `~/.pi/agent/prompts`.

- **SRS-354**: MUST implement the following behavior: Provider `pi` skill installation MUST write `req-<prompt_name>/SKILL.md` files under `~/.pi/agent/skills`.

- **SRS-366**: MUST implement the following behavior: `scripts/test-install.sh` MUST pass `--enable pi:prompts,skills` to `scripts/req.sh` during its configuration run and MUST invoke the `install` subcommand for the installation run.

- **SRS-367**: MUST implement the following behavior: `scripts/test-install.sh` MUST isolate `HOME` to a disposable directory and delete `~/.pi/agent/prompts` and `~/.pi/agent/skills` inside it before its clean-install execution path.

- **SRS-263**: MUST implement the following behavior: The CLI MUST treat files under `src/usereq/resources/prompts` as read-only package inputs and MUST NOT create, modify, overwrite, rename, or delete files in that directory.

### 3.4 Removal and Cleanup
- **SRS-390**: MUST implement the following behavior: The `--remove` command MUST load `providers` from the global configuration file and delete `req-*` artifacts from user-level provider directories only.

### 3.5 CI/CD Release Workflow
- **SRS-128**: MUST implement the following behavior: The workflow MUST build Python package (sdist and wheel) in `dist/`.
- **SRS-129**: MUST implement the following behavior: The workflow MUST create GitHub Release for the tag and load assets from `dist/`.
- **SRS-130**: MUST implement the following behavior: The workflow MUST generate artifact certifications for files in `dist/`.
- **SRS-268**: MUST implement the following behavior: The `.github/workflows/release-uvx.yml` workflow MUST define `workflow_dispatch` under `on` in addition to tag-push triggers so releases MAY be launched manually without altering automatic tag-trigger behavior.

### 3.5.1 Package Distribution and Resource Inclusion
- **SRS-272**: MUST implement the following behavior: The `[tool.setuptools.package-data]` section in `pyproject.toml` MUST enumerate only `resources/prompts/*.md`, `resources/docs/*.md`, and `resources/prompts-version.txt`.
- **SRS-273**: MUST implement the following behavior: The `[tool.setuptools.package-data]` section in `pyproject.toml` MUST NOT list glob patterns that reference non-existent directories under `src/usereq/resources/`.
- **SRS-274**: MUST implement the following behavior: The built distribution (sdist and wheel) MUST include all files under `src/usereq/resources/` that are required for program operation, ensuring congruent behavior between local development execution, `uv`-installed package execution, and `uvx` live execution.

### 3.6 Source Analysis Core
- **SRS-131**: MUST implement the following behavior: The `usereq.source_analyzer` module MUST support 20 programming languages: C (`.c`), C++ (`.cpp`), C# (`.cs`), Elixir (`.ex`), Go (`.go`), Haskell (`.hs`), Java (`.java`), JavaScript (`.js`, `.mjs`), Kotlin (`.kt`), Lua (`.lua`), Perl (`.pl`), PHP (`.php`), Python (`.py`), Ruby (`.rb`), Rust (`.rs`), Scala (`.scala`), Shell (`.sh`), Swift (`.swift`), TypeScript (`.ts`), and Zig (`.zig`).
- **SRS-133**: MUST implement the following behavior: Each recognized element MUST contain: element type, initial row, final row, source code extract (maximum 5 rows), optional name, optional signature, optional visibility, optional parent name, optional inheritance, hierarchical depth.
- **SRS-143**: MUST implement the following behavior: The `usereq.source_analyzer` module MUST extract the documentation comment blocks associated with each construct and store them in `SourceElement` for the Doxygen parsing downstream.

### 3.7 Token Counting

### 3.8 Reference Markdown Generation

### 3.9 Source Compression

### 3.10 Construct Extraction and Command Operations
- **SRS-177**: MUST implement the following behavior: The `references` command MUST select candidate files from `git ls-files` output under `src-dir` values loaded from `~/.config/usereq/config.json`, then keep only supported extensions from SRS-131.
- **SRS-179**: MUST implement the following behavior: The `compress` command MUST select candidate files from `git ls-files` output under `src-dir` values loaded from `~/.config/usereq/config.json`, then keep only supported extensions from SRS-131.
- **SRS-180**: MUST implement the following behavior: For `references`, `compress`, `find`, and `static-check`, `EXCLUDED_DIRS` MUST contain only directory names that are not already excluded by `.gitignore`.
- **SRS-181**: MUST implement the following behavior: Source-file selection for `references` and `compress` MUST be derived from `git ls-files` relative paths and MUST NOT rely on recursive filesystem walking.

### 3.11 Doxygen Parsing and Field Emission
- **SRS-213**: MUST implement the following behavior: The parser MUST recognize these Doxygen tags: @brief, @details, @param, @param[in], @param[out], @param[in,out], @return, @retval, @exception, @throws, @warning, @deprecated, @note, @see, @sa, @satisfies, @pre, @post.

### 3.12 Bundled Prompts Update Script
- **SRS-375**: `scripts/prompts-update.sh` MUST fully synchronize the upstream `src/prompts` directory of `https://github.com/Ogekuri/Prompts` into `src/usereq/resources/prompts`, overwriting existing files and removing files absent upstream.
- **SRS-376**: `scripts/prompts-update.sh` MUST resolve the newest upstream release through the GitHub Releases API, falling back to the newest version-sorted tag reachable from `develop`, then the `develop` head.
- **SRS-377**: `scripts/prompts-update.sh` MUST print the resolved release version and the stored version before modifications, and MUST require exact input `Y` to proceed; any other input MUST abort without modifications.
- **SRS-378**: `scripts/prompts-update.sh` MUST report `unknown` for a missing or empty version marker and MUST write the resolved release version to `src/usereq/resources/prompts-version.txt` only after successful synchronization.
- **SRS-379**: `scripts/prompts-update.sh` MUST clone the upstream `develop` branch into a temporary directory using the `.git` URL first and the plain URL as fallback, and MUST remove temporary directories on every exit path.
- **SRS-380**: `scripts/prompts-update.sh` MUST preserve upstream file timestamps during synchronization and MUST NOT modify any repository content outside `src/usereq/resources/prompts` and `src/usereq/resources/prompts-version.txt`.

## 4. Test Requirements

### 4.1 Test and Verification Requirements
- **SRS-231**: MUST implement the following behavior: Every file in `tests/fixtures/` MUST include one file-level Doxygen block with `@file`, `@brief`, and `@details`, and MUST retain at least five construct-level blocks with `@brief`, `@details`, `@param`, and `@return`.
- **SRS-233**: MUST implement the following behavior: The project MUST include `tests/fixtures/`-based Doxygen tests that, for each fixture file, extract all the constructions present compatible with SRS-187, validate the Doxygen fields expected for each construct, and verify that the comment association→built is correct for both pre-built comments and post-built comments when allowed by the language syntax.
- **SRS-234**: MUST verify in `tests/test_files_commands.py` that `files-references` outputs Doxygen field bullets with original tags from SRS-213 (`@brief` ... `@post`) and never emits converted labels like `Brief:`.
- **SRS-235**: MUST verify in `tests/test_files_commands.py` that `references` outputs Doxygen field bullets with original tags from SRS-213 (`@brief` ... `@post`) and never emits converted labels like `Brief:`.
- **SRS-236**: MUST verify command-level `files-find` outputs Doxygen field bullets using original tags from SRS-213 (`@brief` ... `@post`) with SRS-220 placement and SRS-221 order, never converted labels.
- **SRS-237**: MUST verify command-level `find` outputs Doxygen field bullets using original tags from SRS-213 (`@brief` ... `@post`) with SRS-220 placement, SRS-221 order, and no converted labels.
- **SRS-405**: MUST include unit tests in `tests/test_cli.py` verifying that commands requiring `--prj-base` or `--git-base` exit with code 1 when the required argument is absent.
- **SRS-406**: MUST include unit tests in `tests/test_cli.py` verifying that `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` persist their keys and preserve unrelated configuration keys.
- **SRS-284**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `--enable PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]` parsing accepts valid specs and rejects unknown providers, artifacts, or options with exit code 1.
- **SRS-285**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that multiple `--enable` specs correctly enable distinct per-provider artifact types and per-provider options independently.
- **SRS-286**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `--enable` specs are persisted to `~/.config/usereq/config.json` under the `"providers"` key and restored by the `install` command.
- **SRS-287**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that provider-scoped `prompts-use-agents` from `--enable` specs is applied independently to each targeted provider.
- **SRS-288**: MUST persist only the configuration keys `docs-dir`, `tests-dir`, `src-dir`, `providers`, `static-check`, and `auto-install` in `~/.config/usereq/config.json`.
- **SRS-293**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `Prompts Installed` content wraps with a maximum display width of 50 characters.
- **SRS-294**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `Modules Installed` renders one module-entry line per active `--enable` artifact item using `artifact` without options or `artifact:options` when applicable options exist.
- **SRS-297**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that each `Modules Installed` line preserves parsed artifact-local option order and appended applicable provider-option order, and emits only `artifact` when no options apply.
- **SRS-298**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `Modules Installed` does not wrap module-entry lines and widths include the longest rendered module-entry line.
- **SRS-374**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that a CLI installation generates representative `req-flowchart` prompt, agent, command, and skill artifacts from the packaged `flowchart.md` template.
- **SRS-412**: MUST include unit tests in `tests/test_cli.py` and `tests/test_files_commands.py` verifying that SRS-408 subcommands dispatch correctly with both `--prj-base` and `--git-base`, and that legacy `--`-prefixed forms are rejected by the parser.
- **SRS-423**: MUST include unit tests in `tests/test_cli.py` verifying `--enable`/`--disable` persistence, `--enable-auto-install`/`--disable-auto-install` persistence, `--disable-static-check` removal, `show` output, `install` dispatch, `uninstall` dispatch, and auto-install after successful `--upgrade`.

## 5. Static Code Analysis Requirements

### 5.1 Static Analysis Feature Overview
- **SRS-240**: MUST implement the following behavior: The `--test-static-check` flag MUST accept an optional list of `[FILES]...` arguments following the subcommand name and optional subcommand-specific options. Each element of `[FILES]` MAY be: a path to a directory (direct children only), a glob pattern (e.g., `path/**/*.py`) with full `**` recursive expansion support, or a specific file path. No custom `--recursive` flag is defined; recursive traversal is expressed via `**` glob syntax.
- **SRS-241**: MUST implement the following behavior: The implementation MUST provide a `StaticCheckBase` (Dummy) class in `src/usereq/static_check.py` that iterates over resolved input files; when `fail_only` mode is inactive, MUST emit `# Static-Check(Dummy): <filename> [OPTIONS]`, emit `Result: OK`, and append exactly one trailing blank line after each per-file block; when `fail_only` mode is active, a passing file MUST produce no output.
- **SRS-242**: MUST implement the following behavior: The implementation MUST provide a `StaticCheckPylance` class derived from `StaticCheckBase` that invokes `pyright` per resolved file via `[sys.executable, '-m', 'pyright', '--pythonpath', sys.executable, <extra_path_args>, <filepath>, <extra_args>...]` subprocess using the active runtime interpreter; when `fail_only` mode is inactive, MUST emit `# Static-Check(Pylance): <filename> [OPTIONS]`, emit `Result: OK` or `Result: FAIL\nEvidence:\n<output>`, and append exactly one trailing blank line after each per-file block; when `fail_only` mode is active, a passing file MUST produce no output and a failing file MUST emit header, `Result: FAIL\nEvidence:\n<output>`, and one trailing blank line.
- **SRS-243**: MUST implement the following behavior: The implementation MUST provide a `StaticCheckRuff` class derived from `StaticCheckBase` that invokes `ruff check` per resolved file via `[sys.executable, '-m', 'ruff', 'check', <filepath>, <extra_args>...]` subprocess using the active runtime interpreter; when `fail_only` mode is inactive, MUST emit `# Static-Check(Ruff): <filename> [OPTIONS]`, emit `Result: OK` or `Result: FAIL\nEvidence:\n<output>`, and append exactly one trailing blank line after each per-file block; when `fail_only` mode is active, a passing file MUST produce no output and a failing file MUST emit header, `Result: FAIL\nEvidence:\n<output>`, and one trailing blank line.
- **SRS-244**: MUST implement the following behavior: The implementation MUST provide a `StaticCheckCommand` class derived from `StaticCheckBase` that requires `command <cmd>`, invokes external tools as `<cmd> [params...] <filename>` with `cmd` availability resolved by the SRS-427 pre-flight; when `fail_only` mode is inactive, MUST emit `# Static-Check(Command[<cmd>]): <filename> [OPTIONS]`, emit pass/fail output, and append exactly one trailing blank line after each per-file block; when `fail_only` mode is active, a passing file MUST produce no output and a failing file MUST emit header, `Result: FAIL\nEvidence:\n<output>`, and one trailing blank line.
- **SRS-245**: MUST implement the following behavior: All static-check classes MUST resolve `[FILES]` input using glob expansion (with `**` recursive support always enabled) for patterns, and direct-children-only traversal for bare directory entries, collecting only regular files. If the resolved file list is empty, the command MUST print a warning to stderr and exit with code 0.

### 5.2 Static Analysis Test Requirements
- **SRS-247**: MUST implement the following behavior: The project MUST include `tests/test_static_check.py` with unit tests for: `StaticCheckBase` (Dummy) output format with one trailing blank separator line per file block; `StaticCheckPylance` and `StaticCheckRuff` OK/FAIL branches with mocked subprocess; pyright command composition including `--pythonpath sys.executable` and excluding `--extra-path`; absence of `.venv` interpreter probing; `StaticCheckCommand` availability check and OK/FAIL branches with mocked subprocess; glob pattern resolution including `**` recursive expansion; direct-children-only directory resolution; empty-file-list warning behavior; `fail_only` mode suppressing all output on pass for each checker class.

### 5.3 Static Analysis Configuration Requirements
- **SRS-248**: MUST implement the following behavior: The CLI MUST support repeatable `--enable-static-check SPEC` (`LANG=MODULE[,CMD[,PARAM...]]`), and each SPEC occurrence MUST append one static-check entry under the canonical language key in `~/.config/usereq/config.json` key `"static-check"`.
- **SRS-249**: MUST implement the following behavior: `--enable-static-check` MUST accept language names case-insensitively; the 20 valid canonical language names are: Python, C, C++, C#, Rust, JavaScript, TypeScript, Java, Go, Ruby, PHP, Swift, Kotlin, Scala, Lua, Shell, Perl, Haskell, Zig, Elixir; any unknown language name MUST produce a `ReqError` with exit code 1.
- **SRS-250**: MUST implement the following behavior: `--enable-static-check` MUST accept a module name (case-insensitive) as the first comma-separated token after `=`: Dummy, Pylance, Ruff, or Command; for Command the second comma-separated token is the mandatory `cmd` binary; during non-`--update` initialization that does not load config values, Command `cmd` MUST resolve to an executable program (`shutil.which`) or the command MUST fail with `ReqError` exit code 1 before any configuration is persisted; all subsequent comma-separated tokens are `params` stored as a JSON array, commas inside single-quoted or double-quoted tokens MUST NOT split parameters, and surrounding single or double quotes on each token MUST be stripped before persistence; unknown module names MUST produce a `ReqError` with exit code 1.
- **SRS-251**: MUST implement the following behavior: When `--enable-static-check` is specified multiple times, entries MUST be preserved in insertion order per canonical language; an entry structurally identical (`module`, `cmd`, and `params` fields all equal) to an already-accumulated entry for the same canonical language MUST be silently discarded.
- **SRS-301**: MUST implement the following behavior: When `--enable-static-check` is invoked against an existing global configuration file, the command MUST load and preserve all pre-existing `"static-check"` entries without removal; for each new CLI-specified entry, presence MUST be decided by exact tuple match `(canonical language, module, cmd, params)` in the loaded config; if present discard, otherwise append.
- **SRS-252**: MUST implement the following behavior: When `--enable-static-check` is used during installation or update, the global configuration file key `"static-check"` MUST be a JSON object keyed by canonical language name, and each language value MUST be a non-empty JSON array of entry objects with required `"module"` and optional `"cmd"`/`"params"` fields.

### 5.4 Static Analysis Execution Commands
- **SRS-253**: MUST support `files-static-check FILE [FILE ...]` as a subcommand per SRS-408 requiring `--prj-base` and `--git-base`; for each FILE it MUST resolve the absolute path, detect the language, load the language array from `"static-check"`, and execute all configured entries sequentially with `fail_only` mode active and a dispatch context containing the mandatory `--prj-base` value.
- **SRS-254**: MUST implement the following behavior: When `--files-static-check` cannot locate `~/.config/usereq/config.json`, the command MUST print a warning to stderr, apply the SRS-424 default static-check configuration, and continue with SRS-255 exit-code semantics.
- **SRS-255**: MUST implement the following behavior: The `--files-static-check` command exit code MUST be 0 when all checked files pass (or no files are checked), and 1 when at least one file fails static analysis.
- **SRS-256**: MUST support `static-check` as a project-scan subcommand per SRS-408 requiring `--prj-base` and `--git-base`, with file selection from `git ls-files` under configured `src-dir` values and the `tests-dir` value plus SRS-131/SRS-180 filtering; all checks MUST execute with `fail_only` mode active and dispatch context containing `--prj-base`.
- **SRS-257**: MUST implement the following behavior: The `static-check` command exit code MUST be 0 when all checked files pass (or no files are checked), and 1 when at least one file fails static analysis.
- **SRS-336**: MUST implement the following behavior: The `--static-check` command MUST load the `tests-dir` value from `~/.config/usereq/config.json` and append it to the `src-dir` list for file selection; if `tests-dir` is missing or invalid the command MUST skip test directory inclusion without error.
- **SRS-424**: MUST apply the SRS-425 and SRS-426 default static-check configuration when the configuration stores no `"static-check"` entry; a present entry, including an empty object, MUST suppress the defaults.
- **SRS-425**: MUST default language `C` to Command `cppcheck --error-exitcode=1 --enable=warning,style,performance,portability --std=c11` plus Command `clang-format --dry-run --Werror`, and `C++` to the same entries with `--std=c++20`.
- **SRS-426**: MUST default language `JavaScript` to Command `node --check`, `TypeScript` to Command `eslint`, and `Python` to the `Pylance` and `Ruff` modules.
- **SRS-427**: MUST pre-flight every static checker before execution: `Dummy` is always available, `Pylance` and `Ruff` require their module in the active interpreter, and `Command` requires `shutil.which(cmd)` resolution.
- **SRS-428**: MUST report an unavailable checker as `Result: FAIL` with English evidence identifying the missing checker or binary, MUST NOT abort, and MUST continue executing the remaining checks.
### 5.5 Static Analysis Dispatch Implementation Requirements
- **SRS-258**: MUST implement the following behavior: The implementation MUST provide a `STATIC_CHECK_LANG_CANONICAL` dict in `src/usereq/static_check.py` mapping lowercase language identifiers (including common aliases: `cpp` for C++, `csharp` for C#, `js` for JavaScript, `ts` for TypeScript, `sh` for Shell) to canonical language names from SRS-249.
- **SRS-259**: MUST implement the following behavior: The implementation MUST provide a `STATIC_CHECK_EXT_TO_LANG` dict in `src/usereq/static_check.py` mapping file extensions to canonical language names, using the same 20-language extension set as SRS-131.
- **SRS-260**: MUST implement the following behavior: The implementation MUST provide a `parse_enable_static_check(spec: str) -> tuple[str, dict]` function in `src/usereq/static_check.py` that: splits on the first `=`, validates the language (case-insensitive) and module (case-insensitive), tokenizes the right side as a comma-separated list to extract MODULE, optional `cmd` (for Command), and `params`, treats commas inside single-quoted or double-quoted tokens as literal characters, strips surrounding single or double quotes from each token, and returns `(canonical_lang, config_dict)`.
- **SRS-261**: MUST implement the following behavior: The implementation MUST provide a `dispatch_static_check_for_file(filepath: str, lang_config: dict, *, fail_only: bool = False, project_base: Optional[Path] = None) -> int` function in `src/usereq/static_check.py` that: reads `module`, `cmd`, and `params` from `lang_config`; instantiates the appropriate checker class (`StaticCheckBase`, `StaticCheckPylance`, `StaticCheckRuff`, or `StaticCheckCommand`) passing `fail_only`; forwards `project_base` to `StaticCheckPylance`; and calls `run()` on a single-element file list.

### 5.6 Static Analysis Configuration and Dispatch Test Requirements
- **SRS-262**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_static_check.py` for parser/dispatcher behavior plus multi-entry language arrays, including repeated `Command` entries for one language and sequential execution checks for `--files-static-check` and `--static-check`.
- **SRS-337**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_static_check.py` verifying that `--static-check` includes files from both `src-dir` and `tests-dir` directories in its file selection.
- **SRS-338**: MUST implement the following behavior: `pyproject.toml` `[project].dependencies` MUST include `ruff` and `pyright` as runtime dependencies so that static-analysis tools are distributed and installed with the package.
- **SRS-339**: MUST implement the following behavior: `StaticCheckPylance` and `StaticCheckRuff` MUST invoke their respective tools via `[sys.executable, '-m', '<tool_module>', ...]` subprocess commands using the current process interpreter (uv tool/uvx runtime when executed via uv), MUST NOT require external PATH resolution, and MUST NOT require project `.venv` discovery.
- **SRS-341**: MUST implement the following behavior: `StaticCheckPylance` MUST NOT pass any `--extra-path` argument to pyright and MUST invoke pyright using only the fixed interpreter/module command form and target filepath.
- **SRS-340**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_dependency_manifests.py` verifying that `ruff` and `pyright` are declared in `pyproject.toml` `[project].dependencies`.
- **SRS-429**: MUST include unit tests in `tests/test_static_check.py` verifying the SRS-424 default static-check resolution and the SRS-427/SRS-428 pre-flight failure and continuation behavior.

## 6. Git Integration and Worktree Management Requirements

### 6.1 Runtime Path Resolution
- **SRS-391**: MUST execute every git-integration operation with the mandatory `--git-base` directory as working directory and MUST NOT derive git context from the current working directory.
- **SRS-392**: MUST accept `--prj-base PATH` as the sole command-line source of the project base used for project file operations.
- **SRS-393**: MUST accept `--git-base PATH` as the sole command-line source of the git repository base used for git operations.
- **SRS-394**: MUST NOT persist `--prj-base` or `--git-base` in `~/.config/usereq/config.json` and MUST NOT load them from it.
- **SRS-395**: MUST print an English error to stderr and exit with code 1 when a dispatched command requires `--prj-base` or `--git-base` and that argument is absent.
- **SRS-396**: MUST require `--prj-base` for the `install` command, `--update`, `references`, `compress`, `tokens`, `find`, `static-check`, `files-tokens`, `files-references`, `files-compress`, `files-find`, `files-static-check`, `--docs-check`, `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir`.
- **SRS-397**: MUST require `--git-base` for `--git-check`, `--git-wt-name`, `--git-wt-create`, and `--git-wt-delete`, and for every SRS-408 subcommand per SRS-410.
- **SRS-310**: MUST implement the following behavior: When the global configuration file is loaded, ALL key-value parameters MUST be loaded and available to CLI command functions.

### 6.2 Git Check Command
- **SRS-311**: MUST support `--git-check` as a command that requires the mandatory `--git-base` argument.
- **SRS-312**: MUST implement the following behavior: The `--git-check` command MUST execute `git rev-parse --is-inside-work-tree && ! git status --porcelain | grep -q . && { git symbolic-ref -q HEAD || git rev-parse --verify HEAD ; }` in the runtime-resolved git repository root, MUST print no output on success, and on non-zero exit MUST print `ERROR: Git status unclear!\n` to stdout and exit with non-zero code.

### 6.3 Docs Check Command
- **SRS-313**: MUST support `--docs-check` as a command that requires the mandatory `--prj-base` argument.
- **SRS-314**: MUST construct `DOC_PATH` as the `--prj-base` directory joined with the `docs-dir` value from `~/.config/usereq/config.json` and verify existence of `REQUIREMENTS.md`, `WORKFLOW.md`, and `REFERENCES.md` in sequential order.
- **SRS-315**: MUST implement the following behavior: If `DOC_PATH/REQUIREMENTS.md` does not exist, `--docs-check` MUST print `ERROR: File <DOC_PATH>/REQUIREMENTS.md does not exist, generate it with the /req-write prompt!\n` to stdout and exit with non-zero code.
- **SRS-316**: MUST implement the following behavior: If `DOC_PATH/WORKFLOW.md` does not exist, `--docs-check` MUST print `ERROR: File <DOC_PATH>/WORKFLOW.md does not exist, generate it with the /req-workflow prompt!\n` to stdout and exit with non-zero code.
- **SRS-317**: MUST implement the following behavior: If `DOC_PATH/REFERENCES.md` does not exist, `--docs-check` MUST print `ERROR: File <DOC_PATH>/REFERENCES.md does not exist, generate it with the /req-references prompt!\n` to stdout and exit with non-zero code.

### 6.4 Git Worktree Name Command
- **SRS-318**: MUST support `--git-wt-name` as a command that requires the mandatory `--git-base` argument.
- **SRS-319**: MUST implement the following behavior: The `--git-wt-name` command MUST print exactly `useReq-<PROJECT_NAME>-<ORIGINAL_BRANCH>-<EXECUTION_ID>` where `<PROJECT_NAME>` is the basename of the runtime-resolved git repository root, `<ORIGINAL_BRANCH>` is the current git branch name with characters incompatible with Linux or Windows paths replaced by `-`, and `<EXECUTION_ID>` is the current timestamp formatted as `YYYYMMDDHHmmss`.

### 6.5 Git Worktree Create Command
- **SRS-320**: MUST support `--git-wt-create WT_NAME` as a command that requires the mandatory `--git-base` argument; `WT_NAME` is mandatory.
- **SRS-321**: MUST implement the following behavior: The `--git-wt-create` command MUST validate that `WT_NAME` contains only characters compatible with both Linux and Windows directory names; if invalid, it MUST print `ERROR: Invalid worktree/branch name: <WT_NAME>.\n` and exit with non-zero code.
- **SRS-322**: MUST implement the following behavior: The `--git-wt-create` command MUST execute `git worktree add "<parent-path>/<WT_NAME>" -b <WT_NAME>` from within the runtime-resolved git repository root.
- **SRS-331**: MUST implement the following behavior: The `--git-wt-create` command MUST NOT change the current directory on success or failure; if post-create operations fail, it MUST rollback created worktree and branch and exit with non-zero code.
- **SRS-335**: MUST check for a `.venv` directory under `--prj-base` first when provided, otherwise under `--git-base`; when found and the destination is absent, it MUST copy `.venv` preserving its relative path from the git repository root.

### 6.6 Git Worktree Delete Command
- **SRS-326**: MUST support `--git-wt-delete WT_NAME` as a command that requires the mandatory `--git-base` argument; `WT_NAME` is mandatory.
- **SRS-327**: MUST implement the following behavior: The `--git-wt-delete` command MUST validate only exact targets for `WT_NAME`: branch ref `refs/heads/<WT_NAME>` and worktree path `"<parent-path>/<WT_NAME>"`; substring or partial-name matches MUST NOT be accepted.
- **SRS-328**: MUST implement the following behavior: The `--git-wt-delete` command MUST force-remove only the exact target worktree and exact target branch using git commands, remaining robust when the target worktree contains pending/uncommitted changes.
- **SRS-332**: MUST implement the following behavior: The `--git-wt-delete` command MUST NOT execute explicit file-system deletions of worktree content paths (for example `.req`, `.claude`, `.codex`), and MUST rely only on `git worktree remove` and `git branch -D`.

### 6.7 Git Repository Path Commands
- **SRS-333**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-334**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-347**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.

### 6.8 Git Integration Test Requirements
- **SRS-329**: MUST include unit tests in `tests/test_cli.py` verifying that git-integration commands execute git operations with `--git-base` as working directory.
- **SRS-330**: MUST include unit tests in `tests/test_cli.py` verifying the `--git-check`, `--docs-check`, `--git-wt-name`, `--git-wt-create` (including `.venv` copy behavior), and `--git-wt-delete` commands behave per their respective requirements.
