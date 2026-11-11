---
title: "useReq Requirements"
description: "Software Requirements Specification"
date: "2026-11-11"
version: 1.21
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
- Primary interface: CLI (`req`, `usereq`, `cli-usereq`).
- Functional domains: user-level CLI resource generation, global configuration persistence, source analysis, token counting, compression, construct extraction, Doxygen field extraction, and git worktree management.
- Out-of-scope for this SRS rewrite: source-code modification.

### 1.3 Components and Dependencies
- Runtime: Python 3.11+.
- Core libraries: `argparse`, `pathlib`, `json`, `re`, `os`, `shutil`, `subprocess`, `urllib`.
- Tokenization: `tiktoken` (`cl100k_base` default).
- Workflow automation: `.github/workflows/release-pypi.yml`.

### 1.4 Project Structure (evidence tree)
```text
.
├── docs/
│   ├── REQUIREMENTS.md
│   ├── REFERENCES.md
│   └── WORKFLOW.md
├── .github/workflows/
│   └── release-pypi.yml
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
│       ├── guidelines/
│       ├── prompts/
│       └── templates/
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
- **SRS-034**: MUST accept `--upgrade` and `--uninstall`; provider configuration MUST remain exclusive to repeatable `--enable PROVIDER`; removed legacy flags, including `--provider`, `--enable-provider`, `--disable-provider`, `--base`, `--here`, `--get-base-path`, `--docs-dir`, `--src-dir`, `--tests-dir`, `--guidelines-dir`, `--add-guidelines`, `--upgrade-guidelines`, `--update`, and `--remove`, MUST NOT be parsed.
- **SRS-035**: MUST implement the following behavior: The `install` command MUST require at least one enabled provider persisted under `"providers"`; otherwise it MUST print an English error and exit code 4. Each enabled provider installs skills only.
- **SRS-036**: MUST implement the following behavior: The installation summary table MUST include rows only for providers whose skills were installed during the current invocation.
- **SRS-049**: MUST implement the following behavior: Immediately after the SRS-513/SRS-514 resource report, CLI MUST print a Unicode box-drawing installation summary table with bright-red border lines.
- **SRS-290**: MUST implement the following behavior: The `Skills Installed` column MUST use a maximum display width of 50 characters and MUST wrap overflowing content onto subsequent lines.
- **SRS-291**: MUST implement the following behavior: The installation summary table MUST contain exactly the `Provider` and `Skills Installed` columns.
- **SRS-296**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-055**: MUST implement the following behavior: The repository MUST keep `uv.lock` as the canonical committed dependency lockfile for execution, build, development, testing, and static analysis environments, and MUST NOT keep a root `requirements.txt` manifest.
- **SRS-056**: MUST implement the following behavior: `scripts/req.sh` MUST execute the CLI via `uv run python -m usereq.cli` from repository root, MUST forward all user-provided CLI arguments unchanged, and MUST rely on uv-managed runtime environments.
- **SRS-342**: MUST implement the following behavior: `README.md` MUST include a `Requirements` section stating that Astral `uv` tool is required for `scripts/req.sh` and recommended project CLI execution workflows.
- **SRS-352**: MUST implement the following behavior: `README.md` MUST describe only currently supported CLI flags and provider syntax, and MUST NOT describe removed standalone flags or `--enable SPEC` syntax superseded by `--enable PROVIDER`.
- **SRS-264**: MUST implement the following behavior: Runtime dependency declarations in `pyproject.toml` `[project].dependencies` MUST be present in the locked package set defined by `uv.lock`; `[project].dependencies` MUST include `ruff` and `pyright`; `[build-system].requires` MAY be outside `uv.lock`.
- **SRS-064**: MUST load persisted `providers` from `~/.config/usereq/config.json` for the `install` command and the implicit installation flow; if no provider remains enabled, it MUST raise a config-invalid error.
- **SRS-275**: MUST implement the following behavior: The CLI MUST accept a repeatable `--enable PROVIDER` argument as the sole mechanism for provider enablement, accepting only the provider CLI name exactly like `--disable PROVIDER`.
- **SRS-364**: MUST implement the following behavior: `PROVIDER` MUST be one of `antigravity`, `claude`, `codex`, `copilot`, `openclaw`, `opencode`, `pi`.
- **SRS-365**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-276**: MUST implement the following behavior: `--enable` MUST only update `~/.config/usereq/config.json` and MUST NOT install provider artifacts.
- **SRS-278**: MUST implement the following behavior: If an `--enable` or `--disable` token is unknown, invalid, or misplaced, the CLI MUST print an English error message identifying the invalid token and exit with code 1.
- **SRS-279**: MUST implement the following behavior: The CLI MUST persist `--enable PROVIDER` provider names in the `"providers"` JSON array, replacing all previously persisted entries of the named providers while preserving other providers.
- **SRS-280**: MUST implement the following behavior: The bare `install`, `uninstall`, and `show` subcommands MUST be accepted without the `--` prefix and MUST NOT require `--git-base`.
- **SRS-281**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-282**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-343**: MUST implement the following behavior: `--upgrade` MUST execute `uv tool install cli-usereq` from the PyPI index only on Linux; on non-Linux, it MUST NOT execute `uv` and MUST print the manual command.
- **SRS-430**: MUST implement the following behavior: The startup release-check MUST query the PyPI JSON API endpoint `https://pypi.org/pypi/cli-usereq/json` and read `info.version` as the latest version.
- **SRS-344**: MUST implement the following behavior: `--uninstall` on Linux MUST execute `uv tool uninstall cli-usereq` and MUST run release-check cache cleanup per SRS-346; on non-Linux, it MUST NOT execute `uv` and MUST print the manual command.
- **SRS-345**: MUST persist startup release-check idle-state at `~/.cache/usereq/check_version_idle-time.json`; idle-state writes MUST create parent directories; `--ver`/`--version` MUST force the HTTP release-check and bypass idle gating.
- **SRS-346**: MUST implement the following behavior: On Linux, `--uninstall` MUST delete `~/.cache/usereq/check_version_idle-time.json` when present and MUST remove `~/.cache/usereq` only when the directory is empty.
- **SRS-348**: MUST execute the startup HTTP release-check only when the idle-state file is missing, the persisted `idle_until_timestamp` is expired, or `--ver`/`--version` is active; otherwise it MUST skip the request.
- **SRS-349**: MUST persist a 3600-second idle-delay after a successful startup HTTP release-check; when the fetched version is newer than the installed version, it MUST print a bright-green stderr message `New version available: installed <installed_version>, latest <latest_version>.`.
- **SRS-350**: MUST print a bright-red stderr diagnostic for every startup release-check failure and MUST rewrite `~/.cache/usereq/check_version_idle-time.json` with a newly calculated `idle_until_timestamp` on every failure.
- **SRS-351**: MUST use an 86400-second idle-delay for startup release-check API call failures (`HTTPError`, `URLError`, `TimeoutError`); all other startup release-check failures MUST use the default 3600-second idle-delay.
- **SRS-359**: MUST use `usereq/docs` as the `docs-dir` default value when `~/.config/usereq/config.json` stores no `docs-dir` entry.
- **SRS-360**: MUST resolve `GUIDELINES_DIR` as the packaged `resources/guidelines` directory of the running installation, which MUST NOT be configurable.
- **SRS-361**: MUST use `tests` as the `tests-dir` default value when `~/.config/usereq/config.json` stores no `tests-dir` entry.
- **SRS-362**: MUST use `src` as the sole `src-dir` list entry when `~/.config/usereq/config.json` stores no `src-dir` entry.
- **SRS-363**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-387**: MUST persist all configuration state in the single user-global file `~/.config/usereq/config.json` and MUST create missing parent directories on first write.
- **SRS-388**: MUST NOT create, read, or require the `.req` project directory or any per-project configuration file under the project base or git repository path.
- **SRS-398**: MUST support `--set-docs-dir PATH` to persist the project-relative `docs-dir` value in `~/.config/usereq/config.json`.
- **SRS-399**: MUST support repeatable `--set-src-dir PATH` to persist the ordered project-relative `src-dir` list in `~/.config/usereq/config.json`, replacing previous entries.
- **SRS-400**: MUST support `--set-tests-dir PATH` to persist the project-relative `tests-dir` value in `~/.config/usereq/config.json`.
- **SRS-401**: MUST preserve all unrelated configuration keys when `--set-docs-dir`, `--set-src-dir`, or `--set-tests-dir` writes `~/.config/usereq/config.json`.
- **SRS-407**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-408**: MUST implement the following behavior: The CLI MUST accept exactly these ten analysis subcommand tokens without the `--` prefix: `files-tokens`, `files-references`, `files-compress`, `files-find`, `tokens`, `references`, `compress`, `find`, `files-static-check`, `static-check`.
- **SRS-409**: MUST NOT parse the legacy `--`-prefixed forms of the SRS-408 subcommands (`--files-tokens`, `--files-references`, `--files-compress`, `--files-find`, `--tokens`, `--references`, `--compress`, `--find`, `--files-static-check`, `--static-check`).
- **SRS-410**: MUST NOT require `--git-base` for any SRS-408 subcommand; `--prj-base` MUST be mandatory exactly for the SRS-408 subcommands listed in SRS-396, and its absence MUST trigger the SRS-395 error behavior.
- **SRS-411**: MUST implement the following behavior: The CLI help output MUST document every SRS-408 subcommand together with exactly the mandatory base arguments required by SRS-396 and SRS-397.
- **SRS-413**: MUST implement the following behavior: `--disable PROVIDER` MUST remove all persisted entries of `PROVIDER` from the `"providers"` array; absent entries MUST leave the configuration unchanged.
- **SRS-414**: MUST implement the following behavior: `--disable-static-check LANG=MODULE[,CMD[,PARAM...]]` MUST remove entries matching the SRS-301 identity tuple; `--disable-static-check LANG` MUST remove the whole canonical language key.
- **SRS-415**: MUST implement the following behavior: `--enable-static-check` and `--disable-static-check` MUST only update the `"static-check"` key in `~/.config/usereq/config.json` and MUST NOT require `--prj-base`.
- **SRS-416**: MUST implement the following behavior: The `show` subcommand MUST print the active configuration in tabular form, including `docs-dir`, `tests-dir`, `src-dir`, `auto-install`, enabled providers, and enabled static-check entries.
- **SRS-417**: MUST implement the following behavior: The `show` subcommand MUST print exactly one installation-status table titled `Installation Status` covering every enabled provider.
- **SRS-462**: MUST implement the following behavior: The `show` Providers table MUST print every configurable provider with the `CLI`, `Enabled`, and `Skills Path` columns.
- **SRS-463**: MUST implement the following behavior: Each `Skills Path` cell MUST render the home-relative `~/`-prefixed hardcoded provider skills root from SRS-382..SRS-386, SRS-486, and SRS-493.
- **SRS-464**: MUST implement the following behavior: Provider skill installation MUST write `{skills_root}/req-{prompt_name}/SKILL.md` files for every enabled provider.
- **SRS-465**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-466**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-418**: MUST implement the following behavior: The `install` subcommand MUST install or update the providers persisted under `"providers"` and MUST print the installation summary report.
- **SRS-419**: MUST implement the following behavior: The `uninstall` subcommand MUST remove `req-*` skill artifacts of the providers persisted under `"providers"`.
- **SRS-420**: MUST implement the following behavior: `auto-install` MUST default to enabled; `--disable-auto-install` MUST persist `"auto-install": false` and `--enable-auto-install` MUST persist `"auto-install": true` in `~/.config/usereq/config.json`.
- **SRS-421**: MUST implement the following behavior: When `--upgrade` succeeds and `auto-install` is enabled, the CLI MUST execute the provider installation flow with the persisted providers.
- **SRS-450**: MUST implement the following behavior: When post-upgrade auto-install runs and no provider is persisted, the CLI SHOULD print an English stderr warning and skip installation.
- **SRS-422**: MUST implement the following behavior: `--disable-static-check` and `--disable` with unknown language or provider tokens MUST print an English error and exit with code 1.
- **SRS-440**: MUST implement the following behavior: `--upgrade --develop` MUST install the latest tagged GitHub release resolved per SRS-451; without `--develop`/`--dev`, `--upgrade` MUST install from the PyPI index.
- **SRS-445**: MUST implement the following behavior: `--dev` MUST be accepted as an equivalent command-line alias of `--develop` when selecting the GitHub upgrade source for `--upgrade`.
- **SRS-441**: MUST implement the following behavior: `--ver`/`--version` MUST print exactly three stdout lines in order: installed version, PyPI latest version, and GitHub latest version.
- **SRS-442**: MUST implement the following behavior: `--ver`/`--version` MUST query the PyPI JSON API and the GitHub latest-release API bypassing idle gating; unfetchable versions MUST print `unknown`.
- **SRS-518**: MUST implement the following behavior: Each `--ver`/`--version` line MUST render `<LABEL>` left-justified in an 18-character field followed by `: <version>`; labels MUST be `Current Installed`, `Latest @ PyPI`, and `Latest @ GitHub`.
- **SRS-443**: MUST implement the following behavior: `README.md` MUST present PyPI as the primary install/upgrade channel and a dedicated non-primary GitHub section covering GitHub installation and `--develop`/`--dev` upgrades.
- **SRS-446**: MUST implement the following behavior: The CLI help output MUST NOT document removed legacy project-directory persistence and removal flags.
- **SRS-447**: MUST accept the `install` subcommand without `--prj-base`; the `install` subparser MUST NOT define or consume `--prj-base`.
- **SRS-448**: MUST implement the following behavior: The `install` subcommand MUST NOT create project directories, validate project-path containment, or persist `docs-dir`/`tests-dir`/`src-dir` values.
- **SRS-449**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-451**: MUST implement the following behavior: `--upgrade --develop` MUST resolve the installation tag by querying `https://api.github.com/repos/Ogekuri/CLI-useReq/releases/latest` and reading `tag_name`, regardless of the branch holding that tag.
- **SRS-452**: MUST implement the following behavior: On Linux, `--upgrade --develop` MUST execute `uv tool install cli-usereq --from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>`; non-Linux MUST print this manual command and MUST NOT execute `uv`.
- **SRS-453**: MUST implement the following behavior: When the SRS-451 GitHub query fails, `--upgrade --develop` MUST print an English stderr error, MUST NOT execute `uv`, and MUST exit with code 1.
- **SRS-485**: MUST implement the following behavior: The `show` subcommand MUST print providers in alphabetical order by provider name in every provider table.
- **SRS-488**: MUST implement the following behavior: The Providers table `Enabled` cell MUST print `yes` when the provider is enabled and `no` when the provider is disabled.
- **SRS-489**: MUST implement the following behavior: The installation-status table MUST contain one row for every packaged prompt name and enabled provider pair, ordered by prompt name then provider name.
- **SRS-490**: MUST implement the following behavior: Each installation-status `Installed` cell MUST print `OK` when `req-<prompt_name>` exists under the provider skills root and `MISSING` otherwise.
- **SRS-491**: MUST implement the following behavior: Each installation-status row MUST report `Type` `Skill`, the skill name `req-<prompt_name>`, the provider CLI name, and the provider enabled state.
- **SRS-508**: MUST implement the following behavior: `--upgrade` MUST accept the auxiliary `--force` argument that forces full package download and complete reinstallation.
- **SRS-509**: MUST implement the following behavior: `--upgrade --force` MUST execute `uv tool install cli-usereq --force --reinstall --refresh` on Linux only; on non-Linux it MUST print this command and MUST NOT execute `uv`.
- **SRS-510**: MUST implement the following behavior: `--upgrade --develop --force` MUST execute `uv tool install cli-usereq --force --reinstall --refresh --from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` on Linux; non-Linux MUST print this manual command and MUST NOT execute `uv`.
- **SRS-511**: MUST implement the following behavior: The CLI inline help MUST document `--force` as an auxiliary `--upgrade` argument that forces download and complete reinstallation.
- **SRS-512**: MUST implement the following behavior: `README.md` MUST document the `--force` auxiliary argument of `--upgrade` for both PyPI and GitHub develop upgrade channels.
- **SRS-513**: MUST implement the following behavior: When installation completes, the CLI MUST print the home-relative packaged guidelines directory path ending with `/` on one line, then bare guideline file names on the next line.
- **SRS-514**: MUST implement the following behavior: Immediately after SRS-513, the CLI MUST print the home-relative packaged templates directory path ending with `/` on one line, then bare template file names on the next line.
- **SRS-515**: MUST implement the following behavior: Every path printed by the installation completion report MUST be composed lexically and MUST NOT resolve symbolic links.
- **SRS-516**: MUST implement the following behavior: Guideline and template file-name lists MUST enumerate only non-hidden, non-symbolic-link regular files in deterministic sorted order.

