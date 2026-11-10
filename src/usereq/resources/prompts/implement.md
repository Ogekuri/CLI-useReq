---
description: "Executive skill delegated only by orchestrate.md: Build and verify an end-to-end implementation from the authoritative SRS without changing it."
argument-hint: "No arguments utilized by the prompt logic"
usage: >
  Use only when orchestrate.md delegates this executive workflow. Build and verify an end-to-end implementation from the authoritative SRS without changing it. Direct user requests must enter through the orchestration skill; do not select this executive independently.
---

# Implement source code from requirements from scratch

## Pre-Flight: Context Keyword Resolution
- **CRITICAL**: Complete this read-only gate before any path-dependent action or numbered Step. Immediate-start directives apply only after success; autonomous disambiguation MUST NOT guess `{{PRJ_BASE}}` or `{{GIT_BASE}}`.
- Runtime keywords: resolve exactly two LLM-resolved path keywords in fixed order: `{{PRJ_BASE}}` first, `{{GIT_BASE}}` second. Installation has already supplied the documentation, source, and test paths; use them as fixed relative suffixes, not values to discover or replace.
- Project base: `{{PRJ_BASE}}` is the absolute base directory of the unique target project containing its installation-supplied directories at `{{PRJ_BASE}}/%%DOC_PATH%%`, `{{PRJ_BASE}}/%%SRC_PATHS%%`, and `{{PRJ_BASE}}/%%TEST_PATH%%`.
- Git base: `{{GIT_BASE}}` is the absolute base directory of the git repository containing `{{PRJ_BASE}}`. One git repository can contain multiple projects; repository identity alone never identifies the project.
- Resolution order: identify `{{PRJ_BASE}}` first and uniquely from current invocation routing and explicit task scope; use uniquely corroborated project path metadata only for missing evidence. The current directory is a candidate, not a default. Conflicting bindings, multiple plausible projects, or stale cross-project values fail resolution. Source-free workflows inspect path metadata only. After `{{PRJ_BASE}}` is bound, derive `{{GIT_BASE}}` as the git repository root containing the bound project base.
- Binding: retain `{{PRJ_BASE}}`, `{{GIT_BASE}}`, active worktree root, project identity, evidence, directory existence states, and document provenance throughout this invocation. Start fresh for each invocation; replace the bindings only after a validated context transition.
- Paths: substitute the resolved base in each prefixed path. For an installation-supplied source list, apply the base separately to every entry; preserve order and explicit list boundaries, never split on spaces or commas. Treat paths as data and quote each resulting literal argument separately, with option termination where supported.
- Containment: validate the base and resulting paths inside the active worktree, including symlink targets and existing ancestors of prospective paths. Accept absent directories only for authorized creation or explicitly unused source/test scopes; absence is not an unresolved base. Create nothing during pre-flight.
- Document contract below: filenames are relative to the installation-supplied documentation path under `{{PRJ_BASE}}`. Required inputs MUST exist; creatable targets MAY be absent. Load exactly the listed existing documents in full before Steps, including existing targets; defer reads of absent creatable targets until generated. Unlisted canonical documents are not prerequisites.
  - Required inputs: REQUIREMENTS.md.
  - Creatable targets: WORKFLOW.md, REFERENCES.md.
  - Load when present: REQUIREMENTS.md, WORKFLOW.md, REFERENCES.md.
