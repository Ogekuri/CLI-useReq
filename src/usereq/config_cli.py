"""!
@file config_cli.py
@brief Configuration CLI operations and deterministic tree rendering.
@details Implements the canonical configuration interface of the useReq CLI:
typed path resolution, strict schema validation, atomic persistence, JSON reads, and the
single recursive tree renderer shared by `--print` and `--info` (SRS-519..SRS-545).
The module never imports `usereq.cli`; callers pass the resolved global configuration path
and translate `ConfigError` into the CLI error channel.
@author useReq
@version 0.75.3
"""

from __future__ import annotations

import copy
import json
import os
import shlex
import stat
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

from .config_schema import (
    CONFIG_KEYS,
    CONFIG_SECTION,
    KIND_ARRAY,
    KIND_BOOLEAN,
    KIND_DICTIONARY,
    KIND_MAP,
    KIND_SECTION,
    KIND_STRING,
    ROOT_LABEL,
    SchemaNode,
    find_field,
)

BRANCH = "├── "
"""! @brief Structural marker for a configuration node with a later sibling (SRS-524)."""

LAST = "└── "
"""! @brief Structural marker for the final configuration sibling at its depth (SRS-524)."""

INDENT = "    "
"""! @brief Exact four-ASCII-space ancestor prefix segment (SRS-524)."""

CONTINUE = "│   "
"""! @brief Ancestor prefix segment for an ancestor with a later sibling (SRS-524)."""

MISSING: Any = object()
"""! @brief Sentinel marking an absent optional configuration value (SRS-527)."""


class ConfigError(Exception):
    """!
    @brief Expected configuration CLI failure with an English diagnostic.
    @details Carries the diagnostic text and the process exit code consumed by the CLI
    dispatcher so configuration failures never leak stack traces (SRS-532).
    """

    def __init__(self, message: str, code: int = 1) -> None:
        """!
        @brief Initialize one configuration failure payload.
        @param message {str} English diagnostic text written to stderr.
        @param code {int} Process exit code bound to the failure category.
        """
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class RenderNode:
    """!
    @brief One real configuration node of the rendered tree.
    @details Holds the canonical token, canonical path, node kind, the finalized heading
    line, attached detail blocks, and real child nodes. Tree topology derives exclusively
    from `children`; details never create structural depth (SRS-524, SRS-525).
    """

    token: str
    canonical_path: str
    kind: str
    heading: str
    details: list[list[str]] = field(default_factory=list)
    children: list["RenderNode"] = field(default_factory=list)


@dataclass
class Target:
    """!
    @brief Resolved configuration path describing the operation target.
    @details `op` is one of `node`, `array_item`, `append`, `insert`, `dict_field`, or
    `map_key`. `container` is the mutable parent list/dictionary, `key` the list index or
    dictionary key, and `spec` the schema node governing the target value (SRS-533, SRS-534).
    """

    op: str
    spec: SchemaNode
    value: Any
    container: Any
    key: Any


def default_config() -> dict[str, Any]:
    """!
    @brief Build the complete default configuration from the canonical schema.
    @return {dict[str, Any]} Configuration payload holding every canonical key default.
    @details Defaults are deep-copied so callers never mutate the shared schema objects
    (SRS-521, SRS-529).
    """
    result: dict[str, Any] = {}
    for child in CONFIG_SECTION.children:
        result[child.token] = (
            copy.deepcopy(child.default) if child.has_default else None
        )
    return result


def read_raw_payload(config_path: Path) -> dict[str, Any]:
    """!
    @brief Read the raw configuration JSON payload without applying defaults.
    @param config_path {Path} Absolute global configuration file path.
    @return {dict[str, Any]} Parsed JSON object; empty dictionary when the file is absent.
    @throws {ConfigError} Raised when the file is unreadable, not JSON, or not a JSON object.
    @details Only the raw stored payload is returned; unknown keys are preserved here and
    dropped by the canonical writer (SRS-528, SRS-530).
    """
    if not config_path.is_file():
        return {}
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(
            f"Error: cannot read configuration file '{config_path}': {exc}"
        ) from exc
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Error: configuration file '{config_path}' is not valid JSON: "
            f"{exc.msg} at line {exc.lineno} column {exc.colno}."
        ) from exc
    if not isinstance(payload, dict):
        raise ConfigError(
            f"Error: configuration file '{config_path}' must contain a JSON object."
        )
    return payload