### 3.2.1 Configuration Schema, CLI Access, and Tree Rendering
- **SRS-519**: MUST expose configuration display and mutation exclusively through `--print [Path]`, `--info [Path]`, `--print-raw`, `--get Path`, `--set Path Value`, and `--unset Path`.
- **SRS-520**: MUST resolve canonical configuration paths as colon-separated case-sensitive schema tokens and MUST NOT accept the virtual root label `Application_Configuration` inside any CLI path.
- **SRS-521**: MUST define one canonical schema for the `Configuration` section containing `docs-dir`, `tests-dir`, `src-dir`, `providers`, `static-check`, and `auto-install` that drives parsing, validation, defaults, display, and help.
- **SRS-522**: MUST display every configuration node identifier as its exact canonical schema token, byte for byte, with descriptions and statuses appended after the token.
- **SRS-523**: MUST render every section heading in `--print` and `--info` output as `Token - [Path: <full canonical path>]`.
- **SRS-524**: MUST render `--print` and `--info` through one recursive renderer whose `├──`, `└──`, `│   `, and four-space prefixes derive only from real configuration node topology.
- **SRS-525**: MUST render attached detail lines with the owning node continuation prefix and MUST NOT start any detail line with `├── ` or `└── `.
- **SRS-526**: MUST render a requested subtree as its unconnected node heading followed only by that node's details and descendants.
- **SRS-527**: MUST emit `--get` output as JSON only on stdout without labels, tree decoration, or prompts.
- **SRS-528**: MUST emit `--print-raw` as the unmodified bytes of `~/.config/usereq/config.json` without tree formatting, headings, or reformatting.
- **SRS-529**: MUST create missing `~/.config/usereq/config.json` parent directories and initialize the file from schema defaults before running a configuration command when the file is absent.
- **SRS-530**: MUST validate the complete resulting configuration against the schema before any `--set` or `--unset` write and MUST NOT mutate stored values when validation fails.
- **SRS-531**: MUST persist `--set` and `--unset` atomically through a same-directory temporary file using flush, fsync, and atomic replacement while preserving the file mode.
- **SRS-532**: MUST write valid `--get`, `--print`, `--print-raw`, and `--info` payloads to stdout and every diagnostic to stderr with exit code 1 on failure and 0 on success.
- **SRS-533**: MUST accept `:<Idx>` array tokens as non-negative 0-based indices and MUST reject negative or out-of-range indices without mutation.
- **SRS-534**: MUST support `append`, `+`, and `insert:<Idx>` array operations that insert exactly one validated item and keep indices contiguous after deletion.
- **SRS-535**: MUST accept exactly one JSON item for `:<Idx>`, `:append`, `:+`, and `:insert:<Idx>` array writes and a JSON array only for whole-array writes.
- **SRS-536**: MUST reject `--unset` on a required dictionary field without a schema default with an English error and no mutation.
- **SRS-537**: MUST render `--print` parameters as `Token = <JSON value>` followed by `(default)` or `(custom | default: <default>)`, and collections as summaries with attached rectangular tables.
- **SRS-538**: MUST render `--info` parameters as `Token - [Type: constraints] Description` followed by `Default`, `Set cmd`, `Reset cmd`, schema tables, and complete canonical-path command examples.
- **SRS-539**: MUST build every table from measured Unicode display widths with aligned borders and MUST omit tables for empty collections in favor of complete-path action hints.
- **SRS-540**: MUST document `static-check` entry fields through an `Item Schema` table and expose field-level `Configuration:static-check:<Language>:<Idx>:<Field>` write paths.
- **SRS-541**: MUST render every published command example with shell quoting, a complete canonical path, and a value valid under the active schema.
- **SRS-542**: MUST update the shared schema, CLI behavior, `--info` documentation, and tests together whenever configurable options, defaults, constraints, or storage change.

