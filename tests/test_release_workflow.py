"""@brief Tests for GitHub release workflow trigger, gating, and PyPI publication configuration.
@details Validates the release-pypi.yml workflow: manual dispatch and tag-push triggers,
uv-based build step, master-independent build/release execution (SRS-432), artifact
hand-off, master-only OIDC trusted publishing to PyPI (SRS-433, SRS-434), Node24-or-later
runtime execution of every JavaScript action (SRS-455, SRS-456, SRS-457), and absence of
transitional Node20 opt-out overrides (SRS-458).
@satisfies SRS-268
@satisfies SRS-431
@satisfies SRS-432
@satisfies SRS-433
@satisfies SRS-434
@satisfies SRS-438
@satisfies SRS-455
@satisfies SRS-456
@satisfies SRS-457
@satisfies SRS-458
@satisfies SRS-459
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release-pypi.yml"
LEGACY_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release-uvx.yml"


def _load_workflow() -> dict:
    """@brief Parse the release workflow YAML into a deterministic dictionary.
    @details Reads release-pypi.yml with yaml.safe_load for structural assertions.
    @return {dict} Parsed workflow mapping.
    """

    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


# @brief Minimum action major versions whose runtime is Node24 or later (SRS-455..SRS-457).
# @details Each entry maps an action slug referenced by `uses:` to the first major release
# that executes on the Node24 runtime, verified against the upstream action metadata
# (`runs.using: node24`). Composite `actions/attest-build-provenance` v3 delegates to the
# Node24-runtime `actions/attest` v3 action. Docker-based actions (e.g.
# `pypa/gh-action-pypi-publish`) do not execute on a Node runtime and are excluded.
NODE24_MINIMUM_ACTION_MAJORS: dict[str, int] = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "astral-sh/setup-uv": 7,
    "actions/upload-artifact": 6,
    "actions/download-artifact": 7,
    "actions/attest-build-provenance": 3,
    "softprops/action-gh-release": 3,
    "mikepenz/release-changelog-builder-action": 6,
}


def _workflow_uses_references(content: str) -> list[str]:
    """@brief Extract every `uses:` action reference from the workflow text.
    @details Matches YAML `uses:` keys regardless of indentation and strips trailing
    inline comments and surrounding whitespace from each value.
    @param {str} content Raw workflow file text.
    @return {list[str]} Ordered action references such as `actions/checkout@v5`.
    """

    references: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:"):
            continue
        value = stripped[len("uses:"):].split("#", 1)[0].strip()
        if value:
            references.append(value)
    return references


class TestReleaseWorkflowLocation(unittest.TestCase):
    """SRS-431: workflow file location and legacy file removal."""

    def test_release_workflow_is_defined_at_release_pypi_yml(self) -> None:
        """@brief Assert the release automation lives at release-pypi.yml.
        @details The PyPI trusted publisher is registered for workflow release-pypi.yml.
        @return {None} No return value.
        @satisfies SRS-431
        """

        self.assertTrue(
            WORKFLOW_PATH.is_file(),
            "Release workflow must be defined at .github/workflows/release-pypi.yml",
        )
        self.assertFalse(
            LEGACY_WORKFLOW_PATH.exists(),
            "Legacy .github/workflows/release-uvx.yml must be absent",
        )


class TestReleaseWorkflowTriggers(unittest.TestCase):
    """Validates release workflow trigger declarations (SRS-268)."""

    def test_release_workflow_supports_manual_dispatch(self) -> None:
        """@brief Release workflow must declare workflow_dispatch under on.
        @return {None} No return value.
        @satisfies SRS-268
        """

        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        on_block = re.search(
            r"^on:\n(?P<body>(?:^[ \t].*\n?)*)",
            content,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(on_block, "Workflow must define an 'on' block")
        assert on_block is not None
        self.assertIn(
            "workflow_dispatch:",
            on_block.group("body"),
            "Release workflow must allow manual dispatch",
        )
        self.assertRegex(
            on_block.group("body"),
            r"push:\n[ \t]+tags:\n[ \t]+- 'v\[0-9\]\+\.\[0-9\]\+\.\[0-9\]\+'",
            "Release workflow must retain tag push trigger",
        )

    def test_release_workflow_build_step_installs_build_module(self) -> None:
        """@brief Release workflow build step must include build module in uv execution.
        @return {None} No return value.
        """

        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "uv run --frozen --with build python -m build",
            content,
            "Release workflow build step must ensure `build` module availability",
        )


class TestReleaseWorkflowBranchGating(unittest.TestCase):
    """SRS-432/SRS-434: build/release independence and master-only publication."""

    def test_build_release_job_runs_independently_of_master_reachability(self) -> None:
        """@brief build-release must not gate on the is_master output.
        @details Develop-only tags must still produce build, attestation, and GitHub
        Release steps (SRS-432).
        @return {None} No return value.
        @satisfies SRS-432
        """

        workflow = _load_workflow()
        build_release = workflow["jobs"]["build-release"]
        self.assertNotIn(
            "if",
            build_release,
            "build-release job must execute for master and develop tags",
        )
        build_steps = {step.get("name", "") for step in build_release["steps"]}
        self.assertIn("Build distributions", build_steps)
        self.assertIn("Attest build provenance", build_steps)
        self.assertIn("Create GitHub Release and upload assets", build_steps)

    def test_check_branch_job_reports_is_master_output(self) -> None:
        """@brief check-branch must publish the is_master output for downstream gating.
        @return {None} No return value.
        """

        workflow = _load_workflow()
        check_branch = workflow["jobs"]["check-branch"]
        self.assertIn("is_master", check_branch["outputs"])
        run_step = next(
            step for step in check_branch["steps"] if "run" in step
        )
        self.assertIn("git branch -r --contains", run_step["run"])

    def test_publish_pypi_job_gated_on_master_output(self) -> None:
        """@brief publish-pypi must execute only when is_master is true.
        @details Tags reachable only from origin/develop must skip PyPI publication
        while the release workflow still runs (SRS-434).
        @return {None} No return value.
        @satisfies SRS-434
        """

        workflow = _load_workflow()
        publish_job = workflow["jobs"]["publish-pypi"]
        self.assertEqual(
            publish_job.get("if"),
            "needs.check-branch.outputs.is_master == 'true'",
            "publish-pypi job must be gated on master reachability",
        )
        self.assertIn("check-branch", publish_job["needs"])
        self.assertIn("build-release", publish_job["needs"])

    def test_build_release_uploads_dist_artifact_for_publish_job(self) -> None:
        """@brief build-release must upload dist artifacts consumed by publish-pypi.
        @return {None} No return value.
        """

        workflow = _load_workflow()
        upload_step = next(
            step
            for step in workflow["jobs"]["build-release"]["steps"]
            if step.get("uses", "").startswith("actions/upload-artifact@")
        )
        self.assertEqual(upload_step["with"]["name"], "dist")
        self.assertEqual(upload_step["with"]["path"], "dist/*")
        download_step = next(
            step
            for step in workflow["jobs"]["publish-pypi"]["steps"]
            if step.get("uses", "").startswith("actions/download-artifact@")
        )
        self.assertEqual(download_step["with"]["name"], "dist")
        self.assertEqual(download_step["with"]["path"], "dist/")


class TestReleaseWorkflowPyPITrustedPublishing(unittest.TestCase):
    """SRS-433: OIDC trusted publishing via pypa/gh-action-pypi-publish."""

    def test_publish_job_uses_official_pypi_publish_action_with_oidc(self) -> None:
        """@brief publish-pypi must use pypa/gh-action-pypi-publish with id-token permission.
        @details OIDC trusted publishing requires the GitHub id-token write permission
        and the official publishing action (SRS-433).
        @return {None} No return value.
        @satisfies SRS-433
        """

        workflow = _load_workflow()
        publish_job = workflow["jobs"]["publish-pypi"]
        self.assertEqual(
            publish_job.get("permissions", {}).get("id-token"),
            "write",
            "publish-pypi job must grant id-token: write for OIDC trusted publishing",
        )
        uses = [
            step.get("uses", "")
            for step in publish_job["steps"]
        ]
        self.assertIn(
            "pypa/gh-action-pypi-publish@release/v1",
            uses,
            "publish-pypi job must publish via pypa/gh-action-pypi-publish",
        )

    def test_publish_action_uses_no_static_credentials(self) -> None:
        """@brief publish step must not declare API-token or password credentials.
        @details Trusted publishing relies exclusively on the OIDC token; no
        `password` or `api-token` input may be configured.
        @return {None} No return value.
        @satisfies SRS-433
        """

        workflow = _load_workflow()
        publish_step = next(
            step
            for step in workflow["jobs"]["publish-pypi"]["steps"]
            if step.get("uses") == "pypa/gh-action-pypi-publish@release/v1"
        )
        publish_inputs = publish_step.get("with", {})
        self.assertNotIn("password", publish_inputs)
        self.assertNotIn("api-token", publish_inputs)

    def test_workflow_level_permissions_enable_attestation_oidc(self) -> None:
        """@brief Workflow permissions must include id-token and attestations writes.
        @return {None} No return value.
        """

        workflow = _load_workflow()
        permissions = workflow.get("permissions", {})
        self.assertEqual(permissions.get("id-token"), "write")
        self.assertEqual(permissions.get("attestations"), "write")
        self.assertEqual(permissions.get("contents"), "write")


class TestReleaseWorkflowNode24Runtime(unittest.TestCase):
    """SRS-455/SRS-456/SRS-457/SRS-458: Node24-or-later action runtime constraints."""

    def test_all_javascript_actions_run_on_node24_or_later(self) -> None:
        """@brief Every JavaScript action major must satisfy the Node24 floor map.
        @details Resolves each `uses:` reference, extracts its `v<major>` tag, and
        asserts the major is greater than or equal to the first Node24-runtime major
        for that action (SRS-455, SRS-456, SRS-457). Docker-based actions are not
        executed on a Node runtime and are exempt (SRS-455).
        @return {None} No return value.
        @satisfies SRS-455
        @satisfies SRS-456
        @satisfies SRS-457
        @satisfies SRS-459
        """

        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        references = _workflow_uses_references(content)
        self.assertTrue(references, "Workflow must reference at least one action")
        referenced_slugs: set[str] = set()
        for reference in references:
            slug, _, ref = reference.partition("@")
            self.assertTrue(ref, f"Action reference must pin a version: {reference}")
            if slug not in NODE24_MINIMUM_ACTION_MAJORS:
                continue
            referenced_slugs.add(slug)
            major_match = re.match(r"v(\d+)", ref)
            self.assertIsNotNone(
                major_match,
                f"JavaScript action reference must use a v<major> tag: {reference}",
            )
            assert major_match is not None
            major = int(major_match.group(1))
            minimum = NODE24_MINIMUM_ACTION_MAJORS[slug]
            self.assertGreaterEqual(
                major,
                minimum,
                f"{slug}@v{major} runs on Node20; Node24 floor is v{minimum} (SRS-455)",
            )
        self.assertEqual(
            referenced_slugs,
            set(NODE24_MINIMUM_ACTION_MAJORS),
            "Every Node24-constrained action must be referenced by the workflow",
        )

    def test_no_transitional_node_opt_out_env_overrides(self) -> None:
        """@brief Transitional Node20 opt-out and Node24 force overrides must be absent.
        @details The back-compatibility workarounds `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`
        and `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` MUST NOT appear anywhere in the workflow
        (SRS-458): actions are migrated natively to Node24-runtime majors.
        @return {None} No return value.
        @satisfies SRS-458
        @satisfies SRS-459
        """

        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertNotIn(
            "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION",
            content,
            "Transitional Node20 opt-out override must be absent (SRS-458)",
        )
        self.assertNotIn(
            "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24",
            content,
            "Transitional Node24 force override must be absent (SRS-458)",
        )
