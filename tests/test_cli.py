"""
Test suite for the useReq CLI command.

This module implements unit tests to verify the correct operation
of the CLI under the user-level installation architecture: skills are
installed into user-level CLI configuration directories under the user
HOME, and configuration is persisted in the single user-global file
`~/.config/usereq/config.json`.

Covers: SRS-026/027 (read-only prompts), SRS-034/035 (provider gating),
SRS-055/056 (uv runner), SRS-064 (update), SRS-249..252 (static-check
config), SRS-263 (read-only packaged prompts), SRS-275..280 (provider
names), SRS-284..286/288 (test requirements), SRS-290/291 (install
table), SRS-342/352 (README), SRS-343/344 (upgrade/uninstall),
SRS-345..351 (release check helpers), SRS-359..363 (install defaults),
SRS-364..366 (provider grammar), SRS-368 (SKILL.md front matter),
SRS-371/374 (flowchart artifacts), SRS-381..390 (user-level install,
global config, model removal), SRS-391 (runtime git resolution),
SRS-462..SRS-494 (show providers table, installation status, alphabetical
order, skills path), SRS-495 (packaged templates directory), SRS-513..SRS-517
(compact post-installation resource report).
"""

import json
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Imports the CLI module to test.
from usereq import cli

ALL_PROVIDERS = [
    "--enable",
    "antigravity",
    "--enable",
    "claude",
    "--enable",
    "codex",
    "--enable",
    "copilot",
    "--enable",
    "openclaw",
    "--enable",
    "opencode",
    "--enable",
    "pi",
]
"""Repeatable --enable PROVIDER names that enable every supported provider."""

EXPECTED_SKILL_ROOTS = {
    "antigravity": (".gemini", "config", "skills"),
    "claude": (".claude", "skills"),
    "codex": (".codex", "skills"),
    "copilot": (".copilot", "skills"),
    "openclaw": (".openclaw", "workspace", "skills"),
    "opencode": (".config", "opencode", "skills"),
    "pi": (".pi", "agent", "skills"),
}
"""Hardcoded user-level skills roots per provider (SRS-382..SRS-386, SRS-486, SRS-493)."""

EXPECTED_PROMPTS = sorted(
    path.stem for path in (cli.RESOURCE_ROOT / "prompts").glob("*.md")
)


