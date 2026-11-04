#!/bin/bash
# -*- coding: utf-8 -*-
# VERSION: 0.68.0
# AUTHORS: Ogekuri
# @file test-install.sh
# @brief Rebuilds a disposable user-level installation with the repository
# smoke-test configuration.
# @details Resolves repository-relative paths, isolates HOME to a disposable
# directory, removes previously generated user-level provider directories
# from the disposable HOME, recreates the required project directory scaffold,
# and invokes `scripts/req.sh` with the canonical installation argument set.
# The provider list includes Pi prompts and Pi skills so `~/.pi/agent`
# resources are exercised during smoke installation.
# @satisfies SRS-366, SRS-367

# @brief Stores a timestamp string for ad hoc diagnostics.
# @details Retained for compatibility with the existing script layout. No
# downstream consumer reads this variable.
now=$(date '+%Y-%m-%d_%H-%M-%S')

# @brief Stores the canonical absolute path to the current script file.
# @details Resolves symbolic links so downstream path derivation is stable
# across direct and symlinked invocation modes.
FULL_PATH=$(readlink -f "$0")

# @brief Stores the directory that contains the current script file.
# @details Derived from `FULL_PATH`; used to locate `req.sh` without relying on
# the caller working directory.
SCRIPT_PATH=$(dirname "$FULL_PATH")

# @brief Stores the basename of the current script file.
# @details Retained for manual diagnostics and parity with the existing
# smoke-test script layout.
SCRIPT_NAME=$(basename "$FULL_PATH")

# @brief Stores the repository root directory inferred from the script
# location.
# @details Derived from the parent directory of `SCRIPT_PATH`; used as the
# default base for temporary installation targets.
BASE_DIR=$(dirname "$SCRIPT_PATH")

# --- Output tests (can be removed) ---
#echo "Full path:          $FULL_PATH"
#echo "Directory:          $SCRIPT_PATH"
#echo "Script name:        $SCRIPT_NAME"
#echo "Base Directory:     $BASE_DIR"

# @brief Stores the requested installation target path.
# @details Uses the first positional argument when it names an existing
# directory; otherwise the script falls back to a disposable target under
# `temp/test-install`.
FOLDER_PATH="${1:-}"
if ! [ -d "$FOLDER_PATH" ]; then
    # @brief Stores the fallback disposable installation target path.
    # @details Used by the clean-install path when the caller does not provide
    # an existing target directory.
    FOLDER_PATH="$BASE_DIR/temp/test-install"
    echo "Clean+Install on path: ${FOLDER_PATH}"
    rm -rf "${FOLDER_PATH}"
    mkdir -p "${FOLDER_PATH}"
else
    echo "Install on path: ${FOLDER_PATH}"
fi

# @brief Isolates HOME to a disposable directory for the smoke run.
# @details User-level provider artifacts and the global configuration file are
# written under this HOME so the developer environment is never modified.
# @satisfies SRS-367
SMOKE_HOME="$BASE_DIR/temp/test-install-home"
export HOME="$SMOKE_HOME"

# @brief Declares generated user-level provider directories deleted before reinstall.
# @details Enumerates provider output roots under the disposable HOME that are
# removed before the smoke-test installation runs. Pi prompt and skill roots
# are included to keep repeated executions deterministic.
# @satisfies SRS-367
delete_dirs=(
    ".antigravity/commands"
    ".antigravity/skills"
    ".claude/commands"
    ".claude/agents"
    ".claude/skills"
    ".codex/prompts"
    ".codex/skills"
    ".config/opencode/agent"
    ".config/opencode/command"
    ".config/opencode/skill"
    ".config/usereq"
    ".pi/agent/prompts"
    ".pi/agent/skills"
)

if [ ! -d "$FOLDER_PATH" ]; then
    echo "Path does not exist"
    exit 1
else
    echo "Remove old user-level dirs under disposable HOME."
    for del in "${delete_dirs[@]}"; do
        #echo Remove directory: "${HOME}/${del}"
        if [ -d "${HOME}/${del}" ]; then
            rm -rf "${HOME}/${del}"
        fi
    done

    # make dirs
    mkdir -p "${FOLDER_PATH}/guidelines"
    mkdir -p "${FOLDER_PATH}/docs"
    mkdir -p "${FOLDER_PATH}/tests"
    mkdir -p "${FOLDER_PATH}/src"

    # @brief Prints the exact smoke-test installation command line.
    # @details Mirrors the execution command for manual reproduction and keeps
    # the Pi provider visible in installation logs.
    echo "${SCRIPT_PATH}/req.sh" \
        --base "${FOLDER_PATH}" --docs-dir "${FOLDER_PATH}/docs" \
        --guidelines-dir "${FOLDER_PATH}/guidelines" \
        --src-dir "${FOLDER_PATH}/src" \
        --tests-dir "${FOLDER_PATH}/tests" \
        --upgrade-guidelines \
        --provider antigravity:prompts,skills \
        --provider claude:prompts,agents,skills \
        --provider codex:prompts,skills \
        --provider opencode:prompts,agents,skills \
        --provider "pi:prompts,skills" \
        --enable-static-check C=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c11 \
        --enable-static-check C=Command,clang-format,--dry-run,--Werror \
        --enable-static-check C++=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c++20 \
        --enable-static-check C++=Command,clang-format,--dry-run,--Werror \
        --enable-static-check Python=Pylance \
        --enable-static-check Python=Ruff

    # @brief Executes the smoke-test installation command.
    # @details Installs the canonical provider/resource set, including Pi
    # prompts and Pi skills, into user-level directories under the disposable
    # HOME.
    "${SCRIPT_PATH}/req.sh" \
        --base "${FOLDER_PATH}" --docs-dir "${FOLDER_PATH}/docs" \
        --guidelines-dir "${FOLDER_PATH}/guidelines" \
        --src-dir "${FOLDER_PATH}/src" \
        --tests-dir "${FOLDER_PATH}/tests" \
        --upgrade-guidelines \
        --provider antigravity:prompts,skills \
        --provider claude:prompts,agents,skills \
        --provider codex:prompts,skills \
        --provider opencode:prompts,agents,skills \
        --provider "pi:prompts,skills" \
        --enable-static-check C=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c11 \
        --enable-static-check C=Command,clang-format,--dry-run,--Werror \
        --enable-static-check C++=Command,cppcheck,--error-exitcode=1,\"--enable=warning,style,performance,portability\",--std=c++20 \
        --enable-static-check C++=Command,clang-format,--dry-run,--Werror \
        --enable-static-check Python=Pylance \
        --enable-static-check Python=Ruff
fi