def _type_name(value: Any) -> str:
    """!
    @brief Return a stable English type name for one JSON value.
    @param value {Any} Parsed JSON value.
    @return {str} JSON type name used inside diagnostics.
    """
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def validate_node(node: SchemaNode, value: Any, path: str) -> None:
    """!
    @brief Validate one value against its schema node, including nested values.
    @param node {SchemaNode} Schema node governing the value.
    @param value {Any} Parsed JSON value to validate.
    @param path {str} Canonical path used inside diagnostics.
    @return {None} Function return value.
    @throws {ConfigError} Raised with an English diagnostic on any schema violation.
    @details Covers primitives, enums, arrays, map keys, fixed-field dictionaries, required
    fields, and the Command `cmd` cross-field constraint (SRS-530, SRS-536).
    """
    if node.kind == KIND_STRING:
        if not isinstance(value, str):
            raise ConfigError(
                f"Error: '{path}' must be a string, got {_type_name(value)}."
            )
        if node.non_empty and not value.strip():
            raise ConfigError(f"Error: '{path}' must be a non-empty string.")
        if node.enum is not None and value not in node.enum:
            allowed = ", ".join(node.enum)
            raise ConfigError(
                f"Error: '{path}' must be one of: {allowed}; got '{value}'."
            )
        return
    if node.kind == KIND_BOOLEAN:
        if not isinstance(value, bool):
            raise ConfigError(
                f"Error: '{path}' must be a JSON boolean, got {_type_name(value)}."
            )
        return
    if node.kind == KIND_ARRAY:
        if not isinstance(value, list):
            raise ConfigError(
                f"Error: '{path}' must be a JSON array, got {_type_name(value)}."
            )
        assert node.item is not None
        for index, item in enumerate(value):
            validate_node(node.item, item, f"{path}:{index}")
        return
    if node.kind == KIND_MAP:
        if not isinstance(value, dict):
            raise ConfigError(
                f"Error: '{path}' must be a JSON object, got {_type_name(value)}."
            )
        assert node.item is not None
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ConfigError(
                    f"Error: '{path}' keys must be non-empty strings."
                )
            if node.key_enum is not None and key not in node.key_enum:
                allowed = ", ".join(node.key_enum)
                raise ConfigError(
                    f"Error: '{path}' key '{key}' must be one of: {allowed}."
                )
            validate_node(node.item, item, f"{path}:{key}")
        return
    if node.kind == KIND_DICTIONARY:
        if not isinstance(value, dict):
            raise ConfigError(
                f"Error: '{path}' must be a JSON object, got {_type_name(value)}."
            )
        known = {child.token: child for child in node.fields}
        for key in value:
            if key not in known:
                allowed = ", ".join(known)
                raise ConfigError(
                    f"Error: '{path}' has unknown field '{key}'; allowed fields: {allowed}."
                )
        for child in node.fields:
            if child.token in value:
                validate_node(child, value[child.token], f"{path}:{child.token}")
            elif not child.has_default and not child.optional:
                raise ConfigError(
                    f"Error: '{path}:{child.token}' is a required field."
                )
        if value.get("module") == "Command":
            cmd = value.get("cmd")
            if not isinstance(cmd, str) or not cmd.strip():
                raise ConfigError(
                    f"Error: '{path}:cmd' is required when module is Command."
                )
        return
    if node.kind == KIND_SECTION:
        if not isinstance(value, dict):
            raise ConfigError(
                f"Error: '{path}' must be a JSON object, got {_type_name(value)}."
            )
        for child in node.children:
            if child.token in value:
                validate_node(child, value[child.token], f"{path}:{child.token}")
        return
    raise ConfigError(f"Error: '{path}' uses unsupported schema kind '{node.kind}'.")


def normalize_config(payload: dict[str, Any]) -> dict[str, Any]:
    """!
    @brief Merge a raw payload over the schema defaults and validate stored values.
    @param payload {dict[str, Any]} Raw stored JSON payload.
    @return {dict[str, Any]} Effective configuration holding every canonical key.
    @throws {ConfigError} Raised when a stored canonical value violates the schema.
    @details Unknown top-level keys are outside the canonical schema and are therefore
    ignored here and dropped by `write_config` (SRS-288, SRS-530).
    """
    config = default_config()
    children = {child.token: child for child in CONFIG_SECTION.children}
    for key, value in payload.items():
        child = children.get(key)
        if child is None:
            continue
        validate_node(child, value, key)
        config[key] = value
    return config


def load_effective_config(config_path: Path) -> dict[str, Any]:
    """!
    @brief Load and validate the effective configuration for one configuration command.
    @param config_path {Path} Absolute global configuration file path.
    @return {dict[str, Any]} Effective configuration with defaults applied.
    @throws {ConfigError} Raised when the file is unreadable or schema-invalid.
    """
    return normalize_config(read_raw_payload(config_path))