def make_git_repo(path: Path) -> None:
    """Initialize a deterministic git repository for command-level tests."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "tests@example.com"],
        cwd=str(path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "tests"],
        cwd=str(path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(path),
        capture_output=True,
    )


class HomeIsolatedTestCase(unittest.TestCase):
    """Base class isolating the user HOME for user-level installation tests."""

    def setUp(self) -> None:
        self.HOME = Path(tempfile.mkdtemp(prefix="usereq-test-home-"))
        patcher = patch("usereq.cli.home_dir", return_value=self.HOME)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.HOME, ignore_errors=True)

    def run_cli(self, argv: list[str]) -> int:
        """Run cli.main with release-check disabled and isolated HOME."""
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            return cli.main(argv)

    def seed_directory_config(
        self,
        docs: str = "docs",
        tests: str = "tests",
        src: tuple[str, ...] = ("src",),
    ) -> None:
        """Persist project-relative directory values for the isolated HOME (SRS-398..SRS-400)."""
        cli.update_directory_config(docs, tests, list(src))


class TestUserLevelInstall(HomeIsolatedTestCase):
    """SRS-381..SRS-389: single install run with every provider (skills only)."""

    @classmethod
    def setUpClass(cls) -> None:
        """Executes one installation for all assertion methods."""
        cls.CLASS_HOME = Path(tempfile.mkdtemp(prefix="usereq-install-home-"))
        cls.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-install-project-"))
        for sub in ("docs", "tests", "src"):
            (cls.TEST_DIR / sub).mkdir(exist_ok=True)
        cls.prompts_snapshot_before = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted((cli.RESOURCE_ROOT / "prompts").iterdir())
            if p.is_file() and not p.name.startswith(".")
        }
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("usereq.cli.home_dir", return_value=cls.CLASS_HOME),
        ):
            cli.update_directory_config("docs", "tests", ["src"])
            cls.exit_code = cli.main(
                [
                    "--prj-base",
                    str(cls.TEST_DIR),
                ]
                + ALL_PROVIDERS
                + ["install"]
            )
        cls.prompts_snapshot_after = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted((cli.RESOURCE_ROOT / "prompts").iterdir())
            if p.is_file() and not p.name.startswith(".")
        }

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.TEST_DIR, ignore_errors=True)
        shutil.rmtree(cls.CLASS_HOME, ignore_errors=True)

    def setUp(self) -> None:
        self.HOME = self.CLASS_HOME
        self.TEST_DIR = type(self).TEST_DIR
        patcher = patch("usereq.cli.home_dir", return_value=self.HOME)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exit_code_is_zero(self) -> None:
        """The installation must complete with exit code 0."""
        self.assertEqual(self.exit_code, 0)

    def test_packaged_prompt_templates_are_read_only(self) -> None:
        """SRS-263: packaged prompt templates are not modified by the CLI run."""
        self.assertEqual(self.prompts_snapshot_before, self.prompts_snapshot_after)

    def test_no_project_local_files_are_created(self) -> None:
        """SRS-388: no `.req` directory or provider dirs are created in the project."""
        self.assertFalse((self.TEST_DIR / ".req").exists())
        for hidden in (".claude", ".codex", ".copilot", ".gemini", ".openclaw", ".pi", ".opencode"):
            self.assertFalse(
                (self.TEST_DIR / hidden).exists(),
                f"The project must not contain {hidden}",
            )

    def test_skills_roots_created_for_every_provider(self) -> None:
        """SRS-382..SRS-386/SRS-486: skills roots are created under HOME."""
        for provider, parts in EXPECTED_SKILL_ROOTS.items():
            root = self.HOME.joinpath(*parts)
            self.assertTrue(root.is_dir(), f"Missing {provider} skills root {root}")

    def test_prompt_artifacts_are_not_created(self) -> None:
        """SRS-353/SRS-467..SRS-470: prompts and agents are no longer installed."""
        self.assertFalse((self.HOME / ".claude" / "commands").exists())
        self.assertFalse((self.HOME / ".claude" / "agents").exists())
        self.assertFalse((self.HOME / ".codex" / "prompts").exists())
        self.assertFalse((self.HOME / ".codex" / "agents").exists())
        self.assertFalse((self.HOME / ".gemini" / "config" / "workflows").exists())
        self.assertFalse((self.HOME / ".gemini" / "config" / "agents").exists())
        self.assertFalse((self.HOME / ".pi" / "agent" / "prompts").exists())
        self.assertFalse((self.HOME / ".config" / "opencode" / "commands").exists())
        self.assertFalse((self.HOME / ".config" / "opencode" / "agents").exists())

    def test_skill_arguments_substituted(self) -> None:
        """%%ARGS%% is substituted with $ARGUMENTS in generated skills."""
        with_args = [
            p
            for p in EXPECTED_PROMPTS
            if "%%ARGS%%"
            in (cli.RESOURCE_ROOT / "prompts" / f"{p}.md").read_text(
                encoding="utf-8"
            )
        ]
        self.assertTrue(with_args, "bundled prompts must include argument-based prompts")
        prompt = with_args[0]
        skill = self.HOME / ".claude" / "skills" / f"req-{prompt}" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertIn("$ARGUMENTS", content)
        self.assertNotIn("%%ARGS%%", content)

    def test_skill_files_created_for_every_provider(self) -> None:
        """Skills are created as req-<name>/SKILL.md for every enabled provider."""
        skill_roots = {
            "antigravity": self.HOME / ".gemini" / "config" / "skills",
            "claude": self.HOME / ".claude" / "skills",
            "codex": self.HOME / ".codex" / "skills",
            "copilot": self.HOME / ".copilot" / "skills",
            "opencode": self.HOME / ".config" / "opencode" / "skills",
            "pi": self.HOME / ".pi" / "agent" / "skills",
        }
        for provider, root in skill_roots.items():
            for prompt in EXPECTED_PROMPTS:
                skill = root / f"req-{prompt}" / "SKILL.md"
                self.assertTrue(
                    skill.exists(), f"Missing {provider} skill {skill}"
                )

    def test_skill_front_matter_structure(self) -> None:
        """SRS-368/SRS-389: SKILL.md has name and description, never model/tools."""
        skill = (
            self.HOME
            / ".claude"
            / "skills"
            / f"req-{EXPECTED_PROMPTS[0]}"
            / "SKILL.md"
        )
        content = skill.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"))
        self.assertIn("name: req-", content)
        self.assertIn("description:", content)
        self.assertNotIn("model:", content)
        self.assertNotIn("tools:", content)
        self.assertNotIn("allowed-tools:", content)

    def test_skills_have_no_model_or_tools_fields(self) -> None:
        """SRS-389: generated skills contain no model/tools fields."""
        skill = (
            self.HOME
            / ".claude"
            / "skills"
            / f"req-{EXPECTED_PROMPTS[0]}"
            / "SKILL.md"
        )
        content = skill.read_text(encoding="utf-8")
        self.assertNotIn("model:", content)
        self.assertNotIn("tools:", content)
        self.assertNotIn("allowed-tools:", content)

    def test_global_config_saved_with_canonical_keys(self) -> None:
        """SRS-288: single global config file with canonical directory/provider keys only."""
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        self.assertTrue(config_path.is_file())
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(data.keys()),
            sorted(["docs-dir", "tests-dir", "src-dir", "providers"]),
        )
        self.assertEqual(data["docs-dir"], "docs")
        self.assertEqual(data["tests-dir"], "tests")
        self.assertEqual(data["src-dir"], ["src"])
        self.assertIsInstance(data["providers"], list)

    def test_prj_base_and_git_base_not_persisted(self) -> None:
        """SRS-394: --prj-base and --git-base are never written to the configuration file."""
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertNotIn("prj-base", data)
        self.assertNotIn("git-base", data)

    def test_flowchart_resources_created(self) -> None:
        """SRS-371/SRS-374: req-flowchart skill artifacts are emitted when bundled."""
        if "flowchart" not in EXPECTED_PROMPTS:
            self.skipTest("flowchart.md template not bundled")
        self.assertTrue(
            (
                self.HOME / ".claude" / "skills" / "req-flowchart" / "SKILL.md"
            ).exists()
        )
        self.assertTrue(
            (self.HOME / ".pi" / "agent" / "skills" / "req-flowchart").is_dir()
        )
        self.assertTrue(
            (
                self.HOME / ".codex" / "skills" / "req-flowchart" / "SKILL.md"
            ).exists()
        )
        self.assertTrue(
            (
                self.HOME
                / ".openclaw"
                / "workspace"
                / "skills"
                / "req-flowchart"
                / "SKILL.md"
            ).exists()
        )

    def test_guidelines_tokens_replaced(self) -> None:
        """SRS-402/SRS-403/SRS-499: packaged-resource tokens are fully substituted."""
        skill = self.HOME / ".claude" / "skills" / "req-analyze" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertNotIn("%%GUIDELINES_PATH%%", content)
        self.assertNotIn("%%GUIDELINES_FILES%%", content)
        self.assertNotIn("%%TEMPLATE_PATH%%", content)
        self.assertIn("src/usereq/resources/guidelines", content)
        self.assertIn("src/usereq/resources/templates", content)

    def test_directory_tokens_use_configured_values(self) -> None:
        """SRS-500/SRS-501/SRS-502/SRS-503: configured directory values are rendered."""
        skill = self.HOME / ".claude" / "skills" / "req-analyze" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertNotIn("%%DOC_PATH%%", content)
        self.assertNotIn("%%SRC_PATHS%%", content)
        self.assertNotIn("%%TEST_PATH%%", content)
        self.assertIn("docs/REQUIREMENTS.md", content)
        self.assertIn("`src/`", content)


class TestProviderNameParsing(unittest.TestCase):
    """SRS-275/278/364: --enable/--disable PROVIDER name validation."""

    def test_valid_provider_name_accepted(self) -> None:
        self.assertEqual(cli.validate_provider_name("codex"), "codex")

    def test_provider_name_is_case_insensitive(self) -> None:
        self.assertEqual(cli.validate_provider_name("Codex"), "codex")
        self.assertEqual(cli.validate_provider_name(" PI "), "pi")

    def test_openclaw_provider_accepted(self) -> None:
        self.assertEqual(cli.validate_provider_name("openclaw"), "openclaw")

    def test_removed_providers_rejected(self) -> None:
        """SRS-364: gemini, github, and kiro are not valid providers."""
        for provider in ("gemini", "github", "kiro"):
            with self.assertRaises(cli.ReqError):
                cli.validate_provider_name(provider)

    def test_unknown_provider_rejected(self) -> None:
        with self.assertRaises(cli.ReqError):
            cli.validate_provider_name("unknown")

    def test_legacy_spec_tokens_rejected_as_providers(self) -> None:
        """SRS-275: the legacy PROVIDER:ARTIFACT SPEC grammar is no longer accepted."""
        for token in (
            "codex:prompts,skills",
            "pi:skills",
            "claude:prompts:prompts-use-agents",
        ):
            with self.assertRaises(cli.ReqError):
                cli.validate_provider_name(token)


class TestProviderMultiple(HomeIsolatedTestCase):
    """SRS-276/285: multiple --enable PROVIDER occurrences activate independently."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-multi-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()

    def install(self, *providers: str) -> int:
        argv = [
            "--prj-base",
            str(self.TEST_DIR),
        ]
        for provider in providers:
            argv.extend(["--enable", provider])
        argv.append("install")
        return self.run_cli(argv)

    def test_exit_code_zero(self) -> None:
        self.assertEqual(self.install("codex", "claude", "pi"), 0)

    def test_codex_skills_created(self) -> None:
        """SRS-383: codex skills install under ~/.codex/skills."""
        self.install("codex")
        self.assertTrue(
            (self.HOME / ".codex" / "skills" / f"req-{EXPECTED_PROMPTS[0]}").is_dir()
        )
        self.assertFalse((self.HOME / ".agents").exists())

    def test_copilot_skills_created(self) -> None:
        """SRS-493/SRS-494: copilot skills install under ~/.copilot/skills."""
        self.install("copilot")
        self.assertTrue(
            (self.HOME / ".copilot" / "skills" / f"req-{EXPECTED_PROMPTS[0]}").is_dir()
        )

    def test_claude_skills_created(self) -> None:
        self.install("claude")
        self.assertTrue(
            (self.HOME / ".claude" / "skills" / f"req-{EXPECTED_PROMPTS[0]}").is_dir()
        )
        self.assertFalse((self.HOME / ".claude" / "commands").exists())

    def test_openclaw_skills_created(self) -> None:
        self.install("openclaw")
        self.assertTrue(
            (
                self.HOME
                / ".openclaw"
                / "workspace"
                / "skills"
                / f"req-{EXPECTED_PROMPTS[0]}"
            ).is_dir()
        )

    def test_disabled_providers_absent(self) -> None:
        self.install("codex")
        for provider_dir in (".claude", ".gemini", ".openclaw", ".pi"):
            self.assertFalse((self.HOME / provider_dir).exists())

    def test_at_least_one_provider_required(self) -> None:
        """SRS-035: installation without enabled providers fails with exit code 4."""
        rc = self.run_cli(
            [
                "--prj-base",
                str(self.TEST_DIR),
            ]
        )
        self.assertEqual(rc, 4)


class TestProviderPersistence(HomeIsolatedTestCase):
    """SRS-279/SRS-280/SRS-286: provider name persistence round-trips."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-persist-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()
        self.base_argv = [
            "--prj-base",
            str(self.TEST_DIR),
        ]

    def test_providers_persisted_to_global_config(self) -> None:
        self.run_cli(self.base_argv + ["--enable", "pi", "install"])
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["providers"], ["pi"])

    def test_providers_restored_on_install(self) -> None:
        """SRS-280/SRS-064: install without --enable reuses persisted providers."""
        self.run_cli(self.base_argv + ["--enable", "codex", "install"])
        shutil.rmtree(self.HOME / ".codex")
        rc = self.run_cli(["install"])
        self.assertEqual(rc, 0)
        self.assertTrue(
            (self.HOME / ".codex" / "skills" / f"req-{EXPECTED_PROMPTS[0]}").is_dir()
        )

    def test_cli_provider_replaces_persisted_on_update(self) -> None:
        """SRS-279: --enable replaces the named provider's entries, preserving others."""
        self.run_cli(self.base_argv + ["--enable", "codex", "install"])
        rc = self.run_cli(
            ["--prj-base", str(self.TEST_DIR), "--enable", "claude", "install"]
        )
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["providers"], ["codex", "claude"])


