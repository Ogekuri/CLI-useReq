#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.75.3
# AUTHORS: Ogekuri
##
# @file scripts/build.sh
# @brief Reproducible clean release build producing every distributable artifact into dist/.
# @details Executes the following ordered stages from the repository root resolved from
# this script location (SRS-546):
# 1. `environment`: verify the `uv` and `git` commands are executable (SRS-547, SRS-566).
# 2. `dist-preparation`: at bootstrap, before the compile stage, remove from `dist/` every
#    entry that is not git-tracked, covering every artifact version left by previous builds,
#    remove the `dist/` directory when it becomes empty, and preserve every git-tracked file
#    under `dist/` (SRS-548, SRS-577).
# 3. `intermediate-preparation`: remove the `build/` directory and every `src/*.egg-info`
#    directory left by previous builds (SRS-567).
# 4. `compile`: build the sdist and wheel into `dist/` through the canonical frozen-lock
#    command `uv run --project <root> --frozen --with build python -m build --outdir
#    <root>/dist`, mirroring `.github/workflows/release-pypi.yml` (SRS-549).
# 5. `intermediate-cleanup`: remove the `build/` directory and every `src/*.egg-info`
#    directory created by the compile stage so the repository retains only git-tracked
#    files plus the built artifacts in `dist/` (SRS-569).
# 6. `artifact-verification`: verify that `dist/` contains at least one `.tar.gz` sdist
#    and one `.whl` wheel (SRS-550).
# 7. `summary`: print every artifact currently stored in `dist/` plus every removed and
#    every skipped cleanup path (SRS-551, SRS-570).
# Every removal target containing git-tracked files is preserved and reported with an
# English warning identifying the skipped path (SRS-568). Every stage runs unconditionally
# under `set -e`, so the first failing command aborts the script; the EXIT trap then prints
# `Release build failed at stage <stage>.` and exits with code 1. Exit code 0 is returned
# only when every stage succeeds (SRS-551).
# @retval 0 Every stage succeeded and the artifacts are available in `dist/`.
# @retval 1 A stage failed, `uv` or `git` is unavailable, or an expected artifact is missing.
# @warning Requires `bash`, `git`, and the Astral `uv` tool; network access is required
#          by the build isolation and dependency resolution steps.
# @see scripts/pre-release-check.sh
# @satisfies SRS-546, SRS-547, SRS-548, SRS-549, SRS-550, SRS-551, SRS-566, SRS-567, SRS-568, SRS-569, SRS-570, SRS-577
##

set -euo pipefail

##
# @brief Default exit code for every release build failure path.
# @details Single constant shared by the EXIT trap and stage failure paths so all failure
# exits stay uniform (SRS-551).
# @satisfies SRS-551
BUILD_ERROR_EXIT_CODE=1

##
# @brief Name of the currently executing stage used by failure diagnostics.
# @details Mutated by `run_stage` before each stage invocation and consumed by `on_exit`
# to print the canonical `Release build failed at stage <stage>.` message (SRS-551).
# @satisfies SRS-551
CURRENT_STAGE=""

##
# @brief Repository-relative paths removed during the current execution.
# @details Populated by `remove_untracked_target` and consumed by `print_build_summary`;
# declared before any stage runs so `set -u` never observes an unset array (SRS-570).
# @satisfies SRS-570
REMOVED_TARGETS=()

##
# @brief Repository-relative paths skipped because they contain git-tracked files.
# @details Populated by `remove_untracked_target` and consumed by `print_build_summary`;
# declared before any stage runs so `set -u` never observes an unset array (SRS-568,
# SRS-570).
# @satisfies SRS-568, SRS-570
SKIPPED_TARGETS=()

##
# @brief Terminate the build with the canonical stage-failure diagnostic on any failing exit.
# @details Installed as the EXIT trap. Reads the terminating status from `$?`; when the
# status is non-zero it prints `Release build failed at stage <stage>.` on stderr if a stage
# was running and exits with `BUILD_ERROR_EXIT_CODE`. A zero status returns without output,
# so the successful path keeps exit code 0 (SRS-551). Stage functions are invoked without any
# conditional wrapper (see `run_stage`), so `set -e` remains active inside every stage body
# and no failure is masked.
# @return Does not return on failure; returns 0 on successful termination.
# @note Complexity: O(1). Side effects: writes one diagnostic line to stderr on failure.
# @satisfies SRS-551
on_exit() {
  local status=$?
  if [ "${status}" -ne 0 ]; then
    if [ -n "${CURRENT_STAGE}" ]; then
      echo "Release build failed at stage ${CURRENT_STAGE}." >&2
    fi
    exit "${BUILD_ERROR_EXIT_CODE}"
  fi
}
trap on_exit EXIT

##
# @brief Resolve the absolute repository root from this script filesystem location.
# @details Mirrors the resolution logic of `scripts/pre-release-check.sh`: canonicalize
# `$0` through `readlink -f`, derive the script directory, and step one level up. All
# stages execute with this root so the caller working directory never influences
# behavior (SRS-546).
# @return Prints nothing; sets the global `BASE_DIR` variable to the absolute repository root.
# @satisfies SRS-546
FULL_PATH="$(readlink -f "$0")"
SCRIPT_PATH="$(dirname "$FULL_PATH")"
BASE_DIR="$(dirname "$SCRIPT_PATH")"

