---
description: "Write a REFERENCES.md using the project's source code"
argument-hint: "No arguments utilized by the prompt logic"
usage: >
  Use when the user asks to create, regenerate, or update REFERENCES.md as a source-derived repository navigation and symbol index. Change only that document and commit the update. Use /req-workflow for the runtime execution model, /req-flowchart for a Mermaid runtime diagram, or /req-analyze for an investigation without file edits. Do not select for general reference research, requirements changes, implementation, tests, or edits to other documents.
---

# Write a REFERENCES.md using the project's source code

## Purpose
Maintain a machine-usable reference index (`%%DOC_PATH%%/REFERENCES.md`) derived from repository evidence so downstream LLM Agents MUST quickly discover entrypoints, modules, dependencies, and other navigational anchors during SRS-driven work.

## Scope
In scope: generate/update only `%%DOC_PATH%%/REFERENCES.md` in English (following the prompt’s `req --references` workflow) and commit that doc change. Out of scope: changes to requirements, workflow docs, source code, or tests.

## Professional Personas
- **Act as a Prompt Engineer and LLM Optimization Specialist** whenever you design, write, modify, or analyze prompts, agents, skills, or documents whose target audience is an LLM Agent instead of a human reader.
- **Act as a Senior System Engineer** when analyzing source code and directory structures to understand the system's architecture and logic.
- **Act as a Technical Writer** when producing the final reference index, ensuring clarity, technical precision, and structured formatting.
- **Act as an Expert GitOps Engineer** when executing git workflows, especially when creating/removing/managing git worktrees to isolate changes safely.

## Iteration and Context Economy
- **CRITICAL**: Plan every Step to complete in the minimum number of iterations; batch independent reads, searches, and edits into a single response and dispatch parallel tool calls whenever no dependency forces sequencing.
- **CRITICAL**: MUST NOT re-read, re-search, or re-fetch any file already provided as injected context or already read in the current session; reuse prior tool-output evidence instead.
- **CRITICAL**: MUST NOT restate requirement text, prior tool output, or unchanged file contents into the context; cite them by file path, symbol, and line range, quoting only the minimal changed snippet.
- **CRITICAL**: MUST add only information required by the active Step, a requirement ID, or explicit user-request text; omit narration, filler, restatements, and speculative commentary.
- **CRITICAL**: MUST choose the most token-efficient evidence path in order: `%%DOC_PATH%%/REQUIREMENTS.md`, `%%DOC_PATH%%/WORKFLOW.md`, `%%DOC_PATH%%/REFERENCES.md`, then `req --find`/`req --files-find`, then `rg`/`grep` fallback, reading only targeted constructs and line ranges.
- **CRITICAL**: MUST gather all evidence a Step needs before producing its output and MUST NOT split a single logical operation across multiple iterations when one suffices.
- **CRITICAL**: MUST pause and wait for a tool response only when a Step explicitly depends on it; otherwise proceed autonomously to the next Step without requesting confirmation.
- **CRITICAL**: These rules MUST govern how the agent organizes and sequences the work described in the `## Steps` section.

## Pre-requisite: Execution Context
- **CRITICAL**: All information declared in this `Pre-requisite: Execution Context` section MUST remain continuously available in the active execution context for the entire workflow and MUST NEVER be dropped, forgotten, or overwritten.
- Generate <WORKTREE_NAME> with `req --git-wt-name`, retain the literal result for later steps, and use simple sequential execution with only linear shell commands compatible with restrictive filtering systems for all worktree operations in this workflow.


## Absolute Rules, Non-Negotiable
- **CRITICAL**: When instructions generate shell commands, they MUST generate only linear shell commands compatible with restrictive filtering systems, MUST verify and apply correct quoting, escaping, or option termination for literal arguments that could be parsed as options or flags, MUST use explicit option termination for `rg` and `git grep` patterns beginning with `-` or `--`, MUST NOT rely on quoting or backslash escaping alone for those patterns, and MUST NOT use command substitution (`$()` or backticks), complex variable expansion, nested substitution, shell-derived helper composition, nested shell logic, or nested pipelines.
- **CRITICAL**: NEVER write, modify, edit, or delete files outside of the active git worktree directory, except under `/tmp`, and except for worktree operations executed through `req --git-wt-create <WORKTREE_NAME>` and `req --git-wt-delete <WORKTREE_NAME>`.
- You can read, write, or edit `%%DOC_PATH%%/REFERENCES.md`.
- Treat static analysis as safe. Verification commands MUST NOT modify tracked files and MUST be treated as read-only evidence collection.
- **CRITICAL**: Do not modify any project files except creating/updating `%%DOC_PATH%%/REFERENCES.md`.
- **CRITICAL**: GIT operations and GIT rules:
   - Do not run any shell/git commands and do not modify any files before starting Step 1 (including creating/modifying files, installing deps, formatting, etc.), except the read-only repository checks required by the `## Pre-Flight: Context Keyword Resolution` section: **CRITICAL**: Check GIT Status.
   - Step 1 may run only the git commands `git rev-parse --is-inside-work-tree`, `git rev-parse --verify HEAD`, `git status --porcelain`, and `git symbolic-ref -q HEAD` (plus minimal shell built-ins to combine their outputs into a single cleanliness check).
   - If the repository is NOT clean (modified files, staged changes, OR untracked files), exit immediately without changing anything.
   - At the end you MUST commit only the intended changes with a unique identifier and change description in the commit message.
   - Leave the working tree AND index clean (git `status --porcelain` must be empty).
   - Do NOT “fix” a dirty repo by force (no `git reset --hard`, no `git clean -fd`, no stash) unless explicitly requested. If dirty: abort.