class TestInstallDefaultDirectories(HomeIsolatedTestCase):
    """SRS-448: install performs no project-side directory operations."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-defaults-"))
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def test_install_does_not_persist_default_directories(self) -> None:
        """SRS-448: install persists no docs-dir/tests-dir/src-dir keys."""
        rc = self.run_cli(["--enable", "codex", "install"])
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertNotIn("docs-dir", data)
        self.assertNotIn("tests-dir", data)
        self.assertNotIn("src-dir", data)

    def test_install_does_not_create_missing_directories(self) -> None:
        """SRS-448: installation creates no project directories."""
        rc = self.run_cli(["--enable", "codex", "install"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.TEST_DIR / "usereq").is_dir())
        self.assertFalse((self.TEST_DIR / "tests").is_dir())
        self.assertFalse((self.TEST_DIR / "src").is_dir())

    def test_install_ignores_configured_directories(self) -> None:
        """SRS-448: seeded directory configuration stays untouched by install."""
        self.seed_directory_config(docs="req/docs")
        rc = self.run_cli(["--enable", "codex", "install"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.TEST_DIR / "req" / "docs").is_dir())

    def test_install_does_not_touch_persisted_configuration(self) -> None:
        """SRS-448: install persists no directory keys and rewrites nothing."""
        self.seed_directory_config()
        self.run_cli(["--enable", "codex"])
        rc = self.run_cli(["install"])
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["docs-dir"], "docs")


class TestGuidelinesDirectory(HomeIsolatedTestCase):
    """SRS-360/SRS-402/SRS-403/SRS-404/SRS-498: packaged resources of the running installation."""

    def setUp(self) -> None:
        super().setUp()
        self.resource_root = self.HOME / "resources"
        self.guidelines = self.resource_root / "guidelines"
        self.templates = self.resource_root / "templates"
        (self.resource_root / "prompts").mkdir(parents=True, exist_ok=True)
        self.original_resource_root = cli.RESOURCE_ROOT
        cli.RESOURCE_ROOT = self.resource_root
        self.addCleanup(
            setattr, cli, "RESOURCE_ROOT", self.original_resource_root
        )

    def test_guidelines_dir_is_fixed_home_relative_path(self) -> None:
        """SRS-360: GUIDELINES_DIR resolves to packaged resources and is not configurable."""
        self.assertEqual(cli.guidelines_dir(), self.guidelines)
        project = Path(tempfile.mkdtemp(prefix="usereq-guidelines-"))
        self.addCleanup(shutil.rmtree, project, ignore_errors=True)
        rc = self.run_cli(
            ["--prj-base", str(project), "--enable", "codex", "install"]
        )
        self.assertEqual(rc, 0)
        self.assertNotIn(
            "guidelines-dir",
            (self.HOME / ".config" / "usereq" / "config.json").read_text(
                encoding="utf-8"
            ),
        )

    def test_home_relative_path_rendering(self) -> None:
        """SRS-402/SRS-403: substitution values use the ~/ form."""
        self.assertEqual(cli.format_home_relative_path(self.HOME), "~")
        self.assertEqual(
            cli.format_home_relative_path(self.guidelines / "RFC2119.md"),
            "~/resources/guidelines/RFC2119.md",
        )

    def test_guidelines_file_list_uses_installed_directory(self) -> None:
        """SRS-403: %%GUIDELINES_FILES%% lists installed guideline files."""
        self.guidelines.mkdir(parents=True, exist_ok=True)
        (self.guidelines / "RFC2119.md").write_text("rfc\n", encoding="utf-8")
        self.assertEqual(
            cli.generate_guidelines_file_list(),
            "`~/resources/guidelines/RFC2119.md`",
        )
        self.assertEqual(
            cli.generate_guidelines_file_names(),
            ["RFC2119.md"],
        )

    def test_guidelines_file_list_falls_back_to_directory(self) -> None:
        """SRS-402: missing guidelines directory renders the directory with a trailing slash."""
        self.assertEqual(
            cli.generate_guidelines_file_list(),
            "`~/resources/guidelines/`",
        )

    def test_templates_dir_resolves_packaged_templates_directory(self) -> None:
        """SRS-498: %%TEMPLATE_PATH%% renders the packaged templates directory."""
        self.assertEqual(cli.templates_dir(), self.templates)
        self.assertEqual(cli.templates_dir(), self.resource_root / "templates")

    def test_guidelines_enumeration_excludes_symlinks(self) -> None:
        """SRS-504/SRS-507: %%GUIDELINES_FILES%% never follows symbolic links."""
        # Arrange
        self.guidelines.mkdir(parents=True, exist_ok=True)
        (self.guidelines / "RFC2119.md").write_text("rfc\n", encoding="utf-8")
        (self.guidelines / "Linked.md").symlink_to(self.guidelines / "RFC2119.md")
        (self.guidelines / "LinkedDir").symlink_to(self.resource_root)
        # Act
        file_list = cli.generate_guidelines_file_list()
        names = cli.generate_guidelines_file_names()
        # Assert
        self.assertEqual(file_list, "`~/resources/guidelines/RFC2119.md`")
        self.assertEqual(names, ["RFC2119.md"])

    def test_symlinked_guidelines_directory_falls_back_to_directory(self) -> None:
        """SRS-504/SRS-507: a symlinked guidelines directory is not followed."""
        # Arrange
        real_dir = self.HOME / "real-guidelines"
        real_dir.mkdir(parents=True)
        (real_dir / "RFC2119.md").write_text("rfc\n", encoding="utf-8")
        self.guidelines.symlink_to(real_dir)
        # Act
        file_list = cli.generate_guidelines_file_list()
        # Assert
        self.assertEqual(file_list, "`~/resources/guidelines/`")

    def test_packaged_paths_render_lexically_without_symlink_resolution(self) -> None:
        """SRS-505/SRS-507: packaged directory tokens never resolve symbolic links."""
        # Arrange
        shutil.rmtree(self.resource_root)
        real_root = self.HOME / "real-resources"
        (real_root / "guidelines").mkdir(parents=True)
        (real_root / "templates").mkdir(parents=True)
        self.resource_root.symlink_to(real_root)
        # Act
        rendered_guidelines = cli.format_home_relative_path(cli.guidelines_dir())
        rendered_templates = cli.format_home_relative_path(cli.templates_dir())
        # Assert
        self.assertEqual(rendered_guidelines, "~/resources/guidelines")
        self.assertEqual(rendered_templates, "~/resources/templates")

    def test_install_reports_guidelines_and_templates_compactly(self) -> None:
        """SRS-513/SRS-514/SRS-516/SRS-517: compact bare file-name resource report."""
        # Arrange
        self.guidelines.mkdir(parents=True, exist_ok=True)
        (self.guidelines / "RFC2119.md").write_text("rfc\n", encoding="utf-8")
        (self.guidelines / "Linked.md").symlink_to(self.guidelines / "RFC2119.md")
        self.templates.mkdir(parents=True, exist_ok=True)
        (self.templates / "Requirements_Template.md").write_text(
            "tpl\n", encoding="utf-8"
        )
        expected_output = [
            "Installation completed successfully in ~",
            "Guidelines: ~/resources/guidelines/",
            "RFC2119.md",
            "Templates: ~/resources/templates/",
            "Requirements_Template.md",
        ]
        # Act
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["--enable", "codex", "install"])
        lines = mock_stdout.getvalue().splitlines()
        # Assert
        self.assertEqual(rc, 0)
        for expected_line in expected_output:
            self.assertIn(expected_line, lines)
        self.assertNotIn("Linked.md", mock_stdout.getvalue())
        self.assertNotIn(
            "~/resources/guidelines/RFC2119.md", mock_stdout.getvalue()
        )

    def test_install_report_keeps_symlinked_resource_root_lexical(self) -> None:
        """SRS-515/SRS-517: printed resource paths never resolve symbolic links."""
        # Arrange
        real_root = self.HOME / "real-resources"
        (real_root / "guidelines").mkdir(parents=True)
        (real_root / "templates").mkdir(parents=True)
        (real_root / "prompts").mkdir(parents=True)
        shutil.rmtree(self.resource_root)
        self.resource_root.symlink_to(real_root)
        expected_output = [
            "Guidelines: ~/resources/guidelines/",
            "Templates: ~/resources/templates/",
        ]
        # Act
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["--enable", "codex", "install"])
        lines = mock_stdout.getvalue().splitlines()
        # Assert
        self.assertEqual(rc, 0)
        for expected_line in expected_output:
            self.assertIn(expected_line, lines)
        self.assertNotIn(str(real_root), mock_stdout.getvalue())

    def test_install_does_not_copy_guidelines_into_project(self) -> None:
        """SRS-404: installation never writes guideline files into the project."""
        project = Path(tempfile.mkdtemp(prefix="usereq-guidelines-"))
        self.addCleanup(shutil.rmtree, project, ignore_errors=True)
        self.guidelines.mkdir(parents=True, exist_ok=True)
        (self.guidelines / "RFC2119.md").write_text("rfc\n", encoding="utf-8")
        rc = self.run_cli(["--prj-base", str(project), "--enable", "codex", "install"])
        self.assertEqual(rc, 0)
        self.assertFalse((project / "guidelines").exists())
        self.assertFalse((project / "usereq" / "guidelines").exists())


class TestDirectoryTokenSubstitution(HomeIsolatedTestCase):
    """SRS-359/SRS-500..SRS-503: default directory token substitution."""

    def test_defaults_apply_without_persisted_directory_keys(self) -> None:
        """SRS-359/SRS-500..SRS-502: absent config keys fall back to defaults."""
        config = cli.load_config()
        self.assertEqual(config["docs-dir"], "usereq/docs")
        self.assertEqual(config["src-dir"], ["src"])
        self.assertEqual(config["tests-dir"], "tests")

    def test_install_substitutes_directory_tokens_with_defaults(self) -> None:
        """SRS-500/SRS-501/SRS-503: install renders default directory tokens."""
        self.run_cli(["--enable", "claude", "install"])
        skill = self.HOME / ".claude" / "skills" / "req-analyze" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertNotIn("%%DOC_PATH%%", content)
        self.assertNotIn("%%SRC_PATHS%%", content)
        self.assertNotIn("%%TEST_PATH%%", content)
        self.assertIn("usereq/docs/REQUIREMENTS.md", content)
        self.assertIn("`src/`", content)

    def test_directory_tokens_render_configured_lexical_values(self) -> None:
        """SRS-506/SRS-507: configured directory values render without resolution."""
        # Arrange
        (self.HOME / "real-docs").mkdir()
        (self.HOME / "docs").symlink_to(self.HOME / "real-docs")
        cli.update_directory_config("docs", "tests", ["src"])
        # Act
        self.run_cli(["--enable", "claude", "install"])
        skill = self.HOME / ".claude" / "skills" / "req-analyze" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        # Assert
        self.assertIn("docs/REQUIREMENTS.md", content)
        self.assertNotIn("real-docs", content)


class TestPackagedTemplatesDirectory(unittest.TestCase):
    """SRS-495: packaged document templates resolve under resources/templates."""

    def setUp(self) -> None:
        self.original_resource_root = cli.RESOURCE_ROOT

    def tearDown(self) -> None:
        cli.RESOURCE_ROOT = self.original_resource_root

    def test_list_docs_templates_reads_templates_directory(self) -> None:
        """SRS-495: non-hidden packaged templates are listed from resources/templates."""
        templates = cli.list_docs_templates()
        expected_template = (
            cli.RESOURCE_ROOT / "templates" / cli.REQUIREMENTS_TEMPLATE_NAME
        )
        self.assertIn(expected_template, templates)
        for template in templates:
            self.assertEqual(template.parent, cli.RESOURCE_ROOT / "templates")
            self.assertFalse(template.name.startswith("."))

    def test_find_requirements_template_locates_packaged_template(self) -> None:
        """SRS-495: Requirements_Template.md is resolved from resources/templates."""
        template = cli.find_requirements_template(cli.list_docs_templates())
        self.assertEqual(template.name, cli.REQUIREMENTS_TEMPLATE_NAME)

    def test_list_docs_templates_missing_directory_raises_req_error(self) -> None:
        """SRS-495: absent resources/templates raises ReqError with exit code 9."""
        empty_root = Path(tempfile.mkdtemp(prefix="usereq-templates-"))
        self.addCleanup(shutil.rmtree, empty_root, ignore_errors=True)
        cli.RESOURCE_ROOT = empty_root
        with self.assertRaises(cli.ReqError) as ctx:
            cli.list_docs_templates()
        self.assertEqual(ctx.exception.code, 9)


class TestUninstallCommand(HomeIsolatedTestCase):
    """SRS-419: uninstall removes req-* skill artifacts from user-level directories."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-remove-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()
        rc = self.run_cli(
            [
                "--prj-base",
                str(self.TEST_DIR),
                "--enable",
                "claude",
                "--enable",
                "codex",
            ]
        )
        self.assertEqual(rc, 0)
        rc = self.run_cli(["install"])
        self.assertEqual(rc, 0)

    def test_uninstall_deletes_req_skill_artifacts(self) -> None:
        rc = self.run_cli(["uninstall"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.HOME / ".claude" / "skills" / "req-write").exists())
        self.assertFalse((self.HOME / ".codex" / "skills" / "req-write").exists())

    def test_uninstall_preserves_unrelated_user_content(self) -> None:
        unrelated_skill = self.HOME / ".claude" / "skills" / "user-skill"
        unrelated_skill.mkdir(parents=True, exist_ok=True)
        (unrelated_skill / "SKILL.md").write_text("user\n", encoding="utf-8")
        rc = self.run_cli(["uninstall"])
        self.assertEqual(rc, 0)
        self.assertTrue((unrelated_skill / "SKILL.md").exists())

    def test_uninstall_without_global_config_fails(self) -> None:
        (self.HOME / ".config" / "usereq" / "config.json").unlink()
        rc = self.run_cli(["uninstall"])
        self.assertNotEqual(rc, 0)


