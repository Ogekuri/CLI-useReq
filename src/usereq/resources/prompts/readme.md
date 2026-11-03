---
description: "Write README.md from user-visible implementation evidence"
argument-hint: "Description of additional edits to perform on README.md file"
usage: >
  Use when the user asks to create, update, or correct root README.md using current implementation evidence, or requests explicit editorial changes confined to that file. Cover user-visible features, setup, CLI options, GUI interactions, APIs, and configuration; preserve unrelated content and formatting. A source-code behavior change is not required for activation. Change only README.md and commit the update. Do not select for internal architecture documentation, other document updates, or changes to requirements, source code, or tests.
---

# Write README.md from user-visible implementation evidence

## Pre-Flight: Context Keyword Resolution
- **CRITICAL**: Complete this read-only gate before any path-dependent action or numbered Step. Immediate-start directives apply only after success; autonomous disambiguation MUST NOT guess `{{PRJ_BASE}}` or `{{GIT_BASE}}`.
- Runtime keywords: resolve exactly two LLM-resolved path keywords in fixed order: `{{PRJ_BASE}}` first, `{{GIT_BASE}}` second. Installation has already supplied the documentation, source, and test paths; use them as fixed relative suffixes, not values to discover or replace.
- Project base: `{{PRJ_BASE}}` is the absolute base directory of the unique target project containing its installation-supplied `%%DOC_PATH%%`, `%%SRC_PATHS%%`, and `%%TEST_PATH%%` directories.
- Git base: `{{GIT_BASE}}` is the absolute base directory of the git repository containing `{{PRJ_BASE}}`. One git repository can contain multiple projects; repository identity alone never identifies the project.
- Resolution order: identify `{{PRJ_BASE}}` first and uniquely from current invocation routing and explicit task scope; use uniquely corroborated project path metadata only for missing evidence. The current directory is a candidate, not a default. Conflicting bindings, multiple plausible projects, or stale cross-project values fail resolution. Source-free workflows inspect path metadata only. After `{{PRJ_BASE}}` is bound, derive `{{GIT_BASE}}` as the git repository root containing the bound project base.
- Binding: retain `{{PRJ_BASE}}`, `{{GIT_BASE}}`, active worktree root, project identity, evidence, directory existence states, and document provenance throughout this invocation. Start fresh for each invocation; replace the bindings only after a validated context transition.
- Paths: substitute the resolved base in each prefixed path. For an installation-supplied source list, apply the base separately to every entry; preserve order and explicit list boundaries, never split on spaces or commas. Treat paths as data and quote each resulting literal argument separately, with option termination where supported.
- Containment: validate the base and resulting paths inside the active worktree, including symlink targets and existing ancestors of prospective paths. Accept absent directories only for authorized creation or explicitly unused source/test scopes; absence is not an unresolved base. Create nothing during pre-flight.
- Document contract below: filenames are relative to the installation-supplied documentation path under `{{PRJ_BASE}}`. Required inputs MUST exist; creatable targets MAY be absent. Load exactly the listed existing documents in full before Steps, including existing targets; defer reads of absent creatable targets until generated. Unlisted canonical documents are not prerequisites.
  - Required inputs: WORKFLOW.md, REFERENCES.md.
  - Creatable targets: none.
  - Load when present: WORKFLOW.md, REFERENCES.md.
- Context reuse: treat injected or previously read content as loaded only when repository, worktree, project-area, path, and revision provenance match this binding. Current runtime attestation or unchanged-file evidence can establish a match; a basename alone cannot. Refresh stale or unverified content from the resolved path; reuse matching content without re-reading. After an edit, retain the verified updated content and invalidate superseded evidence.
- Operation scope: run cwd-sensitive commands and configured tools from `{{PRJ_BASE}}` only when their effective scope matches the target project; otherwise use a documented explicit-path equivalent or fail resolution.
- Activity routing: reference all project-modification and requirements-modification activities exclusively to `{{PRJ_BASE}}`; reference only working-tree creation and git-management activities to `{{GIT_BASE}}`.
- Context transitions: after an authorized worktree change, rebase `{{PRJ_BASE}}` to the same project-relative location in the new worktree and rebase `{{GIT_BASE}}` to the new worktree's repository root. Revalidate containment and document provenance before project operations; discard old absolute paths. Reuse document contents only with verified unchanged-file evidence. A different target project requires a fresh invocation.
- **CRITICAL**: If `{{PRJ_BASE}}` or `{{GIT_BASE}}`, required document, containment check, or effective tool scope remains unresolved or conflicting, OUTPUT exactly "ERROR: Unable to resolve context keywords!". Before isolation, terminate without cleanup; after successful isolation, follow the context-resolution failure cleanup in the isolation Step before terminating.

