> [!CAUTION]
> ### 🚨 STRICTLY EXPERIMENTAL — PROOF OF CONCEPT (PRE-ALPHA)
> 
> ![Status: Proof of Concept](https://img.shields.io/badge/Status-Proof_of_Concept-red?style=flat-square) ![Stage: Pre-Alpha](https://img.shields.io/badge/Stage-Pre--Alpha-critical?style=flat-square) ![Maintenance: Personal Use Only](https://img.shields.io/badge/Scope-Personal_Use_Only-important?style=flat-square) ![Issues: Closed](https://img.shields.io/badge/Issues_%26_PRs-Not_Accepted-inactive?style=flat-square)
>
> **PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE:**
> 
> * **Very Early Stage:** This project is currently a raw **Proof of Concept (PoC)** in a **pre-alpha** state. It is nowhere near production-ready and may contain severe bugs, breaking changes, or incomplete logic.
> * **Personal Use Only:** This repository is developed, maintained, and shared strictly for **personal use**. 
> * **No Support or Feature Requests:** Please **do not** open issues, bug reports, or feature requests. They will not be addressed or accepted at this stage of development.
> * **No Warranty:** This software is provided **"AS IS"**, without warranty of any kind, express or implied. You may use it strictly for **testing and evaluation purposes** at your own sole risk.

# useReq / req (0.75.12)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>

<p align="center">
<strong>The `req` CLI provisions requirements-driven development skills for LLM agents.</strong><br>
In more detail: useReq packages a catalog of requirements-engineering prompts (write, create, change, implement, check, and more) and installs them as user-level skills for the CLIs and agents you already use — exposed as `/skill:req-<name>` or `$req-<name>` depending on the provider. It also ships an embedded source-analysis toolkit (token counting, references, compression, construct extraction, static checks) that operates on your project across 20 programming languages, plus git-worktree helpers for parallel task execution. Everything is driven by one user-global configuration file (`~/.config/usereq/config.json`); nothing is written into your project repository. It runs as a Python package (installed as `req`, `usereq`, or `cli-usereq`) or directly via `uvx`.
</p>

<p align="center">
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#requirements">Requirements</a> |
  <a href="#users-guide">User's Guide</a> |
  <a href="#acknowledgments">Acknowledgments</a>
</p>

<p align="center">
🚧 <strong>STAGE:</strong> PRE-ALPHA 📝 - Proof-of-Concept (PoC) version 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://www.npmjs.com/package/pi-usereq"><strong>PI-useReq/pi-usereq</strong></a> 🤖✨ ⚠️<br>
</p>

# Feature Highlights

The highlights below are what give the most value day-to-day:

- **Drives development through requirement changes**, keeping the work under control with an uninterrupted linear progression.
- **One catalog, many CLIs**: a single skill catalog published to pi.dev, Antigravity, Claude Code, GitHub Copilot, OpenAI Codex, OpenClaw, and OpenCode through a common interface.
- **LLM-optimized documentation**: creates and maintains a *Software Requirements Specification* (SRS) plus `WORKFLOW.md`, `REFERENCES.md`, and `FLOWCHART.md` for new or existing projects, tuned for LLM-agent reasoning.
- **Embedded source analysis** for 20 languages (Python, C, C++, C#, Rust, JavaScript, TypeScript, Java, Go, Ruby, PHP, Swift, Kotlin, Scala, Lua, Shell, Perl, Haskell, Zig, Elixir): token counting, reference markdown, compression, and construct extraction.
- **Configurable static analysis** with Pylance, Ruff, or arbitrary Command-Line checkers — sensible defaults included, with per-checker pre-flight validation that never blocks the run.
- **Declarative provider configuration**: enable/disable providers and static checkers in one global config; `install`/`uninstall`/`show` lifecycle subcommands report exactly what is deployed where.
- **Self-maintaining**: optional auto-install re-provisions your providers after every self-upgrade.
- **Git worktree support** to parallelize tasks on clean repositories.
- Compatible with [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) and [release-changelog-builder-action](https://github.com/mikepenz/release-changelog-builder-action); integrates with [G/Git-Alias CLI](https://github.com/Ogekuri/G).

# Quick Start

Get running in three steps: install the tool, configure one provider, and install the artifacts into your CLI.

**1. Install** (pick one):

```bash
# persistent install from PyPI (recommended)
uv tool install cli-usereq

# or persistent install tracking the git repository
uv tool install cli-usereq --force --refresh --from git+https://github.com/Ogekuri/CLI-useReq.git

# or run instantly without installing (PyPI release)
uvx --from cli-usereq req --help

# or run instantly without installing (git repository)
uvx --from git+https://github.com/Ogekuri/CLI-useReq.git req --help
```

**2. Configure** — enable a provider by name (configuration only; nothing is installed yet, all providers are disabled by default):

```bash
req --enable pi
```

**3. Run** — install the skills for the configured providers:

```bash
req install
```

Skills are installed under your HOME (e.g. `~/.pi/agent/skills/` for the `pi` provider) and are immediately available as `/skill:req-<name>` skills. Start with `req-orchestrate` (for example `/skill:req-orchestrate` on pi), the parent skill that routes every executive workflow: it delegates to `req-write` to draft the SRS of a new project, `req-create` to derive it from existing source code, and to the implementation skills such as `req-implement`, `req-change`, and `req-new`.

<!-- Legacy section anchor retained for SRS-342 tooling: ## Requirements -->
# Requirements

- **Astral `uv` tool is required** to run `scripts/req.sh` and is the recommended workflow for all project CLI executions. Install it from [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/).
- **Python 3.11+**.
- **git** — required by project-scan commands (`references`, `compress`, `find`, `static-check`) and by the git-integration commands.
- **Primary validated environment: Linux** — automatic `--upgrade` and `--uninstall` execution is Linux-only; on other platforms the manual command is printed instead.
- `uv.lock` is the canonical dependency lockfile for this repository; no root `requirements.txt` is maintained.
- Optional external binaries for the default static-check configuration: `cppcheck` and `clang-format` (C/C++), `node` (JavaScript), `eslint` (TypeScript). Python checking uses the bundled `Pylance` (pyright) and `Ruff` modules. Missing binaries are reported per check and never abort the run.

# User's Guide

## Install, Upgrade, and Uninstall

### Tool installation

```bash
uv tool install cli-usereq
```

PyPI is the canonical distribution channel (project [`cli-usereq`](https://pypi.org/project/cli-usereq/), published via OIDC trusted publishing by the `release-pypi.yml` workflow for `master` tags). GitHub hosts intermediate and test releases; see [Install from GitHub (alternative channel)](#install-from-github-alternative-channel) below.

This exposes the CLI as `req` (also callable as `usereq`, `cli-usereq`, or `python -m usereq`). After installation, verify with `req --version`.

### Tool upgrade and auto-install

```bash
req --upgrade

# force full package download and complete reinstallation
req --upgrade --force
```

On Linux this executes `uv tool install cli-usereq --upgrade` from the PyPI index, so an outdated installation is actually upgraded to the latest published version; when the installed tool was provisioned from a non-PyPI source (for example by `req --upgrade --develop`), the command additionally carries `--force` so `uv` discards the recorded git source and installs the production PyPI release, downgrading when that release is older; on other platforms the manual command is printed and `uv` is not executed. Adding `--force` forces full package download and complete reinstallation: `req --upgrade --force` executes `uv tool install cli-usereq --force --reinstall --refresh`. Use `req --upgrade --develop` (or the equivalent `req --upgrade --dev`) to install the latest tagged GitHub release instead of PyPI. When the upgrade succeeds and `auto-install` is enabled (the default), the persisted providers are automatically re-provisioned — equivalent to running `install`; no `--prj-base` is required. When no provider is enabled, a warning is printed and the automatic installation is skipped. Disable the behavior persistently with `--disable-auto-install` and re-enable it with `--enable-auto-install`.

### Install from GitHub (alternative channel)

Intermediate and test releases are published on GitHub at [`Ogekuri/CLI-useReq`](https://github.com/Ogekuri/CLI-useReq) and can be installed as an alternative to the PyPI channel:

```bash
# persistent install tracking the git repository
uv tool install cli-usereq --force --refresh --from git+https://github.com/Ogekuri/CLI-useReq.git

# or run instantly without installing
uvx --from git+https://github.com/Ogekuri/CLI-useReq.git req --help

# or upgrade an existing installation to the latest GitHub release
req --upgrade --develop
```

On Linux `req --upgrade --develop` (or `req --upgrade --dev`) executes the standard `uv tool install cli-usereq --from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` command, where `<TAG>` is the latest tagged release resolved through the GitHub releases API regardless of the branch holding it; on other platforms the manual command is printed and `uv` is not executed. Adding `--force` (`req --upgrade --develop --force`) executes `uv tool install cli-usereq --force --reinstall --refresh --from git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>` instead.

### Tool removal

```bash
req --uninstall     # executes `uv tool uninstall cli-usereq` on Linux and cleans the release-check cache
```

### Provider artifacts

- `req install` — installs or updates the skills of the providers persisted in the configuration into user-level directories and prints a Unicode installation summary report (`Provider` / `Skills Installed` columns). Requires at least one enabled provider, otherwise an English error is printed and the exit code is 4. Skills are the only supported artifact type: prompts and agents are no longer installed.
- `req uninstall` — reciprocal of `install`: removes the `req-*` skill artifacts of the configured providers from the user-level skills directories.
- `req show` — prints four tables: `Active Configuration` (`docs-dir`, `tests-dir`, `src-dir`, `auto-install`), `Providers` (every configurable provider in alphabetical order with the `CLI`, `Enabled`, and `Skills Path` columns), a single `Installation Status` table (`Type`, `Name`, `CLI`, `Enabled`, `Installed`) with one row per packaged prompt name and enabled provider pair ordered by prompt name then provider name, reporting `OK` or `MISSING` per skill on disk, and `Static Checks` (configured language, module, command, and parameters).

Skills are always installed into **user-level CLI configuration directories under your HOME** (`~/.claude/skills`, `~/.codex/skills`, `~/.copilot/skills`, `~/.gemini/config/skills`, `~/.openclaw/workspace/skills`, `~/.config/opencode/skills`, `~/.pi/agent/skills`); nothing is ever written into the project repository.

## Configuration

All configuration lives in a single user-global file: `~/.config/usereq/config.json`. No configuration files are written to the project home or git repository path.

Canonical keys: `docs-dir`, `tests-dir`, `src-dir`, `providers`, `static-check`, `auto-install`.

### Configuration commands

The configuration file is inspected and edited exclusively through these commands. Paths are colon-separated, case-sensitive canonical tokens rooted at `Configuration`; the virtual root label `Application_Configuration` is not accepted on the command line.

```bash
req --print [PATH]           # render the configuration tree, or one subtree/parameter
req --info [PATH]            # render schema documentation, defaults, and copyable commands
req --print-raw              # print the unmodified bytes of ~/.config/usereq/config.json
req --get PATH               # print the JSON value stored at PATH
req --set PATH VALUE         # validate and store VALUE at PATH
req --unset PATH             # restore the schema default or remove the addressed element
```

- Example paths: `Configuration`, `Configuration:docs-dir`, `Configuration:providers`, `Configuration:static-check`, `Configuration:static-check:Python:0:module`.
- Arrays accept `:<Idx>` (0-based), `:append`, `:+`, and `:insert:<Idx>` writes; single-item writes take one item, whole-array writes take a JSON array (e.g. `req --set Configuration:providers:+ pi`, `req --set Configuration:src-dir '["src","lib"]'`).
- Booleans, arrays, dictionaries, and sections require JSON text; plain strings are taken verbatim.
- A missing configuration file is created from the schema defaults before the command runs; each write is validated as a whole and persisted atomically, so a rejected operation leaves stored values unchanged.
- Valid payloads go to stdout, every diagnostic goes to stderr, and the exit code is 0 on success and 1 on failure.

### Project directories

- `--set-docs-dir DOCS_DIR`, `--set-src-dir SRC_DIR` (repeatable), and `--set-tests-dir TESTS_DIR` persist project-relative directory values (each requires `--prj-base`; values must resolve under it). Install-time prompt substitution renders `%%DOC_PATH%%`/`%%SRC_PATHS%%`/`%%TEST_PATH%%` from these values, defaulting to `usereq/docs`, `src`, and `tests` when unset.
- The same values are readable and writable through `Configuration:docs-dir`, `Configuration:src-dir`, and `Configuration:tests-dir` (`--set-docs-dir` and `--set Configuration:docs-dir` are equivalent storage operations).
- Defaults when the configuration stores no value: `usereq/docs` (documentation), `src` (sources), `tests` (tests).
- `install` never creates project directories; configured paths are resolved only by the commands that consume them.

Typical project layout:

```text
.
├── usereq/docs/     # default docs-dir: REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md, FLOWCHART.md
├── src/             # source code (default src-dir)
└── tests/           # unit test suite (default tests-dir)
```

### Providers

All providers are disabled by default. Provider enablement is exclusive to the repeatable config-only flag, which accepts only the provider CLI name exactly like `--disable PROVIDER`:

```bash
req --enable PROVIDER
```

- `PROVIDER`: `antigravity`, `claude`, `codex`, `copilot`, `openclaw`, `opencode`, or `pi`.
- Example: `req --enable pi`, or equivalently `req --set Configuration:providers:+ pi`.

Behavior:

- `--enable` only updates `~/.config/usereq/config.json`; it never installs artifacts. Enabling a provider again replaces all its previously persisted entries while preserving every other provider.
- `--disable PROVIDER` removes all persisted entries of that provider (unknown tokens exit with code 1).
- Unknown or invalid tokens print an English error identifying the invalid token and exit with code 1.
- Configuration flags may be combined with the `install` subcommand in one invocation (`req --enable pi install`): configuration is applied first, then installation proceeds.

Provider skills paths:

| Provider | Skills path |
| --- | --- |
| antigravity | `~/.gemini/config/skills` |
| claude | `~/.claude/skills` |
| codex | `~/.codex/skills` |
| copilot | `~/.copilot/skills` |
| openclaw | `~/.openclaw/workspace/skills` |
| opencode | `~/.config/opencode/skills` |
| pi | `~/.pi/agent/skills` |

### Static checks

```bash
req --enable-static-check SPEC    # repeatable, config-only, no --prj-base required
req --disable-static-check SPEC   # reciprocal removal
```

- `SPEC` format: `LANG=MODULE[,CMD[,PARAM...]]`.
- `MODULE`: `Dummy`, `Pylance`, `Ruff`, or `Command` (case-insensitive); for `Command`, `CMD` is the mandatory binary and the remaining tokens are `params`. Tokens containing commas must be wrapped in single or double quotes.
- `LANG`: the 20 canonical language names, case-insensitive (Python, C, C++, C#, Rust, JavaScript, TypeScript, Java, Go, Ruby, PHP, Swift, Kotlin, Scala, Lua, Shell, Perl, Haskell, Zig, Elixir); aliases like `cpp`, `csharp`, `js`, `ts`, `sh` are accepted.
- Enabling merges into the configuration without replacing existing entries: pre-existing entries are preserved, identity-duplicates (same language, module, cmd, params) are ignored.
- Disabling: `LANG=MODULE[,CMD[,PARAM...]]` removes the exact matching entry; bare `LANG` removes the whole language key. Explicitly disabling everything persists an empty `"static-check"` object, which keeps the defaults switched off.

Default static-check configuration (applied when the configuration stores no `"static-check"` entry; any present entry — including an empty object — suppresses the defaults):

| Language | Default checkers |
| --- | --- |
| C | `cppcheck --error-exitcode=1 --enable=warning,style,performance,portability --std=c11`, `clang-format --dry-run --Werror` |
| C++ | `cppcheck ... --std=c++20`, `clang-format --dry-run --Werror` |
| JavaScript | `node --check` |
| Python | `Pylance` (pyright), `Ruff` |
| TypeScript | `eslint` |

Pre-flight: before executing any checker, availability is verified — `Dummy` always; `Pylance`/`Ruff` via their module in the active interpreter; `Command` via its binary on PATH. An unavailable checker yields `Result: FAIL` with evidence identifying the missing checker or binary, and execution continues with the remaining checks.

Each stored entry exposes the fields `module`, `cmd`, and `params` as writable config paths (e.g. `Configuration:static-check:Python:0:module`); run `req --info Configuration:static-check` for the complete entry schema and copyable commands.

A standalone testbed is available: `req --test-static-check {dummy,pylance,ruff,command <cmd>} [FILES...]`, where `[FILES]` may be files, directories (direct children only), or glob patterns including `**` recursive expansion.

## Command Reference

`req` can be run from any directory. Two path arguments drive location resolution:

- `--prj-base <project-folder>` — mandatory for commands that read or write project files (`--docs-check`, `--set-*-dir`, and the project-scan subcommands `tokens`, `references`, `compress`, `find`, `static-check`, `files-static-check`); the `install` subcommand neither requires nor accepts it.
- `--git-base <git-repository-folder>` — mandatory for the git commands (`--git-check`, `--git-wt-name`, `--git-wt-create`, `--git-wt-delete`); not required by any analysis subcommand.
- `--prj-base` and `--git-base` are never persisted in `~/.config/usereq/config.json`.
- The configuration commands `--print`, `--info`, `--print-raw`, `--get`, `--set`, and `--unset` require neither base argument; paths are resolved from the configuration schema, not from a project.

### Analysis subcommands

The analysis commands are bare subcommands (no `--` prefix); the project-scan ones require `--prj-base`, and none of them requires `--git-base`. Legacy `--`-prefixed forms are not accepted.

| Subcommand | Purpose |
| --- | --- |
| `files-tokens FILE [FILE ...]` | Count tokens and chars for the given files |
| `files-references FILE [FILE ...]` | Generate LLM reference markdown for the given files |
| `files-compress [--enable-line-numbers] FILE [FILE ...]` | Generate compressed output for the given files |
| `files-find [--enable-line-numbers] TAG PATTERN FILE [FILE ...]` | Find and extract specific constructs from the given files |
| `files-static-check --prj-base P FILE [FILE ...]` | Run static analysis on the given files |
| `tokens --prj-base P` | Count tokens/chars for canonical docs (`REQUIREMENTS.md`, `WORKFLOW.md`, `REFERENCES.md`) in configured `docs-dir` |
| `references --prj-base P` | Reference markdown for source files selected by `git ls-files --cached --others --exclude-standard` under configured `src-dir` |
| `compress --prj-base P [--enable-line-numbers]` | Compressed output for the same project selection |
| `find --prj-base P [--enable-line-numbers] TAG PATTERN` | Extract constructs from the same project selection |
| `static-check --prj-base P` | Static analysis on `src-dir` + `tests-dir` selections (excluding `fixtures/`) |

Notes:

- Add `--enable-line-numbers` (accepted before or after the subcommand token) to include `<n>:` prefixes in `files-compress`, `compress`, `files-find`, and `find` output.
- `files-static-check` and `static-check` exit with code 0 when all checked files pass (or none are checked) and 1 when at least one file fails; passing checks produce no output (`fail_only` mode).
- `static-check` includes files from both `src-dir` and `tests-dir`; if `tests-dir` is missing or invalid, test-directory inclusion is skipped without error.

#### Supported &lt;TAG&gt; in `find` commands

- **Python**: CLASS, FUNCTION, DECORATOR, IMPORT, VARIABLE
- **C**: STRUCT, UNION, ENUM, TYPEDEF, MACRO, FUNCTION, IMPORT, VARIABLE
- **C++**: CLASS, STRUCT, ENUM, NAMESPACE, FUNCTION, MACRO, IMPORT, TYPE_ALIAS
- **C#**: CLASS, INTERFACE, STRUCT, ENUM, NAMESPACE, FUNCTION, PROPERTY, IMPORT, DECORATOR, CONSTANT
- **Rust**: FUNCTION, STRUCT, ENUM, TRAIT, IMPL, MODULE, MACRO, CONSTANT, TYPE_ALIAS, IMPORT, DECORATOR
- **JavaScript**: CLASS, FUNCTION, COMPONENT, CONSTANT, IMPORT, MODULE
- **TypeScript**: INTERFACE, TYPE_ALIAS, ENUM, CLASS, FUNCTION, NAMESPACE, MODULE, IMPORT, DECORATOR
- **Java**: CLASS, INTERFACE, ENUM, FUNCTION, IMPORT, MODULE, DECORATOR, CONSTANT
- **Go**: FUNCTION, METHOD, STRUCT, INTERFACE, TYPE_ALIAS, CONSTANT, IMPORT, MODULE
- **Ruby**: CLASS, MODULE, FUNCTION, CONSTANT, IMPORT, DECORATOR
- **PHP**: CLASS, INTERFACE, TRAIT, FUNCTION, NAMESPACE, IMPORT, CONSTANT
- **Swift**: CLASS, STRUCT, ENUM, PROTOCOL, EXTENSION, FUNCTION, IMPORT, CONSTANT, VARIABLE
- **Kotlin**: CLASS, INTERFACE, ENUM, FUNCTION, CONSTANT, VARIABLE, MODULE, IMPORT, DECORATOR
- **Scala**: CLASS, TRAIT, MODULE, FUNCTION, CONSTANT, VARIABLE, TYPE_ALIAS, IMPORT
- **Lua**: FUNCTION, VARIABLE
- **Shell**: FUNCTION, VARIABLE, IMPORT
- **Perl**: FUNCTION, MODULE, IMPORT, CONSTANT
- **Haskell**: MODULE, TYPE_ALIAS, STRUCT, CLASS, FUNCTION, IMPORT
- **Zig**: FUNCTION, STRUCT, ENUM, UNION, CONSTANT, VARIABLE, IMPORT
- **Elixir**: MODULE, FUNCTION, PROTOCOL, IMPL, STRUCT, IMPORT

### Git and docs commands

- `--git-check` — verify clean working tree and valid HEAD in the `--git-base` repository (requires `--git-base`).
- `--docs-check` — verify existence of `REQUIREMENTS.md`, `WORKFLOW.md`, and `REFERENCES.md` in the configured `docs-dir` (requires `--prj-base`).
- `--git-wt-name` — print a standardized worktree name `useReq-<PROJECT>-<BRANCH>-<TIMESTAMP>` (requires `--git-base`).
- `--git-wt-create WT_NAME` — create an isolated git worktree and branch with the given name under the `--git-base` repository; copies `.venv` from `--prj-base` into the new worktree when it exists (requires both `--git-base` and `--prj-base`).
- `--git-wt-delete WT_NAME` — force-remove the exact target worktree and branch by name (requires `--git-base`).

### Other flags

- `--verbose` / `--debug` — detailed and diagnostic output.
- `--ver` / `--version` — print the installed package version and query PyPI and GitHub, printing three aligned lines: `Current Installed : <version>`, `Latest @ PyPI : <version>`, and `Latest @ GitHub : <version>` (`unknown` when a repository cannot be reached).
- `--develop` / `--dev` — with `--upgrade`: install the latest tagged GitHub release from `git+https://github.com/Ogekuri/CLI-useReq.git@<TAG>`, with `<TAG>` resolved through the GitHub releases API regardless of branch, instead of PyPI; `--dev` is an equivalent alias of `--develop`.
- `--force` — with `--upgrade`: force full package download and complete reinstallation (`uv tool install ... --force --reinstall --refresh`); without `--force` the command requests the latest PyPI version through `--upgrade` and runs without `--reinstall`/`--refresh`, adding `--force` only when the installed tool comes from a non-PyPI source that `--upgrade` alone cannot replace.
- `-h` / `--help` — print command help and exit.

A startup release check queries the latest PyPI release (idle-gated to at most once per hour; once per day on API failures) and prints a bright-green stderr notice when a newer version is available.

## Prompt Catalog

| Prompt | Description |
| --- | --- |
| `orchestrate` | Route a software-development request and drive the delegated executive skills until no follow-up tasks remain |
| `write` | Produce a *SRS* draft based on the User Request description |
| `create` | Write a *Software Requirements Specification* using the project's source code |
| `recreate` | Reorganize and update the *SRS* based on source code analysis (preserve requirement IDs) |
| `renumber` | Deterministically renumber requirement IDs in the *SRS* without changing requirement text or order |
| `analyze` | Produce an analysis report |
| `change` | Update the requirements and implement the corresponding changes |
| `check` | Run the requirements check |
| `cover` | Implement minimal changes to cover uncovered existing requirements |
| `fix` | Fix a defect without changing the requirements |
| `implement` | Implement source code from requirements (from scratch) |
| `new` | Implement a new requirement and the corresponding source code changes |
| `refactor` | Perform a refactor without changing the requirements |
| `readme` | Write `README.md` from user-visible implementation evidence |
| `references` | Write a `REFERENCES.md` using the project's source code |
| `workflow` | Write a `WORKFLOW.md` using the project's source code |
| `flowchart` | Write a `FLOWCHART.md` using the project's source code |

# Documentation

## Supported CLIs and Extensions

### High-Level Assessment

- 🌟 **pi.dev CLI** 🌟 - Supports user-level Agent Skills from `~/.pi/agent/skills/`.
- 🌟 **Antigravity CLI** 🌟 - Evolution of Gemini CLI; supports user-level skills from `~/.gemini/config/skills/`.
- 👍 **OpenClaw** 👍 - Supports user-level skills from `~/.openclaw/workspace/skills/`.
- 👍 **OpenCode** 👍 - Many models available; supports user-level skills from `~/.config/opencode/skills/`.
- ⚖️ **Claude Code** ⚖️ - Only supports Claude/Anthropic models; supports user-level skills from `~/.claude/skills/`.
- ⚖️ **GitHub Copilot** ⚖️ - Supports user-level skills from `~/.copilot/skills/`.
- 🆘 **OpenAI Codex** 🆘 - Only supports OpenAI models; supports user-level skills from `~/.codex/skills/`.

### useReq/req Support

- ✅ pi.dev CLI
- ✅ Antigravity CLI
- ✅ Claude Code
- ✅ GitHub Copilot
- ✅ OpenAI Codex
- ✅ OpenClaw
- ✅ OpenCode

| ✅ supported | ❌ not supported |

The supported provider set is exactly the seven CLI names listed above and in the `providers` configuration array; any other CLI is unsupported, and a provider token outside that set is rejected with an English error and exit code 1. Prompts and agents are no longer supported artifacts: useReq installs skills only.

### Skills Details

Every enabled provider receives `req-<name>/SKILL.md` skill directories under its hardcoded skills root:

- ✅ pi.dev CLI: [`/skill:req-create`] — `~/.pi/agent/skills/req-create/SKILL.md`; pi discovers user skills from `~/.pi/agent/skills/` and registers them as `/skill:name` commands; arguments after the command are appended to the skill content as `User: <args>`.
- ✅ Antigravity CLI: [`$req-create`] — `~/.gemini/config/skills/req-create/SKILL.md`.
- ✅ OpenAI Codex: [`$req-create`] — `~/.codex/skills/req-create/SKILL.md`.
- ✅ Claude Code: [`/req-create`] — `~/.claude/skills/req-create/SKILL.md`.
- ✅ GitHub Copilot: [`/req-create`] — `~/.copilot/skills/req-create/SKILL.md`.
- ✅ OpenClaw: [`$req-create`] — `~/.openclaw/workspace/skills/req-create/SKILL.md`.
- ✅ OpenCode: [`/req-create`] — `~/.config/opencode/skills/req-create/SKILL.md`.

## Default Workflow

Click to zoom flowchart image.

[![Flowchart](https://raw.githubusercontent.com/Ogekuri/CLI-useReq/refs/heads/master/images/flowchart-bw.svg)](https://raw.githubusercontent.com/Ogekuri/CLI-useReq/refs/heads/master/images/flowchart-bw.svg)

## Guidelines

`GUIDELINES_DIR` is fixed to the packaged `resources/guidelines` directory of the running installation and is not configurable. Generated prompts and skills reference the packaged resources of the active installation through home-relative paths, including `%%TEMPLATE_PATH%%` for templates; guideline files themselves are never copied, created, or modified in project or user directories. Re-run `req install` after an upgrade so rendered paths follow the active installation.

## Repository Documentation

Requirements-driven projects keep their normative documentation under the configured `docs-dir`:

- `REQUIREMENTS.md` — the Software Requirements Specification (SRS).
- `WORKFLOW.md` — runtime model: execution units, call-trace trees, communication edges.
- `REFERENCES.md` — structured symbol index of the source code.
- `FLOWCHART.md` — workflow flowchart.

## Development Notes

- `scripts/req.sh` runs the CLI via `uv run python -m usereq.cli` from the repository root, forwarding all user arguments unchanged.
- `scripts/test-install.sh` performs an isolated-HOME smoke installation (`--enable pi` + `install`).
- `scripts/prompts-update.sh` synchronizes the bundled prompts and document templates from the upstream [Ogekuri/CLI-Prompts](https://github.com/Ogekuri/CLI-Prompts) releases into `src/usereq/resources/prompts` and `src/usereq/resources/templates`, and persists the release version marker.
- `scripts/build.sh` performs a clean release build into `dist/`: it verifies `uv` and `git`, removes non-tracked and old-version `dist/` entries, builds the sdist and wheel with the frozen lockfile, prunes build intermediates, and prints the artifact and cleanup summary.
- `scripts/pre-release-check.sh` runs the release gate in order: environment, worktree cleanliness (skippable with `--allow-dirty`), `uv sync --frozen`, a temporary-directory sdist/wheel build, `static-check`, and `uv run pytest`, cleaning every generated intermediate on exit.
- `uv.lock` is the canonical dependency lockfile for execution, build, development, testing, and static analysis.

## Note on Git usage

This section describes the Git behavior when executing the commands provided by the scripts.

- Required state before execution:
  - Execute commands from a working branch (not in detached HEAD).
  - Preferably, the working tree should be clean: avoid unintended changes in the repository before starting the scripts.
  - Save all files and verify that you are in the correct project directory.
  - **IMPORTANT:** `useReq/req` stores its configuration in the user-global file `~/.config/usereq/config.json`; no configuration is written to the project repository, so git worktree checkouts need no configuration tracking.

- What the scripts do to the repository:
  - The scripts may modify, create, or remove files in the working tree (files on disk).
  - They do not modify Git history (HEAD), branches, or tags automatically.
  - The index (staging area) and history remain unchanged until the user manually performs staging/commit operations.

- How to commit (recommended practice):
  - Review changes generated by the scripts before including them in a commit.
  - Manually add files to commit using `git add <file...>`.
  - Execute the commit with a structured message, for example:
    `git commit -m "change(<COMPONENT>): <SHORT-DESCRIPTION> [<DATE>]"`.
  - Staging and commit operations are under the user's control; the scripts do not perform automatic commits or update Git references.

- Practical warnings:
  - Do not use destructive commands (e.g., `git reset --hard`, `git clean -fd`) to "clean" the repository without verifying the impact.
  - If you prefer to isolate changes, execute commands in a branch or a copy of the repository.

# License

Copyright (C) Ogekuri.

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License as published by the Free Software Foundation, version 3** (GPL-3.0), of which a full copy is provided in the [`LICENSE`](LICENSE) file of this repository.

This program is distributed in the hope that it will be useful, but **without any warranty**; without even the implied warranty of merchantability or fitness for a particular purpose. See the LICENSE file for details.

# Acknowledgments

- **[Ogekuri/CLI-Prompts](https://github.com/Ogekuri/CLI-Prompts)** — upstream source of the bundled requirements-engineering prompt catalog (`src/usereq/resources/prompts`).
- **[Astral](https://astral.sh)** — for `uv`, the Python package and project manager that powers installation, execution, and self-upgrade.
- **[OpenAI tiktoken](https://github.com/openai/tiktoken)** — token counting for LLM context budgeting.
- **[pyright](https://github.com/microsoft/pyright)** and **[ruff](https://github.com/astral-sh/ruff)** — the static-analysis engines exposed through the `Pylance` and `Ruff` modules.
- **[tree-sitter](https://tree-sitter.github.io/tree-sitter/)** — inspiration for the multi-language source-analysis approach.