def write_config(config_path: Path, config: dict[str, Any]) -> None:
    """!
    @brief Atomically persist the canonical configuration payload.
    @param config_path {Path} Absolute global configuration file path.
    @param config {dict[str, Any]} Fully validated effective configuration.
    @return {None} Function return value.
    @throws {ConfigError} Raised when the write fails; the original file is preserved.
    @details Creates missing parent directories, writes a same-directory temporary file,
    flushes and fsyncs it, preserves the existing file mode, atomically replaces the target,
    and fsyncs the parent directory (SRS-529, SRS-531).
    """
    ordered = {key: config[key] for key in CONFIG_KEYS if key in config}
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigError(
            f"Error: cannot create configuration directory '{config_path.parent}': {exc}"
        ) from exc
    tmp_name: Optional[str] = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(config_path.parent), prefix=config_path.name + ".", suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(ordered, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        if config_path.is_file():
            os.chmod(tmp_name, stat.S_IMODE(config_path.stat().st_mode))
        os.replace(tmp_name, config_path)
        directory_fd = os.open(str(config_path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
        raise ConfigError(
            f"Error: cannot write configuration file '{config_path}': {exc}"
        ) from exc


def ensure_config_file(config_path: Path) -> None:
    """!
    @brief Bootstrap the global configuration file from schema defaults when absent.
    @param config_path {Path} Absolute global configuration file path.
    @return {None} Function return value.
    @throws {ConfigError} Raised when the path is a directory or the bootstrap write fails.
    @details Missing parent directories are created and the file is initialized from the
    canonical schema defaults; an existing file is never overwritten (SRS-529).
    """
    if config_path.is_dir():
        raise ConfigError(
            f"Error: configuration path '{config_path}' is a directory, not a file."
        )
    if config_path.exists():
        return
    write_config(config_path, default_config())


def _parse_index(token: str, path: str) -> int:
    """!
    @brief Parse one non-negative decimal array index token.
    @param token {str} Raw path token.
    @param path {str} Canonical path used inside diagnostics.
    @return {int} Parsed zero-based index.
    @throws {ConfigError} Raised for negative, signed, or non-decimal tokens.
    """
    if not token.isdigit():
        raise ConfigError(
            f"Error: invalid array index '{token}' in path '{path}'; "
            "use a non-negative decimal index, 'append', '+', or 'insert:<Idx>'."
        )
    return int(token)


def _out_of_range(owner_path: str, index: int, length: int) -> ConfigError:
    """!
    @brief Build the out-of-range diagnostic for an array access.
    @param owner_path {str} Canonical path of the owning array parameter.
    @param index {int} Rejected index.
    @param length {int} Current array length.
    @return {ConfigError} English diagnostic describing the valid range and append option.
    """
    valid = "0" if length == 0 else f"0..{length - 1}"
    return ConfigError(
        f"Error: index {index} is out of range for '{owner_path}' (valid range: {valid}); "
        f"use '{owner_path}:append' or '{owner_path}:+' to add an item."
    )


def _child_of_section(spec: SchemaNode, token: str, path: str) -> SchemaNode:
    """!
    @brief Resolve one section/dictionary field token or raise an unknown-token error.
    @param spec {SchemaNode} Section or dictionary node holding candidate fields.
    @param token {str} Exact canonical field token.
    @param path {str} Canonical path used inside diagnostics.
    @return {SchemaNode} Matching field node.
    @throws {ConfigError} Raised when the token is not a canonical schema token.
    """
    child = find_field(spec, token)
    if child is None:
        raise ConfigError(
            f"Error: unknown configuration token '{token}' in path '{path}'."
        )
    return child


def resolve_target(config: dict[str, Any], path: str) -> Target:
    """!
    @brief Resolve a canonical colon-separated path against the configuration schema.
    @param config {dict[str, Any]} Effective configuration used as the resolution root.
    @param path {str} Canonical colon-separated configuration path.
    @return {Target} Resolved operation target.
    @throws {ConfigError} Raised for empty tokens, unknown tokens, invalid indices,
    out-of-range indices, and missing dynamic map keys.
    @details Paths are resolved token by token against the schema, never against displayed
    strings; `append`, `+`, and `insert:<Idx>` are recognized only inside array paths
    (SRS-520, SRS-533, SRS-534).
    """
    if not path:
        raise ConfigError("Error: a configuration path is required.")
    tokens = path.split(":")
    if any(token == "" for token in tokens):
        raise ConfigError(
            f"Error: path '{path}' contains an empty token; map keys containing ':' "
            "are not addressable."
        )
    spec = CONFIG_SECTION
    value: Any = config
    container: Any = config
    key: Any = None
    if tokens[0] != CONFIG_SECTION.token:
        raise ConfigError(
            f"Error: unknown configuration section '{tokens[0]}' in path '{path}'; "
            f"canonical paths start with '{CONFIG_SECTION.token}'."
        )
    index = 1
    while index < len(tokens):
        token = tokens[index]
        is_last = index == len(tokens) - 1
        if spec.kind == KIND_SECTION:
            child = _child_of_section(spec, token, path)
            if not isinstance(value, dict) or token not in value:
                raise ConfigError(
                    f"Error: configuration node '{path}' is not available."
                )
            container, key = value, token
            value, spec = value[token], child
            index += 1
        elif spec.kind == KIND_ARRAY:
            if not isinstance(value, list):
                raise ConfigError(
                    f"Error: '{path}' does not resolve to a JSON array."
                )
            if token in ("append", "+"):
                if not is_last:
                    raise ConfigError(
                        f"Error: array operation '{token}' must terminate path '{path}'."
                    )
                assert spec.item is not None
                return Target("append", spec.item, None, value, None)
            if token == "insert":
                if index + 2 != len(tokens):
                    raise ConfigError(
                        f"Error: array operation 'insert' requires exactly one index "
                        f"at the end of path '{path}'."
                    )
                insert_at = _parse_index(tokens[index + 1], path)
                if insert_at > len(value):
                    raise ConfigError(
                        f"Error: insertion index {insert_at} is out of range for '{path}' "
                        f"(valid range: 0..{len(value)})."
                    )
                assert spec.item is not None
                return Target("insert", spec.item, None, value, insert_at)
            item_index = _parse_index(token, path)
            if item_index >= len(value):
                owner_path = ":".join(tokens[:index])
                raise _out_of_range(owner_path, item_index, len(value))
            if is_last:
                assert spec.item is not None
                return Target("array_item", spec.item, value[item_index], value, item_index)
            if spec.item is None or spec.item.kind != KIND_DICTIONARY:
                raise ConfigError(
                    f"Error: '{path}' has no configurable descendants."
                )
            container, key = value, item_index
            value, spec = value[item_index], spec.item
            index += 1
        elif spec.kind == KIND_MAP:
            if not isinstance(value, dict):
                raise ConfigError(
                    f"Error: '{path}' does not resolve to a JSON object."
                )
            assert spec.item is not None
            if is_last:
                return Target(
                    "map_key",
                    spec.item,
                    value[token] if token in value else MISSING,
                    value,
                    token,
                )
            if token not in value:
                raise ConfigError(
                    f"Error: configuration key '{token}' does not exist in '{path}'."
                )
            container, key = value, token
            value, spec = value[token], spec.item
            index += 1
        elif spec.kind == KIND_DICTIONARY:
            child = _child_of_section(spec, token, path)
            if not isinstance(value, dict):
                raise ConfigError(
                    f"Error: '{path}' does not resolve to a JSON object."
                )
            container, key = value, token
            if is_last:
                return Target(
                    "dict_field",
                    child,
                    value[token] if token in value else MISSING,
                    value,
                    token,
                )
            if token not in value:
                raise ConfigError(
                    f"Error: configuration field '{token}' does not exist in '{path}'."
                )
            value, spec = value[token], child
            index += 1
        else:
            raise ConfigError(
                f"Error: configuration token '{token}' has no descendants in path '{path}'."
            )
    return Target("node", spec, value, container, key)


def parse_cli_value(
    spec: SchemaNode, text: str, path: str, reject_collections: bool = False
) -> Any:
    """!
    @brief Parse one CLI value into the schema type of the target node.
    @param spec {SchemaNode} Schema node governing the target value.
    @param text {str} Raw CLI value text.
    @param path {str} Canonical path used inside diagnostics.
    @param reject_collections {bool} True for single-item array writes; rejects JSON arrays
    and objects supplied where exactly one item is required.
    @return {Any} Parsed and validated typed value.
    @throws {ConfigError} Raised for malformed JSON, invalid types, or schema violations.
    @details Plain strings are taken verbatim; booleans, arrays, maps, dictionaries, and
    sections require JSON text so numbers and booleans stay typed (SRS-530, SRS-535).
    """
    if spec.kind == KIND_STRING:
        if reject_collections and text.strip().startswith(("[", "{")):
            try:
                collection = json.loads(text)
            except json.JSONDecodeError:
                collection = None
            if isinstance(collection, (list, dict)):
                raise ConfigError(
                    f"Error: '{path}' accepts exactly one item; supply one string "
                    "value instead of a JSON array or object."
                )
        validate_node(spec, text, path)
        return text
    if spec.kind == KIND_BOOLEAN:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"Error: value for '{path}' must be the JSON boolean true or false."
            ) from exc
        validate_node(spec, parsed, path)
        return parsed
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"Error: value for '{path}' is not valid JSON: "
            f"{exc.msg} at line {exc.lineno} column {exc.colno}."
        ) from exc
    validate_node(spec, parsed, path)
    return parsed


def get_value(config: dict[str, Any], path: str) -> Any:
    """!
    @brief Read the effective value addressed by one canonical path.
    @param config {dict[str, Any]} Effective configuration.
    @param path {str} Canonical colon-separated configuration path.
    @return {Any} JSON-serializable value addressed by the path.
    @throws {ConfigError} Raised for invalid paths, absent values, and write-only operations.
    """
    target = resolve_target(config, path)
    if target.op in ("node", "array_item"):
        return target.value
    if target.op in ("dict_field", "map_key"):
        if target.value is MISSING:
            if target.op == "dict_field" and target.spec.has_default:
                return copy.deepcopy(target.spec.default)
            raise ConfigError(f"Error: '{path}' has no stored value.")
        return target.value
    raise ConfigError(
        f"Error: '{path}' is a write-only array operation and cannot be read."
    )


def apply_set(config: dict[str, Any], path: str, text: str) -> dict[str, Any]:
    """!
    @brief Apply one `--set` operation to a copy of the effective configuration.
    @param config {dict[str, Any]} Effective configuration.
    @param path {str} Canonical colon-separated configuration path.
    @param text {str} Raw CLI value text.
    @return {dict[str, Any]} New validated configuration payload.
    @throws {ConfigError} Raised before mutation when the path or value is invalid.
    @details Supports primitives, whole branches, whole arrays/maps, single array items,
    append and insert operations, dictionary fields, and dynamic map keys
    (SRS-530, SRS-533, SRS-534, SRS-535).
    """
    working = copy.deepcopy(config)
    target = resolve_target(working, path)
    if target.op == "node" and target.key is None:
        try:
            parsed_root = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"Error: value for '{path}' is not valid JSON: "
                f"{exc.msg} at line {exc.lineno} column {exc.colno}."
            ) from exc
        if not isinstance(parsed_root, dict):
            raise ConfigError(f"Error: '{path}' must be replaced by a JSON object.")
        working = normalize_config(parsed_root)
    else:
        parsed = parse_cli_value(
            target.spec,
            text,
            path,
            reject_collections=target.op in ("append", "insert", "array_item"),
        )
        if target.op == "append":
            target.container.append(parsed)
        elif target.op == "insert":
            target.container.insert(target.key, parsed)
        else:
            target.container[target.key] = parsed
    validate_node(CONFIG_SECTION, working, CONFIG_SECTION.token)
    return working