##
# @brief Execute one build stage under unconditional `set -e` semantics.
# @details Assigns `CURRENT_STAGE` from the first argument, prints a progress line on
# stdout, then executes the remaining arguments as a plain command. The command is never
# placed in an `if`, `||`, `&&`, or `!` context: Bash disables `set -e` for every command
# executed in those contexts, including nested function bodies, which would mask failures.
# A non-zero status therefore terminates the script immediately and `on_exit` reports the
# failing stage (SRS-551).
# @param[in] $1 Stage identifier used in progress and failure diagnostics.
# @param[in] $2... Command and arguments composing the stage.
# @return Returns the stage status when it is zero; otherwise terminates via `set -e`.
# @satisfies SRS-551
run_stage() {
  CURRENT_STAGE="$1"
  shift
  printf '[build] stage %s\n' "${CURRENT_STAGE}"
  "$@"
}

##
# @brief Stage `environment`: verify that the `uv` command is executable (SRS-547).
# @details Emits an English error on stderr and returns non-zero when `uv` is absent,
# because the compile stage depends on uv-managed runtime environments (SRS-056).
# @return Returns 0 when `uv` is available; returns 1 otherwise.
# @satisfies SRS-547
check_uv_available() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv command not found in PATH" >&2
    return "${BUILD_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Stage `environment`: verify that the `git` command is executable (SRS-566).