### 3.3 Provider Resource Generation
- **SRS-381**: MUST install provider skills into user-level CLI configuration directories under the user HOME directory and MUST NOT write into project or git-repository directories.
- **SRS-382**: MUST install provider `claude` skills to `~/.claude/skills`.
- **SRS-383**: MUST install provider `codex` skills to `~/.codex/skills`.
- **SRS-384**: MUST install provider `antigravity` skills to `~/.gemini/config/skills`.
- **SRS-385**: MUST install provider `opencode` skills to `~/.config/opencode/skills`.
- **SRS-386**: MUST install provider `pi` skills to `~/.pi/agent/skills`.
- **SRS-095**: MUST generate `SKILL.md` for each skill subdirectory of every enabled provider using prompt body substituted with only `%%TEMPLATE_PATH%%`, `%%GUIDELINES_FILES%%`, `%%GUIDELINES_PATH%%`, `%%DOC_PATH%%`, `%%SRC_PATHS%%`, `%%TEST_PATH%%`, and `%%ARGS%%` tokens, and provider-resolved YAML front matter.
- **SRS-368**: MUST set `SKILL.md` YAML `name` to `req-<prompt_name>` and `description` to the YAML-escaped output of `extract_skill_description(prompt_frontmatter)`.
- **SRS-389**: MUST NOT emit `model`, `tools`, or `allowed-tools` fields in generated skill artifacts.
- **SRS-402**: MUST render the `%%GUIDELINES_PATH%%` substitution as the home-relative `~/`-prefixed GUIDELINES_DIR path ending with `/`.
- **SRS-403**: MUST render the `%%GUIDELINES_FILES%%` substitution as a comma-separated list of home-relative `~/`-prefixed guideline file paths.
- **SRS-498**: MUST render the `%%TEMPLATE_PATH%%` substitution as the home-relative `~/`-prefixed packaged `resources/templates` directory path of the running installation, ending with `/`.
- **SRS-500**: MUST render the `%%DOC_PATH%%` substitution as the configured `docs-dir` value from `~/.config/usereq/config.json`, defaulting per SRS-359.
- **SRS-501**: MUST render the `%%SRC_PATHS%%` substitution as comma-separated backticked `src-dir` entries from `~/.config/usereq/config.json`, each ending with `/`.
- **SRS-502**: MUST render the `%%TEST_PATH%%` substitution as the backticked `tests-dir` value from `~/.config/usereq/config.json`, ending with `/`.
- **SRS-504**: MUST enumerate the `%%GUIDELINES_FILES%%` substitution without following symbolic links, excluding symbolic-link directory entries.
- **SRS-505**: MUST render the `%%GUIDELINES_PATH%%` and `%%TEMPLATE_PATH%%` substitutions as lexical packaged directory paths without resolving symbolic links.
- **SRS-404**: MUST NOT copy, create, update, or delete guideline files in project or user directories.
- **SRS-371**: MUST implement the following behavior: When `src/usereq/resources/prompts/flowchart.md` exists, provider resource generation MUST emit `req-flowchart` skill artifacts for every enabled provider.