def apply_unset(config: dict[str, Any], path: str) -> dict[str, Any]:
    """!
    @brief Apply one `--unset` operation to a copy of the effective configuration.
    @param config {dict[str, Any]} Effective configuration.
    @param path {str} Canonical colon-separated configuration path.
    @return {dict[str, Any]} New validated configuration payload.
    @throws {ConfigError} Raised for write-only operations, absent keys, and required fields.
    @details Restores declared schema defaults, deletes optional fields and map keys, and
    removes array elements while keeping indices contiguous (SRS-530, SRS-533, SRS-536).
    """
    working = copy.deepcopy(config)
    target = resolve_target(working, path)
    if target.op in ("append", "insert"):
        raise ConfigError(
            f"Error: '{path}' is a write-only array operation and cannot be unset."
        )
    if target.op == "array_item":
        del target.container[target.key]
    elif target.op == "map_key":
        if target.key not in target.container:
            raise ConfigError(
                f"Error: configuration key '{target.key}' does not exist in '{path}'."
            )
        del target.container[target.key]
    else:
        if target.key is None:
            working = default_config()
        elif target.spec.has_default:
            target.container[target.key] = copy.deepcopy(target.spec.default)
        elif target.spec.kind == KIND_SECTION:
            target.container[target.key] = default_config()
        elif target.spec.optional:
            if target.key not in target.container:
                raise ConfigError(f"Error: '{path}' has no stored value.")
            del target.container[target.key]
        else:
            raise ConfigError(
                f"Error: '{path}' is required by the schema and has no default; "
                "it cannot be reset."
            )
    validate_node(CONFIG_SECTION, working, CONFIG_SECTION.token)
    return working