## Behavior
- Do not perform unrelated edits.
- If `.venv/bin/python` exists in the project root, use it for Python executions (eg, `PYTHONPATH=src .venv/bin/python -m <program name>`).
- Non-Python tooling should use the project's standard commands.
- Use filesystem/shell tools to read/write/delete files as needed (e.g., `cat`, `sed`, `perl -pi`, `printf > file`, `rm -f`, ...), but only to read project files and to write/update `%%DOC_PATH%%/REFERENCES.md`. Avoid in-place edits on any other path. Prefer read-only commands for analysis.


## Execution Protocol (Global vs Local)
You must manage the execution flow using two distinct methods:
-  **Global Roadmap** (*check-list*): 
   - You MUST maintain a *check-list* internally with `6` Steps (one item per Step).
   - **Do NOT** use the *task-list tool* for this high-level roadmap.
-  **Local Sub-tasks** (Tool Usage): 
   - If a *task-list tool* is available, use it **exclusively** to manage granular sub-tasks *within* a specific step (e.g., in Step X: "1. Edit file A", "2. Edit file B"; or in Step Y: "1. Fix test K", "2. Fix test L").
   - Clear or reset the tool's state when transitioning between high-level steps.

## Execution Directives (absolute rules, non-negotiable)
During the execution flow you MUST follow these directives:
- **CRITICAL** Autonomous Execution:
   - Implicit Autonomy: Execute all tasks with full autonomy. Do not request permission, confirmation, or feedback. Make executive decisions based on logic and technical best practices.
   - Tool-Aware Workflow: Proceed through the Steps sequentially; when a tool call is required, stop and wait for the tool response before continuing. Never fabricate tool outputs or tool results. Do not reveal internal reasoning; output only the deliverables explicitly requested by the Steps section.
   - Autonomous Resolution: If ambiguity is encountered, first disambiguate using repository evidence (requirements, code search, tests, logs). If multiple interpretations remain, choose the least-invasive option that preserves documented behavior and record the assumption as a testable requirement/acceptance criterion.
   - After the prompt's execution: Strictly omit all concluding remarks and do not propose any other steps/actions.
- **CRITICAL**: Order of Execution:
  - Execute the numbered steps below sequentially and strictly, one at a time, without skipping or merging steps. Create and maintain a *check-list* internally while executing the Steps. Execute the Steps strictly in order, updating the *check-list* as each step completes. 
- **CRITICAL**: Immediate start and never stop:
  - Complete all Steps in order; you may pause only to perform required tool calls and to wait for their responses. Do not proceed past a Step that depends on a tool result until that result is available.
  - Start immediately by creating a *check-list* for the **Global Roadmap** and directly start following the roadmap from the Step 1.


## Pre-Flight: Context Keyword Resolution
- **CRITICAL**: Before executing any Step, determine the concrete value of each context keyword below, validate it against repository evidence, and save all three resolved values in the active execution context; they MUST remain continuously available for the entire workflow and MUST NEVER be dropped, forgotten, or overwritten.
- `%%DOC_PATH%%`: directory containing `REQUIREMENTS.md`, `WORKFLOW.md`, and `REFERENCES.md`; normally `usereq/docs` inside the git repository root. Different projects may declare different `usereq/docs` directories, each belonging to exactly one project; determine the correct path based on the modifications this workflow will execute.
- `%%SRC_PATHS%%`: directory containing the project sources to modify; normally `src/` inside the working git repository. Different projects may declare different `src/` paths; determine the correct working path for the current task.
- `%%TEST_PATH%%`: directory containing the project tests; normally `tests/` inside the working git repository. Different projects may declare different `tests/` paths; determine the correct working path for the current task.
- Resolution rules, executed in order, using read-only commands only:
  1. Start from the substituted values provided in this prompt.
  2. For `%%DOC_PATH%%`, verify that `REQUIREMENTS.md`, `WORKFLOW.md`, and `REFERENCES.md` exist under the resolved directory.
  3. For `%%SRC_PATHS%%` and `%%TEST_PATH%%`, select the path pertinent to the modifications this workflow will execute when multiple candidate paths exist in the working git repository.
