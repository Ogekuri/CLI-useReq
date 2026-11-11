#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# VERSION: 0.75.3
# AUTHORS: Ogekuri
##
# @file scripts/build.sh
# @brief Reproducible release build producing every distributable artifact into dist/.
# @details Executes the following ordered stages from the repository root resolved from
# this script location (SRS-546):
# 1. `environment`: verify the `uv` command is executable (SRS-547).
# 2. `dist-preparation`: remove from `dist/` only gitignored entries left by previous
#    builds, preserving every git-tracked or non-ignored file (SRS-548).
# 3. `compile`: build the sdist and wheel into `dist/` through the canonical frozen-lock
#    command `uv run --project <root> --frozen --with build python -m build --outdir
#    <root>/dist`, mirroring `.github/workflows/release-pypi.yml` (SRS-549).
# 4. `intermediate-cleanup`: remove the setuptools `src/*.egg-info` build intermediates
#    only when they are gitignored and untracked (SRS-548).
# 5. `artifact-verification`: verify that `dist/` contains at least one `.tar.gz` sdist
#    and one `.whl` wheel (SRS-550).
# 6. `summary`: print every artifact currently stored in `dist/` (SRS-551).
# Every stage runs unconditionally under `set -e`, so the first failing command aborts
# the script; the EXIT trap then prints `Release build failed at stage <stage>.` and exits
# with code 1. Exit code 0 is returned only when every stage succeeds (SRS-551). On success
# the artifacts remain available in `dist/`; cleanup of the remaining build and test
# intermediates is the responsibility of `scripts/pre-release-check.sh` (SRS-482).
# @retval 0 Every stage succeeded and the artifacts are available in `dist/`.
# @retval 1 A stage failed, `uv` is unavailable, or an expected artifact is missing.
# @warning Requires `bash`, `git`, and the Astral `uv` tool; network access is required
#          by the build isolation and dependency resolution steps.
# @see scripts/pre-release-check.sh
# @satisfies SRS-546, SRS-547, SRS-548, SRS-549, SRS-550, SRS-551
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
# @brief Stage `dist-preparation`: remove only gitignored entries from a previous dist/.
# @details Enumerates the direct children of `dist/` into a variable through command
# substitution so a failing `find` terminates the stage under `set -e` instead of being
# silently discarded by a process substitution. Each entry is removed only when
# `git check-ignore -q` classifies it as gitignored, which covers the generated artifacts of
# previous builds (SRS-553). Git-tracked files are never reported as ignored and untracked
# non-ignored files are preserved, so both survive the pruning (SRS-548). A failing `rm`
# inside the loop aborts the stage under `set -e`. An absent `dist/` directory is a no-op,
# making the stage idempotent for first builds. Complexity O(N) over the direct children of
# `dist/`; side effects: deletes gitignored entries under `dist/`.
# @return Returns 0 after pruning or when `dist/` is absent; non-zero when a removal fails.
# @satisfies SRS-548
clean_stale_dist_artifacts() {
  [ -d "${BASE_DIR}/dist" ] || return 0
  local entries
  local entry
  local relative_entry
  entries="$(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print)"
  if [ -z "${entries}" ]; then
    return 0
  fi
  while IFS= read -r entry; do
    relative_entry="${entry#"${BASE_DIR}/"}"
    if git -C "${BASE_DIR}" check-ignore -q -- "${relative_entry}"; then
      rm -rf -- "${entry}"
    fi
  done <<< "${entries}"
}

##
# @brief Stage `compile`: produce the release sdist and wheel into dist/.
# @details Executes the canonical frozen-lock build command mirroring
# `.github/workflows/release-pypi.yml` (SRS-549); the build tool writes both artifact
# families into `dist/`. A non-zero build exit status terminates the script through `set -e`.
# @return Returns the build exit status (0 success, non-zero failure).
# @satisfies SRS-549
compile_distribution_artifacts() {
  uv run --project "${BASE_DIR}" --frozen --with build python -m build --outdir "${BASE_DIR}/dist"
}

##
# @brief Stage `intermediate-cleanup`: remove generated egg-info directories that are disposable.
# @details Enumerates the `src/*.egg-info` directories produced by the setuptools build into a
# variable through command substitution. A directory is removed only when `git check-ignore -q`
# classifies it as gitignored AND `git ls-files` reports no tracked entry beneath it, so
# git-tracked metadata and any non-ignored content are preserved (SRS-548). An absent match
# set is a no-op. Complexity O(K) over K egg-info directories; side effects: deletes untracked
# gitignored egg-info directories under `src/`.
# @return Returns 0 after pruning or when no candidate exists; non-zero when a removal fails.
# @satisfies SRS-548
clean_build_intermediates() {
  [ -d "${BASE_DIR}/src" ] || return 0
  local egg_dirs
  local egg_dir
  local relative_dir
  egg_dirs="$(find "${BASE_DIR}/src" -mindepth 1 -maxdepth 1 -type d -name '*.egg-info' -print)"
  if [ -z "${egg_dirs}" ]; then
    return 0
  fi
  while IFS= read -r egg_dir; do
    relative_dir="${egg_dir#"${BASE_DIR}/"}"
    if git -C "${BASE_DIR}" check-ignore -q -- "${relative_dir}" \
      && [ -z "$(git -C "${BASE_DIR}" ls-files -- "${relative_dir}")" ]; then
      rm -rf -- "${egg_dir}"
    fi
  done <<< "${egg_dirs}"
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
# @brief Stage `summary`: print every artifact currently stored in dist/.
# @details Enumerates the direct children of `dist/` in lexicographic order into a variable
# through command substitution so a failing `find` or `sort` terminates the stage under
# `set -e`; lists each entry so the caller can record exactly which distributable artifacts
# the build produced (SRS-551). Complexity O(N log N) over the children of `dist/`.
# @return Returns 0 after printing the summary; non-zero when enumeration fails.
# @satisfies SRS-551
print_artifact_summary() {
  local entries
  local entry
  entries="$(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print | sort)"
  printf '[build] artifacts in dist/:\n'
  if [ -z "${entries}" ]; then
    return 0
  fi
  while IFS= read -r entry; do
    printf '  %s\n' "${entry#"${BASE_DIR}/dist/"}"
  done <<< "${entries}"
}

cd "${BASE_DIR}"

run_stage "environment" check_uv_available
run_stage "dist-preparation" clean_stale_dist_artifacts
run_stage "compile" compile_distribution_artifacts
run_stage "intermediate-cleanup" clean_build_intermediates
run_stage "artifact-verification" verify_distribution_artifacts
run_stage "summary" print_artifact_summary