def _display_width(text: str) -> int:
    """!
    @brief Measure the terminal display width of one table cell.
    @param text {str} Sanitized cell text.
    @return {int} Display column count honoring wide and combining characters.
    """
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def _sanitize_cell(text: str) -> str:
    """!
    @brief Escape control characters so one cell stays on one physical line.
    @param text {str} Raw cell payload.
    @return {str} Printable single-line cell text.
    """
    out: list[str] = []
    for char in text:
        if char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif ord(char) < 0x20 or ord(char) == 0x7F:
            out.append("\\x{:02x}".format(ord(char)))
        else:
            out.append(char)
    return "".join(out)


def format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    """!
    @brief Render one rectangular Unicode box-drawing table.
    @param headers {Sequence[str]} Column header labels.
    @param rows {Sequence[Sequence[str]]} Cell values matching the header count.
    @return {list[str]} Physical table lines without structural tree prefixes.
    @details Column widths derive from the maximum display width of the header and every
    formatted cell; all borders share the same column boundaries (SRS-539).
    """
    safe_headers = [_sanitize_cell(header) for header in headers]
    safe_rows = [[_sanitize_cell(cell) for cell in row] for row in rows]
    widths = []
    for position, header in enumerate(safe_headers):
        widths.append(
            max([_display_width(header)] + [
                _display_width(row[position]) for row in safe_rows
            ])
        )

    def border(left: str, middle: str, right: str) -> str:
        """! @brief Build one horizontal table border line. """
        return left + middle.join("─" * (width + 2) for width in widths) + right

    def line(cells: Sequence[str]) -> str:
        """! @brief Build one padded table content line. """
        padded = [
            " " + cell + " " * (widths[position] - _display_width(cell) + 1)
            for position, cell in enumerate(cells)
        ]
        return "│" + "│".join(padded) + "│"

    lines = [border("┌", "┬", "┐"), line(safe_headers), border("├", "┼", "┤")]
    lines.extend(line(row) for row in safe_rows)
    lines.append(border("└", "┴", "┘"))
    return lines


def render_tree(root: RenderNode) -> list[str]:
    """!
    @brief Render one configuration tree with the mandatory prefix algorithm.
    @param root {RenderNode} Display root of the requested tree.
    @return {list[str]} Complete physical output lines.
    @details The display root has no structural marker and attached root details use a
    four-space indent; every real child is emitted by `_emit_node` (SRS-524, SRS-525).
    """
    lines = [root.heading]
    for detail in root.details:
        lines.extend(INDENT + detail_line for detail_line in detail)
    for position, child in enumerate(root.children):
        _emit_node(child, [], position == len(root.children) - 1, lines)
    return lines


def _emit_node(
    node: RenderNode,
    ancestor_has_next: list[bool],
    is_last: bool,
    lines: list[str],
) -> None:
    """!
    @brief Emit one real configuration node and its attached details recursively.
    @param node {RenderNode} Node to emit.
    @param ancestor_has_next {list[bool]} Per-ancestor later-sibling flags.
    @param is_last {bool} True when the node is the final sibling at its depth.
    @param lines {list[str]} Accumulated output lines.
    @return {None} Function return value.
    @details Heading prefix and detail prefix derive only from real sibling topology;
    details never receive a structural marker or additional depth (SRS-524, SRS-525).
    """
    prefix = "".join(
        CONTINUE if has_next else INDENT for has_next in ancestor_has_next
    )
    lines.append(prefix + (LAST if is_last else BRANCH) + node.heading)
    detail_prefix = prefix + (INDENT if is_last else CONTINUE)
    for detail in node.details:
        lines.extend(detail_prefix + detail_line for detail_line in detail)
    for position, child in enumerate(node.children):
        _emit_node(
            child,
            ancestor_has_next + [not is_last],
            position == len(node.children) - 1,
            lines,
        )


def render_text(root: RenderNode) -> str:
    """!
    @brief Render one configuration tree as newline-terminated text.
    @param root {RenderNode} Display root of the requested tree.
    @return {str} Complete output text without a trailing newline.
    """
    return "\n".join(render_tree(root))


def _json_value(value: Any) -> str:
    """!
    @brief Encode one value as JSON text for display.
    @param value {Any} JSON-serializable value.
    @return {str} JSON-encoded text with non-ASCII characters preserved.
    """
    return json.dumps(value, ensure_ascii=False)


def _shell(value: str) -> str:
    """!
    @brief Shell-quote one literal value for a copyable command example.
    @param value {str} Literal value.
    @return {str} POSIX shell-quoted value.
    """
    return shlex.quote(value)


def _example_item(node: SchemaNode) -> str:
    """!
    @brief Choose a schema-valid example value for one collection item.
    @param node {SchemaNode} Item schema node.
    @return {str} Example value text.
    """
    if node.enum:
        return node.enum[0]
    return "src"


def _example_key(map_node: SchemaNode) -> str:
    """!
    @brief Choose a schema-valid example key for one dynamic map.
    @param map_node {SchemaNode} Map schema node.
    @return {str} Example key text.
    """
    if map_node.key_enum:
        return map_node.key_enum[0]
    return "ExampleKey"


_STRING_EXAMPLES: dict[str, str] = {
    "docs-dir": "documentation",
    "tests-dir": "unittests",
}
"""! @brief Schema-valid alternative example values for string parameters (SRS-541)."""


def _print_marker(spec: SchemaNode, value: Any) -> str:
    """!
    @brief Build the default/custom status marker of one primitive parameter.
    @param spec {SchemaNode} Parameter schema node.
    @param value {Any} Current typed value.
    @return {str} Empty text for nodes without defaults, otherwise the status marker.
    """
    if not spec.has_default:
        return ""
    if value == spec.default:
        return " (default)"
    return " (custom | default: " + _json_value(spec.default) + ")"


