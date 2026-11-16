"""@file test_prompts_update.py
@brief Verify scripts/prompts-update.sh composes the bundled-prompts update commit text.
@details Level 1 contract test over the `commit_update` shell function definition. The
function cannot be executed in isolation because `main` performs a network clone, so the
test extracts the function body from the tracked script text and asserts the canonical
repository commit subject plus the previous-to-new version statement required by SRS-602,
and executes the extracted `should_proceed_update` gate to verify the strictly greater
version update policy required by SRS-599 and SRS-600.
Reading the tracked script is deterministic and side-effect free; no network, user paths,
or git index mutations occur.
@satisfies SRS-599, SRS-600, SRS-601, SRS-602
"""

from pathlib import Path
import re
import subprocess

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "prompts-update.sh"

EXPECTED_COMMIT_SUBJECT = (
    "change(prompts): Update bundled prompts from"
    " ${previous_version} to ${new_version} [useReq]"
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
    exact canonical subject line `change(prompts): Update bundled prompts from
    ${previous_version} to ${new_version} [useReq]` is composed as a `-m` commit
    message argument.
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


def _run_should_proceed_update(tmp_path: Path, latest_version: str, stored_version: str) -> int:
    """@brief Execute the extracted `should_proceed_update` function in a temporary shell.
    @details Extracts the `log` helper, the `PROMPTS_VERSION_REL` constant, and the
    `should_proceed_update` function from the tracked script text, composes them into one
    temporary Bash script that invokes the gate with the supplied arguments, and returns
    its exit status. O(n) in script length plus one subprocess; all writes stay under
    tmp_path and no repository or network state is touched.
    @param tmp_path {Path} Pytest-owned disposable filesystem root.
    @param latest_version {str} Resolved upstream release version argument.
    @param stored_version {str} Stored version marker argument.
    @return {int} Exit status: 0 when the update must proceed, 1 when it must abort.
    @throws {AssertionError} Raised when a required script block cannot be located.
    """
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    log_match = re.search(r"^log\(\) \{\n.*?^\}\n", script_text, re.DOTALL | re.MULTILINE)
    constant_match = re.search(r"^PROMPTS_VERSION_REL=.*\n", script_text, re.MULTILINE)
    gate_match = re.search(
        r"^should_proceed_update\(\) \{\n.*?^\}\n", script_text, re.DOTALL | re.MULTILINE
    )
    assert log_match is not None, "log function definition not found"
    assert constant_match is not None, "PROMPTS_VERSION_REL definition not found"
    assert gate_match is not None, "should_proceed_update definition not found"
    gate_script = tmp_path / "should-proceed-update.sh"
    gate_script.write_text(
        log_match.group(0)
        + constant_match.group(0)
        + gate_match.group(0)
        + 'should_proceed_update "$1" "$2"\n',
        encoding="utf-8",
    )
    completed = subprocess.run(
        ["bash", str(gate_script), latest_version, stored_version],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.returncode


def test_should_proceed_update_aborts_for_equal_or_lower_version(tmp_path):
    """@brief Verify the update gate aborts when the resolved version is not strictly greater.
    @details Arrange extracted gate function executions for an equal tuple, a `v`-prefixed
    equal tuple, and a lower resolved version; assert each aborts with exit status 1 so
    synchronization never runs for lower-than-or-equal comparisons (SRS-599).
    @return {None} Function return value.
    """
    assert _run_should_proceed_update(tmp_path, "1.2.3", "1.2.3") == 1
    assert _run_should_proceed_update(tmp_path, "v1.2.3", "v1.2.3") == 1
    assert _run_should_proceed_update(tmp_path, "1.2.2", "1.2.3") == 1


def test_should_proceed_update_proceeds_for_strictly_greater_or_unknown(tmp_path):
    """@brief Verify the update gate proceeds for a strictly greater or unknown stored version.
    @details Arrange extracted gate function executions for a strictly greater tuple, a
    `v`-prefixed strictly greater tuple, and an `unknown` stored marker; assert each
    proceeds with exit status 0 (SRS-600).
    @return {None} Function return value.
    """
    assert _run_should_proceed_update(tmp_path, "1.2.4", "1.2.3") == 0
    assert _run_should_proceed_update(tmp_path, "v1.2.4", "v1.2.3") == 0
    assert _run_should_proceed_update(tmp_path, "1.2.4", "unknown") == 0