## Purpose
Maintain root `README.md` as the first user-facing document by aligning it with externally visible behavior from repository evidence, so downstream LLM Agents and users can understand current usage without reading internal implementation.

## Scope
In scope: static analysis of user-visible behavior from {{PRJ_BASE}}/%%SRC_PATHS%% and related runtime interfaces, then targeted updates to root `README.md` in English only, then commit that doc change. Out of scope: changes to requirements/workflow/references docs, source code, or tests.


## Professional Personas
- **Act as a Prompt Engineer and LLM Optimization Specialist** whenever you design, write, modify, or analyze prompts, agents, skills, or documents whose target audience is an LLM Agent instead of a human reader.
- **Act as a Senior System Engineer** when analyzing source code and interfaces to identify externally visible behavior changes.
- **Act as a Business Analyst** when mapping implementation behavior to user outcomes and usage expectations.
- **Act as a Senior Technical Writer** when producing the final README text as concise, user-centric guidance for first-time readers.
- **Act as a QA Auditor** when reporting facts, requiring concrete evidence (file paths, line numbers) for every user-visible claim.
- **Act as an Expert GitOps Engineer** when executing git workflows, especially when creating/removing/managing git worktrees to isolate changes safely.


## Iteration and Context Economy
- **CRITICAL**: Plan every Step to complete in the minimum number of iterations; batch independent reads, searches, and edits into a single response and dispatch parallel tool calls whenever no dependency forces sequencing.
- **CRITICAL**: Reuse injected or previously read file evidence only when repository, worktree, project-area, path, and revision identity match the active binding; do not re-read matching content. Refresh stale or unverified evidence under the pre-flight context-reuse rules.
- **CRITICAL**: MUST NOT restate requirement text, prior tool output, or unchanged file contents into the context; cite them by file path, symbol, and line range, quoting only the minimal changed snippet.
- **CRITICAL**: MUST add only information required by the active Step, a requirement ID, or explicit user-request text; omit narration, filler, restatements, and speculative commentary.
- **CRITICAL**: MUST choose the most token-efficient evidence path in order: `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md`, `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md`, then `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --find`/`req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --files-find`, then `rg`/`git grep` fallback, reading only targeted constructs and line ranges.
- **CRITICAL**: MUST gather all evidence a Step needs before producing its output and MUST NOT split a single logical operation across multiple iterations when one suffices.
- **CRITICAL**: MUST pause and wait for a tool response only when a Step explicitly depends on it; otherwise proceed autonomously to the next Step without requesting confirmation.
- **CRITICAL**: These rules MUST govern how the agent organizes and sequences the work described in the `## Steps` section.