def _collection_summary(spec: SchemaNode, value: Any, path: str) -> str:
    """!
    @brief Build the `--print` value summary of one collection parameter.
    @param spec {SchemaNode} Collection schema node.
    @param value {Any} Current collection value.
    @param path {str} Canonical parameter path.
    @return {str} Collection summary text.
    @details Empty collections emit a complete-path action hint instead of an empty table
    (SRS-537, SRS-539).
    """
    if spec.kind == KIND_ARRAY:
        assert spec.item is not None
        if not value:
            example = _example_item(spec.item)
            return f"(empty list | add: --set {path}:+ {_shell(example)})"
        if spec.item.kind == KIND_DICTIONARY:
            return (
                f"({len(value)} rows | cell target: {path}:<Idx>:<Field> | "
                f"add: {path}:+)"
            )
        return f"({len(value)} items | row target: {path}:<Idx> | add: {path}:+)"
    if spec.kind == KIND_MAP:
        if not value:
            example_key = _example_key(spec)
            assert spec.item is not None
            return (
                f"(empty map | set key: --set {path}:{example_key} "
                f"{_shell(_example_map_value(spec.item))})"
            )
        return f"({len(value)} entries | key target: {path}:<Key>)"
    return _json_value(value)


def _example_map_value(item: SchemaNode) -> str:
    """!
    @brief Build one schema-valid example JSON text for a map value.
    @param item {SchemaNode} Map value schema node.
    @return {str} JSON text accepted by the map value schema.
    """
    if item.kind == KIND_ARRAY and item.item is not None:
        if item.item.kind == KIND_DICTIONARY:
            return '[{"module": "Pylance"}]'
        return '["' + _example_item(item.item) + '"]'
    if item.kind == KIND_STRING:
        return '"example"'
    return "{}"


def _value_cell(spec: SchemaNode, value: Any) -> str:
    """!
    @brief Render one table cell value for a configuration value.
    @param spec {SchemaNode} Schema node of the value.
    @param value {Any} JSON-serializable value.
    @return {str} Single-line cell text.
    """
    if spec.kind == KIND_ARRAY:
        label = "rows" if spec.item is not None and spec.item.kind == KIND_DICTIONARY else "items"
        return f"{len(value)} {label}"
    if spec.kind == KIND_MAP:
        return f"{len(value)} entries"
    return _json_value(value)


def _print_parameter_details(
    spec: SchemaNode, value: Any, path: str
) -> list[list[str]]:
    """!
    @brief Build the attached `--print` details of one parameter node.
    @param spec {SchemaNode} Parameter schema node.
    @param value {Any} Current typed value.
    @param path {str} Canonical parameter path.
    @return {list[list[str]]} Attached detail blocks rendered with the owner prefix.
    @details Non-empty collections attach measured rectangular tables; scalars attach no
    details (SRS-537, SRS-539).
    """
    details: list[list[str]] = []
    if spec.kind == KIND_ARRAY and value:
        assert spec.item is not None
        if spec.item.kind == KIND_DICTIONARY:
            headers = ["Idx"] + [child.token for child in spec.item.fields]
            rows = [
                [str(position)] + [
                    "" if child.token not in entry else _json_value(entry[child.token])
                    for child in spec.item.fields
                ]
                for position, entry in enumerate(value)
            ]
        else:
            headers = ["Idx", "Value"]
            rows = [
                [str(position), _json_value(item)]
                for position, item in enumerate(value)
            ]
        details.append(format_table(headers, rows))
    elif spec.kind == KIND_MAP and value:
        assert spec.item is not None
        details.append(
            format_table(
                ["Key", "Value"],
                [
                    [key, _value_cell(spec.item, item)]
                    for key, item in value.items()
                ],
            )
        )
    return details


def _dictionary_fields(spec: SchemaNode) -> tuple[SchemaNode, ...]:
    """!
    @brief Resolve the fixed field set documented by an `Item Schema` table.
    @param spec {SchemaNode} Array or dictionary schema node.
    @return {tuple[SchemaNode, ...]} Fixed fields, or an empty tuple for primitives.
    """
    if spec.kind == KIND_DICTIONARY:
        return spec.fields
    if spec.kind == KIND_ARRAY and spec.item is not None:
        return spec.item.fields
    return ()


def _item_schema_table(fields: Sequence[SchemaNode]) -> list[str]:
    """!
    @brief Render the `Item Schema` table of one fixed-field dictionary.
    @param fields {Sequence[SchemaNode]} Fixed field schema nodes.
    @return {list[str]} Table lines.
    """
    headers = ["Field", "Type & Constraints", "Default / Req", "Description & Example"]
    rows = []
    for child in fields:
        type_text = child.type_label
        if child.constraints:
            type_text += ": " + child.constraints
        if child.has_default:
            requirement = _json_value(child.default)
        elif child.optional:
            requirement = "optional"
        else:
            requirement = "REQUIRED"
        rows.append(
            [
                child.token,
                type_text,
                requirement,
                child.description
                + (" (example: " + child.example + ")" if child.example else ""),
            ]
        )
    return format_table(headers, rows)