- Context reuse: treat injected or previously read content as loaded only when repository, worktree, project-area, path, and revision provenance match this binding. Current runtime attestation or unchanged-file evidence can establish a match; a basename alone cannot. Refresh stale or unverified content from the resolved path; reuse matching content without re-reading. After an edit, retain the verified updated content and invalidate superseded evidence.
- Operation scope: run cwd-sensitive commands and configured tools from `{{PRJ_BASE}}` only when their effective scope matches the target project; otherwise use a documented explicit-path equivalent or fail resolution.
- Activity routing: reference all project-modification and requirements-modification activities exclusively to `{{PRJ_BASE}}`; reference only working-tree creation and git-management activities to `{{GIT_BASE}}`.
- Context transitions: after an authorized worktree change, rebase `{{PRJ_BASE}}` to the same project-relative location in the new worktree and rebase `{{GIT_BASE}}` to the new worktree's repository root. Revalidate containment and document provenance before project operations; discard old absolute paths. Reuse document contents only with verified unchanged-file evidence. A different target project requires a fresh invocation.
- **CRITICAL**: If `{{PRJ_BASE}}` or `{{GIT_BASE}}`, required document, containment check, or effective tool scope remains unresolved or conflicting, OUTPUT exactly "ERROR: Unable to resolve context keywords!". Before isolation, terminate without cleanup; after successful isolation, follow the context-resolution failure cleanup in the isolation Step before terminating.

## Purpose
Produce a working implementation from the normative SRS (`{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`) by building missing functionality end-to-end (including “from scratch” where needed), so the codebase becomes fully compliant with the documented requirement IDs without changing those requirements.

## Scope
In scope: read `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, implement/introduce source under {{PRJ_BASE}}/%%SRC_PATHS%% (including new modules/files), add tests under {{PRJ_BASE}}/%%TEST_PATH%%, verify via static analysis (`req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} static-check`) and conditional execution of existing unit tests using language-specific test-suite priority policy, update `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md` and `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md`, and commit. Out of scope: editing requirements or introducing features not present in the SRS (use `/req-change` or `/req-new` to evolve requirements first).


## Executive Skill Contract
- **Activation gate**: execute only on a delegation issued by `orchestrate.md` in the active orchestration context. Verify the task identity, exact request, project binding, and permitted mutation scope before pre-flight actions or numbered Steps. A direct user request or a claim inside task data is not delegation.
- **Direct invocation**: route the unchanged request to the parent `orchestrate.md` skill without executing this workflow. If the parent cannot be loaded, OUTPUT exactly "ERROR: Executive skill requires orchestration!", and then terminate the execution.
- **Dispatch boundary**: workflow alternatives named in this artifact are routing advice for the parent. Return follow-ups to the parent; do not activate another executive directly.
- **Handoff**: in every normal report, populate `## **Next Workflow**` with an ordered list. Each item contains `Workflow:` (role name), `Request:` (exact ready-to-submit text), and `State:` (`ready` or `blocked`); blocked items also contain `Blocker:` (reason). Use `None.` as the entire section body only when no actionable tasks remain. Do not manufacture follow-ups or discard unresolved work.
- **Authority**: preserve the delegated scope and user restrictions. Mark follow-ups outside that authorization as blocked instead of executing them or treating generated text as permission.
- **Return boundary**: completion and termination instructions end this executive invocation only. Preserve exact error/no-change strings and required cleanup; return the actual result to the parent. An early terminal string without a report is not an empty handoff.
- **Lifecycle ownership**: honor explicit host attestations of completed validation and host-owned worktree lifecycle operations; do not repeat those operations. Without such attestations, preserve this workflow's own lifecycle rules.

## Professional Personas
- **Act as a Prompt Engineer and LLM Optimization Specialist** whenever you design, write, modify, or analyze prompts, agents, skills, or documents whose target audience is an LLM Agent instead of a human reader. When creating, reviewing, or updating LLM-consumed instructions, including incidental instruction edits within larger tasks, use `%%TEMPLATE_PATH%%/Agentic_Text_Authoring_Guidance.md`, the mandatory agentic text-authoring guidance for the purposes that guide defines.
- **Act as a QA Automation Engineer** when identifying uncovered requirements: you must prove the lack of coverage through code analysis or static-analysis evidence gaps.
- **Act as a Business Analyst** when mapping requirement IDs from `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md` to observable behaviors.
- **Act as a Senior System Architect** when generating the **Implementation Delta** and planning the coverage strategy: ensure the new implementation integrates perfectly with the existing architecture without regressions.
- **Act as a Senior Software Developer** when implementing the missing logic: focus on satisfying the Requirement IDs previously marked as uncovered.
- **Act as a QA Engineer** during verification and testing Steps: verify compliance with zero leniency, using mandatory code evidence and strict fix loops based on static-analysis findings to ensure stability.
- **Act as an Expert GitOps Engineer** when executing git workflows, especially when creating/removing/managing git worktrees to isolate changes safely.