# @details Emits an English error on stderr and returns non-zero when `git` is absent,
# because every cleanup decision depends on `git ls-files` tracked-file classification
# (SRS-568).
# @return Returns 0 when `git` is available; returns 1 otherwise.
# @satisfies SRS-566
check_git_available() {
  if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git command not found in PATH" >&2
    return "${BUILD_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Remove one cleanup target unless it contains git-tracked files.
# @details An absent target is a no-op, keeping every stage idempotent. The target is
# classified through `git ls-files`: when any tracked entry exists beneath it, the target
# is preserved, an English warning identifying the repository-relative path is printed on
# stderr, and the path is recorded in `SKIPPED_TARGETS` (SRS-568); otherwise the target is
# deleted with `rm -rf` and recorded in `REMOVED_TARGETS` (SRS-570). Complexity O(T) over
# the tracked entries beneath the target; side effects: deletes untracked filesystem
# entries, mutates the summary arrays.
# @param[in] $1 Absolute path of the cleanup target inside the repository.
# @return Returns 0 after removal, preservation, or no-op; non-zero when a removal fails.
# @satisfies SRS-568, SRS-570
remove_untracked_target() {
  local target="$1"
  [ -e "${target}" ] || return 0
  local relative_target="${target#"${BASE_DIR}/"}"
  local tracked_files
  tracked_files="$(git -C "${BASE_DIR}" ls-files -- "${relative_target}")"
  if [ -n "${tracked_files}" ]; then
    echo "WARNING: cleanup skipped for '${relative_target}' because it contains git-tracked files" >&2
    SKIPPED_TARGETS+=("${relative_target}")
    return 0
  fi
  rm -rf -- "${target}"
  REMOVED_TARGETS+=("${relative_target}")
}

##
# @brief Stage `dist-preparation`: remove every non-git-tracked entry from dist/ as bootstrap.
# @details Executes at bootstrap, before the compile stage, enumerates the direct children of
# `dist/` into a variable through command substitution so a failing `find` terminates the stage
# under `set -e` instead of being silently discarded by a process substitution. Every entry is
# delegated to `remove_untracked_target`, so all previously built artifact versions are deleted
# while git-tracked content is preserved with a warning (SRS-548, SRS-568, SRS-577). After the
# loop, `rmdir` removes the `dist/` directory itself only when it is empty; a non-empty
# survivor (git-tracked entries) is tolerated. An absent `dist/` directory is a no-op,
# making the stage idempotent for first builds. Complexity O(N) over the direct children
# of `dist/`; side effects: deletes untracked entries under `dist/`.
# @return Returns 0 after cleaning or when `dist/` is absent; non-zero when a removal fails.
# @satisfies SRS-548, SRS-568, SRS-577
clean_dist_artifacts() {
  [ -d "${BASE_DIR}/dist" ] || return 0
  local entries
  local entry
  entries="$(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print)"
  if [ -n "${entries}" ]; then
    while IFS= read -r entry; do
      remove_untracked_target "${entry}"
    done <<< "${entries}"
  fi
  rmdir "${BASE_DIR}/dist" 2>/dev/null || true
}

##
# @brief Remove the `build/` directory and every `src/*.egg-info` directory.
# @details Enumerates the `src/*.egg-info` directories produced by the setuptools metadata
# generation into a variable through command substitution so a failing `find` terminates
# the owning stage under `set -e`. The `build/` directory and every egg-info directory are
# delegated to `remove_untracked_target`, so targets containing git-tracked files are
# preserved with a warning (SRS-568) and everything else is deleted (SRS-570). The stage is
# idempotent: absent targets are a no-op. Complexity O(K) over K egg-info directories;
# side effects: deletes untracked build intermediates.
# @return Returns 0 after cleaning or when no candidate exists; non-zero when a removal fails.
# @satisfies SRS-567, SRS-568, SRS-569, SRS-570
clean_build_intermediates() {
  remove_untracked_target "${BASE_DIR}/build"
  [ -d "${BASE_DIR}/src" ] || return 0
  local egg_dirs
  local egg_dir
  egg_dirs="$(find "${BASE_DIR}/src" -mindepth 1 -maxdepth 1 -type d -name '*.egg-info' -print)"
  if [ -z "${egg_dirs}" ]; then
    return 0
  fi
  while IFS= read -r egg_dir; do
    remove_untracked_target "${egg_dir}"
  done <<< "${egg_dirs}"
}

##
# @brief Stage `compile`: produce the release sdist and wheel into dist/.
# @details Executes the canonical frozen-lock build command mirroring
# `.github/workflows/release-pypi.yml` (SRS-549); the build tool writes both artifact
# families into `dist/` and regenerates the `build/` and `src/*.egg-info` intermediates
# removed after the build (SRS-569). A non-zero build exit status terminates the script
# through `set -e`.
# @return Returns the build exit status (0 success, non-zero failure).
# @satisfies SRS-549, SRS-569
compile_distribution_artifacts() {
  uv run --project "${BASE_DIR}" --frozen --with build python -m build --outdir "${BASE_DIR}/dist"
}

##
# @brief Stage `artifact-verification`: verify the expected artifact families exist.
# @details Fails when `dist/` is absent. Otherwise counts the `.tar.gz` sdists and `.whl`
# wheels directly stored in `dist/` and fails when either family is missing, so a failed or
# incomplete build is never presented as successful (SRS-550).
# @return Returns 0 when at least one sdist and one wheel exist; returns 1 otherwise.
# @satisfies SRS-550
verify_distribution_artifacts() {
  local sdist_count
  local wheel_count
  if [ ! -d "${BASE_DIR}/dist" ]; then
    echo "ERROR: build artifacts missing in dist/ (directory absent)" >&2
    return "${BUILD_ERROR_EXIT_CODE}"
  fi
  sdist_count="$(find "${BASE_DIR}/dist" -maxdepth 1 -name '*.tar.gz' | wc -l)"
  wheel_count="$(find "${BASE_DIR}/dist" -maxdepth 1 -name '*.whl' | wc -l)"
  if [ "${sdist_count}" -lt 1 ] || [ "${wheel_count}" -lt 1 ]; then
    echo "ERROR: build artifacts missing in dist/ (expected at least one .tar.gz and one .whl)" >&2
    return "${BUILD_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Stage `summary`: print the artifact inventory and the cleanup report.
# @details Enumerates the direct children of `dist/` in lexicographic order into a variable
# through command substitution so a failing `find` or `sort` terminates the stage under
# `set -e`; lists each artifact so the caller can record exactly which distributable
# artifacts the build produced (SRS-551). Then prints the `REMOVED_TARGETS` and
# `SKIPPED_TARGETS` arrays accumulated by the cleanup stages as two labeled
# repository-relative path lists (SRS-570). Complexity O(N log N) over the children of
# `dist/`; side effects: stdout lines only.
# @return Returns 0 after printing the summary; non-zero when enumeration fails.
# @satisfies SRS-551, SRS-570
print_build_summary() {
  local entries
  local entry
  local target
  entries="$(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print | sort)"
  printf '[build] artifacts in dist/:\n'
  if [ -n "${entries}" ]; then
    while IFS= read -r entry; do
      printf '  %s\n' "${entry#"${BASE_DIR}/dist/"}"
    done <<< "${entries}"
  fi
  printf '[build] removed %d path(s):\n' "${#REMOVED_TARGETS[@]}"
  if [ "${#REMOVED_TARGETS[@]}" -gt 0 ]; then
    for target in "${REMOVED_TARGETS[@]}"; do
      printf '  %s\n' "${target}"
    done
  fi
  printf '[build] skipped %d git-tracked path(s):\n' "${#SKIPPED_TARGETS[@]}"
  if [ "${#SKIPPED_TARGETS[@]}" -gt 0 ]; then
    for target in "${SKIPPED_TARGETS[@]}"; do
      printf '  %s\n' "${target}"
    done
  fi
}

cd "${BASE_DIR}"

run_stage "environment" check_uv_available
run_stage "environment" check_git_available
run_stage "dist-preparation" clean_dist_artifacts
run_stage "intermediate-preparation" clean_build_intermediates
run_stage "compile" compile_distribution_artifacts
run_stage "intermediate-cleanup" clean_build_intermediates
run_stage "artifact-verification" verify_distribution_artifacts
run_stage "summary" print_build_summary