def _array_examples(spec: SchemaNode, path: str) -> list[list[str]]:
    """!
    @brief Build the attached `--info` command examples of one array parameter.
    @param spec {SchemaNode} Array schema node.
    @param path {str} Canonical array path.
    @return {list[list[str]]} Detail blocks with complete copyable commands.
    @details Single-item operations receive exactly one JSON item; the whole-array
    overwrite receives a JSON array (SRS-535, SRS-541).
    """
    assert spec.item is not None
    if spec.item.kind == KIND_DICTIONARY:
        item_text = '{"module": "Pylance"}'
        first_field = spec.item.fields[0]
        cell_path = path + ":0:" + first_field.token
        cell_value = first_field.enum[0] if first_field.enum else "value"
        lines = [
            f"Add new row : --set {path}:+ {_shell(item_text)}",
            f"Insert row : --set {path}:insert:0 {_shell(item_text)}",
            f"Replace row : --set {path}:0 {_shell(item_text)}",
            f"Update cell : --set {cell_path} {_shell(cell_value)}",
            f"Delete row : --unset {path}:0",
            f"Full overwrite : --set {path} {_shell('[' + item_text + ']')}",
        ]
    else:
        example = _shell(_example_item(spec.item))
        array_text = "[" + _json_value(_example_item(spec.item)) + "]"
        lines = [
            f"Add item : --set {path}:+ {example}",
            f"Insert item : --set {path}:insert:0 {example}",
            f"Replace item : --set {path}:0 {example}",
            f"Delete item : --unset {path}:0",
            f"Full overwrite : --set {path} {_shell(array_text)}",
        ]
    lines.append(f"Reset array : --unset {path}")
    return [lines]


def _info_parameter_details(spec: SchemaNode, path: str) -> list[list[str]]:
    """!
    @brief Build the attached `--info` details of one parameter node.
    @param spec {SchemaNode} Parameter schema node.
    @param path {str} Canonical parameter path.
    @return {list[list[str]]} Attached detail blocks with defaults, commands, and tables.
    @details Required dictionary fields without defaults never advertise a reset command
    (SRS-536, SRS-538, SRS-541).
    """
    details: list[list[str]] = []
    if spec.kind == KIND_SECTION:
        return [[f"Reset block : --unset {path}"]]
    if spec.has_default:
        details.append(
            [
                f"Default : {_json_value(spec.default)} "
                f"(restored via: --unset {path})"
            ]
        )
    if spec.kind in (KIND_STRING, KIND_BOOLEAN):
        if spec.kind == KIND_BOOLEAN:
            example = "false" if spec.default is True else "true"
        else:
            example = _STRING_EXAMPLES.get(spec.token, "value")
        details.append([f"Set cmd : --set {path} {_shell(example)}"])
        details.append([f"Reset cmd : --unset {path}"])
        return details
    if spec.kind == KIND_ARRAY:
        assert spec.item is not None
        enum = spec.item.enum
        if enum is not None:
            default_items = spec.default if spec.has_default else []
            rows = [
                [
                    value,
                    "yes" if value in default_items else "no",
                    (spec.item.enum_meanings or {}).get(value, ""),
                    f"--set {path}:+ {_shell(value)}",
                ]
                for value in enum
            ]
            details.append(
                ["Allowed Values:"]
                + format_table(
                    ["Value", "Default", "Meaning", "Set cmd"], rows
                )
            )
        details.extend(_array_examples(spec, path))
        return details
    if spec.kind == KIND_MAP:
        details.append(
            [
                "Key type : "
                + (", ".join(spec.key_enum) if spec.key_enum else "free-form string")
            ]
        )
        assert spec.item is not None
        fields = _dictionary_fields(spec.item)
        if fields:
            details.append(["Item Schema:"] + _item_schema_table(fields))
        example_key = _example_key(spec)
        example_value = _example_map_value(spec.item)
        map_example = (
            '{"' + example_key + '": ' + example_value + "}"
        )
        details.append(
            [
                f"Set key : --set {path}:{example_key} {_shell(example_value)}",
                f"Remove key : --unset {path}:{example_key}",
                f"Full overwrite : --set {path} {_shell(map_example)}",
                f"Reset cmd : --unset {path}",
            ]
        )
        details.extend(_array_examples(spec.item, f"{path}:{example_key}"))
        return details
    details.append([f"Reset cmd : --unset {path}"])
    return details


def _print_parameter_heading(spec: SchemaNode, value: Any, token: str, path: str) -> str:
    """!
    @brief Build the `--print` heading of one parameter node.
    @param spec {SchemaNode} Parameter schema node.
    @param value {Any} Current typed value.
    @param token {str} Exact canonical node token.
    @param path {str} Canonical node path.
    @return {str} Heading text without structural prefix.
    """
    if spec.kind in (KIND_ARRAY, KIND_MAP):
        rendered = _collection_summary(spec, value, path)
        return f"{token} = {rendered}"
    if spec.kind == KIND_DICTIONARY:
        return f"{token} = {_json_value(value)}"
    return f"{token} = {_json_value(value)}{_print_marker(spec, value)}"


def _info_parameter_heading(spec: SchemaNode, token: str) -> str:
    """!
    @brief Build the `--info` heading of one parameter node.
    @param spec {SchemaNode} Parameter schema node.
    @param token {str} Exact canonical node token.
    @return {str} `Token - [Type: constraints] Description` heading text.
    """
    type_text = spec.type_label
    if spec.constraints:
        type_text += ": " + spec.constraints
    return f"{token} - [{type_text}] {spec.description}"