- **CRITICAL**: If any of the three keyword values cannot be determined correctly and unambiguously, OUTPUT exactly "ERROR: Unable to resolve context keywords!", and then terminate the execution.
- Mandatory context loading: after successful keyword resolution, load in full into the active execution context the canonical documents used by this workflow: `%%DOC_PATH%%/REFERENCES.md`; treat a document already injected as prompt context as loaded and do not re-read it; keep every loaded document available for the entire workflow.

## Steps
Create internally a *check-list* for the **Global Roadmap** including all the numbered steps below: `1..6`, and start following the roadmap at the same time, executing the tool call of Step 1 (Check GIT Status). If a tool call is required in Step 1, invoke it immediately; otherwise proceed to Step 1 without additional commentary. Do not add extra intent-adjustment checks unless explicitly listed in the Steps section.
1. **CRITICAL**: Check GIT Status
   - Check GIT status with `req --git-check`. If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Git status unclear!", and then terminate the execution.
2. **CRITICAL**: Worktree Generation & Isolation
   - Derive <BASE_PATH> with `req --get-base-path`, derive <GIT_PATH> with `req --git-path`, and generate <WORKTREE_NAME> with `req --git-wt-name` using literal `req` commands executed sequentially without shell composition.
   - Create the dedicated isolated worktree with `req --git-wt-create <WORKTREE_NAME>`, then execute `cd <GIT_PATH>/../<WORKTREE_NAME>` before proceeding to the next step.
   - If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree generation failed!", and then terminate the execution.

3. Update `%%DOC_PATH%%/REFERENCES.md` references file
   -  Create/update the references file with `req --here --references >"%%DOC_PATH%%/REFERENCES.md"`
4. **CRITICAL**: Stage & commit
   - Show a summary of changes with `git diff` and `git diff --stat`.
   - Stage changes explicitly (prefer targeted add; avoid `git add -A` if it may include unintended files): `git add <file...>` (ensure to include only `%%DOC_PATH%%/REFERENCES.md`).
   - Ensure there is something to commit with: `git diff --cached --quiet && echo "Nothing to commit. Aborting."`. If command output contains "Aborting", OUTPUT exactly "No changes to commit.", and then delete the isolated worktree and branch with `req --git-wt-delete <WORKTREE_NAME>`, and then terminate the execution.
   - Commit a structured commit message with: `git commit -m "docs(<COMPONENT>)<BREAKING>: <DESCRIPTION> [useReq]"`
      - Set `<COMPONENT>` to the most specific component, module, or function affected. If multiple areas are touched, choose the primary one. If you cannot identify a unique component, use `core`.
      - Set `<DESCRIPTION>` to a short, clear summary in **English language** of what changed, including (when applicable) updates to: requirements/specs, source code, tests. Use present tense, avoid vague wording, and keep it under ~80 characters if possible.
      - Set `<BREAKING>` to `!` if a breaking change was implemented (a modification to an API, library, or system that breaks backward compatibility, causing dependent client applications or code to fail or behave incorrectly), set empty otherwise.
      - Include main features added, requirements changes, or a bug-fix description adding a multi-line comment (maximum 10 lines).
         - Do not include the 'Co-authored-by' trailer or any AI attribution. A GPG-signed commit is not required.
   - Confirm the repo is clean with `req --git-check`. If the command returns an error code or prints any text containing "ERROR", override the final line with EXACTLY "WARNING: References request completed with unclean git repository!".
5. **CRITICAL**: Merge Conflict Management
   - Return to the original repository directory (the sibling directory of the worktree).
   - Ensure you are on the original branch used before worktree creation by deriving `<BASE_PATH>` with `req --get-base-path` if needed and executing `cd <BASE_PATH>`.
   - Merge the isolated branch into the original branch: `git merge <WORKTREE_NAME>`
   - If the merge completes successfully, delete the isolated worktree and branch with `req --git-wt-delete <WORKTREE_NAME>`; if the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree cleanup verification failed!", and then terminate the execution.
   - If the merge fails or results in conflicts, do NOT remove the worktree directory and override the final line with EXACTLY "WARNING: References request completed with merge conflicting!".
6. Present results
   - PRINT, in the response, the results for a human reader using clear, easily understandable sentences and readable Markdown formatting that highlight key findings, file paths, and concise evidence. Use the fixed report schema: ## **Outcome**, ## **Requirement Delta**, ## **Design Delta**, ## **Implementation Delta**, ## **Verification Delta**, ## **Evidence**, ## **Assumptions**, ## **Next Workflow**. Final line MUST be exactly: STATUS: OK or STATUS: ERROR.
