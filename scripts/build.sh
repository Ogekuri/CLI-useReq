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
# 4. `artifact-verification`: verify that `dist/` contains at least one `.tar.gz` sdist
#    and one `.whl` wheel (SRS-550).
# 5. `summary`: print every artifact currently stored in `dist/` (SRS-551).
# Execution stops at the first failing stage with the diagnostic
# `Release build failed at stage <stage>.` and exit code 1; exit code 0 is returned only
# when every stage succeeds (SRS-551). On success the artifacts remain available in
# `dist/`; cleanup of generated artifacts is the responsibility of
# `scripts/pre-release-check.sh` (SRS-482), never of this script.
# @retval 0 Every stage succeeded and the artifacts are available in `dist/`.
# @retval 1 A stage failed, `uv` is unavailable, or an expected artifact is missing.
# @warning Requires `bash`, `git`, and the Astral `uv` tool; network access is required
#          by the build isolation and dependency resolution steps.
# @see scripts/pre-release-check.sh
# @satisfies SRS-546, SRS-547, SRS-548, SRS-549, SRS-550, SRS-551
##

set -euo pipefail

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
# @brief Default exit code for every release build failure path.
# @details Single constant shared by stage failure handling so all failure exits stay
# uniform (SRS-551).
# @satisfies SRS-551
BUILD_ERROR_EXIT_CODE=1

##
# @brief Name of the currently executing stage used by failure diagnostics.
# @details Mutated by `run_stage` before each stage invocation and consumed by its
# failure branch to print the canonical `Release build failed at stage <stage>.`
# message (SRS-551).
# @satisfies SRS-551
CURRENT_STAGE=""

##
# @brief Print the canonical first-failure diagnostic and terminate with exit code 1.
# @details Reads the global `CURRENT_STAGE` value, emits the English diagnostic on
# stderr, and exits the whole script (SRS-551).
# @return Does not return; terminates the process with exit code 1.
# @satisfies SRS-551
fail_current_stage() {
  echo "Release build failed at stage ${CURRENT_STAGE}." >&2
  exit "${BUILD_ERROR_EXIT_CODE}"
}

##
# @brief Execute one build stage and stop the script on its first failure.
# @details Assigns `CURRENT_STAGE` from the first argument, prints a progress line on
# stdout, then executes the remaining arguments as a command; any non-zero exit or
# shell error in the command triggers `fail_current_stage`, guaranteeing no subsequent
# stage runs (SRS-551).
# @param[in] $1 Stage identifier used in progress and failure diagnostics.
# @param[in] $2... Command and arguments composing the stage.
# @return Does not return when the stage fails; returns 0 after a successful stage.
# @satisfies SRS-551
run_stage() {
  CURRENT_STAGE="$1"
  shift
  printf '[build] stage %s\n' "${CURRENT_STAGE}"
  if ! "$@"; then
    fail_current_stage
  fi
}

##
# @brief Stage `environment`: verify that the `uv` command is executable (SRS-547).
# @details Emits an English error on stderr and aborts the build when `uv` is absent,
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
# @details Iterates the direct children of `dist/` and removes an entry only when
# `git check-ignore -q` classifies it as gitignored, which by definition covers the
# generated artifacts of previous builds (SRS-553); git-tracked files are never reported
# by `git check-ignore` and untracked non-ignored files are preserved, so both survive
# the pruning (SRS-548). An absent `dist/` directory is a no-op, making the stage
# idempotent for first builds. Complexity O(N) over the direct children of `dist/`.
# @return Returns 0 after pruning or when `dist/` is absent.
# @satisfies SRS-548
clean_stale_dist_artifacts() {
  [ -d "${BASE_DIR}/dist" ] || return 0
  local entry
  local relative_entry
  while IFS= read -r entry; do
    relative_entry="${entry#"${BASE_DIR}/"}"
    if git -C "${BASE_DIR}" check-ignore -q -- "${relative_entry}"; then
      rm -rf -- "${entry}"
    fi
  done < <(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print)
}

##
# @brief Stage `compile`: produce the release sdist and wheel into dist/.
# @details Executes the canonical frozen-lock build command mirroring
# `.github/workflows/release-pypi.yml` (SRS-549); the build tool writes both artifact
# families into `dist/`. A non-zero build exit status propagates through `run_stage`.
# @return Returns the build exit status (0 success, non-zero failure).
# @satisfies SRS-549
compile_distribution_artifacts() {
  uv run --project "${BASE_DIR}" --frozen --with build python -m build --outdir "${BASE_DIR}/dist"
}

##
# @brief Stage `artifact-verification`: verify the expected artifact families exist.
# @details Counts the `.tar.gz` sdists and `.whl` wheels directly stored in `dist/`
# and fails when either family is missing, so a failed or incomplete build is never
# presented as successful (SRS-550).
# @return Returns 0 when at least one sdist and one wheel exist; returns 1 otherwise.
# @satisfies SRS-550
verify_distribution_artifacts() {
  local sdist_count
  local wheel_count
  sdist_count="$(find "${BASE_DIR}/dist" -maxdepth 1 -name '*.tar.gz' | wc -l)"
  wheel_count="$(find "${BASE_DIR}/dist" -maxdepth 1 -name '*.whl' | wc -l)"
  if [ "${sdist_count}" -lt 1 ] || [ "${wheel_count}" -lt 1 ]; then
    echo "ERROR: build artifacts missing in dist/ (expected at least one .tar.gz and one .whl)" >&2
    return "${BUILD_ERROR_EXIT_CODE}"
  fi
}

##
# @brief Stage `summary`: print every artifact currently stored in dist/.
# @details Lists the direct children of `dist/` in lexicographic order so the caller can
# record exactly which distributable artifacts the build produced (SRS-551).
# @return Returns 0 after printing the summary.
# @satisfies SRS-551
print_artifact_summary() {
  local entry
  printf '[build] artifacts in dist/:\n'
  while IFS= read -r entry; do
    printf '  %s\n' "${entry#"${BASE_DIR}/dist/"}"
  done < <(find "${BASE_DIR}/dist" -mindepth 1 -maxdepth 1 -print | sort)
}

cd "${BASE_DIR}"

run_stage "environment" check_uv_available
run_stage "dist-preparation" clean_stale_dist_artifacts
run_stage "compile" compile_distribution_artifacts
run_stage "artifact-verification" verify_distribution_artifacts
run_stage "summary" print_artifact_summary
