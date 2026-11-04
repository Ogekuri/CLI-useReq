"""
Test suite for the useReq CLI command.

This module implements unit tests to verify the correct operation
of the CLI under the user-level installation architecture: prompts,
agents, and skills are installed into user-level CLI configuration
directories under the user HOME, and configuration is persisted in
the single user-global file `~/.config/usereq/config.json`.

Covers: SRS-026/027 (read-only prompts), SRS-034/035 (provider gating),
SRS-055/056 (uv runner), SRS-064 (update), SRS-249..252 (static-check
config), SRS-263 (read-only packaged prompts), SRS-275..280 (provider
specs), SRS-284..288 (test requirements), SRS-290/291/296 (install
table), SRS-342/352 (README), SRS-343/344 (upgrade/uninstall),
SRS-345..351 (release check helpers), SRS-359..363 (install defaults),
SRS-364..366 (spec grammar), SRS-368 (SKILL.md front matter),
SRS-371/374 (flowchart artifacts), SRS-381..390 (user-level install,
global config, model removal), SRS-391 (runtime git resolution).
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

ALL_PROVIDERS_ALL_ARTIFACTS = [
    "--provider",
    "antigravity:prompts,skills",
    "--provider",
    "claude:prompts,agents,skills",
    "--provider",
    "codex:prompts,skills",
    "--provider",
    "opencode:prompts,agents,skills",
    "--provider",
    "pi:prompts,skills",
]
"""Repeatable --provider specs that enable every provider with all artifact types."""

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


class TestUserLevelInstall(HomeIsolatedTestCase):
    """SRS-381..389: single install run with every provider and artifact."""

    @classmethod
    def setUpClass(cls) -> None:
        """Executes one installation for all assertion methods."""
        cls.CLASS_HOME = Path(tempfile.mkdtemp(prefix="usereq-install-home-"))
        cls.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-install-project-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (cls.TEST_DIR / sub).mkdir(exist_ok=True)
        (cls.TEST_DIR / "guidelines" / "sample.md").write_text(
            "guideline\n", encoding="utf-8"
        )
        cls.prompts_snapshot_before = {
            p.name: p.read_text(encoding="utf-8")
            for p in sorted((cli.RESOURCE_ROOT / "prompts").iterdir())
            if p.is_file() and not p.name.startswith(".")
        }
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            patch("usereq.cli.home_dir", return_value=cls.CLASS_HOME),
        ):
            cls.exit_code = cli.main(
                [
                    "--base",
                    str(cls.TEST_DIR),
                    "--docs-dir",
                    "docs",
                    "--guidelines-dir",
                    "guidelines",
                    "--tests-dir",
                    "tests",
                    "--src-dir",
                    "src",
                ]
                + ALL_PROVIDERS_ALL_ARTIFACTS
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
        for hidden in (".claude", ".codex", ".antigravity", ".pi", ".opencode"):
            self.assertFalse(
                (self.TEST_DIR / hidden).exists(),
                f"The project must not contain {hidden}",
            )

    def test_claude_user_level_directories_created(self) -> None:
        """SRS-382: claude artifacts are installed under ~/.claude."""
        self.assertTrue((self.HOME / ".claude" / "commands" / "req").is_dir())
        self.assertTrue((self.HOME / ".claude" / "agents").is_dir())
        self.assertTrue((self.HOME / ".claude" / "skills").is_dir())

    def test_codex_user_level_directories_created(self) -> None:
        """SRS-383: codex artifacts are installed under ~/.codex."""
        self.assertTrue((self.HOME / ".codex" / "prompts").is_dir())
        self.assertTrue((self.HOME / ".codex" / "skills").is_dir())

    def test_antigravity_user_level_directories_created(self) -> None:
        """SRS-384: antigravity artifacts are installed under ~/.antigravity."""
        self.assertTrue((self.HOME / ".antigravity" / "commands" / "req").is_dir())
        self.assertTrue((self.HOME / ".antigravity" / "skills").is_dir())

    def test_opencode_user_level_directories_created(self) -> None:
        """SRS-385: opencode artifacts are installed under ~/.config/opencode."""
        self.assertTrue((self.HOME / ".config" / "opencode" / "command").is_dir())
        self.assertTrue((self.HOME / ".config" / "opencode" / "agent").is_dir())
        self.assertTrue((self.HOME / ".config" / "opencode" / "skill").is_dir())

    def test_pi_user_level_directories_created(self) -> None:
        """SRS-386: pi artifacts are installed under ~/.pi/agent."""
        self.assertTrue((self.HOME / ".pi" / "agent" / "prompts").is_dir())
        self.assertTrue((self.HOME / ".pi" / "agent" / "skills").is_dir())

    def test_codex_prompt_files_created(self) -> None:
        """Codex prompts are created as req-<name>.md under ~/.codex/prompts."""
        prompts_dir = self.HOME / ".codex" / "prompts"
        for prompt in EXPECTED_PROMPTS:
            target = prompts_dir / f"req-{prompt}.md"
            self.assertTrue(target.exists(), f"Missing codex prompt {target}")

    def test_prompt_arguments_substituted(self) -> None:
        """%%ARGS%% is substituted with $ARGUMENTS in generated prompts."""
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
        command = self.HOME / ".claude" / "commands" / "req" / f"{prompt}.md"
        content = command.read_text(encoding="utf-8")
        self.assertIn("$ARGUMENTS", content)
        self.assertNotIn("%%ARGS%%", content)

    def test_claude_command_files_created(self) -> None:
        """Claude commands are created as <name>.md under ~/.claude/commands/req."""
        commands_dir = self.HOME / ".claude" / "commands" / "req"
        for prompt in EXPECTED_PROMPTS:
            target = commands_dir / f"{prompt}.md"
            self.assertTrue(target.exists(), f"Missing claude command {target}")

    def test_antigravity_toml_files_created(self) -> None:
        """Antigravity TOML commands are created under ~/.antigravity/commands/req."""
        toml_dir = self.HOME / ".antigravity" / "commands" / "req"
        for prompt in EXPECTED_PROMPTS:
            target = toml_dir / f"{prompt}.toml"
            self.assertTrue(target.exists(), f"Missing antigravity toml {target}")
            content = target.read_text(encoding="utf-8")
            self.assertIn("prompt", content)

    def test_pi_prompt_files_created(self) -> None:
        """SRS-353: pi prompts use req-<name>.prompt.md under ~/.pi/agent/prompts."""
        prompts_dir = self.HOME / ".pi" / "agent" / "prompts"
        for prompt in EXPECTED_PROMPTS:
            target = prompts_dir / f"req-{prompt}.prompt.md"
            self.assertTrue(target.exists(), f"Missing pi prompt {target}")
            content = target.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), "pi prompt must have front matter")
            self.assertIn("description:", content)

    def test_skill_files_created_for_every_provider(self) -> None:
        """Skills are created as req-<name>/SKILL.md for every enabled provider."""
        skill_roots = {
            "antigravity": self.HOME / ".antigravity" / "skills",
            "claude": self.HOME / ".claude" / "skills",
            "codex": self.HOME / ".codex" / "skills",
            "opencode": self.HOME / ".config" / "opencode" / "skill",
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

    def test_prompts_have_no_model_or_tools_fields(self) -> None:
        """SRS-389: generated agents and commands contain no model/tools fields."""
        agent = self.HOME / ".claude" / "agents" / f"req-{EXPECTED_PROMPTS[0]}.md"
        command = self.HOME / ".claude" / "commands" / "req" / f"{EXPECTED_PROMPTS[0]}.md"
        for artifact in (agent, command):
            content = artifact.read_text(encoding="utf-8")
            self.assertNotIn("model:", content)
            self.assertNotIn("tools:", content)
            self.assertNotIn("allowed-tools:", content)

    def test_global_config_saved_with_canonical_keys(self) -> None:
        """SRS-287/SRS-288: single global config file with canonical keys only."""
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        self.assertTrue(config_path.is_file())
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(data.keys()),
            sorted(
                [
                    "guidelines-dir",
                    "docs-dir",
                    "tests-dir",
                    "src-dir",
                    "providers",
                ]
            ),
        )
        self.assertEqual(data["guidelines-dir"], "guidelines")
        self.assertEqual(data["docs-dir"], "docs")
        self.assertEqual(data["tests-dir"], "tests")
        self.assertEqual(data["src-dir"], ["src"])
        self.assertIsInstance(data["providers"], list)

    def test_flowchart_resources_created(self) -> None:
        """SRS-371/SRS-374: req-flowchart artifacts are emitted when bundled."""
        if "flowchart" not in EXPECTED_PROMPTS:
            self.skipTest("flowchart.md template not bundled")
        self.assertTrue(
            (self.HOME / ".claude" / "commands" / "req" / "flowchart.md").exists()
        )
        self.assertTrue(
            (
                self.HOME / ".pi" / "agent" / "prompts" / "req-flowchart.prompt.md"
            ).exists()
        )
        self.assertTrue(
            (
                self.HOME / ".codex" / "skills" / "req-flowchart" / "SKILL.md"
            ).exists()
        )
        self.assertTrue(
            (self.HOME / ".antigravity" / "commands" / "req" / "flowchart.toml").exists()
        )

    def test_guidelines_tokens_replaced(self) -> None:
        """%%GUIDELINES_PATH%% and %%GUIDELINES_FILES%% are substituted."""
        command = self.HOME / ".claude" / "commands" / "req" / "write.md"
        content = command.read_text(encoding="utf-8")
        self.assertNotIn("%%GUIDELINES_PATH%%", content)
        self.assertNotIn("%%GUIDELINES_FILES%%", content)


class TestProviderSpecParsing(unittest.TestCase):
    """SRS-275/278/364/365: --provider SPEC grammar and validation."""

    def test_valid_provider_spec_accepted(self) -> None:
        provider, artifacts, options = cli.parse_provider_spec("codex:prompts,skills")
        self.assertEqual(provider, "codex")
        self.assertEqual([a for a, _ in artifacts], ["prompts", "skills"])
        self.assertEqual(options, [])

    def test_valid_provider_spec_with_options_accepted(self) -> None:
        provider, _artifacts, options = cli.parse_provider_spec(
            "claude:prompts:prompts-use-agents"
        )
        self.assertEqual(provider, "claude")
        self.assertEqual(options, ["prompts-use-agents"])

    def test_pi_provider_spec_accepted(self) -> None:
        provider, artifacts, _ = cli.parse_provider_spec("pi:prompts,skills")
        self.assertEqual(provider, "pi")
        self.assertEqual(len(artifacts), 2)

    def test_removed_providers_rejected(self) -> None:
        """SRS-364: gemini, github, and kiro are no longer valid providers."""
        for provider in ("gemini", "github", "kiro"):
            with self.assertRaises(cli.ReqError):
                cli.parse_provider_spec(f"{provider}:prompts")

    def test_unknown_provider_rejected(self) -> None:
        with self.assertRaises(cli.ReqError):
            cli.parse_provider_spec("unknown:prompts")

    def test_unknown_artifact_rejected(self) -> None:
        with self.assertRaises(cli.ReqError):
            cli.parse_provider_spec("codex:widgets")

    def test_artifact_option_suffix_rejected(self) -> None:
        """SRS-364: artifact items must be bare artifacts; option suffixes are invalid."""
        for spec in (
            "codex:prompts+enable-models",
            "claude:skills+enable-tools",
            "opencode:prompts+enable-models+enable-tools",
        ):
            with self.assertRaises(cli.ReqError):
                cli.parse_provider_spec(spec)

    def test_unknown_option_rejected(self) -> None:
        with self.assertRaises(cli.ReqError):
            cli.parse_provider_spec("codex:prompts:legacy")

    def test_missing_artifacts_rejected(self) -> None:
        with self.assertRaises(cli.ReqError):
            cli.parse_provider_spec("codex:")


class TestProviderSpecMultiple(HomeIsolatedTestCase):
    """SRS-276: multiple --provider specs activate independently."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-multi-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def install(self, *specs: str) -> int:
        argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]
        for spec in specs:
            argv.extend(["--provider", spec])
        return self.run_cli(argv)

    def test_exit_code_zero(self) -> None:
        self.assertEqual(
            self.install("codex:skills", "claude:prompts,agents", "pi:prompts,skills"),
            0,
        )

    def test_codex_skills_created_prompts_not_created(self) -> None:
        self.install("codex:skills")
        self.assertTrue(
            (self.HOME / ".codex" / "skills" / f"req-{EXPECTED_PROMPTS[0]}").is_dir()
        )
        self.assertFalse((self.HOME / ".codex" / "prompts").exists())

    def test_claude_agents_created_prompts_not_created(self) -> None:
        self.install("claude:agents")
        self.assertTrue(
            (self.HOME / ".claude" / "agents" / f"req-{EXPECTED_PROMPTS[0]}.md").exists()
        )
        self.assertFalse((self.HOME / ".claude" / "commands").exists())

    def test_disabled_providers_absent(self) -> None:
        self.install("codex:prompts")
        for provider_dir in (".claude", ".antigravity", ".pi"):
            self.assertFalse((self.HOME / provider_dir).exists())

    def test_at_least_one_provider_spec_required(self) -> None:
        """SRS-035: installation without --provider specs fails with exit code 4."""
        rc = self.run_cli(
            [
                "--base",
                str(self.TEST_DIR),
                "--docs-dir",
                "docs",
                "--guidelines-dir",
                "guidelines",
                "--tests-dir",
                "tests",
                "--src-dir",
                "src",
            ]
        )
        self.assertEqual(rc, 4)


