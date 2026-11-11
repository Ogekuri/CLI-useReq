"""!
@file config_schema.py
@brief Canonical configuration schema for the user-global useReq configuration file.
@details Single source of truth for the persisted configuration parameter set: section and
parameter tokens, node kinds, defaults, constraints, and canonical paths. The path resolver,
typed value parser, tree renderer, and help generator of `usereq.config_cli` consume this
schema, so `--print`, `--info`, `--get`, `--set`, and `--unset` never maintain duplicated
parameter lists (SRS-521, SRS-542).
@author useReq
@version 0.75.3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

KIND_SECTION = "section"
"""! @brief Schema node kind for a named configuration section (SRS-523)."""

KIND_STRING = "string"
"""! @brief Schema node kind for a plain text value (SRS-521)."""

KIND_BOOLEAN = "boolean"
"""! @brief Schema node kind for a JSON boolean value (SRS-521)."""

KIND_ARRAY = "array"
"""! @brief Schema node kind for an ordered list value (SRS-533, SRS-534)."""

KIND_MAP = "map"
"""! @brief Schema node kind for a dynamic string-keyed dictionary value (SRS-521)."""

KIND_DICTIONARY = "dictionary"
"""! @brief Schema node kind for a fixed-field dictionary value (SRS-540)."""

NO_DEFAULT: Any = object()
"""! @brief Sentinel marking a schema node without a declared default value (SRS-536)."""

DEFAULT_DOCS_DIR = "usereq/docs"
"""! @brief Default docs-dir value when the configuration stores no docs-dir entry (SRS-359)."""

DEFAULT_TESTS_DIR = "tests"
"""! @brief Default tests-dir value when the configuration stores no tests-dir entry (SRS-361)."""

DEFAULT_SRC_DIRS = ("src",)
"""! @brief Default src-dir list when the configuration stores no src-dir entry (SRS-362)."""

DEFAULT_AUTO_INSTALL = True
"""! @brief Default auto-install state when the configuration stores no entry (SRS-420)."""

VALID_PROVIDER_NAMES = (
    "antigravity",
    "claude",
    "codex",
    "copilot",
    "openclaw",
    "opencode",
    "pi",
)
"""! @brief Canonical provider CLI names accepted by the providers schema entry (SRS-275, SRS-364)."""

PROVIDER_MEANINGS: dict[str, str] = {
    "antigravity": "Antigravity provider skills root.",
    "claude": "Claude Code provider skills root.",
    "codex": "Codex provider skills root.",
    "copilot": "GitHub Copilot provider skills root.",
    "openclaw": "OpenClaw provider skills root.",
    "opencode": "OpenCode provider skills root.",
    "pi": "Pi provider skills root.",
}
"""! @brief Short English meaning rendered by the providers `Allowed Values` table (SRS-538)."""

STATIC_CHECK_LANGUAGES = (
    "Python",
    "C",
    "C++",
    "C#",
    "Rust",
    "JavaScript",
    "TypeScript",
    "Java",
    "Go",
    "Ruby",
    "PHP",
    "Swift",
    "Kotlin",
    "Scala",
    "Lua",
    "Shell",
    "Perl",
    "Haskell",
    "Zig",
    "Elixir",
)
"""! @brief Canonical static-check language keys usable as `static-check` map keys (SRS-249, SRS-540)."""

STATIC_CHECK_MODULES = ("Dummy", "Pylance", "Ruff", "Command")
"""! @brief Canonical static-check module names accepted by the entry schema (SRS-250)."""

DEFAULT_STATIC_CHECK: dict[str, list[dict[str, Any]]] = {
    "C": [
        {
            "module": "Command",
            "cmd": "cppcheck",
            "params": [
                "--error-exitcode=1",
                "--enable=warning,style,performance,portability",
                "--std=c11",
            ],
        },
        {"module": "Command", "cmd": "clang-format", "params": ["--dry-run", "--Werror"]},
    ],
    "C++": [
        {
            "module": "Command",
            "cmd": "cppcheck",
            "params": [
                "--error-exitcode=1",
                "--enable=warning,style,performance,portability",
                "--std=c++20",
            ],
        },
        {"module": "Command", "cmd": "clang-format", "params": ["--dry-run", "--Werror"]},
    ],
    "JavaScript": [{"module": "Command", "cmd": "node", "params": ["--check"]}],
    "Python": [{"module": "Pylance"}, {"module": "Ruff"}],
    "TypeScript": [{"module": "Command", "cmd": "eslint"}],
}
"""! @brief Default static-check configuration applied when the configuration stores no
`"static-check"` entry; a present entry, including an empty object, suppresses these
defaults (SRS-424, SRS-425, SRS-426)."""


@dataclass(frozen=True)
class SchemaNode:
    """!
    @brief Typed schema node describing one configuration token or collection element.
    @details Nodes form an ordered tree rooted at `CONFIG_SECTION`. A node carries the exact
    canonical token, the node kind, a concise English description, the textual type label and
    constraints used by `--info`, the typed default (or `NO_DEFAULT`), enumeration metadata,
    and the child collection definitions used by validation and rendering
    (SRS-521, SRS-522, SRS-538).
    """

    token: str
    kind: str
    description: str
    type_label: str = "String"
    constraints: str = ""
    default: Any = NO_DEFAULT
    non_empty: bool = False
    optional: bool = False
    enum: Optional[tuple[str, ...]] = None
    enum_meanings: Optional[dict[str, str]] = None
    example: Optional[str] = None
    key_enum: Optional[tuple[str, ...]] = None
    item: Optional["SchemaNode"] = None
    fields: tuple["SchemaNode", ...] = ()
    children: tuple["SchemaNode", ...] = ()

    @property
    def has_default(self) -> bool:
        """! @brief Return True when the node declares a typed default value (SRS-536)."""
        return self.default is not NO_DEFAULT


def _entry_fields() -> tuple[SchemaNode, ...]:
    """!
    @brief Build the fixed field set of one static-check dictionary entry (SRS-540).
    @return {tuple[SchemaNode, ...]} Ordered `module`, `cmd`, and `params` field nodes.
    """
    return (
        SchemaNode(
            token="module",
            kind=KIND_STRING,
            description="Static checker module name.",
            constraints="enum: " + ", ".join(STATIC_CHECK_MODULES),
            non_empty=True,
            enum=STATIC_CHECK_MODULES,
            example="Pylance",
        ),
        SchemaNode(
            token="cmd",
            kind=KIND_STRING,
            description="Checker executable required when module is Command.",
            constraints="non-empty; required for Command",
            non_empty=True,
            optional=True,
            example="cppcheck",
        ),
        SchemaNode(
            token="params",
            kind=KIND_ARRAY,
            description="Checker argument vector.",
            type_label="Array[String]",
            constraints="",
            optional=True,
            example='["--check"]',
            item=SchemaNode(
                token="",
                kind=KIND_STRING,
                description="One checker argument.",
                non_empty=False,
            ),
        ),
    )


_STATIC_CHECK_ENTRY = SchemaNode(
    token="",
    kind=KIND_DICTIONARY,
    description="One static-check entry.",
    type_label="Dictionary",
    constraints="fields: module, cmd, params",
    fields=_entry_fields(),
)
"""! @brief Fixed-schema dictionary describing one static-check entry (SRS-540)."""

_STATIC_CHECK_ENTRY_ARRAY = SchemaNode(
    token="",
    kind=KIND_ARRAY,
    description="Ordered static-check entries for one canonical language.",
    type_label="Array[Dictionary]",
    constraints="",
    item=_STATIC_CHECK_ENTRY,
)
"""! @brief Array of static-check entries stored under one canonical language key (SRS-540)."""

CONFIG_SECTION = SchemaNode(
    token="Configuration",
    kind=KIND_SECTION,
    description="User-global useReq configuration.",
    type_label="Section",
    constraints="",
    children=(
        SchemaNode(
            token="docs-dir",
            kind=KIND_STRING,
            description="Project-relative documentation directory.",
            type_label="String",
            constraints="non-empty",
            default=DEFAULT_DOCS_DIR,
            non_empty=True,
        ),
        SchemaNode(
            token="tests-dir",
            kind=KIND_STRING,
            description="Project-relative unit-test directory.",
            type_label="String",
            constraints="non-empty",
            default=DEFAULT_TESTS_DIR,
            non_empty=True,
        ),
        SchemaNode(
            token="src-dir",
            kind=KIND_ARRAY,
            description="Ordered project-relative source directories.",
            type_label="Array[String]",
            constraints="non-empty items",
            default=list(DEFAULT_SRC_DIRS),
            item=SchemaNode(
                token="",
                kind=KIND_STRING,
                description="One project-relative source directory.",
                non_empty=True,
            ),
        ),
        SchemaNode(
            token="providers",
            kind=KIND_ARRAY,
            description="Provider CLI names enabled for skill installation.",
            type_label="Array[String]",
            constraints="enum provider",
            default=[],
            item=SchemaNode(
                token="",
                kind=KIND_STRING,
                description="One provider CLI name.",
                non_empty=True,
                enum=VALID_PROVIDER_NAMES,
                enum_meanings=PROVIDER_MEANINGS,
            ),
        ),
        SchemaNode(
            token="static-check",
            kind=KIND_MAP,
            description="Static-check tools keyed by canonical language name.",
            type_label="Map[String, Array[Dictionary]]",
            constraints="",
            default=DEFAULT_STATIC_CHECK,
            key_enum=STATIC_CHECK_LANGUAGES,
            item=_STATIC_CHECK_ENTRY_ARRAY,
        ),
        SchemaNode(
            token="auto-install",
            kind=KIND_BOOLEAN,
            description="Reinstall configured providers after a successful upgrade.",
            type_label="Boolean",
            constraints="",
            default=DEFAULT_AUTO_INSTALL,
        ),
    ),
)
"""! @brief Root schema section holding every persisted configuration parameter (SRS-521)."""

ROOT_LABEL = "Application_Configuration"
"""! @brief Virtual display label of the configuration tree root; never a CLI path token (SRS-520)."""

CONFIG_KEYS: tuple[str, ...] = tuple(child.token for child in CONFIG_SECTION.children)
"""! @brief Canonical persisted configuration keys in schema order (SRS-288, SRS-521)."""


def find_field(node: SchemaNode, token: str) -> Optional[SchemaNode]:
    """!
    @brief Look up one ordered child field of a section or dictionary node.
    @param node {SchemaNode} Section or dictionary node providing the candidate fields.
    @param token {str} Exact canonical field token to resolve.
    @return {Optional[SchemaNode]} Matching field node, or None when the token is unknown.
    @details Matching is case-sensitive and byte-exact so path resolution never depends on
    displayed labels or decorative text (SRS-520, SRS-522).
    """
    for child in node.children or node.fields:
        if child.token == token:
            return child
    return None


def canonical_path(tokens: tuple[str, ...]) -> str:
    """!
    @brief Join canonical path tokens with the colon separator.
    @param tokens {tuple[str, ...]} Ordered canonical path tokens without the virtual root.
    @return {str} Canonical colon-separated configuration path.
    @details Empty tokens are rejected by the resolver, so joining never produces an
    ambiguous empty path segment (SRS-520).
    """
    return ":".join(tokens)