def _build_node(
    spec: SchemaNode,
    value: Any,
    token: str,
    path: str,
    info: bool,
) -> RenderNode:
    """!
    @brief Build one real configuration node for the requested display mode.
    @param spec {SchemaNode} Schema node of the configuration value.
    @param value {Any} Current effective value.
    @param token {str} Exact canonical node token.
    @param path {str} Canonical node path.
    @param info {bool} True for `--info`; False for `--print`.
    @return {RenderNode} Renderable node with attached details and real children.
    @details Only sections expose real child nodes; metadata and tables stay attached
    details (SRS-522, SRS-525, SRS-540).
    """
    if spec.kind == KIND_SECTION:
        heading = _section_heading(path, info)
        details = _info_parameter_details(spec, path) if info else []
    elif info:
        heading = _info_parameter_heading(spec, token)
        details = _info_parameter_details(spec, path)
    else:
        heading = _print_parameter_heading(spec, value, token, path)
        details = _print_parameter_details(spec, value, path)
    children: list[RenderNode] = []
    if spec.kind == KIND_SECTION and isinstance(value, dict):
        for child in spec.children:
            child_value = value.get(child.token)
            if child_value is None and child.has_default:
                child_value = copy.deepcopy(child.default)
            children.append(
                _build_node(
                    child,
                    child_value,
                    child.token,
                    f"{path}:{child.token}",
                    info,
                )
            )
    return RenderNode(
        token=token,
        canonical_path=path,
        kind=spec.kind,
        heading=heading,
        details=details,
        children=children,
    )


def _section_heading(path: str, info: bool) -> str:
    """!
    @brief Build the section heading carrying the canonical path badge.
    @param path {str} Canonical section path.
    @param info {bool} True for `--info`; False for `--print`.
    @return {str} `Token - [Path: <full canonical path>]` heading text.
    """
    heading = f"{CONFIG_SECTION.token} - [Path: {path}]"
    if info:
        heading += " " + CONFIG_SECTION.description
    return heading


def build_full_tree(config: dict[str, Any], info: bool) -> RenderNode:
    """!
    @brief Build the complete configuration tree for `--print` or `--info`.
    @param config {dict[str, Any]} Effective configuration.
    @param info {bool} True for `--info`; False for `--print`.
    @return {RenderNode} Virtual display root holding the `Configuration` section.
    """
    mode_text = "Configuration schema" if info else "Current configuration"
    section = _build_node(
        CONFIG_SECTION, config, CONFIG_SECTION.token, CONFIG_SECTION.token, info
    )
    return RenderNode(
        token=ROOT_LABEL,
        canonical_path="",
        kind=KIND_SECTION,
        heading=f"{ROOT_LABEL} - {mode_text}",
        details=[],
        children=[section],
    )


def build_subtree(config: dict[str, Any], path: str, info: bool) -> RenderNode:
    """!
    @brief Build the requested subtree or parameter display.
    @param config {dict[str, Any]} Effective configuration.
    @param path {str} Canonical colon-separated configuration path.
    @param info {bool} True for `--info`; False for `--print`.
    @return {RenderNode} Requested node as the unconnected display root.
    @throws {ConfigError} Raised for unknown paths and non-displayable collection elements.
    @details No ancestors are invented; the requested node becomes the display root with
    four-space-indented details and normally rendered real children (SRS-526).
    """
    target = resolve_target(config, path)
    token = path.split(":")[-1]
    if target.op == "node":
        return _build_node(target.spec, target.value, token, path, info)
    if target.op == "map_key":
        if target.value is MISSING:
            raise ConfigError(f"Error: '{path}' has no stored value.")
        return _build_node(target.spec, target.value, token, path, info)
    raise ConfigError(
        f"Error: '{path}' is a collection element; use --get for element values."
    )


def handle_get(config_path: Path, path: str) -> str:
    """!
    @brief Execute one `--get` read and return JSON text.
    @param config_path {Path} Absolute global configuration file path.
    @param path {str} Canonical configuration path.
    @return {str} JSON-encoded value text.
    @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.
    """
    ensure_config_file(config_path)
    return _json_value(get_value(load_effective_config(config_path), path))


def handle_set(config_path: Path, path: str, text: str) -> None:
    """!
    @brief Execute one `--set` write.
    @param config_path {Path} Absolute global configuration file path.
    @param path {str} Canonical configuration path.
    @param text {str} Raw CLI value text.
    @return {None} Function return value.
    @throws {ConfigError} Raised before mutation when the operation is invalid.
    """
    ensure_config_file(config_path)
    updated = apply_set(load_effective_config(config_path), path, text)
    write_config(config_path, updated)


def handle_unset(config_path: Path, path: str) -> None:
    """!
    @brief Execute one `--unset` write.
    @param config_path {Path} Absolute global configuration file path.
    @param path {str} Canonical configuration path.
    @return {None} Function return value.
    @throws {ConfigError} Raised before mutation when the operation is invalid.
    """
    ensure_config_file(config_path)
    updated = apply_unset(load_effective_config(config_path), path)
    write_config(config_path, updated)


def handle_print_raw(config_path: Path) -> bytes:
    """!
    @brief Return the unmodified on-disk configuration file bytes.
    @param config_path {Path} Absolute global configuration file path.
    @return {bytes} Raw file bytes exactly as stored.
    @throws {ConfigError} Raised when the bootstrapped file cannot be read.
    @details Never reformats, prepends a heading, or appends explanatory text (SRS-528).
    """
    ensure_config_file(config_path)
    try:
        return config_path.read_bytes()
    except OSError as exc:
        raise ConfigError(
            f"Error: cannot read configuration file '{config_path}': {exc}"
        ) from exc


def handle_display(config_path: Path, path: Optional[str], info: bool) -> str:
    """!
    @brief Execute one `--print` or `--info` display request.
    @param config_path {Path} Absolute global configuration file path.
    @param path {Optional[str]} Requested canonical path; None renders the full tree.
    @param info {bool} True for `--info`; False for `--print`.
    @return {str} Rendered tree text without a trailing newline.
    @throws {ConfigError} Raised for invalid paths or schema-invalid stored values.
    """
    ensure_config_file(config_path)
    config = load_effective_config(config_path)
    if path is None:
        return render_text(build_full_tree(config, info))
    return render_text(build_subtree(config, path, info))