- **SRS-353**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.

- **SRS-354**: MUST implement the following behavior: Provider `pi` skill installation MUST write `req-<prompt_name>/SKILL.md` files under `~/.pi/agent/skills`.

- **SRS-366**: MUST implement the following behavior: `scripts/test-install.sh` MUST pass `--enable pi` to `scripts/req.sh` during its configuration run and MUST invoke the `install` subcommand for the installation run.

- **SRS-367**: MUST implement the following behavior: `scripts/test-install.sh` MUST isolate `HOME` to a disposable directory and delete `~/.pi/agent/skills` inside it before its clean-install execution path.

- **SRS-263**: MUST implement the following behavior: The CLI MUST treat files under `src/usereq/resources/prompts` as read-only package inputs and MUST NOT create, modify, overwrite, rename, or delete files in that directory.
- **SRS-467**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-468**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-469**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-470**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-486**: MUST install provider `openclaw` skills to `~/.openclaw/workspace/skills`.
- **SRS-493**: MUST install provider `copilot` skills to `~/.copilot/skills`.

### 3.4 Removal and Cleanup
- **SRS-390**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.

### 3.5 CI/CD Release Workflow
- **SRS-128**: MUST implement the following behavior: The workflow MUST build Python package (sdist and wheel) in `dist/`.
- **SRS-129**: MUST implement the following behavior: The workflow MUST create GitHub Release for the tag and load assets from `dist/`.
- **SRS-130**: MUST implement the following behavior: The workflow MUST generate artifact certifications for files in `dist/`.
- **SRS-268**: MUST implement the following behavior: The `.github/workflows/release-pypi.yml` workflow MUST define `workflow_dispatch` under `on` in addition to tag-push triggers so releases MAY be launched manually without altering automatic tag-trigger behavior.
- **SRS-431**: MUST implement the following behavior: The release automation workflow MUST be defined at `.github/workflows/release-pypi.yml` and the legacy `.github/workflows/release-uvx.yml` file MUST be absent from the repository.
- **SRS-432**: MUST implement the following behavior: On canonical version-tag push, the workflow MUST execute package build, provenance attestation, and GitHub Release creation independently of `origin/master` reachability.
- **SRS-433**: MUST implement the following behavior: The workflow MUST publish the built sdist and wheel to PyPI project `cli-usereq` through the official `pypa/gh-action-pypi-publish` GitHub Action authenticated via GitHub OIDC trusted publishing.
- **SRS-434**: MUST implement the following behavior: The PyPI publish job MUST execute only when the tagged commit is reachable from `origin/master`; tags reachable only from `origin/develop` MUST skip PyPI publication.
- **SRS-455**: MUST execute every JavaScript-based GitHub Action referenced by `.github/workflows/release-pypi.yml` on Node24 runtime or later.
- **SRS-456**: MUST reference `actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v6`, and `actions/download-artifact@v7` majors or later.
- **SRS-457**: MUST reference `astral-sh/setup-uv@v7`, `actions/attest-build-provenance@v3`, `softprops/action-gh-release@v3`, and `mikepenz/release-changelog-builder-action@v6` majors or later.
- **SRS-458**: MUST NOT set `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` or `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` environment overrides in the workflow.

