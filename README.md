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

# useReq/req (0.67.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/badge/docs-live-b31b1b" alt="Docs">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>

<p align="center">
<strong>The <u>req</u> script provides CLI prompts for requirements-driven software development.</strong><br>
The defined prompts are exposed through provider-specific prompt, skill, and agent surfaces across supported CLIs and Agents (for example <b>/req-<name></b>, <b>/req:<name></b>, <b>/skill:req-<name></b>, or <b>/req-<name>.prompt</b>).<br>
This allows them to be run both as a Python package (installed as <b>req</b>, <b>usereq</b>, or <b>use-req</b>) and directly using <b>uvx</b>.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#feature-highlights">Feature Highlights</a> |
  <a href="#prompts-and-agents">Prompts and Agents</a> |
  <a href="#default-workflow">Default Workflow</a> |
  <a href="#supported-clis-agents-and-extensions">Supported CLIs, Agents, and Extensions</a> |
  <a href="#known-issues">Known Issues</a> |
  <a href="#note-on-git-usage">Note on Git usage</a>
</p>
<p align="center">
<br>
🚧 <strong>DRAFT:</strong> Proof-of-Concept (PoC) Version 📝 - Work in Progress 🏗️ 🚧<br>
⚠️ <strong>IMPORTANT NOTICE</strong>: Created with <a href="https://www.npmjs.com/package/pi-usereq"><strong>PI-useReq/pi-usereq</strong></a> 🤖✨ ⚠️<br>
<br>
</p>

## Requirements

- Astral `uv` tool is required to run `scripts/req.sh` and project CLI workflows.
- `uv.lock` is the canonical dependency lockfile for this repository; do not maintain a root `requirements.txt` file.
- Primary validated environment: `linux` (automatic `--upgrade` and `--uninstall` execution is Linux-only).
- Python 3.11+


