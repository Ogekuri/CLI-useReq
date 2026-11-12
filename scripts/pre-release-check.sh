#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.75.4
# AUTHORS: Ogekuri
##
# @file scripts/pre-release-check.sh
# @brief Pre-release verification pipeline executing every quality gate required before an official release.
# @details Executes the following ordered stages from the repository root resolved from this
# script location (SRS-471):
# 1. `environment`: verify the `uv` command is executable (SRS-473).
# 2. `worktree-cleanliness`: abort when `git status --porcelain` reports any entry,
#    unless `--allow-dirty` was supplied (SRS-474).
# 3. `dependency-sync`: run `uv sync --frozen` against the canonical SRS-055 lockfile and
#    repair stale `.venv/bin/pytest` entry points that target foreign interpreters left
#    behind by a copied or relocated virtual environment (SRS-475, SRS-479).
# 4. `build`: create a script-owned temporary directory outside the repository `dist/`
#    directory, generate the sdist and wheel into it through the canonical frozen-lock
#    `uv run --frozen --with build python -m build --outdir <tmpdir>` command mirroring
#    `.github/workflows/release-pypi.yml` (SRS-476, SRS-574), then verify that at least one
#    `.tar.gz` and one `.whl` artifact exist inside that temporary directory (SRS-477).
# 5. `static-analysis`: run the project `static-check` command with `--prj-base` on the
#    repository root (SRS-478).
# 6. `unit-tests`: run the full unit-test suite through `uv run pytest` (SRS-479).
# 7. `cleanup` (EXIT trap): on every termination path remove the temporary build directory,
#    `build/`, `.pytest_cache/`, `.ruff_cache/`, `src/*.egg-info`, and `src/`- or
#    `tests/`-scoped `__pycache__` directories so the repository is left with only git-tracked
#    files, the uv-managed `.venv` environment, and the pre-existing `dist/` directory content
#    (SRS-482, SRS-484); cleanup targets containing git-tracked files are skipped with an
#    English warning (SRS-483).
# Execution stops at the first failing stage with the diagnostic
# `Pre-release check failed at stage <stage>.` and exit code 1; `Pre-release check passed.`
# is printed only when every stage succeeds (SRS-480). The script never modifies or deletes
# git-tracked repository files (SRS-481) and never creates, reads, deletes, modifies, or
# verifies any entry under the repository `dist/` directory, so its behavior is fully
# independent of the `dist/` content (SRS-556).
# @param[in] $1 Optional literal `--allow-dirty` flag skipping the `worktree-cleanliness` gate (SRS-472).
# @retval 0 Every stage succeeded and `Pre-release check passed.` was printed.
# @retval 1 A stage failed, `uv` is unavailable, or an unknown argument was supplied.
# @warning Requires `bash`, `git`, and the Astral `uv` tool; network access is required by the
#          build isolation and dependency resolution steps.
# @see scripts/req.sh
# @satisfies SRS-471, SRS-472, SRS-473, SRS-474, SRS-475, SRS-476, SRS-477, SRS-478, SRS-479, SRS-480, SRS-481, SRS-482, SRS-483, SRS-484, SRS-556, SRS-574
##

set -euo pipefail

##
# @brief Resolve the absolute repository root from this script filesystem location.
# @details Mirrors the resolution logic of `scripts/req.sh`: canonicalize `$0` through
# `readlink -f`, derive the script directory, and step one level up. All stages execute
# with this root so the caller working directory never influences behavior (SRS-471).
# @return Prints nothing; sets the global `BASE_DIR` variable to the absolute repository root.
# @satisfies SRS-471
FULL_PATH="$(readlink -f "$0")"
SCRIPT_PATH="$(dirname "$FULL_PATH")"
BASE_DIR="$(dirname "$SCRIPT_PATH")"

##
# @brief Default exit code for every pre-release-check failure path.
# @details Single constant shared by argument validation and stage failure handling so all
# failure exits stay uniform (SRS-472, SRS-480).
# @satisfies SRS-472, SRS-480
PRERELEASE_CHECK_ERROR_EXIT_CODE=1

##
# @brief Name of the currently executing stage used by failure diagnostics.
# @details Mutated by `run_stage` before each stage invocation and consumed by its failure
# branch to print the canonical `Pre-release check failed at stage <stage>.` message (SRS-480).
# @satisfies SRS-480
CURRENT_STAGE=""