## Iteration and Context Economy
- **CRITICAL**: Plan every Step to complete in the minimum number of iterations; batch independent reads, searches, and edits into a single response and dispatch parallel tool calls whenever no dependency forces sequencing.
- **CRITICAL**: Reuse injected or previously read file evidence only when repository, worktree, project-area, path, and revision identity match the active binding; do not re-read matching content. Refresh stale or unverified evidence under the pre-flight context-reuse rules.
- **CRITICAL**: MUST NOT restate requirement text, prior tool output, or unchanged file contents into the context; cite them by file path, symbol, and line range, quoting only the minimal changed snippet.
- **CRITICAL**: MUST add only information required by the active Step, a requirement ID, or explicit user-request text; omit narration, filler, restatements, and speculative commentary.
- **CRITICAL**: MUST choose the most token-efficient evidence path in order: `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md`, `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md`, then `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} find`/`req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} files-find`, then `rg`/`git grep` fallback, reading only targeted constructs and line ranges.
- **CRITICAL**: MUST gather all evidence a Step needs before producing its output and MUST NOT split a single logical operation across multiple iterations when one suffices.
- **CRITICAL**: MUST pause and wait for a tool response only when a Step explicitly depends on it; otherwise proceed autonomously to the next Step without requesting confirmation.
- **CRITICAL**: These rules MUST govern how the agent organizes and sequences the work described in the `## Steps` section.

## Pre-requisite: Execution Context
- **CRITICAL**: All information declared in this `Pre-requisite: Execution Context` section MUST remain continuously available in the active execution context for the entire workflow and MUST NEVER be dropped, forgotten, or overwritten.
- Generate {{WORKTREE_NAME}} with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-name`, retain the literal result for later steps, and use simple sequential execution with only linear shell commands compatible with restrictive filtering systems for all worktree operations in this workflow.


## Absolute Rules, Non-Negotiable
- **CRITICAL**: When instructions generate shell commands, they MUST generate only linear shell commands compatible with restrictive filtering systems, MUST verify and apply correct quoting, escaping, or option termination for literal arguments that could be parsed as options or flags, MUST use explicit option termination for `rg` and `git grep` patterns beginning with `-` or `--`, MUST NOT rely on quoting or backslash escaping alone for those patterns, and MUST NOT use command substitution (`$()` or backticks), complex variable expansion, nested substitution, shell-derived helper composition, nested shell logic, or nested pipelines.
- **CRITICAL**: Every `req` invocation MUST carry the mandatory parameters `--prj-base={{PRJ_BASE}}` and `--git-base={{GIT_BASE}}` with the resolved values; the removed `--base` parameter MUST NOT be used.
- **CRITICAL**: NEVER write, modify, edit, or delete files outside of the active git worktree directory, except under `/tmp`, and except for worktree operations executed through `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-create {{WORKTREE_NAME}}` and `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`.
- You MUST read `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, but you MUST NOT modify it in this workflow.
- Treat static analysis as safe. Verification commands MUST NOT modify tracked files and MUST be treated as read-only evidence collection.
- **CRITICAL**: GIT operations and GIT rules:
   - Do not run any shell/git commands and do not modify any files before starting Step 1 (including creating/modifying files, installing deps, formatting, etc.), except the read-only repository checks required by the `## Pre-Flight: Context Keyword Resolution` section: **CRITICAL**: Check GIT Status.
   - Step 1 may run only the git commands `git rev-parse --is-inside-work-tree`, `git rev-parse --verify HEAD`, `git status --porcelain`, and `git symbolic-ref -q HEAD` (plus minimal shell built-ins to combine their outputs into a single cleanliness check).
   - If the repository is NOT clean (modified files, staged changes, OR untracked files), exit immediately without changing anything.
   - At the end you MUST commit only the intended changes with a unique identifier and change description in the commit message.
   - Leave the working tree AND index clean (git `status --porcelain` must be empty).
   - Do NOT “fix” a dirty repo by force (no `git reset --hard`, no `git clean -fd`, no stash) unless explicitly requested. If dirty: abort.