## Pre-requisite: Execution Context
- **CRITICAL**: All information declared in this `Pre-requisite: Execution Context` section MUST remain continuously available in the active execution context for the entire workflow and MUST NEVER be dropped, forgotten, or overwritten.
- Generate <WORKTREE_NAME> with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-name`, retain the literal result for later steps, and use simple sequential execution with only linear shell commands compatible with restrictive filtering systems for all worktree operations in this workflow.


## Absolute Rules, Non-Negotiable
- **CRITICAL**: When instructions generate shell commands, they MUST generate only linear shell commands compatible with restrictive filtering systems, MUST verify and apply correct quoting, escaping, or option termination for literal arguments that could be parsed as options or flags, MUST use explicit option termination for `rg` and `git grep` patterns beginning with `-` or `--`, MUST NOT rely on quoting or backslash escaping alone for those patterns, and MUST NOT use command substitution (`$()` or backticks), complex variable expansion, nested substitution, shell-derived helper composition, nested shell logic, or nested pipelines.
- **CRITICAL**: Every `req` invocation MUST carry the mandatory parameters `--prj-base={{PRJ_BASE}}` and `--git-base={{GIT_BASE}}` with the resolved values; the removed `--base` parameter MUST NOT be used.
- **CRITICAL**: NEVER write, modify, edit, or delete files outside of the active git worktree directory, except under `/tmp`, and except for worktree operations executed through `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-create <WORKTREE_NAME>` and `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete <WORKTREE_NAME>`.
- You can read, write, or edit `README.md`.
- Treat static analysis as safe. Verification commands MUST NOT modify tracked files and MUST be treated as read-only evidence collection.
- **CRITICAL**: Do not modify any project files except creating/updating root `README.md`.
- **CRITICAL**: GIT operations and GIT rules:
   - Do not run any shell/git commands and do not modify any files before starting Step 1 (including creating/modifying files, installing deps, formatting, etc.), except the read-only repository checks required by the `## Pre-Flight: Context Keyword Resolution` section: **CRITICAL**: Check GIT Status.
   - Step 1 may run only the git commands `git rev-parse --is-inside-work-tree`, `git rev-parse --verify HEAD`, `git status --porcelain`, and `git symbolic-ref -q HEAD` (plus minimal shell built-ins to combine their outputs into a single cleanliness check).
   - If the repository is NOT clean (modified files, staged changes, OR untracked files), exit immediately without changing anything.
   - At the end you MUST commit only the intended changes with a unique identifier and change description in the commit message.
   - Leave the working tree AND index clean (git `status --porcelain` must be empty).
   - Do NOT "fix" a dirty repo by force (no `git reset --hard`, no `git clean -fd`, no stash) unless explicitly requested. If dirty: abort.
- **CRITICAL**: Formulate all source code information using a highly structured, machine-interpretable Markdown format with unambiguous, atomic syntax to ensure maximum reliability for downstream LLM agentic reasoning, avoiding any conversational filler or subjective adjectives; the **target audience** is other **LLM Agents** and Automated Parsers, NOT humans, use high semantic density, optimized to contextually enable an LLM to perform future refactoring or extension.