class TestInstallationSummaryTable(HomeIsolatedTestCase):
    """SRS-036/SRS-049/SRS-290/SRS-291/SRS-294: installation summary table rendering."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-table-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()

    def capture_install(self, *providers: str) -> str:
        argv = [
            "--prj-base",
            str(self.TEST_DIR),
        ]
        for provider in providers:
            argv.extend(["--enable", provider])
        argv.append("install")
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(argv)
        self.assertEqual(rc, 0)
        return mock_stdout.getvalue()

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove the ANSI sequences emitted around table border glyphs."""
        return text.replace("\033[91m", "").replace("\033[0m", "")

    def test_table_renders_provider_and_skills_rows(self) -> None:
        output = self.capture_install("codex", "pi")
        self.assertIn("codex", output)
        self.assertIn("pi", output)
        self.assertIn("Skills Installed", output)

    def test_table_contains_exactly_provider_and_skills_columns(self) -> None:
        """SRS-291/SRS-294: exactly the Provider and Skills Installed columns render."""
        output = self.capture_install("codex")
        self.assertIn("Provider", output)
        self.assertIn("Skills Installed", output)
        self.assertNotIn("Modules Installed", output)
        self.assertNotIn("Prompts Installed", output)

    def test_table_rows_are_alphabetical(self) -> None:
        """SRS-485: provider rows print in alphabetical order."""
        output = self.capture_install("pi", "codex", "openclaw")
        clean = self.strip_ansi(output)
        providers = []
        for line in clean.splitlines():
            if line.startswith("\u2502"):
                cell = line.split("\u2502")[1].strip()
                if cell and cell != "Provider":
                    providers.append(cell)
        self.assertEqual(providers, ["codex", "openclaw", "pi"])

    def test_table_wraps_skills_column(self) -> None:
        """SRS-290/SRS-293: Skills Installed wraps at a maximum width of 50 characters."""
        output = self.capture_install("codex")
        clean = self.strip_ansi(output)
        table_lines = [
            line for line in clean.splitlines() if line.startswith("\u2502")
        ]
        self.assertTrue(table_lines, "Installation table must be rendered")
        for line in table_lines:
            cells = line.split("\u2502")
            self.assertLessEqual(len(cells[2].strip()), 50)
        continuation_rows = [
            line for line in table_lines if not line.split("\u2502")[1].strip()
        ]
        self.assertTrue(
            continuation_rows,
            "Skills Installed must wrap onto subsequent lines",
        )