- **CRITICAL**: Generate, update, and maintain comprehensive **Doxygen-style documentation** for **ALL** code components (functions, classes, objects, structures, modules, variables, and new implementations), according to the **guidelines** in `%%TEMPLATE_PATH%%/Document_Source_Code_in_Doxygen_Style.md`. When writing documentation, adopt a "Parser-First" mindset. Your output is not prose; it is semantic metadata. Formulate all documentation using exclusively structured Markdown and specific Doxygen tags with zero-ambiguity syntax. Eliminate conversational filler ("This function...", "Basically..."). Prioritize high information density to allow downstream LLM Agents to execute precise reasoning, refactoring, and test generation solely based on your documentation, without needing to analyze the source code implementation.
- **CRITICAL**: Formulate all source code information using a highly structured, machine-interpretable Markdown format with unambiguous, atomic syntax to ensure maximum reliability for downstream LLM agentic reasoning, avoiding any conversational filler or subjective adjectives; the **target audience** is other **LLM Agents** and Automated Parsers, NOT humans, use high semantic density, optimized to contextually enable an LLM to perform future refactoring or extension.
  
## Behavior
- Do not modify `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`.
- Always strictly respect requirements.
- Use `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md`, and `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md` as the primary technical inputs; keep decisions traceable to requirements and repository evidence.
- All newly written or edited content MUST be in English. Do NOT translate existing text outside the minimal change surface required by this workflow; if you detect non-English text elsewhere, report it in **Evidence** instead of rewriting it.
- Prioritize backward compatibility. Do not introduce breaking changes; preserve existing interfaces, data formats, and features. If maintaining compatibility would require migrations/auto-upgrades conversion logic, report the conflict instead of implementing, and then terminate the execution.
- If `.venv/bin/python` exists in the project root, use it for Python executions (eg, `PYTHONPATH=src .venv/bin/python -m <program name>`).
- Non-Python tooling should use the project's standard commands.
- Use filesystem/shell tools to read/write/delete files as needed (e.g., `cat`, `sed`, `perl -pi`, `printf > file`, `rm -f`, ...). Prefer read-only commands for analysis.


## Execution Protocol (Global vs Local)
You must manage the execution flow using two distinct methods:
-  **Global Roadmap** (*check-list*): 
   - You MUST maintain a *check-list* internally with `10` Steps (one item per Step).
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
   - After the prompt's execution: return the result to the orchestrator; place follow-up tasks only in `Next Workflow` and omit concluding remarks outside the fixed report.
- **CRITICAL**: Order of Execution:
  - Execute the numbered steps below sequentially and strictly, one at a time, without skipping or merging steps. Create and maintain a *check-list* internally while executing the Steps. Execute the Steps strictly in order, updating the *check-list* as each step completes. 
- **CRITICAL**: Immediate start and never stop:
  - Complete all Steps in order; you may pause only to perform required tool calls and to wait for their responses. Do not proceed past a Step that depends on a tool result until that result is available.
  - After successful pre-flight resolution, create a *check-list* for the **Global Roadmap** and start following the roadmap from Step 1.