##
# @brief Absolute path of the script-owned temporary build directory, or empty when unset.
# @details Initially empty so `set -u` never observes an unset global, assigned by
# `build_distribution_artifacts` through `mktemp -d`, and consumed by
# `cleanup_repository_artifacts` to remove the temporary artifacts on every termination path
# (SRS-476, SRS-482). The directory is always created outside the repository and therefore
# never resolves to `dist/` (SRS-556).
# @satisfies SRS-476, SRS-482
PRERELEASE_BUILD_TMP_DIR=""

##
# @brief Print the canonical first-failure diagnostic and terminate with exit code 1.
# @details Reads the global `CURRENT_STAGE` value, emits the English diagnostic on stderr,
# and exits the whole script (SRS-480).
# @return Does not return; terminates the process with exit code 1.
# @satisfies SRS-480
fail_current_stage() {
  echo "Pre-release check failed at stage ${CURRENT_STAGE}." >&2
  exit "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
}

##
# @brief Execute one pipeline stage and stop the script on its first failure.
# @details Assigns `CURRENT_STAGE` from the first argument, prints a progress line on stdout,
# then executes the remaining arguments as a command; any non-zero exit or shell error in the
# command triggers `fail_current_stage`, guaranteeing no subsequent stage runs (SRS-480).
# @param[in] $1 Stage identifier used in progress and failure diagnostics.
# @param[in] $2... Command and arguments composing the stage.
# @return Does not return when the stage fails; returns 0 after a successful stage.
# @satisfies SRS-480
run_stage() {
  CURRENT_STAGE="$1"
  shift
  printf '[pre-release-check] stage %s\n' "${CURRENT_STAGE}"
  if ! "$@"; then
    fail_current_stage
  fi
}

##
# @brief Validate command-line arguments and resolve the `--allow-dirty` flag.
# @details Accepts zero arguments or exactly one literal `--allow-dirty` argument (SRS-472);
# any other token produces an English error on stderr and exits with code 1 (SRS-472).
# Sets the global `ALLOW_DIRTY` flag consumed by the `worktree-cleanliness` stage (SRS-474).
# @param[in] $@ Raw script arguments.
# @return Sets global `ALLOW_DIRTY` to 1 when `--allow-dirty` is present, otherwise 0.
# @retval 0 Arguments are valid.
# @satisfies SRS-472, SRS-474
ALLOW_DIRTY=0
if [ "$#" -gt 1 ]; then
  echo "ERROR: too many arguments; only the optional --allow-dirty flag is accepted" >&2
  exit "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
fi
if [ "$#" -eq 1 ]; then
  if [ "$1" = "--allow-dirty" ]; then
    ALLOW_DIRTY=1
  else
    echo "ERROR: unknown argument '$1'; only the optional --allow-dirty flag is accepted" >&2
    exit "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
fi

##
# @brief Stage `environment`: verify that the `uv` command is executable (SRS-473).
# @details Emits an English error on stderr and aborts the pipeline when `uv` is absent,
# because every subsequent stage depends on uv-managed runtime environments (SRS-056).
# @return Does not return when `uv` is unavailable; returns 0 when available.
# @satisfies SRS-473
check_uv_available() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv command not found in PATH" >&2
    return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Stage `worktree-cleanliness`: verify the repository working tree has no git status entries.
# @details Executes `git status --porcelain` in the repository root; a non-empty output means
# pending modifications, staged changes, or untracked files, and aborts the release check
# (SRS-474). Skipped entirely when `--allow-dirty` was supplied (SRS-472, SRS-474).
# @return Returns 0 when the tree is clean or the gate is skipped; returns 1 otherwise.
# @satisfies SRS-472, SRS-474
check_worktree_clean() {
  if [ "${ALLOW_DIRTY}" -eq 1 ]; then
    return 0
  fi
  local porcelain_output
  porcelain_output="$(git -C "${BASE_DIR}" status --porcelain)"
  if [ -n "${porcelain_output}" ]; then
    echo "ERROR: git working tree is not clean; commit or stash changes, or pass --allow-dirty" >&2
    return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Determine whether a virtual-environment console script targets the project interpreter.
# @details Reads the first line of `script_path`; an absent file is classified as local
# because the subsequent `uv run` invocation surfaces the absence itself. The script is
# local exactly when its shebang interpreter path is anchored at `<BASE_DIR>/.venv/bin/`,
# so shebangs inherited from a copied or relocated virtual environment are classified as
# foreign regardless of whether the referenced interpreter still exists. Complexity O(1)
# per invocation; reads one file line and performs no writes.
# @param[in] $1 Absolute path of the console script to classify.
# @retval 0 The script is absent or its interpreter is inside the project virtual environment.
# @retval 1 The script shebang references an interpreter outside the project virtual environment.
# @satisfies SRS-475, SRS-479
venv_entry_point_targets_project() {
  local script_path="$1"
  [ -f "${script_path}" ] || return 0
  local shebang_line
  shebang_line="$(head -n 1 "${script_path}")"
  case "${shebang_line}" in
    "#!${BASE_DIR}/.venv/bin/"*) return 0 ;;
    *) return 1 ;;
  esac
}