### 3.5.1 Package Distribution and Resource Inclusion
- **SRS-272**: MUST implement the following behavior: The `[tool.setuptools.package-data]` section in `pyproject.toml` MUST enumerate only `resources/guidelines/*`, `resources/prompts/*`, `resources/templates/*`, and `resources/prompts-version.txt`.
- **SRS-273**: MUST implement the following behavior: The `[tool.setuptools.package-data]` section in `pyproject.toml` MUST NOT list glob patterns that reference non-existent directories under `src/usereq/resources/`.
- **SRS-274**: MUST implement the following behavior: The built distribution (sdist and wheel) MUST include every file under `src/usereq/resources/`, ensuring congruent behavior between local development execution, `uv`-installed package execution, and `uvx` live execution.
- **SRS-435**: MUST implement the following behavior: `pyproject.toml` `[project].name` MUST be `cli-usereq`, matching the registered PyPI trusted-publisher project name for repository `Ogekuri/CLI-useReq` and workflow `release-pypi.yml`.
- **SRS-436**: MUST implement the following behavior: `pyproject.toml` `[project].authors` MUST declare `Ogekuri` as the author.
- **SRS-437**: MUST implement the following behavior: `pyproject.toml` `[project.urls]` `Homepage` and `Repository` MUST reference the `https://github.com/Ogekuri/CLI-useReq` repository.
- **SRS-454**: MUST deploy exactly the console-script entry points `req`, `usereq`, and `cli-usereq` declared in `pyproject.toml` `[project.scripts]`, all bound to `usereq.cli:main`.
- **SRS-495**: MUST resolve the packaged document-template directory as `src/usereq/resources/templates` and MUST raise an English error when it is absent or contains no non-hidden files.
- **SRS-497**: MUST bundle the guideline documents as package data under `src/usereq/resources/guidelines`, and the directory MUST contain at least one non-hidden guideline file.