class TestUserLevelPathHelpers(unittest.TestCase):
    """SRS-381..SRS-386/SRS-462/SRS-463/SRS-486: user-level skills path helpers."""

    def test_get_global_config_path_under_home(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            path = cli.get_global_config_path()
        self.assertEqual(
            path, Path("/tmp/testhome/.config/usereq/config.json")
        )

    def test_provider_skills_roots(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_skills_root("antigravity"),
                Path("/tmp/testhome/.gemini/config/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("claude"),
                Path("/tmp/testhome/.claude/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("codex"),
                Path("/tmp/testhome/.codex/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("copilot"),
                Path("/tmp/testhome/.copilot/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("openclaw"),
                Path("/tmp/testhome/.openclaw/workspace/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("opencode"),
                Path("/tmp/testhome/.config/opencode/skills"),
            )
            self.assertEqual(
                cli.provider_skills_root("pi"),
                Path("/tmp/testhome/.pi/agent/skills"),
            )

    def test_provider_skills_path_renders_home_relative(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(cli.provider_skills_path("pi"), "~/.pi/agent/skills")
            self.assertEqual(cli.provider_skills_path("codex"), "~/.codex/skills")
            self.assertEqual(cli.provider_skills_path("copilot"), "~/.copilot/skills")
            self.assertEqual(
                cli.provider_skills_path("openclaw"),
                "~/.openclaw/workspace/skills",
            )

    def test_provider_skills_path_keeps_symlinked_config_prefix(self) -> None:
        """SRS-385/SRS-463: symlinked HOME subpaths keep the hardcoded rendering.

        expected_output: `provider_skills_path("opencode")` renders the hardcoded
        home-relative skills root `~/.config/opencode/skills` even when
        `<HOME>/.config` is a symbolic link to a backup directory.
        """
        home = Path(tempfile.mkdtemp(prefix="usereq-symlink-home-"))
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        backup_config = home / "My-Backup" / "config"
        backup_config.mkdir(parents=True)
        (home / ".config").symlink_to(backup_config, target_is_directory=True)
        with patch("usereq.cli.home_dir", return_value=home):
            self.assertEqual(
                cli.provider_skills_path("opencode"),
                "~/.config/opencode/skills",
            )

    def test_unknown_provider_raises(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            with self.assertRaises(cli.ReqError):
                cli.provider_skills_root("bogus")


class TestGitCheckCommand(HomeIsolatedTestCase):
    """SRS-311/SRS-312/SRS-391: --git-check executes git in --git-base."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-git-check-"))
        make_git_repo(self.TEST_DIR)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def test_git_check_on_clean_repo_succeeds(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
                patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
            ):
                rc = cli.main(["--git-check", "--git-base", str(self.TEST_DIR)])
            self.assertEqual(rc, 0)
            self.assertEqual(mock_stdout.getvalue(), "")
            self.assertEqual(mock_stderr.getvalue(), "")
        finally:
            os.chdir(prev_cwd)

    def test_git_check_on_dirty_repo_fails(self) -> None:
        (self.TEST_DIR / "dirty.txt").write_text("dirty", encoding="utf-8")
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
            ):
                rc = cli.main(["--git-check", "--git-base", str(self.TEST_DIR)])
            self.assertNotEqual(rc, 0)
            self.assertEqual(
                mock_stderr.getvalue().strip(), "ERROR: Git status unclear!"
            )
        finally:
            os.chdir(prev_cwd)

    def test_git_check_requires_git_base(self) -> None:
        """SRS-397/SRS-405: --git-check without --git-base exits with code 1."""
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            rc = cli.main(["--git-check"])
        self.assertEqual(rc, 1)
        self.assertIn("--git-base", mock_stderr.getvalue())

    def test_git_check_outside_git_repo_fails(self) -> None:
        non_git = Path(tempfile.mkdtemp(prefix="usereq-nongit-"))
        self.addCleanup(shutil.rmtree, non_git, ignore_errors=True)
        prev_cwd = Path.cwd()
        try:
            os.chdir(non_git)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-check", "--git-base", str(non_git)])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)


class TestDocsCheckCommand(HomeIsolatedTestCase):
    """SRS-313..SRS-317: --docs-check uses docs-dir from the global configuration."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-docs-check-"))
        (self.TEST_DIR / "docs").mkdir(exist_ok=True)
        (self.TEST_DIR / "tests").mkdir(exist_ok=True)
        (self.TEST_DIR / "src").mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()
        self.run_cli(
            [
                "--prj-base",
                str(self.TEST_DIR),
                "--enable",
                "codex",
            ]
        )

    def test_docs_check_all_present_succeeds(self) -> None:
        for name in ("REQUIREMENTS.md", "WORKFLOW.md", "REFERENCES.md"):
            (self.TEST_DIR / "docs" / name).write_text("doc\n", encoding="utf-8")
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            rc = cli.main(["--docs-check", "--prj-base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)

    def test_docs_check_missing_requirements(self) -> None:
        (self.TEST_DIR / "docs" / "WORKFLOW.md").write_text("doc\n", encoding="utf-8")
        (self.TEST_DIR / "docs" / "REFERENCES.md").write_text("doc\n", encoding="utf-8")
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            rc = cli.main(["--docs-check", "--prj-base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)
        self.assertIn("REQUIREMENTS.md", mock_stdout.getvalue())

    def test_docs_check_requires_prj_base(self) -> None:
        """SRS-396/SRS-405: --docs-check without --prj-base exits with code 1."""
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            rc = cli.main(["--docs-check"])
        self.assertEqual(rc, 1)
        self.assertIn("--prj-base", mock_stderr.getvalue())


class TestGitWtNameCommand(HomeIsolatedTestCase):
    """SRS-318/SRS-319/SRS-391: --git-wt-name uses --git-base."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-wt-name-"))
        make_git_repo(self.TEST_DIR)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def test_git_wt_name_format(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            ):
                rc = cli.main(["--git-wt-name", "--git-base", str(self.TEST_DIR)])
            self.assertEqual(rc, 0)
            value = mock_stdout.getvalue().strip()
        finally:
            os.chdir(prev_cwd)
        self.assertRegex(
            value,
            rf"useReq-{self.TEST_DIR.name}-master-\d{{14}}",
        )

    def test_git_wt_name_outside_git_repo_fails(self) -> None:
        non_git = Path(tempfile.mkdtemp(prefix="usereq-nongit-"))
        self.addCleanup(shutil.rmtree, non_git, ignore_errors=True)
        prev_cwd = Path.cwd()
        try:
            os.chdir(non_git)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-name", "--git-base", str(non_git)])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)


class TestGitWtCreateDeleteCommands(HomeIsolatedTestCase):
    """SRS-320..SRS-332/SRS-335/SRS-391: worktree create/delete with --git-base."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-wt-cd-"))
        make_git_repo(self.TEST_DIR)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        parent = self.TEST_DIR.parent
        self.addCleanup(
            subprocess.run,
            ["git", "worktree", "remove", "--force", str(parent / "wt-test-wt")]
            if (parent / "wt-test-wt").exists()
            else ["true"],
            capture_output=True,
        )

    def test_wt_create_invalid_name_fails(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-create", "bad/name", "--git-base", str(self.TEST_DIR)])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_failure_does_not_change_cwd(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                cli.main(["--git-wt-create", "in valid", "--git-base", str(self.TEST_DIR)])
            self.assertEqual(Path.cwd(), self.TEST_DIR)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_and_delete_roundtrip(self) -> None:
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-roundtrip-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-create", "usereq-roundtrip-wt", "--git-base", str(self.TEST_DIR), "--prj-base", str(self.TEST_DIR)])
            self.assertEqual(rc, 0)
            self.assertTrue(wt_path.is_dir())
            self.assertEqual(Path.cwd(), self.TEST_DIR)
            rc = cli.main(["--git-wt-delete", "usereq-roundtrip-wt", "--git-base", str(self.TEST_DIR)])
            self.assertEqual(rc, 0)
            self.assertFalse(wt_path.exists())
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", "usereq-roundtrip-wt"],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            os.chdir(prev_cwd)

    def test_wt_delete_rejects_partial_name_matches(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-create", "usereq-partial-full", "--git-base", str(self.TEST_DIR), "--prj-base", str(self.TEST_DIR)])
            self.assertEqual(rc, 0)
            rc = cli.main(["--git-wt-delete", "usereq-partial", "--git-base", str(self.TEST_DIR)])
            self.assertNotEqual(rc, 0)
        finally:
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "remove",
                    "--force",
                    str(self.TEST_DIR.parent / "usereq-partial-full"),
                ],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", "usereq-partial-full"],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            os.chdir(prev_cwd)

    def test_wt_delete_nonexistent_fails(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-delete", "does-not-exist", "--git-base", str(self.TEST_DIR)])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_requires_prj_base(self) -> None:
        """SRS-320/SRS-395/SRS-461: --git-wt-create without --prj-base exits non-zero."""
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-noprj-wt"
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
            ):
                rc = cli.main(
                    [
                        "--git-wt-create",
                        "usereq-noprj-wt",
                        "--git-base",
                        str(self.TEST_DIR),
                    ]
                )
            self.assertNotEqual(rc, 0)
            self.assertIn("--prj-base", mock_stderr.getvalue())
            self.assertFalse(wt_path.exists())
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_copies_venv_from_prj_base(self) -> None:
        """SRS-330/SRS-335: .venv is copied from --prj-base into the worktree."""
        prj_dir = Path(tempfile.mkdtemp(prefix="usereq-prj-venv-"))
        self.addCleanup(shutil.rmtree, prj_dir, ignore_errors=True)
        venv = prj_dir / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("cfg\n", encoding="utf-8")
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-venv-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(
                    [
                        "--git-wt-create",
                        "usereq-venv-wt",
                        "--git-base",
                        str(self.TEST_DIR),
                        "--prj-base",
                        str(prj_dir),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertTrue((wt_path / ".venv" / "pyvenv.cfg").exists())
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", "usereq-venv-wt"],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            os.chdir(prev_cwd)

    def test_wt_create_skips_copy_when_prj_venv_absent(self) -> None:
        """SRS-335: absent --prj-base/.venv skips the copy without error."""
        prj_dir = Path(tempfile.mkdtemp(prefix="usereq-prj-noven-"))
        self.addCleanup(shutil.rmtree, prj_dir, ignore_errors=True)
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-noven-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(
                    [
                        "--git-wt-create",
                        "usereq-noven-wt",
                        "--git-base",
                        str(self.TEST_DIR),
                        "--prj-base",
                        str(prj_dir),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertFalse((wt_path / ".venv").exists())
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", "usereq-noven-wt"],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            os.chdir(prev_cwd)

    def test_wt_create_never_copies_git_base_venv(self) -> None:
        """SRS-335/SRS-461: --git-base/.venv is never used as the .venv copy source."""
        git_venv = self.TEST_DIR / ".venv"
        git_venv.mkdir(exist_ok=True)
        (git_venv / "pyvenv.cfg").write_text("cfg\n", encoding="utf-8")
        prj_dir = Path(tempfile.mkdtemp(prefix="usereq-prj-nofb-"))
        self.addCleanup(shutil.rmtree, prj_dir, ignore_errors=True)
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-nofb-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(
                    [
                        "--git-wt-create",
                        "usereq-nofb-wt",
                        "--git-base",
                        str(self.TEST_DIR),
                        "--prj-base",
                        str(prj_dir),
                    ]
                )
            self.assertEqual(rc, 0)
            self.assertFalse((wt_path / ".venv").exists())
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt_path)],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-D", "usereq-nofb-wt"],
                cwd=str(self.TEST_DIR),
                capture_output=True,
            )
            os.chdir(prev_cwd)


class TestGitPathRemovedCommand(HomeIsolatedTestCase):
    """SRS-333/SRS-334/SRS-347: --git-path is removed legacy behavior and is not parsed."""

    def test_git_path_flag_is_not_parsed(self) -> None:
        """SRS-333/SRS-334: --git-path must be rejected by the parser."""
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            with self.assertRaises(SystemExit):
                cli.main(["--git-path", "--git-base", str(tempfile.gettempdir())])

    def test_git_path_get_base_path_is_not_parsed(self) -> None:
        """SRS-347: --get-base-path is no longer parsed."""
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            with self.assertRaises(SystemExit):
                cli.main(["--get-base-path"])


class TestStaticCheckConfig(HomeIsolatedTestCase):
    """SRS-248..SRS-252: static-check configuration persistence."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-scfg-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()
        self.base_argv = [
            "--prj-base",
            str(self.TEST_DIR),
        ]

    def test_enable_static_check_saved_to_global_config(self) -> None:
        rc = self.run_cli(
            self.base_argv
            + [
                "--enable",
                "codex",
                "--enable-static-check",
                "Python=Pylance",
            ]
        )
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            data["static-check"],
            {"Python": [{"module": "Pylance"}]},
        )

    def test_install_preserves_existing_static_check_entries(self) -> None:
        self.run_cli(
            self.base_argv
            + [
                "--enable",
                "codex",
                "--enable-static-check",
                "Python=Pylance",
            ]
        )
        rc = self.run_cli(
            [
                "--enable-static-check",
                "Python=Ruff",
                "install",
            ]
        )
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        modules = sorted(e["module"] for e in data["static-check"]["Python"])
        self.assertEqual(modules, ["Pylance", "Ruff"])

    def test_identity_duplicate_entries_discarded(self) -> None:
        rc = self.run_cli(
            self.base_argv
            + [
                "--enable",
                "codex",
                "--enable-static-check",
                "Python=Pylance",
                "--enable-static-check",
                "Python=Pylance",
            ]
        )
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["static-check"]["Python"]), 1)


class TestSetDirectoryCommands(HomeIsolatedTestCase):
    """SRS-396..SRS-401/SRS-406: directory configuration commands."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-setdirs-"))
        for sub in ("docs", "tests", "src", "app"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def read_config(self) -> dict:
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        return json.loads(config_path.read_text(encoding="utf-8"))

    def test_set_docs_dir_persists_value(self) -> None:
        rc = self.run_cli(
            ["--prj-base", str(self.TEST_DIR), "--set-docs-dir", "docs"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_config()["docs-dir"], "docs")

    def test_set_src_dir_persists_ordered_list(self) -> None:
        rc = self.run_cli(
            [
                "--prj-base",
                str(self.TEST_DIR),
                "--set-src-dir",
                "src",
                "--set-src-dir",
                "app",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_config()["src-dir"], ["src", "app"])

    def test_set_tests_dir_persists_value(self) -> None:
        rc = self.run_cli(
            ["--prj-base", str(self.TEST_DIR), "--set-tests-dir", "tests"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(self.read_config()["tests-dir"], "tests")

    def test_set_directory_preserves_unrelated_keys(self) -> None:
        """SRS-401: unrelated configuration keys survive a directory update."""
        self.run_cli(
            [
                "--prj-base",
                str(self.TEST_DIR),
                "--enable",
                "codex",
                "--enable-static-check",
                "Python=Pylance",
            ]
        )
        rc = self.run_cli(
            ["--prj-base", str(self.TEST_DIR), "--set-docs-dir", "docs"]
        )
        self.assertEqual(rc, 0)
        data = self.read_config()
        self.assertEqual(data["docs-dir"], "docs")
        self.assertEqual(data["providers"], ["codex"])
        self.assertEqual(data["static-check"], {"Python": [{"module": "Pylance"}]})

    def test_set_directory_requires_prj_base(self) -> None:
        """SRS-396/SRS-405: --set-docs-dir without --prj-base exits with code 1."""
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = self.run_cli(["--set-docs-dir", "docs"])
        self.assertEqual(rc, 1)
        self.assertIn("--prj-base", mock_stderr.getvalue())


class TestPrjBaseRequirements(HomeIsolatedTestCase):
    """SRS-396/SRS-405: project commands require --prj-base."""

    def test_install_is_independent_of_prj_base(self) -> None:
        """SRS-447/SRS-448/SRS-461: install neither accepts nor consumes --prj-base."""
        project_dir = Path(tempfile.mkdtemp(prefix="usereq-install-prj-"))
        self.addCleanup(shutil.rmtree, project_dir, ignore_errors=True)
        self.run_cli(["--enable", "codex"])
        with (
            patch("sys.stdout", new_callable=io.StringIO),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            rc = self.run_cli(["install"])
        self.assertEqual(rc, 0)
        with patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                self.run_cli(["install", "--prj-base", str(project_dir)])

    def test_references_requires_prj_base(self) -> None:
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = self.run_cli(["references"])
        self.assertEqual(rc, 1)
        self.assertIn("--prj-base", mock_stderr.getvalue())

    def test_files_tokens_requires_no_bases(self) -> None:
        """SRS-396/SRS-410: files-tokens runs without --prj-base or --git-base.

        expected_output: exit code 0 with neither base argument supplied.
        """
        project = Path(tempfile.mkdtemp(prefix="usereq-prj-"))
        self.addCleanup(shutil.rmtree, project, ignore_errors=True)
        target = project / "sample.py"
        target.write_text("x = 1\n", encoding="utf-8")
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            rc = cli.main(["files-tokens", str(target)])
        self.assertEqual(rc, 0)

    def test_legacy_analysis_flags_are_not_parsed(self) -> None:
        """SRS-409/SRS-412: legacy --prefixed analysis command forms are rejected."""
        for legacy in (
            ["--files-tokens", "f.py"],
            ["--files-references", "f.py"],
            ["--files-compress", "f.py"],
            ["--files-find", "FUNCTION", "x", "f.py"],
            ["--files-static-check", "f.py"],
            ["--tokens"],
            ["--references"],
            ["--compress"],
            ["--find", "FUNCTION", "x"],
            ["--static-check"],
        ):
            with (
                patch("sys.stderr", new_callable=io.StringIO),
                self.assertRaises(SystemExit),
            ):
                cli.main(legacy)

    def test_removed_directory_flags_are_not_parsed(self) -> None:
        """SRS-034: removed directory flags are rejected by the parser."""
        for flag in (
            "--docs-dir",
            "--src-dir",
            "--tests-dir",
            "--guidelines-dir",
            "--add-guidelines",
            "--upgrade-guidelines",
        ):
            with (
                patch("sys.stderr", new_callable=io.StringIO),
                self.assertRaises(SystemExit),
            ):
                cli.main([flag, "value"])

    def test_help_usage_line_is_accurate_and_concise(self) -> None:
        """Help accuracy defect: valid complete usage synopsis without superfluous content.

        expected_output: --help text whose usage line starts with 'usage: req [-h]',
        lists the parsed [--develop] [--dev] options, embeds no version marker,
        no duplicated per-language tag catalog, and no internal SRS identifiers.
        """
        # Arrange
        parser = cli.build_parser()
        version = cli.load_package_version()
        # Act
        with (
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            self.assertRaises(SystemExit),
        ):
            parser.parse_args(["--help"])
        help_text = mock_stdout.getvalue()
        usage_line = help_text.splitlines()[0]
        # Assert: usage synopsis is valid and complete
        self.assertTrue(usage_line.startswith("usage: req [-h]"), usage_line)
        self.assertIn("[--develop]", usage_line)
        self.assertIn("[--dev]", usage_line)
        self.assertNotIn(f"({version})", usage_line)
        # Assert: no superfluous inline-help content
        self.assertNotIn("Available tags:", help_text)
        self.assertNotIn("SRS-", help_text)


class TestUpgradeUninstall(unittest.TestCase):
    """SRS-343/SRS-344: uv upgrade and uninstall command composition."""

    def test_upgrade_on_non_linux_prints_manual_command(self) -> None:
        with (
            patch("usereq.cli.platform.system", return_value="Windows"),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            cli.run_upgrade()
        self.assertIn("uv tool install", mock_stdout.getvalue())

    def test_uninstall_on_non_linux_prints_manual_command(self) -> None:
        with (
            patch("usereq.cli.platform.system", return_value="Windows"),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            cli.run_uninstall()
        self.assertIn("uv tool uninstall", mock_stdout.getvalue())

    def test_upgrade_on_linux_executes_uv_install(self) -> None:
        with (
            patch("usereq.cli.platform.system", return_value="Linux"),
            patch("usereq.cli.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            cli.run_upgrade()
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        self.assertEqual(
            command,
            ["uv", "tool", "install", "cli-usereq"],
        )

    def test_upgrade_with_github_on_linux_executes_uv_install_from_git(self) -> None:
        """SRS-440/SRS-452: GitHub upgrade pins the latest release tag on the git source."""
        with (
            patch("usereq.cli.platform.system", return_value="Linux"),
            patch("usereq.cli.fetch_github_latest_version", return_value="v9.9.9"),
            patch("usereq.cli.subprocess.run") as mock_run,
        ):
            mock_run.return_value.returncode = 0
            cli.run_upgrade(use_github=True)
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        self.assertEqual(
            command,
            [
                "uv",
                "tool",
                "install",
                "cli-usereq",
                "--from",
                "git+https://github.com/Ogekuri/CLI-useReq.git@v9.9.9",
            ],
        )

    def test_uninstall_on_linux_executes_uv_uninstall(self) -> None:
        with (
            patch("usereq.cli.platform.system", return_value="Linux"),
            patch("usereq.cli.subprocess.run") as mock_run,
            patch(
                "usereq.cli.cleanup_release_check_idle_state_cache", autospec=True
            ),
        ):
            mock_run.return_value.returncode = 0
            cli.run_uninstall()
        command = mock_run.call_args[0][0]
        self.assertEqual(command[:3], ["uv", "tool", "uninstall"])


class TestProviderLifecycleCommands(HomeIsolatedTestCase):
    """SRS-275/SRS-276/SRS-279/SRS-413/SRS-422: provider configuration commands."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-lifecycle-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()

    def _read_config(self) -> dict:
        return json.loads(
            (self.HOME / ".config" / "usereq" / "config.json").read_text(
                encoding="utf-8"
            )
        )

    def test_enable_provider_is_config_only(self) -> None:
        """SRS-276: --enable persists config and installs nothing."""
        rc = self.run_cli(["--enable", "pi"])
        self.assertEqual(rc, 0)
        self.assertEqual(self._read_config()["providers"], ["pi"])
        self.assertFalse((self.HOME / ".pi" / "agent" / "skills").exists())

    def test_enable_provider_replaces_named_provider_only(self) -> None:
        """SRS-279: re-enabling replaces the named provider, preserving others."""
        self.run_cli(["--enable", "codex"])
        self.run_cli(["--enable", "pi", "--enable", "pi"])
        self.assertEqual(
            self._read_config()["providers"],
            ["codex", "pi"],
        )

    def test_disable_provider_removes_entries(self) -> None:
        """SRS-413: --disable removes the provider from the persisted array."""
        self.run_cli(
            ["--enable", "codex", "--enable", "pi"]
        )
        rc = self.run_cli(["--disable", "pi"])
        self.assertEqual(rc, 0)
        self.assertEqual(self._read_config()["providers"], ["codex"])

    def test_disable_provider_absent_entries_keeps_config(self) -> None:
        """SRS-413: disabling a provider without entries leaves the config unchanged."""
        self.run_cli(["--enable", "codex"])
        rc = self.run_cli(["--disable", "pi"])
        self.assertEqual(rc, 0)
        self.assertEqual(self._read_config()["providers"], ["codex"])

    def test_disable_provider_unknown_token_fails(self) -> None:
        """SRS-422: unknown provider token exits with code 1."""
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = self.run_cli(["--disable", "nope"])
        self.assertEqual(rc, 1)
        self.assertIn("unknown provider", mock_stderr.getvalue())

    def test_enable_provider_invalid_token_fails(self) -> None:
        """SRS-278: invalid provider token, including legacy SPEC forms, exits with code 1."""
        for token in ("pi:bogus", "pi:prompts,skills"):
            with patch("sys.stderr", new_callable=io.StringIO):
                rc = self.run_cli(["--enable", token])
            self.assertEqual(rc, 1)

    def test_legacy_provider_flag_is_not_parsed(self) -> None:
        """SRS-034: --provider, --enable-provider, and --disable-provider are removed legacy flags."""
        for legacy in (["--provider", "pi"], ["--enable-provider", "pi"], ["--disable-provider", "pi"]):
            with (
                patch("sys.stderr", new_callable=io.StringIO),
                self.assertRaises(SystemExit),
            ):
                cli.main(legacy)

    def test_install_requires_enabled_provider(self) -> None:
        """SRS-035: install without enabled providers exits with code 4."""
        with (
            patch("sys.stderr", new_callable=io.StringIO),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            rc = self.run_cli(["install"])
        self.assertEqual(rc, 4)


class TestStaticCheckLifecycleCommands(HomeIsolatedTestCase):
    """SRS-414/SRS-415/SRS-422: static-check configuration commands."""

    def _read_config(self) -> dict:
        return json.loads(
            (self.HOME / ".config" / "usereq" / "config.json").read_text(
                encoding="utf-8"
            )
        )

    def test_enable_static_check_config_only(self) -> None:
        """SRS-415: enable persists to config without --prj-base."""
        rc = self.run_cli(["--enable-static-check", "Python=Pylance"])
        self.assertEqual(rc, 0)
        self.assertEqual(
            self._read_config()["static-check"],
            {"Python": [{"module": "Pylance"}]},
        )

    def test_disable_static_check_exact_entry(self) -> None:
        """SRS-414: SPEC form removes only the identity-matching entry."""
        self.run_cli(
            [
                "--enable-static-check",
                "Python=Pylance",
                "--enable-static-check",
                "Python=Ruff",
            ]
        )
        rc = self.run_cli(["--disable-static-check", "Python=Pylance"])
        self.assertEqual(rc, 0)
        self.assertEqual(
            self._read_config()["static-check"],
            {"Python": [{"module": "Ruff"}]},
        )

    def test_disable_static_check_whole_language(self) -> None:
        """SRS-414: bare LANG removes the whole language key."""
        self.run_cli(
            ["--enable-static-check", "Python=Pylance", "--enable-static-check", "C=Dummy"]
        )
        rc = self.run_cli(["--disable-static-check", "Python"])
        self.assertEqual(rc, 0)
        self.assertEqual(self._read_config()["static-check"], {"C": [{"module": "Dummy"}]})

    def test_disable_static_check_unknown_language_fails(self) -> None:
        """SRS-422: unknown language token exits with code 1."""
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = self.run_cli(["--disable-static-check", "Klingon"])
        self.assertEqual(rc, 1)
        self.assertIn("unknown static-check language", mock_stderr.getvalue())


class TestAutoInstallLifecycle(HomeIsolatedTestCase):
    """SRS-420/SRS-421: auto-install configuration and post-upgrade behavior."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-autoinstall-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()

    def _read_config(self) -> dict:
        return json.loads(
            (self.HOME / ".config" / "usereq" / "config.json").read_text(
                encoding="utf-8"
            )
        )

    def test_auto_install_defaults_enabled(self) -> None:
        """SRS-420: auto-install is enabled when the config stores no entry."""
        self.assertTrue(cli.load_auto_install_enabled())

    def test_disable_and_enable_auto_install_persist(self) -> None:
        """SRS-420: flags persist the auto-install boolean."""
        rc = self.run_cli(["--disable-auto-install"])
        self.assertEqual(rc, 0)
        self.assertIs(self._read_config()["auto-install"], False)
        rc = self.run_cli(["--enable-auto-install"])
        self.assertEqual(rc, 0)
        self.assertIs(self._read_config()["auto-install"], True)

    def test_upgrade_auto_install_runs_install(self) -> None:
        """SRS-421: successful --upgrade with auto-install triggers the install flow."""
        self.run_cli(["--enable", "pi"])
        with (
            patch("usereq.cli.run_upgrade"),
            patch("usereq.cli.run_install") as mock_install,
        ):
            rc = cli.main(["--upgrade", "--prj-base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        mock_install.assert_called_once()

    def test_upgrade_auto_install_runs_without_prj_base(self) -> None:
        """SRS-421: successful --upgrade triggers auto-install without --prj-base."""
        self.run_cli(["--enable", "pi"])
        with (
            patch("usereq.cli.run_upgrade"),
            patch("usereq.cli.run_install") as mock_install,
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            rc = cli.main(["--upgrade"])
        self.assertEqual(rc, 0)
        mock_install.assert_called_once()

    def test_upgrade_auto_install_disabled_skips_install(self) -> None:
        """SRS-420/SRS-421: disabled auto-install skips the install flow."""
        self.run_cli(
            ["--enable", "pi", "--disable-auto-install"]
        )
        with (
            patch("usereq.cli.run_upgrade"),
            patch("usereq.cli.run_install") as mock_install,
        ):
            rc = cli.main(["--upgrade", "--prj-base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        mock_install.assert_not_called()


class TestShowInstallUninstallCommands(HomeIsolatedTestCase):
    """SRS-280/SRS-416/SRS-417/SRS-418/SRS-419/SRS-462/SRS-487/SRS-492: lifecycle subcommands."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-show-"))
        for sub in ("docs", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.seed_directory_config()

    def test_install_and_uninstall_roundtrip(self) -> None:
        """SRS-418/SRS-419: install creates skill artifacts, uninstall removes them."""
        self.run_cli(["--enable", "pi"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["install"])
        self.assertEqual(rc, 0)
        self.assertIn("Skills Installed", mock_stdout.getvalue())
        skills_root = self.HOME / ".pi" / "agent" / "skills"
        self.assertTrue(skills_root.is_dir())
        rc = self.run_cli(["uninstall"])
        self.assertEqual(rc, 0)
        self.assertFalse(skills_root.exists())

    def test_uninstall_without_config_fails(self) -> None:
        """SRS-419: uninstall requires the global configuration file."""
        (self.HOME / ".config" / "usereq" / "config.json").unlink()
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = self.run_cli(["uninstall"])
        self.assertEqual(rc, 11)
        self.assertIn("not found", mock_stderr.getvalue())

    def test_show_prints_configuration_and_status_tables(self) -> None:
        """SRS-416/SRS-417: show prints configuration, Providers, and Installation Status tables."""
        self.run_cli(
            [
                "--enable",
                "pi",
                "--enable-static-check",
                "Python=Ruff",
            ]
        )
        self.run_cli(["install"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["show"])
        self.assertEqual(rc, 0)
        output = mock_stdout.getvalue()
        for token in (
            "Active Configuration",
            "docs-dir",
            "tests-dir",
            "src-dir",
            "auto-install",
            "enabled",
            "Providers",
            "CLI",
            "Enabled",
            "Skills Path",
            "~/.pi/agent/skills",
            "Installation Status",
            "Type",
            "Name",
            "Installed",
            "OK",
            "Static Checks",
            "Ruff",
        ):
            self.assertIn(token, output)

    def test_show_providers_table_is_alphabetical_with_skills_path(self) -> None:
        """SRS-462/SRS-463/SRS-485/SRS-487/SRS-488: every configurable provider row."""
        self.run_cli(
            ["--enable", "pi", "--enable", "openclaw", "--enable", "codex"]
        )
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["show"])
        self.assertEqual(rc, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Providers", output)
        self.assertNotIn("Prompts", output)
        self.assertNotIn("Agents", output)
        for skills_path in (
            "~/.gemini/config/skills",
            "~/.claude/skills",
            "~/.codex/skills",
            "~/.copilot/skills",
            "~/.openclaw/workspace/skills",
            "~/.config/opencode/skills",
            "~/.pi/agent/skills",
        ):
            self.assertIn(skills_path, output)
        providers_table = output.split("Providers", 1)[1].split(
            "Installation Status", 1
        )[0]
        rows = [
            line
            for line in providers_table.splitlines()
            if line.startswith("\u2502 ")
        ]
        # Header row plus exactly every configurable provider (SRS-462).
        self.assertEqual(len(rows), 1 + len(EXPECTED_SKILL_ROOTS))
        header_cells = [cell.strip() for cell in rows[0].split("\u2502")[1:-1]]
        self.assertEqual(header_cells, ["CLI", "Enabled", "Skills Path"])
        expected_enabled = {
            "antigravity": "no",
            "claude": "no",
            "codex": "yes",
            "copilot": "no",
            "openclaw": "yes",
            "opencode": "no",
            "pi": "yes",
        }
        provider_rows = [row.split("\u2502")[1:-1] for row in rows[1:]]
        self.assertEqual(
            [cells[0].strip() for cells in provider_rows],
            sorted(EXPECTED_SKILL_ROOTS),
        )
        for cells in provider_rows:
            name = cells[0].strip()
            self.assertEqual(cells[1].strip(), expected_enabled[name])
            self.assertEqual(
                cells[2].strip(),
                "~/" + "/".join(EXPECTED_SKILL_ROOTS[name]),
            )

    def test_show_installation_status_single_table(self) -> None:
        """SRS-417/SRS-489/SRS-490/SRS-491/SRS-492: enabled-only Installation Status table."""
        self.run_cli(["--enable", "pi"])
        self.run_cli(["install"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["show"])
        self.assertEqual(rc, 0)
        output = mock_stdout.getvalue()
        self.assertEqual(output.count("Installation Status"), 1)
        status_section = output.split("Installation Status", 1)[1].split(
            "Static Checks", 1
        )[0]
        rows = [
            line
            for line in status_section.splitlines()
            if line.startswith("\u2502 ")
        ]
        self.assertEqual(
            [cell.strip() for cell in rows[0].split("\u2502")[1:-1]],
            ["Type", "Name", "CLI", "Enabled", "Installed"],
        )
        # Rows cover only the enabled provider `pi` (SRS-489).
        expected_pairs = {(prompt, "pi") for prompt in EXPECTED_PROMPTS}
        seen_pairs: set[tuple[str, str]] = set()
        row_order: list[tuple[str, str]] = []
        for row in rows[1:]:
            cells = [cell.strip() for cell in row.split("\u2502")[1:-1]]
            self.assertEqual(cells[0], "Skill")
            self.assertEqual(cells[2], "pi")
            self.assertEqual(cells[3], "yes")
            self.assertEqual(cells[4], "OK")
            pair = (cells[1][len("req-"):], cells[2])
            seen_pairs.add(pair)
            row_order.append(pair)
        self.assertEqual(seen_pairs, expected_pairs)
        self.assertEqual(row_order, sorted(row_order))
        for provider in sorted(set(EXPECTED_SKILL_ROOTS) - {"pi"}):
            self.assertNotIn(f"\u2502 {provider} ", status_section)

    def test_show_reports_not_installed_skills(self) -> None:
        """SRS-417/SRS-490: skills without artifacts are reported as MISSING."""
        self.run_cli(["--enable", "codex"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(["show"])
        self.assertEqual(rc, 0)
        self.assertIn("MISSING", mock_stdout.getvalue())

    def test_show_tolerates_legacy_persisted_provider_entries(self) -> None:
        """Defect: legacy persisted SPEC entries must not crash provider commands.

        expected_output: exit code 0 with the Providers table listing every
        configurable provider and only `pi` enabled, the legacy
        `antigravity:skills` entry ignored with an English stderr warning, and
        uninstall completing with exit code 0 (SRS-416, SRS-417, SRS-419,
        SRS-462, SRS-488, SRS-064).
        """
        # Arrange: seed a legacy SPEC entry persisted by the pre-1.20 CLI grammar.
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        data["providers"] = ["antigravity:skills", "pi"]
        config_path.write_text(json.dumps(data), encoding="utf-8")
        # Act: show must complete and render the Providers table.
        with (
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            rc = self.run_cli(["show"])
        # Assert: no crash; every provider renders and only `pi` is enabled.
        self.assertEqual(rc, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Skills Path", output)
        self.assertIn("~/.pi/agent/skills", output)
        antigravity_rows = [
            line
            for line in output.splitlines()
            if line.startswith("\u2502 antigravity ")
        ]
        self.assertTrue(antigravity_rows)
        self.assertIn("\u2502 no ", antigravity_rows[0])
        self.assertIn(
            "ignoring invalid persisted provider entry 'antigravity:skills'",
            mock_stderr.getvalue(),
        )
        # Act/Assert: uninstall shares the persisted-providers read path (SRS-419).
        self.run_cli(["install"])
        rc = self.run_cli(["uninstall"])
        self.assertEqual(rc, 0)
        self.assertFalse((self.HOME / ".pi" / "agent" / "skills").exists())


if __name__ == "__main__":
    unittest.main()
