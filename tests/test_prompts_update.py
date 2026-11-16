"""@file test_prompts_update.py
@brief Verify scripts/prompts-update.sh composes the bundled-prompts update commit text.
@details Level 1 contract test over the `commit_update` shell function definition. The
function cannot be executed in isolation because `main` performs a network clone, so the
test extracts the function body from the tracked script text and asserts the canonical
repository commit subject plus the previous-to-new version statement required by SRS-602.
Reading the tracked script is deterministic and side-effect free; no network, user paths,
or git index mutations occur.
@satisfies SRS-601, SRS-602
"""

from pathlib import Path
import re

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "prompts-update.sh"

EXPECTED_COMMIT_SUBJECT = (
    "change(prompts-update): auto-update bundled prompts and commit version bump [useReq]"
)
EXPECTED_VERSION_STATEMENT = (
    "from CLI-Prompts version ${previous_version} to ${new_version}"
)


def _extract_commit_update_body() -> str:
    """@brief Extract the `commit_update` function body from the updater script.
    @details Matches the `commit_update() {` opening line through the first closing
    `}` column through a deterministic non-greedy scan and fails with a diagnostic when
    the definition is absent. O(n) in script length; read-only filesystem access.
    @return {str} Full `commit_update` function body including the git commit
    composition lines.
    @throws {AssertionError} Raised when the function definition cannot be located.
    """
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"^commit_update\(\) \{\n(?P<body>.*?)^\}\n",
        script_text,
        re.DOTALL | re.MULTILINE,
    )
    assert match is not None, (
        "commit_update function definition not found in scripts/prompts-update.sh"
    )
    return match.group("body")


def test_commit_update_subject_uses_canonical_repository_format():
    """@brief Verify the update commit subject matches the canonical repository format.
    @details Arrange the script text and extract the `commit_update` body; assert the
    exact canonical subject line `change(prompts-update): auto-update bundled prompts
    and commit version bump [useReq]` is composed as a `-m` commit message argument.
    @return {None} Function return value.
    """
    body = _extract_commit_update_body()
    assert f'-m "{EXPECTED_COMMIT_SUBJECT}"' in body


def test_commit_update_message_states_previous_and_new_versions():
    """@brief Verify the update commit message states the previous and new versions.
    @details Arrange the script text and extract the `commit_update` body; assert the
    commit message states that the bundled prompts were updated from the previous
    version to the new version including both version-number parameters (SRS-602).
    @return {None} Function return value.
    """
    body = _extract_commit_update_body()
    assert EXPECTED_VERSION_STATEMENT in body
