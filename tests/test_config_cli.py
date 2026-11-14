"""!
@file test_config_cli.py
@brief Unit tests for the configuration CLI, tree renderer, and schema operations.
@details Covers exact renderer output, structural tree invariants, rectangular table
alignment, and command behavior of `--print`, `--info`, `--print-raw`, `--get`,
`--set`, and `--unset` (SRS-543, SRS-544, SRS-545).
"""

from __future__ import annotations

import io
import json
import shutil
import stat
import tempfile
import unicodedata
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from usereq import cli
from usereq import config_cli
from usereq.config_cli import RenderNode, format_table, render_text


TREE_MARKERS = ("├── ", "└── ")
PREFIX_SEGMENTS = ("│   ", "    ")
TABLE_CHARS = "│┬┼┴┌┐├┤└┘"


def display_width(text: str) -> int:
    """! @brief Measure terminal display width independently of production code. """
    total = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        total += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return total


def split_prefix(line: str) -> tuple[list[str], str]:
    """! @brief Split leading four-character tree prefix segments from a line. """
    segments: list[str] = []
    rest = line
    while rest.startswith("│   ") or rest.startswith("    "):
        segments.append(rest[:4])
        rest = rest[4:]
    return segments, rest


def validate_tree_structure(lines: list[str], root_details: bool = False) -> None:
    """!
    @brief Assert tree topology invariants over rendered output.
    @param lines {list[str]} Rendered output lines; the first line is the display root heading.
    @param root_details {bool} True when the display root carries attached details.
    @details Verifies ancestor segment encoding, sibling order, detail ownership, and the
    absence of structural markers on detail lines (SRS-544).
    """
    assert lines, "rendered output must not be empty"
    last_flags: list[bool] = []
    previous_at_depth: dict[int, bool] = {}
    owner: tuple[int, bool] | None = None
    for line in lines[1:]:
        assert line.strip(), "empty output line"
        segments, rest = split_prefix(line)
        if rest.startswith(TREE_MARKERS):
            is_last = rest.startswith("└── ")
            depth = len(segments)
            assert depth <= len(last_flags), f"depth jump on line: {line!r}"
            for position in range(depth):
                expected = "    " if last_flags[position] else "│   "
                assert segments[position] == expected, f"bad ancestor prefix: {line!r}"
            for position in [key for key in previous_at_depth if key > depth]:
                del previous_at_depth[position]
            assert previous_at_depth.get(depth) is not True, (
                f"node after final sibling: {line!r}"
            )
            last_flags = last_flags[:depth] + [is_last]
            previous_at_depth[depth] = is_last
            owner = (depth, is_last)
        else:
            assert not rest.startswith(TREE_MARKERS), f"malformed marker: {line!r}"
            if owner is None:
                assert root_details, f"detail before any node: {line!r}"
                assert segments == ["    "], f"root detail prefix: {line!r}"
                continue
            depth, is_last = owner
            assert len(segments) == depth + 1, f"detail depth mismatch: {line!r}"
            for position in range(depth):
                expected = "    " if last_flags[position] else "│   "
                assert segments[position] == expected, f"bad detail ancestor: {line!r}"
            expected_own = "    " if is_last else "│   "
            assert segments[-1] == expected_own, f"bad detail continuation: {line!r}"


def validate_tables(lines: list[str]) -> int:
    """!
    @brief Assert every rendered table is rectangular and correctly anchored.
    @param lines {list[str]} Rendered output lines.
    @return {int} Number of validated tables.
    @details Checks equal display widths, aligned border columns, and identical owner
    prefixes for every table block (SRS-544).
    """
    tables = 0
    position = 0
    while position < len(lines):
        segments, rest = split_prefix(lines[position])
        if not rest.startswith("┌"):
            position += 1
            continue
        prefix = "".join(segments)
        block: list[str] = []
        while position < len(lines):
            current_segments, current_rest = split_prefix(lines[position])
            assert "".join(current_segments) == prefix, "table owner prefix mismatch"
            block.append(current_rest)
            position += 1
            if current_rest.startswith("└"):
                break
        assert block[0].startswith("┌"), "table must start with a top border"
        assert block[-1].startswith("└"), "table must end with a bottom border"
        widths = {display_width(row) for row in block}
        assert len(widths) == 1, f"table rows differ in width: {sorted(widths)}"
        border_columns = None
        for row in block:
            columns = []
            column = 0
            for char in row:
                if char in TABLE_CHARS:
                    columns.append(column)
                column += 2 if (
                    not unicodedata.combining(char)
                    and unicodedata.east_asian_width(char) in ("W", "F")
                ) else (0 if unicodedata.combining(char) else 1)
            if border_columns is None:
                border_columns = columns
            assert border_columns == columns, "misaligned table border columns"
        tables += 1
    return tables