### 3.5.2 Release Build Script and Repository Ignore Policy
- **SRS-546**: MUST implement the following behavior: `scripts/build.sh` MUST resolve the repository root from its own filesystem location and MUST execute every build stage from that root independently of the caller working directory.
- **SRS-547**: MUST implement the following behavior: `scripts/build.sh` MUST verify that the `uv` command is executable and MUST print an English error and exit with code 1 when it is absent.
- **SRS-548**: MUST implement the following behavior: `scripts/build.sh` MUST remove from `dist/` only gitignored entries and MUST preserve every git-tracked or non-ignored file under `dist/`.
- **SRS-549**: MUST implement the following behavior: `scripts/build.sh` MUST build the sdist and wheel into `dist/` via `uv run --project <root> --frozen --with build python -m build --outdir <root>/dist` and MUST exit with a non-zero code when the build fails.
- **SRS-550**: MUST implement the following behavior: `scripts/build.sh` MUST verify after the build that `dist/` contains at least one `.tar.gz` and one `.whl` file and MUST exit with a non-zero code otherwise.
- **SRS-551**: MUST implement the following behavior: `scripts/build.sh` MUST print a summary listing every artifact in `dist/` and MUST exit with code 0 only when every stage succeeds.
- **SRS-552**: MUST implement the following behavior: The `.gitignore` file MUST preserve the inverse exclusion strategy of default exclusions followed by `!` re-inclusion rules.
- **SRS-553**: MUST implement the following behavior: The `.gitignore` file MUST NOT ignore the `dist/` directory itself and MUST ignore `dist/` contents through a targeted rule so build artifacts stay excluded while the directory remains traversable.
- **SRS-554**: MUST implement the following behavior: Git-tracked files inside `dist/` MUST remain versionable and MUST NOT be excluded by the `.gitignore` rules.

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
- **SRS-375**: `scripts/prompts-update.sh` MUST fully synchronize the upstream `src/prompts` directory of `https://github.com/Ogekuri/CLI-Prompts` into `src/usereq/resources/prompts`, overwriting existing files and removing files absent upstream.
- **SRS-376**: `scripts/prompts-update.sh` MUST resolve the newest upstream release through the GitHub Releases API, falling back to the newest version-sorted tag reachable from `develop`, then the `develop` head.
- **SRS-377**: `scripts/prompts-update.sh` MUST print the resolved release version and the stored version before modifications, and MUST require exact input `Y` to proceed; any other input MUST abort without modifications.
- **SRS-378**: `scripts/prompts-update.sh` MUST report `unknown` for a missing or empty version marker and MUST write the resolved release version to `src/usereq/resources/prompts-version.txt` only after successful synchronization.
- **SRS-379**: `scripts/prompts-update.sh` MUST clone the upstream `develop` branch into a temporary directory using the `.git` URL first and the plain URL as fallback, and MUST remove temporary directories on every exit path.
- **SRS-380**: `scripts/prompts-update.sh` MUST preserve upstream file timestamps during synchronization and MUST NOT modify any repository content outside `src/usereq/resources/prompts`, `src/usereq/resources/templates`, and `src/usereq/resources/prompts-version.txt`.
- **SRS-496**: `scripts/prompts-update.sh` MUST fully synchronize the upstream `src/templates` directory of `https://github.com/Ogekuri/CLI-Prompts` into `src/usereq/resources/templates`, overwriting existing files and removing files absent upstream.