class TestProviderSpecPersistence(HomeIsolatedTestCase):
    """SRS-279/SRS-280/SRS-286: provider spec persistence round-trips."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-persist-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.base_argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]

    def test_provider_specs_persisted_to_global_config(self) -> None:
        self.run_cli(self.base_argv + ["--provider", "pi:prompts,skills"])
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["providers"], ["pi:prompts,skills"])

    def test_provider_specs_restored_on_update(self) -> None:
        """SRS-280: --update without --provider reuses persisted specs."""
        self.run_cli(self.base_argv + ["--provider", "codex:prompts"])
        shutil.rmtree(self.HOME / ".codex")
        rc = self.run_cli(["--update", "--base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        self.assertTrue(
            (self.HOME / ".codex" / "prompts" / f"req-{EXPECTED_PROMPTS[0]}.md").exists()
        )

    def test_cli_provider_replaces_persisted_on_update(self) -> None:
        """SRS-280: CLI --provider specs replace persisted entries."""
        self.run_cli(self.base_argv + ["--provider", "codex:prompts"])
        rc = self.run_cli(
            ["--update", "--base", str(self.TEST_DIR), "--provider", "claude:prompts"]
        )
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["providers"], ["claude:prompts"])


class TestPromptsUseAgents(HomeIsolatedTestCase):
    """SRS-276/SRS-287: provider-scoped prompts-use-agents option."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-agents-stub-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.base_argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]

    def test_claude_commands_are_agent_stubs(self) -> None:
        self.run_cli(
            self.base_argv + ["--provider", "claude:prompts:prompts-use-agents"]
        )
        command = self.HOME / ".claude" / "commands" / "req" / "write.md"
        content = command.read_text(encoding="utf-8")
        self.assertIn("agent: req-write", content)
        self.assertNotIn("model:", content)
        self.assertNotIn("tools:", content)

    def test_opencode_commands_are_agent_stubs(self) -> None:
        self.run_cli(
            self.base_argv + ["--provider", "opencode:prompts:prompts-use-agents"]
        )
        command = self.HOME / ".config" / "opencode" / "command" / "req-write.md"
        content = command.read_text(encoding="utf-8")
        self.assertIn("agent: req-write", content)

    def test_pi_prompts_are_agent_stubs(self) -> None:
        self.run_cli(self.base_argv + ["--provider", "pi:prompts:prompts-use-agents"])
        prompt = self.HOME / ".pi" / "agent" / "prompts" / "req-write.prompt.md"
        content = prompt.read_text(encoding="utf-8")
        self.assertIn("agent: req-write", content)

    def test_option_applies_independently_per_provider(self) -> None:
        """SRS-287: prompts-use-agents applies only to the targeted provider."""
        self.run_cli(
            self.base_argv
            + [
                "--provider",
                "claude:prompts:prompts-use-agents",
                "--provider",
                "opencode:prompts",
            ]
        )
        claude_command = self.HOME / ".claude" / "commands" / "req" / "write.md"
        self.assertIn(
            "agent: req-write", claude_command.read_text(encoding="utf-8")
        )
        opencode_command = (
            self.HOME / ".config" / "opencode" / "command" / "req-write.md"
        )
        self.assertNotIn(
            "agent: req-write", opencode_command.read_text(encoding="utf-8")
        )