## Feature Highlights
- **Drives development through requirement changes**.
- Keeps development under control.
- Usable as skills, or agents, or prompts.
- Creates a common interface for different vendor CLIs and Agents.
- Creates **Software Requirements Specification** [*SRS*] file, optimized for LLM Agents, for new or existing projects.
- Keeps source code documentation updated and optimized for LLM Agents reasoning.
- Engineered for uninterrupted linear progression.
- Use **git worktree** to parallelize tasks (only on clean git repositories)
- Provide **source-code analysis tool**, that supports different programming languages: Python, C, C++, C#, Rust, JavaScript, TypeScript, Java, Go, Ruby, PHP, Swift, Kotlin, Scala, Lua, Shell, Perl, Haskell, Zig, Elixir.
- Support **static-code analysis** with Pylance, Ruff or customizable Command-Line commands.
- Support customizable guidelines.
- Supports [Conventional Commit Standards](https://www.conventionalcommits.org/en/v1.0.0/) and is compatible with [release-changelog-builder-action](https://github.com/mikepenz/release-changelog-builder-action).
- Compatible with [G/Git-Alias CLI](https://github.com/Ogekuri/G).
- You will no longer need to read the codebase.


## Prompts and Agents
  | Prompt | Description |
  | --- | --- |
  | `write` | Produce a *SRS* draft based on the User Request description |
  | `create` | Write a *Software Requirements Specification* using the project's source code |
  | `recreate` | Reorganize and update the *Software Requirements Specification* based on source code analysis (preserve requirement IDs) |
  | `renumber` | Deterministically renumber requirement IDs in the *Software Requirements Specification* without changing requirement text or order |
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


## Default Workflow

Click to zoom flowchart image.

[![Flowchart](https://raw.githubusercontent.com/Ogekuri/useReq/refs/heads/master/images/flowchart-bw.svg)](https://raw.githubusercontent.com/Ogekuri/useReq/refs/heads/master/images/flowchart-bw.svg)


## Quick Start

### Prerequisites

- Supported environment: `linux`
- Python 3.11+
- Install the `uv` tool from: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)


### Project's Tree

Here the typical project's tree; configure `docs-dir`, `src-dir`, and `tests-dir` according to your project layout:

```text
.
├── docs/
│   ├── FLOWCHART.md
│   ├── REQUIREMENTS.md
│   ├── REFERENCES.md
│   └── WORKFLOW.md
├── src/
│   └── Source code
└── tests/
    └── Unit tests suite
```

### Run useReq/req with uvx
```bash
uvx --from git+https://github.com/Ogekuri/useReq.git req \
  --prj-base myproject/ \
  --provider pi:prompts
```

### Install/Uninstall useReq/req with uv

#### Install
```bash
uv tool install usereq --force --from git+https://github.com/Ogekuri/useReq.git
```

#### Uninstall
```bash
uv tool uninstall usereq
```

### Quick Install

1. Install on a project in path `project_path` (missing configured directories are created automatically on fresh install):
- Typical Install (directory values come from `~/.config/usereq/config.json`, defaults: `usereq`, `src`, `tests`):
```
req \
--prj-base "project_path" \
--provider pi:prompts \
--provider claude:prompts \
--provider codex:skills \
--provider antigravity:prompts \
--provider opencode:prompts \
--enable-static-check C=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c11 \
--enable-static-check C=Command,clang-format,--dry-run,--Werror \
--enable-static-check C++=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c++20 \
--enable-static-check C++=Command,clang-format,--dry-run,--Werror \
--enable-static-check Python=Pylance \
--enable-static-check Python=Ruff
```
2. Use `/req-write` or `/req-create` to create requirements
3. Use `/req-implement` to implement source-code from requirements, or `/req-cover` to cover new requirements (documentation).
4. Use `/req-workflow`, `/req-flowchart`, and/or `/req-references` to update project's documentation.
5. Start to use `/req-change`, `/req-new`, and `/req-fix`.

### Usage
- Run `req` to create or recreate useReq resources. Prompts, agents, and skills are installed into **user-level CLI configuration directories under your HOME** (`~/.claude`, `~/.codex`, `~/.antigravity`, `~/.config/opencode`, `~/.pi/agent`); nothing is written into the project repository.
  - You can run `req` from any directory:
    - `--prj-base <project-folder>` is mandatory for every command that reads or writes project files (install, `--update`, `--references`, `--compress`, `--tokens`, `--find`, `--static-check`, `--docs-check`, `--set-docs-dir`, `--set-src-dir`, `--set-tests-dir`).
    - `--git-base <git-repository-folder>` is mandatory for every git command (`--git-check`, `--git-path`, `--git-wt-name`, `--git-wt-create`, `--git-wt-delete`).
    - `--prj-base` and `--git-base` are never persisted in `~/.config/usereq/config.json`.
  - Directory configuration:
    - `docs-dir`, `tests-dir`, and `src-dir` are persisted in `~/.config/usereq/config.json`.
    - Defaults when the configuration stores no value: `usereq`, `tests`, and `src`.
    - `--set-docs-dir DOCS_DIR`, `--set-src-dir SRC_DIR` (repeatable), and `--set-tests-dir TESTS_DIR` persist project-relative directory values and require `--prj-base`.
    - Configured directories must resolve under `--prj-base`.
    - On fresh installation, missing configured directories are created automatically.
  - `GUIDELINES_DIR` is fixed to `~/.pi/agent/npm/node_modules/pi-usereq/src/resources/guidelines` and is not configurable; generated prompts and skills reference it through home-relative paths.
  - Use one or more `--provider SPEC` parameters (at least one is required) to configure provider activation, artifact types, and options:
    - `SPEC` format: `PROVIDER:ARTIFACT_ITEM[,ARTIFACT_ITEM...][:PROVIDER_OPTIONS]`
    - `PROVIDER`: `antigravity`, `claude`, `codex`, `opencode`, or `pi`.
    - `ARTIFACT_ITEM`: one of `{prompts, agents, skills}`.
    - `PROVIDER_OPTIONS`: (optional) comma-separated list from `{prompts-use-agents}`.
    - Example: `--provider pi:prompts,skills`
  - Artifact types (specified within the `--provider` spec):
    - `skills` artifact generates skill resources for the provider.
    - `prompts` artifact generates prompts/commands resources for the provider.
    - `agents` artifact generates agent resources for the provider.
  - `--enable-static-check SPEC` Enable static check configuration for a language (repeatable). SPEC format: `LANG=MODULE[,CMD[,PARAM...]]`.
      - Supported `MODULE` values: `Dummy`, `Pylance`, `Ruff`, `Command` (case-insensitive).
      - Entries are merged into `~/.config/usereq/config.json` without replacing existing ones: existing entries are preserved, identity-duplicates are ignored, and only new non-duplicate entries are appended per language.
- Configuration is stored in a single user-global file: `~/.config/usereq/config.json`. No configuration files are written to the project home or git repository path.
- You need to run `req` again if you add or remove requirement-related files in the documentation directory, or if the installed guidelines under `~/.pi/agent/npm/node_modules/pi-usereq/src/resources/guidelines` change.
- Provider-scoped option `prompts-use-agents` (in the optional `:PROVIDER_OPTIONS` segment) generates prompt files as **agent-only references** (adds an `agent:` front matter field) where supported (Claude commands, OpenCode commands, and pi prompts).
- Add `--verbose` and `--debug` to get detailed and diagnostic output.
- Add `--update` to update an existing installation (requires an existing `~/.config/usereq/config.json`).
  - With `--update`, passing one or more `--provider` specs replaces persisted provider specs; without `--provider`, persisted specs are reused.
- Add `-h` / `--help` to print command help and exit.
- Add `--ver` / `--version` to print the installed package version and exit.
- Add `--remove` to remove `req-*` artifacts generated by useReq from the user-level provider directories configured in the global configuration file.
- Add `--upgrade` to self-upgrade useReq via `uv`.
- Add `--uninstall` to uninstall useReq via `uv`.

### Embedded Utility

- Count tokens and chars for the given files (standalone, no --prj-base required).
  `--files-tokens FILE [FILE ...]`

- Generate LLM reference markdown for the given files (standalone, no --prj-base required).
  `--files-references FILE [FILE ...]`

- Generate compressed output for the given files (standalone, no --prj-base required).
  `--files-compress FILE [FILE ...]`

- Find and extract specific constructs from the given files (standalone, no --prj-base required).
  `--files-find TAG PATTERN FILE [FILE ...]`

- Run static analysis on the given files using tools configured in `~/.config/usereq/config.json` (standalone, no --prj-base required).
  `--files-static-check FILE [FILE ...]`

- Count tokens and chars for canonical docs files in configured `docs-dir` (`REQUIREMENTS.md`, `WORKFLOW.md`, `REFERENCES.md`; requires `--prj-base`).
  `--tokens`

- Generate LLM reference markdown for source files selected by `git ls-files --cached --others --exclude-standard` under configured `src-dir` directories (requires `--prj-base`).
  `--references`

- Generate compressed output for source files selected by `git ls-files --cached --others --exclude-standard` under configured `src-dir` directories (requires `--prj-base`).  
  `--compress`

- Find and extract specific constructs from source files selected by `git ls-files --cached --others --exclude-standard` under configured `src-dir` directories (requires `--prj-base`).
  `--find TAG PATTERN`

- Run static analysis on source files selected by `git ls-files --cached --others --exclude-standard` under configured `src-dir` directories (plus configured `tests-dir`, excluding `fixtures/`) using tools configured in `~/.config/usereq/config.json` (requires `--prj-base`).
  `--static-check`

- Check repository integrity for `--git-base`: clean working tree and valid HEAD (requires `--git-base`).
  `--git-check`

- Check canonical docs presence in configured `docs-dir`: `REQUIREMENTS.md`, `WORKFLOW.md`, `REFERENCES.md` (requires `--prj-base`).
  `--docs-check`

- Create an isolated git worktree and branch with the provided name; also copies `.venv` (when present) into the new worktree context (requires `--git-base`).
  `--git-wt-create WT_NAME`

- Remove the git worktree and branch identified by name (force-removes the target worktree and deletes the branch; requires `--git-base`).
  `--git-wt-delete WT_NAME`

- Print the git repository root resolved from `--git-base`; the command fails when `--git-base` is not inside a git repository (requires `--git-base`).
  `--git-path`


- Add `--enable-line-numbers` to include `<n>:` prefixes in `--files-compress`, `--compress`, `--files-find`, and `--find` output.

- Test static check configuration and execution (standalone).
  `--test-static-check {dummy,pylance,ruff,command} [FILES...]`

#### Supported <TAG> in `--find` commands

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

## Supported CLIs, Agents, and Extensions

### High-Level Assessment


- 🌟 **pi.dev CLI** 🌟 - Supports user-level prompt templates and Agent Skills from `~/.pi/agent/prompts/` and `~/.pi/agent/skills/`.
- 🌟 **Antigravity CLI** 🌟 - Evolution of Gemini CLI; supports user-level TOML commands and skills.
- 👍 **OpenCode** 👍 - Many models available; supports user-level commands, agents, and skills from `~/.config/opencode/`.
- ⚖️ **Claude Code** ⚖️ - Only supports Claude/Anthropic models; supports user-level commands, agents, and skills from `~/.claude/`.
- 🆗 **OpenAI Codex** 🆗 - Only supports OpenAI models; supports user-level prompts and skills from `~/.codex/`.


### useReq/req Support
- ✅ pi.dev CLI
- ✅ Antigravity CLI
- ✅ Claude Code
- ✅ OpenAI Codex
- ✅ OpenCode

| ✅ supported | ❌ not supported |

GitHub Copilot and Kiro CLI are not supported: their prompt/agent/skill configuration is repository-scoped only and cannot be managed at user level.

#### Skills Details
- ✅ pi.dev CLI: [`/skill:req-create`]
  - useReq generates `~/.pi/agent/skills/req-create/SKILL.md`.
  - pi discovers user skills from `~/.pi/agent/skills/` and registers them as `/skill:name` commands.
  - Arguments after the command are appended to the skill content as `User: <args>`.
- ✅ Antigravity CLI: [`$req-create`]
- ✅ OpenAI Codex: [`$req-create`]
- ✅ Claude Code: [`/req-create`]
- ✅ OpenCode: [`/req-create`]

#### CLI Prompt Details
- ✅ pi.dev CLI: [`/req-create.prompt`]
  - useReq generates `~/.pi/agent/prompts/req-create.prompt.md`.
  - pi prompt templates use the filename without `.md` as the command name, so the generated `.prompt` suffix remains part of the slash command.
  - Prompt arguments are supported by pi prompt templates (`$1`, `$2`, `$@`, `$ARGUMENTS`).
- ✅ Antigravity CLI: [`/req:create`]
- ✅ OpenAI Codex: [`/prompts:/req-create`]
- ✅ Claude Code: [`/req:create`]
- ✅ OpenCode: [`/req-create`]

#### CLI Agents Details
- ❌ pi.dev CLI
  - useReq does not generate agents for provider `pi`; it emits prompts and skills only.
- ❌ Antigravity CLI
- ❌ OpenAI Codex
- ✅ Claude Code: [`@agent-req-create`]
- ✔️ OpenCode: [`<TAB> ➡️ Req.Create ↩️`]
  - **Starts a new session** (`/new`) for every prompt.


## Known Issues

- **Grok Code Fast 1** does not respect the TODO list and does not wait for user approval.
  * Defect #3180 → [Bug: Grok Code Fast 1 not update to do list correctly #3180](https://github.com/Kilo-Org/kilocode/issues/3180)


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