### 3.13 Pre-Release Verification Script
- **SRS-471**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST resolve the repository root from its own filesystem location, MUST execute every stage from that root, and MUST NOT depend on the caller working directory.
- **SRS-472**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST accept an optional `--allow-dirty` argument that skips the working-tree cleanliness gate; any other argument MUST produce an English error and exit code 1.
- **SRS-473**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST verify that the `uv` command is executable and MUST print an English error and exit with code 1 when it is absent.
- **SRS-474**: MUST implement the following behavior: Without `--allow-dirty`, `scripts/pre-release-check.sh` MUST print an English error and exit with a non-zero code when `git status --porcelain` output is non-empty.
- **SRS-475**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST run `uv sync --frozen` to synchronize the SRS-055 lockfile environment and MUST exit with a non-zero code when synchronization fails.
- **SRS-476**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST generate the sdist and wheel into `dist/` by executing `scripts/build.sh` and MUST exit with a non-zero code when the build fails.
- **SRS-477**: MUST implement the following behavior: After a successful build, `scripts/pre-release-check.sh` MUST verify that `dist/` contains at least one `.tar.gz` and one `.whl` file and MUST exit with a non-zero code otherwise.
- **SRS-478**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST execute the project `static-check` command with `--prj-base` set to the repository root and MUST exit with a non-zero code when static analysis fails.
- **SRS-479**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST execute the unit-test suite through `uv run pytest` and MUST exit with a non-zero code when any test fails.
- **SRS-480**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST stop at the first failing stage, MUST print `Pre-release check failed at stage <stage>.` on failure, and MUST print `Pre-release check passed.` only when every stage succeeds.
- **SRS-481**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST NOT modify or delete any git-tracked repository file, and build intermediates MUST be confined to the `dist/`, `build/`, and `src/*.egg-info` paths.
- **SRS-482**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST remove the `dist/`, `build/`, `.pytest_cache/`, `src/*.egg-info`, and `src/`- or `tests/`-scoped `__pycache__` directories on every termination path.
- **SRS-483**: MUST implement the following behavior: `scripts/pre-release-check.sh` MUST skip removing any cleanup target containing git-tracked files and MUST print an English warning identifying it.
- **SRS-484**: MUST implement the following behavior: After termination, `scripts/pre-release-check.sh` MUST leave the repository directory containing only git-tracked files and the uv-managed `.venv` environment.

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
- **SRS-284**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `--enable PROVIDER` parsing accepts valid provider names and rejects unknown providers with exit code 1.
- **SRS-285**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that multiple `--enable PROVIDER` occurrences enable distinct providers independently.
- **SRS-286**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `--enable` provider names are persisted to `~/.config/usereq/config.json` under the `"providers"` key and restored by the `install` command.
- **SRS-287**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-288**: MUST persist only the configuration keys `docs-dir`, `tests-dir`, `src-dir`, `providers`, `static-check`, and `auto-install` in `~/.config/usereq/config.json`.
- **SRS-293**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that `Skills Installed` content wraps with a maximum display width of 50 characters.
- **SRS-294**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that the installation summary table renders exactly the `Provider` and `Skills Installed` columns.
- **SRS-297**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-298**: MUST treat this requirement as a removed legacy behavior and keep it unsupported.
- **SRS-374**: MUST implement the following behavior: The project MUST include unit tests in `tests/test_cli.py` verifying that a CLI installation generates representative `req-flowchart` skill artifacts from the packaged `flowchart.md` template.
- **SRS-412**: MUST include unit tests in `tests/test_cli.py` and `tests/test_files_commands.py` verifying that SRS-408 subcommands dispatch correctly with their mandatory base arguments, and that legacy `--`-prefixed forms are rejected by the parser.
- **SRS-423**: MUST include unit tests in `tests/test_cli.py` verifying `--enable`/`--disable` persistence, `--enable-auto-install`/`--disable-auto-install` persistence, `--disable-static-check` removal, `show` output, `install` dispatch, `uninstall` dispatch, and auto-install after successful `--upgrade`.
- **SRS-438**: MUST include unit tests in `tests/test_release_workflow.py` verifying the `.github/workflows/release-pypi.yml` location, the SRS-433 OIDC publication steps, the SRS-434 master-only publication gating, and the SRS-432 build/release independence from master reachability.
- **SRS-439**: MUST include unit tests in `tests/test_dependency_manifests.py` verifying the SRS-435 project name, the SRS-436 author, and the SRS-437 repository URLs in `pyproject.toml`.
- **SRS-444**: MUST include unit tests in `tests/test_update_check.py` verifying the SRS-430 PyPI endpoint, the SRS-343/SRS-440/SRS-509/SRS-510 upgrade commands, and the SRS-441/SRS-442 `--ver` output.
- **SRS-459**: MUST include unit tests in `tests/test_release_workflow.py` verifying the SRS-455 Node24 runtime, the SRS-456/SRS-457 action-major floors, and the SRS-458 opt-out override prohibition.
- **SRS-461**: MUST include unit tests in `tests/test_cli.py` verifying that `install` neither accepts `--prj-base` nor performs project-side operations, and that `--git-wt-create` exits with code 1 without `--prj-base` and copies only `--prj-base/.venv`.
- **SRS-487**: MUST include unit tests in `tests/test_cli.py` verifying that the `show` Providers table renders every configurable provider with `CLI`, `Enabled`, and `Skills Path` columns in alphabetical order.
- **SRS-492**: MUST include unit tests in `tests/test_cli.py` verifying the single `Installation Status` table with `Type`, `Name`, `CLI`, `Enabled`, and `Installed` columns reporting only enabled providers with `OK` and `MISSING` rows.
- **SRS-494**: MUST include unit tests in `tests/test_cli.py` verifying that `codex` skills install to `~/.codex/skills` and `copilot` skills install to `~/.copilot/skills`.
- **SRS-499**: MUST include unit tests in `tests/test_cli.py` verifying installed skills contain no residual `%%TEMPLATE_PATH%%` token and rendered template and guideline paths target the packaged resources of the running installation.
- **SRS-503**: MUST include unit tests in `tests/test_cli.py` verifying installed skills contain no residual `%%DOC_PATH%%`, `%%SRC_PATHS%%`, or `%%TEST_PATH%%` token and render configured directory values.
- **SRS-506**: MUST render the `%%DOC_PATH%%`, `%%SRC_PATHS%%`, and `%%TEST_PATH%%` substitutions from configured values without filesystem resolution.
- **SRS-507**: MUST include unit tests in `tests/test_cli.py` verifying substitution sources exclude or do not resolve symbolic links.
- **SRS-517**: MUST include unit tests in `tests/test_cli.py` verifying that the installation completion report prints guidelines and templates directory paths followed by bare file-name lists without symbolic-link resolution.
- **SRS-543**: MUST include unit tests in `tests/test_config_cli.py` verifying exact renderer output for single child, root siblings, nested siblings, detail-bearing leaves, branch details, empty collections, and requested subtrees.
- **SRS-544**: MUST include unit tests in `tests/test_config_cli.py` verifying tree topology invariants, section path badges, and rectangular table alignment.
- **SRS-545**: MUST include unit tests in `tests/test_config_cli.py` verifying `--get`, `--set`, `--unset`, `--print`, `--info`, and `--print-raw` behavior, exit codes, stdout/stderr separation, and no mutation on rejection.

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
- **SRS-250**: MUST implement the following behavior: `--enable-static-check` MUST accept a module name (case-insensitive) as the first comma-separated token after `=`: Dummy, Pylance, Ruff, or Command; for Command the second comma-separated token is the mandatory `cmd` binary; when parsed from command-line SPECs rather than persisted configuration, Command `cmd` MUST resolve to an executable program (`shutil.which`) or the command MUST fail with `ReqError` exit code 1 before any configuration is persisted; all subsequent comma-separated tokens are `params` stored as a JSON array, commas inside single-quoted or double-quoted tokens MUST NOT split parameters, and surrounding single or double quotes on each token MUST be stripped before persistence; unknown module names MUST produce a `ReqError` with exit code 1.
- **SRS-251**: MUST implement the following behavior: When `--enable-static-check` is specified multiple times, entries MUST be preserved in insertion order per canonical language; an entry structurally identical (`module`, `cmd`, and `params` fields all equal) to an already-accumulated entry for the same canonical language MUST be silently discarded.
- **SRS-301**: MUST implement the following behavior: When `--enable-static-check` is invoked against an existing global configuration file, the command MUST load and preserve all pre-existing `"static-check"` entries without removal; for each new CLI-specified entry, presence MUST be decided by exact tuple match `(canonical language, module, cmd, params)` in the loaded config; if present discard, otherwise append.
- **SRS-252**: MUST implement the following behavior: When `--enable-static-check` is used during installation or update, the global configuration file key `"static-check"` MUST be a JSON object keyed by canonical language name, and each language value MUST be a non-empty JSON array of entry objects with required `"module"` and optional `"cmd"`/`"params"` fields.