##
# @brief Detect and repair a stale pytest entry point inside the project virtual environment.
# @details `uv sync --frozen` reuses packages whose dist-info is already present and never
# rewrites console-script shebangs inherited from a copied or relocated virtual environment;
# the SRS-479 `uv run pytest` invocation then executes pytest under a foreign interpreter and
# the unit-tests stage aborts with a misleading conftest `ModuleNotFoundError`. This guard
# verifies the `.venv/bin/pytest` shebang after synchronization, repairs it through
# `uv sync --frozen --reinstall-package pytest`, and fails the stage with actionable English
# guidance when the entry point still targets a foreign interpreter. Only `pytest` is guarded
# because every other pipeline stage spawns Python through module-form invocations that bypass
# console-script shebangs. Complexity O(1) plus one conditional uv subprocess on repair.
# @return Returns 0 when the pytest entry point targets the project virtual environment,
#   possibly after one repair reinstall.
# @retval 1 The entry point still targets a foreign interpreter after the repair attempt.
# @warning The repair rewrites the uv-managed `.venv` console script; no git-tracked file changes.
# @satisfies SRS-475, SRS-479, SRS-480
ensure_venv_pytest_entry_point_local() {
  local pytest_entry_point="${BASE_DIR}/.venv/bin/pytest"
  if venv_entry_point_targets_project "${pytest_entry_point}"; then
    return 0
  fi
  echo "WARNING: stale virtual environment entry point '${pytest_entry_point}' targets a foreign interpreter; reinstalling the pytest entry point" >&2
  uv sync --project "${BASE_DIR}" --frozen --reinstall-package pytest
  if venv_entry_point_targets_project "${pytest_entry_point}"; then
    return 0
  fi
  echo "ERROR: virtual environment entry point '${pytest_entry_point}' still targets a foreign interpreter; recreate the environment with 'rm -rf .venv && uv sync --frozen'" >&2
  return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
}

##
# @brief Stage `dependency-sync`: synchronize the frozen lockfile and guard entry points.
# @details Runs the canonical SRS-475 `uv sync --frozen` command against the SRS-055
# lockfile, propagates any synchronization failure status, and then enforces a
# project-local pytest entry point so the SRS-479 unit-tests stage cannot be hijacked
# by a stale virtual-environment copy. Stage failure propagates through `run_stage`
# for either a synchronization failure or an unrepairable entry point.
# @return Returns 0 when synchronization and entry-point verification both succeed.
# @retval 1 Synchronization failed or the pytest entry point stays foreign after repair.
# @satisfies SRS-475, SRS-479, SRS-480
sync_dependencies() {
  uv sync --project "${BASE_DIR}" --frozen || return $?
  ensure_venv_pytest_entry_point_local
}