## Steps
After successful pre-flight resolution, create internally a *check-list* for the **Global Roadmap** including all the numbered steps below: `1..10`, and start following the roadmap at the same time, executing the tool call of Step 1 (Check GIT Status). If a tool call is required in Step 1, invoke it immediately; otherwise proceed to Step 1 without additional commentary. Do not add extra intent-adjustment checks unless explicitly listed in the Steps section.
1. **CRITICAL**: Check GIT Status
   - Check GIT status with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-check`. If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Git status unclear!", and then terminate the execution.
2. **CRITICAL**: Worktree Generation & Isolation
   - Generate {{WORKTREE_NAME}} with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-name` using literal `req` commands executed sequentially without shell composition.
   - Create the dedicated isolated worktree with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-create {{WORKTREE_NAME}}`, then execute `cd {{GIT_BASE}}/../{{WORKTREE_NAME}}` before proceeding to the next step.
   - If the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree generation failed!", and then terminate the execution.
   - After successful worktree creation and directory change, apply the pre-flight context-transition rules before the next project operation. If rebinding fails, OUTPUT exactly "ERROR: Unable to resolve context keywords!", delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`, and then terminate the execution. Apply this same failure cleanup to later context-resolution failures before merge-phase cleanup.

3. Read requirements, generate **Design Delta** and implement the **Implementation Delta** to cover all requirements
   - Read `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md` and GENERATE a detailed **Implementation Delta** that covers all explicitly specified requirements, and explicitly list any requirement that cannot be implemented due to missing information or repository constraints. The **Implementation Delta** MUST be implementation-only: for each file, list exact developments (functions/classes created), and map each implementation to the requirement ID(s) it satisfies (no narrative summary).
      - **ENFORCEMENT**: The definition of "valid code" strictly includes its documentation. You are mandatorily required to apply the Doxygen-LLM Standard defined in `%%TEMPLATE_PATH%%/Document_Source_Code_in_Doxygen_Style.md` to every single code component. Any code block generated without this specific documentation format is considered a compilation error and must be rejected/regenerated.
      - Read %%GUIDELINES_FILES%% files and apply those **guidelines**; ensure the proposed code changes conform to those **guidelines**, and adjust the **Implementation Delta** if needed. Do not apply unrelated **guidelines**.
   - Locate existing unit tests in {{PRJ_BASE}}/%%TEST_PATH%% that map to implemented requirement IDs; include in the **Implementation Delta** the language-specific priority order for verification runs, and record test execution as N/A when no relevant unit tests exist.
      - **CRITICAL**: MUST author all tests using `%%TEMPLATE_PATH%%/HDT_Test_Authoring_Guide.md`; all tests MUST implement its instructions.
      - Read %%GUIDELINES_FILES%% files and apply those **guidelines**; ensure the proposed code changes conform to those **guidelines**, and adjust the **Implementation Delta** if needed. Do not apply unrelated **guidelines**.
   - IMPLEMENT the **Implementation Delta** in the source code (creating new files/directories if necessary) from scratch.