class TestInstallDefaultDirectories(HomeIsolatedTestCase):
    """SRS-359..SRS-363: fresh-install defaults and directory creation."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-defaults-"))
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def test_install_uses_default_directories_when_cli_flags_omitted(self) -> None:
        rc = self.run_cli(["--base", str(self.TEST_DIR), "--provider", "codex:prompts"])
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["docs-dir"], "req/docs")
        self.assertEqual(data["guidelines-dir"], "req/guidelines/")
        self.assertEqual(data["tests-dir"], "tests/")
        self.assertEqual(data["src-dir"], ["src/"])

    def test_install_creates_missing_parent_directories(self) -> None:
        rc = self.run_cli(["--base", str(self.TEST_DIR), "--provider", "codex:prompts"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.TEST_DIR / "req" / "docs").is_dir())
        self.assertTrue((self.TEST_DIR / "req" / "guidelines").is_dir())
        self.assertTrue((self.TEST_DIR / "tests").is_dir())
        self.assertTrue((self.TEST_DIR / "src").is_dir())

    def test_update_keeps_configured_directories(self) -> None:
        self.run_cli(
            [
                "--base",
                str(self.TEST_DIR),
                "--docs-dir",
                "docs",
                "--guidelines-dir",
                "guidelines",
                "--tests-dir",
                "tests",
                "--src-dir",
                "src",
                "--provider",
                "codex:prompts",
            ]
        )
        rc = self.run_cli(["--update", "--base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        config_path = self.HOME / ".config" / "usereq" / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(data["docs-dir"], "docs")


class TestGuidelinesTemplates(HomeIsolatedTestCase):
    """Guidelines template copy flows (--add-guidelines / --upgrade-guidelines)."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-guidelines-"))
        (self.TEST_DIR / "guidelines").mkdir(exist_ok=True)
        (self.TEST_DIR / "docs").mkdir(exist_ok=True)
        (self.TEST_DIR / "tests").mkdir(exist_ok=True)
        (self.TEST_DIR / "src").mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        # Synthetic guidelines template source so tests never touch packaged resources.
        self.RESOURCE_ROOT = Path(tempfile.mkdtemp(prefix="usereq-resroot-"))
        (self.RESOURCE_ROOT / "guidelines").mkdir()
        (self.RESOURCE_ROOT / "prompts").mkdir()
        (self.RESOURCE_ROOT / "docs").mkdir()
        template = self.RESOURCE_ROOT / "guidelines" / "existing.md"
        template.write_text("template\n", encoding="utf-8")
        (
            self.RESOURCE_ROOT
            / "docs"
            / "Requirements_Template.md"
        ).write_text("template\n", encoding="utf-8")
        self.addCleanup(shutil.rmtree, self.RESOURCE_ROOT, ignore_errors=True)
        root_patcher = patch.object(cli, "RESOURCE_ROOT", self.RESOURCE_ROOT)
        root_patcher.start()
        self.addCleanup(root_patcher.stop)
        self.base_argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]

    def test_add_guidelines_preserves_existing(self) -> None:
        existing = self.TEST_DIR / "guidelines" / "existing.md"
        existing.write_text("existing\n", encoding="utf-8")
        rc = self.run_cli(
            self.base_argv + ["--add-guidelines", "--provider", "codex:prompts"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(existing.read_text(encoding="utf-8"), "existing\n")

    def test_upgrade_guidelines_overwrites_existing(self) -> None:
        existing = self.TEST_DIR / "guidelines" / "existing.md"
        existing.write_text("existing\n", encoding="utf-8")
        rc = self.run_cli(
            self.base_argv + ["--upgrade-guidelines", "--provider", "codex:prompts"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(existing.read_text(encoding="utf-8"), "template\n")

    def test_add_guidelines_copies_missing_templates(self) -> None:
        rc = self.run_cli(
            self.base_argv + ["--add-guidelines", "--provider", "codex:prompts"]
        )
        self.assertEqual(rc, 0)
        self.assertEqual(
            (self.TEST_DIR / "guidelines" / "existing.md").read_text(
                encoding="utf-8"
            ),
            "template\n",
        )

    def test_no_copy_without_flags(self) -> None:
        rc = self.run_cli(self.base_argv + ["--provider", "codex:prompts"])
        self.assertEqual(rc, 0)
        self.assertEqual(list((self.TEST_DIR / "guidelines").iterdir()), [])


class TestRemoveCommand(HomeIsolatedTestCase):
    """SRS-390: --remove deletes req-* artifacts from user-level directories."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-remove-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        rc = self.run_cli(
            [
                "--base",
                str(self.TEST_DIR),
                "--docs-dir",
                "docs",
                "--guidelines-dir",
                "guidelines",
                "--tests-dir",
                "tests",
                "--src-dir",
                "src",
                "--provider",
                "claude:prompts,skills",
                "--provider",
                "codex:prompts,skills",
            ]
        )
        self.assertEqual(rc, 0)

    def test_remove_deletes_req_artifacts(self) -> None:
        rc = self.run_cli(["--remove", "--base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        self.assertFalse(
            (self.HOME / ".claude" / "commands" / "req" / "write.md").exists()
        )
        self.assertFalse(
            (self.HOME / ".claude" / "skills" / "req-write").exists()
        )
        self.assertFalse(
            (self.HOME / ".codex" / "prompts" / "req-write.md").exists()
        )
        self.assertFalse(
            (self.HOME / ".codex" / "skills" / "req-write").exists()
        )

    def test_remove_preserves_unrelated_user_content(self) -> None:
        unrelated = self.HOME / ".claude" / "commands" / "user-command.md"
        unrelated.parent.mkdir(parents=True, exist_ok=True)
        unrelated.write_text("user\n", encoding="utf-8")
        unrelated_skill = self.HOME / ".claude" / "skills" / "user-skill"
        unrelated_skill.mkdir(parents=True, exist_ok=True)
        (unrelated_skill / "SKILL.md").write_text("user\n", encoding="utf-8")
        rc = self.run_cli(["--remove", "--base", str(self.TEST_DIR)])
        self.assertEqual(rc, 0)
        self.assertTrue(unrelated.exists())
        self.assertTrue((unrelated_skill / "SKILL.md").exists())

    def test_remove_without_global_config_fails(self) -> None:
        (self.HOME / ".config" / "usereq" / "config.json").unlink()
        rc = self.run_cli(["--remove", "--base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)


class TestInstallationSummaryTable(HomeIsolatedTestCase):
    """SRS-290/291/296: installation summary table rendering."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-table-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def capture_install(self, *specs: str) -> str:
        argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]
        for spec in specs:
            argv.extend(["--provider", spec])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            rc = self.run_cli(argv)
        self.assertEqual(rc, 0)
        return mock_stdout.getvalue()

    def test_table_renders_provider_and_module_rows(self) -> None:
        output = self.capture_install("codex:prompts,skills")
        self.assertIn("codex", output)
        self.assertIn("prompts", output)
        self.assertIn("skills", output)

    def test_table_modules_reflect_provider_options(self) -> None:
        output = self.capture_install("claude:prompts:prompts-use-agents")
        self.assertIn("prompts:prompts-use-agents", output)

    def test_table_wraps_prompts_column(self) -> None:
        output = self.capture_install("codex:prompts,skills", "claude:prompts")
        lines = [
            line
            for line in output.splitlines()
            if "│" in line
        ]
        self.assertTrue(lines, "Installation table must be rendered")


class TestUserLevelPathHelpers(unittest.TestCase):
    """SRS-381..SRS-387: user-level path resolution helpers."""

    def test_get_global_config_path_under_home(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            path = cli.get_global_config_path()
        self.assertEqual(
            path, Path("/tmp/testhome/.config/usereq/config.json")
        )

    def test_provider_artifact_root_claude(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_artifact_root("claude", "prompts"),
                Path("/tmp/testhome/.claude/commands/req"),
            )
            self.assertEqual(
                cli.provider_artifact_root("claude", "agents"),
                Path("/tmp/testhome/.claude/agents"),
            )
            self.assertEqual(
                cli.provider_artifact_root("claude", "skills"),
                Path("/tmp/testhome/.claude/skills"),
            )

    def test_provider_artifact_root_codex(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_artifact_root("codex", "prompts"),
                Path("/tmp/testhome/.codex/prompts"),
            )

    def test_provider_artifact_root_antigravity(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_artifact_root("antigravity", "prompts"),
                Path("/tmp/testhome/.antigravity/commands/req"),
            )

    def test_provider_artifact_root_opencode(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_artifact_root("opencode", "agents"),
                Path("/tmp/testhome/.config/opencode/agent"),
            )

    def test_provider_artifact_root_pi(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            self.assertEqual(
                cli.provider_artifact_root("pi", "skills"),
                Path("/tmp/testhome/.pi/agent/skills"),
            )

    def test_unsupported_artifact_raises(self) -> None:
        with patch("usereq.cli.home_dir", return_value=Path("/tmp/testhome")):
            with self.assertRaises(cli.ReqError):
                cli.provider_artifact_root("codex", "agents")


class TestGitCheckCommand(HomeIsolatedTestCase):
    """SRS-311/SRS-312/SRS-391: --git-check with runtime git resolution."""

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
                rc = cli.main(["--git-check"])
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
                rc = cli.main(["--git-check"])
            self.assertNotEqual(rc, 0)
            self.assertEqual(
                mock_stderr.getvalue().strip(), "ERROR: Git status unclear!"
            )
        finally:
            os.chdir(prev_cwd)

    def test_git_check_rejects_base(self) -> None:
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            rc = cli.main(["--git-check", "--base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)

    def test_git_check_outside_git_repo_fails(self) -> None:
        non_git = Path(tempfile.mkdtemp(prefix="usereq-nongit-"))
        self.addCleanup(shutil.rmtree, non_git, ignore_errors=True)
        prev_cwd = Path.cwd()
        try:
            os.chdir(non_git)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-check"])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)


class TestDocsCheckCommand(HomeIsolatedTestCase):
    """SRS-313..SRS-317: --docs-check uses docs-dir from the global configuration."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-docs-check-"))
        (self.TEST_DIR / "docs").mkdir(exist_ok=True)
        (self.TEST_DIR / "guidelines").mkdir(exist_ok=True)
        (self.TEST_DIR / "tests").mkdir(exist_ok=True)
        (self.TEST_DIR / "src").mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.run_cli(
            [
                "--base",
                str(self.TEST_DIR),
                "--docs-dir",
                "docs",
                "--guidelines-dir",
                "guidelines",
                "--tests-dir",
                "tests",
                "--src-dir",
                "src",
                "--provider",
                "codex:prompts",
            ]
        )

    def test_docs_check_all_present_succeeds(self) -> None:
        for name in ("REQUIREMENTS.md", "WORKFLOW.md", "REFERENCES.md"):
            (self.TEST_DIR / "docs" / name).write_text("doc\n", encoding="utf-8")
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--docs-check"])
            self.assertEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)

    def test_docs_check_missing_requirements(self) -> None:
        (self.TEST_DIR / "docs" / "WORKFLOW.md").write_text("doc\n", encoding="utf-8")
        (self.TEST_DIR / "docs" / "REFERENCES.md").write_text("doc\n", encoding="utf-8")
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            ):
                rc = cli.main(["--docs-check"])
            self.assertNotEqual(rc, 0)
            self.assertIn("REQUIREMENTS.md", mock_stdout.getvalue())
        finally:
            os.chdir(prev_cwd)

    def test_docs_check_rejects_base(self) -> None:
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            rc = cli.main(["--docs-check", "--base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)


class TestGitWtNameCommand(HomeIsolatedTestCase):
    """SRS-318/SRS-319/SRS-391: --git-wt-name uses runtime git root."""

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
                rc = cli.main(["--git-wt-name"])
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
                rc = cli.main(["--git-wt-name"])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)


class TestGitWtCreateDeleteCommands(HomeIsolatedTestCase):
    """SRS-320..SRS-332/SRS-335/SRS-391: worktree create/delete commands."""

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
                rc = cli.main(["--git-wt-create", "bad/name"])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_failure_does_not_change_cwd(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                cli.main(["--git-wt-create", "in valid"])
            self.assertEqual(Path.cwd(), self.TEST_DIR)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_and_delete_roundtrip(self) -> None:
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-roundtrip-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-create", "usereq-roundtrip-wt"])
            self.assertEqual(rc, 0)
            self.assertTrue(wt_path.is_dir())
            self.assertEqual(Path.cwd(), self.TEST_DIR)
            rc = cli.main(["--git-wt-delete", "usereq-roundtrip-wt"])
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
                rc = cli.main(["--git-wt-create", "usereq-partial-full"])
            self.assertEqual(rc, 0)
            rc = cli.main(["--git-wt-delete", "usereq-partial"])
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
                rc = cli.main(["--git-wt-delete", "does-not-exist"])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)

    def test_wt_create_copies_venv_when_present(self) -> None:
        venv = self.TEST_DIR / ".venv"
        venv.mkdir(exist_ok=True)
        (venv / "pyvenv.cfg").write_text("cfg\n", encoding="utf-8")
        prev_cwd = Path.cwd()
        wt_path = self.TEST_DIR.parent / "usereq-venv-wt"
        try:
            os.chdir(self.TEST_DIR)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-wt-create", "usereq-venv-wt"])
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


class TestGitRepositoryPathCommands(HomeIsolatedTestCase):
    """SRS-333/SRS-334/SRS-347/SRS-391: runtime path resolution commands."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-gitpath-"))
        make_git_repo(self.TEST_DIR)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)

    def test_git_path_prints_runtime_git_root(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            ):
                rc = cli.main(["--git-path"])
            self.assertEqual(rc, 0)
            self.assertEqual(mock_stdout.getvalue().strip(), str(self.TEST_DIR))
        finally:
            os.chdir(prev_cwd)

    def test_get_base_path_prints_cwd(self) -> None:
        prev_cwd = Path.cwd()
        try:
            os.chdir(self.TEST_DIR)
            with (
                patch("usereq.cli.maybe_notify_newer_version", autospec=True),
                patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            ):
                rc = cli.main(["--get-base-path"])
            self.assertEqual(rc, 0)
            self.assertEqual(mock_stdout.getvalue().strip(), str(self.TEST_DIR))
        finally:
            os.chdir(prev_cwd)

    def test_git_path_rejects_base(self) -> None:
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            rc = cli.main(["--git-path", "--base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)

    def test_get_base_path_rejects_base(self) -> None:
        with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
            rc = cli.main(["--get-base-path", "--base", str(self.TEST_DIR)])
        self.assertNotEqual(rc, 0)

    def test_git_path_outside_git_repo_fails(self) -> None:
        non_git = Path(tempfile.mkdtemp(prefix="usereq-nongit-"))
        self.addCleanup(shutil.rmtree, non_git, ignore_errors=True)
        prev_cwd = Path.cwd()
        try:
            os.chdir(non_git)
            with patch("usereq.cli.maybe_notify_newer_version", autospec=True):
                rc = cli.main(["--git-path"])
            self.assertNotEqual(rc, 0)
        finally:
            os.chdir(prev_cwd)


class TestStaticCheckConfig(HomeIsolatedTestCase):
    """SRS-248..SRS-252: static-check configuration persistence."""

    def setUp(self) -> None:
        super().setUp()
        self.TEST_DIR = Path(tempfile.mkdtemp(prefix="usereq-scfg-"))
        for sub in ("docs", "guidelines", "tests", "src"):
            (self.TEST_DIR / sub).mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.TEST_DIR, ignore_errors=True)
        self.base_argv = [
            "--base",
            str(self.TEST_DIR),
            "--docs-dir",
            "docs",
            "--guidelines-dir",
            "guidelines",
            "--tests-dir",
            "tests",
            "--src-dir",
            "src",
        ]

    def test_enable_static_check_saved_to_global_config(self) -> None:
        rc = self.run_cli(
            self.base_argv
            + [
                "--provider",
                "codex:prompts",
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

    def test_update_preserves_existing_static_check_entries(self) -> None:
        self.run_cli(
            self.base_argv
            + [
                "--provider",
                "codex:prompts",
                "--enable-static-check",
                "Python=Pylance",
            ]
        )
        rc = self.run_cli(
            [
                "--update",
                "--base",
                str(self.TEST_DIR),
                "--enable-static-check",
                "Python=Ruff",
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
                "--provider",
                "codex:prompts",
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
        self.assertEqual(command[:4], ["uv", "tool", "install", "usereq"])

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


if __name__ == "__main__":
    unittest.main()