##
# @brief Stage `build`: build the release artifacts in a temporary directory and verify them.
# @details Creates a fresh temporary directory outside the repository through
# `mktemp -d "${TMPDIR:-/tmp}/usereq-pre-release-build.XXXXXXXX"` so no artifact ever reaches
# the repository `dist/` directory (SRS-476, SRS-556), then runs the canonical frozen-lock
# `uv run --project <root> --frozen --with build python -m build --outdir <tmpdir>` command
# mirroring `.github/workflows/release-pypi.yml` (SRS-574). A failed directory creation or
# build is reported in English and returns the failure exit code instead of propagating a
# masked status, because `run_stage` invokes this function in a condition context. After a
# successful build the temporary directory is re-verified to contain at least one `.tar.gz`
# sdist and one `.whl` wheel (SRS-477). Complexity O(A) over the produced artifacts; side
# effects: creates one temporary directory and mutates `PRERELEASE_BUILD_TMP_DIR`.
# @return Returns 0 when both artifact families exist in the temporary directory; returns 1
#         on directory-creation failure, build failure, or missing artifacts.
# @see scripts/build.sh
# @satisfies SRS-476, SRS-477, SRS-481, SRS-556, SRS-574
build_distribution_artifacts() {
  local tmp_dir
  if ! tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/usereq-pre-release-build.XXXXXXXX")"; then
    echo "ERROR: cannot create the temporary build directory" >&2
    return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
  PRERELEASE_BUILD_TMP_DIR="${tmp_dir}"
  if ! uv run --project "${BASE_DIR}" --frozen --with build python -m build --outdir "${PRERELEASE_BUILD_TMP_DIR}"; then
    echo "ERROR: distribution build failed" >&2
    return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
  local sdist_count
  local wheel_count
  sdist_count="$(find "${PRERELEASE_BUILD_TMP_DIR}" -maxdepth 1 -name '*.tar.gz' | wc -l)"
  wheel_count="$(find "${PRERELEASE_BUILD_TMP_DIR}" -maxdepth 1 -name '*.whl' | wc -l)"
  if [ "${sdist_count}" -lt 1 ] || [ "${wheel_count}" -lt 1 ]; then
    echo "ERROR: build artifacts missing in the temporary build directory (expected at least one .tar.gz and one .whl)" >&2
    return "${PRERELEASE_CHECK_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Stage `static-analysis`: run the project static-check command on the repository root.
# @details Invokes `uv run python -m usereq.cli --prj-base <root> static-check` so the SRS-256
# project-scan static analysis executes with `fail_only` semantics and a non-zero exit code on
# any finding (SRS-478).
# @return Returns the static-check exit code (0 pass, 1 any failure).
# @satisfies SRS-478
run_static_analysis() {
  uv run --project "${BASE_DIR}" python -m usereq.cli --prj-base "${BASE_DIR}" static-check
}

##
# @brief Stage `unit-tests`: execute the full unit-test suite through the project test command.
# @details Runs `uv run pytest` from the repository root using the `[tool.pytest.ini_options]`
# test paths; a non-zero pytest exit code propagates and aborts the pipeline (SRS-479).
# @return Returns the pytest exit code (0 all passed, non-zero any failure).
# @satisfies SRS-479
run_unit_tests() {
  uv run --project "${BASE_DIR}" pytest
}

##
# @brief Remove every build and test intermediate artifact from the repository on any exit path.
# @details Registered as an `EXIT` trap so it executes on success, on stage failure, and on
# unexpected termination (SRS-482). Collects the fixed targets `build/`, `.pytest_cache/`, and
# `.ruff_cache/` plus every existing `*.egg-info` or `__pycache__` directory discovered by
# `find` under `src/` and `tests/`, and removes the SRS-476 temporary build directory when it
# was created. The repository `dist/` directory is never enumerated, removed, or otherwise
# touched, so cleanup is independent of its content (SRS-556). For each existing repository
# target, the git-tracked file check via `git ls-files` guards SRS-481: tracked targets are
# skipped with an English stderr warning identifying the path (SRS-483); untracked targets are
# removed with `rm -rf`. After this function returns, the repository directory contains only
# git-tracked files, the uv-managed `.venv` environment, and the pre-existing `dist/` content
# (SRS-484).
# @return {None} Function return value.
# @warning Must stay failure-tolerant: any error raised inside this EXIT trap would override
#          the original script exit status.
# @satisfies SRS-481, SRS-482, SRS-483, SRS-484, SRS-556
cleanup_repository_artifacts() {
  local cleanup_targets=(
    "${BASE_DIR}/build"
    "${BASE_DIR}/.pytest_cache" "${BASE_DIR}/.ruff_cache"
  )
  local target
  local relative_target
  local tracked_files
  while IFS= read -r found_dir; do
    cleanup_targets+=("${found_dir}")
  done < <(find "${BASE_DIR}/src" "${BASE_DIR}/tests" -maxdepth 4 -type d \( -name '*.egg-info' -o -name '__pycache__' \) 2>/dev/null || true)
  for target in "${cleanup_targets[@]}"; do
    [ -e "${target}" ] || continue
    relative_target="${target#"${BASE_DIR}/"}"
    tracked_files="$(git -C "${BASE_DIR}" ls-files -- "${relative_target}")"
    if [ -n "${tracked_files}" ]; then
      echo "WARNING: cleanup skipped for '${relative_target}' because it contains git-tracked files" >&2
      continue
    fi
    rm -rf -- "${target}"
  done
  if [ -n "${PRERELEASE_BUILD_TMP_DIR}" ] && [ -d "${PRERELEASE_BUILD_TMP_DIR}" ]; then
    rm -rf -- "${PRERELEASE_BUILD_TMP_DIR}" || true
  fi
}

trap cleanup_repository_artifacts EXIT

cd "${BASE_DIR}"

run_stage "environment" check_uv_available
run_stage "worktree-cleanliness" check_worktree_clean
run_stage "dependency-sync" sync_dependencies
run_stage "build" build_distribution_artifacts
run_stage "static-analysis" run_static_analysis
run_stage "unit-tests" run_unit_tests

echo "Pre-release check passed."