## Behavior
- Write root `README.md` in English.
- Do not perform unrelated edits.
- Analyze user-visible implementation changes, including new features, CLI parameters/options, GUI interactions, distributed APIs, and configuration-file schema updates when present.
- Validate whether the current root `README.md` is aligned with implementation evidence; identify exact sections to update first, then update only missing, outdated, or incorrect user-facing content in those sections.
- Parse [User Request](#users-request) (`%%ARGS%%`) as explicit additional-edit directives, using the same anchor-based reference model used by `write.md`, and execute those directives in the same scoped README update pass.
- Keep non-analysis documentary sections unchanged, including document headers, versioning metadata, context/scope descriptions, personal motivations, related projects, and high-level conceptual or graphical descriptions that do not alter interface usage.
- Preserve existing README structure and formatting patterns (section order, heading hierarchy, bullet/list style, table style) whenever possible.
- Exclude internal implementation details, internal architecture logic, private symbols, and algorithm internals from `README.md`.
- Use the repository's existing language-specific environment/toolchain to execute code and tests; do NOT create new environments unless explicitly requested by the user. For Python, prefer Astral `uv` (`uv run`, `uvx`) when available, then fall back to the repository's existing `.venv` (if present). For other ecosystems (e.g., Node.js, Rust, C/C++), use the project's standard commands.
- Use filesystem/shell tools to read/write/delete files as needed (e.g., `cat`, `sed`, `perl -pi`, `printf > file`, `rm -f`, ...), but only to read project files and to write/update root `README.md`. Avoid in-place edits on any other path. Prefer read-only commands for analysis.


## Canonical Terminology (MUST use these exact terms)
- **User-visible behavior**: any behavior directly observable by an end user through CLI, GUI, APIs, outputs, or configuration.
- **External interface surface**: the exposed contract that users or integrators interact with (commands, flags, endpoints, UI elements, config schema).
- **Internal implementation detail**: any internal class, function, module wiring, or algorithmic logic not required for end-user operation.
- **README coverage item**: a user-visible behavior that MUST be represented in root `README.md` with actionable usage guidance.


## Source Code Analysis Toolkit
Four complementary pillars provide a complete, token-efficient source code analysis pipeline. Execute in order (1→2→3→4) to maximize evidence quality while minimizing unnecessary code reads.

### 1. Runtime Model: `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md`
Compact document — read in full. Contains:
- **Execution Units Index**: all OS processes and threads with roles and entrypoints.
- **Execution Units**: per-unit internal call-trace trees showing function call order, defining file paths, and external boundaries.
- **Communication Edges**: inter-unit data flow (direction, mechanism, payload).

Use to: identify which execution units (processes/threads) are involved, trace call-order through internal functions, understand data flow between components. Build a runtime mental model before reading any code.

### 2. Symbol Index: `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md`
Structured index of all source-defined symbols (functions, classes, structs, objects, data structures) with file paths and line numbers. Per-symbol Doxygen-style fields may include:
- `@brief`: single-line technical description of the symbol's action.
- `@details`: high-density algorithmic summary (LLM-optimized, not prose).
- `@param` / `@param[out]`: input parameters with type constraints; mutated reference/pointer arguments.
- `@return` / `@retval`: output data structure or specific return values.
- `@exception` / `@throws`: error states and specific exception classes.
- `@satisfies`: linked requirement IDs (e.g., `@satisfies REQ-026, REQ-045`).
- `@pre` / `@post`: pre-conditions and post-conditions.
- `@warning`: critical usage hazards.
- `@note`: vital implementation details.
- `@see` / `@sa`: related symbols for context linkage.
- `@deprecated`: replacement API link.

Use to: identify candidate symbols by name, description, or `@satisfies` link; obtain exact file paths and line ranges; understand function signatures and contracts before extracting code. Cross-reference with WORKFLOW.md call-traces to narrow scope.

### 3. Code Extraction: `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --find` / `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --files-find`
Extract actual source constructs as structured markdown with signatures, line ranges, and optional line-numbered code. Use after pillars 1-2 to extract only the targeted constructs identified during analysis.
#### What these commands do (and what they don't)
- Extract named constructs (e.g., CLASS, FUNCTION, STRUCT, INTERFACE, IMPORT, …) filtered by TAG and name-regex.
- Regex (PATTERN) matches construct name only (not body). For body-content search, use rg/git grep (pillar 4).
- Output per file: header `@@@ <filepath> | <language>`, per-construct blocks with:
    - `### <TAG>: <name>` + optional Signature + `Lines: <start>-<end>`
    - optional extracted Doxygen fields (if present in/around the construct)
    - fenced code block with the complete construct slice (comments stripped, strings preserved)
#### Choose the right mode
- Project-wide scan: use --find (the mandatory `--prj-base`/`--git-base` prefix is required; `--base` is forbidden)
    - Syntax: `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --find <TAG_FILTER> <NAME_REGEX>`
    - Note: --find scans all files under configured source dirs; does not take a filename.
- Target specific files: use --files-find (standalone with the mandatory `--prj-base`/`--git-base` prefix)
    - Syntax: `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --files-find <TAG_FILTER> <NAME_REGEX> <FILE1> [FILE2 ...]`
#### Enable line-numbered code for evidence citation
Add --enable-line-numbers (code lines prefixed as `<n>:`):
- `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --enable-line-numbers --find "<TAG_FILTER>" "<NAME_REGEX>"`
- `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --enable-line-numbers --files-find "<TAG_FILTER>" "<NAME_REGEX>" <FILE...>`
#### TAGs and filters
- TAG_FILTER: pipe-separated, case-insensitive (e.g., `CLASS|FUNCTION|IMPORT`).
- Tags are language-dependent; unsupported tags are ignored. Run `req -h` for supported TAGs per language.
- Broad cross-language TAG_FILTER: `CLASS|STRUCT|ENUM|INTERFACE|TRAIT|IMPL|FUNCTION|METHOD|MODULE|NAMESPACE|TYPE_ALIAS|TYPEDEF|IMPORT|CONSTANT|VARIABLE|MACRO|DECORATOR|COMPONENT|PROPERTY|PROTOCOL|EXTENSION|UNION`
#### Regex rules (NAME_REGEX)
- Regex matching follows `re.search()` semantics against construct names (tool behavior, independent of repository language).
- Prefer anchored patterns: exact `^Foo$`, prefix `^parse_`, suffix `Service$`. Use `.*` only when scope is already constrained by files/TAGs.
#### Failure modes you must handle
- "No constructs found": adjust TAGs (supported?), file paths, or NAME_REGEX (valid regex?).
- Regex-based extractor (not full AST): treat results as evidence pointers; confirm edge cases by opening referenced file/lines.

### 4. Supplementary Search: `rg` / `git grep`
Use for: string/pattern searches inside code bodies, cross-file references, configuration values, error messages, or any content not captured by construct-name-based extraction.

### Recommended Analysis Workflow
1. **Read `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md`** (full read) → identify execution units, call-trace paths, and function names relevant to the task.
2. **Read `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md`** (full read or targeted search) → locate candidate symbols by name/description/`@satisfies`, obtain file paths and line ranges, understand function contracts.
3. **Extract code** via `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --find`/`req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --files-find` → use symbol names from steps 1-2 as NAME_REGEX, file paths as --files-find targets; enable --enable-line-numbers when citing evidence.
4. **Search code bodies** via `rg`/`git grep` → find patterns, references, or values not captured by construct-level extraction.


## Execution Protocol (Global vs Local)
You must manage the execution flow using two distinct methods:
-  **Global Roadmap** (*check-list*):
   - You MUST maintain a *check-list* internally with `7` Steps (one item per Step).
   - **Do NOT** use the *task-list tool* for this high-level roadmap.
-  **Local Sub-tasks** (Tool Usage):
   - If a *task-list tool* is available, use it **exclusively** to manage granular sub-tasks *within* a specific step (e.g., in Step X: "1. Edit file A", "2. Edit file B"; or in Step Y: "1. Fix test K", "2. Fix test L").
   - Clear or reset the tool's state when transitioning between high-level steps.

## Execution Directives (absolute rules, non-negotiable)
During the execution flow you MUST follow these directives:
- **CRITICAL** Autonomous Execution:
   - Implicit Autonomy: Execute all tasks with full autonomy. Do not request permission, confirmation, or feedback. Make executive decisions based on logic and technical best practices.
   - Tool-Aware Workflow: Proceed through the Steps sequentially; when a tool call is required, stop and wait for the tool response before continuing. Never fabricate tool outputs or tool results. Do not reveal internal reasoning; output only the deliverables explicitly requested by the Steps section.
   - Autonomous Resolution: Resolve `{{PRJ_BASE}}` ambiguity only through the pre-flight evidence rules; unresolved bindings trigger the context-resolution failure branch. For other ambiguities, use repository evidence (requirements, code search, tests, logs), choose the least-invasive interpretation preserving documented behavior, and record the assumption as a testable requirement/acceptance criterion.
   - After the prompt's execution: Strictly omit all concluding remarks and do not propose any other steps/actions.
- **CRITICAL**: Order of Execution:
  - Execute the numbered steps below sequentially and strictly, one at a time, without skipping or merging steps. Create and maintain a *check-list* internally while executing the Steps. Execute the Steps strictly in order, updating the *check-list* as each step completes.
- **CRITICAL**: Immediate start and never stop:
  - Complete all Steps in order; you may pause only to perform required tool calls and to wait for their responses. Do not proceed past a Step that depends on a tool result until that result is available.
  - After successful pre-flight resolution, create a *check-list* for the **Global Roadmap** and start following the roadmap from Step 1.


## Steps
After successful pre-flight resolution, create internally a *check-list* for the **Global Roadmap** including all the numbered steps below: `1..7`, and start following the roadmap at the same time, executing the tool call of Step 1 (Check GIT Status). If a tool call is required in Step 1, invoke it immediately; otherwise proceed to Step 1 without additional commentary. Do not add extra intent-adjustment checks unless explicitly listed in the Steps section.
1. **CRITICAL**: Check GIT Status
   - Check GIT status with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-check`. If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Git status unclear!", and then terminate the execution.
2. **CRITICAL**: Worktree Generation & Isolation
   - Derive <BASE_PATH> with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --get-base-path`, derive <GIT_PATH> with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-path`, and generate <WORKTREE_NAME> with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-name` using literal `req` commands executed sequentially without shell composition.
   - Create the dedicated isolated worktree with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-create <WORKTREE_NAME>`, then execute `cd <GIT_PATH>/../<WORKTREE_NAME>` before proceeding to the next step.
   - If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree generation failed!", and then terminate the execution.
   - After successful worktree creation and directory change, apply the pre-flight context-transition rules before the next project operation. If rebinding fails, OUTPUT exactly "ERROR: Unable to resolve context keywords!", delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete <WORKTREE_NAME>`, and then terminate the execution. Apply this same failure cleanup to later context-resolution failures before merge-phase cleanup.

3. Static analysis: detect user-visible implementation surface
   - Analyze files under {{PRJ_BASE}}/%%SRC_PATHS%% and other directly related user-entry artifacts to identify externally visible changes:
      - New or changed end-user features.
      - CLI commands, options, arguments, flags, defaults, or examples.
      - GUI workflows, screens, controls, labels, and interaction flows.
      - Distributed API endpoints, request/response shapes, auth usage, and versioned contracts.
      - Configuration file format, keys, defaults, constraints, and migration notes when present.
   - Use repository evidence only; for each finding, collect file paths and line ranges.
   - Derive a compact "README coverage list" of user-visible behavior that MUST appear in root `README.md`.
4. Validate and update root `README.md`
   - Read the current root `README.md` and compare it with the README coverage list from Step 3.
   - Identify and list the exact `README.md` sections impacted by the detected user-visible implementation changes and explicit additional edits from [User Request](#users-request) before editing.
   - Update only the identified sections so `README.md` reflects the current externally visible behavior and usage flows.
   - Keep all non-analysis documentary sections unchanged (e.g., headers, versioning, context/scope narratives, motivations, related projects, high-level graphics/descriptions not tied to interface behavior).
   - Keep content focused on user interaction, setup, commands, interfaces, and observable outputs.
   - Do NOT add internal implementation details, internal architecture, private symbol names, or algorithm internals.
   - Preserve the existing README structure and formatting whenever possible while applying the scoped updates.
5. **CRITICAL**: Stage & commit
   - Show a summary of changes with `git diff` and `git diff --stat`.
   - Stage changes explicitly (prefer targeted add; avoid `git add -A` if it may include unintended files): `git add <file...>` (ensure to include only `README.md`).
   - Ensure there is something to commit with: `git diff --cached --quiet && echo "Nothing to commit. Aborting."`. If command output contains "Aborting", OUTPUT exactly "No changes to commit.", and then delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete <WORKTREE_NAME>`, and then terminate the execution.
   - Commit a structured commit message with: `git commit -m "docs(<COMPONENT>)<BREAKING>: <DESCRIPTION> [useReq]"`
      - Set `<COMPONENT>` to the most specific component, module, or function affected. If multiple areas are touched, choose the primary one. If you cannot identify a unique component, use `core`.
      - Set `<DESCRIPTION>` to a short, clear summary in **English language** of what changed, including (when applicable) updates to: requirements/specs, source code, tests. Use present tense, avoid vague wording, and keep it under ~80 characters if possible.
      - Set `<BREAKING>` to `!` if a breaking change was implemented (a modification to an API, library, or system that breaks backward compatibility, causing dependent client applications or code to fail or behave incorrectly), set empty otherwise.
      - Include main features added, requirements changes, or a bug-fix description adding a multi-line comment (maximum 10 lines).
         - Do not include the 'Co-authored-by' trailer or any AI attribution. A GPG-signed commit is not required.
   - Confirm the repo is clean with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-check`. If the command returns an error code or prints any text containing "ERROR", override the final line with EXACTLY "WARNING: README request completed with unclean git repository!".
6. **CRITICAL**: Merge Conflict Management
   - Return to the original repository directory (the sibling directory of the worktree).
   - Ensure you are on the original branch used before worktree creation by deriving `<BASE_PATH>` with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --get-base-path` if needed and executing `cd <BASE_PATH>`.
   - Merge the isolated branch into the original branch: `git merge <WORKTREE_NAME>`
   - If the merge completes successfully, delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete <WORKTREE_NAME>`; if the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree cleanup verification failed!", and then terminate the execution.
   - If the merge fails or results in conflicts, do NOT remove the worktree directory and override the final line with EXACTLY "WARNING: README request completed with merge conflicting!".
7. Present results
   - PRINT, in the response, the results for a human reader using clear, easily understandable sentences and readable Markdown formatting that highlight key findings, file paths, and concise evidence. Use the fixed report schema: ## **Outcome**, ## **Requirement Delta**, ## **Design Delta**, ## **Implementation Delta**, ## **Verification Delta**, ## **Evidence**, ## **Assumptions**, ## **Next Workflow**. Final line MUST be exactly: STATUS: OK or STATUS: ERROR.

<h2 id="users-request">User's Request</h2>
%%ARGS%%