### 5.4 Static Analysis Execution Commands
- **SRS-253**: MUST support `files-static-check FILE [FILE ...]` as a subcommand per SRS-408 requiring `--prj-base`; for each FILE it MUST resolve the absolute path, detect the language, load the language array from `"static-check"`, and execute all configured entries sequentially with `fail_only` mode active and a dispatch context containing the mandatory `--prj-base` value.
- **SRS-254**: MUST implement the following behavior: When `files-static-check` cannot locate `~/.config/usereq/config.json`, the command MUST print a warning to stderr, apply the SRS-424 default static-check configuration, and continue with SRS-255 exit-code semantics.
- **SRS-255**: MUST implement the following behavior: The `files-static-check` command exit code MUST be 0 when all checked files pass (or no files are checked), and 1 when at least one file fails static analysis.
- **SRS-256**: MUST support `static-check` as a project-scan subcommand per SRS-408 requiring `--prj-base`, with file selection from `git ls-files` under configured `src-dir` values and the `tests-dir` value plus SRS-131/SRS-180 filtering; all checks MUST execute with `fail_only` mode active and dispatch context containing `--prj-base`.
- **SRS-257**: MUST implement the following behavior: The `static-check` command exit code MUST be 0 when all checked files pass (or no files are checked), and 1 when at least one file fails static analysis.
- **SRS-336**: MUST implement the following behavior: The `static-check` command MUST load the `tests-dir` value from `~/.config/usereq/config.json` and append it to the `src-dir` list for file selection; if `tests-dir` is missing or invalid the command MUST skip test directory inclusion without error.
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
- **SRS-396**: MUST require `--prj-base` for the `references`, `compress`, `tokens`, `find`, `static-check`, `files-static-check`, `--docs-check`, `--set-docs-dir`, `--set-src-dir`, and `--set-tests-dir` commands.
- **SRS-397**: MUST require `--git-base` for `--git-check`, `--git-wt-name`, `--git-wt-create`, and `--git-wt-delete`.
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
- **SRS-320**: MUST support `--git-wt-create WT_NAME` as a command that requires the mandatory `--git-base` and `--prj-base` arguments; `WT_NAME` is mandatory.
- **SRS-321**: MUST implement the following behavior: The `--git-wt-create` command MUST validate that `WT_NAME` contains only characters compatible with both Linux and Windows directory names; if invalid, it MUST print `ERROR: Invalid worktree/branch name: <WT_NAME>.\n` and exit with non-zero code.
- **SRS-322**: MUST implement the following behavior: The `--git-wt-create` command MUST execute `git worktree add "<parent-path>/<WT_NAME>" -b <WT_NAME>` from within the runtime-resolved git repository root.
- **SRS-331**: MUST implement the following behavior: The `--git-wt-create` command MUST NOT change the current directory on success or failure; if post-create operations fail, it MUST rollback created worktree and branch and exit with non-zero code.
- **SRS-335**: MUST copy `--prj-base/.venv` into the created worktree preserving its relative path when the source exists and the destination is absent; an absent source `.venv` MUST skip the copy without error.
- **SRS-460**: MUST document in the `--git-wt-create` inline help that `--prj-base` is mandatory and supplies the `.venv` source copied into the created worktree.

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
- **SRS-330**: MUST include unit tests in `tests/test_cli.py` verifying the `--git-check`, `--docs-check`, `--git-wt-name`, `--git-wt-create` (including mandatory `--prj-base` validation and `.venv` copy behavior), and `--git-wt-delete` commands behave per their respective requirements.