class HomeTestCase(unittest.TestCase):
    """! @brief Base class isolating HOME and disabling the startup release-check. """

    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="usereq-config-home-"))
        patcher = patch("usereq.cli.home_dir", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)

    @property
    def config_path(self) -> Path:
        """! @brief Return the isolated global configuration file path. """
        return self.home / ".config" / "usereq" / "config.json"

    def run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        """! @brief Run one CLI invocation with captured streams. """
        out = io.StringIO()
        err = io.StringIO()
        with (
            patch("usereq.cli.maybe_notify_newer_version", autospec=True),
            redirect_stdout(out),
            redirect_stderr(err),
        ):
            code = cli.main(argv)
        return code, out.getvalue(), err.getvalue()

    def read_config(self) -> dict:
        """! @brief Read the isolated configuration JSON payload. """
        return json.loads(self.config_path.read_text(encoding="utf-8"))


class TestRendererGoldenOutput(unittest.TestCase):
    """! @brief SRS-543: exact renderer output for synthetic trees. """

    def test_single_root_child(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        root.children = [RenderNode("Only", "Only", "string", "Only = 1 (default)")]
        self.assertEqual(render_text(root), "Root - heading\n└── Only = 1 (default)")

    def test_two_root_siblings(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        root.children = [
            RenderNode("First", "First", "string", "First = 1 (default)"),
            RenderNode("Second", "Second", "string", "Second = 2 (custom)"),
        ]
        expected = (
            "Root - heading\n"
            "├── First = 1 (default)\n"
            "└── Second = 2 (custom)"
        )
        self.assertEqual(render_text(root), expected)

    def test_nested_first_middle_last_siblings(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        branch = RenderNode("Branch", "Branch", "section", "Branch - [Path: Branch]")
        branch.children = [
            RenderNode("One", "Branch:One", "string", "One = 1"),
            RenderNode("Two", "Branch:Two", "string", "Two = 2"),
            RenderNode("Three", "Branch:Three", "string", "Three = 3"),
        ]
        root.children = [branch]
        expected = (
            "Root - heading\n"
            "└── Branch - [Path: Branch]\n"
            "    ├── One = 1\n"
            "    ├── Two = 2\n"
            "    └── Three = 3"
        )
        self.assertEqual(render_text(root), expected)

    def test_non_last_leaf_with_details(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        leaf = RenderNode("Leaf", "Leaf", "array", "Leaf = (1 items)")
        leaf.details = [["Default : []"], ["Set cmd : --set Leaf:0 x"]]
        root.children = [leaf, RenderNode("Last", "Last", "string", "Last = 1")]
        expected = (
            "Root - heading\n"
            "├── Leaf = (1 items)\n"
            "│   Default : []\n"
            "│   Set cmd : --set Leaf:0 x\n"
            "└── Last = 1"
        )
        self.assertEqual(render_text(root), expected)

    def test_last_leaf_with_details(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        leaf = RenderNode("Leaf", "Leaf", "map", "Leaf = (0 entries)")
        leaf.details = [["Reset cmd : --unset Leaf"]]
        root.children = [leaf]
        expected = (
            "Root - heading\n"
            "└── Leaf = (0 entries)\n"
            "    Reset cmd : --unset Leaf"
        )
        self.assertEqual(render_text(root), expected)

    def test_branch_with_details_and_children(self) -> None:
        root = RenderNode("Root", "", "section", "Root - heading")
        branch = RenderNode("Block", "Block", "section", "Block - [Path: Block]")
        branch.details = [["Reset block : --unset Block"]]
        branch.children = [RenderNode("Child", "Block:Child", "string", "Child = 1")]
        root.children = [
            branch,
            RenderNode("Tail", "Tail", "string", "Tail = 2"),
        ]
        expected = (
            "Root - heading\n"
            "├── Block - [Path: Block]\n"
            "│   Reset block : --unset Block\n"
            "│   └── Child = 1\n"
            "└── Tail = 2"
        )
        self.assertEqual(render_text(root), expected)
        validate_tree_structure(render_text(root).split("\n"))

    def test_requested_subtree_root_details_indent(self) -> None:
        node = RenderNode("Leaf", "Leaf", "array", "Leaf = (2 items)")
        node.details = [format_table(["Idx", "Value"], [["0", '"a"']])]
        expected = (
            "Leaf = (2 items)\n"
            "    ┌─────┬───────┐\n"
            "    │ Idx │ Value │\n"
            "    ├─────┼───────┤\n"
            '    │ 0   │ "a"   │\n'
            "    └─────┴───────┘"
        )
        self.assertEqual(render_text(node), expected)
        validate_tables(render_text(node).split("\n"))


class TestTableLayout(unittest.TestCase):
    """! @brief SRS-543/SRS-544: measured table layout and escaping. """

    def test_rectangular_ascii_table(self) -> None:
        rows = format_table(["Key", "Value"], [["a", "1"], ["bb", "22"]])
        self.assertEqual(rows[0], "┌─────┬───────┐")
        self.assertEqual(rows[1], "│ Key │ Value │")
        self.assertEqual(rows[2], "├─────┼───────┤")
        validate_tables(rows)

    def test_unicode_and_escaped_newline_cells(self) -> None:
        rows = format_table(["Field", "Text"], [["wide", "日本語"], ["multi", "a\nb"]])
        joined = "\n".join(rows)
        self.assertNotIn("\n" + "a\nb", joined)
        self.assertIn("a\\nb", joined)
        validate_tables(rows)

    def test_empty_row_table_is_rectangular(self) -> None:
        rows = format_table(["Only"], [])
        validate_tables(rows)


class TestConfigurationCommands(HomeTestCase):
    """! @brief SRS-545: command behavior of the configuration CLI. """

    def write_payload(self, payload: dict) -> bytes:
        """! @brief Write a raw payload and return its exact bytes. """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, indent=4).encode("utf-8")
        self.config_path.write_bytes(data)
        return data

    def test_print_bootstraps_configuration_file(self) -> None:
        self.assertFalse(self.config_path.exists())
        code, out, err = self.run_cli(["--print"])
        self.assertEqual(code, 0, err)
        self.assertTrue(self.config_path.is_file())
        self.assertIn("Application_Configuration", out)
        self.assertIn("Configuration - [Path: Configuration]", out)
        validate_tree_structure(out.splitlines())

    def test_print_full_tree_is_structural(self) -> None:
        code, out, _ = self.run_cli(["--print"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        validate_tree_structure(lines)
        self.assertGreaterEqual(validate_tables(lines), 1)
        self.assertNotIn("Application_Configuration:", out)

    def test_info_full_tree_is_structural(self) -> None:
        code, out, err = self.run_cli(["--info"])
        self.assertEqual(code, 0, err)
        validate_tree_structure(out.splitlines())
        self.assertGreaterEqual(validate_tables(out.splitlines()), 1)
        self.assertIn("[Array[String]: enum provider]", out)
        self.assertIn("--set Configuration:providers:+", out)
        self.assertNotIn("...", out)

    def test_info_regression_detail_prefixes(self) -> None:
        code, out, _ = self.run_cli(["--info"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertIn("└── Configuration - [Path: Configuration] User-global useReq configuration.", lines)
        self.assertIn("    Reset block : --unset Configuration", lines)
        self.assertIn("    ├── docs-dir - [String: non-empty] Project-relative documentation directory.", lines)
        self.assertIn(
            "    │   Default : \"usereq/docs\" (restored via: --unset Configuration:docs-dir)",
            lines,
        )
        self.assertIn("        Default : true (restored via: --unset Configuration:auto-install)", lines)
        for line in lines:
            self.assertNotIn("│   ├── ", line)
            self.assertNotIn("│   └── ", line)

    def test_get_emits_json_only(self) -> None:
        code, out, err = self.run_cli(["--get", "Configuration:docs-dir"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out, '"usereq/docs"\n')
        self.assertEqual(json.loads(out), "usereq/docs")

    def test_get_section_emits_json_object(self) -> None:
        code, out, _ = self.run_cli(["--get", "Configuration"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(
            sorted(payload),
            [
                "auto-install",
                "docs-dir",
                "providers",
                "src-dir",
                "static-check",
                "tests-dir",
            ],
        )

    def test_set_typed_values_persist(self) -> None:
        self.assertEqual(self.run_cli(["--set", "Configuration:docs-dir", "documentation"])[0], 0)
        self.assertEqual(self.run_cli(["--set", "Configuration:auto-install", "false"])[0], 0)
        self.assertEqual(self.run_cli(["--set", "Configuration:providers:+", "pi"])[0], 0)
        payload = self.read_config()
        self.assertEqual(payload["docs-dir"], "documentation")
        self.assertIs(payload["auto-install"], False)
        self.assertEqual(payload["providers"], ["pi"])

    def test_set_rejects_invalid_enum_without_mutation(self) -> None:
        before = self.write_payload({"providers": ["pi"]})
        code, out, err = self.run_cli(["--set", "Configuration:providers:+", "unknown"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Configuration:providers:+", err)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_set_rejects_out_of_range_index_without_mutation(self) -> None:
        before = self.write_payload({"src-dir": ["src"]})
        code, _, err = self.run_cli(["--set", "Configuration:src-dir:4", "lib"])
        self.assertEqual(code, 1)
        self.assertIn("out of range", err)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_array_item_requires_single_item(self) -> None:
        self.write_payload({})
        code, _, err = self.run_cli(
            ["--set", "Configuration:src-dir:+", '["one", "two"]']
        )
        self.assertEqual(code, 1)
        self.assertIn("exactly one item", err)

    def test_whole_array_requires_json_array(self) -> None:
        self.write_payload({})
        code, _, err = self.run_cli(
            ["--set", "Configuration:src-dir", '{"a": 1}']
        )
        self.assertEqual(code, 1)
        self.assertIn("must be a JSON array", err)

    def test_unset_restores_default_and_removes_keys(self) -> None:
        self.write_payload({"docs-dir": "docs", "providers": ["pi"]})
        self.assertEqual(self.run_cli(["--unset", "Configuration:docs-dir"])[0], 0)
        self.assertEqual(self.run_cli(["--unset", "Configuration:providers:0"])[0], 0)
        payload = self.read_config()
        self.assertEqual(payload["docs-dir"], "usereq/docs")
        self.assertEqual(payload["providers"], [])

    def test_unset_required_field_fails_without_mutation(self) -> None:
        before = self.write_payload({"static-check": {"Python": [{"module": "Ruff"}]}})
        code, _, err = self.run_cli(
            ["--unset", "Configuration:static-check:Python:0:module"]
        )
        self.assertEqual(code, 1)
        self.assertIn("required", err)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_unset_optional_field_removes_key(self) -> None:
        self.write_payload(
            {"static-check": {"Python": [{"module": "Pylance", "cmd": "pylint"}]}}
        )
        code, _, err = self.run_cli(
            ["--unset", "Configuration:static-check:Python:0:cmd"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(
            self.read_config()["static-check"]["Python"][0], {"module": "Pylance"}
        )

    def test_set_section_resets_missing_keys_to_defaults(self) -> None:
        self.write_payload({"docs-dir": "docs"})
        code, _, err = self.run_cli(
            ["--set", "Configuration", '{"docs-dir": "handbook"}']
        )
        self.assertEqual(code, 0, err)
        payload = self.read_config()
        self.assertEqual(payload["docs-dir"], "handbook")
        self.assertEqual(payload["src-dir"], ["src"])

    def test_print_raw_preserves_bytes(self) -> None:
        raw = self.write_payload({"docs-dir": "docs", "src-dir": ["lib"]})
        code, out, err = self.run_cli(["--print-raw"])
        self.assertEqual(code, 0, err)
        self.assertEqual(out.encode("utf-8"), raw)

    def test_print_raw_does_not_tree_format(self) -> None:
        self.write_payload({"docs-dir": "docs"})
        _, out, _ = self.run_cli(["--print-raw"])
        self.assertNotIn("Application_Configuration", out)
        self.assertNotIn("├──", out)

    def test_print_subtree_has_no_fake_ancestors(self) -> None:
        code, out, err = self.run_cli(["--print", "Configuration:src-dir"])
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("src-dir = "))
        validate_tree_structure(lines, root_details=True)
        self.assertNotIn("Configuration -", out)

    def test_info_subtree_section_badge(self) -> None:
        code, out, err = self.run_cli(["--info", "Configuration"])
        self.assertEqual(code, 0, err)
        first = out.splitlines()[0]
        self.assertEqual(
            first, "Configuration - [Path: Configuration] User-global useReq configuration."
        )
        self.assertIn("    Reset block : --unset Configuration", out.splitlines())

    def test_error_paths_write_stderr_only(self) -> None:
        for argv in (
            ["--get", "Configuration:unknown"],
            ["--set", "Configuration:auto-install", "maybe"],
            ["--unset", "Configuration:static-check:Python:0:module"],
        ):
            code, out, err = self.run_cli(argv)
            self.assertEqual(code, 1, argv)
            self.assertEqual(out, "", argv)
            self.assertTrue(err.strip(), argv)

    def test_multiple_configuration_commands_are_rejected(self) -> None:
        code, out, err = self.run_cli(
            ["--print", "--get", "Configuration:docs-dir"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("exactly one", err)

    def test_invalid_configuration_file_reports_error(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text("{not json", encoding="utf-8")
        code, out, err = self.run_cli(["--print"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("not valid JSON", err)

    def test_atomic_write_failure_preserves_original(self) -> None:
        before = self.write_payload({"docs-dir": "docs"})
        os_mode = config_cli.os
        with patch.object(os_mode, "replace", side_effect=OSError("boom")):
            code, out, err = self.run_cli(
                ["--set", "Configuration:docs-dir", "handbook"]
            )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("cannot write configuration file", err)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_set_preserves_file_mode(self) -> None:
        self.write_payload({"docs-dir": "docs"})
        self.config_path.chmod(0o640)
        self.assertEqual(self.run_cli(["--set", "Configuration:docs-dir", "d"])[0], 0)
        self.assertEqual(stat.S_IMODE(self.config_path.stat().st_mode), 0o640)

    def test_set_static_check_map_key_and_field(self) -> None:
        self.write_payload({})
        code, _, err = self.run_cli(
            [
                "--set",
                "Configuration:static-check:Python",
                '[{"module": "Pylance"}]',
            ]
        )
        self.assertEqual(code, 0, err)
        code, _, err = self.run_cli(
            ["--set", "Configuration:static-check:Python:+", '{"module": "Ruff"}']
        )
        self.assertEqual(code, 0, err)
        code, out, err = self.run_cli(
            ["--get", "Configuration:static-check:Python:1:module"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), "Ruff")

    def test_empty_path_token_is_rejected(self) -> None:
        self.write_payload({})
        code, _, err = self.run_cli(["--get", "Configuration::docs-dir"])
        self.assertEqual(code, 1)
        self.assertIn("empty token", err)

    def test_set_scan_by_dir_true_on_capable_entry(self) -> None:
        """!
        @brief SRS-585/SRS-586: `scan-by-dir` true persists on a directory-scan-capable entry.
        """
        self.write_payload({"static-check": {"Python": [{"module": "Ruff"}]}})
        code, _, err = self.run_cli(
            ["--set", "Configuration:static-check:Python:0:scan-by-dir", "true"]
        )
        self.assertEqual(code, 0, err)
        self.assertIs(self.read_config()["static-check"]["Python"][0]["scan-by-dir"], True)

    def test_set_scan_by_dir_true_on_incapable_entry_rejected(self) -> None:
        """!
        @brief SRS-586: `scan-by-dir` true on an incapable entry fails without mutation.
        """
        before = self.write_payload({"static-check": {"Python": [{"module": "Dummy"}]}})
        code, out, err = self.run_cli(
            ["--set", "Configuration:static-check:Python:0:scan-by-dir", "true"]
        )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("does not support directory scanning", err)
        self.assertEqual(self.config_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