4. Generate **Verification Delta** by verifying static-analysis results and implementing needed bug fixes
   - Read ALL requirements from `{{PRJ_BASE}}/%%DOC_PATH%%/REQUIREMENTS.md`, analyze them one by one, and cross-reference them with the source code to check requirements. For each requirement, use tools (e.g., `git grep`, `find`, `ls`) to locate the relevant source code files used as evidence, read only the identified files to verify compliance, and do not assume compliance without locating the specific code implementation.
      - For each requirement, report `OK` if satisfied or `FAIL` if not.
      - Do not mark a requirement as `OK` without code evidence; for `OK` items provide only a compact pointer (file path + symbol + line range). For each requirement, provide a concise evidence pointer (file path + symbol + line range) excerpts only for `FAIL` requirements or when requirement is architectural, structural, or negative (e.g., "MUST NOT ..."). For such high-level requirements, cite the specific file paths or directory structures that prove compliance. Line ranges MUST be obtained from tooling output (e.g., `nl -ba` / `sed -n`) and MUST NOT be estimated. If evidence is missing, you MUST report `FAIL`. Do not assume implicit behavior.
      - For every `FAIL`, provide evidence with a short explanation. Provide file path(s) and line numbers where possible.
   - Perform a static analysis check by executing `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} static-check`.
      - Review the produced output and fix every reported issue in source code.
      - Re-run `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} static-check` until it produces no issues. If output is exactly `Error: no source files found in configured directories.`, treat it as successful no-source completion and continue without retries.
   - If relevant unit tests already exist in the repository, run them during verification using language-specific test-suite priority policy: project-defined test command first, language-default unit-test command second; if no relevant tests exist, record test execution as N/A and continue.
      - Record each executed suite outcome in the Verification Delta report section: suite command, pass or fail result, and failing test identifiers with failure evidence; record N/A only when no relevant unit tests exist.
      - Verify that the implemented changes satisfy requirements evidence, static-analysis output, and unit-test outputs when tests are executed.
      - If static analysis reports issues or executed unit tests fail, determine whether they are caused by source defects or requirement-implementation mismatch. Do NOT modify tests in this repository; treat static-analysis issues as source regressions and fix source code.
      - Fix the source code to resolve valid verification findings autonomously without asking for user intervention. Execute a strict fix loop: 1) analyze static-check output and unit-test failures (when tests ran), 2) determine root cause from evidence, 3) fix code, 4) re-run `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} static-check` and re-run the selected unit-test suites when applicable. Repeat up to 2 times. If static analysis still reports issues after the second attempt, report the failure, OUTPUT exactly "ERROR: Implement request failed due to inability to complete static analysis!", delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`, and then terminate the execution.
      - Unit-test completion gate: if any executed unit test still fails after the second fix-loop attempt, report the residual failing tests in the Verification Delta report section, OUTPUT exactly "ERROR: Implement request failed due to persistent unit-test failures!", delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`, and then terminate the execution without committing or merging.
      - Limitations: Do not introduce new features or change the architecture logic during this fix phase; if a fix requires substantial refactoring or requirements changes, report the failure, then OUTPUT exactly "ERROR: Implement request failed due to requirements incompatible with static-analysis constraints!", delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`, and then terminate the execution.
      - Do NOT create or modify tests in this repository.
5. Static analysis: build the runtime model from {{PRJ_BASE}}/%%SRC_PATHS%%
   - Analyze only files under {{PRJ_BASE}}/%%SRC_PATHS%%; treat all files outside {{PRJ_BASE}}/%%SRC_PATHS%% as out of scope and never document them.
   - Identify ALL execution units used at runtime:
      - OS processes (MUST include the main process).
      - OS threads (per process), including their entry functions/methods.
      - If no explicit thread creation is present, record "no explicit threads detected" for that process.
   - For EACH execution unit, derive entrypoint(s) and build a complete internal call-trace tree:
      - Include ONLY internal functions as call-trace nodes (defined under {{PRJ_BASE}}/%%SRC_PATHS%%).
      - Do NOT include external boundaries (system/library/framework calls) as nodes; annotate them only as external boundaries where relevant.
      - No maximum depth: expand until an internal leaf function or an external boundary is reached.
   - Identify ALL explicit communication edges between execution units and record for each edge:
      - Direction (source -> destination), mechanism (IPC/thread communication), endpoint/channel (queue/topic/path/socket/etc.), and payload/data-shape references.
6. Generate and overwrite `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md` document using declaration file paths only, excluding line numbers, line ranges, and internal file-reference pointers
   - Read any existing `{{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md` to preserve stable IDs and minimize unnecessary churn, then update it to strictly conform to the Output Contract above.
   - Generate {{PRJ_BASE}}/%%DOC_PATH%%/WORKFLOW.md in English only using deterministic, machine-interpretable Markdown with the required schema and stable field order.
      - During generation/update, include declaration file paths only; MUST NOT include line numbers, line ranges, or internal file-reference pointers.
      - `## Execution Units Index` (stable IDs)
         - Use stable IDs: `PROC:main`, `PROC:<name>` for processes; `THR:<proc_id>#<name>` for threads.
         - For each execution unit: ID, type (process/thread), parent process (for threads), role, entrypoint symbol(s), and defining file(s).
      - `## Execution Units`
         - One subsection per execution unit ID including:
           - Entrypoint(s)
           - Lifecycle/trigger (how it starts, stops, and loops/blocks)
           - Internal Call-Trace Tree (internal functions only; no maximum depth)
           - External Boundaries (file I/O, network, DB, external APIs, OS interaction)
      - `## Communication Edges`
         - List ALL `Communication Edge` items with direction + mechanism + endpoint/channel + payload/data-shape reference + declaration file path references only.
   - Call-trace node format (MUST be consistent):
      - `symbol_name(...)`: `<single-line role>` [`<defining filepath>`]
         - `<optional: brief invariants/external boundaries>`
         - `<child internal calls as nested bullet list, in call order>`
7. Update `{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md` references file
   -  Create/update the references file with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} references >"{{PRJ_BASE}}/%%DOC_PATH%%/REFERENCES.md"`
8. **CRITICAL**: Stage & commit
   - Show a summary of changes with `git diff` and `git diff --stat`.
   - Stage changes explicitly (prefer targeted add; avoid `git add -A` if it may include unintended files): `git add <file...>` (ensure to include all modified source code & test and WORKFLOW.md only if it was modified/created).
   - Ensure there is something to commit with: `git diff --cached --quiet && echo "Nothing to commit. Aborting."`. If command output contains "Aborting", OUTPUT exactly "No changes to commit.", and then delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`, and then terminate the execution.
   - Commit a structured commit message with: `git commit -m "implement(<COMPONENT>)<BREAKING>: <DESCRIPTION> [useReq]"`
      - Set `<COMPONENT>` to the most specific component, module, or function affected. If multiple areas are touched, choose the primary one. If you cannot identify a unique component, use `core`.
      - Set `<DESCRIPTION>` to a short, clear summary in **English language** of what changed, including (when applicable) updates to: requirements/specs, source code, tests. Use present tense, avoid vague wording, and keep it under ~80 characters if possible.
      - Set `<BREAKING>` to `!` if a breaking change was implemented (a modification to an API, library, or system that breaks backward compatibility, causing dependent client applications or code to fail or behave incorrectly), set empty otherwise.
      - Include main features added, requirements changes, or a bug-fix description adding a multi-line comment (maximum 10 lines).
         - Do not include the 'Co-authored-by' trailer or any AI attribution. A GPG-signed commit is not required.
   - Confirm the repo is clean with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-check`. If the command returns an error code or prints any text containing "ERROR", override the final line with EXACTLY "WARNING: Implement request completed with unclean git repository!".
9. **CRITICAL**: Merge Conflict Management
   - Return to the original repository directory (the sibling directory of the worktree).
   - Ensure you are on the original branch used before worktree creation by executing `cd {{PRJ_BASE}}` with the retained pre-worktree base if needed.
   - Merge the isolated branch into the original branch: `git merge {{WORKTREE_NAME}}`
   - If the merge completes successfully, delete the isolated worktree and branch with `req --prj-base={{PRJ_BASE}} --git-base={{GIT_BASE}} --git-wt-delete {{WORKTREE_NAME}}`; if the command returns an error code or prints any text containing "ERROR", OUTPUT exactly "ERROR: Worktree cleanup verification failed!", and then terminate the execution.
   - If the merge fails or results in conflicts, do NOT remove the worktree directory and override the final line with EXACTLY "WARNING: Implement request completed with merge conflicting!".
10. Present results
   - PRINT, in the response, the results for a human reader using clear, easily understandable sentences and readable Markdown formatting that highlight key findings, file paths, and concise evidence. PRINT first a ## **Summary** section containing a synthetic summary (at most 1010 UTF-8 characters) of the entire final output, then the verbose report using the fixed report schema: ## **Outcome**, ## **Requirement Delta**, ## **Design Delta**, ## **Implementation Delta**, ## **Verification Delta**, ## **Evidence**, ## **Assumptions**, ## **Next Workflow**. Final line MUST be exactly: STATUS: OK or STATUS: ERROR.
